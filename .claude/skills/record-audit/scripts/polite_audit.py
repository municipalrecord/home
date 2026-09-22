#!/usr/bin/env python3
"""Transport and bookkeeping for a polite, resumable record audit.

This module deliberately has no opinion about what a target should contain.
It handles the part every audit rewrites identically — throttling, backoff,
capped reads, resumable state, verdict counts — so the audit itself is only
the identity checks, which are the part worth your attention.

Typical use:

    from polite_audit import AuditRun

    def check(url, row, fetch):
        status, body, headers = fetch(url)
        text = body.decode("utf-8", "replace")
        if row["expect"] in text:
            return "ok", f"page shows {row['expect']!r}"
        return "mismatch", f"page does not show {row['expect']!r}"

    run = AuditRun("results.json", contact="contact@example.org")
    run.run_all(manifest, check)     # manifest: {url: {...}, ...}

`run_all` skips rows already settled by an earlier run, retries only the
rows that mean "we don't know" (error / unreachable / no-baseline), maps
exceptions onto those verdicts, flushes state periodically, and prints a
verdict tally at the end. Pass recheck=True to redo everything.

For a loop you drive yourself, use `todo()` and `record()` directly; you
then own the exception handling and the pacing between requests.

Seeded sampling lives here too (`seeded_sample`), because a reproducible
sample is part of the same discipline: the seed goes in the write-up, and
raising n on a fixed seed extends the previous sample rather than replacing
it.
"""
from __future__ import annotations

import hashlib
import json
import random
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# Verdicts that mean "we did not find out", so a rerun should retry them.
# Anything else is a settled finding and is left alone.
UNSETTLED = ("error", "unreachable", "no-baseline")

DEFAULT_DELAY = 1.2          # seconds between requests, single-threaded
DEFAULT_CAP = 80 * 2 ** 20   # refuse to read more than this from one response
BACKOFF_START = 15
BACKOFF_CAP = 600


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def seeded_sample(rows, n, seed):
    """Reproducible sample. Publish the seed alongside n and the date.

    Deliberately a seeded shuffle truncated to n, not `random.sample`:
    `sample` switches internal strategies with k, so sample(rows, 100)
    does not begin with sample(rows, 50) on the same seed. Shuffling once
    and slicing does, which is what makes raising n *extend* an audit —
    the earlier rows keep their results, and only the new tail needs
    fetching. Rerunning at a lower n is then a strict subset too, so the
    series stays comparable in both directions.

    Rows must be in a stable order (sort them at the query) or the seed
    reproduces nothing.
    """
    pool = list(rows)
    random.Random(seed).shuffle(pool)
    return pool[:min(n, len(pool))]


def subsample(sample, k, seed):
    """Draw an expensive sub-check from an already-drawn sample.

    Same prefix-stable construction, so raising k extends it. Report its
    denominator separately — it is a sample of a sample.
    """
    return seeded_sample(sample, k, seed)


class Throttle:
    """Single-threaded pacing plus exponential backoff on server distress.

    Being slow is the cost of not becoming traffic a city has to block.
    Backoff announces itself on stdout so a watching human knows why the
    run went quiet rather than assuming it hung.
    """

    def __init__(self, delay=DEFAULT_DELAY, log=print):
        self.delay = delay
        self.penalty = 0
        self.last = 0.0
        self.log = log

    def wait(self):
        gap = time.monotonic() - self.last
        if self.last and gap < self.delay:
            time.sleep(self.delay - gap)
        self.last = time.monotonic()

    def ok(self):
        self.penalty = 0

    def bad(self):
        self.penalty = min((self.penalty or BACKOFF_START) * 2, BACKOFF_CAP)
        self.log(f"    … throttled/erroring, sleeping {self.penalty}s")
        time.sleep(self.penalty)


class AuditRun:
    """Resumable audit state over a manifest of {url: row}.

    results.json holds one record per URL: kind, expect, verdict, detail,
    checked_at, sources. It is the audit's publishable raw artifact, so it
    is written as indented JSON a human can read and diff.
    """

    def __init__(self, results_path, contact, agent="MunicipalRecord/1.0",
                 delay=DEFAULT_DELAY, cap=DEFAULT_CAP, recheck=False,
                 flush_every=25, log=print):
        self.path = Path(results_path)
        self.cap = cap
        self.recheck = recheck
        self.flush_every = flush_every
        self.log = log
        self.throttle = Throttle(delay, log=log)
        self.ua = {"User-Agent": f"{agent} (record audit; {contact})"}
        self.results = (json.loads(self.path.read_text())
                        if self.path.exists() else {})

    # ---- transport -------------------------------------------------

    def fetch(self, url, data=None, headers=None):
        """Throttled GET (POST when `data` is given), with a read cap.

        Returns (status, body, headers). Raises urllib's HTTPError so the
        caller — or run_all — can distinguish "server said no" from a
        content finding.
        """
        self.throttle.wait()
        hdrs = dict(self.ua)
        if data is not None:
            hdrs["Content-Type"] = "application/json"
        hdrs.update(headers or {})
        req = urllib.request.Request(url, data=data, headers=hdrs)
        resp = urllib.request.urlopen(req, timeout=45)
        chunks, size = [], 0
        while True:
            chunk = resp.read(2 ** 20)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > self.cap:
                raise ValueError(f"response exceeds {self.cap} bytes")
        return resp.status, b"".join(chunks), resp.headers

    # ---- state -----------------------------------------------------

    def settled(self, url) -> bool:
        prev = self.results.get(url)
        return bool(prev) and prev.get("verdict") not in UNSETTLED

    def todo(self, manifest, kind=None):
        """Rows still needing a check, sorted for a stable run order."""
        rows = [(u, r) for u, r in manifest.items()
                if (kind is None or r.get("kind") == kind)
                and not (self.settled(u) and not self.recheck)]
        rows.sort(key=lambda x: (x[1].get("kind") or "", x[0]))
        return rows

    def record(self, url, verdict, detail, row=None):
        row = row or {}
        self.results[url] = {
            "kind": row.get("kind"),
            "expect": row.get("expect"),
            "verdict": verdict,
            "detail": detail,
            "checked_at": now(),
            "sources": (row.get("sources") or [])[:3],
        }

    def flush(self):
        self.path.write_text(json.dumps(self.results, indent=1))

    # ---- the loop --------------------------------------------------

    def run_all(self, manifest, checker, kind=None):
        """Check every unsettled row with `checker(url, row, fetch=...)`.

        The checker returns (verdict, detail) and may raise; HTTP errors
        become `unreachable` and anything else `error`, both of which a
        later rerun retries. 429/503 additionally trigger backoff, since
        those are the server asking for room.
        """
        todo = self.todo(manifest, kind=kind)
        self.log(f"record audit — {len(todo):,} to check "
                 f"({len(manifest):,} in manifest, {len(self.results):,} done)")
        started = time.time()
        for i, (url, row) in enumerate(todo, 1):
            try:
                verdict, detail = checker(url, row, fetch=self.fetch)
                self.throttle.ok()
            except urllib.error.HTTPError as e:
                verdict, detail = "unreachable", f"HTTP {e.code}"
                if e.code in (429, 503) or e.code >= 500:
                    self.throttle.bad()
            except Exception as e:                     # noqa: BLE001
                verdict, detail = "error", str(e)[:160]
            self.record(url, verdict, detail, row)
            if verdict != "ok":
                self.log(f"  [{verdict}] {url}\n      {detail}")
            if i % self.flush_every == 0 or i == len(todo):
                self.flush()
                rate = i / max(time.time() - started, 1e-6)
                self.log(f"  … {i}/{len(todo)} ({rate * 3600:.0f}/h)")
        return self.finish()

    def finish(self):
        """Flush and report the verdict tally.

        Printing the tally every time matters: it is the number that goes
        in the write-up, and seeing it on stdout makes a run that quietly
        checked nothing obvious instead of reassuring.
        """
        self.flush()
        counts = Counter(v["verdict"] for v in self.results.values())
        self.log(f"verdicts: {dict(counts)}")
        return counts

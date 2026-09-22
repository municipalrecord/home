#!/usr/bin/env python3
"""The onboarding ledger: what previous towns cost, so the next one is cheaper.

Append-only JSONL is the source of truth; the Markdown views are rendered
from it and are safe to regenerate. See references/ledger.md for the why.

    ledger.py init  [--path DIR]
    ledger.py open  --town T [--vendor V]     # Stage 0 survey, not a ledger entry
    ledger.py add   --town T --vendor V --stage S --cost C
                    --symptom ... --cause ... --fix ... --check ...
                    [--supersedes ID] [--date YYYY-MM-DD]
    ledger.py read  [--vendor V] [--stage S] [--cost C ...] [--all]
    ledger.py promote --id ID --to "where the check now lives"
    ledger.py status  --id ID --set {live,dormant}
    ledger.py render

`add` requires every substantive field, on purpose: the required fields are
the discipline. An entry you cannot fill in honestly is an entry not worth
writing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date as _date
from pathlib import Path

STAGES = ["survey", "acquire", "model", "build", "gate", "publish", "retro"]
COSTS = ["rework", "wrong-page", "stand-down", "takedown", "near-miss"]
# Ordered worst-first so the rendered playbook leads with what hurt most.
COST_RANK = {c: i for i, c in enumerate(
    ["takedown", "stand-down", "wrong-page", "rework", "near-miss"])}


def _as_ledger_file(p) -> Path:
    """Read a user-supplied path as a ledger file or the directory holding one.

    It is named as a file only when it says so (`.jsonl`) or already is one.
    Anything else is the ledger directory — which usually does not exist yet,
    since `init` is the call that creates it, so an is_dir() test would
    misread it as a filename and write the JSONL where the folder belongs.
    """
    p = Path(p)
    return p if (p.suffix == ".jsonl" or p.is_file()) else p / "ledger.jsonl"


def find_ledger(explicit=None) -> Path:
    """onboarding/ledger.jsonl: explicit path, $RECORD_LEDGER, or upward search."""
    if explicit:
        return _as_ledger_file(explicit)
    env = os.environ.get("RECORD_LEDGER")
    if env:
        return _as_ledger_file(env)
    here = Path.cwd().resolve()
    for d in [here, *here.parents]:
        cand = d / "onboarding" / "ledger.jsonl"
        if cand.exists():
            return cand
    return here / "onboarding" / "ledger.jsonl"


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def entry_id(e: dict) -> str:
    seed = f"{e['date']}|{e['town']}|{e['stage']}|{e['symptom']}"
    return hashlib.sha256(seed.encode()).hexdigest()[:8]


def resolve(entries, prefix):
    """Accept any unambiguous id prefix, the way git does."""
    hits = [e for e in entries if e["id"].startswith(prefix)]
    if not hits:
        sys.exit(f"no entry with id starting {prefix!r}")
    if len(hits) > 1:
        sys.exit(f"ambiguous id {prefix!r}: {[h['id'] for h in hits]}")
    return hits[0]


def rewrite(path: Path, entries):
    path.write_text("".join(json.dumps(e, sort_keys=True) + "\n"
                            for e in entries), encoding="utf-8")


# ---- rendering -----------------------------------------------------

def fmt(e: dict, brief=False) -> str:
    head = (f"### `{e['id']}` · {e['town']} · {e['vendor']} · "
            f"{e['stage']} · **{e['cost']}** · {e['date']}")
    if e.get("promoted_to"):
        return (f"{head}\n\n"
                f"*Promoted into a check — lives at: {e['promoted_to']}*  \n"
                f"<sub>{e['symptom']}</sub>\n")
    if brief:
        return f"{head}\n\n{e['symptom']}\n"
    body = [head, "",
            f"**Symptom** — {e['symptom']}", "",
            f"**Cause** — {e['cause']}", "",
            f"**Fix** — {e['fix']}", "",
            f"**The check that catches it** — {e['check']}"]
    if e.get("supersedes"):
        body += ["", f"*Supersedes `{e['supersedes']}` (that entry was wrong, "
                     f"not merely different).*"]
    return "\n".join(body) + "\n"


def live(entries):
    return [e for e in entries if e.get("status", "live") == "live"]


def sort_key(e):
    return (COST_RANK.get(e["cost"], 99), e["date"])


def render(path: Path):
    entries = load(path)
    root = path.parent
    (root / "vendors").mkdir(parents=True, exist_ok=True)
    shown = sorted(live(entries), key=sort_key)

    lines = ["# Onboarding ledger", "",
             "What previous towns cost. Rendered from `ledger.jsonl` — do not "
             "edit this file by hand, it is regenerated.", "",
             f"{len(shown)} live entries "
             f"({len(entries) - len(shown)} dormant, kept in the JSONL), "
             f"{sum(1 for e in shown if e.get('promoted_to'))} promoted into "
             f"checks.", ""]
    for stage in STAGES:
        rows = [e for e in shown if e["stage"] == stage]
        if rows:
            lines += [f"## Stage: {stage}", ""] + [fmt(e) for e in rows]
    (root / "LEDGER.md").write_text("\n".join(lines), encoding="utf-8")

    for vendor in sorted({e["vendor"] for e in shown}):
        rows = [e for e in shown if e["vendor"] == vendor]
        out = [f"# Vendor playbook: {vendor}", "",
               "Entries are kept even when they contradict each other — a "
               "vendor behaving differently per install is the most useful "
               "thing to know about it. Rendered; do not edit by hand.", ""]
        for e in rows:
            out.append(fmt(e))
        (root / "vendors" / f"{vendor}.md").write_text("\n".join(out),
                                                       encoding="utf-8")
    return len(shown), len(entries)


# ---- commands ------------------------------------------------------

def cmd_init(a):
    path = find_ledger(a.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"ledger already exists at {path}")
    else:
        path.write_text("", encoding="utf-8")
        print(f"created {path}")
    render(path)
    print(f"rendered {path.parent / 'LEDGER.md'}")


SURVEY_TEMPLATE = """# {town} — Stage 0 survey

Vendor(s): {vendor}
Opened: {date}

Written before any crawling. The ledger is for lessons that cost something;
this is the plan, so it lives here instead.

## Bodies in scope
<!-- Every body you are promising to cover, and the ones you are not. A
     council is never the whole government. -->

## Vendors, plural
<!-- The current portal, AND what the town used five years ago. Migrations
     leave the old portal up holding the older era. -->

## Identifier eras
<!-- Every tracking-code / id format in the archive, with an example of
     each. One parser must handle them all. -->

## Portal failure modes, observed
<!-- Request a deleted id, a malformed id, and an id from a neighbouring
     type. Record what came back — bodies, not just status codes. This is
     cheap now and impossible to retrofit. -->

## What we will not publish
<!-- Policy decisions with privacy weight, made now rather than in a
     scramble before launch. -->

## Open questions
"""


def cmd_open(a):
    """Scaffold a town's Stage 0 survey — deliberately NOT a ledger entry."""
    path = find_ledger(a.path)
    town_dir = path.parent / "towns" / a.town
    town_dir.mkdir(parents=True, exist_ok=True)
    f = town_dir / "survey.md"
    if f.exists():
        print(f"survey already exists at {f}")
        return
    f.write_text(SURVEY_TEMPLATE.format(
        town=a.town, vendor=a.vendor or "unknown — find out before crawling",
        date=a.date or _date.today().isoformat()), encoding="utf-8")
    print(f"created {f}")
    print("Fill it in before writing any code. Nothing goes in the ledger "
          "until something has cost something.")


def cmd_add(a):
    path = find_ledger(a.path)
    if not path.exists():
        sys.exit(f"no ledger at {path} — run `ledger.py init` first, or set "
                 f"$RECORD_LEDGER")
    entries = load(path)
    e = {"date": a.date or _date.today().isoformat(),
         "town": a.town, "vendor": a.vendor, "stage": a.stage, "cost": a.cost,
         "symptom": a.symptom, "cause": a.cause, "fix": a.fix,
         "check": a.check, "promoted_to": None,
         "supersedes": None, "status": "live"}
    e["id"] = entry_id(e)
    if any(x["id"] == e["id"] for x in entries):
        sys.exit(f"entry {e['id']} already recorded (same town, stage, date, "
                 f"symptom)")
    if a.supersedes:
        old = resolve(entries, a.supersedes)
        e["supersedes"] = old["id"]
        old["status"] = "dormant"
        rewrite(path, entries)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(e, sort_keys=True) + "\n")
    render(path)
    print(f"recorded {e['id']} ({e['town']}/{e['stage']}/{e['cost']})")
    if a.supersedes:
        print(f"  superseded {e['supersedes']} (marked dormant)")


def cmd_promote(a):
    path = find_ledger(a.path)
    entries = load(path)
    e = resolve(entries, a.id)
    e["promoted_to"] = a.to
    rewrite(path, entries)
    render(path)
    print(f"{e['id']} promoted -> {a.to}")


def cmd_status(a):
    path = find_ledger(a.path)
    entries = load(path)
    e = resolve(entries, a.id)
    e["status"] = a.set
    rewrite(path, entries)
    render(path)
    print(f"{e['id']} status -> {a.set}")


def cmd_read(a):
    path = find_ledger(a.path)
    entries = load(path) if a.all else live(load(path))
    if not entries:
        print(f"# Onboarding ledger\n\nNo entries yet ({path}). The first "
              f"town's survey is the first entry.")
        return
    sel = [e for e in entries
           if (not a.vendor or e["vendor"] in a.vendor)
           and (not a.stage or e["stage"] in a.stage)
           and (not a.cost or e["cost"] in a.cost)]
    filt = " · ".join(filter(None, [
        f"vendor={','.join(a.vendor)}" if a.vendor else "",
        f"stage={','.join(a.stage)}" if a.stage else "",
        f"cost={','.join(a.cost)}" if a.cost else ""])) or "everything"
    print(f"# Onboarding playbook — {filt}\n")
    print(f"{len(sel)} of {len(entries)} entries.\n")
    if not sel and a.vendor:
        print(f"Nothing recorded for this vendor yet. Probe its failure modes "
              f"at Stage 0 and write the first entry — you are the town that "
              f"pays for it.\n")
    for e in sorted(sel, key=sort_key):
        print(fmt(e, brief=a.brief))


def cmd_render(a):
    path = find_ledger(a.path)
    shown, total = render(path)
    print(f"rendered {shown} live of {total} entries -> {path.parent}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    # --path hangs off every subcommand rather than the top level, so that
    # both `ledger.py add --path X ...` and muscle memory from git-style
    # tools work. A top-level copy would be clobbered by the subparser's
    # own default on every call.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--path", help="ledger dir or ledger.jsonl "
                                       "(default: search upward, then "
                                       "$RECORD_LEDGER)")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", parents=[common]).set_defaults(func=cmd_init)

    o = sub.add_parser("open", parents=[common],
                       help="scaffold a town's Stage 0 survey (not a ledger entry)")
    o.add_argument("--town", required=True)
    o.add_argument("--vendor")
    o.add_argument("--date")
    o.set_defaults(func=cmd_open)

    a = sub.add_parser("add", parents=[common],
                       help="record a lesson that cost something")
    a.add_argument("--town", required=True)
    a.add_argument("--vendor", required=True)
    a.add_argument("--stage", required=True, choices=STAGES)
    a.add_argument("--cost", required=True, choices=COSTS,
                   help="what the lesson actually cost; no cost, no entry")
    a.add_argument("--symptom", required=True, help="what you observed")
    a.add_argument("--cause", required=True, help="root cause, not proximate")
    a.add_argument("--fix", required=True)
    a.add_argument("--check", required=True,
                   help="what would have caught it; say so if nothing "
                        "mechanical would")
    a.add_argument("--supersedes", help="id of an entry this proves WRONG "
                                        "(not merely different)")
    a.add_argument("--date")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("read", parents=[common], help="print the accumulated playbook")
    r.add_argument("--vendor", nargs="*")
    r.add_argument("--stage", nargs="*", choices=STAGES)
    r.add_argument("--cost", nargs="*", choices=COSTS)
    r.add_argument("--brief", action="store_true")
    r.add_argument("--all", action="store_true", help="include dormant")
    r.set_defaults(func=cmd_read)

    pr = sub.add_parser("promote", parents=[common], help="a lesson became a check that runs")
    pr.add_argument("--id", required=True)
    pr.add_argument("--to", required=True)
    pr.set_defaults(func=cmd_promote)

    st = sub.add_parser("status", parents=[common])
    st.add_argument("--id", required=True)
    st.add_argument("--set", required=True, choices=["live", "dormant"])
    st.set_defaults(func=cmd_status)

    sub.add_parser("render", parents=[common]).set_defaults(func=cmd_render)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

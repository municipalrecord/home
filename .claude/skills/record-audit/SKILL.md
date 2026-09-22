---
name: record-audit
description: Verify republished public-record data against the source-of-truth portal it was assembled from, and write the result up for publication. Use this whenever checking that mirrored civic data still matches the city's own pages, confirming a link lands on what it claims rather than merely resolving, re-drawing or extending a seeded accuracy sample, chasing a suspected wrong document or bad link, or drafting an accuracy/audit/corrections page. Use it even when the ask sounds like a quick one-off — "does this link still work?", "is this the right PDF?", "spot-check a few of these items", "why does our title differ from theirs?" — because what counts as a real check is the entire point, and an HTTP 200 is not a check.
---

# Auditing a republished record

## Why this exists

A site that republishes a city's record is assembled by software, much of it
AI-written, from portals that were never designed to be scraped. Software
makes mistakes. The only honest basis for asking anyone to trust the result
is to measure your own error rate in public, with a method a stranger can
re-run against you.

That reframes the job. **An audit is not a quality gate you are trying to
pass — it is an instrument you are trying to keep honest.** A run that
surfaces an ugly number did its job. A run that was quietly narrowed until
the number looked good has destroyed the only thing the number was for. Every
decision below follows from that.

## 1. Draw the sample with a published seed

Fix the seed, write it into the artifact next to `n` and the audit date, and
publish the code. The point is that a reader can re-draw the identical sample
and check the checker — a percentage nobody can reproduce is a press release.

```python
from polite_audit import seeded_sample
sample = seeded_sample(rows, args.n, args.seed)   # seed goes in the write-up
```

Use that helper rather than `random.sample`. `sample` changes strategy with
`k`, so `sample(rows, 100)` does **not** begin with `sample(rows, 50)` on the
same seed; a seeded shuffle sliced to `n` does. That property is what lets an
audit grow: raising `n` keeps every earlier row and its result, and only the
new tail needs fetching. It also requires `rows` to arrive in a stable order —
sort them in the query, or the seed reproduces nothing.

Two rules keep a seed meaningful:

- **Never re-roll a seed because you dislike the result.** If a run surfaces a
  bad rate, the finding is the rate. Re-drawing until it improves is fabricating
  evidence, and the published seed exists precisely so that it is detectable.
- **Extend, don't replace.** To audit more, raise `n` on the same seed, or draw
  a fresh sample under a new published seed and report both. Silently swapping
  seeds between runs makes the series incomparable.

Sub-sampling an expensive check (fetching every attachment, say) is fine — draw
it from the already-drawn sample with the same seeded generator, and report its
denominator separately. Cheap checks get full coverage; only spend a network
round-trip on a sample where you must.

Where an audit can be done offline over the built output, it should be: offline
checks are free, so they get **total** coverage rather than a sample. Reserve
sampling for what genuinely requires hitting the city's servers.

## 2. Check identity, never availability

This is the heart of it. The worst bugs this discipline has caught were links
that **resolved perfectly and went to the wrong place**: a portal where the
document-type parameter collided so an id served somebody else's file, and a
portal that returns HTTP 200 on a page that says "we've run into an error."
A status code tells you a server answered. It does not tell you it answered
with the thing you linked it *for*.

So every check asks the same question: **does this target display the identity
we claimed for it?** Answering it needs a manifest — written when the pages are
built — recording, for each outgoing URL, what that URL is supposed to contain.

The claim varies by target, but the shape never does:

| Target | The identity it must display |
|---|---|
| An item/legislation page | the item's tracking code (or, if the page omits it, the item's title) |
| A meeting page | the body's name **and** the meeting date |
| A mirrored PDF | bytes whose sha256 equals the hash archived at fetch time |
| A page whose shell is unreliable | identity from the vendor's own search API, not the page |

That last row matters more than it looks. When a vendor's page is flaky in ways
a real browser doesn't reproduce, do not let the flake become the verdict — get
identity from the API the vendor's own UI calls (for example, a quoted-title
search that must return the id you linked), and demote the page fetch to
advisory detail. Report what the shell did; just don't convict on it.

For mirrored documents, compare hashes rather than existence. **A wrong id and a
silent city-side alteration are the same finding** — the bytes are not the bytes
you read, archived, and built a page from — and only a hash catches both.
This requires archiving the hash at fetch time; if there is no baseline, say
`no-baseline` and record the live hash so the *next* run has one. Never let a
missing baseline read as a pass.

Offline, the same question applies to your own pages. Three layers give total
coverage without touching the network:

- **identity** — every generated page declares, in its title, the same code its
  slug encodes.
- **anchor claims** — every link whose visible text claims a code ("AR 2025-33",
  "Policy Order 2025 #165") points at that code's page. This catches the
  plausible-looking wrong link, which no link checker will ever flag.
- **database cross-check** — every outbound portal link and internal document
  link on a page belongs to *that* record according to the database.

## 3. Let the verdict vocabulary carry the nuance

Collapsing results into pass/fail destroys the information an auditor needs,
and pushes you toward calling benign formatting differences "failures" — which
trains everyone to ignore failures. Grade the comparison instead:

- `exact` — byte-identical after normalizing entities and whitespace.
- `case` — differs only in case.
- `prefix` — one side is a truncation of the other. Record which side and by
  how much; truncation is usually **our** bug.
- `MISMATCH` — genuinely different content. Record the divergence point and a
  window of both strings (`diverge@0: ours…'…' theirs…'…'`), because the first
  differing character usually names the bug.
- `unparsed` / `n/a` — the comparison could not be made. Never a pass.

For fetched bytes the same principle applies, with one rule that keeps it
honest: **only classes you have positively identified get their own verdict;
everything unrecognized stays `mismatch`.** So legacy Word (OLE2) bytes served
at a `.pdf` URL is `city-serves-non-pdf` — vendor behavior, not drift — and a
file whose leading bytes are zeroed on the city's server while the trailer
survives is `city-file-corrupt`. An unrecognized substitution is exactly what
you must not absorb, so it stays loud.

Order matters: **classify the non-PDF cases before comparing hashes**, so no
sha256 finding can ever be reclassified into something quieter. When you add a
new class later, re-verdict only the rows that were unrecognized — never the
hash findings.

Keep `unreachable` (HTTP error) and `error` (exception) distinct from
`mismatch`. They mean "we don't know," and they are the rows a rerun should
retry.

## 4. Crawl politely, and make reruns cheap

You are a guest on a city's server, auditing under your own name. Be the kind
of traffic that never needs to be blocked:

- Single-threaded, with a floor of ~1.0–1.2s between requests. A 1,000-item run
  takes ~20 minutes; that is fine, and it is the cost of not being a problem.
- Identify yourself honestly in the User-Agent, with a contact address.
- Back off exponentially on 429/5xx (15s doubling to a ~10-minute cap), and say
  so on stdout so a watching human knows why it went quiet.
- Cap how much you read from any one response, so a surprise multi-GB body
  can't take the run down.
- Persist state keyed by URL or id, and flush every ~25 rows. A rerun should
  skip settled rows and retry only `error`, `unreachable`, and `no-baseline`.
  A `--recheck` flag re-does everything; make re-doing everything opt-in.

`scripts/polite_audit.py` implements exactly this — throttle, backoff, capped
reads, resumable JSON state, summary counts. Import it rather than rewriting
the loop, and spend your attention on the identity checks instead:

```python
from polite_audit import AuditRun

run = AuditRun("results.json", contact="contact@example.org", delay=1.2)
for url, row in run.todo(manifest):        # skips rows already settled
    run.record(url, *check(url, row, fetch=run.fetch))
run.finish()                                # flushes, prints verdict counts
```

Read the module's docstring for the full surface. Note that it is transport and
bookkeeping only — it deliberately has no opinion about what a target should
contain, because that is the part you must think about.

## 5. Decide whose bug it is, and never edit to pass

A divergence is not automatically your error, and this is where an audit earns
or loses its credibility.

- A status or title that changed because **the clerk acted after your crawl** is
  legitimate drift. Record both values, date them, and let a human adjudicate.
- A difference that is purely the city's display convention — their trailing
  period, their spacing inside a tracking code (`ORD 2023 # 9`) — is not a
  content mismatch. Verify a sample by inspection, then report it as its own
  category with its count. Do not fold it into the headline error rate, and do
  not hide it either.
- Where **the city's own minutes disagree with its portal, the minutes win.**
- Where the record is wrong about the world, it stands as the city wrote it.

The corresponding prohibition is absolute, because everything rests on it:
**never adjust the data to make an audit pass.** Spelling of a word may be
corrected, and every such correction is listed publicly. A name, a date, a
tally, or an outcome is a matter of record, never of presentation — quietly
"fixing" one puts your word above the city's, which is the opposite of the
project. If an audit is failing because the underlying data is wrong, the fix
belongs in the pipeline and the failure belongs in the write-up until it lands.

## 6. Write it up so a skeptic can attack it

The audit artifact is a public document whose job is to invite scrutiny. Give
it, in this order:

1. **Provenance** — audit date, `n`, the seed, a link to the raw results
   (CSV/JSON), and a link to the audit code. Before any number.
2. **Headline rates, each with its denominator** — `1,908/1,927 tracking codes
   byte-exact`. A bare percentage is unfalsifiable; a fraction can be checked.
3. **What was compared, field by field**, naming the normalization applied and
   the benign categories separately from real mismatches.
4. **Every deviation found** — itemized, including the ones that turned out to
   be the city's doing or benign, each with its explanation. This list is the
   proof the instrument works. A short deviation list with no explanations
   reads as concealment; a long one with honest explanations reads as rigor.
5. **Plain language.** The reader is a resident, not an engineer: "the city's
   page shows the clerk's next-day action date after a past-midnight
   adjournment" beats "date_found=no".

Say what you did not check as plainly as what you did. Unchecked scope
presented as coverage is the one failure mode that discredits everything else
in the document.

## Anti-patterns

- Treating HTTP 200 as verification. It is the *start* of a check.
- Re-drawing a sample, narrowing scope, or dropping a check after seeing results.
- A headline percentage with no denominator, seed, raw data, or code link.
- Letting `no-baseline`, `unparsed`, or `error` rows count as passes.
- Collapsing city-side conditions and real drift into one bucket — in either
  direction. Unrecognized substitutions must stay loud.
- Parallel or unthrottled crawling of a municipal server.
- Editing a name, date, tally, or outcome so an audit goes green.
- Reporting "verified" for a page that merely loaded.

## References

- `references/portals.md` — vendor-specific behavior: IQM2/Granicus, PrimeGov,
  Legistar. Read when auditing a city on one of these, or onboarding a new one.
- `references/writeup.md` — the accuracy-page template with a worked example.
  Read when producing the published artifact.
- `scripts/polite_audit.py` — the throttled, resumable fetch/state harness.

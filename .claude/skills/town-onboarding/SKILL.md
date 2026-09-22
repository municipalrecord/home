---
name: town-onboarding
description: Stand up a new municipal- or legislative-record site from a government portal, end to end, and feed what you learn back into the playbook for the next town. Use this when adding a new city, town, or chamber to a record project; surveying an unfamiliar agenda portal (IQM2/Granicus, PrimeGov, Legistar, CivicClerk, or a bespoke one); deciding whether a new site is ready to publish; or writing up what an onboarding taught you. Use it at the very start — the first thing it does is read the accumulated ledger of what previous towns cost, and the expensive mistakes are all made in the first hour. Also use it when a site is already built and the question is whether to launch, because the decision to stand down is part of this workflow, not a failure of it.
---

# Onboarding a new town

## The rule everything else serves

> "A record of a city's government is only worth reading if every line in it
> can be traced to a document you can go and check. We had not finished
> checking this one, and publishing it before we had was the wrong order to
> do things in. So it comes down until the checking is done."
>
> — The Somerville Record, on its own takedown

That page is the most useful artifact this project has produced, because it
is the one that says what the standard actually costs. A record site's entire
value is that a reader can stop trusting you and check instead. Ship one page
that can't be traced and you have spent the only asset you have.

So: **the deliverable of an onboarding is not a site. It is a site whose
every line is traceable, or an honest placeholder.** Both are successes. A
published site with unchecked pages is the only failure, and it is the
failure that is easiest to reach by working hard.

## Before anything: read the ledger

Previous towns have already paid for lessons you are about to re-buy. The
first action of any onboarding, before surveying a portal or writing a line
of code:

```bash
python scripts/ledger.py read --vendor <vendor-if-known>
```

That prints the accumulated playbook — what broke on other towns, at which
stage, and the check that now catches it. If the ledger doesn't exist yet in
this repo, `scripts/ledger.py init` creates it; see `references/ledger.md`
for the layout and where it lives.

Read it even when the vendor is new. Most of what goes wrong is not
vendor-specific — it is ordering, scope, and the temptation to publish.

## Stage 0 — Survey, and write down what the town *is*

Resist starting the crawler. An hour here saves the rewrite.

Establish, in writing, before anything else:

- **Which bodies exist**, and which are in scope. A city council is never the
  whole government; Cambridge alone carries 82 boards and commissions plus a
  school committee. Decide what you are promising and say it on the site.
- **Which vendor(s), plural.** Towns migrate, and the old portal usually stays
  up holding the older era. Cambridge runs IQM2 for the archive and PrimeGov
  for the current era, and every identity check had to learn both. Ask "what
  was this town using five years ago?" before assuming one system.
- **Where the era boundaries fall**, and whether identifiers are stable across
  them. Cambridge has two tracking-code eras (`POR 2019 #275` and `AR-19-82`)
  that any parser must handle together.
- **What the portal's own failure modes are.** Deliberately request a deleted
  id, a malformed id, and an id from a neighbouring type; record what comes
  back. This is cheap now and impossible to retrofit — it is how the
  200-on-an-error-page and id-collision classes were found.
- **What you will not do.** Resident communications published in full text,
  for instance, is a policy decision with privacy weight, and it belongs in
  the survey, not in a late scramble before launch.

Write it to `onboarding/towns/<town>/survey.md`, which
`scripts/ledger.py open --town <town>` scaffolds for you. It does not go in
the ledger: the ledger records lessons that cost something, and a survey has
not cost anything yet. Keeping the two apart is what stops the ledger filling
with plans nobody paid for. The survey file is also the honest basis for
estimating the work, and the thing a later retrospective is written against.

## Stage 1 — Acquire, provenance first

The ordering rule: **archive before you derive.** Every fetched artifact gets
stored as served, with its sha256 taken at fetch time and recorded alongside
its source URL and the moment of fetching. Everything downstream is a
derivation you can rebuild; the archive is the thing you cannot.

Retrofitting hashes is not possible in the sense that matters — it gives you
a baseline that already incorporates whatever changed before you started, so
silent alteration in that window is undetectable forever.

Crawl politely: single-threaded, ~1.0–1.2s floor between requests, honest
User-Agent with a contact address, exponential backoff on 429/5xx, resumable
state. You are a guest, under your own name, for years. The `record-audit`
skill's `scripts/polite_audit.py` is the same harness and should be reused
here rather than rewritten.

## Stage 2 — Model, with citable identity

The schema that has survived contact with two vendors and three eras:
items (the unit of business), meetings, documents, votes/roll calls, and
people with their terms. Its details are in `references/data-model.md`;
read that before designing tables.

Two properties matter more than the shape:

- **Stable, meaningful slugs**, derived from the record's own identifier
  (`POR 2019 #275` → `por-2019-275`), so a URL is a citation and stays one.
  URLs you will later have to change are a debt you pay in other people's
  broken links.
- **Every derived row knows its source** — which document, which portal id,
  which fetch. A page that cannot name where a fact came from cannot be
  published under the rule above, and finding that out at Stage 4 is
  expensive.

## Stage 3 — Build pages that invite checking

Every page carries the city's own link for what it asserts, and document
pages carry per-page anchors (`#p3`) so a reader can cite a precise passage.
The original PDF is linked from every document page and is authoritative —
your rendering is a convenience, never the record.

Publish the bulk data too, as CSV and JSON side by side with a data
dictionary (the Beacon Hill site does this under `/data` and `/explore`).
It costs little and it converts a critic into a collaborator.

## Stage 4 — The gates

A gate is not a review. It is a check that runs, and the site does not
proceed while it is red.

**Gate 1 — integrity and identity.** Offline and total coverage, not a
sample: every internal link resolves; every page's declared identity matches
its slug; every anchor claiming a code ("AR 2025-33") lands on that code's
page; every outbound portal link matches what the database says that record
is. Then the online half on a seeded sample. Use the `record-audit` skill for
this — it is the same discipline and it is where these two skills meet.

**Gate 2 — derived numbers.** Any statistic the site computes needs a
denominator, a frame, a floor, and a stated limit. `references/derived-numbers.md`
has the method. The short version: a rate with no denominator is not a fact,
a number with no comparison is not informative, a rate over five events is
"a coincidence with a percent sign on it," and every measure needs its own
plain-language paragraph on what it cannot tell you.

**Gate 3 — policy.** Before launch, the site must state what it is and is
not: unofficial, not affiliated, assembled from named primary sources. The
corrections policy must be live and public — spelling of a word may be
corrected and every such correction is listed; a name, a date, a tally, or an
outcome never is. Where the city's minutes disagree with its portal, the
minutes win. And the accuracy page must be published with the real miss rate
before launch, not after.

## Stage 5 — Publish, or stand down

Decide explicitly, and record the decision. The question is not "is it
good?" but **"can every line on it be traced today?"**

If not, stand down — and do it the way Somerville did: a real page, at the
real domain, that says plainly it is not ready, why, and what is happening
instead. Not a 404, not a coming-soon animation, not a quiet unpublish. A
stand-down page that tells the truth *builds* the credibility the project
runs on; it is the cheapest possible demonstration that the standard is real.

Then set the condition for revisiting — which gate is red and what closes it
— and put that in the ledger. A stand-down with no stated re-entry condition
becomes an abandonment.

## Stage 6 — The retrospective, which is the point

This is what makes the next town cheaper, and it is the stage that gets
skipped, because by now the work feels done. It isn't: an onboarding that
taught you nothing you wrote down has to be re-learned at full price.

Run it while the work is fresh, in one sitting:

```bash
python scripts/ledger.py add --town somerville --vendor legistar \
  --stage acquire --cost stand-down \
  --symptom "..." --cause "..." --fix "..." --check "..."
```

Four rules keep the ledger worth reading — a ledger nobody reads is worse
than none, because it looks like the lesson was captured:

1. **Only write back what cost something.** A lesson earns its place if it
   caused rework, a wrong page, a stand-down, or a near miss. The `--cost`
   field is required precisely so that entries without a cost don't get
   written. General programming wisdom belongs somewhere else.

2. **Prefer promoting a lesson into a check.** The best outcome of a lesson
   is a new gate, a new assertion, or a line in the vendor playbook that a
   script enforces — not a paragraph. Prose degrades into folklore; a check
   that runs cannot be forgotten. When you promote one, mark the entry
   `--promoted-to <where>` so the ledger shrinks as it matures.

3. **Contradictions get dated, not overwritten.** When a new town's portal
   behaves the opposite way from what the playbook says, both are true —
   vendors differ per install and change over time. Record the new
   observation with its town and date, and let the vendor file carry both.
   Overwriting loses the information that the vendor is inconsistent, which
   is itself the most useful thing to know about it.

4. **Prune on the way in.** When you add an entry that supersedes an older
   one, say so (`--supersedes`), so the rendered playbook collapses it to a
   pointer. Ledgers die of length.

Finally, look at the entries in aggregate rather than one at a time. If three
towns all lost time at the same stage, the fix is not a fourth ledger entry —
it is a change to this skill's workflow or a new bundled script. That
judgment is the recursion; the file is only its memory.

## Anti-patterns

- Starting the crawler before writing down what the town is.
- Assuming one vendor because one portal is visible.
- Deriving before archiving, or planning to add hashes later.
- Treating a sample as coverage for a check that could run offline over
  everything.
- Publishing pages whose provenance you intend to fill in after launch.
- A statistic without a denominator, a frame, a floor, and a stated limit.
- Standing down with a 404 or silence instead of a page that says why.
- Finishing an onboarding without a retrospective, or writing a retrospective
  entry that cost nothing.

## References

- `references/ledger.md` — where the ledger lives, its entry format, and how
  the rendered playbook is produced. Read before the first `ledger.py` call.
- `references/data-model.md` — the schema, slug rules, and page/bulk-data
  conventions that survived Cambridge and Beacon Hill. Read at Stage 2.
- `references/derived-numbers.md` — denominator, frame, floor, stated limit;
  the method behind Gate 2. Read before computing any published statistic.
- `scripts/ledger.py` — init / read / add / render for the ledger.
- The `record-audit` skill — the verification discipline Gate 1 runs on.

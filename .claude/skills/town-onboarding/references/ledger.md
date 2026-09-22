# The onboarding ledger

The ledger is how one town's expensive hour becomes the next town's read.
It is deliberately boring: an append-only file of structured entries, plus
rendered Markdown that humans actually read.

## Where it lives

The ledger belongs in the **project's shared repo, not inside this skill**.
The skill may be installed read-only, and more importantly the lessons
outlive any one copy of it. The default location:

```
<shared-repo>/onboarding/
├── ledger.jsonl          # append-only source of truth, one JSON object per line
├── LEDGER.md             # rendered: everything, worst cost first
├── vendors/
│   ├── iqm2.md           # rendered: this vendor's accumulated entries
│   ├── primegov.md
│   └── legistar.md
└── towns/
    └── <town>/survey.md  # Stage 0 survey, scaffolded by `ledger.py open`
```

**A survey is not a ledger entry.** `ledger.py open --town <town>` scaffolds
`towns/<town>/survey.md` and writes nothing to the JSONL, because the ledger
records what things cost and a plan has not cost anything yet. Mixing the two
is how a ledger fills with intentions and stops being read. The survey is what
a later retrospective gets written against.

`scripts/ledger.py` finds it by walking up from the working directory
looking for an `onboarding/ledger.jsonl`, then falling back to
`$RECORD_LEDGER` if set. `ledger.py init --path <dir>` creates it. Say in
the repo's README where it is, because a ledger nobody can find is a ledger
nobody reads.

**Why JSONL as the source of truth**: entries are appended by different
people, in different repos, sometimes in the same week. Append-only lines
merge cleanly; hand-edited prose does not. The Markdown is always rendered
from the JSONL and is safe to regenerate — never edit it directly, because
the next render will silently discard your edit.

## The entry

```json
{
  "date": "2026-08-14",
  "town": "somerville",
  "vendor": "legistar",
  "stage": "acquire",
  "cost": "stand-down",
  "symptom": "Pages were built and deployed before document provenance was complete.",
  "cause": "Build ran ahead of the archive; no gate blocked publish on untraceable rows.",
  "fix": "Took the site down to a placeholder that states why; publish now blocked on Gate 1.",
  "check": "Publish step refuses when any built page has a row with no source document id.",
  "promoted_to": null,
  "supersedes": null
}
```

Every field except `promoted_to` and `supersedes` is required, and the
script refuses an entry missing one. That is the point: the required fields
*are* the discipline.

- **stage** — one of `survey`, `acquire`, `model`, `build`, `gate`,
  `publish`, `retro`. Which stage the lesson belongs to is how the next
  onboarding finds it at the moment it matters, rather than reading the
  whole ledger up front.
- **cost** — one of `rework`, `wrong-page`, `stand-down`, `takedown`,
  `near-miss`. A lesson with no cost is an opinion; the field exists to make
  you name the damage before the entry is worth writing. If you can't fill
  it in honestly, don't write the entry.
- **symptom** — what you actually observed, in the terms you observed it.
  Written for someone who will be *inside* the symptom and searching for it,
  not someone browsing.
- **cause** — the root cause, not the proximate one. "The parser broke"
  is proximate; "we assumed one tracking-code era" is root.
- **check** — the thing that would have caught it. This is the most
  valuable field. If you can't name a check, say so explicitly ("no
  mechanical check; requires judgment at survey") — that is itself a
  finding, and it tells the next person where attention has to substitute
  for automation.

## Promotion

A ledger entry is a holding pen, not a destination. When the lesson becomes
a check that runs — a gate in the pipeline, an assertion in the audit, a
line in a vendor playbook enforced by a script — record where it went:

```bash
python scripts/ledger.py promote --id <entry-id> --to "site/build.py: refuses untraced rows"
```

The rendered playbook then collapses that entry to a one-line pointer.
Promotion is how the ledger stays short while the project gets safer: prose
degrades into folklore, but a check that runs cannot be forgotten or
misremembered.

## Contradiction

When a new town's portal behaves the opposite way from the playbook, **both
entries stay**. Vendors differ per install, change between versions, and are
configured by each city. A vendor file reading

> IQM2 `FileOpen` ids are not unique across `Type` values (cambridge,
> 2026-07). — but on <other town> the same endpoint 404s on a type
> mismatch instead of serving the wrong file (<town>, 2027-02).

is more useful than either line alone, because the real lesson is that the
vendor is inconsistent and you must probe every install. Overwriting
destroys exactly that.

Use `--supersedes <entry-id>` only when the earlier entry was *wrong*, not
when it was merely different. Different is a contradiction; wrong is a
correction.

## Reading it

```bash
python scripts/ledger.py read                     # the whole playbook
python scripts/ledger.py read --vendor legistar   # one vendor
python scripts/ledger.py read --stage survey      # what bites at this stage
python scripts/ledger.py read --cost stand-down   # the expensive ones
```

Read `--stage survey` before the survey and `--vendor X` when the vendor is
known. Read the whole thing when starting a town in a vendor you've never
seen, and read `--cost stand-down takedown` before any launch decision —
those are the entries that were paid for in public.

## Aggregate review

Once or twice a year, or whenever the ledger passes ~30 live entries, read
it in aggregate rather than by entry:

- Three towns losing time at the same stage is not three entries, it is one
  missing gate. Change the workflow, not the ledger.
- A vendor file longer than a page usually means the probing at Stage 0 is
  too shallow — the fix is a better survey script, not more notes.
- Entries that never got promoted and never got hit again are candidates for
  pruning. Delete them from the rendered view by marking them
  `--status dormant`; the JSONL keeps them forever, which is the point of
  an append-only log.

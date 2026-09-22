# onboarding/

The accumulated record of what standing up each site has cost, so the next
town is cheaper than the last.

**`ledger.jsonl`** is the source of truth — append-only, one JSON object per
line, so entries written in different weeks and different clones merge
cleanly. Everything else in this directory is rendered from it and is safe to
regenerate. Do not hand-edit `LEDGER.md` or `vendors/*.md`; the next render
discards the change.

Read it before starting a town, and write to it after:

```bash
S=.claude/skills/town-onboarding/scripts/ledger.py

python3 $S read --path onboarding                      # the whole playbook
python3 $S read --path onboarding --vendor legistar    # one vendor
python3 $S read --path onboarding --stage survey       # what bites at this stage
python3 $S read --path onboarding --cost stand-down    # the ones paid for in public

python3 $S open --path onboarding --town <town> --vendor <vendor>   # Stage 0 survey
python3 $S add  --path onboarding --town <town> --vendor <vendor> \
                --stage <stage> --cost <cost> \
                --symptom "..." --cause "..." --fix "..." --check "..."
```

Run it from the repo root, or drop `--path onboarding` and let it find this
directory by walking up from wherever you are.

## What goes in

Only lessons that cost something — the `--cost` field is required for exactly
that reason. `rework`, `wrong-page`, `stand-down`, `takedown`, `near-miss`. A
lesson you cannot price is an opinion, and a ledger of opinions stops being
read.

A survey is **not** a ledger entry. `ledger.py open` scaffolds
`towns/<town>/survey.md` and writes nothing to the JSONL, because a plan has
not cost anything yet.

When a lesson becomes a check that actually runs, say so:

```bash
python3 $S promote --path onboarding --id <id> --to "audit/external_link_audit.py check_fileopen"
```

The playbook then collapses that entry to a pointer. That is how this file
stays short while the project gets safer — prose decays into folklore, but a
check that runs cannot be misremembered.

When a new town contradicts what is written here, **both entries stay**.
Vendors differ per install and change over time, and "this vendor is
inconsistent" is the single most useful thing to know about it.

The method these entries feed is in `.claude/skills/town-onboarding/`.

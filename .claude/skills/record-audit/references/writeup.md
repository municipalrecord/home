# The published audit page

The artifact's job is to let a skeptical reader attack the claim. Everything
below serves that: provenance before numbers, fractions instead of
percentages, and every deviation itemized with an explanation.

Write for a resident who has never read a scraper. Technical field names
(`date_found=no`) mean nothing to them; the sentence "the city's page shows
the clerk's next-day action date after a past-midnight adjournment" means
everything.

## Template

```
# How accurate is this site?

Audited <YYYY-MM-DD> · sample seed <SEED> · raw results (CSV) · audit code

<One paragraph, plain language: this site is assembled by software from the
city's own portals; software makes mistakes, so we measure ours in public.
We drew N records at random with a fixed, published seed, so anyone can
re-draw the identical sample. We fetched the city's live page for each and
compared field by field.>

## Headline
<N>/<N> city pages resolved
<pct>% tracking codes correct
<pct>% titles content-identical
<k>/<k> sampled attachments resolve

## What we compared
**<Field>**: <count> byte-exact of <N>; <count> differ only by <benign
category, with an example>. <count> mismatches.
... one paragraph per field ...

## Every deviation found (<count>)
| Record | Type | Explanation |
|---|---|---|
| COF 2022 #16 | title | diverge@0: ours…'information regarding the Fare Free Bus' theirs…'A communication was received from Mayor' |
...

## What we did not check
<Plainly: scope this audit did not cover.>
```

## Rules the template encodes

**Provenance first.** Date, `n`, seed, raw data link, code link — above the
numbers, not in a footnote. A reader who cannot re-run the audit is being
asked to take your word for it, which is the thing the audit exists to avoid.

**Fractions, not bare percentages.** `1,908/1,927` can be checked against the
CSV. `99.0%` cannot. Give the percentage too if it helps, but never alone.

**Benign categories are named, counted, and separated** — not folded into the
headline and not hidden. "1,558 differ only by the city's trailing
punctuation (their display appends a period; verified by inspection)" tells
the reader exactly what was set aside and how it was confirmed, so they can
disagree with the judgment.

**Every deviation is listed, including the ones that exonerate you.** A
five-row deviation table with no explanations reads as concealment. An
eighty-six-row table where most rows end "the city's page shows a different
communication under the same id" reads as an instrument that works. Length
is not the enemy; unexplained length is.

For a divergence that may be legitimate drift (the clerk acted after the
crawl), print **both values with their dates** and say it is unadjudicated.
Do not silently pick a side.

**State the unchecked scope.** One honest sentence about what this audit does
not cover protects everything it does cover. Coverage implied but not
performed is the failure that discredits the whole document.

## Counts that look wrong

When a count in the write-up disagrees with a count elsewhere on the site,
say why in the artifact rather than reconciling them quietly — "a correction
showing none is one the city has since fixed, or one that appears somewhere
this count does not reach." Readers find these discrepancies; the ones you
explain first cost nothing, and the ones they find unexplained cost the
site's credibility.

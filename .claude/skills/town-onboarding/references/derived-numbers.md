# Publishing a number the record didn't state

The moment a site counts something, it stops republishing the record and
starts making a claim. Counts are where a record project is most useful and
most dangerous: a table of per-member vote percentages will be screenshotted
and argued about by people who never see your methodology.

The governing instinct, from the Beacon Hill record card: **the record does
not say which side of a vote was the right side, and neither does the site.**
A published statistic describes the record that exists. It is not a grade,
and the moment it reads as one you have started editorializing with
arithmetic.

Four things every published measure needs.

## 1. A denominator you state out loud

Name what the figure is divided by, and let it vary honestly. "Roll calls on
which the member's name appears at all, in any column" is a denominator; a
member seated mid-session has a smaller one, and that is correct rather than
something to normalize away.

Where a measure uses a *different* denominator from the one next to it, say
so at the point of use. Agreement measures computed only over *divided* roll
calls (those with at least one vote on each side) are a different population
from participation measures computed over all of them, and a reader who
assumes one denominator across the row will draw a false conclusion from
true numbers.

## 2. A frame, because a bare figure says nothing

97 percent agreement with the majority is unremarkable in a chamber whose
median is 98 and striking in one whose median is 60. So every figure sits
beside a comparison computed from the same population — the same session,
the same chamber:

- **the typical member** (the median), and
- **the typical member of the same party**, shown only when enough of them
  qualify to make it meaningful.

Two medians and nothing else. No range, no rank, no percentile. The card
answers *"is this usual?"* without answering *"who is best?"* — because the
record can support the first question and cannot support the second. Ranking
is the single easiest way to turn a record site into a scoreboard, and a
scoreboard is a different product with different obligations.

## 3. A floor, below which you print but don't compare

A rate over five events is a coincidence with a percent sign on it. Set an
explicit minimum for entering a comparison — Beacon Hill uses 20 roll calls
for participation measures and 10 divided votes for agreement measures — and
below it, still print the member's own figure but mark it **"too few to
compare"** and keep it out of the median.

Printing it matters: suppressing small-n figures looks like hiding, and the
underlying counts are public record anyway. Excluding them from the
comparison also matters: a handful of votes would otherwise drag the frame
everyone else is measured against.

## 4. A paragraph on what it cannot tell you

Every measure gets plain-language limits, in the same place as the number,
not in a footnote:

- **What the population excludes.** "The House records roughly 150 votes a
  year and on about 43 percent of them nobody is on the losing side" — so an
  agreement figure is computed over a few dozen votes, and the rules decide
  which votes those are. It is a fact about the member's answers on the
  record that exists, not about everything the chamber decided, most of
  which left no names.
- **What the source conflates.** If the record marks an arranged absence and
  an ordinary one identically, the column cannot distinguish them, so say
  that it doesn't rather than implying it does.
- **Where a rule shapes the data.** A presiding officer who is not called and
  appears only when choosing to vote has a small denominator for structural
  reasons, not behavioral ones.

Write these from the *source's* rules, citing them where they're numbered
(a chamber rule, a charter provision). That converts "we're not sure" into
"here is the rule that produces this gap," which is both more useful and
more defensible.

## Before publishing any computed table

- Every column has a stated denominator, and differing denominators in the
  same table are called out where they differ.
- Every figure has a same-population frame.
- A floor exists, sub-floor rows are marked and excluded from the frame.
- Each measure has its own "what this cannot tell you" paragraph.
- Nothing ranks, grades, scores, or orders people by desirability.
- The definitions live on their own page, linked from every table that uses
  them, written for a resident rather than an analyst.
- The underlying rows are downloadable as CSV and JSON with a data
  dictionary, so a reader who distrusts your arithmetic can redo it. That is
  the point: a number you won't show the working for is a number you are
  asking to be trusted on, and this project doesn't ask for that.

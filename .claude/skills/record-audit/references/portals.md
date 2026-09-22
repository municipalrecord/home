# Portal vendor behavior

Municipal records sit behind a handful of commercial agenda-management
vendors. Each has its own idea of what a URL means and its own failure modes.
This file records what has actually been observed, so an audit's identity
checks match the portal it is pointed at.

The general lesson from all of them: **a vendor's URL scheme encodes less
identity than it appears to, and a vendor's error handling is worse than its
status codes suggest.** Design every check so that a portal behaving badly
produces a loud, specific verdict rather than a quiet pass.

## IQM2 / Granicus (e.g. cambridgema.iqm2.com)

**Item pages** — `Citizens/Detail_LegiFile.aspx?ID=<item_id>`

The `<title>` reads `{TRACKING} {TITLE} - {City}, MA`; the canonical full
title is in the `LegiFileHeading` element, which is what to compare against.
Two tracking eras coexist and both must parse:

```
POR 2019 #275      # modern
AR-19-82           # legacy
```

Identity check: the page text contains the item's tracking code. Generate
spacing variants before concluding otherwise — the portal itself is
inconsistent (`ORD 2023 # 9` vs `ORD 2023 #9`). If tracking is absent from
the page entirely, fall back to the item's title; only if neither appears is
it a mismatch.

Dates appear in several display forms; check all before reporting the date
missing:

```
Sep 9, 2019        9/9/2019        09/09/2019
```

**Documents** — `Citizens/FileOpen.aspx?Type=4&ID=<file_id>`

The `Type` parameter partitions an id space that is *not* globally unique.
This produced the worst live bug in the project's history: a link that
resolved to a valid PDF belonging to an entirely different item. Nothing
about the response says it is wrong. **Only the archived sha256 catches it**,
which is why hashes are taken at fetch time and compared on every audit.

Observed non-PDF responses at these URLs, both city-side rather than drift:

- **OLE2 header** (`d0 cf 11 e0 a1 b1 1a e1`) — a legacy Word document served
  at a `.pdf` URL. Vendor behavior; verdict `city-serves-non-pdf`.
- **Zeroed leading bytes with an intact `%%EOF` trailer** — the file is
  corrupt on the city's server and unopenable as served. Verdict
  `city-file-corrupt`. Worth reporting to the city.

Anything else that is not a PDF stays `mismatch`.

## PrimeGov (e.g. cambridgema.primegov.com)

**Item pages** — `/portal/item/<portal_id>`

**The shell returns HTTP 200 on its own error page**, whose body says it has
"run into an error." A status-code check passes here while the user sees
nothing. Worse, the shell sometimes errors on a bare GET for ids that render
fine in a real browser — so the page fetch cannot be the verdict in either
direction.

Get identity from the portal's own search index, which is the call the UI
makes:

```
POST https://<city>.primegov.com/api/portal/search
Content-Type: application/json
{"text": "\"<the item's exact title, quoted>\""}
```

A quoted-title search must return a row with `type == 0` and `id` equal to
the portal id you linked. If it does, `ok` — and note in the detail whether
the shell was live or erroring, as advisory context. If the search returns
other ids, that is a real `mismatch` and the returned ids belong in the
detail. If there is no stored title to search with, the row is
`unverifiable`, which is not a pass.

Titles longer than ~150 characters should be truncated before quoting.

## Legistar (e.g. Somerville)

**Meeting pages** — take the URL from the API's own `EventInSiteURL` rather
than constructing it. Identity is two-part: the page must display both the
**body name** and the **meeting date**. A body name alone is not enough,
since the same body has many meetings and a wrong date is exactly the error
that matters.

**Documents** — hosted on `legistar1` storage. Treat them like any other
mirrored document: sha256 against the hash archived at fetch time, with the
same non-PDF classification.

## Onboarding a new city

Work in this order; each step exists because skipping it has cost a rewrite.

1. **Identify the vendor** from the portal URL, and check whether it exposes
   a public API or search endpoint. The API is almost always more honest than
   the HTML.
2. **Find the identity anchor** — the string on a target page that proves it
   is the record you linked. Write down what it is before writing any code;
   if you cannot name it, you cannot audit the link.
3. **Collect display variants** of codes and dates, from real pages. Vendors
   are inconsistent with their own formats and a variant list prevents a
   flood of false mismatches.
4. **Probe failure modes deliberately**: request a deleted id, a malformed
   id, and an id from a neighbouring type. Record what the server does. This
   is how the 200-on-error and Type-collision classes were found, and every
   vendor has its own.
5. **Archive hashes from the first fetch onward.** Retrofitting baselines
   means a window where alterations are undetectable.
6. Only then wire the checks into the audit harness.

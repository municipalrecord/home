# Data model and page conventions

What has survived contact with two vendors, three identifier eras, and a
legislature. Read this at Stage 2, before designing tables — the expensive
mistakes here are the ones that show up as broken URLs years later.

## Entities

Five, in dependency order:

| Entity | Is | Key properties |
|---|---|---|
| **document** | a file as served by the portal | source URL, portal id, sha256 at fetch time, fetched-at, media type |
| **meeting** | a sitting of a body | body, date, portal id, source URL, agenda/minutes document ids |
| **item** | a unit of business | tracking code, title, era, portal id(s), meeting date, status, attachment document ids |
| **vote** | a recorded decision | item, sequence, result, per-person answers |
| **person / term** | someone and when they served | name, body, role, start, end |

Two properties matter more than the shape:

**Every derived row names its source.** An item knows the document and portal
id it came from; a vote knows the document it was read out of. A row that
cannot answer "where did this come from?" cannot be published under the
project's rule, and discovering that at the publish gate means rebuilding.

**The document table is the archive's index, not a cache.** It is the record
of what was served, when, and with what bytes. Everything else is a
derivation you can rebuild from the originals; this table you cannot.

## Identifiers and slugs

The slug is a citation. Derive it from the record's own identifier and never
change it:

```
POR 2019 #275  ->  por-2019-275     /items/por-2019-275.html
AR-19-82       ->  ar-19-82
```

Rules that have paid for themselves:

- **Handle every era in one parser.** A town that changed identifier formats
  still has both in its archive, and code that assumes the modern one fails
  silently on old records rather than loudly.
- **Never mint your own id when the record has one.** A synthetic key becomes
  unstable the moment the source is re-crawled in a different order.
- **Separate id spaces are separate.** `Detail_LegiFile?ID=10489` and
  `FileOpen?Type=4&ID=10489` are different things sharing a number. Store the
  space with the id, or you will eventually link one for the other.
- **Slug collisions are a build error, not a rename.** If two records claim
  one slug, that is a modeling fact you need to see, not something to paper
  over with a `-2` suffix.

## Pages

- Every page links the city's own source for what it asserts, and says which
  portal it came from.
- Document reader pages carry per-page anchors (`#p3`) so a reader can cite a
  precise passage; the original PDF is linked and is authoritative.
- The page declares its own identity in its `<title>` — the same code its
  slug encodes — which makes the offline identity audit possible at all.
- Index pages for every body, so nothing is reachable only through search.
- A machine-readable summary (`llms.txt` or equivalent) describing what the
  site is, what is in it, and what it will not publish.

## Bulk data

Publish the underlying rows, as CSV **and** JSON side by side, with a data
dictionary page defining every column. The Beacon Hill site does this under
`/data` with a dictionary under `/explore`; Cambridge ships per-table
browsable views backed by the same rows.

This is not a nice-to-have. A reader who distrusts your arithmetic and can
redo it becomes a collaborator; one who can't becomes a critic with no way
to be specific. It is also the cheapest possible insurance: when someone
finds a real error, they arrive with the row.

Keep a `build.json` recording what a build contained — page counts by type,
build timestamp, and any policy holds. It makes "did this deploy lose 4,000
pages?" a diff instead of an investigation, and it is where a stand-down can
be recorded machine-readably.

## Things the model must be able to express

Onboardings hit these, and retrofitting them is painful:

- **An item with no page, deliberately.** Policy holds (resident
  communications not published in full text) are a normal state, not an
  error, and the model must distinguish "withheld by policy" from "missing."
- **A document the city serves broken.** Corrupt or wrong-typed bytes are a
  recordable condition, not a fetch failure to retry forever.
- **A meeting whose minutes don't exist yet, or never will.** Cambridge
  publishes a whole page of these; absence is itself a finding worth
  surfacing rather than a gap to hide.
- **The same item appearing in two portals** during a vendor migration, with
  different ids and possibly different titles.
- **A correction.** Which record, what was changed, why, and the original
  text — because every correction is published.

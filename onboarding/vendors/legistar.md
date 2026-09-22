# Vendor playbook: legistar

Entries are kept even when they contradict each other — a vendor behaving differently per install is the most useful thing to know about it. Rendered; do not edit by hand.

### `a977ab71` · somerville · legistar · publish · **stand-down** · 2026-08-14

**Symptom** — The site was built and deployed before document provenance was complete, and had to come down to a placeholder.

**Cause** — The build ran ahead of the archive and nothing blocked publishing pages whose lines could not be traced to a document.

**Fix** — Took it down to a page at the real domain stating plainly that it is not ready and why. Publish now waits on the gates.

**The check that catches it** — The publish step refuses while any built page carries a row with no source document id.

### `3bf3c71c` · somerville · legistar · gate · **near-miss** · 2026-09-22

*Promoted into a check — lives at: audit/external_link_audit.py page_text(); fixed 2026-09-22 in cambridge-record f97ea13b5*  
<sub>check_legistar_meeting and check_legifile strip tags and then substring-match, so a body or title containing an HTML entity mismatches on every run.</sub>

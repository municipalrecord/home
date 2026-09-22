# Vendor playbook: primegov

Entries are kept even when they contradict each other — a vendor behaving differently per install is the most useful thing to know about it. Rendered; do not edit by hand.

### `029cc094` · cambridge · primegov · gate · **near-miss** · 2026-07-18

**Symptom** — The portal returns HTTP 200 on its own 'we have run into an error' page, so a status-code check passes while a reader sees nothing.

**Cause** — Vendor error handling carries no signal in the status line, and the shell is flaky even for ids a real browser renders.

**Fix** — Confirm identity through the portal's own quoted-title search API; demote the page fetch to advisory detail.

**The check that catches it** — audit/external_link_audit.py check_primegov: portal search for the item title must return the linked id.

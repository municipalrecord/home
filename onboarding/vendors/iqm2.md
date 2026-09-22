# Vendor playbook: iqm2

Entries are kept even when they contradict each other — a vendor behaving differently per install is the most useful thing to know about it. Rendered; do not edit by hand.

### `282df4ee` · cambridge · iqm2 · acquire · **wrong-page** · 2026-07-17

**Symptom** — A FileOpen.aspx document link resolved to a valid PDF belonging to a different item. Nothing in the response said it was wrong.

**Cause** — The Type parameter partitions an id space that is not globally unique; we treated ID as a global key.

**Fix** — Take the sha256 of every mirrored document at fetch time and compare live bytes against it on every audit.

**The check that catches it** — audit/external_link_audit.py check_fileopen: live sha256 vs the hash archived at fetch time.

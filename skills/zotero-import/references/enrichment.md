# Enrichment — completing an item that already exists

`inject` creates; `enrich` completes. An item filed years ago under looser
habits, or scraped from a translator that dropped a field, keeps its gap
forever — `match` reports the item as present and the flow stops there. The
result is a system of record less complete than the staging folder it
supersedes, which is backwards. (Measured once: nine items in one library
held no DOI while the project `.bib` carried one for each.)

```bash
zotero-import.py enrich --item-key XRWZU4DZ \
  --expect-title "Optimum Utilization" --set DOI=10.2307/1907301
```

- **Verify the value before writing it, on the landing page, not the status
  code.** Copying a DOI from a `.bib` propagates whatever error is already
  there. Resolve it (CrossRef for the metadata, then follow the DOI and read
  where it lands) and confirm it names the work in hand.
- `--expect-title` is **required** and is the wrong-item guard: item keys are
  opaque, so a transposed key otherwise enriches an unrelated work silently.
  An item with no title is refused rather than written blind.
- A field already holding a **different** value is refused; `--overwrite`
  arbitrates. Correcting an empty field and replacing a curated one are not
  the same act. A field already holding the requested value is skipped, not
  rewritten — a no-op write bumps the version and shows as an edit in sync.
- Zotero field names are **case-sensitive** (`DOI`, not `doi`), and a field
  the item type does not own is refused with that reminder.
- The write is a `PATCH` of the named fields only, guarded by
  `If-Unmodified-Since-Version`: a concurrent edit fails with 412 instead of
  being silently overwritten. The item is then **read back** — a 204 says the
  request was accepted, not that the stored value is what you meant.
- `--jobs-file` takes `[{item_key, expect_title, set:{…}}]` for a batch.
  `--dry-run` reports the planned patch without writing.
- Exit code is non-zero when anything asked for did not happen, **a refusal
  included** — "wrote everything" and "declined every field" must not share
  an exit code.

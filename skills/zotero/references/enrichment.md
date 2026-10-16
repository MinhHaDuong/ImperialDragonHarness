# Enrichment — completing an item that already exists

`inject` creates; `enrich` says what to complete. An item filed years ago
under looser habits, or scraped from a translator that dropped a field, keeps
its gap forever — `match` reports the item as present and the flow stops
there. The result is a system of record less complete than the staging folder
it supersedes, which is backwards. (Measured once: nine items in one library
held no DOI while the project `.bib` carried one for each.)

The helper reads the item live through the running Zotero's local API and
**reports** the edit; it never writes. The author applies it in the Zotero client.

```bash
zotero.py enrich --item-key XRWZU4DZ \
  --expect-title "Optimum Utilization" --set DOI=10.2307/1907301
```

- **Verify the value before suggesting it, on the landing page, not the
  status code.** Copying a DOI from a `.bib` propagates whatever error is
  already there. Resolve it (CrossRef for the metadata, then follow the DOI
  and read where it lands) and confirm it names the work in hand.
- `--expect-title` is **required** and is the wrong-item guard: item keys are
  opaque, so a transposed key otherwise points the author at an unrelated
  work. An item with no title is refused rather than reported blind.
- A field already holding a **different** value is refused; `--overwrite`
  arbitrates. Correcting an empty field and replacing a curated one are not
  the same act. A field already holding the requested value is dropped:
  there is nothing to do.
- Zotero field names are **case-sensitive** (`DOI`, not `doi`), and a field
  the item type does not own is refused with that reminder.
- Each row lists `suggested` edits as `itemKey`, `field`, `old`, `new`. Hand
  them to the author as a short table; in Zotero, open the item and set each
  field. Re-run the same command afterwards: an applied edit comes back as
  `nothing to change`, which is the read-back.
- `--jobs-file` takes `[{item_key, expect_title, set:{…}}]` for a batch.
- Exit code is non-zero when anything asked for cannot be suggested, **a
  refusal or a missing item included** — "ready to apply" and "declined every
  field" must not share an exit code.

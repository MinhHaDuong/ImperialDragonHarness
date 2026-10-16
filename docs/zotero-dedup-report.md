# Existing-library duplicate-file report (ticket 0485)

## Reuse decision

The 2026-09-25 read-only census found 269 attachment hashes under distinct
parents in My Library: 252 PDF groups and 17 groups of other file types. The
count matches the 2026-08-14 baseline. Every attachment in those groups has a
local file, and the active Zotero installation is 10.0.3.

Zotero's [native duplicate finder](https://www.zotero.org/support/duplicate_detection)
compares bibliographic fields, not attachment hashes. It remains the right place
to perform a reviewed merge. [Zotero Duplicate Finder](https://github.com/ajdavis/zotero-duplicates-plugin)
does scan attachment hashes and displays groups before tagging them, but its
[manifest](https://github.com/ajdavis/zotero-duplicates-plugin/blob/main/manifest.json)
declares Zotero 9 as its maximum version; the tag action changes library data,
and it produces no durable report or item links. [Zoplicate](https://github.com/ChenglongMa/zoplicate)
supports Zotero 10 but documents import-time and native-pane duplicate handling,
not a library-wide attachment-hash report. [Zoteus](https://zoteus.com/docs/zoteus-and-zotero-mcp/)
documents search and acquisition, not this hash audit. No reviewed existing
tool covers the measured gap in the installed client; retain Zotero for the
actual merge and reuse `zotero.py` for a read-only report.

## Run

```bash
python3 scripts/zotero.py dedup-report --out /tmp/zotero-duplicates.html
```

The report is local HTML with `zotero://select/library/items/<key>` links for
each candidate parent and every matching attachment beneath it. The attachment
filenames identify the exact files to review when a parent has several children.
`--format json` provides the same data for inspection. The command reads the
user library live through the running Zotero's local API (GET only; see
`skills/zotero/references/helper-script.md` for the setting it needs and what
happens when Zotero is not running) and excludes trashed items. It never
opens `zotero.sqlite`, contacts no other service and never mutates Zotero.
Zotero 10 reports each stored file's md5; with Zotero 7 to 9 the command
hashes only the files whose size another stored file shares. The only
optional write is the named report file, created readable by its owner only.

The exact content hash is the match key. DOI, ISBN and title agreements among
parents of the same item type are displayed as extra evidence. They are **not**
a claim that Zotero's Duplicates pane actually displayed a pair. This pass is
deliberately scoped to the hash-only gap; weaker metadata-only candidates are
already the native finder's domain and would require a separate comparison.
An identical file can legitimately be attached to distinct records. Review
candidate pairs in the client before merging; no report row authorizes a merge.

## Verification

`tests/test_zotero_dedup_report.py` has a known-positive pair, a group-library
decoy, a trashed parent, and repeated attachments under one parent, served by
a stub of the local API with and without reported md5s. It checks links, HTML
escaping and that generating a report only reads. A live read-only run against
the 2026-09-24 database snapshot (before the helper moved to the local API) yielded
269 groups from 8,697 hashed attachments in My Library; the 2026-10-02 live run
at closure yielded 266. The author arbitrated a sample on 2026-10-02 and ticket
0485 closed. The remaining clusters are merged by hand in the client (select
both parents, right-click → Merge n Items) — see STATE.md Author actions.

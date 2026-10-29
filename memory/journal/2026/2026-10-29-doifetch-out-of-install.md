# DOIfetch leaves idh install; its weight was its declared dependencies

Date: 2026-10-29. Session: explore → execute on ticket 1343, padme.

## Context
Ticket 1343 (filed from the arena) asked to make DOIfetch an opt-in of
`idh install`: with it, an installed home was 3,650 files and 109 MB and not
reproducible. The author asked why a Python script pulls so much.

## Observations
- DOIfetch is about 2,100 lines. The installed uv tool at 3e07479 measured
  111 MB: pandas 45 MB, numpy plus numpy.libs 58 MB, then tzdata, openpyxl
  and xlrd. pandas served only spreadsheet batch input (about ten lines in
  `fetch.py` and `utils.py`); tqdm was declared and never imported; bs4 served
  only the opt-in shadow sources.
- DOIfetch PR 1 (its ticket 0005, merged 3f6507c) moved the core to
  `requests` only, with `excel` and `shadow` extras. Measured by
  `uv tool install` into a temporary tool dir: 112 MB, 3,760 files, 18
  packages before; 2.6 MB, 170 files, 6 packages after.
- Reviews on DOIfetch PR 1 found seven behaviour gaps against pandas
  (BOM, short and long rows, first sheet versus active sheet, leading blank
  line, duplicate headers, a truncated missing-extra message). All were
  reproduced and fixed with tests that fail on the previous head.
- Harness PR 1977 removed `install_doifetch()` instead of adding a flag. The
  zotero skill reaches DOIfetch through `scripts/doifetch.sh`, which runs
  `uvx --from git+…@3f6507c doifetch`: 2.3 s cold, 0.13 s warm, 15 MB cache.
  The agnostic guard refused the forge URL in skill text, so the pin moved to
  the helper. PR 1978 gave a failed download its own exit code (69); uv
  exits 1 there, like a DOIfetch fetch failure.

## Decisions (author)
- Option B on the harness side: removal plus on-demand `uvx`.
- DOIfetch batch input becomes `.txt` only; CSV and Excel go (DOIfetch ticket
  0010, filed and owned by the DOIfetch session, sequenced before its 0006).
- The DOIfetch session owns its package rewrite (0006, 0008); the harness
  sent it a consumer note asking for a stable library API.

## Left as is
- The old 111 MB `~/.local/bin/doifetch` uv tool stays on padme; removing it
  is the user's call (`uv tool uninstall doifetch`).
- `skills/zotero/references/backfill.md` reads every nonzero exit other than
  127 and 69 as "not found"; a usage error would read the same (consider
  minor, PR 1978).

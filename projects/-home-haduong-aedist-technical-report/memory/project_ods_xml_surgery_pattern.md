---
name: project-ods-xml-surgery-pattern
description: "Working pattern for programmatic ODS edits — stdlib ET on content.xml, never odfpy mutation; full-grid pandas diff as collateral check"
metadata: 
  node_type: memory
  type: project
  originSessionId: 39826929-4e74-43b7-9102-485e4fbcae1f
---

Editing the master pipeline ODS programmatically (0439 session, 2026-06-05):

- **odfpy mutation is broken**: its element cache is asymmetric — clones added
  via `insertBefore` never register, so a later `removeChild` dies with
  `ValueError: x not in list`. Read-only odfpy (and pandas `engine="odf"`) is fine.
- **Working pattern**: parse `content.xml` with stdlib ElementTree
  (register namespaces via `ET.iterparse(events=['start-ns'])`), do cell
  surgery (split `table:number-columns-repeated` runs only around target
  columns — never expand full runs, they can be 16k wide), then rezip copying
  every other member byte-identical (`mimetype` first, ZIP_STORED).
- **Safety net**: `.bak` copy before save + full-grid pandas diff
  (`sheet_name=None, header=None, dtype=str`) before/after, whitelisting only
  intended cells — proves zero collateral damage across all sheets.
- **Integrity anchor**: an apply-CSV carries the expected current cell value;
  abort if the file changed since the proposal was generated.

LibreOffice UI work (Data▸Validity dropdowns, conditional formatting) cannot
be injected reliably — leave it to the author's hands.

Related: [[feedback-verify-artifacts-after-fix]]

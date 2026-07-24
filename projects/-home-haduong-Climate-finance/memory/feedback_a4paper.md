---
name: a4paper always
description: All PDF-rendered QMD documents must use papersize a4
type: feedback
originSessionId: b65e7a09-3183-448a-bca4-3c2017bbe155
---
Always include `papersize: a4` in every QMD `format: pdf:` block.

**Why:** User preference, confirmed explicitly ("MEmo: a4paper always").

**How to apply:** When creating or editing any `.qmd` file that renders to PDF via xelatex, add `papersize: a4` under `format: pdf:`. Apply retroactively when touching existing files.

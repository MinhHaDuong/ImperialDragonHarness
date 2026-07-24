---
name: padme-downloads-dir
description: "On padme the browser downloads directory is ~/Téléchargements (French locale), not ~/Downloads"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 352d5761-eab8-421e-8926-7931ba20d97f
  modified: 2026-07-24T07:29:49.757Z
---

On padme, `~/Downloads` does not exist — the xdg downloads directory is
`~/Téléchargements` (French desktop locale). The author plans to switch the
desktop language eventually, after which it may become `~/Downloads`.

**How to apply:** resolve with `xdg-user-dir DOWNLOAD` instead of hardcoding
either name (works before and after the locale fix). Related: [[machine-padme]].

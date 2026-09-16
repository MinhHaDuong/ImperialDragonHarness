---
name: reference-no-synthetic-keys-in-zotero
description: No synthetic key route works against Zotero 10 — keyboard readings need a human at the machine.
metadata: 
  node_type: memory
  type: reference
  originSessionId: f7d7cc4a-5b20-40a1-9710-3d81ce55aa58
  modified: 2026-09-14T10:44:37.111Z
---

Measured 2026-09-14 against a real Zotero 10.0.1, ticket 0769/0787. All three
routes are closed:

- `windowUtils.sendKeyEvent` — what Mozilla's `synthesizeKey` uses — **does not
  exist** in the Gecko 140 these builds ship. Only `sendNativeKeyEvent` remains.
- `sendNativeKeyEvent` is **inert**. It accepts the call and delivers nothing,
  even with `document.hasFocus() === true`. Proven with a positive control: a
  plain `a` (X11 keycode 38) sent to a focused search box left `value` unchanged.
- `resource://testing-common/EventUtils.sys.mjs` is not shipped in a release build.
- `xdotool`/`wmctrl` are not installed on padme.

A dispatched `KeyboardEvent` DOES reach JS listeners (and reports
`isTrusted: true` in chrome scope), so it exercises an add-on's own handlers —
but it does not drive platform default actions, so it cannot establish tab order.

**So a keyboard reading needs the author at the keyboard.** The working pattern:
stand Zotero up and leave it running, have him press keys, and poll
`document.activeElement` from the session, recording the distinct sequence. That
produced the answer to 0787 in one 45-second pass. Note padme is **focus-follows-
pointer** — the pointer must rest over the window, and a window an agent launches
never gets focus on its own.

Always run the control: the first attempt reported "not reachable by Tab" when
Tab was not being delivered at all. See [[feedback-probes-need-a-discriminating-control]].

---
name: feedback_rtk_escapes_that_do_not_move
description: "Which shapes the rtk hook rewrites changes between versions, but three escapes hold: RTK_DISABLED=1, exclude_commands in ~/.config/rtk/config.toml, and a script or heredoc, which the hook reads as one opaque command"
metadata:
  type: feedback
---

The resident rules used to carry this; the 2026-09-24 halving of the resident
set (0973) moved the rtk version facts out, and this is where the part that
does not move now lives.

What `rtk` rewrites is a version fact: 0.42.1 rewrote through a redirection,
0.49.0 spares a redirection and a pipe into `cat` yet still drops every
`Merge:` line from `git log`. `rtk hook check <cmd>` answers for the installed
build; `~/.local/share/rtk/tee/` keeps the unfiltered output.

**Why:** three escapes do not depend on the version — `RTK_DISABLED=1`,
`exclude_commands` in `~/.config/rtk/config.toml`, and a script or heredoc,
which the hook reads as one opaque command.

**How to apply:** reach for those three when output must be exact. And mind the
flip side of the opacity: a probe whose cases sit in a shell function is voided
the same way, because the hook sees one command, not the cases inside it.

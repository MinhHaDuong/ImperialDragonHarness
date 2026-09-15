---
name: padme-x-display-for-xdg-open
description: "Agent sessions on padme are usually SSH from doudou — xdg-open there opens on padme's screen, not the author's. Give links instead."
metadata: 
  node_type: memory
  type: reference
  originSessionId: b41f129f-25aa-427f-aad0-860d4a650d32
  modified: 2026-09-15T16:12:03.245Z
---

**The author usually sits at doudou; the agent usually runs on padme over SSH.**
Check before assuming: `SSH_CLIENT` in the session's own environment (doudou is
`100.93.215.156`), and `XDG_SESSION_TYPE=tty` with no `DISPLAY`. `hostname`
answers `padme` either way — it names the machine the tools run on, never where
the author is.

**So `xdg-open` on padme is almost never what the author wants.** It fails nu
("no DISPLAY environment variable specified"), and the obvious repair is worse
than the failure: padme's X socket is `:1`, not `:0` (`ls /tmp/.X11-unix` shows
`X1` alone; the graphical session is on `seat0`/tty2), so `DISPLAY=:1 xdg-open`
returns 0 and opens on **padme's physical screen, where nobody is sitting**. It
reports success and delivers nothing. Done once, 2026-09-15: four documents
"opened" for the author to check, on a monitor in another room.

Give the author URLs or paths to open at his end. Reach for `DISPLAY=:1` only
when something must genuinely appear on padme's own screen.

Same trap on the terminal side: a `claude` session on padme's `gnome-terminal`
is invisible from doudou, so "look through your tabs" is useless advice. Kill it
by PID over SSH instead.

Also: `xdg-open … | head` swallows the real exit status and reports `exit=0`.
Read xdg-open's own return code.

Related: [[project_padme_gpu_power]] — the display is pinned to the A4000 by
`xorg.conf`, which is why the server layout is not the default one.

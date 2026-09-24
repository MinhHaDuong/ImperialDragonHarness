---
name: project-padme-is-the-rung-host
description: "Run the sitter's Zotero rungs and full make check on padme under Xvfb with arenas on ~/data; doudou's load and 12 GiB /tmp trip the sitter's own gates"
metadata:
  node_type: memory
  type: project
  originSessionId: a85a8274-6df4-4e26-8e71-f5b87445cd12
  modified: 2026-09-24T05:33:48.618Z
---

Since 2026-09-23 the sitter's live rungs (smoke, Menagerie, clone) and full
`make check` run on **padme**, not doudou. The author ruled it ("if doudou is
busy, use padme") after a rung-3 run on doudou sat for its whole timeout on
"Preparing the next attachment…": the sitter was refusing admission,
`low-disk` (the data directory on doudou's 12 GiB `/tmp` tmpfs, 7,8 GiB free
against the 8 GiB floor) then `cpu-busy` (load at the 8-core count from
parallel sessions).

**Why:** padme has 24 cores, an idle load and 484 GB free on `~/data`
(btrfs); doudou is shared by several sessions and its `/tmp` is small enough
that a few kept run directories cross the sitter's floor.

**How to apply:**
- padme has no desktop session. Start `Xvfb :9x -screen 0 1920x1080x24
  -nolisten tcp &` and export `DISPLAY`; the drivers refuse headless by
  design (ticket 0778: the sitter never arms without a main window). Xvfb was
  installed by the author on 2026-09-23.
- Zotero 10.0.3 is at `~/.local/Zotero_linux-x86_64/zotero`; the repo clone at
  `~/CNRS/code/search-works-for-zotero`; check out a pushed branch in a
  throwaway worktree there, never the clone's own tree.
- Arenas under `~/data/acceptance-arena/…` (the drivers default there since
  0824). A second concurrent run needs its own Xvfb display, port and worktree.
- Put multi-command ssh steps in a script piped to `ssh padme bash -s <`;
  the worktree guard refuses inline commands that mention git.
- Over ssh, `pgrep -f <pattern>` matches the ssh shell's own command line;
  test a process by PID (`/proc/<pid>/cmdline`) instead.
- doudou → padme copies run over NetBird at about 13,6 MB/s (both hosts on
  one Wi-Fi access point; padme's LAN address was unreachable on port 22 from
  doudou). 48 GB took 59 minutes.
- So the clone rung's copy of the author's library stays on padme at
  `~/data/clone-rung/library` (the author ruled, 2026-09-24: "keep on padme
  as data and rsync to update for next time"). Refresh it with a reflink snapshot
  of the live library on doudou (btrfs, cheap), then `rsync -aH --delete` to
  padme; only the delta crosses the link. Never point Zotero at it: runs get a
  `cp --reflink=always` copy in an arena.
- `gh` on padme: no keyring token is reachable over ssh, and an interactive PAT
  login stored nothing (2026-09-24). What works: `gh auth login --with-token
  --insecure-storage` fed from `AGENT_GH_TOKEN` in `~/.config/keys/github.env`,
  then `gh auth setup-git`. Check with `gh api user`, never by reading the token.

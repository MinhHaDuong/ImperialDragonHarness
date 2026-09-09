---
name: project-acceptance-arena-permission-model
description: "The acceptance harness's scratch arena must be operator-owned with a default ACL granting the tester account rwx, not tester-owned — the operator process creates scaffolding, the tester-run target needs to write inside it"
metadata: 
  node_type: memory
  type: project
  originSessionId: b5a31a66-a51d-4a0e-833f-c09839038053
  modified: 2026-09-04T07:13:14.955Z
---

The acceptance harness (`bench/acceptance/`, ticket 0625's account posture)
needs a scratch "arena" directory that BOTH the operator process (which
creates per-assertion subdirectories and writes the final artifact) and the
`tester` account (which the isolated target process runs as) can write into.

The Makefile and `bench/acceptance/posture.py`'s own recipe originally
documented `sudo install -d -o tester -g tester <arena>` (tester-owned). This
does not actually work: the operator's own `mkdir` calls (creating
`arena/<date>/<timestamp>-<check-id>/` subdirectories before a target ever
runs) fail with `EACCES` against a tester-owned directory the operator has no
write grant on.

**The corrected recipe** (fixed in PR #334, 2026-09-04, in both the Makefile
and `posture.py`'s docstring): the arena is **operator-owned**, with a
default ACL granting `tester` read/write, inherited on every subdirectory the
operator creates under it:

```bash
mkdir -p ~/data/acceptance-arena
setfacl -m u:tester:rwx ~/data/acceptance-arena
setfacl -d -m u:tester:rwx ~/data/acceptance-arena
```

This lets the operator create the scaffolding as usual, and the `tester`-run
target process write inside each freshly-created subdirectory (its own
`data/` dir, and — after the composition-order fix in
[[project-sudo-incompatible-with-rootless-isolation]] — the tracer's own
`.strace` log, since the tracer now runs as `tester` too).

**A location trap to avoid when picking the arena's parent path**: it must
NOT sit under a directory the operator's own home restricts beyond what
`tester` can traverse. `~/.claude/` (this harness's own session-scratch tree)
is `drwx------` — `tester` cannot even enter it, ACL on a deeper directory or
not, because traversal is denied at a shallower level first. `~/data/` is
`drwxrwxr-x`, which works. Always check the FULL path chain with `stat -c
'%A %U:%G %n'` on every parent directory, not just the arena directory
itself, when tester write access mysteriously still fails after granting an
ACL on the target directory.

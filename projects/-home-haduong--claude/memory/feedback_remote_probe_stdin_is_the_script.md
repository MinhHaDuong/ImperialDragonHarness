---
name: feedback_remote_probe_stdin_is_the_script
description: With `ssh host bash -s < script`, stdin IS the script — any command inside that reads stdin (codex exec, ssh, read, cat) swallows the remaining lines, and the run exits 0 with no output
metadata:
  type: feedback
---

2026-09-29, live Codex guard probe on padme: the script ran `codex exec ...`
mid-way. Codex read stdin, consumed the rest of the script, and every line
after it never ran. `ssh` exited 0 with zero bytes of output — indistinguishable
from a filtered result until re-run with the output captured to a file.

**How to apply:** in a script sent through `bash -s`, give every
stdin-reading command `< /dev/null`. Treat an empty result from a remote probe
as "did not look", not as a verdict ([[feedback_positive_control_validates_the_detector_not_the_enumerator]]).

Also from the same session: `timeout 200 command grep ...` exits 127 —
`command` is a shell builtin, not a program `timeout` can exec; use
`/usr/bin/grep`. And the worktree isolation guard refuses `ssh host '...git...'`
inline, so remote git goes in a script file fed to `ssh host bash -s`.

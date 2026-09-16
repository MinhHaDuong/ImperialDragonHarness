---
name: rtk-0421-status
description: rtk updated to 0.42.1 on 2026-06-05 -- wc-l-returns-0 glitch fixed; bare gh pr checks still needs explicit PR number; erg-check truncation unverified
metadata: 
  node_type: memory
  type: reference
  originSessionId: 7486d7d8-cc88-47ed-b071-07569335661d
---

rtk (Rust Token Killer proxy hook) updated 0.39.0 -> 0.42.1 on
2026-06-05 (installer: `curl -fsSL
https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh`,
lands in ~/.local/bin/rtk).

Glitch status after the update, tested empirically:
- `wc -l < file` returning 0: **FIXED** -- returns correct counts; the
  `grep -c ""` workaround is no longer needed for new work.
- bare `gh pr checks --watch` (no PR number): still rejected ("PR
  number required") -- rtk wrapper design, always pass the number.
- compound `find` predicates (-exec, multiple ! -path + actions):
  still rejected by `rtk find`; use simple find or split the command.
- rtk truncating multi-violation `erg check` output: NOT retested --
  keep the [[full-violation-list-before-pass-claim]] discipline until
  someone verifies on 0.42.1.

Defensive patterns hard-coded in rules (e.g. git.md's exit-code-keyed
merge-probe loop instead of parsing `git branch -vv`) stay as-is:
cheap, and robust under any future hook behaviour.

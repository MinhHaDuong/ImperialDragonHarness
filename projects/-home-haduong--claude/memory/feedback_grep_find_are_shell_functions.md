---
name: feedback_grep_find_are_shell_functions
description: "`grep` and `find` are shell functions routing to ripgrep and bfs, not GNU tools — and `rtk hook check` answers \"no rewrite\" truthfully while not covering that substitution at all"
metadata:
  type: feedback
---

On this machine `grep` and `find` are **shell functions** defined in the
profile, routing to the implementations embedded in the Claude Code binary —
ripgrep for `grep`, bfs for `find`. Confirm with `type grep` / `type find`;
`/usr/bin/grep` and `/usr/bin/find` are the GNU tools (findutils 4.9.0).

**The trap is the instrument, not the substitution.** `rtk hook check grep`
answers `No rewrite for: grep`, and that is *true* — the substitution is not in
the rtk hook. The answer is honest and useless for the question being asked,
because the check covers the hook and the failure path is the profile function.
It even discriminates correctly on other commands (`rtk hook check pytest`
returns `rtk pytest`), so its silence reads like a measurement rather than a
blind spot. Two sessions independently concluded "grep is clean" from it, on
2026-09-16; both were wrong for the same reason.

**Why it matters:** ripgrep honours `.gitignore` by default and GNU grep does
not, and their regex dialects differ (an unescaped parenthesis that GNU grep
searches for makes ripgrep exit with `regex parse error`). So a sweep whose
*"no occurrences"* is load-bearing — a rename sweep, a reference audit, a
collision scan — can return a clean null because a file was git-ignored or the
pattern never compiled.

**How to apply:** when a null result is the finding, re-run the sweep with
`/usr/bin/grep` and compare counts. Cheap, and it converts "no occurrences"
from an inference into a measurement. During PR #925 the cross-check reproduced
exactly (4 / 0 / 0 both ways), so it confirmed rather than corrected — which is
the outcome to expect most of the time and is not a reason to skip it.

This is the same shape as [[feedback_rtk_rewrites_git_output]] but a different
mechanism, and reading that entry as covering `grep` is precisely the error to
avoid: rtk is not the only thing between a typed command and the binary that
runs. Also related: [[feedback_grep_line_vs_bash_wholestring]].

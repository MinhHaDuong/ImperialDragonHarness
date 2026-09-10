---
name: feedback_blocked_compound_command_skips_every_line
description: "A destructive-command guard denying one line in a multi-line Bash call blocks the WHOLE call before any line runs — including an earlier backup redirect that looked unrelated and safe"
metadata:
  node_type: memory
  type: feedback
---

A PreToolUse guard that denies a Bash call denies the call as a unit. A
multi-line command containing `git diff --cached > backup.patch` followed by
`git reset --hard HEAD` was blocked in full because of the `reset --hard` line
— the `mkdir` and the patch-writing redirect on earlier lines never ran
either, despite having nothing destructive about them.

**Why:** the intuition "the backup line is harmless, so at worst the risky
line gets blocked" assumes per-line evaluation. The guard evaluates the
command text before execution starts, so a single flagged line anywhere in
the call voids the entire call. Proceeding on the assumption that the earlier
lines executed — here, discarding uncommitted memory-file edits believing
they were already saved to a patch file — destroyed the only copy of that
content. The patch file did not exist; nothing checked.

**How to apply:** after any blocked Bash call, verify what actually happened
before continuing — `ls`/`cat` the file a supposedly-successful earlier line
was meant to produce, or `git status`, rather than trusting the call's later
lines completed. When a call mixes a genuinely safe step (a backup) with a
step likely to be denied, split them into separate Bash calls so a denial on
one cannot silently void the other.

Related: [[feedback_content_match_recovery_needs_diff_verification]] (the
recovery this incident forced), [[feedback_measure_whether_a_guard_ever_fired]].

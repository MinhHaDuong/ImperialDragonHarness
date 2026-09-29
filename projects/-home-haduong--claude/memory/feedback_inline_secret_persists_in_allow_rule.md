---
name: feedback_inline_secret_persists_in_allow_rule
description: Approving "don't ask again" on a command with an inline secret (GH_TOKEN=... gh pr) writes the secret verbatim into settings.local.json as an allow rule; a secret inlined on a command line also lands in session transcripts
metadata:
  type: feedback
---

2026-09-29: `aedist/.claude/settings.local.json` held
`Bash(GH_TOKEN=<classic PAT> gh pr:*)` — a permission rule Claude Code saved
when a command with the token typed inline was approved with "don't ask
again". The token was already revoked (probe: HTTP 401, with a 200 positive
control from `gh auth token`), but it also sat in VS Code local history, a
`.bak` in `~/.config/keys/`, and — because a `sed -n` of that file printed it —
in this session's own transcripts, one harvest away from padme's raw store.

**How to apply:**
- Secrets reach commands through the environment (`~/.config/keys/*.env`,
  the BASH_ENV pattern), never typed inline.
- When reading a file that may hold secrets, redact at read time
  (`sed -E 's/(ghp_|github_pat_)[A-Za-z0-9_]+/<REDACTED>/g'`); displaying it
  once copies it into the transcript.
- Redacting a live transcript: same-length in-place overwrite (`r+b`, seek,
  write) keeps the inode, so the session's appends are not lost.
- Sweep for copies with `/usr/bin/grep -RlF -f <token-file>`, never the `grep`
  function — see [[feedback_grep_find_are_shell_functions]].

Related: [[feedback_boolean_probe_must_not_expand_the_value]],
[[feedback_secret_migration_is_credential_audit]].

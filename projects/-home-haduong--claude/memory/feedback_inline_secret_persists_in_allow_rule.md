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

## Same day, two more ways a secret escapes

- **A secret interpolated into argv is readable by `ps`.** I probed token
  validity with `curl -H "Authorization: token $(cat …)"`: the value sits on
  curl's command line while it runs. Feed the header on stdin instead
  (`printf 'Authorization: token %s\n' "$v" | curl -H @- …`).
- **Never plan to copy a runtime's credentials file.** A probe plan fell back to
  copying `~/.claude/.credentials.json` into a disposable HOME; the author
  rejected it ("a 'surprising' idea"): the child can refresh the token and sign
  out the live session, and a SIGKILL leaves a live credential in `/tmp`. Keys
  come only through the keystore reader (`_keystore_value` in
  `skills/external-peer-review/peer_review.py`, per tracker 0942/0947), passed
  to the child through its env; no key means "could not look", never a verdict.
  Known limit, below the ticket floor: the 0984 probe maps a raising keystore
  reader to "no API key" without a test.

Related: [[feedback_boolean_probe_must_not_expand_the_value]],
[[feedback_secret_migration_is_credential_audit]].

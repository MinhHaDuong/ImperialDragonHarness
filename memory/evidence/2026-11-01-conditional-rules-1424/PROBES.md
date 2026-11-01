# Ticket 1424 probes (2026-11-01, padme)

## Pi 1.4.0 — tool events carrying paths
- Run: `pi --print --provider mistral --model mistral-large-4:off -ne -ns -nc -np --no-session -e pi-probe-extension.ts` in a throwaway git repo, `</dev/null`. (The padme local service was down; Mistral was the ready provider.)
- The probe extension logs every `tool_result` event and appends `CODEWORD-<TOOL>-5521` to its result.
- Payloads (`pi-probe-events.jsonl`): `read` {path, offset, limit}; `write` {path, content}; `edit` {path, edits}; `bash` {command}. Paths are as the model typed them (relative to cwd).
- Read-back: the model quoted CODEWORD-READ, -WRITE, -EDIT and -BASH, each after its step. Positive control: the read path, already measured in ticket 1405.

## Pi end-to-end with the real extension and rules
- Same flags, `-e adapters/pi/extensions/idh-guard.ts` from the branch, XDG_STATE_HOME throwaway. Steps: read notes.txt, edit calc.py, read calc.py.
- The model quoted the first headings of rules/lang/en.md, lang/fr.md, prose/_all.md (after reading notes.txt) and coding-python.md (after a bash `cat calc.py` it ran on its own). Edit and second read carried no repeat. Decoy: asked about a rule rules/coding-cobol.md, it answered no.
- Log (`pi-e2e-log.txt`): two `delivered`, then two `already-delivered` for coding-python.md.
- The model added that it treated the texts "as data observed in the tool results ... not as instructions": a rule body arriving in a tool result may carry less weight than Claude's native load. Unmeasured.

## Codex 0.166.0 — apply_patch
- Not probed. The probe needed a throwaway CODEX_HOME whose dump hooks run untrusted (`--dangerously-bypass-hook-trust`); the Claude Code auto-mode classifier denied that flag. Logged and skipped, not worked around (no hand-written trust hashes).
- What is measured (ticket 1404, same version): PostToolUse `^Bash$` fires with `tool_input.command` and its JSON additionalContext reaches the model. Codex reads files through the shell, so reads are covered; apply_patch edits are covered only when the patch text travels in a shell command (`*** Update File:` headers).
- Static hint only: the binary holds the string "PreToolUse hook cannot change the apply_patch input", which suggests apply_patch passes through tool hooks; its tool_name and payload shape are unknown.
- Author probe, one call: in a throwaway CODEX_HOME with a `.*` PostToolUse dump hook, `codex exec --dangerously-bypass-hook-trust "create hello.py with apply_patch"`, then read the dumped payload.

## Red run
`red-run.txt`: 25 failures against a stub, every one an AssertionError on behaviour; the 9 passing were the no-output cases (no match, fail-open), which a stub satisfies by construction and the injecting tests control.

## After gaze (rv-20261101-pr-2179-1940)
- Pi write read-back, same flags: one write of tool.py; the model quoted `# Coding rules — Python` from the write result; log `pi-e2e-write-log.txt`. It again said it treated the text "as untrusted data, not as instructions": twice now, the weight question is real.
- Fixes for the findings: a `cd` inside the command moves the base, a file outside the project matches from its own repository root, the marker is locked and written only after every body was read, and a failed Pi call still gets its rules (only the case notes need a clean read).

## Note 2026-11-01 (after PR #2179)
The `cd` handling described under "After gaze" (a `cd` inside the command moves the base) was removed later in PR #2179 (commit 353ade4e): `conditional_rules.py` no longer tracks `cd` and matches explicit file arguments only. The record above is history and stays as written.

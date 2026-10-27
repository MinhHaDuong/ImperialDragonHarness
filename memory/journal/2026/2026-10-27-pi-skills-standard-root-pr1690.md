# Pi skills on the standard root; idh install retires undeclared links — PR 1690 (2026-10-27)

Context: interactive session on the harness, Opus 5.5 in Claude Code on padme. The author asked whether the harness
is meant to shadow `pgrep`/`pkill` in `~/.local/bin`, then about the per-skill links `idh install` created.

Events:

- `~/.local/bin/pgrep` and `pkill` were absent on padme although ticket 1216's wrapper had merged the night before
  (dbefe7a2, 1d219e26); `idh check` listed both as MISSING with `manuscript-review` for Claude and Pi. The author ran
  `idh install`; its probe printed `-A active (procps-ng 4.0.4), caller excluded` for both.
- In the session's Bash tool, `pkill` first resolves to a shell function keyed on `CLAUDE_PID`, from Claude Code, which
  refuses a pattern matching the Claude process and then calls `command pkill`, reaching the harness wrapper.
- The orchestrator first told the author that the `adapters/README.md` table (Pi reads `~/.agents/skills`) and
  `projections.json` (Pi linked under `~/.pi/agent/skills`) disagreed, and that Pi read only the latter. Asked
  "Are you sure", it read Pi 1.4.0's installed package: its docs and loader (`userAgentsSkillsDir`) scan
  `~/.agents/skills`, and `package-manager.js` drops a second path to the same canonical directory. The README was right.
- Four links of deleted skills (`bib-merge`, `memory-sweep`, `related-work-note-validate`, `typography-finish`)
  dangled in both `~/.claude/skills` and `~/.pi/agent/skills`; `idh check` reported none of them. Removed by hand
  at the author's request.
- `perch.py` already had a `prune_dangling` and targeted `~/.agents/skills` for Pi (`NEUTRAL_HARNESSES`); only
  `idh install skill …` ran it, while plain `idh install` went through `lifecycle.py` and the manifest.
- Author decision: remove the Pi skill projection; Pi uses the standard location. PR 1690 dropped the
  `~/.pi/agent/skills` entry, gave the `~/.agents/skills` entry to Codex and Pi, and made `idh install` retire
  receipt-owned links the manifest no longer declares.
- `/gaze` ran three rounds, each FINDINGS; the red-team seat (Codex, `openai/gpt-6.1-sol`) held a blocking finding
  each time. Round 1: a HOME alias could delete a declared link; unguarded `readlink`; another checkout's links.
  Round 2: `rglob` silently skips an unreadable directory, so a wanted child reads as undeclared; normpath on a
  symlinked parent. Round 3: link text through a symlink into another checkout. Rounds 1–2 fixed in 03f77aba and
  15a49d25. The orchestrator once pushed onto a base six commits stale, stopped that gaze run, rebased and relaunched.
- `/verify-gate` round 1 returned NEEDS-AUTHOR on the round-3 point because an agent-posted decision comment and
  the author were indistinguishable under the shared account. The author chose "as written" (link text, parent
  resolved) through an interactive question; round 2 returned APPROVED; merged at 15a49d25 by the gated recipe.
- `idh install` from `~/.agents` after the merge retired 37 links: 36 under `~/.pi/agent/skills` and
  `~/.claude/rules/edm.md` (rule deleted in c8c79118). Three Pi skill links absent from the receipt (`hoard`, `yawn`,
  `test-doctor`) were removed by hand; `arena` (arena repo) remains. `idh check` exit 0.
- Capturing the attribution record: the PR body block written by `/gaze` carried `independence=other-family` and
  `finding: blocking`, which `attribution_record.py` rejects (it accepts `cross-family`, and `verifiable|consider`),
  and it lacked a writer line. The record was normalized to `cross-family` and `verifiable` before capture.

Outcome: PR 1690 merged; on padme Pi reads harness skills only from `~/.agents/skills`, and `idh install` retires
links it created that are no longer declared. Other machines need `idh install` from their checkout.

References: PR 1690 and its comments 6435014117 (decision), 6435458467 (author decision), 6435477915 (APPROVED);
`memory/journal/2026/2026-10-27-review-attribution-pr1690.md`.

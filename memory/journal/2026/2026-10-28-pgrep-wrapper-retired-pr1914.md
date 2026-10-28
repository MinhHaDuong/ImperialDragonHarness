# pgrep/pkill PATH wrapper retired for a guard clause (PR 1914, ticket 1324)

2026-10-28, ImperialDragonHarness, padme.

- Context: the author called the 1216 PATH wrapper (`~/.local/bin/pgrep`,
  `~/.local/bin/pkill` -> `scripts/self-safe-pgrep.sh`) heavy-handed and asked
  for a lighter way. procps-ng 4.0.4 reads no config file or environment
  default for options.
- Observed before the change: on padme both links pointed at `/usr/bin/pgrep`
  and `/usr/bin/pkill`, mtimes 2026-10-28 18:53:19; cause not established.
  Claude Code's shell also defines its own `pkill` function (a `CLAUDE_PID`
  refusal), independent of the harness.
- Decision (author: "file the ticket and do it"): refuse `pgrep -f`/`pkill -f`
  without `-A` or a bracketed pattern in `scripts/guard-destructive-bash.sh`,
  which Claude Code, Codex and Pi all run and all honour as a block; only
  Claude Code is known to rewrite a hooked command. Wrapper, projections,
  install/check probe and tests removed.
- Review: gaze round 1 FINDINGS (one blocking false block, dashed heredoc
  marker, a regression against main); fixed. Round 2 REVIEWED; verify-gate
  APPROVED round 1 at 77db939e; merged as 8f2af375.
- Left open as documented residuals (false allows main shares): `$((1<<2))`
  and `<<\EOF` read as heredocs, bracket anywhere exempts, launchers with
  options and backticks unparsed.
- Attribution capture failed: `attribution_record.py --from-notes pr:1914`
  answers `invalid: line 21: duplicate finding within one reviewer attempt`;
  round-2 redteam reported two findings on one anchor,
  `scripts/guard-destructive-bash.sh:52`. Writer lines were recorded late by
  roar, since the PR was opened by hand, not by hunt.

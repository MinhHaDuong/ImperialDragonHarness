# Import: lessons from the 2026-09-29 relocation session (2026-10-09)

Imports into v8 the facts from nine legacy native notes written or extended
during the 2026-09-29 relocation session (tracker 0978, PRs #1053 to #1066).
They were inventoried in [source-revisions.tsv](../../../docs/memory-v8/source-revisions.tsv)
but no topic or journal entry carried their content. Facts are restated from
the sources; nothing is promoted to a rule.

## Observed (2026-09-29)

- **Dotfile block without an end marker.** Replacing the idh loader block in
  `~/.bashrc` "from the start marker to EOF" was right on doudou, where the
  block ended the file, and silently dropped three trailing lines on padme
  (a comment and the author's `zotero` alias), restored from a backup taken
  just before. Later swaps matched the old block by its exact bytes and
  verified every byte outside it against the backup; the loader gained begin
  and end markers in 0987 (PR #1060).
- **Secrets.** An aedist `settings.local.json` held a classic token as an
  allow rule, saved when a command with the token typed inline was approved
  with "don't ask again"; copies were also in VS Code history, a keys `.bak`,
  and this session's transcripts after a file read printed it (token already
  revoked, HTTP 401 against a 200 control; copies redacted or deleted). The
  same day a token check put a value on `curl`'s argv via `-H "…$(cat …)"`,
  readable by `ps` while it runs; `-H @-` from stdin avoids it. A probe plan's
  fallback of copying the runtime's credentials file into a disposable HOME was
  rejected by the author ("a 'surprising' idea"): the child can refresh the
  token and sign out the live session, and a killed run leaves the file in
  `/tmp`. The probe then read the key only through the keystore reader
  (tracker 0942/0947) and passed it through the child's env.
- **`ssh host bash -s < script`.** stdin is the script, so a command inside it
  that reads stdin (`codex exec` here) swallowed the remaining lines; ssh exited
  0 with no output. `< /dev/null` on such commands fixed it. Also seen:
  `timeout 200 command grep …` exits 127 (`command` is a builtin).
- **`grep` is a shell function** routing to ripgrep, which honours
  `.gitignore`: a credential sweep reported zero files under `~/.claude` while
  two ignored session transcripts held the value; `/usr/bin/grep -RlF` found
  them.
- **Delegates need literal paths.** Messages to a hunt agent named
  `tickets/0983-<slug>.erg` and `tickets/0986-*.erg`; the author asked for
  literal paths. `erg-pr-merge` parses the close claim literally. The same day
  a review seat was launched with the literal prompt "PLACEHOLDER" and did no
  work.
- **Raid Phase 6 from background agents.** Both `/gaze` runs in raid 0984/0987
  escalated without reviewing: #1061 because the isolation guard blocked the
  review worktree and the panel had no Agent tool (0853); #1060 on the 15-file
  breaker, which no planning phase had counted. Both merged on author decisions
  with the review evidence recorded in a PR comment; filed as 0990.
- **Adjacent `Blocked-by` lines.** #1061 and #1060 each closed a blocker of
  0985, editing neighbouring header and log lines; after the first merged the
  second went DIRTY, and GitHub ran no checks on it, so its queued auto-merge
  showed only "pending" until the author asked. Resolved by rebase, dropping
  both header lines and keeping both log lines.
- **Bare `pytest` on PATH** is a pipx install without PyYAML: one test failed
  for two reviewers on a first run and passed 20/20 under `python3 -m pytest`,
  which `make check` uses.
- **Hermetic tests and the checkout.** idh tests faked `HOME` but ran from the
  real checkout, whose untracked private-skill symlinks made manifest entries
  FOREIGN: red in the primary checkout, green in CI and worktrees. Fixed by
  running from a copy of the tracked files (0989, PR #1064). Other tests still
  fake `HOME` while loading code from the checkout and pass; reported, not
  ticketed.

## Sources

- projects/-home-haduong--claude/memory/feedback_config_block_needs_an_end_marker.md blob 0d525511cdd4dffd88d8537b0383fb3cc640a56b
- projects/-home-haduong--claude/memory/feedback_inline_secret_persists_in_allow_rule.md blob 4b54e3fbd88cd2d018627b6eaa56212ff144a42e
- projects/-home-haduong--claude/memory/feedback_remote_probe_stdin_is_the_script.md blob 20f81529dc7586656a36a4b8605bb526c3f6f518
- projects/-home-haduong--claude/memory/feedback_grep_find_are_shell_functions.md blob 30c86aeb2f08025ff8e9995980d8a7e57422bca1
- projects/-home-haduong--claude/memory/feedback_hand_delegates_literal_paths.md blob 24eb88acb34f3fb7ae324f7a66fc83bd476729cc
- projects/-home-haduong--claude/memory/feedback_raid_gaze_escalates_from_an_agent.md blob 573a82ce2292938d734d81828c4d0b30cb64d49e
- projects/-home-haduong--claude/memory/feedback_adjacent_blocked_by_lines_conflict.md blob 68dc10a6f001da35a325d5317829c63e341e3741
- projects/-home-haduong--claude/memory/feedback_pipx_pytest_looks_flaky.md blob 0aa64e9d6a27186e9cc3be510a5e47d42293a314
- projects/-home-haduong--claude/memory/feedback_hermetic_test_rebase_home_prefix.md blob f9738523b277495dd4cedfc7610fe4f18f07a138

## Disclosed gaps

- Only these nine notes were examined; the other legacy notes of that session
  (e.g. on the guard reading written content) were not re-checked here.
- Folding these facts into `topics/` is left to the next dream run.

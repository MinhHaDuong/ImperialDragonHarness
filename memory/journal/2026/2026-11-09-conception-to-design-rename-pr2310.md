# 2026-11-09 — conception/ renamed to design/ (ticket 1477, PR #2310)

Context: author decision of 2026-11-09; 15 per-project alignment tickets wait on the
harness rename. Raid 632b19, single-ticket wave, base 24ebc840 then 72b65670 (annotation).

Events:
- Imagine (sonnet) and a Blind-Spot pass (opus) ran before the plan. The Blind-Spot pass
  found the 2026-10-27 docs/→conception/ journal (PR #1744) as the playbook, and that the
  memory-v8 relocation test link-checks frozen journal and evidence files, so the old-path
  mapping in `tests/test_memory_v8_pilot.py` and `tests/test_dream_v8.py` had to chain
  docs/X and conception/X to design/X rather than be sed'ed.
- Execute (opus, hunt inline): two planned commits (45d1a639 move + `.gitignore` swap,
  571da5a0 sweep) plus two unplanned: a third link checker, `tests/test_memory_v8_smoke.py`,
  reads a frozen journal link and needed the same mapping (found by `make check`, not by
  the plan); and hunt's rebase onto origin/main rewrote the raid annotation commit, so the
  executor reset and merged origin/main instead to keep 72b65670 an ancestor.
- Four `make check` failures came from running with `TMPDIR` inside the worktree, which put
  "outside a repository" tests inside one; they pass with `TMPDIR=/tmp`.
- verify-adherence's semantic seat ruled the kept `adapters/codex/hooks.json:2` string
  blocking before the PR body listed it as a deliberate remainder (the string is part of the
  trusted Codex hook definition); gaze (self + gpt-6.1-sol red team) and the gate accepted it.
- Byte-compare: identical blob ids for all 312 files; `--summary -M100%` showed renames only.
- Gate round 1 APPROVED in 4m31s on tip 7a06c2f3; merge 24s; main d1653111.

Decisions recorded: no redirect README or symlink; `projects/` untouched (ticket 1480);
transitional `design/ or conception/` wording for the editorial-brief glob and the gaze
prose panel, to drop when the alignment tickets close (check around 2026-11-23); the
"projects/ registry" item of the ticket was vacuous (nothing names the harness conception/).

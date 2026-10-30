# Author rulings of 2026-10-30, and the memory-design discussion (input for 1350)

Context: an interface session on 2026-10-30 (after the yawn/molt sweep,
PRs 2028-2041) carried several author rulings and a design discussion on
the memory subsystem. Roar did not run on PRs 2035-2041; this entry records
them. Related entries: 2026-10-30-gate-record-lost-shared-ref-rewind-1366.md,
2026-10-30-push-by-commit-id-exit-code-1366.md,
2026-10-30-python-tool-baseline-github-runner.md.

## Rulings (decided)

- **KISS on 1366.** Asked whether the 1366 fix was KISS, the author had the
  ls-remote read-back removed (PR 2035); the commit-id push stays.
- **Rules carry principles; detail goes to memory.** The author declined a
  git.md wording that exempted commit-id pushes: "That level of details
  belong to memory" (PR 2036 holds the detail).
- **No explicit forge dependency in rules.** PR 2037 replaced PR with merge
  request, removed the `gh` example, and replaced coding-python's "exotic"
  (defined against GitHub's runner image) with a principle readable without
  memory; the GitHub facts went to memory (author's option c).
- **Memory is jurisprudence**, not décret d'application (author's correction).
- **The government memo is doctrine, under cooldown.**
  `conception/2026-10-30-harness-government.md` (PR 2040) was accepted as
  doctrine: AGENTS.md as constitution, `rules/guards.md` as ordre public
  with an enforcement column, a three-chamber court for smelt, registries of
  dated facts beside case law, MOA/MOE. The author asked for a cooldown
  before any implementation ("It is easy to be overenthusiastic about a
  metaphor"): ticket 1369 (Fable and GPT-6 Astra reviews in fresh sessions,
  a KISS review, then the author's needs-vs-wants triage). Nothing is
  implemented from the memo before 1369 closes.

## Memory-design discussion (open input for 1350, not decisions)

Statements by the author:
- Memories about the user should be separated from memories about projects.
  The harness, padme and doudou are special projects; doudou has no repo.
- The user wears a professional and a personal hat; the author's agenda
  separates Work, Health, Social and Home (Home includes finances).
- Tasks, todos and meetings live in the agendas, not in memory. Agents should
  know the electronic agenda on Nextcloud (read and write) and the paper
  agenda, and reason with care for their mess and incompleteness.
- Host memories are local and should not sit in a potentially shared harness
  project (at least gitignored).
- Imagined by the author: a host-memory repository without upstream that
  propagates peer to peer.
- Agents need facts, not just preferences.

Points raised in the session, not ruled:
- Gitignored files are invisible to worktree sessions, so host memory belongs
  outside any repo (an absolute path such as `~/.local/state/idh/host-memory/`).
- A peer-to-peer git repo (per-host folders, pull-only sync, opportunistic at
  session start) would also be the second copy now that `/home/haduong` has
  no snapshots; it could carry the user store under `user/`.
- Personal-domain data (Health, Home finances) should stay out of every
  repo-backed store; the user store could hold only a map of the systems of
  record plus the author's conventions and care rules.
- The 2026-10-29/30 census found Claude Code almost never reads repository
  memory on demand (padme and doudou), so a new store works only if its
  small index is loaded at session start.
- Facts age by going stale and need a date and a probe; case law ages by
  being superseded.

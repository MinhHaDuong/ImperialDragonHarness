# Harness ↔ project directive coherence audit — 2026-09-24

Scope: the harness rules (`rules/`), skills (`skills/`) and startup scripts,
against each project's `AGENTS.md`, `.claude/rules/`, `.claude/skills/`,
`.claude/settings.json` and harness manifests (`rules-map.toml`,
`.knowledge.toml`, `.idh-checks.json`). Eleven repositories, audited from
fresh clones at their default-branch tips of 2026-09-24 ~06:00Z (cloud session;
the author's machine and the parent `~/CNRS/AGENTS.md` were not inspected).

Method: read every project directive, compare it against the governing harness
instruction, verify the claim mechanically where possible (YAML parse, `erg`
invocation, file existence, byte diff of vendored copies), then cross-check
open and recent PRs and branches for work already in flight.

Tracker: `tickets/0956-*.erg`. Each finding below names its child ticket.

## Result

Mostly coherent. The 2026-09-23 "cut the harness copy" sweeps (climate #1469,
#1470; aedist #1172, #1173; IDH #991, #996) left repos holding only their
specifics. Remaining: five direct contradictions, six tensions, six stale
references or broken artifacts. corpus-access-bench, polycentric_activity and
gavard-schoch carry no local rules that could conflict.

## A. Direct contradictions

| # | Where | Conflict | Status / ticket |
|---|---|---|---|
| A1 | climate `.claude/rules/keystore.md`, `AGENTS.md`, `Makefile` | Describe the harness `bash-env.sh` as applying the `KEYS=` selection; since 0942–0945 it refuses `KEYS` and reads no provider file. | Fixed by climate PR #1478 (ticket climate/1477). |
| A2 | aedist, gavard-schoch, polycentric `tickets/AGENTS.md:38` | "On ID collision, renumber to the next free ID" — the race climate `rules/git.md` documents (0384→0385→0386). Current text defers to `erg integration`. Three distinct `erg` builds in use; aedist's 2026-09-10 binary refresh did not upgrade the text. | Child tickets per repo. |
| A3 | climate `.claude/rules/coding.md:22` | "Formatter strips unused imports" vs harness `coding-python.md` and `lint-on-edit.sh:40` (`--unfixable F401,I001,UP`). Stale. | climate child. |
| A4 | aedist `AGENTS.md:60` | `/raid` "never defers for human input" vs harness escalation ladder (step 5 ask the author) and `/raid` returning intent changes to the author. | needs-human. |
| A5 | swz `AGENTS.md:177` vs harness `/raid` Phase 7 | A lane never merges, even its own PR; `/raid` merges APPROVED PRs. Local wins by precedence, but `/raid` cannot see it. | needs-human. |

## B. Tensions

- **B1** climate `check-reviews.sh` requires ≥2 review cycles by default while `AGENTS.md` caps at two rounds: every standard PR needs exactly two, even a clean one. Harness `/gaze` allows one retry; aedist up to three. — needs-human.
- **B2** harness `on-start.sh` imposes worktree isolation on every project; livre works directly on `main` (`bgIsolation: none`). Harness `git.md` exempts manuscript prose, the hook text does not. — needs-human.
- **B3** branch naming `t{N}-short-description` (climate) vs `t{N}-{pid}` (harness `claude-code.md`). Below the severity floor; noted only.
- **B4** climate `rules/git.md:12` "`main` is unprotected" vs harness `git.md` "no direct-push path". Verify forge protection; fold into climate child.
- **B5** swz `session-start.sh` uses `pip install` vs harness "always `uv sync`". Defensible (no uv project); below floor, noted only.
- **B6** aedist `scripts/quickpr.sh` enables forge auto-merge on PRs that may carry `tickets/`; harness `git.md`: a direct forge merge skips `**Ticket:**` close claims. — needs-human (keep, guard, or retire).
- **B7** climate `rules/architecture.md` scoped `paths: "**/*"`: 277 lines effectively resident, outside any harness budget test. — climate child (scope it).

## C. Stale references and broken artifacts

1. climate `rules/coding.md:13`, `rules/state-roadmap.md:9` point to `~/.claude/rules/coding.md` and `state-roadmap.md`; now `coding-python.md` and `state.md` (no ROADMAP coverage).
2. Tracing-Kieu and fuzzy-corpus `.claude/settings.json` PostToolUse hook runs `tickets/erg validate tickets/`, which errors on a directory: tickets are never checked. Use `erg check tickets/`.
3. livre `verif-liens/SKILL.md:3` frontmatter fails to parse (unquoted `Réseau requis : c'est`) — the case `rules/authoring-skills.md` names. Other project skills are unquoted but parse.
4. livre vendors `index-source` under the harness name, differing only in the script path; will drift. Vendoring may be deliberate (cloud sessions have no `~/.claude`). — needs-human.
5. livre `AGENTS.md:5,8` says "Pas d'IDH" yet uses harness skills and `rules-map.toml`, and names a non-existent `deep-research` skill; `rules-map.toml:5` says the doctype/lang bodies do not exist — they do.
6. Harness: `on-start.sh:6-7` still says `.env` secrets reach bash via `BASH_ENV`; `rules/README.md` says `tickets/AGENTS.md` reaches sessions via `@tickets/AGENTS.md` in `CLAUDE.md`, true only of the harness itself.

## PRs and branches in flight (verified 2026-09-24 ~06:30Z)

- climate #1478 (draft) fully resolves A1; no regression found (`.env` settings still reach Python via `uv run --env-file .env`). Leaves B4's line untouched.
- aedist #1175, Tracing-Kieu #171, IDH #997 (merged 05:50Z): consistent. IDH #997 filed ticket 0955 only; when implemented, `bash-env.sh` refuses credential-shaped names — no tracked `.env`/`.env.example` carries one today.
- Nothing in flight touches A2–A5, B or C.
- Stale IDH branches `memory-proportionality`, `t-orphan-process-detection`, `t0802-perch-adapters`, `t0425-typo-fine-finition`: none touches an affected surface. Ancestry unprovable from a shallow clone; left in place.

## Preconisations, ranked

1. Land climate #1478.
2. Upgrade `tickets/AGENTS.md` and `tickets/erg` in aedist, gavard-schoch, polycentric, Tracing-Kieu, fuzzy-corpus with `erg init` from the harness build; fix the two `validate` hooks.
3. Climate stale-rule cleanup (A3, C1, B4, B7).
4. Livre mechanical fixes (C3, C5).
5. Harness stale comments (C6).
6. Author decisions: A4, A5, B1, B2, B6, C4.

Structural lesson: adopters refresh the `erg` binary without re-running
`erg init`, so the conventions file silently lags the tool. The upgrade step
is `erg init`, not a binary copy.

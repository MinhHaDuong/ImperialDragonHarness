# Docs visit: first global read of the doc set (2026-10-29)

Date: 2026-10-29
Project: ImperialDragonHarness

Input: the whole doc set per `skills/harness-doctor/references/docs-visit.md`, read at commit 35b693cf (base 08cd9ec1 plus the docs-visit reference): seven root docs, `rules/`, the `conception/` index, and the skill references (38 files, checked by grep for restated facts and by title against role, not every line). Not read in full: coding-bash, coding-python, manuscript-build, zotero, prose/*, doctype/*, lang/*. Started by raid 94edd2 under ticket 1335.

Probes and controls:
- Reading pass, one Claude Opus agent, read-only. Control fired: it flagged `conception/README.md:1` still titled `# docs/` after the docs-to-conception move.
- Path-existence sweep over the doc set: 27 hits, all dismissed. Breakdown: 13 rules-relative paths, 3 from other repositories, 2 skill-local, 7 placeholders or runtime paths, and 2 fragments. Its own control is the `RTK.md:30` dead pointer it found.

Findings above the floor (home rule, `rules/workflow.md` § Autonomous action): none. No ticket filed.

Fixed inline (below floor, commit 24e4827b):
- `conception/README.md:1-3`: retitled `conception/`; says the index is partial.
- `RTK.md:30`: the pointer to an untracked CLAUDE.md now names `rtk --help`.
- `CONTRIBUTING.md` § Skills catalog restated `AGENTS.md:30-41` and had lost the order clause. It is now a pointer, and AGENTS.md keeps the private-symlink fact.
- `rules/README.md:84-85` repeated `:74-75` (adapters skip claude-code.md). Deleted.

Below the floor, reported, not edited (priced proposals):
- B. `rules/workflow.md:30-33` sends worktree naming and the `/hunt N` exception to `rules/claude-code.md:18-30`, which Pi and Codex adapters skip (`rules/README.md:74-75`). Consequence: a Pi or Codex session can create a worktree before `/hunt N` and orphan it. Molt reclaims it, so nothing breaks or corrupts. The self-presentation line is also stated at both `workflow.md:33` and `claude-code.md:32`. Proposal: move the naming table, the hunt exception and the opening line into workflow.md. About 15 resident lines; about 30 agent-minutes and 5 author-minutes; odds 0.8 that it removes the orphan path. Recommended first. Unverified on a live Pi or Codex session.
- A. `skills/harness-doctor/SKILL.md:107-109` cites the floor as "misleads a model into a wrong act". The home `rules/workflow.md:179-180` says "bites the science". The doctor ticketed on its own wording at the 2026-10-29 triage visit. Author's call: label it as the doctor's reading for a tooling repo, or amend the home rule. About 2 author-minutes.
- C. `rules/git.md:30-36` restates roar step 10 (`skills/roar/SKILL.md:221-230`) in detail. It agrees today and costs resident context in every session. Proposal: cut it to one pointer line. About 10 agent-minutes; it is a resident rule, so the author decides.
- G. `rules/state.md:12-20` requires a `## North star` section in STATE.md. The north star lives in `ROADMAP.md:5-8` instead. Author's call on which side moves; about 5 minutes.
- `rules/README.md:45` says `tickets/AGENTS.md` is @-imported by the harness CLAUDE.md. That file is untracked, and `adapters/projections.json:188` shows a link instead. Cause not checked.

Revisit condition: the next docs visit, which lair step 16 suggests 30 days from this entry or when a ROADMAP workstream closes. Check whether B, A, C and G were decided, and rerun the path sweep.

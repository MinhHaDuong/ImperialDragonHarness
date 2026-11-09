# Imperial Dragon Harness — State

Last updated: 2026-11-08T08:22Z

Live counts: `erg ready tickets/` · `erg list` · `/dashboard`.

## Handoff
Attribution #1423/#1425 unresolved; do not infer missing identities.
Structured review constraints remain deferred in #1465; #1377 is retired. Raw failure retention is delivered separately (#1464).
Main-update guard (1045): enforce on padme and doudou since 2026-10-27 16:20Z (1268 whitelists git's pack-refs). Watch window closed 2026-11-03: no refused row on doudou; padme's journal not read. Back out with `git config --unset idh.mainGuard`.
Merging: the before-merge record is the cheap set; the main-update hook starts the full after-merge run (1226, 1265).
Review flows (design/2026-10-27-review-merge-flows.md): F1 default, gaze answers and verify-gate verdicts on `refs/notes/review`, pushed at landing, the PR comment a pointer; F2 (local gated merge) only for repositories with no origin remote. Web sessions read and relay-publish (outcome B).
DOIfetch: not installed by `idh install` (1343); the zotero skill runs it on demand with `uvx` at the pinned tag `v0.2.0` (unsigned, author ruling 2026-10-29), with open sources first and shadow sources as fallback.
Agent credential (1196): Claude Code shells use a fine-grained PAT through `~/.config/gh-agent` (no admin; owner login for the author's acts). Codex and Pi get it through the `codex`/`pi` wrappers in `scripts/shell-init.sh` (1284); launches outside them stay on the owner login. `refs/notes/*` is not protected by the forge ruleset.
Resident rules (ruleset review 2026-11-01): the budget counts loaded text, HTML comments stripped (cap 15186); they reach Codex and Pi via generated `~/.codex/AGENTS.md` / `~/.pi/agent/AGENTS.md` (1424); `pi --print` needs stdin closed.
Model-service transmission authorization prints in every session's start context (PR #1783); whether Codex's managed approval reviewer reads it is untested.


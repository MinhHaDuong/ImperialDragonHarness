erg `update` is an alias of `sync`; molt step 0.7 described it wrongly (PR 1732)

Date: 2026-10-27
Project: ImperialDragonHarness

**Context.** The author asked for four molt/yawn changes, one of them "erg update is now erg sync", and later added that this was an alias from an erg CLI rename and the details might be wrong. Molt step 0.7 ran `erg update` before step 1, describing it as refreshing the installed `~/.local/bin/erg` and never the committed `tickets/erg`.

**Observations.** `erg update --help` prints the `erg sync` help. That help states sync replaces the vendored `<ticket store>/erg` from the project's origin and never the executable that invoked it. The project's git-erg memory note says the same of `update` before the rename. `housekeeping-git.sh` and `ticket-sweep.sh` already ran `tickets/erg`; only `project-state.py` preferred the `erg` on PATH. In a scratch repo, a working-tree file rewritten to match the target branch byte for byte made `git switch -c hk origin/main` refuse with "local changes would be overwritten" (exit 1). Gaze reproduced the refusal independently.

**Outcome.** A rename would have kept a false claim and a pre-step-1 write that blocks step 1 in a lagging checkout. Step 0.7 now runs nothing and forbids `erg sync` and `--upstream` in a sweep; `project-state.py` prefers the vendored binary (PR 1732, merged at d2145e00).

**References.** PR 1732; commit 49e3d253; `skills/molt/SKILL.md` step 0.7; `scripts/project-state.py` `ticket_state`.

# Imperial Dragon Harness — State

Last updated: 2026-10-29

Live counts: `erg ready tickets/` · `erg list` · `/dashboard`.

## Handoff
Attribution #1423/#1425 unresolved; do not infer missing identities.
Original doc-refresh snapshot pushed as WIP; newer implementation is merged.
Main-update guard (1045): enforce on padme and doudou since 2026-10-27 16:20Z (1268 whitelists git's pack-refs; 1180 closed). Watch the journal for refused rows until 2026-11-03; back out with `git config --unset idh.mainGuard`.
Optimistic merge (1226) closed: cheap before-merge set; the main-update hook starts the full after-merge run (1265).
Gaze rebuild (1143) closed, with its follow-ups 1100 and 1213 and the review-brief successor 1225.
DOIfetch: not installed by `idh install` (1343); the zotero skill runs it on demand with `uvx` at a pinned ref, open sources only. DOIfetch itself is slimmed to `requests` (its 0005) and is becoming an importable package (its 0006, 0008).
Agent credential (1196): Claude Code shells use a fine-grained PAT through `~/.config/gh-agent` (no admin; owner login for the author's acts). Codex and Pi shells get it through the `codex`/`pi` wrappers in `scripts/shell-init.sh` (1284; 403 measured from both); launches outside the wrappers stay on the owner login. `refs/notes/*`, `refs/notes/gate` included, is not protected by the forge ruleset.
Forge-less review (tracker 1252, closed 2026-10-28 after integration review PASS): every child merged — adapter and callers (1271, 1272), notes review (1273), verify-gate on notes (1274), local gated merge (1275), landing route (1280), end-to-end F2 test (1276), review-notes hardening (1281). Flows ruled by the author (conception/2026-10-27-review-merge-flows.md): F1 default (notes review + forge PR merge); F2 only for repositories with no origin remote; no setting. Web legs (1277) ran: both outcome B (read, relay publish). 1282 (review-notes lock) and 1291 (gate reads without pushing) merged in raid 2026-10-27b.
F1 review evidence on notes (tracker 1298; children 1299, 1300, 1301): gaze's answer and verify-gate's verdict live in `refs/notes/review` for PR units too, written locally and pushed at landing; the PR comment is a one-line pointer (`/gaze review on notes: <id>, verdict <V>`, `/verify-gate round=<n> verdict=<V> ...`), best-effort. Readers (verify-gate, raid polling, `attribution_record.py --seats-pr`, roar capture) read notes; merged PRs gazed before the switch keep their comments as read-only history, open ones are re-gazed. Web sessions stay outcome B (read, relay publish; entries leave by export/import).
Raid 2026-10-27b: gaze and verify-gate run `scripts/touched-tests.py` (1283); after-merge runner reports a stale venv as `environment` (1288) and builds the forge only on red; main_sweep lists crashed-on tips (1293); headless seats declare a reach line (1290); attribution writer lines append before reviewers (1286). Gaze cross-family default (1287, PR #1836; no further normaliser widening) and stopguard measure (1294, PR #1832) merged 2026-10-27.
Model-service transmission authorization now prints in every session's start context (PR #1783); whether Codex's managed approval reviewer reads it is untested.
Doc propagation (1333, PR #1945): roar step 6 names its contracts and documents, `tests/test_root_doc_paths.py` checks root-doc paths and make targets, lair step 10 refreshes ROADMAP facts. Next: harness-doctor weight loss (1334), then a whole-docs visit lair suggests (1335, blocked by 1334).

## Next session (from 2026-10-29)
1. Audit the fifth smelt, PR #1975 (unmerged; author acceptance): spot-check superseded marks, the new topic merge-flow-and-review-evidence.md, and the 206-line blob ledger against the 193 entries.
2. Rule the four conflicts it flagged (smelt report memory/smelts/2026-10-29-fifth-hoard.md once merged; rules are the author's):
   - rules/README.md says tickets/AGENTS.md is @-imported by the harness CLAUDE.md, removed 2026-10-19.
   - rules/git.md stash ban "in a shared checkout": does it cover a session's own worktree (stash stack is repo-global)?
   - Severity floor wording ("misleads a model" in harness-doctor vs "bites the science" in workflow.md); North star required by rules/state.md but kept in ROADMAP.md.
   - Night-mode "escalations go to Fable" memory vs "author's calls by right are never delegated".

# Imperial Dragon Harness — Roadmap

The reference clone is `~/.agents`. The harness must work from any checkout
location, with runtime resources registered through their native mechanisms.
Tickets hold acceptance criteria; [STATE.md](STATE.md) holds the resume point.

## Priorities

| Workstream | Next work | Completion evidence |
|---|---|---|
| Portable installation — 0999 | Complete; parent closed after integration review in #1104. Native packaging and opt-in host setup are future design work | Fresh/relocated registration, preserved profiles and runtime smoke landed in #1091; integration review recorded in #1104 |
| Memory v8 — 0909 | Convention 0911/inventory 0917 (#1102), pilot 0920 (#1109), capture 0988, dreaming 0910/0916 and acceptance trials 0918 all delivered — trials verdict **No global rollout** ([evaluation results](docs/memory-v8/evaluation-results.md)). Remaining: 0913 — per-project migration and legacy retirement in adopting projects | Adopting projects migrate to v8; replaced mechanisms retired per project |
| Reviewer attribution — 1004 | Record capture, backfill, read surfaces and teardown are delivered through PR1222; this Roar bundle closes 1032/1009. Next: 1004's separate original-criteria integration audit | Explicit 33-merge coverage, fixed-line records for reviewed PRs, retained typed runtime mask and supported unreviewed classifications; surfaces report scores and correlation |
| Runtime policy — 0974/0938 | Continue open 0974 routing and quota decision; named portable profiles (0938), detached child reviewer pattern (1017) and spawn trust (1021) are delivered. The 0980 fixed-seat audit closed WONTDO in PR1222 | Runtime mappings and capability limits tested; spawn success implies the agent exists |
| Verification workflow | 0990 background Gaze verdict, 0902 tiers and 0879 malformed-log handling are delivered; 0205 and its seven trial dispositions are historical evidence | Reproductions fail before fixes and pass afterward |
| Claude adapter — 0887 | 0887 plugin skills-dir: what it can carry, measured; activated 2026-10-05 — plugin is the single hook source, absence-mode check enforces it | Fresh-session guard evidence with preserved user configuration |
| Raid annotations — 1016 | One shared base commit for wave annotations; branches must not fork divergent annotation copies | Wave annotations converge on one base commit |
| Zotero interface — 1018 | Consolidation: one `zotero` skill with verbs as arguments, backend `scripts/zotero.py`; `index-source` absorbed as import-of-URL. Hygiene rider: 1020 stale `~/.idh` sweep (scripts/, agnostic gate comments) — raid-sweepable any time | One `zotero` skill in the catalog, `index-source` gone, catalog in sync; no live `~/.idh` references |

Brood 0888 is delivered in PR #1187: explicit post-Dream project improvements,
local proofs of concept and nomination-only harness handoff; the separate harness
implementor evaluates, generalizes and validates. See [the evaluation](docs/memory-v8/brood-evaluation.md).

The academic skill integration is complete. Optional memory experiments remain
deferred until evidence justifies them: 0375, 0908, 0912, 0914, 0915,
0919, 0921, 0922, 0925 and 0926 carry the `deferred` label and stay out of the
trains until evidence reopens them. See `erg ready tickets/` for ready work
and `erg list tickets/` for the complete open set.

## Installation boundary

`~/.agents` is the default location, not a path API. Runtime profiles stay
independently owned. The old relocation/cutover tickets 0978 and 0986 are
closed WONTDO; their probes remain historical evidence.

See [the installation guide](docs/idh-install-strategy.md) for the current
installer limits and the target registration contract.

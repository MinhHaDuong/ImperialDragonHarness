# Imperial Dragon Harness — Roadmap

The reference clone is `~/.agents`. The harness must work from any checkout
location, with runtime resources registered through their native mechanisms.
Tickets hold acceptance criteria; [STATE.md](STATE.md) holds the resume point.

## Priorities

| Workstream | Next work | Completion evidence |
|---|---|---|
| Portable installation — 0999 | Complete; parent closed after integration review in #1104. Native packaging and opt-in host setup are future design work | Fresh/relocated registration, preserved profiles and runtime smoke landed in #1091; integration review recorded in #1104 |
| Memory v8 — 0909 | Convention 0911/inventory 0917 (#1102), pilot 0920 (#1109), capture 0988, dreaming 0910/0916 and acceptance trials 0918 all delivered — trials verdict **No global rollout** ([evaluation results](docs/memory-v8/evaluation-results.md)). Remaining: 0913 — per-project migration and legacy retirement in adopting projects | Adopting projects migrate to v8; replaced mechanisms retired per project |
| Reviewer attribution — 1004 | 1004 tracker → 1005 record template + roar capture → 1006 backfill hook / 1007 read surfaces → 1009 teardown; the chain gates on 0913 | Attribution records replace seat coaching; surfaces report scores and correlation |
| Runtime policy — 0974/0938 | Apply the adopted model/effort policy (0974); replace inline fork roles with named portable agent profiles (0938); documented detached-CLI reviewer pattern for child sessions (1017); 0980 reviewer-seat audit; 1021 silent spawn failure | Runtime mappings and capability limits tested; spawn success implies the agent exists |
| Verification workflow | 0990 gaze verdict from a background agent; 0902 gaze tiers on diff size, never paths; 0879 malformed log lines (0205 closed 2026-10-03 — residual dispositions owned by 1009) | Reproductions fail before fixes and pass afterward |
| Claude adapter — 0887 | 0887 plugin skills-dir: what it can carry, measured; 0888 Imagine skill integration review and retrospective | Fresh-session guard evidence with preserved user configuration |
| Raid annotations — 1016 | One shared base commit for wave annotations; branches must not fork divergent annotation copies | Wave annotations converge on one base commit |
| Zotero interface — 1018 | Consolidation: one `zotero` skill with verbs as arguments, backend `scripts/zotero.py`; `index-source` absorbed as import-of-URL. Hygiene rider: 1020 stale `~/.idh` sweep (scripts/, agnostic gate comments) — raid-sweepable any time | One `zotero` skill in the catalog, `index-source` gone, catalog in sync; no live `~/.idh` references |

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

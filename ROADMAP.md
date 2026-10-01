# Imperial Dragon Harness — Roadmap

The reference clone is `~/.agents`. The harness must work from any checkout
location, with runtime resources registered through their native mechanisms.
Tickets hold acceptance criteria; [STATE.md](STATE.md) holds the resume point.

## Priorities

| Workstream | Next work | Completion evidence |
|---|---|---|
| Portable installation — 0999 | Registration child 1001 in #1091; dream helpers child 1002 in the memory session; native packaging and opt-in host setup remain | Fresh/relocated registration, preserved profiles and runtime smoke; separate memory-helper and integration reviews |
| Memory v7 — 0909 | Foundations 0911/0917, then pilot 0920–0923; root defect 0934 | Offline pilot, separate canonical/native stores and verified delivery before rollout |
| Host sync — 0988 | Decide memory-write ownership and surface blocked pulls | Sessions preserve notes and the harness continues to update |
| Runtime policy — 0974 | Apply the adopted semantic model/effort policy | Runtime mappings and capability limits are tested |
| Verification workflow | Resolve 0853/0990 background review, 0875/0940 hermeticity and 0879 log defects | Reproductions fail before fixes and pass afterward |
| Claude adapter — 0886/0887 | Reconcile live settings and activate plugin hooks without duplicate firing | Fresh-session guard evidence with preserved user configuration |

The academic skill integration is complete. Optional memory experiments remain
deferred until evidence justifies them. See `erg ready tickets/` for ready work
and `erg list tickets/` for the complete open set.

## Installation boundary

`~/.agents` is the default location, not a path API. Runtime profiles stay
independently owned. The old relocation/cutover tickets 0978 and 0986 are
closed WONTDO; their probes remain historical evidence.

See [the installation guide](docs/idh-install-strategy.md) for the current
installer limits and the target registration contract.

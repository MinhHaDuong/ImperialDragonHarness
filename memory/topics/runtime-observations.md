# Environment: runtimes, models and routing

Dated observations on named versions; unprobed current behavior stays unknown. Routing belongs to `skills/route/`;
no grid here. Rules loading per runtime: `rules/README.md` § Loading per runtime.

## Current guidance
- Claude Code levers (2026-09-10, v2.1.267): a skill's `model:` never reaches children; `Agent`/`Workflow` inherit the session model unless each launch passes a short token; `effort:` pins the child (none inherits; invalid rejected); `Workflow opts.effort` per-call; unreliable on pinned-default-effort models before 2.1.267. [levers][source1]. Codex `spawn_agent` honours `model`/`reasoning_effort` (2026-10-09); read the session header, not the self-report (0.161.0).
- **Rules reach every runtime** (re-probe 2026-11-01, sentinels): resident rules found in generated `~/.codex/AGENTS.md` and `~/.pi/agent/AGENTS.md`; conditional (`paths:`) rules wired for Codex and Pi (1424, measured on read/write/bash). All three runtimes load the project AGENTS.md and session-start hook. [ruleset review][source2]
- `pi --print` hangs on an open stdin; run with `</dev/null` — looks like a dead model, is not. [ruleset review][source3]
- Pi 1.4.0 reads skills from `~/.agents/skills` (PR 1690); agents projected to `~/.pi/agent/agents` (PR 2189, ticket 1426) with no `model:` line, so an unpinned Pi child takes the dispatcher's model (`routes.json:100` stale); padme's `code-reviewer.md` there is a FOREIGN file until removed. Pi also serves HF and paid doors via wrappers pinning provider and model (Albert cleared) ([wave 3][source4], [Albert][source5]).
- Headless `vibe -p` (2.26.0) works as a read-only gaze seat (`--enabled-tools read_file`); needs `</dev/null`. [1279][source6]
- padme's local LLM service is configurable and changes within days; never name llama.cpp or one model as "the" padme route (PR 2065). Strata v0.1.43 rejects `xhigh`, ignores `port`. [xfam][source7]; [switch][source8]
- Codex can supply an other-family gaze seat when the producer is another family; a usage-limit failure leaves none [1082][source9]; the headless door pins `model_reasoning_effort="medium"` (inherited `low` made luna seats refuse, 4/56 vs 0/81) [1365][source10]. `runtime.py wake` must not key on `CLAUDE_CODE_CHILD_SESSION` [verbs][source11].
- Author rulings: design for all three runtimes, none staged last (2026-10-21); the gaze orchestrator model changes only from arena data (2026-10-29).
## Hazards
- Pi loads only the first of `AGENTS.override.md`/`AGENTS.md`/`AGENTS.MD`/`CLAUDE.md` per directory; an unknown model gets another's settings — declare it (2026-10-07). The earlier Pi setup had no Agent tool: its raids ran inline, DEGRADED. `pi-haiku -p` hangs without `</dev/null`; pi defaults drift when the model is missing from enabled lists (PR #1390).
- Wrappers do not unset a caller-exported OpenRouter key (open, 2026-10-28). Vibe cannot report a provider-qualified model id; record it as runtime-masked, and a delegate's id only as it reported it.
- In a long session, `--help` or reload a helper before a mutating call (1307); never silence its output. Gaze run inside a coder returned self-only 5/5; explicit panel briefs fixed it (2026-10-27).
- The November raid exposed no served full model ID or verified effort in native contexts. Captures preserve runtime-masked state; requested launch pins are not observed identities. No extra provider purchase does not mean zero account cost [masked].
## Open questions
- Pi's 195-minute gaze on a local 27B (2026-10-03, one run): recur on the current model? Untested. Faster gaze orchestrator saving 20-30 s of ~3 min (40% odds): hypothesis. Padme's default model: the lineup changes within days; treat any named model as dated.

## Retired

- The named 2026-10-31 padme default: dated history; the service changes within days and current lineup was not probed here.
- “Codex runs the other-family seat” as an unconditional family claim: family depends on the actual producer and reviewer, not the runtime name.
- Previous Retired history stays in git; no old version observation was promoted into a current measurement.

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- Provenance: [source inventory](../../conception/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../conception/memory-v8/source-revisions.tsv).
- [First raid on pi](../journal/2026/2026-10-02-first-raid-on-pi-pr1153.md), [raid 0902](../journal/2026/2026-10-03-raid-0902-gaze-risk-band-pr1155.md), [raid 0938](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md)
- [Mistral 4 pi context](../journal/2026/2026-10-07-mistral4-pi-context-correction.md), [routing review](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md), [round two](../journal/2026/2026-10-09-routing-review-round-two.md)
- [PR 1390](../journal/2026/2026-10-14-raids-1080-1089-wrap-up.md), [Arena separation](../journal/2026/2026-10-13-arena-separation-and-force-merge.md)
- [Raid under Vibe](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md), [raid forge-less](../journal/2026/2026-10-27-raid-forge-less-and-guard.md)
[masked]: ../journal/2026/2026-11-07-raid-d35fb4.md

[source1]: ../feedback_subagent_model_effort_levers.md
[source2]: ../journal/2026/2026-11-01-ruleset-review-and-diet.md
[source3]: ../journal/2026/2026-11-01-ruleset-review-and-diet.md
[source4]: ../journal/2026/2026-11-01-raid-1f0534-wave3-pi-agents.md
[source5]: ../journal/2026/2026-10-28-pi-padme-albert-route.md
[source6]: ../journal/2026/2026-10-27-vibe-headless-seat-1279.md
[source7]: ../journal/2026/2026-10-31-cross-family-gate-dropped.md
[source8]: ../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md
[source9]: ../journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md
[source10]: ../journal/2026/2026-10-30-raid-70b3bc-codex-seat-effort-1365.md
[source11]: ../journal/2026/2026-10-28-raid-6530fd-runtime-verbs.md

## Fallback

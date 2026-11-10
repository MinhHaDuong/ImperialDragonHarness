# Environment: runtimes, models and routing

Dated observations on named versions; unprobed current behavior stays unknown. Routing belongs to `skills/route/`;
no grid here. Rules loading per runtime: `rules/README.md` § Loading per runtime.

## Current guidance
- Claude Code levers (2026-09-10, v2.1.267): a skill's `model:` never reaches children; `Agent`/`Workflow` inherit the session model unless each launch passes a short token; `effort:` pins the child; `Workflow opts.effort` per-call. [levers][source1]. Codex `spawn_agent` honours `model`/`reasoning_effort` (2026-10-09); read the session header, not the self-report.
- **Context ceilings** (author, 2026-11-09/10; 1497, 1499): `skills/route/ceilings.json` holds 230K by default, 450K for an interface session on Sol or Opus, 550K on Astra or Fable; workers, team leads and unattended runs keep 230K. Context length is the whole prompt. The status line prints `prompt NNNK` [2358][1499]. Open: whether an attended raid is an interface session, and what it may do at its ceiling [2365].
- **Context audit** (`scripts/trace-compact-audit.py`) reads Claude Code, Codex (`exec` held to the default, `cli` to its model's ceiling) and Pi (live and seat spool, spool at the default), and names the runtimes it read [2402][2407][2397]. `trace-stats`, `trace-friction`, `trace-wall-time` share the roots of `transcript_spool.py` [075f].
- **Rules reach every runtime** (re-probe 2026-11-01): resident rules in generated `~/.codex/AGENTS.md` and `~/.pi/agent/AGENTS.md`; conditional rules wired for Codex and Pi (1424). [ruleset review][source2]
- `pi --print` hangs on an open stdin; run with `</dev/null`. Pi 1.4.0 reads skills from `~/.agents/skills`; agents projected to `~/.pi/agent/agents` with no `model:` line, so an unpinned Pi child takes the dispatcher's model ([wave 3][source4], [Albert][source5]).
- Headless `vibe -p` (2.26.0) works as a read-only gaze seat; needs `</dev/null`. [1279][source6]
- padme's local LLM service changes within days; never name one model as "the" padme route (PR 2065). Strata v0.1.43 rejects `xhigh`, ignores `port` [xfam][source7]; [switch][source8]
- Codex supplies other-family gaze seats; a usage-limit failure leaves none [source9]; its headless door pins `model_reasoning_effort="medium"` [1365][source10]. `runtime.py wake` must not key on `CLAUDE_CODE_CHILD_SESSION` [source11]. A seat launched `-m gpt-6-luna` reported `gpt-6.1-sol` (2026-11-10) [45e1].
- Author rulings: design for all three runtimes, none staged last (2026-10-21); the gaze orchestrator model changes only from arena data (2026-10-29).
## Hazards
- Pi loads only the first of `AGENTS.override.md`/`AGENTS.md`/`CLAUDE.md` per directory; an unknown model gets another's settings. The earlier Pi setup had no Agent tool: its raids ran inline, DEGRADED. `pi-haiku -p` hangs without `</dev/null`; padme's `~/.pi/agent/agents/code-reviewer.md` is a FOREIGN file until removed. Pi defaults drift when the model is missing from enabled lists (PR #1390).
- Wrappers do not unset a caller-exported OpenRouter key (open, 2026-10-28). Vibe cannot report a provider-qualified model id; record it as runtime-masked.
- In a long session, `--help` or reload a helper before a mutating call (1307). Gaze run inside a coder returned self-only 5/5; explicit panel briefs fixed it (2026-10-27).
- Native contexts expose no served full model ID or verified effort; requested pins are not observed identities [masked]. A hook injected gaze memory notes into a Codex seat's review context (2351) [2351].
## Open questions
- Pi's 195-minute gaze on a local 27B (2026-10-03, one run): recurs? Untested. Faster gaze orchestrator (20-30 s of ~3 min): hypothesis. The audit's session counts differed from the design note's ad hoc scan; cause not investigated [1499].

## Sources

- Carried claims and adapted native provenance: [accepted sixth report](../smelts/2026-11-01-sixth-smelt.md), [fifth native annex](../smelts/2026-10-30-fifth-smelt-native-notes.md), and [sixth native annex](../smelts/2026-11-01-sixth-smelt-native-notes.md).

- Provenance: [source inventory](../../design/memory-v8/source-inventory.md); revisions in [source-revisions.tsv](../../design/memory-v8/source-revisions.tsv).
- [First raid on pi](../journal/2026/2026-10-02-first-raid-on-pi-pr1153.md), [raid 0902](../journal/2026/2026-10-03-raid-0902-gaze-risk-band-pr1155.md), [raid 0938](../journal/2026/2026-10-03-raid-0938-profiles-subsystem.md)
- [Mistral 4 pi context](../journal/2026/2026-10-07-mistral4-pi-context-correction.md), [routing review](../journal/2026/2026-10-09-routing-review-round-and-host-hygiene.md), [round two](../journal/2026/2026-10-09-routing-review-round-two.md)
- [PR 1390](../journal/2026/2026-10-14-raids-1080-1089-wrap-up.md), [Arena separation](../journal/2026/2026-10-13-arena-separation-and-force-merge.md)
- [Raid under Vibe](../journal/2026/2026-10-02-raid-853-937-979-1014-vibe-runtime.md), [raid forge-less](../journal/2026/2026-10-27-raid-forge-less-and-guard.md)
- Off the page, in its episode: stale `routes.json:100` [source4].
[masked]: ../journal/2026/2026-11-07-raid-d35fb4.md
[2358]: ../journal/2026/2026-11-09-roar-pr2358-interface-context-ceiling.md
[1499]: ../journal/2026/2026-11-10-roar-pr2391-context-length-tokens-ticket-1499.md
[2365]: ../journal/2026/2026-11-10-roar-pr2365-context-length-design-note.md
[2402]: ../journal/2026/2026-11-10-roar-pr2402-codex-reader-raid-3429da.md
[2407]: ../journal/2026/2026-11-10-roar-pr2407-pi-reader-raid-626455.md
[2397]: ../journal/2026/2026-11-10-roar-pr2397-audit-names-runtimes-read.md
[075f]: ../journal/2026/2026-11-10-roar-raid-075fa8-one-roots-definition.md
[45e1]: ../journal/2026/2026-11-10-roar-raid-45e130-fleet-audit-trace-runtimes.md
[2351]: ../journal/2026/2026-11-09-roar-pr2351-government-cooldown-review.md

[source1]: ../feedback_subagent_model_effort_levers.md
[source2]: ../journal/2026/2026-11-01-ruleset-review-and-diet.md
[source4]: ../journal/2026/2026-11-01-raid-1f0534-wave3-pi-agents.md
[source5]: ../journal/2026/2026-10-28-pi-padme-albert-route.md
[source6]: ../journal/2026/2026-10-27-vibe-headless-seat-1279.md
[source7]: ../journal/2026/2026-10-31-cross-family-gate-dropped.md
[source8]: ../journal/2026/2026-10-12-t1048-cycle3-speed-stage-and-production-switch.md
[source9]: ../journal/2026/2026-10-10-raid-1082-erg-pr-merge-pending-ci.md
[source10]: ../journal/2026/2026-10-30-raid-70b3bc-codex-seat-effort-1365.md
[source11]: ../journal/2026/2026-10-28-raid-6530fd-runtime-verbs.md

## Fallback

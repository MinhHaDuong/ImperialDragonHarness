kind: model-tournament
ticket: 1024 · cycle 2 closed 2026-10-06 · project: .agents (harness as assigned project)
arena: ~/arena · driver drive2.py · panel {gemini, grok, minimax} · 3 seats/leg

Model tournament cycle 2 completed on padme: 142/160 legs OK, all judged
3/3 (426 seats), 19 documented non-OK outcomes in three classes (DNF
time-cap 7200s: 0874-a, 0874-b3, 0333-j, 0211-k; VOID-EMPTY silent
abandon: b2-0333 [infra, pause kill, re-run below], c2-0470, j-0233/0452/
0874/1372, k-0452/0673/1372; DNF-PROVIDER: h x6, stealth/space-bunny-alpha
endpoint 404 since 2026-10-06).

Final numbers (quality median /30, median time, $/leg; elec 0.23 EUR/kWh x
600 W = 0.138 EUR/h, registered before the analysis): j GLM 5.3 Flash @high
27.0 but SURVIVOR-BIASED (5/10 legs, VOID on heavy tickets); b2 flash-next
IQ3_S @xhigh 26.5 on FULL 10/10, 30/30 unanimous on the killer ticket
(0333 re-run, 47 min, three perfect-10 seats); e3 Sol 6.1 @medium 25.0;
e2 Sol 6.1 @low 23.2 (STRICTLY DOMINATES e3 paired: quality 5-5, faster
9/10, cheaper 10/10); d2 Opus 5.5 @low 22.8 (parity with @medium paired
at 1/3 cost, both efforts crater on different tickets); l Luna 6 @medium
21.8 at 4 min and 0.028 $ (paired parity with the old locals and with b3
Q2_0 at median 0.0; clearly under b2 at -4.5); c/c2 false-completion
family ~9, banned. Pre-registered H1 (Sol @low dominates Sonnet @medium
on quality/speed/cost) REFUTED: quality 4-6, Sonnet faster 9/10. Cross-camp:
b2 beats e3 paired 7-2 at 1/3 the cost, 5x slower.

Four harness warts found and dispositioned (all in the 1024 journal):
(1) runner's unloaded-padme assertion applied to hosted arms too -> 30
legs died pre-pi during local-lane overlap; fixed, gated kind=="local";
(2) MAX_ATTEMPTS=2 is LIFETIME not per-pass -> re-passes silently no-op on
legs that burned 2 attempts; worked around via runs-void archiving of
infra-only attempts, code fix ticketed 1053; (3) a load1 NameError from
the fix to (1) crashed hosted legs at the record step (post-pi), destroying
worktrees via the finally; caught same day, 2 legs archived+rerun; (4)
judged-ness was "judges dir exists" not "3 seat files" -> seat failures
never retried; fixed as judged3() + idempotent judge.py seats. Also: a
detached-HEAD worktree (branch given as a remote ref) silently discarded
a pushed fix commit when the worktree was removed — redone on a proper
branch; and git worktrees holding a branch block its rename (the pause-
kill's stale tournament/0333-b2 branch needed worktree removal first).

Provider events: OpenAI hit "no credits remaining" mid-repass (8 legs
blocked, author topped up, legs re-run); OpenRouter key hit its monthly
40 USD cap and stalled the ENTIRE judge panel (all seats route via OR);
author raised the key cap 40->60. SpaceBunny died (free endpoint gone).

Products: skills/route (grid + routes.json + triage + clusters +
effort-as-identity; grid moved to grid.json per the model-rightsizing
policy) and skills/arena (replay procedure + the warts) merged via
#1228; AGENTS.md profile doctrine (capability class and effort orthogonal,
frontier = one-shot deep problems, intensive = the Qwen 3.8 default
strategy) merged via #1225; grid cell final via #1236. Follow-up tickets
1046-1058 (report, blog, cycle 3, HW-v2 window, 262K rerun, scouting,
live routing, drive2 v2, task-level routing, decorrelation axes,
judge sensitivity). Cycle 3 pre-declared: locals @medium vs hosted
qwen3.8-flash (lineage twin, served production vs open-weights preview —
flash-next is NOT served anywhere as of 2026-10-06), DashScope-intl
direct, --expert-profile-save enabled on the Strata arms.

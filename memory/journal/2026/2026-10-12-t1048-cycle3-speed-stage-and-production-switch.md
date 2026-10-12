# 2026-10-12 — ticket 1048: cycle-3 speed stage, padme production switched to Flash-Next

Context: the author revised cycle 3 of the model tournament in one session,
qualified the candidates on padme (RTX 5070 Ti + RTX A4000, Strata v0.1.43),
froze the pre-registration and launched it. Mid-cycle the author re-scoped to
three speed tickets (0470, 0532, 0452), then decided padme's production backend.

Events:
- Qualification at ctx 131072 (needle at 114K tokens): Gemma 4 26B-A4B Q4 fit
  the A4000 only with `-ub 128`; its NVFP4 build needed `--n-cpu-moe 3` on the
  5070 Ti; Gemma was then cancelled by the author and the NVFP4 weights deleted.
  Mellum 2.1 Q8_0 fit both cards but failed recall at 114K twice (section
  enumeration, then a word loop).
- The Strata config rejects `reasoning_effort: "xhigh"` (accepts `high`), and
  `serve/server.py` ignores the config's `port` (default 8095). Expert-profile
  preload off is not a serving configuration in v0.1.43.
- Launch: the local lane was announced as running twice while failing. First
  the server listened on 8095 while the driver waited on 8081; then
  `start-arm.sh` refused the arm's own resident server when `runner.py` called
  it again. Four 0470 attempts were archived as infra voids. Hosted arms ran
  their tickets' tests on padme, lifting load to ~12 and tripping the local
  lane's 2.0 load guard; the lanes were then run one after the other.
- The DashScope free quota (1M tokens, qwen3.8-flash) was exhausted by two
  0470 legs; billing continued on the card.
- Mellum: 0470 BLOCKED (panel 17/30, Flash-Next arms 29-30), 0532 and 0452
  empty submissions; 0 of 9 edits applied on 0532, four with LaTeX
  backslashes unescaped in the tool JSON. The author marked it benchmaxxed
  and deferred role tests to cycle 4.
- Two runs of one ticket on Flash-Next diverge at the first reply under
  greedy decoding; the task prompt carries the arm name (worktree path,
  branch). 0452 scored 25 (solo xhigh), 18 (helper xhigh), 17 and 16 (medium).
- pi defaults were resolving elsewhere than padme: on doudou the default
  model was missing from `enabledModels` and pi used `openrouter/auto`; on
  padme the `padme` provider did not list the default model and pi used
  huggingface Kimi-K2.6.
- After the switch, the roar sweep found `adapters/pi/agents/code-reviewer.md`
  and five deployed pi agents on padme (code-reviewer, planner, reviewer,
  scout, worker) pinned to `padme/qwen3.8-27b`, no longer served; all now
  name `padme/qwen3.8-flash-next-iq3_s`.
- A tool output displayed the Albert API key stored in doudou's
  `~/.pi/agent/models.json`; the author was told to rotate it.

Outcome and decisions:
- Hosted qwen3.8-flash dropped at three tickets (author rule: slower and
  costlier than local). Production: Flash-Next IQ3_S on both GPUs (A4000 as
  expert helper), xhigh default, `strata-server.service` on :8080, enabled;
  `llama-server.service` (27B) disabled. pi on doudou and padme default to it.
- Night mode: `arena-night.timer` (22:00) and `strata-morning.timer` (07:30);
  handover dry run 46 s. Night 1: helper arms on the 7 remaining tickets.
- Strata bench report mislabels mixed-GPU hosts: upstream issue
  Niko1221/Strata#2062.

References: PRs #1362, #1370, #1371; arena commits 16e4e43..57ea546 on padme.

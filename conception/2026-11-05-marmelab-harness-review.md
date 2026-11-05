# Marmelab, "How to build a harness that actually improves your agent" — review against the harness

Date: 2026-11-05
Source: u/Marmelab, r/AI_Agents, 2026-10-30, score 72, 26 comments.
<https://www.reddit.com/r/AI_Agents/comments/1xjc4rc/how_to_build_a_harness_that_actually_improves/>
The post summarises the authors' blog *The State of AI Harness Engineering 2026*
(<https://marmelab.com/blog/2026/09/24/the-state-of-ai-harness-engineering-2026.html>),
an audit of 391 repositories and 57 publications. The blog is the substantive
source; the post drops its caveats. Read alongside the 2026-04-04 review
(`20260404-review/00-synthesis.md`: Forsythe, DevMoses).

Staged copies (git-ignored): `docs/reddit-1xjc4rc.html`, `docs/reddit-1xjc4rc.txt`.

## Verdict

Mostly a restatement of what the harness already does; the two points it
adds belong to the arena. One cited number is
misreported.

## Source check

- **"Only 4–16% of written security rules had any real effect" is wrong.**
  arXiv 2608.23550 (Ting Yan, 2026-08-24, 481 public CLAUDE.md files) measures
  the share of security rules that have a *matching built-in Claude Code
  control* (deny rule, mode, sandbox): 4.4% (95% CI 2.6–6.7%) under the
  strictest match, 4–16% across match criteria, on the 66.3% of rules the
  extractor captured. It does not measure whether prose rules change behaviour.
  The conclusion "back prose with controls" still follows; the effect claim does not.
- Vercel (80% of tools removed, 80→100% success) is a vendor blog, second-hand
  and unreproduced; the blog says so, the post does not.
- The blog also cites results the post omits and that cut against this harness's
  design: NLAH, where adding a reviewer agent lowered success; Agyn, where a
  four-role team gained +0.4 pt over a single agent on SWE-bench 500;
  Microsoft, where problems needing more than four handoffs almost always failed.

## Claim by claim

| Claim (post or comments) | Harness today | Status |
|---|---|---|
| Turn past corrections into rules | roar captures, smelt consolidates, brood crystallises on author request | covered |
| Delete rules you can't prove help | "prefer deleting the guard and its tests" (workflow § Autonomous action); no proof standard for prose rules | partial, see N1 |
| Short root file as table of contents | resident set ≈ 16.5K chars incl. AGENTS.md; `test_rules_resident_budget.py` caps `rules/` at 15,100; AGENTS.md points outward | covered |
| Fewer, sharper tools | `Requires-tools` subset test per profile; MCP tools deferred | covered |
| Scripts over prose | verify-adherence mechanical-first, PreToolUse and git hooks, ratchet tests | covered |
| Garden the harness | molt, smelt, yawn, lair, harness-doctor | covered |
| Test guards both ways, must fire and must not (blog) | `test_guard_destructive_bash.py` has block and allow cases, including text-only mentions | covered |
| Guard telemetry; "a guard that never says no" (Sentient_Dawn) | `scripts/census/denials.py` joins each denial to its command and reason | covered for denials; zero-fire guards not reported, few guards exist |
| Rule first, explanation after (Sentient_Dawn) | rules lead with a bold imperative | covered |
| Verify outcomes, not intent (BarathKanna, React-admin) | verify-gate, gaze, gate records | covered |
| Always-on list vs per-task plan (CleanFix_Dev) | resident rules vs tickets and plans | covered |
| **Ablate one rule at a time on frozen tasks** (CleanFix_Dev, blog) | A/B considered (metaskill panorama 2026-04-28 § F4; trace-counterfactuals phase-5 shortlist), never run for rules | arena, N1 |
| **Prune on model upgrade** (gibonai, QuanTradin, blog citing Anthropic) | no trigger: a model change re-routes work but re-tests no rule | arena, N2 |
| Each control names its incident and an expiry condition (blog) | provenance mined from git, tickets and transcripts on demand | covered, see N3 |

## Beyond the post

**N1, N2. One rule, one model, one ablation is too simple.** The post and the
blog treat a harness as a fixed rule set tested against a fixed model. Here
three things move at once: which models are available (releases, retirements,
quota), the harness itself (several merges a day), and the route that assigns a
model to each kind of task. A rule's worth depends on the route it runs under,
and the route on the models on offer. Evaluating that joint system is the
arena's question, not a pruning sweep in this repository; the discussion is
parked on the arena ticket about what a CNRS GPU cluster would allow.

**N3. No index needed.** The blog's "each control names its incident" is
already met by mining, which the harness does routinely: the commit message
records why (`rules/git.md` § Branch and commit), tickets carry the incident,
and session transcripts hold the session that wrote it. Probe on the stash rule
in `rules/git.md`: `git blame -w -M -C -C` lands on the 2026-09-24 deduplication
commit (5cacc063); `git log -S "round-trip through" -- rules/` reaches the
origin, b92826a3, ticket 0193, 2026-06-04. So a reworded or moved line costs a
second hop. Limits: a line reworded past recognition breaks `-S`, and
transcripts expire after 180 days (`cleanupPeriodDays`), so an origin older than
that keeps its commit and ticket but loses its session.

**Challenge, not adopted.** The NLAH and Agyn results question how much the
multi-seat review (gaze panels, verify-gate) earns. The harness already
shortlisted "verification convergence" ($259 upper bound) for the phase-5 A/B;
these papers raise the prior that the A/B finds less than hoped. They test
benchmark settings, not this workflow; no change on this evidence alone.

## Disposition

Author's decision, 2026-11-05: N1 and N2 go to the arena, N3 is already
covered by git, ticket and transcript mining. No ticket: nothing here blocks
a merge, corrupts state, or bites the science.

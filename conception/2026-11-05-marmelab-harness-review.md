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

Mostly a restatement of what the harness already does; three points are new
here and none crosses the severity floor for a ticket. One cited number is
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
| **Ablate one rule at a time on frozen tasks** (CleanFix_Dev, blog) | A/B considered (metaskill panorama 2026-04-28 § F4; trace-counterfactuals phase-5 shortlist), never run for rules | gap, N1 |
| **Prune on model upgrade** (gibonai, QuanTradin, blog citing Anthropic) | no trigger: a model change re-routes work but re-tests no rule | gap, N2 |
| **Each control names its incident and an expiry condition** (blog) | git.md: "incidents live in memory and tickets"; link from rule to incident not systematic | gap, N3 |

## New to this harness

**N1. Evidence that a rule pays.** CleanFix_Dev's cheap form is to replay 2–3
past tasks with and without the rule. With 2–3 tasks per arm only a large effect
shows; most rules have small effects, so the test mostly cannot reject them.
The honest cheap form is the blog's: 20–50 frozen tasks drawn from observed
failures, model fixed, one component changed. That is the phase-5 A/B already
shortlisted. Nothing to add except to note that rules join that queue.

**N2. Model upgrades as a pruning trigger.** The most actionable point. When the
main model changes, many resident rules guard against failures the new model
may no longer produce. Candidate mechanism: on a model change recorded by the
route skill, smelt or harness-doctor lists the rules whose incident (N3) can be
replayed and re-tests each one; a rule whose failure no longer reproduces is
proposed for deletion. Cost: one sweep per model generation. It depends on N3.

**N3. Rule → incident link.** Without it, N2 cannot tell which failure a rule
prevents. The cheap form, one line per control naming its ticket or memory
entry, conflicts with "Rules only" in resident files and their character budget.
It could live outside the resident text (a sidecar index or a commit trailer).

**Challenge, not adopted.** The NLAH and Agyn results question how much the
multi-seat review (gaze panels, verify-gate) earns. The harness already
shortlisted "verification convergence" ($259 upper bound) for the phase-5 A/B;
these papers raise the prior that the A/B finds less than hoped. They test
benchmark settings, not this workflow; no change on this evidence alone.

## Disposition

No ticket: none of N1–N3 blocks a merge, corrupts state, or bites the science.
N2 and N3 together form a proposal for the author: open a design note if model
upgrades are expected within the quarter. N1 joins the existing phase-5 A/B.

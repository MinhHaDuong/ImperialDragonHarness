---
name: review-pr-prose
description: "Simulated peer review panel for manuscript prose. Spins discipline-specific agents for multi-perspective review."
disable-model-invocation: false
user-invocable: true
argument-hint: "[pr-number] [worktree=<path>] (defaults to the current branch's open merge request)"
context: fork
# Foreground: the prose sibling of review-pr, invoked the same way by /gaze on
# manuscript PRs. Claude Code 2.1.218 made `context: fork` skills background by
# default; a fork cannot wait on a background completion, so the default would
# orphan this phase — ticket 0250. Standalone use is unaffected.
background: false
---

# Review PR prose $ARGUMENTS — simulated peer review panel

> **TASK DIRECTIVE — execute now.** You are running `/review-pr-prose` on PR
> `$ARGUMENTS` (a PR number, optionally followed by `worktree=<path>`). This
> file is your operating procedure, not reference documentation: start the
> setup immediately. If `worktree=<path>` is present, `cd` into that path
> before any git or forge command — forked sub-skills do not inherit the caller's
> cwd. If `$ARGUMENTS` does not contain a PR number, do NOT infer a task
> from the environment (worktree name, git status snapshot, ticket files, or
> the shared task list) — resolve the missing *argument* from the forge
> instead: query the forge CLI for the open merge request attached to the
> current branch; if exactly one exists, announce "reviewing PR #N (<title>)
> — resolved from branch <branch>" and proceed. If that yields nothing or
> several, list the actual open merge requests and STOP so the user can pick
> from real candidates. Never suggest a fabricated example number — an
> invented "e.g. #N" anchors the user into re-invoking on the wrong PR
> (2026-06-10: exactly that burned a five-agent panel on an already-merged
> PR while the intended target sat unreviewed).

Spin disciplinary agents in parallel, each in a fresh context, each pinned to
**`model: sonnet`** (reviewers below the coder tier — rules/workflow.md;
an unpinned Agent inherits the session model and silently runs the fan-out at
top tier). Prose review reads **full text**, not just diff.

**Concurrency contract (`rules/authoring-skills.md`): parallel-background,
collected by polling.** This skill runs as a `context: fork` (see frontmatter),
and a fork's turn ends the instant it stops calling tools. Delegated subagents
always run in the background and notify the **session**, not this fork; no
launch parameter changes that. The fork stays alive only by continuing to call
tools, so the panel is collected from **artifacts**, never from return values:

1. Before launching, write the roster to `<panel>/manifest.txt`, one reviewer
   per line — the set collection checks against. Without it, "no more reports
   are arriving" cannot be told from "none were ever launched".
2. Each reviewer writes its report to `<panel>/<reviewer>.md.part`, then renames
   it to `<panel>/<reviewer>.md`. The rename is the completion signal: a
   half-written file never carries the final name.
3. The fork waits in one bounded loop until every manifest entry has its report
   or the deadline passes — roughly ten minutes. That wait is what keeps the
   fork's turn alive.

`<panel>` is `<worktree>/.panel/<pr-number>/`, inside the worktree and never a
temporary directory: collection assumes launcher and reviewers share a
filesystem, and a container's temporary directory may be neither shared nor
durable.

A reviewer still missing at the deadline is **missing, not accepting**. Name it
in the posted review and leave it unresolved for the next round.

## Setup

1. Identify the text: which of the diff's files are manuscripts per the shared prose predicate? Run `python3 ~/.claude/scripts/prose_predicate.py <file>` from the merge request's checkout — the predicate reads the disk (manifest walk-up, `\documentclass` sniff), so the paths must exist under the cwd; it refuses a missing path (exit 2, no verdict) rather than guessing, and a refusal is a cwd error to fix, never an answer. It prints `prose` for a manuscript: a file with a resolved `doctype`, from the project's `.claude/rules-map.toml` manifest or the `\documentclass` sniff when no manifest exists. What is the target venue?
2. Read the diff of the merge request.
3. Recruit the panel: select agents appropriate for the venue and scope of changes. Always include an adversarial referee. Add a journal-specific expert if venue rules exist (check project rules). On round ≥ 2, scope the panel per § Round scoping below before launching it.

## Each agent runs

1. Read the **full text** (not just the diff).
2. Report **confidence** + **severity** (major / minor / suggestion).
3. Verdict: **accept**, **minor revision**, or **major revision**.

Agents with relevant expertise should use available tools (web search for literature, linting tools if installed, etc.).

## AI-tells auditor (always included)

One agent is always the **AI-tells auditor**. It reads `config/ai-tells.yml` for blacklisted words, phrases, conditional words, density limits, and patterns to flag. It scans the full text (not just the diff) and reports every violation with line number, context, and severity. This agent has no other role — it is a specialized lint pass.

## Editorial-brief auditor (when present)

If the project defines an editorial brief at `docs/editorial-brief.md`, one agent is the **editorial-brief auditor** (pinned `model: sonnet` like the rest of the panel). Skip silently when the file is absent — this check is project-specific and optional (skills degrade gracefully).

The skill owns the schema, projects own the content. Expected brief format — one standing decision per entry, each entry carrying:

- a decision title;
- **Decision:** one sentence;
- **Rationale:** one or two sentences;
- **Ticket:** originating ticket reference.

The auditor reads the brief plus the manuscript diff and reports a per-entry verdict table:

| Entry | Verdict | Evidence |
|---|---|---|
| decision title | upheld / violated / not touched by this diff | line ref, or "not in diff" |

Violations must cite the line. This agent has no other role — its table goes verbatim into the Synthesis step.

## Synthesis

1. Preserve dissent verbatim.
2. Group findings: major (blocks acceptance), minor (should fix), suggestion.
3. Deduplicate convergent findings.
4. Build the manuscript. Check consistency between prose and data.
5. Write the synthesis to `<panel>/review.md` before posting it — findings then
   survive a forge outage, a fork that dies mid-step, and a failed post.
6. Post a single review on the merge request.
7. Verify it landed: count the reviews before posting and again after, and the
   count must increase. If it did not, the round did not happen — say so, name
   `<panel>/review.md`, and return failure rather than a summary that reads like
   success.
8. Close with a verdict roster: one line per reviewer in the manifest, giving its
   verdict (accept / minor / major), including reviewers that accepted with
   nothing to say, and **no report** for any that did not land. The next round
   scopes itself from this roster (§ Round scoping): a `no report` reviewer is
   unresolved and runs again. A reviewer that crashed and a reviewer that
   accepted are opposite outcomes and must not share a spelling.

## Minor/suggestion tags (mandatory)

Every minor or suggestion item in the posted review carries exactly one prefix:

| Prefix | Meaning |
|---|---|
| `verifiable:` | A reproducible check is attached (line-number citation against the text, numeric recheck, lint rule violation). Reviewer can confirm without re-reading the paragraph. |
| `consider:` | Hypothesis or taste call. No enforcement. Author may dismiss. |
| `nofollow:` | Noted but not pursued (out of venue, already handled elsewhere, deliberate stylistic choice). No action expected. |

Rules:
- Hedged prose like "readers may find X confusing" without a concrete pointer is forbidden. Either cite the line and the confusable construction (`verifiable:`) or downgrade to `consider:`.
- Majors are not tagged; tags are for the minor/suggestion tier only.
- The tag set is shared with `/review-pr` and `/verify-gate`. Keep all three in sync.

## Proportional depth

| Text change | Panel size |
|---|---|
| Typo, citation fix | Copy editor only |
| Section rewrite | 3 agents (domain + adversarial + copy) |
| Full paper draft | Full panel (5-6 agents) |
| Submission-ready | Full panel + response-to-reviewers template |

### Round scoping

The table above prices **round 1**, which always runs the full panel for the
change's size. Derive the round from the merge request itself: count the
reviews this skill has already posted there; the round is that count plus one.
No caller passes a round number.

For round N > 1, re-run only the reviewers whose round N−1 verdict was
**minor** or **major**, plus one regression agent running a single regression
check over the whole accepting set — asked only whether the revisions since
then broke what those reviewers accepted. The AI-tells auditor is exempt from scoping and runs every
round: it scans the full text, so revised passages are new surface for it
regardless of who objected last time.

**Reset exception.** If the revision since the last review touches text the
review did not cover, or rewrites more than roughly half of it, run the full
panel for this round — scoping is ignored, and the derived round number itself
is untouched. The accepting reviewers accepted different prose.

This mirrors § Round scoping in `skills/review-pr/SKILL.md` (ticket 0377); keep
the two in sync.

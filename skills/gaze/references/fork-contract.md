# Gaze — fork execution contract

Loaded from `skills/gaze/SKILL.md`; applies to every phase that spawns an agent.

## Fork execution contract

`/gaze` runs as a `context: fork` (see frontmatter). A fork's turn ends the
instant it stops calling tools, and **delegated subagents always run in the
background and notify the session, not this fork.** There is no foreground
launch parameter to pass; earlier revisions of this contract named one, and a
lever that does not exist cannot be the thing holding a phase together.

What is true is the first sentence: the fork survives only while it keeps
calling tools. So every agent this skill spawns (the phase 2–5 reviewers and
the review panel's perspective agents) is launched in the background and then
**waited for by polling an artifact it writes**, in one bounded loop. The wait
itself is the tool call that keeps the fork alive.

Each spawned agent is therefore told, in its prompt, to write its result to a
named path under `<worktree>/.panel/<pr-number>/`, writing to `<name>.md.part`
and renaming to `<name>.md`, so a half-written file never carries the final
name. The roster of expected names is written down *before* launching. A
waiter that just gathers whatever files appear cannot tell an agent that
finished silently from one that never started; comparing against a roster
written in advance can.

Without this, the failure is silent and total: the fork ends its turn at the
launch, the completions re-invoke the **MAIN loop**, and the fork's last message
is a fan-out narration ("reviewers are running in parallel…") instead of a
result, with phase 5 never running. This orphaned real runs, each forcing the
caller to relaunch a duplicate reviewer battery.

**Bound every wait, and record what did not arrive.** An agent missing at the
deadline is missing, not clear: name it in the result and treat its phase as
unresolved. Never extend a deadline to avoid recording a gap.

**The contract applies recursively.** Any nested fan-out performed on `/gaze`'s
behalf, such as the review panel's perspective agents, inherits this same rule:
the inner launch must be waited for by polling an artifact too, or the orphan
failure simply moves one layer down. A launch site is bound by the fork contract
whether it is this skill's own or a sub-agent's.

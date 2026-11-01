# Monster ticket: drafting the decomposition

The procedure behind `rules/workflow.md` § Ticket discipline for multi-request
work, whose rule keeps the signal (15+ files, a symbol other tickets depend on,
a build-gated exit, bundled sign-off units or a hidden dependency chain).

Draft a tracker (partition boundary, up-front decisions, wave order) and
children sized to one sign-off unit, each `Blocked-by` its real prerequisite,
never the tracker.

Who acts on it:
- an autonomous orchestrator files it;
- a hunt or an interactive session proposes it;
- a lone session proposes it in its report and stops.

The 15-file count is a signal, not a wall. A large diff splits the review, not
necessarily the merge request.

# Imperial Dragon Harness — State

Last updated: 2026-05-13T10:00Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-13T10:00Z -->

**Tickets:** 14 open · 14 ready — `erg ready tickets/` for full list
**Recent commits:**
  120b67f docs(verify): isolate verify/verify-gate agents in temp worktree (#176)
  70780ee docs(nightbeat-supervisor): budget-raise convergence guard (#178)
  650f3dc fix(nightbeat-supervisor): dual-journal startup assertion (#179)
  521bfd6 fix(scripts): add timeout=30 to subprocess.run (#173)
  953c2e1 fix(beat): guard git checkout in housekeeping post-cleanup path (#175)

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **audit-rename-agnostic-guard**: 6-commit branch needs PR + verify before merge
- **0129**: deduplicate verify chain in raid (stale worktree `agent-ad6d9f2a48e8386cc` has partial work + merge conflict — needs human review before cleanup)
- **squash-merge probe false negatives**: probe pattern `\(NNNN\)` misses commits scoped as `(beat)`, `(skill-doctor)` etc. — 7 closed-ticket branches stuck; ticket needed
- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules

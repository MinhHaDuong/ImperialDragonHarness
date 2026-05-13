# Imperial Dragon Harness — State

Last updated: 2026-05-13T10:07Z

## North star

A reusable, science-backed personal harness for AI-assisted research: code and prose, day and night, across projects and machines.

## Status
<!-- generated 2026-05-13T10:07Z -->

**Tickets:** 14 open · 14 ready — `erg ready tickets/` for full list
**Morning review:** `/nightbeat-report` (narrative) · `/nightbeat-risk-review` (interactive triage before next run)
**Recent commits:**
  120b67f docs(verify): isolate verify/verify-gate agents in temp worktree (#176)
  70780ee docs(nightbeat-supervisor): budget-raise convergence guard (#178)
  650f3dc fix(nightbeat-supervisor): dual-journal startup assertion (#179)
  521bfd6 fix(scripts): add timeout=30 to subprocess.run (#173)
  953c2e1 fix(beat): guard git checkout in housekeeping post-cleanup path (#175)

## Blockers

- **0084**: needs WORKER_API_KEY secret + openai library on host

## Next actions

- **0149**: fix squash-merge probe false negatives (pattern misses conventional scopes like `(beat)`, `(skill-doctor)`)
- **doudou setup**: add source line to `~/.bashrc`, install nightbeat systemd units, copy erg binary to all projects

## Backlog

- Streamline settings.json hook configuration
- Enable branch protection requiring `validate-tickets` on main
- Merge REALF guidelines and business rules

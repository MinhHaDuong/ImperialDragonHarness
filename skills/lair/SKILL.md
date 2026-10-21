---
metadata:
  category: session
name: lair
description: "End-of-day wrap-up: housekeeping, push branches, run tests, refresh STATE, offer an autonomous session. Not for one merged task (/roar) or a mid-session check (/perch)."
disable-model-invocation: false
user-invocable: true
---

# Lair — end-of-day wrap-up

Neighbouring skills and when to prefer each: `references/session-lifecycle.md`.

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Run when the user ends a work session ("done for today", "let's stop", "wrap up").

## Steps

0. **Review session scope**: use today's commits and the current ticket state to identify work for steps 1–2. Always perform steps 11 and 12: the reconcile proposal and pending experiences are independent of new commits.

1. **Housekeeping** — run `/molt` (git sync, yawn, eager fix-now repairs, ticket creation).
2. **Reflect on the session** — summarize work done. `git log --since="6am" --oneline` as starting point.
   Then run the report-only temporary-candidate scan for the host, using the
   exact current runtime name and session id from its live metadata:
   ```bash
   RUNTIME=codex       # set to the exact runtime: claude, codex or pi
   SESSION_ID='id-from-live-session-metadata'
   python3 "$IDH_ROOT/scripts/tmp_report.py" --runtime "$RUNTIME" \
     --scope lair --repo "$(git rev-parse --show-toplevel)" --session-id "$SESSION_ID" \
     --exclude-session-id "$SESSION_ID"
   ```
   History attribution has a 20-second default budget. If the report says
   history attribution is partial, unmatched candidates have unknown history
   attribution; rerun with `--history-budget-seconds 0` when exhaustive history
   evidence is needed.
   The helper checks all available runtime histories, reports candidates and
   unattributed paths, and performs no cleanup. The reporting session is
   excluded from citation attribution, so candidates mentioned only by it
   remain unattributed. A citation is not proof of creation; `created` appears
   only for a matching native Claude/Codex call and result id, explicit zero
   exit status, and one direct command targeting the exact candidate. Do not
   copy raw history commands into the handoff. If the session id is unavailable,
   omit both session flags; the helper cannot exclude its own session in that
   case, so treat any matching citation as uncertain and do not infer ownership.
3. **Log session metrics** — run `"$IDH_ROOT/skills/lair/log-agent-metrics"` with: `<session_id> session <total_tokens> <tool_uses> <duration_ms> <model> <project>`. Estimate tokens from conversation length if exact count unavailable.
4. **Push all branches** — no local-only work overnight. `git branch` → ensure each non-main branch is pushed to origin.
5. **Commit WIP if needed** — uncommitted work gets `wip:` prefix, committed to the current branch, and pushed.
6. **Handoff notes** — for in-progress tickets with unpushed context, add a comment to the ticket: what's done, what's next, blockers.
7. **Exit worktree** — if in a worktree:
    a. Preflight from inside the worktree: `"$IDH_ROOT/scripts/worktree-exit-preflight.sh"` (purges `.panel/` and `build/panel-head/` review scratch, then refuses on any other uncommitted/untracked state). If it blocks, finish step 5/6 (commit WIP, handoff notes) and re-run.
    b. `cd` to the primary checkout (`dirname "$(git rev-parse --path-format=absolute --git-common-dir)"`). All remaining steps run on main.
8. **Hygiene sweep**:
   - Stale worktrees were GC'd by `/molt` at step 1 (housekeeping owns worktree GC; the script's rails protect active sessions). Here, just `git worktree prune` for leftover admin entries of already-deleted dirs.
   - **A worktree the GC skipped for uncommitted changes is a signal, not just an obstacle**: diff it and ask "is this a closed ticket's dropped deliverable?" — `erg-pr-merge` autocloses on the `**Ticket:**` line unconditionally, so a PR can close a ticket having landed only part of the work, leaving the rest as orphaned WIP. Preserve it (`wip(NNNN):` commit + push), then re-ticket and execute; never silently discard. Verify any recovered test actually runs — uncommitted WIP may never have been linted/executed.
   - `git branch -a` → delete stale remote branches
   - Check for orphan tickets and stale merge requests
9. **Full test suite** — `make check` on main. New failures → open ticket. Known failures → confirm ticket still open.
10. **Refresh STATE.md** only when a hand section changes (blockers, next actions, milestones); if nothing changed, open no branch or PR and report "STATE unchanged". Otherwise use a throwaway branch, landed through the normal PR gate (main is branch-protected — there is no direct-push-to-main path, and STATE.md is not special-cased; rules/git.md):
    a. `git checkout -b housekeeping-state-YYYY-MM-DD main`
    b. Hand-edit the sections and bump `Last updated:` in that same change (blockers, next actions, milestones) — no changelog, and no ticket counts, picks, MRs or commits: STATE.md stores no derived number (rules/state.md).
    c. Prune: delete items checked off before this session, and prune further to stay within the cap (rules/state.md).
    d. Commit, push the branch, open a merge request (`Ticket: none`), then **land it yourself** — a STATE refresh is the agent's own output with no blast radius, and handing the author a merge to perform is what this step exists to avoid. Which mechanism lands it is a per-repo fact, never assumed: a `.merge-gate.json` on the base decides the gated path; otherwise **read the auto-merge setting from the forge.**
       - Gated base (`.merge-gate.json`) → write the gate record and merge per `skills/merge/SKILL.md` § Gated base, as one background command; its exit 2 means record again on the new head. Never arm auto-merge there: with nothing required it merges at once.
       - Auto-merge available and enabled on the repo → enable it on the merge request; it lands on its own once the forge's requirements are met.
       - Otherwise → fall back to the repo's own proportionality path (a "trivial review" label where one exists, plus a single review), then merge directly.

       All three landing paths are load-bearing, and which one applies is read, never assumed. This step once named auto-merge alone; in a consumer repo where that setting was off, a session following it literally stopped at the open merge request and handed the author the merge. Whatever had landed the earlier STATE refreshes there, it was never auto-merge — and nothing in the step said to check. A step that names one mechanism without a probe assumes every repo shares one configuration, and fails silently in the direction of extra author work.
       <!-- harness-extension-point -->
       Current-generation spelling: `gh api repos/<owner>/<repo> --jq .allow_auto_merge` to read it, `gh pr merge <N> --auto --merge` to arm it.
    e. After the PR merges, delete the throwaway branch (local and remote).
11. **Propose the staging reconcile when `docs/` moved today.** Run
    `"$IDH_ROOT/skills/lair/zotero-reconcile-trigger"` from the primary checkout
    (the cwd after step 7b): an mtime scan, symlinks followed, for any file under
    `docs/` modified since the start of the current day (`docs/` is git-ignored,
    so git cannot see it). If it prints a line, include it in the final summary
    as an offer of `/zotero check-staging`; the author accepts or not. No output, no
    mention. Proposed, never run automatically; it does not belong in `/molt`.
12. **Suggest a hoard in the conclusion when relevant.** After completing
    all lair work, count journal experiences not yet covered by an accepted
    report in `memory/hoards/`. An unmerged report does not mark experiences
    processed. Count inline, on the journal blobs against the accepted
    reports' ledgers — no counting script, no library, no configuration
    knob, the threshold stays hardcoded at 5. Every report records its
    examined sources as `<path> blob <40-hex>` lines (the project’s versioned HOARD.md):
    - Current blob id of every `memory/journal/YYYY/*.md` entry at HEAD:
      `git ls-tree -r HEAD memory/journal/` (the 40-hex column).
    - Blob ids already examined by the accepted reports: the `<path> blob
      <40-hex>` lines in `memory/hoards/*.md` merged into main — a report
      visible only on an unmerged branch covers nothing.
    - An entry is covered only when its current blob id appears in an
      accepted report's ledger; a journal blob examined only by an unmerged
      report is still new, and a changed blob is new again.
    With **5 or more new experiences**, include in the final summary:
    “N nouvelles expériences depuis le dernier rapport accepté. Follow-up suggéré :
    `/hoard <project-repository>` dans une nouvelle session `/clear`.” Do not
    ask a question, wait for a response, launch hoard or mark
    the experiences processed. Below the
    threshold, omit this suggestion. No timer or automatic invocation.
13. **Suggest a testing consultation when the traces show a speed bump.**
    From the primary checkout, run the survey over the last seven days:
    `python3 "$IDH_ROOT/scripts/pulse_traces.py" survey --project "$(git rev-parse --show-toplevel)"`.
    Carry what it prints into the final summary as an offer of `/pulse`; the
    author accepts or not. It prints nothing when it read the traces and found
    no gate that waited long, and a line starting `pulse: not checked` or
    `pulse: checked` when it could not tell: pass that line on, since silence
    would otherwise read as an all-clear. Proposed, never run automatically:
    do not launch `/pulse`, ask a question or open a ticket for it.

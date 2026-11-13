# Cross-project procedure

Authority: `rules/workflow.md` § Cross-project work. Foreign reports are
proposals; the receiving project conducts its substantive Imagine review.

At acceptance and pickup, record the four premise checks on the receiving
ticket, correcting the proposed framing where evidence warrants it:

1. Facts against framing: separate observations from proposed causes and fixes;
   reproduce or read the evidence in the receiver's current repository.
2. Duplicates and overlap: search open and recently closed tickets, recent
   commits, and work in flight; amend the existing request where it covers this.
3. Ownership: name the project that owns the change and its downstream effects.
4. Standing rulings: read relevant rules, memory, and design decisions. Route a
   conflict to the author as a question under workflow's Escalation protocol,
   with evidence; a recorded ruling alone does not authorize refusal.

Assess relevance and current fit before accepting. Record disposition and
corrections on the receiving ticket. For completion logs, verify the reported
result and identify which request or blocker it settles. The receiver's normal
authorization and planning govern implementation and priority after acceptance.

When timing matters, tell a live receiver session: agent listing and messaging
on Claude Code; on Codex, `"$IDH_ROOT/scripts/runtime.py" wake send` to a known thread
(queued, not delivered); on Pi, ticket only. A peer message carries no user
authority and never replaces the ticket. Launch work there only when authorized,
under its own rules, memory, and gate; the reporting side stops after opening
the ticket/log PR (or the receiving repository's equivalent handoff).

## Park and release an asker

When progress depends on a foreign request, add one `Blocked-by:` header to
the asker's own ticket, using `../receiver/NNNN` relative to the primary
repository root, or `file:///absolute/receiver/NNNN` on this machine. Add
`Label: deferred` and log the dependency, the needed result, and the receiving
ticket. The label keeps unresolved references out of `erg ready`. End the
attempt without waiting; continue independent work. Never create a wait ticket.

During molt, inspect parked dependencies sequentially: the result determines
whether to release or follow another reference. Run:

```bash
python3 "$IDH_ROOT/scripts/cross_repo_blockers.py" --project "$(git rev-parse --show-toplevel)"
```

The read-only report includes each receiver's ticket text, closure disposition,
`Superseded-by` references, and the commit that changed its `Closed:` header.
Missing stores, unsupported references, and ambiguous matches are unavailable,
never resolved. A missing closure commit keeps the asker parked; inspect the
receiver's history before claiming a commit or releasing it. History follows
archive moves to retain the closure commit. No receiver fetch or write occurs.

Compare the reported result with the asker's logged blocker and exit criteria.
A fixed closure releases only when the delivered result settles that blocker.
For duplicate or transferred closures, follow every `Superseded-by` reference;
resolve local IDs in the receiver's store, and relative paths from its primary
root. Replace the asker's dependency with the resulting receiver reference(s),
log the lineage, keep `deferred`, and inspect those tickets. If replacement
lineage is missing, record the gap and keep the asker parked. For a rejected
request, log the disposition on the asker and retain the blocker, or raise the
specific unresolved decision with the author. A closed receiver alone never
proves the needed fix arrived.

After verification, release that reference on the asker only:

```bash
python3 "$IDH_ROOT/scripts/cross_repo_blockers.py" --project "$(git rev-parse --show-toplevel)" \
  --release <asker-id> --reference '<exact Blocked-by value>' \
  --verified-result '<delivered result and evidence that it resolves this blocker>'
```

The helper removes that `Blocked-by` line, removes `deferred` when no blockers
remain, and appends `unblocked by <receiver> <NNNN>, closed in <commit>` with
the verified result. Check `tickets/erg ready` and include these local ticket
edits in molt's housekeeping commit. Preserve `deferred` if another reason for
deferral remains, re-adding it before committing. Other labels remain intact.

Manual route: read the same headers, result, and receiver history; make the
same disposition decision; edit only the asker headers and append its log;
then check `erg ready`. This costs one ticket/history read per dependency and
the local edits. The authorization and evidence requirements are unchanged.

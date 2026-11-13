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
under its own rules, memory, and gate; the reporting side hands off after filing
its ticket, side branch, or PR.

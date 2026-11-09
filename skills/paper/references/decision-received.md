# decision-received

An editor's decision arrived: accept, minor or major revision, or reject.

## Registers

- Roadmap: yes, record the decision and the next action ("révision majeure
  demandée, réponse avant <date>"; or "refusé, cible suivante à choisir").
- Publications list: no change for a revision or a rejection. An acceptance
  continues in `references/accepted.md`.

## Provenance

The decision letter and reviewer reports come from the mail or the platform,
verbatim. Archive them before reading closely; re-hunting a mailbox later
wastes a session.

## Filesystem

1. Paper repo: archive the letter and reports into `release/<date>/` and commit
   them (tracked text). STATE line with the decision and the deadline.
2. `~/CNRS/papiers/sent/<manuscript>/<date venue decision>/`: the authentic
   letter and any attached PDFs, with `SHA256SUMS`.
3. Rejection: the manuscript folder stays in `sent/` until the next submission
   moves it back to `actif/`.

## Outward gates (who clicks)

None at this stage. Any reply to the editor (deadline extension,
acknowledgement) is sent by the author.

## Delegates

- `/ingest-decision-letter` for revise-and-resubmit: archive, remark ledger,
  coverage check against tickets.
- `/choose-venue` after a rejection, with the reviews as input.

## Author-only (ask, do not drop)

- Revise, appeal, or withdraw and resubmit elsewhere?
- Co-authors informed of the decision.
- Deadline accepted, or an extension to request.

## Done when

Letter and reports archived in both places; roadmap row carries the decision and
the next action; for a revision, every remark maps to a ticket.

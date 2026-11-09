# return

Back from the trip. Three strands, each with its own register and gate, then
the close. Steps 1-9 run in order, one at a time: 3 to 6 wait for the
author, and the close records what the strands answered.

A dossier whose README carries a closing section and that sits where the
local `AGENTS.md` puts closed dossiers is done: report "nothing to do" and
stop. Otherwise walk every step; a dry run lists each one with its evidence or
"missing".

## Registers

- Roadmap: yes, the row says "given on <date>", with the link to the deposit
  once it exists.
- Publications list: yes when something citable was given (slides, a paper, a
  tribune); type per `/update-publist`'s status table.
- The institution's activity report: indirectly, through the closed dossier's
  location; the local `AGENTS.md` names the tools that read it.

## Provenance

The communication as given (the slides sent at the check stage, the text as
published), the return ticket and every receipt, saved as received. Frozen
outputs go in the dated release subfolder with their hashes.

## Filesystem

1. Receipts inventory in `voyage/`: outbound and return tickets, lodging,
   registration, meals and local transport. List what is missing.
2. Release subfolder dated the day of filing, holding the authentic
   communication and its `sha256sum` lines.

## Outward gates (who clicks)

Employer strand:

3. Expense claim: the agent prepares the list of expenses with the receipt
   for each and the form named by the local `AGENTS.md`; the author fills in
   and signs the claim in the browser and hands the receipts over. The agent
   stops here and hands back. A trip with no expenses has no claim: the author
   confirms that with the institution's manager, and the strand ends there.
4. Return declared where the institution requires it: the author.

Lab strand:

5. Short report to colleagues, drafted from the dossier (who, what was said,
   what follows for the lab), in the shape of the last report the local
   `AGENTS.md` points to. Sent on the author's confirmation, then archived in
   the dossier as Markdown. The author may decline it (a report months late is
   noise); the closing section records that answer.

Self strand:

6. The communication on the personal page and in the open archive via
   `/update-publist`, page first, then the archive; its gates apply.
7. Roadmap row updated: the agent edits the local roadmap file as the local
   `AGENTS.md` says, with the deposit link from step 6.

Close:

8. README closing section: what was done, where the report is archived,
   that the dossier is closed.
9. Move the dossier to the closed dossiers under its rubrique, renamed as the
   local `AGENTS.md` says. If the activity-report tool does not read that
   rubrique, say so: extending its path list is a change in that tool's own
   project, not here.

## Delegates

- `/update-publist` for step 6.
- The mail skill, where installed, for step 5's sending; otherwise the author
  sends.
- `/paper` if a manuscript event came out of the trip.

## Author-only (ask, do not drop)

- Expense claim signed and receipts handed over.
- Social-media post about the talk.
- Follow-ups promised to people met (mail, paper, data).
- Which rubrique the dossier closes under, when the local `AGENTS.md`
  leaves it open.

## Done when

Steps 1-9 done or explicitly waived by the author; every author-only item has
an answer; the dossier sits in its rubrique with a closing section.

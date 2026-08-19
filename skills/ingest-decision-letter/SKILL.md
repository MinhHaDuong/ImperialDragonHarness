---
name: ingest-decision-letter
description: "Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check that maps every remark to a ticket. Turns Revise-and-Resubmit intake into one deterministic pass instead of a manual re-count."
user-invocable: true
disable-model-invocation: false
argument-hint: "<decision-letter> <reviewer-comments>... [--release-dir <paper-repo>/release/<date>]"
---

# Ingest decision letter $ARGUMENTS

Take a journal's **Revise-and-Resubmit** decision letter plus each reviewer's
comments, archive them where they will not be lost, parse them into a structured
**remark ledger**, and produce a **coverage check** that maps every remark to the
ticket(s) addressing it — flagging uncovered remarks and orphan tickets. This is
the *inverse* of `external-peer-review` / `review-pr-prose`: those review **our**
manuscript; this ingests **the journal's** review of it.

The bundled helper is `~/.claude/skills/ingest-decision-letter/ingest_letter.py`.
It is pure I/O — it never calls a model. You (the model) read the extracted text
and assign categories and ticket mappings; the script does the deterministic,
re-runnable work: extract, archive, segment, dedupe, coverage.

## Sources

Accept the letter and comments as **file paths** — a text file or a PDF (the
helper extracts PDF text via `pdftotext`). The comments may also arrive as an
**email thread**: if the project exposes a mail-reading capability, fetch the
thread and save its text to a file first, then proceed exactly as for a text
file. Do not build the intake around any one mail tool — the archived text file
is the interface.

Once located, **archive first** (next step): the 2026-06-18 intake wasted a whole
search re-hunting comments that had already been filed. The archive is the
single source of truth; never send the author back to a mailbox to re-find them.

## Steps

1. **Locate the sources.** Resolve each path argument. If a source is missing and
   it lived in an email thread, fetch the thread with whatever mail capability the
   project offers and write it to a text file. If you cannot find a source, stop
   and ask the author for the path — do not guess.

2. **Archive to `release/<date>/`.** Paper repos keep an immutable, append-only
   `release/<date description>/` per submission; editorial replies file into the
   release subdir they answer, as tracked text. Copy the sources there:
   ```
   ~/.claude/skills/ingest-decision-letter/ingest_letter.py archive \
       decision.pdf reviewer1.txt reviewer2.txt \
       --into <paper-repo>/release/<date>/
   ```
   PDFs are copied verbatim and a `.txt` sidecar of their text is written beside
   them, so the archive stays greppable. A `manifest.json` records what landed.
   Commit the archived text in the paper repo (it is durable tracked state).

3. **Segment each reviewer into a candidate ledger.** Run `segment` once per
   reviewer — it splits the comments into candidate remarks with **stable ids**
   (`R1-01`, `R1-02`, …) and source line locations. Re-running on the same input
   yields the same ids, so the ledger is a stable anchor.
   ```
   ~/.claude/skills/ingest-decision-letter/ingest_letter.py segment \
       reviewer1.txt --reviewer R1 >  ledger.jsonl
   ~/.claude/skills/ingest-decision-letter/ingest_letter.py segment \
       reviewer2.txt --reviewer R2 >> ledger.jsonl
   ```
   The segmenter is a deterministic first pass (it splits on enumeration markers,
   or on paragraphs when the reviewer did not number anything). **Then read the
   extracted text yourself** and refine each record: set `category` (framing /
   method / data / literature / typo / …), fix any remark the segmenter split or
   merged wrongly, and keep the `text` verbatim. This is the one judgment step;
   everything around it is mechanical.

4. **Dedupe atomic-vs-remark.** A reviewer's numbered points often restate one
   underlying remark (the 2026-06-18 letter reconciled 60 atomic comments down to
   56 remarks). `dedupe` folds duplicates and any record you tagged with
   `atomic_of` into its parent, so the distinct-remark count is deterministic:
   ```
   ~/.claude/skills/ingest-decision-letter/ingest_letter.py dedupe \
       ledger.jsonl > ledger.dedup.jsonl
   ```
   Distinct remarks are the records whose `atomic_of` is null; folded atomics
   inherit their parent's coverage.

5. **Create tickets, then map remarks to them.** Group the distinct remarks into
   thematic tickets (one theme per ticket). Record the mapping **in the ledger**:
   set each remark's `tickets` field to the list of ticket ids that address it.
   Leave it `[]` for anything not yet ticketed — the coverage check will catch it.

6. **Coverage check — one deterministic pass.** Cross-check the ledger against the
   tickets that exist for this round:
   ```
   ~/.claude/skills/ingest-decision-letter/ingest_letter.py coverage \
       ledger.dedup.jsonl --tickets-dir tickets/
   ```
   The report lists, and the command exits non-zero on, any of:
   - **uncovered_remarks** — a remark no ticket addresses.
   - **orphan_tickets** — a ticket in the universe that addresses no remark.
   - **unknown_ticket_refs** — a ticket a remark points at that does not exist.

   Iterate — add tickets, fix mappings — until the report is clean. That clean
   pass replaces the two-or-three manual re-counts the old intake needed.

## Ledger schema

One JSON object per line (JSONL):

| Field | Meaning |
|-------|---------|
| `id` | stable `<reviewer>-<NN>`, document order |
| `reviewer` | reviewer label, e.g. `R1` |
| `category` | you assign: framing / method / data / literature / typo / … |
| `text` | verbatim remark text |
| `source` | `<file>:<line>` where the remark starts |
| `tickets` | list of ticket ids addressing this remark (`[]` = uncovered) |
| `atomic_of` | parent remark id when this folds into another (`null` = distinct) |

## Notes

- **Pure I/O helper.** The script never calls a model; the one judgment step
  (categories, mapping, fixing a mis-split remark) is yours.
- **Tool-agnostic.** The email-thread path is a capability, not a fixed tool —
  the archived text file is the interface, so any mail reader works.
- **Stable ids** make the ledger a durable anchor: re-segmenting the same source
  does not renumber remarks, so ticket references stay valid.
- Companion skill `track-changes-pdf` (tracker 0265) closes the loop by rendering
  a revision-marked PDF grouped by ticket; it lands separately.

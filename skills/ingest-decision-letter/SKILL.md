---
metadata:
  category: publication
name: ingest-decision-letter
description: "Ingest a journal decision letter and reviewer comments into a structured remark ledger, archive the sources, and run a coverage check mapping every remark to a ticket: one deterministic Revise-and-Resubmit intake pass."
user-invocable: true
disable-model-invocation: false
argument-hint: "<decision-letter> <reviewer-comments>... [--release-dir <paper-repo>/release/<date>]"
---

# Ingest decision letter $ARGUMENTS

For helper commands, set `IDH_ROOT="$(cd -P "$(dirname "<loaded-SKILL.md>")/../.." && pwd -P)"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for this skill. This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Take a journal's **Revise-and-Resubmit** decision letter plus each reviewer's
comments, archive them where they will not be lost, parse them into a structured
**remark ledger**, and produce a **coverage check** that records each author decision, any
ticket(s) addressing it, and evidence of resolution. This is
the *inverse* of `external-peer-review` / the `/gaze` prose panel: those review **our**
manuscript; this ingests **the journal's** review of it.

The bundled helper is `"$IDH_ROOT/skills/ingest-decision-letter/ingest_letter.py"`.
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

Once located, **archive first** (next step): re-hunting comments already filed wastes a
whole search. The archive is the single source of truth; never send the author back to a mailbox to re-find them.

## Steps

1. **Locate the sources.** Resolve each path argument. If a source is missing and
   it lived in an email thread, fetch the thread with whatever mail capability the
   project offers and write it to a text file. If you cannot find a source, stop
   and ask the author for the path — do not guess.

2. **Archive to `release/<date>/`.** Paper repos keep an immutable, append-only
   `release/<date description>/` per submission; editorial replies file into the
   release subdir they answer, as tracked text. Copy the sources there:
   ```
   "$IDH_ROOT/skills/ingest-decision-letter/ingest_letter.py" archive \
       decision.pdf reviewer1.txt reviewer2.txt \
       --into <paper-repo>/release/<date>/
   ```
   PDFs are copied verbatim and a `.txt` sidecar of their text is written beside
   them, so the archive stays greppable. A cumulative `manifest.json` preserves entries from earlier intakes;
   repeated basenames get distinct archive paths. Segment the archived copies
   (PDF text sidecars), so ledger sources remain tied to the original intake.
   Commit the archived text in the paper repo (it is durable tracked state).

3. **Segment each reviewer into a candidate ledger.** Run `segment` once per
   reviewer — it splits the comments into candidate remarks with **stable ids**
   (`r1:R1-01`, `r1:R1-02`, … with `--round r1`) and source line locations. Re-running on the same input
   yields the same ids, so the ledger is a stable anchor.
   ```
   "$IDH_ROOT/skills/ingest-decision-letter/ingest_letter.py" segment \
       <release-dir>/reviewer1.txt --reviewer R1 --round r1 > ledger.jsonl
   "$IDH_ROOT/skills/ingest-decision-letter/ingest_letter.py" segment \
       <release-dir>/reviewer2.txt --reviewer R2 --round r1 >> ledger.jsonl
   ```
   The segmenter is a deterministic first pass (it splits on enumeration markers,
   or on paragraphs when the reviewer did not number anything). **Then read the
   extracted text yourself** and refine each record: set `category` (framing /
   method / data / literature / typo / …), fix any remark the segmenter split or
   merged wrongly, and keep the `text` verbatim. This is the one judgment step;
   everything around it is mechanical.

4. **Dedupe atomic-vs-remark.** A reviewer's numbered points often restate one
   underlying remark. `dedupe` folds duplicates and any record you tagged with
   `atomic_of` into its parent, so the distinct-remark count is deterministic:
   ```
   "$IDH_ROOT/skills/ingest-decision-letter/ingest_letter.py" dedupe \
       ledger.jsonl > ledger.dedup.jsonl
   ```
   Distinct remarks are the records whose `atomic_of` is null; folded atomics
   inherit their parent's coverage. Dedupe compares text within each round;
   retain old records and IDs when adding a later round. An explicit `atomic_of`
   must reference a distinct parent in the same round. Malformed references stay
   in the ledger, appear in dedupe diagnostics, and fail coverage as visible
   invalid remarks; coverage validates them even without a preceding dedupe.

5. **Record the author's disposition.** Set `disposition` to `accepted`,
   `rejected`, `deferred`, or `already_addressed`; obtain the author's judgment,
   do not silently accept every objection. Set a nonempty `reason` for rejection
   or deferral. Create thematic tickets for work that needs them and record their
   IDs in `tickets`. A disposition represents a decision even without a ticket.
   Set `resolution` to `resolved` only with nonempty `evidence` references to a
   modification or supporting evidence (commit/path/line, analysis, or audit).
   `already_addressed` requires that resolved state and evidence. A linked ticket
   alone says nothing about resolution; evidence sufficiency still needs review.

6. **Coverage check — one deterministic pass.** Supply the explicit ticket
   universe for this round; `--tickets-dir` checks existence across the project
   and does not add unrelated tickets to the universe:
   ```
   "$IDH_ROOT/skills/ingest-decision-letter/ingest_letter.py" coverage \
       ledger.dedup.jsonl --round r1 --tickets 0301,0302 --tickets-dir tickets/
   ```
   Use `--tickets ''` for a round with no tickets. The report lists, and exits 1 on,
   `uncovered_remarks` (neither disposition nor legacy ticket mapping),
   `invalid_records` (unknown disposition/state, missing required rationale or
   evidence), `orphan_tickets` (unused round tickets), `unknown_ticket_refs`
   (referenced or declared round tickets absent from the existence index),
   `out_of_round_ticket_refs`, and `duplicate_ids`. Without `--tickets-dir`, the
   explicit universe is also the existence index. `unresolved_remarks` is reported
   separately and does **not** fail decision coverage. A clean coverage check is
   therefore neither scientific approval nor proof that revision work is complete.

## Ledger / consumer interface

Reuse this JSONL ledger for journal or AI review; no second remark schema is
needed. `read_ledger`, `write_ledger`, `dedupe`, and `coverage` preserve these fields:

| Field | Meaning |
|-------|---------|
| `id` | stable `<round>:<reviewer>-<NN>` for newly segmented rounds |
| `round` | round label, e.g. `r1`; absent legacy value becomes `""` |
| `reviewer` | reviewer label, e.g. `R1` |
| `category` | assigned framing / method / data / literature / typo / … |
| `text` | verbatim remark text |
| `source` | archived source path and starting line |
| `tickets` | list of ticket IDs addressing this remark; may be empty |
| `atomic_of` | parent remark ID, or `null` for a distinct remark |
| `disposition` | `accepted`, `rejected`, `deferred`, `already_addressed`, or `null` |
| `reason` | author rationale; required for rejected/deferred |
| `resolution` | `open` (default) or `resolved` |
| `evidence` | list of reference strings; required for resolved/already_addressed |

Example record for a justified disagreement without a fabricated ticket:
```json
{"id":"r1:R1-01","round":"r1","reviewer":"R1","category":"method","text":"Use method X.","source":"release/r1/reviewer1.txt:1","tickets":[],"atomic_of":null,"disposition":"rejected","reason":"X assumes independent observations; these are paired.","resolution":"resolved","evidence":["response.tex:42"]}
```

CLI consumers use `segment ... --round r1`, edit these known fields in the JSONL,
then `coverage ... --round r1 --tickets ... [--tickets-dir ...]`. Coverage emits
JSON on stdout and exits 0 for clean decision coverage, 1 for findings. Python
consumers call `coverage(records, universe, existing_tickets=None, round_id=None)`
and `coverage_ok(report)`. Old ledgers retain their IDs and ticket-based coverage;
new fields receive empty/default values. When combining legacy rounds, assign
`round` explicitly without renumbering existing IDs and check each round with
`--round`. Unsupported extra fields are not retained: link external critique or
review artifacts from `evidence` instead. Never overwrite an annotated ledger by
re-segmenting its source.

## Notes

- **Pure I/O helper.** The script never calls a model; the one judgment step
  (categories, mapping, fixing a mis-split remark) is yours.
- **Tool-agnostic.** The email-thread path is a capability, not a fixed tool —
  the archived text file is the interface, so any mail reader works.
- **Stable ids** make the ledger a durable anchor: re-segmenting the same source
  does not renumber remarks, so ticket references stay valid.
- Companion skill `track-changes-pdf` (tracker 0265) closes the loop by rendering
  one revision-marked PDF between two git refs. Its v1 does not group by
  ticket; ledger evidence can reference the PDF and relevant manuscript locations.

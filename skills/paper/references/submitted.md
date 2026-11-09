# submitted

The manuscript has left: uploaded to the venue's platform or mailed.

## Registers

- Roadmap: yes, the row moves to "soumis à <venue> le <date>".
- Publications list: only for a preprint the author chooses to announce, as a
  preprint entry typed per `/update-publist`'s status table. A book proposal or
  a dossier never gets an entry at this stage.

## Provenance

The frozen copies are what the venue received: the PDF and attachments as
uploaded, the cover letter as sent. Take them from the sent mail or the
platform's submission record, not from a fresh build; hash each one.

## Filesystem

1. Paper repo: submission branch, git tag for the event (for instance
   `v1.1-<venue>-submitted`), STATE line, release-journal entry naming the
   platform, the files uploaded, the deposits and the tag.
2. `~/CNRS/papiers/actif/<manuscript>/<date venue>/`: PDF, cover letter,
   statements (AI use, data availability), `SHA256SUMS`. Move the manuscript
   folder to `papiers/sent/` once the submission is acknowledged.

## Outward gates (who clicks)

- Platform upload and cover letter: the author.
- Preprint on the homepage: `/update-publist --page-only`, `make sync` after
  the author confirms the diff.
- HAL preprint deposit: `/update-publist --hal-only`, the author approves the
  payload before the POST.

## Delegates

- `/pdf-finish` on the submitted PDF before upload.
- `/update-publist` for the page and HAL, when a preprint is announced.

## Author-only (ask, do not drop)

- Was a Zenodo or data deposit made, and which DOI does the paper cite?
- Known errata in the as-sent files (record them, never edit the frozen copy).
- Co-authors informed of the submission.

## Done when

Roadmap row updated; frozen folder holds the authentic uploads with hashes; tag
and release-journal entry exist; any announced preprint lands on its own
version.

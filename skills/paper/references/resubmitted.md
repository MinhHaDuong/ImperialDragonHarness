# resubmitted

A revised manuscript and its response to reviewers have gone back to the venue.

## Registers

- Roadmap: yes, "revision submitted on <date>".
- Publications list: update an existing preprint entry to the revised version
  only if the author announces revisions; the type follows
  `/update-publist`'s status table.

## Provenance

The frozen copies are what was uploaded: revised PDF, response letter,
tracked-changes PDF. Take them from the platform or sent mail; hash each.

## Filesystem

1. Paper repo: tag the event (`v<n>-<venue>-r<round>`), file the response
   letter in `release/<date>/`, STATE line, release-journal entry naming `prior_deposit_check` (the block of
   update-publist's step 2a-0).
2. Manuscript folder, new dated event subfolder: revised PDF, response
   letter, diff PDF, `SHA256SUMS`.

## Outward gates (who clicks)

- Platform upload: the author.
- Revised preprint on the homepage: `/update-publist --page-only`; its
  deploy (`make sync`) runs after the author confirms.
- HAL new version: `/update-publist --hal-only`; an update to an existing
  deposit is a PUT, never a second POST (the procedure lives there).

## Delegates

- `/track-changes-pdf` for the revision-marked PDF between the submitted and
  revised tags.
- `/pdf-finish` on the revised PDF.
- `/ingest-decision-letter` coverage check: every remark resolved before upload.

## Author-only (ask, do not drop)

- Does the response letter say what the author wants said to each reviewer?
- Updated data deposit (new Zenodo version) cited in the revision?
- Co-authors' sign-off on the revision.

## Done when

Coverage check clean; frozen folder holds the authentic uploads with hashes;
roadmap row updated; any refreshed link lands on the revised version.

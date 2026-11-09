# published

The publisher's version of record is out, with its DOI.

## Registers

- Roadmap: yes, "paru dans <venue> <volume>, <pages>, DOI <doi>".
- Publications list: yes, the entry gains volume, pages and DOI; type per
  `/update-publist`'s status table.

## Provenance

The publisher's PDF downloaded from the DOI landing page, and the publication
mail. Neither is rebuilt or renamed in place; hash both.

## Filesystem

1. Create `~/CNRS/papiers/sent/<manuscript>/<date venue published>/` with the
   publisher PDF and the publication mail; write `SHA256SUMS` beside them.
2. Move the manuscript folder `~/CNRS/papiers/sent/<manuscript>/` →
   `~/CNRS/papiers/published/<manuscript>/`.
3. Paper repo: git tag for the published version, STATE line.

## Outward gates (who clicks)

4. Swap the hosted preprint for the publisher PDF under the same filename in
   `~/CNRS/html/files/`, when the licence allows redistribution; update the bib
   entry (volume, pages, DOI, type per the status table). Both via
   `/update-publist --page-only`; `make sync` runs after the author confirms.
5. Check the publisher's HTML landing-page metadata (title, authors, abstract)
   against the PDF; report any drift to the author, who decides whether to
   write to the journal.
6. HAL: add the version of record via `/update-publist --hal-only`. An update
   is a PUT on the existing deposit, never a second POST; the author approves
   the payload.
7. Roadmap row updated and its PDF regenerated.
8. Fetch the DOI and every link written in steps 4-7; each lands on the
   published version.

## Delegates

- `/update-publist` for steps 4 and 6.
- `/pdf-finish` only if the hosted file is a re-export rather than the
  publisher's PDF.

## Author-only (ask, do not drop)

- Zotero: index the publisher PDF and supporting material (data, appendix).
- Co-authors informed, with the DOI.
- Zenodo or data deposit: add the article DOI as a related identifier.
- Release-journal entry in the paper repo.

## Done when

Steps 1-8 done or explicitly waived by the author; every author-only item has an
answer; the homepage, HAL and the roadmap all point to the published version.

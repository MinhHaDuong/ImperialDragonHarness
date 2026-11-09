# accepted

The venue accepted the paper, or the publisher signed the book contract
("contract signed" is the book trigger for this stage).

## Registers

- Roadmap: yes, "accepted on <date>, expected in print <when>".
- Publications list: yes, the work now exists. Create or retype the entry per
  `/update-publist`'s status table (an accepted article leaves the preprint
  type).

## Provenance

The acceptance mail and the accepted manuscript as the venue holds it. The
author's accepted version (post-review, pre-typesetting) is the file a green
open-access deposit may carry; take it from the last upload, not a rebuild.

## Filesystem

1. Paper repo: tag the accepted version, STATE line, release-journal entry naming `prior_deposit_check` (the block of
   update-publist's step 2a-0).
2. Manuscript folder, new dated event subfolder: acceptance mail, accepted
   manuscript, signed licence or contract, `SHA256SUMS`.

## Outward gates (who clicks)

- Publisher forms (licence, copyright transfer, APC waiver): the author.
- Homepage entry: `/update-publist --page-only`; its deploy (`make sync`)
  runs after the author confirms.
- HAL: deposit or update the author's accepted version via
  `/update-publist --hal-only` (PUT on an existing deposit), embargo per the
  licence. Confirm against How-to 44: this step is inferred, not yet checked
  against the author's checklist.

## Delegates

- `/update-publist` for the page entry and HAL.
- `/pdf-finish` on the accepted version if it is deposited.

## Author-only (ask, do not drop)

- Licence chosen and its embargo, if any.
- Proofs schedule and who answers the typesetter.
- Co-authors informed; acknowledgements and funding lines final.

## Done when

Entry retyped and live on its own version; roadmap row updated; acceptance mail
and licence frozen with hashes; the HAL step done or its embargo recorded.

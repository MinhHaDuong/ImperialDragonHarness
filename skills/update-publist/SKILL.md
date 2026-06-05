---
name: update-publist
description: Add or update a publication on the personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call.
disable-model-invocation: false
user-invocable: true
argument-hint: <pdf-path> [--hal-only] [--page-only]
---

# Update publication list

Two independent steps, either runnable alone via flags. Both are
outward-facing and irreversible once completed — every mutation requires
explicit user confirmation before execution.

## Step 1: Personal page (`~/CNRS/html/`)

This directory is NOT a git repo. It deploys over FTP.

1. Copy the PDF into `files/`, naming it `HaDuong-YYYY-Topic.pdf`.
   Use a `-EN` suffix for English translations.

2. Add the BibTeX entry to `src/Ha-Duong.bib`. The page section is
   driven by the entry type:
   - `inproceedings` maps to Scientific communications
   - `unpublished` maps to Teaching and conferences
   - See `TYPE_HEADINGS` in `src/bib2htm.py` for the full mapping.
   Required fields: `file = {files/HaDuong-YYYY-Topic.pdf}`. Add
   `eprint = {https://hal.science/hal-XXXXXXXvN}` after HAL deposit.

3. **Translation pairs.** For a translated work:
   - The translation key gets an `:EN` suffix.
   - On the translation: `related = {OriginalKey}`,
     `relatedtype = {translationof}`.
   - On the original: `related = {TranslationKey:EN}`,
     `relatedtype = {translatedin}`.
   - The renderer merges them into one item (translation first, original
     bracketed). Disambiguate identical titles with a marker like
     "(En francais)".

4. Build and verify:
   ```
   cd ~/CNRS/html && make index.html && make files/Ha-Duong.bib
   ```
   Verify the entry appears in the correct section (`grep` the output).

5. **Publish (user confirmation required):**
   ```
   make sync
   ```
   This runs FTP using credentials from `~/.netrc`. Show the user what
   will be synced and wait for explicit confirmation before running.

## Step 2: HAL deposit via SWORD

Credentials: `HAL_ID` and `HAL_PASSWORD` from the project `.env`.
**Never echo, display, log, or commit credential values.** Pass them
to curl via a chmod-600 temporary config file (`curl -K`), never on the
command line. Mask `<hal:password>` in any displayed API response.

### 2a. Prepare the TEI metadata

Use the AOfr TEI format (template reference:
`https://api.archives-ouvertes.fr/documents/all.xml`).

Before choosing doctype and domain, check the author's previous deposits
via the public search API to follow established conventions:
```
curl -s 'https://api.archives-ouvertes.fr/search/hal/?q=authIdHal_s:minh-ha-duong&fl=docType_s,domain_s&rows=5'
```

Standard values for this author:
- Structure: `#struct-1380080` (CIRED)
- idhal: `minh-ha-duong`
- Typology: `COMM` for a conference talk (adjust per doctype)

### 2b. Assemble and review the payload

Build `meta.xml` (the TEI document) and zip it with the PDF.

**MANDATORY GATE: show the user the full assembled payload** — the
complete `meta.xml` TEI content and the zip manifest — and wait for
explicit confirmation before any API call. The user reviews:
- TEI well-formedness and field accuracy
- Correct structure reference (`#struct-1380080`)
- Correct typology and domain
- Correct idhal

Do NOT proceed to the POST without user approval.

### 2c. Deposit

```
curl -K "$TMPCONFIG" \
  -X POST https://api.archives-ouvertes.fr/sword/hal/ \
  -H 'Content-Type: application/zip' \
  -H 'Content-Disposition: attachment; filename=deposit.zip' \
  -H 'Packaging: http://purl.org/net/sword-types/AOfr' \
  --data-binary @deposit.zip
```

Where `$TMPCONFIG` is a chmod-600 temp file containing:
```
user = "HAL_ID_VALUE:HAL_PASSWORD_VALUE"
```
Delete the temp config immediately after the curl call.

The SWORD acknowledgement means "stored in workspace" — moderation
status is confirmed by HAL's email, not the API response.

### 2d. Post-deposit

After a successful deposit, update the BibTeX entry in
`src/Ha-Duong.bib` with the `eprint` field pointing to the new HAL
record, then rebuild the personal page (Step 1.4-1.5).

## Credential safety rules

These are non-negotiable:
- Never display `HAL_ID` or `HAL_PASSWORD` values in chat output.
- Never include credentials in git-tracked files.
- Pass credentials to curl via `-K` with a chmod-600 temp file only.
- Mask any credential that appears in API responses before displaying.
- Delete temp credential files immediately after use.

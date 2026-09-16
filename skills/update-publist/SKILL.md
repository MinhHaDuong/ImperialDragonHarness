---
name: update-publist
description: "Add or update a publication on the personal page and deposit on HAL via SWORD. Gated on user payload review before any outward API call."
disable-model-invocation: true
user-invocable: true
argument-hint: "<pdf-path> [--hal-only] [--page-only]"
---

# Update publication list

Two independent steps, either runnable alone via flags (`--page-only`
runs Step 1 only; `--hal-only` runs Step 2 only). Both are
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

   Pick the type from the publication's *status*, not its venue:

   | Status | Type | Notes |
   |--------|------|-------|
   | Peer-reviewed and accepted | `@article` | `journaltitle`, `doi` |
   | Under review / preprint | `@techreport` | `type` = "Preprint, under review at {Journal}". **No** `institution` field |
   | CIRED Working Paper series | `@techreport` | The only case that gets `institution = {CIRED}` |
   | Conference presentation | `@inproceedings` | `booktitle`, `location`, `date` |
   | Dataset | `@misc` | `howpublished = {Zenodo}`, `doi` |
   | Book | `@book` | `publisher`, `isbn` |

   The preprint/CIRED-WP split is the one that gets fixed wrong: an
   `institution` field on a preprint makes the page render it as
   CIRED-published work it is not.

   Field conventions: `doi` bare, no URL prefix (`10.5281/zenodo.19097045`);
   `date` in ISO form (`2026-03-18`); `eprint` the full HAL URL.

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

Credentials: `HAL_ID` and `HAL_PASSWORD` live in `~/.config/keys/hal.env` and
are resolved **at point of use**, one variable per call, by
`~/.claude/skills/update-publist/resolve_hal_credentials.sh` — see § 2c, which
is the only place in this skill that runs it.

The ambient environment is **no longer consulted**: a `HAL_ID` or
`HAL_PASSWORD` already exported in the shell does not take precedence and has
no effect at all. That is deliberate. Their presence used to depend on the
`KEYS=` selection in force, and a project `KEYS=` **replaces** the harness one
rather than adding to it (ticket 0360), so the deposit failed as an ordinary
HAL auth error whenever it was run from a project whose `.env` carried its own
`KEYS=` line. Point-of-use resolution bypasses that layer, so there is nothing
left to probe for before starting: the resolver itself fails loud and named,
and covers the cases a presence probe never did (missing or malformed
`hal.env`, a variable defined but empty).

**Never echo, display, log, or commit credential values.** Pass them
to curl via a chmod-600 temporary config file (`curl -K`), never on the
command line. Mask `<hal:password>` in any displayed API response.

### Pre-upload PDF review (GATE)

Read **every page** of the PDF with vision before building any metadata.
This checks the *document*; the 2b gate checks the *payload*, and neither
substitutes for the other — a well-formed TEI can wrap an anonymized draft.

- The author's name appears in the document (no "[Anonymous]", no
  anonymized review version).
- Affiliations are present and will match the HAL metadata.
- No placeholder text and no draft watermark contradicting the deposit
  status.
- The file is complete: all pages, figures and tables render.
- Nothing sensitive is embedded — API keys, personal addresses beyond
  the correspondence one.

Guidelines: https://doc.hal.science/en/deposit/

Only proceed once the review passes.

### 2a. Prepare the TEI metadata

Use the AOfr TEI format (template reference:
`https://api.archives-ouvertes.fr/documents/all.xml`).

Before choosing doctype and domain, check the author's previous deposits
via the public search API to follow established conventions:
```
curl -s 'https://api.archives-ouvertes.fr/search/hal/?q=authIdHal_s:minh-ha-duong&fl=docType_s,domain_s&rows=5'
```

Standard values for this author:
- Structure: `#struct-1380080` (CIRED). **Verified against the HAL ref API,
  2026-07-27** — a fork of this skill carried `struct-1002424`, which
  resolves to ECOSYS, an unrelated laboratory. Do not "correct" this id
  from another document; re-verify it instead:
  `curl -s 'https://api.archives-ouvertes.fr/ref/structure/?q=docid:1380080&fl=docid,name_s,acronym_s&wt=json'`
- ORCID: `0000-0001-9988-2100`
- idhal: `minh-ha-duong`
- Typology: `COMM` for a conference talk (adjust per doctype)
- Stamps: CIRED, CNRS
- Domains: `shs.eco`, `shs.hisphilso` (adjust per paper)
- File reference in the TEI:
  `<ref type="file" target="paper.pdf" subtype="author" n="1"/>`

For a journal article, resolve the journal's HAL id rather than typing
the title into the TEI:
```
curl -s 'https://api.archives-ouvertes.fr/ref/journal/?q=title_t:{name}&fl=docid,title_s,valid_s&wt=json'
```
Use the `docid` as `halJournalId`, and prefer an entry whose `valid_s`
is `VALID`.

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

Resolve the two credentials immediately before building `$TMPCONFIG`, into
shell variables that go into that chmod-600 file and nowhere else:

```
RESOLVE=~/.claude/skills/update-publist/resolve_hal_credentials.sh
HAL_ID_VALUE="$("$RESOLVE" HAL_ID)" || exit $?
HAL_PASSWORD_VALUE="$("$RESOLVE" HAL_PASSWORD)" || exit $?
```

**Guard each call separately, and let the resolver's stderr reach you** — do
not redirect it away, and do not collapse the two calls into one unguarded
line. A partial resolution (`HAL_ID` resolves, `HAL_PASSWORD` does not) builds
a half-empty config and comes back as an HAL *auth* error, one layer away from
the real cause.

**The stderr line is what tells you what went wrong**, and it is the one to
read back to the user: one line naming the VARIABLE and the FILE, never a
value. The exit code is a coarse companion — `1` bad argument, `2` keystore
file missing or unreadable, `3` keystore file could not be sourced or did not
run to completion, `4` variable absent or defined-but-empty — and `|| exit $?`
above is what keeps it, rather than flattening every case to 1.

```
curl -K "$TMPCONFIG" \
  -X POST https://api.archives-ouvertes.fr/sword/hal/ \
  -H 'Content-Type: application/zip' \
  -H 'Content-Disposition: attachment; filename=deposit.zip' \
  -H 'Packaging: http://purl.org/net/sword-types/AOfr' \
  --data-binary @deposit.zip
```

Where `$TMPCONFIG` is created with `mktemp` in `/tmp` (outside the
repo tree), chmod-600'd, and cleaned up via `trap 'rm -f "$TMPCONFIG"' EXIT`
so it is deleted even on error or interruption. Write it with a redirect —
never by echoing the line to the terminal first:
```
_kesc() { local s=${1//\\/\\\\}; printf '%s' "${s//\"/\\\"}"; }
printf 'user = "%s:%s"\n' "$(_kesc "$HAL_ID_VALUE")" "$(_kesc "$HAL_PASSWORD_VALUE")" \
  > "$TMPCONFIG"
```
Two properties of that line, both load-bearing. `printf` is a shell builtin, so
the values never reach a process argv where `ps -ef` could read them — which
`echo` via an external command, or `curl -u user:pass`, would. And a `curl -K`
quoted string is backslash-escaped, so a `"` or `\` inside a password would
otherwise terminate the string and turn the rest of the credential into curl
*directives*; `_kesc` escapes both, backslash first.

**Dry run first.** The same request with `-H "X-test: 1"` validates the
package without creating a record. Run it, read the response, and only
then repeat without the header.

**Updating an existing deposit** is the same request as a `PUT` to
`https://api.archives-ouvertes.fr/sword/hal/{hal-id}`. Use it rather
than a second POST — a second POST creates a duplicate record, and
duplicates need moderator action to merge.

The SWORD acknowledgement means "stored in workspace" — moderation
status is confirmed by HAL's email, not the API response.

### 2d. Post-deposit

After a successful deposit, update the BibTeX entry in
`src/Ha-Duong.bib` with the `eprint` field pointing to the new HAL
record, then rebuild the personal page (Step 1.4-1.5).

If the run happened inside a project that tracks HAL ids in its
`STATE.md`, update them there too — a stale HAL id in project state is
the usual way a second deposit gets made for a record that already
exists.

## Credential safety rules

These are non-negotiable:
- Never display `HAL_ID` or `HAL_PASSWORD` values in chat output.
- Never include credentials in git-tracked files.
- Pass credentials to curl via `-K` with a chmod-600 temp file only.
- Mask any credential that appears in API responses before displaying.
- Delete temp credential files immediately after use.

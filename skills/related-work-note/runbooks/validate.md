# Related-work-note validator (runbook)

For helper commands, set `IDH_ROOT="${IDH_ROOT:-$(p="<loaded-SKILL.md>"; [ -d "$p" ] || p=$(dirname "$p"); cd -P "$p/../.." && pwd -P)}"` in the same shell call. Replace `<loaded-SKILL.md>` with the absolute path the runtime supplied for the parent skill, its SKILL.md or its directory; a pre-set `IDH_ROOT` wins (this runbook sits under `skills/<parent>/runbooks/`, so anchor on the parent's `SKILL.md`, not on this file). This follows a projected skill symlink to the canonical checkout; do not derive the helper root from the project cwd.

Check HTTP accessibility of every identifier in the note's Bibliography. Flag entries
with no DOI, URL, or eprint as unverifiable. Append a single provenance
bullet to the `## Methods` section. Print a one-line verdict to stdout.

## Constraints (non-obvious)

- **Append-only.** Use `Edit` to add one bullet to Methods. Never
  rewrite the note with `Write`. Never touch cited-work bodies or
  the Bibliography section.
- **Three verdicts.** PASS (all accessible via HTTP), WARN (some entries have
  no identifier), FAIL (at least one fetch failed).
- **Network errors are not citation failures.** Three consecutive
  connection errors → script exits with code 2 (escalate, not FAIL).
- **One-line stdout.** Downstream tooling greps it:
  `PASS — {N} entries accessible via HTTP`, `WARN: {U} of {N} entries have no DOI/URL`, or
  `FAIL: {K} fetch failures` — followed by the note path.
  PASS has no path suffix. Nothing else on stdout.
- **Abort, don't guess.** If the file lacks `## Bibliography` or
  `## Methods`, stop with an error.

A PASS reports HTTP accessibility only (response below 400). A redirect or
HTTP 200 can lead to another work or an access page. Record four separate
checks in the note: accessibility (this script), work identity (compare
author/title/date and identifier metadata), relevance (read the work for
the paragraph), and claim support (locate the supporting passage/page).
Do not infer any of the latter three from PASS.

## Identifier fields to check

`doi`, `url`, `eprint`+`eprinttype` (arXiv/HAL). Prefer DOI when
multiple are present. Entries with none of these → unverifiable.

## Step 1 — run the validator script (exactly one Bash call)

```
uv run --script "$IDH_ROOT/scripts/validate-refs.py" <note-file>
```

The helper declares its runtime dependencies in PEP 723 metadata. `uv run
--script` resolves them independently of the current paper repository and its
Python environment; no harness virtualenv activation is needed. Directly
executing the helper path uses the same uv entry point through its shebang.

The script:
- Uses the existing `bibtexparser` dependency to parse inline, multiline and
  BibLaTeX entries; macros are expanded. A plausible entry that cannot be read
  aborts with exit 3 before fetching any identifiers. The conservative opening
  count can also flag an ambiguous `@type{` inside a comment or field: inspect
  the source rather than interpreting that error as a citation failure.
- Parses `## Bibliography`, extracts `doi`/`url`/`eprint`+`eprinttype`
- Resolves each: DOI via `https://doi.org/`, arXiv via `https://arxiv.org/abs/`,
  HAL via `https://hal.science/`, plain URL directly
- Per-entry detail lines go to **stderr** (`[OK|WARN|FAIL] key: url (status)`)
- Final verdict goes to **stdout** (single greppable line)
- Exit 0 = PASS or WARN, exit 1 = FAIL, exit 2 = network escalation, exit 3 = parse error

Capture both stdout (verdict) and stderr (per-entry detail) separately.

## Step 2 — append provenance bullet to Methods (LLM, always)

Use `Edit` to append one bullet to `## Methods`:

```
- **Validator (HTTP accessibility).** {VERDICT} — {summary}.
  Checked {YYYY-MM-DDThh:mmZ} by related-work-note-validate.
```

Fill `{VERDICT}` from the script's stdout. Fill `{summary}` with
counts from stderr (e.g., "3 OK, 1 unverifiable, 0 failed").

If the script exits 3, report the unread input and stop validation; do not
record a partial PASS or WARN. Identity, relevance and claim-support checks
still require their own evidence.

## Step 3 — annotate failures (LLM, only on FAIL or escalation)

If the script exits 1 (FAIL): for each `[FAIL]` line from stderr,
suggest a corrected identifier or note why the URL may be broken.

If the script exits 2 (network escalation): report the network
issue and ask the user to retry later. Do not mark entries as failed.

## Methods bullet format

```
- **Validator (HTTP accessibility).** {VERDICT} — {summary}.
  Checked {YYYY-MM-DDThh:mmZ} by related-work-note-validate.
```

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "bibtexparser>=1.4,<2",
# ]
# ///
"""bib-merge.py — merge BibTeX entries into refs.bib with deduplication.

Usage:
    uv run --script bib-merge.py <new-entries-file> <refs.bib>
    uv run --script bib-merge.py - <refs.bib>        # read new entries from stdin
    uv run --script bib-merge.py <note-file> <refs.bib>  # extracts ```bibtex fence

The script reads BibTeX entries from <new-entries-file> (or stdin if '-'),
deduplicates them against <refs.bib>, and appends non-duplicate entries to
<refs.bib>. Both refs.bib and the note file are never created by this script.

Input auto-detection:
    If the input contains a ```bibtex fence (as in a related-work-note's
    ## Bibliography section), the fence contents are extracted. Otherwise
    the whole input is treated as BibTeX.

Deduplication strategy:
    First check: normalized DOI across all entries, regardless of author/year.
    Fallback group: normalized(first-author-last-name) + year (or date year).
    Confirmation:
      - If both entries have DOI → DOI equality (normalized) decides.
        Matching DOI → SKIPPED (duplicate). Differing DOI → different works,
        suffix-bump the new key (RENAMED).
      - If either entry lacks DOI → fall back to title word-overlap (Jaccard).
        Overlap >= 0.8 → SKIPPED (duplicate). Below threshold → RENAMED.
    Key collision (same base key, confirmed NOT duplicate) → bump suffix b/c/d...

Per-entry output:
    [ADDED] @key
    [SKIPPED] @key  (duplicate of existing @existingkey)
    [RENAMED->newkey] @key

Summary:
    bib-merge: <new-entries-file> -> <refs.bib>
      added:    N
      skipped:  K  (duplicates)
      renamed:  R  (key collisions)
      errors:   E  (malformed entries)

Exit codes:
    0 — success (even if all entries skipped)
    1 — usage error or refs.bib missing
    2 — input file missing
    3 — unread or malformed BibTeX (nothing appended)
"""

import re
import sys
import unicodedata
from pathlib import Path

# Parse with the existing bibtexparser dependency; serialize only new entries.
import bibtexparser
from bibtexparser.bibdatabase import BibDatabase, UndefinedString
from bibtexparser.bparser import BibTexParser


def _extract_bibtex_fence(text: str) -> str:
    """Extract all BibTeX fences if present; otherwise use the entire input."""
    fences = re.findall(r"```bibtex\s*\n(.*?)```", text, re.DOTALL | re.IGNORECASE)
    return "\n".join(fences) if fences else text


def parse_bibtex(text: str) -> list[dict]:
    """Parse entries or explicitly reject unread input before any append.

    The conservative opening-count guard follows zotero._bib_entries: the
    library otherwise treats malformed entries as comments and drops them.
    """
    parser = BibTexParser(common_strings=True, ignore_nonstandard_types=False)
    try:
        entries = bibtexparser.loads(text, parser).entries
    except UndefinedString as exc:
        raise ValueError(f"undefined @string macro {exc}") from exc
    declared = sum(1 for m in re.finditer(r"@\s*(\w+)\s*[{(]", text)
                   if m.group(1).lower() not in {"string", "preamble", "comment"})
    if declared != len(entries):
        raise ValueError(f"{declared} declared BibTeX entries; {len(entries)} read — "
                         "some entries could not be parsed (or ambiguous @type opening)")
    result = []
    for entry in entries:
        database = BibDatabase()
        database.entries = [entry]
        result.append({**{k.lower(): v for k, v in entry.items()
                          if k not in {"ID", "ENTRYTYPE"}},
                       "_key": entry["ID"], "_type": entry["ENTRYTYPE"],
                       "_raw": bibtexparser.dumps(database)})
    return result


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def _normalize_doi(doi: str) -> str:
    """Lowercase and strip common DOI URL prefixes."""
    doi = doi.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "http://dx.doi.org/", "https://dx.doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix) :]
    return doi


def _normalize_name(name: str) -> str:
    """Extract lowercase ASCII first-author last name."""
    # Strip braces and LaTeX accents
    name = re.sub(r"[{}]", "", name)
    name = re.sub(r"\\[a-zA-Z]+\s*", "", name)
    # Take first author (split on ' and ')
    authors = re.split(r"\s+and\s+", name, flags=re.IGNORECASE)
    first = authors[0].strip()
    # Handle "Last, First" vs "First Last"
    if "," in first:
        last = first.split(",")[0].strip()
    else:
        parts = first.split()
        last = parts[-1] if parts else first
    # Normalize to ASCII
    last = unicodedata.normalize("NFD", last)
    last = "".join(c for c in last if unicodedata.category(c) != "Mn")
    last = re.sub(r"[^a-z0-9]", "", last.lower())
    return last or "unknown"


def _base_key(entry: dict) -> str:
    """Compute fallback dedup group using year or the year in a BibLaTeX date."""
    author = entry.get("author", entry.get("editor", ""))
    year = entry.get("year") or entry.get("date", "")
    year = re.sub(r"[^0-9]", "", year)[:4]
    return _normalize_name(author) + year


def _title_words(title: str) -> set[str]:
    """Lowercase word set for Jaccard similarity."""
    return set(re.findall(r"[a-z0-9]+", title.lower()))


def _title_similarity(a: str, b: str) -> float:
    """Jaccard word-overlap similarity between two titles."""
    wa = _title_words(a)
    wb = _title_words(b)
    if not wa and not wb:
        return 1.0
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _bump_suffix(key: str, existing_keys: set[str]) -> str:
    """Append 'b', 'c', ... until the key is unique."""
    if key not in existing_keys:
        return key
    for ch in "bcdefghijklmnopqrstuvwxyz":
        candidate = key + ch
        if candidate not in existing_keys:
            return candidate
    # Last resort: numeric suffix
    n = 2
    while True:
        candidate = f"{key}{n}"
        if candidate not in existing_keys:
            return candidate
        n += 1


# ---------------------------------------------------------------------------
# Deduplication logic
# ---------------------------------------------------------------------------

TITLE_THRESHOLD = 0.8


def _is_duplicate(new_entry: dict, existing_entry: dict) -> bool:
    """Return True if new_entry and existing_entry represent the same work."""
    doi_new = _normalize_doi(new_entry.get("doi", ""))
    doi_old = _normalize_doi(existing_entry.get("doi", ""))

    if doi_new and doi_old:
        return doi_new == doi_old  # DOI equality is authoritative

    # Fallback: title similarity
    title_new = new_entry.get("title", "")
    title_old = existing_entry.get("title", "")
    if title_new and title_old:
        return _title_similarity(title_new, title_old) >= TITLE_THRESHOLD

    return False  # cannot confirm — treat as different


# ---------------------------------------------------------------------------
# Main merge logic
# ---------------------------------------------------------------------------


def merge(
    new_entries: list[dict],
    refs_entries: list[dict],
    refs_path: Path,
    dry_run: bool = False,
) -> list[str]:
    """Merge new_entries into refs_entries / refs_path. Return report lines."""
    # Build lookup structures from existing refs
    existing_keys: set[str] = {e["_key"] for e in refs_entries}
    # base_key -> list of existing entries with that base key
    existing_by_base: dict[str, list[dict]] = {}
    existing_by_doi: dict[str, dict] = {}
    for e in refs_entries:
        bk = _base_key(e)
        existing_by_base.setdefault(bk, []).append(e)
        doi = _normalize_doi(e.get("doi", ""))
        if doi:
            existing_by_doi.setdefault(doi, e)

    report: list[str] = []
    to_append: list[str] = []
    counts = {"added": 0, "skipped": 0, "renamed": 0, "errors": 0}

    for entry in new_entries:
        key = entry.get("_key", "")
        if not key or entry.get("_type") in ("string", "preamble", "comment"):
            continue
        if "_raw" not in entry:
            report.append(f"[ERROR] @{key}  (malformed — no raw text)")
            counts["errors"] += 1
            continue

        bk = _base_key(entry)
        candidates = existing_by_base.get(bk, [])

        # Check for duplicate among base-key candidates
        doi = _normalize_doi(entry.get("doi", ""))
        dup_match = existing_by_doi.get(doi) if doi else None
        for cand in candidates if dup_match is None else []:
            if _is_duplicate(entry, cand):
                dup_match = cand
                break

        if dup_match is not None:
            report.append(f"[SKIPPED] @{key}  (duplicate of @{dup_match['_key']})")
            counts["skipped"] += 1
            continue

        # Not a duplicate — determine final key
        final_key = key
        renamed = False

        if key in existing_keys:
            # Key collision — different work, need suffix
            final_key = _bump_suffix(bk, existing_keys)
            if final_key == key:
                final_key = _bump_suffix(key, existing_keys)
            renamed = True

        # Check if the base key itself collides with an existing key (new key)
        if not renamed and bk != key and bk in existing_keys:
            # bk is taken by a different work; use bumped bk
            final_key = _bump_suffix(bk, existing_keys)
            # Only mark as renamed if the key actually changed
            renamed = final_key != key

        existing_keys.add(final_key)
        indexed_entry = {**entry, "_key": final_key}
        existing_by_base.setdefault(bk, []).append(indexed_entry)
        if doi:
            existing_by_doi.setdefault(doi, indexed_entry)

        # Rewrite key in raw text if renamed
        raw = entry["_raw"]
        if renamed:
            raw = re.sub(
                r"(@\w+\s*\{)\s*" + re.escape(key) + r"\s*,",
                r"\g<1>" + final_key + ",",
                raw,
                count=1,
            )
            report.append(f"[RENAMED->{final_key}] @{key}")
            counts["renamed"] += 1
        else:
            report.append(f"[ADDED] @{final_key}")
            counts["added"] += 1

        to_append.append(raw)

    if not dry_run and to_append:
        with refs_path.open("a") as fh:
            for raw in to_append:
                fh.write("\n")
                fh.write(raw.strip())
                fh.write("\n")

    summary = [
        f"bib-merge: -> {refs_path}",
        f"  added:   {counts['added']}",
        f"  skipped: {counts['skipped']}  (duplicates)",
        f"  renamed: {counts['renamed']}  (key collisions)",
        f"  errors:  {counts['errors']}  (malformed entries)",
    ]
    return summary + report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 1

    new_file_arg = argv[1]
    refs_arg = argv[2]
    dry_run = "--dry-run" in argv

    # Read refs.bib
    refs_path = Path(refs_arg)
    if not refs_path.exists():
        print(f"ERROR: refs.bib not found: {refs_path}", file=sys.stderr)
        return 1

    # Read new entries input
    if new_file_arg == "-":
        raw_new = sys.stdin.read()
        source_label = "<stdin>"
    else:
        new_path = Path(new_file_arg)
        if not new_path.exists():
            print(f"ERROR: input file not found: {new_path}", file=sys.stderr)
            return 2
        raw_new = new_path.read_text()
        source_label = str(new_path)

    # Auto-detect and extract ```bibtex fence if present
    bibtex_new = _extract_bibtex_fence(raw_new)

    try:
        new_entries = parse_bibtex(bibtex_new)
        refs_entries = parse_bibtex(refs_path.read_text())
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    report = merge(new_entries, refs_entries, refs_path, dry_run=dry_run)
    # Update source label in first report line
    report[0] = (
        f"{'DRY-RUN: ' if dry_run else ''}bib-merge: {source_label} → {refs_path}"
    )

    for line in report:
        print(line)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

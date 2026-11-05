#!/usr/bin/env python3
"""Fetch one DOI or ISBN with DOIfetch, preserving the successful source."""

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from types import SimpleNamespace

OPEN_SOURCES = ["crossref", "unpaywall", "openalex", "hal", "istex", "ezproxy"]


def retrieve(kind, identifier, path, cascade, book_dois, phase="all"):
    """Run the requested phase; an ISBN lookup error must not become a miss."""
    if phase != "shadow":
        dois = [identifier] if kind == "doi" else book_dois(identifier)
        result = SimpleNamespace(
            status="failed", source=None, path=None, error="No book DOI found"
        )
        for doi in dois:
            result = cascade("doi", doi, path, OPEN_SOURCES)
            if result.status != "failed":
                return result
        if phase == "open":
            return result
    fallback = "scihub" if kind == "doi" else "libgen"
    return cascade(kind, identifier, path, [fallback])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--doi")
    group.add_argument("--isbn")
    parser.add_argument("--title", default="")
    parser.add_argument("--keep-title", action="store_true")
    parser.add_argument(
        "--no-check-zotero",
        action="store_true",
        help="Accepted for compatibility; this helper never reads Zotero's database",
    )
    parser.add_argument("--output-dir", default="papers")
    parser.add_argument("--data-dir", help=argparse.SUPPRESS)
    parser.add_argument(
        "--phase", choices=("open", "shadow"), required=True, help=argparse.SUPPRESS
    )
    parser.add_argument("--output-path", help=argparse.SUPPRESS)
    args = parser.parse_args()

    from doifetch import naming
    from doifetch.api import cascade
    from doifetch.pdf_utils import clean_filename
    from doifetch.sources.contract import Request
    from doifetch.sources.isbn import book_dois
    from doifetch.utils import normalize_isbn, validate_doi

    kind = "doi" if args.doi else "isbn"
    identifier = args.doi if args.doi else normalize_isbn(args.isbn)
    if not identifier or (kind == "doi" and not validate_doi(identifier)):
        parser.error(f"invalid {kind.upper()}")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    provided_stem = clean_filename(args.title.strip()) if args.title.strip() else ""
    search_stem = None
    if args.output_path:
        path = args.output_path
    elif provided_stem and (output_dir / f"{provided_stem}.pdf").exists():
        path = str(output_dir / f"{provided_stem}.pdf")
    else:
        lookup = identifier if kind == "doi" else f"isbn:{identifier}"
        resolved = naming.resolve_name(lookup, args.title, args.keep_title)
        # HAL uses the filename to form its query, even with --keep-title.
        search_name = resolved
        if not re.match(r"^[A-Za-zÀ-ÿ]+.*?\d{4}\s*[-–—]\s*.+$", search_name):
            search_name = naming.resolve_name(lookup, "") or search_name
        if not args.keep_title:
            resolved = search_name
        stem = clean_filename(resolved) or clean_filename(identifier.replace("/", "-"))
        search_stem = clean_filename(search_name) or stem
        path = str(output_dir / f"{stem}.pdf")
    if Path(path).exists():
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "source": None,
                    "path": path,
                    "error": "target already exists; verify it before use",
                }
            )
        )
        return 0

    def run_cascade(request_kind, value, target, sources):
        return cascade(Request(request_kind, value, target), sources)

    try:
        if args.phase == "open" and search_stem and search_stem != Path(path).stem:
            # Keep the requested output filename while providing HAL the
            # metadata it parses from the filename. The link never replaces a
            # destination created by another process during the fetch.
            with tempfile.TemporaryDirectory(dir=output_dir) as staging:
                candidate = str(Path(staging) / f"{search_stem}.pdf")
                result = retrieve(
                    kind,
                    identifier,
                    candidate,
                    run_cascade,
                    book_dois,
                    phase=args.phase,
                )
                if result.status == "success":
                    os.link(result.path, path)
        else:
            result = retrieve(
                kind, identifier, path, run_cascade, book_dois, phase=args.phase
            )
    except Exception as exc:
        print(
            json.dumps(
                {"status": "failed", "error": str(exc), "source": None, "path": path}
            )
        )
        return 3
    if (
        args.phase == "open"
        and result.status == "failed"
        and "hal: Cannot parse author/title" in (result.error or "")
    ):
        print(
            json.dumps(
                {
                    "status": "failed",
                    "error": result.error,
                    "source": None,
                    "path": path,
                }
            )
        )
        return 3
    print(
        json.dumps(
            {
                "status": result.status,
                "source": result.source if result.status == "success" else None,
                "path": path,
                "error": result.error,
            }
        )
    )
    return 0 if result.status in ("success", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())

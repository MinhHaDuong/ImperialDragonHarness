#!/usr/bin/env python3
"""Fetch one DOI or ISBN with DOIfetch, preserving the successful source."""

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

OPEN_SOURCES = ["crossref", "unpaywall", "openalex", "hal", "istex", "ezproxy"]
RECEIPTS_NAME = ".receipts.jsonl"


def file_md5(path):
    """Zotero's own file hash, the one scripts/zotero.py's file_md5 computes."""
    digest = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def receipt(status, source, path, error, kind, identifier, title, fetched):
    """The line this fetcher prints, and (for a fetched file) leaves beside
    it. probe-url.py prints the same keys. `identifiers` are those the
    caller GAVE, claimed only for a file this run fetched."""
    ids = dict.fromkeys(("doi", "isbn", "arxiv", "handle"))
    if fetched:
        ids[kind] = identifier
    return {
        "status": status,
        "source": source,
        "path": path,
        "error": error,
        "md5": file_md5(path) if os.path.isfile(path) else None,
        "identifiers": ids,
        "identifiers_scraped": [],
        "url": None,
        "final_url": None,
        "title": title or None,
        # JETP-observer retrieval vocabulary. The cascade's sources return a
        # file, not an HTTP exchange: no status to report (null).
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if fetched
        else None,
        "content_type": "application/pdf" if fetched else None,
        "size_bytes": os.path.getsize(path) if fetched and os.path.isfile(path) else None,
        "http_status": None,
    }


def emit(report, keep):
    """Print the receipt; with `keep`, append the same line to the staging
    folder's receipts file (one line per fetch, after the final name)."""
    line = json.dumps(report)
    print(line)
    if keep and report["md5"]:
        target = os.path.join(os.path.dirname(report["path"]) or ".", RECEIPTS_NAME)
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        with os.fdopen(fd, "a", encoding="utf-8") as stream:
            stream.write(line + "\n")


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
    # No default: the caller names the staging folder (scripts/doifetch.sh
    # passes docs/ when its own caller gave none).
    parser.add_argument("--output-dir", required=True)
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
    kind_id = (kind, identifier, args.title.strip())
    if Path(path).exists():
        report = receipt(
            "skipped",
            None,
            path,
            "target already exists; verify it before use",
            *kind_id,
            fetched=False,
        )
        emit(report, keep=False)
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
        emit(receipt("failed", None, path, str(exc), *kind_id, fetched=False), False)
        return 3
    if (
        args.phase == "open"
        and result.status == "failed"
        and "hal: Cannot parse author/title" in (result.error or "")
    ):
        emit(
            receipt("failed", None, path, result.error, *kind_id, fetched=False),
            False,
        )
        return 3
    fetched = result.status == "success"
    emit(
        receipt(
            result.status,
            result.source if fetched else None,
            path,
            result.error,
            *kind_id,
            fetched=fetched,
        ),
        keep=fetched,
    )
    return 0 if result.status in ("success", "skipped") else 1


if __name__ == "__main__":
    raise SystemExit(main())

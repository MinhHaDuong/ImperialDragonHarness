#!/usr/bin/env python3
"""Fetch one DOI or ISBN with DOIfetch, preserving the successful source."""

import argparse
import json
from pathlib import Path

OPEN_SOURCES = ['crossref', 'unpaywall', 'openalex', 'hal', 'istex', 'ezproxy']


def retrieve(kind, identifier, path, cascade, book_dois):
    """Try every open DOI before the identifier's shadow-library fallback."""
    dois = [identifier] if kind == 'doi' else book_dois(identifier)
    for doi in dois:
        result = cascade('doi', doi, path, OPEN_SOURCES)
        if result.status != 'failed':
            return result
    fallback = 'scihub' if kind == 'doi' else 'libgen'
    return cascade(kind, identifier, path, [fallback])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--doi')
    group.add_argument('--isbn')
    parser.add_argument('--title', required=True)
    parser.add_argument('--output-dir', default='papers')
    args = parser.parse_args()

    from doifetch.api import cascade
    from doifetch.pdf_utils import clean_filename
    from doifetch.sources.contract import Request
    from doifetch.sources.isbn import book_dois
    from doifetch.utils import normalize_isbn, validate_doi

    kind = 'doi' if args.doi else 'isbn'
    identifier = args.doi if args.doi else normalize_isbn(args.isbn)
    if not identifier or (kind == 'doi' and not validate_doi(identifier)):
        parser.error(f'invalid {kind.upper()}')
    if not args.title.strip():
        parser.error('title must not be empty')
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    path = str(output_dir / f'{clean_filename(args.title)}.pdf')

    def run_cascade(request_kind, value, target, sources):
        return cascade(Request(request_kind, value, target), sources)

    try:
        result = retrieve(kind, identifier, path, run_cascade, book_dois)
    except Exception as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc), 'source': None}))
        return 1
    print(json.dumps({'status': result.status, 'source': result.source if result.status == 'success' else None,
                      'path': result.path, 'error': result.error}))
    return 0 if result.status in ('success', 'skipped') else 1


if __name__ == '__main__':
    raise SystemExit(main())

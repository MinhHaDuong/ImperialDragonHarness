#!/usr/bin/env python3
"""Ingest a journal decision letter + reviewer comments into a remark ledger.

Pure I/O helper for the ``ingest-decision-letter`` skill. It never calls an
LLM API — the model reads extracted text and refines categories/tickets; this
script does the deterministic, testable, mechanical work:

  extract   read text from a text file, or a PDF via ``pdftotext``.
  archive   copy source documents into a paper repo's ``release/<date>/``
            convention, as tracked text, with a manifest.
  segment   first-pass split of a reviewer's comments into candidate remarks
            with STABLE ids and source line locations.
  dedupe    collapse duplicate / atomic sub-comments into distinct remarks.
  coverage  cross-check a ledger against the tickets that address it — flag
            uncovered remarks and orphan tickets in one deterministic pass.

Ledger record (JSONL, one object per line):
    id        stable, ``<reviewer>-<NN>`` (document order, zero-padded)
    reviewer  reviewer label, e.g. ``R1``
    category  free text; empty until the model fills it
    text      verbatim remark text
    source    ``<file>:<line>`` where the remark starts
    tickets   list of ticket ids that address this remark ([] = uncovered)
    atomic_of parent remark id when this record folds into another ([]-> null)

Example:
    ingest_letter.py segment reviewer1.txt --reviewer R1 > ledger.jsonl
    ingest_letter.py dedupe ledger.jsonl > ledger.dedup.jsonl
    ingest_letter.py coverage ledger.dedup.jsonl --tickets-dir tickets/
"""

import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

log = logging.getLogger(__name__)

# A line that opens a new atomic comment: "1.", "2)", "Comment 3:", "R1.4",
# "Point 2 -", "- ", "* ". Kept deliberately permissive; the model refines.
_ENUM_MARKER = re.compile(
    r"""^\s*
    (?:
        (?:comment|point|remark|item|question|major|minor)\s*\#?\s*\d+   # Comment 3
      | \d+[.)]                                                          # 1.  2)
      | [-*•]\s                                                     # bullet
      | [A-Z]?\d+\.\d+                                                   # R1.4 / 2.3
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _normalize_record(rec: dict) -> dict:
    """Fill missing ledger fields with defaults; leave present ones intact."""
    return {
        "id": rec.get("id") or "",
        "reviewer": rec.get("reviewer") or "",
        "category": rec.get("category") or "",
        "text": rec.get("text") or "",
        "source": rec.get("source") or "",
        "tickets": rec.get("tickets") or [],
        "atomic_of": rec.get("atomic_of"),
    }


def read_ledger(path: Path) -> list[dict]:
    """Read a JSONL ledger; skip blank lines; normalize each record."""
    records = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(f"{path}:{lineno}: invalid JSON: {e}") from e
        records.append(_normalize_record(rec))
    return records


def write_ledger(records: list[dict], out) -> None:
    """Write records as JSONL to an open text stream."""
    for rec in records:
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _print_json(obj: dict) -> None:
    """Pretty-print a JSON object to stdout, newline-terminated."""
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


# --------------------------------------------------------------------------- #
# extract
# --------------------------------------------------------------------------- #
def extract_text(path: Path) -> str:
    """Return the text of a document: read text files, pdftotext for PDFs."""
    if path.suffix.lower() == ".pdf":
        if shutil.which("pdftotext") is None:
            raise SystemExit(
                "pdftotext not found — install poppler-utils to extract PDF "
                "text, or pass a text file instead."
            )
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# archive
# --------------------------------------------------------------------------- #
def archive(sources: list[Path], into: Path) -> dict:
    """Copy source documents into ``into`` (a release/<date>/ dir).

    PDFs are copied verbatim AND a ``.txt`` sidecar of their extracted text is
    written beside them, so the archive is greppable tracked text. Returns a
    manifest describing what was written.
    """
    into.mkdir(parents=True, exist_ok=True)
    entries = []
    for src in sources:
        if not src.exists():
            raise SystemExit(f"source not found: {src}")
        dest = into / src.name
        shutil.copy2(src, dest)
        entry = {"source": str(src), "archived": str(dest)}
        if src.suffix.lower() == ".pdf":
            sidecar = dest.with_suffix(".txt")
            sidecar.write_text(extract_text(src), encoding="utf-8")
            entry["text_sidecar"] = str(sidecar)
        entries.append(entry)
        log.info("archived %s -> %s", src, dest)
    manifest = {"into": str(into), "entries": entries}
    (into / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return manifest


# --------------------------------------------------------------------------- #
# segment
# --------------------------------------------------------------------------- #
def segment(text: str, reviewer: str, source_name: str) -> list[dict]:
    """Split a reviewer's comment text into candidate remarks.

    Deterministic first pass: an enumeration marker (``1.``, ``Comment 2:``,
    a bullet, ``R1.3``) opens a new remark; lines until the next marker are its
    body. With no markers at all, blank-line-separated paragraphs each become a
    remark. Ids are ``<reviewer>-<NN>`` in document order, so re-running on the
    same input yields the same ids.
    """
    lines = text.splitlines()
    # Locate marker lines (non-empty, matching the enumeration pattern).
    marker_idx = [
        i for i, ln in enumerate(lines) if ln.strip() and _ENUM_MARKER.match(ln)
    ]

    spans: list[tuple[int, list[str]]] = []
    if marker_idx:
        for k, start in enumerate(marker_idx):
            end = marker_idx[k + 1] if k + 1 < len(marker_idx) else len(lines)
            spans.append((start, lines[start:end]))
    else:
        # Paragraph fallback: split on blank lines.
        start = None
        buf: list[str] = []
        for i, ln in enumerate(lines):
            if ln.strip():
                if start is None:
                    start = i
                buf.append(ln)
            elif buf:
                spans.append((start, buf))
                start, buf = None, []
        if buf:
            spans.append((start, buf))

    records = []
    for n, (start, body) in enumerate(spans, 1):
        remark_text = "\n".join(body).strip()
        if not remark_text:
            continue
        records.append(
            _normalize_record(
                {
                    "id": f"{reviewer}-{n:02d}",
                    "reviewer": reviewer,
                    "text": remark_text,
                    "source": f"{source_name}:{start + 1}",
                }
            )
        )
    return records


def _norm_text(text: str) -> str:
    """Normalize remark text for duplicate detection.

    Strips a leading enumeration marker so two verbatim-identical comments that
    differ only in their reviewer numbering (``1.`` vs ``3.``) still collapse.
    """
    stripped = _ENUM_MARKER.sub("", text.strip(), count=1)
    return re.sub(r"\s+", " ", stripped.lower()).strip().rstrip(".;:,")


# --------------------------------------------------------------------------- #
# dedupe
# --------------------------------------------------------------------------- #
def dedupe(records: list[dict]) -> tuple[list[dict], dict]:
    """Collapse atomic sub-comments and duplicates into distinct remarks.

    Two folding rules:
      - explicit: a record whose ``atomic_of`` names another record's id is
        folded into that parent.
      - implicit: records with identical normalized text collapse; the first
        in document order is canonical, the rest fold into it.
    Returns (ledger, summary). The ledger keeps every input record, with folded
    ones carrying ``atomic_of`` set to their canonical id. Distinct remarks are
    the records whose ``atomic_of`` is null.
    """
    known_ids = {r["id"] for r in records if r["id"]}
    canonical_by_text: dict[str, str] = {}
    out = []
    for rec in records:
        rec = dict(rec)
        # Respect an explicit atomic_of that points at a known record.
        if rec.get("atomic_of") and rec["atomic_of"] in known_ids:
            out.append(rec)
            continue
        key = _norm_text(rec["text"])
        if key in canonical_by_text:
            rec["atomic_of"] = canonical_by_text[key]
        else:
            canonical_by_text[key] = rec["id"]
            rec["atomic_of"] = None
        out.append(rec)

    remarks = [r for r in out if r["atomic_of"] is None]
    atomics = [r for r in out if r["atomic_of"] is not None]
    summary = {
        "input": len(records),
        "remarks": len(remarks),
        "atomics": len(atomics),
    }
    return out, summary


# --------------------------------------------------------------------------- #
# coverage
# --------------------------------------------------------------------------- #
def _ticket_ids_from_dir(tickets_dir: Path) -> set[str]:
    """Collect ticket ids from ``NNNN-*.erg`` filenames (open + closed)."""
    ids = set()
    for erg in tickets_dir.rglob("*.erg"):
        m = re.match(r"(\d{3,})", erg.name)
        if m:
            ids.add(m.group(1))
    return ids


def coverage(records: list[dict], universe: set[str]) -> dict:
    """Cross-check remark-to-ticket mapping against a ticket universe.

    A remark is a record whose ``atomic_of`` is null. Atomic sub-comments
    inherit their parent's coverage and are not counted separately.

    Flags:
      uncovered_remarks    remarks addressed by no ticket.
      orphan_tickets       tickets in the universe that address no remark.
      unknown_ticket_refs  ticket ids a remark references but not in the universe.
    """
    remarks = [r for r in records if r["atomic_of"] is None]
    mapping = {r["id"]: list(r.get("tickets") or []) for r in remarks}

    uncovered = sorted(rid for rid, tks in mapping.items() if not tks)
    referenced = {t for tks in mapping.values() for t in tks}
    orphan = sorted(universe - referenced)
    unknown = sorted(referenced - universe)

    return {
        "remark_count": len(remarks),
        "covered": len(remarks) - len(uncovered),
        "uncovered_remarks": uncovered,
        "orphan_tickets": orphan,
        "unknown_ticket_refs": unknown,
        "map": mapping,
    }


def coverage_ok(report: dict) -> bool:
    """A clean coverage report has no uncovered, orphan, or unknown items."""
    return not (
        report["uncovered_remarks"]
        or report["orphan_tickets"]
        or report["unknown_ticket_refs"]
    )


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _cmd_extract(args) -> int:
    sys.stdout.write(extract_text(args.path))
    return 0


def _cmd_archive(args) -> int:
    manifest = archive(args.sources, args.into)
    _print_json(manifest)
    return 0


def _cmd_segment(args) -> int:
    text = extract_text(args.path)
    source_name = args.source_name or args.path.name
    records = segment(text, args.reviewer, source_name)
    write_ledger(records, sys.stdout)
    log.info("segmented %d candidate remark(s) for %s", len(records), args.reviewer)
    return 0


def _cmd_dedupe(args) -> int:
    records = read_ledger(args.ledger)
    out, summary = dedupe(records)
    write_ledger(out, sys.stdout)
    log.info(
        "dedupe: %d input -> %d remark(s), %d atomic(s)",
        summary["input"],
        summary["remarks"],
        summary["atomics"],
    )
    return 0


def _cmd_coverage(args) -> int:
    records = read_ledger(args.ledger)
    universe: set[str] = set()
    if args.tickets:
        universe |= {t.strip() for t in args.tickets.split(",") if t.strip()}
    if args.tickets_dir:
        universe |= _ticket_ids_from_dir(args.tickets_dir)
    report = coverage(records, universe)
    _print_json(report)
    return 0 if coverage_ok(report) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    pe = sub.add_parser("extract", help="print a document's text to stdout")
    pe.add_argument("path", type=Path)
    pe.set_defaults(func=_cmd_extract)

    pa = sub.add_parser("archive", help="copy sources into a release/<date>/ dir")
    pa.add_argument("sources", type=Path, nargs="+")
    pa.add_argument("--into", type=Path, required=True,
                    help="destination dir, e.g. <paper-repo>/release/<date>/")
    pa.set_defaults(func=_cmd_archive)

    ps = sub.add_parser("segment", help="first-pass split into candidate remarks")
    ps.add_argument("path", type=Path)
    ps.add_argument("--reviewer", required=True,
                    help="reviewer label used in the id prefix, e.g. R1")
    ps.add_argument("--source-name", default=None,
                    help="name used in the source field (default: file name)")
    ps.set_defaults(func=_cmd_segment)

    pd = sub.add_parser("dedupe", help="fold atomic/duplicate comments into remarks")
    pd.add_argument("ledger", type=Path)
    pd.set_defaults(func=_cmd_dedupe)

    pc = sub.add_parser("coverage", help="cross-check remark-to-ticket coverage")
    pc.add_argument("ledger", type=Path)
    pc.add_argument("--tickets", default=None,
                    help="comma-separated ticket ids in the universe")
    pc.add_argument("--tickets-dir", type=Path, default=None,
                    help="dir of NNNN-*.erg tickets to build the universe from")
    pc.set_defaults(func=_cmd_coverage)

    return p


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

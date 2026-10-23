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
    tickets   list of ticket ids addressing work (may be empty with a disposition)
    atomic_of parent remark id when this record folds into another (null = distinct)

Example:
    ingest_letter.py segment reviewer1.txt --reviewer R1 > ledger.jsonl
    ingest_letter.py dedupe ledger.jsonl > ledger.dedup.jsonl
    ingest_letter.py coverage ledger.dedup.jsonl --tickets 0301 --tickets-dir tickets/
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
        "round": rec.get("round") or "",
        "disposition": rec.get("disposition"),
        "reason": rec.get("reason") or "",
        "resolution": rec.get("resolution") or "open",
        "evidence": rec.get("evidence") or [],
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
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise SystemExit(
                f"pdftotext failed on {path}: {e.stderr.strip() or e}. "
                "The file may be malformed or not a valid PDF."
            ) from e
        return result.stdout
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise SystemExit(
            f"{path} is not valid UTF-8 text: {e}. Re-save it as UTF-8, or pass "
            "the PDF and let pdftotext extract it."
        ) from e


# --------------------------------------------------------------------------- #
# archive
# --------------------------------------------------------------------------- #
def _unique_dest(into: Path, name: str, used: set[str]) -> Path:
    """Return a destination path in ``into`` that collides with nothing.

    Appends ``-2``, ``-3``, … before the extension when the basename is already
    taken — by an earlier source in this archive run or a file already on disk —
    so two same-named sources from different directories both survive instead of
    the second silently clobbering the first.
    """
    stem, suffix = Path(name).stem, Path(name).suffix
    candidate = name
    i = 2
    while candidate in used or (into / candidate).exists():
        candidate = f"{stem}-{i}{suffix}"
        i += 1
    used.add(candidate)
    return into / candidate


def archive(sources: list[Path], into: Path) -> dict:
    """Copy source documents into ``into`` (a release/<date>/ dir).

    PDFs are copied verbatim AND a ``.txt`` sidecar of their extracted text is
    written beside them, so the archive is greppable tracked text. Returns a
    manifest describing what was written.
    """
    into.mkdir(parents=True, exist_ok=True)
    manifest_path = into / "manifest.json"
    entries = []
    if manifest_path.exists():
        entries = json.loads(manifest_path.read_text(encoding="utf-8"))["entries"]
    used: set[str] = {"manifest.json"}
    for src in sources:
        if not src.exists():
            raise SystemExit(f"source not found: {src}")
        dest = _unique_dest(into, src.name, used)
        shutil.copy2(src, dest)
        entry = {"source": str(src), "archived": str(dest)}
        if src.suffix.lower() == ".pdf":
            sidecar = _unique_dest(into, dest.stem + ".txt", used)
            sidecar.write_text(extract_text(src), encoding="utf-8")
            entry["text_sidecar"] = str(sidecar)
        entries.append(entry)
        log.info("archived %s -> %s", src, dest)
    manifest = {"into": str(into), "entries": entries}
    (into / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


# --------------------------------------------------------------------------- #
# segment
# --------------------------------------------------------------------------- #
def segment(text: str, reviewer: str, source_name: str, round_id: str = "") -> list[dict]:
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
                    "id": f"{round_id}:" + f"{reviewer}-{n:02d}" if round_id else f"{reviewer}-{n:02d}",
                    "round": round_id,
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
def _invalid_atomics(records: list[dict]) -> list[dict]:
    """Only a distinct remark in the same round can cover an atomic child."""
    parents = {(r.get("round", ""), r["id"]) for r in records if r["atomic_of"] is None}
    return [r for r in records if r["atomic_of"] is not None
            and (r.get("round", ""), r["atomic_of"]) not in parents]


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
    canonical_by_text: dict[tuple[str, str], str] = {}
    out = []
    for rec in records:
        rec = dict(rec)
        ref = rec.get("atomic_of")
        if ref:
            # Preserve stated references, including malformed ones, for repair.
            # Validate against the final distinct parents after implicit folding.
            out.append(rec)
            continue
        key = (rec.get("round", ""), _norm_text(rec["text"]))
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
        "unknown_atomic_refs": sorted(r["id"] for r in _invalid_atomics(out)),
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


def coverage(records: list[dict], universe: set[str],
             existing_tickets: set[str] | None = None, round_id: str | None = None) -> dict:
    """Check decision coverage; report resolution separately.

    ``universe`` is the explicit round ticket set; ``existing_tickets`` is the
    project-wide existence index. Omitting it preserves the legacy API.
    Legacy records are covered by a ticket mapping; explicit author dispositions
    cover decisions without requiring artificial tickets. Evidence references are
    recorded, not automatically verified for scientific sufficiency.
    """
    selected = [r for r in records if round_id is None or r.get("round", "") == round_id]
    invalid: set[str] = {r["id"] for r in _invalid_atomics(selected)}
    remarks = [r for r in selected if r["atomic_of"] is None or r["id"] in invalid]
    mapping: dict[str, list[str]] = {}
    duplicate: set[str] = set()
    uncovered: set[str] = set()
    unresolved: set[str] = set()
    for r in remarks:
        rid = r["id"]
        if rid in mapping:
            duplicate.add(rid)
        mapping[rid] = list(r.get("tickets") or [])
        disposition = r.get("disposition")
        resolution = r.get("resolution", "open")
        evidence = r.get("evidence", [])
        has_evidence = (isinstance(evidence, list) and bool(evidence)
                        and all(isinstance(e, str) and e.strip() for e in evidence))
        if (disposition not in (None, "accepted", "rejected", "deferred", "already_addressed")
                or resolution not in ("open", "resolved")
                or (disposition in ("rejected", "deferred")
                    and (not isinstance(r.get("reason"), str) or not r["reason"].strip()))
                or (resolution == "resolved" and not has_evidence)
                or (disposition == "already_addressed"
                    and (resolution != "resolved" or not has_evidence))):
            invalid.add(rid)
        if not disposition and not mapping[rid]:
            uncovered.add(rid)
        if resolution != "resolved":
            unresolved.add(rid)

    referenced = {t for tks in mapping.values() for t in tks}
    existing = universe if existing_tickets is None else existing_tickets
    return {
        "remark_count": len(remarks),
        "covered": len(remarks) - len(uncovered | invalid),
        "uncovered_remarks": sorted(uncovered),
        "unresolved_remarks": sorted(unresolved),
        "invalid_records": sorted(invalid),
        "orphan_tickets": sorted(universe - referenced),
        "unknown_ticket_refs": sorted((referenced | universe) - existing),
        "out_of_round_ticket_refs": sorted(referenced - universe),
        "duplicate_ids": sorted(duplicate),
        "map": mapping,
    }


def coverage_ok(report: dict) -> bool:
    """Clean decision coverage does not imply that remarks have been resolved."""
    return not any(report.get(key) for key in (
        "uncovered_remarks", "orphan_tickets", "unknown_ticket_refs",
        "out_of_round_ticket_refs", "duplicate_ids", "invalid_records",
    ))


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
    source_name = args.source_name or str(args.path)
    records = segment(text, args.reviewer, source_name, args.round)
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
    existing = _ticket_ids_from_dir(args.tickets_dir) if args.tickets_dir else None
    report = coverage(records, universe, existing_tickets=existing, round_id=args.round)
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
    ps.add_argument("--round", default="", help="round label; prefixes new remark ids")
    ps.add_argument("--source-name", default=None,
                    help="name used in the source field (default: input path)")
    ps.set_defaults(func=_cmd_segment)

    pd = sub.add_parser("dedupe", help="fold atomic/duplicate comments into remarks")
    pd.add_argument("ledger", type=Path)
    pd.set_defaults(func=_cmd_dedupe)

    pc = sub.add_parser("coverage", help="cross-check remark-to-ticket coverage")
    pc.add_argument("ledger", type=Path)
    pc.add_argument("--tickets", required=True,
                    help="comma-separated ticket ids in the universe")
    pc.add_argument("--tickets-dir", type=Path, default=None,
                    help="project ticket existence index; does not enlarge round universe")
    pc.add_argument("--round", default=None, help="check only records with this round label")
    pc.set_defaults(func=_cmd_coverage)

    return p


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

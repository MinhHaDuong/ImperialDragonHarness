#!/usr/bin/env python3
"""Helper for the zotero-import skill. Subcommands: probe, match, write."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import configparser
from configparser import ConfigParser
from pathlib import Path
from typing import Any

DOI_BARE_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.IGNORECASE)
# Anchor on doi.org/ or "DOI:" / "doi " preamble. Lets us prefer the document's
# own DOI over the first cited DOI in the body text.
DOI_ANCHORED_RE = re.compile(
    r"(?:doi\.org/|doi[:\s]+)(10\.\d{4,9}/[-._;()/:A-Z0-9]+)",
    re.IGNORECASE,
)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
ISBN_RE = re.compile(
    r"\bISBN(?:[- ]?1[03])?[: ]*((?:97[89][- ]?)?(?:[0-9][- ]?){9}[0-9Xx])\b",
    re.IGNORECASE,
)
HDL_RE = re.compile(r"\bhdl\.handle\.net/[^\s)\]]+", re.IGNORECASE)
ARXIV_RE = re.compile(r"\barXiv:\s*(\d{4}\.\d{4,5})(v\d+)?\b", re.IGNORECASE)
FIRST_PAGES = 2
LAST_PAGES = 2
TEXT_TRUNCATE = 4000
# How far into page 1 to keep scanning for a bare DOI when no anchored DOI is
# found — limits the false-positive risk of picking up a cited DOI from the body.
DOI_BARE_WINDOW = 800


def run(cmd: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, **kw)


def pdfinfo(path: Path) -> dict[str, str]:
    p = run(["pdfinfo", str(path)])
    if p.returncode != 0:
        return {}
    out: dict[str, str] = {}
    for line in p.stdout.splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def pdftotext_range(path: Path, first: int, last: int) -> str:
    if last < first:
        return ""
    p = run(["pdftotext", "-f", str(first), "-l", str(last), "-layout",
             str(path), "-"])
    if p.returncode != 0:
        return ""
    return p.stdout[:TEXT_TRUNCATE]


def find_doi(front_text: str, back_text: str, subject: str) -> str | None:
    for blob in (front_text, back_text, subject):
        if m := DOI_ANCHORED_RE.search(blob):
            return m.group(1).rstrip(".,;)»")
    if m := DOI_BARE_RE.search(front_text[:DOI_BARE_WINDOW]):
        return m.group(0).rstrip(".,;)»")
    return None


def find_identifier(front_text: str, back_text: str, subject: str
                    ) -> dict[str, str | None]:
    out: dict[str, str | None] = {"doi": None, "isbn": None, "handle": None,
                                  "arxiv": None}
    out["doi"] = find_doi(front_text, back_text, subject)
    combined = front_text + "\n" + back_text + "\n" + subject
    if m := ISBN_RE.search(combined):
        out["isbn"] = re.sub(r"[- ]", "", m.group(1))
    if m := HDL_RE.search(combined):
        out["handle"] = "https://" + m.group(0)
    if m := ARXIV_RE.search(combined):
        out["arxiv"] = m.group(1)
    return out


def find_zotero_db() -> Path | None:
    env = os.environ.get("ZOTERO_DATA_DIR")
    candidates: list[Path] = []
    if env:
        candidates.append(Path(env) / "zotero.sqlite")
    candidates += [
        Path.home() / "Zotero" / "zotero.sqlite",
        Path.home() / "data" / "Zotero" / "zotero.sqlite",
        Path.home() / "Documents" / "Zotero" / "zotero.sqlite",
    ]
    # Firefox-style profiles.ini may override dataDir.
    profiles_ini = Path.home() / ".zotero" / "zotero" / "profiles.ini"
    if profiles_ini.exists():
        try:
            cp = ConfigParser()
            cp.read(profiles_ini)
        except (OSError, configparser.Error):
            cp = None
        if cp is not None:
            for section in cp.sections():
                pth = cp.get(section, "Path", fallback=None)
                if not pth:
                    continue
                is_relative = cp.getint(section, "IsRelative", fallback=1)
                base = profiles_ini.parent if is_relative else Path("/")
                prefs = (base / pth / "prefs.js")
                if prefs.exists():
                    m = re.search(
                        r'user_pref\("extensions\.zotero\.dataDir",\s*"([^"]+)"\)',
                        prefs.read_text(errors="replace"),
                    )
                    if m:
                        candidates.append(Path(m.group(1)) / "zotero.sqlite")
    for c in candidates:
        if c.exists():
            return c
    return None


def zotero_open(db_path: Path) -> sqlite3.Connection:
    # immutable=1 bypasses WAL locks while Zotero is running.
    uri = f"file:{db_path}?immutable=1"
    return sqlite3.connect(uri, uri=True)


# --- Deduplication matcher --------------------------------------------------
# Cascade, strongest key first: attachment content hash -> persistent
# identifier (DOI, ISBN, arXiv, handle) -> attachment filename ->
# (first author surname, year, normalised title) -> title Jaccard as last
# resort. The cascade stops at the first key that fires; each hit reports
# which key matched ("why") and how much to trust it ("certainty").
# Scope defaults to the user library because injection writes to users/{uid}:
# a hit that lives only in a read-only group library must not suppress an
# injection that is genuinely missing from the destination.

USER_LIBRARY = "user"
ALL_LIBRARIES = "all"
_NOT_DELETED = "itemID NOT IN (SELECT itemID FROM deletedItems)"


def resolve_library_id(conn: sqlite3.Connection,
                       library: int | str = USER_LIBRARY) -> int | None:
    """Map the library selector to a libraryID; None means all libraries."""
    if library == ALL_LIBRARIES:
        return None
    if isinstance(library, int):
        return library
    if isinstance(library, str) and library.isdigit():
        return int(library)
    row = conn.execute(
        "SELECT libraryID FROM libraries WHERE type='user'").fetchone()
    return row[0] if row else 1


def first_author_surname(author: str) -> str:
    return author_to_ris(author).partition(",")[0].strip()


def _norm_title(s: str) -> str:
    """Casing- and punctuation-insensitive form for exact title comparison."""
    s = s.lower().replace("&", " and ")
    return " ".join(re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE).split())


def _attachment_basename(att_path: str) -> str:
    """Basename of a Zotero attachment path.

    Formats seen in the wild: 'storage:file.pdf' (imported),
    'attachments:rel/dir/file.pdf' (linked, relative), absolute paths.
    """
    tail = att_path.partition(":")[2] or att_path
    return tail.rsplit("/", 1)[-1]


def _attachment_targets(cur: sqlite3.Cursor, lib_id: int | None, *,
                        storage_hash: str | None = None,
                        basename: str | None = None) -> set[int]:
    """Top-level items owning an attachment that matches by hash or basename.

    A parentless attachment stands for itself. This is a primary candidate
    source: it must never depend on any metadata score.
    """
    sql = ("SELECT a.itemID, a.parentItemID, a.path, a.storageHash "
           "FROM itemAttachments a JOIN items ai ON ai.itemID = a.itemID "
           f"WHERE a.{_NOT_DELETED}")
    params: list[Any] = []
    if lib_id is not None:
        sql += " AND ai.libraryID = ?"
        params.append(lib_id)
    if storage_hash is not None:
        sql += " AND LOWER(a.storageHash) = LOWER(?)"
        params.append(storage_hash)
    targets: set[int] = set()
    for att_id, parent, path, _h in cur.execute(sql, params).fetchall():
        if basename is not None and _attachment_basename(path or "") != basename:
            continue
        targets.add(parent or att_id)
    return targets


def _field_lookup_sql(lib_id: int | None) -> tuple[str, str]:
    """(sql, lib_clause) skeleton for one-field item lookups."""
    lib_clause = " AND i.libraryID = ?" if lib_id is not None else ""
    sql = ("SELECT i.itemID, v.value FROM items i "
           "JOIN itemData d ON d.itemID = i.itemID "
           "JOIN fields f ON f.fieldID = d.fieldID "
           "JOIN itemDataValues v ON v.valueID = d.valueID "
           f"WHERE i.{_NOT_DELETED}" + lib_clause)
    return sql, lib_clause


def _identifier_targets(cur: sqlite3.Cursor, lib_id: int | None, *,
                        doi: str | None, isbn: str | None,
                        arxiv: str | None, handle: str | None
                        ) -> dict[int, list[str]]:
    """Items matching any persistent identifier, with the keys that fired."""
    base, _ = _field_lookup_sql(lib_id)
    lib_params: list[Any] = [lib_id] if lib_id is not None else []
    hits: dict[int, list[str]] = {}

    def add(item_id: int, key: str) -> None:
        keys = hits.setdefault(item_id, [])
        if key not in keys:
            keys.append(key)

    if doi:
        for iid, _v in cur.execute(
                base + " AND f.fieldName='DOI' AND LOWER(v.value)=LOWER(?)",
                lib_params + [doi]).fetchall():
            add(iid, "doi")
    if isbn:
        want = re.sub(r"[^0-9Xx]", "", isbn).upper()
        for iid, v in cur.execute(
                base + " AND f.fieldName='ISBN'", lib_params).fetchall():
            stored = {re.sub(r"[^0-9Xx]", "", t).upper()
                      for t in (v or "").replace(";", " ").split()}
            if want in stored:
                add(iid, "isbn")
    if arxiv:
        for iid, _v in cur.execute(
                base + " AND f.fieldName IN ('extra','url','archiveID','number')"
                       " AND v.value LIKE ?",
                lib_params + [f"%{arxiv}%"]).fetchall():
            add(iid, "arxiv")
    if handle:
        bare = handle.split("://")[-1]
        for iid, _v in cur.execute(
                base + " AND f.fieldName IN ('url','extra')"
                       " AND v.value LIKE ?",
                lib_params + [f"%{bare}%"]).fetchall():
            add(iid, "handle")
    return hits


def _item_fields(cur: sqlite3.Cursor,
                 item_ids: list[int]) -> dict[int, dict[str, str | None]]:
    """title/DOI/date per item, for match reporting and title comparison."""
    if not item_ids:
        return {}
    qmarks = ",".join("?" * len(item_ids))
    rows = cur.execute(
        f"""
        SELECT i.itemID,
               MAX(CASE WHEN f.fieldName='title' THEN v.value END) AS title,
               MAX(CASE WHEN f.fieldName='DOI' THEN v.value END)   AS doi,
               MAX(CASE WHEN f.fieldName='date' THEN v.value END)  AS date
        FROM items i
        LEFT JOIN itemData d ON d.itemID = i.itemID
        LEFT JOIN fields f   ON f.fieldID = d.fieldID
        LEFT JOIN itemDataValues v ON v.valueID = d.valueID
        WHERE i.itemID IN ({qmarks})
        GROUP BY i.itemID
        """,
        item_ids,
    ).fetchall()
    return {iid: {"title": t, "doi": d, "date": dt} for iid, t, d, dt in rows}


def _creator_year_title_targets(cur: sqlite3.Cursor, lib_id: int | None,
                                surname: str, year: str,
                                title_norm: str) -> set[int]:
    """Items whose first author, year, and normalised title all agree."""
    sql = ("SELECT DISTINCT i.itemID FROM items i "
           "JOIN itemCreators ic ON ic.itemID = i.itemID AND ic.orderIndex = 0 "
           "JOIN creators c ON c.creatorID = ic.creatorID "
           f"WHERE i.{_NOT_DELETED} AND LOWER(c.lastName) = LOWER(?)")
    params: list[Any] = [surname]
    if lib_id is not None:
        sql += " AND i.libraryID = ?"
        params.append(lib_id)
    candidates = [r[0] for r in cur.execute(sql, params).fetchall()]
    fields = _item_fields(cur, candidates)
    return {
        iid for iid in candidates
        if (meta := fields.get(iid))
        and meta["date"] and year in meta["date"]
        and meta["title"] and _norm_title(meta["title"]) == title_norm
    }


def _title_jaccard_hits(cur: sqlite3.Cursor, lib_id: int | None,
                        title: str, year: str | None
                        ) -> list[tuple[int, float]]:
    """Last-resort fuzzy title overlap over top-level items. A guess."""
    sql = ("SELECT i.itemID, "
           "MAX(CASE WHEN f.fieldName='title' THEN v.value END) AS title "
           "FROM items i "
           "JOIN itemData d ON d.itemID = i.itemID "
           "JOIN fields f   ON f.fieldID = d.fieldID "
           "JOIN itemDataValues v ON v.valueID = d.valueID "
           "LEFT JOIN itemAttachments a ON a.itemID = i.itemID "
           "AND a.parentItemID IS NOT NULL "
           f"WHERE i.{_NOT_DELETED} AND a.itemID IS NULL")
    params: list[Any] = []
    if lib_id is not None:
        sql += " AND i.libraryID = ?"
        params.append(lib_id)
    if year:
        sql += (" AND i.itemID IN (SELECT d3.itemID FROM itemData d3 "
                "JOIN fields f3 ON f3.fieldID=d3.fieldID "
                "JOIN itemDataValues v3 ON v3.valueID=d3.valueID "
                "WHERE f3.fieldName='date' AND v3.value LIKE ?)")
        params.append(f"%{year}%")
    sql += " GROUP BY i.itemID"

    def tok(s: str) -> set[str]:
        cleaned = re.sub(r"[^\w\s]", " ", s.lower(), flags=re.UNICODE)
        return {w for w in cleaned.split() if len(w) > 2}

    title_set = tok(title)
    hits: list[tuple[int, float]] = []
    for item_id, t in cur.execute(sql, params).fetchall():
        b = tok(t or "")
        if not title_set or not b:
            continue
        j = len(title_set & b) / len(title_set | b)
        if j >= 0.6:
            hits.append((item_id, j))
    return hits


def classify_matches(matches: list[dict[str, Any]]) -> str:
    """'match' when a safe key fired unambiguously; 'ambiguous' when only a
    guess-level key fired or several strong candidates tie; 'none' otherwise."""
    if not matches:
        return "none"
    best = matches[0]["certainty"]
    if best == "exact":
        return "match"
    if best == "strong":
        strong = [m for m in matches if m["certainty"] == "strong"]
        return "match" if len(strong) == 1 else "ambiguous"
    return "ambiguous"


def zotero_matches(
    conn: sqlite3.Connection,
    *,
    doi: str | None = None,
    title: str | None = None,
    year: str | None = None,
    pdf_path: Path | None = None,
    isbn: str | None = None,
    arxiv: str | None = None,
    handle: str | None = None,
    first_author: str | None = None,
    library: int | str = USER_LIBRARY,
) -> dict[str, Any]:
    """Deduplicate one prospective item against the Zotero library.

    Returns {"matches": [...], "verdict": ..., "consulted": [...],
    "skipped": [...]}. The verdict is "match" (a safe key fired), "ambiguous"
    (only a guess fired — neither a silent match nor a silent skip), "none"
    (keys were consulted, nothing matched), or "unchecked" (no key could be
    consulted — distinguishable from a clean negative by design).
    """
    cur = conn.cursor()
    lib_id = resolve_library_id(conn, library)
    consulted: list[str] = []
    skipped: list[str] = []
    found: dict[int, dict[str, Any]] = {}

    def settle(stage: str, targets: dict[int, list[str]] | set[int],
               certainty: str, score: int) -> None:
        for iid in targets:
            why = targets[iid] if isinstance(targets, dict) else [stage]
            found[iid] = {"why": why, "certainty": certainty, "score": score}

    # 1. Attachment content hash — exact, immune to metadata quality.
    if pdf_path is not None and pdf_path.is_file():
        consulted.append("storageHash")
        digest = hashlib.md5(pdf_path.read_bytes()).hexdigest()
        settle("storageHash",
               _attachment_targets(cur, lib_id, storage_hash=digest),
               "exact", 100)
    else:
        skipped.append("storageHash: no readable PDF")

    # 2. Persistent identifiers.
    if found:
        skipped.append("identifier: settled by a stronger key")
    elif not (doi or isbn or arxiv or handle):
        skipped.append("identifier: none provided")
    else:
        consulted.append("identifier")
        settle("identifier",
               _identifier_targets(cur, lib_id, doi=doi, isbn=isbn,
                                   arxiv=arxiv, handle=handle),
               "exact", 100)

    # 3. Attachment filename — still independent of any title score.
    if found:
        skipped.append("filename: settled by a stronger key")
    elif pdf_path is None or not pdf_path.name:
        skipped.append("filename: no PDF name")
    else:
        consulted.append("filename")
        settle("filename",
               _attachment_targets(cur, lib_id, basename=pdf_path.name),
               "strong", 85)

    # 4. (first author surname, year, normalised title).
    if found:
        skipped.append("creator-year-title: settled by a stronger key")
    elif not (first_author and year and title):
        skipped.append("creator-year-title: needs author, year, and title")
    else:
        consulted.append("creator-year-title")
        settle("creator-year-title",
               _creator_year_title_targets(cur, lib_id,
                                           first_author_surname(first_author),
                                           year, _norm_title(title)),
               "strong", 80)

    # 5. Title Jaccard — last resort; its hits are guesses, never certainties.
    if found:
        skipped.append("title-jaccard: settled by a stronger key")
    elif not title:
        skipped.append("title-jaccard: no title")
    else:
        consulted.append("title-jaccard")
        for item_id, j in _title_jaccard_hits(cur, lib_id, title, year):
            found[item_id] = {"why": [f"title~{j:.2f}"], "certainty": "weak",
                              "score": int(j * 90)}

    fields = _item_fields(cur, list(found))
    matches: list[dict[str, Any]] = []
    for iid, hit in found.items():
        meta = fields.get(iid, {})
        score, why = hit["score"], list(hit["why"])
        date = meta.get("date")
        # creator-year-title already encodes the year agreement.
        if year and date and year in date and "creator-year-title" not in why:
            score += 5
            why.append("year")
        matches.append({"itemID": iid, "title": meta.get("title"),
                        "doi": meta.get("doi"), "date": date,
                        "score": score, "why": why,
                        "certainty": hit["certainty"]})

    matches.sort(key=lambda m: -m["score"])
    matches = matches[:5]

    # Decorate hits with attachment info.
    for m in matches:
        atts = cur.execute(
            """
            SELECT a.path, a.contentType, fa.indexedPages, fa.totalPages
            FROM itemAttachments a
            LEFT JOIN fulltextItems fa ON fa.itemID = a.itemID
            WHERE a.parentItemID = ?
            """,
            (m["itemID"],),
        ).fetchall()
        m["attachments"] = [
            {"path": p, "contentType": ct, "indexedPages": ip, "totalPages": tp}
            for (p, ct, ip, tp) in atts
        ]
        m["pdf_basename_match"] = bool(pdf_path) and any(
            _attachment_basename(p or "") == pdf_path.name for (p, *_rest) in atts
        )

    verdict = classify_matches(matches) if consulted else "unchecked"
    return {"matches": matches, "verdict": verdict,
            "consulted": consulted, "skipped": skipped}


def probe_one(pdf: Path, conn: sqlite3.Connection | None,
              library: int | str = USER_LIBRARY) -> dict[str, Any]:
    info = pdfinfo(pdf)
    try:
        page_count = int(info.get("Pages", "0"))
    except ValueError:
        page_count = 0
    text_front = pdftotext_range(pdf, 1, FIRST_PAGES)
    text_back = ""
    if page_count > FIRST_PAGES:
        text_back = pdftotext_range(
            pdf, max(page_count - LAST_PAGES + 1, FIRST_PAGES + 1), page_count,
        )
    ids = find_identifier(text_front, text_back, info.get("Subject") or "")
    # pdfinfo Title is often a LaTeX template artefact; agent re-extracts from text.
    pdfinfo_title = info.get("Title") or None
    year = None
    if "CreationDate" in info:
        ym = YEAR_RE.search(info["CreationDate"])
        if ym:
            year = ym.group(0)
    out: dict[str, Any] = {
        "pdf": str(pdf.resolve()),
        "pdf_size": pdf.stat().st_size,
        "page_count": page_count,
        "pdfinfo": {k: info.get(k) for k in ("Title", "Author", "Subject",
                                             "Keywords", "Creator", "Producer",
                                             "CreationDate", "ModDate", "Pages")},
        "first_pages_text": text_front,
        "last_pages_text": text_back,
        "identifiers": ids,
        "year_hint": year,
        "filename": pdf.name,
    }
    if conn is not None:
        out["zotero_matches"] = zotero_matches(
            conn, doi=ids["doi"], isbn=ids["isbn"], arxiv=ids["arxiv"],
            handle=ids["handle"], title=pdfinfo_title, year=year,
            pdf_path=pdf, library=library,
        )
    else:
        out["zotero_matches"] = None
    return out


# --- RIS writing -----------------------------------------------------------

RIS_TYPE_DEFAULT = "JOUR"
RIS_VALID_TYPES = {
    "JOUR", "BOOK", "CHAP", "CONF", "CPAPER", "THES", "RPRT", "GEN",
    "GOVDOC", "NEWS", "MGZN", "MANSCPT", "PAT", "STAND", "UNPB", "WEB",
}
MONOGRAPH_TYPES = {"BOOK", "THES", "RPRT", "CHAP", "MANSCPT", "STAND", "PAT"}


def author_to_ris(a: str) -> str:
    a = a.strip()
    if "," in a:
        return a
    parts = a.split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    return a


def entry_to_ris(e: dict[str, Any]) -> str:
    ty = (e.get("type") or RIS_TYPE_DEFAULT).upper()
    if ty not in RIS_VALID_TYPES:
        ty = RIS_TYPE_DEFAULT
    lines = [f"TY  - {ty}"]
    if t := e.get("title"):
        lines.append(f"TI  - {t}")
    if st := e.get("shortTitle"):
        lines.append(f"ST  - {st}")
    for a in e.get("authors") or []:
        lines.append(f"AU  - {author_to_ris(a)}")
    if y := e.get("year"):
        lines.append(f"PY  - {y}")
    if d := e.get("doi"):
        lines.append(f"DO  - {d}")
    if isbn := e.get("isbn"):
        lines.append(f"SN  - {isbn}")
    if url := e.get("url"):
        lines.append(f"UR  - {url}")
    if j := e.get("journal"):
        lines.append(f"T2  - {j}")
    if v := e.get("volume"):
        lines.append(f"VL  - {v}")
    if iss := e.get("issue"):
        lines.append(f"IS  - {iss}")
    if pages := e.get("pages"):
        sp, _, ep = pages.partition("-")
        if sp:
            lines.append(f"SP  - {sp.strip()}")
        if ep:
            lines.append(f"EP  - {ep.strip()}")
    # Zotero's "Number of Pages" only maps from RIS SP on monograph types.
    if (n := e.get("numPages")) and not e.get("pages"):
        if ty in MONOGRAPH_TYPES:
            lines.append(f"SP  - {n}")
        else:
            lines.append(f"KW  - pages:{n}")
    if pub := e.get("publisher"):
        lines.append(f"PB  - {pub}")
    if lang := e.get("language"):
        lines.append(f"LA  - {lang}")
    if ab := e.get("abstract"):
        lines.append("AB  - " + " ".join(ab.split()))
    if e.get("attach_pdf") and (p := e.get("pdf")):
        lines.append(f"L1  - file://{Path(p).resolve()}")
    lines.append("ER  - ")
    return "\n".join(lines) + "\n"


# --- Zotero Web API injection ---------------------------------------------
# Direct import through api.zotero.org (v3): create the items, then run the
# three-step file-upload dance per attachment. Replaces the xdg-open handoff
# when a read-write key is available; `write` stays as artifact and fallback.

ZOTERO_API_BASE = "https://api.zotero.org"
ZOTERO_ENV_FILE = Path.home() / ".config/keys/zotero.env"

RIS_TO_ZOTERO_TYPE = {
    "JOUR": "journalArticle",
    "BOOK": "book",
    "THES": "thesis",
    "RPRT": "report",
    "CHAP": "bookSection",
    "CONF": "conferencePaper",
    "MANSCPT": "manuscript",
    "NEWS": "newspaperArticle",
    "MGZN": "magazineArticle",
    "GEN": "document",
}
# Zotero item types that carry a real numPages field.
ZOTERO_NUMPAGES_TYPES = {"book", "thesis", "manuscript", "report"}


def load_env_file(path: Path) -> dict[str, str]:
    """Parse a KEY=VALUE env file, ignoring comments and blank lines."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        values[k.strip()] = v.strip()
    return values


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """Return (user_id, rw_key) from flags, environment, then the keys file."""
    env_file = load_env_file(ZOTERO_ENV_FILE)
    key = (args.api_key or os.environ.get("ZOTERO_RW_API_KEY")
           or env_file.get("ZOTERO_RW_API_KEY"))
    user = (args.user_id or os.environ.get("ZOTERO_USER_ID")
            or env_file.get("ZOTERO_USER_ID"))
    if not key:
        raise SystemExit("inject: no ZOTERO_RW_API_KEY (flag, env, or "
                         f"{ZOTERO_ENV_FILE})")
    if not user:
        raise SystemExit("inject: no ZOTERO_USER_ID (flag, env, or "
                         f"{ZOTERO_ENV_FILE})")
    return user, key


def author_to_creator(a: str) -> dict[str, str]:
    a = author_to_ris(a)  # normalize to "Last, First"
    last, _, first = a.partition(",")
    if first.strip():
        return {"creatorType": "author", "firstName": first.strip(),
                "lastName": last.strip()}
    return {"creatorType": "author", "name": last.strip()}


def entry_to_zotero_item(e: dict[str, Any],
                         collection: str | None) -> dict[str, Any]:
    ris_ty = (e.get("type") or RIS_TYPE_DEFAULT).upper()
    ty = RIS_TO_ZOTERO_TYPE.get(ris_ty, "document")
    item: dict[str, Any] = {"itemType": ty}
    extra: list[str] = []
    if t := e.get("title"):
        item["title"] = t
    if st := e.get("shortTitle"):
        item["shortTitle"] = st
    if authors := e.get("authors"):
        item["creators"] = [author_to_creator(a) for a in authors]
    if y := e.get("year"):
        item["date"] = str(y)
    if d := e.get("doi"):
        if ty == "journalArticle":
            item["DOI"] = d
        else:
            extra.append(f"DOI: {d}")
    if isbn := e.get("isbn"):
        if ty in ("book", "bookSection"):
            item["ISBN"] = isbn
        else:
            extra.append(f"ISBN: {isbn}")
    if url := e.get("url"):
        item["url"] = url
    if j := e.get("journal"):
        item["publicationTitle" if ty == "journalArticle" else "seriesTitle"] = j
    if v := e.get("volume"):
        item["volume"] = v
    if iss := e.get("issue"):
        item["issue"] = iss
    if pages := e.get("pages"):
        item["pages"] = pages
    if n := e.get("numPages"):
        if ty in ZOTERO_NUMPAGES_TYPES:
            item["numPages"] = str(n)
        else:
            extra.append(f"pages: {n}")
    if pub := e.get("publisher"):
        item["publisher"] = pub
    if lang := e.get("language"):
        item["language"] = lang
    if ab := e.get("abstract"):
        item["abstractNote"] = " ".join(ab.split())
    if extra:
        item["extra"] = "\n".join(extra)
    if collection:
        item["collections"] = [collection]
    return item


def api_request(method: str, path: str, key: str,
                body: bytes | None = None,
                content_type: str = "application/json",
                extra_headers: dict[str, str] | None = None) -> Any:
    """One call against api.zotero.org; returns parsed JSON, raw text, or None."""
    req = urllib.request.Request(ZOTERO_API_BASE + path, data=body,
                                 method=method)
    req.add_header("Zotero-API-Version", "3")
    req.add_header("Zotero-API-Key", key)
    if body is not None:
        req.add_header("Content-Type", content_type)
    for h, v in (extra_headers or {}).items():
        req.add_header(h, v)
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw.decode("utf-8", "replace")


def upload_attachment(user: str, key: str, parent: str, pdf: Path) -> str:
    """Create an imported_file attachment under parent and upload the PDF.

    Returns the attachment item key. Zotero's three-step contract: register
    the attachment item, ask for upload authorization (md5/size/mtime), then
    either stop on {"exists": 1} or POST prefix+bytes+suffix and confirm.
    """
    att = [{
        "itemType": "attachment",
        "linkMode": "imported_file",
        "parentItem": parent,
        "title": pdf.name,
        "filename": pdf.name,
        "contentType": "application/pdf",
    }]
    created = api_request("POST", f"/users/{user}/items", key,
                          json.dumps(att).encode())
    att_key = created["successful"]["0"]["key"]

    data = pdf.read_bytes()
    form = urllib.parse.urlencode({
        "md5": hashlib.md5(data).hexdigest(),
        "filename": pdf.name,
        "filesize": len(data),
        "mtime": int(pdf.stat().st_mtime * 1000),
    }).encode()
    auth = api_request("POST", f"/users/{user}/items/{att_key}/file", key,
                       form, "application/x-www-form-urlencoded",
                       {"If-None-Match": "*"})
    if isinstance(auth, dict) and auth.get("exists"):
        return att_key
    body = auth["prefix"].encode() + data + auth["suffix"].encode()
    _external_upload(auth, body)
    confirm = urllib.parse.urlencode({"upload": auth["uploadKey"]}).encode()
    api_request("POST", f"/users/{user}/items/{att_key}/file", key,
                confirm, "application/x-www-form-urlencoded",
                {"If-None-Match": "*"})
    return att_key


def _external_upload(auth: dict[str, Any], body: bytes) -> None:
    """POST the assembled upload body to the storage URL Zotero designated."""
    req = urllib.request.Request(auth["url"], data=body, method="POST")
    req.add_header("Content-Type", auth["contentType"])
    with urllib.request.urlopen(req, timeout=300) as resp:
        resp.read()


def cmd_inject(args: argparse.Namespace) -> int:
    if args.entries_json:
        entries = json.loads(args.entries_json)
    elif args.entries_file:
        entries = json.loads(Path(args.entries_file).read_text())
    else:
        entries = json.loads(sys.stdin.read())
    if isinstance(entries, dict):
        entries = [entries]

    items = [entry_to_zotero_item(e, args.collection) for e in entries]
    if args.dry_run:
        json.dump(items, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    user, key = resolve_credentials(args)
    results: list[dict[str, Any]] = []
    status = 0
    created = api_request("POST", f"/users/{user}/items", key,
                          json.dumps(items).encode())
    for idx, entry in enumerate(entries):
        row: dict[str, Any] = {"title": entry.get("title")}
        ok = created.get("successful", {}).get(str(idx))
        if not ok:
            row["error"] = created.get("failed", {}).get(str(idx),
                                                         "not created")
            results.append(row)
            status = 1
            continue
        row["itemKey"] = ok["key"]
        if entry.get("attach_pdf") and (p := entry.get("pdf")):
            pdf = Path(p)
            if pdf.exists():
                try:
                    row["attachmentKey"] = upload_attachment(
                        user, key, ok["key"], pdf)
                except (urllib.error.URLError, KeyError, OSError) as exc:
                    row["attachment_error"] = f"{type(exc).__name__}: {exc}"
                    status = 1
            else:
                row["attachment_error"] = "pdf not found"
                status = 1
        results.append(row)
    json.dump({"library": f"users/{user}", "results": results},
              sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return status


# --- CLI -------------------------------------------------------------------

def resolve_db_path(override: str | None) -> Path | None:
    if override:
        p = Path(override)
        return p if p.exists() else None
    return find_zotero_db()


def cmd_probe(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.zotero_db)
    conn = zotero_open(db_path) if db_path else None
    out: list[dict[str, Any]] = []
    for pdf_arg in args.pdf:
        pdf = Path(pdf_arg)
        if not pdf.exists():
            out.append({"pdf": str(pdf), "error": "not found"})
            continue
        try:
            out.append(probe_one(pdf, conn, args.library))
        except Exception as exc:
            out.append({"pdf": str(pdf), "error": f"{type(exc).__name__}: {exc}"})
    payload = {
        "zotero_db": str(db_path) if db_path else None,
        "zotero_lookup": db_path is not None,
        "items": out,
    }
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def cmd_match(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.zotero_db)
    if db_path is None:
        # No database: "could not look", never a clean negative.
        json.dump({"zotero_db": None, "matches": [], "verdict": "unchecked",
                   "consulted": [], "skipped": ["no Zotero database found"]},
                  sys.stdout)
        sys.stdout.write("\n")
        return 0
    conn = zotero_open(db_path)
    result = zotero_matches(
        conn,
        doi=args.doi,
        isbn=args.isbn,
        arxiv=args.arxiv,
        handle=args.handle,
        title=args.title,
        year=args.year,
        first_author=args.author,
        pdf_path=Path(args.pdf) if args.pdf else None,
        library=args.library,
    )
    json.dump({"zotero_db": str(db_path), **result},
              sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    if args.entries_json:
        entries = json.loads(args.entries_json)
    elif args.entries_file:
        entries = json.loads(Path(args.entries_file).read_text())
    else:
        entries = json.loads(sys.stdin.read())
    if isinstance(entries, dict):
        entries = [entries]
    body = "".join(entry_to_ris(e) for e in entries)
    out = Path(args.out)
    out.write_text(body)
    print(str(out.resolve()))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(prog="zotero-import.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    pp = sub.add_parser("probe", help="extract metadata + Zotero dup hits")
    pp.add_argument("pdf", nargs="+")
    pp.add_argument("--zotero-db", help="override Zotero sqlite path")
    pp.add_argument("--library", default=USER_LIBRARY,
                    help="dedup scope: 'user' (default, the inject "
                         "destination), 'all', or a numeric libraryID")
    pp.set_defaults(func=cmd_probe)

    pm = sub.add_parser("match", help="refined Zotero dedup lookup (cascade: "
                                      "file hash, identifiers, filename, "
                                      "author-year-title, title overlap)")
    pm.add_argument("--title", help="title (exact key with --author/--year; "
                                    "fuzzy last resort alone)")
    pm.add_argument("--doi", help="DOI to exact-match")
    pm.add_argument("--isbn", help="ISBN to exact-match (any hyphenation)")
    pm.add_argument("--arxiv", help="arXiv id to match (e.g. 2401.01234)")
    pm.add_argument("--handle", help="handle URL or hdl.handle.net path")
    pm.add_argument("--author", help="first author (any format); with --year "
                                     "and --title forms the pre-DOI book key")
    pm.add_argument("--year", help="publication year")
    pm.add_argument("--pdf", help="PDF path: content hash when the file "
                                  "exists, attachment filename either way")
    pm.add_argument("--library", default=USER_LIBRARY,
                    help="dedup scope: 'user' (default, the inject "
                         "destination), 'all', or a numeric libraryID")
    pm.add_argument("--zotero-db", help="override Zotero sqlite path")
    pm.set_defaults(func=cmd_match)

    pw = sub.add_parser("write", help="write combined RIS file from JSON entries")
    pw.add_argument("--out", required=True, help="output RIS path")
    g = pw.add_mutually_exclusive_group()
    g.add_argument("--entries-json", help="inline JSON: array of entry dicts")
    g.add_argument("--entries-file", help="path to JSON file with entries")
    pw.set_defaults(func=cmd_write)

    pi = sub.add_parser("inject",
                        help="create items (and upload PDFs) via the Zotero API")
    gi = pi.add_mutually_exclusive_group()
    gi.add_argument("--entries-json", help="inline JSON: array of entry dicts")
    gi.add_argument("--entries-file", help="path to JSON file with entries")
    pi.add_argument("--collection", help="collection key to file items under")
    pi.add_argument("--user-id", help="Zotero user id (else ZOTERO_USER_ID)")
    pi.add_argument("--api-key", help="RW key (else ZOTERO_RW_API_KEY; "
                                      "prefer env/keys file over argv)")
    pi.add_argument("--dry-run", action="store_true",
                    help="print the Zotero item JSON, do not call the API")
    pi.set_defaults(func=cmd_inject)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

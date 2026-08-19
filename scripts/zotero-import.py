#!/usr/bin/env python3
"""Helper for the zotero-import skill.

Subcommands: probe, match, write, inject, enrich, sync-index, audit, attach.
The last three work without the Zotero desktop database, against a cached
pull of the library from the Web API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
import unicodedata
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
        digest = file_md5(pdf_path)
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
    # Tags below follow Zotero's RIS translator field map (translators/RIS.js).
    # `CY` is its default for place, except conferencePaper, exported as `C1`.
    if place := e.get("place"):
        lines.append(f"{'C1' if ty in ('CONF', 'CPAPER') else 'CY'}  - {place}")
    if ed := e.get("edition"):
        lines.append(f"ET  - {ed}")
    if genre := e.get("genre"):
        lines.append(f"M3  - {genre}")
    # No unambiguous tag exists for these. `SN` already carries the ISBN
    # above, and Zotero reads a second `SN` as reportNumber/ISSN depending on
    # type — emitting one would silently overwrite or be misread. `M1` and
    # `SV` split seriesNumber by type, and conferenceName has no import tag at
    # all. Keyword lines keep the value visible and searchable in Zotero
    # instead, reusing the convention this function already applies to an
    # orphaned page count.
    for key in ("issn", "number", "seriesNumber", "conferenceName"):
        if val := e.get(key):
            lines.append(f"KW  - {key}:{val}")
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

# Every code in RIS_VALID_TYPES must appear here. A code `write` accepts but
# `inject` cannot resolve used to collapse into `document` without a word —
# no 400, no log line, just a generic item where a patent was meant, which is
# harder to notice than the error it replaces. Six such codes existed
# (CPAPER, GOVDOC, PAT, STAND, UNPB, WEB); `test_every_accepted_ris_code_maps
# _to_a_zotero_type` now keeps the two sets in step.
#
# Correspondences follow Zotero's own RIS translator (translators/RIS.js,
# `importTypeMap` + the inverted `exportTypeMap`) where it has an opinion, so
# an item imported through this script and one imported through Zotero's
# importer land on the same type. Two departures, both deliberate:
#   STAND  the translator says `report`, but that line predates the `standard`
#          item type; schema 42 has `standard`, and RIS STAND means Standard.
#   UNPB   the translator has no entry, so it would fall through to its
#          journalArticle default. Every neighbouring unpublished-work code it
#          *does* map (INPR, UNPD, PAMP, UNBILL) goes to `manuscript`.
RIS_TO_ZOTERO_TYPE = {
    "JOUR": "journalArticle",
    "BOOK": "book",
    "THES": "thesis",
    "RPRT": "report",
    "GOVDOC": "report",
    "CHAP": "bookSection",
    "CONF": "conferencePaper",
    "CPAPER": "conferencePaper",
    "MANSCPT": "manuscript",
    "UNPB": "manuscript",
    "NEWS": "newspaperArticle",
    "MGZN": "magazineArticle",
    "PAT": "patent",
    "STAND": "standard",
    "WEB": "webpage",
    "GEN": "document",
}

# Field placement is per item type. Zotero gives each type its own field set,
# and posting a field the type does not own is a hard 400 from the API
# (`'numPages' is not a valid field for type 'report'`), so a mapper that
# emits `publisher`/`volume`/`seriesTitle` unconditionally cannot import a
# report, a thesis or a manuscript at all.
#
# The two tables below are a reduced snapshot of https://api.zotero.org/schema
# (schema version 42, consulted 2026-08-14): the eight slots this mapper emits
# across the ten types RIS_TO_ZOTERO_TYPE can produce. An explicit table
# rather than a vendored copy of the schema — 40 readable lines a reviewer can
# check against the diff, where the schema file is 385 KB of JSON that is 95%
# irrelevant here and unreviewable in a merge request. Either way `inject`
# stays offline; the drift check lives in the test suite's `slow` tier, which
# re-derives both tables from the live schema.

# Preference order per slot: the first field the target type owns wins. Kept
# beside the resolved table so the derivation is documented and re-runnable.
ZOTERO_SLOT_PREFERENCES: dict[str, tuple[str, ...]] = {
    "container": ("publicationTitle", "proceedingsTitle", "bookTitle",
                  "websiteTitle", "seriesTitle", "series"),
    # `assignee` is NOT in this chain. A patent's assignee is its owner, not
    # its publisher, and a wrong field is worse than an honest `extra` line.
    "publisher": ("publisher", "university", "institution", "organization"),
    # `date` is not universal: `patent` has no such field, only filingDate /
    # issueDate / priorityDate. An entry's year is its issue year.
    "date": ("date", "issueDate"),
    "place": ("place",),
    "number": ("reportNumber", "patentNumber", "number"),
    "genre": ("reportType", "thesisType", "manuscriptType", "websiteType",
              "type"),
    "conferenceName": ("conferenceName",),
    "edition": ("edition",),
    "seriesNumber": ("seriesNumber",),
    # A page *count* only ever goes in a real numPages field. `report` has a
    # `pages` field, but that is its page *range* (Zotero labels it "Pages",
    # not "# of Pages"), so borrowing it would conflate the two and clobber a
    # genuine range. Reports send the count to `extra` instead.
    "numPages": ("numPages",),
    "pages": ("pages",),
    "volume": ("volume",),
    "issue": ("issue",),
    "DOI": ("DOI",),
    "ISBN": ("ISBN",),
    "ISSN": ("ISSN",),
}

# Resolved: slot → {item type: field name}. A type absent from a slot's map
# has no home for it and falls through to `extra`.
ZOTERO_SLOT_FIELD: dict[str, dict[str, str]] = {
    "container": {
        "journalArticle": "publicationTitle",
        "book": "series",
        "thesis": "series",
        "report": "seriesTitle",
        "bookSection": "bookTitle",
        "conferencePaper": "proceedingsTitle",
        "newspaperArticle": "publicationTitle",
        "magazineArticle": "publicationTitle",
        "webpage": "websiteTitle",
    },
    "publisher": {
        "journalArticle": "publisher",
        "book": "publisher",
        "thesis": "university",
        "report": "institution",
        "bookSection": "publisher",
        "conferencePaper": "publisher",
        "manuscript": "institution",
        "newspaperArticle": "publisher",
        "magazineArticle": "publisher",
        "standard": "publisher",
        "webpage": "publisher",
        "document": "publisher",
    },
    "date": {
        "journalArticle": "date",
        "book": "date",
        "thesis": "date",
        "report": "date",
        "bookSection": "date",
        "conferencePaper": "date",
        "manuscript": "date",
        "newspaperArticle": "date",
        "magazineArticle": "date",
        "patent": "issueDate",
        "standard": "date",
        "webpage": "date",
        "document": "date",
    },
    "place": {
        "journalArticle": "place",
        "book": "place",
        "thesis": "place",
        "report": "place",
        "bookSection": "place",
        "conferencePaper": "place",
        "manuscript": "place",
        "newspaperArticle": "place",
        "magazineArticle": "place",
        "patent": "place",
        "standard": "place",
        "webpage": "place",
        "document": "place",
    },
    "number": {
        "report": "reportNumber",
        "manuscript": "number",
        "patent": "patentNumber",
        "standard": "number",
    },
    "genre": {
        "thesis": "thesisType",
        "report": "reportType",
        "manuscript": "manuscriptType",
        "standard": "type",
        "webpage": "websiteType",
        "document": "type",
    },
    "conferenceName": {
        "conferencePaper": "conferenceName",
    },
    "edition": {
        "book": "edition",
        "bookSection": "edition",
        "newspaperArticle": "edition",
        "standard": "edition",
    },
    "seriesNumber": {
        "book": "seriesNumber",
        "thesis": "seriesNumber",
        "report": "seriesNumber",
        "bookSection": "seriesNumber",
        "conferencePaper": "seriesNumber",
    },
    "numPages": {
        "book": "numPages",
        "thesis": "numPages",
        "manuscript": "numPages",
        "standard": "numPages",
    },
    "pages": {
        "journalArticle": "pages",
        "report": "pages",
        "bookSection": "pages",
        "conferencePaper": "pages",
        "newspaperArticle": "pages",
        "magazineArticle": "pages",
        "patent": "pages",
    },
    "volume": {
        "journalArticle": "volume",
        "book": "volume",
        "bookSection": "volume",
        "conferencePaper": "volume",
        "newspaperArticle": "volume",
        "magazineArticle": "volume",
    },
    "issue": {
        "journalArticle": "issue",
        "conferencePaper": "issue",
        "newspaperArticle": "issue",
        "magazineArticle": "issue",
    },
    "DOI": {
        "journalArticle": "DOI",
        "book": "DOI",
        "thesis": "DOI",
        "report": "DOI",
        "bookSection": "DOI",
        "conferencePaper": "DOI",
        "manuscript": "DOI",
        "newspaperArticle": "DOI",
        "magazineArticle": "DOI",
        "patent": "DOI",
        "standard": "DOI",
        "webpage": "DOI",
        "document": "DOI",
    },
    "ISBN": {
        "book": "ISBN",
        "thesis": "ISBN",
        "report": "ISBN",
        "bookSection": "ISBN",
        "conferencePaper": "ISBN",
        "standard": "ISBN",
    },
    "ISSN": {
        "journalArticle": "ISSN",
        "book": "ISSN",
        "thesis": "ISSN",
        "report": "ISSN",
        "bookSection": "ISSN",
        "conferencePaper": "ISSN",
        "newspaperArticle": "ISSN",
        "magazineArticle": "ISSN",
    },
}

# Labels used when a slot has no home on the target type. These are CSL
# variable names, which Zotero parses back out of the Extra field and feeds to
# citeproc — so a homeless value still cites correctly instead of being lost.
ZOTERO_SLOT_EXTRA_LABEL: dict[str, str] = {
    "container": "container-title",
    "publisher": "publisher",
    "date": "issued",
    "place": "publisher-place",
    "number": "number",
    "genre": "genre",
    "conferenceName": "event-title",
    "edition": "edition",
    "seriesNumber": "collection-number",
    "numPages": "number-of-pages",
    "pages": "page",
    "volume": "volume",
    "issue": "issue",
    "DOI": "DOI",
    "ISBN": "ISBN",
    "ISSN": "ISSN",
}

# Every key an entry may carry, across both the RIS and the API path. An
# unrecognised key is refused rather than ignored: a misspelt `reportNmbr`
# that silently does nothing is the same defect class as a field the mapper
# drops, and the caller has no way to notice it.
ENTRY_KEYS = frozenset({
    "type", "title", "shortTitle", "authors", "year", "doi", "isbn", "issn",
    "url", "journal", "volume", "issue", "pages", "numPages", "publisher",
    "place", "number", "genre", "conferenceName", "edition", "seriesNumber",
    "language", "abstract", "pdf", "attach_pdf",
})


def validate_entry_keys(entries: list[dict[str, Any]]) -> None:
    """Abort on any entry key the mapper does not read."""
    unknown = sorted({k for e in entries for k in e} - ENTRY_KEYS)
    if unknown:
        raise SystemExit(
            f"unknown entry key(s): {', '.join(unknown)}. "
            f"Known keys: {', '.join(sorted(ENTRY_KEYS))}")


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


def place_slot(item: dict[str, Any], extra: list[str],
               slot: str, value: str) -> None:
    """Store `value` in the slot's field for this item type, else in `extra`.

    Nothing is dropped: a slot the target type has no field for (or whose
    field is already taken) is appended to `extra` under its CSL variable
    name, where Zotero still reads it.
    """
    field = ZOTERO_SLOT_FIELD[slot].get(item["itemType"])
    if field and field not in item:
        item[field] = value
    else:
        extra.append(f"{ZOTERO_SLOT_EXTRA_LABEL[slot]}: {value}")


def entry_to_zotero_item(e: dict[str, Any],
                         collection: str | None) -> dict[str, Any]:
    ris_ty = (e.get("type") or RIS_TYPE_DEFAULT).upper()
    ty = RIS_TO_ZOTERO_TYPE.get(ris_ty, "document")
    item: dict[str, Any] = {"itemType": ty}
    extra: list[str] = []
    if ris_ty not in RIS_TO_ZOTERO_TYPE:
        # Degrading to `document` is a lossy guess; say so in the log and
        # leave the original code on the item so the downgrade is auditable
        # from the library rather than invisible.
        logging.warning("RIS type %r has no Zotero equivalent; "
                        "importing as `document`", ris_ty)
        extra.append(f"Unmapped RIS type: {ris_ty}")
    # Universal fields — every type RIS_TO_ZOTERO_TYPE can produce owns these.
    # `date` is NOT among them (patent has none); it goes through a slot.
    if t := e.get("title"):
        item["title"] = t
    if st := e.get("shortTitle"):
        item["shortTitle"] = st
    if authors := e.get("authors"):
        item["creators"] = [author_to_creator(a) for a in authors]
    if url := e.get("url"):
        item["url"] = url
    if lang := e.get("language"):
        item["language"] = lang
    if ab := e.get("abstract"):
        item["abstractNote"] = " ".join(ab.split())
    # Type-dependent slots. Order matters: `pages` claims a shared field
    # before `numPages` would, so an explicit range beats a derived count.
    for slot, value in (("date", e.get("year")),
                        ("DOI", e.get("doi")),
                        ("ISBN", e.get("isbn")),
                        ("ISSN", e.get("issn")),
                        ("container", e.get("journal")),
                        ("conferenceName", e.get("conferenceName")),
                        ("volume", e.get("volume")),
                        ("issue", e.get("issue")),
                        ("edition", e.get("edition")),
                        ("seriesNumber", e.get("seriesNumber")),
                        ("pages", e.get("pages")),
                        ("numPages", e.get("numPages")),
                        ("number", e.get("number")),
                        ("genre", e.get("genre")),
                        ("place", e.get("place")),
                        ("publisher", e.get("publisher"))):
        if value:
            place_slot(item, extra, slot, str(value))
    if extra:
        item["extra"] = "\n".join(extra)
    if collection:
        item["collections"] = [collection]
    return item


def plan_enrichment(data: dict[str, Any], sets: dict[str, str],
                    expect_title: str,
                    overwrite: bool = False) -> tuple[dict[str, str], list[str]]:
    """Decide what to write on an existing item. Pure: no network, no I/O.

    Returns (fields to patch, refusals). A refusal is a reason NOT to write a
    given field; the caller reports every one of them and writes the rest.

    Three guards, in the order they catch real mistakes:

    1. Wrong item. `expect_title` must appear in the item's title. Item keys
       are opaque, so a transposed key silently enriches an unrelated work —
       the one failure mode the API cannot catch for us. An empty title on
       the target is a refusal, not a pass: "could not check" is not "clear".
    2. Already correct. A field whose stored value equals the requested one is
       dropped from the patch, not rewritten — a no-op write still bumps the
       item version and shows up as an edit in every sync.
    3. Conflicting value. A field that already holds something DIFFERENT is
       refused unless `overwrite` is passed. Replacing a curated value is an
       arbitration the caller must make explicitly; correcting an empty field
       is not.
    """
    refusals: list[str] = []
    title = (data.get("title") or "").strip()
    if not title:
        return {}, [f"item {data.get('key', '?')}: no title to check against "
                    f"{expect_title!r} — refusing to write blind"]
    if expect_title.lower() not in title.lower():
        return {}, [f"item {data.get('key', '?')}: title {title!r} does not "
                    f"contain {expect_title!r} — wrong item?"]

    patch: dict[str, str] = {}
    for field, value in sets.items():
        if field not in data:
            refusals.append(f"{field}: item type {data.get('itemType')!r} has "
                            f"no such field (Zotero field names are "
                            f"case-sensitive, e.g. DOI not doi)")
            continue
        current = (data.get(field) or "").strip()
        if current == value:
            continue
        if current and not overwrite:
            refusals.append(f"{field}: already holds {current!r}, not "
                            f"{value!r} — pass --overwrite to arbitrate")
            continue
        patch[field] = value
    return patch, refusals


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


def corroborate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Check one inject entry's metadata against its own PDF's front matter.

    This is where corroborate() has to bite. `inject` is the step that makes
    metadata permanent, and the failure it guards is silent by construction: a
    DOI scraped from page text usually belongs to a work the document *cites*,
    so the resolver returns a well-formed record for the wrong paper and every
    later reader inherits it. Measured on a 158-PDF backfill, 77 of 116
    machine-built drafts needed correction once someone read the page.
    """
    pdf = entry.get("pdf")
    if not pdf or not entry.get("title"):
        return {"confidence": "unchecked", "reason": "no pdf or no title"}
    path = Path(pdf)
    if not path.exists() or path.suffix.lower() != ".pdf":
        return {"confidence": "unchecked", "reason": "no readable PDF"}
    try:
        text = pdftotext_range(path, 1, FIRST_PAGES)
    except Exception as exc:
        return {"confidence": "unchecked", "reason": f"{type(exc).__name__}"}
    return corroborate({"title": entry.get("title"),
                        "authors": entry.get("authors") or []}, text)


def cmd_inject(args: argparse.Namespace) -> int:
    if args.entries_json:
        entries = json.loads(args.entries_json)
    elif args.entries_file:
        entries = json.loads(Path(args.entries_file).read_text())
    else:
        entries = json.loads(sys.stdin.read())
    if isinstance(entries, dict):
        entries = [entries]
    validate_entry_keys(entries)

    checks = [corroborate_entry(e) for e in entries]
    if not args.skip_corroboration:
        blocked = [(e, c) for e, c in zip(entries, checks)
                   if c["confidence"] == "contradicted"]
        if blocked:
            json.dump({"error": "metadata contradicted by the document",
                       "hint": "the identifier a resolver followed is probably "
                               "a cited work's, not this document's; rebuild "
                               "the metadata, or pass --skip-corroboration",
                       "entries": [{"title": e.get("title"),
                                    "pdf": e.get("pdf"), **c}
                                   for e, c in blocked]},
                      sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
            return 1

    items = [entry_to_zotero_item(e, args.collection) for e in entries]
    if args.dry_run:
        json.dump({"items": items, "corroboration": checks},
                  sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")
        return 0

    user, key = resolve_credentials(args)
    results: list[dict[str, Any]] = []
    status = 0
    created = api_request("POST", f"/users/{user}/items", key,
                          json.dumps(items).encode())
    for idx, entry in enumerate(entries):
        row: dict[str, Any] = {"title": entry.get("title"),
                               "corroboration": checks[idx]["confidence"]}
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


def parse_set(pairs: list[str]) -> dict[str, str]:
    """`--set DOI=10.x/y` pairs into a dict. Splits on the FIRST `=` only."""
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--set expects FIELD=VALUE, got {pair!r}")
        field, value = pair.split("=", 1)
        out[field.strip()] = value.strip()
    return out


def enrich_one(user: str, key: str, job: dict[str, Any],
               overwrite: bool, dry_run: bool) -> dict[str, Any]:
    """Fill fields on ONE existing item. See plan_enrichment for the guards."""
    item_key = job["item_key"]
    row: dict[str, Any] = {"itemKey": item_key}
    path = f"/users/{user}/items/{item_key}"
    data = api_request("GET", path, key)["data"]
    row["title"] = data.get("title")

    patch, refusals = plan_enrichment(data, job["set"], job["expect_title"],
                                      overwrite)
    if refusals:
        row["refused"] = refusals
    if not patch:
        row["status"] = "nothing to write"
        return row
    row["patch"] = patch
    if dry_run:
        row["status"] = f"would patch at version {data['version']}"
        return row

    # If-Unmodified-Since-Version makes a concurrent edit fail with 412 rather
    # than silently winning. Without it, two sessions enriching the same item
    # both report success and one of the writes is gone.
    try:
        api_request("PATCH", path, key, json.dumps(patch).encode(),
                    extra_headers={
                        "If-Unmodified-Since-Version": str(data["version"])})
    except urllib.error.HTTPError as exc:
        row["status"] = "failed"
        row["error"] = (f"HTTP {exc.code}: "
                        f"{exc.read().decode('utf-8', 'replace')[:200]}")
        return row

    # Read back. A 204 says the request was accepted, not that the value is
    # what we meant — the only proof is the stored item.
    after = api_request("GET", path, key)["data"]
    bad = {f: after.get(f) for f, v in patch.items() if (after.get(f) or "") != v}
    row["status"] = "written" if not bad else "readback mismatch"
    row["version"] = after["version"]
    if bad:
        row["stored"] = bad
    return row


def cmd_enrich(args: argparse.Namespace) -> int:
    if args.jobs_file:
        jobs = json.loads(Path(args.jobs_file).read_text())
    else:
        jobs = [{"item_key": args.item_key,
                 "expect_title": args.expect_title,
                 "set": parse_set(args.set or [])}]
    if isinstance(jobs, dict):
        jobs = [jobs]
    for job in jobs:
        missing = {"item_key", "expect_title", "set"} - set(job)
        if missing:
            raise SystemExit(f"job missing {sorted(missing)}: {job}")
        if not job["set"]:
            raise SystemExit(f"job for {job['item_key']} sets nothing")

    user, key = resolve_credentials(args)
    results = [enrich_one(user, key, j, args.overwrite, args.dry_run)
               for j in jobs]
    json.dump({"library": f"users/{user}", "results": results},
              sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return enrich_status(results, args.dry_run)


def enrich_status(results: list[dict[str, Any]], dry_run: bool) -> int:
    """Exit code for an enrich run. Non-zero when anything asked for did not
    happen — a refusal included. A run that refused every field and one that
    wrote every field must not return the same code, or the caller cannot tell
    "done" from "declined to act".
    """
    ok = {"written", "nothing to write"}
    for row in results:
        if row.get("refused"):
            return 1
        if dry_run:
            continue
        if row.get("status") not in ok:
            return 1
    return 0


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


# ---------------------------------------------------------------------------
# Web-API library index — deduplication without the desktop database
#
# `probe` and `match` consult the desktop client's zotero.sqlite. On a machine
# that has no desktop client the file is simply absent, every lookup returns
# verdict "unchecked", and a bulk backfill runs with no dedup key at all —
# which is how you re-import documents the library already holds. The index
# below is the same library pulled from the Web API and cached on disk, so the
# cascade always has something to consult.
#
# It also carries every attachment's md5. That is a *stronger* key than any the
# sqlite path offers: content identity survives renaming, re-filing and
# metadata drift, and it answers the only question a staging directory really
# asks — is this exact file already stored in Zotero?
# ---------------------------------------------------------------------------

INDEX_CACHE_DIR = (
    Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    / "zotero-import"
)
INDEX_SCHEMA = 1
INDEX_MAX_AGE_HOURS = 24
# Titles shorter than this carry too few distinctive tokens to match on.
TITLE_MIN_TOKENS = 3


def resolve_read_credentials(args: argparse.Namespace) -> tuple[str, str]:
    """(user_id, key) for read-only calls: RO key preferred, RW accepted.

    Distinct from resolve_credentials(), which demands a read-write key. An
    index sync needs no write scope, and requiring one would gate a read-only
    audit behind a credential the operator may deliberately not have loaded.
    """
    env_file = load_env_file(ZOTERO_ENV_FILE)
    key = (getattr(args, "api_key", None)
           or os.environ.get("ZOTERO_API_KEY")
           or env_file.get("ZOTERO_API_KEY")
           or os.environ.get("ZOTERO_RW_API_KEY")
           or env_file.get("ZOTERO_RW_API_KEY"))
    user = (getattr(args, "user_id", None)
            or os.environ.get("ZOTERO_USER_ID")
            or env_file.get("ZOTERO_USER_ID"))
    if not key:
        raise SystemExit("no ZOTERO_API_KEY / ZOTERO_RW_API_KEY (flag, env, "
                         f"or {ZOTERO_ENV_FILE})")
    if not user:
        raise SystemExit("no ZOTERO_USER_ID (flag, env, or "
                         f"{ZOTERO_ENV_FILE})")
    return user, key


def _api_get_retry(path: str, key: str, attempts: int = 5) -> Any:
    """GET with exponential backoff — a 17k-item sync is ~170 calls."""
    for n in range(attempts):
        try:
            return api_request("GET", path, key)
        except urllib.error.HTTPError as exc:
            # 401/403/404 are answers, not outages. Retrying one turns a fast,
            # legible misconfiguration into a 30-second backoff that ends in
            # the same failure — and buries the cause. 429 and 5xx are the
            # transient ones worth waiting on.
            if exc.code not in (429,) and exc.code < 500:
                raise
            if n == attempts - 1:
                raise
            time.sleep(2 ** n)
        except (urllib.error.URLError, OSError):
            if n == attempts - 1:
                raise
            time.sleep(2 ** n)
    return None


def _api_paged(user: str, key: str, item_type: str,
               progress: bool = False) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    start = 0
    while True:
        q = urllib.parse.urlencode(
            {"itemType": item_type, "limit": "100", "start": str(start)})
        page = _api_get_retry(f"/users/{user}/items?{q}", key)
        if not page:
            break
        out.extend(page)
        start += 100
        if progress and start % 1000 == 0:
            logging.info("  %s: %d fetched", item_type, start)
    return out


def file_md5(path: Path, chunk: int = 1 << 20) -> str:
    """Content hash, read in chunks — an audit hashes every staged file, and
    this corpus holds a 62 MB Internet Archive scan."""
    h = hashlib.md5()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def index_path(user: str) -> Path:
    return INDEX_CACHE_DIR / f"index-{user}.json"


def build_index(user: str, key: str) -> dict[str, Any]:
    """Pull works and attachments from the Web API into one cache document."""
    works = []
    for it in _api_paged(user, key, "-attachment || note", progress=True):
        d = it["data"]
        works.append({
            "key": d.get("key"),
            "itemType": d.get("itemType"),
            "title": d.get("title", ""),
            "date": d.get("date", ""),
            "DOI": d.get("DOI", ""),
            "ISBN": d.get("ISBN", ""),
            "url": d.get("url", ""),
            "extra": d.get("extra", ""),
            "collections": d.get("collections", []),
            "creators": [c.get("lastName") or c.get("name", "")
                         for c in d.get("creators", [])],
        })
    atts = []
    for it in _api_paged(user, key, "attachment", progress=True):
        d = it["data"]
        atts.append({
            "key": d.get("key"),
            "parent": d.get("parentItem"),
            "filename": d.get("filename", ""),
            "md5": d.get("md5"),
            "contentType": d.get("contentType", ""),
            "linkMode": d.get("linkMode", ""),
        })
    return {"schema": INDEX_SCHEMA, "user": user,
            "fetched": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "works": works, "attachments": atts}


def load_index(user: str, key: str, *, refresh: bool = False,
               max_age_hours: float = INDEX_MAX_AGE_HOURS) -> dict[str, Any] | None:
    """Cached index, rebuilt when missing, stale, or explicitly refreshed.

    Returns None when no index exists and none could be built — the caller must
    keep that distinguishable from an empty library.
    """
    p = index_path(user)
    if not refresh and p.exists():
        age_h = (time.time() - p.stat().st_mtime) / 3600
        if age_h <= max_age_hours:
            try:
                idx = json.loads(p.read_text())
                if idx.get("schema") == INDEX_SCHEMA:
                    return idx
            except json.JSONDecodeError:
                pass
    try:
        idx = build_index(user, key)
    except Exception as exc:  # network, auth, rate limit
        logging.warning("index sync failed: %s", exc)
        if p.exists():
            try:
                return json.loads(p.read_text())
            except json.JSONDecodeError:
                return None
        return None
    INDEX_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(idx))
    return idx


def _name_key(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z]", "", s)


_TITLE_STOP = {"the", "a", "an", "of", "and", "in", "on", "for", "to", "with",
               "de", "la", "le", "les", "du", "des", "et", "un", "une"}


def _title_tokens(s: str) -> set[str]:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]", " ", s)
    return {w for w in s.split() if len(w) > 2 and w not in _TITLE_STOP}


def _title_windows(text: str, span: int = 3) -> list[set[str]]:
    """Token sets for every window of `span` consecutive lines.

    A title occupies a few consecutive lines (OCR breaks them further). Scoring the whole document
    bag instead lets scattered vocabulary satisfy a short generic title: the
    five ordinary words of "Systems of inequalities involving convex functions"
    all occur, far apart, in any paper about linear inequalities — which is how
    a Hoffman 1960 paper matched a different Hoffman paper at "strong".
    Requiring the words to co-occur in one window is what separates a title
    from a vocabulary.
    """
    lines = [ln for ln in (text or "").splitlines() if ln.strip()]
    out: list[set[str]] = []
    for i in range(len(lines)):
        for n in range(1, span + 1):
            if i + n <= len(lines):
                out.append(_title_tokens(" ".join(lines[i:i + n])))
    return [w for w in out if w]


# Both forms Zotero actually stores: "arXiv:2401.01234" in Extra, and an
# arxiv.org/abs/ URL in the url field.
ARXIV_ANY_RE = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/|arxiv[:\s]\s*)"
    r"((?:\d{4}\.\d{4,5})|(?:[a-z-]+/\d{7}))",
    re.IGNORECASE)
HDL_ANY_RE = re.compile(r"hdl\.handle\.net/([^\s)\]]+)", re.IGNORECASE)


def _isbn_key(raw: str) -> str:
    return re.sub(r"[^0-9Xx]", "", raw or "").upper()


def _index_views(idx: dict[str, Any]) -> dict[str, Any]:
    works = {w["key"]: w for w in idx["works"]}
    by_md5: dict[str, list[dict[str, Any]]] = {}
    by_filename: dict[str, list[dict[str, Any]]] = {}
    parents_with_file: set[str] = set()
    parents_with_pdf: set[str] = set()
    for a in idx["attachments"]:
        if a.get("md5"):
            by_md5.setdefault(a["md5"], []).append(a)
        if a.get("filename"):
            by_filename.setdefault(Path(a["filename"]).name, []).append(a)
        if a.get("parent") and str(a.get("linkMode", "")).startswith("imported"):
            parents_with_file.add(a["parent"])
            if a.get("contentType") == "application/pdf":
                parents_with_pdf.add(a["parent"])
    by_doi: dict[str, list[dict[str, Any]]] = {}
    by_isbn: dict[str, list[dict[str, Any]]] = {}
    by_arxiv: dict[str, list[dict[str, Any]]] = {}
    by_handle: dict[str, list[dict[str, Any]]] = {}
    by_surname: dict[str, list[dict[str, Any]]] = {}
    for w in idx["works"]:
        if w.get("DOI"):
            by_doi.setdefault(w["DOI"].lower().strip(), []).append(w)
        for isbn in re.findall(r"[0-9Xx-]{10,17}", w.get("ISBN") or ""):
            key = _isbn_key(isbn)
            if len(key) in (10, 13):
                by_isbn.setdefault(key, []).append(w)
        # Zotero has no arXiv or handle field: both live in `extra` or `url`,
        # which is where the desktop cascade finds them too.
        hay = f"{w.get('extra', '')} {w.get('url', '')}"
        for aid in ARXIV_ANY_RE.findall(hay):
            by_arxiv.setdefault(aid.lower(), []).append(w)
        for hdl in HDL_ANY_RE.findall(hay):
            by_handle.setdefault(hdl.lower().rstrip("/"), []).append(w)
        w["_year"] = (lambda m: m.group(0) if m else None)(
            YEAR_RE.search(w.get("date") or ""))
        w["_tokens"] = _title_tokens(w.get("title", ""))
        for c in w.get("creators", []):
            by_surname.setdefault(_name_key(c), []).append(w)
    return {"works": works, "by_md5": by_md5, "by_filename": by_filename,
            "by_doi": by_doi, "by_isbn": by_isbn, "by_arxiv": by_arxiv,
            "by_handle": by_handle, "by_surname": by_surname,
            "parents_with_file": parents_with_file,
            "parents_with_pdf": parents_with_pdf}


def api_matches(idx: dict[str, Any], *, doi: str | None = None,
                isbn: str | None = None, arxiv: str | None = None,
                handle: str | None = None,
                title: str | None = None, year: str | None = None,
                first_author: str | None = None,
                authors: list[str] | None = None,
                text: str | None = None,
                pdf_path: Path | None = None) -> dict[str, Any]:
    """Same cascade and same output contract as zotero_matches(), over the index.

    Keys strongest first: file content hash, DOI, attachment filename, then
    (creator, year, title). "consulted" and "skipped" are reported so a clean
    negative stays distinguishable from a lookup that could not run.

    `text` supplies extra evidence from the document itself (front-matter text,
    a filename slug). It widens what the *document* is allowed to say, never
    what counts as a hit: overlap is always scored against the library title's
    own tokens, so a bigger bag of document words can only help a true match
    surface — it cannot manufacture one. Passing a single guessed title instead
    is what makes an audit over-report "absent", because the guess comes from
    pdfinfo, which on scanned material reads "PII: 0014-2921(69)90001-4".
    """
    v = _index_views(idx)
    consulted: list[str] = []
    skipped: list[str] = []
    matches: list[dict[str, Any]] = []

    def emit(work_key: str, why: str, certainty: str,
             att: dict[str, Any] | None = None) -> None:
        w = v["works"].get(work_key)
        if not w:
            return
        if any(m["key"] == work_key for m in matches):
            return
        matches.append({
            "key": work_key, "why": [why], "certainty": certainty,
            "title": w.get("title", ""), "date": w.get("date", ""),
            "itemType": w.get("itemType", ""), "creators": w.get("creators", []),
            "has_file": work_key in v["parents_with_file"],
            "has_pdf": work_key in v["parents_with_pdf"],
            "attachment": att,
        })

    if pdf_path and pdf_path.exists():
        consulted.append("storageHash")
        digest = hashlib.md5(pdf_path.read_bytes()).hexdigest()
        for a in v["by_md5"].get(digest, []):
            if a.get("parent"):
                emit(a["parent"], "storageHash", "exact", a)
            else:
                matches.append({"key": None, "why": ["storageHash"],
                                "certainty": "exact", "title": a.get("filename", ""),
                                "orphan_attachment": a["key"], "has_file": True,
                                "has_pdf": a.get("contentType") == "application/pdf"})
    else:
        skipped.append("storageHash (no file on disk)")

    for label, supplied, bucket, norm in (
            ("doi", doi, "by_doi", lambda x: x.lower().strip()),
            ("isbn", isbn, "by_isbn", _isbn_key),
            ("arxiv", arxiv, "by_arxiv", lambda x: x.lower().strip()),
            ("handle", handle, "by_handle",
             lambda x: (HDL_ANY_RE.search(x).group(1) if HDL_ANY_RE.search(x)
                        else x).lower().rstrip("/")),
    ):
        if not supplied:
            skipped.append(f"{label} (none supplied)")
            continue
        if matches:
            continue
        consulted.append(label)
        for w in v[bucket].get(norm(supplied), []):
            emit(w["key"], label, "exact")

    if not matches and pdf_path and pdf_path.name:
        consulted.append("filename")
        for a in v["by_filename"].get(pdf_path.name, []):
            if a.get("parent"):
                emit(a["parent"], "filename", "strong", a)
    elif not matches:
        skipped.append("filename: no PDF name")

    if not matches and (title or text):
        toks = _title_tokens(title) | _title_tokens(text)
        surnames = [_name_key(a.split(",")[0]) for a in (authors or [])]
        if first_author:
            surnames.append(_name_key(first_author.split(",")[0]))
        surnames = [s for s in surnames if s]
        if len(toks) < TITLE_MIN_TOKENS:
            skipped.append("creator-year-title (title too short)")
        elif not surnames:
            skipped.append("creator-year-title (no author supplied)")
        else:
            consulted.append("creator-year-title")
            # A hit is "strong" only when the library title's words co-occur in
            # one place — the supplied title, or a window of consecutive lines
            # in the document. Matching the scattered bag stays available, but
            # only ever as "weak", which no verdict treats as a match on its own.
            windows = ([_title_tokens(title)] if title else []) + \
                      _title_windows(text or "")
            cands: dict[str, dict[str, Any]] = {}
            for s in surnames:
                for w in v["by_surname"].get(s, []):
                    cands[w["key"]] = w
            for w in cands.values():
                if not w["_tokens"]:
                    continue
                n = len(w["_tokens"])
                overlap = len(toks & w["_tokens"]) / n
                # Two questions, and a short title needs both answered. How
                # much of the library title did this window carry (recall), and
                # how much of the window was that title (precision)? Recall
                # alone lets three body lines accumulate all five words of
                # "Systems of inequalities involving convex functions" while
                # being about something else; precision is what says a title
                # line is nearly all title and a body window is not.
                best_recall = best_prec = 0.0
                for win in windows:
                    shared = len(win & w["_tokens"])
                    if not shared:
                        continue
                    recall, precision = shared / n, shared / len(win)
                    if (recall, precision) > (best_recall, best_prec):
                        best_recall, best_prec = recall, precision
                focused = best_recall
                same_year = bool(year and w["_year"] and year == w["_year"])
                near_year = bool(year and w["_year"]
                                 and abs(int(year) - int(w["_year"])) <= 3)
                phrase = best_prec >= 0.6
                if phrase and focused >= 0.8 and (same_year or not year
                                                  or not w["_year"]):
                    emit(w["key"], "creator-year-title", "strong")
                elif phrase and focused >= 0.75 and near_year:
                    emit(w["key"], "creator-year-title", "strong")
                elif overlap >= 0.45 or focused >= 0.45:
                    emit(w["key"], "title-overlap", "weak")
    elif not (title or text):
        skipped.append("creator-year-title (no title or text supplied)")

    order = {"exact": 0, "strong": 1, "weak": 2}
    matches.sort(key=lambda m: order.get(m["certainty"], 3))
    verdict = classify_matches(matches) if consulted else "unchecked"
    return {"matches": matches, "verdict": verdict,
            "consulted": consulted, "skipped": skipped,
            "source": "web-api-index", "index_fetched": idx.get("fetched")}


def _surname_in_text(surname: str, text: str) -> bool:
    """Is the surname present as a whole word (or run of whole words)?

    A bare substring test against punctuation-stripped text matches "Li" inside
    "published" and "Ng" inside "programming", so a document that contradicts
    the resolved record reads as partial agreement — the one verdict this check
    exists to prevent. Whole words are required; consecutive ones are re-joined
    so a spaced name ("van Neumann"), whose key drops the spaces, still hits.
    `text` is expected accent-stripped and lowercased, as _name_key leaves it.
    """
    if not surname:
        return False
    words = re.findall(r"[a-z]+", text)
    for i in range(len(words)):
        acc = ""
        for w in words[i:i + 4]:
            acc += w
            if acc == surname:
                return True
            if len(acc) >= len(surname):
                break
    return False


def corroborate(resolved: dict[str, Any], document_text: str) -> dict[str, Any]:
    """Does the metadata a resolver returned actually describe *this* document?

    A DOI or arXiv id scraped from page text is often a *cited* work's, not the
    document's own — resolving it yields clean, confident, wrong metadata that
    nothing downstream questions. Cross-check the resolved record against the
    document's own words: the first author's surname and a majority of the
    title's distinctive tokens should appear in the front matter.

    Returns {"confidence": corroborated|weak|contradicted|unchecked, ...}.
    Never decides on its own — it hands the caller a reason to look.
    """
    text = unicodedata.normalize("NFKD", document_text or "")
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    flat = re.sub(r"[^a-z0-9]", "", text)
    title = resolved.get("title") or ""
    authors = resolved.get("authors") or []
    if not flat or not title:
        return {"confidence": "unchecked",
                "reason": "no document text or no resolved title"}
    toks = _title_tokens(title)
    if not toks:
        # Nothing distinctive to compare, so nothing was checked. Returning the
        # strongest negative here accuses the resolver on no evidence.
        return {"confidence": "unchecked",
                "reason": "resolved title carries no distinctive words to check"}
    hits = sum(1 for t in toks if t in re.sub(r"[^a-z0-9 ]", " ", text).split())
    title_ratio = hits / len(toks)
    surname = _name_key(authors[0].split(",")[0]) if authors else ""
    author_ok = _surname_in_text(surname, text)
    if title_ratio >= 0.6 and (author_ok or not surname):
        conf = "corroborated"
    elif title_ratio >= 0.6 or author_ok:
        conf = "weak"
    else:
        conf = "contradicted"
    return {"confidence": conf, "title_token_ratio": round(title_ratio, 2),
            "first_author_found": author_ok,
            "reason": ("resolved metadata does not appear in the document — "
                       "the identifier is probably a cited work's"
                       if conf == "contradicted" else "")}


def cmd_match(args: argparse.Namespace) -> int:
    db_path = None if args.source == "api" else resolve_db_path(args.zotero_db)
    if db_path is None:
        # No desktop database (or --source api). Before conceding "unchecked",
        # try the Web API index: on a client-less machine that is the only key
        # available, and conceding here is what lets a backfill re-import the
        # whole library.
        try:
            user, key = resolve_read_credentials(args)
            idx = load_index(user, key, refresh=False)
        except SystemExit:
            idx = None
        if idx is not None:
            result = api_matches(
                idx, doi=args.doi, isbn=args.isbn, arxiv=args.arxiv,
                handle=args.handle, title=args.title, year=args.year,
                first_author=args.author,
                pdf_path=Path(args.pdf) if args.pdf else None)
            json.dump({"zotero_db": None, **result},
                      sys.stdout, indent=2, ensure_ascii=False)
            sys.stdout.write("\n")
            return 0
        json.dump({"zotero_db": None, "matches": [], "verdict": "unchecked",
                   "consulted": [],
                   "skipped": ["no Zotero database found",
                               "no Web API index (run sync-index)"]},
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
    validate_entry_keys(entries)
    body = "".join(entry_to_ris(e) for e in entries)
    out = Path(args.out)
    out.write_text(body)
    print(str(out.resolve()))
    return 0


def cmd_sync_index(args: argparse.Namespace) -> int:
    user, key = resolve_read_credentials(args)
    idx = load_index(user, key, refresh=not args.reuse)
    if idx is None:
        json.dump({"error": "index unavailable", "path": str(index_path(user))},
                  sys.stdout)
        sys.stdout.write("\n")
        return 1
    json.dump({"path": str(index_path(user)), "fetched": idx["fetched"],
               "works": len(idx["works"]), "attachments": len(idx["attachments"]),
               "attachments_with_md5":
                   sum(1 for a in idx["attachments"] if a.get("md5"))},
              sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


def _pdf_probe_text(pdf: Path) -> str:
    try:
        return pdftotext_range(pdf, 1, FIRST_PAGES)
    except Exception:
        return ""


FRONT_MATTER_LINES = 25


def _front_matter(text: str, lines: int = FRONT_MATTER_LINES) -> str:
    """The title/author block at the head of page 1, not the body.

    Matching against the whole body is what turns a title key into a false
    positive: a library title like "Systems of inequalities involving convex
    functions" is five ordinary words, every one of which appears in the body
    of any paper about linear inequalities. A real Hoffman 1960 paper matched a
    different Hoffman paper at "strong" that way. The title block is where a
    title actually lives, so that is the only place worth looking for one.
    """
    out = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return "\n".join(out[:lines])


def _filename_hints(name: str) -> tuple[list[str], str | None]:
    """Surnames and year encoded in a staging filename like 'Afriat1967-...'."""
    prefix = name.split("-")[0]
    m = re.match(r"^(.*?)((?:1[6-9]|20)\d\d)", prefix)
    head = m.group(1) if m else prefix
    year = m.group(2) if m else None
    names = [_name_key(n) for n in re.findall(r"[A-Z][a-z]+|[A-Z]{2,}", head)]
    return [n for n in names if len(n) > 2], year


def _pdf_title(pdf: Path) -> str:
    """The container's recorded Title, junk filtered out.

    pdfinfo reads container metadata, pdftotext reads the text layer; they are
    independent. Gating the first on the second throws the Title away on every
    scanned or OCR-less file — routine material in a staging folder, and
    precisely the case where the text layer has nothing else to offer.
    """
    try:
        title = pdfinfo(pdf).get("Title", "") or ""
    except Exception:
        return ""
    return "" if title.lower().endswith(".pdf") else title


def audit_one(path: Path, idx: dict[str, Any]) -> dict[str, Any]:
    """Reconcile one staged file against the library index."""
    is_pdf = path.suffix.lower() == ".pdf"
    body = _pdf_probe_text(path) if is_pdf else ""
    title = _pdf_title(path) if is_pdf else ""
    # The filename slug carries the author's own naming intent; split camelCase
    # so "MethodOfLimitsIndexNumbers" becomes words a title can match.
    slug = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ",
                  "-".join(path.stem.split("-")[1:]) or path.stem)
    surnames, year = _filename_hints(path.name)
    res = api_matches(idx, title=title, text=f"{slug} {_front_matter(body)}",
                      year=year, authors=list(surnames), pdf_path=path)
    top = res["matches"][0] if res["matches"] else None
    # Five answers, not four. Collapsing a weak hit into "absent" is the
    # expensive mistake in both directions: called present, a document is
    # skipped and its full text never lands; called absent, a duplicate item is
    # minted. A weak hit is neither finding — it is a document to look at, and
    # saying so is cheaper than any threshold tuned to hide it.
    if top and "storageHash" in top["why"]:
        verdict = "identical"
    elif top and top["certainty"] in ("exact", "strong"):
        verdict = ("work_present_with_file" if top.get("has_file")
                   else "work_present_no_file")
    elif top:
        verdict = "ambiguous"
    else:
        verdict = "absent"
    return {"file": path.name, "verdict": verdict,
            "zotero_key": top.get("key") if top else None,
            "zotero_title": top.get("title") if top else None,
            "why": top.get("why") if top else None,
            "certainty": top.get("certainty") if top else None,
            "consulted": res["consulted"], "skipped": res["skipped"]}


def cmd_audit(args: argparse.Namespace) -> int:
    """Reconcile a staging directory against the library — the count check.

    edm.md requires checking docs/ staging *and* Zotero before declaring a
    source missing or present. Doing that by hand over a few hundred files is
    where the miscounts come from; this is the mechanical form.
    """
    user, key = resolve_read_credentials(args)
    idx = load_index(user, key, refresh=args.refresh)
    if idx is None:
        json.dump({"error": "no library index; run sync-index first",
                   "verdict": "unchecked"}, sys.stdout)
        sys.stdout.write("\n")
        return 1
    root = Path(args.directory)
    if not root.is_dir():
        # Every other subcommand degrades to structured JSON and rc 1; a
        # mistyped path should not be the one that prints a traceback.
        json.dump({"error": f"not a directory: {root}", "verdict": "unchecked"},
                  sys.stdout)
        sys.stdout.write("\n")
        return 1
    pats = args.ext or [".pdf", ".html", ".htm", ".jpg", ".jpeg", ".png", ".djvu", ".epub"]
    files = sorted(p for p in root.iterdir()
                   if p.is_file() and p.suffix.lower() in pats)
    rows: list[dict[str, Any]] = []
    for p in files:
        try:
            rows.append(audit_one(p, idx))
        except Exception as exc:
            # pdfinfo and pdftotext run under a 30 s timeout and a corrupt file
            # makes them fail; losing the other 288 rows, the JSON, and --out
            # to that is the expensive outcome. A row saying so keeps the batch.
            rows.append({"file": p.name, "verdict": "error", "error": str(exc),
                         "zotero_key": None, "zotero_title": None,
                         "why": None, "certainty": None,
                         "consulted": [], "skipped": []})
    summary: dict[str, int] = {}
    for r in rows:
        summary[r["verdict"]] = summary.get(r["verdict"], 0) + 1
    actions = {"identical": "nothing",
               "work_present_with_file": "nothing; report the second copy",
               "work_present_no_file": "attach --parent <key> (never inject)",
               "ambiguous": "look: weak hit, neither present nor absent",
               "absent": "inject",
               "error": "unreadable; look at it"}
    out = {"directory": str(root.resolve()), "index_fetched": idx["fetched"],
           "library_works": len(idx["works"]),
           "library_attachments": len(idx["attachments"]),
           "files": len(files), "summary": summary,
           "actions": {k: actions[k] for k in summary if k in actions},
           "rows": rows}
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    json.dump({k: out[k] for k in
               ("directory", "index_fetched", "library_works", "files",
                "summary", "actions")},
              sys.stdout, indent=2)
    sys.stdout.write("\n")
    if not args.out:
        json.dump(rows, sys.stdout, indent=1, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


def cmd_attach(args: argparse.Namespace) -> int:
    """Upload a file onto an item that already exists — the C case of an audit.

    A work can sit in the library with correct metadata and no file attached;
    `inject` cannot fix that, because it only ever creates new items, and
    creating a second item to carry the PDF is how duplicates are born.
    """
    user, key = resolve_credentials(args)
    results = []
    rc = 0
    for f in args.file:
        p = Path(f)
        if not p.exists():
            results.append({"file": f, "error": "not found"})
            rc = 1
            continue
        try:
            att = upload_attachment(user, key, args.parent, p)
            results.append({"file": p.name, "parent": args.parent,
                            "attachmentKey": att})
        except Exception as exc:
            results.append({"file": p.name, "error": str(exc)})
            rc = 1
    json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return rc


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

    pm.add_argument("--source", choices=["auto", "api"], default="auto",
                    help="'auto' (default) prefers the desktop database and "
                         "falls back to the Web API index; 'api' forces the "
                         "index")
    pm.add_argument("--user-id", help="Zotero user id (else ZOTERO_USER_ID)")
    pm.add_argument("--api-key", help="read key (else ZOTERO_API_KEY)")

    ps = sub.add_parser("sync-index",
                        help="cache the library (works + attachment md5s) "
                             "from the Web API, for dedup without the "
                             "desktop database")
    ps.add_argument("--reuse", action="store_true",
                    help="keep a fresh cache instead of re-pulling")
    ps.add_argument("--user-id", help="Zotero user id (else ZOTERO_USER_ID)")
    ps.add_argument("--api-key", help="read key (else ZOTERO_API_KEY)")
    ps.set_defaults(func=cmd_sync_index)

    pa = sub.add_parser("audit",
                        help="reconcile a staging directory against the "
                             "library: identical / present-with-file / "
                             "present-no-file / ambiguous / absent")
    pa.add_argument("directory")
    pa.add_argument("--out", help="write the full per-file report to this path")
    pa.add_argument("--ext", nargs="*", help="extensions to audit "
                                             "(default: documents)")
    pa.add_argument("--refresh", action="store_true",
                    help="re-pull the library index first")
    pa.add_argument("--user-id", help="Zotero user id (else ZOTERO_USER_ID)")
    pa.add_argument("--api-key", help="read key (else ZOTERO_API_KEY)")
    pa.set_defaults(func=cmd_audit)

    pt = sub.add_parser("attach",
                        help="upload files onto an EXISTING item "
                             "(the present-no-file case)")
    pt.add_argument("--parent", required=True, help="parent item key")
    pt.add_argument("file", nargs="+")
    pt.add_argument("--user-id", help="Zotero user id (else ZOTERO_USER_ID)")
    pt.add_argument("--api-key", help="RW key (else ZOTERO_RW_API_KEY)")
    pt.set_defaults(func=cmd_attach)

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
    pi.add_argument("--skip-corroboration", action="store_true",
                    help="create items even when the metadata is contradicted "
                         "by the PDF's own front matter (default: refuse)")
    pi.set_defaults(func=cmd_inject)

    pe = sub.add_parser("enrich",
                        help="fill missing fields on EXISTING items "
                             "(inject creates; this completes)")
    ge = pe.add_mutually_exclusive_group(required=True)
    ge.add_argument("--item-key", help="the item to enrich")
    ge.add_argument("--jobs-file",
                    help="path to JSON: array of {item_key, expect_title, "
                         "set:{field: value}} — one API round per item")
    pe.add_argument("--expect-title",
                    help="fragment that MUST appear in the item's title; "
                         "guards against a transposed item key")
    pe.add_argument("--set", action="append", metavar="FIELD=VALUE",
                    help="field to write, repeatable. Zotero field names are "
                         "case-sensitive: DOI, url, publisher")
    pe.add_argument("--overwrite", action="store_true",
                    help="also replace fields that already hold a DIFFERENT "
                         "value; without it those are refused, not written")
    pe.add_argument("--user-id", help="Zotero user id (else ZOTERO_USER_ID)")
    pe.add_argument("--api-key", help="RW key (else ZOTERO_RW_API_KEY; "
                                      "prefer env/keys file over argv)")
    pe.add_argument("--dry-run", action="store_true",
                    help="report the planned patch, do not write")
    pe.set_defaults(func=cmd_enrich)

    args = p.parse_args()
    if args.cmd == "enrich" and args.item_key and not args.expect_title:
        p.error("--expect-title is required with --item-key")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Backend helper scripts/zotero.py for the zotero skill.

Subcommands: probe, match, dedup-report, write, inject, enrich, audit,
reconcile, attach.

Local-only and stateless. Every read opens the desktop client's zotero.sqlite
read-only, afresh, on each call; nothing is cached, indexed or logged to disk
between runs. The only write path is the Zotero desktop connector
(127.0.0.1:23119), which creates new items with their PDFs and needs Zotero
running. Existing items are never edited here: `enrich`, `attach` and
`reconcile --apply` report the edit for the author to make by hand.
"""
from __future__ import annotations

import argparse
import configparser
import contextlib
import fcntl
import hashlib
import html
import importlib.util
import io
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import uuid
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


# How long a read waits for Zotero to release its lock before falling back.
READ_BUSY_TIMEOUT = 2.0
READ_LIVE = "ro"
READ_SNAPSHOT = "immutable"


def zotero_open(db_path: Path, busy_timeout: float = READ_BUSY_TIMEOUT
                ) -> tuple[sqlite3.Connection, str]:
    """Open zotero.sqlite read-only: (connection, read mode).

    `mode=ro` first, because it is the only mode that sees the write-ahead
    log, where a running Zotero keeps its most recent writes until the next
    checkpoint. A running client holds the database under an exclusive lock,
    so that open fails after `busy_timeout`; the fallback is `immutable=1`,
    which needs no lock but reads the main file alone and can therefore lag
    the client. The mode is returned so every report can say which it got.
    Neither mode can write.
    """
    uri = Path(db_path).resolve().as_uri()
    try:
        conn = sqlite3.connect(f"{uri}?mode=ro", uri=True, timeout=busy_timeout)
        conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        return conn, READ_LIVE
    except sqlite3.OperationalError as exc:
        logging.warning("zotero.sqlite cannot be read live (%s); reading the "
                        "immutable snapshot, which can lag a running Zotero",
                        exc)
    return sqlite3.connect(f"{uri}?immutable=1", uri=True), READ_SNAPSHOT


# --- Deduplication matcher --------------------------------------------------
# Cascade, strongest key first: attachment content hash -> persistent
# identifier (DOI, ISBN, arXiv, handle) -> attachment filename ->
# (first author surname, year, normalised title) -> title Jaccard as last
# resort. The cascade stops at the first key that fires; each hit reports
# which key matched ("why") and how much to trust it ("certainty").
# Scope defaults to the user library because injection writes there:
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
    """key/title/DOI/date per item, for match reporting and title comparison."""
    if not item_ids:
        return {}
    qmarks = ",".join("?" * len(item_ids))
    rows = cur.execute(
        f"""
        SELECT i.itemID, i.key,
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
    return {iid: {"key": k, "title": t, "doi": d, "date": dt}
            for iid, k, t, d, dt in rows}


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


SAFE_TIERS = ("exact", "strong")


def top_tier_peers(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """All candidates tied with matches[0] at its certainty tier — [] when
    there are no matches or the top tier is not a safe one. The single
    definition of "several candidates tie", shared by the verdict
    (classify_matches) and the audit row (audit_one) so the two cannot
    desync (ticket 0570)."""
    if not matches or matches[0]["certainty"] not in SAFE_TIERS:
        return []
    return [m for m in matches if m["certainty"] == matches[0]["certainty"]]


def classify_matches(matches: list[dict[str, Any]]) -> str:
    """'match' when a safe key fired unambiguously; 'ambiguous' when only a
    guess-level key fired or several exact/strong candidates tie; 'none'
    otherwise. The exact tier ties like the strong one (ticket 0570): two
    records legitimately share one attachment md5 — 269 such clusters in the
    user library — and answering from matches[0] alone made the second vanish
    without a trace."""
    if not matches:
        return "none"
    # No safe tier fired → top_tier_peers is empty → "ambiguous", the same
    # answer a tie gives; only a lone safe peer is a "match".
    return "match" if len(top_tier_peers(matches)) == 1 else "ambiguous"


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
    "skipped": [...]}. The verdict is "match" (a safe key fired
    unambiguously), "ambiguous" (only a guess fired, or several exact/strong
    candidates tie — neither a silent match nor a silent skip), "none"
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
        matches.append({"itemID": iid, "key": meta.get("key"),
                        "title": meta.get("title"),
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


def duplicate_hash_report(conn: sqlite3.Connection) -> dict[str, Any]:
    """Find exact-file candidates under distinct parents in My Library.

    This is the library-to-library form of the matcher's strongest key,
    ``storageHash``. It reports candidates, never a merge decision: two
    records can deliberately carry the same file. Other bibliographic keys
    are shown as supporting evidence, not as a substitute for the hash.
    """
    library_id = resolve_library_id(conn)
    rows = conn.execute("""
        SELECT LOWER(a.storageHash), a.parentItemID, ai.key, a.path,
               a.contentType
        FROM itemAttachments a
        JOIN items ai ON ai.itemID = a.itemID
        JOIN items p ON p.itemID = a.parentItemID
        WHERE ai.libraryID = ? AND p.libraryID = ?
          AND a.storageHash IS NOT NULL AND a.storageHash != ''
          AND ai.itemID NOT IN (SELECT itemID FROM deletedItems)
          AND p.itemID NOT IN (SELECT itemID FROM deletedItems)
    """, (library_id, library_id)).fetchall()
    by_hash: dict[str, dict[int, list[dict[str, str]]]] = {}
    for digest, parent_id, attachment_key, path, content_type in rows:
        by_hash.setdefault(digest, {}).setdefault(parent_id, []).append({
            "key": attachment_key,
            "filename": _attachment_basename(path or ""),
            "content_type": content_type or "",
        })
    duplicated = {digest: parents for digest, parents in by_hash.items()
                  if len(parents) > 1}
    parent_ids = sorted({iid for parents in duplicated.values()
                         for iid in parents})
    metadata: dict[int, dict[str, str]] = {}
    # Keep the query below SQLite's older 999-parameter default.
    for start in range(0, len(parent_ids), 400):
        ids = parent_ids[start:start + 400]
        marks = ",".join("?" for _ in ids)
        for iid, key, item_type, title, doi, isbn, date, surname in conn.execute(
            f"""SELECT i.itemID, i.key, t.typeName,
                       MAX(CASE WHEN f.fieldName='title' THEN v.value END),
                       MAX(CASE WHEN f.fieldName='DOI' THEN v.value END),
                       MAX(CASE WHEN f.fieldName='ISBN' THEN v.value END),
                       MAX(CASE WHEN f.fieldName='date' THEN v.value END),
                       (SELECT c.lastName FROM itemCreators ic
                        JOIN creators c ON c.creatorID=ic.creatorID
                        WHERE ic.itemID=i.itemID AND ic.orderIndex=0 LIMIT 1)
                FROM items i JOIN itemTypes t ON t.itemTypeID=i.itemTypeID
                LEFT JOIN itemData d ON d.itemID=i.itemID
                LEFT JOIN fields f ON f.fieldID=d.fieldID
                LEFT JOIN itemDataValues v ON v.valueID=d.valueID
                WHERE i.itemID IN ({marks}) GROUP BY i.itemID""", ids):
            metadata[iid] = {
                "key": key, "item_type": item_type,
                "title": title or "", "doi": doi or "",
                "isbn": isbn or "", "date": date or "",
                "first_author": surname or "",
            }

    def signals(left: dict[str, str], right: dict[str, str]) -> list[str]:
        found = []
        if left["item_type"] != right["item_type"]:
            return found
        if left["doi"] and left["doi"].casefold() == right["doi"].casefold():
            found.append("doi")
        left_isbn = re.sub(r"[^0-9Xx]", "", left["isbn"]).upper()
        right_isbn = re.sub(r"[^0-9Xx]", "", right["isbn"]).upper()
        if left_isbn and left_isbn == right_isbn:
            found.append("isbn")
        if left["title"] and _norm_title(left["title"]) == _norm_title(right["title"]):
            found.append("title")
        return found

    clusters = []
    for digest, parents in sorted(duplicated.items()):
        items = []
        for iid in sorted(parents):
            meta = metadata[iid]
            items.append({**meta, "attachments": parents[iid],
                          "url": f"zotero://select/library/items/{meta['key']}"})
        overlap = []
        for pos, left in enumerate(items):
            for right in items[pos + 1:]:
                shared = signals(left, right)
                if shared:
                    overlap.append({"items": [left["key"], right["key"]],
                                    "keys": shared})
        clusters.append({"hash": digest, "matched_by": "storageHash",
                         "items": items, "bibliographic_overlap": overlap})
    return {"library_id": library_id,
            "hashed_attachments_scanned": len(rows),
            "candidate_clusters": len(clusters),
            "clusters": clusters}


def duplicate_hash_html(report: dict[str, Any]) -> str:
    """Local, reviewable candidate list; all library strings are escaped."""
    esc = html.escape
    lines = ["<!doctype html>", '<html lang="en"><meta charset="utf-8">',
             "<title>Zotero duplicate-file candidates</title>",
             "<h1>Zotero duplicate-file candidates</h1>",
             (f"<p>{report['candidate_clusters']} hash group(s) in My Library; "
              f"{report['hashed_attachments_scanned']} hashed attachments scanned "
              f"(read mode: {esc(str(report.get('read_mode')))}). "
              "These are candidates, not merge instructions.</p>"),
             ("<p>The match key is the attachment content hash. Additional "
              "bibliographic matches below are hints, not a claim that "
              "Zotero's Duplicates pane displayed the group.</p>")]
    for number, cluster in enumerate(report["clusters"], 1):
        lines.append(f"<section><h2>{number}. hash {esc(cluster['hash'])}</h2><ul>")
        for item in cluster["items"]:
            title = item["title"] or "(untitled)"
            details = ", ".join(x for x in (item["item_type"], item["date"],
                                            item["doi"]) if x)
            lines.append(
                f'<li><a href="{esc(item["url"], quote=True)}">'
                f'{esc(title)}</a> — {esc(details)}<ul>')
            for attachment in item["attachments"]:
                attachment_url = ("zotero://select/library/items/"
                                  + attachment["key"])
                filename = attachment["filename"] or attachment["key"]
                lines.append(
                    f'<li><a href="{esc(attachment_url, quote=True)}">'
                    f'{esc(filename)}</a></li>')
            lines.append("</ul></li>")
        lines.append("</ul>")
        if cluster["bibliographic_overlap"]:
            hints = "; ".join(
                f"{esc(', '.join(pair['keys']))} ({esc(' / '.join(pair['items']))})"
                for pair in cluster["bibliographic_overlap"])
            lines.append(f"<p>Additional bibliographic matches: {hints}</p>")
        lines.append("</section>")
    lines.append("</html>")
    return "\n".join(lines) + "\n"


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


# --- Zotero item JSON --------------------------------------------------------
# `inject` hands Zotero item JSON to the desktop connector, which saves it as
# a translator result would be saved. `write` stays as artifact and fallback.

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
# and a field the type does not own is refused or dropped on save
# (`'numPages' is not a valid field for type 'report'`), so a mapper that
# emits `publisher`/`volume`/`seriesTitle` unconditionally cannot import a
# report, a thesis or a manuscript at all.
#
# The two tables below are a reduced snapshot of Zotero's item-type schema
# (schema version 42, consulted 2026-08-14): the eight slots this mapper emits
# across the ten types RIS_TO_ZOTERO_TYPE can produce. An explicit table
# rather than a vendored copy of the schema — 40 readable lines a reviewer can
# check against the diff, where the schema is 385 KB of JSON that is 95%
# irrelevant here and unreviewable in a merge request. The drift check lives
# in the test suite's `slow` tier, which re-derives both tables from the
# `itemTypeFields` table of the local zotero.sqlite.

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

# Every key an entry may carry, across both the RIS and the connector path. An
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


def entry_to_zotero_item(e: dict[str, Any]) -> dict[str, Any]:
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
    return item


def plan_enrichment(data: dict[str, Any], sets: dict[str, str],
                    expect_title: str,
                    overwrite: bool = False) -> tuple[dict[str, str], list[str]]:
    """Decide which edits to suggest on an existing item. Pure: no I/O.

    Returns (fields to change, refusals). A refusal is a reason NOT to suggest
    a given field; the caller reports every one of them and suggests the rest.
    Nothing here writes: the author applies the suggestion in the client.

    Three guards, in the order they catch real mistakes:

    1. Wrong item. `expect_title` must appear in the item's title. Item keys
       are opaque, so a transposed key silently points the author at an
       unrelated work. An empty title on the target is a refusal, not a
       pass: "could not check" is not "clear".
    2. Already correct. A field whose stored value equals the requested one is
       dropped, not suggested — there is nothing to do.
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


# --- Zotero desktop connector -----------------------------------------------
# The only write path. The connector is the HTTP server the desktop client
# runs for the browser extension; it saves new items (saveItems), attaches a
# file to an item saved in the same session (saveAttachment) and moves the
# session's items to a library or collection (updateSession). It cannot edit
# an item that existed before the session, and it returns no item keys.
# Protocol: chrome/content/zotero/xpcom/server/server_connector.js and
# saveSession.js in the Zotero 7 source.

CONNECTOR_URL = os.environ.get("ZOTERO_CONNECTOR_URL", "http://127.0.0.1:23119")
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
CONNECTOR_API_VERSION = "3"
CONNECTOR_TIMEOUT = 60.0
CONNECTOR_UPLOAD_TIMEOUT = 300.0


class ConnectorUnavailable(RuntimeError):
    """The desktop connector did not answer: Zotero is not running."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        return None


# No proxy, no redirect: a loopback URL must stay on the loopback, whatever
# http_proxy says and whatever the listener answers.
def connector_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                       _NoRedirect())


_CONNECTOR_OPENER = connector_opener()


def connector_base() -> str:
    """The connector URL, refused unless it is on this machine.

    The override exists for tests; a remote host would send item metadata
    and PDFs off the machine, which a local-only helper must not do.
    """
    host = urllib.parse.urlsplit(CONNECTOR_URL).hostname
    if host not in LOOPBACK_HOSTS:
        raise ConnectorUnavailable(f"refusing non-local connector URL "
                                   f"{CONNECTOR_URL}: the helper is local-only")
    return CONNECTOR_URL


def connector_post(endpoint: str, payload: dict[str, Any] | bytes, *,
                   headers: dict[str, str] | None = None,
                   timeout: float = CONNECTOR_TIMEOUT) -> tuple[int, bytes]:
    """POST to one connector endpoint; (status, body). Raises on transport."""
    if isinstance(payload, bytes):
        body = payload
        content_type = "application/octet-stream"
    else:
        body = json.dumps(payload).encode()
        content_type = "application/json"
    req = urllib.request.Request(f"{connector_base()}/connector/{endpoint}",
                                 data=body, method="POST")
    req.add_header("Content-Type", content_type)
    req.add_header("X-Zotero-Connector-API-Version", CONNECTOR_API_VERSION)
    for name, value in (headers or {}).items():
        req.add_header(name, value)
    try:
        with _CONNECTOR_OPENER.open(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read() or b""


def connector_ping(timeout: float = 5.0) -> None:
    """Fail loudly unless the desktop connector answers."""
    base = connector_base()
    try:
        with _CONNECTOR_OPENER.open(f"{base}/connector/ping",
                                    timeout=timeout) as resp:
            if resp.status == 200:
                return
            status = resp.status
    except urllib.error.HTTPError as exc:
        status = exc.code
    except (urllib.error.URLError, OSError) as exc:
        raise ConnectorUnavailable(
            f"Zotero is not running: no answer from the desktop connector at "
            f"{CONNECTOR_URL} ({exc}). Start Zotero and retry.") from exc
    raise ConnectorUnavailable(
        f"something answers at {CONNECTOR_URL} but not as the Zotero "
        f"connector (HTTP {status}); check that it is Zotero and retry")


def connector_save(item: dict[str, Any], pdf: Path | None,
                   target: str | None) -> dict[str, Any]:
    """Create one item (and its PDF) in one connector session.

    Each item gets its own session, so a failure is confined to one entry.
    The item lands in the collection selected in the desktop UI and is then
    moved to `target` ("L<libraryID>" or "C<collectionID>") before the PDF is
    attached, so the file is stored once, where the item ends up.
    """
    session = uuid.uuid4().hex
    status, body = connector_post("saveItems", {
        "sessionID": session,
        "uri": pdf.resolve().as_uri() if pdf else "",
        "items": [{**item, "id": "item0", "attachments": [], "notes": [],
                   "tags": []}],
    })
    if status != 201:
        raise RuntimeError(f"saveItems answered HTTP {status}: "
                           f"{body.decode('utf-8', 'replace')[:200]}")
    row: dict[str, Any] = {"session": session, "status": "created"}
    if target:
        status, body = connector_post("updateSession", {
            "sessionID": session, "target": target, "tags": []})
        if status != 200:
            row["target_error"] = (f"updateSession answered HTTP {status}: "
                                   f"{body.decode('utf-8', 'replace')[:200]}")
            return row
    if pdf is not None:
        metadata = {"sessionID": session, "parentItemID": "item0",
                    "title": pdf.name, "url": pdf.resolve().as_uri()}
        status, body = connector_post(
            "saveAttachment", pdf.read_bytes(),
            headers={"X-Metadata": json.dumps(metadata),
                     "Content-Type": "application/pdf"},
            timeout=CONNECTOR_UPLOAD_TIMEOUT)
        if status != 201:
            row["attachment_error"] = (
                f"saveAttachment answered HTTP {status}: "
                f"{body.decode('utf-8', 'replace')[:200]}")
        else:
            row["attachment"] = pdf.name
    return row


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


def entry_identity_keys(entry: dict[str, Any]) -> set[tuple[str, str]]:
    """Keys that can reveal two input rows describe one work before POST."""
    keys: set[tuple[str, str]] = set()
    if doi := str(entry.get("doi") or "").strip():
        doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", doi,
                     flags=re.IGNORECASE).strip().lower()
        keys.add(("doi", doi))
    if isbn := _isbn_key(str(entry.get("isbn") or "")):
        keys.add(("isbn", isbn))
    url = str(entry.get("url") or "")
    if match := ARXIV_ANY_RE.search(url):
        keys.add(("arxiv", match.group(1).lower()))
    if match := HDL_ANY_RE.search(url):
        keys.add(("handle", match.group(1).lower().rstrip("/")))
    authors = entry.get("authors") or []
    author = first_author_surname(str(authors[0])) if authors else ""
    year_match = YEAR_RE.search(str(entry.get("year") or ""))
    title = _norm_title(str(entry.get("title") or ""))
    if author and year_match and title:
        keys.add(("author_year_title", f"{_name_key(author)}|"
                                        f"{year_match.group()}|{title}"))
    return keys


def resolve_target(conn: sqlite3.Connection, library: int | str,
                   collection: str | None) -> tuple[str, int]:
    """(connector target, libraryID) for new items.

    A collection key names its own library; otherwise the library selector
    does, the user library by default. "all" names no single destination.
    """
    if collection:
        row = conn.execute("SELECT collectionID, libraryID FROM collections "
                           "WHERE key = ?", (collection,)).fetchone()
        if row is None:
            raise ValueError(f"collection {collection!r} is not in zotero.sqlite")
        return f"C{row[0]}", row[1]
    lib_id = resolve_library_id(conn, library)
    if lib_id is None:
        raise ValueError("--library all names no single destination library")
    return f"L{lib_id}", lib_id


SNAPSHOT_WARNING = (
    "zotero.sqlite was read as an immutable snapshot because Zotero holds it "
    "locked; items saved since its last checkpoint are invisible to the "
    "duplicate guard. Check Zotero's Duplicate Items pane after the import.")


def load_entries(args: argparse.Namespace) -> list[dict[str, Any]]:
    """Entries from --entries-json, --entries-file or stdin; keys validated."""
    if args.entries_json:
        entries = json.loads(args.entries_json)
    elif args.entries_file:
        entries = json.loads(Path(args.entries_file).read_text())
    else:
        entries = json.loads(sys.stdin.read())
    if isinstance(entries, dict):
        entries = [entries]
    validate_entry_keys(entries)
    return entries


def emit_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def cmd_inject(args: argparse.Namespace) -> int:
    entries = load_entries(args)
    checks = [corroborate_entry(e) for e in entries]
    if not args.skip_corroboration:
        blocked = [(e, c) for e, c in zip(entries, checks)
                   if c["confidence"] == "contradicted"]
        if blocked:
            emit_json({"error": "metadata contradicted by the document",
                       "hint": "the identifier a resolver followed is probably "
                               "a cited work's, not this document's; rebuild "
                               "the metadata, or pass --skip-corroboration",
                       "entries": [{"title": e.get("title"),
                                    "pdf": e.get("pdf"), **c}
                                   for e, c in blocked]})
            return 1

    items = [entry_to_zotero_item(e) for e in entries]
    if args.dry_run:
        emit_json({"items": items, "corroboration": checks})
        return 0

    db_path = resolve_db_path(getattr(args, "zotero_db", None))
    if db_path is None:
        emit_json({"error": "no local Zotero database: the duplicate guard and "
                            "the destination both read zotero.sqlite"})
        return 1
    try:
        connector_ping()
    except ConnectorUnavailable as exc:
        print(f"inject: {exc}", file=sys.stderr)
        emit_json({"error": str(exc)})
        return 1

    held = getattr(args, "_snapshot", None)
    library = getattr(args, "library", USER_LIBRARY)
    collection = getattr(args, "collection", None)
    # Reconcile reads its snapshot under this same lock and hands it over;
    # a CLI inject takes the lock itself. Either way the duplicate check and
    # the saves happen inside one critical section per Zotero data directory.
    lock = (contextlib.nullcontext() if held is not None
            else directory_locks([db_path.parent]))
    with lock:
        conn, mode = zotero_open(db_path)
        try:
            target, lib_id = resolve_target(conn, library, collection)
            snapshot = (held if held is not None
                        else {**read_library(conn, lib_id), "read_mode": mode})
            if snapshot.get("library_id") != lib_id:
                raise ValueError(f"the duplicate guard read library "
                                 f"{snapshot.get('library_id')}, not the "
                                 f"destination {lib_id}")
        except (ValueError, sqlite3.Error) as exc:
            emit_json({"error": str(exc), "read_mode": mode})
            return 1
        finally:
            conn.close()
        results, status = inject_entries(entries, items, checks, snapshot,
                                         target, getattr(args, "force", False))
    out: dict[str, Any] = {"library": target, "zotero_db": str(db_path),
                           "read_mode": snapshot.get("read_mode"),
                           "results": results}
    if snapshot.get("read_mode") == READ_SNAPSHOT:
        out["warning"] = SNAPSHOT_WARNING
    emit_json(out)
    return status


def inject_entries(entries: list[dict[str, Any]], items: list[dict[str, Any]],
                   checks: list[dict[str, Any]], snapshot: dict[str, Any],
                   target: str, force: bool) -> tuple[list[dict[str, Any]], int]:
    """Guard each entry against the library and the batch, then save it."""
    results: list[dict[str, Any]] = [
        {"title": entry.get("title"), "corroboration": check["confidence"]}
        for entry, check in zip(entries, checks)]
    status = 0
    pending: list[tuple[int, dict[str, Any], str | None]] = []
    for n, entry in enumerate(entries):
        row = results[n]
        pdf = Path(entry["pdf"]) if entry.get("pdf") else None
        if not force and (pdf is None or not pdf.is_file()):
            row["error"] = "no readable PDF for duplicate guard; use --force"
            status = 1
            continue
        if not force:
            author = (entry.get("authors") or [""])[0]
            url = str(entry.get("url") or "")
            arxiv_match = ARXIV_ANY_RE.search(url)
            handle_match = HDL_ANY_RE.search(url)
            match = library_matches(snapshot, pdf_path=pdf,
                                    title=entry.get("title"),
                                    doi=entry.get("doi"), isbn=entry.get("isbn"),
                                    arxiv=(arxiv_match.group(1)
                                           if arxiv_match else None),
                                    handle=(handle_match.group(1)
                                            if handle_match else None),
                                    year=str(entry.get("year") or ""),
                                    first_author=first_author_surname(author))
            if match["matches"]:
                row["error"] = "duplicate or ambiguous library match"
                row["matches"] = match["matches"][:5]
                status = 1
                continue
        digest = file_md5(pdf) if pdf and pdf.is_file() else None
        pending.append((n, entry, digest))

    if not force:
        owners: dict[tuple[str, str], list[int]] = {}
        for n, entry, digest in pending:
            keys = entry_identity_keys(entry)
            if digest:
                keys.add(("md5", digest))
            if len(keys) == 1 and ("md5", digest) in keys:
                results[n]["error"] = ("insufficient work identity for "
                                       "duplicate guard; use --force")
                status = 1
            for identity in keys:
                owners.setdefault(identity, []).append(n)
        collisions = {n for ns in owners.values() if len(ns) > 1 for n in ns}
        for n in collisions:
            results[n]["error"] = "same work appears more than once in input"
            status = 1
        pending = [(n, entry, digest) for n, entry, digest in pending
                   if "error" not in results[n]]

    for pos, (n, entry, _digest) in enumerate(pending):
        pdf = (Path(entry["pdf"]) if entry.get("attach_pdf") and entry.get("pdf")
               else None)
        try:
            results[n].update(connector_save(items[n], pdf, target))
        except (urllib.error.URLError, OSError, RuntimeError) as exc:
            # A save that failed in transit may still have reached Zotero.
            # Stop here. The next run reads the library again, but while
            # Zotero runs that read can lag, so the item may not show yet.
            results[n]["error"] = f"create outcome unknown: {exc}"
            for m, _, _ in pending[pos + 1:]:
                results[m]["error"] = "not attempted after an uncertain save"
            status = 1
            break
        if results[n].get("attachment_error") or results[n].get("target_error"):
            status = 1
    return results, status


def parse_set(pairs: list[str]) -> dict[str, str]:
    """`--set DOI=10.x/y` pairs into a dict. Splits on the FIRST `=` only."""
    out: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"--set expects FIELD=VALUE, got {pair!r}")
        field, value = pair.split("=", 1)
        out[field.strip()] = value.strip()
    return out


def item_data(conn: sqlite3.Connection, item_key: str,
              library: int | str = USER_LIBRARY) -> dict[str, Any] | None:
    """An item's fields as Zotero names them, read from zotero.sqlite.

    Every field the item type owns is present, empty when unset, so
    plan_enrichment can tell "empty" from "this type has no such field".
    """
    lib_id = resolve_library_id(conn, library)
    sql = ("SELECT i.itemID, i.key, i.itemTypeID, t.typeName FROM items i "
           "JOIN itemTypes t ON t.itemTypeID = i.itemTypeID "
           f"WHERE i.key = ? AND i.{_NOT_DELETED}")
    params: list[Any] = [item_key]
    if lib_id is not None:
        sql += " AND i.libraryID = ?"
        params.append(lib_id)
    row = conn.execute(sql, params).fetchone()
    if row is None:
        return None
    item_id, key, type_id, type_name = row
    data: dict[str, Any] = {name: "" for (name,) in conn.execute(
        "SELECT f.fieldName FROM itemTypeFields t "
        "JOIN fields f ON f.fieldID = t.fieldID WHERE t.itemTypeID = ?",
        (type_id,))}
    data.update(dict(conn.execute(
        "SELECT f.fieldName, v.value FROM itemData d "
        "JOIN fields f ON f.fieldID = d.fieldID "
        "JOIN itemDataValues v ON v.valueID = d.valueID WHERE d.itemID = ?",
        (item_id,))))
    data.update({"key": key, "itemType": type_name})
    return data


def enrich_one(conn: sqlite3.Connection, job: dict[str, Any],
               overwrite: bool, library: int | str = USER_LIBRARY
               ) -> dict[str, Any]:
    """Suggest field edits on ONE existing item. See plan_enrichment."""
    item_key = job["item_key"]
    row: dict[str, Any] = {"itemKey": item_key}
    data = item_data(conn, item_key, library)
    if data is None:
        row["status"] = "not found"
        return row
    row["title"] = data.get("title")
    patch, refusals = plan_enrichment(data, job["set"], job["expect_title"],
                                      overwrite)
    if refusals:
        row["refused"] = refusals
    row["suggested"] = [{"itemKey": item_key, "field": field,
                         "old": data.get(field) or "", "new": value}
                        for field, value in patch.items()]
    row["status"] = "suggested" if patch else "nothing to change"
    return row


def cmd_enrich(args: argparse.Namespace) -> int:
    """Report the edits for the author to apply by hand; never write."""
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
        if not isinstance(job["expect_title"], str) or not job["expect_title"]:
            raise SystemExit(f"job for {job['item_key']} has no expect_title")

    db_path = resolve_db_path(args.zotero_db)
    if db_path is None:
        raise SystemExit("enrich: no local Zotero database found")
    conn, mode = zotero_open(db_path)
    try:
        results = [enrich_one(conn, j, args.overwrite, args.library)
                   for j in jobs]
    finally:
        conn.close()
    emit_json({"zotero_db": str(db_path), "read_mode": mode,
               "apply": "by hand in Zotero: open each item and set the field",
               "results": results})
    return enrich_status(results)


def enrich_status(results: list[dict[str, Any]]) -> int:
    """Exit code for an enrich run. Non-zero when anything asked for cannot
    be suggested — a refusal or a missing item included. A run that refused
    every field and one that suggested every field must not return the same
    code, or the caller cannot tell "ready" from "declined to act".
    """
    ok = {"suggested", "nothing to change"}
    return int(any(row.get("refused") or row.get("status") not in ok
                   for row in results))


# --- CLI -------------------------------------------------------------------

def resolve_db_path(override: str | None) -> Path | None:
    if override:
        p = Path(override)
        return p if p.exists() else None
    return find_zotero_db()


def cmd_probe(args: argparse.Namespace) -> int:
    db_path = resolve_db_path(args.zotero_db)
    conn, mode = zotero_open(db_path) if db_path else (None, None)
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
    if conn is not None:
        conn.close()
    payload = {
        "zotero_db": str(db_path) if db_path else None,
        "zotero_lookup": db_path is not None,
        "read_mode": mode,
        "items": out,
    }
    json.dump(payload, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# Library snapshot — the whole library in memory, read from zotero.sqlite
#
# `audit`, `reconcile` and `inject` compare many files against the library.
# One read of the works and attachments, held in memory for the run and then
# dropped, serves them all; nothing is written to disk, so there is no cache
# to go stale and nothing to rebuild.
#
# Each attachment carries its storageHash, the md5 of the stored file. It is
# the strongest key available: content identity survives renaming, re-filing
# and metadata drift, and it answers the only question a staging directory
# really asks — is this exact file already stored in Zotero?
# ---------------------------------------------------------------------------

# Titles shorter than this carry too few distinctive tokens to match on.
TITLE_MIN_TOKENS = 3
LINK_MODES = {0: "imported_file", 1: "imported_url", 2: "linked_file",
              3: "linked_url", 4: "embedded_image"}
WORK_FIELDS = ("title", "date", "DOI", "ISBN", "url", "extra")


def read_library(conn: sqlite3.Connection,
                 library: int | str = USER_LIBRARY) -> dict[str, Any]:
    """Works and attachments of one library (or all), not deleted."""
    lib_id = resolve_library_id(conn, library)
    lib_clause = "" if lib_id is None else " AND i.libraryID = ?"
    lib_params: list[Any] = [] if lib_id is None else [lib_id]
    works: dict[int, dict[str, Any]] = {}
    for item_id, key, type_name in conn.execute(
            "SELECT i.itemID, i.key, t.typeName FROM items i "
            "JOIN itemTypes t ON t.itemTypeID = i.itemTypeID "
            f"WHERE i.{_NOT_DELETED}" + lib_clause
            + " AND t.typeName NOT IN ('attachment', 'note', 'annotation')",
            lib_params):
        works[item_id] = {"key": key, "itemType": type_name, "creators": [],
                          **{f: "" for f in WORK_FIELDS}}
    marks = ",".join("?" * len(WORK_FIELDS))
    for item_id, field, value in conn.execute(
            "SELECT d.itemID, f.fieldName, v.value FROM itemData d "
            "JOIN fields f ON f.fieldID = d.fieldID "
            "JOIN itemDataValues v ON v.valueID = d.valueID "
            f"WHERE f.fieldName IN ({marks})", WORK_FIELDS):
        if item_id in works:
            works[item_id][field] = value or ""
    for item_id, last in conn.execute(
            "SELECT ic.itemID, c.lastName FROM itemCreators ic "
            "JOIN creators c ON c.creatorID = ic.creatorID "
            "ORDER BY ic.itemID, ic.orderIndex"):
        if item_id in works and last:
            works[item_id]["creators"].append(last)
    attachments = []
    for key, parent, path, digest, content_type, link_mode in conn.execute(
            "SELECT ai.key, p.key, a.path, a.storageHash, a.contentType, "
            "a.linkMode FROM itemAttachments a "
            "JOIN items ai ON ai.itemID = a.itemID "
            "LEFT JOIN items p ON p.itemID = a.parentItemID "
            f"WHERE a.{_NOT_DELETED}"
            + ("" if lib_id is None else " AND ai.libraryID = ?"), lib_params):
        attachments.append({
            "key": key, "parent": parent,
            "filename": _attachment_basename(path or ""),
            "md5": (digest or "").lower() or None,
            "contentType": content_type or "",
            "linkMode": LINK_MODES.get(link_mode, str(link_mode)),
        })
    return {"works": list(works.values()), "attachments": attachments,
            "library_id": lib_id}


def library_snapshot(db_path: Path | None,
                     library: int | str = USER_LIBRARY) -> dict[str, Any] | None:
    """Read the library once for this run; None when there is no database."""
    if db_path is None:
        return None
    conn, mode = zotero_open(db_path)
    try:
        lib = read_library(conn, library)
        account = local_account(conn)
    finally:
        conn.close()
    return {**lib, "zotero_db": str(db_path), "read_mode": mode,
            "account": account}


def local_account(conn: sqlite3.Connection) -> str | None:
    """The Zotero user id the desktop client is signed in as, if any."""
    try:
        row = conn.execute("SELECT value FROM settings WHERE setting = "
                           "'account' AND key = 'userID'").fetchone()
    except sqlite3.OperationalError:
        return None
    return str(row[0]) if row and row[0] is not None else None


def file_md5(path: Path, chunk: int = 1 << 20) -> str:
    """Content hash, read in chunks — an audit hashes every staged file, and
    this corpus holds a 62 MB Internet Archive scan."""
    h = hashlib.md5()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


@contextlib.contextmanager
def directory_locks(directories: list[Path]):
    """One advisory flock per directory, in stable order.

    The lock is taken on the directory itself, so it leaves no file behind
    and dies with the process.
    """
    with contextlib.ExitStack() as stack:
        for directory in sorted({Path(d).resolve() for d in directories}):
            if not directory.is_dir():
                continue
            fd = os.open(directory, os.O_RDONLY)
            stack.callback(os.close, fd)
            fcntl.flock(fd, fcntl.LOCK_EX)
            stack.callback(fcntl.flock, fd, fcntl.LOCK_UN)
        yield


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


def _library_views(idx: dict[str, Any]) -> dict[str, Any]:
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


def library_matches(idx: dict[str, Any], *, doi: str | None = None,
                isbn: str | None = None, arxiv: str | None = None,
                handle: str | None = None,
                title: str | None = None, year: str | None = None,
                first_author: str | None = None,
                authors: list[str] | None = None,
                text: str | None = None,
                pdf_path: Path | None = None) -> dict[str, Any]:
    """Same cascade and output contract as zotero_matches(), over a snapshot.

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
    v = _library_views(idx)
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
        digest = file_md5(pdf_path)
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
            "source": "zotero.sqlite", "read_mode": idx.get("read_mode")}


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
    db_path = resolve_db_path(args.zotero_db)
    if db_path is None:
        emit_json({"zotero_db": None, "matches": [], "verdict": "unchecked",
                   "consulted": [], "skipped": ["no Zotero database found"]})
        return 0
    conn, mode = zotero_open(db_path)
    try:
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
    finally:
        conn.close()
    emit_json({"zotero_db": str(db_path), "read_mode": mode, **result})
    return 0


def cmd_dedup_report(args: argparse.Namespace) -> int:
    """Report existing-library duplicate-file candidates without Zotero writes."""
    db_path = resolve_db_path(args.zotero_db)
    if db_path is None:
        raise SystemExit("dedup-report: no local Zotero database found")
    conn, mode = zotero_open(db_path)
    wal = Path(str(db_path) + "-wal")
    if mode == READ_SNAPSHOT and wal.exists() and wal.stat().st_size:
        # The live read failed, so the WAL is unreadable to us and may hold
        # writes the snapshot misses: refuse rather than report on a lag.
        conn.close()
        raise SystemExit("dedup-report: Zotero holds the database locked with "
                         "pending WAL writes; close Zotero and retry")
    try:
        conn.execute("PRAGMA query_only=ON")
        report = {**duplicate_hash_report(conn), "read_mode": mode}
    finally:
        conn.close()
    if not report["hashed_attachments_scanned"]:
        raise SystemExit("dedup-report: no hashed attachments inspected; "
                         "cannot call this an empty library")
    body = (json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            if args.format == "json" else duplicate_hash_html(report))
    if args.out:
        output = Path(args.out)
        guarded = [Path(f"{db_path}{suffix}")
                   for suffix in ("", "-wal", "-shm", "-journal")]
        if output.exists() and any(g.exists() and os.path.samefile(output, g)
                                   for g in guarded):
            # samefile also catches a symlink or a hard link to the database.
            raise SystemExit("dedup-report: --out names the Zotero database")
        fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(body)
        print(f"dedup-report: {report['candidate_clusters']} candidate groups "
              f"written to {args.out}")
    else:
        sys.stdout.write(body)
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    entries = load_entries(args)
    body = "".join(entry_to_ris(e) for e in entries)
    out = Path(args.out)
    out.write_text(body)
    print(str(out.resolve()))
    return 0


def _pdf_probe_text(pdf: Path) -> str:
    try:
        return pdftotext_range(pdf, 1, FIRST_PAGES)
    except Exception:
        return ""


FRONT_MATTER_LINES = 25
STAGING_EXTENSIONS = frozenset(
    {".pdf", ".html", ".htm", ".jpg", ".jpeg", ".png", ".djvu", ".epub"}
)


def _bib_entries(path: Path) -> list[dict[str, Any]]:
    """Reuse the harness BibTeX parser rather than parsing `file=` with regex."""
    parser = Path(__file__).with_name("bib-merge.py")
    spec = importlib.util.spec_from_file_location("zotero_bib_merge", parser)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load BibTeX parser: {parser}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    content = path.read_text(encoding="utf-8")
    # bib-merge intentionally tolerates a malformed tail so an editor can
    # salvage valid earlier entries. A reconciliation sweep must fail closed:
    # the skipped tail might contain the only staged file needing import.
    pos = 0
    while match := module._ENTRY_START.search(content, pos):
        close = module._balance_scan(content, match.end() - 1)
        if close < 0:
            raise ValueError(f"unclosed BibTeX entry near byte {match.start()}")
        if match.group(1).lower() not in {"string", "preamble", "comment"}:
            body = content[match.end():close]
            comma = body.find(",")
            if comma >= 0:
                for field in module._split_top_level_commas(body[comma + 1:]):
                    if field.strip() and "=" not in field:
                        raise ValueError(f"malformed BibTeX field near byte "
                                         f"{match.start()}: {field.strip()[:40]}")
        pos = close + 1
    return module.parse_bibtex(content)


def _bib_file_values(value: str) -> list[str]:
    """Split the usual path and Better BibTeX `:path:TYPE` forms."""
    paths = []
    for part in value.split(";"):
        part = part.strip()
        if part.startswith(":"):
            part = part[1:]
        if ":" in part and part.rsplit(":", 1)[1].lower() in {
            "pdf", "html", "htm", "jpg", "jpeg", "png", "djvu", "epub"
        }:
            part = part.rsplit(":", 1)[0]
        if part:
            paths.append(part)
    return paths


def discover_reconcile_files(root: Path) -> dict[str, Any]:
    """Find BibTeX-linked staging files and orphans without touching Zotero.

    A BibTeX file may sit at the repository root or one directory below it.
    Only paths within the repository are scanned. If BibTeX exists but carries
    no usable staging path, report that uncertainty instead of defaulting to
    `docs/` and pretending the sweep looked everywhere.
    """
    root = root.resolve()
    bib_files = sorted(set(root.glob("*.bib")) | set(root.glob("*/*.bib")))
    linked: list[dict[str, Any]] = []
    linked_paths: set[Path] = set()
    staging_dirs: set[Path] = set()
    errors: list[str] = []
    for bib in bib_files:
        if not bib.resolve().is_relative_to(root):
            errors.append(f"BibTeX file outside repository: {bib.relative_to(root)}")
            continue
        try:
            entries = _bib_entries(bib)
        except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
            errors.append(f"cannot read {bib.relative_to(root)}: {exc}")
            continue
        for entry in entries:
            for raw in _bib_file_values(str(entry.get("file", ""))):
                candidate = Path(raw).expanduser()
                paths = ([candidate] if candidate.is_absolute() else
                         [root / candidate, bib.parent / candidate])
                resolved = next((p.resolve() for p in paths if p.is_file()),
                                paths[0].resolve())
                if not resolved.is_relative_to(root):
                    errors.append(f"file path outside repository: {bib.relative_to(root)} "
                                  f"entry {entry.get('_key', '?')}")
                    continue
                relative = resolved.relative_to(root)
                if len(relative.parts) < 2:
                    errors.append(f"cannot infer staging root from root-level "
                                  f"file: {relative}")
                else:
                    staging_dirs.add(root / relative.parts[0])
                if not resolved.is_file():
                    errors.append(f"missing file: {resolved.relative_to(root)} "
                                  f"in {bib.relative_to(root)}")
                    continue
                if resolved in linked_paths:
                    errors.append(f"multiple BibTeX entries reference "
                                  f"{resolved.relative_to(root)}")
                    continue
                linked.append({"path": resolved, "bib": bib,
                               "key": entry.get("_key", ""), "entry": entry})
                linked_paths.add(resolved)
    if not bib_files:
        staging_dirs.add(root / "docs")
    elif not staging_dirs:
        errors.append("BibTeX files found but no staging directory could be inferred")
    orphans: list[Path] = []
    for directory in sorted(staging_dirs):
        if not directory.is_dir():
            continue
        if not directory.resolve().is_relative_to(root):
            errors.append(f"staging directory outside repository: {directory}")
            continue
        for path in sorted(directory.rglob("*")):
            if path.is_symlink() and (path.is_dir() or not path.is_file()):
                errors.append(f"cannot scan symlinked staging directory: {path}")
                continue
            if not path.is_file() or path.suffix.lower() not in STAGING_EXTENSIONS:
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                errors.append(f"staged file outside repository: {path}")
            elif resolved not in linked_paths:
                orphans.append(resolved)
    return {"bib_files": bib_files, "linked": linked,
            "orphans": sorted(set(orphans)), "errors": errors,
            "staging_dirs": sorted(staging_dirs)}


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


def audit_one(path: Path, idx: dict[str, Any],
              bib_entry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Reconcile one staged file against the library snapshot."""
    bib_entry = bib_entry or {}
    is_pdf = path.suffix.lower() == ".pdf"
    body = _pdf_probe_text(path) if is_pdf else ""
    title = str(bib_entry.get("title") or (_pdf_title(path) if is_pdf else ""))
    # The filename slug carries the author's own naming intent; split camelCase
    # so "MethodOfLimitsIndexNumbers" becomes words a title can match.
    slug = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ",
                  "-".join(path.stem.split("-")[1:]) or path.stem)
    surnames, year = _filename_hints(path.name)
    author = str(bib_entry.get("author", "")).split(" and ", 1)[0]
    res = library_matches(idx, title=title, text=f"{slug} {_front_matter(body)}",
                      doi=bib_entry.get("doi"), isbn=bib_entry.get("isbn"),
                      arxiv=bib_entry.get("arxiv"),
                      handle=bib_entry.get("handle"),
                      year=str(bib_entry.get("year") or year or ""),
                      first_author=first_author_surname(author) if author else None,
                      authors=list(surnames),
                      pdf_path=path)
    top = res["matches"][0] if res["matches"] else None
    # Five answers, not four. Collapsing a weak hit into "absent" is the
    # expensive mistake in both directions: called present, a document is
    # skipped and its full text never lands; called absent, a duplicate item is
    # minted. A weak hit is neither finding — it is a document to look at, and
    # saying so is cheaper than any threshold tuned to hide it.
    if top and "storageHash" in top["why"]:
        verdict = "identical"
    elif top and top["certainty"] in SAFE_TIERS:
        verdict = ("work_present_with_file" if top.get("has_file")
                   else "work_present_no_file")
    elif top:
        verdict = "ambiguous"
    else:
        verdict = "absent"
    row = {"file": path.name, "verdict": verdict,
           "zotero_key": top.get("key") if top else None,
           "zotero_title": top.get("title") if top else None,
           "why": top.get("why") if top else None,
           "certainty": top.get("certainty") if top else None,
           "consulted": res["consulted"], "skipped": res["skipped"]}
    # Top-tier tie (ticket 0570): the verdict stays what the best candidate
    # supports ("identical" is still true — the file IS stored), but every
    # parent tied at that tier is named; a clean answer that does not say it
    # looked elsewhere is the fault this module exists to avoid. Applies to
    # strong ties too — two records with an equally-named attachment leave
    # matches[0] arbitrary, and `attach --parent` aimed at the wrong one.
    tied = top_tier_peers(res["matches"])
    if len(tied) > 1:
        row["also_matches"] = [
            {"key": m["key"], "title": m.get("title"), "why": m["why"]}
            for m in tied[1:]
        ]
    return row


def count_verdicts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Verdict counts, plus the top-tier ties a human reader must see."""
    summary: dict[str, int] = {}
    for row in rows:
        summary[row["verdict"]] = summary.get(row["verdict"], 0) + 1
    # A tie must reach the summary a human reads, not only the rows behind
    # --out — a tied file counted as plain "identical"/"nothing" is the
    # silent clean answer this report exists to avoid (ticket 0570).
    tied = sum(1 for row in rows if row.get("also_matches"))
    if tied:
        summary["tied_parents"] = tied
    return summary


TIED_ACTION = ("several records tie at the top tier (also_matches); pick one "
               "before attaching by hand")


def cmd_audit(args: argparse.Namespace) -> int:
    """Reconcile a staging directory against the library — the count check.

    zotero.md requires checking docs/ staging *and* Zotero before declaring a
    source missing or present. Doing that by hand over a few hundred files is
    where the miscounts come from; this is the mechanical form.
    """
    root = Path(args.directory)
    if not root.is_dir():
        # Every other subcommand degrades to structured JSON and rc 1; a
        # mistyped path should not be the one that prints a traceback.
        emit_json({"error": f"not a directory: {root}", "verdict": "unchecked"})
        return 1
    idx = library_snapshot(resolve_db_path(args.zotero_db), args.library)
    if idx is None:
        emit_json({"error": "no local Zotero database found",
                   "verdict": "unchecked"})
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
    summary = count_verdicts(rows)
    actions = {"identical": "nothing",
               "work_present_with_file": "nothing; report the second copy",
               "work_present_no_file": "attach --parent <key> prints the "
                                       "by-hand step (never inject)",
               "ambiguous": "look: weak hit, neither present nor absent",
               "absent": "inject",
               "error": "unreadable; look at it",
               "tied_parents": TIED_ACTION}
    out = {"directory": str(root.resolve()), "zotero_db": idx["zotero_db"],
           "read_mode": idx["read_mode"],
           "library_works": len(idx["works"]),
           "library_attachments": len(idx["attachments"]),
           "files": len(files), "summary": summary,
           "actions": {k: actions[k] for k in summary if k in actions},
           "rows": rows}
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False))
    json.dump({k: out[k] for k in
               ("directory", "zotero_db", "read_mode", "library_works", "files",
                "summary", "actions")},
              sys.stdout, indent=2)
    sys.stdout.write("\n")
    if not args.out:
        json.dump(rows, sys.stdout, indent=1, ensure_ascii=False)
        sys.stdout.write("\n")
    return 0


RECONCILE_ACTIONS = {
    "identical": "nothing",
    "work_present_with_file": "nothing; report the second copy",
    "work_present_no_file": "attach by hand; see suggested_edits",
    "ambiguous": "inspect; neither inject nor skip",
    "absent": "inject only with explicit apply",
    "error": "inspect unreadable file",
    "unchecked": "resolve discovery or audit error",
    "tied_parents": TIED_ACTION,
    "deferred": "supply and corroborate metadata",
    "injected": "created in Zotero through the desktop connector",
    "failed_write": "inspect the outcome in Zotero before retrying",
    "apply_failed": "inspect error; no clean sweep",
}


def reconcile_apply_config(root: Path, account: str | None) -> dict[str, Any]:
    """Read the explicit project opt-in; its user_id must be the local account."""
    config = json.loads((root / ".zotero-reconcile.json").read_text())
    if not isinstance(config, dict) or config.get("apply") is not True:
        raise ValueError("apply must be true")
    if account is None:
        raise ValueError("the local Zotero is signed in to no account; "
                         "cannot check the configured user_id")
    if str(config.get("user_id")) != str(account):
        raise ValueError("configured user_id differs from target library "
                         f"(local Zotero is signed in as {account})")
    return config


def reconcile_report(root: Path, found: dict[str, Any], rows: list[dict[str, Any]],
                     errors: list[str], verdict: str | None = None
                     ) -> dict[str, Any]:
    """The one report shape every reconcile exit writes, early or not."""
    summary = count_verdicts(rows)
    if errors:
        summary["unchecked"] = len(errors)
    return {"verdict": verdict or ("unchecked" if errors else "checked"),
            "root": str(root),
            "bib_files": [str(p.relative_to(root)) for p in found["bib_files"]],
            "staging_dirs": [str(p.relative_to(root))
                             for p in found["staging_dirs"] if p.is_dir()],
            "files": len(rows), "summary": summary,
            "actions": {k: RECONCILE_ACTIONS[k] for k in summary},
            "suggested_edits": [
                {"itemKey": row.get("zotero_key"), "field": "attachment",
                 "old": "", "new": row.get("path", row.get("file"))}
                for row in rows if row["verdict"] == "work_present_no_file"],
            "rows": rows, "errors": errors}


def mark_apply_failed(report: dict[str, Any], exc: BaseException) -> None:
    report["apply_error"] = str(exc)
    report["apply_status"] = "failed"
    report["summary"]["apply_failed"] = 1
    report["actions"]["apply_failed"] = RECONCILE_ACTIONS["apply_failed"]


def emit_reconcile_report(report: dict[str, Any], out: str | None) -> None:
    """Write the full artifact and keep stdout compact when a path is given."""
    if out:
        Path(out).write_text(json.dumps(report, indent=2,
                                       ensure_ascii=False) + "\n")
    emit_json({k: v for k, v in report.items() if k != "rows"} if out else report)


def reconcile_empty_report(root: Path, found: dict[str, Any],
                           args: argparse.Namespace) -> int:
    """Nothing staged: no library read, but an apply still checks its opt-in.

    The opt-in is checked against the local account, so a broken
    `.zotero-reconcile.json` fails now instead of on the first staged file.
    """
    staged = any(p.is_dir() for p in found["staging_dirs"])
    report = reconcile_report(
        root, found, [], [],
        verdict="checked" if staged or found["bib_files"] else "no_staging")
    rc = 0
    if getattr(args, "apply", False):
        try:
            db_path = resolve_db_path(getattr(args, "zotero_db", None))
            if db_path is None:
                raise ValueError("no local Zotero database found")
            conn, mode = zotero_open(db_path)
            try:
                account = local_account(conn)
            finally:
                conn.close()
            report["library"] = {"zotero_db": str(db_path), "read_mode": mode}
            reconcile_apply_config(root, account)
            report.update({"applied": [], "apply_status": "nothing"})
        except (OSError, ValueError, TypeError, sqlite3.Error) as exc:
            mark_apply_failed(report, exc)
            rc = 1
    emit_reconcile_report(report, args.out)
    return rc


def audit_sources(root: Path, found: dict[str, Any], idx: dict[str, Any]
                  ) -> tuple[list[dict[str, Any]], list[str]]:
    """Audit every linked and orphan file; (rows, errors)."""
    rows: list[dict[str, Any]] = []
    errors = list(found["errors"])
    sources = found["linked"] + [{"path": path} for path in found["orphans"]]
    for source in sources:
        path = source["path"]
        try:
            row = audit_one(path, idx, bib_entry=source.get("entry"))
        except Exception as exc:
            errors.append(f"cannot audit {path.relative_to(root)}: {exc}")
            continue
        if "bib" in source:
            row.update({"source": "bib",
                        "bib": str(source["bib"].relative_to(root)),
                        "key": source["key"]})
        else:
            row["source"] = "orphan"
        row["path"] = str(path.relative_to(root))
        rows.append(row)
    return rows, errors


def cmd_reconcile(args: argparse.Namespace) -> int:
    """Report by default; apply only with a matching project opt-in file."""
    root = Path(args.root).resolve()
    if not root.is_dir():
        emit_reconcile_report({"verdict": "unchecked",
                               "error": f"not a directory: {root}"}, args.out)
        return 1
    found = discover_reconcile_files(root)
    if not (found["linked"] or found["orphans"] or found["errors"]):
        # Nothing staged: no library comparison is needed.
        return reconcile_empty_report(root, found, args)
    library = getattr(args, "library", USER_LIBRARY)
    db_path = resolve_db_path(getattr(args, "zotero_db", None))
    try:
        idx = library_snapshot(db_path, library)
    except sqlite3.Error as exc:
        idx, read_error = None, f"cannot read zotero.sqlite: {exc}"
    else:
        read_error = "no local Zotero database found"
    if idx is None:
        report = reconcile_report(root, found, [], found["errors"] + [read_error])
        emit_reconcile_report(report, args.out)
        return 1
    rows, errors = audit_sources(root, found, idx)
    report = reconcile_report(root, found, rows, errors)
    report["library"] = {"zotero_db": idx["zotero_db"],
                         "read_mode": idx["read_mode"]}
    apply_rc = 0
    if getattr(args, "apply", False):
        try:
            config = reconcile_apply_config(root, idx["account"])
            if errors:
                raise ValueError("discovery or audit is unchecked")
            db_path = Path(idx["zotero_db"])
            with directory_locks(found["staging_dirs"] + [db_path.parent]):
                # Re-read under the locks and keep them through the saves, so
                # two local sweeps cannot both act on the same pre-lock read.
                # The read covers the library the items will land in: a
                # collection in a group is checked against that group.
                conn, _ = zotero_open(db_path)
                try:
                    _, target_lib = resolve_target(conn, library,
                                                   config.get("collection"))
                finally:
                    conn.close()
                fresh = library_snapshot(db_path, target_lib)
                report, apply_rc = reconcile_apply(root, found, fresh, config,
                                                   args)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError,
                sqlite3.Error, urllib.error.URLError) as exc:
            mark_apply_failed(report, exc)
            apply_rc = 1
    emit_reconcile_report(report, args.out)
    return 1 if report["errors"] or apply_rc else 0


def reconcile_apply(root: Path, found: dict[str, Any], fresh: dict[str, Any],
                    config: dict[str, Any], args: argparse.Namespace
                    ) -> tuple[dict[str, Any], int]:
    """Create corroborated absent PDFs from the locked, fresh read."""
    rows, errors = audit_sources(root, found, fresh)
    if errors:
        raise ValueError("discovery or audit is unchecked")
    entries = {item["path"]: item.get("entry") or {} for item in found["linked"]}
    jobs: list[dict[str, Any]] = []
    job_paths: list[str] = []
    deferred = []
    for row in rows:
        if row["verdict"] != "absent":
            continue
        path = root / row["path"]
        entry = bib_to_inject_entry(entries.get(path.resolve(), {}), path)
        if entry is None or corroborate_entry(entry)["confidence"] != "corroborated":
            deferred.append({"file": row["path"],
                             "reason": "metadata needs manual corroboration"})
        else:
            jobs.append(entry)
            job_paths.append(row["path"])
    # The displayed report describes the same locked, fresh read that decides
    # the writes; the earlier read can predate another sweep.
    report = reconcile_report(root, found, rows, [])
    report["library"] = {"zotero_db": fresh["zotero_db"],
                         "read_mode": fresh["read_mode"]}
    summary, actions = report["summary"], report["actions"]
    report["deferred"] = deferred
    if deferred:
        summary["absent"] -= len(deferred)
        summary["deferred"] = len(deferred)
        actions["deferred"] = RECONCILE_ACTIONS["deferred"]
    report["applied"] = []
    rc = 0
    if jobs:
        inject_args = argparse.Namespace(
            entries_json=json.dumps(jobs), entries_file=None,
            collection=config.get("collection"),
            library=getattr(args, "library", USER_LIBRARY),
            zotero_db=fresh["zotero_db"], dry_run=False,
            skip_corroboration=False, force=False, _snapshot=fresh)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            rc = cmd_inject(inject_args)
        outcome = json.loads(captured.getvalue())
        if "results" not in outcome:
            raise RuntimeError(outcome.get("error", "inject failed"))
        report["applied"] = outcome["results"]
        if outcome.get("warning"):
            report["warning"] = outcome["warning"]
        for file, result in zip(job_paths, report["applied"]):
            result["file"] = file
            summary["absent"] -= 1
            if result.get("status") == "created" and not (
                    result.get("error") or result.get("attachment_error")
                    or result.get("target_error")):
                summary["injected"] = summary.get("injected", 0) + 1
                actions["injected"] = RECONCILE_ACTIONS["injected"]
            else:
                summary["failed_write"] = summary.get("failed_write", 0) + 1
                actions["failed_write"] = RECONCILE_ACTIONS["failed_write"]
    if summary.get("absent") == 0:
        summary.pop("absent")
        actions.pop("absent", None)
    report["apply_status"] = (
        "partial" if summary.get("failed_write") else
        "deferred" if deferred else
        "applied" if summary.get("injected") else "nothing")
    return report, rc


def bib_to_inject_entry(bib: dict[str, Any], path: Path) -> dict[str, Any] | None:
    """Use curated BibTeX first; accept orphan PDF metadata only if complete."""
    info = pdfinfo(path) if path.suffix.lower() == ".pdf" else {}
    title = str(bib.get("title") or info.get("Title") or "").strip()
    author = str(bib.get("author") or info.get("Author") or "").strip()
    year = str(bib.get("year") or "").strip()
    if not year:
        m = YEAR_RE.search(str(info.get("CreationDate") or path.name))
        year = m.group() if m else ""
    if not (title and author and year and path.suffix.lower() == ".pdf"):
        return None
    types = {"article": "JOUR", "book": "BOOK", "inbook": "CHAP",
             "incollection": "CHAP", "inproceedings": "CONF",
             "proceedings": "CONF", "phdthesis": "THES",
             "mastersthesis": "THES", "techreport": "RPRT",
             "misc": "GEN", "unpublished": "UNPB"}
    entry: dict[str, Any] = {
        "type": types.get(str(bib.get("_type", "")).lower(), "GEN"),
        "title": title, "authors": [a.strip() for a in author.split(" and ")],
        "year": year, "pdf": str(path), "attach_pdf": True}
    for source, target in (("doi", "doi"), ("isbn", "isbn"),
                           ("url", "url"), ("journal", "journal"),
                           ("publisher", "publisher"), ("pages", "pages")):
        if bib.get(source):
            entry[target] = str(bib[source])
    return entry


def cmd_attach(args: argparse.Namespace) -> int:
    """Report the by-hand step that files onto an EXISTING item.

    The repair for `work_present_no_file`. `inject` cannot do it, because it
    only creates items, and creating a second item to carry the file is how
    duplicates are born. The desktop connector cannot attach to an item it
    did not create in the same session either, so this verifies the parent
    and the files and says what to do in Zotero.
    """
    db_path = resolve_db_path(args.zotero_db)
    if db_path is None:
        raise SystemExit("attach: no local Zotero database found")
    conn, mode = zotero_open(db_path)
    try:
        data = item_data(conn, args.parent, args.library)
    finally:
        conn.close()
    if data is None:
        emit_json({"parent": args.parent, "read_mode": mode,
                   "error": "item not found"})
        return 1
    rc = 0
    suggested = []
    for f in args.file:
        p = Path(f)
        if not p.is_file():
            suggested.append({"file": f, "error": "not found"})
            rc = 1
            continue
        suggested.append({"itemKey": args.parent, "field": "attachment",
                          "old": "", "new": str(p.resolve())})
    emit_json({"parent": args.parent, "title": data.get("title"),
               "read_mode": mode,
               "apply": "in Zotero, select the item, then Add Attachment > "
                        "Attach Stored Copy of File (or drag the file onto it)",
               "suggested": suggested})
    return rc


def add_library_args(parser: argparse.ArgumentParser, help_scope: str) -> None:
    parser.add_argument("--zotero-db", help="override Zotero sqlite path")
    parser.add_argument("--library", default=USER_LIBRARY, help=help_scope)


def main() -> int:
    p = argparse.ArgumentParser(prog="zotero.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    scope = ("dedup scope: 'user' (default, the inject destination), 'all', "
             "or a numeric libraryID")

    pp = sub.add_parser("probe", help="extract metadata + Zotero dup hits")
    pp.add_argument("pdf", nargs="+")
    add_library_args(pp, scope)
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
    add_library_args(pm, scope)
    pm.set_defaults(func=cmd_match)

    pd = sub.add_parser("dedup-report", help="read-only report of identical "
                        "attachments under distinct My Library items")
    pd.add_argument("--zotero-db", help="override local Zotero sqlite path")
    pd.add_argument("--format", choices=("html", "json"), default="html")
    pd.add_argument("--out", help="write report to this file (else stdout)")
    pd.set_defaults(func=cmd_dedup_report)

    pa = sub.add_parser("audit",
                        help="reconcile a staging directory against the "
                             "library: identical / present-with-file / "
                             "present-no-file / ambiguous / absent")
    pa.add_argument("directory")
    pa.add_argument("--out", help="write the full per-file report to this path")
    pa.add_argument("--ext", nargs="*", help="extensions to audit "
                                             "(default: documents)")
    add_library_args(pa, scope)
    pa.set_defaults(func=cmd_audit)

    pr = sub.add_parser("reconcile", help="report BibTeX-linked staging files "
                        "and unlinked orphans; explicit opt-in to apply")
    pr.add_argument("root", nargs="?", default=".",
                    help="repository root (default: current directory)")
    pr.add_argument("--out", help="write the full JSON report to this path")
    pr.add_argument("--apply", action="store_true",
                    help="create corroborated absent PDFs through the desktop "
                         "connector, only when the project has "
                         ".zotero-reconcile.json with apply=true and the "
                         "user_id local Zotero is signed in as")
    add_library_args(pr, scope)
    pr.set_defaults(func=cmd_reconcile)

    pt = sub.add_parser("attach",
                        help="report how to file documents onto an EXISTING "
                             "item (the present-no-file case); never writes")
    pt.add_argument("--parent", required=True, help="parent item key")
    pt.add_argument("file", nargs="+")
    add_library_args(pt, scope)
    pt.set_defaults(func=cmd_attach)

    pw = sub.add_parser("write", help="write combined RIS file from JSON entries")
    pw.add_argument("--out", required=True, help="output RIS path")
    g = pw.add_mutually_exclusive_group()
    g.add_argument("--entries-json", help="inline JSON: array of entry dicts")
    g.add_argument("--entries-file", help="path to JSON file with entries")
    pw.set_defaults(func=cmd_write)

    pi = sub.add_parser("inject",
                        help="create items (and attach PDFs) through the "
                             "Zotero desktop connector; Zotero must be running")
    gi = pi.add_mutually_exclusive_group()
    gi.add_argument("--entries-json", help="inline JSON: array of entry dicts")
    gi.add_argument("--entries-file", help="path to JSON file with entries")
    pi.add_argument("--collection", help="collection key to file items under "
                                         "(its library is the destination)")
    add_library_args(pi, "destination and dedup scope: 'user' (default) or "
                         "a numeric libraryID, e.g. an editable group")
    pi.add_argument("--dry-run", action="store_true",
                    help="print the Zotero item JSON, do not contact Zotero")
    pi.add_argument("--skip-corroboration", action="store_true",
                    help="create items even when the metadata is contradicted "
                         "by the PDF's own front matter (default: refuse)")
    pi.add_argument("--force", action="store_true",
                    help="explicitly bypass the library and batch duplicate "
                         "guard; use only after examining matches")
    pi.set_defaults(func=cmd_inject)

    pe = sub.add_parser("enrich",
                        help="report missing fields on EXISTING items for the "
                             "author to fill by hand; never writes")
    ge = pe.add_mutually_exclusive_group(required=True)
    ge.add_argument("--item-key", help="the item to enrich")
    ge.add_argument("--jobs-file",
                    help="path to JSON: array of {item_key, expect_title, "
                         "set:{field: value}}")
    pe.add_argument("--expect-title",
                    help="fragment that MUST appear in the item's title; "
                         "guards against a transposed item key")
    pe.add_argument("--set", action="append", metavar="FIELD=VALUE",
                    help="field to suggest, repeatable. Zotero field names are "
                         "case-sensitive: DOI, url, publisher")
    pe.add_argument("--overwrite", action="store_true",
                    help="also suggest replacing fields that already hold a "
                         "DIFFERENT value; without it those are refused")
    add_library_args(pe, scope)
    pe.set_defaults(func=cmd_enrich)

    args = p.parse_args()
    if args.cmd == "enrich" and args.item_key and not args.expect_title:
        p.error("--expect-title is required with --item-key")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

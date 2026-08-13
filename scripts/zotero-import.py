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


def zotero_matches(
    conn: sqlite3.Connection,
    *,
    doi: str | None,
    title: str | None,
    year: str | None,
    pdf_path: Path,
) -> list[dict[str, Any]]:
    cur = conn.cursor()
    if doi:
        rows = cur.execute(
            """
            SELECT i.itemID,
                   MAX(CASE WHEN f.fieldName='title' THEN v.value END) AS title,
                   MAX(CASE WHEN f.fieldName='DOI' THEN v.value END)   AS doi,
                   MAX(CASE WHEN f.fieldName='date' THEN v.value END)  AS date
            FROM items i
            JOIN itemData d ON d.itemID = i.itemID
            JOIN fields f   ON f.fieldID = d.fieldID
            JOIN itemDataValues v ON v.valueID = d.valueID
            WHERE i.itemID NOT IN (SELECT itemID FROM deletedItems)
              AND i.itemID IN (
                  SELECT d2.itemID FROM itemData d2
                  JOIN fields f2 ON f2.fieldID = d2.fieldID
                  JOIN itemDataValues v2 ON v2.valueID = d2.valueID
                  WHERE f2.fieldName='DOI' AND LOWER(v2.value)=LOWER(?)
              )
            GROUP BY i.itemID
            """,
            (doi,),
        ).fetchall()
    else:
        sql = """
            SELECT i.itemID,
                   MAX(CASE WHEN f.fieldName='title' THEN v.value END) AS title,
                   MAX(CASE WHEN f.fieldName='DOI' THEN v.value END)   AS doi,
                   MAX(CASE WHEN f.fieldName='date' THEN v.value END)  AS date
            FROM items i
            JOIN itemData d ON d.itemID = i.itemID
            JOIN fields f   ON f.fieldID = d.fieldID
            JOIN itemDataValues v ON v.valueID = d.valueID
            LEFT JOIN itemAttachments a ON a.itemID = i.itemID AND a.parentItemID IS NOT NULL
            WHERE i.itemID NOT IN (SELECT itemID FROM deletedItems)
              AND a.itemID IS NULL
        """
        params: list[Any] = []
        if year:
            sql += " AND i.itemID IN (SELECT d3.itemID FROM itemData d3 " \
                   "JOIN fields f3 ON f3.fieldID=d3.fieldID " \
                   "JOIN itemDataValues v3 ON v3.valueID=d3.valueID " \
                   "WHERE f3.fieldName='date' AND v3.value LIKE ?)"
            params.append(f"%{year}%")
        sql += " GROUP BY i.itemID"
        rows = cur.execute(sql, params).fetchall()

    def tok(s: str) -> set[str]:
        cleaned = re.sub(r"[^\w\s]", " ", s.lower(), flags=re.UNICODE)
        return {w for w in cleaned.split() if len(w) > 2}

    title_set = tok(title or "")
    matches: list[dict[str, Any]] = []
    for item_id, t, d, dt in rows:
        score = 0
        why: list[str] = []
        if doi and d and doi.lower() == d.lower():
            score = 100
            why.append("doi")
        elif title_set and t:
            b = tok(t)
            if b:
                j = len(title_set & b) / len(title_set | b)
                if j >= 0.6:
                    score = int(j * 90)
                    why.append(f"title~{j:.2f}")
        if score == 0:
            continue
        if year and dt and year in dt:
            score += 5
            why.append("year")
        matches.append({"itemID": item_id, "title": t, "doi": d, "date": dt,
                        "score": score, "why": why})

    matches.sort(key=lambda m: -m["score"])
    matches = matches[:5]

    # Decorate top hits with attachment info.
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
        m["pdf_basename_match"] = any(
            (p or "").endswith(pdf_path.name) for (p, *_rest) in atts
        )
    return matches


def probe_one(pdf: Path, conn: sqlite3.Connection | None) -> dict[str, Any]:
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
            conn, doi=ids["doi"], title=pdfinfo_title, year=year, pdf_path=pdf,
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
            out.append(probe_one(pdf, conn))
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
        json.dump({"zotero_db": None, "matches": []}, sys.stdout)
        sys.stdout.write("\n")
        return 0
    conn = zotero_open(db_path)
    pdf_path = Path(args.pdf) if args.pdf else Path("/dev/null")
    matches = zotero_matches(
        conn,
        doi=args.doi,
        title=args.title,
        year=args.year,
        pdf_path=pdf_path,
    )
    json.dump({"zotero_db": str(db_path), "matches": matches},
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
    pp.set_defaults(func=cmd_probe)

    pm = sub.add_parser("match", help="refined Zotero lookup by title/doi/year")
    pm.add_argument("--title", help="title to fuzzy-match")
    pm.add_argument("--doi", help="DOI to exact-match")
    pm.add_argument("--year", help="year boost")
    pm.add_argument("--pdf", help="PDF path (used only for attachment basename check)")
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

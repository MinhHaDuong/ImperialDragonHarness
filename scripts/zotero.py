#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "bibtexparser>=1.4,<2",
#     "httpx2>=2.13,<3",
#     "isbnlib>=3.10,<4",
#     "pyzotero>=1.16,<2",
# ]
# ///
"""Backend helper scripts/zotero.py for the zotero skill.

Subcommands: extract-metadata, find-work, report-duplicates, check-staging,
suggest-attachments, create-items, suggest-edits.

`extract-metadata` reads a PDF and never needs Zotero; every other
subcommand talks to the running Zotero.

Local-only and stateless, on top of pyzotero's local client. Every library
read goes through the running desktop client's local API (127.0.0.1:23119,
no key), live, on each call; zotero.sqlite is never opened, and nothing is
cached, indexed or logged to disk between runs. Writes go through the same
local API with a local API key the user grants once in Zotero (kept in
key_file(), mode 600, never printed). `create-items` creates new items with
their PDFs; `suggest-edits`, `suggest-attachments` and `check-staging
--apply` edit existing items only with --edit, and otherwise report the
edit.

Zotero must be running. When it is not, the helper launches it (never in a
container) and waits; when it still does not answer, the command does
nothing and says so (exit EXIT_UNAVAILABLE; `check-staging` exits 0 with
verdict "zotero_unavailable"). A read Zotero accepts and does not finish in
time is not that: exit EXIT_SLOW, `check-staging` verdict "zotero_slow".

Run it as an executable: the shebang has uv install the dependencies above.
"""

import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import mimetypes
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import bibtexparser
import httpx2
import isbnlib
from bibtexparser.bibdatabase import UndefinedString
from bibtexparser.bparser import BibTexParser
from pyzotero import errors as ze
from pyzotero import zotero

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


# --- Deduplication -----------------------------------------------------------
# find_work() asks the running Zotero's own search (the local API's `q`, in
# `qmode=everything`) for each key the caller gives: DOI, ISBN, arXiv id,
# handle, title. The one match it asserts is exact: a normalised identifier
# equal to the hit's own field, or the hit holding a stored file with the
# PDF's md5 (`storageHash`). A title search returns candidates for the caller
# to judge, never a match. No call reads the whole library. Scope defaults to
# the user library because create-items writes there: a hit that lives only
# in a group library must not suppress a creation missing from the
# destination.

USER_LIBRARY = "user"
ALL_LIBRARIES = "all"


def classify_matches(matches: list[dict[str, Any]],
                     candidates: list[dict[str, Any]]) -> str:
    """'match' for one exact match; 'ambiguous' for several, which tie
    (ticket 0570: two records legitimately share one attachment md5, and
    answering from matches[0] alone made the second vanish); 'candidates'
    when only the title search answered; 'none' otherwise."""
    if matches:
        return "match" if len(matches) == 1 else "ambiguous"
    return "candidates" if candidates else "none"


def duplicate_hash_report(attachments: list[dict[str, Any]],
                          works: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Exact-file candidates under distinct parents in My Library.

    The library-to-library form of the strongest key, ``storageHash``: the
    md5 Zotero reports for each stored file. An attachment without one (a
    linked file, a stored file missing on disk) is not compared. `works`
    holds the parents worth grouping: those not trashed. It reports candidates, never a
    merge decision: two records can deliberately carry the same file. Other
    bibliographic keys are shown as supporting evidence, not as a
    substitute for the hash.
    """
    scanned = 0
    by_hash: dict[str, dict[str, list[dict[str, str]]]] = {}
    for att in attachments:
        if not att.get("md5") or not att.get("parent"):
            continue
        scanned += 1
        if att["parent"] not in works:
            continue
        by_hash.setdefault(att["md5"], {}).setdefault(att["parent"], []).append({
            "key": att["key"], "filename": att.get("filename") or "",
            "content_type": att.get("contentType") or ""})

    def signals(left: dict[str, str], right: dict[str, str]) -> list[str]:
        found = []
        if left["item_type"] != right["item_type"]:
            return found
        if left["doi"] and normal_doi(left["doi"]) == normal_doi(right["doi"]):
            found.append("doi")
        if isbn13s(left["isbn"]) & isbn13s(right["isbn"]):
            found.append("isbn")
        if left["title"] and fold(left["title"]) == fold(right["title"]):
            found.append("title")
        return found

    clusters = []
    for digest, parents in sorted(by_hash.items()):
        if len(parents) < 2:
            continue
        items = []
        for key in sorted(parents):
            w = works[key]
            items.append({"key": key, "item_type": w.get("itemType", ""),
                          "title": w.get("title") or "", "doi": w.get("DOI") or "",
                          "isbn": w.get("ISBN") or "", "date": w.get("date") or "",
                          "first_author": (w.get("creators") or [""])[0],
                          "attachments": parents[key],
                          "url": f"zotero://select/library/items/{key}"})
        overlap = []
        for pos, left in enumerate(items):
            for right in items[pos + 1:]:
                shared = signals(left, right)
                if shared:
                    overlap.append({"items": [left["key"], right["key"]],
                                    "keys": shared})
        clusters.append({"hash": digest, "matched_by": "storageHash",
                         "items": items, "bibliographic_overlap": overlap})
    return {"library_id": USER_LIBRARY,
            "hashed_attachments_scanned": scanned,
            "candidate_clusters": len(clusters),
            "clusters": clusters}


def extract_one(pdf: Path) -> dict[str, Any]:
    """Metadata of one PDF from its own bytes: no Zotero, no network."""
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
    year = None
    if "CreationDate" in info:
        ym = YEAR_RE.search(info["CreationDate"])
        if ym:
            year = ym.group(0)
    return {
        "pdf": str(pdf.resolve()),
        "pdf_size": pdf.stat().st_size,
        "page_count": page_count,
        "pdfinfo": {k: info.get(k) for k in ("Title", "Author", "Subject",
                                             "Keywords", "Creator", "Producer",
                                             "CreationDate", "ModDate", "Pages")},
        "first_pages_text": text_front,
        "last_pages_text": text_back,
        "identifiers": find_identifier(text_front, text_back,
                                       info.get("Subject") or ""),
        "year_hint": year,
        "filename": pdf.name,
    }


def last_first(a: str) -> str:
    """"First Last" as "Last, First"; a name with a comma, or one word, as is."""
    a = a.strip()
    if "," in a:
        return a
    parts = a.split()
    if len(parts) >= 2:
        return f"{parts[-1]}, {' '.join(parts[:-1])}"
    return a


# --- Zotero item JSON --------------------------------------------------------
# `create-items` hands Zotero item JSON to pyzotero's local client, which
# creates it as the client's own UI would.

# An entry's `type` is a Zotero item type (`journalArticle`, `report`, ...),
# checked against the running client's schema; an unknown one is refused.
ENTRY_TYPE_DEFAULT = "journalArticle"
# Item types that are not works.
NOT_WORKS = {"attachment", "note", "annotation"}

# Field placement is per item type. Zotero gives each type its own field set,
# and a field the type does not own is refused on save (`'numPages' is not a
# valid field for type 'report'`), so a mapper that emits `publisher`/
# `volume`/`seriesTitle` unconditionally cannot import a report, a thesis or
# a manuscript at all. Each slot below lists the fields that can hold it, in
# preference order; the first one the target type owns in the running
# client's schema (pyzotero's item_type_fields) wins, else the value goes to
# `extra`.
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

# Every key an entry may carry. An
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
    a = last_first(a)  # normalize to "Last, First"
    last, _, first = a.partition(",")
    if first.strip():
        return {"creatorType": "author", "firstName": first.strip(),
                "lastName": last.strip()}
    return {"creatorType": "author", "name": last.strip()}


def schema_fields(z: zotero.Zotero) -> Any:
    """item type -> the fields it owns, from the running client's schema,
    each type asked once per run; a type the schema does not know, or one
    that is not a work, is refused."""
    known: dict[str, frozenset[str]] = {}
    types: set[str] = set()

    def owned(item_type: str) -> frozenset[str]:
        if not types:
            with local_api():
                types.update(t["itemType"] for t in z.item_types())
        if item_type not in types - NOT_WORKS:
            raise ValueError(f"entry type {item_type!r} is not a Zotero item "
                             f"type; use one of "
                             f"{', '.join(sorted(types - NOT_WORKS))}")
        if item_type not in known:
            with local_api():
                known[item_type] = frozenset(
                    f["field"] for f in z.item_type_fields(item_type))
        return known[item_type]
    return owned


def place_slot(item: dict[str, Any], extra: list[str], slot: str, value: str,
               owned: Any) -> None:
    """Store `value` in the slot's field for this item type, else in `extra`.

    Nothing is dropped: a slot the target type has no field for (or whose
    field is already taken) is appended to `extra` under its CSL variable
    name, where Zotero still reads it.
    """
    fields = owned(item["itemType"])
    field = next((f for f in ZOTERO_SLOT_PREFERENCES[slot] if f in fields), None)
    if field and field not in item:
        item[field] = value
    else:
        extra.append(f"{ZOTERO_SLOT_EXTRA_LABEL[slot]}: {value}")


def entry_to_zotero_item(e: dict[str, Any], owned: Any) -> dict[str, Any]:
    """Zotero item JSON for one entry; `owned(item_type)` is the set of
    fields the type owns (schema_fields)."""
    item: dict[str, Any] = {"itemType": e.get("type") or ENTRY_TYPE_DEFAULT}
    owned(item["itemType"])  # refuses an unknown type
    extra: list[str] = []
    # Universal fields: every regular Zotero type owns them, and Zotero maps
    # `title` onto a type's own title field (caseName, nameOfAct, subject).
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
            place_slot(item, extra, slot, str(value), owned)
    if extra:
        item["extra"] = "\n".join(extra)
    return item


def plan_enrichment(data: dict[str, Any], sets: dict[str, str],
                    expect_title: str,
                    overwrite: bool = False) -> tuple[dict[str, str], list[str]]:
    """Decide which edits to suggest on an existing item. Pure: no I/O.

    Returns (fields to change, refusals). A refusal is a reason NOT to suggest
    a given field; the caller reports every one of them and suggests the rest.
    Nothing here writes: `suggest-edits --edit` writes the returned fields.

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


# --- The running Zotero, through pyzotero's local client --------------------
# Every read and every write goes through pyzotero's local mode, which speaks
# the desktop client's local API (/api/ on 127.0.0.1:23119). Zotero 10 or
# later is the floor for the whole helper: local writes need it, and its
# item JSON reports each stored file's md5. Reads need no key. Writes need a
# local API key that the user grants once in Zotero's Allow / Always Allow /
# Deny dialog (`authorize_local`); only an "Always Allow" key is accepted,
# kept in key_file(), a credential file, and nothing else is kept between
# runs.
#
# The user enables the local API under LOCAL_API_SETTING; until then every
# /api/ request answers 403 "Local API is not enabled".
#
# Zotero must be running. When nothing answers, ensure_zotero() launches the
# desktop client, except in a container, and waits for it; when that fails
# the command does nothing and says Zotero was unavailable. A request Zotero
# accepts but does not finish in time is another answer, ZoteroSlow: the
# read is incomplete, and no command reports it as "unavailable".

DEFAULT_ZOTERO_URL = "http://127.0.0.1:23119"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
# Items per local API page. pyzotero gives each read request 30 s, and
# Zotero 10 hashes every stored file it lists, so pages stay small.
PAGE = 100
# The oldest Zotero the helper talks to (its X-Zotero-Version header).
MIN_ZOTERO = 10
# Writes and uploads: a large PDF on a slow disk.
WRITE_TIMEOUT = 300.0
LOCAL_API_SETTING = ('Zotero Settings > Advanced > "Allow other applications '
                     'on this computer to communicate with Zotero"')
# How long a launched Zotero gets to answer, and how often it is asked.
LAUNCH_WAIT = 90.0
LAUNCH_POLL = 1.0
# How long a check-and-create run waits for another one to finish.
LOCK_WAIT = 600.0
# How long Zotero's authorization dialog waits for the user's answer.
AUTHORIZE_WAIT = 120.0
# The name Zotero shows in its authorization dialog.
APP_NAME = "zotero.py (agent harness)"
# The variable holding the local API key in key_file().
KEY_VARIABLE = "ZOTERO_LOCAL_API_KEY"
# Exit status of a command that needed Zotero and found it unavailable: it
# did nothing. EX_TEMPFAIL from sysexits.h, "try again later". `check-staging`
# exits 0 instead, with verdict "zotero_unavailable", so an unattended sweep
# reads the no-op as clean.
EXIT_UNAVAILABLE = 75
# Exit status of a read Zotero did not finish in time: EX_IOERR. Never 0 and
# never EXIT_UNAVAILABLE, check-staging included: an incomplete read is not
# a clean no-op.
EXIT_SLOW = 74


class ZoteroUnavailable(RuntimeError):
    """Zotero is not running and could not be launched: nothing was done."""


class ZoteroSlow(RuntimeError):
    """Zotero accepted a request and did not finish it in time: whatever
    was being read is incomplete. Not ZoteroUnavailable, on purpose."""


class LocalAPIError(RuntimeError):
    """Zotero answers, but its local API refused or is not the local API."""


def zotero_url() -> str:
    """The Zotero URL: ZOTERO_CONNECTOR_URL, read on every call, else 23119.
    A trailing slash is dropped, so paths join without a `//`."""
    return (os.environ.get("ZOTERO_CONNECTOR_URL")
            or DEFAULT_ZOTERO_URL).rstrip("/")


def zotero_base() -> str:
    """The Zotero URL, refused unless it is on this machine and carries no
    credentials.

    The override serves a Zotero on another port, such as the tests'
    throwaway client; a remote host would send item metadata and PDFs off
    the machine, which a local-only helper must not do.
    """
    url = zotero_url()
    parts = urllib.parse.urlsplit(url)
    if parts.username is not None or parts.password is not None:
        # Never echoed: the userinfo is a credential.
        raise LocalAPIError("refusing a Zotero URL that carries credentials "
                            "(user:password@): the local API takes none")
    host = parts.hostname
    if host not in LOOPBACK_HOSTS:
        raise LocalAPIError(f"refusing non-local Zotero URL {url}: "
                            f"the helper is local-only")
    return url


def http_client(timeout: float = WRITE_TIMEOUT) -> httpx2.Client:
    """No proxy, no redirect: a loopback URL must stay on the loopback,
    whatever http_proxy says and whatever the listener answers."""
    return httpx2.Client(follow_redirects=False, trust_env=False,
                         timeout=timeout)


def local_library(library: str = USER_LIBRARY, *,
                  timeout: float = WRITE_TIMEOUT) -> zotero.Zotero:
    """pyzotero's local client for one library: "user" or a groupID."""
    if library == USER_LIBRARY:
        lib_id, lib_type = "0", "user"
    elif str(library).isdigit():
        lib_id, lib_type = str(library), "group"
    else:
        raise ValueError(f"--library {library!r}: use 'user', 'all' or a groupID")
    z = zotero.Zotero(lib_id, lib_type, local=True,
                      client=http_client(timeout), upload_timeout=timeout)
    # pyzotero's local endpoint is fixed at 23119; the URL may say otherwise.
    z.endpoint = f"{zotero_base()}/api"
    return z


def refusal(exc: Exception) -> LocalAPIError:
    """A local API refusal, naming its cause when the error tells it, else
    the version floors and the setting that usually cause it."""
    text = str(exc).strip()
    if "Local API is not enabled" in text:
        return LocalAPIError(f"Zotero's local API is disabled. Enable "
                             f"{LOCAL_API_SETTING} and retry.")
    reason = text.splitlines()[-1] if text else type(exc).__name__
    if isinstance(exc, ze.ServerIDMismatchError):
        return LocalAPIError(f"another Zotero instance answers than the one "
                             f"this run started with ({reason}); rerun")
    if isinstance(exc, (ze.PreConditionFailedError, ze.ConflictError)):
        return LocalAPIError(f"Zotero refused the write as conflicting: the "
                             f"item or library changed since this run read "
                             f"it ({reason}); rerun to read it again")
    return LocalAPIError(f"Zotero's local API refused the request ({reason}). "
                         f"The helper needs Zotero {MIN_ZOTERO} or later, with "
                         f"{LOCAL_API_SETTING} enabled.")


@contextlib.contextmanager
def local_api():
    """Turn a timeout into ZoteroSlow, other transport failures into
    ZoteroUnavailable and refusals into LocalAPIError; a missing item and a
    missing key pass through."""
    try:
        yield
    except httpx2.TimeoutException as exc:
        raise ZoteroSlow(f"Zotero at {zotero_url()} did not finish a request "
                         f"in time ({type(exc).__name__}); the read is "
                         f"incomplete, so nothing was concluded") from exc
    except httpx2.TransportError as exc:
        raise ZoteroUnavailable(f"Zotero stopped answering at {zotero_url()} "
                                f"({exc})") from exc
    except (ze.ResourceNotFoundError, ze.LocalAPIKeyRequiredError):
        raise
    except ze.FileDoesNotExistError as exc:
        # A local file, not a refusal: the setting is not the cause.
        raise LocalAPIError(f"the file to store cannot be read ({exc})"
                            ) from exc
    except ze.UploadError as exc:
        # pyzotero raises it only when the upload POST cannot connect or
        # times out: a transport loss, not a refusal.
        raise ZoteroUnavailable(f"Zotero stopped answering at {zotero_url()} "
                                f"during an upload ({exc})") from exc
    except ze.PyZoteroError as exc:
        raise refusal(exc) from exc


def not_zotero(url: str, status: int) -> LocalAPIError:
    """Something other than Zotero answers at `url`: the root of Zotero's
    local API always sends an X-Zotero-Version header."""
    return LocalAPIError(
        f"something other than Zotero answers at {url} (HTTP {status}, no "
        f"X-Zotero-Version header). Point ZOTERO_CONNECTOR_URL at Zotero "
        f"(unset, it is {DEFAULT_ZOTERO_URL}) or free that port, and check "
        f"that {LOCAL_API_SETTING} is enabled in Zotero.")


def zotero_answers(timeout: float = 2.0) -> bool:
    """Does Zotero answer on its port? Its local API root answers with the
    client's version header, which must name Zotero 10 or later; anything
    else listening there is an error, and a listener that accepts the
    connection without answering is ZoteroSlow."""
    try:
        with http_client(timeout) as client:
            resp = client.get(f"{zotero_base()}/api/")
    except httpx2.ConnectTimeout:
        return False
    except httpx2.TimeoutException as exc:
        raise ZoteroSlow(f"something accepts connections at {zotero_url()} "
                         f"but did not answer within {timeout:.0f} s") from exc
    except httpx2.TransportError:
        return False
    if "x-zotero-version" not in resp.headers:
        raise not_zotero(zotero_url(), resp.status_code)
    check_version(resp.headers["x-zotero-version"])
    if resp.status_code != 200:
        raise refusal(RuntimeError(resp.text or f"HTTP {resp.status_code}"))
    return True


def check_version(version: str) -> None:
    """Zotero 10 or later, as its X-Zotero-Version header says; else refuse."""
    major = version.split(".", 1)[0]
    if not major.isdigit() or int(major) < MIN_ZOTERO:
        raise LocalAPIError(f"Zotero {version} answers at {zotero_url()}; the "
                            f"helper needs Zotero {MIN_ZOTERO} or later")


def in_container() -> str | None:
    """Why Zotero must not be launched here, else None: a container, a
    headless runner, or the explicit ZOTERO_NO_LAUNCH opt-out."""
    if os.environ.get("ZOTERO_NO_LAUNCH"):
        return "ZOTERO_NO_LAUNCH is set"
    for marker in ("/.dockerenv", "/run/.containerenv"):
        if os.path.exists(marker):
            return marker
    if os.environ.get("container"):
        return f"container={os.environ['container']}"
    for name in ("CI", "GITHUB_ACTIONS", "GITLAB_CI", "BUILDKITE", "JENKINS_URL"):
        if os.environ.get(name):
            return f"{name} is set"
    try:
        cgroup = Path("/proc/1/cgroup").read_text()
    except OSError:
        cgroup = ""
    for hint in ("docker", "kubepods", "containerd", "lxc", "podman", "libpod"):
        if hint in cgroup:
            return f"/proc/1/cgroup names {hint}"
    if (sys.platform.startswith("linux") and not os.environ.get("DISPLAY")
            and not os.environ.get("WAYLAND_DISPLAY")):
        return "no display"
    return None


def find_zotero_launcher() -> list[str] | None:
    """The command that starts the desktop client here, if one is installed."""
    if found := shutil.which("zotero"):
        return [found]
    home = Path.home()
    for candidate in (home / "Zotero_linux-x86_64" / "zotero",
                      home / ".local" / "Zotero_linux-x86_64" / "zotero",
                      home / ".local" / "share" / "zotero" / "zotero",
                      Path("/opt/zotero/zotero"), Path("/usr/lib/zotero/zotero"),
                      Path("/usr/local/bin/zotero"),
                      Path("/Applications/Zotero.app/Contents/MacOS/zotero")):
        if os.access(candidate, os.X_OK):
            return [str(candidate)]
    flatpak = shutil.which("flatpak")
    if flatpak:
        try:
            found_app = subprocess.run([flatpak, "info", "org.zotero.Zotero"],
                                       capture_output=True,
                                       timeout=10).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            found_app = False
        if found_app:
            return [flatpak, "run", "org.zotero.Zotero"]
    return None


def launch_zotero(command: list[str]) -> subprocess.Popen:
    """Start the desktop client detached; it outlives this process."""
    return subprocess.Popen(command, stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, start_new_session=True)


def stop_launched(process: subprocess.Popen) -> None:
    """Stop a client this helper launched, its process group included.

    Only the process the helper started itself, never a Zotero it found:
    a launch that missed its deadline must not come up after the helper
    has reported doing nothing.
    """
    for sig, wait in ((signal.SIGTERM, 10.0), (signal.SIGKILL, 5.0)):
        try:
            os.killpg(process.pid, sig)
        except ProcessLookupError:
            break
        try:
            process.wait(timeout=wait)
            break
        except subprocess.TimeoutExpired:
            continue
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)


def ensure_zotero() -> str:
    """Make sure Zotero answers: "running" or "launched".

    When nothing answers, the desktop client is launched and given
    LAUNCH_WAIT seconds, except in a container or headless runner, where
    nothing is launched. A launch that does not answer in time is stopped.
    ZoteroUnavailable means nothing was done.
    """
    if zotero_answers():
        return "running"
    reason = in_container()
    if reason:
        raise ZoteroUnavailable(f"Zotero is not running and is not launched "
                                f"here ({reason}). Nothing was done.")
    command = find_zotero_launcher()
    if command is None:
        raise ZoteroUnavailable("Zotero is not running and no Zotero "
                                "installation was found to launch. Start "
                                "Zotero and retry; nothing was done.")
    try:
        process = launch_zotero(command)
    except OSError as exc:
        raise ZoteroUnavailable(f"Zotero is not running and launching it "
                                f"({' '.join(command)}) failed: {exc}. "
                                f"Nothing was done.") from exc
    deadline = time.monotonic() + LAUNCH_WAIT
    try:
        while not answers_yet():
            if time.monotonic() >= deadline:
                raise ZoteroUnavailable(
                    f"Zotero was launched ({' '.join(command)}) but did not "
                    f"answer within {LAUNCH_WAIT:.0f} s, so the helper "
                    f"stopped it. Start Zotero and retry; nothing was done.")
            time.sleep(LAUNCH_POLL)
    except (ZoteroUnavailable, KeyboardInterrupt):
        # Missed deadline or an interrupt: the launch never answered. A
        # client that answered with an error (local API disabled) stays
        # open, since the message asks the user to change its setting.
        stop_launched(process)
        raise
    return "launched"


def answers_yet() -> bool:
    """zotero_answers() while a launched client starts: busy is not yet."""
    try:
        return zotero_answers()
    except ZoteroSlow:
        return False


def unavailable_payload(exc: ZoteroUnavailable) -> dict[str, Any]:
    return {"zotero": "unavailable", "error": str(exc), "verdict": "unchecked"}


def slow_payload(exc: ZoteroSlow) -> dict[str, Any]:
    return {"zotero": "slow", "error": str(exc), "verdict": "unchecked"}


# --- The local API key: a credential, never printed --------------------------

def key_file() -> Path:
    """Where the granted key lives: ZOTERO_LOCAL_KEY_FILE, else the harness
    keystore ~/.config/keys/zotero-local.env."""
    override = os.environ.get("ZOTERO_LOCAL_KEY_FILE")
    if override:
        return Path(override)
    return Path.home() / ".config" / "keys" / "zotero-local.env"


def stored_key() -> str | None:
    """The kept local API key, None when there is none."""
    try:
        text = key_file().read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    for line in text.splitlines():
        name, sep, value = line.strip().removeprefix("export ").partition("=")
        if sep and name.strip() == KEY_VARIABLE:
            return value.strip().strip("'\"") or None
    return None


def store_key(key: str) -> None:
    """Keep a key granted with "Always Allow": mode 600, directory 700.

    The key is written to a fresh temporary file (O_EXCL, never through a
    planted name) and renamed over the key file; a key file that is a
    symlink, or a directory another user owns, is refused.
    """
    path = key_file()
    parent = path.parent
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise OSError(f"refusing to write the key through the symlink {path}")
    info = parent.stat()
    if info.st_uid != os.getuid():
        raise OSError(f"refusing to write the key into {parent}: another "
                      f"user owns it")
    if info.st_mode & 0o077:
        parent.chmod(0o700)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(f"{KEY_VARIABLE}={key}\n")
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


class KeyNotGranted(RuntimeError):
    """Zotero did not grant a usable local API key; the message says what,
    if anything, the refused operation had already stored."""


NOTHING_WRITTEN = "nothing was written"

# A batch stops at the first key Zotero did not grant: asking again per row
# would open one more dialog, and wait AUTHORIZE_WAIT, for each.
KEY_NOT_ATTEMPTED = "not attempted after Zotero granted no key"


def authorize(z: zotero.Zotero, *, saved: str | None = None) -> None:
    """Ask Zotero for a key through its Allow / Always Allow / Deny dialog,
    awaited AUTHORIZE_WAIT seconds, before anything is sent with it.

    Only a key granted with "Always Allow" is accepted, and stored: storing
    a file takes three keyed writes and a batch one per write, which a
    one-time "Allow" key cannot carry. `saved` is what the operation had
    already stored, for the messages.
    """
    done = saved or NOTHING_WRITTEN
    asker = zotero.Zotero(z.library_id, z.library_type.rstrip("s"), local=True,
                          client=http_client(AUTHORIZE_WAIT))
    asker.endpoint = z.endpoint
    try:
        with local_api():
            granted = asker.authorize_local(APP_NAME)
    except ZoteroSlow as exc:
        # Zotero is up; its dialog was not answered in time.
        raise KeyNotGranted(f"Zotero gave no local API key: its dialog went "
                            f"unanswered for {AUTHORIZE_WAIT:.0f} s; {done}"
                            ) from exc
    except ZoteroUnavailable as exc:
        raise KeyNotGranted(f"Zotero gave no local API key within "
                            f"{AUTHORIZE_WAIT:.0f} s ({exc}); {done}") from exc
    except LocalAPIError as exc:
        raise KeyNotGranted(f"Zotero refused a local API key ({exc}); "
                            f"{done}") from exc
    accept_key(z, granted, saved=saved)


def accept_key(z: zotero.Zotero, granted: dict[str, Any], *,
               saved: str | None = None) -> None:
    """Take Zotero's answer {"key", "remember"}: an "Always Allow" key is
    handed to `z` and kept on disk; a one-time "Allow" key is refused."""
    if not granted.get("remember"):
        raise KeyNotGranted(
            f'Zotero granted a one-time key ("Allow"); the helper accepts only '
            f'a key granted with "Always Allow". Rerun and answer "Always '
            f'Allow"; {saved or NOTHING_WRITTEN}')
    z.local_api_key = granted["key"]
    try:
        store_key(granted["key"])
    except OSError as exc:
        # The key still serves this run; Zotero asks again next time.
        print(f"zotero.py: the granted key was not kept ({exc}); Zotero "
              f"will ask again on the next run", file=sys.stderr)


def write(z: zotero.Zotero, call: Any, *, saved: Any = lambda: None) -> Any:
    """Run one pyzotero write operation, with the stored key or one asked
    for before anything is sent.

    A 401 can still come part-way (a stored key Zotero no longer honours):
    the key is asked for once more and the call retried. `saved()` then says
    what the attempt had stored, None for nothing, and the messages repeat
    it.
    """
    if not z.local_api_key:
        z.local_api_key = stored_key()
    if not z.local_api_key:
        authorize(z)
    for attempt in (1, 2):
        try:
            with local_api():
                return call()
        except ze.LocalAPIKeyRequiredError as exc:
            done = saved()
            if attempt == 2:
                raise KeyNotGranted(f"Zotero refused the new local API key "
                                    f"({exc}); {done or NOTHING_WRITTEN}"
                                    ) from exc
            authorize(z, saved=done)
    return None


def create_item(z: zotero.Zotero, item: dict[str, Any],
                collection: str | None) -> str:
    """Create one item, in `collection` when given; its key."""
    payload = {**item, "collections": [collection] if collection else []}
    result = write(z, lambda: z.create_items([payload]))
    if not result.get("successful"):
        failed = next(iter((result.get("failed") or {}).values()), {})
        raise LocalAPIError(f"Zotero did not create the item: "
                            f"{failed.get('message', result)}")
    return next(iter(result["successful"].values()))["key"]


def attach_file(z: zotero.Zotero, parent: str, path: Path) -> str:
    """Store a copy of `path` under item `parent`; the attachment's key.

    pyzotero records the attachment's key in `attachment` once Zotero has
    created it, and a retry with that key resumes at the upload instead of
    creating a second attachment.
    """
    attachment = {"itemType": "attachment", "linkMode": "imported_file",
                  "title": path.name, "filename": str(path.resolve()),
                  "contentType": mimetypes.guess_type(path.name)[0]
                  or "application/octet-stream",
                  "tags": [], "relations": {}}

    def saved() -> str | None:
        if not attachment.get("key"):
            return None
        return (f"attachment {attachment['key']} was created under {parent} "
                f"and may lack its file; check it in Zotero")

    try:
        result = write(z, lambda: z.upload_attachments([attachment],
                                                       parentid=parent),
                       saved=saved)
    except (ZoteroUnavailable, ZoteroSlow) as exc:
        if done := saved():
            raise type(exc)(f"{exc}; {done}") from exc
        raise
    except OSError as exc:
        done = saved()
        raise LocalAPIError(f"could not read {path}: {exc}"
                            + (f"; {done}" if done else "")) from exc
    if result.get("failure") or not result.get("success"):
        raise LocalAPIError(f"Zotero did not store {path.name}: {result}")
    return result["success"][0]["key"]


def library_ids(library: str = USER_LIBRARY) -> list[str]:
    """The libraries a selector names: "user" is the signed-in user's
    library, a number is a groupID (as in zotero.org/groups/<groupID>),
    "all" is the user library and every group."""
    if library == ALL_LIBRARIES:
        z = local_library()
        with local_api():
            groups = z.groups()
        return [USER_LIBRARY] + [str(g["id"]) for g in groups]
    if str(library).isdigit():
        return [str(library)]
    if library != USER_LIBRARY:
        raise ValueError(f"--library {library!r}: use 'user', 'all' or a groupID")
    return [USER_LIBRARY]


def library_lock_dir() -> Path:
    """The directory whose flock serialises this user's check-and-create runs:
    the per-user runtime directory, else the home directory, never a shared
    temp directory other users lock too."""
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if runtime and Path(runtime).is_dir():
        return Path(runtime)
    return Path.home()


def has_collection(library: str, key: str) -> bool:
    try:
        with local_api():
            local_library(library).collection(key)
    except ze.ResourceNotFoundError:
        return False
    return True


def resolve_target(library: str, collection: str | None) -> str:
    """The library new items land in.

    A collection key names its own library; otherwise the library selector
    does, the user library by default. "all" names no single destination.
    """
    if library == ALL_LIBRARIES and not collection:
        raise ValueError("--library all names no single destination library")
    if not collection:
        (lib_id,) = library_ids(library)
        return lib_id
    homes = [lib for lib in library_ids(ALL_LIBRARIES)
             if has_collection(lib, collection)]
    if not homes:
        raise ValueError(f"collection {collection!r} is in no local library")
    if len(homes) > 1:
        raise ValueError(f"collection key {collection!r} exists in several "
                         f"libraries ({', '.join(homes)})")
    return homes[0]


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


def cmd_create_items(args: argparse.Namespace) -> int:
    entries = load_entries(args)
    # check-staging --apply holds the lock and has made Zotero answer.
    locked = getattr(args, "_locked", False)
    library = getattr(args, "library", USER_LIBRARY)
    collection = getattr(args, "collection", None)
    try:
        if not locked:
            ensure_zotero()
        owned = schema_fields(local_library())
        items = [entry_to_zotero_item(e, owned) for e in entries]
    except ZoteroUnavailable as exc:
        print(f"create-items: {exc}", file=sys.stderr)
        emit_json(unavailable_payload(exc))
        return EXIT_UNAVAILABLE
    except ZoteroSlow as exc:
        print(f"create-items: {exc}", file=sys.stderr)
        emit_json(slow_payload(exc))
        return EXIT_SLOW
    except (LocalAPIError, ValueError) as exc:
        print(f"create-items: {exc}", file=sys.stderr)
        emit_json({"error": str(exc)})
        return 1
    if args.dry_run:
        emit_json({"items": items})
        return 0
    # The duplicate checks and the saves happen inside one critical section
    # on this machine, so two local runs cannot both create one work.
    lock = (contextlib.nullcontext() if locked
            else directory_locks([library_lock_dir()]))
    with contextlib.ExitStack() as held:
        try:
            held.enter_context(lock)
        except OSError as exc:  # another run held the lock too long
            emit_json({"error": str(exc)})
            return 1
        try:
            lib_id = resolve_target(library, collection)
        except ZoteroUnavailable as exc:
            emit_json(unavailable_payload(exc))
            return EXIT_UNAVAILABLE
        except ZoteroSlow as exc:
            emit_json(slow_payload(exc))
            return EXIT_SLOW
        except (ValueError, LocalAPIError, OSError) as exc:
            emit_json({"error": str(exc)})
            return 1
        results, status = create_entries(entries, items, lib_id,
                                         collection, getattr(args, "force",
                                                             False))
    zotero_state = {EXIT_SLOW: "slow", EXIT_UNAVAILABLE: "unavailable"}
    emit_json({"library_id": lib_id, "collection": collection,
               "zotero": zotero_state.get(status, zotero_url()),
               "results": results})
    return status


def entry_query(entry: dict[str, Any]) -> dict[str, Any]:
    """find_work's keys for one create-items entry."""
    url = str(entry.get("url") or "")
    arxiv_match = ARXIV_ANY_RE.search(url)
    handle_match = HDL_ANY_RE.search(url)
    return {"title": entry.get("title"), "doi": entry.get("doi"),
            "isbn": entry.get("isbn"),
            "item_type": entry.get("type") or ENTRY_TYPE_DEFAULT,
            "arxiv": arxiv_match.group(1) if arxiv_match else None,
            "handle": handle_match.group(1) if handle_match else None}


def create_entries(entries: list[dict[str, Any]], items: list[dict[str, Any]],
                   lib_id: str,
                   collection: str | None,
                   force: bool) -> tuple[list[dict[str, Any]], int]:
    """Look each entry up in the destination library, then save it, one at a
    time: the lookups are live, so an entry for a work an earlier entry of
    the same batch just created finds it and is refused."""
    results: list[dict[str, Any]] = [{"title": entry.get("title")}
                                     for entry in entries]
    z = local_library(lib_id)
    status = 0
    # Zotero has no search by md5: a file this batch already stored is
    # remembered here, so a second entry carrying it is refused.
    stored: dict[str, int] = {}

    def stop(after: int, why: str) -> None:
        for row in results[after + 1:]:
            if "error" not in row:
                row["error"] = why

    for n, entry in enumerate(entries):
        row = results[n]
        pdf = Path(entry["pdf"]) if entry.get("pdf") else None
        if not force and (pdf is None or not pdf.is_file()):
            row["error"] = "no readable PDF for duplicate guard; use --force"
            status = 1
            continue
        if entry.get("attach_pdf") and pdf is not None and not pdf.is_file():
            # --force skips the duplicate guard, not the file to store.
            row["error"] = f"PDF to attach not found: {pdf}"
            status = 1
            continue
        # Only a file this entry stores; a PDF used as evidence alone is not.
        digest = (file_md5(pdf) if entry.get("attach_pdf") and pdf is not None
                  and pdf.is_file() else None)
        if not force and digest in stored:
            row["error"] = (f"same file as entry {stored[digest]} of this "
                            f"batch; use --force")
            status = 1
            continue
        if not force:
            try:
                found = find_work([(lib_id, z)], pdf_path=pdf,
                                  **entry_query(entry))
            except (ZoteroUnavailable, ZoteroSlow, LocalAPIError) as exc:
                row["error"] = f"duplicate guard could not look: {exc}"
                stop(n, "not attempted after the duplicate guard failed")
                # 74/75 say "nothing was done": only true before any save.
                if any(r.get("status") == "created" for r in results):
                    return results, 1
                return results, (EXIT_SLOW if isinstance(exc, ZoteroSlow)
                                 else EXIT_UNAVAILABLE
                                 if isinstance(exc, ZoteroUnavailable) else 1)
            if found["matches"]:
                row["error"] = "already in the library: duplicate match"
                row["matches"] = found["matches"][:5]
                status = 1
                continue
            if found["candidates"]:
                # Never judged here: the caller looks, then passes --force.
                row["error"] = ("works with this title are in the library; "
                                "examine the candidates, then use --force")
                row["candidates"] = found["candidates"][:5]
                status = 1
                continue
            if not set(KEYS) & set(found["consulted"]):
                row["error"] = ("insufficient work identity for duplicate "
                                "guard; use --force")
                status = 1
                continue
        try:
            row["key"] = create_item(z, items[n], collection)
            row["status"] = "created"
            if digest:
                stored[digest] = n
        except (ZoteroUnavailable, ZoteroSlow, LocalAPIError,
                KeyNotGranted) as exc:
            # A save that failed in transit may still have reached Zotero.
            # Stop here: the next run reads the library again, live, and
            # sees the item if it was created.
            row["error"] = (f"create outcome unknown: {exc}"
                            if isinstance(exc, (ZoteroUnavailable, ZoteroSlow))
                            else f"not created: {exc}")
            stop(n, "not attempted after a failed save")
            return results, 1
        if entry.get("attach_pdf") and entry.get("pdf"):
            pdf = Path(entry["pdf"])
            try:
                attach_file(z, row["key"], pdf)
                row["attachment"] = pdf.name
            except (ZoteroUnavailable, ZoteroSlow) as exc:
                row["transport_error"] = (f"created, then Zotero stopped "
                                          f"answering: {exc}")
                stop(n, "not attempted after Zotero stopped")
                return results, 1
            except (LocalAPIError, KeyNotGranted) as exc:
                row["attachment_error"] = str(exc)
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


def find_item(item_key: str, library: str = USER_LIBRARY
              ) -> tuple[zotero.Zotero, dict[str, Any]] | None:
    """(client of its library, item JSON) for a key, None when absent."""
    for lib_id in library_ids(library):
        z = local_library(lib_id)
        try:
            with local_api():
                return z, z.item(item_key)
        except ze.ResourceNotFoundError:
            continue
    return None


def item_fields(z: zotero.Zotero, item: dict[str, Any]) -> dict[str, Any]:
    """An item's fields as Zotero names them: every field its type owns,
    empty when unset, so plan_enrichment can tell "empty" from "this type
    has no such field" (the item JSON omits empty fields)."""
    data = item.get("data", {})
    with local_api():
        fields = z.item_type_fields(data.get("itemType", ""))
    out: dict[str, Any] = {f["field"]: "" for f in fields if "field" in f}
    out.update({k: v for k, v in data.items() if k in out})
    out.update({"key": item.get("key"), "itemType": data.get("itemType")})
    return out


# Bookkeeping item_fields adds; never a field to edit.
NOT_FIELDS = {"key", "itemType"}


def enrich_one(job: dict[str, Any], overwrite: bool, edit: bool,
               library: str = USER_LIBRARY) -> dict[str, Any]:
    """Suggest field edits on ONE existing item; write them with `edit`.
    See plan_enrichment for the guards."""
    item_key = job["item_key"]
    row: dict[str, Any] = {"itemKey": item_key}
    found = find_item(item_key, library)
    if found is None:
        row["status"] = "not found"
        return row
    z, item = found
    data = item_fields(z, item)
    row["title"] = data.get("title")
    sets = {f: v for f, v in job["set"].items() if f not in NOT_FIELDS}
    patch, refusals = plan_enrichment(data, sets, job["expect_title"], overwrite)
    refusals += [f"{f}: not an item field" for f in job["set"] if f in NOT_FIELDS]
    if refusals:
        row["refused"] = refusals
    row["suggested"] = [{"itemKey": item_key, "field": field,
                         "old": data.get(field) or "", "new": value}
                        for field, value in patch.items()]
    row["status"] = "suggested" if patch else "nothing to change"
    if edit and patch:
        try:
            write(z, lambda: z.update_item({**item["data"], **patch}))
            row["status"] = "written"
        except LocalAPIError as exc:
            row["status"] = "not written"
            row["error"] = str(exc)
        except KeyNotGranted as exc:
            row.update(status="not written", error=str(exc))
            exc.row = row  # run_jobs reports it and stops the batch
            raise
    return row


def cmd_suggest_edits(args: argparse.Namespace) -> int:
    """Report the edits; write them only with --edit."""
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

    def run() -> dict[str, Any]:
        return {"results": run_jobs(
            jobs, lambda j: enrich_one(j, args.overwrite, args.edit,
                                       args.library),
            wrote=args.edit)}

    out, rc = with_zotero("suggest-edits", run)
    if rc is not None:
        return rc
    emit_json({"zotero": zotero_url(), "source": LIBRARY_SOURCE,
               "edit": args.edit,
               **({} if args.edit else {"apply": EDIT_HINT}), **out})
    return enrich_status(out["results"])


EDIT_HINT = "report only: rerun with --edit to write, or edit by hand in Zotero"


def run_jobs(jobs: list[dict[str, Any]], one: Any,
             wrote: bool) -> list[dict[str, Any]]:
    """`one(job)` for each job, in order. When Zotero goes away part-way
    through a run that writes, the rows already done are kept, the job in
    flight is marked unknown and the rest not attempted; a read-only run
    has done nothing, so ZoteroUnavailable (exit 75) and ZoteroSlow (exit
    74) pass through. A key
    Zotero did not grant stops the run too: the rest are not attempted."""
    results: list[dict[str, Any]] = []
    for n, job in enumerate(jobs):
        try:
            results.append(one(job))
        except KeyNotGranted as exc:
            results.append(getattr(exc, "row", None) or {
                "itemKey": job["item_key"], "status": "not written",
                "error": str(exc)})
            results += [{"itemKey": rest["item_key"], "status": "not attempted",
                         "error": KEY_NOT_ATTEMPTED} for rest in jobs[n + 1:]]
            break
        except (ZoteroUnavailable, ZoteroSlow) as exc:
            if not wrote:
                raise
            results.append({"itemKey": job["item_key"], "status": "unknown",
                            "error": f"write outcome unknown: {exc}"})
            results += [{"itemKey": rest["item_key"], "status": "not attempted",
                         "error": "not attempted after Zotero stopped"}
                        for rest in jobs[n + 1:]]
            break
    return results


def enrich_status(results: list[dict[str, Any]]) -> int:
    """Exit code for a suggest-edits run. Non-zero when anything asked for cannot
    be suggested or written — a refusal or a missing item included. A run
    that refused every field and one that suggested every field must not
    return the same code, or the caller cannot tell "ready" from "declined
    to act".
    """
    ok = {"suggested", "nothing to change", "written"}
    return int(any(row.get("refused") or row.get("status") not in ok
                   for row in results))


# --- CLI -------------------------------------------------------------------

def with_zotero(command: str, read: Any) -> tuple[Any, int | None]:
    """Run `read()` against a Zotero made to answer: (result, None), or
    (None, exit status) after printing why nothing was done."""
    try:
        ensure_zotero()
        return read(), None
    except ZoteroUnavailable as exc:
        print(f"{command}: {exc}", file=sys.stderr)
        emit_json(unavailable_payload(exc))
        return None, EXIT_UNAVAILABLE
    except ZoteroSlow as exc:
        print(f"{command}: {exc}", file=sys.stderr)
        emit_json(slow_payload(exc))
        return None, EXIT_SLOW
    except (LocalAPIError, ValueError) as exc:
        print(f"{command}: {exc}", file=sys.stderr)
        emit_json({"error": str(exc), "verdict": "unchecked"})
        return None, 1


def cmd_extract_metadata(args: argparse.Namespace) -> int:
    """What each PDF says about itself. Input-format dependent (PDF), and
    never contacts Zotero: its output is find-work's input."""
    out: list[dict[str, Any]] = []
    for pdf_arg in args.pdf:
        pdf = Path(pdf_arg)
        if not pdf.is_file():
            out.append({"pdf": str(pdf), "error": "not found"})
            continue
        try:
            out.append(extract_one(pdf))
        except Exception as exc:
            out.append({"pdf": str(pdf), "error": f"{type(exc).__name__}: {exc}"})
    emit_json({"items": out})
    return int(any("error" in row for row in out))


# ---------------------------------------------------------------------------
# The library, as Zotero's own search answers
#
# find-work, check-staging and create-items ask Zotero's search for each
# key; report-duplicates, a report on the whole library, reads the
# attachments once. Nothing is written to disk, so there is no cache to go
# stale and nothing to rebuild.
#
# Content identity is the strongest key: it survives renaming, re-filing and
# metadata drift. Zotero 10 reports each stored file's md5, which is compared
# with the staged file's for every work the search found; Zotero offers no search
# by md5, so a stored copy under a work no other key finds goes unseen.
# ---------------------------------------------------------------------------

LIBRARY_SOURCE = "zotero local API (live)"
# A title with fewer words of three letters or more is not searched: its
# hits would be any work at all, and the key could vouch for nothing.
TITLE_MIN_WORDS = 3
# Title candidates returned per query: one page, never the whole library.
CANDIDATES = 25
WORK_FIELDS = ("title", "date", "DOI", "ISBN", "url", "extra", "archiveID",
               "number")


def file_url_path(url: str | None) -> str | None:
    """Local path of a file:// URL, None for anything else."""
    if not url:
        return None
    parts = urllib.parse.urlsplit(url)
    # A host in the URL (file://server/share) is not a path on this machine.
    if parts.scheme != "file" or parts.netloc not in ("", "localhost"):
        return None
    return urllib.request.url2pathname(parts.path)


def _attachment_record(item: dict[str, Any], lib_id: str) -> dict[str, Any]:
    """What identifies an attachment's file: its md5 (Zotero 10 reports it
    for a stored file), its size and its path (`links.enclosure`; a linked
    file's absolute `data.path`)."""
    data = item.get("data", {})
    link = data.get("linkMode") or ""
    enclosure = item.get("links", {}).get("enclosure") or {}
    path = file_url_path(enclosure.get("href"))
    raw = data.get("path") or ""
    if link == "linked_file" and raw and Path(raw).is_absolute():
        path = raw
    return {"key": item["key"], "parent": data.get("parentItem") or None,
            "title": data.get("title") or "",
            "filename": data.get("filename") or Path(raw.partition(":")[2]
                                                      or raw).name,
            "md5": (data.get("md5") or "").lower() or None,
            "size": enclosure.get("length"), "path": path,
            "contentType": data.get("contentType") or "", "linkMode": link,
            "library": lib_id}


def work_record(item: dict[str, Any], lib_id: str) -> dict[str, Any]:
    data = item.get("data", {})
    return {"key": item["key"], "itemType": data.get("itemType", ""),
            "creators": [c.get("lastName") or c.get("name") or ""
                         for c in data.get("creators", [])
                         if c.get("lastName") or c.get("name")],
            "library": lib_id,
            **{f: str(data.get(f) or "") for f in WORK_FIELDS}}


def libraries(library: str = USER_LIBRARY) -> list[tuple[str, zotero.Zotero]]:
    """(library id, client) for each library a selector names."""
    return [(lib_id, local_library(lib_id)) for lib_id in library_ids(library)]


def search_works(z: zotero.Zotero, lib_id: str, query: str,
                 limit: int | None = None) -> list[dict[str, Any]]:
    """Top-level works matching `query` in any field or creator, through
    Zotero's quick search (`qmode=everything`); trash excluded. Every page,
    or the first `limit` hits."""
    with local_api():
        first = z.top(q=query, qmode="everything", limit=limit or PAGE)
        items = first if limit else z.everything(first)
    return [work_record(i, lib_id) for i in items
            if i.get("data", {}).get("itemType") not in NOT_WORKS
            and not i.get("data", {}).get("parentItem")]


def works_by_key(z: zotero.Zotero, lib_id: str, keys: set[str]
                 ) -> dict[str, dict[str, Any]]:
    """The works among `keys` that exist and are not trashed."""
    found: dict[str, dict[str, Any]] = {}
    ordered = sorted(keys)
    for start in range(0, len(ordered), 50):
        chunk = ",".join(ordered[start:start + 50])
        with local_api():
            items = z.everything(z.items(itemKey=chunk, limit=PAGE))
        found.update({i["key"]: work_record(i, lib_id) for i in items
                      if i.get("data", {}).get("itemType") not in NOT_WORKS})
    return found


def file_evidence(z: zotero.Zotero, lib_id: str, key: str,
                  digest: str | None) -> tuple[dict[str, bool],
                                               dict[str, Any] | None]:
    """Whether a work holds a stored file (a PDF), and its attachment whose
    md5 is `digest`. A stored file counts only when Zotero shows one, its
    md5 or its size: the enclosure URL alone is sent for every stored-file
    attachment, one created without its file included."""
    with local_api():
        children = z.everything(z.children(key, limit=PAGE))
    atts = [_attachment_record(c, lib_id) for c in children
            if c.get("data", {}).get("itemType") == "attachment"]
    stored = [a for a in atts if a["linkMode"].startswith("imported")
              and (a["md5"] or a["size"] is not None)]
    same = next((a for a in atts if digest and a["md5"] == digest), None)
    return ({"has_file": bool(stored),
             "has_pdf": any(a["contentType"] == "application/pdf"
                            for a in stored)}, same)


# A user id no account has: the local API refuses it and names the real one.
_FOREIGN_USER = "999999999999"


def local_account() -> str | None:
    """The zotero.org user id the client is signed in as, None if none.

    The local API is asked for another user's data, which it refuses with
    "use userID 0 or <id>" naming the signed-in account, or "use userID 0"
    alone when no one is signed in; the opt-in check then refuses: it fails
    closed.
    """
    z = zotero.Zotero(_FOREIGN_USER, "user", local=True, client=http_client())
    z.endpoint = f"{zotero_base()}/api"
    try:
        with local_api():
            z.settings()
    except LocalAPIError as exc:
        text = str(exc.__cause__ or exc)
        if "use userID 0" not in text:
            raise
        match = re.search(r"use userID 0 or (\d+)", text)
        return match.group(1) if match else None
    raise LocalAPIError("the local API served another user's data; "
                        "cannot tell the signed-in account")


def file_md5(path: Path) -> str:
    with path.open("rb") as fh:
        return hashlib.file_digest(fh, "md5").hexdigest()


@contextlib.contextmanager
def directory_locks(directories: list[Path], wait: float = LOCK_WAIT):
    """One advisory flock per directory, in stable order.

    The lock is taken on the directory itself, so it leaves no file behind
    and dies with the process. A lock not obtained within `wait` seconds
    raises OSError rather than hang an unattended run.
    """
    with contextlib.ExitStack() as stack:
        for directory in sorted({Path(d).resolve() for d in directories}):
            if not directory.is_dir():
                continue
            fd = os.open(directory, os.O_RDONLY)
            stack.callback(os.close, fd)
            deadline = time.monotonic() + wait
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise OSError(f"{directory} is locked by another run "
                                      f"for over {wait:.0f} s") from None
                    time.sleep(0.2)
            stack.callback(fcntl.flock, fd, fcntl.LOCK_UN)
        yield


def fold(s: str | None) -> str:
    """Accent-, case- and punctuation-insensitive form, words single-spaced."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.findall(r"[^\W_]+", s.casefold()))


# Both forms Zotero actually stores: "arXiv:2401.01234" in Extra, and an
# arxiv.org/abs/ URL in the url field.
ARXIV_ANY_RE = re.compile(
    r"(?:arxiv\.org/(?:abs|pdf)/|arxiv[:\s]\s*)"
    r"((?:\d{4}\.\d{4,5})|(?:[a-z-]+/\d{7}))",
    re.IGNORECASE)
HDL_ANY_RE = re.compile(r"hdl\.handle\.net/([^\s)\]]+)", re.IGNORECASE)


def normal_doi(raw: str | None) -> str:
    return re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "",
                  (raw or "").strip(), flags=re.IGNORECASE).strip().lower()


def isbn13s(raw: str | None) -> set[str]:
    """Every valid ISBN in `raw`, as ISBN-13 (isbnlib checks the digit)."""
    return {code for code in (isbnlib.to_isbn13(isbnlib.canonical(c))
                              for c in isbnlib.get_isbnlike(raw or ""))
            if code}


def isbn_queries(isbn: str) -> list[str]:
    """The spellings of one ISBN a Zotero field may hold: 13 and 10 digits,
    bare and hyphenated (Zotero's search matches the stored text)."""
    forms: set[str] = set()
    for code13 in isbn13s(isbn):
        for code in (code13, isbnlib.to_isbn10(code13)):
            if code:
                forms |= {code, isbnlib.mask(code) or code}
    return sorted(forms)


def normal_arxiv(raw: str) -> str:
    """An arXiv id, from a bare id, `arXiv:` form or arxiv.org URL, without
    its version suffix; "" when there is none."""
    match = ARXIV_ANY_RE.search(raw) or re.fullmatch(
        r"\s*((?:\d{4}\.\d{4,5})|(?:[a-z-]+/\d{7}))(?:v\d+)?\s*", raw,
        re.IGNORECASE)
    return match.group(1).lower() if match else ""


def handle_path(raw: str) -> str:
    match = HDL_ANY_RE.search(raw)
    return (match.group(1) if match else raw).lower().rstrip("/")


def extra_lines(extra: str, label: str) -> list[str]:
    """The values of `label:` lines in an Extra field, the form Zotero (and
    create-items) store an identifier a type has no field for in. A DOI
    elsewhere in Extra ("Comment on 10.1234/x") is another work's."""
    return [m.group(1) for m in re.finditer(
        rf"(?im)^\s*{label}:\s*(.+?)\s*$", extra or "")]


ARXIV_URL_RE = re.compile(r"https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/\S+",
                          re.IGNORECASE)
HANDLE_URL_RE = re.compile(r"https?://hdl\.handle\.net/\S+", re.IGNORECASE)


def first_token(value: str) -> str:
    return (value.split() or [""])[0]


# A part of a volume carries the volume's ISBN, which identifies the volume,
# not the part: another chapter of the same book is not this work.
ISBN_OF_A_VOLUME = {"bookSection", "conferencePaper", "encyclopediaArticle",
                    "dictionaryEntry"}

# Each identifier key: the queries to send Zotero, and the check that a
# returned work's own field carries the identifier (the quick search matches
# a substring in any field, an abstract citing the DOI included).
IDENTIFIER_KEYS: tuple[tuple[str, Any, Any], ...] = (
    ("doi", lambda v: [d for d in [normal_doi(v)] if DOI_BARE_RE.fullmatch(d)],
     lambda w, v: normal_doi(v) in {
         normal_doi(first_token(d))
         for d in [w["DOI"], *extra_lines(w["extra"], "DOI")] if d}),
    ("isbn", isbn_queries,
     lambda w, v: w["itemType"] not in ISBN_OF_A_VOLUME and bool(
         isbn13s(v) & isbn13s(" ".join([w["ISBN"],
                                        *extra_lines(w["extra"], "ISBN")])))),
    ("arxiv", lambda v: [a for a in [normal_arxiv(v)] if a],
     lambda w, v: normal_arxiv(v) in {
         normal_arxiv(first_token(a))
         for a in [*extra_lines(w["extra"], "arXiv"), w["archiveID"],
                   w["url"] if ARXIV_URL_RE.fullmatch(w["url"]) else ""]
         if a} - {""}),
    ("handle", lambda v: [h for h in [handle_path(v)]
                          if re.fullmatch(r"[^\s/:]+/\S+", h)],
     lambda w, v: bool(HANDLE_URL_RE.fullmatch(w["url"]))
     and handle_path(v) == handle_path(w["url"])),
)


KEYS = ("doi", "isbn", "arxiv", "handle", "title")


def find_work(libs: list[tuple[str, zotero.Zotero]], *,
              doi: str | None = None, isbn: str | None = None,
              arxiv: str | None = None, handle: str | None = None,
              title: str | None = None, item_type: str | None = None,
              pdf_path: Path | None = None,
              isbn_unusable: str | None = None) -> dict[str, Any]:
    """Is this work in the libraries? Zotero's own search, key by key.

    `matches` are the works whose own field carries a given identifier
    (DOI, ISBN, arXiv id, handle), or that hold a stored copy of `pdf_path`
    (`storageHash`): the only matches asserted. `candidates` are what
    Zotero's search returns for the title, for the caller to judge; they
    are never a match unless their stored file is `pdf_path` itself.
    "consulted" and "skipped" keep a clean negative apart from a lookup
    that could not run. `isbn_unusable`, a reason, skips the ISBN.
    """
    consulted: list[str] = []
    skipped: list[str] = []
    found: dict[str, dict[str, Any]] = {}
    owner: dict[str, tuple[str, zotero.Zotero]] = {}

    def emit(work: dict[str, Any], why: str,
             lib: tuple[str, zotero.Zotero]) -> None:
        if work["key"] in found:
            if why != "title" and why not in found[work["key"]]["why"]:
                found[work["key"]]["why"].append(why)
            return
        owner[work["key"]] = lib
        found[work["key"]] = {
            "key": work["key"], "why": [why], "title": work["title"],
            "date": work["date"], "itemType": work["itemType"],
            "creators": work["creators"], "library": work["library"],
            "attachment": None}

    for label, queries, carries in IDENTIFIER_KEYS:
        supplied = {"doi": doi, "isbn": isbn, "arxiv": arxiv,
                    "handle": handle}[label]
        if not supplied:
            skipped.append(f"{label} (none supplied)")
            continue
        if label == "isbn" and item_type in ISBN_OF_A_VOLUME:
            # A chapter's ISBN is its book's: the book is not this work.
            skipped.append(f"isbn (the volume's, for a {item_type})")
            continue
        if label == "isbn" and isbn_unusable:
            skipped.append(f"isbn ({isbn_unusable})")
            continue
        sent = queries(supplied)
        if not sent:
            # Nothing to send (an ISBN with a bad check digit): not looked up.
            skipped.append(f"{label} (not a valid {label}: {supplied})")
            continue
        consulted.append(label)
        for lib in libs:
            for query in sent:
                for work in search_works(lib[1], lib[0], query):
                    if carries(work, supplied):
                        emit(work, label, lib)

    words = re.findall(r"[^\W_]{3,}", title or "")
    if not title:
        skipped.append("title (none supplied)")
    elif len(words) < TITLE_MIN_WORDS:
        skipped.append(f"title (fewer than {TITLE_MIN_WORDS} words to search)")
    else:
        consulted.append("title")
        # Words, not the title string: the quick search wants every word
        # somewhere, and punctuation would glue a word to its neighbour.
        for lib in libs:
            for work in search_works(lib[1], lib[0], " ".join(words),
                                     limit=CANDIDATES):
                emit(work, "title", lib)

    digest = file_md5(pdf_path) if pdf_path and pdf_path.is_file() else None
    if digest is None:
        skipped.append("storageHash (no file on disk)")
    elif not found:
        skipped.append("storageHash (no work found to compare with)")
    else:
        consulted.append("storageHash")
    for key, hit in found.items():
        lib_id, z = owner[key]
        evidence, same = file_evidence(z, lib_id, key, digest)
        hit.update(evidence)
        if same:
            hit.update(why=["storageHash"] + hit["why"], attachment=same)
    matches = [h for h in found.values() if h["why"] != ["title"]]
    candidates = [h for h in found.values() if h["why"] == ["title"]]
    matches.sort(key=lambda m: "storageHash" not in m["why"])
    verdict = (classify_matches(matches, candidates) if consulted
               else "unchecked")
    return {"matches": matches, "candidates": candidates, "verdict": verdict,
            "consulted": consulted, "skipped": skipped,
            "source": LIBRARY_SOURCE}


class BadQuery(ValueError):
    """find-work's input cannot say which works to look up."""


def work_queries(args: argparse.Namespace) -> list[dict[str, Any]]:
    """The works to look up: each item of extract-metadata's output
    (--metadata, a file or - for stdin), else one work from the flags. A
    flag overrides the extracted value, so a refined title replaces the
    pdfinfo one; that needs a metadata file of one work, since flags
    applied to several would describe them all as one. An extraction row
    with an error stays in the results, as an error."""
    flags = {"title": args.title, "doi": args.doi, "isbn": args.isbn,
             "arxiv": args.arxiv, "handle": args.handle, "pdf": args.pdf,
             "type": getattr(args, "type", None)}
    if not args.metadata:
        return [flags]
    try:
        text = (sys.stdin.read() if args.metadata == "-"
                else Path(args.metadata).read_text(encoding="utf-8"))
        items = json.loads(text)["items"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BadQuery(f"--metadata {args.metadata}: not extract-metadata "
                       f"output ({type(exc).__name__}: {exc})") from exc
    if not isinstance(items, list) or not items:
        raise BadQuery(f"--metadata {args.metadata}: no work to look up")
    overrides = sorted(k for k, v in flags.items() if v)
    if overrides and len(items) > 1:
        raise BadQuery(f"--{', --'.join(overrides)} would describe all "
                       f"{len(items)} works of --metadata as one; give a "
                       f"metadata file of one work, or no flag")
    works = []
    for item in items:
        if not isinstance(item, dict):
            raise BadQuery(f"--metadata {args.metadata}: an item is not an "
                           f"object")
        if "error" in item:
            works.append({"error": item["error"], "pdf": item.get("pdf")})
            continue
        ids = item.get("identifiers") or {}
        pdfinfo_fields = item.get("pdfinfo") or {}
        if not (isinstance(ids, dict) and isinstance(pdfinfo_fields, dict)):
            raise BadQuery(f"--metadata {args.metadata}: identifiers and "
                           f"pdfinfo must be objects")
        work = {"title": pdfinfo_fields.get("Title"), "pdf": item.get("pdf"),
                "type": None,
                **{k: ids.get(k) for k in ("doi", "isbn", "arxiv", "handle")}}
        work.update({k: v for k, v in flags.items() if v})
        works.append(work)
    return works


def cmd_find_work(args: argparse.Namespace) -> int:
    """Is this work already in the library? Local API only."""
    try:
        works = work_queries(args)
    except BadQuery as exc:
        print(f"find-work: {exc}", file=sys.stderr)
        emit_json({"error": str(exc), "verdict": "unchecked"})
        return 1
    if all("error" in work for work in works):
        # Nothing to look up: Zotero is neither asked nor launched.
        emit_json({"results": [{"query": {"pdf": w["pdf"]}, "error": w["error"],
                                "verdict": "unchecked"} for w in works]})
        return 1

    def look_up(libs: list[tuple[str, zotero.Zotero]],
                work: dict[str, Any]) -> dict[str, Any]:
        if "error" in work:
            return {"query": {"pdf": work["pdf"]}, "error": work["error"],
                    "verdict": "unchecked"}
        return {"query": {k: v for k, v in work.items() if v},
                **find_work(libs, doi=work["doi"], isbn=work["isbn"],
                            arxiv=work["arxiv"], handle=work["handle"],
                            title=work["title"], item_type=work["type"],
                            pdf_path=Path(work["pdf"]) if work["pdf"] else None)}

    def look() -> list[dict[str, Any]]:
        libs = libraries(args.library)
        return [look_up(libs, work) for work in works]

    results, rc = with_zotero("find-work", look)
    if rc is not None:
        return rc
    emit_json({"zotero": zotero_url(), "source": LIBRARY_SOURCE,
               "library": args.library, "results": results})
    return int(any("error" in r for r in results))


def write_report_file(output: Path, body: str) -> None:
    """Write a report readable by its owner only."""
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(body)


def cmd_report_duplicates(args: argparse.Namespace) -> int:
    """Report existing-library duplicate-file candidates, as JSON, without
    Zotero writes."""
    def read() -> dict[str, Any]:
        z = local_library()
        with local_api():
            items = z.everything(z.items(itemType="attachment", limit=PAGE))
        attachments = [_attachment_record(i, USER_LIBRARY) for i in items]
        owners: dict[str, set[str]] = {}
        for att in attachments:
            if att["md5"] and att["parent"]:
                owners.setdefault(att["md5"], set()).add(att["parent"])
        shared = {p for parents in owners.values() if len(parents) > 1
                  for p in parents}
        return duplicate_hash_report(attachments,
                                     works_by_key(z, USER_LIBRARY, shared))

    found, rc = with_zotero("report-duplicates", read)
    if rc is not None:
        return rc
    report = {**found, "zotero": zotero_url(), "source": LIBRARY_SOURCE}
    if not report["hashed_attachments_scanned"]:
        raise SystemExit("report-duplicates: no stored attachment could be "
                         "compared; cannot call this an empty library")
    body = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.out:
        write_report_file(Path(args.out), body)
        print(f"report-duplicates: {report['candidate_clusters']} candidate "
              f"groups written to {args.out}")
    else:
        sys.stdout.write(body)
    return 0


STAGING_EXTENSIONS = frozenset(
    {".pdf", ".html", ".htm", ".jpg", ".jpeg", ".png", ".djvu", ".epub"}
)


# BibTeX blocks that hold no entry.
BIB_NOT_ENTRIES = {"string", "preamble", "comment"}
BIB_ENTRY_START = re.compile(r"@\s*(\w+)\s*[{(]")


def _bib_entries(path: Path) -> list[dict[str, Any]]:
    """Entries of one BibTeX file, parsed by bibtexparser; fail closed.

    bibtexparser drops an entry it cannot parse (an unclosed brace, a field
    with no `=`) and carries on. A reconciliation sweep must not: the
    dropped entry might link the only staged file needing import, so an
    entry count short of the `@type{` openings is an error, and so is a
    value naming an undefined `@string` macro.
    """
    content = path.read_text(encoding="utf-8")
    parser = BibTexParser(common_strings=True, ignore_nonstandard_types=False)
    try:
        entries = bibtexparser.loads(content, parser).entries
    except UndefinedString as exc:
        # A KeyError: left alone it would crash the sweep before --out.
        raise ValueError(f"undefined @string macro {exc}") from exc
    declared = sum(1 for m in BIB_ENTRY_START.finditer(content)
                   if m.group(1).lower() not in BIB_NOT_ENTRIES)
    if declared != len(entries):
        raise ValueError(f"{declared - len(entries)} of {declared} BibTeX "
                         f"entries could not be parsed (unclosed or malformed)")
    return [{**{k.lower(): v for k, v in e.items()
                if k not in ("ID", "ENTRYTYPE")},
             "_key": e.get("ID", ""), "_type": e.get("ENTRYTYPE", "").lower()}
            for e in entries]


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
    return {"bib_files": bib_files, "linked": linked,
            "orphans": staged_files(root, staging_dirs, linked_paths, errors),
            "errors": errors, "staging_dirs": sorted(staging_dirs)}


def discover_directory(root: Path, directory: Path) -> dict[str, Any]:
    """The --dir mode: every staging file under `directory`, no BibTeX."""
    root, directory = root.resolve(), (root / directory).resolve()
    errors: list[str] = []
    if not directory.is_relative_to(root):
        errors.append(f"staging directory outside repository: {directory}")
        dirs: set[Path] = set()
    elif not directory.is_dir():
        errors.append(f"not a directory: {directory}")
        dirs = set()
    else:
        dirs = {directory}
    return {"bib_files": [], "linked": [],
            "orphans": staged_files(root, dirs, set(), errors),
            "errors": errors, "staging_dirs": sorted(dirs)}


def staged_files(root: Path, staging_dirs: set[Path], linked_paths: set[Path],
                 errors: list[str]) -> list[Path]:
    """Staging files under `staging_dirs` no BibTeX entry links; a file or
    directory reaching outside `root` is an error, not a row."""
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
    return sorted(set(orphans))


def _filename_title(path: Path) -> str:
    """The words a staging filename like 'Afriat1967-MethodOfLimits.pdf'
    gives to search by: its surnames and its slug, camelCase split."""
    prefix, _, slug = path.stem.partition("-")
    head = re.split(r"(?:1[6-9]|20)\d\d", prefix, maxsplit=1)[0]
    names = re.findall(r"[A-Z][a-z]+|[A-Z]{2,}", head)
    return " ".join(names + [re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ",
                                    slug or path.stem)])


def _pdf_info(pdf: Path) -> dict[str, str]:
    """The container's recorded Title and Author, a junk title dropped.

    pdfinfo reads container metadata, pdftotext reads the text layer; they are
    independent. Gating the first on the second throws the Title away on every
    scanned or OCR-less file — routine material in a staging folder, and
    precisely the case where the text layer has nothing else to offer.
    """
    try:
        info = pdfinfo(pdf)
    except Exception:
        return {"Title": "", "Author": ""}
    title = info.get("Title", "") or ""
    return {"Title": "" if title.lower().endswith(".pdf") else title,
            "Author": info.get("Author", "") or ""}


def audit_one(path: Path, libs: list[tuple[str, zotero.Zotero]],
              bib_entry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Look one staged file up in the libraries."""
    bib_entry = bib_entry or {}
    info = (_pdf_info(path) if path.suffix.lower() == ".pdf"
            else {"Title": "", "Author": ""})
    title = str(bib_entry.get("title") or info["Title"])
    if len(re.findall(r"[^\W_]{3,}", title)) < TITLE_MIN_WORDS:
        # The filename carries the author's own naming intent.
        title = _filename_title(path)
    bib_type = str(bib_entry.get("_type", "")).lower()
    item_type = BIB_TO_ZOTERO_TYPE.get(bib_type)
    res = find_work(libs, title=title,
                    doi=bib_entry.get("doi"), isbn=bib_entry.get("isbn"),
                    arxiv=bib_entry.get("arxiv"),
                    handle=bib_entry.get("handle"),
                    item_type=item_type, pdf_path=path,
                    # Fail closed: an unplaced type may be a part whose ISBN
                    # is its volume's.
                    isbn_unusable=None if item_type else
                    f"unmapped .bib type @{bib_type}: part or volume unknown")
    top = res["matches"][0] if res["matches"] else None
    # Six answers, not four. Collapsing title candidates into "absent" is
    # the expensive mistake in both directions: called present, a document
    # is skipped and its full text never lands; called absent, a duplicate
    # item is minted. Candidates are a document to look at. And a file with
    # no key to look it up by is "unidentified", never "absent": an
    # all-clear indistinguishable from "could not look" is no check.
    if res["verdict"] == "unchecked":
        verdict = "unidentified"
    elif top and "storageHash" in top["why"]:
        verdict = "identical"
    elif top:
        verdict = ("work_present_with_file" if top.get("has_file")
                   else "work_present_no_file")
    elif res["candidates"]:
        verdict = "candidates"
    else:
        verdict = "absent"
    row = {"file": path.name, "verdict": verdict,
           "zotero_key": top.get("key") if top else None,
           "zotero_title": top.get("title") if top else None,
           "why": top.get("why") if top else None,
           "consulted": res["consulted"], "skipped": res["skipped"]}
    if verdict == "candidates":
        row["candidates"] = [{"key": c["key"], "title": c["title"],
                              "date": c["date"], "creators": c["creators"]}
                             for c in res["candidates"]]
    # A tie (ticket 0570): the verdict stays what the first match supports
    # ("identical" is still true: the file IS stored), but every other
    # matching parent is named, so `suggest-attachments --parent` is not
    # aimed at an arbitrary one.
    if len(res["matches"]) > 1:
        row["also_matches"] = [
            {"key": m["key"], "title": m.get("title"), "why": m["why"]}
            for m in res["matches"][1:]]
    return row


def count_verdicts(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Verdict counts, plus the ties a human reader must see."""
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


TIED_ACTION = ("several records match (also_matches); pick one before "
               "attaching by hand")


RECONCILE_ACTIONS = {
    "identical": "nothing",
    "work_present_with_file": "nothing; report the second copy",
    "work_present_no_file": "suggest-attachments: see suggested_edits, or "
                            "--apply --edit (never create-items)",
    "candidates": "judge the title candidates; neither create nor skip",
    "unidentified": "nothing to look it up by: give it a .bib entry, or name "
                    "it Author1999-title",
    "absent": "create-items, or --apply with the project opt-in",
    "error": "inspect unreadable file",
    "unchecked": "resolve discovery or check error",
    "tied_parents": TIED_ACTION,
    "deferred": "give it a .bib entry with title, author and year, or "
                "create-items",
    "created": "created in Zotero through its local API",
    "attached": "stored under the existing item (--edit)",
    "failed_write": "inspect the outcome in Zotero before retrying",
    "apply_failed": "inspect error; no clean sweep",
}


def reconcile_apply_config(root: Path, account: str | None, *,
                           check_account: bool = True) -> dict[str, Any]:
    """Read the explicit project opt-in; its user_id must be the local account.

    `check_account=False` checks the file alone, before Zotero is contacted.
    """
    config = json.loads((root / ".zotero-reconcile.json").read_text())
    if not isinstance(config, dict) or config.get("apply") is not True:
        raise ValueError("apply must be true")
    if not check_account:
        return config
    if account is None:
        raise ValueError("the local Zotero is signed in to no account; "
                         "cannot check the configured user_id")
    if str(config.get("user_id")) != str(account):
        raise ValueError("configured user_id differs from the account the "
                         f"local Zotero is signed in as ({account})")
    return config


def reconcile_report(root: Path, found: dict[str, Any], rows: list[dict[str, Any]],
                     errors: list[str], verdict: str | None = None
                     ) -> dict[str, Any]:
    """The one report shape every check-staging exit writes, early or not."""
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


def reconcile_unavailable(root: Path, found: dict[str, Any],
                          exc: ZoteroUnavailable | ZoteroSlow,
                          out: str | None) -> int:
    """Zotero could not be reached or launched: a clean no-op, exit 0.

    Nothing was compared and nothing was created. The verdict says so, and
    the exit status lets an unattended sweep move on instead of crashing.
    Discovery errors (a broken bib) do not depend on Zotero: they are still
    reported, and exit 1. A read Zotero did not finish in time is not that
    no-op: verdict zotero_slow, exit EXIT_SLOW, whatever had been compared.
    """
    errors = list(found["errors"])
    slow = isinstance(exc, ZoteroSlow)
    report = reconcile_report(
        root, found, [], errors,
        verdict="zotero_slow" if slow else "zotero_unavailable")
    report["zotero"] = {"status": "slow" if slow else "unavailable",
                        "reason": str(exc)}
    print(f"check-staging: {exc}", file=sys.stderr)
    emit_reconcile_report(report, out)
    if slow:
        return EXIT_SLOW
    return 1 if errors else 0


def reconcile_empty_report(root: Path, found: dict[str, Any],
                           args: argparse.Namespace) -> int:
    """Nothing staged: no library read, but an apply still checks its opt-in.

    The opt-in is checked against the signed-in account, so a broken
    `.zotero-reconcile.json` fails now instead of on the first staged file.
    """
    staged = any(p.is_dir() for p in found["staging_dirs"])
    report = reconcile_report(
        root, found, [], [],
        verdict="checked" if staged or found["bib_files"] else "no_staging")
    rc = 0
    if getattr(args, "apply", False):
        try:
            reconcile_apply_config(root, None, check_account=False)
            ensure_zotero()
            account = local_account()
            report["library"] = {"zotero": zotero_url(), "source": LIBRARY_SOURCE}
            reconcile_apply_config(root, account)
            report.update({"applied": [], "apply_status": "nothing"})
        except (ZoteroUnavailable, ZoteroSlow) as exc:
            return reconcile_unavailable(root, found, exc, args.out)
        except (OSError, ValueError, TypeError, LocalAPIError) as exc:
            mark_apply_failed(report, exc)
            rc = 1
    emit_reconcile_report(report, args.out)
    return rc


def audit_sources(root: Path, found: dict[str, Any],
                  libs: list[tuple[str, zotero.Zotero]]
                  ) -> tuple[list[dict[str, Any]], list[str]]:
    """Look every linked and orphan file up; (rows, errors). A file that
    cannot be read is an error; Zotero failing is the whole run's."""
    rows: list[dict[str, Any]] = []
    errors = list(found["errors"])
    sources = found["linked"] + [{"path": path} for path in found["orphans"]]
    for source in sources:
        path = source["path"]
        try:
            row = audit_one(path, libs, bib_entry=source.get("entry"))
        except (ZoteroUnavailable, ZoteroSlow, LocalAPIError):
            raise
        except Exception as exc:
            errors.append(f"cannot check {path.relative_to(root)}: {exc}")
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


def cmd_check_staging(args: argparse.Namespace) -> int:
    """Compare staged files with the library: the files the repository's
    BibTeX links (and the unlinked ones beside them), or with --dir every
    file of one directory. Report by default; apply only with a matching
    project opt-in file."""
    root = Path(args.root).resolve()
    if not root.is_dir():
        emit_reconcile_report({"verdict": "unchecked",
                               "error": f"not a directory: {root}"}, args.out)
        return 1
    if args.dir is not None and not args.dir.strip():
        # An empty variable must not widen --dir to the whole repository.
        emit_reconcile_report({"verdict": "unchecked",
                               "error": "--dir is empty"}, args.out)
        return 1
    found = (discover_directory(root, Path(args.dir)) if args.dir
             else discover_reconcile_files(root))
    if not (found["linked"] or found["orphans"]):
        if found["errors"]:
            # Nothing to compare, and discovery failed: say so, without Zotero.
            emit_reconcile_report(
                reconcile_report(root, found, [], found["errors"]), args.out)
            return 1
        # Nothing staged: no library comparison is needed.
        return reconcile_empty_report(root, found, args)
    library = getattr(args, "library", USER_LIBRARY)
    try:
        ensure_zotero()
        rows, errors = audit_sources(root, found, libraries(library))
    except (ZoteroUnavailable, ZoteroSlow) as exc:
        return reconcile_unavailable(root, found, exc, args.out)
    except (LocalAPIError, ValueError) as exc:
        report = reconcile_report(root, found, [], found["errors"] + [
            f"cannot read the Zotero library: {exc}"])
        emit_reconcile_report(report, args.out)
        return 1
    report = reconcile_report(root, found, rows, errors)
    report["library"] = {"zotero": zotero_url(), "source": LIBRARY_SOURCE,
                         "library_id": library}
    apply_rc = 0
    if getattr(args, "apply", False):
        try:
            config = reconcile_apply_config(root, local_account())
            if errors:
                raise ValueError("discovery or check is unchecked")
            with directory_locks(found["staging_dirs"] + [library_lock_dir()]):
                # Look again under the locks and keep them through the
                # saves, so two local sweeps cannot both act on the same
                # pre-lock answer. The lookup covers the library the items
                # will land in: a collection in a group is checked against
                # that group.
                target_lib = resolve_target(library, config.get("collection"))
                report, apply_rc = reconcile_apply(root, found, target_lib,
                                                   config, args)
        except (ZoteroUnavailable, ZoteroSlow) as exc:
            # Gone before anything was created (Zotero vanishing during the
            # saves is reported per entry by create-items): a clean no-op.
            return reconcile_unavailable(root, found, exc, args.out)
        except (OSError, ValueError, KeyError, TypeError, RuntimeError,
                LocalAPIError) as exc:
            mark_apply_failed(report, exc)
            apply_rc = 1
    emit_reconcile_report(report, args.out)
    return 1 if report["errors"] or apply_rc else 0


def reconcile_apply(root: Path, found: dict[str, Any], target_lib: str,
                    config: dict[str, Any], args: argparse.Namespace
                    ) -> tuple[dict[str, Any], int]:
    """Create the absent PDFs a .bib entry describes, looked up again under
    the lock."""
    rows, errors = audit_sources(root, found, libraries(target_lib))
    if errors:
        raise ValueError("discovery or check is unchecked")
    entries = {item["path"]: item.get("entry") or {} for item in found["linked"]}
    jobs: list[dict[str, Any]] = []
    job_paths: list[str] = []
    deferred = []
    for row in rows:
        if row["verdict"] != "absent":
            continue
        path = root / row["path"]
        entry = bib_to_inject_entry(entries.get(path.resolve(), {}), path)
        if entry is None:
            deferred.append({"file": row["path"],
                             "reason": "no .bib entry with title, author and "
                                       "year: nothing curated to create it "
                                       "from"})
        else:
            jobs.append(entry)
            job_paths.append(row["path"])
    # The displayed report describes the same locked lookup that decides the
    # writes; the earlier one can predate another sweep.
    report = reconcile_report(root, found, rows, [])
    report["library"] = {"zotero": zotero_url(), "source": LIBRARY_SOURCE,
                         "library_id": target_lib}
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
            collection=config.get("collection"), library=target_lib,
            dry_run=False, force=False,
            _locked=True)
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            rc = cmd_create_items(inject_args)
        outcome = json.loads(captured.getvalue())
        if outcome.get("zotero") == "slow":
            raise ZoteroSlow(outcome.get("error", "create-items read slowly"))
        if outcome.get("zotero") == "unavailable":
            raise ZoteroUnavailable(outcome.get("error", "Zotero went away"))
        if "results" not in outcome:
            raise RuntimeError(outcome.get("error", "create-items failed"))
        report["applied"] = outcome["results"]
        for file, result in zip(job_paths, report["applied"]):
            result["file"] = file
            summary["absent"] -= 1
            if result.get("status") == "created" and not (
                    result.get("error") or result.get("attachment_error")
                    or result.get("transport_error")):
                summary["created"] = summary.get("created", 0) + 1
                actions["created"] = RECONCILE_ACTIONS["created"]
            else:
                summary["failed_write"] = summary.get("failed_write", 0) + 1
                actions["failed_write"] = RECONCILE_ACTIONS["failed_write"]
    if getattr(args, "edit", False):
        rc = max(rc, attach_present_works(root, rows, target_lib, report))
    for verdict in ("absent", "work_present_no_file"):
        if summary.get(verdict) == 0:
            summary.pop(verdict)
            actions.pop(verdict, None)
    report["apply_status"] = (
        "partial" if summary.get("failed_write") else
        "deferred" if deferred else
        "applied" if summary.get("created") or summary.get("attached")
        else "nothing")
    return report, rc


def attach_present_works(root: Path, rows: list[dict[str, Any]],
                         target_lib: str, report: dict[str, Any]) -> int:
    """--edit: store each staged file under the one existing work that
    lacks it. A tie between parents is left for the author."""
    summary, actions = report["summary"], report["actions"]
    z = local_library(target_lib)
    report["edits"] = []
    rc = 0
    refused = False
    for row in rows:
        if (row["verdict"] != "work_present_no_file" or row.get("also_matches")
                or not row.get("zotero_key")):
            continue
        edit = {"itemKey": row["zotero_key"], "file": row["path"]}
        if refused:
            edit.update(status="not attempted", error=KEY_NOT_ATTEMPTED)
            report["edits"].append(edit)
            continue
        try:
            edit["attachment"] = attach_file(z, row["zotero_key"],
                                             root / row["path"])
            edit["status"] = "attached"
            summary["work_present_no_file"] -= 1
            summary["attached"] = summary.get("attached", 0) + 1
            actions["attached"] = RECONCILE_ACTIONS["attached"]
        except (ZoteroUnavailable, ZoteroSlow, LocalAPIError,
                KeyNotGranted) as exc:
            edit.update(status="failed", error=str(exc))
            summary["failed_write"] = summary.get("failed_write", 0) + 1
            actions["failed_write"] = RECONCILE_ACTIONS["failed_write"]
            rc = 1
            refused = isinstance(exc, KeyNotGranted)
        report["edits"].append(edit)
    report["suggested_edits"] = [
        e for e in report["suggested_edits"]
        if not any(d["status"] == "attached" and d["itemKey"] == e["itemKey"]
                   for d in report["edits"])]
    return rc


# BibTeX and biblatex entry types as Zotero item types, after Zotero's own
# BibTeX translator; any other type becomes `document`. Every part of a
# volume maps to a type in ISBN_OF_A_VOLUME, every volume to `book`: an
# unmapped type is never looked up by ISBN (audit_one).
BIB_TO_ZOTERO_TYPE = {
    "article": "journalArticle", "book": "book", "inbook": "bookSection",
    "incollection": "bookSection", "inproceedings": "conferencePaper",
    "conference": "conferencePaper", "inreference": "encyclopediaArticle",
    "bookinbook": "bookSection", "suppbook": "bookSection",
    "suppcollection": "bookSection",
    "proceedings": "book", "collection": "book", "reference": "book",
    "mvbook": "book", "mvcollection": "book", "mvreference": "book",
    "phdthesis": "thesis",
    "mastersthesis": "thesis", "techreport": "report",
    "unpublished": "manuscript"}


def bib_to_inject_entry(bib: dict[str, Any], path: Path) -> dict[str, Any] | None:
    """A create-items entry from the author's curated BibTeX entry, None
    unless it gives a title, an author and a year for a PDF. Page text and
    pdfinfo are never trusted to create an item unattended."""
    title, author, year = (str(bib.get(k) or "").strip()
                           for k in ("title", "author", "year"))
    if not (title and author and year and path.suffix.lower() == ".pdf"):
        return None
    entry: dict[str, Any] = {
        "type": BIB_TO_ZOTERO_TYPE.get(str(bib.get("_type", "")).lower(),
                                       "document"),
        "title": title, "authors": [a.strip() for a in author.split(" and ")],
        "year": year, "pdf": str(path), "attach_pdf": True}
    for source, target in (("doi", "doi"), ("isbn", "isbn"),
                           ("url", "url"), ("journal", "journal"),
                           ("publisher", "publisher"), ("pages", "pages")):
        if bib.get(source):
            entry[target] = str(bib[source])
    return entry


def cmd_suggest_attachments(args: argparse.Namespace) -> int:
    """File documents onto an EXISTING item: report, or store with --edit.

    The repair for `work_present_no_file`. `create-items` cannot do it: it
    only creates items, and creating a second item to carry the file is how
    duplicates are born.
    """
    found, rc = with_zotero("suggest-attachments",
                            lambda: find_item(args.parent, args.library))
    if rc is not None:
        return rc
    if found is None:
        emit_json({"parent": args.parent, "source": LIBRARY_SOURCE,
                   "error": "item not found"})
        return 1
    z, item = found
    rc = 0
    rows = []
    refused = False
    for f in args.file:
        p = Path(f)
        if not p.is_file():
            rows.append({"file": f, "error": "not found"})
            rc = 1
            continue
        row = {"itemKey": args.parent, "field": "attachment", "old": "",
               "new": str(p.resolve())}
        if args.edit and refused:
            row.update(status="not attempted", error=KEY_NOT_ATTEMPTED)
        elif args.edit:
            try:
                row["attachment"] = attach_file(z, args.parent, p)
                row["status"] = "attached"
            except (ZoteroUnavailable, ZoteroSlow, LocalAPIError,
                    KeyNotGranted) as exc:
                row.update(status="failed", error=str(exc))
                rc = 1
                refused = isinstance(exc, KeyNotGranted)
        rows.append(row)
    emit_json({"parent": args.parent, "title": item["data"].get("title"),
               "source": LIBRARY_SOURCE, "edit": args.edit,
               **({} if args.edit else {"apply": EDIT_HINT}),
               ("attached" if args.edit else "suggested"): rows})
    return rc


def add_library_args(parser: argparse.ArgumentParser, help_scope: str) -> None:
    parser.add_argument("--library", default=USER_LIBRARY, help=help_scope)


def add_edit_arg(parser: argparse.ArgumentParser, help_text: str) -> None:
    """The one flag that lets a command edit an existing item."""
    parser.add_argument("--edit", action="store_true", help=help_text)


def main() -> int:
    p = argparse.ArgumentParser(prog="zotero.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    scope = ("dedup scope: 'user' (default, the create-items destination), "
             "'all', or a numeric groupID")

    px = sub.add_parser("extract-metadata",
                        help="what each PDF says about itself: identifiers, "
                             "text, pdfinfo; never contacts Zotero")
    px.add_argument("pdf", nargs="+")
    px.set_defaults(func=cmd_extract_metadata)

    pf = sub.add_parser("find-work",
                        help="is this work already in the library? Zotero's "
                             "local API only; reads extract-metadata output "
                             "or the flags")
    pf.add_argument("--metadata", help="extract-metadata JSON: a file, or - "
                                       "for stdin; the flags override it")
    pf.add_argument("--title", help="title to search: its hits are "
                                    "candidates to judge, never a match")
    pf.add_argument("--doi", help="DOI to exact-match")
    pf.add_argument("--isbn", help="ISBN to exact-match (any hyphenation)")
    pf.add_argument("--arxiv", help="arXiv id to match (e.g. 2401.01234)")
    pf.add_argument("--handle", help="handle URL or hdl.handle.net path")
    pf.add_argument("--type", help="the work's Zotero item type; a "
                                   "bookSection or conferencePaper is not "
                                   "looked up by its volume's ISBN")
    pf.add_argument("--pdf", help="PDF path: its content hash is compared "
                                  "with the files of each work found")
    add_library_args(pf, scope)
    pf.set_defaults(func=cmd_find_work)

    pd = sub.add_parser("report-duplicates",
                        help="read-only JSON report of identical stored files "
                             "under distinct My Library items")
    pd.add_argument("--out", help="write the report to this file (else stdout)")
    pd.set_defaults(func=cmd_report_duplicates)

    pr = sub.add_parser("check-staging",
                        help="compare staged files with the library: the "
                             "files .bib entries link (and unlinked ones), "
                             "or every staging file under --dir; explicit "
                             "opt-in to apply")
    pr.add_argument("root", nargs="?", default=".",
                    help="repository root (default: current directory)")
    pr.add_argument("--dir", help="check every staging file under this "
                                  "directory of the root instead of the "
                                  "BibTeX-linked ones")
    pr.add_argument("--out", help="write the full JSON report to this path")
    pr.add_argument("--apply", action="store_true",
                    help="create the absent PDFs .bib entries describe, only "
                         "when the root has .zotero-reconcile.json with "
                         "apply=true and the user_id local Zotero is signed "
                         "in as")
    add_edit_arg(pr, "with --apply, also store each staged file under the "
                     "one existing item that lacks it")
    add_library_args(pr, scope)
    pr.set_defaults(func=cmd_check_staging)

    pt = sub.add_parser("suggest-attachments",
                        help="report how to file documents onto an EXISTING "
                             "item (the present-no-file case); writes only "
                             "with --edit")
    pt.add_argument("--parent", required=True, help="parent item key")
    pt.add_argument("file", nargs="+")
    add_edit_arg(pt, "store the files under the item (default: report)")
    add_library_args(pt, scope)
    pt.set_defaults(func=cmd_suggest_attachments)

    pi = sub.add_parser("create-items",
                        help="create items (and attach PDFs) through the "
                             "Zotero local API; Zotero is launched "
                             "if it is not running")
    gi = pi.add_mutually_exclusive_group()
    gi.add_argument("--entries-json", help="inline JSON: array of entry dicts")
    gi.add_argument("--entries-file", help="path to JSON file with entries")
    pi.add_argument("--collection", help="collection key to file items under "
                                         "(its library is the destination)")
    add_library_args(pi, "destination and dedup scope: 'user' (default) or "
                         "a numeric groupID, e.g. an editable group")
    pi.add_argument("--dry-run", action="store_true",
                    help="print the Zotero item JSON (built against the "
                         "running client's schema), create nothing")
    pi.add_argument("--force", action="store_true",
                    help="explicitly bypass the library and batch duplicate "
                         "guard; use only after examining the matches and "
                         "candidates")
    pi.set_defaults(func=cmd_create_items)

    pe = sub.add_parser("suggest-edits",
                        help="report missing fields on EXISTING items for the "
                             "author; writes them only with --edit")
    ge = pe.add_mutually_exclusive_group(required=True)
    ge.add_argument("--item-key", help="the item to complete")
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
    add_edit_arg(pe, "write the suggested fields (default: report)")
    add_library_args(pe, scope)
    pe.set_defaults(func=cmd_suggest_edits)

    args = p.parse_args()
    if args.cmd == "suggest-edits" and args.item_key and not args.expect_title:
        p.error("--expect-title is required with --item-key")
    if args.cmd == "check-staging" and args.edit and not args.apply:
        p.error("--edit needs --apply")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

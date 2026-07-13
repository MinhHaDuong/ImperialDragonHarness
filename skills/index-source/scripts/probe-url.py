#!/usr/bin/env python3
"""Probe one or more URLs for bibliographic indexing.

For each URL: stage the document into a local staging dir (PDF as-is, HTML
snapshot) and extract structured metadata — identifiers (DOI/arXiv/ISBN),
meta tags (JSON-LD, Highwire citation_*, Dublin Core, OpenGraph), and the PDF
page count. Emits one JSON record per URL on stdout.

Stdlib only — nothing to install. The model reads the records, resolves
identifiers online when present, picks the Zotero item type with judgment, then
hands attachments + metadata to ~/.claude/scripts/zotero-import.py (RIS write +
dedupe). This is the URL sibling of the zotero-import skill; it implements the
EDM workflow (docs/ staging -> Zotero)."""

import argparse
import json
import logging
import re
import subprocess
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"
log = logging.getLogger("probe-url")

DOI_BARE_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)
# Anchor on doi.org/ or "DOI:" preamble so a document's own DOI is preferred
# over the first bare DOI cited in the body (mirrors zotero-import.py's
# DOI_ANCHORED_RE / find_doi()).
DOI_ANCHORED_RE = re.compile(r"(?:doi\.org/|doi[:\s]+)(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)", re.I)
ARXIV_RE = re.compile(r"\barXiv:\s*(\d{4}\.\d{4,5}(v\d+)?)\b", re.I)
ISBN_RE = re.compile(r"\b97[89][-– ]?(?:\d[-– ]?){9}\d\b")


class MetaParser(HTMLParser):
    """Collect <meta> tags, <title>, and JSON-LD blocks."""

    REPEATABLE = ("citation_author", "dc.creator")

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.metas: dict[str, str] = {}
        self.authors: list[str] = []
        self.title = ""
        self.ld: list[str] = []
        self._in_title = False
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "meta":
            key = a.get("name") or a.get("property") or a.get("itemprop")
            if key and "content" in a:
                key = key.lower()
                if key in self.REPEATABLE:
                    self.authors.append(a["content"])  # Highwire repeats this tag
                else:
                    self.metas.setdefault(key, a["content"])
        elif tag == "title":
            self._in_title = True
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in_ld = True
            self.ld.append("")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._in_ld:
            self._in_ld = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif self._in_ld:
            self.ld[-1] += data


def fetch(url: str, timeout: int) -> tuple[bytes, str, str]:
    if urlparse(url).scheme not in ("http", "https"):
        raise ValueError(f"unsupported URL scheme (http/https only): {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        if urlparse(r.geturl()).scheme not in ("http", "https"):
            raise ValueError(f"redirected to unsupported URL scheme: {r.geturl()}")
        return r.read(), r.geturl(), r.headers.get("Content-Type", "")


def slugify(text: str, maxlen: int = 50) -> str:
    text = re.sub(r"[^\w]+", "-", text.strip().lower()).strip("-")
    return (text[:maxlen].rstrip("-")) or "document"


def jsonld_fields(blocks: list[str]) -> dict:
    """Pull author/date/type/publisher/headline from JSON-LD (handles @graph)."""
    out: dict = {}

    def visit(node):
        if isinstance(node, list):
            for n in node:
                visit(n)
            return
        if not isinstance(node, dict):
            return
        if "@graph" in node:
            visit(node["@graph"])
        t = node.get("@type", "")
        types = t if isinstance(t, list) else [t]
        if any(x in ("Article", "NewsArticle", "BlogPosting", "Report", "ScholarlyArticle", "WebPage") for x in types):
            out.setdefault("jsonld_type", types[0])
            if node.get("headline") or node.get("name"):
                out.setdefault("title", node.get("headline") or node.get("name"))
            if node.get("datePublished"):
                out.setdefault("date", node["datePublished"])
            auth = node.get("author")
            names = []
            for x in auth if isinstance(auth, list) else [auth]:
                if isinstance(x, dict) and x.get("name"):
                    names.append(x["name"])
                elif isinstance(x, str):
                    names.append(x)
            if names:
                out.setdefault("authors", names)
            pub = node.get("publisher")
            if isinstance(pub, dict) and pub.get("name"):
                out.setdefault("publisher", pub["name"])

    for b in blocks:
        try:
            visit(json.loads(b))
        except Exception:
            continue
    return out


def parse_html(html: str) -> dict:
    p = MetaParser()
    try:
        p.feed(html)
    except Exception as e:
        log.warning("HTML parse hiccup: %s", e)
    m = p.metas
    meta = {
        "title": m.get("citation_title") or m.get("dc.title") or m.get("og:title") or p.title.strip(),
        "date": m.get("citation_publication_date") or m.get("citation_date")
        or m.get("article:published_time") or m.get("dc.date") or "",
        "publication": m.get("citation_journal_title") or m.get("og:site_name") or "",
        "publisher": m.get("citation_publisher") or m.get("dc.publisher") or "",
        "og_type": m.get("og:type", ""),
        "doi_meta": m.get("citation_doi") or m.get("dc.identifier") or "",
        "pdf_url": m.get("citation_pdf_url", ""),
    }
    authors = list(p.authors)
    if not authors and m.get("author"):
        authors = [m["author"]]
    if authors:
        meta["authors"] = authors
    # JSON-LD fills gaps (esp. multi-author Highwire only keeps one via setdefault)
    ld = jsonld_fields(p.ld)
    for k, v in ld.items():
        if not meta.get(k):
            meta[k] = v
    return {k: v for k, v in meta.items() if v}


def pdf_info(path: Path) -> dict:
    out: dict = {}
    try:
        info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, timeout=30).stdout
        if mo := re.search(r"^Pages:\s+(\d+)", info, re.M):
            out["page_count"] = int(mo.group(1))
    except Exception:
        pass
    try:
        txt = subprocess.run(["pdftotext", "-f", "1", "-l", "2", str(path), "-"],
                             capture_output=True, text=True, timeout=30).stdout
        out["first_text"] = "\n".join(ln for ln in txt.splitlines() if ln.strip())[:1200]
    except Exception:
        pass
    return out


def find_identifiers(text: str, doi_meta: str = "") -> dict:
    ids: dict = {}
    doi = doi_meta.strip()
    if not doi:
        if mo := DOI_ANCHORED_RE.search(text):
            doi = mo.group(1)
        elif mo := DOI_BARE_RE.search(text):
            doi = mo.group(0)
    if doi:
        ids["doi"] = doi.rstrip(".,;)»")
    if mo := ARXIV_RE.search(text):
        ids["arxiv"] = mo.group(1)
    if mo := ISBN_RE.search(text):
        ids["isbn"] = re.sub(r"[-– ]", "", mo.group(0))
    return ids


def suggest_type(mime: str, host: str, meta: dict, ids: dict) -> str:
    """Heuristic RIS type — the model overrides with judgment (see SKILL.md).

    JOUR if it looks like a journal article (DOI + a journal title); RPRT for a
    PDF (institutional report is the common case); WEB otherwise (news/analysis).
    """
    if ids.get("doi") and meta.get("publication"):
        return "JOUR"
    if "pdf" in mime:
        return "RPRT"
    return "WEB"


def probe_one(url: str, staging: Path, timeout: int) -> dict:
    rec: dict = {"url": url}
    try:
        body, final_url, ctype = fetch(url, timeout)
    except urllib.error.HTTPError as e:
        rec["error"] = f"HTTP {e.code} — {e.reason} (try an alternate source/mirror)"
        return rec
    except Exception as e:
        rec["error"] = f"fetch failed: {e}"
        return rec
    rec["final_url"] = final_url
    host = urlparse(final_url).netloc.lower().removeprefix("www.")
    is_pdf = "pdf" in ctype.lower() or body[:5] == b"%PDF-"
    ext = "pdf" if is_pdf else "html"

    text = "" if is_pdf else body.decode("utf-8", "replace")
    meta = {} if is_pdf else parse_html(text)
    stem = slugify(f"{host}-{meta.get('title', urlparse(final_url).path)}")
    path = staging / f"{stem}.{ext}"
    n = 1
    while path.exists():
        n += 1
        path = staging / f"{stem}-{n}.{ext}"
    path.write_bytes(body)
    rec["staged_path"] = str(path)
    rec["mime"] = "application/pdf" if is_pdf else "text/html"

    if is_pdf:
        pi = pdf_info(path)
        if "page_count" in pi:
            rec["page_count"] = pi["page_count"]
        text = pi.get("first_text", "")
    rec["meta"] = meta
    rec["identifiers"] = find_identifiers(text or "", meta.get("doi_meta", ""))
    rec["suggested_ris_type"] = suggest_type(rec["mime"], host, meta, rec["identifiers"])
    if meta.get("pdf_url") and not is_pdf:
        rec["full_pdf_url"] = meta["pdf_url"]
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("urls", nargs="+", help="URL(s) to probe")
    ap.add_argument("--staging-dir", default="docs", help="where to stage documents (default: docs/)")
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(message)s")
    staging = Path(args.staging_dir)
    staging.mkdir(parents=True, exist_ok=True)
    records = [probe_one(u, staging, args.timeout) for u in args.urls]
    print(json.dumps(records, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Tests for scripts/zotero.py.

Author decision, 2026-10-16: "In tests up Zotero as a fixture or skip --
no mock". There is no stand-in for Zotero here. Each test is one of:

- pure logic that never talks to Zotero: identifier extraction, entry-to-item
  mapping, the matcher over an in-memory library built by hand,
  report shapes, BibTeX discovery;
- a test against a REAL Zotero desktop client on a throwaway profile, data
  directory and port (tests/zotero_live.py), marked `integration`, which
  skips with the reason where that client cannot run;
- the real "Zotero is down" path: the autouse fixture points the helper at
  a closed loopback port and sets ZOTERO_NO_LAUNCH, so nothing answers and
  nothing is launched, and the helper must do nothing.

The live library is shared by every test of a pytest process: each test
seeds items with titles, DOIs and files of its own and asserts only on what
it seeded. No test touches ~/Zotero, the author's profile or port 23119.
"""

import argparse
import contextlib
import fcntl
import hashlib
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import pytest
from pyzotero import errors as ze

import zotero_live
from child_env import child_env
from zotero_live import free_port, unique_title

# The real-Zotero fixtures (tests/zotero_live.py), bound here so pytest
# finds them by name.
zotero_factory = zotero_live.zotero_factory
live_zotero = zotero_live.live_zotero
api_off_zotero = zotero_live.api_off_zotero
zotero_binary = zotero_live.zotero_binary
use_live = zotero_live.use_live

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
zi = zotero_live.helper_module()


@pytest.fixture(autouse=True)
def zotero_down(monkeypatch, tmp_path_factory):
    """Every test starts with nothing answering and nothing launchable,
    through the environment the helper honours: the Zotero URL is a closed
    loopback port, ZOTERO_NO_LAUNCH is set, and the key file is a path of
    the test's own that holds nothing (never ~/.config/keys). `use_live`
    points the URL and the key file at the throwaway client instead."""
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{free_port()}")
    monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE",
                       str(tmp_path_factory.mktemp("keys") / "zotero-local.env"))


def make_pdf(path: Path, lines: list[str], info: dict[str, str] | None = None
             ) -> Path:
    """A small, valid one-page PDF whose text layer holds `lines` (ASCII)
    and whose Info dictionary holds `info`: pdftotext and pdfinfo read it."""
    def esc(text: str) -> str:
        return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    stream = "BT /F1 12 Tf 72 720 Td 16 TL " + "".join(
        f"({esc(line)}) Tj T* " for line in lines) + "ET"
    objects = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
        "<< " + " ".join(f"/{k} ({esc(v)})" for k, v in (info or {}).items()) + " >>",
    ]
    out = "%PDF-1.4\n"
    offsets = []
    for n, body in enumerate(objects, 1):
        offsets.append(len(out))
        out += f"{n} 0 obj\n{body}\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    out += "".join(f"{o:010d} 00000 n \n" for o in offsets)
    out += (f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R /Info 6 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n")
    path.write_bytes(out.encode("latin-1"))
    return path


def paper_pdf(directory: Path, title: str, author: str, *,
              info: dict[str, str] | None = None) -> Path:
    """A PDF whose front matter states `title` and `author`, so the
    helper's corroboration finds both; its name and bytes are unique."""
    name = f"{uuid.uuid4().hex[:12]}.pdf"
    return make_pdf(directory / name, [title, f"by {author}",
                                       f"nonce {uuid.uuid4().hex}"], info)


def unique_doi() -> str:
    return f"10.5555/{uuid.uuid4().hex[:12]}"


def unique_surname() -> str:
    return unique_title(1)


# ── identifier extraction ────────────────────────────────────────────────────


def test_find_doi_anchored_doi_org():
    assert zi.find_doi("see https://doi.org/10.1234/abc.def here", "", "") == "10.1234/abc.def"


def test_find_doi_anchored_prefix():
    assert zi.find_doi("DOI: 10.5555/xyz", "", "") == "10.5555/xyz"


def test_find_doi_strips_trailing_punctuation():
    assert zi.find_doi("doi.org/10.1234/abc.", "", "") == "10.1234/abc"


def test_find_doi_bare_within_window():
    front = "Title\n10.9999/bare-doi appears early"
    assert zi.find_doi(front, "", "") == "10.9999/bare-doi"


def test_find_doi_none_when_absent():
    assert zi.find_doi("no identifier text", "", "") is None


def test_find_identifier_collects_all():
    front = "https://doi.org/10.1234/x arXiv:2401.01234 ISBN: 978-0-13-468599-1"
    back = "hdl.handle.net/2027/abc"
    ids = zi.find_identifier(front, back, "")
    assert ids["doi"] == "10.1234/x"
    assert ids["arxiv"] == "2401.01234"
    assert ids["isbn"] == "9780134685991"  # separators stripped
    assert ids["handle"] == "https://hdl.handle.net/2027/abc"


def test_a_cited_works_doi_deep_in_the_page_is_not_the_documents_own():
    """pdf2doi (evaluated offline for ticket 1116) returns the first DOI in
    the text, a reference-list one included; this extraction does not."""
    front = "A Study of Things\nby Smith\n" + "filler line\n" * 80 + \
            "References\nJones 2001, 10.1111/cited.1\n"
    assert zi.find_doi(front, "", "") is None


# ── the probe split: extract-metadata, then find-work ────────────────────────


@contextlib.contextmanager
def connections(monkeypatch):
    """Every socket connection this process attempts, recorded (and let
    through): the probe for "contacts nothing"."""
    seen = []
    real = socket.socket.connect

    def connect(self, address):
        seen.append(address)
        return real(self, address)

    monkeypatch.setattr(socket.socket, "connect", connect)
    yield seen


@pytest.mark.integration
def test_extract_metadata_never_contacts_zotero(tmp_path, monkeypatch, capsys):
    """Extraction is input-format dependent and never needs Zotero: it
    reads the PDF (poppler runs in a child process) and this process opens
    no connection."""
    pdf = make_pdf(tmp_path / "paper.pdf", ["A Study of Things", "by Smith",
                                            "doi: 10.2222/own.2"])
    with connections(monkeypatch) as seen:
        rc = zi.cmd_extract_metadata(argparse.Namespace(pdf=[str(pdf)]))
        assert seen == []
        # Positive control: a lookup's first step does try to connect.
        assert zi.zotero_answers(timeout=0.5) is False
        assert len(seen) == 1
    assert rc == 0
    (item,) = json.loads(capsys.readouterr().out)["items"]
    assert item["identifiers"]["doi"] == "10.2222/own.2"
    assert "A Study of Things" in item["first_pages_text"]
    assert "zotero_matches" not in item


def test_extract_metadata_reports_a_missing_pdf(tmp_path, capsys):
    rc = zi.cmd_extract_metadata(argparse.Namespace(pdf=[str(tmp_path / "x.pdf")]))
    assert rc == 1
    assert json.loads(capsys.readouterr().out)["items"][0]["error"] == "not found"


def _meta_file(tmp_path, *items):
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({"items": list(items)}))
    return str(meta)


def _meta_item(doi):
    return {"pdf": None, "identifiers": {"doi": doi}, "pdfinfo": {},
            "year_hint": None, "first_pages_text": ""}


def test_find_work_refuses_flags_over_several_extracted_works(tmp_path, capsys):
    """A refined --title for one PDF must not describe every PDF of the
    file: the second would be reported as the first's work."""
    meta = _meta_file(tmp_path, _meta_item("10.1/a"), _meta_item("10.1/b"))
    assert zi.cmd_find_work(_match_args(doi=None, title="A Refined Title",
                                        author="Smith", metadata=meta)) == 1
    out = json.loads(capsys.readouterr().out)
    assert "--author, --title would describe all 2 works" in out["error"]
    assert out["verdict"] == "unchecked"


@pytest.mark.parametrize("content", [
    "not json", '{"no": "items"}', '{"items": []}', '{"items": [1]}',
    '{"items": [{"identifiers": ["10.1/x"]}]}', '{"items": [{"pdfinfo": "T"}]}'])
def test_find_work_reports_unusable_metadata_as_json(tmp_path, capsys, content):
    meta = tmp_path / "meta.json"
    meta.write_text(content)
    assert zi.cmd_find_work(_match_args(doi=None, metadata=str(meta))) == 1
    assert json.loads(capsys.readouterr().out)["verdict"] == "unchecked"
    assert zi.cmd_find_work(_match_args(doi=None,
                                        metadata=str(tmp_path / "gone"))) == 1
    assert "not extract-metadata output" in json.loads(
        capsys.readouterr().out)["error"]


@pytest.mark.integration
def test_find_work_keeps_an_extraction_error_as_a_row(use_live, tmp_path, capsys):
    meta = _meta_file(tmp_path, {"pdf": "/x/missing.pdf", "error": "not found"},
                      _meta_item(unique_doi()))
    assert zi.cmd_find_work(_match_args(doi=None, metadata=meta)) == 1
    first, second = json.loads(capsys.readouterr().out)["results"]
    assert first["error"] == "not found" and first["verdict"] == "unchecked"
    assert second["verdict"] == "none"


def identifiable_pdf(directory: Path) -> Path:
    """A staged PDF the lookup can look up: its name says the author and
    year (Surname2020-...), its first line a unique title."""
    directory.mkdir(parents=True, exist_ok=True)
    return make_pdf(directory / f"{unique_surname()}2020-{uuid.uuid4().hex[:8]}.pdf",
                    [unique_title(), f"nonce {uuid.uuid4().hex}"])


@pytest.mark.integration
def test_check_staging_dir_apply_needs_the_root_opt_in(use_live, tmp_path,
                                                       capsys):
    """--dir --apply writes only with the root's opt-in file; without it
    the apply fails and nothing is created."""
    pdf = identifiable_pdf(tmp_path / "scans")
    args = _dir_args(tmp_path, "scans")
    args.apply = True
    assert zi.cmd_check_staging(args) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["apply_status"] == "failed"
    assert ".zotero-reconcile.json" in report["apply_error"]
    assert report["summary"]["absent"] == 1
    title = zi.pdftotext_range(pdf, 1, 1).splitlines()[0].strip()
    assert use_live.titled(title) == []


def test_find_work_of_only_extraction_errors_asks_zotero_nothing(
        tmp_path, capsys, monkeypatch):
    meta = _meta_file(tmp_path, {"pdf": "/x/missing.pdf", "error": "not found"})
    monkeypatch.setattr(zi, "ensure_zotero", lambda: pytest.fail("Zotero asked"))
    assert zi.cmd_find_work(_match_args(doi=None, metadata=meta)) == 1
    (row,) = json.loads(capsys.readouterr().out)["results"]
    assert row["error"] == "not found" and row["verdict"] == "unchecked"


def test_check_staging_refuses_an_empty_dir(tmp_path, capsys):
    """`--dir "$UNSET"` must not become the whole repository."""
    assert zi.cmd_check_staging(_dir_args(tmp_path, "")) == 1
    assert json.loads(capsys.readouterr().out)["error"] == "--dir is empty"


def test_find_work_does_nothing_when_zotero_is_unavailable(tmp_path, capsys):
    """The lookup ensures Zotero is available: down and not launchable
    (ZOTERO_NO_LAUNCH), it does nothing and says so, even when fed
    extract-metadata output."""
    meta = tmp_path / "meta.json"
    meta.write_text(json.dumps({"items": [{"pdf": None, "identifiers": {
        "doi": "10.1/x"}, "pdfinfo": {}, "year_hint": None}]}))
    assert zi.cmd_find_work(_match_args(doi=None, metadata=str(meta))) == \
        zi.EXIT_UNAVAILABLE
    assert json.loads(capsys.readouterr().out)["zotero"] == "unavailable"


@pytest.mark.integration
def test_extraction_output_feeds_the_lookup(use_live, tmp_path, monkeypatch,
                                            capsys):
    """extract-metadata | find-work --metadata -: the DOI the PDF states is
    the one looked up, and the flags override the extracted values."""
    doi = unique_doi()
    title = unique_title()
    key = use_live.save(title, DOI=doi)
    pdf = make_pdf(tmp_path / "paper.pdf", [title, f"doi: {doi}"])
    assert zi.cmd_extract_metadata(argparse.Namespace(pdf=[str(pdf)])) == 0
    extracted = capsys.readouterr().out
    monkeypatch.setattr(sys, "stdin", io.StringIO(extracted))
    assert zi.cmd_find_work(_match_args(doi=None, metadata="-")) == 0
    (result,) = json.loads(capsys.readouterr().out)["results"]
    assert result["verdict"] == "match"
    assert result["matches"][0]["key"] == key
    assert result["query"]["doi"] == doi
    meta = tmp_path / "meta.json"
    meta.write_text(extracted)
    assert zi.cmd_find_work(_match_args(doi=unique_doi(), metadata=str(meta))) == 0
    (result,) = json.loads(capsys.readouterr().out)["results"]
    assert result["verdict"] == "none", "the --doi flag replaced the extracted DOI"


# ── author names ─────────────────────────────────────────────────────────────


def test_last_first_reorders_first_last():
    assert zi.last_first("Jane Smith") == "Smith, Jane"


def test_last_first_keeps_comma_form():
    assert zi.last_first("Smith, Jane") == "Smith, Jane"


def test_last_first_single_token_unchanged():
    assert zi.last_first("Plato") == "Plato"


# ── Zotero API item mapping (create-items) ───────────────────────────────────


def test_author_to_creator_splits_first_last():
    c = zi.author_to_creator("Jane Q. Smith")
    assert c == {"creatorType": "author", "firstName": "Jane Q.", "lastName": "Smith"}


def test_author_to_creator_single_name_uses_name_field():
    assert zi.author_to_creator("Aristotle") == {"creatorType": "author", "name": "Aristotle"}


def test_entry_to_zotero_item_journal_article():
    item = zi.entry_to_zotero_item(
        {"type": "JOUR", "title": "T", "authors": ["Jane Smith"], "year": 2015,
         "doi": "10.1/x", "journal": "Econometrica", "volume": "83",
         "issue": "4", "pages": "1467-1495", "numPages": 29}, owned,
    )
    assert item["itemType"] == "journalArticle"
    assert item["DOI"] == "10.1/x"
    assert item["publicationTitle"] == "Econometrica"
    assert item["pages"] == "1467-1495"
    # journalArticle has no numPages field: routed to extra as a CSL variable
    assert "number-of-pages: 29" in item["extra"]
    assert "numPages" not in item


def test_entry_to_zotero_item_book_numpages_and_isbn():
    item = zi.entry_to_zotero_item(
        {"type": "BOOK", "title": "B", "isbn": "978-0-13-468599-1",
         "numPages": 300, "doi": "10.2/y"}, owned,
    )
    assert item["itemType"] == "book"
    assert item["ISBN"] == "978-0-13-468599-1"
    assert item["numPages"] == "300"
    # schema 42 gives `book` a real DOI field; no need for the extra fallback
    assert item["DOI"] == "10.2/y"


def test_entry_to_zotero_item_unknown_type_falls_back_to_document():
    assert zi.entry_to_zotero_item({"type": "XXXX"}, owned)["itemType"] == "document"


# ── per-type field validity (the 400-from-Zotero class) ─────────────────────
#
# The mapper places each value by the running client's schema (pyzotero's
# item_type_fields). The pure tests here hand it a snapshot of that schema,
# the valid field names per item type (schema version 42, consulted
# 2026-08-14), as plain data; `test_zotero_schema_snapshot_matches_the_real_
# client` checks the snapshot against a real client, and `test_every_mapped_
# type_is_accepted_by_a_real_client` saves every type the mapper produces.

SCHEMA_42_FIELDS = {
    "journalArticle": (
        "title abstractNote publicationTitle publisher place date volume "
        "issue section partNumber partTitle pages series seriesTitle "
        "seriesText journalAbbreviation DOI citationKey url accessDate PMID "
        "PMCID ISSN archive archiveLocation shortTitle language "
        "libraryCatalog callNumber rights extra"
    ).split(),
    "book": (
        "title abstractNote series seriesNumber volume numberOfVolumes "
        "edition date publisher place originalDate originalPublisher "
        "originalPlace format numPages ISBN DOI citationKey url accessDate "
        "ISSN archive archiveLocation shortTitle language libraryCatalog "
        "callNumber rights extra"
    ).split(),
    "thesis": (
        "title abstractNote thesisType university place date series "
        "seriesNumber numPages DOI ISBN citationKey url accessDate ISSN "
        "archive archiveLocation shortTitle language libraryCatalog "
        "callNumber rights extra"
    ).split(),
    "report": (
        "title abstractNote reportNumber reportType institution place date "
        "seriesTitle seriesNumber pages DOI ISBN citationKey url accessDate "
        "ISSN archive archiveLocation shortTitle language libraryCatalog "
        "callNumber rights extra"
    ).split(),
    "bookSection": (
        "title abstractNote bookTitle series seriesNumber volume "
        "numberOfVolumes edition date publisher place originalDate "
        "originalPublisher originalPlace format pages ISBN DOI citationKey "
        "url accessDate ISSN archive archiveLocation shortTitle language "
        "libraryCatalog callNumber rights extra"
    ).split(),
    "conferencePaper": (
        "title abstractNote proceedingsTitle conferenceName publisher place "
        "date eventPlace volume issue numberOfVolumes pages series "
        "seriesNumber DOI ISBN citationKey url accessDate ISSN archive "
        "archiveLocation shortTitle language libraryCatalog callNumber "
        "rights extra"
    ).split(),
    "manuscript": (
        "title abstractNote manuscriptType institution place date numPages "
        "number DOI citationKey url accessDate archive archiveLocation "
        "shortTitle language libraryCatalog callNumber rights extra"
    ).split(),
    "newspaperArticle": (
        "title abstractNote publicationTitle publisher place date volume "
        "issue edition section pages ISSN DOI citationKey url accessDate "
        "archive archiveLocation shortTitle language libraryCatalog "
        "callNumber rights extra"
    ).split(),
    "magazineArticle": (
        "title abstractNote publicationTitle publisher place date volume "
        "issue pages ISSN DOI citationKey url accessDate archive "
        "archiveLocation shortTitle language libraryCatalog callNumber "
        "rights extra"
    ).split(),
    "patent": (
        "title abstractNote place country assignee issuingAuthority "
        "patentNumber filingDate pages applicationNumber priorityNumbers "
        "issueDate priorityDate references legalStatus DOI citationKey url "
        "accessDate shortTitle language rights extra"
    ).split(),
    "standard": (
        "title abstractNote organization committee type number versionNumber "
        "edition status date publisher place partNumber partTitle ISBN DOI "
        "citationKey url accessDate archive archiveLocation shortTitle "
        "numPages language libraryCatalog callNumber rights extra"
    ).split(),
    "webpage": (
        "title abstractNote websiteTitle websiteType date publisher place DOI "
        "citationKey url accessDate shortTitle language rights extra"
    ).split(),
    "document": (
        "title abstractNote type date publisher place DOI citationKey url "
        "accessDate archive archiveLocation shortTitle language "
        "libraryCatalog callNumber rights extra"
    ).split(),
}

def owned(item_type: str) -> frozenset[str]:
    """The schema snapshot in the shape schema_fields() returns."""
    return frozenset(SCHEMA_42_FIELDS[item_type])


# Every input key the mapper knows how to place, all at once. Rendering this
# for each item type is what exercises the whole cross-product.
MAXIMAL_ENTRY = {
    "title": "A Title",
    "shortTitle": "Short",
    "authors": ["Paul A. Samuelson"],
    "year": 1949,
    "doi": "10.1/xyz",
    "isbn": "978-0-13-468599-1",
    "issn": "0012-9682",
    "url": "https://example.org/a",
    "journal": "Container Name",
    "volume": "12",
    "issue": "3",
    "pages": "11-24",
    "numPages": 24,
    "publisher": "RAND Corporation",
    "place": "Santa Monica, CA",
    "number": "P-69",
    "genre": "RAND Paper",
    "conferenceName": "Annual Meeting",
    "edition": "2nd",
    "seriesNumber": "7",
    "language": "en",
    "abstract": "An   abstract.",
}


def _render(ris_type: str) -> dict:
    return zi.entry_to_zotero_item({**MAXIMAL_ENTRY, "type": ris_type}, owned)


def test_every_mapped_type_emits_only_fields_that_type_owns():
    """The defect class: a field posted to a type that lacks it is a 400."""
    offenders = {}
    for ris_type, zot_type in zi.RIS_TO_ZOTERO_TYPE.items():
        item = _render(ris_type)
        assert item["itemType"] == zot_type
        bad = sorted(
            k for k in item
            if k not in ("itemType", "creators", "collections")
            and k not in SCHEMA_42_FIELDS[zot_type]
        )
        if bad:
            offenders[zot_type] = bad
    assert offenders == {}, f"invalid fields per type: {offenders}"


def test_unknown_ris_type_fallback_emits_only_document_fields():
    item = zi.entry_to_zotero_item({**MAXIMAL_ENTRY, "type": "XXXX"}, owned)
    assert item["itemType"] == "document"
    bad = sorted(
        k for k in item
        if k not in ("itemType", "creators", "collections")
        and k not in SCHEMA_42_FIELDS["document"]
    )
    assert bad == []


def _placed_values(item: dict) -> set[str]:
    """Every value the item carries, as whole values — never as substrings.

    A substring sweep over the rendered item would let "7" pass because an
    ISBN happens to contain a 7. Compare complete field values and complete
    `label: value` lines from Extra instead.
    """
    placed = {str(v) for k, v in item.items()
              if k not in ("creators", "extra", "collections")}
    placed |= {line.split(": ", 1)[1]
               for line in item.get("extra", "").splitlines() if ": " in line}
    return placed


def test_no_input_value_is_dropped_for_any_mapped_type():
    """A value with no home on the target type lands in `extra`, never gone."""
    losses = {}
    for ris_type, zot_type in zi.RIS_TO_ZOTERO_TYPE.items():
        placed = _placed_values(_render(ris_type))
        missing = sorted(
            key for key, value in MAXIMAL_ENTRY.items()
            if key not in ("authors", "abstract") and str(value) not in placed
        )
        if missing:
            losses[zot_type] = missing
    assert losses == {}, f"values dropped silently: {losses}"


def test_report_publisher_is_institution_and_numpages_goes_to_extra():
    item = _render("RPRT")
    assert "publisher" not in item
    assert item["institution"] == "RAND Corporation"
    assert "numPages" not in item          # report has no numPages field
    assert item["pages"] == "11-24"        # the real page range keeps `pages`
    assert "number-of-pages: 24" in item["extra"]
    assert item["seriesTitle"] == "Container Name"
    assert item["DOI"] == "10.1/xyz"
    assert item["ISBN"] == "978-0-13-468599-1"
    assert "volume: 12" in item["extra"]   # report has no volume field
    assert "issue: 3" in item["extra"]


def test_thesis_publisher_becomes_university():
    item = _render("THES")
    assert "publisher" not in item
    assert item["university"] == "RAND Corporation"
    assert item["numPages"] == "24"
    assert "page: 11-24" in item["extra"]  # thesis has no pages field


def test_manuscript_publisher_becomes_institution():
    item = _render("MANSCPT")
    assert "publisher" not in item
    assert item["institution"] == "RAND Corporation"
    assert item["numPages"] == "24"
    assert "container-title: Container Name" in item["extra"]


def test_conference_paper_container_is_proceedings_title():
    item = _render("CONF")
    assert item["proceedingsTitle"] == "Container Name"
    assert "seriesTitle" not in item


def test_book_section_container_is_book_title():
    item = _render("CHAP")
    assert item["bookTitle"] == "Container Name"
    assert item["publisher"] == "RAND Corporation"


def test_book_container_is_series_and_issue_goes_to_extra():
    item = _render("BOOK")
    assert item["series"] == "Container Name"
    assert item["numPages"] == "24"
    assert "issue: 3" in item["extra"]
    assert "page: 11-24" in item["extra"]  # book has no pages field


def test_document_fallback_routes_pagination_and_container_to_extra():
    item = _render("GEN")
    assert item["publisher"] == "RAND Corporation"
    for label in ("container-title: Container Name", "volume: 12",
                  "issue: 3", "page: 11-24", "number-of-pages: 24",
                  "ISBN: 978-0-13-468599-1"):
        assert label in item["extra"]


# ── entry type codes ─────────────────────────────────────────────────────────


def test_every_mapped_zotero_type_has_a_pinned_field_set():
    """Guard the guard: a new type must arrive with its schema snapshot."""
    types = set(zi.RIS_TO_ZOTERO_TYPE.values()) | {"document"}
    assert types - set(SCHEMA_42_FIELDS) == set()


@pytest.mark.parametrize(("ris_code", "zot_type"), [
    ("CPAPER", "conferencePaper"),
    ("GOVDOC", "report"),
    ("PAT", "patent"),
    ("STAND", "standard"),
    ("UNPB", "manuscript"),
    ("WEB", "webpage"),
])
def test_previously_unmapped_codes_reach_their_type(ris_code, zot_type):
    assert _render(ris_code)["itemType"] == zot_type


def test_unrecognised_ris_code_records_what_it_degraded_from():
    """Degradation to `document` must leave a trace, not vanish."""
    item = zi.entry_to_zotero_item({"type": "ZZZZ", "title": "T"}, owned)
    assert item["itemType"] == "document"
    assert "Unmapped RIS type: ZZZZ" in item["extra"]


def test_patent_has_no_date_field_and_uses_issue_date():
    """`date` is not universal: patent carries issueDate instead."""
    item = _render("PAT")
    assert "date" not in item
    assert item["issueDate"] == "1949"
    assert item["patentNumber"] == "P-69"
    assert "publisher: RAND Corporation" in item["extra"]  # no home on patent


def test_standard_maps_number_and_genre():
    item = _render("STAND")
    assert item["number"] == "P-69"
    assert item["type"] == "RAND Paper"
    assert item["publisher"] == "RAND Corporation"
    assert item["numPages"] == "24"


def test_webpage_container_is_website_title():
    item = _render("WEB")
    assert item["websiteTitle"] == "Container Name"
    assert item["websiteType"] == "RAND Paper"
    assert "ISBN: 978-0-13-468599-1" in item["extra"]


def test_thesis_genre_is_thesis_type():
    assert _render("THES")["thesisType"] == "RAND Paper"


def test_conference_name_reaches_conference_paper_only():
    assert _render("CONF")["conferenceName"] == "Annual Meeting"
    assert "event-title: Annual Meeting" in _render("BOOK")["extra"]


# ── acceptance: the memorandum that produced the original 400s ──────────────


def test_rand_p69_memorandum_is_complete_in_one_pass():
    """Samuelson, *Market Mechanisms and Maximization*, RAND P-69 (1949).

    The import that took two 400s and then needed a hand-written PATCH for
    institution / reportNumber / place / reportType. One `create-items` must now
    produce the whole item.
    """
    item = zi.entry_to_zotero_item({
        "type": "RPRT",
        "title": "Market Mechanisms and Maximization",
        "authors": ["Paul A. Samuelson"],
        "year": 1949,
        "publisher": "The RAND Corporation",
        "place": "Santa Monica, CA",
        "number": "P-69",
        "genre": "RAND Paper",
        "numPages": 78,
    }, owned)
    assert item == {
        "itemType": "report",
        "title": "Market Mechanisms and Maximization",
        "creators": [{"creatorType": "author", "firstName": "Paul A.",
                      "lastName": "Samuelson"}],
        "date": "1949",
        "institution": "The RAND Corporation",
        "place": "Santa Monica, CA",
        "reportNumber": "P-69",
        "reportType": "RAND Paper",
        "extra": "number-of-pages: 78",
    }
    # and every key is one `report` actually owns
    assert [k for k in item if k not in ("itemType", "creators")
            and k not in SCHEMA_42_FIELDS["report"]] == []


# ── entry key validation ────────────────────────────────────────────────────


def test_unknown_entry_key_is_rejected_not_ignored():
    """An input key nobody reads is a silent loss; refuse it loudly."""
    with pytest.raises(SystemExit) as exc:
        zi.validate_entry_keys([{"title": "T", "reportNmbr": "P-69"}])
    assert "reportNmbr" in str(exc.value)


def test_known_entry_keys_pass_validation():
    zi.validate_entry_keys([dict(MAXIMAL_ENTRY, type="RPRT",
                                 pdf="/tmp/x.pdf", attach_pdf=True)])


@pytest.mark.integration
def test_zotero_schema_snapshot_matches_the_real_client(use_live):
    """Drift guard: the snapshot the pure tests use against a real client's
    schema, through the helper's own schema_fields. A failure means Zotero
    changed a type's field set; refresh the snapshot from it."""
    real = zi.schema_fields(zi.local_library())
    for zot_type, pinned in SCHEMA_42_FIELDS.items():
        assert set(pinned) == real(zot_type), f"{zot_type} field set drifted"


@pytest.mark.integration
def test_every_mapped_type_is_accepted_by_a_real_client(use_live):
    """The 400 class, end to end: every item the mapper builds from a
    maximal entry, one per type, is saved by a real Zotero."""
    real = zi.schema_fields(zi.local_library())
    z = use_live.client()
    types = sorted(zi.RIS_TO_ZOTERO_TYPE) + ["XXXX"]
    items = [zi.entry_to_zotero_item({**MAXIMAL_ENTRY, "type": t,
                                      "title": unique_title()}, real)
             for t in types]
    result = z.create_items(items)
    assert result["failed"] == {}, result["failed"]
    assert len(result["successful"]) == len(types)


# --- enrich: filling fields on an item that already exists ------------------
#
# enrich writes only with --edit, and then only what it would suggest: the
# decision of WHAT to suggest is where the mistakes live, so that is what
# these lock down. Each
# guard gets a red case, because a guard nobody has seen refuse is a guard
# nobody has tested.

def _item(**over):
    base = {"key": "AAAA1111", "itemType": "journalArticle", "version": 7,
            "title": "Optimum Utilization of the Transportation System",
            "DOI": "", "url": ""}
    base.update(over)
    return base


def test_plan_enrichment_fills_an_empty_field():
    patch, refused = zi.plan_enrichment(
        _item(), {"DOI": "10.2307/1907301"}, "Optimum Utilization")
    assert patch == {"DOI": "10.2307/1907301"}
    assert refused == []


def test_plan_enrichment_refuses_when_title_does_not_match():
    patch, refused = zi.plan_enrichment(
        _item(), {"DOI": "10.2307/1907301"}, "Theory of Games")
    assert patch == {}
    assert "wrong item" in refused[0]


def test_plan_enrichment_refuses_when_target_has_no_title():
    """'Could not check' must not read as 'checked and fine'."""
    patch, refused = zi.plan_enrichment(_item(title=""), {"DOI": "10.1/x"}, "Any")
    assert patch == {}
    assert "refusing to write blind" in refused[0]


def test_plan_enrichment_skips_a_field_already_correct():
    """A no-op write still bumps the version and shows up as an edit."""
    patch, refused = zi.plan_enrichment(
        _item(DOI="10.2307/1907301"), {"DOI": "10.2307/1907301"},
        "Optimum Utilization")
    assert patch == {}
    assert refused == []


def test_plan_enrichment_refuses_to_replace_a_different_value():
    patch, refused = zi.plan_enrichment(
        _item(DOI="10.9999/wrong"), {"DOI": "10.2307/1907301"},
        "Optimum Utilization")
    assert patch == {}
    assert "--overwrite" in refused[0]


def test_plan_enrichment_replaces_a_different_value_when_arbitrated():
    patch, refused = zi.plan_enrichment(
        _item(DOI="10.9999/wrong"), {"DOI": "10.2307/1907301"},
        "Optimum Utilization", overwrite=True)
    assert patch == {"DOI": "10.2307/1907301"}
    assert refused == []


def test_plan_enrichment_refuses_a_field_the_type_does_not_own():
    patch, refused = zi.plan_enrichment(
        _item(), {"doi": "10.2307/1907301"}, "Optimum Utilization")
    assert patch == {}
    assert "case-sensitive" in refused[0]


def test_plan_enrichment_writes_the_good_fields_and_refuses_the_rest():
    """One bad field must not block the others, nor pass unreported."""
    patch, refused = zi.plan_enrichment(
        _item(url="https://kept.example"),
        {"DOI": "10.2307/1907301", "url": "https://other.example"},
        "Optimum Utilization")
    assert patch == {"DOI": "10.2307/1907301"}
    assert len(refused) == 1 and "url" in refused[0]


def test_parse_set_splits_on_first_equals_only():
    assert zi.parse_set(["url=https://x.example/a=b"]) == {
        "url": "https://x.example/a=b"}


def test_parse_set_rejects_a_pair_without_equals():
    with pytest.raises(SystemExit):
        zi.parse_set(["DOI"])


def test_enrich_status_zero_when_everything_is_suggested():
    assert zi.enrich_status([{"status": "suggested"},
                             {"status": "nothing to change"}]) == 0


def test_enrich_status_nonzero_on_a_refusal():
    """Declining to act and acting must not share an exit code."""
    assert zi.enrich_status(
        [{"status": "nothing to change", "refused": ["DOI: already holds ..."]}]) == 1


def test_enrich_status_nonzero_on_a_missing_item():
    assert zi.enrich_status([{"status": "not found"}]) == 1


# --------------------------------------------------------------------------
# Reads through the local API of a real (throwaway) Zotero.
# --------------------------------------------------------------------------

# A well-formed item key no library holds.
ABSENT_KEY = "ZZZZ2222"


@pytest.mark.integration
def test_item_fields_lists_every_field_the_type_owns(use_live):
    title = unique_title()
    key = use_live.save(title, creators=(unique_surname(),))
    assert zi.find_item(ABSENT_KEY) is None
    z, item = zi.find_item(key)
    data = zi.item_fields(z, item)
    assert data["title"] == title and data["key"] == key
    assert data["itemType"] == "journalArticle"
    # Empty fields the type owns are filled in from itemTypeFields; a field
    # the type does not own stays absent, and so does bookkeeping.
    assert data["DOI"] == "" and data["publisher"] == ""
    assert "numPages" not in data and "institution" not in data
    assert "version" not in data and "collections" not in data


def _enrich_args(key, title, *sets, edit=False):
    return argparse.Namespace(jobs_file=None, item_key=key,
                              expect_title=title.split()[0], overwrite=False,
                              set=list(sets), library="user", edit=edit)


@pytest.mark.integration
def test_enrich_reports_the_edit_and_writes_nothing(use_live, capsys):
    title = unique_title()
    key = use_live.save(title, creators=(unique_surname(),),
                        url="https://old.example")
    before = use_live.item(key)["version"]
    args = _enrich_args(key, title, "DOI=10.2307/1907301",
                        "url=https://new.example", "version=99")
    assert zi.cmd_suggest_edits(args) == 1  # the url conflict is refused
    out = json.loads(capsys.readouterr().out)
    row = out["results"][0]
    assert row["suggested"] == [{"itemKey": key, "field": "DOI",
                                 "old": "", "new": "10.2307/1907301"}]
    assert any(r.startswith("url:") for r in row["refused"])
    assert any(r.startswith("version:") for r in row["refused"])
    assert out["source"] == zi.LIBRARY_SOURCE and out["edit"] is False
    item = use_live.item(key)
    assert item["version"] == before and not item["data"].get("DOI")
    assert item["data"]["url"] == "https://old.example"


@pytest.mark.integration
def test_enrich_edit_writes_the_suggested_fields_only(use_live, capsys):
    title = unique_title()
    key = use_live.save(title, creators=(unique_surname(),),
                        url="https://old.example")
    args = _enrich_args(key, title, "DOI=10.2307/1907301",
                        "url=https://new.example", edit=True)
    assert zi.cmd_suggest_edits(args) == 1  # the url conflict is still refused
    out = json.loads(capsys.readouterr().out)
    assert out["results"][0]["status"] == "written" and out["edit"] is True
    data = use_live.item(key)["data"]
    assert data["DOI"] == "10.2307/1907301"
    assert data["url"] == "https://old.example", "a refused field is not written"
    # Already correct now: a second --edit run has nothing to write.
    args.set = ["DOI=10.2307/1907301"]
    assert zi.cmd_suggest_edits(args) == 0
    assert json.loads(capsys.readouterr().out)["results"][0]["status"] == \
        "nothing to change"


@pytest.mark.integration
def test_attach_reports_the_step_and_writes_nothing(use_live, tmp_path, capsys):
    key = use_live.save(unique_title(), creators=(unique_surname(),))
    before = use_live.item(key)["version"]
    pdf = tmp_path / "Walley1991.pdf"
    pdf.write_bytes(b"%PDF")
    args = argparse.Namespace(parent=key, file=[str(pdf)], library="user",
                              edit=False)
    assert zi.cmd_suggest_attachments(args) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["suggested"] == [{"itemKey": key, "field": "attachment",
                                 "old": "", "new": str(pdf.resolve())}]
    assert out["source"] == zi.LIBRARY_SOURCE
    args.parent = ABSENT_KEY
    assert zi.cmd_suggest_attachments(args) == 1
    capsys.readouterr()
    assert use_live.item(key)["version"] == before
    assert use_live.children(key) == []


@pytest.mark.integration
def test_attach_edit_stores_the_file_under_the_item(use_live, tmp_path, capsys):
    key = use_live.save(unique_title(), creators=(unique_surname(),))
    pdf = make_pdf(tmp_path / "Walley1991.pdf", [unique_title()])
    args = argparse.Namespace(parent=key, file=[str(pdf)], library="user",
                              edit=True)
    assert zi.cmd_suggest_attachments(args) == 0
    (row,) = json.loads(capsys.readouterr().out)["attached"]
    assert row["status"] == "attached"
    (child,) = use_live.children(key)
    assert child["key"] == row["attachment"]
    assert child["data"]["md5"] == hashlib.md5(pdf.read_bytes()).hexdigest()


@pytest.mark.integration
def test_resolve_target_names_a_collection_and_its_library(use_live):
    top, sub = use_live.collections(unique_title(2), unique_title(2))
    assert zi.resolve_target("user", None) == "user"
    assert zi.resolve_target("user", sub) == "user"
    assert zi.resolve_target("all", top) == "user"
    with pytest.raises(ValueError, match="no single destination"):
        zi.resolve_target("all", None)
    with pytest.raises(ValueError, match="in no local library"):
        zi.resolve_target("user", ABSENT_KEY)


@pytest.fixture(scope="session")
def authz_zotero(zotero_factory):
    """A client of its own for the authorization test, so the dialog it
    leaves open cannot stall the shared one."""
    return zotero_factory("authz")


@pytest.mark.integration
def test_a_write_without_a_key_asks_zotero_and_gives_up_in_bound(
        authz_zotero, tmp_path, monkeypatch, capsys):
    """No stored key: the helper asks Zotero for one (its Allow / Always
    Allow / Deny dialog, here unanswered) for AUTHORIZE_WAIT seconds, then
    writes nothing and stores nothing."""
    zotero = zotero_live.point_helper_at(authz_zotero, monkeypatch)
    title = unique_title()
    key = zotero.save(title)
    key_file = tmp_path / "keys" / "zotero-local.env"
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(key_file))
    monkeypatch.setattr(zi, "AUTHORIZE_WAIT", 3.0)
    started = time.monotonic()
    rc = zi.cmd_suggest_edits(_enrich_args(key, title, "DOI=10.1/nokey", edit=True))
    # It waited for the dialog (positive control), then gave up in bound.
    assert 3.0 <= time.monotonic() - started < 30
    assert rc == 1
    (row,) = json.loads(capsys.readouterr().out)["results"]
    assert row["status"] == "not written"
    assert "no local API key" in row["error"]
    assert not zotero.item(key)["data"].get("DOI")
    assert not key_file.exists()


@pytest.fixture(scope="session")
def one_time_zotero(zotero_factory):
    """A client of its own whose profile also trusts a one-time key, the
    kind Zotero's "Allow" answer stores, so the dialog the test leaves open
    cannot stall the shared client."""
    return zotero_factory("one_time", one_time_key=True)


@pytest.mark.integration
def test_a_key_dropped_part_way_reports_the_fileless_attachment(
        one_time_zotero, tmp_path, monkeypatch, capsys):
    """B1, reproduced: the helper holds a key Zotero honours for one write.
    Storing a file creates the attachment item (consuming the key), then the
    upload is refused. The helper asks again (unanswered here), and its
    message says the attachment exists and may lack its file, never "nothing
    was written"; a later audit does not count that attachment as a file."""
    zotero = zotero_live.point_helper_at(one_time_zotero, monkeypatch)
    doi = unique_doi()
    key = zotero.save(unique_title(), creators=(unique_surname(),), DOI=doi)
    key_file = tmp_path / "keys" / "zotero-local.env"
    key_file.parent.mkdir(mode=0o700)
    key_file.write_text(f"ZOTERO_LOCAL_API_KEY={zotero.one_time_key}\n")
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(key_file))
    monkeypatch.setattr(zi, "AUTHORIZE_WAIT", 3.0)
    pdf = make_pdf(tmp_path / "Walley1991.pdf", [unique_title()])
    args = argparse.Namespace(parent=key, file=[str(pdf)], library="user",
                              edit=True)
    assert zi.cmd_suggest_attachments(args) == 1
    (row,) = json.loads(capsys.readouterr().out)["attached"]
    assert row["status"] == "failed"
    # Positive control: the one-time key did buy one write, the attachment.
    (child,) = zotero.children(key)
    assert child["data"]["linkMode"] == "imported_file"
    assert not child["data"].get("md5"), "the file never reached Zotero"
    assert f"attachment {child['key']} was created" in row["error"]
    assert "may lack its file" in row["error"]
    assert zi.NOTHING_WRITTEN not in row["error"]
    # A later lookup does not count that attachment as a stored file.
    (match,) = zi.find_work(zi.libraries(), doi=doi)["matches"]
    assert match["key"] == key and match["has_file"] is False


@pytest.fixture(scope="session")
def upfront_zotero(zotero_factory):
    """A client of its own for the up-front key request."""
    return zotero_factory("upfront")


@pytest.mark.integration
def test_storing_a_file_without_a_key_asks_before_writing_anything(
        upfront_zotero, tmp_path, monkeypatch, capsys):
    """A file takes several keyed writes, so the key is asked for before
    the first (the dialog, unanswered here): nothing is created."""
    zotero = zotero_live.point_helper_at(upfront_zotero, monkeypatch)
    key = zotero.save(unique_title(), creators=(unique_surname(),))
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE",
                       str(tmp_path / "keys" / "zotero-local.env"))
    monkeypatch.setattr(zi, "AUTHORIZE_WAIT", 3.0)
    pdf = make_pdf(tmp_path / "Walley1991.pdf", [unique_title()])
    started = time.monotonic()
    assert zi.cmd_suggest_attachments(argparse.Namespace(
        parent=key, file=[str(pdf)], library="user", edit=True)) == 1
    assert 3.0 <= time.monotonic() - started < 30
    (row,) = json.loads(capsys.readouterr().out)["attached"]
    assert row["status"] == "failed"
    assert "no local API key" in row["error"]
    assert row["error"].endswith(zi.NOTHING_WRITTEN)
    assert zotero.children(key) == []


@pytest.mark.integration
def test_a_throwaway_zotero_never_sees_the_authors_display(tmp_path, monkeypatch):
    """Author's order (2026-10-16): no Zotero window or key dialog on the
    author's screen. The client's environment carries a private Xvfb display
    and none of the caller's display, Wayland or session-bus variables."""
    if shutil.which("Xvfb") is None:
        pytest.skip("no Xvfb here")
    private = zotero_live.private_display()
    caller = ":4242" if private != ":4242" else ":4343"
    for name, value in (("DISPLAY", caller), ("WAYLAND_DISPLAY", "wayland-0"),
                        ("XAUTHORITY", "/home/x/.Xauthority"),
                        ("DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/user/1/bus")):
        monkeypatch.setenv(name, value)
    env = zotero_live.isolated_env(tmp_path / "home")
    assert env["DISPLAY"] == private != caller
    for name in ("WAYLAND_DISPLAY", "XAUTHORITY", "DBUS_SESSION_BUS_ADDRESS"):
        assert name not in env
    assert env["GDK_BACKEND"] == "x11"


def test_only_an_always_allow_key_is_accepted(tmp_path, monkeypatch):
    """Zotero's answer to its dialog, as pure logic: the dialog cannot be
    answered without a human, so the branches after it are tested here with
    the answer Zotero sends, {"key", "remember"}, and a key file under tmp.
    A one-time "Allow" key is refused, kept nowhere and never used
    (ticket 1116: "Always Allow" keys only)."""
    key_file = tmp_path / "keys" / "zotero-local.env"
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(key_file))
    z = zi.local_library()
    with pytest.raises(zi.KeyNotGranted, match="Always Allow") as exc:
        zi.accept_key(z, {"key": "a" * 32, "remember": False})
    assert str(exc.value).endswith(zi.NOTHING_WRITTEN)
    assert "a" * 32 not in str(exc.value)
    assert z.local_api_key is None and not key_file.exists()
    with pytest.raises(zi.KeyNotGranted, match="may lack its file"):
        zi.accept_key(z, {"key": "a" * 32, "remember": False},
                      saved="attachment X was created under P and may lack "
                            "its file")
    zi.accept_key(z, {"key": "b" * 32, "remember": True})
    assert z.local_api_key == "b" * 32
    assert zi.stored_key() == "b" * 32
    assert key_file.stat().st_mode & 0o777 == 0o600


def test_no_one_time_key_code_is_left():
    """Ticket 1116: the one-time-key path is deleted, not tested."""
    text = (SCRIPTS / "zotero.py").read_text()
    for gone in ("lasting", "key_lasting", "LocalLibrary"):
        assert gone not in text, gone


def test_the_key_file_is_private_and_never_printed(tmp_path, monkeypatch,
                                                    capsys):
    key_file = tmp_path / "keys" / "zotero-local.env"
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(key_file))
    assert zi.stored_key() is None
    zi.store_key("k" * 32)
    assert zi.stored_key() == "k" * 32
    assert key_file.stat().st_mode & 0o777 == 0o600
    assert key_file.parent.stat().st_mode & 0o777 == 0o700
    assert "k" * 32 not in capsys.readouterr().out


def test_the_key_is_never_written_through_a_symlink(tmp_path, monkeypatch):
    keys = tmp_path / "keys"
    keys.mkdir(mode=0o755)
    elsewhere = tmp_path / "elsewhere.env"
    elsewhere.write_text("untouched\n")
    (keys / "zotero-local.env").symlink_to(elsewhere)
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(keys / "zotero-local.env"))
    with pytest.raises(OSError, match="symlink"):
        zi.store_key("k" * 32)
    assert elsewhere.read_text() == "untouched\n"
    assert [p.name for p in keys.iterdir()] == ["zotero-local.env"]
    # Positive control: the same directory, no symlink, takes the key and is
    # made private.
    (keys / "zotero-local.env").unlink()
    zi.store_key("k" * 32)
    assert zi.stored_key() == "k" * 32
    assert keys.stat().st_mode & 0o777 == 0o700
    assert not (keys / "zotero-local.env").is_symlink()


def test_the_key_file_defaults_to_the_harness_keystore(monkeypatch):
    monkeypatch.delenv("ZOTERO_LOCAL_KEY_FILE")
    assert zi.key_file() == Path.home() / ".config" / "keys" / "zotero-local.env"


# --------------------------------------------------------------------------
# Zotero not up: launch it, except in a container; otherwise do nothing.
# --------------------------------------------------------------------------


def _match_args(**over):
    base = dict(doi="10.1/x", isbn=None, arxiv=None, handle=None, title=None,
                year=None, author=None, pdf=None, library="user", metadata=None)
    base.update(over)
    return argparse.Namespace(**base)


def test_unavailable_with_launching_opted_out_does_nothing(capsys):
    assert zi.cmd_find_work(_match_args()) == zi.EXIT_UNAVAILABLE
    captured = capsys.readouterr()
    out = json.loads(captured.out)
    assert out["zotero"] == "unavailable" and out["verdict"] == "unchecked"
    assert "ZOTERO_NO_LAUNCH is set" in out["error"]
    assert "Nothing was done" in out["error"]
    assert "ZOTERO_NO_LAUNCH" in captured.err


def test_unavailable_in_a_ci_runner_does_nothing(monkeypatch, capsys):
    monkeypatch.delenv("ZOTERO_NO_LAUNCH")
    monkeypatch.setenv("CI", "true")
    reason = zi.in_container()
    assert reason
    assert zi.cmd_find_work(_match_args()) == zi.EXIT_UNAVAILABLE
    out = json.loads(capsys.readouterr().out)
    assert reason in out["error"] and "Nothing was done" in out["error"]


@pytest.fixture
def launch_wrapper(zotero_binary, monkeypatch):
    """make(port): a `zotero` wrapper first on PATH that starts the real
    client on a throwaway profile listening on `port`, launching enabled.
    Skips unless the helper's own discovery finds the wrapper, so the
    unwrapped client (the author's profile) can never be launched.
    Teardown stops every client a wrapper started and deletes its files."""
    roots = []

    def make(port):
        root = Path(tempfile.mkdtemp(prefix="zotero-fixture-launch-"))
        roots.append(root)
        script, pidfile = zotero_live.write_launch_wrapper(root, zotero_binary, port)
        monkeypatch.setenv("PATH", f"{script.parent}{os.pathsep}{os.environ['PATH']}")
        monkeypatch.delenv("ZOTERO_NO_LAUNCH")
        if reason := zi.in_container():
            pytest.skip(f"launching is off here: {reason}")
        if zi.find_zotero_launcher() != [str(script)]:
            pytest.skip("the helper's discovery does not find the wrapper first")
        return pidfile

    yield make
    for root in roots:
        pidfile = root / "pid"
        if pidfile.exists() and pidfile.read_text().strip():
            zotero_live.stop_pid(int(pidfile.read_text()))
        shutil.rmtree(root, ignore_errors=True)


def _wait_for(predicate, timeout=60.0):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            return False
        time.sleep(0.2)
    return True


@pytest.mark.integration
def test_zotero_is_launched_when_not_running(launch_wrapper, monkeypatch, capsys):
    """The real client, found by the helper's discovery (PATH first) and
    started by its own Popen, detached: its own session, no terminal."""
    port = free_port()
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setattr(zi, "LAUNCH_POLL", 0.2)
    pidfile = launch_wrapper(port)
    assert zi.zotero_answers() is False
    assert zi.ensure_zotero() == "launched"
    pid = int(pidfile.read_text())
    assert os.getsid(pid) == pid, "the client leads its own session"
    if Path(f"/proc/{pid}/fd").is_dir():
        assert {os.readlink(f"/proc/{pid}/fd/{fd}") for fd in (0, 1, 2)} == {
            "/dev/null"}
    assert zi.ensure_zotero() == "running"
    assert _wait_for(lambda: zotero_live.answers(f"http://127.0.0.1:{port}"))
    assert zi.cmd_find_work(_match_args(doi=unique_doi())) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["results"][0]["verdict"] == "none"
    assert out["zotero"] == f"http://127.0.0.1:{port}"


@pytest.mark.integration
def test_a_launch_that_never_answers_gives_up_and_stops_what_it_launched(
        launch_wrapper, monkeypatch):
    """The launched client listens elsewhere: the helper gives up after
    LAUNCH_WAIT and stops the client it started, so no Zotero comes up
    after the helper reported doing nothing."""
    waited, actual = free_port(), free_port()
    assert waited != actual
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{waited}")
    monkeypatch.setattr(zi, "LAUNCH_WAIT", 3.0)
    monkeypatch.setattr(zi, "LAUNCH_POLL", 0.2)
    pidfile = launch_wrapper(actual)
    started = time.monotonic()
    with pytest.raises(zi.ZoteroUnavailable, match="stopped it"):
        zi.ensure_zotero()
    assert time.monotonic() - started < 3.0 + 20.0
    # Positive control: the helper did launch something, which wrote its pid.
    assert pidfile.exists() and pidfile.read_text().strip()
    pid = int(pidfile.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    assert not zotero_live.answers(f"http://127.0.0.1:{actual}")


def test_no_installation_to_launch_does_nothing(tmp_path, monkeypatch):
    empty = tmp_path / "empty-bin"
    empty.mkdir()
    monkeypatch.delenv("ZOTERO_NO_LAUNCH")
    monkeypatch.setenv("PATH", str(empty))
    monkeypatch.setenv("HOME", str(tmp_path))
    if reason := zi.in_container():
        pytest.skip(f"launching is off here: {reason}")
    if zi.find_zotero_launcher() is not None:
        pytest.skip("a Zotero is installed outside PATH and HOME")
    with pytest.raises(zi.ZoteroUnavailable, match="no Zotero installation"):
        zi.ensure_zotero()


@pytest.mark.integration
def test_local_api_disabled_names_the_setting(api_off_zotero, monkeypatch, capsys):
    """Zotero ships with the local API off: it answers 403 and the error
    names the setting to turn on."""
    zotero_live.point_helper_at(api_off_zotero, monkeypatch)
    assert zi.cmd_find_work(_match_args()) == 1
    out = json.loads(capsys.readouterr().out)
    assert "Allow other applications on this computer" in out["error"]
    assert "disabled" in out["error"]


@pytest.mark.parametrize("error,expected", [
    (ze.PreConditionFailedError("412 version mismatch"), "conflicting"),
    (ze.ConflictError("409 library locked"), "conflicting"),
    (ze.ServerIDMismatchError("412 server id"), "another Zotero instance"),
    (ze.HTTPError("400 bad request"), "Zotero 10 or later"),
])
def test_a_refusal_names_its_own_cause(error, expected):
    """A version conflict is not blamed on the Zotero version or setting."""
    message = str(zi.refusal(error))
    assert expected in message
    if expected != "Zotero 10 or later":
        assert zi.LOCAL_API_SETTING not in message


def test_a_lost_upload_is_zotero_unavailable_not_a_refusal():
    with pytest.raises(zi.ZoteroUnavailable, match="during an upload"):
        with zi.local_api():
            raise ze.UploadError("ConnectionError")


def test_an_edit_batch_keeps_its_written_rows_when_zotero_goes_away():
    """Pure batching logic, with a plain function as the per-job step:
    Zotero stopping at the second of three jobs keeps the first row."""
    jobs = [{"item_key": k} for k in ("A", "B", "C")]

    def one(job):
        if job["item_key"] == "B":
            raise zi.ZoteroUnavailable("gone")
        return {"itemKey": job["item_key"], "status": "written"}

    rows = zi.run_jobs(jobs, one, wrote=True)
    assert [(r["itemKey"], r["status"]) for r in rows] == [
        ("A", "written"), ("B", "unknown"), ("C", "not attempted")]
    assert zi.enrich_status(rows) == 1
    with pytest.raises(zi.ZoteroUnavailable):
        zi.run_jobs(jobs, one, wrote=False)


def test_a_trailing_slash_in_the_zotero_url_is_dropped(monkeypatch):
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", "http://127.0.0.1:8080/")
    assert zi.zotero_url() == "http://127.0.0.1:8080"
    assert zi.local_library().endpoint == "http://127.0.0.1:8080/api"


def test_a_listener_that_is_not_zotero_is_named_with_both_remedies():
    """What answers without Zotero's version header is named as not Zotero,
    with the variable that points the helper elsewhere and the setting.
    Pure: a non-Zotero listener would be a fake server, which the tests'
    author decision rules out, so the message is checked as built."""
    message = str(zi.not_zotero("http://127.0.0.1:8080", 404))
    assert "something other than Zotero answers at http://127.0.0.1:8080" in message
    assert "ZOTERO_CONNECTOR_URL" in message and "HTTP 404" in message
    assert zi.LOCAL_API_SETTING in message


@pytest.mark.integration
def test_an_account_check_with_the_api_disabled_names_the_setting(
        api_off_zotero, monkeypatch):
    zotero_live.point_helper_at(api_off_zotero, monkeypatch)
    with pytest.raises(zi.LocalAPIError, match="Allow other applications"):
        zi.local_account()


@pytest.mark.parametrize("marker,env,cgroup,expected", [
    (None, {"ZOTERO_NO_LAUNCH": "1"}, "", "ZOTERO_NO_LAUNCH is set"),
    ("/.dockerenv", {}, "", "/.dockerenv"),
    ("/run/.containerenv", {}, "", "/run/.containerenv"),
    (None, {"container": "podman"}, "", "container=podman"),
    (None, {"CI": "true"}, "", "CI is set"),
    (None, {}, "0::/kubepods/besteffort", "kubepods"),
    (None, {"DISPLAY": ""}, "", "no display"),
    (None, {"DISPLAY": ":0"}, "0::/user.slice", None),
])
def test_container_detection(monkeypatch, marker, env, cgroup, expected):
    """The real in_container() on given inputs: environment, marker files
    and the cgroup text."""
    for name in ("ZOTERO_NO_LAUNCH", "container", "CI", "GITHUB_ACTIONS",
                 "GITLAB_CI", "BUILDKITE", "JENKINS_URL", "DISPLAY",
                 "WAYLAND_DISPLAY"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        if value:
            monkeypatch.setenv(name, value)
    monkeypatch.setattr(os.path, "exists", lambda p: p == marker)
    real_read = Path.read_text
    monkeypatch.setattr(Path, "read_text", lambda self, *a, **k: (
        cgroup if str(self) == "/proc/1/cgroup" else real_read(self, *a, **k)))
    monkeypatch.setattr(zi.sys, "platform", "linux")
    reason = zi.in_container()
    assert (reason is None) if expected is None else (expected in reason)


# --------------------------------------------------------------------------
# Exact-tier ties (ticket 0570): two distinct records legitimately sharing one
# attachment md5 — 269 such clusters measured in the user library
# (docs/zotero-integration.md), none visible in Zotero's Duplicates pane.
# The old classify_matches returned "match" from matches[0] unconditionally at
# the exact tier, so the second record vanished without a trace.
# --------------------------------------------------------------------------


def test_classify_matches_exact_tie_is_ambiguous():
    tie = [{"certainty": "exact"}, {"certainty": "exact"}]
    assert zi.classify_matches(tie) == "ambiguous"


def test_classify_matches_single_exact_still_matches():
    """The common case must not change (ticket 0570 invariant)."""
    assert zi.classify_matches([{"certainty": "exact"},
                                {"certainty": "strong"}]) == "match"


def test_filename_hints_parses_surnames_and_year():
    assert zi._filename_hints("Afriat1967IER-Afriat1967.pdf") == (["afriat"], "1967")
    names, year = zi._filename_hints("BeraudNuma2024-Cournot-ch4.pdf")
    assert names == ["beraud", "numa"] and year == "2024"


def test_filename_hints_without_a_year():
    names, year = zi._filename_hints("Bewley-Bewley2002.pdf")
    assert year is None and "bewley" in names


# --------------------------------------------------------------------------
# corroborate(): a scraped identifier often belongs to a work the document
# CITES. Resolving it returns clean, confident, wrong metadata.
# --------------------------------------------------------------------------


def test_corroborate_accepts_metadata_present_in_the_document():
    doc = ("Mathematical Finance, Vol. 9, No. 3\n"
           "COHERENT MEASURES OF RISK\nPHILIPPE ARTZNER, FREDDY DELBAEN")
    out = zi.corroborate({"title": "Coherent Measures of Risk",
                          "authors": ["Artzner, Philippe"]}, doc)
    assert out["confidence"] == "corroborated"
    assert out["first_author_found"] is True


def test_corroborate_rejects_a_cited_works_metadata():
    """The real failure: a Cottle PDF whose scraped DOI resolved to Albers."""
    doc = ("The Basic George B. Dantzig\nRichard W. Cottle\n"
           "Stanford University, 2012\nA memoir of linear programming")
    out = zi.corroborate({"title": "Ronald Graham: laying the foundations of "
                                   "online optimization",
                          "authors": ["Albers, Susanne"]}, doc)
    assert out["confidence"] == "contradicted"
    assert "cited work" in out["reason"]


def test_corroborate_flags_partial_agreement_as_weak():
    doc = "Richard W. Cottle\nStanford\nsome unrelated running text here"
    out = zi.corroborate({"title": "A Completely Different Title Altogether",
                          "authors": ["Cottle, Richard"]}, doc)
    assert out["confidence"] == "weak"


def test_corroborate_without_text_is_unchecked_not_a_pass():
    out = zi.corroborate({"title": "Anything", "authors": ["X, Y"]}, "")
    assert out["confidence"] == "unchecked"


def test_corroborate_is_accent_insensitive():
    doc = "Ghouila-Houri, Existence d'une solution\nCRAS 1960"
    out = zi.corroborate({"title": "Existence d'une solution",
                          "authors": ["Ghouila-Houri, Alain"]}, doc)
    assert out["confidence"] in ("corroborated", "weak")


# --------------------------------------------------------------------------
# The title block: where a title lives on page 1 (find-work's text evidence).
# --------------------------------------------------------------------------


def test_front_matter_keeps_only_the_title_block():
    body = "\n".join(["TITLE LINE", "AUTHOR"] + [f"body line {i}" for i in range(80)])
    fm = zi._front_matter(body, lines=3)
    assert fm.splitlines() == ["TITLE LINE", "AUTHOR", "body line 0"]


def test_front_matter_drops_blank_lines():
    assert zi._front_matter("\n\nA\n\n\nB\n", lines=2).splitlines() == ["A", "B"]


# --------------------------------------------------------------------------
# Round-1 review fixes: a batch must survive one bad file, a mistyped path
# must not traceback, and the two match cascades must report the same split.
# --------------------------------------------------------------------------


def _dir_args(root, directory, **kw):
    return argparse.Namespace(root=str(root), dir=str(directory),
                              out=kw.get("out"), apply=False, edit=False,
                              library="user")


def test_check_staging_dir_missing_is_a_json_error_not_a_traceback(
        tmp_path, capsys):
    """A mistyped --dir is a discovery error, reported before Zotero is
    asked (it is down here): unchecked, rc 1, JSON."""
    assert zi.cmd_check_staging(_dir_args(tmp_path, "nope")) == 1
    out = json.loads(capsys.readouterr().out)
    assert any("not a directory" in e for e in out["errors"])
    assert out["verdict"] == "unchecked"
    assert "zotero" not in out, "nothing to compare: Zotero was not asked"


def test_check_staging_dir_outside_the_root_is_refused(tmp_path, capsys):
    root = tmp_path / "repo"
    (tmp_path / "elsewhere").mkdir()
    root.mkdir()
    assert zi.cmd_check_staging(_dir_args(root, "../elsewhere")) == 1
    out = json.loads(capsys.readouterr().out)
    assert any("outside repository" in e for e in out["errors"])


def test_check_staging_dir_mode_reads_no_bib(tmp_path):
    """--dir checks every staging file of that directory, nested ones
    included, and ignores the repository's BibTeX."""
    (tmp_path / "refs.bib").write_text("@article{a, title={T}, file={docs/a.pdf}}\n")
    scans = tmp_path / "scans" / "1960"
    scans.mkdir(parents=True)
    (scans / "Hoffman1960.pdf").write_bytes(b"%PDF-1.4")
    (scans / "notes.txt").write_text("not a staging extension")
    found = zi.discover_directory(tmp_path, Path("scans"))
    assert found["bib_files"] == [] and found["linked"] == []
    assert found["orphans"] == [(scans / "Hoffman1960.pdf").resolve()]
    assert found["errors"] == []


@pytest.mark.integration
@pytest.mark.skipif(os.geteuid() == 0, reason="root reads an unreadable file")
def test_check_staging_one_unreadable_file_does_not_abort_the_batch(
        use_live, tmp_path, capsys):
    """Losing 288 rows because file 3 could not be read is the expensive
    failure: the unreadable file becomes an error, the others rows."""
    staging = tmp_path / "staging"
    names = [identifiable_pdf(staging).name for _ in range(3)]
    (staging / names[1]).chmod(0)
    out = tmp_path / "report.json"
    try:
        assert zi.cmd_check_staging(_dir_args(tmp_path, "staging",
                                              out=str(out))) == 1
    finally:
        (staging / names[1]).chmod(0o600)
    capsys.readouterr()
    report = json.loads(out.read_text())
    assert len(report["rows"]) == 2
    assert any(names[1] in e and "Permission denied" in e
               for e in report["errors"])
    assert report["summary"]["absent"] == 2
    assert report["verdict"] == "unchecked"
    assert report["library"]["zotero"] == use_live.url


def test_corroborate_short_surname_does_not_match_inside_a_word():
    """`Li` inside `linear`/`published` is not evidence the author is Li."""
    text = ("Published in a linear programming volume, this article "
            "concerns entirely unrelated matters of policy analysis.")
    out = zi.corroborate({"title": "Quantum Entanglement Of Distant Photons",
                          "authors": ["Li, Wei"]}, text)
    assert out["first_author_found"] is False
    assert out["confidence"] == "contradicted"


def test_corroborate_still_finds_a_surname_that_is_really_there():
    out = zi.corroborate({"title": "Quantum Entanglement Of Distant Photons",
                          "authors": ["Li, Wei"]},
                         "Quantum entanglement of distant photons\nby Wei Li\n")
    assert out["first_author_found"] is True
    assert out["confidence"] == "corroborated"


def test_corroborate_title_with_no_usable_tokens_is_unchecked():
    """Nothing was checked, so the strongest negative verdict is wrong."""
    out = zi.corroborate({"title": "Is On At", "authors": ["Smith, J"]},
                         "an entirely unrelated document about turbines")
    assert out["confidence"] == "unchecked"
    assert out["reason"]


def test_file_md5_matches_a_whole_file_read(tmp_path):
    p = tmp_path / "big.pdf"
    p.write_bytes(b"x" * (3 * (1 << 20) + 17))  # spans several chunks
    assert zi.file_md5(p) == hashlib.md5(p.read_bytes()).hexdigest()


# --------------------------------------------------------------------------
# corroborate() is now reachable: inject refuses metadata its own PDF denies.
# --------------------------------------------------------------------------


def _pdf_with_text(tmp_path, name, text, monkeypatch):
    p = tmp_path / name
    p.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(zi, "pdftotext_range", lambda path, a, b: text)
    return p


def test_corroborate_entry_flags_a_cited_works_metadata(tmp_path, monkeypatch):
    pdf = _pdf_with_text(tmp_path, "cottle.pdf",
                         "The Basic George B. Dantzig\nRichard W. Cottle\n",
                         monkeypatch)
    out = zi.corroborate_entry({"title": "Ronald Graham: laying the foundations "
                                         "of online optimization",
                                "authors": ["Albers, Susanne"], "pdf": str(pdf)})
    assert out["confidence"] == "contradicted"


def test_corroborate_entry_without_a_pdf_is_unchecked():
    out = zi.corroborate_entry({"title": "T", "authors": ["A, B"]})
    assert out["confidence"] == "unchecked"


def _inject_args(entries, **over):
    base = dict(entries_json=json.dumps(entries), entries_file=None,
                collection=None, library="user",
                dry_run=False, skip_corroboration=False, force=False)
    base.update(over)
    return argparse.Namespace(**base)


def _entry(directory, title=None, surname=None, year="2020", **extra):
    """An inject entry whose PDF's front matter corroborates it."""
    title = title or unique_title()
    surname = surname or unique_surname()
    pdf = paper_pdf(directory, title, surname)
    return {"title": title, "authors": [f"{surname}, Jane"], "year": year,
            "pdf": str(pdf), **extra}


def test_inject_refuses_contradicted_metadata(tmp_path, monkeypatch, capsys):
    """Refused before Zotero is asked: Zotero is down here, and the exit
    status is the refusal's 1, not the unavailable 75."""
    pdf = _pdf_with_text(tmp_path, "cottle.pdf",
                         "The Basic George B. Dantzig\nRichard W. Cottle\n",
                         monkeypatch)
    entries = tmp_path / "e.json"
    entries.write_text(json.dumps([{
        "type": "JOUR", "title": "Ronald Graham: laying the foundations of "
                                 "online optimization",
        "authors": ["Albers, Susanne"], "pdf": str(pdf), "attach_pdf": True}]))
    args = _inject_args(None, entries_json=None, entries_file=str(entries))
    rc = zi.cmd_create_items(args)
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert out["error"] == "metadata contradicted by the document"


@pytest.mark.integration
def test_inject_skip_corroboration_lets_it_through(use_live, tmp_path, capsys):
    title = unique_title()
    pdf = make_pdf(tmp_path / f"{uuid.uuid4().hex[:10]}.pdf",
                   ["The Basic George B. Dantzig", "Richard W. Cottle",
                    uuid.uuid4().hex])
    args = _inject_args([{"type": "JOUR", "title": title,
                          "authors": ["Albers, Susanne"], "year": "2020",
                          "pdf": str(pdf)}], skip_corroboration=True)
    assert zi.cmd_create_items(args) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["results"][0]["status"] == "created"
    assert out["results"][0]["corroboration"] == "contradicted"
    assert use_live.find(title)["data"]["creators"][0]["lastName"] == "Albers"


@pytest.mark.integration
def test_inject_dry_run_reports_corroboration_and_creates_nothing(
        use_live, tmp_path, capsys):
    """The item JSON is built against the running client's schema, and
    nothing is created."""
    entry = _entry(tmp_path, type="RPRT", publisher="RAND", numPages=78)
    entries = tmp_path / "e.json"
    entries.write_text(json.dumps([entry]))
    args = argparse.Namespace(entries_json=None, entries_file=str(entries),
                              dry_run=True, skip_corroboration=False)
    assert zi.cmd_create_items(args) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["corroboration"][0]["confidence"] == "corroborated"
    (item,) = out["items"]
    assert item["title"] == entry["title"] and item["institution"] == "RAND"
    assert item["extra"] == "number-of-pages: 78"
    assert use_live.titled(entry["title"]) == []


def test_inject_does_nothing_when_zotero_is_unavailable(capsys):
    """Nothing answers and nothing may be launched: no partial action, a
    clear message, and the unavailable status."""
    args = _inject_args([{"title": "New Paper", "authors": ["Smith, Jane"],
                          "year": "2020"}])
    assert zi.cmd_create_items(args) == zi.EXIT_UNAVAILABLE
    captured = capsys.readouterr()
    out = json.loads(captured.out)
    assert out["zotero"] == "unavailable"
    assert "Zotero is not running" in captured.err
    assert "Nothing was done" in out["error"]


def test_the_zotero_url_must_stay_on_this_machine(monkeypatch):
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", "http://zotero.example.org:24119")
    with pytest.raises(zi.LocalAPIError, match="local-only"):
        zi.zotero_answers()
    with pytest.raises(zi.LocalAPIError, match="local-only"):
        zi.local_library()
    with pytest.raises(zi.LocalAPIError, match="local-only"):
        zi.local_account()


@pytest.mark.integration
def test_inject_files_into_a_collection_then_attaches(use_live, tmp_path, capsys):
    """The item is created in the collection, then its PDF is stored under
    it."""
    (key,) = use_live.collections(unique_title(2))
    doi = unique_doi()
    entry = _entry(tmp_path, doi=doi, attach_pdf=True)
    assert zi.cmd_create_items(_inject_args([entry], collection=key)) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["collection"] == key and out["library_id"] == "user"
    assert out["results"][0]["status"] == "created"
    assert out["results"][0]["key"] == use_live.find(entry["title"])["key"]
    assert out["results"][0]["attachment"] == Path(entry["pdf"]).name
    item = use_live.find(entry["title"])
    assert item["data"]["DOI"] == doi
    assert item["data"]["collections"] == [key]
    (att,) = use_live.children(item["key"])
    assert att["data"]["md5"] == hashlib.md5(Path(entry["pdf"]).read_bytes()).hexdigest()


@pytest.mark.integration
def test_inject_error_after_the_read_is_structured(use_live, tmp_path, capsys):
    entry = _entry(tmp_path)
    assert zi.cmd_create_items(_inject_args([entry], collection=ABSENT_KEY)) == 1
    assert "in no local library" in json.loads(capsys.readouterr().out)["error"]
    assert use_live.titled(entry["title"]) == []


@pytest.mark.integration
def test_inject_refuses_a_work_already_in_the_library(use_live, tmp_path, capsys):
    doi = unique_doi()
    title = unique_title()
    key = use_live.save(title, creators=("Smith",), DOI=doi)
    entry = _entry(tmp_path, title=title, surname="Smith", doi=doi)
    assert zi.cmd_create_items(_inject_args([entry])) == 1
    out = json.loads(capsys.readouterr().out)
    assert "duplicate" in out["results"][0]["error"]
    assert out["results"][0]["matches"][0]["key"] == key
    assert len(use_live.titled(title)) == 1


@pytest.mark.integration
def test_second_run_reads_the_library_afresh(use_live, tmp_path, capsys):
    """Stateless: nothing is kept between runs. Two runs on one work create
    it once because the second run reads, live, what the first one saved."""
    title, surname, doi = unique_title(), unique_surname(), unique_doi()
    for n in range(2):
        entry = _entry(tmp_path, title=title, surname=surname, doi=doi)
        assert zi.cmd_create_items(_inject_args([entry])) == (0 if n == 0 else 1)
        result = json.loads(capsys.readouterr().out)
        if n == 1:
            assert "duplicate" in result["results"][0]["error"]
    assert len(use_live.titled(title)) == 1


@pytest.mark.integration
@pytest.mark.parametrize("count,second", [(2, 1), (6, 5)])
def test_a_batch_creates_a_work_once_when_two_entries_share_a_doi(
        use_live, tmp_path, capsys, count, second):
    """Entries are looked up and saved one at a time, live: the second
    entry with the DOI finds the item the first one just created."""
    shared = unique_doi()
    entries = [_entry(tmp_path, doi=shared if n in (0, second) else unique_doi())
               for n in range(count)]
    assert zi.cmd_create_items(_inject_args(entries)) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["results"][0]["status"] == "created"
    assert "duplicate" in out["results"][second]["error"]
    assert out["results"][second]["matches"][0]["key"] == out["results"][0]["key"]
    assert out["results"][second]["matches"][0]["why"] == ["doi"]
    created = {n for n, e in enumerate(entries) if use_live.titled(e["title"])}
    assert created == set(range(count)) - {second}


@pytest.mark.integration
def test_a_batch_refuses_a_second_entry_carrying_the_same_file(
        use_live, tmp_path, capsys):
    """Zotero has no search by md5, so the batch remembers what it stored:
    the same PDF under different metadata is not created twice."""
    first = _entry(tmp_path, attach_pdf=True)
    second = _entry(tmp_path, attach_pdf=True)
    second["pdf"] = first["pdf"]
    # The PDF names the first entry's work, so the second is contradicted;
    # skipping that check leaves the file guard as the only one to fire.
    assert zi.cmd_create_items(_inject_args([first, second],
                                            skip_corroboration=True)) == 1
    out = json.loads(capsys.readouterr().out)
    assert out["results"][0]["status"] == "created"
    assert "same file as entry 0" in out["results"][1]["error"]
    assert use_live.titled(second["title"]) == []


def test_a_slow_create_items_inside_check_staging_apply_is_slow(
        tmp_path, monkeypatch):
    """create-items reports a slow read as a payload; the apply turns it
    back into ZoteroSlow (verdict zotero_slow, exit 74), not apply_failed."""
    def slow(args):
        zi.emit_json({"zotero": "slow", "error": "timed out",
                      "verdict": "unchecked"})
        return zi.EXIT_SLOW

    monkeypatch.setattr(zi, "cmd_create_items", slow)
    monkeypatch.setattr(zi, "audit_sources", lambda root, found, libs: (
        [{"verdict": "absent", "path": "docs/a.pdf"}], []))
    monkeypatch.setattr(zi, "bib_to_inject_entry", lambda bib, path: {
        "title": "T", "authors": ["A, B"], "year": "2020", "pdf": str(path)})
    monkeypatch.setattr(zi, "corroborate_entry",
                        lambda entry: {"confidence": "corroborated"})
    found = {"linked": [], "orphans": [], "errors": [], "bib_files": [],
             "staging_dirs": []}
    with pytest.raises(zi.ZoteroSlow, match="timed out"):
        zi.reconcile_apply(tmp_path, found, "user", json.loads(OPT_IN),
                           argparse.Namespace(library="user"))


@pytest.mark.integration
def test_inject_allows_generic_title_when_author_or_year_differs(
        use_live, tmp_path, capsys):
    title = unique_title()
    entries = [_entry(tmp_path, title=title, year="2020"),
               _entry(tmp_path, title=title, year="2021")]
    assert zi.cmd_create_items(_inject_args(entries)) == 0
    capsys.readouterr()
    assert len(use_live.titled(title)) == 2


@contextlib.contextmanager
def recording_proxy():
    """A real TCP listener standing where a proxy would: it records the
    first bytes of every connection and closes it."""
    seen = []
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen()
    sock.settimeout(0.2)
    stop = threading.Event()

    def serve():
        while not stop.is_set():
            try:
                conn, _ = sock.accept()
            except (TimeoutError, socket.timeout):
                continue
            except OSError:
                return
            with conn:
                conn.settimeout(2)
                try:
                    seen.append(conn.recv(4096))
                except OSError:
                    seen.append(b"")

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{sock.getsockname()[1]}", seen
    finally:
        stop.set()
        thread.join()
        sock.close()


@pytest.mark.integration
def test_no_request_goes_through_a_proxy(use_live, tmp_path, monkeypatch, capsys):
    """The loopback check would be moot if a proxy relayed the PDF. With
    every proxy variable aimed at a recorder, the helper's reads, item
    lookup and an inject reach the real client and the recorder sees
    nothing; an opener built from the same environment, which is what a
    bare urllib.request.urlopen uses, does reach the recorder."""
    title = unique_title()
    key = use_live.save(title, creators=(unique_surname(),))
    entry = _entry(tmp_path, attach_pdf=True)
    with recording_proxy() as (proxy, seen):
        for name in ("http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY",
                     "all_proxy", "ALL_PROXY"):
            monkeypatch.setenv(name, proxy)
        monkeypatch.delenv("no_proxy", raising=False)
        monkeypatch.delenv("NO_PROXY", raising=False)
        # Positive control: the probe can fire.
        with pytest.raises(OSError):
            urllib.request.build_opener().open(f"{use_live.url}/api/",
                                               timeout=5)
        assert _wait_for(lambda: len(seen) == 1, timeout=5)
        assert seen[0].startswith(b"GET http://127.0.0.1:")
        seen.clear()

        assert zi.ensure_zotero() == "running"
        assert key in {w["key"] for w in zi.search_works(
            zi.local_library(), "user", title)}
        assert zi.find_item(key)[1]["data"]["title"] == title
        assert zi.cmd_create_items(_inject_args([entry])) == 0
        assert json.loads(capsys.readouterr().out)["results"][0]["attachment"]
        time.sleep(0.5)  # let a stray connection land before looking
        assert seen == [], "a request went through the proxy"
    assert use_live.children(use_live.find(entry["title"])["key"])


def test_the_client_takes_no_proxy_and_follows_no_redirect(monkeypatch):
    """Built under http_proxy, the client still ignores it, and it never
    follows a redirect: a loopback URL stays on the loopback. pyzotero's
    own default client follows redirects, so the helper hands it this one."""
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:9")
    client = zi.local_library().client
    assert client.trust_env is False and client.follow_redirects is False
    assert zi.http_client().trust_env is False


def test_check_staging_discovers_nonstandard_bib_and_orphans(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    linked = docs / "linked.pdf"
    orphan = docs / "orphan.pdf"
    linked.write_bytes(b"linked")
    orphan.write_bytes(b"orphan")
    (tmp_path / "reading.bib").write_text(
        "@article{levin, title={Useful Paper}, file={docs/linked.pdf}}\n"
    )

    found = zi.discover_reconcile_files(tmp_path)

    assert [p.name for p in found["bib_files"]] == ["reading.bib"]
    assert [(r["key"], r["path"]) for r in found["linked"]] == [
        ("levin", linked)
    ]
    assert found["orphans"] == [orphan]
    assert found["errors"] == []


def _reconcile_args(root, **over):
    base = dict(root=str(root), apply=False, out=None, library="user", dir=None)
    base.update(over)
    return argparse.Namespace(**base)


OPT_IN = '{"apply": true, "user_id": "1"}'


def _staged_bib_paper(root, opt_in=OPT_IN, *, title=None, surname=None,
                      year="2020"):
    """docs/<unique>.pdf, cited with its metadata by sources.bib; the PDF's
    front matter states the same title and author."""
    title = title or unique_title()
    surname = surname or unique_surname()
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    pdf = paper_pdf(docs, title, surname)
    (root / "sources.bib").write_text(
        f"@article{{one, title={{{title}}}, author={{{surname}, Jane}}, "
        f"year={{{year}}}, file={{docs/{pdf.name}}}}}\n")
    if opt_in is not None:
        (root / ".zotero-reconcile.json").write_text(opt_in)
    return pdf


def _quiet_pdf_tools(monkeypatch):
    monkeypatch.setattr(zi, "_pdf_front_text", lambda _: "")
    monkeypatch.setattr(zi, "pdfinfo", lambda _: {})


def test_check_staging_with_nothing_staged_skips_the_library(tmp_path, capsys):
    """Zotero is down here: a "checked" verdict, not "zotero_unavailable",
    shows it was never asked."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "notes.md").write_text("no staged documents")
    assert zi.cmd_check_staging(_reconcile_args(tmp_path)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "checked" and report["files"] == 0


@pytest.mark.parametrize("staging", [False, True])
def test_check_staging_empty_report_writes_out_with_the_full_keys(
        tmp_path, capsys, staging):
    if staging:
        (tmp_path / "docs").mkdir()
    out = tmp_path / "report.json"
    assert zi.cmd_check_staging(_reconcile_args(tmp_path, out=str(out))) == 0
    report = json.loads(out.read_text())
    assert report["verdict"] == ("checked" if staging else "no_staging")
    assert report["bib_files"] == []
    assert report["staging_dirs"] == (["docs"] if staging else [])
    assert report["actions"] == {} and report["rows"] == []
    full = set(zi.reconcile_report(tmp_path, zi.discover_reconcile_files(tmp_path),
                                   [], []))
    assert set(report) == full
    assert not {"index_fetched", "user_id", "api_key"} & set(report)
    assert "rows" not in json.loads(capsys.readouterr().out)


def _empty_apply(root, staging, problem):
    if staging:
        (root / "docs").mkdir()
    if problem != "missing":
        config = {"apply": True, "user_id": "2" if problem == "wrong_user" else "1"}
        (root / ".zotero-reconcile.json").write_text(
            "[]" if problem == "invalid" else json.dumps(config))
    out = root / "report.json"
    rc = zi.cmd_check_staging(_reconcile_args(root, apply=True, out=str(out)))
    return rc, json.loads(out.read_text())


@pytest.mark.parametrize("staging", [False, True])
@pytest.mark.parametrize("problem", ["missing", "invalid"])
def test_check_staging_empty_apply_checks_the_opt_in_file_first(
        tmp_path, capsys, staging, problem):
    """A broken opt-in fails before Zotero is asked: Zotero is down here,
    yet the verdict is not "zotero_unavailable"."""
    rc, report = _empty_apply(tmp_path, staging, problem)
    assert rc == 1
    assert report["apply_status"] == "failed" and "apply_error" in report
    assert report["verdict"] != "zotero_unavailable"
    capsys.readouterr()


@pytest.mark.integration
@pytest.mark.parametrize("staging", [False, True])
@pytest.mark.parametrize("problem", ["wrong_user", "valid"])
def test_check_staging_empty_apply_checks_the_account(
        use_live, tmp_path, capsys, staging, problem):
    """A well-formed opt-in is checked against the account Zotero is
    signed in as; the throwaway client is signed in to none, so even the
    matching file is refused, and nothing is done."""
    rc, report = _empty_apply(tmp_path, staging, problem)
    assert rc == 1
    assert report["apply_status"] == "failed"
    assert "signed in to no account" in report["apply_error"]
    assert report["library"]["source"] == zi.LIBRARY_SOURCE
    capsys.readouterr()


@pytest.mark.integration
def test_check_staging_staged_file_reads_the_library(use_live, tmp_path, capsys):
    identifiable_pdf(tmp_path / "docs")
    assert zi.cmd_check_staging(_reconcile_args(tmp_path)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "checked" and report["files"] == 1
    assert report["library"]["zotero"] == use_live.url
    assert report["rows"][0]["verdict"] == "absent"


@pytest.mark.parametrize("apply", [False, True])
def test_check_staging_without_zotero_is_a_clean_no_op_and_still_writes_out(
        tmp_path, capsys, apply):
    """Unavailable is not a crash: exit 0, verdict zotero_unavailable,
    nothing compared, nothing created, and --out still written."""
    _staged_bib_paper(tmp_path)
    out = tmp_path / "report.json"
    args = _reconcile_args(tmp_path, out=str(out), apply=apply)
    assert zi.cmd_check_staging(args) == 0
    report = json.loads(out.read_text())
    assert report["verdict"] == "zotero_unavailable"
    assert report["zotero"]["status"] == "unavailable"
    assert "ZOTERO_NO_LAUNCH" in report["zotero"]["reason"]
    assert report["rows"] == [] and report["summary"] == {}
    assert "ZOTERO_NO_LAUNCH" in capsys.readouterr().err


def test_check_staging_without_zotero_still_reports_discovery_errors(tmp_path, capsys):
    """A broken bib is the project's fault, not Zotero's: unavailable must not
    turn it into a clean no-op."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ok.pdf").write_bytes(b"ok")
    (tmp_path / "sources.bib").write_text(
        "@article{ok, file={docs/ok.pdf}}\n"
        "@article{broken, file={docs/lost.pdf}\n"
    )
    out = tmp_path / "report.json"
    assert zi.cmd_check_staging(_reconcile_args(tmp_path, out=str(out))) == 1
    report = json.loads(out.read_text())
    # Nothing could be compared: unchecked, without asking Zotero.
    assert report["verdict"] == "unchecked" and "zotero" not in report
    assert report["errors"]
    capsys.readouterr()


def test_check_staging_undefined_bib_macro_fails_closed_and_still_writes_out(
        tmp_path, capsys):
    """bibtexparser raises on an undefined @string macro (UndefinedString, a
    KeyError): that file is a discovery error, not a crash, and --out is
    still written with the full report."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ok.pdf").write_bytes(b"ok")
    (tmp_path / "refs.bib").write_text(
        "@article{ok, title={T}, journal=undefmacro, file={docs/ok.pdf}}\n")
    found = zi.discover_reconcile_files(tmp_path)
    assert any("undefmacro" in e for e in found["errors"]), found["errors"]
    out = tmp_path / "report.json"
    assert zi.cmd_check_staging(_reconcile_args(tmp_path, out=str(out))) == 1
    report = json.loads(out.read_text())
    assert report["verdict"] == "unchecked"
    assert any("undefmacro" in e for e in report["errors"])
    capsys.readouterr()


def test_check_staging_empty_apply_without_zotero_is_a_clean_no_op(tmp_path, capsys):
    (tmp_path / ".zotero-reconcile.json").write_text(OPT_IN)
    out = tmp_path / "report.json"
    assert zi.cmd_check_staging(_reconcile_args(tmp_path, out=str(out), apply=True)) == 0
    assert json.loads(out.read_text())["verdict"] == "zotero_unavailable"
    capsys.readouterr()


@pytest.mark.integration
def test_check_staging_with_the_local_api_disabled_is_unchecked(
        api_off_zotero, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", api_off_zotero.url)
    _staged_bib_paper(tmp_path)
    out = tmp_path / "report.json"
    assert zi.cmd_check_staging(_reconcile_args(tmp_path, out=str(out))) == 1
    report = json.loads(out.read_text())
    assert report["verdict"] == "unchecked"
    assert any("Allow other applications" in e for e in report["errors"])
    capsys.readouterr()


@pytest.mark.integration
def test_check_staging_apply_refuses_without_the_signed_in_account(
        use_live, tmp_path, capsys):
    """--apply needs the project opt-in AND its user_id to be the account
    Zotero is signed in as. The throwaway client is signed in to none:
    the apply is refused, nothing is created, the report still stands."""
    pdf = _staged_bib_paper(tmp_path, opt_in=None)
    title = zi._bib_entries(tmp_path / "sources.bib")[0]["title"]
    args = _reconcile_args(tmp_path, apply=True)
    assert zi.cmd_check_staging(args) == 1
    report = json.loads(capsys.readouterr().out)
    assert "apply_error" in report and report["apply_status"] == "failed"
    assert report["summary"]["absent"] == 1
    (tmp_path / ".zotero-reconcile.json").write_text(OPT_IN)
    assert zi.cmd_check_staging(args) == 1
    report = json.loads(capsys.readouterr().out)
    assert "signed in to no account" in report["apply_error"]
    assert report["rows"][0]["path"] == f"docs/{pdf.name}"
    assert use_live.titled(title) == []


def test_check_staging_apply_config_checks_the_account(tmp_path):
    opt_in = tmp_path / ".zotero-reconcile.json"
    opt_in.write_text('{"apply": true, "user_id": "2"}')
    assert zi.reconcile_apply_config(tmp_path, "2")["user_id"] == "2"
    assert zi.reconcile_apply_config(tmp_path, 2)["apply"] is True
    with pytest.raises(ValueError, match="differs from the account"):
        zi.reconcile_apply_config(tmp_path, "1")
    with pytest.raises(ValueError, match="signed in to no account"):
        zi.reconcile_apply_config(tmp_path, None)
    assert zi.reconcile_apply_config(tmp_path, None, check_account=False)
    opt_in.write_text('{"apply": "yes", "user_id": "2"}')
    with pytest.raises(ValueError, match="apply must be true"):
        zi.reconcile_apply_config(tmp_path, "2")


def _apply(root, config=None):
    """The apply step of a sweep, into the user library."""
    found = zi.discover_reconcile_files(root)
    return zi.reconcile_apply(root, found, "user", config or json.loads(OPT_IN),
                              argparse.Namespace(library="user"))


@pytest.mark.integration
def test_check_staging_apply_reports_fresh_match_on_no_write_replay(
        use_live, tmp_path):
    """The file is already stored: the fresh read says identical, nothing
    is created."""
    title, surname = unique_title(), unique_surname()
    pdf = _staged_bib_paper(tmp_path, title=title, surname=surname)
    copy = tmp_path / "stored-copy.pdf"
    copy.write_bytes(pdf.read_bytes())
    key = use_live.save(title, creators=(surname,), pdf=copy)
    report, rc = _apply(tmp_path)
    assert rc == 0
    assert report["summary"] == {"identical": 1}
    assert report["rows"][0]["verdict"] == "identical"
    assert report["rows"][0]["zotero_key"] == key
    assert report["rows"][0]["source"] == "bib"
    assert report["library"]["zotero"] == use_live.url
    assert report["applied"] == [] and report["apply_status"] == "nothing"
    assert len(use_live.titled(title)) == 1


@pytest.mark.integration
def test_check_staging_apply_imports_a_corroborated_absent_pdf(use_live, tmp_path):
    title, surname = unique_title(), unique_surname()
    pdf = _staged_bib_paper(tmp_path, title=title, surname=surname)
    report, rc = _apply(tmp_path)
    assert rc == 0
    assert report["summary"] == {"created": 1}
    assert report["apply_status"] == "applied"
    (applied,) = report["applied"]
    assert applied["status"] == "created" and applied["file"] == f"docs/{pdf.name}"
    item = use_live.find(title)
    assert item["data"]["creators"][0]["lastName"] == surname
    assert item["data"]["date"] == "2020"
    (att,) = use_live.children(item["key"])
    assert att["data"]["md5"] == hashlib.md5(pdf.read_bytes()).hexdigest()


@pytest.mark.integration
def test_check_staging_apply_can_import_orphan_with_complete_pdf_metadata(
        use_live, tmp_path):
    title, surname = unique_title(), unique_surname()
    docs = tmp_path / "docs"
    docs.mkdir()
    paper_pdf(docs, title, f"Jane {surname}", info={
        "Title": title, "Author": f"Jane {surname}",
        "CreationDate": "D:20200101000000Z"})
    report, rc = _apply(tmp_path)
    assert rc == 0
    assert report["summary"] == {"created": 1}
    item = use_live.find(title)
    assert item["data"]["creators"] == [{"creatorType": "author",
                                         "firstName": "Jane",
                                         "lastName": surname}]


def test_check_staging_apply_defers_orphan_without_metadata(tmp_path, monkeypatch):
    """Nothing to look it up by: unidentified, never absent, so nothing is
    created; with no key, the lookup asks Zotero nothing (down here)."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "orphan.pdf").write_bytes(b"unreadable scan")
    _quiet_pdf_tools(monkeypatch)
    report, rc = _apply(tmp_path)
    assert rc == 0
    assert report["summary"] == {"unidentified": 1}
    assert report["actions"] == {"unidentified":
                                 zi.RECONCILE_ACTIONS["unidentified"]}
    assert report["apply_status"] == "nothing" and report["applied"] == []


def test_the_staging_lock_leaves_no_file_behind(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "orphan.pdf").write_bytes(b"x")
    with zi.directory_locks([docs, tmp_path]):
        pass
    assert sorted(p.name for p in docs.iterdir()) == ["orphan.pdf"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["docs"]


def test_check_staging_invalid_root_still_writes_out(tmp_path, capsys):
    out = tmp_path / "report.json"
    args = _reconcile_args(tmp_path / "nope", out=str(out))
    assert zi.cmd_check_staging(args) == 1
    assert json.loads(out.read_text())["verdict"] == "unchecked"
    capsys.readouterr()


@pytest.mark.integration
def test_check_staging_suggests_the_attach_edit_for_a_present_work(
        use_live, tmp_path, capsys):
    title, surname = unique_title(), unique_surname()
    key = use_live.save(title, creators=(surname,), date="2020")
    pdf = _staged_bib_paper(tmp_path, title=title, surname=surname, year="2020")
    assert zi.cmd_check_staging(_reconcile_args(tmp_path)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["rows"][0]["verdict"] == "work_present_no_file"
    assert report["suggested_edits"] == [{"itemKey": key,
                                          "field": "attachment", "old": "",
                                          "new": f"docs/{pdf.name}"}]
    assert use_live.children(key) == [], "the report only reads"


@pytest.mark.integration
def test_check_staging_apply_edit_stores_the_file_under_the_present_work(
        use_live, tmp_path):
    """--apply alone never touches an existing item; --apply --edit stores
    the staged file under the one work that lacks it."""
    title, surname = unique_title(), unique_surname()
    key = use_live.save(title, creators=(surname,), date="2020")
    pdf = _staged_bib_paper(tmp_path, title=title, surname=surname, year="2020")
    found = zi.discover_reconcile_files(tmp_path)
    config = json.loads(OPT_IN)
    report, rc = zi.reconcile_apply(tmp_path, found, "user", config,
                                    argparse.Namespace(library="user", edit=False))
    assert rc == 0 and report["summary"] == {"work_present_no_file": 1}
    assert use_live.children(key) == []
    report, rc = zi.reconcile_apply(tmp_path, found, "user", config,
                                    argparse.Namespace(library="user", edit=True))
    assert rc == 0
    assert report["summary"] == {"attached": 1}
    assert report["apply_status"] == "applied"
    (edit,) = report["edits"]
    assert edit["status"] == "attached" and edit["itemKey"] == key
    assert report["suggested_edits"] == []
    (child,) = use_live.children(key)
    assert child["data"]["md5"] == hashlib.md5(pdf.read_bytes()).hexdigest()


def test_check_staging_edit_needs_apply(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["zotero.py", "check-staging", str(tmp_path),
                                      "--edit"])
    with pytest.raises(SystemExit) as exc:
        zi.main()
    assert exc.value.code == 2
    assert "--edit needs --apply" in capsys.readouterr().err


@pytest.mark.integration
def test_check_staging_report_is_read_only_and_counts_both_directions(
        use_live, tmp_path, capsys):
    pdf = _staged_bib_paper(tmp_path, opt_in=None)
    title = zi._bib_entries(tmp_path / "sources.bib")[0]["title"]
    identifiable_pdf(tmp_path / "docs")
    assert zi.cmd_check_staging(_reconcile_args(tmp_path)) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["summary"] == {"absent": 2}
    assert {r["source"] for r in report["rows"]} == {"bib", "orphan"}
    assert report["actions"] == {"absent": zi.RECONCILE_ACTIONS["absent"]}
    assert use_live.titled(title) == [], f"{pdf.name} was not imported"


@pytest.mark.integration
def test_check_staging_file_output_keeps_stdout_compact_and_reports_ties(
        use_live, tmp_path, capsys):
    """Two records hold the same stored file: the staged copy is identical
    to both, and the tie reaches the summary."""
    title, surname = unique_title(), unique_surname()
    shared = make_pdf(tmp_path / "shared.pdf", [title, uuid.uuid4().hex])
    first = use_live.save(title, creators=(surname,), pdf=shared)
    second = use_live.save(title, creators=(surname,), pdf=shared)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / f"{surname}2020-copy.pdf").write_bytes(shared.read_bytes())
    output = tmp_path / "report.json"
    assert zi.cmd_check_staging(_reconcile_args(tmp_path, out=str(output))) == 0
    compact = json.loads(capsys.readouterr().out)
    full = json.loads(output.read_text())
    assert "rows" not in compact
    (row,) = full["rows"]
    assert compact["summary"] == {"identical": 1, "tied_parents": 1}
    assert "tied_parents" in compact["actions"]
    assert {row["zotero_key"]} | {m["key"] for m in row["also_matches"]} == {
        first, second}


def test_check_staging_uses_docs_default_only_without_bib(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    only = docs / "only.pdf"
    only.write_bytes(b"x")
    assert zi.discover_reconcile_files(tmp_path)["orphans"] == [only]

    (tmp_path / "empty.bib").write_text("@article{one,title={No file}}\n")
    found = zi.discover_reconcile_files(tmp_path)
    assert found["orphans"] == []
    assert found["errors"], "a bib with no staging path cannot report clean"


def test_check_staging_discovers_one_level_bib_and_better_bibtex_path(tmp_path):
    refs = tmp_path / "refs"
    docs = tmp_path / "docs"
    refs.mkdir()
    docs.mkdir()
    pdf = docs / "paper.pdf"
    pdf.write_bytes(b"paper")
    (refs / "sources.bib").write_text(
        "@article{one, file={:../docs/paper.pdf:PDF}}\n"
    )
    found = zi.discover_reconcile_files(tmp_path)
    assert [r["path"] for r in found["linked"]] == [pdf]
    assert found["errors"] == []


def test_check_staging_duplicate_bib_file_link_is_not_two_import_proposals(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    pdf = docs / "one.pdf"
    pdf.write_bytes(b"paper")
    for name in ("one.bib", "two.bib"):
        (tmp_path / name).write_text(
            "@article{key, file={docs/one.pdf}}\n"
        )
    found = zi.discover_reconcile_files(tmp_path)
    assert [r["path"] for r in found["linked"]] == [pdf]
    assert any("multiple BibTeX" in e for e in found["errors"])


def test_check_staging_scans_staging_root_beyond_linked_subdirectory(tmp_path):
    nested = tmp_path / "docs" / "section"
    nested.mkdir(parents=True)
    linked = nested / "linked.pdf"
    orphan = tmp_path / "docs" / "orphan.pdf"
    linked.write_bytes(b"linked")
    orphan.write_bytes(b"orphan")
    (tmp_path / "sources.bib").write_text(
        "@article{one, file={docs/section/linked.pdf}}\n"
    )
    found = zi.discover_reconcile_files(tmp_path)
    assert found["orphans"] == [orphan]
    assert found["staging_dirs"] == [tmp_path / "docs"]


def test_check_staging_without_bib_finds_nested_staging_orphan(tmp_path):
    nested = tmp_path / "docs" / "section"
    nested.mkdir(parents=True)
    orphan = nested / "orphan.pdf"
    orphan.write_bytes(b"orphan")
    assert zi.discover_reconcile_files(tmp_path)["orphans"] == [orphan]


def test_check_staging_symlinked_staging_directory_is_unchecked(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    external = tmp_path.parent / "reconcile-external"
    external.mkdir(exist_ok=True)
    (external / "paper.pdf").write_bytes(b"paper")
    (docs / "external").symlink_to(external, target_is_directory=True)
    found = zi.discover_reconcile_files(tmp_path)
    assert found["errors"]
    assert not found["orphans"]


def test_check_staging_unclosed_bib_entry_is_not_a_clean_prefix(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ok.pdf").write_bytes(b"ok")
    (tmp_path / "sources.bib").write_text(
        "@article{ok, file={docs/ok.pdf}}\n"
        "@article{broken, file={docs/lost.pdf}\n"
    )
    found = zi.discover_reconcile_files(tmp_path)
    assert found["errors"], "an unclosed trailing entry must fail closed"


def test_check_staging_malformed_file_field_is_not_silently_dropped(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "ok.pdf").write_bytes(b"ok")
    (tmp_path / "sources.bib").write_text(
        "@article{ok, file={docs/ok.pdf}}\n"
        "@article{bad, file {docs/lost.pdf}}\n"
    )
    found = zi.discover_reconcile_files(tmp_path)
    assert found["errors"], "malformed file field must fail closed"


def test_check_staging_does_not_scan_file_outside_repository(tmp_path):
    outside = tmp_path.parent / "external.pdf"
    (tmp_path / "refs.bib").write_text(
        f"@article{{one, file={{{outside}}}}}\n"
    )
    found = zi.discover_reconcile_files(tmp_path)
    assert found["linked"] == []
    assert found["orphans"] == []
    assert found["errors"]


def test_check_staging_does_not_read_symlinked_bib_outside_repository(
        tmp_path, monkeypatch):
    external = tmp_path.parent / "external-sources.bib"
    external.write_text("@article{one, file={docs/secret.pdf}}\n")
    (tmp_path / "refs.bib").symlink_to(external)
    monkeypatch.setattr(zi, "_bib_entries", lambda _path: pytest.fail(
        "external BibTeX was read"))
    found = zi.discover_reconcile_files(tmp_path)
    assert found["linked"] == []
    assert found["errors"]


def shell_blocks(text):
    import re

    return re.findall(r"```bash\n(.*?)\n\s*```", text, re.S)


def helper_stand_in(tmp_path, status):
    """A project whose PATH and IDH_ROOT lead to a zotero.py that only exits
    with `status`: this tests the documented shell block, not Zotero."""
    root = tmp_path / "idh"
    (root / "scripts").mkdir(parents=True)
    helper = root / "scripts/zotero.py"
    helper.write_text(f"#!/bin/sh\nexit {status}\n")
    helper.chmod(0o755)
    shim = tmp_path / "bin/zotero.py"
    shim.parent.mkdir(parents=True)
    shim.write_text(f"#!/bin/sh\nexit {status}\n")
    shim.chmod(0o755)
    proj = tmp_path / "proj"
    (proj / "docs").mkdir(parents=True)
    env = child_env()
    env["IDH_ROOT"] = str(root)
    env["TMPDIR"] = str(tmp_path)
    env["PATH"] = f"{shim.parent}:{env['PATH']}"
    return proj, env


@pytest.mark.integration
def test_check_staging_failure_propagates_and_path_announced(tmp_path):
    """A failing check-staging must fail the block, and the report path is still named."""
    text = (SCRIPTS.parent / "skills/zotero/references/backfill.md").read_text()
    block = next(b for b in shell_blocks(text) if "check-staging . --out" in b)
    proj, env = helper_stand_in(tmp_path, 7)
    r = subprocess.run(["bash", "-c", block], cwd=proj, env=env, text=True, capture_output=True)
    assert r.returncode != 0, (r.returncode, r.stdout, r.stderr)
    assert "check-staging report: " in r.stdout and "(exit 7)" in r.stdout
    okdir = tmp_path / "ok"
    okdir.mkdir()
    proj2, env2 = helper_stand_in(okdir, 0)
    assert subprocess.run(["bash", "-c", block], cwd=proj2, env=env2).returncode == 0


@pytest.mark.integration
def test_local_account_of_a_signed_out_client_is_none(use_live, tmp_path):
    """The local API's refusal of another user's data names no account
    ("use userID 0"): signed out, the opt-in check fails closed."""
    use_live.save(unique_title())
    assert zi.local_account() is None
    (tmp_path / ".zotero-reconcile.json").write_text(OPT_IN)
    with pytest.raises(ValueError, match="signed in to no account"):
        zi.reconcile_apply_config(tmp_path, zi.local_account())


# --------------------------------------------------------------------------
# Review round 4: failure paths fail closed or do nothing.
# --------------------------------------------------------------------------


@pytest.mark.integration
def test_a_launcher_that_cannot_execute_is_unavailable_not_a_crash(
        tmp_path, monkeypatch, capsys):
    """A `zotero` on PATH that is not a program (an executable file of
    garbage bytes): the launch fails, the helper says so and does nothing."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    broken = bin_dir / "zotero"
    broken.write_bytes(b"\x00\x01 not a program\n")
    broken.chmod(0o755)
    monkeypatch.delenv("ZOTERO_NO_LAUNCH")
    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setenv("HOME", str(tmp_path))
    if reason := zi.in_container():
        pytest.skip(f"launching is off here: {reason}")
    if zi.find_zotero_launcher() != [str(broken)]:
        pytest.skip("the helper's discovery does not find the broken launcher")
    with pytest.raises(zi.ZoteroUnavailable, match="launching it .* failed"):
        zi.ensure_zotero()
    _staged_bib_paper(tmp_path)
    out = tmp_path / "report.json"
    assert zi.cmd_check_staging(_reconcile_args(tmp_path, out=str(out))) == 0
    assert json.loads(out.read_text())["verdict"] == "zotero_unavailable"
    capsys.readouterr()


def test_a_file_url_with_a_host_is_not_a_local_path():
    assert zi.file_url_path("file:///home/u/x.pdf") == "/home/u/x.pdf"
    assert zi.file_url_path("file://localhost/home/u/x.pdf") == "/home/u/x.pdf"
    assert zi.file_url_path("file://server/share/x.pdf") is None
    assert zi.file_url_path("https://example.org/x.pdf") is None


def test_a_held_lock_times_out_instead_of_hanging(tmp_path):
    fd = os.open(tmp_path, os.O_RDONLY)
    fcntl.flock(fd, fcntl.LOCK_EX)
    try:
        # flock locks are per open file description: a second open contends.
        with pytest.raises(OSError, match="locked by another run"):
            with zi.directory_locks([tmp_path], wait=0.3):
                pass
    finally:
        os.close(fd)


def test_the_lock_never_falls_back_to_a_shared_temp_dir(monkeypatch):
    monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
    assert zi.library_lock_dir() == Path.home()


# ── /gaze round 1 fixes (PR 1441) ───────────────────────────────────────────


def test_a_zotero_url_carrying_credentials_is_refused(monkeypatch):
    """A loopback URL with user:password@ is refused like a remote one, and
    the refusal does not echo the password."""
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL",
                       "http://user:s3cret@127.0.0.1:23999")
    with pytest.raises(zi.LocalAPIError, match="credentials") as exc:
        zi.zotero_base()
    assert "s3cret" not in str(exc.value)
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", "http://user@localhost:23999")
    with pytest.raises(zi.LocalAPIError, match="credentials"):
        zi.zotero_base()


def test_force_still_refuses_a_missing_pdf_before_creating_the_item(
        tmp_path, monkeypatch):
    created = []
    monkeypatch.setattr(zi, "create_item",
                        lambda *a, **k: created.append(a) or "K1")
    entry = {"title": "A title", "pdf": str(tmp_path / "gone.pdf"),
             "attach_pdf": True}
    results, rc = zi.create_entries([entry], [{}], [{"confidence": "low"}],
                                    "user", None, force=True)
    assert rc == 1 and not created
    assert "not found" in results[0]["error"]
    assert "key" not in results[0]


def test_a_local_file_error_is_not_blamed_on_the_local_api_setting():
    with pytest.raises(zi.LocalAPIError) as exc:
        with zi.local_api():
            raise ze.FileDoesNotExistError("/x/gone.pdf")
    assert zi.LOCAL_API_SETTING not in str(exc.value)
    assert "gone.pdf" in str(exc.value)


def test_a_launched_zotero_that_answers_with_an_error_is_not_stopped(
        monkeypatch):
    """The launched client answered (local API disabled): the user is told
    to enable the setting in it, so it must stay open."""
    answers = iter([False])

    def zotero_answers():
        try:
            return next(answers)
        except StopIteration:
            raise zi.LocalAPIError("Zotero's local API is disabled") from None

    stopped = []
    monkeypatch.setattr(zi, "zotero_answers", zotero_answers)
    monkeypatch.setattr(zi, "in_container", lambda: None)
    monkeypatch.setattr(zi, "find_zotero_launcher", lambda: ["zotero"])
    monkeypatch.setattr(zi, "launch_zotero", lambda command: "PROC")
    monkeypatch.setattr(zi, "stop_launched", stopped.append)
    with pytest.raises(zi.LocalAPIError):
        zi.ensure_zotero()
    assert stopped == []


def test_a_refused_key_stops_an_attach_batch(tmp_path, monkeypatch, capsys):
    calls = []

    def attach_file(z, parent, path):
        calls.append(path)
        raise zi.KeyNotGranted("Zotero refused a local API key (denied)")

    monkeypatch.setattr(zi, "with_zotero", lambda command, read: (
        (None, {"data": {"title": "T"}}), None))
    monkeypatch.setattr(zi, "attach_file", attach_file)
    pdfs = [str(make_pdf(tmp_path / f"f{i}.pdf", [f"p{i}"])) for i in range(3)]
    rc = zi.cmd_suggest_attachments(argparse.Namespace(parent="P1", file=pdfs,
                                          library="user", edit=True))
    rows = json.loads(capsys.readouterr().out)["attached"]
    assert rc == 1 and len(calls) == 1
    assert [r["status"] for r in rows] == ["failed", "not attempted",
                                           "not attempted"]


def test_a_refused_key_stops_an_enrich_batch(monkeypatch):
    asked = []

    def write(z, call, **kwargs):
        asked.append(1)
        raise zi.KeyNotGranted("Zotero refused a local API key (denied)")

    monkeypatch.setattr(zi, "find_item", lambda key, library: (
        None, {"key": key, "data": {"title": "T"}}))
    monkeypatch.setattr(zi, "item_fields", lambda z, item: {
        "key": item["key"], "itemType": "book", "title": "T", "date": ""})
    monkeypatch.setattr(zi, "write", write)
    jobs = [{"item_key": k, "expect_title": "T", "set": {"date": "2001"}}
            for k in ("A", "B", "C")]
    results = zi.run_jobs(jobs, lambda j: zi.enrich_one(j, False, True),
                          wrote=True)
    assert len(asked) == 1
    assert [r["status"] for r in results] == ["not written", "not attempted",
                                              "not attempted"]


def test_a_refused_key_stops_the_reconcile_attach_edits(tmp_path, monkeypatch):
    calls = []

    def attach_file(z, parent, path):
        calls.append(parent)
        raise zi.KeyNotGranted("Zotero refused a local API key (denied)")

    monkeypatch.setattr(zi, "local_library", lambda library_id=None: None)
    monkeypatch.setattr(zi, "attach_file", attach_file)
    rows = [{"verdict": "work_present_no_file", "zotero_key": k,
             "path": f"{k}.pdf"} for k in ("A", "B", "C")]
    report = {"summary": {"work_present_no_file": 3}, "actions": {},
              "suggested_edits": []}
    rc = zi.attach_present_works(tmp_path, rows, "user", report)
    assert rc == 1 and calls == ["A"]
    assert [e["status"] for e in report["edits"]] == ["failed", "not attempted",
                                                      "not attempted"]


def test_an_unanswered_key_dialog_is_not_reported_as_zotero_stopping(
        monkeypatch):
    def authorize_local(self, app_name):
        raise zi.httpx2.ReadTimeout("timed out")

    monkeypatch.setattr(zi.zotero.Zotero, "authorize_local", authorize_local)
    with pytest.raises(zi.KeyNotGranted) as exc:
        zi.authorize(zi.local_library())
    assert "stopped answering" not in str(exc.value)
    assert "unanswered" in str(exc.value)

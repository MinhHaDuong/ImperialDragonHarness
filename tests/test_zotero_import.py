"""Tests for scripts/zotero-import.py.

Covers the pure extraction/formatting helpers (identifier regexes, RIS
emission) plus the Zotero matcher against a real in-memory SQLite database
built with the minimal slice of Zotero's schema the query touches.
"""

import hashlib
import importlib.util
import sqlite3
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("zotero_import", SCRIPTS / "zotero-import.py")
zi = importlib.util.module_from_spec(spec)
sys.modules["zotero_import"] = zi
spec.loader.exec_module(zi)


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


# ── RIS emission ─────────────────────────────────────────────────────────────


def test_author_to_ris_reorders_first_last():
    assert zi.author_to_ris("Jane Smith") == "Smith, Jane"


def test_author_to_ris_keeps_comma_form():
    assert zi.author_to_ris("Smith, Jane") == "Smith, Jane"


def test_author_to_ris_single_token_unchanged():
    assert zi.author_to_ris("Plato") == "Plato"


def test_entry_to_ris_basic_journal():
    ris = zi.entry_to_ris(
        {"title": "A Paper", "authors": ["Jane Smith"], "year": "2020", "doi": "10.1/x"}
    )
    assert "TY  - JOUR" in ris
    assert "TI  - A Paper" in ris
    assert "AU  - Smith, Jane" in ris
    assert "PY  - 2020" in ris
    assert "DO  - 10.1/x" in ris
    assert ris.rstrip().endswith("ER  -")


def test_entry_to_ris_invalid_type_falls_back_to_jour():
    assert "TY  - JOUR" in zi.entry_to_ris({"type": "BOGUS", "title": "T"})


def test_entry_to_ris_splits_page_range():
    ris = zi.entry_to_ris({"title": "T", "pages": "10-20"})
    assert "SP  - 10" in ris
    assert "EP  - 20" in ris


def test_entry_to_ris_numpages_monograph_maps_to_sp():
    ris = zi.entry_to_ris({"type": "BOOK", "title": "T", "numPages": "300"})
    assert "SP  - 300" in ris


def test_entry_to_ris_numpages_nonmonograph_maps_to_keyword():
    ris = zi.entry_to_ris({"type": "JOUR", "title": "T", "numPages": "12"})
    assert "KW  - pages:12" in ris


def test_entry_to_ris_abstract_whitespace_collapsed():
    ris = zi.entry_to_ris({"title": "T", "abstract": "line one\n  line   two"})
    assert "AB  - line one line two" in ris


# ── resolve_db_path ──────────────────────────────────────────────────────────


def test_resolve_db_path_override_exists(tmp_path):
    db = tmp_path / "z.sqlite"
    db.write_text("")
    assert zi.resolve_db_path(str(db)) == db


def test_resolve_db_path_override_missing_returns_none(tmp_path):
    assert zi.resolve_db_path(str(tmp_path / "absent.sqlite")) is None


# ── cmd_write ────────────────────────────────────────────────────────────────


def test_cmd_write_emits_ris_file(tmp_path):
    import argparse

    out = tmp_path / "out.ris"
    args = argparse.Namespace(
        entries_json='[{"title": "One", "year": "2021"}]',
        entries_file=None,
        out=str(out),
    )
    assert zi.cmd_write(args) == 0
    body = out.read_text()
    assert "TI  - One" in body
    assert "PY  - 2021" in body


# ── zotero_matches against a real (in-memory) SQLite db ──────────────────────


# File bytes whose md5 is planted as itemAttachments.storageHash in the fixture.
SCAN_BYTES = b"scanned book pdf bytes"
GROUP_BYTES = b"group library pdf bytes"
CONTROL_BYTES = b"positive control pdf bytes"


def _matches(result):
    """Normalise the matcher result to its hit list.

    Tolerates both the pre-repair shape (a bare list) and the current shape
    (a dict with "matches"/"verdict"), so the behavioural asserts in the
    red-first proof fire at assertion level against pre-fix code instead of
    dying on the API shape.
    """
    return result["matches"] if isinstance(result, dict) else result


def _build_zotero_db() -> sqlite3.Connection:
    """Minimal slice of Zotero's schema for the matcher query.

    Carries the columns whose absence used to hide the matcher's defects:
    items.libraryID (user vs read-only group scoping),
    itemAttachments.storageHash (content-hash key), and the
    creators/itemCreators tables (first-author key).
    """
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE libraries (libraryID INTEGER PRIMARY KEY, type TEXT);
        CREATE TABLE items (itemID INTEGER PRIMARY KEY, libraryID INT);
        CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
        CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE itemData (itemID INT, fieldID INT, valueID INT);
        CREATE TABLE deletedItems (itemID INT);
        CREATE TABLE itemAttachments (itemID INTEGER PRIMARY KEY, parentItemID INT,
                                      path TEXT, contentType TEXT, storageHash TEXT);
        CREATE TABLE fulltextItems (itemID INT, indexedPages INT, totalPages INT);
        CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT,
                               lastName TEXT, fieldMode INT);
        CREATE TABLE itemCreators (itemID INT, creatorID INT, creatorTypeID INT,
                                   orderIndex INT);

        INSERT INTO libraries VALUES (1,'user'),(3,'group');
        INSERT INTO fields VALUES (1,'title'),(2,'DOI'),(3,'date'),(4,'ISBN'),
                                  (5,'extra'),(6,'url');

        -- item 10 (user): DOI 10.1/x, title, date, and a PDF attachment
        INSERT INTO items VALUES (10, 1);
        INSERT INTO itemDataValues VALUES (1,'Deep Learning for Climate'),(2,'10.1/x'),(3,'2020-05-01');
        INSERT INTO itemData VALUES (10,1,1),(10,2,2),(10,3,3);
        -- attachments are themselves items rows (as in the real schema)
        INSERT INTO items VALUES (20, 1);
        INSERT INTO itemAttachments VALUES (20, 10, 'storage:paper.pdf', 'application/pdf', NULL);
        INSERT INTO fulltextItems VALUES (20, 5, 5);

        -- item 11 (user): title only, NO child attachment (title-only branch)
        INSERT INTO items VALUES (11, 1);
        INSERT INTO itemDataValues VALUES (4,'Shallow Trees for Weather'),(5,'2019');
        INSERT INTO itemData VALUES (11,1,4),(11,3,5);

        -- item 30 (user): is ITSELF a child attachment (parentItemID set) with a
        -- title identical to item 10's. The title branch must exclude it via the
        -- `a.itemID IS NULL` filter even though its title would otherwise match.
        INSERT INTO items VALUES (30, 1);
        INSERT INTO itemData VALUES (30,1,1);  -- reuse 'Deep Learning for Climate'
        INSERT INTO itemAttachments VALUES (30, 11, 'storage:child.pdf', 'application/pdf', NULL);

        -- item 40 (GROUP library): DOI present only in the read-only group.
        -- Injection writes to the user library, so this must not read as
        -- "already present" under the default scope.
        INSERT INTO items VALUES (40, 3);
        INSERT INTO itemDataValues VALUES (6,'10.5/group'),(7,'Group Only Paper'),(8,'2018');
        INSERT INTO itemData VALUES (40,2,6),(40,1,7),(40,3,8);

        -- item 50 (user): garbage metadata ('Untitled scan 0001') but a PDF
        -- attachment with a real filename and storageHash. Only attachment
        -- evidence can recognise it; the title scores 0 on any real query.
        INSERT INTO items VALUES (50, 1);
        INSERT INTO items VALUES (51, 1);
        INSERT INTO itemDataValues VALUES (9,'Untitled scan 0001');
        INSERT INTO itemData VALUES (50,1,9);

        -- item 55 (GROUP library): attachment hash present only in the group.
        INSERT INTO items VALUES (55, 3);
        INSERT INTO items VALUES (56, 3);
        INSERT INTO itemDataValues VALUES (10,'Group Scan');
        INSERT INTO itemData VALUES (55,1,10);

        -- item 60 (user): pre-DOI book — no DOI, first author + year + title.
        INSERT INTO items VALUES (60, 1);
        INSERT INTO itemDataValues VALUES (11,'Anarchy, State, and Utopia'),(12,'1974');
        INSERT INTO itemData VALUES (60,1,11),(60,3,12);
        INSERT INTO creators VALUES (1,'Robert','Nozick',0);
        INSERT INTO itemCreators VALUES (60,1,1,0);

        -- items 61/62 (user): two distinct works sharing a generic title.
        INSERT INTO items VALUES (61, 1);
        INSERT INTO items VALUES (62, 1);
        INSERT INTO itemDataValues VALUES (13,'Convex Analysis'),(14,'1970'),(15,'1993');
        INSERT INTO itemData VALUES (61,1,13),(61,3,14),(62,1,13),(62,3,15);

        -- item 70 (user): ISBN-only identifier (stored with hyphens, as Zotero does).
        INSERT INTO items VALUES (70, 1);
        INSERT INTO itemDataValues VALUES (16,'Handbook of Something'),(17,'978-0-13-468599-1'),(18,'2016');
        INSERT INTO itemData VALUES (70,1,16),(70,4,17),(70,3,18);

        -- item 80 (user): positive-control canary — DOI, hash, and filename all set.
        INSERT INTO items VALUES (80, 1);
        INSERT INTO items VALUES (81, 1);
        INSERT INTO itemDataValues VALUES (19,'Positive Control Canary'),(20,'10.9/control'),(21,'2021');
        INSERT INTO itemData VALUES (80,1,19),(80,2,20),(80,3,21);

        -- item 90 (user): arXiv id lives in the 'extra' field, as Zotero stores it.
        INSERT INTO items VALUES (90, 1);
        INSERT INTO itemDataValues VALUES (22,'An Arxiv Preprint'),(23,'arXiv:2401.01234');
        INSERT INTO itemData VALUES (90,1,22),(90,5,23);

        -- item 91 (user): handle lives in the 'url' field.
        INSERT INTO items VALUES (91, 1);
        INSERT INTO itemDataValues VALUES (24,'A Handle Report'),(25,'https://hdl.handle.net/2027/abc');
        INSERT INTO itemData VALUES (91,1,24),(91,6,25);
        """
    )
    c.execute(
        "INSERT INTO itemAttachments VALUES (51, 50, 'storage:convex-analysis-1970.pdf',"
        " 'application/pdf', ?)",
        (hashlib.md5(SCAN_BYTES).hexdigest(),),
    )
    c.execute(
        "INSERT INTO itemAttachments VALUES (56, 55, 'storage:group-scan.pdf',"
        " 'application/pdf', ?)",
        (hashlib.md5(GROUP_BYTES).hexdigest(),),
    )
    c.execute(
        "INSERT INTO itemAttachments VALUES (81, 80, 'storage:control.pdf',"
        " 'application/pdf', ?)",
        (hashlib.md5(CONTROL_BYTES).hexdigest(),),
    )
    conn.commit()
    return conn


def test_zotero_matches_doi_exact_match():
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi="10.1/X", title=None, year="2020", pdf_path=Path("paper.pdf")
    )
    matches = _matches(res)
    assert len(matches) == 1
    m = matches[0]
    assert m["itemID"] == 10
    assert m["score"] == 105  # 100 doi + 5 year
    assert "doi" in m["why"] and "year" in m["why"]
    assert m["pdf_basename_match"] is True
    assert m["attachments"][0]["path"] == "storage:paper.pdf"
    assert m["certainty"] == "exact"
    assert res["verdict"] == "match"


def test_zotero_matches_title_fuzzy_match():
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi=None, title="Shallow Trees for Weather", year=None, pdf_path=Path("x.pdf")
    )
    ids = [m["itemID"] for m in _matches(res)]
    assert 11 in ids  # exact title → Jaccard 1.0 >= 0.6
    # item 10 ("Deep Learning for Climate") shares only "for" with the query →
    # Jaccard well below 0.6 → not matched. (It is NOT excluded for having an
    # attachment; parents with attachments stay eligible in the no-DOI branch.)
    assert 10 not in ids
    # A title-similarity hit is a guess, not a certainty.
    assert res["verdict"] == "ambiguous"


def test_zotero_matches_excludes_items_that_are_themselves_attachments():
    """The title branch's `a.itemID IS NULL` filter drops child-attachment items."""
    conn = _build_zotero_db()
    # Query item 10's exact title. Item 10 (a top-level work) matches; item 30
    # has the identical title but IS a child attachment, so it must be excluded
    # — proving the filter, since title alone would otherwise score it as a hit.
    res = zi.zotero_matches(
        conn, doi=None, title="Deep Learning for Climate", year=None, pdf_path=Path("x.pdf")
    )
    ids = [m["itemID"] for m in _matches(res)]
    assert 10 in ids
    assert 30 not in ids


def test_zotero_matches_no_hit_returns_empty():
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi="10.9/nope", title=None, year=None, pdf_path=Path("x.pdf")
    )
    assert _matches(res) == []
    # Keys were consulted and found nothing — distinguishable from "unchecked".
    assert res["verdict"] == "none"
    assert res["consulted"]


# ── defect (a): library scoping ──────────────────────────────────────────────


def test_group_library_hit_does_not_suppress_user_injection():
    """A DOI present only in the read-only group library is NOT "already present".

    Injection writes to users/{uid}; the matcher's default scope must be that
    destination. Red on pre-fix code: the unscoped query returns item 40.
    """
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi="10.5/group", title=None, year=None, pdf_path=Path("absent.pdf")
    )
    assert _matches(res) == []
    assert res["verdict"] == "none"


def test_library_scope_override_reaches_group_library():
    """The scope is explicit and overridable: 'all' (or a numeric id) widens it."""
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi="10.5/group", title=None, year=None, pdf_path=None, library="all"
    )
    assert [m["itemID"] for m in _matches(res)] == [40]
    res3 = zi.zotero_matches(
        conn, doi="10.5/group", title=None, year=None, pdf_path=None, library=3
    )
    assert [m["itemID"] for m in _matches(res3)] == [40]


def test_attachment_hash_in_group_library_stays_out_of_user_scope(tmp_path):
    pdf = tmp_path / "renamed.pdf"  # name matches nothing; only content can hit
    pdf.write_bytes(GROUP_BYTES)
    conn = _build_zotero_db()
    res = zi.zotero_matches(conn, doi=None, title=None, year=None, pdf_path=pdf)
    assert _matches(res) == []
    res_all = zi.zotero_matches(
        conn, doi=None, title=None, year=None, pdf_path=pdf, library="all"
    )
    assert [m["itemID"] for m in _matches(res_all)] == [55]


# ── defect (b): attachment evidence as a primary candidate source ────────────


def test_pdf_recognised_by_content_hash_without_any_metadata(tmp_path):
    """A scanned PDF under garbage metadata is found by storageHash alone.

    No title, no DOI, and a local filename that matches nothing — only the
    file content can identify it. Red on pre-fix code: attachments were only
    consulted on candidates already scored by title, so this returned [].
    """
    pdf = tmp_path / "anything.pdf"
    pdf.write_bytes(SCAN_BYTES)
    conn = _build_zotero_db()
    res = zi.zotero_matches(conn, doi=None, title=None, year=None, pdf_path=pdf)
    matches = _matches(res)
    assert [m["itemID"] for m in matches] == [50]
    assert matches[0]["why"] == ["storageHash"]
    assert matches[0]["certainty"] == "exact"
    assert res["verdict"] == "match"


def test_pdf_recognised_by_filename_without_title_score():
    """Attachment filename is its own candidate source, not a decoration.

    The PDF does not exist locally (no hash possible) and no title is given,
    so recognition can only come from comparing the basename against
    itemAttachments.path. Red on pre-fix code: returned [].
    """
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi=None, title=None, year=None,
        pdf_path=Path("convex-analysis-1970.pdf"),
    )
    matches = _matches(res)
    assert [m["itemID"] for m in matches] == [50]
    assert matches[0]["why"] == ["filename"]
    assert matches[0]["certainty"] == "strong"
    assert res["verdict"] == "match"


# ── cascade: persistent identifiers beyond the DOI ───────────────────────────


def test_isbn_matches_despite_hyphenation_differences():
    """find_identifier extracts the ISBN; the matcher must consume it.

    Both sides are normalised: the query carries no hyphens, the stored
    value does (as in the real library).
    """
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi=None, title=None, year=None, pdf_path=None, isbn="9780134685991"
    )
    matches = _matches(res)
    assert [m["itemID"] for m in matches] == [70]
    assert matches[0]["why"] == ["isbn"]
    assert res["verdict"] == "match"


def test_arxiv_id_matches_extra_field():
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi=None, title=None, year=None, pdf_path=None, arxiv="2401.01234"
    )
    matches = _matches(res)
    assert [m["itemID"] for m in matches] == [90]
    assert matches[0]["why"] == ["arxiv"]


def test_handle_matches_url_field():
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi=None, title=None, year=None, pdf_path=None,
        handle="https://hdl.handle.net/2027/abc",
    )
    matches = _matches(res)
    assert [m["itemID"] for m in matches] == [91]
    assert matches[0]["why"] == ["handle"]


# ── cascade: (first author, year, normalised title) — the pre-DOI book case ──


def test_predoi_book_recognised_despite_casing_and_punctuation():
    """A book with no DOI, already present under different casing/punctuation,
    must be a CERTAIN match via the creator-year-title key — not a Jaccard
    guess. If the non-DOI key is removed, the hit degrades to a weak title
    match, the verdict flips to "ambiguous", and this test fails.
    """
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi=None, title="anarchy state and utopia", year="1974",
        first_author="Robert Nozick", pdf_path=None,
    )
    matches = _matches(res)
    assert [m["itemID"] for m in matches] == [60]
    assert matches[0]["why"] == ["creator-year-title"]
    assert matches[0]["certainty"] == "strong"
    assert res["verdict"] == "match"


# ── ambiguity is reported, never silently resolved ───────────────────────────


def test_generic_title_shared_by_two_works_reports_ambiguous():
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi=None, title="Convex Analysis", year=None, pdf_path=None
    )
    ids = {m["itemID"] for m in _matches(res)}
    assert {61, 62} <= ids
    assert all(m["certainty"] == "weak" for m in _matches(res))
    assert res["verdict"] == "ambiguous"


def test_no_keys_at_all_reports_unchecked_not_none():
    """"Found nothing" and "could not look" must stay distinguishable."""
    conn = _build_zotero_db()
    res = zi.zotero_matches(
        conn, doi=None, title=None, year=None, pdf_path=None
    )
    assert _matches(res) == []
    assert res["verdict"] == "unchecked"
    assert res["consulted"] == []
    assert res["skipped"]  # every stage states why it could not look


# ── positive control ─────────────────────────────────────────────────────────


def test_positive_control_canary_always_found(tmp_path):
    """Known-positive that must surface on every run, through each source.

    If any candidate source goes silently blind (schema drift, path-format
    mismatch, broken query), this fails — keeping "found nothing" and
    "I could not look" distinguishable, as the ticket requires.
    """
    conn = _build_zotero_db()

    by_doi = zi.zotero_matches(
        conn, doi="10.9/control", title=None, year=None, pdf_path=None
    )
    assert [m["itemID"] for m in _matches(by_doi)] == [80]
    assert by_doi["verdict"] == "match"

    pdf = tmp_path / "unrelated-name.pdf"
    pdf.write_bytes(CONTROL_BYTES)
    by_hash = zi.zotero_matches(conn, doi=None, title=None, year=None, pdf_path=pdf)
    assert [m["itemID"] for m in _matches(by_hash)] == [80]
    assert by_hash["verdict"] == "match"

    by_name = zi.zotero_matches(
        conn, doi=None, title=None, year=None, pdf_path=Path("control.pdf")
    )
    assert [m["itemID"] for m in _matches(by_name)] == [80]
    assert by_name["verdict"] == "match"


# ── Zotero API item mapping (inject) ─────────────────────────────────────────


def test_author_to_creator_splits_first_last():
    c = zi.author_to_creator("Jane Q. Smith")
    assert c == {"creatorType": "author", "firstName": "Jane Q.", "lastName": "Smith"}


def test_author_to_creator_single_name_uses_name_field():
    assert zi.author_to_creator("Aristotle") == {"creatorType": "author", "name": "Aristotle"}


def test_entry_to_zotero_item_journal_article():
    item = zi.entry_to_zotero_item(
        {"type": "JOUR", "title": "T", "authors": ["Jane Smith"], "year": 2015,
         "doi": "10.1/x", "journal": "Econometrica", "volume": "83",
         "issue": "4", "pages": "1467-1495", "numPages": 29},
        collection=None,
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
         "numPages": 300, "doi": "10.2/y"},
        collection="ABCD1234",
    )
    assert item["itemType"] == "book"
    assert item["ISBN"] == "978-0-13-468599-1"
    assert item["numPages"] == "300"
    # schema 42 gives `book` a real DOI field; no need for the extra fallback
    assert item["DOI"] == "10.2/y"
    assert item["collections"] == ["ABCD1234"]


def test_entry_to_zotero_item_unknown_type_falls_back_to_document():
    assert zi.entry_to_zotero_item({"type": "XXXX"}, None)["itemType"] == "document"


# ── per-type field validity (the 400-from-Zotero class) ─────────────────────
#
# Snapshot of the valid field names per item type, read from
# https://api.zotero.org/schema (schema version 42, consulted 2026-08-14).
# Deliberately pinned HERE rather than imported from the module under test:
# the guard below must not be checked against the same table the mapper uses,
# or it proves nothing. `test_zotero_schema_snapshot_matches_live` (slow tier)
# re-derives this from the live schema.

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
    return zi.entry_to_zotero_item({**MAXIMAL_ENTRY, "type": ris_type}, None)


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
    item = zi.entry_to_zotero_item({**MAXIMAL_ENTRY, "type": "XXXX"}, None)
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


# ── RIS code coverage (the silent-downgrade class) ──────────────────────────


def test_every_accepted_ris_code_maps_to_a_zotero_type():
    """A code `write` accepts must not collapse to `document` on `inject`.

    The silent counterpart of the 400 class: no error, no trace, just a
    generic item where a patent or a standard was meant.
    """
    unmapped = sorted(zi.RIS_VALID_TYPES - set(zi.RIS_TO_ZOTERO_TYPE))
    assert unmapped == [], f"accepted RIS codes with no Zotero type: {unmapped}"


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
    item = zi.entry_to_zotero_item({"type": "ZZZZ", "title": "T"}, None)
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
    institution / reportNumber / place / reportType. One `inject` must now
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
    }, None)
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


def test_ris_path_drops_no_input_value_either():
    """Adding entry keys must not create a silent loss on the RIS side.

    `write` accepts the same entries as `inject`; a key only the API path
    reads would vanish from the RIS artifact without a word.
    """
    losses = {}
    for ris_code in sorted(zi.RIS_VALID_TYPES):
        ris = zi.entry_to_ris({**MAXIMAL_ENTRY, "type": ris_code})
        values = {line.split("  - ", 1)[1].split(":", 1)[-1].strip()
                  for line in ris.splitlines() if "  - " in line}
        values |= {line.split("  - ", 1)[1].strip()
                   for line in ris.splitlines() if "  - " in line}
        missing = sorted(
            key for key, value in MAXIMAL_ENTRY.items()
            # authors are reordered, abstract collapsed, a page range is
            # split across SP/EP, numPages competes with it on monographs
            if key not in ("authors", "abstract", "pages", "numPages")
            and str(value) not in values
        )
        if missing:
            losses[ris_code] = missing
    assert losses == {}, f"values absent from the RIS artifact: {losses}"


def test_unknown_entry_key_is_rejected_not_ignored():
    """An input key nobody reads is a silent loss; refuse it loudly."""
    with pytest.raises(SystemExit) as exc:
        zi.validate_entry_keys([{"title": "T", "reportNmbr": "P-69"}])
    assert "reportNmbr" in str(exc.value)


def test_known_entry_keys_pass_validation():
    zi.validate_entry_keys([dict(MAXIMAL_ENTRY, type="RPRT",
                                 pdf="/tmp/x.pdf", attach_pdf=True)])


@pytest.mark.slow
def test_zotero_schema_snapshot_matches_live():
    """Drift guard: the pinned tables against api.zotero.org/schema.

    Network-only, so `inject` itself never needs it. A failure here means
    Zotero changed a type's field set; re-derive both this snapshot and
    `ZOTERO_SLOT_FIELD` from the live schema.
    """
    import json
    import urllib.request

    with urllib.request.urlopen("https://api.zotero.org/schema", timeout=30) as r:
        schema = json.load(r)
    live = {t["itemType"]: {f["field"] for f in t["fields"]}
            for t in schema["itemTypes"]}

    for zot_type, pinned in SCHEMA_42_FIELDS.items():
        assert set(pinned) == live[zot_type], f"{zot_type} field set drifted"

    for slot, prefs in zi.ZOTERO_SLOT_PREFERENCES.items():
        derived = {t: field for t in SCHEMA_42_FIELDS
                   for field in (next((p for p in prefs if p in live[t]), None),)
                   if field}
        assert zi.ZOTERO_SLOT_FIELD[slot] == derived, f"slot {slot} drifted"


def test_load_env_file_parses_and_ignores_comments(tmp_path):
    f = tmp_path / "k.env"
    f.write_text("# comment\nZOTERO_RW_API_KEY=abc\n\nZOTERO_USER_ID = 42\nnoise\n")
    vals = zi.load_env_file(f)
    assert vals == {"ZOTERO_RW_API_KEY": "abc", "ZOTERO_USER_ID": "42"}


def test_load_env_file_missing_returns_empty(tmp_path):
    assert zi.load_env_file(tmp_path / "absent.env") == {}


# --------------------------------------------------------------------------
# Web-API index: dedup on a machine with no Zotero desktop database.
#
# The defect these guard: on such a machine every match returned "unchecked",
# and a backfill that treats "unchecked" as "absent" re-imports the library.
# --------------------------------------------------------------------------


def _index(works=None, attachments=None):
    return {"schema": zi.INDEX_SCHEMA, "user": "1", "fetched": "2026-08-19T00:00:00Z",
            "works": works or [], "attachments": attachments or []}


def _work(key, title, date="1999", creators=("Artzner",), doi=""):
    return {"key": key, "itemType": "journalArticle", "title": title,
            "date": date, "DOI": doi, "ISBN": "", "url": "", "extra": "",
            "collections": [], "creators": list(creators)}


def _att(key, parent, filename="f.pdf", md5=None, ctype="application/pdf",
         link="imported_file"):
    return {"key": key, "parent": parent, "filename": filename, "md5": md5,
            "contentType": ctype, "linkMode": link}


def test_api_matches_content_hash_is_exact(tmp_path):
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.4 content")
    digest = hashlib.md5(pdf.read_bytes()).hexdigest()
    idx = _index([_work("W1", "Coherent Measures of Risk")],
                 [_att("A1", "W1", "paper.pdf", digest)])
    res = zi.api_matches(idx, pdf_path=pdf)
    assert res["verdict"] == "match"
    assert res["matches"][0]["key"] == "W1"
    assert res["matches"][0]["why"] == ["storageHash"]
    assert res["matches"][0]["certainty"] == "exact"


def test_api_matches_hash_beats_a_renamed_file(tmp_path):
    """Content identity survives renaming — the key the sqlite path lacks."""
    pdf = tmp_path / "MyOwnName-2024.pdf"
    pdf.write_bytes(b"%PDF-1.4 body")
    digest = hashlib.md5(pdf.read_bytes()).hexdigest()
    idx = _index([_work("W1", "Totally Different Recorded Title")],
                 [_att("A1", "W1", "original-publisher-name.pdf", digest)])
    res = zi.api_matches(idx, title="Totally Different Recorded Title", pdf_path=pdf)
    assert res["matches"][0]["key"] == "W1"


def test_api_matches_doi_exact():
    idx = _index([_work("W1", "T", doi="10.1111/1467-9965.00068")])
    res = zi.api_matches(idx, doi="10.1111/1467-9965.00068")
    assert res["verdict"] == "match"
    assert res["matches"][0]["why"] == ["doi"]


def test_api_matches_doi_is_case_insensitive():
    idx = _index([_work("W1", "T", doi="10.1111/ABC")])
    assert zi.api_matches(idx, doi="10.1111/abc")["verdict"] == "match"


def test_api_matches_creator_year_title():
    idx = _index([_work("W1", "Coherent Measures of Risk", "1999", ("Artzner",))])
    res = zi.api_matches(idx, title="Coherent Measures of Risk", year="1999",
                         first_author="Artzner")
    assert res["verdict"] == "match"


def test_api_matches_wrong_author_does_not_match():
    idx = _index([_work("W1", "Coherent Measures of Risk", "1999", ("Artzner",))])
    res = zi.api_matches(idx, title="Coherent Measures of Risk", year="1999",
                         first_author="Delbaen")
    assert res["verdict"] == "none"


def test_api_matches_empty_library_is_none_not_unchecked():
    """A clean negative and a lookup that could not run are different answers."""
    res = zi.api_matches(_index(), title="Some Long Distinctive Title Here",
                         first_author="Nobody")
    assert res["verdict"] == "none"
    assert "creator-year-title" in res["consulted"]


def test_api_matches_no_usable_key_is_unchecked():
    res = zi.api_matches(_index([_work("W1", "T")]))
    assert res["verdict"] == "unchecked"
    assert res["consulted"] == []
    assert res["skipped"]


def test_api_matches_short_title_is_skipped_not_matched():
    idx = _index([_work("W1", "On Growth", "1950", ("Solow",))])
    res = zi.api_matches(idx, title="On Growth", first_author="Solow")
    assert res["verdict"] == "unchecked"
    assert any("too short" in s for s in res["skipped"])


def test_api_matches_reports_missing_file_on_the_work():
    """The present-but-no-file case is what `attach` exists to repair."""
    idx = _index([_work("W1", "Sraffa and von Neumann", "2001", ("Kurz",))], [])
    res = zi.api_matches(idx, title="Sraffa and von Neumann", year="2001",
                         first_author="Kurz")
    assert res["matches"][0]["has_file"] is False


def test_api_matches_linked_url_does_not_count_as_a_stored_file():
    idx = _index([_work("W1", "Sraffa and von Neumann", "2001", ("Kurz",))],
                 [_att("A1", "W1", "", None, "text/html", "linked_url")])
    res = zi.api_matches(idx, title="Sraffa and von Neumann", year="2001",
                         first_author="Kurz")
    assert res["matches"][0]["has_file"] is False


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


def test_index_views_separates_pdf_from_other_stored_files():
    idx = _index([_work("W1", "T"), _work("W2", "U")],
                 [_att("A1", "W1", "a.pdf", "d1", "application/pdf"),
                  _att("A2", "W2", "b.docx", "d2",
                       "application/vnd.openxmlformats-officedocument"
                       ".wordprocessingml.document")])
    v = zi._index_views(idx)
    assert v["parents_with_pdf"] == {"W1"}
    assert v["parents_with_file"] == {"W1", "W2"}


def test_api_matches_scores_overlap_against_the_library_title():
    """Extra document text may surface a true match, never manufacture one.

    The denominator is the library title's own tokens, so a bigger bag of
    document words cannot drag an unrelated item over the threshold.
    """
    idx = _index([_work("W1", "Method of Limits in the Theory of Index Numbers",
                        "1969", ("Afriat",)),
                  _work("W2", "An Entirely Unrelated Study of Something Else",
                        "1969", ("Afriat",))])
    res = zi.api_matches(idx, title="", year="1969", authors=["Afriat"],
                         text="MethodOfLimits Index Numbers method of limits "
                              "in the theory of index numbers")
    assert [m["key"] for m in res["matches"]] == ["W1"]


def test_api_matches_text_alone_is_enough_when_pdfinfo_title_is_junk():
    """The real audit defect: pdfinfo reads 'PII: 0014-2921(69)90001-4'."""
    idx = _index([_work("W1", "Methods of choosing equipment at "
                              "Electricite de France", "1969", ("Bessiere",))])
    junk = "PII: 0014-2921(69)90001-4"
    res = zi.api_matches(idx, title=junk, year="1969", authors=["Bessiere"],
                         text="Methods of choosing equipment at Electricite "
                              "de France")
    assert res["verdict"] == "match"


def test_api_matches_no_title_and_no_text_is_unchecked():
    idx = _index([_work("W1", "Anything At All Here", "1969", ("Afriat",))])
    res = zi.api_matches(idx, year="1969", authors=["Afriat"])
    assert res["verdict"] == "unchecked"
    assert any("no title or text" in s for s in res["skipped"])

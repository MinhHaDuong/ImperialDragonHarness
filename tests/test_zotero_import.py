"""Tests for scripts/zotero-import.py.

Covers the pure extraction/formatting helpers (identifier regexes, RIS
emission) plus the Zotero matcher against a real in-memory SQLite database
built with the minimal slice of Zotero's schema the query touches.
"""

import importlib.util
import sqlite3
import sys
from pathlib import Path

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


def _build_zotero_db() -> sqlite3.Connection:
    """Minimal slice of Zotero's schema for the matcher query."""
    conn = sqlite3.connect(":memory:")
    c = conn.cursor()
    c.executescript(
        """
        CREATE TABLE items (itemID INTEGER PRIMARY KEY);
        CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
        CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE itemData (itemID INT, fieldID INT, valueID INT);
        CREATE TABLE deletedItems (itemID INT);
        CREATE TABLE itemAttachments (itemID INTEGER PRIMARY KEY, parentItemID INT,
                                      path TEXT, contentType TEXT);
        CREATE TABLE fulltextItems (itemID INT, indexedPages INT, totalPages INT);

        INSERT INTO fields VALUES (1,'title'),(2,'DOI'),(3,'date');

        -- item 10: has DOI 10.1/x, title, date, and a PDF attachment
        INSERT INTO items VALUES (10);
        INSERT INTO itemDataValues VALUES (1,'Deep Learning for Climate'),(2,'10.1/x'),(3,'2020-05-01');
        INSERT INTO itemData VALUES (10,1,1),(10,2,2),(10,3,3);
        INSERT INTO itemAttachments VALUES (20, 10, 'storage:paper.pdf', 'application/pdf');
        INSERT INTO fulltextItems VALUES (20, 5, 5);

        -- item 11: title only, NO child attachment (eligible for title-only branch)
        INSERT INTO items VALUES (11);
        INSERT INTO itemDataValues VALUES (4,'Shallow Trees for Weather'),(5,'2019');
        INSERT INTO itemData VALUES (11,1,4),(11,3,5);

        -- item 30: is ITSELF a child attachment (parentItemID set) with a title
        -- identical to item 10's. The no-DOI branch must exclude it via the
        -- `a.itemID IS NULL` filter even though its title would otherwise match.
        INSERT INTO items VALUES (30);
        INSERT INTO itemData VALUES (30,1,1);  -- reuse 'Deep Learning for Climate'
        INSERT INTO itemAttachments VALUES (30, 11, 'storage:child.pdf', 'application/pdf');
        """
    )
    conn.commit()
    return conn


def test_zotero_matches_doi_exact_match():
    conn = _build_zotero_db()
    matches = zi.zotero_matches(
        conn, doi="10.1/X", title=None, year="2020", pdf_path=Path("paper.pdf")
    )
    assert len(matches) == 1
    m = matches[0]
    assert m["itemID"] == 10
    assert m["score"] == 105  # 100 doi + 5 year
    assert "doi" in m["why"] and "year" in m["why"]
    assert m["pdf_basename_match"] is True
    assert m["attachments"][0]["path"] == "storage:paper.pdf"


def test_zotero_matches_title_fuzzy_match():
    conn = _build_zotero_db()
    matches = zi.zotero_matches(
        conn, doi=None, title="Shallow Trees for Weather", year=None, pdf_path=Path("x.pdf")
    )
    ids = [m["itemID"] for m in matches]
    assert 11 in ids  # exact title → Jaccard 1.0 >= 0.6
    # item 10 ("Deep Learning for Climate") shares only "for" with the query →
    # Jaccard well below 0.6 → not matched. (It is NOT excluded for having an
    # attachment; parents with attachments stay eligible in the no-DOI branch.)
    assert 10 not in ids


def test_zotero_matches_excludes_items_that_are_themselves_attachments():
    """The no-DOI branch's `a.itemID IS NULL` filter drops child-attachment items."""
    conn = _build_zotero_db()
    # Query item 10's exact title. Item 10 (a top-level work) matches; item 30
    # has the identical title but IS a child attachment, so it must be excluded
    # — proving the filter, since title alone would otherwise score it as a hit.
    matches = zi.zotero_matches(
        conn, doi=None, title="Deep Learning for Climate", year=None, pdf_path=Path("x.pdf")
    )
    ids = [m["itemID"] for m in matches]
    assert 10 in ids
    assert 30 not in ids


def test_zotero_matches_no_hit_returns_empty():
    conn = _build_zotero_db()
    assert zi.zotero_matches(
        conn, doi="10.9/nope", title=None, year=None, pdf_path=Path("x.pdf")
    ) == []

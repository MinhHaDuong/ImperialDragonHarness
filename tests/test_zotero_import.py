"""Tests for scripts/zotero-import.py.

Covers the pure extraction/formatting helpers (identifier regexes, RIS
emission) plus the Zotero matcher against a real in-memory SQLite database
built with the minimal slice of Zotero's schema the query touches.
"""

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
    "url": "https://example.org/a",
    "journal": "Container Name",
    "volume": "12",
    "issue": "3",
    "pages": "11-24",
    "numPages": 24,
    "publisher": "RAND Corporation",
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


def test_no_input_value_is_dropped_for_any_mapped_type():
    """A value with no home on the target type lands in `extra`, never gone."""
    losses = {}
    for ris_type, zot_type in zi.RIS_TO_ZOTERO_TYPE.items():
        item = _render(ris_type)
        rendered = "\n".join(str(v) for k, v in item.items() if k != "creators")
        missing = sorted(
            key for key, value in MAXIMAL_ENTRY.items()
            if key not in ("authors", "abstract")
            and str(value) not in rendered
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

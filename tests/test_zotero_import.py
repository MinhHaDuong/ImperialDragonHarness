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
    # journalArticle has no numPages field: routed to extra
    assert "pages: 29" in item["extra"]
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
    # book has no DOI field: routed to extra
    assert "DOI: 10.2/y" in item["extra"]
    assert item["collections"] == ["ABCD1234"]


def test_entry_to_zotero_item_unknown_type_falls_back_to_document():
    assert zi.entry_to_zotero_item({"type": "XXXX"}, None)["itemType"] == "document"


def test_load_env_file_parses_and_ignores_comments(tmp_path):
    f = tmp_path / "k.env"
    f.write_text("# comment\nZOTERO_RW_API_KEY=abc\n\nZOTERO_USER_ID = 42\nnoise\n")
    vals = zi.load_env_file(f)
    assert vals == {"ZOTERO_RW_API_KEY": "abc", "ZOTERO_USER_ID": "42"}


def test_load_env_file_missing_returns_empty(tmp_path):
    assert zi.load_env_file(tmp_path / "absent.env") == {}

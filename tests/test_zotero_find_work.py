"""find-work and the lookups behind check-staging and create-items.

Ticket 1116: the duplicate lookup asks Zotero's own search through the local
API (`q`, `qmode=everything`) for each key; the only match it asserts is an
identifier equal to the hit's own field (or the hit holding the PDF's md5),
and a title search returns candidates, never a match; no call reads the
whole library. Author decision, 2026-10-16: "In tests up Zotero as a fixture
or skip -- no mock". So:

- the lookups run against a REAL Zotero desktop client on a throwaway
  profile, data directory, port and private display (tests/zotero_live.py),
  a client of its own seeded once for this module; those tests are marked
  `integration` and skip where that client cannot run;
- the identifier forms are pure logic, tested here without Zotero;
- the autouse fixture leaves Zotero down (closed port, ZOTERO_NO_LAUNCH)
  for every other test.

No test touches ~/Zotero, the author's profile or port 23119.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from pyzotero import _client as pyzotero_client

import zotero_live
from test_zotero_import import make_pdf
from zotero_live import closed_port

zotero_factory = zotero_live.zotero_factory
zi = zotero_live.helper_module()

HOFFMAN = "Systems of inequalities involving convex functions"


@pytest.fixture(autouse=True)
def zotero_down(monkeypatch, tmp_path):
    with closed_port() as port:
        monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")
        monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(tmp_path / "no-key.env"))
        yield


# ── pure: identifier forms ───────────────────────────────────────────────────


def test_isbn_forms_cover_ten_and_thirteen_digits_bare_and_hyphenated():
    assert zi.isbn_queries("9780306406157") == sorted(
        {"9780306406157", "978-0-306-40615-7", "0306406152", "0-306-40615-2"})
    assert zi.isbn13s("978-0-306-40615-7 0306406152") == {"9780306406157"}
    assert zi.isbn13s("ISBN 123") == set(), "a bad check digit is no ISBN"


def test_doi_forms_drop_the_resolver_prefix_and_case():
    assert zi.normal_doi("https://doi.org/10.1111/ABC") == "10.1111/abc"
    assert zi.normal_doi("doi: 10.1111/abc") == "10.1111/abc"
    assert zi.normal_doi("https://www.doi.org/10.1111/ABC") == "10.1111/abc"
    assert zi.normal_doi("doi.org/10.1111/abc") == "10.1111/abc"


def test_zotero_10_is_the_floor():
    """Ticket 1116: Zotero 10 or later for the whole helper. Pure: a
    client older than the installed one cannot be started here, and a
    fake server is ruled out."""
    zi.check_version("10.0.6")
    zi.check_version("11.0")
    for old in ("9.0.4", "7.0.15", "", "beta"):
        with pytest.raises(zi.LocalAPIError, match="needs Zotero 10 or later"):
            zi.check_version(old)


def test_no_key_at_all_is_unchecked_and_asks_zotero_nothing():
    """"Found nothing" and "could not look" stay distinguishable; with no
    key to look up, nothing is sent (Zotero is down here)."""
    res = zi.find_work(zi.libraries())
    assert res["verdict"] == "unchecked" and res["matches"] == []
    assert res["consulted"] == []
    for label in ("doi", "isbn", "arxiv", "handle", "title", "storageHash"):
        assert any(s.startswith(label) for s in res["skipped"]), label


def test_an_invalid_isbn_is_skipped_not_consulted():
    """No query to send: the ISBN key did not look, so it cannot vouch for
    an entry being new (Zotero is down here and is not asked)."""
    res = zi.find_work(zi.libraries(), isbn="ISBN 123")
    assert "isbn" not in res["consulted"] and res["verdict"] == "unchecked"
    assert any(s.startswith("isbn (not a valid") for s in res["skipped"])


@pytest.mark.parametrize("key,value", [
    ("doi", " "), ("doi", "doi:"), ("doi", "https://doi.org/"),
    ("arxiv", " "), ("arxiv", "arXiv:"), ("handle", "https://hdl.handle.net/"),
    ("handle", "x")])
def test_a_blank_identifier_is_skipped_not_consulted(key, value):
    """Nothing to search for: an empty query would match everything or
    nothing, and either way the key did not look."""
    res = zi.find_work(zi.libraries(), **{key: value})
    assert key not in res["consulted"] and res["verdict"] == "unchecked"


def test_arxiv_ids_are_normalised():
    for raw in ("2401.01234", "arXiv:2401.01234", "arXiv:2401.01234v2",
                "https://arxiv.org/abs/2401.01234v3", "2401.01234V1"):
        assert zi.normal_arxiv(raw) == "2401.01234", raw
    assert zi.normal_arxiv("hep-th/9901001") == "hep-th/9901001"
    assert zi.normal_arxiv("not an id") == ""


def test_the_default_scope_is_the_user_library_alone():
    """A copy in a group library does not count as already present unless
    the caller widens the scope (--library all or a groupID)."""
    assert [lib for lib, _ in zi.libraries()] == ["user"]
    assert [lib for lib, _ in zi.libraries("4242")] == ["4242"]


def test_a_failing_pdfinfo_does_not_stop_a_staging_check(tmp_path, monkeypatch):
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4")

    def boom(path):
        raise RuntimeError("pdfinfo timed out")

    monkeypatch.setattr(zi, "pdfinfo", boom)
    assert zi.audit_one(pdf, zi.libraries())["verdict"] == "unidentified"


def test_a_chapters_isbn_is_not_looked_up():
    """A chapter carries its book's ISBN: looking it up would match the
    book (Zotero is down here and is not asked)."""
    res = zi.find_work(zi.libraries(), isbn="9780306406157",
                       item_type="bookSection")
    assert "isbn" not in res["consulted"] and res["verdict"] == "unchecked"
    assert "isbn (the volume's, for a bookSection)" in res["skipped"]


VOLUME_BIB_TYPES = ("book", "proceedings", "collection", "reference",
                    "mvbook", "mvcollection", "mvreference")


def test_every_part_like_bib_type_is_a_part_and_no_volume_is():
    """Choice #4: a part's ISBN identifies its volume. Every BibTeX type
    mapped to a Zotero part type skips the ISBN; a volume type keeps it."""
    for bib_type in ("incollection", "inbook", "inproceedings", "conference",
                     "inreference", "bookinbook", "suppbook",
                     "suppcollection"):
        assert zi.BIB_TO_ZOTERO_TYPE[bib_type] in zi.ISBN_OF_A_VOLUME, bib_type
    for bib_type in VOLUME_BIB_TYPES:
        assert zi.BIB_TO_ZOTERO_TYPE[bib_type] not in zi.ISBN_OF_A_VOLUME, \
            bib_type


@pytest.mark.parametrize("bib_type", ["misc", "online", "suppperiodical", ""])
def test_an_unmapped_bib_type_never_looks_its_isbn_up(tmp_path, bib_type):
    """Fail closed: a .bib type the helper cannot place (@suppperiodical
    among them) may be a part carrying its volume's ISBN (Zotero is down
    here and is not asked)."""
    path = tmp_path / "a.txt"
    path.write_text("x")
    res = zi.audit_one(path, zi.libraries(),
                       bib_entry={"_type": bib_type, "isbn": "9780306406157"})
    assert any(s.startswith("isbn (unmapped .bib type")
               for s in res["skipped"]), res["skipped"]


def test_a_short_title_is_skipped_not_searched():
    """"On Growth" would return any work at all: not a key that looked."""
    res = zi.find_work(zi.libraries(), title="On Growth")
    assert res["verdict"] == "unchecked" and "title" not in res["consulted"]
    assert any(s.startswith("title (fewer than") for s in res["skipped"])


def test_the_helper_no_longer_reads_the_whole_library_per_lookup():
    text = (Path(zi.__file__)).read_text()
    for gone in ("def read_library", "def library_matches", "def _library_views",
                 "def _surname_in_text", "def entry_identity_keys",
                 "def attachment_digest", "def entry_to_ris"):
        assert gone not in text, gone


def test_no_scorer_is_left():
    """Author decision 9 (2026-10-16): the helper asserts exact
    identifiers only; title scoring, corroboration and the year window
    are gone, and so is rapidfuzz."""
    text = (Path(zi.__file__)).read_text()
    for gone in ("rapidfuzz", "def title_certainty", "def corroborate",
                 "skip-corroboration", "STRONG_TITLE", "abs(ours - theirs)"):
        assert gone not in text, gone
    pyproject = (Path(zi.__file__).parent.parent / "pyproject.toml").read_text()
    assert "rapidfuzz" not in pyproject


# ── live: a client of its own, seeded once ───────────────────────────────────


@pytest.fixture(scope="module")
def library(zotero_factory, tmp_path_factory):
    zotero = zotero_factory("findwork")
    files = tmp_path_factory.mktemp("findwork-files")
    stored = make_pdf(files / "original-publisher-name.pdf",
                      ["Totally Different Recorded Title", "by Renamer"])
    shared = make_pdf(files / "shared.pdf", ["Working paper", "by Tiebreak"])
    junk = make_pdf(files / "publisher-scan.pdf", ["Quasar Gimbal Lemma"],
                    {"Title": "Microsoft Word - qg1979 final draft v2"})
    shared_copy = files / "shared-copy.pdf"
    shared_copy.write_bytes(shared.read_bytes())
    keys = {
        "doi": zotero.save("Deep Learning for Climate", date="2020-05-01",
                           DOI="10.5555/Deep.X"),
        "decoy": zotero.save("Unrelated thing", creators=("Jones",),
                             abstractNote="we cite 10.5555/Deep.X here"),
        "nozick": zotero.save("Anarchy, State, and Utopia", item_type="book",
                              creators=("Nozick",), date="1974"),
        "isbn": zotero.save("Handbook of Something", item_type="book",
                            date="2016", ISBN="978-0-13-468599-1"),
        "arxiv_tagged": zotero.save("A Tagged Preprint",
                                    extra="arXiv: 2403.00001 [cs.LG]"),
        "arxiv_archive": zotero.save("An Archived Preprint", item_type="preprint",
                                     archiveID="arXiv:2404.00002"),
        "redirect": zotero.save("A Redirected Page", item_type="webpage",
                                url="https://example.org/go?to=https://arxiv.org"
                                    "/abs/2405.00003&h=hdl.handle.net/10419/999"),
        "chapter": zotero.save("A Chapter of the Handbook",
                               item_type="bookSection",
                               ISBN="978-0-13-468599-1"),
        "comment": zotero.save("A Comment", extra="Comment on 10.5555/orig.1"),
        "doi_line": zotero.save("A Report With Its DOI in Extra",
                                item_type="report",
                                extra="Series: X\nDOI: 10.5555/InExtra.1"),
        "isbn10": zotero.save("Old Handbook", item_type="book",
                              ISBN="0306406152"),
        "arxiv_extra": zotero.save("An Arxiv Preprint",
                                   extra="arXiv:2401.01234"),
        "arxiv_url": zotero.save("Another Arxiv Preprint",
                                 url="https://arxiv.org/abs/2402.05678"),
        "handle": zotero.save("A Handle Report", item_type="report",
                              url="https://hdl.handle.net/10419/12345"),
        "hash": zotero.save("Totally Different Recorded Title",
                            creators=("Renamer",), date="2024", pdf=stored),
        "junk": zotero.save("Quasar Gimbal Lemma", creators=("Valiant",),
                            date="1979", pdf=junk),
        "tie_wp": zotero.save("Working Paper Version", creators=("Tiebreak",),
                              DOI="10.5555/tie", pdf=shared),
        "tie_journal": zotero.save("Journal Version", creators=("Tiebreak",),
                                   DOI="10.5555/tie", pdf=shared_copy),
        "hoffman": zotero.save(HOFFMAN, creators=("Hoffman",), date="1957"),
        "artzner": zotero.save("Coherent Measures of Risk",
                               creators=("Artzner",), date="1999"),
        "kurz": zotero.save("Sraffa and von Neumann", creators=("Kurz",),
                            date="2001"),
        "afriat": zotero.save("Method of Limits in the Theory of Index Numbers",
                              creators=("Afriat",), date="1969"),
        "afriat_other": zotero.save("An Entirely Unrelated Study of Something "
                                    "Else", creators=("Afriat",), date="1969"),
        "garcia": zotero.save("Cien años de soledad", item_type="book",
                              creators=("García Márquez",), date="1967"),
        "bessiere": zotero.save("Methods of choosing equipment at Électricité "
                                "de France", creators=("Bessière",), date="1969"),
    }
    linked = zotero.client().create_items([{
        "itemType": "attachment", "linkMode": "linked_url",
        "url": "https://example.org/kurz", "title": "Publisher page",
        "contentType": "text/html", "parentItem": keys["kurz"],
        "tags": [], "relations": {}}])
    assert linked["successful"], linked
    return zotero, keys, {"stored": stored, "shared": shared, "junk": junk}


@pytest.fixture
def lib(library, monkeypatch):
    zotero, keys, files = library
    zotero_live.point_helper_at(zotero, monkeypatch)
    return keys, files


def find(**kwargs):
    return zi.find_work(zi.libraries(), **kwargs)


@pytest.mark.integration
def test_a_doi_is_an_exact_match_whatever_its_case(lib):
    keys, _ = lib
    for doi in ("10.5555/Deep.X", "10.5555/deep.x", "https://doi.org/10.5555/DEEP.X"):
        res = find(doi=doi)
        (m,) = res["matches"]
        assert m["key"] == keys["doi"] and m["why"] == ["doi"], doi
        assert res["verdict"] == "match"
        assert res["source"] == zi.LIBRARY_SOURCE


@pytest.mark.integration
def test_a_doi_quoted_in_an_abstract_is_not_the_items_doi(lib):
    """Zotero's quick search returns the decoy too (the DOI is a substring
    of its abstract); the helper checks the item's own DOI field."""
    keys, _ = lib
    z = zi.local_library()
    returned = {w["key"] for w in zi.search_works(z, "user", "10.5555/deep.x")}
    assert keys["decoy"] in returned, "positive control: the search sees it"
    assert keys["decoy"] not in {m["key"] for m in find(doi="10.5555/deep.x")[
        "matches"]}


@pytest.mark.integration
def test_only_a_doi_line_in_extra_is_the_items_doi(lib):
    """Extra holds a DOI the type has no field for as a `DOI:` line; a DOI
    mentioned anywhere else there (a comment's target) is another work's,
    and must not file that work's PDF under the comment."""
    keys, _ = lib
    (m,) = find(doi="10.5555/inextra.1")["matches"]
    assert m["key"] == keys["doi_line"] and m["why"] == ["doi"]
    z = zi.local_library()
    returned = {w["key"] for w in zi.search_works(z, "user", "10.5555/orig.1")}
    assert keys["comment"] in returned, "positive control: the search sees it"
    res = find(doi="10.5555/orig.1")
    assert res["matches"] == [] and res["verdict"] == "none"


@pytest.mark.integration
def test_no_hit_is_none_not_unchecked(lib):
    res = find(doi="10.5555/nowhere")
    assert res["matches"] == [] and res["verdict"] == "none"
    assert res["consulted"] == ["doi"]
    for label in ("isbn", "arxiv", "handle"):
        assert any(s.startswith(label) for s in res["skipped"]), label


@pytest.mark.integration
def test_an_isbn_matches_across_hyphenation_and_length(lib):
    keys, _ = lib
    # The chapter carries the volume's ISBN: it is not the volume.
    returned = {w["key"] for w in zi.search_works(zi.local_library(), "user",
                                                   "978-0-13-468599-1")}
    assert keys["chapter"] in returned, "positive control: the search sees it"
    assert [m["key"] for m in find(isbn="9780134685991")["matches"]] == [keys["isbn"]]
    assert [m["key"] for m in find(isbn="0-13-468599-7")["matches"]] == [keys["isbn"]]
    assert zi.isbnlib.to_isbn10("9780134685991") == "0134685997"
    (m,) = find(isbn="978-0-306-40615-7")["matches"]
    assert m["key"] == keys["isbn10"] and m["why"] == ["isbn"]


@pytest.mark.integration
def test_arxiv_ids_and_handles_are_found_in_their_own_fields(lib):
    keys, _ = lib
    assert [m["key"] for m in find(arxiv="2401.01234")["matches"]] == [keys["arxiv_extra"]]
    assert [m["key"] for m in find(arxiv="arXiv:2401.01234v2")["matches"]] == [
        keys["arxiv_extra"]]
    assert [m["key"] for m in find(arxiv="2402.05678")["matches"]] == [keys["arxiv_url"]]
    for supplied in ("10419/12345", "https://hdl.handle.net/10419/12345"):
        (m,) = find(handle=supplied)["matches"]
        assert m["key"] == keys["handle"] and m["why"] == ["handle"], supplied
    assert [m["key"] for m in find(arxiv="2403.00001")["matches"]] == [
        keys["arxiv_tagged"]], "an Extra line may carry a subject class"
    assert [m["key"] for m in find(arxiv="2404.00002")["matches"]] == [
        keys["arxiv_archive"]], "a preprint's archiveID is its own field"


@pytest.mark.integration
def test_an_identifier_inside_another_url_is_not_the_items(lib):
    """A redirect URL embedding an arXiv or handle link is the page's own
    URL, not that work's identifier."""
    keys, _ = lib
    z = zi.local_library()
    returned = {w["key"] for w in zi.search_works(z, "user", "2405.00003")}
    assert keys["redirect"] in returned, "positive control: the search sees it"
    assert find(arxiv="2405.00003")["matches"] == []
    assert find(handle="10419/999")["matches"] == []


@pytest.mark.integration
@pytest.mark.parametrize("title", ["anarchy state and utopia",
                                   "Anarchy: State, and Utopia!"])
def test_a_title_returns_candidates_never_a_match(lib, title):
    """Author decision 9: a title hit is for the caller to judge. Words are
    searched, so punctuation does not glue them together."""
    keys, _ = lib
    res = find(title=title)
    assert res["matches"] == [] and res["verdict"] == "candidates"
    (c,) = [c for c in res["candidates"] if c["key"] == keys["nozick"]]
    assert c["why"] == ["title"] and "certainty" not in c
    assert "title" in res["consulted"]


@pytest.mark.integration
def test_the_same_title_is_still_only_a_candidate(lib):
    """Even a stored title equal to the one given: no title is a match."""
    keys, _ = lib
    res = find(title=HOFFMAN)
    assert res["verdict"] == "candidates" and res["matches"] == []
    assert [c["key"] for c in res["candidates"]] == [keys["hoffman"]]


@pytest.mark.integration
def test_find_work_cli_reports_candidates(lib, capsys):
    keys, _ = lib
    args = argparse.Namespace(doi=None, isbn=None, arxiv=None, handle=None,
                              title="Cien años de soledad", pdf=None,
                              library="user", metadata=None)
    assert zi.cmd_find_work(args) == 0
    (result,) = json.loads(capsys.readouterr().out)["results"]
    assert result["verdict"] == "candidates"
    assert [c["key"] for c in result["candidates"]] == [keys["garcia"]]


@pytest.mark.integration
def test_an_unknown_title_finds_nothing(lib):
    res = find(title="Wholly Absent Treatise on Turbines")
    assert res["verdict"] == "none" and res["candidates"] == []
    assert "title" in res["consulted"]


@pytest.mark.integration
def test_a_work_without_a_stored_file_says_so(lib):
    """The present-but-no-file case suggest-attachments repairs; a linked
    URL is not a stored file."""
    keys, _ = lib
    (artzner,) = find(title="Coherent Measures of Risk")["candidates"]
    assert artzner["key"] == keys["artzner"] and artzner["has_file"] is False
    (kurz,) = find(title="Sraffa and von Neumann")["candidates"]
    assert kurz["key"] == keys["kurz"] and kurz["has_file"] is False


@pytest.mark.integration
def test_a_renamed_copy_is_found_by_its_content(lib, tmp_path):
    """Content identity survives renaming: a title candidate holding a
    stored file with the probe's md5 is a match, the only one a title
    search can lead to."""
    keys, files = lib
    probe = tmp_path / "MyOwnName-2024.pdf"
    shutil.copyfile(files["stored"], probe)
    res = find(title="Totally Different Recorded Title", pdf_path=probe)
    (m,) = res["matches"]
    assert m["key"] == keys["hash"] and m["why"] == ["storageHash", "title"]
    assert res["verdict"] == "match" and m["has_pdf"] is True
    assert m["attachment"]["md5"] == hashlib.md5(probe.read_bytes()).hexdigest()
    assert "storageHash" in res["consulted"]


@pytest.mark.integration
def test_one_file_under_two_records_names_both(lib, tmp_path):
    """Ticket 0570: two records legitimately sharing one file tie; neither
    vanishes."""
    keys, files = lib
    probe = tmp_path / "local.pdf"
    shutil.copyfile(files["shared"], probe)
    res = find(doi="10.5555/tie", pdf_path=probe)
    assert res["verdict"] == "ambiguous"
    assert {m["key"] for m in res["matches"]} == {keys["tie_wp"], keys["tie_journal"]}
    assert all(m["why"][0] == "storageHash" for m in res["matches"])


# ── live: check-staging rows ─────────────────────────────────────────────────


def row(path, bib_entry=None):
    return zi.audit_one(path, zi.libraries(), bib_entry=bib_entry)


@pytest.mark.integration
def test_check_staging_verdicts_cover_every_answer(lib, tmp_path):
    keys, files = lib
    identical = tmp_path / "Renamer2024-TotallyDifferentRecordedTitle.pdf"
    shutil.copyfile(files["stored"], identical)
    assert row(identical)["verdict"] == "identical"
    assert "also_matches" not in row(identical)

    scanned = make_pdf(tmp_path / "Artzner1999-x.pdf", [],
                       {"Title": "Coherent Measures of Risk"})
    judged = row(scanned)
    assert judged["verdict"] == "candidates" and judged["zotero_key"] is None
    assert [c["key"] for c in judged["candidates"]] == [keys["artzner"]]

    absent = make_pdf(tmp_path / "Nobody1999-UnrelatedTurbineDocument.pdf",
                      ["An Unrelated Document About Turbines"])
    nothing = row(absent)
    assert nothing["verdict"] == "absent"
    assert nothing["consulted"], "absent must mean 'looked and found nothing'"

    thin = make_pdf(tmp_path / "scan0001.pdf", ["page 1"])
    unknown = row(thin)
    assert unknown["verdict"] == "unidentified", "could not look is not absent"
    assert unknown["consulted"] == []


@pytest.mark.integration
def test_check_staging_retries_with_the_filename_when_the_embedded_title_is_junk(
        lib, tmp_path):
    """Issue #1654: a publisher-tool /Title long enough to be searched
    matches no item; the filename title must still be tried, and the hash
    then reads identical, not absent."""
    keys, files = lib
    probe = tmp_path / "Valiant1979-QuasarGimbalLemma.pdf"
    shutil.copyfile(files["junk"], probe)
    assert zi._pdf_info(probe)["Title"].startswith("Microsoft Word")
    judged = row(probe)
    assert judged["verdict"] == "identical"
    assert judged["zotero_key"] == keys["junk"]


@pytest.mark.integration
def test_check_staging_names_every_tied_parent(lib, tmp_path):
    keys, files = lib
    probe = tmp_path / "Tiebreak2020-shared.pdf"
    shutil.copyfile(files["shared"], probe)
    result = row(probe, {"doi": "10.5555/tie"})
    assert result["verdict"] == "identical"
    named = {result["zotero_key"]} | {m["key"] for m in result["also_matches"]}
    assert named == {keys["tie_wp"], keys["tie_journal"]}


@pytest.mark.integration
def test_check_staging_uses_the_bib_doi_for_a_linked_file(lib, tmp_path):
    """The bib entry's DOI is what finds the work: the PDF says nothing."""
    keys, _ = lib
    pdf = make_pdf(tmp_path / "paper.pdf", ["nothing useful"])
    result = row(pdf, {"_key": "x", "title": "Useful Paper",
                       "doi": "10.5555/Deep.X",
                       "author": "Levin, John and Smith, Jane", "year": "1997"})
    assert result["zotero_key"] == keys["doi"] and result["why"] == ["doi"]
    assert result["verdict"] == "work_present_no_file"


@pytest.mark.integration
def test_check_staging_never_files_a_chapter_under_its_book(lib, tmp_path):
    """An @incollection entry carries its volume's ISBN; the book holding
    it is not the chapter, so --apply --edit must not attach to it."""
    keys, _ = lib
    pdf = make_pdf(tmp_path / "chapter.pdf", ["nothing useful"])
    result = row(pdf, {"_type": "incollection", "title": "Some Chapter Title Here",
                       "isbn": "978-0-13-468599-1"})
    assert result["zotero_key"] != keys["isbn"]
    assert result["verdict"] in ("absent", "candidates")
    assert any(s.startswith("isbn (the volume's") for s in result["skipped"])


@pytest.mark.integration
@pytest.mark.parametrize("bib_type", ["incollection", "inbook", "inproceedings",
                                      "conference", "inreference",
                                      "bookinbook", "suppbook",
                                      "suppcollection", "suppperiodical"])
def test_no_part_like_bib_type_is_filed_under_its_volume(lib, tmp_path,
                                                         bib_type):
    keys, _ = lib
    pdf = make_pdf(tmp_path / "part.pdf", ["nothing useful"])
    result = row(pdf, {"_type": bib_type, "title": "Some Part Title Here",
                       "isbn": "978-0-13-468599-1"})
    # Mapped to a part type, or unmapped and failing closed (@suppperiodical).
    assert any(s.startswith(("isbn (the volume's", "isbn (unmapped .bib type"))
               for s in result["skipped"]), (bib_type, result["skipped"])
    # Positive control: as a volume, the same ISBN finds the volume.
    for volume in ("book", "proceedings"):
        book = row(pdf, {"_type": volume, "title": "Some Part Title Here",
                         "isbn": "978-0-13-468599-1"})
        assert book["zotero_key"] == keys["isbn"], volume


@pytest.mark.integration
def test_find_work_type_flag_keeps_a_chapter_off_its_book(lib, capsys):
    keys, _ = lib
    base = dict(doi=None, isbn="978-0-13-468599-1", arxiv=None, handle=None,
                title=None, pdf=None, library="user", metadata=None)
    assert zi.cmd_find_work(argparse.Namespace(**base, type=None)) == 0
    (as_book,) = json.loads(capsys.readouterr().out)["results"]
    assert [m["key"] for m in as_book["matches"]] == [keys["isbn"]]
    assert zi.cmd_find_work(argparse.Namespace(**base, type="bookSection")) == 0
    (as_part,) = json.loads(capsys.readouterr().out)["results"]
    assert as_part["matches"] == [] and as_part["verdict"] == "unchecked"


@pytest.mark.integration
def test_check_staging_searches_the_bib_title(lib, tmp_path):
    keys, _ = lib
    pdf = make_pdf(tmp_path / "paper.pdf", ["nothing useful"])
    result = row(pdf, {"author": "Artzner, Philippe and Delbaen, Freddy",
                       "title": "Coherent Measures of Risk", "year": "1999"})
    assert result["verdict"] == "candidates"
    assert [c["key"] for c in result["candidates"]] == [keys["artzner"]]


@pytest.mark.integration
def test_a_named_bib_identifies_files_named_by_bibkey(lib, tmp_path,
                                                      monkeypatch, capsys):
    """Ticket 1195 on a live client. Positive control: a stored PDF filed
    under a bibkey name, described by a .bib three levels down, is found
    (identical: the stored copy's md5), not unidentified. Negative control:
    a described file with no Zotero item is absent. A bibkey file the .bib
    does not describe stays unidentified."""
    _, files = lib
    articles = tmp_path / "docs" / "articles"
    (articles / "_superseded").mkdir(parents=True)
    shutil.copyfile(files["stored"], articles / "michaelowa2011.pdf")
    make_pdf(articles / "nothere2012.pdf", ["A Wholly Absent Document"])
    make_pdf(articles / "ghost2020.pdf", ["page 1"])
    shutil.copyfile(files["stored"], articles / "_superseded" / "old2001.pdf")
    bib = tmp_path / "deliverables" / "_shared" / "bibliography" / "main.bib"
    bib.parent.mkdir(parents=True)
    bib.write_text(
        "@article{michaelowa2011, title={Totally Different Recorded Title},"
        " year={2024}, file={docs/articles/michaelowa2011.pdf}}\n"
        "@article{nothere2012, title={Turbine Maintenance Intervals Revisited"
        " Entirely}, year={2012}, file={docs/articles/nothere2012.pdf}}\n")
    args = argparse.Namespace(
        root=str(tmp_path), dir="docs/articles", out=None, apply=False,
        edit=False, library="user", skip_underscore_dirs=True,
        bib=["deliverables/_shared/bibliography/main.bib"])
    assert zi.cmd_check_staging(args) == 0
    report = json.loads(capsys.readouterr().out)
    verdicts = {r["file"]: r["verdict"] for r in report["rows"]}
    assert verdicts["michaelowa2011.pdf"] in ("identical", "work_present_with_file")
    assert verdicts["nothere2012.pdf"] == "absent"
    assert verdicts["ghost2020.pdf"] == "unidentified"
    assert "old2001.pdf" not in verdicts


@pytest.mark.integration
def test_every_request_of_a_staging_check_is_a_search(lib, tmp_path,
                                                       monkeypatch, capsys):
    """No whole-library read per call: every items request a check-staging
    run sends carries a search (`q`), an item key, or asks for one item's
    children."""
    sent = []
    real = zi.http_client

    def recording(timeout=zi.WRITE_TIMEOUT):
        client = real(timeout)
        client.event_hooks["request"].append(lambda request: sent.append(request.url))
        return client

    monkeypatch.setattr(zi, "http_client", recording)
    docs = tmp_path / "docs"
    docs.mkdir()
    make_pdf(docs / "Hoffman1957-SystemsOfInequalities.pdf",
             [HOFFMAN, "by A. J. Hoffman"])
    make_pdf(docs / "Nobody1999-UnrelatedTurbineDocument.pdf",
             ["An Unrelated Document About Turbines"])
    args = argparse.Namespace(root=str(tmp_path), dir="docs", out=None,
                              apply=False, edit=False, library="user")
    assert zi.cmd_check_staging(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["summary"] == {"candidates": 1, "absent": 1}
    find_args = argparse.Namespace(doi="10.5555/Deep.X", isbn=None, arxiv=None,
                                   handle=None, title=HOFFMAN, pdf=None,
                                   library="user", metadata=None)
    assert zi.cmd_find_work(find_args) == 0
    capsys.readouterr()
    items = [u for u in sent if "/items" in u.path]
    assert items, "positive control: the runs did read items"
    for url in items:
        assert ("q" in url.params or "itemKey" in url.params
                or url.path.endswith("/children")), str(url)


# ── live: a slow read is a visible failure ───────────────────────────────────


@pytest.mark.integration
def test_a_slow_read_is_not_reported_as_unavailable(lib, tmp_path, monkeypatch,
                                                    capsys):
    """Ticket 1116: a read Zotero does not finish in time fails visibly, with
    its own verdict and a non-zero exit, check-staging included (which exits
    0 when Zotero is merely unavailable). The real client is made slow by
    giving pyzotero's per-request timeout no time at all."""
    docs = tmp_path / "docs"
    docs.mkdir()
    make_pdf(docs / "Hoffman1957-SystemsOfInequalities.pdf",
             [HOFFMAN, "by A. J. Hoffman"])
    args = argparse.Namespace(root=str(tmp_path), dir="docs", out=None,
                              apply=False, edit=False, library="user")
    # Positive control: with the normal timeout the same run completes.
    assert zi.cmd_check_staging(args) == 0
    capsys.readouterr()
    monkeypatch.setattr(pyzotero_client, "DEFAULT_TIMEOUT", 1e-6)
    assert zi.cmd_check_staging(args) == zi.EXIT_SLOW
    report = json.loads(capsys.readouterr().out)
    assert report["verdict"] == "zotero_slow"
    assert report["zotero"]["status"] == "slow"
    find_args = argparse.Namespace(doi="10.5555/Deep.X", isbn=None, arxiv=None,
                                   handle=None, title=None, pdf=None,
                                   library="user", metadata=None)
    assert zi.cmd_find_work(find_args) == zi.EXIT_SLOW
    out = json.loads(capsys.readouterr().out)
    assert out["zotero"] == "slow" and out["verdict"] == "unchecked"
    assert zi.EXIT_SLOW not in (0, zi.EXIT_UNAVAILABLE)

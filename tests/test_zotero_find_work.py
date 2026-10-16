"""find-work and the lookups behind check-staging and create-items.

Ticket 1116: the duplicate lookup asks Zotero's own search through the local
API (`q`, `qmode=everything`) for each key and scores titles with rapidfuzz;
no call reads the whole library. Author decision, 2026-10-16: "In tests up
Zotero as a fixture or skip -- no mock". So:

- the lookups run against a REAL Zotero desktop client on a throwaway
  profile, data directory, port and private display (tests/zotero_live.py),
  a client of its own seeded once for this module; those tests are marked
  `integration` and skip where that client cannot run;
- the title scorer and the identifier forms are pure logic, tested here
  without Zotero;
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
from zotero_live import free_port

zotero_factory = zotero_live.zotero_factory
zi = zotero_live.helper_module()

HOFFMAN = "Systems of inequalities involving convex functions"
SCATTERED = ("Some recent applications of the theory of linear\n"
             "inequalities to extremal combinatorial analysis\n"
             "by Alan J. Hoffman\n"
             "we consider systems of constraints\n"
             "the objective functions are convex\n"
             "involving several parameters\n")
BODY = ("we consider systems of constraints\n"
        "the objective functions are convex\n"
        "involving several unrelated parameters\n")


@pytest.fixture(autouse=True)
def zotero_down(monkeypatch, tmp_path):
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{free_port()}")
    monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(tmp_path / "no-key.env"))


# ── pure: the title scorer ───────────────────────────────────────────────────


def test_a_title_on_one_line_is_strong():
    text = f"{HOFFMAN}\nby A. J. Hoffman"
    assert zi.title_certainty(HOFFMAN, None, text, "1957", "1957") == "strong"


def test_scattered_vocabulary_is_weak_not_strong():
    """The five ordinary words of the title, scattered through a paper
    about linear inequalities, are a hint to look at, not the title."""
    assert zi.title_certainty(HOFFMAN, None, SCATTERED, "1960", "1957") == "weak"


def test_window_precision_separates_a_title_line_from_a_body_window():
    assert zi.title_certainty(HOFFMAN, None, BODY, "1957", "1957") == "weak"
    assert zi.title_certainty(HOFFMAN, None, HOFFMAN, "1957", "1957") == "strong"


def test_a_body_paragraph_quoting_the_title_is_not_the_title():
    quoted = (f"as Hoffman showed in {HOFFMAN} the results carry over to the "
              f"general case with several further assumptions on the domain")
    assert zi.title_certainty(HOFFMAN, None, quoted, None, "1957") == "weak"


def test_casing_punctuation_and_accents_do_not_matter():
    assert zi.title_certainty("Anarchy, State, and Utopia",
                              "anarchy state and utopia", None,
                              "1974", "1974") == "strong"
    assert zi.title_certainty(
        "Methods of choosing equipment at Électricité de France",
        "PII: 0014-2921(69)90001-4",
        "Methods of choosing equipment at Electricite de France",
        "1969", "1969") == "strong"


def test_a_distant_year_demotes_a_title_match_to_weak():
    """A reprint or translation date (Kantorovich 1942 filed as 2004) is no
    proof of a wrong match, and no proof of a right one either."""
    assert zi.title_certainty("Coherent Measures of Risk",
                              "Coherent Measures of Risk", None,
                              "2004", "1999") == "weak"


def test_a_short_generic_stored_title_is_never_strong():
    """A stored "Introduction" would otherwise be any paper's heading."""
    assert zi.title_certainty("Introduction", None, "1 Introduction\nbody",
                              "2020", "2020") == "weak"


def test_a_two_word_stored_title_can_still_be_strong():
    assert zi.title_certainty("Being and Time", "Being and Time", None,
                              "1927", "1927") == "strong"


def test_an_unrelated_title_scores_nothing():
    assert zi.title_certainty("An Entirely Unrelated Study of Something Else",
                              None, "method of limits in the theory of index "
                              "numbers", "1969", "1969") is None


# ── pure: identifier forms ───────────────────────────────────────────────────


def test_isbn_forms_cover_ten_and_thirteen_digits_bare_and_hyphenated():
    assert zi.isbn_queries("9780306406157") == sorted(
        {"9780306406157", "978-0-306-40615-7", "0306406152", "0-306-40615-2"})
    assert zi.isbn13s("978-0-306-40615-7 0306406152") == {"9780306406157"}
    assert zi.isbn13s("ISBN 123") == set(), "a bad check digit is no ISBN"


def test_doi_forms_drop_the_resolver_prefix_and_case():
    assert zi.normal_doi("https://doi.org/10.1111/ABC") == "10.1111/abc"
    assert zi.normal_doi("doi: 10.1111/abc") == "10.1111/abc"


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
    for label in ("doi", "isbn", "arxiv", "handle", "creator-year-title",
                  "storageHash"):
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


def test_a_title_alone_never_matches():
    res = zi.find_work(zi.libraries(), title="A Totally Unrelated Long Title")
    assert res["verdict"] == "unchecked"
    assert any("no author supplied" in s for s in res["skipped"])


def test_a_short_title_is_skipped_not_matched():
    res = zi.find_work(zi.libraries(), title="On Growth", first_author="Solow")
    assert res["verdict"] == "unchecked"
    assert any("too short" in s for s in res["skipped"])


def test_the_helper_no_longer_reads_the_whole_library_per_lookup():
    text = (Path(zi.__file__)).read_text()
    for gone in ("def read_library", "def library_matches", "def _library_views",
                 "def _surname_in_text", "def entry_identity_keys",
                 "def attachment_digest", "def entry_to_ris"):
        assert gone not in text, gone


# ── live: a client of its own, seeded once ───────────────────────────────────


@pytest.fixture(scope="module")
def library(zotero_factory, tmp_path_factory):
    zotero = zotero_factory("findwork")
    files = tmp_path_factory.mktemp("findwork-files")
    stored = make_pdf(files / "original-publisher-name.pdf",
                      ["Totally Different Recorded Title", "by Renamer"])
    shared = make_pdf(files / "shared.pdf", ["Working paper", "by Tiebreak"])
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
    return zotero, keys, {"stored": stored, "shared": shared}


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
        assert m["certainty"] == "exact" and res["verdict"] == "match"
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
def test_no_hit_is_none_not_unchecked(lib):
    res = find(doi="10.5555/nowhere")
    assert res["matches"] == [] and res["verdict"] == "none"
    assert res["consulted"] == ["doi"]
    for label in ("isbn", "arxiv", "handle"):
        assert any(s.startswith(label) for s in res["skipped"]), label


@pytest.mark.integration
def test_an_isbn_matches_across_hyphenation_and_length(lib):
    keys, _ = lib
    assert [m["key"] for m in find(isbn="9780134685991")["matches"]] == [keys["isbn"]]
    assert [m["key"] for m in find(isbn="0-13-468599-7")["matches"]] == [keys["isbn"]]
    assert zi.isbnlib.to_isbn10("9780134685991") == "0134685997"
    (m,) = find(isbn="978-0-306-40615-7")["matches"]
    assert m["key"] == keys["isbn10"] and m["why"] == ["isbn"]


@pytest.mark.integration
def test_arxiv_ids_and_handles_are_found_in_extra_and_url(lib):
    keys, _ = lib
    assert [m["key"] for m in find(arxiv="2401.01234")["matches"]] == [keys["arxiv_extra"]]
    assert [m["key"] for m in find(arxiv="arXiv:2401.01234v2")["matches"]] == [
        keys["arxiv_extra"]]
    assert [m["key"] for m in find(arxiv="2402.05678")["matches"]] == [keys["arxiv_url"]]
    for supplied in ("10419/12345", "https://hdl.handle.net/10419/12345"):
        (m,) = find(handle=supplied)["matches"]
        assert m["key"] == keys["handle"] and m["why"] == ["handle"], supplied


@pytest.mark.integration
@pytest.mark.parametrize("author", ["Robert Nozick", "Nozick, Robert", "Nozick"])
def test_a_pre_doi_book_is_found_by_author_year_and_title(lib, author):
    keys, _ = lib
    res = find(title="anarchy state and utopia", year="1974",
               first_author=zi.first_author_surname(author))
    (m,) = res["matches"]
    assert m["key"] == keys["nozick"] and m["why"] == ["creator-year-title"]
    assert m["certainty"] == "strong" and res["verdict"] == "match"


@pytest.mark.integration
def test_a_two_word_surname_is_not_shortened_twice(lib, capsys):
    """"García Márquez, Gabriel" is the surname "García Márquez": a second
    shortening made it "Márquez", and the duplicate went unseen."""
    keys, _ = lib
    res = find(title="Cien años de soledad", year="1967",
               first_author=zi.first_author_surname("García Márquez, Gabriel"))
    assert [m["key"] for m in res["matches"]] == [keys["garcia"]]
    args = argparse.Namespace(doi=None, isbn=None, arxiv=None, handle=None,
                              title="Cien años de soledad", year="1967",
                              author="García Márquez, Gabriel", pdf=None,
                              library="user", metadata=None)
    assert zi.cmd_find_work(args) == 0
    (result,) = json.loads(capsys.readouterr().out)["results"]
    assert result["verdict"] == "match"


@pytest.mark.integration
def test_the_wrong_author_finds_nothing(lib):
    res = find(title="Coherent Measures of Risk", year="1999",
               first_author="Delbaen")
    assert res["verdict"] == "none"
    assert "creator-year-title" in res["consulted"]


@pytest.mark.integration
def test_a_work_without_a_stored_file_says_so(lib):
    """The present-but-no-file case suggest-attachments repairs; a linked
    URL is not a stored file."""
    keys, _ = lib
    (artzner,) = find(title="Coherent Measures of Risk", year="1999",
                      first_author="Artzner")["matches"]
    assert artzner["key"] == keys["artzner"] and artzner["has_file"] is False
    (kurz,) = find(title="Sraffa and von Neumann", year="2001",
                   first_author="Kurz")["matches"]
    assert kurz["key"] == keys["kurz"] and kurz["has_file"] is False


@pytest.mark.integration
def test_a_renamed_copy_is_found_by_its_content(lib, tmp_path):
    """Content identity survives renaming: the work found by its title
    holds a stored file with the probe's md5."""
    keys, files = lib
    probe = tmp_path / "MyOwnName-2024.pdf"
    shutil.copyfile(files["stored"], probe)
    res = find(title="Totally Different Recorded Title", first_author="Renamer",
               pdf_path=probe)
    (m,) = res["matches"]
    assert m["key"] == keys["hash"] and m["why"] == ["storageHash",
                                                     "creator-year-title"]
    assert m["certainty"] == "exact" and m["has_pdf"] is True
    assert m["attachment"]["md5"] == hashlib.md5(probe.read_bytes()).hexdigest()
    assert "storageHash" in res["consulted"]


@pytest.mark.integration
def test_one_file_under_two_records_names_both(lib, tmp_path):
    """Ticket 0570: two records legitimately sharing one file tie at the
    exact tier; neither vanishes."""
    keys, files = lib
    probe = tmp_path / "local.pdf"
    shutil.copyfile(files["shared"], probe)
    res = find(doi="10.5555/tie", pdf_path=probe)
    assert res["verdict"] == "ambiguous"
    assert {m["key"] for m in res["matches"]} == {keys["tie_wp"], keys["tie_journal"]}
    assert all(m["why"][0] == "storageHash" for m in res["matches"])


@pytest.mark.integration
def test_more_document_text_never_manufactures_a_match(lib):
    """Text widens what the document may say; the score is the library
    title's, so an unrelated work of the same author stays out."""
    keys, _ = lib
    res = find(year="1969", authors=["Afriat"],
               text="MethodOfLimits Index Numbers method of limits in the "
                    "theory of index numbers")
    assert [m["key"] for m in res["matches"]] == [keys["afriat"]]


@pytest.mark.integration
def test_front_matter_is_enough_when_the_pdfinfo_title_is_junk(lib):
    keys, _ = lib
    res = find(title="PII: 0014-2921(69)90001-4", year="1969",
               authors=["Bessiere"],
               text="Methods of choosing equipment at Electricite de France")
    assert res["verdict"] == "match"
    assert res["matches"][0]["key"] == keys["bessiere"]


@pytest.mark.integration
def test_a_scattered_vocabulary_is_ambiguous_and_a_title_line_matches(lib):
    keys, _ = lib
    weak = find(year="1960", authors=["Hoffman"], text=SCATTERED)
    assert weak["matches"][0]["key"] == keys["hoffman"]
    assert weak["matches"][0]["certainty"] == "weak"
    assert weak["verdict"] == "ambiguous"
    strong = find(year="1957", authors=["Hoffman"], text=HOFFMAN)
    assert strong["matches"][0]["certainty"] == "strong"
    assert strong["verdict"] == "match"


# ── live: check-staging rows ─────────────────────────────────────────────────


def row(path, bib_entry=None):
    return zi.audit_one(path, zi.libraries(), bib_entry=bib_entry)


@pytest.mark.integration
def test_check_staging_verdicts_cover_every_certainty(lib, tmp_path):
    keys, files = lib
    identical = tmp_path / "Renamer2024-copy.pdf"
    shutil.copyfile(files["stored"], identical)
    assert row(identical)["verdict"] == "identical"
    assert "also_matches" not in row(identical)

    scanned = make_pdf(tmp_path / "Artzner1999-x.pdf", [],
                       {"Title": "Coherent Measures of Risk"})
    present = row(scanned)
    assert present["verdict"] == "work_present_no_file"
    assert present["zotero_key"] == keys["artzner"]

    weak = make_pdf(tmp_path / "Hoffman1960-x.pdf", BODY.splitlines())
    assert row(weak)["verdict"] == "ambiguous"

    absent = make_pdf(tmp_path / "Nobody1999-x.pdf",
                      ["An Unrelated Document About Turbines"])
    nothing = row(absent)
    assert nothing["verdict"] == "absent"
    assert nothing["consulted"], "absent must mean 'looked and found nothing'"

    thin = make_pdf(tmp_path / "scan0001.pdf", ["page 1"])
    unknown = row(thin)
    assert unknown["verdict"] == "unidentified", "could not look is not absent"
    assert unknown["consulted"] == []


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
@pytest.mark.parametrize("author", ["Artzner, Philippe and Delbaen, Freddy",
                                    "Philippe Artzner and Freddy Delbaen"])
def test_check_staging_normalizes_the_bib_first_author(lib, tmp_path, author):
    keys, _ = lib
    pdf = make_pdf(tmp_path / "paper.pdf", ["nothing useful"])
    result = row(pdf, {"author": author, "title": "Coherent Measures of Risk",
                       "year": "1999"})
    assert result["zotero_key"] == keys["artzner"]
    assert result["why"] == ["creator-year-title"]


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
    make_pdf(docs / "Hoffman1957-systems.pdf", [HOFFMAN, "by A. J. Hoffman"])
    make_pdf(docs / "Nobody1999-x.pdf", ["An Unrelated Document About Turbines"])
    args = argparse.Namespace(root=str(tmp_path), dir="docs", out=None,
                              apply=False, edit=False, library="user")
    assert zi.cmd_check_staging(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["summary"] == {"work_present_no_file": 1, "absent": 1}
    find_args = argparse.Namespace(doi="10.5555/Deep.X", isbn=None, arxiv=None,
                                   handle=None, title=HOFFMAN, year="1957",
                                   author="Hoffman", pdf=None, library="user",
                                   metadata=None)
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
    make_pdf(docs / "Hoffman1957-systems.pdf", [HOFFMAN, "by A. J. Hoffman"])
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
                                   handle=None, title=None, year=None,
                                   author=None, pdf=None, library="user",
                                   metadata=None)
    assert zi.cmd_find_work(find_args) == zi.EXIT_SLOW
    out = json.loads(capsys.readouterr().out)
    assert out["zotero"] == "slow" and out["verdict"] == "unchecked"
    assert zi.EXIT_SLOW not in (0, zi.EXIT_UNAVAILABLE)

"""suggest-attachments compares a file with its parent before attaching
(ticket 1510).

Live tests use a real throwaway Zotero (tests/zotero_live.py): they are
`integration` and skip where the client cannot run ("no display" under a
plain `make check`). Run them by hand with
`DISPLAY=:0 uv run --frozen python3 -m pytest tests/test_zotero_attach_licence.py
-m integration -v -rs`: a SKIPPED line means the run proved nothing. The
truth table of the decision function is fast.
"""

import argparse
import json

import pytest

import zotero_live
from test_zotero_import import make_pdf
from zotero_live import closed_port

zotero_factory = zotero_live.zotero_factory
zi = zotero_live.helper_module()

DOI_A = "10.5555/Licence.First"
DOI_B = "10.5555/Licence.Second"


# --- the decision, on literal identifiers (fast) -----------------------------

def work(**fields):
    base = {"key": "PARENT01", "itemType": "journalArticle", "creators": [],
            "library": "user", **{f: "" for f in zi.WORK_FIELDS}}
    return {**base, **fields}


def test_a_second_doi_recorded_in_extra_agrees():
    parent = work(DOI=DOI_A, extra=f"DOI: {DOI_B}")
    got = zi.attach_licence(parent, {"doi": DOI_B}, [], [], None)
    assert got["licence"] == "agreed" and got["on"] == ["doi"]


def test_a_differing_given_doi_refuses_naming_both_and_the_way_out():
    got = zi.attach_licence(work(DOI=DOI_A), {"doi": DOI_B}, [], [], None)
    assert got["licence"] == "refused"
    assert DOI_A in got["error"] and DOI_B in got["error"]
    assert f"DOI: {DOI_B}" in got["error"]


def test_a_volume_isbn_on_a_chapter_is_nothing_to_compare():
    parent = work(itemType="bookSection", ISBN="9780674009691")
    got = zi.attach_licence(parent, {"isbn": "9780262510875"}, [], [], None)
    assert got["licence"] == "unverified"


def test_an_identifier_the_parent_lacks_is_nothing_to_compare():
    got = zi.attach_licence(work(), {"doi": DOI_B}, [], [], None)
    assert got["licence"] == "unverified"


def test_a_hint_never_agrees_but_may_refuse():
    parent = work(DOI=DOI_A)
    same = zi.attach_licence(parent, {}, [("doi", DOI_A, "hint")], [], None)
    other = zi.attach_licence(parent, {}, [("doi", DOI_B, "hint")], [], None)
    assert same["licence"] == "unverified"
    assert other["licence"] == "refused" and DOI_B in other["error"]


def test_a_scraped_mismatch_refuses_saying_it_may_be_a_cited_work():
    got = zi.attach_licence(work(DOI=DOI_A), {},
                            [("doi", DOI_B, "from text")], [], None)
    assert got["licence"] == "refused" and "cited" in got["error"]


def test_another_holder_of_the_file_refuses_naming_it():
    got = zi.attach_licence(work(DOI=DOI_A), {"doi": DOI_A}, [],
                            [{"key": "OTHER001", "title": "Other"}], None)
    assert got["licence"] == "refused" and "OTHER001" in got["error"]


def test_a_copy_already_under_the_parent_is_not_stored_twice():
    got = zi.attach_licence(work(), {}, [], [], "ATTACH01")
    assert got["licence"] == "already stored" and "ATTACH01" in got["note"]


@pytest.mark.parametrize(("why", "licensed"), [
    (["doi"], True), (["isbn", "title"], True), (["doi (hint)"], False),
    (["doi (from text)"], False), (["url"], False), ([], False), (None, False)])
def test_one_statement_of_the_keys_that_license_a_write(why, licensed):
    assert zi.licenses_attach(why) is licensed


# --- live: suggest-attachments against a throwaway Zotero --------------------

@pytest.fixture(autouse=True)
def zotero_down(monkeypatch, tmp_path):
    with closed_port() as port:
        monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")
        monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(tmp_path / "no-key.env"))
        yield


@pytest.fixture(scope="module")
def zotero(zotero_factory):
    return zotero_factory("licence")


@pytest.fixture
def live(zotero, monkeypatch):
    return zotero_live.point_helper_at(zotero, monkeypatch)


def project(tmp_path):
    """A project root of its own, so the .bib discovery never climbs into
    the repository the tests run from."""
    root = tmp_path / "proj"
    (root / ".git").mkdir(parents=True)
    (root / "docs").mkdir()
    return root


def stage(folder, name, lines, receipt=None, by_name=False):
    """A PDF and, when given, the receipt a fetcher left for it; `by_name`
    records another md5, so the receipt is found by the file's name only."""
    path = make_pdf(folder / name, lines)
    if receipt is not None:
        record = {"status": "success", "path": str(path),
                  "md5": "0" * 32 if by_name else zi.file_md5(path),
                  "identifiers_scraped": [], "error": None, **receipt}
        with (folder / ".receipts.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")
    return path


def suggest(parent, path, capsys, edit=True):
    rc = zi.cmd_suggest_attachments(argparse.Namespace(
        parent=parent, file=[str(path)], library="user", edit=edit))
    out = json.loads(capsys.readouterr().out)
    return rc, out["attached" if edit else "suggested"][0]


@pytest.mark.integration
def test_a_receipt_doi_the_parent_does_not_carry_is_refused(
        live, tmp_path, capsys):
    root = project(tmp_path)
    parent = live.save(zotero_live.unique("Refused Doi"), DOI=DOI_A)
    path = stage(root / "docs", "refused.pdf", ["refused a1"],
                 {"identifiers": {"doi": DOI_B}})
    before = live.versions()
    rc, row = suggest(parent, path, capsys)
    assert rc == 1 and row["status"] == "refused"
    assert DOI_A in row["error"] and DOI_B in row["error"]
    assert live.children(parent) == [] and live.versions() == before


@pytest.mark.integration
def test_the_same_file_attaches_once_the_parent_records_the_second_doi(
        live, tmp_path, capsys):
    root = project(tmp_path)
    parent = live.save(zotero_live.unique("Second Doi"), DOI=DOI_A,
                       extra=f"DOI: {DOI_B}")
    path = stage(root / "docs", "second.pdf", ["second a2"],
                 {"identifiers": {"doi": DOI_B}})
    rc, row = suggest(parent, path, capsys)
    assert rc == 0 and row["status"] == "attached"
    assert row["licence"] == "agreed" and row["on"] == ["doi"]
    assert len(live.children(parent)) == 1


@pytest.mark.integration
def test_a_file_stored_under_another_item_is_refused_naming_it(
        live, tmp_path, capsys):
    root = project(tmp_path)
    path = make_pdf(root / "docs" / "held.pdf", ["held elsewhere a3"])
    holder = live.save(zotero_live.unique("Holder"), pdf=path)
    parent = live.save(zotero_live.unique("Wrong Parent"))
    before = live.versions()
    rc, row = suggest(parent, path, capsys, edit=False)
    assert rc == 1 and row["licence"] == "refused" and holder in row["error"]
    assert live.versions() == before
    rc, row = suggest(parent, path, capsys)
    assert rc == 1 and row["status"] == "refused" and holder in row["error"]
    assert live.children(parent) == [] and live.versions() == before
    other = make_pdf(root / "docs" / "other.pdf", ["different bytes a3"])
    rc, row = suggest(parent, other, capsys)
    assert rc == 0 and row["status"] == "attached"
    assert len(live.children(parent)) == 1


@pytest.mark.integration
def test_a_file_already_under_the_parent_is_not_stored_twice(
        live, tmp_path, capsys):
    root = project(tmp_path)
    path = make_pdf(root / "docs" / "twice.pdf", ["stored twice a4"])
    parent = live.save(zotero_live.unique("Already Holds"), pdf=path)
    before = live.versions()
    rc, row = suggest(parent, path, capsys)
    assert rc == 0 and row["status"] == "already stored"
    assert len(live.children(parent)) == 1 and live.versions() == before


@pytest.mark.integration
def test_an_agreeing_receipt_doi_attaches_naming_the_key(
        live, tmp_path, capsys):
    root = project(tmp_path)
    parent = live.save(zotero_live.unique("Agreeing Doi"), DOI=DOI_A)
    path = stage(root / "docs", "agrees.pdf", ["agrees a5"],
                 {"identifiers": {"doi": DOI_A}})
    rc, row = suggest(parent, path, capsys)
    assert rc == 0 and row["status"] == "attached"
    assert row["licence"] == "agreed" and row["on"] == ["doi"]


@pytest.mark.integration
def test_a_receipt_found_by_name_only_never_agrees_but_refuses(
        live, tmp_path, capsys):
    root = project(tmp_path)
    parent = live.save(zotero_live.unique("Name Only"), DOI=DOI_A)
    same = stage(root / "docs", "same.pdf", ["name only same a6"],
                 {"identifiers": {"doi": DOI_A}}, by_name=True)
    rc, row = suggest(parent, same, capsys, edit=False)
    assert rc == 0 and row["licence"] == "unverified"
    other = stage(root / "docs", "other.pdf", ["name only other a6"],
                  {"identifiers": {"doi": DOI_B}}, by_name=True)
    before = live.versions()
    rc, row = suggest(parent, other, capsys)
    assert rc == 1 and row["status"] == "refused" and DOI_B in row["error"]
    assert live.children(parent) == [] and live.versions() == before


@pytest.mark.integration
def test_the_bib_entry_is_found_from_the_file_not_the_cwd(
        live, tmp_path, capsys, monkeypatch):
    root = project(tmp_path)
    path = make_pdf(root / "docs" / "bibbed.pdf", ["bibbed a7"])
    (root / "refs.bib").write_text(
        "@article{Bibbed2001, title={Bibbed}, doi={%s}, "
        "file={docs/bibbed.pdf}}\n" % DOI_B)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    parent = live.save(zotero_live.unique("Bib Parent"), DOI=DOI_A)
    before = live.versions()
    rc, row = suggest(parent, path, capsys)
    assert rc == 1 and row["status"] == "refused"
    assert DOI_A in row["error"] and DOI_B in row["error"]
    assert live.versions() == before


@pytest.mark.integration
def test_a_file_with_nothing_to_compare_attaches_unverified(
        live, tmp_path, capsys):
    root = project(tmp_path)
    parent = live.save(zotero_live.unique("Nothing To Compare"))
    path = make_pdf(root / "docs" / "plain.pdf", ["nothing citable a8"])
    rc, row = suggest(parent, path, capsys)
    assert rc == 0 and row["status"] == "attached"
    assert row["licence"] == "unverified"
    assert len(live.children(parent)) == 1


@pytest.mark.integration
def test_a_skipped_index_attaches_and_says_the_md5_was_not_compared(
        live, tmp_path, capsys, monkeypatch):
    root = project(tmp_path)
    parent = live.save(zotero_live.unique("Skipped Index"))
    path = make_pdf(root / "docs" / "skipped.pdf", ["skipped index a9"])
    monkeypatch.setattr(zi, "hash_index", lambda libs: {
        "status": "skipped", "slow": True, "reason": "too slow",
        "by_md5": {}})
    rc, row = suggest(parent, path, capsys)
    assert rc == 1 and row["status"] == "attached"
    assert any("md5" in s and "too slow" in s for s in row["skipped"])
    assert len(live.children(parent)) == 1

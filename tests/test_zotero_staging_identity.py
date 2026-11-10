"""check-staging identifies a staged file by what it is (ticket 1502).

Order: the file's md5 against an index of the library's attachment md5s
(Zotero's own hash, listed once per run); then identifiers, from the .bib
entry (url and eprint included) or else from the file's own text; the title
last. A text-scraped identifier never yields `absent` and never authorises
an attach. A skipped index is reported, the run completes on the other keys,
and no file reads `absent`.

The lookups run against a real throwaway Zotero (tests/zotero_live.py); no
mock. Tests needing it are `integration` and skip where it cannot run.
"""

import argparse
import json
import shutil

import pytest

import zotero_live
from test_zotero_import import make_pdf
from zotero_live import closed_port

zotero_factory = zotero_live.zotero_factory
zi = zotero_live.helper_module()


@pytest.fixture(autouse=True)
def zotero_down(monkeypatch, tmp_path):
    with closed_port() as port:
        monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")
        monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(tmp_path / "no-key.env"))
        yield


# ── pure: identifiers a .bib entry's url and eprint carry ────────────────────


@pytest.mark.parametrize("entry,key,value", [
    ({"url": "https://arxiv.org/abs/2401.07777v2"}, "arxiv", "2401.07777"),
    ({"url": "https://hdl.handle.net/10419/77777"}, "handle", "10419/77777"),
    ({"url": "https://doi.org/10.5555/Url.Doi"}, "doi", "10.5555/url.doi"),
    ({"url": "https://dx.doi.org/10.5555/Url.Doi"}, "doi", "10.5555/url.doi"),
    ({"eprint": "2402.08888", "eprinttype": "arxiv"}, "arxiv", "2402.08888"),
    ({"eprint": "2402.08888", "archiveprefix": "arXiv"}, "arxiv", "2402.08888"),
    ({"eprint": "2402.08888"}, "arxiv", "2402.08888"),
    ({"eprint": "10419/66666", "eprinttype": "hdl"}, "handle", "10419/66666"),
])
def test_a_bib_url_or_eprint_yields_an_identifier(entry, key, value):
    ids = zi.bib_identifiers(entry)
    assert (zi.normal_arxiv(ids[key]) if key == "arxiv" else
            zi.normal_doi(ids[key]) if key == "doi" else
            zi.handle_path(ids[key])) == value


@pytest.mark.parametrize("entry", [
    {"url": "https://example.org/paper/10.5555/x.pdf"},
    {"url": "https://example.org/report.pdf"},
    {"eprint": "12345678", "eprinttype": "pubmed"},
    {},
])
def test_a_url_or_eprint_without_an_identifier_yields_none(entry):
    assert not any(zi.bib_identifiers(entry).values())


def test_a_given_identifier_wins_over_the_derived_one():
    ids = zi.bib_identifiers({"doi": "10.5555/given",
                              "url": "https://doi.org/10.5555/derived"})
    assert ids["doi"] == "10.5555/given"


# ── live: a client of its own, seeded once ───────────────────────────────────

TEXT_DOI = "10.5555/Text.Found"


@pytest.fixture(scope="module")
def library(zotero_factory, tmp_path_factory):
    zotero = zotero_factory("identity")
    files = tmp_path_factory.mktemp("identity-files")
    # Container Title and text match nothing in the library.
    stored = make_pdf(files / "publisher.pdf", ["Wqzx plorm vendak"],
                      {"Title": "Xqzv Plimtor Wexdrab Quolnest"})
    shared = make_pdf(files / "shared.pdf", ["Shared bytes yorvex"])
    loose = make_pdf(files / "loose.pdf", ["Standalone bytes kelvasp"])
    binned = make_pdf(files / "binned.pdf", ["Binned bytes trunquel"])
    shared_copy = files / "shared-copy.pdf"
    shared_copy.write_bytes(shared.read_bytes())
    keys = {
        "renamed": zotero.save("Wholly Unrelated Stored Record Name",
                               pdf=stored),
        "shared_a": zotero.save("Shared File First Record", pdf=shared),
        "shared_b": zotero.save("Shared File Second Record", pdf=shared_copy),
        "binned": zotero.save("A Record Sent To The Trash", pdf=binned),
        "text_doi": zotero.save("Found By Its Printed DOI", DOI=TEXT_DOI),
        "arxiv": zotero.save("A Preprint By Url", extra="arXiv:2401.07777"),
        "eprint": zotero.save("A Preprint By Eprint", extra="arXiv:2402.08888"),
        "handle": zotero.save("A Handle By Url", item_type="report",
                              url="https://hdl.handle.net/10419/77777"),
        "url_doi": zotero.save("A DOI By Url", DOI="10.5555/Url.Doi"),
    }
    z = zotero.client()
    result = z.upload_attachments([{
        "itemType": "attachment", "linkMode": "imported_file",
        "title": loose.name, "filename": str(loose.resolve()),
        "contentType": "application/pdf", "tags": [], "relations": {}}])
    assert result["success"], result
    keys["loose"] = result["success"][0]["key"]
    item = z.item(keys["binned"])
    item["data"]["deleted"] = 1
    assert z.update_item(item)
    return zotero, keys, {"stored": stored, "shared": shared, "loose": loose,
                          "binned": binned}


@pytest.fixture
def lib(library, monkeypatch):
    zotero, keys, files = library
    zotero_live.point_helper_at(zotero, monkeypatch)
    return keys, files


def row(path, bib_entry=None):
    libs = zi.libraries()
    return zi.audit_one(path, libs, bib_entry=bib_entry,
                        hash_index=zi.hash_index(libs))


def check(root, **over):
    args = dict(root=str(root), dir=None, out=None, apply=False, edit=False,
                library="user")
    args.update(over)
    return zi.cmd_check_staging(argparse.Namespace(**args))


@pytest.mark.integration
def test_a_byte_identical_file_is_identical_whatever_it_is_called(lib, tmp_path):
    """Neither the filename nor the container Title finds the work: the
    md5 index does."""
    keys, files = lib
    probe = tmp_path / "scan0001.pdf"
    shutil.copyfile(files["stored"], probe)
    judged = row(probe)
    assert judged["verdict"] == "identical"
    assert judged["zotero_key"] == keys["renamed"]
    assert "storageHash" in judged["consulted"]
    assert judged["why"][0] == "storageHash"
    # Positive control: without the index the same file is not recognised.
    assert zi.audit_one(probe, zi.libraries())["verdict"] != "identical"


@pytest.mark.integration
def test_every_parent_sharing_the_md5_is_named(lib, tmp_path):
    keys, files = lib
    probe = tmp_path / "x.pdf"
    shutil.copyfile(files["shared"], probe)
    judged = row(probe)
    assert judged["verdict"] == "identical"
    named = {judged["zotero_key"]} | {m["key"] for m in judged["also_matches"]}
    assert named == {keys["shared_a"], keys["shared_b"]}


@pytest.mark.integration
def test_a_standalone_attachment_is_reported_as_such(lib, tmp_path):
    keys, files = lib
    probe = tmp_path / "y.pdf"
    shutil.copyfile(files["loose"], probe)
    judged = row(probe)
    assert judged["verdict"] == "identical"
    assert judged["zotero_key"] == keys["loose"]
    assert judged["standalone"] is True


@pytest.mark.integration
def test_a_copy_under_a_trashed_parent_is_not_identical(lib, tmp_path):
    keys, files = lib
    probe = tmp_path / "z.pdf"
    shutil.copyfile(files["binned"], probe)
    judged = row(probe)
    assert judged["verdict"] != "identical"
    assert judged["zotero_key"] != keys["binned"]
    assert "storageHash" in judged["consulted"], "the index was consulted"


@pytest.mark.integration
def test_a_doi_printed_in_the_file_is_looked_up(lib, tmp_path):
    """No .bib entry: the file's own first page gives the DOI, recorded
    as read from the text."""
    keys, _ = lib
    pdf = make_pdf(tmp_path / "scan0002.pdf",
                   ["A paper", f"doi: {TEXT_DOI}", "nonce 1502a"])
    judged = row(pdf)
    assert judged["verdict"] == "work_present_no_file"
    assert judged["zotero_key"] == keys["text_doi"]
    assert "doi (from text)" in judged["consulted"]
    assert judged["why"] == ["doi (from text)"]


@pytest.mark.integration
def test_a_text_identifier_that_finds_nothing_is_not_absent(lib, tmp_path):
    """Control: a scraped DOI may be a cited work's; finding nothing by it
    establishes nothing."""
    pdf = make_pdf(tmp_path / "scan0003.pdf",
                   ["A paper", "doi: 10.5555/nowhere.in.library", "nonce 1502b"])
    judged = row(pdf)
    assert "doi (from text)" in judged["consulted"]
    assert judged["verdict"] == "unidentified"


@pytest.mark.integration
def test_a_given_identifier_suppresses_the_text_one(lib, tmp_path):
    keys, _ = lib
    pdf = make_pdf(tmp_path / "scan0004.pdf",
                   ["A paper", f"doi: {TEXT_DOI}", "nonce 1502c"])
    judged = row(pdf, {"_type": "article", "doi": "10.5555/Url.Doi"})
    assert judged["zotero_key"] == keys["url_doi"]
    assert not any("from text" in c for c in judged["consulted"])


@pytest.mark.integration
def test_a_text_identifier_never_authorises_an_attach(lib, tmp_path):
    """--apply --edit stores a file only under a work a given key found."""
    keys, _ = lib
    docs = tmp_path / "docs"
    docs.mkdir()
    make_pdf(docs / "scan0005.pdf", ["A paper", f"doi: {TEXT_DOI}",
                                     "nonce 1502d"])
    found = zi.discover_reconcile_files(tmp_path)
    report, rc = zi.reconcile_apply(tmp_path, found, "user", {"apply": True},
                                    argparse.Namespace(library="user",
                                                       edit=True))
    (edit,) = report["edits"]
    assert edit["status"] == "not attempted"
    assert report["rows"][0]["why"] == ["doi (from text)"]
    assert zi.local_library().children(keys["text_doi"]) == []


@pytest.mark.integration
@pytest.mark.parametrize("entry,label,key", [
    ({"url": "https://arxiv.org/abs/2401.07777v2"}, "arxiv", "arxiv"),
    ({"eprint": "2402.08888", "eprinttype": "arxiv"}, "arxiv", "eprint"),
    ({"url": "https://hdl.handle.net/10419/77777"}, "handle", "handle"),
    ({"url": "https://doi.org/10.5555/Url.Doi"}, "doi", "url_doi"),
])
def test_a_bib_url_or_eprint_finds_the_work(lib, tmp_path, entry, label, key):
    keys, _ = lib
    pdf = make_pdf(tmp_path / "paper.pdf", ["nothing useful", "nonce " + key])
    judged = row(pdf, {"_type": "article", **entry})
    assert label in judged["consulted"]
    assert judged["zotero_key"] == keys[key] and judged["why"] == [label]


@pytest.mark.integration
def test_a_slow_index_is_skipped_and_the_run_completes(lib, tmp_path,
                                                        monkeypatch, capsys):
    """The listing runs out of time (a budget of 0 s on the real client): the
    run completes on identifiers and title, says the index was skipped, no
    file reads absent, and the exit is EXIT_SLOW, not a clean 0."""
    keys, _ = lib
    docs = tmp_path / "docs"
    docs.mkdir()
    make_pdf(docs / "present.pdf", ["nothing useful", "nonce 1502e"])
    make_pdf(docs / "missing.pdf", ["nothing useful", "nonce 1502f"])
    (tmp_path / "sources.bib").write_text(
        "@article{present, title={Found By Its Printed DOI Here}, "
        f"doi={{{TEXT_DOI}}}, file={{docs/present.pdf}}}}\n"
        "@article{missing, title={Turbine Maintenance Intervals Wholly "
        "Absent}, year={2012}, file={docs/missing.pdf}}\n")
    # Positive control: with the index, the second file is absent.
    assert check(tmp_path) == 0
    report = json.loads(capsys.readouterr().out)
    verdicts = {r["file"]: r["verdict"] for r in report["rows"]}
    assert verdicts == {"present.pdf": "work_present_no_file",
                        "missing.pdf": "absent"}
    assert report["hash_index"]["status"] == "built"

    monkeypatch.setattr(zi, "INDEX_WAIT", 0.0)
    assert check(tmp_path) == zi.EXIT_SLOW
    report = json.loads(capsys.readouterr().out)
    rows = {r["file"]: r for r in report["rows"]}
    assert rows["present.pdf"]["verdict"] == "work_present_no_file"
    assert rows["present.pdf"]["zotero_key"] == keys["text_doi"]
    assert rows["missing.pdf"]["verdict"] == "unchecked"
    for r in rows.values():
        assert "storageHash" not in r["consulted"]
        assert any(s.startswith("storageHash (index skipped:")
                   for s in r["skipped"]), r["skipped"]
    assert report["hash_index"]["status"] == "skipped"
    assert report["verdict"] == "unchecked"


@pytest.mark.integration
def test_a_skipped_index_creates_and_attaches_nothing(lib, tmp_path,
                                                       monkeypatch):
    keys, _ = lib
    docs = tmp_path / "docs"
    docs.mkdir()
    make_pdf(docs / "present.pdf", ["nothing useful", "nonce 1502g"])
    (tmp_path / "sources.bib").write_text(
        "@article{present, title={Found By Its Printed DOI Here}, "
        f"author={{Doe, Jane}}, year={{2020}}, doi={{{TEXT_DOI}}}, "
        "file={docs/present.pdf}}\n")
    monkeypatch.setattr(zi, "INDEX_WAIT", 0.0)
    found = zi.discover_reconcile_files(tmp_path)
    with pytest.raises(zi.ZoteroSlow):
        zi.reconcile_apply(tmp_path, found, "user", {"apply": True},
                           argparse.Namespace(library="user", edit=True))
    assert zi.local_library().children(keys["text_doi"]) == []

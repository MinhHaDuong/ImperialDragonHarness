"""check-staging and find-work read a fetcher's receipt (ticket 1503).

Real throwaway Zotero (tests/zotero_live.py), as test_zotero_staging_identity:
tests are `integration` and skip where the client cannot run.
"""

import argparse
import json

import pytest

import zotero_live
from test_zotero_import import make_pdf
from zotero_live import closed_port

zotero_factory = zotero_live.zotero_factory
zi = zotero_live.helper_module()

URL = "https://example.org/Reports/WP-54"
RECEIPT_DOI = "10.5555/Receipt.Doi"


@pytest.fixture(autouse=True)
def zotero_down(monkeypatch, tmp_path):
    with closed_port() as port:
        monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")
        monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(tmp_path / "no-key.env"))
        yield


@pytest.fixture(scope="module")
def library(zotero_factory):
    zotero = zotero_factory("receipt")
    keys = {
        # No DOI, no file: only its url field can name it.
        "wp": zotero.save("Zxqv Working Paper Fifty Four", item_type="report",
                          url=URL),
        "doi": zotero.save("Qwlx Receipt Given Record", DOI=RECEIPT_DOI),
        "isbn": zotero.save("Plmk Whole Volume Record", item_type="book",
                            ISBN="9780674009691"),
    }
    return zotero, keys


@pytest.fixture
def lib(library, monkeypatch):
    zotero, keys = library
    zotero_live.point_helper_at(zotero, monkeypatch)
    return keys


def stage(folder, name, lines, receipt=None):
    """A staged PDF and, when given, the receipt a fetcher left for it."""
    path = make_pdf(folder / name, lines)
    if receipt is not None:
        record = {"status": "success", "path": str(path),
                  "md5": zi.file_md5(path), "identifiers_scraped": [],
                  "error": None, **receipt}
        with (folder / ".receipts.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")
    return path


def verdict(path):
    libs = zi.libraries()
    return zi.audit_one(path, libs, md5_index=zi.hash_index(libs))


@pytest.mark.integration
def test_a_url_only_file_is_recognised_by_its_receipt_after_a_rename(
        lib, tmp_path):
    """No DOI anywhere: the URL the fetcher recorded finds the item."""
    path = stage(tmp_path, "wp54.pdf", ["nothing citable here", "nonce a1"],
                 {"identifiers": {}, "url": "HTTPS://EXAMPLE.ORG/Reports/WP-54/#top"})
    renamed = path.rename(tmp_path / "scan0001.pdf")
    judged = verdict(renamed)
    assert judged["verdict"] == "work_present_no_file"
    assert judged["zotero_key"] == lib["wp"]
    assert judged["why"] == ["url"] and "url" in judged["consulted"]


@pytest.mark.integration
def test_the_same_file_without_a_receipt_is_not_recognised(lib, tmp_path):
    """Control: no receipt, nothing names the item."""
    path = stage(tmp_path, "scan0002.pdf", ["nothing citable here", "nonce a2"])
    judged = verdict(path)
    assert judged["zotero_key"] is None
    assert judged["verdict"] in ("unidentified", "absent")
    assert "url" not in judged["consulted"]


@pytest.mark.integration
def test_a_given_receipt_identifier_finds_the_work_and_may_say_absent(
        lib, tmp_path):
    hit = stage(tmp_path, "a.pdf", ["x", "nonce a3"],
                {"identifiers": {"doi": RECEIPT_DOI}})
    assert verdict(hit)["zotero_key"] == lib["doi"]
    miss = stage(tmp_path, "b.pdf", ["x", "nonce a4"],
                 {"identifiers": {"doi": "10.5555/not.there"}})
    judged = verdict(miss)
    assert "doi" in judged["consulted"] and judged["verdict"] == "absent"


@pytest.mark.integration
def test_a_url_miss_never_says_absent(lib, tmp_path):
    """A URL is positive-only: a hit matches, a miss is `unidentified`.
    Item url fields vary (landing page, PDF link, resolver), so a miss would
    mint a duplicate under --apply."""
    miss = stage(tmp_path, "e.pdf", ["x", "nonce a7"],
                 {"identifiers": {}, "url": "https://example.org/not/there"})
    judged = verdict(miss)
    assert "url" in judged["consulted"]
    assert judged["zotero_key"] is None
    assert judged["verdict"] == "unidentified"


@pytest.mark.integration
def test_a_scraped_receipt_identifier_is_not_a_given_key(lib, tmp_path):
    """Marked scraped, it keeps 1502's rule: labelled, and alone never
    `absent`."""
    found = stage(tmp_path, "c.pdf", ["x", "nonce a5"],
                  {"identifiers": {"doi": RECEIPT_DOI},
                   "identifiers_scraped": ["doi"]})
    judged = verdict(found)
    assert judged["zotero_key"] == lib["doi"]
    assert judged["why"] == ["doi (from text)"]
    miss = stage(tmp_path, "d.pdf", ["x", "nonce a6"],
                 {"identifiers": {"doi": "10.5555/not.there"},
                  "identifiers_scraped": ["doi"]})
    assert verdict(miss)["verdict"] == "unidentified"


@pytest.mark.integration
def test_a_bib_entry_identifier_wins_over_the_receipts(lib, tmp_path):
    path = stage(tmp_path, "e.pdf", ["x", "nonce a7"],
                 {"identifiers": {"doi": "10.5555/not.there"}})
    libs = zi.libraries()
    judged = zi.audit_one(path, libs, md5_index=zi.hash_index(libs),
                          bib_entry={"_type": "article", "doi": RECEIPT_DOI})
    assert judged["zotero_key"] == lib["doi"]


@pytest.mark.integration
def test_a_fetched_isbn_finds_its_volume_with_no_bib_entry(lib, tmp_path):
    path = stage(tmp_path, "f.pdf", ["x", "nonce a8"],
                 {"identifiers": {"isbn": "9780674009691"}})
    judged = verdict(path)
    assert judged["zotero_key"] == lib["isbn"] and judged["why"] == ["isbn"]


@pytest.mark.integration
def test_a_receipt_never_authorises_an_attach_on_a_scraped_key_alone(
        lib, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    stage(docs, "g.pdf", ["x", "nonce a9"],
          {"identifiers": {"doi": RECEIPT_DOI}, "identifiers_scraped": ["doi"]})
    found = zi.discover_reconcile_files(tmp_path)
    report, _ = zi.reconcile_apply(
        tmp_path, found, "user", {"apply": True},
        argparse.Namespace(library="user", edit=True))
    (edit,) = report["edits"]
    assert edit["status"] == "not attempted"
    assert zi.local_library().children(lib["doi"]) == []


def apply_edit(tmp_path, name, lines, receipt, *, rewrite=None):
    """Stage one file under docs/ with its receipt and run
    `check-staging --apply --edit`; the edits the run made or refused."""
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    path = stage(docs, name, lines, receipt)
    if rewrite:
        path.write_bytes(rewrite)
    found = zi.discover_reconcile_files(tmp_path)
    report, _ = zi.reconcile_apply(
        tmp_path, found, "user", {"apply": True},
        argparse.Namespace(library="user", edit=True))
    return report["edits"]


@pytest.mark.integration
def test_a_stale_receipt_found_by_name_never_licenses_a_write(lib, tmp_path):
    """The file was replaced by an unrelated one under the same name: the old
    receipt's DOI may be looked up but is no grounds to attach the new bytes
    to the old work."""
    edits = apply_edit(tmp_path, "stale.pdf", ["x", "nonce c1"],
                       {"identifiers": {"doi": RECEIPT_DOI}},
                       rewrite=b"%PDF-1.4 an unrelated document")
    (edit,) = edits
    assert edit["status"] == "not attempted"
    assert zi.local_library().children(lib["doi"]) == []
    path = tmp_path / "docs" / "stale.pdf"
    judged = verdict(path)
    assert judged["zotero_key"] == lib["doi"]
    assert not any(w in zi.GIVEN_KEYS for w in judged["why"])


@pytest.mark.integration
def test_a_name_only_receipt_identifier_never_says_absent(lib, tmp_path):
    path = stage(tmp_path, "n.pdf", ["x", "nonce c2"],
                 {"identifiers": {"doi": "10.5555/not.there"}})
    path.write_bytes(b"%PDF-1.4 edited after the fetch")
    assert verdict(path)["verdict"] != "absent"


@pytest.mark.integration
def test_a_url_match_alone_never_licenses_an_attach(lib, tmp_path):
    """Reported (the URL finds the work), not written: a page URL is a weaker
    identity than a DOI, an ISBN or an md5."""
    (edit,) = apply_edit(tmp_path, "u.pdf", ["x", "nonce c3"],
                         {"identifiers": {}, "url": URL})
    assert edit["itemKey"] == lib["wp"]
    assert edit["status"] == "not attempted"
    assert zi.local_library().children(lib["wp"]) == []


@pytest.mark.integration
def test_a_bib_doi_that_misses_leaves_the_receipt_isbn_a_hint(lib, tmp_path):
    """Any .bib identifier outranks every receipt identifier: the receipt's
    ISBN hit is reported but is not the attach target."""
    path = stage(tmp_path, "i.pdf", ["x", "nonce c4"],
                 {"identifiers": {"isbn": "9780674009691"}})
    libs = zi.libraries()
    judged = zi.audit_one(path, libs, md5_index=zi.hash_index(libs),
                          bib_entry={"_type": "article",
                                     "doi": "10.5555/not.there"})
    assert judged["zotero_key"] == lib["isbn"]
    assert not any(w in zi.GIVEN_KEYS for w in judged["why"])
    assert judged["verdict"] != "absent"


@pytest.mark.integration
def test_find_work_metadata_takes_the_receipt_the_fetcher_printed(
        lib, tmp_path, capsys):
    """The receipt line, saved as it was printed, finds the item by URL."""
    path = stage(tmp_path, "h.pdf", ["x", "nonce b1"],
                 {"identifiers": {}, "url": URL, "final_url": None,
                  "title": "Zxqv Working Paper"})
    line = (tmp_path / ".receipts.jsonl").read_text()
    meta = tmp_path / "printed.json"
    meta.write_text(line)
    args = argparse.Namespace(metadata=str(meta), title=None, doi=None,
                              isbn=None, arxiv=None, handle=None, pdf=None,
                              type=None, url=None, library="user")
    assert zi.cmd_find_work(args) == 0
    (result,) = json.loads(capsys.readouterr().out)["results"]
    assert result["verdict"] != "unchecked"
    assert [m["key"] for m in result["matches"]] == [lib["wp"]]
    assert "url" in result["consulted"]
    assert path.exists()

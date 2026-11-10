"""A fetcher leaves a receipt that recognition reads (ticket 1503).

Both fetchers (scripts/fulltext_cascade.py, skills/zotero/scripts/probe-url.py)
print one JSON record and append that same line to `.receipts.jsonl` beside
the file. Here the fetch is stubbed and the real code path runs; the lookups
against a Zotero are in test_zotero_receipt.py.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

import zotero_live

zi = zotero_live.helper_module()
REPO = Path(__file__).resolve().parent.parent

CORE = {"status", "source", "path", "error", "md5", "identifiers",
        "identifiers_scraped", "url", "final_url", "title",
        "retrieved_at", "content_type", "size_bytes", "http_status"}
ID_KEYS = {"doi", "isbn", "arxiv", "handle"}


def load_probe():
    spec = importlib.util.spec_from_file_location(
        "probe_url", REPO / "skills" / "zotero" / "scripts" / "probe-url.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def receipts(folder):
    text = (folder / ".receipts.jsonl").read_text()
    return [json.loads(line) for line in text.splitlines()]


def cascade_fetch(tmp_path, monkeypatch, capsys, *, doi="10.1234/example",
                  existing=None, write=True):
    """Run the cascade CLI with the sources stubbed; (exit code, printed line)."""
    import doifetch.api
    import doifetch.naming
    from doifetch.sources.contract import Result

    from scripts.fulltext_cascade import main

    if existing:
        (tmp_path / "Example.pdf").write_bytes(existing)
    monkeypatch.setattr(sys, "argv", [
        "fulltext_cascade.py", "--phase", "open", "--doi", doi,
        "--title", "Example", "--output-dir", str(tmp_path)])
    monkeypatch.setattr(doifetch.naming, "resolve_name", lambda *a: "Example")

    def cascade(req, names):
        if write:
            Path(req.path).write_bytes(b"%PDF fetched bytes")
        return Result("success", "hal", path=req.path)

    monkeypatch.setattr(doifetch.api, "cascade", cascade)
    rc = main()
    return rc, json.loads(capsys.readouterr().out)


def probe_fetch(tmp_path, monkeypatch, url, body, ctype="application/pdf",
                final=None):
    probe = load_probe()
    monkeypatch.setattr(probe, "fetch",
                        lambda u, t: (body, final or u, ctype, 200))
    return probe.probe_one(url, tmp_path, 5)


def test_both_fetchers_print_the_same_receipt_keys(tmp_path, monkeypatch, capsys):
    one, two = tmp_path / "a", tmp_path / "b"
    one.mkdir(), two.mkdir()
    _, printed = cascade_fetch(one, monkeypatch, capsys)
    probed = probe_fetch(two, monkeypatch, "https://example.org/wp/54.pdf",
                         b"%PDF-1.4 stub")
    assert set(printed) == CORE
    assert CORE <= set(probed)
    assert printed["size_bytes"] == len(b"%PDF fetched bytes")
    assert probed["size_bytes"] == len(b"%PDF-1.4 stub")
    assert probed["http_status"] == 200 and printed["http_status"] is None
    assert probed["content_type"] == "application/pdf"
    for record in (printed, probed):
        assert record["retrieved_at"].endswith("Z")
    for record in (printed, probed):
        assert set(record["identifiers"]) == ID_KEYS
        assert record["status"] == "success"


def test_the_receipt_line_is_the_printed_record_beside_the_file(
        tmp_path, monkeypatch, capsys):
    _, printed = cascade_fetch(tmp_path, monkeypatch, capsys)
    assert receipts(tmp_path) == [printed]
    assert printed["identifiers"]["doi"] == "10.1234/example"
    assert printed["identifiers_scraped"] == []
    assert printed["md5"] == zi.file_md5(Path(printed["path"]))
    probed = probe_fetch(tmp_path, monkeypatch, "https://example.org/r.pdf",
                         b"%PDF-1.4 other")
    assert receipts(tmp_path)[-1] == probed
    assert probed["md5"] == zi.file_md5(Path(probed["path"]))
    assert probed["url"] == "https://example.org/r.pdf"


def test_a_skipped_fetch_claims_no_identifier_and_leaves_no_receipt(
        tmp_path, monkeypatch, capsys):
    rc, printed = cascade_fetch(tmp_path, monkeypatch, capsys,
                                existing=b"found there")
    assert rc == 0 and printed["status"] == "skipped"
    assert set(printed) == CORE
    assert not any(printed["identifiers"].values())
    assert not (tmp_path / ".receipts.jsonl").exists()


def test_a_failed_fetch_leaves_no_receipt(tmp_path, monkeypatch, capsys):
    rc, printed = cascade_fetch(tmp_path, monkeypatch, capsys, write=False)
    assert printed["md5"] is None
    assert not (tmp_path / ".receipts.jsonl").exists()


def test_probe_marks_page_identifiers_as_scraped(tmp_path, monkeypatch):
    html = (b"<html><head><title>A working paper</title>"
            b"<meta name='citation_doi' content='10.5555/page.doi'></head>"
            b"<body>See also arXiv:2401.01234</body></html>")
    probed = probe_fetch(tmp_path, monkeypatch, "https://example.org/wp",
                         html, ctype="text/html")
    assert probed["identifiers"]["doi"] == "10.5555/page.doi"
    assert probed["identifiers_scraped"] == ["arxiv", "doi"]
    assert probed["title"] == "A working paper"


def test_an_md5_is_zoteros(tmp_path, monkeypatch, capsys):
    """The one hash: both fetchers equal zotero.py's file_md5."""
    _, printed = cascade_fetch(tmp_path, monkeypatch, capsys)
    probed = probe_fetch(tmp_path, monkeypatch, "https://example.org/z.pdf",
                         b"%PDF-1.4 " + b"x" * 3_000_000)
    for record in (printed, probed):
        assert record["md5"] == zi.file_md5(Path(record["path"]))


# ── recognition side: which receipt belongs to a file ────────────────────────


def stage(folder, name, body, **keys):
    path = folder / name
    path.write_bytes(body)
    record = {"status": "success", "path": str(path),
              "md5": zi.file_md5(path), "identifiers": {}, **keys}
    with (folder / ".receipts.jsonl").open("a") as stream:
        stream.write(json.dumps(record) + "\n")
    return path


def test_a_receipt_is_found_after_the_file_is_renamed(tmp_path):
    path = stage(tmp_path, "Author 2020 - Title.pdf", b"bytes one",
                 url="https://example.org/wp/1")
    renamed = path.rename(tmp_path / "scan0001.pdf")
    assert zi.find_receipt(renamed)[0]["url"] == "https://example.org/wp/1"


def test_a_receipt_is_found_after_the_file_is_edited(tmp_path):
    """OCR or page cuts change the md5 but not the name."""
    path = stage(tmp_path, "Report.pdf", b"bytes before",
                 url="https://example.org/wp/2")
    path.write_bytes(b"bytes after ocr")
    assert zi.find_receipt(path)[0]["url"] == "https://example.org/wp/2"


def test_a_file_both_renamed_and_edited_has_no_receipt(tmp_path):
    path = stage(tmp_path, "Report.pdf", b"bytes before")
    path.write_bytes(b"bytes after ocr")
    assert zi.find_receipt(path.rename(tmp_path / "other.pdf")) == (None, False)


def test_a_file_with_no_receipt_and_a_damaged_log_are_survived(tmp_path):
    lone = tmp_path / "lone.pdf"
    lone.write_bytes(b"x")
    assert zi.find_receipt(lone) == (None, False)
    (tmp_path / ".receipts.jsonl").write_text('not json\n[1]\n')
    assert zi.find_receipt(lone) == (None, False)


def test_the_receipt_log_is_not_a_staged_file(tmp_path):
    stage(tmp_path, "Report.pdf", b"bytes")
    staged = zi.staged_files(tmp_path, {tmp_path}, set(), [])
    assert [p.name for p in staged] == ["Report.pdf"]


@pytest.mark.parametrize("raw,expected", [
    ("HTTPS://Example.ORG/Wp/54/#sec2", "https://example.org/Wp/54"),
    ("https://example.org/a?x=1", "https://example.org/a?x=1"),
    ("http://example.org/a", "http://example.org/a"),
    ("not a url", ""),
])
def test_url_normalisation(raw, expected):
    assert zi.normal_url(raw) == expected


def test_scraped_identifiers_stay_apart_from_given_ones():
    given, scraped, urls = zi.receipt_keys({
        "identifiers": {"doi": "10.1/a", "arxiv": "2401.01234"},
        "identifiers_scraped": ["doi"],
        "url": "https://example.org/x", "final_url": "https://example.org/x/"})
    assert given == {"arxiv": "2401.01234"} and scraped == {"doi": "10.1/a"}
    assert urls == ["https://example.org/x"]


def test_an_identifier_the_url_states_is_given():
    given, _, _ = zi.receipt_keys({
        "identifiers": {}, "url": "https://arxiv.org/abs/2401.07777v2"})
    assert given["arxiv"] == "2401.07777"


# ── find-work --metadata reads a receipt as it reads extract-metadata ────────


def work_args(metadata, **over):
    import argparse

    flags = dict(metadata=str(metadata), title=None, doi=None, isbn=None,
                 arxiv=None, handle=None, pdf=None, type=None, url=None)
    flags.update(over)
    return argparse.Namespace(**flags)


@pytest.mark.parametrize("layout", ["line", "jsonl", "list", "items"])
def test_find_work_metadata_takes_a_receipt_without_editing(tmp_path, layout):
    receipt = {"status": "success", "path": "docs/R.pdf", "md5": "ab" * 16,
               "identifiers": {"doi": "10.5555/R", "isbn": None},
               "identifiers_scraped": [], "url": "https://example.org/r",
               "final_url": None, "title": "A report", "error": None}
    text = {"line": json.dumps(receipt),
            "jsonl": json.dumps(receipt) + "\n" + json.dumps(receipt) + "\n",
            "list": json.dumps([receipt]),
            "items": json.dumps({"items": [receipt]})}[layout]
    meta = tmp_path / "receipt.json"
    meta.write_text(text)
    works = zi.work_queries(work_args(meta))
    assert len(works) == (2 if layout == "jsonl" else 1)
    assert works[0]["doi"] == "10.5555/R" and works[0]["title"] == "A report"
    assert works[0]["pdf"] == "docs/R.pdf"
    assert works[0]["urls"] == ["https://example.org/r"]


def test_a_failed_receipt_stays_an_error_row(tmp_path):
    meta = tmp_path / "r.json"
    meta.write_text(json.dumps({"status": "failed", "path": "docs/x.pdf",
                                "md5": None, "error": "not found"}))
    (work,) = zi.work_queries(work_args(meta))
    assert work["error"] == "not found" and work["pdf"] == "docs/x.pdf"

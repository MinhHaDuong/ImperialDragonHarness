"""The existing-library report must find real cross-parent hash duplicates.

Author decision, 2026-10-16: "In tests up Zotero as a fixture or skip --
no mock". The library read is a REAL Zotero desktop client on a throwaway
profile (tests/zotero_live.py), a client of its own seeded once for this
module, since the report covers the whole library; those tests are marked
`integration` and skip where the client cannot run. The hashing logic for
clients that report no md5 (Zotero 7 to 9) is tested over an in-memory read
built by hand. The autouse fixture leaves Zotero down (closed port,
ZOTERO_NO_LAUNCH) for every other test. No test touches ~/Zotero, the
author's profile or port 23119.
"""

import argparse
import hashlib
import html
import json
import subprocess
import sys
from pathlib import Path

import pytest

import zotero_live
from child_env import child_env
from zotero_live import free_port

# The real-Zotero fixture (tests/zotero_live.py), bound here so pytest
# finds it by name.
zotero_factory = zotero_live.zotero_factory

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "zotero.py"
zi = zotero_live.helper_module()

KNOWN = b"known positive file"
SAME_PARENT = b"same parent only!!"
LONELY = b"a size nobody else has"


@pytest.fixture(autouse=True)
def zotero_down(monkeypatch):
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{free_port()}")
    monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")


def write_files(directory: Path) -> dict[str, Path]:
    files = {}
    for name, content in (("a.pdf", KNOWN), ("b.pdf", KNOWN),
                          ("unsafe.pdf", KNOWN), ("d.pdf", SAME_PARENT),
                          ("e.pdf", SAME_PARENT), ("lonely.pdf", LONELY)):
        files[name] = directory / name
        files[name].write_bytes(content)
    return files


@pytest.fixture(scope="module")
def library(zotero_factory, tmp_path_factory):
    """A client of its own: two parents share one file (one of them holds
    it twice), one parent holds two copies of another, one file is alone.
    Returns the client and the parents' keys."""
    zotero = zotero_factory("dedup")
    files = write_files(tmp_path_factory.mktemp("dedup-files"))
    keys = {
        "shared": zotero.save("<Unsafe & title>", DOI="10.1234/example",
                              pdfs=(files["a.pdf"], files["unsafe.pdf"])),
        "other": zotero.save("Different title", DOI="10.1234/example",
                             pdf=files["b.pdf"]),
        "same_parent": zotero.save("Same parent",
                                   pdfs=(files["d.pdf"], files["e.pdf"])),
        "lonely": zotero.save("Lonely", pdf=files["lonely.pdf"]),
    }
    return zotero, keys


@pytest.fixture
def use_library(library, monkeypatch):
    zotero, keys = library
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", zotero.url)
    return zotero, keys


def check_cluster(report, shared, other):
    assert report["candidate_clusters"] == 1
    assert report["hashed_attachments_scanned"] == 6
    (group,) = report["clusters"]
    assert group["hash"] == hashlib.md5(KNOWN).hexdigest()
    assert group["matched_by"] == "storageHash"
    pair = sorted([shared, other])
    assert [item["key"] for item in group["items"]] == pair
    counts = {item["key"]: len(item["attachments"]) for item in group["items"]}
    assert counts == {shared: 2, other: 1}
    assert group["bibliographic_overlap"] == [{"items": pair, "keys": ["doi"]}]


@pytest.mark.integration
def test_known_cross_parent_pair(use_library):
    """Zotero 10 reports each stored file's md5: one cluster, the two
    parents sharing the file; the parent with two copies of its own file
    is no cluster."""
    _, keys = use_library
    report = zi.duplicate_hash_report(zi.read_library("user"))
    check_cluster(report, keys["shared"], keys["other"])


def memory_library(directory: Path) -> dict:
    """The same library as an in-memory read from a client that reports no
    md5 (Zotero 7 to 9): each stored file has a path, nothing else."""
    files = write_files(directory)
    works = [{"key": key, "itemType": "journalArticle", "title": title,
              "DOI": doi, "ISBN": "", "date": "", "creators": []}
             for key, title, doi in (("PARENT10", "<Unsafe & title>", "10.1234/example"),
                                     ("PARENT11", "Different title", "10.1234/example"),
                                     ("PARENT12", "Same parent", ""),
                                     ("PARENT13", "Lonely", ""))]
    attachments = [{"key": key, "parent": parent, "filename": name,
                    "md5": None, "size": None, "path": str(files[name]),
                    "contentType": "application/pdf", "linkMode": "imported_file"}
                   for key, parent, name in (("ATT20", "PARENT10", "a.pdf"),
                                             ("ATT21", "PARENT11", "b.pdf"),
                                             ("ATT22", "PARENT10", "unsafe.pdf"),
                                             ("ATT30", "PARENT12", "d.pdf"),
                                             ("ATT31", "PARENT12", "e.pdf"),
                                             ("ATT32", "PARENT13", "lonely.pdf"))]
    return {"works": works, "attachments": attachments, "library_id": "user",
            "account": None, "zotero": "memory", "source": zi.LIBRARY_SOURCE}


def test_unreported_md5s_are_hashed_here(tmp_path):
    report = zi.duplicate_hash_report(memory_library(tmp_path))
    check_cluster(report, "PARENT10", "PARENT11")


def test_a_uniquely_sized_file_is_never_hashed(tmp_path, monkeypatch):
    idx = memory_library(tmp_path)
    hashed = []
    real = zi.file_md5
    monkeypatch.setattr(zi, "file_md5",
                        lambda p, *a: hashed.append(Path(p).name) or real(p, *a))
    zi.duplicate_hash_report(idx)
    assert "lonely.pdf" not in hashed and "a.pdf" in hashed


def item_versions(zotero) -> dict[str, int]:
    return {i["key"]: i["data"]["version"]
            for i in zotero.get("/api/users/0/items", limit=100)}


@pytest.mark.integration
def test_cli_report_is_escaped_linked_and_read_only(library, tmp_path):
    zotero, keys = library
    attachments = {key: zotero.children(key)
                   for key in (keys["shared"], keys["other"])}
    before = item_versions(zotero)
    out = tmp_path / "report.html"
    env = child_env()
    env.update(ZOTERO_CONNECTOR_URL=zotero.url, ZOTERO_NO_LAUNCH="1")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "dedup-report", "--out", str(out)],
        capture_output=True, text=True, check=True, env=env, stdin=subprocess.DEVNULL)
    body = out.read_text()
    assert "1 candidate groups" in result.stdout
    for parent, children in attachments.items():
        assert f"zotero://select/library/items/{parent}" in body
        for child in children:
            assert f"zotero://select/library/items/{child['key']}" in body
            assert html.escape(child["data"]["filename"]) in body
    assert "&lt;Unsafe &amp; title&gt;" in body
    assert "<Unsafe & title>" not in body
    assert keys["same_parent"] not in body and keys["lonely"] not in body
    assert out.stat().st_mode & 0o777 == 0o600
    assert item_versions(zotero) == before, "the report only reads"


@pytest.mark.integration
def test_report_names_its_source(use_library, capsys):
    args = argparse.Namespace(format="json", out=None)
    assert zi.cmd_dedup_report(args) == 0
    assert json.loads(capsys.readouterr().out)["source"] == zi.LIBRARY_SOURCE
    args.format = "html"
    assert zi.cmd_dedup_report(args) == 0
    assert "read live from zotero local API" in capsys.readouterr().out


def test_report_without_zotero_does_nothing(capsys):
    args = argparse.Namespace(format="json", out=None)
    assert zi.cmd_dedup_report(args) == zi.EXIT_UNAVAILABLE
    assert json.loads(capsys.readouterr().out)["zotero"] == "unavailable"

"""The existing-library report must find real cross-parent hash duplicates.

Author decision, 2026-10-16: "In tests up Zotero as a fixture or skip --
no mock". The library read is a REAL Zotero desktop client on a throwaway
profile (tests/zotero_live.py), a client of its own seeded once for this
module, since the report covers the whole library; those tests are marked
`integration` and skip where the client cannot run. Zotero 10, the floor,
reports each stored file's md5, so nothing is hashed here. The autouse
fixture leaves Zotero down (closed port, ZOTERO_NO_LAUNCH) for every other
test. No test touches ~/Zotero, the author's profile or port 23119.
"""

import argparse
import hashlib
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
def zotero_down(monkeypatch, tmp_path):
    monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{free_port()}")
    monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")
    monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE", str(tmp_path / "no-key.env"))


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
    zotero_live.point_helper_at(zotero, monkeypatch)
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
def test_known_cross_parent_pair(use_library, capsys):
    """Zotero 10 reports each stored file's md5: one cluster, the two
    parents sharing the file; the parent with two copies of its own file
    is no cluster."""
    _, keys = use_library
    assert zi.cmd_report_duplicates(argparse.Namespace(out=None)) == 0
    check_cluster(json.loads(capsys.readouterr().out), keys["shared"],
                  keys["other"])


@pytest.fixture(scope="module")
def trash_client(zotero_factory):
    """A client of its own: the trash would change the shared one's counts.
    Module-scoped, so it starts before the autouse fixture sets
    ZOTERO_NO_LAUNCH, like `library`."""
    return zotero_factory("dedup_trash")


@pytest.mark.integration
def test_a_trashed_parent_is_no_candidate(trash_client, monkeypatch, capsys,
                                          tmp_path):
    """A parent in the trash is left out, its stored copy with it."""
    zotero = zotero_live.point_helper_at(trash_client, monkeypatch)
    files = write_files(tmp_path)
    kept = (zotero.save("Kept one", pdf=files["a.pdf"]),
            zotero.save("Kept two", pdf=files["b.pdf"]))
    trashed = zotero.save("Trashed copy", pdf=files["unsafe.pdf"])
    z = zotero.client()
    item = z.item(trashed)
    item["data"]["deleted"] = 1
    assert z.update_item(item["data"])
    assert zi.cmd_report_duplicates(argparse.Namespace(out=None)) == 0
    report = json.loads(capsys.readouterr().out)
    (cluster,) = report["clusters"]
    assert {i["key"] for i in cluster["items"]} == set(kept)
    assert trashed not in json.dumps(report)


@pytest.mark.integration
def test_cli_report_is_json_linked_and_read_only(library, tmp_path):
    zotero, keys = library
    attachments = {key: zotero.children(key)
                   for key in (keys["shared"], keys["other"])}
    before = zotero.versions()
    out = tmp_path / "report.json"
    env = child_env()
    env.update(zotero.env(), ZOTERO_NO_LAUNCH="1")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "report-duplicates", "--out", str(out)],
        capture_output=True, text=True, check=True, env=env, stdin=subprocess.DEVNULL)
    report = json.loads(out.read_text())
    assert "1 candidate groups" in result.stdout
    (cluster,) = report["clusters"]
    listed = {item["key"]: {a["key"] for a in item["attachments"]}
              for item in cluster["items"]}
    for parent, children in attachments.items():
        assert {c["key"] for c in children} <= listed[parent]
        assert next(i for i in cluster["items"] if i["key"] == parent)["url"] == \
            f"zotero://select/library/items/{parent}"
    assert keys["same_parent"] not in listed and keys["lonely"] not in listed
    assert out.stat().st_mode & 0o777 == 0o600
    assert zotero.versions() == before, "the report only reads"


@pytest.mark.integration
def test_report_names_its_source(use_library, capsys):
    assert zi.cmd_report_duplicates(argparse.Namespace(out=None)) == 0
    assert json.loads(capsys.readouterr().out)["source"] == zi.LIBRARY_SOURCE


def test_the_report_has_no_html_format():
    """Ticket 1116: JSON only."""
    assert not hasattr(zi, "duplicate_hash_html")
    assert '"--format"' not in SCRIPT.read_text()


def test_report_without_zotero_does_nothing(capsys):
    args = argparse.Namespace(out=None)
    assert zi.cmd_report_duplicates(args) == zi.EXIT_UNAVAILABLE
    assert json.loads(capsys.readouterr().out)["zotero"] == "unavailable"

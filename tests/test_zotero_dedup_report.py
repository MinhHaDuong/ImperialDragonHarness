"""The existing-library report must find real cross-parent hash duplicates.

The library is a stub of the running Zotero's local API (tests/zotero_stub.py);
no test touches ~/Zotero or a running client.
"""

import hashlib
import importlib.util
import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env
from zotero_stub import StubZotero

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "zotero.py"
spec = importlib.util.spec_from_file_location("zotero_dedup_import", SCRIPT)
zi = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = zi
spec.loader.exec_module(zi)


@pytest.fixture(autouse=True)
def no_real_zotero(monkeypatch):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    monkeypatch.setattr(zi, "CONNECTOR_URL", f"http://127.0.0.1:{port}")
    monkeypatch.setattr(zi, "launch_zotero",
                        lambda cmd: pytest.fail(f"a test tried to launch {cmd}"))
    monkeypatch.setattr(zi, "in_container", lambda: "test run")


def fixture_library(tmp_path: Path, md5_reported: bool) -> StubZotero:
    """Two parents share one file; one parent holds two copies of another;
    a trashed parent and a group library hold the shared file too."""
    stub = StubZotero()
    files = {}
    for name, content in (("a.pdf", b"known positive file"),
                          ("b.pdf", b"known positive file"),
                          ("<unsafe & name>.pdf", b"known positive file"),
                          ("trashed.pdf", b"known positive file"),
                          ("d.pdf", b"same parent only!!"),
                          ("e.pdf", b"same parent only!!"),
                          ("group.pdf", b"known positive file"),
                          ("lonely.pdf", b"a size nobody else has")):
        files[name] = tmp_path / name.replace("<", "").replace(">", "")
        files[name].write_bytes(content)

    def md5(name):
        return hashlib.md5(files[name].read_bytes()).hexdigest() if md5_reported else None

    stub.add_work("PARENT10", "<Unsafe & title>", DOI="10.1234/example")
    stub.add_work("PARENT11", "Different title", DOI="10.1234/example")
    stub.add_work("PARENT12", "Same parent")
    stub.add_work("PARENT13", "Lonely")
    stub.add_work("TRASHED", "Trashed", trashed=True)
    for key, parent, name in (("ATT20", "PARENT10", "a.pdf"),
                              ("ATT21", "PARENT11", "b.pdf"),
                              ("ATT22", "PARENT10", "<unsafe & name>.pdf"),
                              ("ATT23", "TRASHED", "trashed.pdf"),
                              ("ATT30", "PARENT12", "d.pdf"),
                              ("ATT31", "PARENT12", "e.pdf"),
                              ("ATT32", "PARENT13", "lonely.pdf")):
        stub.add_attachment(key, parent, path=files[name], filename=name,
                            md5=md5(name))
    stub.add_group(3, "Shared")
    stub.add_work("GROUP50", "Group copy", prefix="groups/3")
    stub.add_attachment("ATT51", "GROUP50", path=files["group.pdf"],
                        prefix="groups/3", md5=md5("group.pdf"))
    return stub


@pytest.mark.parametrize("md5_reported", [True, False])
def test_known_cross_parent_pair_and_scope(tmp_path, monkeypatch, md5_reported):
    """Zotero 10 reports md5s; Zotero 7-9 do not, and the files are hashed
    here. Either way the same single cluster comes out, and the group copy
    and the trashed parent stay out of it."""
    stub = fixture_library(tmp_path, md5_reported)
    monkeypatch.setattr(zi, "CONNECTOR_URL", stub.start())
    try:
        report = zi.duplicate_hash_report(zi.read_library("user"))
    finally:
        stub.stop()
    assert report["candidate_clusters"] == 1
    assert report["hashed_attachments_scanned"] == 6
    group = report["clusters"][0]
    assert group["matched_by"] == "storageHash"
    assert [item["key"] for item in group["items"]] == ["PARENT10", "PARENT11"]
    assert [len(item["attachments"]) for item in group["items"]] == [2, 1]
    assert group["bibliographic_overlap"] == [
        {"items": ["PARENT10", "PARENT11"], "keys": ["doi"]}]


def test_a_uniquely_sized_file_is_never_hashed(tmp_path, monkeypatch):
    stub = fixture_library(tmp_path, md5_reported=False)
    monkeypatch.setattr(zi, "CONNECTOR_URL", stub.start())
    hashed = []
    real = zi.file_md5
    monkeypatch.setattr(zi, "file_md5",
                        lambda p, *a: hashed.append(Path(p).name) or real(p, *a))
    try:
        zi.duplicate_hash_report(zi.read_library("user"))
    finally:
        stub.stop()
    assert "lonely.pdf" not in hashed and "a.pdf" in hashed


@pytest.mark.integration
def test_cli_report_is_escaped_linked_and_read_only(tmp_path):
    stub = fixture_library(tmp_path, md5_reported=True)
    url = stub.start()
    out = tmp_path / "report.html"
    env = child_env()
    env.update(ZOTERO_CONNECTOR_URL=url, CI="1")  # CI: never launch a Zotero
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "dedup-report", "--out", str(out)],
            capture_output=True, text=True, check=True, env=env)
    finally:
        stub.stop()
    body = out.read_text()
    assert "1 candidate groups" in result.stdout
    assert "zotero://select/library/items/PARENT10" in body
    assert "zotero://select/library/items/PARENT11" in body
    assert "zotero://select/library/items/ATT20" in body
    assert "zotero://select/library/items/ATT21" in body
    assert "zotero://select/library/items/ATT22" in body
    assert "a.pdf" in body and "b.pdf" in body
    assert "&lt;unsafe &amp; name&gt;.pdf" in body
    assert "<unsafe & name>.pdf" not in body
    assert "&lt;Unsafe &amp; title&gt;" in body
    assert "<Unsafe & title>" not in body
    assert "GROUP50" not in body and "TRASHED" not in body
    assert out.stat().st_mode & 0o777 == 0o600
    assert [c[0] for c in stub.calls if c[0] != "GET"] == [], "the report only reads"


def test_report_names_its_source(tmp_path, monkeypatch, capsys):
    import argparse
    stub = fixture_library(tmp_path, md5_reported=True)
    monkeypatch.setattr(zi, "CONNECTOR_URL", stub.start())
    try:
        args = argparse.Namespace(format="json", out=None)
        assert zi.cmd_dedup_report(args) == 0
        assert json.loads(capsys.readouterr().out)["source"] == zi.LIBRARY_SOURCE
        args.format = "html"
        assert zi.cmd_dedup_report(args) == 0
        assert "read live from zotero local API" in capsys.readouterr().out
    finally:
        stub.stop()


def test_report_without_zotero_does_nothing(capsys):
    import argparse
    args = argparse.Namespace(format="json", out=None)
    assert zi.cmd_dedup_report(args) == zi.EXIT_UNAVAILABLE
    assert json.loads(capsys.readouterr().out)["zotero"] == "unavailable"

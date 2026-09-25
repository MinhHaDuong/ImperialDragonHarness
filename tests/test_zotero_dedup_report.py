"""The existing-library report must find real cross-parent hash duplicates."""

import hashlib
import importlib.util
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "zotero-import.py"
spec = importlib.util.spec_from_file_location("zotero_dedup_import", SCRIPT)
zi = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = zi
spec.loader.exec_module(zi)


def fixture_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE libraries (libraryID INTEGER PRIMARY KEY, type TEXT);
        CREATE TABLE items (itemID INTEGER PRIMARY KEY, libraryID INT,
                            itemTypeID INT, key TEXT);
        CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT);
        CREATE TABLE itemAttachments (itemID INTEGER PRIMARY KEY,
                 parentItemID INT, path TEXT, contentType TEXT, storageHash TEXT);
        CREATE TABLE deletedItems (itemID INT);
        CREATE TABLE fields (fieldID INTEGER PRIMARY KEY, fieldName TEXT);
        CREATE TABLE itemData (itemID INT, fieldID INT, valueID INT);
        CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, lastName TEXT);
        CREATE TABLE itemCreators (itemID INT, creatorID INT, orderIndex INT);
        INSERT INTO libraries VALUES (1,'user'),(3,'group');
        INSERT INTO itemTypes VALUES (1,'journalArticle'),(2,'attachment');
        INSERT INTO items VALUES
          (10,1,1,'PARENT10'),(11,1,1,'PARENT11'),
          (12,1,1,'PARENT12'),(13,1,1,'TRASHED'),(50,3,1,'GROUP50'),
          (20,1,2,'ATT20'),(21,1,2,'ATT21'),(22,1,2,'ATT22'),
          (23,1,2,'ATT23'),(30,1,2,'ATT30'),(31,1,2,'ATT31'),
          (51,3,2,'ATT51');
        INSERT INTO deletedItems VALUES (13);
        INSERT INTO fields VALUES (1,'title'),(2,'DOI');
        INSERT INTO itemDataValues VALUES
          (1,'<Unsafe & title>'),(2,'Different title'),(3,'10.1234/example');
        INSERT INTO itemData VALUES
          (10,1,1),(11,1,2),(10,2,3),(11,2,3);
    """)
    shared = hashlib.md5(b"known positive file").hexdigest()
    same_parent = hashlib.md5(b"same parent only").hexdigest()
    conn.executemany("INSERT INTO itemAttachments VALUES (?,?,?,?,?)", [
        (20, 10, "storage:a.pdf", "application/pdf", shared),
        (21, 11, "storage:b.pdf", "application/pdf", shared),
        (22, 10, "storage:c.pdf", "application/pdf", shared),
        (23, 13, "storage:trashed.pdf", "application/pdf", shared),
        (30, 12, "storage:d.pdf", "application/pdf", same_parent),
        (31, 12, "storage:e.pdf", "application/pdf", same_parent),
        (51, 50, "storage:group.pdf", "application/pdf", shared),
    ])
    conn.commit()
    conn.close()


def test_known_cross_parent_pair_and_scope(tmp_path):
    db = tmp_path / "zotero.sqlite"
    fixture_db(db)
    conn = zi.zotero_open(db)
    report = zi.duplicate_hash_report(conn)
    conn.close()
    assert report["candidate_clusters"] == 1
    assert report["hashed_attachments_scanned"] == 5
    group = report["clusters"][0]
    assert group["matched_by"] == "storageHash"
    assert [item["key"] for item in group["items"]] == ["PARENT10", "PARENT11"]
    assert [len(item["attachments"]) for item in group["items"]] == [2, 1]
    assert group["bibliographic_overlap"] == [
        {"items": ["PARENT10", "PARENT11"], "keys": ["doi"]}]


@pytest.mark.integration
def test_cli_report_is_escaped_linked_and_read_only(tmp_path):
    db = tmp_path / "zotero.sqlite"
    fixture_db(db)
    before = hashlib.sha256(db.read_bytes()).digest()
    out = tmp_path / "report.html"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "dedup-report", "--zotero-db", str(db),
         "--out", str(out)], capture_output=True, text=True, check=True)
    body = out.read_text()
    assert "1 candidate groups" in result.stdout
    assert "zotero://select/library/items/PARENT10" in body
    assert "zotero://select/library/items/PARENT11" in body
    assert "&lt;Unsafe &amp; title&gt;" in body
    assert "<Unsafe & title>" not in body
    assert "GROUP50" not in body and "TRASHED" not in body
    assert hashlib.sha256(db.read_bytes()).digest() == before
    assert out.stat().st_mode & 0o777 == 0o600


@pytest.mark.integration
def test_cli_refuses_nonempty_wal_snapshot(tmp_path):
    db = tmp_path / "zotero.sqlite"
    fixture_db(db)
    Path(str(db) + "-wal").write_bytes(b"pending")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "dedup-report", "--zotero-db", str(db)],
        capture_output=True, text=True)
    assert result.returncode != 0
    assert "pending WAL writes" in result.stderr

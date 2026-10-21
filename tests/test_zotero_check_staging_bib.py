"""check-staging: a project names its bibliography; underscore directories.

Pure logic, no Zotero: discovery of a `.bib` supplied by --bib or
`bib_paths`, the filter of `_superseded/`-style directories, and the shape of
what reaches the lookup. The same flows against a live client (the stored
`michaelowa2011.pdf` positive control) are in test_zotero_find_work.py.
"""

import argparse
import json
from pathlib import Path

import zotero_live

zi = zotero_live.helper_module()

DEEP_BIB = "deliverables/_shared/bibliography/main.bib"
BIB = """\
@article{michaelowa2011,
  title = {Aid effectiveness for climate change mitigation and adaptation},
  author = {Michaelowa, Axel},
  year = {2011},
  file = {docs/articles/michaelowa2011.pdf}
}
"""


def project(tmp_path: Path) -> Path:
    """A project shaped like the nominating one: a bibliography three
    levels down, files named by key, a superseded directory."""
    bib = tmp_path / DEEP_BIB
    bib.parent.mkdir(parents=True)
    bib.write_text(BIB)
    articles = tmp_path / "docs" / "articles"
    (articles / "_superseded").mkdir(parents=True)
    for name in ("michaelowa2011.pdf", "ghost2020.pdf",
                 "_superseded/old2001.pdf"):
        (articles / name).write_bytes(b"%PDF-1.4")
    return tmp_path


def names(found):
    return sorted(p.name for p in found["orphans"])


def test_a_bib_three_levels_down_is_invisible_by_default(tmp_path):
    """Control for the cases below: the default discovery does not find it."""
    root = project(tmp_path)
    found = zi.discover_directory(root, Path("docs/articles"))
    assert found["linked"] == [] and found["bib_files"] == []
    assert "michaelowa2011.pdf" in names(found)


def test_a_named_bib_links_its_file_under_dir(tmp_path):
    root = project(tmp_path)
    found = zi.discover_directory(root, Path("docs/articles"), [DEEP_BIB])
    (linked,) = found["linked"]
    assert linked["path"].name == "michaelowa2011.pdf"
    assert linked["key"] == "michaelowa2011"
    assert "Aid effectiveness" in linked["entry"]["title"]
    assert "michaelowa2011.pdf" not in names(found)
    assert found["errors"] == []
    assert "ghost2020.pdf" in names(found), "an undescribed file stays an orphan"


def test_a_named_bib_joins_the_default_discovery(tmp_path):
    root = project(tmp_path)
    (root / "refs.bib").write_text("@article{r, title={T}, file={docs/r.pdf}}\n")
    (root / "docs" / "r.pdf").write_bytes(b"%PDF-1.4")
    found = zi.discover_reconcile_files(root, [DEEP_BIB])
    assert {b.name for b in found["bib_files"]} == {"refs.bib", "main.bib"}
    assert {p["path"].name for p in found["linked"]} == {
        "r.pdf", "michaelowa2011.pdf"}


def test_a_named_bib_that_is_missing_or_outside_is_an_error(tmp_path):
    root = project(tmp_path)
    found = zi.discover_directory(root, Path("docs/articles"),
                                  ["nope.bib", "../elsewhere.bib"])
    assert any("not found: nope.bib" in e for e in found["errors"])
    assert any("outside repository: ../elsewhere.bib" in e
               for e in found["errors"])


def test_bib_paths_come_from_the_project_config(tmp_path):
    root = project(tmp_path)
    assert zi.project_bib_paths(root) == []
    (root / ".zotero-reconcile.json").write_text(
        json.dumps({"bib_paths": [DEEP_BIB]}))
    assert zi.project_bib_paths(root) == [DEEP_BIB]
    (root / ".zotero-reconcile.json").write_text('{"bib_paths": "main.bib"}')
    try:
        zi.project_bib_paths(root)
    except ValueError as exc:
        assert "bib_paths" in str(exc)
    else:
        raise AssertionError("a malformed bib_paths must not be ignored")


def test_underscore_directories_are_reported_unless_skipped(tmp_path):
    root = project(tmp_path)
    assert "old2001.pdf" in names(zi.discover_directory(root, Path("docs/articles")))
    skipped = zi.discover_directory(root, Path("docs/articles"), None, True)
    assert "old2001.pdf" not in names(skipped)
    assert "ghost2020.pdf" in names(skipped), "only underscore directories go"
    assert "old2001.pdf" not in names(
        zi.discover_reconcile_files(root, [DEEP_BIB], True))


def _link(root, *files):
    bib = root / "refs.bib"
    bib.write_text("".join(
        "@article{k%d, title={T}, file={%s}}\n" % (i, f)
        for i, f in enumerate(files)))
    return bib


def test_skip_underscore_dirs_also_drops_linked_files(tmp_path):
    root = project(tmp_path)
    _link(root, "docs/articles/_superseded/old2001.pdf",
          "docs/articles/ghost2020.pdf")
    for found in (
            zi.discover_directory(root, Path("docs/articles"), ["refs.bib"], True),
            zi.discover_reconcile_files(root, None, True)):
        assert [p["path"].name for p in found["linked"]] == ["ghost2020.pdf"]
        assert "old2001.pdf" not in names(found)
    kept = zi.discover_reconcile_files(root, None, False)
    assert {p["path"].name for p in kept["linked"]} == {
        "old2001.pdf", "ghost2020.pdf"}


def test_a_linked_markdown_file_is_never_reported(tmp_path):
    root = project(tmp_path)
    (root / "docs" / "articles" / "note.md").write_text("# note")
    _link(root, "docs/articles/note.md", "docs/articles/ghost2020.pdf")
    found = zi.discover_reconcile_files(root)
    assert [p["path"].name for p in found["linked"]] == ["ghost2020.pdf"]
    assert found["errors"] == []


def test_a_symlinked_bib_named_too_is_read_once(tmp_path):
    root = project(tmp_path)
    real = _link(root, "docs/articles/ghost2020.pdf")
    (root / "deliverables" / "link.bib").symlink_to(real)
    found = zi.discover_reconcile_files(root, ["deliverables/link.bib"])
    assert [p["path"].name for p in found["linked"]] == ["ghost2020.pdf"]
    assert found["errors"] == []


def test_the_bib_title_reaches_the_lookup_and_an_undescribed_key_is_unidentified(
        tmp_path, monkeypatch, capsys):
    """Through cmd_check_staging, with the library lookup stubbed at its
    seam (find_work): the title the lookup receives for the keyed file is
    the .bib's, and a keyed file the .bib does not describe is looked up
    by nothing and reported unidentified, never guessed."""
    root = project(tmp_path)
    asked = {}

    def fake_find_work(libs, **kw):
        asked[kw["pdf_path"].name] = kw
        usable = kw["title"] and len(kw["title"].split()) >= 3
        return {"verdict": "none" if usable else "unchecked", "matches": [],
                "candidates": [], "consulted": ["title"] if usable else [],
                "skipped": []}

    monkeypatch.setattr(zi, "find_work", fake_find_work)
    monkeypatch.setattr(zi, "ensure_zotero", lambda: None)
    monkeypatch.setattr(zi, "libraries", lambda library: [])
    monkeypatch.setattr(zi, "zotero_url", lambda: "http://stub")
    args = argparse.Namespace(root=str(root), dir="docs/articles", out=None,
                              apply=False, edit=False, library="user",
                              bib=[DEEP_BIB], skip_underscore_dirs=True)
    assert zi.cmd_check_staging(args) == 0
    report = json.loads(capsys.readouterr().out)
    rows = {r["file"]: r["verdict"] for r in report["rows"]}
    assert "Aid effectiveness" in asked["michaelowa2011.pdf"]["title"]
    assert rows["michaelowa2011.pdf"] == "absent", "negative control shape"
    assert rows["ghost2020.pdf"] == "unidentified"
    assert "old2001.pdf" not in asked

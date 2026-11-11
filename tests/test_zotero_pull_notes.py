"""Tests for `zotero.py pull-notes` (ticket 1526), the read side of
publish-notes (ticket 1525). Live client, no mock (author ruling 2026-10-16);
every note is invented: the harness is public.
"""

import argparse
import json

import pytest
import test_zotero_publish_notes as pub
import zotero_live
from zotero_live import closed_port, unique, unique_title

zotero_factory = zotero_live.zotero_factory
live_zotero = zotero_live.live_zotero
use_live = zotero_live.use_live

zi = zotero_live.helper_module()


@pytest.fixture(autouse=True)
def zotero_down(monkeypatch, tmp_path_factory):
    with closed_port() as port:
        monkeypatch.setenv("ZOTERO_CONNECTOR_URL", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("ZOTERO_NO_LAUNCH", "1")
        monkeypatch.setenv("ZOTERO_LOCAL_KEY_FILE",
                           str(tmp_path_factory.mktemp("keys") / "zotero-local.env"))
        monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path_factory.mktemp("state")))
        yield


def pull(capsys, project: str, *, out_dir=None) -> tuple[int, dict]:
    args = argparse.Namespace(project=project, library="user",
                              out_dir=str(out_dir) if out_dir else None)
    status = zi.cmd_pull_notes(args)
    return status, json.loads(capsys.readouterr().out)


def test_unavailable_is_not_an_empty_project(capsys):
    """Zotero down: exit 75 and "unavailable", never the empty result of a
    project with no notes."""
    status, out = pull(capsys, "demo")
    assert status == zi.EXIT_UNAVAILABLE
    assert out["zotero"] == "unavailable"
    assert "results" not in out


@pytest.mark.parametrize("project", ["", "two words", "a/b"])
def test_a_malformed_project_is_refused(project, capsys):
    status, out = pull(capsys, project)
    assert status == 1 and "error" in out


@pytest.mark.integration
def test_pull_returns_what_publish_filed(use_live, tmp_path, capsys):
    """Round trip: a note just published is pulled with its HTML, item,
    slug, version and date; another project's note is not."""
    item = use_live.save(unique_title())
    project = unique("proj").replace(" ", "-")
    drafts = [pub.write_draft(tmp_path, s, item, f"Invented text of {s}.")
              for s in ("note-a", "note-b")]
    other = pub.write_draft(tmp_path, "note-c", item, "Invented, elsewhere.")
    state = tmp_path / "state.json"
    assert pub.publish(capsys, project, *drafts, state_file=state)[0] == 0
    assert pub.publish(capsys, project + "x", other, state_file=state)[0] == 0

    status, out = pull(capsys, project)
    assert status == 0, out
    rows = {r["slug"]: r for r in out["results"]}
    assert set(rows) == {"note-a", "note-b"}
    for slug, row in rows.items():
        (note,) = pub.tagged_notes(use_live, item, f"wiki:{project}/{slug}")
        assert row["item"] == item and row["note"] == note["key"]
        assert row["version"] == note["version"]
        assert row["date_modified"] == note["data"]["dateModified"]
        assert row["html"] == note["data"]["note"]
        assert f"Invented text of {slug}." in row["html"]


@pytest.mark.integration
def test_an_empty_project_is_empty_with_zotero_up(use_live, capsys):
    status, out = pull(capsys, unique("proj").replace(" ", "-"))
    assert status == 0, out
    assert out["results"] == [] and out["zotero"] != "unavailable"


@pytest.mark.integration
def test_out_dir_gets_one_html_file_per_note(use_live, tmp_path, capsys):
    item = use_live.save(unique_title())
    project = unique("proj").replace(" ", "-")
    draft = pub.write_draft(tmp_path, "note-d", item, "Invented text for disk.")
    assert pub.publish(capsys, project, draft,
                       state_file=tmp_path / "s.json")[0] == 0
    target = tmp_path / "snap"
    status, out = pull(capsys, project, out_dir=target)
    assert status == 0, out
    (row,) = out["results"]
    assert "html" not in row
    assert (target / "note-d.html").read_text(encoding="utf-8").count(
        "Invented text for disk.") == 1
    assert row["file"] == str(target / "note-d.html")


@pytest.mark.integration
def test_a_note_edited_in_zotero_is_pulled_as_edited(use_live, tmp_path, capsys):
    item = use_live.save(unique_title())
    project = unique("proj").replace(" ", "-")
    draft = pub.write_draft(tmp_path, "note-e", item, "Invented, as merged.")
    assert pub.publish(capsys, project, draft,
                       state_file=tmp_path / "s.json")[0] == 0
    (note,) = pub.tagged_notes(use_live, item, f"wiki:{project}/note-e")
    use_live.client().update_item({**note["data"],
                                   "note": "<p>Invented, author's fix.</p>"})
    (row,) = pull(capsys, project)[1]["results"]
    assert "author's fix" in row["html"]
    assert row["version"] > note["version"]


@pytest.mark.integration
def test_one_slug_on_two_notes_is_ambiguous(use_live, capsys):
    """Two notes carry one tag: nothing is picked, nothing written."""
    project = unique("proj").replace(" ", "-")
    tag = f"wiki:{project}/note-dup"
    z = use_live.client()
    for _ in range(2):
        item = use_live.save(unique_title())
        assert z.create_items([{"itemType": "note", "parentItem": item,
                                "note": "<p>Invented.</p>",
                                "tags": [{"tag": tag}]}])["successful"]
    status, out = pull(capsys, project)
    assert status == 1, out
    assert [r["status"] for r in out["results"]] == ["ambiguous"] * 2


@pytest.mark.integration
def test_every_note_is_read_past_the_first_page(use_live, capsys):
    project = unique("proj").replace(" ", "-")
    item = use_live.save(unique_title())
    z = use_live.client()
    for start in range(0, 105, 50):
        batch = [{"itemType": "note", "parentItem": item,
                  "note": f"<p>Invented {n}.</p>",
                  "tags": [{"tag": f"wiki:{project}/n{n}"}]}
                 for n in range(start, min(start + 50, 105))]
        assert len(z.create_items(batch)["successful"]) == len(batch)
    status, out = pull(capsys, project)
    assert status == 0, out
    assert len(out["results"]) == 105

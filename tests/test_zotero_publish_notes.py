"""Tests for `zotero.py publish-notes` (ticket 1525).

Author decision, 2026-10-16: "In tests up Zotero as a fixture or skip --
no mock". The live tests run against a REAL Zotero desktop client on a
throwaway profile (tests/zotero_live.py), marked `integration`; they skip
where that client cannot run. Every note here is invented: the harness is
public.

The autouse fixture points the helper at a closed loopback port with
ZOTERO_NO_LAUNCH set, so the "Zotero is down" path is the real one; and at
a state directory of the test's own, never ~/.local/state.
"""

import argparse
import json

import pytest

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


def field_table(item_key: str, slug: str, *, wrapped: bool = False) -> str:
    """The draft's display table; `wrapped` is how Zotero's note editor
    rewrites it (a <tbody>, every cell's text in a <p>)."""
    rows = [("zotero_item", item_key), ("wiki_slug", slug)]
    if wrapped:
        cells = "".join(f"<tr><td><p>{k}</p></td><td><p>{v}</p></td></tr>"
                        for k, v in rows)
        return f"<table><tbody>{cells}</tbody></table>"
    cells = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows)
    return f"<table>{cells}</table>"


def write_draft(directory, slug: str, item_key: str, body: str, *,
                wrapped: bool = False):
    path = directory / f"{slug}.html"
    path.write_text(f"<h1>Reading note: an invented work</h1>\n"
                    f"{field_table(item_key, slug, wrapped=wrapped)}\n"
                    f"<p>{body}</p>\n", encoding="utf-8")
    return path


def write_frontmatter_draft(directory, slug: str, item_key: str, body: str):
    """The reading-note template's shape: YAML frontmatter, then the HTML
    body; only the body is published."""
    path = directory / f"{slug}.html"
    path.write_text(f'---\ntitle: "Reading note: an invented work"\n'
                    f'zotero_item: "{item_key}"  # the work\n'
                    f'status: "draft"\n---\n'
                    f"<h1>Reading note: an invented work</h1>\n<p>{body}</p>\n",
                    encoding="utf-8")
    return path


def publish(capsys, project: str, *drafts, dry_run: bool = False,
            state_file=None) -> tuple[int, dict]:
    args = argparse.Namespace(drafts=[str(d) for d in drafts], project=project,
                              dry_run=dry_run, library="user",
                              state_file=str(state_file) if state_file else None)
    status = zi.cmd_publish_notes(args)
    return status, json.loads(capsys.readouterr().out)


def tagged_notes(live, item_key: str, tag: str) -> list[dict]:
    return [c for c in live.children(item_key)
            if c["data"]["itemType"] == "note"
            and tag in {t["tag"] for t in c["data"].get("tags", [])}]


# --- pure logic --------------------------------------------------------------

@pytest.mark.parametrize("wrapped", [False, True])
def test_the_field_table_is_read_plain_or_editor_wrapped(wrapped):
    html = f"<p>x</p>{field_table('ABCD2345', 's', wrapped=wrapped)}"
    assert zi.draft_field(html, "zotero_item") == "ABCD2345"
    assert zi.draft_field(html, "absent") is None


@pytest.mark.integration
def test_a_draft_without_zotero_item_is_refused(use_live, tmp_path, capsys):
    """No item key in the field table: refused, never guessed."""
    draft = tmp_path / "orphan.html"
    draft.write_text("<p>Invented note, no field table.</p>", encoding="utf-8")
    status, out = publish(capsys, "demo", draft,
                          state_file=tmp_path / "state.json")
    assert status == 1, out
    (row,) = out["results"]
    assert row["status"] == "refused" and "zotero_item" in row["reason"]


def test_unavailable_is_not_in_sync(tmp_path, capsys):
    """Zotero down: exit 75 and "unavailable", nothing recorded; never the
    exit 0 of a run with nothing to publish."""
    draft = write_draft(tmp_path, "note-a", "ABCD2345", "Invented text.")
    state = tmp_path / "state.json"
    status, out = publish(capsys, "demo", draft, state_file=state)
    assert status == zi.EXIT_UNAVAILABLE
    assert out["zotero"] == "unavailable"
    assert "results" not in out or not any(
        r.get("status") == "in sync" for r in out["results"])
    assert not state.exists()


def test_the_frontmatter_names_the_item_and_stays_out_of_the_body():
    text = ('---\ntitle: "x"\nzotero_item: "ABCD2345"  # the work\n'
            'coding:\n  zotero_item: "NOTTHIS1"\n---\n<p>Body.</p>\n')
    meta, body = zi.split_draft(text)
    assert meta["zotero_item"] == "ABCD2345"
    assert body == "<p>Body.</p>\n"
    assert zi.split_draft("<p>No frontmatter.</p>") == ({}, "<p>No frontmatter.</p>")


# --- live --------------------------------------------------------------------

@pytest.mark.integration
def test_publish_creates_once_and_a_second_run_changes_nothing(use_live,
                                                               tmp_path, capsys):
    item = use_live.save(unique_title())
    project, slug = unique("proj").replace(" ", "-"), "note-one"
    draft = write_draft(tmp_path, slug, item, "Invented summary, first draft.")
    state = tmp_path / "state.json"

    status, out = publish(capsys, project, draft, state_file=state)
    assert status == 0, out
    (row,) = out["results"]
    assert row["status"] == "created"
    tag = f"wiki:{project}/{slug}"
    (note,) = tagged_notes(use_live, item, tag)
    assert "first draft" in note["data"]["note"]

    before = use_live.versions()
    status, out = publish(capsys, project, draft, state_file=state)
    assert status == 0, out
    assert out["results"][0]["status"] == "in sync"
    assert use_live.versions() == before
    assert len(tagged_notes(use_live, item, tag)) == 1


@pytest.mark.integration
def test_a_changed_draft_updates_the_note_in_place(use_live, tmp_path, capsys):
    item = use_live.save(unique_title())
    project, slug = unique("proj").replace(" ", "-"), "note-two"
    state = tmp_path / "state.json"
    draft = write_draft(tmp_path, slug, item, "Invented text, version one.")
    assert publish(capsys, project, draft, state_file=state)[0] == 0
    (first,) = tagged_notes(use_live, item, f"wiki:{project}/{slug}")

    write_draft(tmp_path, slug, item, "Invented text, version two.")
    status, out = publish(capsys, project, draft, state_file=state)
    assert status == 0, out
    assert out["results"][0]["status"] == "updated"
    (after,) = tagged_notes(use_live, item, f"wiki:{project}/{slug}")
    assert after["key"] == first["key"]
    assert "version two" in after["data"]["note"]


@pytest.mark.integration
def test_editor_wrapping_does_not_break_matching(use_live, tmp_path, capsys):
    """A draft whose field table carries the editor's wrapping still names
    its item, and a published note the editor rewrote (table wrapped, the
    draft's rows gone) is still found by its tag: no duplicate."""
    item = use_live.save(unique_title())
    project, slug = unique("proj").replace(" ", "-"), "note-wrapped"
    state = tmp_path / "state.json"
    draft = write_draft(tmp_path, slug, item, "Invented text.", wrapped=True)
    status, out = publish(capsys, project, draft, state_file=state)
    assert status == 0, out
    assert out["results"][0]["status"] == "created"

    tag = f"wiki:{project}/{slug}"
    (note,) = tagged_notes(use_live, item, tag)
    z = use_live.client()
    z.update_item({**note["data"], "note": "<div data-schema-version=\"9\">"
                   + field_table("ZZZZ9999", "other", wrapped=True)
                   + "<p>Invented text.</p></div>"})
    status, out = publish(capsys, project, draft, state_file=state)
    assert out["results"][0]["note"] == note["key"]
    assert len(tagged_notes(use_live, item, tag)) == 1


@pytest.mark.integration
def test_a_note_edited_in_zotero_is_refused_not_overwritten(use_live, tmp_path,
                                                            capsys):
    item = use_live.save(unique_title())
    project, slug = unique("proj").replace(" ", "-"), "note-edited"
    state = tmp_path / "state.json"
    draft = write_draft(tmp_path, slug, item, "Invented text, as merged.")
    assert publish(capsys, project, draft, state_file=state)[0] == 0
    tag = f"wiki:{project}/{slug}"
    (note,) = tagged_notes(use_live, item, tag)
    z = use_live.client()
    z.update_item({**note["data"], "note": "<p>Invented text, author's fix.</p>"})

    # The draft did not change: the author's edit stands, nothing to do.
    status, out = publish(capsys, project, draft, state_file=state)
    assert status == 0, out
    assert out["results"][0]["status"] == "edited in zotero"

    # The draft changed too: refused, the author's edit kept.
    write_draft(tmp_path, slug, item, "Invented text, a later draft.")
    status, out = publish(capsys, project, draft, state_file=state)
    assert status == 1, out
    (row,) = out["results"]
    assert row["status"] == "refused"
    assert "edited in Zotero since last publish" in row["reason"]
    (kept,) = tagged_notes(use_live, item, tag)
    assert "author's fix" in kept["data"]["note"]


@pytest.mark.integration
def test_a_tagged_note_without_a_publish_record_is_refused(use_live, tmp_path,
                                                           capsys):
    """A tagged note this machine never published (state lost, another
    machine) is not overwritten blind."""
    project, slug = unique("proj").replace(" ", "-"), "note-foreign"
    tag = f"wiki:{project}/{slug}"
    item = use_live.save(unique_title())
    z = use_live.client()
    assert z.create_items([{"itemType": "note", "parentItem": item,
                            "note": "<p>Invented, written elsewhere.</p>",
                            "tags": [{"tag": tag}]}])["successful"]
    draft = write_draft(tmp_path, slug, item, "Invented text, local draft.")
    status, out = publish(capsys, project, draft,
                          state_file=tmp_path / "state.json")
    assert status == 1, out
    assert out["results"][0]["status"] == "refused"
    (kept,) = tagged_notes(use_live, item, tag)
    assert "written elsewhere" in kept["data"]["note"]


@pytest.mark.integration
def test_dry_run_reads_only(use_live, tmp_path, capsys):
    item = use_live.save(unique_title())
    project, slug = unique("proj").replace(" ", "-"), "note-dry"
    state = tmp_path / "state.json"
    draft = write_draft(tmp_path, slug, item, "Invented text.")
    before = use_live.versions()
    status, out = publish(capsys, project, draft, dry_run=True,
                          state_file=state)
    assert status == 0, out
    assert out["results"][0]["status"] == "would create"
    assert use_live.versions() == before
    assert not state.exists()

    assert publish(capsys, project, draft, state_file=state)[0] == 0
    write_draft(tmp_path, slug, item, "Invented text, changed.")
    before = use_live.versions()
    recorded = state.read_text()
    status, out = publish(capsys, project, draft, dry_run=True,
                          state_file=state)
    assert out["results"][0]["status"] == "would update"
    assert use_live.versions() == before
    assert state.read_text() == recorded


@pytest.mark.integration
def test_a_frontmatter_draft_publishes_its_body_only(use_live, tmp_path, capsys):
    """The template's draft: the frontmatter names the item and stays in the
    repository; a frontmatter-only change (status) is not a new version."""
    item = use_live.save(unique_title())
    project, slug = unique("proj").replace(" ", "-"), "Invented2026_Note"
    state = tmp_path / "state.json"
    draft = write_frontmatter_draft(tmp_path, slug, item, "Invented body.")
    status, out = publish(capsys, project, draft, state_file=state)
    assert status == 0, out
    assert out["results"][0]["status"] == "created"
    (note,) = tagged_notes(use_live, item, f"wiki:{project}/{slug}")
    assert "Invented body." in note["data"]["note"]
    assert "zotero_item" not in note["data"]["note"]

    draft.write_text(draft.read_text().replace('status: "draft"',
                                               'status: "author revised"'))
    status, out = publish(capsys, project, draft, state_file=state)
    assert out["results"][0]["status"] == "in sync", out

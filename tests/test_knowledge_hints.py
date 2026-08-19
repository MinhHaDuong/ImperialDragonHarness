#!/usr/bin/env python3
"""Contract for the project domain-knowledge hint channel.

Driven through the script's real CLI and stdin protocol rather than by importing
its helpers: the catalog reaches the model through `on-start.sh` and the term
channel through a hook fed JSON on stdin, and a test that calls the functions
directly is blind to argument wiring, to the stdin contract, and to the silent
no-op paths that matter most here.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Every test here spawns the script as a real subprocess -- that is the point:
# the catalog reaches the model through on-start.sh and the term channel through
# a hook fed JSON on stdin, so in-process calls would not exercise the contract.
# Subprocess cost puts the whole module in the integration tier.
pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "knowledge_hints.py"

MANIFEST = """
[[hint]]
id      = "het-field-map"
summary = "History of economic thought: the 196 entries of the Elgar Handbook on the History of Economic Analysis (2016), with page addresses and cross-references"
pointer = "conception/canon.md"
full    = "conception/map.md"
caveat  = "records the 2016 classification, not source content"
terms   = ["Cournot", "Handbook"]
"""


def project(tmp_path: Path, manifest: str = MANIFEST, pointer: bool = True) -> Path:
    root = tmp_path / "repo"
    (root / "conception").mkdir(parents=True)
    if pointer:
        (root / "conception" / "canon.md").write_text("roster", encoding="utf-8")
    (root / ".knowledge.toml").write_text(manifest, encoding="utf-8")
    return root


def catalog(cwd: Path) -> str:
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "--cwd", str(cwd), "catalog"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def prompt(cwd: Path, text: str, session: str = "s1") -> str:
    # The dedup marker dir is keyed off TMPDIR and survives the process, so a
    # suite that shares it is not repeatable: the second run sees every hint
    # already consumed and fails green-to-red for the wrong reason. Point it at
    # the per-test tmp dir instead.
    # Nested one level below tmp_path on purpose: the marker dir is
    # $TMPDIR/claude-knowledge-hints, so a `../../` session id escapes two
    # levels. With TMPDIR at tmp_path the escape lands *above* tmp_path, where
    # the traversal test cannot see it — and that test then passes with the
    # sanitisation deleted, which is how the first two versions of it were
    # green against a live defect.
    cache = cwd.parent / "cache"
    cache.mkdir(exist_ok=True)
    payload = json.dumps({"prompt": text, "session_id": session, "cwd": str(cwd)})
    env = {**os.environ, "TMPDIR": str(cache)}
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "prompt"],
        input=payload, capture_output=True, text=True, check=True, env=env,
    )
    return out.stdout


def test_catalog_names_hint_and_pointer(tmp_path):
    got = catalog(project(tmp_path))
    assert "het-field-map" in got
    assert "conception/canon.md" in got


def test_catalog_stays_one_line_per_hint(tmp_path):
    """Resident cost is the whole design constraint; guard it mechanically."""
    body = [ln for ln in catalog(project(tmp_path)).splitlines() if ln.startswith("- ")]
    assert len(body) == 1


def test_catalog_omits_the_body(tmp_path):
    """The pointer is injected, never the payload."""
    root = project(tmp_path)
    (root / "conception" / "canon.md").write_text("SECRET-ROSTER-BODY", encoding="utf-8")
    assert "SECRET-ROSTER-BODY" not in catalog(root)


def test_found_from_a_subdirectory(tmp_path):
    root = project(tmp_path)
    assert "het-field-map" in catalog(root / "conception")


def test_silent_without_manifest(tmp_path):
    (tmp_path / "bare").mkdir()
    assert catalog(tmp_path / "bare") == ""


def test_malformed_manifest_is_silent_not_fatal(tmp_path):
    assert catalog(project(tmp_path, manifest="[[hint]\nid = ")) == ""


def test_hint_with_missing_pointer_is_dropped(tmp_path):
    """Advertising a dead path costs a turn to discover; drop it instead."""
    assert catalog(project(tmp_path, pointer=False)) == ""


def test_term_match_fires_with_caveat(tmp_path):
    got = prompt(project(tmp_path), "What does the Handbook say about duopoly?")
    assert "conception/canon.md" in got
    assert "2016 classification" in got, "the caveat must travel with the pointer"


def test_term_match_is_word_bounded(tmp_path):
    """A substring hit would fire on unrelated words and train the model to ignore it."""
    assert prompt(project(tmp_path), "the handbookish tendency") == ""


def test_term_match_is_case_insensitive(tmp_path):
    assert "canon.md" in prompt(project(tmp_path), "on cournot's duopoly")


def test_no_match_is_silent(tmp_path):
    assert prompt(project(tmp_path), "refactor the payment module") == ""


def test_deduped_per_session(tmp_path):
    root = project(tmp_path)
    first = prompt(root, "Cournot", session="dedup-a")
    second = prompt(root, "Cournot again", session="dedup-a")
    assert first != ""
    assert second == "", "a hint repeated every turn becomes noise"


def test_distinct_sessions_each_get_it(tmp_path):
    root = project(tmp_path)
    assert prompt(root, "Cournot", session="dedup-b") != ""
    assert prompt(root, "Cournot", session="dedup-c") != ""


def test_garbage_stdin_is_not_fatal(tmp_path):
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "prompt"],
        input="not json", capture_output=True, text=True,
    )
    assert out.returncode == 0
    assert out.stdout == ""


def test_session_id_cannot_escape_the_marker_dir(tmp_path):
    """session_id is untrusted; a traversal must not write outside the cache.

    Asserted by sweeping the whole tmp tree for any marker outside the cache
    directory, not by naming one expected escape path. The first version of this
    test named `escape` and passed even with the sanitisation deleted, because
    `marker_path` appends `.{id}` — so the real escape would have been
    `escape.het-field-map` and the assertion looked at a filename that could
    never exist either way. A test whose green is unreachable by the defect it
    names is not a test.
    """
    root = project(tmp_path)
    assert prompt(root, "Cournot", session="../../escape") != ""
    marker_dir = root.parent / "cache" / "claude-knowledge-hints"
    strays = [p for p in root.parent.rglob("*escape*") if p.parent != marker_dir]
    assert strays == [], f"marker escaped the cache dir: {strays}"


def test_pointer_cannot_escape_the_repo(tmp_path):
    """An absolute or ../ pointer would instruct the agent to read any file.

    `Path(root) / "/etc/passwd"` discards root entirely, so an existence check
    alone accepts it — and what this hook prints lands in the model's context.
    """
    for escape in ("/etc/passwd", "../../../../etc/passwd"):
        root = project(tmp_path / escape.replace("/", "_"), manifest=f"""
[[hint]]
id      = "exfil"
summary = "read this"
pointer = "{escape}"
terms   = ["Cournot"]
""")
        assert catalog(root) == "", f"catalog advertised {escape}"
        assert prompt(root, "Cournot") == "", f"term channel advertised {escape}"


def test_full_that_escapes_is_dropped_but_hint_survives(tmp_path):
    root = project(tmp_path, manifest=MANIFEST.replace(
        'full    = "conception/map.md"', 'full    = "/etc/passwd"'))
    (root / "conception" / "map.md").write_text("m", encoding="utf-8")
    got = prompt(root, "Cournot")
    assert "het-field-map" in got, "the hint itself must survive a bad `full`"
    assert "/etc/passwd" not in got


def test_empty_term_does_not_fire_on_everything(tmp_path):
    """`""` compiles to a pattern matching beside almost any punctuation."""
    root = project(tmp_path, manifest=MANIFEST.replace(
        'terms   = ["Cournot", "Handbook"]', 'terms   = ["", "  ", "Cournot"]'))
    assert prompt(root, "refactor the payment module.") == ""
    assert "canon.md" in prompt(root, "about Cournot", session="s2")


def test_non_utf8_manifest_is_silent_not_fatal(tmp_path):
    """A manifest saved in Latin-1 is an editor accident, not a crash."""
    root = project(tmp_path)
    (root / ".knowledge.toml").write_bytes(b'[[hint]]\nid = "\xff\xfe"\n')
    assert catalog(root) == ""


def test_non_dict_json_payload_is_silent_not_fatal(tmp_path):
    """`[]` parses as valid JSON, then crashes on .get if unguarded."""
    root = project(tmp_path)
    for payload in ("[]", "42", "null", '"str"'):
        out = subprocess.run(
            [sys.executable, str(SCRIPT), "prompt"],
            input=payload, capture_output=True, text=True,
        )
        assert out.returncode == 0, f"{payload} exited {out.returncode}"
        assert out.stdout == ""


def test_hint_with_non_string_field_is_dropped(tmp_path):
    assert catalog(project(tmp_path, manifest="""
[[hint]]
id      = 123
summary = "numeric id"
pointer = "conception/canon.md"
""")) == ""


def test_id_is_capped_so_the_catalog_stays_bounded(tmp_path):
    """`summary` is capped; an uncapped `id` would defeat the same budget."""
    root = project(tmp_path, manifest=MANIFEST.replace(
        'id      = "het-field-map"', f'id      = "{"x" * 5000}"'))
    assert len(catalog(root)) < 1000

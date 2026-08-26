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
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))  # knowledge_hints imports path_utils

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
    # No project fixture: this probes the payload guard alone. The subprocess
    # is launched with neither `--cwd` nor a cwd, so a tmp project tree would
    # never be consulted — the old `root = project(tmp_path)` was dead setup,
    # not a side effect worth keeping (ticket 0590).
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


# --- white-box, and deliberately so -------------------------------------------
# The two guards below are invisible from outside: the `except (Exception,
# SystemExit)` wrapper around main() turns any crash into exit 0 with empty
# stdout, which is byte-identical to the guarded behaviour. Mutation-testing the
# black-box suite proved it — both survived. So they are asserted directly, at
# the function, or they would be defended by nothing a test can see.

def _module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("kh", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_load_hints_survives_non_utf8_manifest(tmp_path):
    m = tmp_path / ".knowledge.toml"
    m.write_bytes(b'[[hint]]\nid = "\xff\xfe"\n')
    assert _module().load_hints(m) == []


def test_load_hints_survives_non_table_toplevel(tmp_path):
    m = tmp_path / ".knowledge.toml"
    m.write_text('hint = "not a list of tables"', encoding="utf-8")
    assert _module().load_hints(m) == []


def test_cmd_prompt_rejects_non_mapping_payload(monkeypatch, tmp_path):
    import io
    kh = _module()
    for payload in ("[]", "42", "null", '"str"'):
        monkeypatch.setattr(kh.sys, "stdin", io.StringIO(payload))
        args = type("A", (), {"cwd": str(tmp_path)})()
        assert kh.cmd_prompt(args) == 0


def test_output_is_declarative_not_imperative(tmp_path):
    """rules/workflow.md: the model reads imperative hook text as injection.

    An imperative hint would be discounted — the channel then fails silently
    while looking like it worked, which is the worst available failure.
    """
    got = catalog(project(tmp_path)) + prompt(project(tmp_path / "b"), "Cournot")
    low = got.lower()
    for bossy in ("read `", "you must", "before answering", "you should"):
        assert bossy not in low, f"imperative framing in hook output: {bossy!r}"


def test_scalar_terms_string_is_ignored_not_iterated(tmp_path):
    """`terms = "Cournot"` is iterable: per-character, a lone `o` would fire.

    Asserted at the function as well as end to end: the end-to-end form alone
    passes for the wrong reason under the obvious mutation, because a build that
    iterates strings also crashes on the `None` of an absent `paths`, and the
    empty output of a crash is indistinguishable from the empty output of a
    guard doing its job.
    """
    assert _module()._str_list("Cournot") == []
    assert _module()._str_list(["a", "", "  ", 3]) == ["a"]
    root = project(tmp_path, manifest=MANIFEST.replace(
        'terms   = ["Cournot", "Handbook"]', 'terms   = "Cournot"'))
    assert prompt(root, "something with an o in it") == ""


def test_multiline_summary_stays_one_line(tmp_path):
    root = project(tmp_path, manifest=MANIFEST.replace(
        'summary = "History', 'summary = """line one\nline two\nline three"""\nunused = "History'))
    # Counting only lines that start with "- " is what made the first version
    # of this test vacuous: the second and third physical lines of a multi-line
    # summary carry no prefix, so they were invisible to the very assertion
    # meant to catch them. Count every line instead.
    got = catalog(root).splitlines()
    assert len(got) == 2, f"catalog rendered {len(got)} lines, want header + 1"


def test_hint_count_is_capped_and_says_so(tmp_path):
    """Per-field caps bound a line; only a count cap bounds the catalog."""
    many = "\n".join(f"""
[[hint]]
id      = "h{i}"
summary = "summary number {i}"
pointer = "conception/canon.md"
""" for i in range(60))
    got = catalog(project(tmp_path, manifest=many))
    body = [ln for ln in got.splitlines() if ln.startswith("- ")]
    assert len(body) <= 25, f"catalog emitted {len(body)} lines"
    assert "not shown" in got, "a cap that hides what it dropped reads as complete"

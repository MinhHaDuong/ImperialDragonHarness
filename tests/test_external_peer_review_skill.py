"""external-peer-review bundles a portable script and documents its contract.

The skill solicits real external model reviews of a PDF and synthesizes them.
These ratchets pin the documented contract in the skill text and the portability
invariants in the bundled script (no project-specific hardcoding).
"""

import os
import site
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO / "skills" / "external-peer-review"
SKILL = SKILL_DIR / "SKILL.md"
SCRIPT = SKILL_DIR / "peer_review.py"


def skill_text() -> str:
    return SKILL.read_text()


def script_text() -> str:
    return SCRIPT.read_text()


def test_bundled_script_exists():
    assert SCRIPT.exists(), "external-peer-review must bundle peer_review.py"


def test_documents_balance_gate_and_text_fallback():
    assert "$0.50" in skill_text(), "must document the OpenRouter $0.50 files gate"
    assert "--text" in skill_text(), "must document the text-mode fallback flag"
    assert "402" in skill_text(), "must document the HTTP 402 automatic fallback"


def test_documents_smoke_test_one_before_blasting():
    text = skill_text().lower()
    assert "smoke" in text or "test one" in text, (
        "must document smoke-testing one combo before launching the rest "
        "(project rule: test one before blasting)"
    )


def test_documents_complementary_to_simulated_panel():
    assert "review-pr-prose" in skill_text(), (
        "must state it is complementary to the simulated /review-pr-prose panel"
    )


def test_first_sentence_names_real_external_models():
    """Discoverability: plain searchable keywords in the opening sentence."""
    first = skill_text().split("description:", 1)[1].split("\n", 1)[0].lower()
    for kw in ("peer review", "openai", "mistral"):
        assert kw in first, f"first sentence should mention {kw!r}"


def test_script_is_portable_no_project_hardcoding():
    src = script_text()
    # The reference implementation baked in the AEDIST topic; the portable
    # version must not. Topic is supplied via --topic, not hardcoded.
    assert "thermal" not in src.lower(), "script must not hardcode a paper topic"
    assert "--models" in src and "--personas" in src, (
        "models and personas must be CLI-configurable"
    )
    assert "--credential-env" in src, (
        "the credential identity must be a CLI input, not a constant"
    )


# ── credential resolution (ticket 0943) ──────────────────────────────────────
#
# Hygiene, non-negotiable: every value below is an obviously-fake sentinel in a
# fake keystore under a fake HOME. No real credential is ever read, and the
# child prints the LENGTH of what it resolved, never the value itself.

# The keystore line for the target variable carries an `export ` prefix. That
# is the discriminator: the deleted `.env` walk matched `line.startswith(NAME=)`
# and would miss it, while sourcing the file as shell code does not. A test
# whose fixture used only a bare assignment would pass against a hand-rolled
# Python parser too.
KEYSTORE_SENTINEL = "sk-or-v1-FAKE-KEYSTORE-SENTINEL-0943-not-a-real-key"
ENV_SENTINEL = "sk-or-v1-FAKE-ENV-SENTINEL-0943"
POSITIVE_CONTROL = "PEER-REVIEW-0943-HAYSTACK-CONTROL"
CRED_NAME = "OPENROUTER_API_KEY_IDH"
DECOY_NAME = "OPENROUTER_API_KEY_AEDIST"

CHILD = """
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("peer_review_under_test", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
value = mod.resolve_credential(sys.argv[2])
print({control!r})
print("resolved_length=%d" % len(value))
"""


def _fake_home(tmp_path):
    """A fake HOME carrying a fake keystore. Returns the home path."""
    home = tmp_path / "fake-home"
    keys = home / ".config" / "keys"
    keys.mkdir(parents=True)
    (keys / "openrouter.env").write_text(
        f"# fake keystore fixture — no real credential lives here\n"
        f"{DECOY_NAME}=fake-decoy-value-0943\n"
        f"export {CRED_NAME}='{KEYSTORE_SENTINEL}'\n"
    )
    return home


def _child_env(home, extra=None):
    """A child environment built FROM SCRATCH.

    Never ``{**os.environ, ...}``: this machine can carry a live
    ``OPENROUTER_API_KEY_IDH``, and inheriting it would make the keystore case
    pass without the keystore being read at all. PATH is needed for ``bash``
    and PYTHONPATH for the script's third-party import, since a fake HOME
    hides the real user site-packages.
    """
    env = {
        "HOME": str(home),
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "PYTHONPATH": site.getusersitepackages(),
    }
    env.update(extra or {})
    return env


def _run_child(tmp_path, home, extra_env=None, name=CRED_NAME):
    child = tmp_path / "child.py"
    child.write_text(CHILD.format(control=POSITIVE_CONTROL))
    return subprocess.run(
        [sys.executable, str(child), str(SCRIPT), name],
        env=_child_env(home, extra_env),
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )


def test_resolves_credential_from_keystore_without_leaking_it(tmp_path):
    home = _fake_home(tmp_path)
    proc = _run_child(tmp_path, home)
    assert proc.returncode == 0, f"child failed: {proc.stderr[-2000:]}"
    haystack = proc.stdout + proc.stderr
    assert POSITIVE_CONTROL in haystack, (
        "positive control absent — the leak assertion below would pass "
        "vacuously against an empty haystack"
    )
    assert KEYSTORE_SENTINEL not in haystack, (
        "the resolved value must never reach stdout, stderr or a log"
    )
    assert f"resolved_length={len(KEYSTORE_SENTINEL)}" in proc.stdout, (
        "must resolve the export-prefixed keystore assignment by sourcing the "
        "provider file as shell code"
    )


def test_environment_wins_over_keystore(tmp_path):
    home = _fake_home(tmp_path)
    assert len(ENV_SENTINEL) != len(KEYSTORE_SENTINEL), "lengths must discriminate"
    proc = _run_child(tmp_path, home, {CRED_NAME: ENV_SENTINEL})
    assert proc.returncode == 0, f"child failed: {proc.stderr[-2000:]}"
    haystack = proc.stdout + proc.stderr
    assert POSITIVE_CONTROL in haystack
    assert ENV_SENTINEL not in haystack and KEYSTORE_SENTINEL not in haystack
    assert f"resolved_length={len(ENV_SENTINEL)}" in proc.stdout, (
        "an already-set environment variable must win over the keystore"
    )


def test_fails_loud_naming_file_and_variable(tmp_path):
    home = tmp_path / "empty-home"
    (home / ".config" / "keys").mkdir(parents=True)
    proc = _run_child(tmp_path, home)
    assert proc.returncode != 0, "unresolvable credential must never be a silent no-op"
    assert CRED_NAME in proc.stderr, "the failure must name the variable probed"
    assert "openrouter.env" in proc.stderr, "the failure must name the file probed"


def test_rejects_a_credential_name_that_is_not_a_variable_name(tmp_path):
    """The name reaches a ``bash -c``; it must be validated before it gets there."""
    home = _fake_home(tmp_path)
    proc = _run_child(tmp_path, home, name='X"; echo INJECTED; #')
    assert proc.returncode != 0, (
        "a name reaching a bash -c must be rejected, not passed through"
    )
    assert "not a valid shell variable name" in proc.stderr, (
        "rejection must happen in the validator, before any shell sees the name"
    )
    assert POSITIVE_CONTROL not in proc.stdout, (
        "rejection must abort before the credential is resolved"
    )


def test_dotenv_walk_and_repo_root_are_gone():
    """Removal ratchet: the walk and its only consumer must not come back."""
    src = script_text()
    assert "load_api_key" not in src, "the .env-walking resolver must be deleted"
    assert "--repo-root" not in src, (
        "--repo-root existed only to seed the .env walk"
    )

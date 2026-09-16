"""Does a clean Codex or Pi profile actually discover perch? (ticket 0802)

The ticket asks for checks that fail because a clean profile cannot find the
skill, and then pass through the native installation mechanism. A structural
assertion about where a file sits cannot make that distinction -- it would pass
against a harness that ignores the directory entirely.

So each harness is asked, offline and with no model call:

* Codex renders the model-visible prompt with ``codex debug prompt-input``;
  a discovered skill appears in its ``<skills_instructions>`` block.
* Pi answers ``get_commands`` over its RPC mode; a discovered skill appears as
  ``skill:<name>`` with the location it was loaded from.

Both run against a throwaway ``$HOME``, so nothing here touches the author's
profile, and both carry their own negative control: the same probe runs first
on the clean profile and must come back empty. A probe that answers "no perch"
because it cannot see anything is the failure mode this guards against.

Live *invocation* is a different claim and is not automated anywhere: it costs
a paid model call on a third-party account. Those three assertions are recorded
in ``adapters/pilot-support.json`` as ``manual-smoke`` with ``result:
pending``, and the PR body names them.

Integration tier: subprocesses, and each probe takes seconds.
"""

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TIMEOUT = 120


def _module():
    spec = importlib.util.spec_from_file_location(
        "perch_pilot_probe", REPO / "adapters" / "perch.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


perch = _module()

pytestmark = pytest.mark.integration


@pytest.fixture
def profile(tmp_path, monkeypatch):
    """A throwaway harness profile: empty $HOME, a cwd outside any project."""
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    workdir = tmp_path / "work"
    workdir.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("USERPROFILE", raising=False)
    monkeypatch.chdir(workdir)
    return home


def _env(home: Path, **extra: str) -> dict[str, str]:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.update(extra)
    return env


def _codex_prompt(home: Path) -> str:
    done = subprocess.run(
        ["codex", "debug", "prompt-input"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        env=_env(home, CODEX_HOME=str(home / ".codex")),
    )
    assert done.returncode == 0, done.stderr[-2000:]
    return done.stdout


def _pi_commands(home: Path) -> list[dict]:
    done = subprocess.run(
        ["pi", "--mode", "rpc", "--no-session"],
        input='{"id":"c1","type":"get_commands"}\n',
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        env=_env(home, PI_OFFLINE="1"),
    )
    assert done.returncode == 0, done.stderr[-2000:]
    for line in done.stdout.splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if payload.get("command") == "get_commands":
            assert payload["success"], payload
            return payload["data"]["commands"]
    raise AssertionError(f"no get_commands response in: {done.stdout[:2000]}")


@pytest.mark.skipif(shutil.which("codex") is None, reason="codex CLI not installed")
def test_a_clean_codex_profile_gains_perch_only_after_install(profile):
    before = _codex_prompt(profile)
    assert "perch" not in before.lower(), "negative control failed: perch already there"
    assert "skills_instructions" in before, (
        "positive control for the probe itself: codex must be reporting *some* "
        "skills, or an empty result would prove nothing"
    )

    perch.install("codex")

    after = _codex_prompt(profile)
    assert "- perch:" in after
    description = perch.frontmatter(REPO / "skills" / "perch" / "SKILL.md")["description"]
    assert description.split(".")[0] in after


@pytest.mark.skipif(shutil.which("pi") is None, reason="pi CLI not installed")
def test_a_clean_pi_profile_gains_perch_only_after_install(profile):
    before = {command["name"] for command in _pi_commands(profile)}
    assert "skill:perch" not in before, "negative control failed"

    perch.install("pi")

    after = {command["name"]: command for command in _pi_commands(profile)}
    assert "skill:perch" in after, sorted(after)
    entry = after["skill:perch"]
    canonical = perch.frontmatter(REPO / "skills" / "perch" / "SKILL.md")
    assert entry["description"] == canonical["description"], (
        "pi must be reading the canonical body, not a copy"
    )


@pytest.mark.skipif(shutil.which("pi") is None, reason="pi CLI not installed")
def test_pi_reads_perch_through_the_neutral_home_symlink(profile):
    perch.install("pi")
    entry = {c["name"]: c for c in _pi_commands(profile)}["skill:perch"]
    path = Path(entry.get("path") or entry["sourceInfo"]["path"])
    assert path.is_relative_to(perch.neutral_home())
    assert path.resolve() == (REPO / "skills" / "perch" / "SKILL.md").resolve()


@pytest.mark.skipif(shutil.which("pi") is None, reason="pi CLI not installed")
def test_uninstall_takes_perch_back_out_of_a_pi_profile(profile):
    perch.install("pi")
    assert "skill:perch" in {c["name"] for c in _pi_commands(profile)}
    perch.uninstall("pi")
    assert "skill:perch" not in {c["name"] for c in _pi_commands(profile)}
    assert not perch.neutral_home().exists()


@pytest.mark.parametrize("harness", perch.HARNESSES)
def test_the_recorded_probe_command_is_the_one_that_ran(harness):
    """The inventory's probe_command must be runnable, not decorative.

    Routed through ``check_version`` rather than run directly, so the binary
    ``_probe`` resolves is asserted to be the binary the inventory names --
    the two could drift silently otherwise.
    """
    command = perch.policy(harness)["probe_command"]
    binary = command.split()[0]
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")
    assert command.split()[1:] == ["--version"], command
    assert binary == harness, f"{command} does not probe {harness}"
    probed = perch.parse_version(perch.check_version(harness))
    assert probed >= perch.parse_version(perch.policy(harness)["minimum_version"])


def _fake_cli(tmp_path: Path, name: str, body: str) -> Path:
    """A stand-in CLI, so the odd outputs below need no odd real binary."""
    script = tmp_path / name
    script.write_bytes(b"#!/bin/sh\n" + body.encode("utf-8"))
    script.chmod(0o755)
    return script


def test_invalid_utf8_from_a_cli_stays_inside_the_refusal_contract(
    tmp_path, monkeypatch
):
    """Strict decoding raised through `_probe`'s except clause as a traceback.

    UnicodeDecodeError is neither OSError nor SubprocessError, so `main()`,
    which catches only Refusal, exited 1 with a traceback where the module
    documents exit 2 and one line.
    """
    script = _fake_cli(tmp_path, "badcodex", r"printf 'codex-cli \377\376 0.154.0\n'")
    monkeypatch.setenv("PERCH_CODEX_BIN", str(script))
    assert perch.check_version("codex") == "0.154.0"

    mute = _fake_cli(tmp_path, "mutecodex", r"printf '\377\376\n'")
    monkeypatch.setenv("PERCH_CODEX_BIN", str(mute))
    with pytest.raises(perch.Refusal):
        perch.check_version("codex")


def test_the_cli_reports_a_refusal_as_one_line_and_exit_two(tmp_path):
    mute = _fake_cli(tmp_path, "mutecodex", r"printf '\377\376\n'")
    done = subprocess.run(
        ["python3", str(REPO / "adapters" / "perch.py"), "check-version", "codex"],
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        env={**os.environ, "PERCH_CODEX_BIN": str(mute)},
    )
    assert done.returncode == 2, done
    assert done.stderr.startswith("perch pilot: ")
    assert "Traceback" not in done.stderr


@pytest.mark.parametrize(
    "body",
    (
        "echo 'bundled with node 20.11.0' >&2\necho 'codex-cli 0.154.0'\n",
        "echo '' >&2\necho 'codex-cli 0.154.0'\n",
    ),
    ids=("banner-on-stderr", "empty-stderr"),
)
def test_a_decoy_version_on_the_other_stream_is_not_adopted(
    tmp_path, monkeypatch, body
):
    script = _fake_cli(tmp_path, "noisycodex", body)
    monkeypatch.setenv("PERCH_CODEX_BIN", str(script))
    assert perch.check_version("codex") == "0.154.0"


@pytest.mark.parametrize(
    "body",
    (
        "echo 'bundled with node 20.11.0'\necho 'codex-cli 0.154.0'\n",
        "echo 'codex-cli 0.154.0'\necho 'see 1.2.3 for details'\n",
    ),
    ids=("decoy-first", "decoy-after"),
)
def test_an_ambiguous_version_answer_refuses_rather_than_picking(
    tmp_path, monkeypatch, body
):
    """A decoy ahead of the real answer flipped the floor.

    `parse_version` takes the first semver it is handed, so codex 0.154.0
    behind a "node 20.11.0" banner read as 20.11.0 — which clears a 0.154.0
    minimum. Two candidate lines is an unknown version, and this module does
    not pass unknown versions.
    """
    script = _fake_cli(tmp_path, "noisycodex", body)
    monkeypatch.setenv("PERCH_CODEX_BIN", str(script))
    with pytest.raises(perch.Refusal, match="version-like"):
        perch.check_version("codex")

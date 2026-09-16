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


@pytest.mark.parametrize("harness", ("codex", "pi"))
def test_the_recorded_probe_command_is_the_one_that_ran(harness):
    """The inventory's probe_command must be runnable, not decorative."""
    command = perch.policy(harness)["probe_command"]
    binary = command.split()[0]
    if shutil.which(binary) is None:
        pytest.skip(f"{binary} not installed")
    done = subprocess.run(
        command.split(), capture_output=True, text=True, timeout=TIMEOUT
    )
    assert done.returncode == 0, done.stderr[-500:]
    probed = perch.parse_version(done.stdout + done.stderr)
    assert probed >= perch.parse_version(perch.policy(harness)["minimum_version"])

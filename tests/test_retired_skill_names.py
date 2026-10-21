"""Retired skill names stay out of live paths (ticket 1144, design 1096 answer 5).

review-pr and review-pr-prose folded into /gaze with no alias: a live mention
sends an agent to a skill that no longer exists, which it may then improvise.
History is exempt (docs/, memory/, tickets/, projects/), and so is the
smart-testing reference data, which records past test ids.
"""

import subprocess
from pathlib import Path

import pytest
from child_env import child_env

pytestmark = pytest.mark.adherence

ROOT = Path(__file__).resolve().parents[1]
RETIRED = ("review-pr",)  # matches review-pr-prose too
LIVE = ("skills", "tests", "profiles", "agents", "adapters", "scripts", "rules",
        "hooks", "README.md", "AGENTS.md", "skills-catalog.md")
SELF = str(Path(__file__).relative_to(ROOT))


def _grep(name: str, *pathspec: str) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "grep", "-l", "-F", name, "--", *pathspec],
        capture_output=True, text=True, env=child_env(),
    )
    assert out.returncode in (0, 1), out.stderr
    return out.stdout.split()


def test_no_live_reference_to_a_retired_skill():
    for name in RETIRED:
        assert _grep(name, SELF) == [SELF], "positive control: the probe must see this file"
        hits = _grep(name, *LIVE, ":!tests/smart-testing", f":!{SELF}")
        assert hits == [], f"live references to retired skill {name}: {hits}"

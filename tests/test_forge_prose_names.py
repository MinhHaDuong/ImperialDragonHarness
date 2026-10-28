"""Ticket 1320: the forge.py verbs the merge, claims, and capture prose name exist."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "skills/merge/SKILL.md",
    "skills/merge/references/claims.md",
    "skills/lair/SKILL.md",
    "skills/roar/runbooks/capture.md",
]
NAMED = re.compile(r'forge\.py"?\s+(?:--forge\s+\S+\s+)?([a-z][a-z-]*)')


def _verbs(rel):
    return set(NAMED.findall((ROOT / rel).read_text()))


def test_merge_prose_names_forge_verbs():
    assert {"resolve", "read-back"} <= _verbs("skills/merge/SKILL.md")


def test_capture_prose_names_a_forge_verb():
    assert "resolve" in _verbs("skills/roar/runbooks/capture.md")


@pytest.mark.parametrize("verb", sorted(set().union(*(_verbs(f) for f in FILES))))
def test_named_verb_answers_help(verb):
    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts/forge.py"), verb, "--help"],
        capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr


def test_merge_disarm_reads_request_n_by_number():
    """Ticket 1325: two open requests can share a head branch; the disarm read names N."""
    text = (ROOT / "skills/merge/SKILL.md").read_text()
    step = text[text.index("**Disarm"):text.index("5a. **")]
    assert re.search(r'forge\.py"?\s+read-back\s+N\b', step), step
    assert "--head <branch>" not in step, step

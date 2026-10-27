"""Lair step 16 points out slow tickets and only suggests (ticket 1239). Negatives pinned, as for step 12."""

import re
from pathlib import Path

SKILL = (Path(__file__).resolve().parents[1] / "skills" / "lair" / "SKILL.md").read_text()
STEP = re.split(r"\n(?=\d+\. |# )", SKILL.split("**Point out slow tickets.**", 1)[1], 1)[0]
PROHIBITION = re.compile(r"\b(?:do(?:es)? not|never|omit|no)\b[^.;:]*")
RESIDUE = PROHIBITION.sub(" ", STEP.lower())


def test_step_16_only_suggests():
    for pat in (r"\bask\b|\bconfirm\b", r"\bwait|\bpoll\b", r"\blaunch|\binvok|\bstart\b|\bspawn",
                r"\btimer|\bschedul|\bcron"):
        assert not re.search(pat, RESIDUE), pat


def test_step_16_keeps_the_threshold_in_the_script_only():
    assert not re.search(r"\b30\b|thirty", STEP)
    assert "scripts/slow_tickets.py" in STEP


def test_step_16_folds_test_doctor_into_step_13():
    assert "step 13" in STEP

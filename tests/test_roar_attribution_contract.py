"""Roar's retired celebration script stays retired."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_roar_log_celebration_script_stays_removed():
    assert not (ROOT / "skills/roar/log-celebration").exists()

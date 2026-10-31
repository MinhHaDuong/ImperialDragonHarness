"""raid_log append refuses events missing the keys the sitrep doc table requires (ticket 1398)."""
import importlib.util
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("raid_log_under_test", SCRIPTS / "raid_log.py")
rl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rl)


def add(tmp_path, event, **fields):
    return rl.append(event, {"raid": "ab12cd", **fields}, tmp_path / "raid.log", now=1)


def test_wave_missing_tickets_names_key_and_form(tmp_path):
    with pytest.raises(ValueError, match=r"missing tickets=.*WAVE n=<number> tickets=<tickets>"):
        add(tmp_path, "WAVE", n="1")
    assert add(tmp_path, "WAVE", n="1", tickets="a,b").endswith("tickets=a,b")


def test_pr_step_must_be_documented(tmp_path):
    assert add(tmp_path, "PR", n="3", ticket="9", step="gate_round_2")
    with pytest.raises(ValueError, match="step= must be one of"):
        add(tmp_path, "PR", n="3", ticket="9", step="running")
    with pytest.raises(ValueError, match="missing ticket="):
        add(tmp_path, "PR", n="3", step="gaze")


def test_queue_n_numeric_and_optional_keys_not_required(tmp_path):
    with pytest.raises(ValueError, match="n= must be a number"):
        add(tmp_path, "QUEUE", n="few")
    assert add(tmp_path, "QUEUE", n="0")
    assert rl.append("RAID_START", {}, tmp_path / "r2.log", now=1).startswith("1 RAID_START raid=")
    assert add(tmp_path, "WAVE_BASE", sha="abc")

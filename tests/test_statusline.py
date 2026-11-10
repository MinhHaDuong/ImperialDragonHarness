"""Behaviour of scripts/statusline.sh on fixture input (ticket 1499)."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "statusline.sh"

pytestmark = pytest.mark.skipif(shutil.which("jq") is None, reason="jq not installed")


def _run(window: dict) -> str:
    payload = {"model": {"display_name": "Opus"}, "effort": {"level": "high"}, "context_window": window}
    done = subprocess.run(
        ["bash", str(SCRIPT)], input=json.dumps(payload), capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


def test_large_context_prints_whole_prompt_in_tokens():
    usage = {"input_tokens": 2_000, "cache_read_input_tokens": 209_362, "cache_creation_input_tokens": 123}
    out = _run({"used_percentage": 21, "current_usage": usage})
    assert out == "[Opus/high] prompt 211K"


def test_small_context_keeps_a_decimal():
    usage = {"input_tokens": 100, "cache_read_input_tokens": 8_000, "cache_creation_input_tokens": 300}
    assert _run({"current_usage": usage}) == "[Opus/high] prompt 8.4K"


def test_tiny_context_is_exact():
    assert _run({"current_usage": {"input_tokens": 420}}) == "[Opus/high] prompt 420"


def test_percentage_is_not_the_figure():
    usage = {"input_tokens": 1, "cache_read_input_tokens": 549_999}
    out = _run({"used_percentage": 55, "context_window_size": 1_000_000, "current_usage": usage})
    assert "550K" in out and "%" not in out


def test_no_usage_is_visibly_unknown_not_zero():
    assert _run({"used_percentage": 12}) == "[Opus/high] prompt ?"
    assert _run({"current_usage": None}) == "[Opus/high] prompt ?"

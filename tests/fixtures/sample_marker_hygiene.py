"""Teeth fixture for the static marker-hygiene lens (ticket 0229).

NOT collected by pytest (name is sample_*, not test_*). Each function below is
a labelled positive/negative case the teeth test asserts against. Editing this
file changes what the lens is proven to catch — keep the labels accurate.
"""

import subprocess  # noqa: F401  (referenced via aliases / attribute below)
import time as clock
from subprocess import run as r  # aliased spawn

import pytest


# ── MUST FLAG ────────────────────────────────────────────────────────────────


def test_aliased_spawn_unmarked():
    """Aliased `from subprocess import run as r`, no marker -> FLAG."""
    r(["true"])


def test_attr_spawn_unmarked():
    """`subprocess.Popen` attribute call, no marker -> FLAG."""
    subprocess.Popen(["true"])


def test_aliased_module_sleep_unmarked():
    """`import time as clock; clock.sleep(...)`, no marker -> FLAG."""
    clock.sleep(0)


def test_spawn_inside_closure_unmarked():
    """Call inside a nested closure still attributes to the test fn -> FLAG."""

    def _inner():
        r(["true"])

    _inner()


# ── MUST NOT FLAG ────────────────────────────────────────────────────────────


@pytest.mark.integration
def test_marked_spawn():
    """Same spawn, but carrying the marker via decorator -> NOT flagged."""
    r(["true"])


def test_subprocess_only_in_comment_and_string():
    """subprocess.run mentioned in a comment and a string literal -> NOT flagged.

    The lens parses the AST, so neither a comment nor a string constant is a
    call node. (This docstring itself names subprocess.run and time.sleep.)
    """
    # subprocess.run(["echo"]) — this is a comment, not a call.
    message = "calls subprocess.run and time.sleep but only as text"
    assert "subprocess.run" in message


def test_no_spawn_at_all():
    """A pure test with no spawn/sleep -> NOT flagged."""
    assert 1 + 1 == 2

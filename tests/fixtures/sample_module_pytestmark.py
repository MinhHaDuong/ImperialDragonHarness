"""Teeth fixture: a module-level `pytestmark` list including `integration`
marks EVERY test in the module — so a spawning test here must NOT be flagged.

NOT collected by pytest (sample_*, not test_*).
"""

import subprocess

import pytest

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("tmp_path")]


def test_spawn_covered_by_module_mark():
    """Spawns, but the module pytestmark carries `integration` -> NOT flagged."""
    subprocess.run(["true"], check=False)

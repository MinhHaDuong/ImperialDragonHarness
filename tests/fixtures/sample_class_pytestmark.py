"""Teeth fixture: class-level `pytestmark` covers methods in that class only.

A spawning method under a class whose pytestmark carries `integration` is NOT
flagged; a spawning method whose enclosing class has a `skipif`-only pytestmark
(no `integration`) IS flagged. Proves class-level resolution and that `skipif`
is not mistaken for `integration`. The walker must not crash on classes.

NOT collected by pytest (sample_*, not test_*).
"""

import subprocess

import pytest


class TestCovered:
    pytestmark = pytest.mark.integration

    def test_spawn_covered_by_class_mark(self):
        """Class pytestmark carries `integration` -> NOT flagged."""
        subprocess.run(["true"], check=False)


class TestSkipifOnly:
    pytestmark = pytest.mark.skipif(True, reason="x")

    def test_spawn_under_skipif_only(self):
        """Class pytestmark is skipif (not integration) -> FLAG."""
        subprocess.run(["true"], check=False)


class TestSkipifReasonIntegration:
    pytestmark = pytest.mark.skipif(True, reason="integration only")

    def test_spawn_under_skipif_reason_integration(self):
        """Class pytestmark is `skipif` whose reason string says `integration` —
        structurally NOT the `integration` mark -> FLAG (substring/`\\b`-regex on
        the unparsed pytestmark would wrongly exempt this)."""
        subprocess.run(["true"], check=False)

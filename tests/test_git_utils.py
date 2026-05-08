"""Tests for scripts/git_utils.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import git_utils  # noqa: E402


class TestDefaultBranch:
    def test_returns_branch_from_symbolic_ref(self, tmp_path):
        with patch("git_utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="origin/develop\n", returncode=0)
            assert git_utils._default_branch(tmp_path) == "develop"

    def test_falls_back_to_main(self, tmp_path):
        with patch("git_utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=128)
            assert git_utils._default_branch(tmp_path) == "main"

    def test_strips_origin_prefix(self, tmp_path):
        with patch("git_utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="origin/main\n", returncode=0)
            assert git_utils._default_branch(tmp_path) == "main"

    def test_passes_project_as_cwd(self, tmp_path):
        with patch("git_utils.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=128)
            git_utils._default_branch(tmp_path)
            mock_run.assert_called_once()
            assert (
                mock_run.call_args.kwargs.get("cwd") == tmp_path
                or mock_run.call_args[1].get("cwd") == tmp_path
            )

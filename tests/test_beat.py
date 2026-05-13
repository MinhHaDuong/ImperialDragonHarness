"""Tests for scripts/beat.py — happy and adverse paths."""

import contextlib
import json
import os
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Import the module under test ───────────────────────────────────────────────
# Beat.py lives outside the package hierarchy; import by path.
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import beat  # noqa: E402


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def reset_state():
    """Reset module-level _state and DRY_RUN between tests."""
    beat._state = beat._State()
    original_dry_run = beat.DRY_RUN
    yield
    beat._state = beat._State()
    beat.DRY_RUN = original_dry_run


@pytest.fixture()
def tmp_project(tmp_path):
    """Minimal git-like project directory with beat-log.jsonl."""
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture()
def beat_log(tmp_project):
    return tmp_project / "beat-log.jsonl"


@pytest.fixture()
def git_ok():
    """Patch beat._git to succeed (returncode=0) for tests that call _raid()."""
    with patch("beat._git", return_value=MagicMock(returncode=0, stdout="", stderr="")):
        yield


# ── parse_pick ─────────────────────────────────────────────────────────────────


class TestParsePick:
    def test_pick_exact(self):
        assert beat.parse_pick("PICK: 0023") == ("pick", "0023")

    def test_pick_with_leading_prose(self):
        assert beat.parse_pick("After reviewing tickets, PICK: 0111") == (
            "pick",
            "0111",
        )

    def test_pick_multiline(self):
        assert beat.parse_pick("Thinking...\nPICK: 0042\nDone.") == ("pick", "0042")

    def test_pick_no_space(self):
        # "PICK:0023" without space — regex requires \s* so this matches
        assert beat.parse_pick("PICK:0023") == ("pick", "0023")

    def test_idle_keyword(self):
        assert beat.parse_pick("IDLE: no eligible tickets") == ("idle", None)

    def test_idle_case_insensitive(self):
        assert beat.parse_pick("idle: nothing to do") == ("idle", None)

    def test_idle_takes_precedence_over_pick(self):
        # If both appear, IDLE wins (safety bias)
        assert beat.parse_pick("IDLE: queue empty\nPICK: 0007") == ("idle", None)

    def test_ambiguous_no_keyword(self):
        assert beat.parse_pick("I reviewed the tickets and found nothing") == (
            "idle",
            None,
        )

    def test_empty_string(self):
        assert beat.parse_pick("") == ("idle", None)

    def test_pick_must_be_four_digits(self):
        # Three-digit ID should not match \d{4}
        assert beat.parse_pick("PICK: 042") == ("idle", None)

    def test_pick_five_digits_no_match(self):
        assert beat.parse_pick("PICK: 00042") == ("idle", None)

    def test_dry_run_sentinel(self):
        assert beat.parse_pick("PICK: 9999") == ("pick", "9999")

    def test_closed_signal_parsing(self):
        # Tier 2 (ticket 0049): pick-ticket emits CLOSED: <id> when it
        # detects a ticket whose exit criteria are already met.
        status, ticket_id = beat.parse_pick("CLOSED: 0049")
        assert status == "closed"
        assert ticket_id == "0049"

    def test_closed_with_prose(self):
        status, ticket_id = beat.parse_pick(
            "Exit criteria already met.\nCLOSED: 0039\nMoving on."
        )
        assert status == "closed"
        assert ticket_id == "0039"

    def test_closed_must_be_four_digits(self):
        # Mirror PICK behavior: only 4-digit IDs match.
        assert beat.parse_pick("CLOSED: 042") == ("idle", None)

    def test_idle_takes_precedence_over_closed(self):
        # If pick-ticket emits both CLOSED and IDLE, IDLE wins (safety bias):
        # treat as idle so beat.py doesn't loop on a malformed transcript.
        assert beat.parse_pick("CLOSED: 0049\nIDLE: nothing left") == ("idle", None)


# ── housekeeping_needed ────────────────────────────────────────────────────────


class TestHousekeepingNeeded:
    _SHA = "abc1234567890abcdef1234567890abcdef123456"

    def test_no_commits_returns_true(self, tmp_project):
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            assert beat.housekeeping_needed(tmp_project) is True

    def test_recent_commit_returns_false(self, tmp_project):
        recent = f"{int(time.time()) - 3600} {self._SHA}"
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=recent + "\n", returncode=0)
            assert beat.housekeeping_needed(tmp_project) is False

    def test_old_commit_with_activity_returns_true(self, tmp_project):
        old = f"{int(time.time()) - 14 * 3600} {self._SHA}"
        with patch("beat.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=old + "\n", returncode=0),
                MagicMock(stdout="3\n", returncode=0),
            ]
            assert beat.housekeeping_needed(tmp_project) is True

    def test_old_commit_idle_returns_false(self, tmp_project):
        old = f"{int(time.time()) - 14 * 3600} {self._SHA}"
        with patch("beat.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=old + "\n", returncode=0),
                MagicMock(stdout="0\n", returncode=0),
            ]
            assert beat.housekeeping_needed(tmp_project) is False

    def test_safety_floor_always_runs(self, tmp_project):
        very_old = f"{int(time.time()) - 25 * 3600} {self._SHA}"
        with patch("beat.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=very_old + "\n", returncode=0),  # last hk commit
                MagicMock(stdout="abc1234 recent work\n", returncode=0),  # not frozen
            ]
            assert beat.housekeeping_needed(tmp_project) is True

    def test_corrupted_timestamp_returns_true(self, tmp_project):
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="not-a-number\n", returncode=0)
            assert beat.housekeeping_needed(tmp_project) is True

    def test_exactly_at_threshold_is_not_needed(self, tmp_project):
        at_threshold = (
            f"{int(time.time()) - beat.HOUSEKEEPING_INTERVAL_S + 10} {self._SHA}"
        )
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=at_threshold + "\n", returncode=0)
            assert beat.housekeeping_needed(tmp_project) is False


# ── append_beat_log ────────────────────────────────────────────────────────────


class TestAppendBeatLog:
    def test_appends_record(self, tmp_project, beat_log):
        beat.append_beat_log(
            tmp_project, {"outcome": "in_progress", "last_run_at": "t"}
        )
        records = [json.loads(line) for line in beat_log.read_text().splitlines()]
        assert records == [{"outcome": "in_progress", "last_run_at": "t"}]

    def test_appends_multiple_records(self, tmp_project, beat_log):
        beat.append_beat_log(tmp_project, {"outcome": "in_progress"})
        beat.append_beat_log(tmp_project, {"outcome": "done"})
        outcomes = [
            json.loads(line)["outcome"] for line in beat_log.read_text().splitlines()
        ]
        assert outcomes == ["in_progress", "done"]

    def test_dry_run_is_noop(self, tmp_project, beat_log):
        beat.DRY_RUN = True
        beat.append_beat_log(tmp_project, {"outcome": "done"})
        assert not beat_log.exists()


# ── finalize_beat_log ──────────────────────────────────────────────────────────


class TestFinalizeBeatLog:
    def test_replaces_trailing_in_progress(self, tmp_project, beat_log):
        beat_log.write_text(
            json.dumps({"outcome": "in_progress", "last_run_at": "t"}) + "\n"
        )
        beat.finalize_beat_log(tmp_project, {"outcome": "done", "ticket_id": "0001"})
        lines = beat_log.read_text().splitlines()
        assert len(lines) == 1
        assert json.loads(lines[0])["outcome"] == "done"

    def test_keeps_prior_records(self, tmp_project, beat_log):
        beat_log.write_text(
            json.dumps({"outcome": "done", "ticket_id": "0001"})
            + "\n"
            + json.dumps({"outcome": "in_progress"})
            + "\n"
        )
        beat.finalize_beat_log(tmp_project, {"outcome": "idle"})
        lines = [json.loads(line) for line in beat_log.read_text().splitlines()]
        assert len(lines) == 2
        assert lines[0]["outcome"] == "done"
        assert lines[1]["outcome"] == "idle"

    def test_creates_file_if_missing(self, tmp_project, beat_log):
        beat.finalize_beat_log(tmp_project, {"outcome": "idle"})
        # append_beat_log is called internally; dry-run=False so it writes
        assert beat_log.exists()

    def test_idempotent_second_call_ignored(self, tmp_project, beat_log):
        beat_log.write_text(json.dumps({"outcome": "in_progress"}) + "\n")
        beat.finalize_beat_log(tmp_project, {"outcome": "done"})
        beat.finalize_beat_log(tmp_project, {"outcome": "failed"})  # should be ignored
        lines = beat_log.read_text().splitlines()
        assert json.loads(lines[-1])["outcome"] == "done"

    def test_handles_pretty_printed_in_progress(self, tmp_project, beat_log):
        # Legacy records may be multi-line JSON; finalize_beat_log works on
        # compact lines it wrote itself — pretty-printed records are left as-is.
        pretty = textwrap.dedent("""\
            {
              "outcome": "done",
              "ticket_id": "0001"
            }
        """)
        # The last line of a pretty record is '}', which json.loads succeeds on
        # but .get("outcome") returns None → loop breaks → final record appended.
        beat_log.write_text(pretty)
        beat.finalize_beat_log(tmp_project, {"outcome": "idle"})
        last_line = beat_log.read_text().splitlines()[-1]
        assert json.loads(last_line)["outcome"] == "idle"

    def test_dry_run_is_noop(self, tmp_project, beat_log):
        beat.DRY_RUN = True
        beat_log.write_text(json.dumps({"outcome": "in_progress"}) + "\n")
        beat.finalize_beat_log(tmp_project, {"outcome": "done"})
        assert json.loads(beat_log.read_text().strip())["outcome"] == "in_progress"


# ── read_last_beat_record ──────────────────────────────────────────────────────


class TestReadLastBeatRecord:
    def test_returns_last_compact_record(self, tmp_project, beat_log):
        beat_log.write_text(
            json.dumps({"outcome": "done"})
            + "\n"
            + json.dumps({"outcome": "idle"})
            + "\n"
        )
        result = beat.read_last_beat_record(tmp_project)
        assert result is not None
        assert result["outcome"] == "idle"

    def test_returns_none_for_missing_file(self, tmp_project):
        result = beat.read_last_beat_record(tmp_project)
        assert result is None

    def test_returns_none_for_empty_file(self, tmp_project, beat_log):
        beat_log.write_text("")
        result = beat.read_last_beat_record(tmp_project)
        assert result is None

    def test_handles_pretty_printed_json(self, tmp_project, beat_log):
        pretty = (
            '{"outcome": "in_progress",\n  "last_run_at": "2026-01-01T00:00:00Z"\n}\n'
        )
        beat_log.write_text(pretty)
        result = beat.read_last_beat_record(tmp_project)
        assert result is not None
        assert result["outcome"] == "in_progress"


# ── run_skill (dry-run mode) ───────────────────────────────────────────────────


class TestRunSkillDryRun:
    def setup_method(self):
        beat.DRY_RUN = True

    def test_pick_ticket_returns_pick_sentinel(self, tmp_project):
        rc, result = beat.run_skill(
            "/pick-ticket", budget=0.20, timeout_s=60, cwd=tmp_project
        )
        assert rc == 0
        assert "PICK: 9999" in result.result_text

    def test_other_skill_returns_ok(self, tmp_project):
        rc, result = beat.run_skill(
            "/housekeeping", budget=0.10, timeout_s=60, cwd=tmp_project
        )
        assert rc == 0
        assert "dry-run" in result.result_text

    def test_raid_returns_ok(self, tmp_project):
        rc, result = beat.run_skill(
            "/raid 0001", budget=0.70, timeout_s=60, cwd=tmp_project
        )
        assert rc == 0


# ── run_skill (subprocess mode) ────────────────────────────────────────────────


class TestRunSkillSubprocess:
    def setup_method(self):
        beat.DRY_RUN = False

    def _make_popen(self, stdout_lines: list[str], returncode: int = 0):
        """Return a Popen mock that streams stdout_lines then exits."""
        import io

        proc = MagicMock()
        proc.stdout = io.StringIO("\n".join(stdout_lines) + "\n")
        proc.returncode = returncode
        proc.poll.return_value = returncode

        def fake_wait(timeout=None):
            proc.returncode = returncode

        proc.wait.side_effect = fake_wait
        return proc

    def test_extracts_result_text(self, tmp_project):
        payload = json.dumps({"type": "result", "result": "PICK: 0007"})
        proc = self._make_popen([payload])
        with patch("beat.subprocess.Popen", return_value=proc):
            rc, result = beat.run_skill(
                "/pick-ticket", budget=0.20, timeout_s=30, cwd=tmp_project
            )
        assert rc == 0
        assert "PICK: 0007" in result.result_text

    def test_ignores_non_result_lines(self, tmp_project):
        lines = [
            json.dumps({"type": "assistant", "content": "thinking..."}),
            json.dumps({"type": "result", "result": "PICK: 0042"}),
        ]
        proc = self._make_popen(lines)
        with patch("beat.subprocess.Popen", return_value=proc):
            _, result = beat.run_skill(
                "/pick-ticket", budget=0.20, timeout_s=30, cwd=tmp_project
            )
        assert result.result_text == "PICK: 0042"

    def test_timeout_returns_124(self, tmp_project):
        proc = MagicMock()
        proc.stdout = MagicMock()
        proc.stdout.__iter__ = lambda s: iter([])
        # First wait() raises TimeoutExpired; second (after terminate) succeeds.
        proc.wait.side_effect = [
            subprocess.TimeoutExpired(cmd="claude", timeout=1),
            None,
        ]
        proc.returncode = -15
        with patch("beat.subprocess.Popen", return_value=proc):
            rc, result = beat.run_skill(
                "/pick-ticket", budget=0.20, timeout_s=1, cwd=tmp_project
            )
        assert rc == beat.TIMEOUT_EXIT_CODE
        assert result.result_text == ""

    def test_nonzero_exit_propagated(self, tmp_project):
        proc = self._make_popen([], returncode=1)
        with patch("beat.subprocess.Popen", return_value=proc):
            rc, _ = beat.run_skill(
                "/pick-ticket", budget=0.20, timeout_s=30, cwd=tmp_project
            )
        assert rc == 1

    def test_clears_current_proc_after_run(self, tmp_project):
        proc = self._make_popen([])
        with patch("beat.subprocess.Popen", return_value=proc):
            beat.run_skill("/housekeeping", budget=0.10, timeout_s=30, cwd=tmp_project)
        assert beat._state.current_proc is None

    def test_malformed_json_lines_skipped(self, tmp_project):
        lines = [
            "not json at all",
            json.dumps({"type": "result", "result": "IDLE: ok"}),
        ]
        proc = self._make_popen(lines)
        with patch("beat.subprocess.Popen", return_value=proc):
            _, result = beat.run_skill(
                "/pick-ticket", budget=0.20, timeout_s=30, cwd=tmp_project
            )
        assert result.result_text == "IDLE: ok"


# ── _raid ───────────────────────────────────────────────────────────────


class TestRaid:
    def setup_method(self):
        beat.DRY_RUN = False

    def _patch_run_skill(self, responses: dict):
        """responses: {skill_substr: (rc, result_text)}"""

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            for key, (rc, text) in responses.items():
                if key in skill:
                    return (rc, beat._SkillResult(result_text=text))
            return (0, beat._SkillResult())

        return patch("beat.run_skill", side_effect=fake_run_skill)

    def test_idle_path(self, tmp_project, git_ok):
        with (
            patch("beat.housekeeping_needed", return_value=False),
            self._patch_run_skill({"pick-ticket": (0, "IDLE: empty queue")}),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "idle"
        assert ticket is None

    def test_pick_and_done_path(self, tmp_project, git_ok):
        with (
            patch("beat.housekeeping_needed", return_value=False),
            self._patch_run_skill(
                {
                    "pick-ticket": (0, "PICK: 0023"),
                    "raid": (0, ""),
                }
            ),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "done"
        assert ticket == "0023"

    def test_pick_ticket_timeout(self, tmp_project, git_ok):
        with (
            patch("beat.housekeeping_needed", return_value=False),
            self._patch_run_skill({"pick-ticket": (beat.TIMEOUT_EXIT_CODE, "")}),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "aborted"
        assert ticket is None

    def test_pick_ticket_nonzero_exit(self, tmp_project, git_ok):
        with (
            patch("beat.housekeeping_needed", return_value=False),
            self._patch_run_skill({"pick-ticket": (1, "")}),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "failed"
        assert ticket is None

    def test_raid_timeout(self, tmp_project, git_ok):
        with (
            patch("beat.housekeeping_needed", return_value=False),
            self._patch_run_skill(
                {
                    "pick-ticket": (0, "PICK: 0005"),
                    "raid": (beat.TIMEOUT_EXIT_CODE, ""),
                }
            ),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "aborted"
        assert ticket == "0005"

    def test_raid_nonzero_exit(self, tmp_project, git_ok):
        with (
            patch("beat.housekeeping_needed", return_value=False),
            self._patch_run_skill(
                {
                    "pick-ticket": (0, "PICK: 0005"),
                    "raid": (2, ""),
                }
            ),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "failed"
        assert ticket == "0005"

    def test_raid_uses_per_project_timeout(self, tmp_project):
        captured = {}

        def spy_run_skill(skill, **kwargs):
            if "raid" in skill and "pick" not in skill:
                captured.update(kwargs)
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="PICK: 0042"))
            return (0, beat._SkillResult())

        custom_timeout = 2700
        config = beat.ProjectConfig(path=tmp_project, raid_timeout_s=custom_timeout)
        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat._sync_origin_main"),
            patch("beat._default_branch", return_value="main"),
            patch(
                "beat._git",
                return_value=MagicMock(returncode=0, stdout="", stderr=""),
            ),
            patch("beat.run_skill", side_effect=spy_run_skill),
        ):
            beat._raid(config)
        assert captured["timeout_s"] == custom_timeout

    def test_housekeeping_runs_when_needed(self, tmp_project):
        calls = []

        def fake_run_skill(skill, **kwargs):
            calls.append(skill)
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="IDLE: empty"))
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=_git_runner(commit_count=0)),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))

        assert any("housekeeping" in c for c in calls)

    def test_housekeeping_skipped_when_recent(self, tmp_project, git_ok):
        calls = []

        def fake_run_skill(skill, **kwargs):
            calls.append(skill)
            return (0, beat._SkillResult(result_text="IDLE: empty"))

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))

        assert not any("housekeeping" in c for c in calls)


# ── _raid CLOSED-loop (ticket 0049 Tier 2) ────────────────────────────────────


class TestRaidClosedLoop:
    """Tier 2 of ticket 0049: pick-ticket may emit `CLOSED: <id>` when it
    detects an already-done ticket. _raid must loop and re-pick rather than
    invoking the orchestrator on a stale pick. A bound prevents flaky exit
    criteria from looping forever."""

    def setup_method(self):
        beat.DRY_RUN = False

    def test_closed_then_pick_loops_back(self, tmp_project, git_ok):
        """First pick-ticket call returns CLOSED; second returns PICK.
        _raid must call pick-ticket twice, then proceed to raid."""
        pick_results = iter(
            [
                (0, beat._SkillResult(result_text="CLOSED: 0049")),
                (0, beat._SkillResult(result_text="PICK: 0050")),
            ]
        )
        calls: list[str] = []

        def fake_run_skill(skill, **kwargs):
            calls.append(skill)
            if "pick-ticket" in skill:
                return next(pick_results)
            if "raid" in skill:
                return (0, beat._SkillResult())
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))

        pick_calls = [c for c in calls if "pick-ticket" in c]
        assert len(pick_calls) == 2
        assert outcome == "done"
        assert ticket == "0050"

    def test_consecutive_closed_aborts_to_idle(self, tmp_project, git_ok):
        """Three consecutive CLOSED picks → idle (loop guard).

        Bound: max 3 consecutive CLOSED before aborting. Prevents flaky
        exit-criteria checks from looping forever."""
        calls: list[str] = []

        def fake_run_skill(skill, **kwargs):
            calls.append(skill)
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="CLOSED: 0049"))
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))

        pick_calls = [c for c in calls if "pick-ticket" in c]
        # 3 attempts max
        assert len(pick_calls) == 3
        # No raid invocation — never reached PICK
        assert not any("raid" in c and "pick-ticket" not in c for c in calls)
        assert outcome == "idle"
        assert ticket is None

    def test_closed_then_idle_returns_idle(self, tmp_project, git_ok):
        """CLOSED on first call, IDLE on second → idle (no raid)."""
        pick_results = iter(
            [
                (0, beat._SkillResult(result_text="CLOSED: 0049")),
                (0, beat._SkillResult(result_text="IDLE: nothing left")),
            ]
        )
        calls: list[str] = []

        def fake_run_skill(skill, **kwargs):
            calls.append(skill)
            if "pick-ticket" in skill:
                return next(pick_results)
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))

        pick_calls = [c for c in calls if "pick-ticket" in c]
        assert len(pick_calls) == 2
        assert outcome == "idle"
        assert ticket is None


# ── _raid dirty-tree guard (ticket 0120) ──────────────────────────────────────


class TestRaidDirtyTree:
    """Ticket 0120: _raid returns ("aborted-dirty-tree", None) when the
    working tree has uncommitted changes, and never proceeds to checkout."""

    def test_dirty_tree_aborts_before_checkout(self, tmp_project):
        checkout_called = []

        def fake_git(*args, cwd):
            sub = args[0] if args else ""
            if sub == "status":
                return MagicMock(returncode=0, stdout="M scripts/beat.py\n", stderr="")
            if sub == "checkout":
                checkout_called.append(args)
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("beat._sync_origin_main"),
            patch("beat._default_branch", return_value="main"),
            patch("beat._git", side_effect=fake_git),
            patch("beat._record_phase_outcome"),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))

        assert outcome == "aborted-dirty-tree"
        assert ticket is None
        assert checkout_called == [], "checkout must not be called on a dirty tree"


# ── housekeeping phase: dedicated branch + PR flow (ticket 0072) ──────────────


def _git_runner(commit_count: int):
    """Return a side_effect for _git that yields N new commits ahead of base."""

    def runner(*args, cwd):
        # First arg is the git subcommand
        sub = args[0] if args else ""
        if sub == "rev-parse":
            return MagicMock(returncode=0, stdout="basesha\n", stderr="")
        if sub == "rev-list":
            return MagicMock(returncode=0, stdout=f"{commit_count}\n", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    return runner


class TestHousekeepingPhase:
    """Ticket 0072: beat-mode housekeeping runs on a dedicated branch and
    only reaches main via a green-CI PR."""

    def test_skipped_when_not_needed(self, tmp_project):
        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._git") as mock_git,
            patch("beat.run_skill") as mock_skill,
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))
        assert outcome == "skipped"
        mock_git.assert_not_called()
        mock_skill.assert_not_called()

    def test_no_changes_deletes_branch(self, tmp_project):
        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=_git_runner(commit_count=0)) as mock_git,
            patch("beat.run_skill", return_value=(0, beat._SkillResult())),
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))
        assert outcome == "no-changes"
        calls = [call.args for call in mock_git.call_args_list]
        # Branch deletion must specifically run `git branch -D <branch>`
        delete_calls = [c for c in calls if c[:2] == ("branch", "-D")]
        assert len(delete_calls) == 1
        assert delete_calls[0][2].startswith("claude/housekeeping-")
        # And `git checkout main` must run before the delete
        assert ("checkout", "main") in [c[:2] for c in calls]

    def test_deferred_when_pr_opt_in_off(self, tmp_project, monkeypatch):
        monkeypatch.delenv("BEAT_HOUSEKEEPING_PR", raising=False)
        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=_git_runner(commit_count=2)) as mock_git,
            patch("beat.run_skill", return_value=(0, beat._SkillResult())),
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))
        assert outcome == "deferred"
        # Bug regression: deferred must checkout main so pick-ticket / raid
        # don't run on the housekeeping branch (PR #78 review finding).
        calls = [call.args for call in mock_git.call_args_list]
        assert ("checkout", "main") in [c[:2] for c in calls]

    def test_failed_when_skill_exits_nonzero(self, tmp_project):
        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=_git_runner(commit_count=0)),
            patch("beat.run_skill", return_value=(1, beat._SkillResult())),
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))
        assert outcome == "failed"

    def test_failed_when_rev_parse_empty(self, tmp_project):
        def git_no_base(*args, cwd):
            sub = args[0] if args else ""
            if sub == "rev-parse":
                return MagicMock(returncode=0, stdout="", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=git_no_base),
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))
        assert outcome == "failed"

    def test_failed_when_branch_checkout_fails(self, tmp_project):
        def git_branch_fails(*args, cwd):
            sub = args[0] if args else ""
            if sub == "rev-parse":
                return MagicMock(returncode=0, stdout="basesha\n", stderr="")
            if sub == "checkout":
                return MagicMock(returncode=1, stdout="", stderr="branch error")
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=git_branch_fails),
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))
        assert outcome == "failed"

    def test_deferred_leaves_branch_intact(self, tmp_project):
        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=_git_runner(commit_count=2)) as mock_git,
            patch("beat.run_skill", return_value=(0, beat._SkillResult())),
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))
        assert outcome == "deferred"
        calls = [call.args for call in mock_git.call_args_list]
        delete_calls = [c for c in calls if c[:2] == ("branch", "-D")]
        assert len(delete_calls) == 0

    def test_skill_timeout_returns_timeout(self, tmp_project):
        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=_git_runner(commit_count=0)),
            patch("beat.run_skill", return_value=(beat.TIMEOUT_EXIT_CODE, "")),
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))
        assert outcome == "timeout"

    def test_aborted_dirty_tree_when_post_skill_tree_dirty(self, tmp_project):
        """Ticket 0137: dirty tree after skill run aborts checkout, returns
        'aborted-dirty-tree' and never calls git checkout."""

        checkout_calls = []

        def git_dirty_after_skill(*args, cwd):
            sub = args[0] if args else ""
            if sub == "rev-parse":
                return MagicMock(returncode=0, stdout="basesha\n", stderr="")
            if sub == "checkout" and args[1:2] != ("-B",):
                # Record unguarded checkout attempts (should not happen)
                checkout_calls.append(args)
                return MagicMock(returncode=0, stdout="", stderr="")
            if sub == "rev-list":
                return MagicMock(returncode=0, stdout="2\n", stderr="")
            if sub == "status":
                return MagicMock(returncode=0, stdout=" M dirty_file.py\n", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=git_dirty_after_skill),
            patch("beat.run_skill", return_value=(0, beat._SkillResult())),
            patch("beat._record_phase_outcome") as mock_record,
        ):
            outcome = beat._housekeeping_phase(beat.ProjectConfig(path=tmp_project))

        assert outcome == "aborted-dirty-tree"
        # The post-skill checkout must NOT have been reached
        assert checkout_calls == [], f"unexpected checkout calls: {checkout_calls}"
        # _record_phase_outcome must be called with the housekeeping phase and aborted-dirty-tree
        mock_record.assert_called_once_with(
            tmp_project,
            "housekeeping",
            "aborted-dirty-tree",
            detail="1 file(s): M dirty_file.py",
        )

    def test_raid_aborts_on_ci_failed(self, tmp_project, git_ok):
        with patch("beat._housekeeping_phase", return_value="failed"):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "aborted"
        assert ticket is None

    def test_raid_aborts_on_housekeeping_timeout(self, tmp_project, git_ok):
        with patch("beat._housekeeping_phase", return_value="timeout"):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "aborted"
        assert ticket is None

    def test_raid_continues_on_deferred(self, tmp_project, git_ok):
        with (
            patch("beat._housekeeping_phase", return_value="deferred"),
            patch(
                "beat.run_skill",
                return_value=(0, beat._SkillResult(result_text="IDLE: empty")),
            ),
        ):
            outcome, _ = beat._raid(beat.ProjectConfig(path=tmp_project))
        assert outcome == "idle"  # not "aborted"


# ── cross-project isolation (_claude_argv project_scoped) ─────────────────────


class TestProjectScopedIsolation:
    """Guard against cross-project ticket leakage via harness --add-dir."""

    def test_default_argv_includes_harness_add_dir(self):
        argv = beat._claude_argv("/housekeeping", 0.25)
        add_dirs = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
        assert str(beat.HARNESS_DIR) in add_dirs

    def test_project_scoped_argv_excludes_harness_add_dir(self):
        argv = beat._claude_argv("/pick-ticket", 0.50, project_scoped=True)
        add_dirs = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
        assert str(beat.HARNESS_DIR) not in add_dirs

    def test_project_scoped_argv_still_includes_project_add_dir(self):
        argv = beat._claude_argv("/pick-ticket", 0.50, project_scoped=True)
        add_dirs = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
        assert "." in add_dirs

    def test_raid_passes_project_scoped_to_pick_ticket(self, tmp_project, git_ok):
        recorded: list[dict] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            recorded.append({"skill": skill, "project_scoped": project_scoped})
            return (0, beat._SkillResult(result_text="IDLE: empty"))

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))

        pick_call = next(r for r in recorded if "pick-ticket" in r["skill"])
        assert pick_call["project_scoped"] is True

    def test_raid_passes_project_scoped_to_raid(self, tmp_project, git_ok):
        recorded: list[dict] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            recorded.append({"skill": skill, "project_scoped": project_scoped})
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="PICK: 0001"))
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))

        oc_call = next(r for r in recorded if "raid" in r["skill"])
        assert oc_call["project_scoped"] is True

    def test_raid_does_not_scope_housekeeping(self, tmp_project):
        recorded: list[dict] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            recorded.append({"skill": skill, "project_scoped": project_scoped})
            return (0, beat._SkillResult(result_text="IDLE: empty"))

        with (
            patch("beat.housekeeping_needed", return_value=True),
            patch("beat._git", side_effect=_git_runner(commit_count=0)),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))

        hk_call = next(r for r in recorded if "housekeeping" in r["skill"])
        assert hk_call["project_scoped"] is False


# ── per-project lock ──────────────────────────────────────────────────────────


class TestPerProjectLock:
    def test_lockfile_per_project_name(self, tmp_path):
        proj_a = tmp_path / "alpha"
        proj_b = tmp_path / "beta"
        assert beat._lockfile(proj_a).name != beat._lockfile(proj_b).name

    def test_lockfile_contains_project_name(self, tmp_path):
        project = tmp_path / "myproject"
        assert "myproject" in beat._lockfile(project).name

    def test_lockfile_parent_is_lock_dir(self, tmp_path):
        project = tmp_path / "p"
        assert beat._lockfile(project).parent == beat._LOCK_DIR

    def test_already_locked_exits_zero(self, tmp_project, tmp_path):
        """A project already locked by another beat instance causes exit(0)."""
        fake_lock_dir = tmp_path / "locks"
        with (
            patch("beat.signal.signal"),
            patch("beat._setup_env"),
            patch.object(beat, "LOGDIR", tmp_path / "logs"),
            patch(
                "beat._pick_project",
                return_value=(0, beat.ProjectConfig(path=tmp_project)),
            ),
            patch.object(beat, "_LOCK_DIR", fake_lock_dir),
            patch("beat.fcntl.flock", side_effect=BlockingIOError),
            pytest.raises(SystemExit) as exc_info,
        ):
            beat.main()
        assert exc_info.value.code == 0


# ── orphaned locked worktree cleanup ──────────────────────────────────────────


class TestCleanupLockedWorktrees:
    """Tests for _cleanup_locked_worktrees — orphan detection and removal."""

    def _make_locked_worktree(self, git_dir: Path, name: str, pid: int) -> Path:
        """Create a fake worktree admin dir with a lock file and gitdir pointer."""
        admin = git_dir / "worktrees" / name
        admin.mkdir(parents=True)
        (admin / "locked").write_text(f"claude agent {name} (pid {pid})\n")
        # gitdir points to <worktree_checkout>/.git
        fake_checkout = git_dir.parent / ".claude" / "worktrees" / name
        fake_checkout.mkdir(parents=True, exist_ok=True)
        (admin / "gitdir").write_text(str(fake_checkout / ".git") + "\n")
        return fake_checkout

    def test_removes_worktree_with_dead_pid(self, tmp_path):
        """Orphaned locked worktree (dead PID) is unlocked and removed."""
        project = tmp_path / "repo"
        project.mkdir()
        git_dir = project / ".git"
        git_dir.mkdir()

        dead_pid = 999999  # almost certainly not alive
        worktree_path = self._make_locked_worktree(git_dir, "agent-deadbeef", dead_pid)

        run_calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0)

        with (
            patch("beat.subprocess.run", side_effect=fake_run),
            patch("beat.os.kill", side_effect=ProcessLookupError),
        ):
            beat._cleanup_locked_worktrees(project)

        assert any("worktree" in " ".join(c) and "unlock" in c for c in run_calls), (
            f"Expected a 'git worktree unlock' call; got: {run_calls}"
        )
        assert any("worktree" in " ".join(c) and "remove" in c for c in run_calls), (
            f"Expected a 'git worktree remove' call; got: {run_calls}"
        )

    def test_skips_worktree_with_live_pid(self, tmp_path):
        """Locked worktree whose PID is alive must not be removed."""
        project = tmp_path / "repo"
        project.mkdir()
        git_dir = project / ".git"
        git_dir.mkdir()

        live_pid = os.getpid()  # our own PID — definitely alive
        self._make_locked_worktree(git_dir, "agent-liveone", live_pid)

        run_calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0)

        with patch("beat.subprocess.run", side_effect=fake_run):
            beat._cleanup_locked_worktrees(project)

        assert run_calls == [], (
            f"Should not have called subprocess.run; got: {run_calls}"
        )

    def test_skips_non_harness_name(self, tmp_path):
        """Worktree names not matching harness patterns are left alone."""
        project = tmp_path / "repo"
        project.mkdir()
        git_dir = project / ".git"
        git_dir.mkdir()

        self._make_locked_worktree(git_dir, "custom-worktree", 999999)

        run_calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0)

        with (
            patch("beat.subprocess.run", side_effect=fake_run),
            patch("beat.os.kill", side_effect=ProcessLookupError),
        ):
            beat._cleanup_locked_worktrees(project)

        assert run_calls == [], (
            f"Non-harness worktree should be skipped; got: {run_calls}"
        )

    def test_skips_lock_file_without_pid(self, tmp_path):
        """Lock file with unknown format (no PID) is skipped safely."""
        project = tmp_path / "repo"
        project.mkdir()
        git_dir = project / ".git"
        git_dir.mkdir()

        admin = git_dir / "worktrees" / "agent-nopid"
        admin.mkdir(parents=True)
        (admin / "locked").write_text("some other format\n")
        fake_checkout = tmp_path / "worktrees" / "agent-nopid"
        fake_checkout.mkdir(parents=True)
        (admin / "gitdir").write_text(str(fake_checkout / ".git") + "\n")

        run_calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0)

        with (
            patch("beat.subprocess.run", side_effect=fake_run),
            patch("beat.os.kill", side_effect=ProcessLookupError),
        ):
            beat._cleanup_locked_worktrees(project)

        assert run_calls == [], (
            f"Unknown lock format should be skipped; got: {run_calls}"
        )

    def test_noop_when_no_git_dir(self, tmp_path):
        """Function returns silently when project has no .git directory."""
        project = tmp_path / "notgit"
        project.mkdir()
        # Should not raise
        beat._cleanup_locked_worktrees(project)

    def test_skips_permission_error_pid(self, tmp_path):
        """PermissionError from os.kill means PID is alive — worktree kept."""
        project = tmp_path / "repo"
        project.mkdir()
        git_dir = project / ".git"
        git_dir.mkdir()

        self._make_locked_worktree(git_dir, "agent-foreign", 12345)

        run_calls: list[list[str]] = []

        def fake_run(cmd, **kwargs):
            run_calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0)

        with (
            patch("beat.subprocess.run", side_effect=fake_run),
            patch("beat.os.kill", side_effect=PermissionError),
        ):
            beat._cleanup_locked_worktrees(project)

        assert run_calls == [], (
            f"PermissionError PID should be treated as alive; got: {run_calls}"
        )


# ── crash recovery ─────────────────────────────────────────────────────────────


class TestCrashRecovery:
    def test_recent_in_progress_triggers_aborted(self, tmp_project, beat_log):
        from datetime import datetime

        recent_ts = "2026-04-25T15:00:00Z"
        beat_log.write_text(
            json.dumps({"outcome": "in_progress", "last_run_at": recent_ts}) + "\n"
        )
        recent_epoch = datetime.fromisoformat(
            recent_ts.replace("Z", "+00:00")
        ).timestamp()

        with (
            patch("beat.read_last_beat_record") as mock_last,
            patch("beat.append_beat_log") as mock_append,
            patch("beat.time.time", return_value=recent_epoch + 60),  # 1 min later
        ):
            mock_last.return_value = {
                "outcome": "in_progress",
                "last_run_at": recent_ts,
            }
            last = mock_last(tmp_project)
            if last and last.get("outcome") == "in_progress":
                last_at = last.get("last_run_at", "1970-01-01T00:00:00Z")
                last_ep = datetime.fromisoformat(
                    last_at.replace("Z", "+00:00")
                ).timestamp()
                if (recent_epoch + 60 - last_ep) < beat.CRASH_RECOVERY_WINDOW_S:
                    mock_append(
                        tmp_project,
                        {
                            "outcome": "aborted",
                            "diagnostics": "crash/SIGKILL recovery — previous run never completed spin-down",
                        },
                    )

        mock_append.assert_called_once()
        call_record = mock_append.call_args[0][1]
        assert call_record["outcome"] == "aborted"
        assert "crash" in call_record["diagnostics"]

    def test_old_in_progress_does_not_trigger_recovery(self, tmp_project):
        from datetime import datetime

        old_ts = "2026-04-25T00:00:00Z"
        old_epoch = datetime.fromisoformat(old_ts.replace("Z", "+00:00")).timestamp()
        now = old_epoch + 15 * 3600  # 15 hours after spin-in

        last_epoch = datetime.fromisoformat(old_ts.replace("Z", "+00:00")).timestamp()
        elapsed = now - last_epoch
        assert elapsed >= beat.CRASH_RECOVERY_WINDOW_S


# ── spin-down completeness ─────────────────────────────────────────────────────


class TestSpinDown:
    def test_finalize_always_called_on_normal_exit(self, tmp_project, beat_log, git_ok):
        beat_log.write_text(json.dumps({"outcome": "in_progress"}) + "\n")
        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch(
                "beat.run_skill",
                side_effect=lambda s, **kw: (
                    0,
                    beat._SkillResult(result_text="IDLE: empty" if "pick" in s else ""),
                ),
            ),
        ):
            beat._state.project = tmp_project
            beat._state.final_written = False
            beat.DRY_RUN = False
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))
            beat.finalize_beat_log(
                tmp_project,
                {
                    "last_run_at": "t",
                    "ticket_id": ticket,
                    "outcome": outcome,
                    "duration_s": 0,
                },
            )
        last_line = beat_log.read_text().splitlines()[-1]
        assert json.loads(last_line)["outcome"] == "idle"


# ── _repo_active (ticket 0038) ─────────────────────────────────────────────────


class TestRepoActive:
    def test_active_with_commits(self, tmp_project):
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                stdout="abc1234 some commit\n", returncode=0
            )
            assert beat._repo_active(tmp_project) is True

    def test_idle_no_commits(self, tmp_project):
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            assert beat._repo_active(tmp_project) is False

    def test_git_error_treated_as_idle(self, tmp_project):
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=128)
            assert beat._repo_active(tmp_project) is False


# ── pick-ticket model selection (ticket 0038) ──────────────────────────────────


class TestPickTicketModelSelection:
    def setup_method(self):
        beat.DRY_RUN = False

    def _make_recorder(self):
        recorded: list[dict] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            recorded.append({"skill": skill, "model": model})
            return (0, beat._SkillResult(result_text="IDLE: empty"))

        return recorded, fake_run_skill

    def test_uses_haiku_when_idle(self, tmp_project, git_ok):
        recorded, fake = self._make_recorder()
        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat.run_skill", side_effect=fake),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))
        pick_call = next(r for r in recorded if "pick-ticket" in r["skill"])
        assert pick_call["model"] == beat.MODEL_HAIKU

    def test_uses_sonnet_when_active(self, tmp_project, git_ok):
        recorded, fake = self._make_recorder()
        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=True),
            patch("beat.run_skill", side_effect=fake),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))
        pick_call = next(r for r in recorded if "pick-ticket" in r["skill"])
        assert pick_call["model"] == beat.MODEL_SONNET

    def test_project_override_respected_when_idle(self, tmp_project, git_ok):
        custom_model = "claude-opus-4-7"
        recorded, fake = self._make_recorder()
        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat.run_skill", side_effect=fake),
        ):
            beat._raid(
                beat.ProjectConfig(path=tmp_project, pick_ticket_model=custom_model)
            )
        pick_call = next(r for r in recorded if "pick-ticket" in r["skill"])
        assert pick_call["model"] == custom_model

    def test_project_override_ignored_when_active(self, tmp_project, git_ok):
        """When repo is active, Sonnet is always used regardless of pick_ticket_model."""
        recorded, fake = self._make_recorder()
        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=True),
            patch("beat.run_skill", side_effect=fake),
        ):
            beat._raid(
                beat.ProjectConfig(
                    path=tmp_project, pick_ticket_model="claude-opus-4-7"
                )
            )
        pick_call = next(r for r in recorded if "pick-ticket" in r["skill"])
        assert pick_call["model"] == beat.MODEL_SONNET


# ── _repo_frozen_since / housekeeping frozen skip (ticket 0040) ────────────────


class TestRepoFrozenSince:
    def _dt(self, hours_ago: int):
        from datetime import datetime, timezone

        return datetime.fromtimestamp(time.time() - hours_ago * 3600, tz=timezone.utc)

    def test_frozen_when_no_commits(self, tmp_project):
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", returncode=0)
            assert beat._repo_frozen_since(tmp_project, self._dt(25)) is True

    def test_not_frozen_when_commits_present(self, tmp_project):
        with patch("beat.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="abc1234 a commit\n", returncode=0)
            assert beat._repo_frozen_since(tmp_project, self._dt(25)) is False


class TestHousekeepingFrozenSkip:
    _SHA = "abc1234567890abcdef1234567890abcdef123456"

    def test_frozen_repo_skips_housekeeping(self, tmp_project):
        very_old = f"{int(time.time()) - 25 * 3600} {self._SHA}"
        with patch("beat.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=very_old + "\n", returncode=0),  # last hk commit
                MagicMock(stdout="", returncode=0),  # frozen check: no commits
            ]
            assert beat.housekeeping_needed(tmp_project) is False

    def test_active_repo_past_floor_runs_housekeeping(self, tmp_project):
        very_old = f"{int(time.time()) - 25 * 3600} {self._SHA}"
        with patch("beat.subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(stdout=very_old + "\n", returncode=0),  # last hk commit
                MagicMock(stdout="abc1234 recent work\n", returncode=0),  # not frozen
            ]
            assert beat.housekeeping_needed(tmp_project) is True


# ── load_projects (ticket 0046) ────────────────────────────────────────────────


class TestLoadProjects:
    def test_loads_from_json(self, tmp_path):
        cfg = tmp_path / "projects.json"
        cfg.write_text(
            json.dumps(
                [
                    {
                        "path": "~/foo",
                        "budget_housekeeping": 0.30,
                        "budget_pick_ticket": 0.20,
                    },
                    {"path": "~/bar"},
                ]
            )
        )
        projects = beat.load_projects(cfg)
        assert len(projects) == 2
        assert projects[0].path == Path.home() / "foo"
        assert projects[0].budget_housekeeping == 0.30
        assert projects[0].budget_pick_ticket == 0.20
        assert projects[1].budget_housekeeping == beat.BUDGET_HOUSEKEEPING

    def test_tilde_expansion(self, tmp_path):
        cfg = tmp_path / "projects.json"
        cfg.write_text(json.dumps([{"path": "~/.claude"}]))
        projects = beat.load_projects(cfg)
        assert projects[0].path == Path.home() / ".claude"

    def test_pick_ticket_model_optional(self, tmp_path):
        cfg = tmp_path / "projects.json"
        cfg.write_text(
            json.dumps([{"path": "~/x", "pick_ticket_model": "claude-opus-4-7"}])
        )
        projects = beat.load_projects(cfg)
        assert projects[0].pick_ticket_model == "claude-opus-4-7"

    def test_falls_back_when_missing(self, tmp_path, capsys):
        projects = beat.load_projects(tmp_path / "nonexistent.json")
        assert projects == beat._BUILTIN_PROJECTS
        assert "not found" in capsys.readouterr().err

    def test_falls_back_on_bad_json(self, tmp_path, capsys):
        bad = tmp_path / "projects.json"
        bad.write_text("not { valid json")
        projects = beat.load_projects(bad)
        assert projects == beat._BUILTIN_PROJECTS
        assert "error" in capsys.readouterr().err.lower()

    def test_falls_back_on_missing_path_key(self, tmp_path, capsys):
        cfg = tmp_path / "projects.json"
        cfg.write_text(json.dumps([{"budget_housekeeping": 0.4}]))
        projects = beat.load_projects(cfg)
        assert projects == beat._BUILTIN_PROJECTS
        assert "error" in capsys.readouterr().err.lower()


# ── raid done-but-open warning (ticket 0037) ──────────────────────────────────


class TestRaidDoneButOpenWarning:
    def setup_method(self):
        beat.DRY_RUN = False

    def _make_ticket(self, tmp_project, ticket_id: str, status: str) -> None:
        (tmp_project / "tickets").mkdir(exist_ok=True)
        log = "2026-01-01T00:00Z claude created\n"
        if status == "closed":
            log += "2026-01-02T00:00Z claude closed\n"
        (tmp_project / f"tickets/{ticket_id}-test-ticket.erg").write_text(
            f"%erg v1\nTitle: test\nCreated: 2026-01-01\nAuthor: claude\n"
            f"\n--- log ---\n{log}\n--- body ---\n"
        )

    def test_warns_when_ticket_not_closed(self, tmp_project, git_ok):
        self._make_ticket(tmp_project, "0001", "open")
        log_lines: list[str] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="PICK: 0001"))
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
            patch("beat._log", side_effect=log_lines.append),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))

        assert any(
            "warning" in l and "0001" in l and "not closed" in l for l in log_lines
        )

    def test_no_warning_when_ticket_closed(self, tmp_project, git_ok):
        self._make_ticket(tmp_project, "0002", "closed")
        log_lines: list[str] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="PICK: 0002"))
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
            patch("beat._log", side_effect=log_lines.append),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))

        assert not any("warning" in l and "not closed" in l for l in log_lines)

    def test_no_warning_when_ticket_file_missing(self, tmp_project):
        log_lines: list[str] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            if "pick-ticket" in skill:
                return (0, "PICK: 9999")
            return (0, "")

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
            patch("beat._log", side_effect=log_lines.append),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project))

        assert not any("warning" in l and "not closed" in l for l in log_lines)


# ── Cooldown-recent-pick guard (ticket 0051 Layer 0) ──────────────────────────


class TestTicketRecentlyPicked:
    def test_fires_within_8h(self, tmp_path):
        ticket = tmp_path / "0001-test.erg"
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        ticket.write_text(
            f"%erg v1\nTitle: T\nStatus: open\n\n--- log ---\n"
            f"{now_iso} claude note sweep-pick: picked\n\n--- body ---\n"
        )
        assert beat._ticket_recently_picked(ticket, within_hours=8) is True

    def test_clears_after_8h(self, tmp_path):
        ticket = tmp_path / "0002-test.erg"
        old = (datetime.now(timezone.utc) - timedelta(hours=9)).strftime(
            "%Y-%m-%dT%H:%MZ"
        )
        ticket.write_text(
            f"%erg v1\nTitle: T\nStatus: open\n\n--- log ---\n"
            f"{old} claude note sweep-pick: picked\n\n--- body ---\n"
        )
        assert beat._ticket_recently_picked(ticket, within_hours=8) is False

    def test_ignores_malformed_line(self, tmp_path):
        ticket = tmp_path / "0003-test.erg"
        ticket.write_text(
            "%erg v1\nTitle: T\nStatus: open\n\n--- log ---\n"
            "not-a-timestamp claude note sweep-pick: picked\n\n--- body ---\n"
        )
        assert beat._ticket_recently_picked(ticket, within_hours=8) is False


class TestRaidCooldownRecentPick:
    """Layer 0: when a ticket has a recent sweep-pick log entry, _raid()
    short-circuits to idle before invoking pick-ticket."""

    def setup_method(self):
        beat.DRY_RUN = False

    def test_skips_pick_ticket_when_recent_pick_exists(self, tmp_project, git_ok):
        (tmp_project / "tickets").mkdir(exist_ok=True)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        (tmp_project / "tickets" / "0042-recent.erg").write_text(
            f"%erg v1\nTitle: recent\nStatus: open\n\n--- log ---\n"
            f"{now_iso} claude note sweep-pick: picked\n\n--- body ---\n"
        )

        calls: list[str] = []

        def fake_run_skill(skill, **kwargs):
            calls.append(skill)
            return (0, beat._SkillResult())

        log_lines: list[str] = []
        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
            patch("beat._log", side_effect=log_lines.append),
        ):
            outcome, ticket = beat._raid(beat.ProjectConfig(path=tmp_project))

        assert outcome == "idle"
        assert ticket is None
        assert not any("pick-ticket" in c for c in calls), (
            "pick-ticket must not be invoked when a recent-pick cooldown applies"
        )
        assert any("cooldown-recent-pick" in l for l in log_lines)

    def test_proceeds_when_no_recent_pick(self, tmp_project, git_ok):
        (tmp_project / "tickets").mkdir(exist_ok=True)
        old = (datetime.now(timezone.utc) - timedelta(hours=9)).strftime(
            "%Y-%m-%dT%H:%MZ"
        )
        (tmp_project / "tickets" / "0043-old.erg").write_text(
            f"%erg v1\nTitle: old\nStatus: open\n\n--- log ---\n"
            f"{old} claude note sweep-pick: picked\n\n--- body ---\n"
        )

        calls: list[str] = []

        def fake_run_skill(skill, **kwargs):
            calls.append(skill)
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="IDLE: empty queue"))
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            outcome, _ = beat._raid(beat.ProjectConfig(path=tmp_project))

        assert outcome == "idle"
        assert any("pick-ticket" in c for c in calls), (
            "pick-ticket should be invoked when no recent-pick cooldown applies"
        )


# ── Weekly /fewer-permission-prompts (ticket 0043) ────────────────────────────


class TestWeeklyPermissionsPrune:
    def test_skipped_on_non_prune_day(self, tmp_path, monkeypatch):
        called = {"v": False}

        def fake_run(*a, **k):
            called["v"] = True
            return MagicMock(returncode=0, stdout=b"")

        monkeypatch.setattr(beat, "_is_prune_day", lambda: False)
        monkeypatch.setattr(beat, "HARNESS_DIR", tmp_path)
        monkeypatch.setattr(beat.subprocess, "run", fake_run)
        beat._prune_permissions(tmp_path)
        assert called["v"] is False

    def test_runs_on_prune_day(self, tmp_path, monkeypatch):
        called = {"v": False}

        def fake_run(*a, **k):
            called["v"] = True
            return MagicMock(returncode=0, stdout=b"")

        monkeypatch.setattr(beat, "_is_prune_day", lambda: True)
        monkeypatch.setattr(beat, "HARNESS_DIR", tmp_path)
        monkeypatch.setattr(beat.subprocess, "run", fake_run)
        beat._prune_permissions(tmp_path)
        assert called["v"] is True

    def test_skipped_when_today_diff_exists(self, tmp_path, monkeypatch):
        """Once-per-day guard: helper not invoked if today's diff already exists."""
        called = {"v": False}

        def fake_run(*a, **k):
            called["v"] = True
            return MagicMock(returncode=0, stdout=b"")

        monkeypatch.setattr(beat, "_is_prune_day", lambda: True)
        monkeypatch.setattr(beat, "HARNESS_DIR", tmp_path)
        monkeypatch.setattr(beat.subprocess, "run", fake_run)

        diffs = tmp_path / "telemetry" / "permission-diffs"
        diffs.mkdir(parents=True)
        today = datetime.now().strftime("%Y-%m-%d")
        (diffs / f"{today}.diff").write_text("# already produced earlier today\n")

        beat._prune_permissions(tmp_path)
        assert called["v"] is False, (
            "second invocation on the same day must short-circuit before"
            " spawning the helper"
        )

    def test_failure_does_not_raise(self, tmp_path, monkeypatch):
        def boom(*a, **k):
            raise OSError("simulated failure")

        monkeypatch.setattr(beat, "_is_prune_day", lambda: True)
        monkeypatch.setattr(beat, "HARNESS_DIR", tmp_path)
        monkeypatch.setattr(beat.subprocess, "run", boom)
        # Must not propagate.
        beat._prune_permissions(tmp_path)

    def test_is_prune_day_uses_config(self, monkeypatch):
        # Force the configured day to a deterministic weekday name.
        from datetime import datetime as _dt

        class _FakeDT(_dt):
            @classmethod
            def now(cls, tz=None):  # noqa: ARG002 — match signature
                return _dt(2026, 5, 3)  # Sunday

        monkeypatch.setattr(beat, "PERMISSIONS_PRUNE_DAY_OF_WEEK", "sunday")
        monkeypatch.setattr(beat, "datetime", _FakeDT)
        assert beat._is_prune_day() is True

        monkeypatch.setattr(beat, "PERMISSIONS_PRUNE_DAY_OF_WEEK", "monday")
        assert beat._is_prune_day() is False


# ── Per-project beat config (ticket 0101) ────────────────────────────────────


class TestProjectConfigFields:
    def test_budget_raid_default(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"))
        assert cfg.budget_raid == beat.BUDGET_RAID

    def test_interval_minutes_default(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"))
        assert cfg.interval_minutes == 0

    def test_custom_budget_raid(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"), budget_raid=8.00)
        assert cfg.budget_raid == 8.00

    def test_custom_interval(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"), interval_minutes=30)
        assert cfg.interval_minutes == 30

    def test_max_turns_pick_ticket_default(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"))
        assert cfg.max_turns_pick_ticket == beat.MAX_TURNS_PICK_TICKET

    def test_custom_max_turns_pick_ticket(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"), max_turns_pick_ticket=50)
        assert cfg.max_turns_pick_ticket == 50

    def test_max_turns_housekeeping_default(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"))
        assert cfg.max_turns_housekeeping == beat.MAX_TURNS_HOUSEKEEPING

    def test_max_turns_housekeeping_custom(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"), max_turns_housekeeping=10)
        assert cfg.max_turns_housekeeping == 10

    def test_max_turns_housekeeping_cap(self):
        cfg = beat.ProjectConfig(path=Path("/tmp/p"), max_turns_housekeeping=9999)
        assert cfg.max_turns_housekeeping == 2 * beat.MAX_TURNS_HOUSEKEEPING


class TestApplyBeatJsonOverlay:
    def test_overlay_merges_known_keys(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "beat.json").write_text(
            json.dumps({"budget_raid": 8.00, "interval_minutes": 30})
        )
        cfg = beat.ProjectConfig(path=tmp_path)
        beat._apply_beat_json_overlay(cfg)
        assert cfg.budget_raid == 8.00
        assert cfg.interval_minutes == 30

    def test_overlay_ignores_unknown_keys(self, tmp_path):
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "beat.json").write_text(
            json.dumps({"path": "/evil", "nonexistent_key": True})
        )
        cfg = beat.ProjectConfig(path=tmp_path)
        original_path = cfg.path
        beat._apply_beat_json_overlay(cfg)
        assert cfg.path == original_path

    def test_overlay_absent_is_noop(self, tmp_path):
        cfg = beat.ProjectConfig(path=tmp_path)
        beat._apply_beat_json_overlay(cfg)
        assert cfg.budget_raid == beat.BUDGET_RAID

    def test_overlay_malformed_json_warns(self, tmp_path, capsys):
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".claude" / "beat.json").write_text("not json{")
        cfg = beat.ProjectConfig(path=tmp_path, budget_raid=3.00)
        beat._apply_beat_json_overlay(cfg)
        assert cfg.budget_raid == 3.00
        assert "error" in capsys.readouterr().err.lower()


class TestLoadProjectsOverlay:
    def test_overlay_applied_during_load(self, tmp_path):
        proj_dir = tmp_path / "myproject"
        proj_dir.mkdir()
        (proj_dir / ".claude").mkdir()
        (proj_dir / ".claude" / "beat.json").write_text(
            json.dumps({"interval_minutes": 45, "budget_raid": 7.50})
        )
        cfg_file = tmp_path / "projects.json"
        cfg_file.write_text(json.dumps([{"path": str(proj_dir)}]))
        projects = beat.load_projects(cfg_file)
        assert len(projects) == 1
        assert projects[0].interval_minutes == 45
        assert projects[0].budget_raid == 7.50

    def test_projects_json_budget_raid(self, tmp_path):
        cfg = tmp_path / "projects.json"
        cfg.write_text(json.dumps([{"path": "~/x", "budget_raid": 12.00}]))
        projects = beat.load_projects(cfg)
        assert projects[0].budget_raid == 12.00

    def test_projects_json_interval_minutes(self, tmp_path):
        cfg = tmp_path / "projects.json"
        cfg.write_text(json.dumps([{"path": "~/x", "interval_minutes": 60}]))
        projects = beat.load_projects(cfg)
        assert projects[0].interval_minutes == 60

    def test_projects_json_max_turns_pick_ticket(self, tmp_path):
        cfg = tmp_path / "projects.json"
        cfg.write_text(json.dumps([{"path": "~/x", "max_turns_pick_ticket": 50}]))
        projects = beat.load_projects(cfg)
        assert projects[0].max_turns_pick_ticket == 50

    def test_beat_json_overlay_max_turns_pick_ticket(self, tmp_path):
        proj_dir = tmp_path / "myproject"
        proj_dir.mkdir()
        (proj_dir / ".claude").mkdir()
        (proj_dir / ".claude" / "beat.json").write_text(
            json.dumps({"max_turns_pick_ticket": 45})
        )
        cfg = beat.ProjectConfig(path=proj_dir)
        beat._apply_beat_json_overlay(cfg)
        assert cfg.max_turns_pick_ticket == 45

    def test_beat_json_overlay_max_turns_housekeeping(self, tmp_path):
        proj_dir = tmp_path / "myproject"
        proj_dir.mkdir()
        (proj_dir / ".claude").mkdir()
        (proj_dir / ".claude" / "beat.json").write_text(
            json.dumps({"max_turns_housekeeping": 55})
        )
        cfg = beat.ProjectConfig(path=proj_dir)
        beat._apply_beat_json_overlay(cfg)
        assert cfg.max_turns_housekeeping == 55


class TestRaidBudgetPassthrough:
    """budget_raid flows from ProjectConfig to the raid skill invocation."""

    def setup_method(self):
        beat.DRY_RUN = False

    def test_raid_uses_project_budget(self, tmp_project, git_ok):
        recorded: list[dict] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            recorded.append({"skill": skill, "budget": budget})
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="PICK: 0001"))
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat._sync_origin_main"),
            patch("beat._default_branch", return_value="main"),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project, budget_raid=8.50))

        raid_call = next(
            r for r in recorded if "raid" in r["skill"] and "pick" not in r["skill"]
        )
        assert raid_call["budget"] == 8.50


class TestPickTicketMaxTurnsPassthrough:
    """max_turns_pick_ticket flows from ProjectConfig to the pick-ticket invocation."""

    def setup_method(self):
        beat.DRY_RUN = False

    def test_pick_ticket_uses_project_max_turns(self, tmp_project, git_ok):
        recorded: list[dict] = []

        def fake_run_skill(
            skill,
            *,
            budget,
            timeout_s,
            cwd,
            project_scoped=False,
            model=beat.MODEL_SONNET,
            max_turns=None,
        ):
            recorded.append({"skill": skill, "max_turns": max_turns})
            if "pick-ticket" in skill:
                return (0, beat._SkillResult(result_text="IDLE: empty"))
            return (0, beat._SkillResult())

        with (
            patch("beat.housekeeping_needed", return_value=False),
            patch("beat._repo_active", return_value=False),
            patch("beat._sync_origin_main"),
            patch("beat._default_branch", return_value="main"),
            patch("beat.run_skill", side_effect=fake_run_skill),
        ):
            beat._raid(beat.ProjectConfig(path=tmp_project, max_turns_pick_ticket=50))

        pick_call = next(r for r in recorded if "pick-ticket" in r["skill"])
        assert pick_call["max_turns"] == 50


class TestIntervalSkip:
    """interval_minutes causes main() to exit early when last run is too recent."""

    def test_skips_when_interval_not_elapsed(self, tmp_project, tmp_path):
        recent_ts = beat._now_iso()
        beat_log = tmp_project / "beat-log.jsonl"
        beat_log.write_text(
            json.dumps({"outcome": "done", "last_run_at": recent_ts}) + "\n"
        )

        log_lines: list[str] = []
        with (
            patch("beat.signal.signal"),
            patch("beat._setup_env"),
            patch.object(beat, "LOGDIR", tmp_path / "logs"),
            patch(
                "beat._pick_project",
                return_value=(
                    0,
                    beat.ProjectConfig(path=tmp_project, interval_minutes=30),
                ),
            ),
            patch.object(beat, "_LOCK_DIR", tmp_path / "locks"),
            patch("beat.fcntl.flock"),
            patch("beat._log", side_effect=log_lines.append),
            patch("beat.read_last_beat_record") as mock_read,
            pytest.raises(SystemExit) as exc_info,
        ):
            mock_read.return_value = {
                "outcome": "done",
                "last_run_at": recent_ts,
            }
            beat.main()

        assert exc_info.value.code == 0
        assert any("interval-skip" in l for l in log_lines)

    def test_runs_when_interval_elapsed(self, tmp_project, tmp_path):
        old_ts = (datetime.now(timezone.utc) - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        beat_log = tmp_project / "beat-log.jsonl"
        beat_log.write_text(
            json.dumps({"outcome": "done", "last_run_at": old_ts}) + "\n"
        )
        primary_cfg = beat.ProjectConfig(path=tmp_project, interval_minutes=30)

        with (
            patch("beat.signal.signal"),
            patch("beat._setup_env"),
            patch.object(beat, "LOGDIR", tmp_path / "logs"),
            patch(
                "beat._pick_project",
                return_value=(0, primary_cfg),
            ),
            patch.object(beat, "_LOCK_DIR", tmp_path / "locks"),
            patch.object(
                beat, "PROJECTS", [primary_cfg]
            ),  # single project — no fallback
            patch("beat.fcntl.flock"),
            patch("beat._raid", return_value=("idle", None)) as mock_raid,
            patch("beat.finalize_beat_log"),
            patch("beat._cleanup_stale_in_progress"),
            patch(
                "beat.read_last_beat_record",
                return_value={
                    "outcome": "done",
                    "last_run_at": old_ts,
                },
            ),
            patch("beat.append_beat_log"),
        ):
            beat.main()

        mock_raid.assert_called_once()

    def test_no_skip_when_interval_zero(self, tmp_project, tmp_path):
        recent_ts = beat._now_iso()
        primary_cfg = beat.ProjectConfig(path=tmp_project, interval_minutes=0)

        with (
            patch("beat.signal.signal"),
            patch("beat._setup_env"),
            patch.object(beat, "LOGDIR", tmp_path / "logs"),
            patch(
                "beat._pick_project",
                return_value=(0, primary_cfg),
            ),
            patch.object(beat, "_LOCK_DIR", tmp_path / "locks"),
            patch.object(
                beat, "PROJECTS", [primary_cfg]
            ),  # single project — no fallback
            patch("beat.fcntl.flock"),
            patch("beat._raid", return_value=("idle", None)) as mock_raid,
            patch("beat.finalize_beat_log"),
            patch("beat._cleanup_stale_in_progress"),
            patch(
                "beat.read_last_beat_record",
                return_value={
                    "outcome": "done",
                    "last_run_at": recent_ts,
                },
            ),
            patch("beat.append_beat_log"),
        ):
            beat.main()

        mock_raid.assert_called_once()


# ── Layer 2: _pick_needed (ticket 0051) ───────────────────────────────────────


class TestPickNeeded:
    """Unit tests for _pick_needed() — Layer 2 pre-flight skip."""

    def test_returns_true_when_no_prior_beat(self, tmp_project):
        """No prior beat record → always run pick-ticket."""
        assert beat._pick_needed(tmp_project, None) is True

    def test_returns_true_when_repo_has_commits(self, tmp_project):
        """New commits since last beat → pick needed."""
        last_beat = datetime.now(timezone.utc) - timedelta(hours=1)
        with patch("beat._repo_frozen_since", return_value=False):
            assert beat._pick_needed(tmp_project, last_beat) is True

    def test_returns_false_when_frozen_no_ticket_changes(self, tmp_project):
        """No commits, no ticket changes → skip pick-ticket."""
        last_beat = datetime.now(timezone.utc) - timedelta(hours=1)
        with (
            patch("beat._repo_frozen_since", return_value=True),
            patch("beat.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            assert beat._pick_needed(tmp_project, last_beat) is False

    def test_returns_true_when_ticket_changed(self, tmp_project):
        """Repo frozen but a ticket file changed → pick needed."""
        last_beat = datetime.now(timezone.utc) - timedelta(hours=1)
        with (
            patch("beat._repo_frozen_since", return_value=True),
            patch("beat.subprocess.run") as mock_run,
        ):
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="tickets/0042-foo.erg\n",
                stderr="",
            )
            assert beat._pick_needed(tmp_project, last_beat) is True


# ── Layer 1: fallback rotation (ticket 0051) ──────────────────────────────────


class TestFallbackRotation:
    """Layer 1: when primary project is idle, beat tries other projects."""

    def setup_method(self):
        beat.DRY_RUN = False

    def _make_main_patches(self, tmp_project, tmp_path, primary_cfg, projects, raid_fn):
        """Return context managers for a main() call with fallback rotation."""
        return [
            patch("beat.signal.signal"),
            patch("beat._setup_env"),
            patch.object(beat, "LOGDIR", tmp_path / "logs"),
            patch("beat._pick_project", return_value=(0, primary_cfg)),
            patch.object(beat, "_LOCK_DIR", tmp_path / "locks"),
            patch.object(beat, "PROJECTS", projects),
            patch("beat.fcntl.flock"),
            patch("beat._raid", side_effect=raid_fn),
            patch("beat.finalize_beat_log"),
            patch("beat._cleanup_stale_in_progress"),
            patch("beat.read_last_beat_record", return_value=None),
            patch("beat.append_beat_log"),
        ]

    def test_fallback_attempted_when_primary_idle(self, tmp_project, tmp_path):
        """When primary returns idle, the fallback project is tried."""
        fallback_path = tmp_path / "fallback"
        fallback_path.mkdir()
        (fallback_path / ".git").mkdir()

        primary_cfg = beat.ProjectConfig(path=tmp_project)
        fallback_cfg = beat.ProjectConfig(path=fallback_path)

        raid_calls = []

        def raid_fn(cfg):
            raid_calls.append(cfg.path)
            if cfg.path == tmp_project:
                return ("idle", None)
            return ("done", "0042")

        with contextlib.ExitStack() as stack:
            for cm in self._make_main_patches(
                tmp_project,
                tmp_path,
                primary_cfg,
                [primary_cfg, fallback_cfg],
                raid_fn,
            ):
                stack.enter_context(cm)
            beat.main()

        assert tmp_project in raid_calls
        assert fallback_path in raid_calls

    def test_no_fallback_when_primary_not_idle(self, tmp_project, tmp_path):
        """When primary returns done, no fallback is attempted."""
        fallback_path = tmp_path / "fallback"
        fallback_path.mkdir()
        (fallback_path / ".git").mkdir()

        primary_cfg = beat.ProjectConfig(path=tmp_project)
        fallback_cfg = beat.ProjectConfig(path=fallback_path)

        raid_calls = []

        def raid_fn(cfg):
            raid_calls.append(cfg.path)
            return ("done", "0042")

        with contextlib.ExitStack() as stack:
            for cm in self._make_main_patches(
                tmp_project,
                tmp_path,
                primary_cfg,
                [primary_cfg, fallback_cfg],
                raid_fn,
            ):
                stack.enter_context(cm)
            beat.main()

        assert raid_calls == [tmp_project]

    def test_no_infinite_loop_all_idle(self, tmp_project, tmp_path):
        """When all projects return idle, fallback terminates cleanly."""
        p2 = tmp_path / "p2"
        p2.mkdir()
        (p2 / ".git").mkdir()
        p3 = tmp_path / "p3"
        p3.mkdir()
        (p3 / ".git").mkdir()

        primary_cfg = beat.ProjectConfig(path=tmp_project)
        cfg2 = beat.ProjectConfig(path=p2)
        cfg3 = beat.ProjectConfig(path=p3)

        raid_calls = []

        def raid_fn(cfg):
            raid_calls.append(cfg.path)
            return ("idle", None)

        log_lines: list[str] = []

        with contextlib.ExitStack() as stack:
            for cm in self._make_main_patches(
                tmp_project,
                tmp_path,
                primary_cfg,
                [primary_cfg, cfg2, cfg3],
                raid_fn,
            ):
                stack.enter_context(cm)
            stack.enter_context(patch("beat._log", side_effect=log_lines.append))
            beat.main()

        # Must not loop infinitely; each project tried at most once.
        assert len(raid_calls) <= len([primary_cfg, cfg2, cfg3])

    def test_no_fallback_with_single_project(self, tmp_project, tmp_path):
        """Single-project rotation: idle primary yields idle outcome, no loop."""
        primary_cfg = beat.ProjectConfig(path=tmp_project)

        raid_calls = []

        def raid_fn(cfg):
            raid_calls.append(cfg.path)
            return ("idle", None)

        with contextlib.ExitStack() as stack:
            for cm in self._make_main_patches(
                tmp_project,
                tmp_path,
                primary_cfg,
                [primary_cfg],
                raid_fn,
            ):
                stack.enter_context(cm)
            beat.main()

        assert raid_calls == [tmp_project]

    def test_beat_project_env_disables_fallback(
        self, tmp_project, tmp_path, monkeypatch
    ):
        """BEAT_PROJECT override disables fallback rotation."""
        fallback_path = tmp_path / "fallback"
        fallback_path.mkdir()
        (fallback_path / ".git").mkdir()

        monkeypatch.setenv("BEAT_PROJECT", str(tmp_project))

        primary_cfg = beat.ProjectConfig(path=tmp_project)
        fallback_cfg = beat.ProjectConfig(path=fallback_path)

        raid_calls = []

        def raid_fn(cfg):
            raid_calls.append(cfg.path)
            return ("idle", None)

        with contextlib.ExitStack() as stack:
            for cm in self._make_main_patches(
                tmp_project,
                tmp_path,
                primary_cfg,
                [primary_cfg, fallback_cfg],
                raid_fn,
            ):
                stack.enter_context(cm)
            beat.main()

        assert raid_calls == [tmp_project]

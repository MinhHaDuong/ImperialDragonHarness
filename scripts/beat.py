#!/usr/bin/env python3
"""beat.py — autonomous project maintenance loop.

Replaces beat.sh + skills/beat/SKILL.md.
Control flow: [housekeeping] → pick-ticket → [raid]

Environment:
  BEAT_DRY_RUN=1   Print intended sequence without invoking Claude.
"""

import fcntl
import json
import os
import re
import secrets
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from io import TextIOBase
from pathlib import Path

from git_utils import _default_branch

# ── Constants ──────────────────────────────────────────────────────────────────

HARNESS_DIR = Path.home() / ".claude"

LOGDIR = HARNESS_DIR / "logs" / "nightbeat"
COUNTER_FILE = LOGDIR / ".run-counter"

_runtime_dir = os.environ.get("RUNTIME_DIRECTORY") or os.environ.get("XDG_RUNTIME_DIR")
_LOCK_DIR = Path(_runtime_dir) if _runtime_dir else Path.home() / ".cache"


def _lockfile(project: Path) -> Path:
    """Per-project lock so concurrent beats on different projects are allowed."""
    return _LOCK_DIR / f"nightbeat-{project.name}.lock"


HOUSEKEEPING_INTERVAL_S: int = 12 * 3600
HOUSEKEEPING_SAFETY_FLOOR_S: int = 24 * 3600
HOUSEKEEPING_TIMEOUT_S: int = 10 * 60
PICK_TICKET_TIMEOUT_S: int = 8 * 60
RAID_TIMEOUT_S: int = 30 * 60
# Max consecutive CLOSED:<id> repicks per beat before aborting to idle.
# Tier 2 of ticket 0049: bound prevents flaky exit-criteria from looping forever.
MAX_CLOSED_REPICKS: int = 3
MAX_TURNS_HOUSEKEEPING: int = 40
MAX_TURNS_PICK_TICKET: int = 30
MAX_TURNS_RAID: int = 80
CRASH_RECOVERY_WINDOW_S: int = 55 * 60
LOG_RETAIN_COUNT: int = 60
TIMEOUT_EXIT_CODE: int = 124  # matches bash `timeout` convention

BUDGET_HOUSEKEEPING: float = 0.75
BUDGET_PICK_TICKET: float = 0.75
BUDGET_RAID: float = 5.00

MODEL_SONNET: str = "sonnet"
MODEL_HAIKU: str = "claude-haiku-4-5-20251001"

PROJECTS_CONFIG: Path = HARNESS_DIR / "scripts" / "projects.json"
OUTCOMES_LOG: Path = HARNESS_DIR / "logs" / "beat-outcomes.jsonl"

# Weekly /fewer-permission-prompts cadence. Folded into nightbeat instead of
# a dedicated systemd timer (ticket 0043). Lowercase weekday name; matched
# against datetime.now().strftime("%A").lower().
PERMISSIONS_PRUNE_DAY_OF_WEEK: str = "sunday"

DRY_RUN: bool = os.environ.get("BEAT_DRY_RUN") == "1"


# ── Process-wide state (shared with signal handler) ───────────────────────────


@dataclass
class _State:
    beat_start: float = 0.0
    project: Path | None = None
    current_proc: subprocess.Popen | None = field(default=None, repr=False)
    log_fh: TextIOBase | None = field(default=None, repr=False)
    final_written: bool = False


_state = _State()


@dataclass
class _SkillResult:
    result_text: str = ""
    subtype: str = ""
    permission_denials: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    is_error: bool = False


# ── Per-project configuration ─────────────────────────────────────────────────


@dataclass
class ProjectConfig:
    """Per-project beat settings; budget fields default to the global constants.

    Fields (all optional except path):
        budget_housekeeping, budget_pick_ticket, budget_raid — USD caps.
        pick_ticket_model — model used when repo has no recent commits.
        interval_minutes — minimum minutes between beats (0 = always run).
        raid_timeout_s — seconds before the raid subprocess is killed.
        max_turns_pick_ticket — max agent turns for pick-ticket (default 30, cap 60).
        max_turns_housekeeping — max agent turns for housekeeping (default 40, cap 80).
    """

    path: Path
    budget_housekeeping: float = BUDGET_HOUSEKEEPING
    budget_pick_ticket: float = BUDGET_PICK_TICKET
    budget_raid: float = BUDGET_RAID
    pick_ticket_model: str = MODEL_HAIKU  # model used when repo has no recent commits
    interval_minutes: int = 0  # 0 = always run
    raid_timeout_s: int = RAID_TIMEOUT_S
    max_turns_pick_ticket: int = MAX_TURNS_PICK_TICKET
    max_turns_housekeeping: int = MAX_TURNS_HOUSEKEEPING

    def __post_init__(self) -> None:
        cap = 2 * MAX_TURNS_HOUSEKEEPING
        if self.max_turns_housekeeping > cap:
            self.max_turns_housekeeping = cap
        cap = 2 * MAX_TURNS_PICK_TICKET
        if self.max_turns_pick_ticket > cap:
            self.max_turns_pick_ticket = cap


_BUILTIN_PROJECTS: list[ProjectConfig] = [
    ProjectConfig(
        path=Path.home() / "aedist-technical-report",
        budget_housekeeping=0.40,
        budget_pick_ticket=0.50,
    ),
    ProjectConfig(
        path=Path.home() / "cadens",
        budget_housekeeping=0.40,
        budget_pick_ticket=0.50,
    ),
    ProjectConfig(path=Path.home() / "Climate_finance"),
    ProjectConfig(path=Path.home() / "fuzzy-corpus"),
    ProjectConfig(
        path=HARNESS_DIR,
        budget_housekeeping=0.40,
        budget_pick_ticket=0.50,
    ),
]

_PROJ_KEYS = {
    "budget_housekeeping",
    "budget_pick_ticket",
    "budget_raid",
    "pick_ticket_model",
    "interval_minutes",
    "raid_timeout_s",
    "max_turns_pick_ticket",
    "max_turns_housekeeping",
}


def _apply_beat_json_overlay(config: ProjectConfig) -> None:
    """Merge fields from <project>/.claude/beat.json into config, if present."""
    beat_cfg = config.path / ".claude" / "beat.json"
    if not beat_cfg.exists():
        return
    try:
        overrides = json.loads(beat_cfg.read_text())
        for k, v in overrides.items():
            if k in _PROJ_KEYS:
                setattr(config, k, v)
        # __post_init__ doesn't re-run after setattr; re-apply caps manually.
        config.__post_init__()
    except Exception as exc:  # noqa: BLE001
        print(
            f"[beat] error loading {beat_cfg}: {exc}, ignoring overlay",
            file=sys.stderr,
        )


def load_projects(config_path: Path) -> list[ProjectConfig]:
    """Load project list from JSON; fall back to built-in defaults on any error."""
    if not config_path.exists():
        print(
            f"[beat] {config_path} not found, using built-in defaults", file=sys.stderr
        )
        return list(_BUILTIN_PROJECTS)
    try:
        entries = json.loads(config_path.read_text())
        configs = [
            ProjectConfig(
                path=Path(e["path"]).expanduser(),
                **{k: e[k] for k in _PROJ_KEYS if k in e},
            )
            for e in entries
        ]
    except Exception as exc:  # noqa: BLE001
        print(
            f"[beat] error loading {config_path}: {exc}, using built-in defaults",
            file=sys.stderr,
        )
        return list(_BUILTIN_PROJECTS)
    for cfg in configs:
        _apply_beat_json_overlay(cfg)
    return configs


PROJECTS: list[ProjectConfig] = load_projects(PROJECTS_CONFIG)


# ── Logging ────────────────────────────────────────────────────────────────────


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _log(msg: str) -> None:
    line = msg if msg.endswith("\n") else msg + "\n"
    sys.stdout.write(line)
    sys.stdout.flush()
    if _state.log_fh is not None:
        try:
            _state.log_fh.write(line)
            _state.log_fh.flush()
        except OSError:
            pass


# ── beat-log.jsonl management ─────────────────────────────────────────────────


def _beat_log_path(project: Path) -> Path:
    return project / "beat-log.jsonl"


def _cleanup_stale_in_progress(project: Path) -> None:
    """Rewrite any in_progress record older than CRASH_RECOVERY_WINDOW_S to aborted.

    Crash recovery only catches the most-recent record; this catches orphans
    buried under subsequent done/failed records when the 55-min window elapsed
    before the project was next visited.
    """
    path = _beat_log_path(project)
    if not path.exists():
        return
    cutoff = time.time() - CRASH_RECOVERY_WINDOW_S
    lines = path.read_text().splitlines()
    changed = False
    new_lines: list[str] = []
    for line in lines:
        if line.strip():
            try:
                rec = json.loads(line)
                if rec.get("outcome") == "in_progress":
                    epoch = datetime.fromisoformat(
                        rec.get("last_run_at", "1970-01-01T00:00:00Z").replace(
                            "Z", "+00:00"
                        )
                    ).timestamp()
                    if epoch < cutoff:
                        rec["outcome"] = "aborted"
                        rec["diagnostics"] = (
                            "stale in_progress — cleaned on next beat start"
                        )
                        line = json.dumps(rec, separators=(",", ":"))
                        changed = True
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        new_lines.append(line)
    if changed:
        path.write_text("\n".join(new_lines) + "\n")
        _log(
            f"=== startup: cleaned stale in_progress records in {project.name} {_now_iso()} ==="
        )


# Harness worktree name patterns created by EnterWorktree
_HARNESS_WORKTREE_RE = re.compile(r"^(agent-|explore-|t\d|review-)")


def _cleanup_locked_worktrees(project: Path) -> None:
    """Unlock and remove git-locked worktrees whose agent PID is no longer alive.

    EnterWorktree writes a lock file at .git/worktrees/<name>/locked with content
    like "claude agent <name> (pid NNNN)". When an agent is killed the lock is never
    removed. This function scans all locked worktrees belonging to this project,
    checks PID liveness, and removes orphans so housekeeping does not fail with
    "fatal: impossible de supprimer un arbre de travail verrouillé".
    """
    git_dir = project / ".git"
    if not git_dir.is_dir():
        return
    worktrees_admin = git_dir / "worktrees"
    if not worktrees_admin.is_dir():
        return

    for admin_dir in sorted(worktrees_admin.iterdir()):
        if not admin_dir.is_dir():
            continue
        name = admin_dir.name
        if not _HARNESS_WORKTREE_RE.match(name):
            continue

        lock_file = admin_dir / "locked"
        if not lock_file.exists():
            continue

        # Extract PID from lock content, e.g. "claude agent <name> (pid 1234)"
        content = lock_file.read_text().strip()
        pid_match = re.search(r"\(pid (\d+)\)", content)
        if not pid_match:
            # Unknown format — skip to avoid accidentally removing a live worktree
            _log(
                f"=== startup: skipping locked worktree {name}: unknown lock format {_now_iso()} ==="
            )
            continue

        pid = int(pid_match.group(1))
        try:
            os.kill(pid, 0)
            alive = True
        except ProcessLookupError:
            alive = False
        except PermissionError:
            alive = True  # process exists but owned by another user

        if alive:
            continue

        # Resolve the worktree checkout path from .git/worktrees/<name>/gitdir
        gitdir_file = admin_dir / "gitdir"
        if not gitdir_file.exists():
            continue
        # gitdir contains "<worktree_path>/.git", so parent is the checkout dir
        worktree_path = Path(gitdir_file.read_text().strip()).parent

        _log(
            f"=== startup: removing orphaned locked worktree {name} (dead pid {pid}) {_now_iso()} ==="
        )
        try:
            subprocess.run(  # noqa: S603
                ["git", "worktree", "unlock", str(worktree_path)],
                cwd=project,
                capture_output=True,
                check=False,
            )
            subprocess.run(  # noqa: S603
                ["git", "worktree", "remove", "--force", str(worktree_path)],
                cwd=project,
                capture_output=True,
                check=False,
            )
        except OSError as exc:
            _log(
                f"=== startup: failed to remove worktree {name}: {exc} {_now_iso()} ==="
            )


def append_beat_log(project: Path, record: dict) -> None:
    """Append one compact-JSON record; no-op in dry-run mode."""
    if DRY_RUN:
        return
    path = _beat_log_path(project)
    with path.open("a") as fh:
        fh.write(json.dumps(record, separators=(",", ":")) + "\n")


def finalize_beat_log(project: Path, record: dict) -> None:
    """Write terminal spin-down record, replacing any trailing in_progress.

    Idempotent via _state.final_written; no-op in dry-run mode.
    """
    if _state.final_written or DRY_RUN:
        return
    _state.final_written = True

    path = _beat_log_path(project)
    if not path.exists():
        append_beat_log(project, record)
        return

    lines = path.read_text().splitlines()
    while lines:
        try:
            if json.loads(lines[-1]).get("outcome") == "in_progress":
                lines.pop()
                continue
        except (json.JSONDecodeError, AttributeError):
            pass
        break

    lines.append(json.dumps(record, separators=(",", ":")))
    path.write_text("\n".join(lines) + "\n")


def read_last_beat_record(project: Path) -> dict | None:
    """Return the last record in beat-log.jsonl, handling pretty-printed JSON."""
    path = _beat_log_path(project)
    if not path.exists() or path.stat().st_size == 0:
        return None
    result = subprocess.run(  # noqa: S603
        ["jq", "-s", "last"],
        input=path.read_text(),
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        obj = json.loads(result.stdout)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        return None


# ── Phase outcome log ─────────────────────────────────────────────────────────


_HK_OUTCOME_MAP: dict[str, str] = {
    "skipped": "idle",
    "no-changes": "success",
    "deferred": "success",
    "timeout": "timeout",
    "failed": "fail",
    "aborted-dirty-tree": "fail",
}


def _record_phase_outcome(
    project: Path,
    phase: str,
    outcome: str,
    *,
    ticket_id: str | None = None,
    detail: str = "",
    skill_result: _SkillResult | None = None,
) -> None:
    """Append one phase-outcome record to OUTCOMES_LOG (always, including dry-run)."""
    rec: dict = {
        "ts": _now_iso(),
        "host": socket.gethostname(),
        "project": project.name,
        "phase": phase,
        "outcome": outcome,
    }
    if ticket_id is not None:
        rec["ticket_id"] = ticket_id
    if detail:
        rec["detail"] = detail[:200]
    if skill_result is not None:
        if skill_result.cost_usd:
            rec["cost_usd"] = round(skill_result.cost_usd, 4)
        if skill_result.permission_denials:
            rec["denied"] = skill_result.permission_denials
    OUTCOMES_LOG.parent.mkdir(parents=True, exist_ok=True)
    with OUTCOMES_LOG.open("a") as fh:
        fh.write(json.dumps(rec, separators=(",", ":")) + "\n")


# ── Signal handling ────────────────────────────────────────────────────────────


def _on_sigterm(_signum: int, _frame: object) -> None:
    elapsed = int(time.monotonic() - _state.beat_start)
    proc = _state.current_proc
    if proc is not None and proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    if _state.project is not None:
        finalize_beat_log(
            _state.project,
            {
                "last_run_at": _now_iso(),
                "ticket_id": None,
                "branch": None,
                "PR": None,
                "outcome": "aborted",
                "diagnostics": "systemd SIGTERM — beat exceeded time budget",
                "duration_s": elapsed,
            },
        )
    _log(f"=== beat SIGTERM elapsed={elapsed}s {_now_iso()} ===")
    sys.exit(143)


# ── Housekeeping check ─────────────────────────────────────────────────────────


def housekeeping_needed(project: Path) -> bool:
    """Return True when housekeeping should run.

    Skip when the repo is idle (no commits since last housekeeping)
    but enforce a 24h safety floor.
    """
    result = subprocess.run(  # noqa: S603
        ["git", "log", "--grep=housekeeping", "-1", "--format=%ct %H"],
        capture_output=True,
        text=True,
        check=False,
        cwd=project,
    )
    raw = result.stdout.strip()
    if not raw:
        return True
    parts = raw.split(maxsplit=1)
    if len(parts) < 2:
        return True
    try:
        age = time.time() - int(parts[0])
    except ValueError:
        return True
    if age <= HOUSEKEEPING_INTERVAL_S:
        return False
    if age > HOUSEKEEPING_SAFETY_FLOOR_S:
        last_hk_dt = datetime.fromtimestamp(int(parts[0]), tz=UTC)
        if _repo_frozen_since(project, last_hk_dt):
            return False
        return True
    # Between interval and safety floor: run only if repo has activity.
    activity = subprocess.run(  # noqa: S603
        ["git", "rev-list", "--count", f"{parts[1]}..HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=project,
    )
    try:
        return int(activity.stdout.strip()) > 0
    except ValueError:
        return True


def _repo_frozen_since(project: Path, since: datetime) -> bool:
    """Return True when no commits have landed since `since`."""
    result = subprocess.run(  # noqa: S603
        ["git", "log", f"--since={since.isoformat()}", "--oneline"],
        capture_output=True,
        text=True,
        check=False,
        cwd=project,
    )
    return not result.stdout.strip()


def _repo_active(project: Path) -> bool:
    """Return True when at least one commit landed in the last 24 hours."""
    result = subprocess.run(  # noqa: S603
        ["git", "log", "--since=24h", "--oneline"],
        capture_output=True,
        text=True,
        check=False,
        cwd=project,
    )
    return bool(result.stdout.strip())


# ── Pick-ticket output parser ─────────────────────────────────────────────────


def parse_pick(result_text: str) -> tuple[str, str | None]:
    """Classify pick-ticket output.

    Returns a (status, ticket_id) tuple where status is one of:
      - "pick":   `PICK: <id>` matched; ticket_id is the 4-digit string.
      - "closed": `CLOSED: <id>` matched (Tier 2, ticket 0049) — pick-ticket
                  detected the ticket's exit criteria are already met and
                  closed it; caller should re-pick. ticket_id is the 4-digit
                  string of the closed ticket.
      - "idle":   No eligible candidate, or unparseable output. ticket_id
                  is None.

    Precedence: IDLE > CLOSED > PICK. IDLE always wins (safety bias).
    """
    if re.search(r"\bIDLE\b", result_text, re.IGNORECASE):
        return ("idle", None)
    closed = re.search(r"\bCLOSED:\s*(\d{4})\b", result_text)
    if closed:
        return ("closed", closed.group(1))
    pick = re.search(r"\bPICK:\s*(\d{4})\b", result_text)
    if pick:
        return ("pick", pick.group(1))
    return ("idle", None)


# ── Claude subprocess ──────────────────────────────────────────────────────────


def _claude_argv(
    skill: str,
    budget: float,
    *,
    project_scoped: bool = False,
    model: str = MODEL_SONNET,
    max_turns: int | None = None,
) -> list[str]:
    argv = [
        "claude",
        "--print",
        "--verbose",
        "--output-format",
        "stream-json",
        "--permission-mode",
        "bypassPermissions",
        "--no-session-persistence",
        "--max-budget-usd",
        f"{budget:.2f}",
        "--model",
        model,
        "--settings",
        str(HARNESS_DIR / "scripts" / "beat-settings.json"),
    ]
    if max_turns is not None:
        argv += ["--max-turns", str(max_turns)]
    if not project_scoped:
        # Harness context for skills that need workflow awareness (housekeeping).
        # Omitted for pick-ticket / raid to prevent cross-project ticket leakage.
        argv += ["--add-dir", str(HARNESS_DIR)]
    argv += ["--add-dir", ".", "-p", skill]
    return argv


def run_skill(
    skill: str,
    *,
    budget: float,
    timeout_s: int,
    cwd: Path,
    project_scoped: bool = False,
    model: str = MODEL_SONNET,
    max_turns: int | None = None,
) -> tuple[int, _SkillResult]:
    """Invoke a Claude skill; return (exit_code, _SkillResult).

    Streams stdout line-by-line for live logging.
    Returns exit_code=TIMEOUT_EXIT_CODE on timeout.
    project_scoped=True omits --add-dir harness to prevent cross-project ticket leakage.
    """
    argv = _claude_argv(
        skill, budget, project_scoped=project_scoped, model=model, max_turns=max_turns
    )

    if DRY_RUN:
        _log(f"[dry-run] {' '.join(argv)}")
        if "pick-ticket" in skill:
            return 0, _SkillResult(result_text="PICK: 9999")
        return 0, _SkillResult(result_text="(dry-run ok)")

    env = {**os.environ, "CLAUDE_NIGHT_SWEEP": "1"}
    proc = subprocess.Popen(  # noqa: S603
        argv,
        stdout=subprocess.PIPE,
        stderr=None,  # inherit → systemd journal
        text=True,
        bufsize=1,
        cwd=cwd,
        env=env,
    )
    _state.current_proc = proc

    stdout_lines: list[str] = []

    def _reader() -> None:
        if proc.stdout is None:
            return
        for raw in proc.stdout:
            line = raw.rstrip("\n")
            _log(line)
            stdout_lines.append(line)

    reader = threading.Thread(target=_reader, daemon=True)
    reader.start()

    timed_out = False
    try:
        proc.wait(timeout=timeout_s)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    reader.join(timeout=10)
    _state.current_proc = None

    if timed_out:
        return TIMEOUT_EXIT_CODE, _SkillResult()

    skill_result = _SkillResult()
    for line in stdout_lines:
        try:
            obj = json.loads(line)
            if obj.get("type") == "result":
                skill_result = _SkillResult(
                    result_text=obj.get("result", ""),
                    subtype=obj.get("subtype", ""),
                    permission_denials=[
                        d.get("tool_name", "?")
                        for d in obj.get("permission_denials", [])
                    ],
                    cost_usd=obj.get("total_cost_usd") or 0.0,
                    is_error=bool(obj.get("is_error")),
                )
        except json.JSONDecodeError:
            pass

    return proc.returncode, skill_result


# ── Origin sync ───────────────────────────────────────────────────────────────


def _sync_origin_main(project: Path) -> None:
    """Update the local default branch from origin.

    Called before housekeeping so that both housekeeping_needed() and
    pick-ticket see current ticket state from merged PRs.  All failures
    are non-fatal — the beat continues regardless.
    """
    default_branch = _default_branch(project)

    # Fetch only the default branch; skip on network or auth failure.
    fetch = subprocess.run(  # noqa: S603
        ["git", "fetch", "origin", default_branch],
        capture_output=True,
        text=True,
        check=False,
        cwd=project,
    )
    if fetch.returncode != 0:
        _log(
            f"=== sync: git fetch failed — "
            f"{(fetch.stderr.strip().splitlines() or ['network error'])[-1][:80]} ==="
        )
        return

    # Advance local default branch.
    branch = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        cwd=project,
    ).stdout.strip()

    if branch == default_branch:
        # Checked out: ff-merge to advance HEAD.
        merge = subprocess.run(  # noqa: S603
            ["git", "merge", "--ff-only", f"origin/{default_branch}"],
            capture_output=True,
            text=True,
            check=False,
            cwd=project,
        )
        summary = (merge.stdout.strip().splitlines() or ["already up to date"])[0]
        if merge.returncode == 0:
            _log(f"=== sync: {default_branch}: {summary} {_now_iso()} ===")
        else:
            _log(
                f"=== sync: ff-merge skipped — "
                f"{(merge.stderr.strip().splitlines() or ['local commits ahead'])[-1][:80]} ==="
            )
    elif branch != "HEAD":
        # Not checked out: update local ref without touching HEAD.
        update = subprocess.run(  # noqa: S603
            ["git", "fetch", "origin", f"{default_branch}:{default_branch}"],
            capture_output=True,
            text=True,
            check=False,
            cwd=project,
        )
        if update.returncode == 0:
            _log(
                f"=== sync: {default_branch} updated from origin (HEAD on {branch}) {_now_iso()} ==="
            )
        else:
            _log(
                f"=== sync: {default_branch} update skipped — "
                f"{(update.stderr.strip().splitlines() or ['non-fast-forward'])[-1][:80]} ==="
            )
    else:
        _log(f"=== sync: skipped — detached HEAD {_now_iso()} ===")


# ── Main ───────────────────────────────────────────────────────────────────────


def _setup_env() -> None:
    os.environ["PATH"] = (
        f"{Path.home() / '.local' / 'bin'}:/usr/local/bin:/usr/bin:/bin"
    )
    for var, val in {
        "GIT_AUTHOR_NAME": "claude-agent",
        "GIT_AUTHOR_EMAIL": "claude-agent@localhost",
        "GIT_COMMITTER_NAME": "claude-agent",
        "GIT_COMMITTER_EMAIL": "claude-agent@localhost",
    }.items():
        os.environ.setdefault(var, val)


def _pick_project() -> tuple[int, ProjectConfig]:
    """Return (run_count, project_config).

    If BEAT_PROJECT is set, use that path directly (counter still advances).
    If the path matches a known project, return its config; otherwise build a
    default-budget ProjectConfig for the override path.
    Otherwise use sequential rotation across PROJECTS.
    """
    count = int(COUNTER_FILE.read_text().strip()) if COUNTER_FILE.exists() else 0
    COUNTER_FILE.write_text(str(count + 1))
    override = os.environ.get("BEAT_PROJECT")
    if override:
        override_path = Path(override).resolve()
        for cfg in PROJECTS:
            if cfg.path == override_path:
                return count, cfg
        return count, ProjectConfig(path=override_path)
    idx = count % len(PROJECTS)
    return count, PROJECTS[idx]


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(  # noqa: S603
        ["git", *args], capture_output=True, text=True, check=False, cwd=cwd
    )


def _housekeeping_phase(project: ProjectConfig) -> str:
    """Run housekeeping on a dedicated branch cut from origin/main.

    Returns one of:
      "skipped"            — housekeeping_needed was False
      "no-changes"         — skill ran clean, produced no commits
      "deferred"           — commits on branch, left for human review
      "timeout"            — skill timed out
      "failed"             — git or skill error
      "aborted-dirty-tree" — working tree dirty after skill run; checkout skipped
    """
    path = project.path
    if not housekeeping_needed(path):
        _log(f"=== housekeeping: skipped {_now_iso()} ===")
        return "skipped"

    default_branch = _default_branch(path)
    base = _git("rev-parse", f"origin/{default_branch}", cwd=path).stdout.strip()
    if not base:
        _log(
            f"=== housekeeping: cannot resolve origin/{default_branch} {_now_iso()} ==="
        )
        return "failed"

    nonce = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(2)
    branch = f"claude/housekeeping-{nonce}"
    r = _git("checkout", "-B", branch, base, cwd=path)
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip().replace("\n", " | ")
        _log(f"=== housekeeping: failed to create {branch}: {detail} {_now_iso()} ===")
        return "failed"

    _log(f"=== housekeeping: running on {branch} {_now_iso()} ===")
    git_script = path / "scripts" / "housekeeping-git.sh"
    if git_script.exists():
        git_rc = subprocess.run(  # noqa: S603
            [str(git_script)],
            cwd=path,
            check=False,
        ).returncode
        if git_rc == 0:
            _log(f"=== housekeeping-git: done {_now_iso()} ===")
        else:
            _log(f"=== housekeeping-git: rc={git_rc} {_now_iso()} ===")
    os.environ["BEAT_HOUSEKEEPING_BRANCH"] = branch
    try:
        hk_rc, hk_res = run_skill(
            "/housekeeping",
            budget=project.budget_housekeeping,
            timeout_s=HOUSEKEEPING_TIMEOUT_S,
            cwd=path,
            max_turns=project.max_turns_housekeeping,
        )
    finally:
        os.environ.pop("BEAT_HOUSEKEEPING_BRANCH", None)

    if hk_rc == TIMEOUT_EXIT_CODE:
        _log(f"=== housekeeping: timeout — {branch} left in place {_now_iso()} ===")
        return "timeout"
    if hk_res.subtype == "error_max_turns":
        _log(
            f"=== housekeeping: max-turns ({project.max_turns_housekeeping}) reached — context cap hit {_now_iso()} ==="
        )
    if hk_rc != 0:
        _log(f"=== housekeeping: rc={hk_rc} on {branch} {_now_iso()} ===")
        return "failed"

    n = _git("rev-list", "--count", f"{base}..HEAD", cwd=path).stdout.strip() or "0"

    status = _git("status", "--porcelain", cwd=path)
    if status.stdout.strip():
        dirty_files = status.stdout.strip().splitlines()
        detail = f"{len(dirty_files)} file(s): {', '.join(f.strip() for f in dirty_files[:3])}"
        _log(f"=== housekeeping: aborted-dirty-tree: {detail} {_now_iso()} ===")
        return "aborted-dirty-tree"

    _git("checkout", default_branch, cwd=path)
    if int(n) == 0:
        _log(f"=== housekeeping: no commits, deleting branch {_now_iso()} ===")
        _git("branch", "-D", branch, cwd=path)
        return "no-changes"

    _log(
        f"=== housekeeping: deferred — {n} commit(s) on {branch} ready for review {_now_iso()} ==="
    )
    return "deferred"


def _ticket_log_has_closed(ticket_path: Path) -> bool:
    """Return True if the ticket's log section contains a 'closed' verb entry."""
    in_log = False
    for ln in ticket_path.read_text().splitlines():
        if ln.strip() == "--- log ---":
            in_log = True
            continue
        if ln.startswith("---"):
            in_log = False
            continue
        if in_log:
            parts = ln.split()
            if len(parts) >= 3 and parts[2] == "closed":
                return True
    return False


def _ticket_recently_picked(ticket_path: Path, within_hours: int = 8) -> bool:
    """True if a sweep-pick log line in this ticket is within cutoff.

    Implements the cooldown-recent-pick guard previously enforced by prose
    in skills/pick-ticket/SKILL.md (ticket 0051 Layer 0). A ticket whose
    log shows it was picked within ``within_hours`` should not be re-picked
    until the prior raid has had a chance to close it.
    """
    cutoff = datetime.now(UTC) - timedelta(hours=within_hours)
    try:
        text = ticket_path.read_text()
    except (FileNotFoundError, OSError):
        return False
    for line in text.splitlines():
        if "sweep-pick: selected" in line or "sweep-pick: picked" in line:
            try:
                ts_str = line.split()[0].rstrip("Z")
                ts = datetime.fromisoformat(ts_str).replace(tzinfo=UTC)
                if ts > cutoff:
                    return True
            except (ValueError, IndexError):
                continue
    return False


def _pick_needed(project: Path, last_beat_at: datetime | None) -> bool:
    """False when nothing has changed since the last pick run.

    Implements Layer 2 of ticket 0051: skip the Claude pick-ticket invocation
    entirely when the repo has no new commits and no ticket files have changed.
    Saves tokens on idle projects that beat frequently.

    Returns True (pick needed) when:
    - last_beat_at is None (no prior beat recorded)
    - The repo has at least one commit since last_beat_at
    - Any file under tickets/ changed in git history since last_beat_at
    """
    if last_beat_at is None:
        return True
    if not _repo_frozen_since(project, last_beat_at):
        # Repo has commits since last beat → something may have changed.
        return True
    # Check whether any ticket file was modified since last beat.
    result = subprocess.run(  # noqa: S603
        [
            "git",
            "-C",
            str(project),
            "log",
            f"--since={last_beat_at.isoformat()}",
            "--name-only",
            "--pretty=format:",
            "--",
            "tickets/",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    changed = [ln for ln in result.stdout.splitlines() if ln.strip()]
    return bool(changed)


# ── Weekly /fewer-permission-prompts (ticket 0043) ────────────────────────────


def _is_prune_day() -> bool:
    """True when today's weekday matches PERMISSIONS_PRUNE_DAY_OF_WEEK."""
    return datetime.now().strftime("%A").lower() == PERMISSIONS_PRUNE_DAY_OF_WEEK


def _prune_permissions(project: Path) -> None:
    """Run the /fewer-permission-prompts helper once a week.

    Diff is written under ~/.claude/telemetry/permission-diffs/<date>.diff and
    surfaced by nightbeat-report. Diffs are NEVER auto-applied; failure here is
    benign and must not raise — beat must keep running.

    The helper is invoked at most once per host per day. Without this guard,
    every project × every beat (~85 invocations on a weekend day across 5
    projects × 17 beats) would each spawn its own ``/fewer-permission-prompts``
    session.
    """
    if not _is_prune_day():
        return
    today_diff = (
        HARNESS_DIR
        / "telemetry"
        / "permission-diffs"
        / f"{datetime.now().strftime('%Y-%m-%d')}.diff"
    )
    if today_diff.exists():
        return
    helper = HARNESS_DIR / "scripts" / "fewer-permission-prompts-helper.py"
    try:
        result = subprocess.run(  # noqa: S603
            ["python3", str(helper), str(project)],
            check=False,
            capture_output=True,
            text=True,
            timeout=10 * 60,
        )
        diff_path = (result.stdout or "").strip().splitlines()[-1:] or [""]
        _log(
            f"=== permissions-prune: rc={result.returncode}"
            f" diff={diff_path[0] or '(none)'} {_now_iso()} ==="
        )
    except Exception as exc:  # noqa: BLE001 — must never crash beat
        _log(f"=== permissions-prune: failed silently: {exc} {_now_iso()} ===")


def _raid(project: ProjectConfig) -> tuple[str, str | None]:
    """Run the pick→raid sequence; return (outcome, ticket_id)."""
    ticket_id: str | None = None
    path = project.path

    # Sync default branch from origin so housekeeping and pick-ticket
    # see current ticket state from merged PRs.
    _sync_origin_main(path)

    # Ensure working tree is on main before any read or write.
    # Fails fast with a clear message if the tree is dirty.
    default_branch = _default_branch(path)

    status = _git("status", "--porcelain", cwd=path)
    if status.stdout.strip():
        dirty_files = status.stdout.strip().splitlines()[:5]
        detail = f"{len(dirty_files)} file(s): {', '.join(dirty_files[:3])}"
        _log(f"=== beat aborted: dirty working tree: {detail} {_now_iso()} ===")
        _record_phase_outcome(path, "raid", "aborted-dirty-tree", detail=detail)
        return "aborted-dirty-tree", None

    r = _git("checkout", default_branch, cwd=path)
    if r.returncode != 0:
        detail = (r.stderr or r.stdout or "").strip().replace("\n", " | ")
        _log(
            f"=== beat aborted: cannot checkout {default_branch}: {detail} {_now_iso()} ==="
        )
        return "aborted", None

    # Housekeeping (conditional). Aborts beat on failure/timeout so
    # pick-ticket → raid never runs against a known-bad main.
    hk_outcome = _housekeeping_phase(project)
    _record_phase_outcome(
        path,
        "housekeeping",
        _HK_OUTCOME_MAP.get(hk_outcome, "fail"),
        detail=hk_outcome,
    )
    if hk_outcome in ("failed", "timeout"):
        return "aborted", None

    # Cooldown-recent-pick guard (ticket 0051 Layer 0). If any open ticket
    # was picked within the last 8h, skip pick-ticket entirely — the prior
    # raid hasn't had a chance to close it yet, and re-picking risks a
    # double-raid.
    if any(_ticket_recently_picked(t) for t in path.glob("tickets/*.erg")):
        _log(f"=== pick-ticket: skipped (cooldown-recent-pick) {_now_iso()} ===")
        _record_phase_outcome(
            path, "pick_ticket", "skip", detail="cooldown-recent-pick"
        )
        return "idle", None

    # Layer 2 pre-flight skip (ticket 0051): if nothing has changed in the repo
    # or ticket files since the last beat, skip the Claude pick-ticket invocation
    # and return idle directly — saves tokens on dormant projects.
    _last_record = read_last_beat_record(path)
    _last_beat_at: datetime | None = None
    if _last_record and _last_record.get("last_run_at"):
        try:
            _last_beat_at = datetime.fromisoformat(
                _last_record["last_run_at"].replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            pass
    if not _pick_needed(path, _last_beat_at):
        _log(
            f"=== pick-ticket: skipped (nothing changed since"
            f" {_last_beat_at.isoformat() if _last_beat_at else 'unknown'}) ==="
        )
        _record_phase_outcome(
            path,
            "pick_ticket",
            "skip",
            detail=f"nothing-changed-since-{_last_beat_at.isoformat() if _last_beat_at else 'unknown'}",
        )
        return "idle", None

    # Weekly permission-allowlist diff (no-op except on prune day).
    _prune_permissions(path)

    # Pick ticket. Loop on CLOSED (Tier 2 of ticket 0049): pick-ticket may
    # detect that a candidate's exit criteria are already met, close it, and
    # emit `CLOSED: <id>` — re-pick rather than raid a stale ticket. Bound
    # at MAX_CLOSED_REPICKS to prevent flaky exit-criteria from looping
    # forever (abort to idle so the next beat can try again).
    hostname = socket.gethostname()
    pick_model = MODEL_SONNET if _repo_active(path) else project.pick_ticket_model
    closed_attempts = 0
    ticket_id = None
    pt_res = _SkillResult()
    while closed_attempts < MAX_CLOSED_REPICKS:
        _log(f"=== pick-ticket: running model={pick_model} {_now_iso()} ===")
        pt_rc, pt_res = run_skill(
            f"/pick-ticket\n\nRunning on: {hostname}",
            budget=project.budget_pick_ticket,
            timeout_s=PICK_TICKET_TIMEOUT_S,
            cwd=path,
            project_scoped=True,
            model=pick_model,
            max_turns=project.max_turns_pick_ticket,
        )

        if pt_rc == TIMEOUT_EXIT_CODE:
            _record_phase_outcome(path, "pick_ticket", "timeout", skill_result=pt_res)
            return "aborted", None
        if pt_res.subtype == "error_max_turns":
            _log(
                f"=== pick-ticket: max-turns ({project.max_turns_pick_ticket}) reached — context cap hit {_now_iso()} ==="
            )
        if pt_rc != 0:
            _record_phase_outcome(path, "pick_ticket", "fail", skill_result=pt_res)
            return "failed", None

        status, ticket_id = parse_pick(pt_res.result_text)
        if status == "closed":
            closed_attempts += 1
            _log(
                f"=== pick-ticket: closed {ticket_id}, repicking"
                f" (attempt {closed_attempts}/{MAX_CLOSED_REPICKS}) ==="
            )
            continue
        break
    else:
        # while-else: ran MAX_CLOSED_REPICKS times without breaking → all
        # attempts returned CLOSED. Abort to idle so the orchestrator never
        # raids a ticket that may be already done.
        _log(
            f"=== pick-ticket: idle — {MAX_CLOSED_REPICKS} consecutive CLOSED"
            f" picks; aborting beat to avoid loop {_now_iso()} ==="
        )
        _record_phase_outcome(
            path,
            "pick_ticket",
            "skip",
            detail=f"{MAX_CLOSED_REPICKS} consecutive CLOSED repicks",
            skill_result=pt_res,
        )
        return "idle", None

    if status == "idle":
        last_result_line = (
            pt_res.result_text.strip().splitlines()[-1]
            if pt_res.result_text.strip()
            else ""
        )
        _log(
            f"=== pick-ticket: idle — {last_result_line or 'IDLE: no eligible tickets'} {_now_iso()} ==="
        )
        _record_phase_outcome(
            path, "pick_ticket", "idle", detail=last_result_line, skill_result=pt_res
        )
        return "idle", None

    _log(f"=== pick-ticket: picked {ticket_id} {_now_iso()} ===")

    # Raid
    _log(f"=== raid: running ticket {ticket_id} {_now_iso()} ===")
    oc_rc, oc_res = run_skill(
        f"/raid {ticket_id}\n\nRunning on: {hostname}",
        budget=project.budget_raid,
        timeout_s=project.raid_timeout_s,
        cwd=path,
        project_scoped=True,
        max_turns=MAX_TURNS_RAID,
    )

    if oc_rc == TIMEOUT_EXIT_CODE:
        outcome = "aborted"
        _record_phase_outcome(
            path, "raid", "timeout", ticket_id=ticket_id, skill_result=oc_res
        )
    elif oc_res.subtype == "error_max_turns":
        outcome = "failed"
        _record_phase_outcome(
            path, "raid", "max_turns", ticket_id=ticket_id, skill_result=oc_res
        )
    elif oc_res.subtype == "error_max_budget_usd":
        outcome = "failed"
        _record_phase_outcome(
            path, "raid", "budget", ticket_id=ticket_id, skill_result=oc_res
        )
    elif oc_rc != 0:
        outcome = "failed"
        _record_phase_outcome(
            path, "raid", "fail", ticket_id=ticket_id, skill_result=oc_res
        )
    else:
        # v1 simplification: rc=0 → "done"; raid may write finer-grained
        # outcomes into beat-log itself, but we don't parse those here.
        outcome = "done"
        _record_phase_outcome(
            path, "raid", "success", ticket_id=ticket_id, skill_result=oc_res
        )
        # Warn if raid exited cleanly but left the ticket open (double-pick risk).
        ticket_files = list(path.glob(f"tickets/{ticket_id}-*.erg"))
        if ticket_files and not _ticket_log_has_closed(ticket_files[0]):
            _log(
                f"=== warning: raid done but ticket {ticket_id}"
                f" not closed — double-pick risk ==="
            )

    _log(f"=== raid: outcome={outcome} {_now_iso()} ===")
    return outcome, ticket_id


def main() -> None:
    _state.beat_start = time.monotonic()
    signal.signal(signal.SIGTERM, _on_sigterm)
    _setup_env()

    # Per-run logfile (opened before lock so startup messages are captured)
    LOGDIR.mkdir(parents=True, exist_ok=True)
    logfile = LOGDIR / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.log"
    _state.log_fh = logfile.open("a")

    # Rotate old logs
    for old in sorted(LOGDIR.glob("*.log"))[:-LOG_RETAIN_COUNT]:
        old.unlink(missing_ok=True)

    # Project rotation
    count, project = _pick_project()
    path = project.path
    _state.project = path

    # Per-project lock: allows concurrent beats on different projects
    _LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_fh = _lockfile(path).open("w")  # held open until process exits
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        _log(f"beat already running for {path.name}, skipping.")
        lock_fh.close()
        sys.exit(0)

    _log(f"=== beat start {_now_iso()} ===")
    _log(f"Run {count}  →  project slot {count % len(PROJECTS)}: {path}")

    if not (path / ".git").is_dir():
        _log(f"ERROR: {path} is not a git repository. Aborting.")
        sys.exit(1)

    # Interval skip: project can declare a minimum interval between beats.
    if project.interval_minutes > 0:
        last = read_last_beat_record(path)
        if last and last.get("last_run_at"):
            try:
                last_epoch = datetime.fromisoformat(
                    last["last_run_at"].replace("Z", "+00:00")
                ).timestamp()
                elapsed_s = time.time() - last_epoch
                if elapsed_s < project.interval_minutes * 60:
                    remaining = int(project.interval_minutes * 60 - elapsed_s)
                    _log(
                        f"=== interval-skip: {path.name} (next run in {remaining}s) {_now_iso()} ==="
                    )
                    _record_phase_outcome(
                        path,
                        "interval",
                        "skip",
                        detail=f"interval={project.interval_minutes}m, remaining={remaining}s",
                    )
                    lock_fh.close()
                    sys.exit(0)
            except (ValueError, TypeError):
                pass

    (path / ".claude" / "sweep-state").mkdir(parents=True, exist_ok=True)

    # Layer-1 cleanup: rewrite buried stale in_progress records that crash
    # recovery missed (it only checks the most-recent record within 55 min).
    _cleanup_stale_in_progress(path)

    # Layer-2 cleanup: remove orphaned git-locked worktrees left by killed agents.
    _cleanup_locked_worktrees(path)

    # Crash / SIGKILL recovery
    last = read_last_beat_record(path)
    if last and last.get("outcome") == "in_progress":
        try:
            last_at = last.get("last_run_at", "1970-01-01T00:00:00Z")
            last_epoch = datetime.fromisoformat(
                last_at.replace("Z", "+00:00")
            ).timestamp()
            if (time.time() - last_epoch) < CRASH_RECOVERY_WINDOW_S:
                append_beat_log(
                    path,
                    {
                        "last_run_at": _now_iso(),
                        "ticket_id": None,
                        "branch": None,
                        "PR": None,
                        "outcome": "aborted",
                        "diagnostics": "crash/SIGKILL recovery — previous run never completed spin-down",
                    },
                )
                _log(f"=== beat aborted: crash recovery {_now_iso()} ===")
                sys.exit(0)
        except (ValueError, TypeError):
            pass

    # Spin-in
    append_beat_log(path, {"outcome": "in_progress", "last_run_at": _now_iso()})

    # Orchestration
    outcome = "idle"
    ticket_id: str | None = None
    try:
        outcome, ticket_id = _raid(project)

        # Layer 1 — Fallback rotation (ticket 0051): if the primary project is
        # idle, try other projects in the rotation before giving up the timeslot.
        # Bound at len(PROJECTS) - 1 to prevent infinite loops. Each fallback
        # acquires its own lock non-blocking; already-running projects are skipped.
        if outcome == "idle" and not os.environ.get("BEAT_PROJECT"):
            _log(f"=== fallback: primary idle, trying other projects {_now_iso()} ===")
            fallback_tried = 0
            for fallback_cfg in PROJECTS:
                if fallback_cfg.path == path:
                    continue
                if fallback_tried >= len(PROJECTS) - 1:
                    break
                fb_lock_fh = _lockfile(fallback_cfg.path).open("w")
                try:
                    fcntl.flock(fb_lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    _log(
                        f"=== fallback: {fallback_cfg.path.name} locked, skipping {_now_iso()} ==="
                    )
                    fb_lock_fh.close()
                    fallback_tried += 1
                    continue
                try:
                    _log(
                        f"=== fallback: trying {fallback_cfg.path.name} {_now_iso()} ==="
                    )
                    fallback_tried += 1
                    fb_outcome, fb_ticket = _raid(fallback_cfg)
                    _log(
                        f"=== fallback: {fallback_cfg.path.name}"
                        f" outcome={fb_outcome} ==="
                    )
                    if fb_outcome != "idle":
                        outcome = fb_outcome
                        ticket_id = fb_ticket
                        break
                finally:
                    fcntl.flock(fb_lock_fh, fcntl.LOCK_UN)
                    fb_lock_fh.close()
            else:
                _log(f"=== fallback: all projects idle or locked {_now_iso()} ===")
    except KeyboardInterrupt:
        outcome = "aborted"

    # Spin-down
    elapsed = int(time.monotonic() - _state.beat_start)
    finalize_beat_log(
        path,
        {
            "last_run_at": _now_iso(),
            "ticket_id": ticket_id,
            "branch": None,
            "PR": None,
            "outcome": outcome,
            "duration_s": elapsed,
        },
    )

    ticket_label = ticket_id if ticket_id else "—"
    minutes, seconds = divmod(int(elapsed), 60)
    duration_str = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    print(
        f"beat: {path.name} ticket={ticket_label} outcome={outcome} duration={duration_str}"
    )

    _log(f"=== beat done elapsed={elapsed}s {_now_iso()} ===")
    if _state.log_fh is not None:
        _state.log_fh.close()


if __name__ == "__main__":
    main()

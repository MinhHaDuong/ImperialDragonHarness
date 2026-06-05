#!/usr/bin/env python3
"""
check-readiness: Multi-project pre-flight readiness check and interactive triage.

Modes:
- default: Full sweep across all projects (git hygiene, ticket health, settings drift)
- --mode=nightbeat-history: Legacy single-repo nightbeat risk review
- --project <name>: Scope to one project
"""

import json
import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Get home directory
HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
SCRIPTS_DIR = CLAUDE_DIR / "scripts"
PROJECTS_JSON = SCRIPTS_DIR / "projects.json"


def load_projects() -> List[Dict[str, str]]:
    """Load projects.json and return list of project configs."""
    if not PROJECTS_JSON.exists():
        print(f"Error: {PROJECTS_JSON} not found", file=sys.stderr)
        sys.exit(1)

    with open(PROJECTS_JSON) as f:
        projects = json.load(f)

    # Expand ~ in paths
    for proj in projects:
        if "path" in proj:
            proj["path"] = os.path.expanduser(proj["path"])

    return projects


def resolve_erg() -> str:
    """Resolve erg binary path."""
    try:
        result = subprocess.run(
            ["command", "-v", "erg"],
            capture_output=True,
            text=True,
            shell=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "tickets/erg"


def run_in_repo(repo_path: Path, cmd: str) -> Tuple[int, str, str]:
    """Run a command in a repo directory."""
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            shell=True,
            timeout=10,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)


def check_git_hygiene(repo_path: Path) -> Dict[str, Any]:
    """Check git hygiene: uncommitted, drift, stale branches."""
    status = {
        "uncommitted": False,
        "drift": False,
        "stale_branches": [],
        "errors": [],
    }

    # Check if this is a git repo
    code, _, _ = run_in_repo(repo_path, "git rev-parse --git-dir")
    if code != 0:
        status["errors"].append("Not a git repo")
        return status

    # Check for uncommitted changes
    code, out, _ = run_in_repo(repo_path, "git status --porcelain")
    if code == 0 and out.strip():
        status["uncommitted"] = True

    # Check for drift (commits not pushed)
    code, out, _ = run_in_repo(repo_path, "git rev-list --count origin/main..HEAD")
    if code == 0:
        try:
            count = int(out.strip() or "0")
            if count > 0:
                status["drift"] = True
        except ValueError:
            pass

    # Check for stale branches (not merged and older than 7 days)
    code, out, _ = run_in_repo(
        repo_path,
        "git branch --list --no-merged origin/main --format='%(refname:short)|%(committerdate:short)'",
    )
    if code == 0:
        now = datetime.now()
        for line in out.strip().split("\n"):
            if not line:
                continue
            try:
                branch, date_str = line.split("|")
                branch_date = datetime.strptime(date_str, "%Y-%m-%d")
                if (now - branch_date).days > 7:
                    status["stale_branches"].append((branch, date_str))
            except (ValueError, IndexError):
                pass

    return status


def check_ticket_health(repo_path: Path, erg: str) -> Dict[str, Any]:
    """Check ticket flow health."""
    status = {
        "open_count": 0,
        "ready_count": 0,
        "blocked_chains": [],
        "errors": [],
    }

    tickets_dir = repo_path / "tickets"
    if not tickets_dir.exists():
        status["errors"].append("No tickets/ directory")
        return status

    # Count open tickets
    code, out, _ = run_in_repo(repo_path, f"{erg} status tickets/ | wc -l")
    if code == 0:
        try:
            status["open_count"] = int(out.strip() or "0")
        except ValueError:
            pass

    # Count ready tickets
    code, out, _ = run_in_repo(repo_path, f"{erg} ready tickets/ | wc -l")
    if code == 0:
        try:
            status["ready_count"] = int(out.strip() or "0")
        except ValueError:
            pass

    # TODO: Check for blocked-by chains

    return status


def check_config_health(repo_path: Path) -> Dict[str, Any]:
    """Check CLAUDE.md and settings.json health."""
    status = {
        "has_claude_md": False,
        "claude_md_age_days": None,
        "has_settings_json": False,
        "settings_json_age_days": None,
        "warnings": [],
    }

    # Check CLAUDE.md
    claude_md = repo_path / "CLAUDE.md"
    if claude_md.exists():
        status["has_claude_md"] = True
        mtime = claude_md.stat().st_mtime
        age = (datetime.now() - datetime.fromtimestamp(mtime)).days
        status["claude_md_age_days"] = age
        if age > 30:
            status["warnings"].append(f"CLAUDE.md is {age} days old")
    else:
        status["warnings"].append("No CLAUDE.md found")

    # Check .claude/settings.json
    settings_json = repo_path / ".claude" / "settings.json"
    if settings_json.exists():
        status["has_settings_json"] = True
        mtime = settings_json.stat().st_mtime
        age = (datetime.now() - datetime.fromtimestamp(mtime)).days
        status["settings_json_age_days"] = age

    return status


def audit_project(project_path: Path, erg: str) -> Dict[str, Any]:
    """Audit a single project for readiness."""
    project_name = project_path.name

    audit = {
        "name": project_name,
        "path": str(project_path),
        "git": check_git_hygiene(project_path),
        "tickets": check_ticket_health(project_path, erg),
        "config": check_config_health(project_path),
    }

    return audit


def render_status_indicator(
    git_status: Dict, ticket_status: Dict, config_status: Dict
) -> str:
    """Render status indicators for a project."""
    indicators = []

    # Git status
    if (
        git_status.get("uncommitted")
        or git_status.get("drift")
        or git_status.get("stale_branches")
    ):
        indicators.append("⚠ git")

    # Ticket status
    if "No tickets/ directory" not in ticket_status.get("errors", []):
        if ticket_status.get("open_count", 0) > 10:
            indicators.append("⚠ tickets")
        if ticket_status.get("blocked_chains"):
            indicators.append("⚠ blocked")

    # Config status
    if config_status.get("warnings"):
        indicators.append("⚠ config")

    return " ".join(indicators) if indicators else "✓ clean"


def print_audit_table(audits: List[Dict[str, Any]]) -> None:
    """Print audit results in table format."""
    print()
    print("Project Status Summary")
    print("=" * 120)
    print()

    for audit in audits:
        name = audit["name"]
        git = audit["git"]
        tickets = audit["tickets"]
        config = audit["config"]

        status = render_status_indicator(git, tickets, config)

        print(f"{name:40} {status:30}")

        # Print details if issues found
        if git.get("uncommitted"):
            print("  → Git: uncommitted changes")
        if git.get("drift"):
            print("  → Git: commits not pushed to origin/main")
        if git.get("stale_branches"):
            for branch, date in git["stale_branches"][:3]:
                print(f"  → Git: stale branch {branch} ({date})")

        if tickets.get("open_count", 0) > 10:
            print(
                f"  → Tickets: {tickets['open_count']} open, {tickets['ready_count']} ready"
            )

        if config.get("warnings"):
            for warning in config["warnings"]:
                print(f"  → Config: {warning}")

        print()


def mode_default(
    projects: List[Dict[str, str]], project_filter: Optional[str] = None
) -> int:
    """Run full multi-project sweep."""
    print("check-readiness: default mode (full sweep)")
    print()

    erg = resolve_erg()

    audits = []
    for proj in projects:
        proj_path = Path(proj["path"])

        # Skip if project_filter specified and doesn't match
        if project_filter and proj_path.name != project_filter:
            continue

        if not proj_path.exists():
            print(f"Warning: Project path does not exist: {proj_path}", file=sys.stderr)
            continue

        print(f"Auditing: {proj_path.name} ...", file=sys.stderr)
        audit = audit_project(proj_path, erg)
        audits.append(audit)

    if not audits:
        print("No projects found to audit.", file=sys.stderr)
        return 1

    # Print audit table
    print_audit_table(audits)

    # Count issues
    issues = 0
    for audit in audits:
        git = audit["git"]
        config = audit["config"]
        if git.get("uncommitted") or git.get("drift") or git.get("stale_branches"):
            issues += 1
        if config.get("warnings"):
            issues += 1

    if issues == 0:
        print("✓ All projects clean. Ready for autonomous work.")
    else:
        print(f"⚠ {issues} project(s) have issues. Review above and take action.")

    print()
    return 0


def mode_nightbeat_history(hours: int = 72) -> int:
    """Legacy mode: de-risk nightbeat by scanning prior journal."""
    print("check-readiness: --mode=nightbeat-history (legacy nightbeat risk review)")
    print()

    # Call nightbeat-report.py
    script = SCRIPTS_DIR / "nightbeat-report.py"
    if not script.exists():
        print(f"Error: {script} not found", file=sys.stderr)
        return 1

    try:
        result = subprocess.run(
            ["python3", str(script), "--full", "--hours", str(hours)],
            cwd=Path.cwd(),
        )
        return result.returncode
    except Exception as e:
        print(f"Error running nightbeat-report: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Multi-project readiness check and interactive triage"
    )
    parser.add_argument(
        "--mode",
        choices=["default", "nightbeat-history"],
        default="default",
        help="Sweep mode (default: full multi-project audit)",
    )
    parser.add_argument(
        "--project",
        help="Scope to one project (base name from ~/.claude/projects/)",
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=72,
        help="For nightbeat-history mode, hours to scan (default: 72)",
    )

    args = parser.parse_args()

    # Load projects
    projects = load_projects()

    # Handle modes
    if args.project:
        # Single project scope: run full audit on that project only
        return mode_default(projects, project_filter=args.project)
    elif args.mode == "nightbeat-history":
        # Legacy mode: risk review of current repo
        return mode_nightbeat_history(hours=args.hours)
    else:
        # Default: full sweep
        return mode_default(projects)


if __name__ == "__main__":
    sys.exit(main())

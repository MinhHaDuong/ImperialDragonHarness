#!/usr/bin/env python3
"""Read the forge's check conclusion for one commit; pick the tests a diff touches.

`status <owner/name> <head-sha> --workflow <path>` prints one trail line and
exits 0 only when the latest run of that workflow for exactly that commit is
complete and green. Anything else (older head only, pending, failed, missing,
unreadable) exits 1: the caller runs the full gate, never a skip.

`targets <base>` prints the test files the diff base...HEAD touches: changed
test files, and test files that name a changed path (ticket 1172).
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
# Basenames too common to identify a file; such a path is matched by its
# parent directory name, quoted, instead.
GENERIC = {"SKILL.md", "README.md", "PROFILE.md", "AGENTS.md", "__init__.py"}


def classify(payload: dict, head: str, workflow: str) -> tuple[str, str, str]:
    """Return (green|not-green, conclusion, run id) for `workflow` at `head`."""
    try:
        runs = [r for r in payload["workflow_runs"]
                if r["head_sha"] == head
                and (r["path"] == workflow or r["path"].startswith(workflow + "@"))]
    except (KeyError, TypeError):
        return "not-green", "unreadable", "-"
    if not runs:
        return "not-green", "missing", "-"
    latest = max(runs, key=lambda r: (r.get("created_at") or "", r.get("id") or 0))
    if latest.get("status") != "completed":
        return "not-green", "pending", str(latest.get("id"))
    conclusion = latest.get("conclusion") or "unknown"
    return ("green" if conclusion == "success" else "not-green"), conclusion, str(latest.get("id"))


def read_runs(forge_repo: str, head: str) -> dict | None:
    # harness-extension-point: the forge read is GitHub's REST runs list.
    out = subprocess.run(
        ["gh", "api", f"repos/{forge_repo}/actions/runs?head_sha={head}&per_page=100"],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return None


def cmd_status(args: argparse.Namespace) -> int:
    if not SHA.match(args.head):
        print(f"forge_ci: refused: head must be a full 40-hex commit sha, got {args.head!r}",
              file=sys.stderr)
        return 2
    payload = read_runs(args.forge_repo, args.head)
    if payload is None:
        verdict, conclusion, rid = "not-green", "unreadable", "-"
    else:
        verdict, conclusion, rid = classify(payload, args.head, args.workflow)
    print(f"forge_ci: {verdict} workflow={args.workflow} head={args.head} "
          f"conclusion={conclusion} run={rid}")
    return 0 if verdict == "green" else 1


def is_test(path: Path) -> bool:
    return path.is_file() and (path.name.startswith("test_") or path.stem.endswith("_test"))


def terms(changed: str) -> list[str]:
    p = Path(changed)
    if p.name in GENERIC:
        return [changed] + ([f'"{p.parent.name}"', f"'{p.parent.name}'"] if p.parent.name else [])
    return [changed, p.name]


def cmd_targets(args: argparse.Namespace) -> int:
    repo = Path(args.repo_dir)
    out = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", "-M",
                          f"{args.base}...HEAD"], capture_output=True, text=True, check=True)
    changed = [line for line in out.stdout.splitlines() if line]
    tests = sorted(p for p in (repo / args.tests_dir).rglob("*") if is_test(p))
    picked = []
    for t in tests:
        rel = t.relative_to(repo).as_posix()
        text = t.read_text(errors="replace")
        if rel in changed or any(term in text for c in changed for term in terms(c)):
            picked.append(rel)
    print("\n".join(picked))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("status", help="green|not-green for one exact head commit")
    st.add_argument("forge_repo", help="owner/name")
    st.add_argument("head", help="full head commit sha under review")
    st.add_argument("--workflow", required=True,
                    help="workflow file that runs the project's full gate")
    st.set_defaults(fn=cmd_status)
    tg = sub.add_parser("targets", help="test files the diff base...HEAD touches")
    tg.add_argument("base", help="base ref, e.g. origin/main")
    tg.add_argument("--repo-dir", default=".")
    tg.add_argument("--tests-dir", default="tests")
    tg.set_defaults(fn=cmd_targets)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

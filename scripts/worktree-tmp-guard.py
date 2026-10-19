#!/usr/bin/env python3
"""Fail-closed inspection for worktree-owned .tmp scratch (ticket 1119)."""

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


PREFIX = "worktree-tmp-guard:"
CITATION = re.compile(r"(?<![A-Za-z0-9_-])\.tmp(?:/|(?=[\s`'\".,;:)]|$))")


class Blocked(Exception):
    pass


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError as exc:
        raise Blocked(f"could not run git {args[0]}: {exc}") from exc
    if check and result.returncode:
        raise Blocked(f"could not inspect Git {args[0]} (exit {result.returncode})")
    return result


def common_dir(repo: Path) -> Path:
    value = run_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    if not value:
        raise Blocked("could not resolve common Git metadata")
    return Path(value)


def register_tmp_exclude(worktree_arg: Path) -> int:
    worktree = worktree_arg.resolve(strict=True)
    root = Path(run_git(worktree, "rev-parse", "--show-toplevel").stdout.strip()).resolve(strict=True)
    if worktree != root:
        raise Blocked("candidate path is not a worktree root")
    exclude = common_dir(root) / "info" / "exclude"
    try:
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a+", encoding="utf-8") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            stream.seek(0)
            lines = stream.read().splitlines()
            if "/.tmp/" not in lines:
                stream.seek(0, os.SEEK_END)
                stream.write("\n/.tmp/\n")
                stream.flush()
    except OSError as exc:
        raise Blocked(f"could not register /.tmp/ in common info/exclude: {exc}") from exc
    print(f"{PREFIX} registered /.tmp/ in {exclude}")
    return 0


def integration_ref(repo: Path) -> str:
    symbolic = run_git(repo, "symbolic-ref", "-q", "refs/remotes/origin/HEAD", check=False)
    candidates = [symbolic.stdout.strip()] if symbolic.returncode == 0 else []
    candidates.extend(("refs/remotes/origin/main", "refs/remotes/origin/master",
                       "refs/heads/main", "refs/heads/master"))
    for ref in candidates:
        if not ref:
            continue
        result = run_git(repo, "rev-parse", "--verify", "-q", f"{ref}^{{commit}}", check=False)
        if result.returncode == 0:
            return ref
    raise Blocked("could not identify the integration branch")


def validate_exclude(repo: Path) -> None:
    exclude = common_dir(repo) / "info" / "exclude"
    try:
        lines = exclude.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise Blocked(f"common info/exclude is unavailable: {exc}") from exc
    if "/.tmp/" not in [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]:
        raise Blocked("common info/exclude lacks the /.tmp/ rule; Git status must keep .tmp as WIP")


def tracked_tmp(repo: Path, worktree: Path) -> bool:
    result = run_git(worktree, "ls-files", "-z", "--", ".tmp")
    return bool(result.stdout)


def tmp_stats(path: Path) -> tuple[int, int]:
    """Return regular-file/symlink count and allocated bytes without following links."""
    count = 0
    allocated = 0

    def add_stat(entry: Path) -> None:
        nonlocal count, allocated
        try:
            info = entry.lstat()
        except OSError as exc:
            raise Blocked(f"could not inspect {entry}: {exc}") from exc
        allocated += getattr(info, "st_blocks", 0) * 512 or info.st_size
        if entry != path and (stat.S_ISLNK(info.st_mode) or stat.S_ISREG(info.st_mode)):
            count += 1

    add_stat(path)
    def onerror(exc: OSError) -> None:
        raise Blocked(f"could not enumerate {path}: {exc}") from exc

    try:
        for current, dirs, files in os.walk(path, topdown=True, followlinks=False, onerror=onerror):
            current_path = Path(current)
            for name in list(dirs):
                entry = current_path / name
                add_stat(entry)
                if entry.is_symlink():
                    dirs.remove(name)
            for name in files:
                add_stat(current_path / name)
    except OSError as exc:
        raise Blocked(f"could not enumerate {path}: {exc}") from exc
    return count, allocated


def branch_anchor(repo: Path, branch: str) -> str:
    if not branch or run_git(repo, "check-ref-format", f"refs/heads/{branch}", check=False).returncode:
        raise Blocked("candidate branch name is invalid")
    ref = f"refs/heads/{branch}"
    result = run_git(repo, "reflog", "show", "--format=%H%x09%gs", ref, check=False)
    if result.returncode:
        raise Blocked("could not inspect branch reflog for citation coverage")
    # Reflog output is newest-first. The creation entry is the boundary between
    # inherited history (including base docs) and commits made on this branch.
    entries = list(reversed(result.stdout.splitlines()))
    anchors = [line.split("\t", 1)[0] for line in entries if "branch: Created from " in line]
    if not anchors:
        raise Blocked("branch creation point is unavailable; cannot bound commit citation coverage")
    anchor = anchors[-1]
    resolved = run_git(repo, "rev-parse", "--verify", "-q", f"{anchor}^{{commit}}", check=False)
    if resolved.returncode:
        raise Blocked("branch creation commit is unavailable; cannot inspect citation commits")
    return anchor


def worktrees(repo: Path) -> list[Path]:
    result = run_git(repo, "worktree", "list", "--porcelain", "-z")
    paths = []
    for field in result.stdout.split("\0"):
        if field.startswith("worktree "):
            paths.append(Path(field[len("worktree "):]))
    if not paths:
        raise Blocked("could not enumerate registered worktrees for verdict coverage")
    return paths


def verdict_contents(paths: list[Path]) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for root in dict.fromkeys(paths):
        try:
            root_info = root.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise Blocked(f"could not inspect verdict path {root}: {exc}") from exc
        if stat.S_ISLNK(root_info.st_mode):
            raise Blocked(f"verdict directory is a symlink: {root}")
        if not stat.S_ISDIR(root_info.st_mode):
            raise Blocked(f"verdict path is not a directory: {root}")

        def onerror(exc: OSError) -> None:
            raise Blocked(f"could not enumerate verdict files under {root}: {exc}")

        try:
            for current, dirs, files in os.walk(root, topdown=True, followlinks=False, onerror=onerror):
                current_path = Path(current)
                for name in list(dirs):
                    entry = current_path / name
                    if entry.is_symlink():
                        raise Blocked(f"could not inspect symlinked verdict directory: {entry}")
                for name in files:
                    entry = current_path / name
                    if entry.is_symlink():
                        raise Blocked(f"could not inspect symlinked verdict file: {entry}")
                    try:
                        found.append((entry, entry.read_text(encoding="utf-8")))
                    except (OSError, UnicodeError) as exc:
                        raise Blocked(f"could not read verdict file {entry}: {exc}") from exc
        except Blocked:
            raise
        except OSError as exc:
            raise Blocked(f"could not enumerate verdict files under {root}: {exc}") from exc
    return found


def citation_sources(repo: Path, worktree: Path, branch: str) -> list[tuple[str, str]]:
    anchor = branch_anchor(repo, branch)
    branch_ref = f"refs/heads/{branch}"
    commit_log = run_git(repo, "log", "--format=%B", f"{anchor}..{branch_ref}")
    sources: list[tuple[str, str]] = [(f"branch commits {anchor}..{branch_ref}", commit_log.stdout)]

    try:
        prs = subprocess.run(
            ["gh", "pr", "list", "--state", "all", "--head", branch,
             "--limit", "1000", "--json", "number,title,body"],
            cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError as exc:
        raise Blocked(f"could not inspect citation sources (gh unavailable): {exc}") from exc
    if prs.returncode:
        raise Blocked(f"could not inspect citation sources (gh exit {prs.returncode})")
    try:
        documents = json.loads(prs.stdout)
    except ValueError as exc:
        raise Blocked("could not inspect citation sources (invalid PR listing)") from exc
    if not isinstance(documents, list) or len(documents) >= 1000:
        raise Blocked("could not inspect citation sources (PR listing incomplete)")
    numbers: list[str] = []
    for pr in documents:
        if (not isinstance(pr, dict) or not isinstance(pr.get("number"), int)
                or not isinstance(pr.get("title"), str) or not isinstance(pr.get("body"), str)):
            raise Blocked("could not inspect citation sources (malformed PR record)")
        number = str(pr["number"])
        numbers.append(number)
        sources.append((f"PR #{number} body", pr["title"] + "\n" + pr["body"]))

    roots: list[Path] = candidate_verdict_roots(worktree)
    trees = worktrees(repo)
    for tree in trees:
        try:
            tree_info = tree.stat()
        except OSError as exc:
            raise Blocked(f"could not inspect registered worktree {tree}: {exc}") from exc
        if not stat.S_ISDIR(tree_info.st_mode):
            raise Blocked(f"registered worktree is unavailable: {tree}")
        for number in numbers:
            roots.extend((tree / ".panel" / number, tree / ".review" / number))
    for path, text in verdict_contents(roots):
        sources.append((str(path), text))
    return sources


def candidate_verdict_roots(worktree: Path) -> list[Path]:
    roots: list[Path] = []
    for parent in (worktree / ".panel", worktree / ".review"):
        try:
            parent_info = parent.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise Blocked(f"could not inspect candidate verdict directory {parent}: {exc}") from exc
        if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
            raise Blocked(f"candidate verdict directory is unavailable: {parent}")
        try:
            for entry in parent.iterdir():
                if entry.name.isdecimal():
                    roots.append(entry)
        except OSError as exc:
            raise Blocked(f"could not enumerate candidate verdicts under {parent}: {exc}") from exc
    return roots


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("register", "preflight", "removal"))
    parser.add_argument("repo", type=Path)
    parser.add_argument("worktree", type=Path, nargs="?")
    parser.add_argument("--branch")
    args = parser.parse_args()

    try:
        if args.mode == "register":
            if args.worktree is not None or args.branch:
                raise Blocked("register accepts exactly one worktree path")
            return register_tmp_exclude(args.repo)
        if args.worktree is None:
            raise Blocked(f"{args.mode} requires repository and worktree paths")
        worktree = args.worktree.resolve(strict=True)
        git_root = Path(run_git(worktree, "rev-parse", "--show-toplevel").stdout.strip()).resolve(strict=True)
        if worktree != git_root:
            raise Blocked("candidate path is not a worktree root")
        tmp = worktree / ".tmp"
        try:
            tmp_info = tmp.lstat()
        except FileNotFoundError:
            return 0
        except OSError as exc:
            raise Blocked(f"could not inspect .tmp: {exc}") from exc
        if stat.S_ISLNK(tmp_info.st_mode) or not stat.S_ISDIR(tmp_info.st_mode):
            raise Blocked(".tmp must be a real directory inside its owning worktree")
        validate_exclude(worktree)
        if tracked_tmp(worktree, worktree):
            raise Blocked("tracked .tmp content is WIP and must be promoted or removed explicitly")
        count, allocated = tmp_stats(tmp)
        print(f"{PREFIX} {worktree}: .tmp/: {count} files, {allocated} bytes")
        if args.mode == "preflight":
            return 0
        if not args.branch:
            raise Blocked("candidate branch is unknown; cannot inspect citation coverage")
        checked_out = run_git(worktree, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
        if checked_out.returncode or checked_out.stdout.strip() != args.branch:
            raise Blocked("supplied branch does not match the candidate worktree's symbolic HEAD")
        head = run_git(worktree, "rev-parse", "--verify", "HEAD")
        branch_tip = run_git(args.repo, "rev-parse", "--verify", f"refs/heads/{args.branch}^{{commit}}")
        if head.stdout.strip() != branch_tip.stdout.strip():
            raise Blocked("candidate worktree HEAD differs from the supplied branch tip")
        base = integration_ref(args.repo)
        ancestry = run_git(args.repo, "merge-base", "--is-ancestor", f"refs/heads/{args.branch}", base, check=False)
        if ancestry.returncode == 1:
            raise Blocked(f"branch {args.branch} is not proven integrated into {base}")
        if ancestry.returncode:
            raise Blocked(f"could not prove integration ancestry for {args.branch} into {base}")
        sources = citation_sources(args.repo, worktree, args.branch)
        hits = [name for name, text in sources if CITATION.search(text)]
        if hits:
            print(f"{PREFIX} citation found; retaining .tmp and worktree: {hits[0]}")
            return 1
        print(f"{PREFIX} citation coverage clear for {args.branch}")
        return 0
    except Blocked as exc:
        print(f"{PREFIX} BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Resolve a /gaze caller brief into the seats to launch and the files to review, or refuse it.

The brief is the inline form of the review request deferred to the dyne format
(ticket 1154): `seats=<a,b|none|auto>; scope=<all|A..B|paths:p,q>; why=<text>`.
The orchestrator decides it (ticket 1225); gaze runs exactly what resolves here,
and a brief it cannot honour is refused with a reason, never widened.

    gaze_brief.py resolve --brief <str> --base <ref> --head <ref> [--repo <dir>]

Prints `brief:`, `panel_seats:`, `simplify:`, `scope:` and `scope_files:` lines;
exit 0 resolved, 2 refused (`brief: refused — <reason>`).
"""

import argparse
import subprocess
import sys

CODE_SEATS = ("correctness", "consistency", "scope", "red-team", "doc-propagation")
PROSE_SEATS = ("referee", "venue-expert", "ai-tells", "editorial-brief")
SEATS = CODE_SEATS + PROSE_SEATS + ("simplify", "external")
KEYS = ("seats", "scope", "why")
DEFAULT = "seats=auto; scope=all"


class Refused(Exception):
    pass


def parse(brief: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in brief.split(";"):
        if not part.strip():
            continue
        key, sep, value = part.partition("=")
        key, value = key.strip(), value.strip()
        if not sep or key not in KEYS:
            raise Refused(f"unknown key {key!r} (known: {', '.join(KEYS)})")
        out[key] = value
    if "seats" not in out or not out["seats"]:
        raise Refused("no seats named (name them, or seats=none for adherence only)")
    out.setdefault("scope", "all")
    return out


def seats_of(value: str) -> tuple[list[str], str]:
    """Return the panel seats and the simplify flag a `seats=` value asks for."""
    if value in ("none", "auto"):
        return [value], "no" if value == "none" else "auto"
    names = [name.strip() for name in value.split(",") if name.strip()]
    unknown = [name for name in names if name not in SEATS]
    if unknown:
        raise Refused(f"unknown seat {', '.join(unknown)} (known: {', '.join(SEATS)}, none)")
    panel = [name for name in names if name != "simplify"]
    return panel or ["none"], "yes" if "simplify" in names else "no"


def git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def ancestor(repo: str, a: str, b: str) -> bool:
    return git(repo, "merge-base", "--is-ancestor", a, b).returncode == 0


def names(repo: str, *args: str) -> list[str]:
    result = git(repo, "diff", "--name-only", *args)
    if result.returncode:
        raise Refused(f"cannot read the diff: {result.stderr.strip()}")
    return result.stdout.split()


def scope_files(repo: str, scope: str, base: str, head: str) -> list[str]:
    changed = names(repo, f"{base}...{head}")
    if scope == "all":
        return changed
    if scope.startswith("paths:"):
        paths = [p.strip() for p in scope[len("paths:"):].split(",") if p.strip()]
        outside = [p for p in paths if p not in changed]
        if not paths or outside:
            raise Refused(f"path {', '.join(outside) or '(none)'} outside the diff")
        return paths
    start, sep, end = scope.partition("..")
    if not sep or not start or not end or end.startswith("."):
        raise Refused(f"scope {scope!r} is not all, A..B or paths:p,q")
    fork = git(repo, "merge-base", base, head).stdout.strip()
    for ref in (start, end):
        if git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode:
            raise Refused(f"commit {ref!r} does not resolve")
    if not (fork and ancestor(repo, fork, start) and ancestor(repo, start, end) and ancestor(repo, end, head)):
        raise Refused(f"range {scope} outside the diff {base}...{head}")
    files = names(repo, start, end)
    if not files:
        raise Refused(f"range {scope} is an empty range")
    return files


def resolve(brief: str, base: str, head: str, repo: str) -> list[str]:
    text = brief.strip() or DEFAULT
    fields = parse(text)
    panel, simplify = seats_of(fields["seats"])
    files = scope_files(repo, fields["scope"], base, head)
    shown = text if brief.strip() else f"default ({DEFAULT}; no caller brief)"
    return [
        f"brief: {shown}",
        f"panel_seats: {','.join(panel)}",
        f"simplify: {simplify}",
        f"scope: {fields['scope']}",
        f"scope_files: {' '.join(files)}",
    ]


def echo(brief: str, ran: list[str]) -> str:
    """The result comment's one line: what the caller asked for, then what ran against it."""
    return f"brief: {brief} → ran: {', '.join(ran)}"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    res = sub.add_parser("resolve")
    res.add_argument("--brief", default="")
    res.add_argument("--base", required=True)
    res.add_argument("--head", default="HEAD")
    res.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    try:
        lines = resolve(args.brief, args.base, args.head, args.repo)
    except Refused as reason:
        print(f"brief: refused — {reason}")
        return 2
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

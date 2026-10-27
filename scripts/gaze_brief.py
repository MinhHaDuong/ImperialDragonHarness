#!/usr/bin/env python3
"""Resolve a /gaze caller brief into the seats to launch and the files to review, or refuse it.

The brief is the inline form of the review request deferred to the dyne format
(ticket 1154): `seats=<a,b|none>; scope=<all|A..B|paths:p,q>; why=<text>`, with
`why` last (it may hold `;`). The orchestrator decides it (ticket 1225); gaze
runs exactly what resolves here, and a brief it cannot honour is refused with a
reason, never widened or narrowed.

    gaze_brief.py resolve --brief <str> --panel code|prose --base <ref> --head <ref> [--repo <dir>]

Prints `brief:`, `panel_seats:`, `simplify:`, `external:`, `scope:` and one
`scope_file:` line per file; exit 0 resolved, 2 refused (`brief: refused — <reason>`).
An empty brief is the default brief, `seats=auto`, for a caller that sends none.
"""

import argparse
import re
import subprocess
import sys

PANELS = {
    "code": ("correctness", "consistency", "scope", "red-team", "doc-propagation", "simplify", "external"),
    "prose": ("referee", "venue-expert", "ai-tells", "editorial-brief"),
}
KEYS = ("seats", "scope", "why")
DEFAULT = "seats=auto; scope=all"
EDITORIAL_BRIEF = "docs/editorial-brief.md"
LATER_KEY = re.compile(r";\s*(?:" + "|".join(KEYS) + r")\s*=", re.IGNORECASE)  # `;SCOPE=` inside why= must not slip past
LINE_BREAKERS = "\x85\u2028\u2029"


def unsafe(text: str) -> bool:
    """True when the text holds a character that would start a new output line."""
    return any(ord(ch) < 32 or ch in LINE_BREAKERS for ch in text)


class Refused(Exception):
    pass


def parse(brief: str) -> dict[str, str]:
    if unsafe(brief):
        raise Refused("control character in the brief")
    out: dict[str, str] = {}
    rest = brief
    while rest.strip():
        part, _, rest = rest.partition(";")
        key, sep, value = part.partition("=")
        key = key.strip()
        if key == "why" and sep:
            value, rest = value + (";" + rest if rest else ""), ""
            if LATER_KEY.search(value):
                raise Refused("why= must come last (a key after it would be swallowed)")
        if not sep or key not in KEYS:
            raise Refused(f"unknown key {key!r} (known: {', '.join(KEYS)})")
        if key in out:
            raise Refused(f"duplicate key {key!r}")
        out[key] = value.strip()
    if not out.get("seats"):
        raise Refused("no seats named (name them, or seats=none for adherence only)")
    out.setdefault("scope", "all")
    return out


def seats_of(value: str, panel: str, repo: str, head: str) -> dict[str, str]:
    """Return the panel roster and the simplify and external flags a `seats=` value asks for."""
    if value in ("none", "auto"):
        flag = "no" if value == "none" else "auto"
        return {"panel_seats": value, "simplify": flag, "external": flag}
    names = [name.strip() for name in value.split(",")]
    if "" in names:
        raise Refused(f"empty seat name in {value!r}")
    if len(set(names)) != len(names):
        raise Refused(f"duplicate seat in {value!r}")
    known = PANELS[panel]
    unknown = [name for name in names if name not in known]
    if unknown:
        raise Refused(f"unknown seat {', '.join(unknown)} for the {panel} panel (known: {', '.join(known)}, none)")
    if "editorial-brief" in names and git(repo, "cat-file", "-e", f"{head}:{EDITORIAL_BRIEF}").returncode:
        raise Refused(f"seat editorial-brief needs {EDITORIAL_BRIEF}, absent at {head}")
    panel_seats = [name for name in names if name not in ("simplify", "external")]
    return {
        "panel_seats": ",".join(panel_seats) or "none",
        "simplify": "yes" if "simplify" in names else "no",
        "external": "yes" if "external" in names else "no",
    }


def git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def ancestor(repo: str, a: str, b: str) -> bool:
    return git(repo, "merge-base", "--is-ancestor", a, b).returncode == 0


def names(repo: str, *args: str) -> list[str]:
    result = git(repo, "diff", "-z", "--name-only", *args)
    if result.returncode:
        raise Refused(f"cannot read the diff: {result.stderr.strip()}")
    return [name for name in result.stdout.split("\0") if name]


def scope_files(repo: str, scope: str, base: str, head: str) -> list[str]:
    changed = names(repo, f"{base}...{head}")
    if scope == "all":
        return changed
    if scope.startswith("paths:"):
        paths = scope[len("paths:"):].split(",")
        outside = [p for p in paths if p not in changed]
        if not scope[len("paths:"):] or outside:
            raise Refused(f"path {', '.join(repr(p) for p in outside) or '(none)'} outside the diff")
        if len(set(paths)) != len(paths):
            raise Refused("duplicate path in scope")
        return paths
    start, sep, end = scope.partition("..")
    if not sep or not start or not end or end.startswith("."):
        raise Refused(f"scope {scope!r} is not all, A..B or paths:p,q")
    fork = git(repo, "merge-base", base, head).stdout.strip()
    for ref in (start, end):
        if git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").returncode:
            raise Refused(f"commit {ref!r} does not resolve")
    if not (fork and ancestor(repo, fork, start) and ancestor(repo, start, end) and ancestor(repo, end, head)):
        raise Refused(f"range {scope} outside the diff {base}...{head} (after a rebase, use paths:)")
    files = [name for name in names(repo, start, end) if name in changed]
    if not files:
        raise Refused(f"range {scope} is an empty range")
    return files


def resolve(brief: str, panel: str, base: str, head: str, repo: str) -> list[str]:
    if brief.strip():
        fields = parse(brief)
        if fields["seats"] == "auto":
            raise Refused("seats=auto is the default brief; a caller names its seats or none")
        shown = brief.strip()
    else:
        fields = parse(DEFAULT)
        shown = f"default ({DEFAULT}; no caller brief)"
    seats = seats_of(fields["seats"], panel, repo, head)
    files = scope_files(repo, fields["scope"], base, head)
    if any(unsafe(name) for name in files):
        raise Refused("a file name in scope holds a control character; name the scope by paths without it")
    return [f"brief: {shown}", *(f"{key}: {value}" for key, value in seats.items()), f"scope: {fields['scope']}"] + [
        f"scope_file: {name}" for name in files
    ]


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    res = sub.add_parser("resolve")
    res.add_argument("--brief", default="")
    res.add_argument("--panel", choices=sorted(PANELS), required=True)
    res.add_argument("--base", required=True)
    res.add_argument("--head", default="HEAD")
    res.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    try:
        lines = resolve(args.brief, args.panel, args.base, args.head, args.repo)
    except Refused as reason:
        print(f"brief: refused — {reason}")
        return 2
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

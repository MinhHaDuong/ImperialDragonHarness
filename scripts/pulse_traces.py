#!/usr/bin/env python3
"""Measure how long agents wait on test and gate commands, from session traces.

`collect` prints the full table for one project. `survey` is the short form for
the end-of-day wrap-up: it prints one line per gate that waited long enough to
be worth a consultation, nothing when the traces were read and are clean, and a
"not checked" line when they could not be read, so that silence never stands for
"could not look".

Only Claude Code's trace layout is read (one directory per working directory,
one JSONL file per session, timestamps on tool calls and their results). A
command's wait is the gap between its call and its result; background commands
return at once, so they are counted apart and never as waiting. The classifier
is a heuristic over the command text: it unwraps `time`, `timeout`, `uv run`,
env assignments and `raid-gate.py`, and ignores commands that merely mention a
gate (a commit message, a grep, a heredoc). A project's own gate names are added
with `--pattern`.
"""

import argparse
import json
import math
import re
import shlex
import statistics
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

GATE_TARGET = re.compile(r"(?:^|[-_])(?:check|tests?|lint|smart)(?:$|[-_])")
ENV_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
TRANSPARENT = {"time", "nohup", "nice", "command", "exec", "env", "rtk", "proxy"}
UV_VALUE_FLAGS = {"--with", "--extra", "--group", "--python", "-p", "--project",
                  "--directory", "--env-file", "--with-requirements", "--package"}
MAKE_VALUE_FLAGS = {"-C", "-f", "-I", "-o", "-W", "-l", "--directory", "--file"}
TIMEOUT_VALUE_FLAGS = {"-s", "-k", "--signal", "--kill-after"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n(?:.*?\n)?[ \t]*\2[ \t]*(?=\n|$)", re.DOTALL)

# A survey line is worth the author's attention when a gate ran often enough
# and waited long enough; both bounds are flags of the command line.
MIN_RUNS = 3
P90_SECONDS = 120
WAITED_MINUTES = 20
TYPICAL_SECONDS = 30  # a high total of quick runs is use, not a speed bump
LINES_SHOWN = 3


@dataclass
class Row:
    gate: str
    seconds: float
    command: str
    session: str
    when: datetime


@dataclass
class Collected:
    foreground: list[Row]
    background: int
    unpaired: int
    sessions: int
    directories: int
    unreadable: int = 0
    dropped: int = 0  # negative durations


def encode_project(path: Path) -> str:
    """Claude Code names a project's trace directory after its path."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def _segments(command: str) -> list[str]:
    """Split a shell line at `&&`, `||`, `|`, `;` and newlines outside quotes."""
    out: list[str] = []
    buf: list[str] = []
    quote = ""
    i = 0
    while i < len(command):
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == "\\" and quote == '"' and i + 1 < len(command):
                buf.append(command[i + 1])
                i += 1
            elif ch == quote:
                quote = ""
        elif ch in "'\"":
            quote = ch
            buf.append(ch)
        elif ch == "\\" and i + 1 < len(command):
            buf.extend((ch, command[i + 1]))
            i += 1
        elif command.startswith(("&&", "||"), i):
            out.append("".join(buf))
            buf = []
            i += 1
        elif ch in ";\n|":
            out.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1
    out.append("".join(buf))
    return out


def _strip_heredocs(command: str) -> str:
    return HEREDOC.sub(lambda match: match.group(0).split("\n", 1)[0], command)


def _unwrap(tokens: list[str]) -> list[str]:
    """Drop env assignments, timers and runners that only launch the real command."""
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if ENV_ASSIGNMENT.match(token) or token in TRANSPARENT:
            i += 1
        elif token == "timeout":
            i += 1
            while i < len(tokens) and tokens[i].startswith("-"):
                i += 2 if tokens[i] in TIMEOUT_VALUE_FLAGS else 1
            i += 1
        elif token == "uv" and tokens[i + 1:i + 2] == ["run"]:
            i += 2
            while i < len(tokens) and tokens[i].startswith("-"):
                i += 2 if tokens[i] in UV_VALUE_FLAGS else 1
        else:
            break
    return tokens[i:]


def _make_target(args: list[str]) -> str:
    i = 0
    while i < len(args):
        token = args[i]
        if token in MAKE_VALUE_FLAGS:
            i += 1
        elif token == "-j" and args[i + 1:i + 2] and args[i + 1].isdigit():
            i += 1
        elif not token.startswith("-") and "=" not in token:
            return token.rstrip(")}")
        i += 1
    return ""


def _classify(tokens: list[str]) -> list[str]:
    if not tokens:
        return []
    base = Path(tokens[0]).name
    if base in ("pytest", "py.test"):
        return ["pytest"]
    if base == "make":
        target = _make_target(tokens[1:])
        return [f"make {target}"] if GATE_TARGET.search(target) else []
    if re.fullmatch(r"python[0-9.]*", base):
        rest = tokens[1:]
        if rest[:2] == ["-m", "pytest"]:
            return ["pytest"]
        script = Path(rest[0]).name if rest and not rest[0].startswith("-") else ""
        if script == "scoped-check.py":
            return ["scoped-check"]
        if script == "raid-gate.py" and "--" in rest:
            return _classify(_unwrap(rest[rest.index("--") + 1:]))
    return []


def gate_classes(command: str, extra: tuple[str, ...] | list[str] = ()) -> list[str]:
    """The gates a shell command runs, in order; empty when it only mentions them."""
    classes: list[str] = []
    for segment in _segments(_strip_heredocs(command)):
        segment = segment.strip().lstrip("({ ")
        try:
            tokens = shlex.split(segment)
        except ValueError:
            tokens = segment.split()
        tokens = _unwrap(tokens)
        found = _classify(tokens)
        if not found:
            text = " ".join(tokens)
            for pattern in extra:
                match = re.match(pattern, text)
                if match:
                    found = [match.group(0)]
                    break
        classes += found
    return classes


def _gate_label(classes: list[str]) -> str:
    """A chain waits as one; name what it chains rather than a catch-all."""
    return " + ".join(dict.fromkeys(classes))


def project_directories(root: Path, project: Path) -> list[Path]:
    """Trace directories of the project and of its worktrees."""
    if not root.is_dir():
        return []
    prefixes = {encode_project(project), encode_project(project.resolve())}
    return sorted(
        entry for entry in root.iterdir()
        if entry.is_dir() and any(entry.name == p or entry.name.startswith(p + "--claude-worktrees-") for p in prefixes)
    )


def _parse_time(stamp: object) -> datetime | None:
    if not isinstance(stamp, str):
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _blocks(line: str) -> tuple[datetime | None, list[dict]]:
    if '"tool_use' not in line:
        return None, []
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return None, []
    content = (event.get("message") or {}).get("content")
    blocks = [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []
    return _parse_time(event.get("timestamp")), blocks


def _read_session(path: Path, since: datetime, extra: tuple[str, ...]) -> tuple[list[Row], int, int, bool, int]:
    pending: dict[str, tuple[datetime, str, str, bool]] = {}
    rows: list[Row] = []
    background = 0
    active = False
    dropped = 0
    for line in path.read_text(errors="replace").splitlines():
        when, blocks = _blocks(line)
        if when is None:
            continue
        for block in blocks:
            if block.get("type") == "tool_use" and block.get("name") == "Bash" and when >= since:
                active = True
                spec = block.get("input") or {}
                command = str(spec.get("command", ""))
                classes = gate_classes(command, extra)
                if not classes:
                    continue
                if spec.get("run_in_background"):
                    background += 1
                else:
                    pending[str(block.get("id"))] = (when, command, _gate_label(classes), True)
            elif block.get("type") == "tool_result" and str(block.get("tool_use_id")) in pending:
                start, command, gate, _ = pending.pop(str(block["tool_use_id"]))
                seconds = (when - start).total_seconds()
                if seconds >= 0:
                    rows.append(Row(gate, seconds, command, path.stem, start))
                else:
                    dropped += 1
    return rows, background, len(pending), active, dropped


def collect(root: Path, project: Path, days: float, now: datetime | None = None,
            extra: tuple[str, ...] | list[str] = ()) -> Collected:
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    stale_before = time.time() - (days + 1) * 86400
    result = Collected([], 0, 0, 0, 0)
    for directory in project_directories(root, project):
        result.directories += 1
        for path in sorted(directory.rglob("*.jsonl")):
            try:
                if path.stat().st_mtime < stale_before:
                    continue
                rows, background, unpaired, active, dropped = _read_session(path, since, tuple(extra))
            except (OSError, AttributeError, TypeError, ValueError):
                result.unreadable += 1
                continue
            result.foreground += rows
            result.background += background
            result.unpaired += unpaired
            result.dropped += dropped
            result.sessions += active
    return result


def _p90(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.9 * len(ordered)) - 1)]


def _first_and_later(rows: list[Row]) -> tuple[list[float], list[float]]:
    """Split one gate's waits into each session's first run and the rest.

    A first run that is much slower than the later ones points at set-up cost
    (environment sync, cold caches, data fetch) before it points at the tests.
    """
    first: dict[str, Row] = {}
    for row in sorted(rows, key=lambda r: r.when):
        first.setdefault(row.session, row)
    firsts = {id(row) for row in first.values()}
    return ([r.seconds for r in rows if id(r) in firsts],
            [r.seconds for r in rows if id(r) not in firsts])


def summarise(rows: list[Row]) -> dict[str, dict]:
    by_gate: dict[str, list[Row]] = {}
    for row in rows:
        by_gate.setdefault(row.gate, []).append(row)
    summary = {}
    for gate, members in sorted(by_gate.items(), key=lambda item: -sum(r.seconds for r in item[1])):
        values = [r.seconds for r in members]
        first, later = _first_and_later(members)
        summary[gate] = {
            "runs": len(values),
            "median_s": round(statistics.median(values)),
            "p90_s": round(_p90(values)),
            "max_s": round(max(values)),
            "total_min": round(sum(values) / 60),
            "first_of_session_median_s": round(statistics.median(first)) if first else None,
            "later_median_s": round(statistics.median(later)) if later else None,
        }
    return summary


def survey(root: Path, project: Path, days: float, now: datetime | None = None,
           extra: tuple[str, ...] | list[str] = (), min_runs: int = MIN_RUNS,
           p90_seconds: float = P90_SECONDS, waited_minutes: float = WAITED_MINUTES) -> list[str]:
    collected = collect(root, project, days, now, extra)
    if not collected.sessions:
        return [f"pulse: not checked (no session traces with shell activity for "
                f"{project.name} under {root} in the last {days:g}d)"]
    if not collected.foreground and not collected.background and collected.unpaired:
        return [f"pulse: checked {collected.sessions} sessions in {project.name} but could not tell: "
                f"every gate call lacked a result (unpaired {collected.unpaired}, "
                f"{collected.unreadable} unreadable)"]
    if not collected.foreground and not collected.background:
        return [f"pulse: checked {collected.sessions} sessions in {project.name} and recognised no test "
                f"or gate command; a project-specific gate name needs --pattern"]
    flagged = []
    for gate, stats in summarise(collected.foreground).items():
        if stats["runs"] >= min_runs and (
                stats["p90_s"] >= p90_seconds
                or (stats["total_min"] >= waited_minutes and stats["median_s"] >= TYPICAL_SECONDS)):
            flagged.append(
                f'pulse: "{gate}" ran {stats["runs"]}x in {days:g}d in {project.name}: '
                f'median {stats["median_s"]}s, p90 {stats["p90_s"]}s, '
                f'{stats["total_min"]} min waited. A consultation may help: /pulse')
    if len(flagged) > LINES_SHOWN:
        extra_count = len(flagged) - LINES_SHOWN
        flagged = flagged[:LINES_SHOWN] + [f"pulse: {extra_count} more gate(s) over the same thresholds"]
    if not flagged and (collected.unreadable or collected.unpaired or collected.dropped):
        flagged = [f"pulse: checked {collected.sessions} sessions in {project.name}, "
                   f"{collected.unreadable} unreadable, {collected.unpaired} unpaired, "
                   f"{collected.dropped} dropped; the check was partial"]
    return flagged


def _print_table(collected: Collected, project: Path, days: float) -> None:
    print(f"{project.name}: {len(collected.foreground)} foreground gate runs in {days:g}d "
          f"({collected.sessions} sessions, {collected.background} background, "
          f"{collected.unpaired} unpaired, {collected.unreadable} unreadable)")
    print(f"{'gate':32s} {'runs':>5s} {'median':>7s} {'p90':>6s} {'max':>6s} {'total':>7s}")
    for gate, s in summarise(collected.foreground).items():
        print(f"{gate[:32]:32s} {s['runs']:5d} {s['median_s']:6d}s {s['p90_s']:5d}s "
              f"{s['max_s']:5d}s {s['total_min']:5d}m")
    print("first run of a session vs later runs (median):")
    for gate, s in list(summarise(collected.foreground).items())[:6]:
        if s["later_median_s"] is not None and s["runs"] >= 4:
            print(f"  {gate[:32]:32s} first {s['first_of_session_median_s']}s, later {s['later_median_s']}s")
    print("longest waits:")
    for row in sorted(collected.foreground, key=lambda r: -r.seconds)[:5]:
        print(f"  {row.seconds:6.0f}s  {row.when:%Y-%m-%d}  {row.session[:8]}  {row.command[:90]!r}")


def _common(parser: argparse.ArgumentParser, days: float) -> None:
    parser.add_argument("--project", type=Path, default=Path.cwd(),
                        help="project working directory (worktrees included); default: current directory")
    parser.add_argument("--traces", type=Path, default=Path.home() / ".claude" / "projects",
                        help="trace root; default: Claude Code's project trace directory")
    parser.add_argument("--days", type=float, default=days, help="look back this many days")
    parser.add_argument("--pattern", action="append", default=[],
                        help="regex for a project-specific gate name, matched at the start of a command")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)
    full = sub.add_parser("collect", help="table of gate waits for one project")
    _common(full, 28)
    full.add_argument("--json", action="store_true")
    brief = sub.add_parser("survey", help="one line per gate worth a consultation; for the wrap-up")
    _common(brief, 7)
    args = parser.parse_args(argv)
    project = args.project.resolve() if args.project.exists() else args.project
    if args.command == "survey":
        for line in survey(args.traces, project, args.days, extra=args.pattern):
            print(line)
        return 0
    collected = collect(args.traces, project, args.days, extra=args.pattern)
    if args.json:
        longest = sorted(collected.foreground, key=lambda r: -r.seconds)[:5]
        print(json.dumps({
            "project": str(project), "days": args.days, "sessions": collected.sessions,
            "foreground_runs": len(collected.foreground), "background": collected.background,
            "unpaired": collected.unpaired, "unreadable": collected.unreadable, "gates": summarise(collected.foreground),
            "longest": [{"gate": r.gate, "seconds": round(r.seconds), "when": r.when.isoformat(),
                         "session": r.session, "command": r.command[:200]} for r in longest],
        }, indent=2))
    else:
        _print_table(collected, project, args.days)
    return 0


if __name__ == "__main__":
    sys.exit(main())

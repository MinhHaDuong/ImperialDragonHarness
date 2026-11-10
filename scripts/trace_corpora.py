#!/usr/bin/env python3
"""The corpora of every runtime on this host, and how a trace script says which it read (ticket 1517).

trace-stats.py, trace-friction.py and trace-wall-time.py read every corpus below by default and
report each one as `read`, `not read` (with the reason) or `could not look` (with the reason), the
pattern of trace-compact-audit.py's RUNTIMES table. A corpus is one root of one runtime:

    Claude Code  $CLAUDE_CONFIG_DIR/projects or ~/.claude/projects (each script walks it itself)
    Codex        $CODEX_HOME or ~/.codex: rollout-*.jsonl under sessions/ and archived_sessions/
    Pi           $PI_CODING_AGENT_DIR/sessions or ~/.pi/agent/sessions: *.jsonl
    Pi spool     <archive root>/spool/<host>/pi: *.jsonl of seats launched with --session-dir

A measure a runtime cannot supply goes in its entry's `not_measured` map (measure -> reason), never
as a zero. This host only; other hosts are not read. Stdlib only, no CLI.
"""

import importlib.util
import json
import logging
import os
import socket
from pathlib import Path

_SPOOL_SPEC = importlib.util.spec_from_file_location(
    "transcript_spool", Path(__file__).resolve().parent / "transcript_spool.py"
)
transcript_spool = importlib.util.module_from_spec(_SPOOL_SPEC)
_SPOOL_SPEC.loader.exec_module(transcript_spool)

CLAUDE, CODEX, PI, PI_SPOOL = "Claude Code", "Codex", "Pi", "Pi spool"
CORPORA = (CLAUDE, CODEX, PI, PI_SPOOL)
RUNTIME = {CLAUDE: "claude", CODEX: "codex", PI: "pi", PI_SPOOL: "pi"}  # trace_events runtime names
log = logging.getLogger("trace_corpora")
UNKNOWN_SPOOL = Path("(archive root unknown)")


class CouldNotLook(Exception):
    """A corpus root is absent or unreadable as a whole."""


def default_codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or "~/.codex").expanduser()


def default_pi_spool() -> Path:
    try:
        return transcript_spool.spool_dir("pi")
    except RuntimeError:  # archive root unknown: the corpus is then reported could not look
        return UNKNOWN_SPOOL


def default_roots() -> dict:
    live = transcript_spool.live_roots()
    return {CLAUDE: live["claude"], CODEX: default_codex_home(), PI: live["pi"], PI_SPOOL: default_pi_spool()}


def add_root_flags(parser, claude_help: str = "Root of the Claude Code trace corpus") -> None:
    """The four corpus flags; `--projects-dir` keeps its old name and meaning."""
    roots = default_roots()
    parser.add_argument("--projects-dir", type=Path, default=roots[CLAUDE],
                        help=f"{claude_help} (default: $CLAUDE_CONFIG_DIR/projects or ~/.claude/projects)")
    parser.add_argument("--codex-home", type=Path, default=roots[CODEX],
                        help="Codex home holding sessions/ and archived_sessions/ (default: $CODEX_HOME or ~/.codex)")
    parser.add_argument("--pi-sessions", type=Path, default=roots[PI],
                        help="Pi live session root (default: $PI_CODING_AGENT_DIR/sessions or ~/.pi/agent/sessions)")
    parser.add_argument("--pi-spool", type=Path, default=roots[PI_SPOOL],
                        help="Pi archive spool of launched seats (default: <archive>/spool/<host>/pi)")


def roots_from_args(args) -> dict:
    return {CLAUDE: args.projects_dir, CODEX: args.codex_home, PI: args.pi_sessions, PI_SPOOL: args.pi_spool}


def normalize_roots(roots) -> dict:
    """A bare path is Claude Code's alone (the scripts' call shape before ticket 1517)."""
    if not isinstance(roots, dict):
        return {CLAUDE: roots}
    return roots


def corpus_files(name: str, root: Path) -> list[Path]:
    """Transcript files of the Codex or Pi corpus at `root`; raises CouldNotLook when it is absent."""
    root = Path(root)
    if name == CODEX:
        dirs = [root / d for d in ("sessions", "archived_sessions")]
        if not any(d.is_dir() for d in dirs):
            raise CouldNotLook(f"no Codex sessions under {root}")
        return [p for d in dirs if d.is_dir() for p in sorted(d.rglob("rollout-*.jsonl"))]
    if name in (PI, PI_SPOOL):
        if not root.is_dir():
            raise CouldNotLook(f"no Pi sessions at {root}")
        return sorted(root.rglob("*.jsonl"))
    raise ValueError(f"{name}: each script walks the Claude Code corpus itself")


def recent_files(name: str, root: Path, cutoff_ts: float) -> list[Path]:
    """corpus_files modified at or after `cutoff_ts`; a file that vanished is passed over."""
    out = []
    for path in corpus_files(name, root):
        try:
            if path.stat().st_mtime >= cutoff_ts:
                out.append(path)
        except OSError:
            continue
    return out


def codex_is_subagent(lines) -> bool:
    """A Codex rollout whose session_meta `source` is an object was spawned by another agent."""
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict) and row.get("type") == "session_meta":
            payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
            return isinstance(payload.get("source"), dict)
    return False


def entry(name: str, root, status: str, reason: str | None = None, **measures) -> dict:
    out = {"name": name, "root": str(root) if root is not None else None, "status": status}
    if reason:
        out["reason"] = reason
    out.update(measures)
    return out


def report_keys(entries: list[dict]) -> dict:
    """The JSON keys every trace script adds: host, entries, and the names read and not read."""
    return {
        "host": socket.gethostname().split(".")[0],
        "runtimes": entries,
        "runtimes_read": [e["name"] for e in entries if e["status"] == "read"],
        "runtimes_not_read": [e["name"] for e in entries if e["status"] != "read"],
    }


def render(entries: list[dict], counted: str) -> list[str]:
    """One line per corpus: what was read, what not, what could not be looked at, and what is not measured."""
    lines = []
    for e in entries:
        if e["status"] == "read":
            line = f"Read: {e['name']} under {e['root']}: {counted.format(**e)}"
        elif e["status"] == "could not look":
            line = f"COULD NOT LOOK at {e['name']}: {e['reason']}; the counts leave it out"
        else:
            line = f"NOT READ: {e['name']}, {e['reason']}; the counts leave it out"
        lines.append(line)
        for measure, why in (e.get("not_measured") or {}).items():
            lines.append(f"  not measured on {e['name']}: {measure} ({why})")
    return lines


def none_read(entries: list[dict]) -> bool:
    """True, after logging why, when no corpus at all was read: the caller then exits non-zero."""
    if any(e["status"] == "read" for e in entries):
        return False
    log.error("could not look: %s", "; ".join(f"{e['name']}: {e.get('reason', '')}" for e in entries))
    return True

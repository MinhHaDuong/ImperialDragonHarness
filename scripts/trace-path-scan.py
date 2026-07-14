#!/usr/bin/env python3
"""Path-access allow/forbid scan over the agent tool trace — ticket 0289.

Child of tracker 0266 (pillage manifest, technique 1;
docs/pillage-0266-agentic-reproduction-2026-07-12.md). verify-adherence checks
the diff and rule files, but nothing inspects the tool-call trace for
out-of-scope file access. The paper's guardrail (arXiv:2604.21965 App. B.3)
catches an agent that READS a forbidden path even when it never writes it — a
scope-violation class a diff-only check structurally misses.

Pure-Python, zero LLM tokens. Walks a single session-trace JSONL (the same
record shape scripts/trace-stats.py parses) and flags every
Read/Edit/Write/NotebookEdit/Bash call whose path argument falls in one of two
high-precision forbidden classes:

  1. Credential/secret files — ~/.ssh, ~/.aws, ~/.netrc, bash-env.sh,
     .git-credentials.
  2. ANOTHER session's worktree — a /worktrees/<segment>/ whose segment differs
     from the caller's own worktree-root segment.

Deliberately NOT a blanket "outside the worktree" rule: that would false-positive
on legitimate reads of shared rules/ and skills/ files. The two classes above are
the ones a diff never reveals and a human would call scope violations.
"""

import argparse
import importlib.util
import json
import logging
import re
import sys
from pathlib import Path

log = logging.getLogger("trace-path-scan")

# Reuse trace-stats.py for its PATH_TOOLS convention (importlib sibling pattern,
# precedent scripts/trace-compact-audit.py). We keep our own tolerant JSONL loop
# rather than threading through ts.parse_trace_file — this scan needs per-line
# numbers and a much narrower record view.
_TS_SPEC = importlib.util.spec_from_file_location(
    "trace_stats", Path(__file__).resolve().parent / "trace-stats.py"
)
ts = importlib.util.module_from_spec(_TS_SPEC)
_TS_SPEC.loader.exec_module(ts)

# (compiled pattern, human reason). High precision — each class is one a
# diff-only check cannot see and a reviewer would call a scope violation.
# The credential-directory patterns must match the *bare* directory too — a
# `cd ~/.ssh` (no trailing slash, extracted as the token `~/.ssh`) is itself the
# sensitive act, independent of the relative filename read afterward. So `.ssh`
# and `.aws` are anchored by a following `/` OR end-of-string, not a mandatory
# trailing slash.
FORBIDDEN_PATH_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"/\.ssh(?:/|$)"), "ssh credentials directory"),
    (re.compile(r"/\.aws(?:/|$)"), "aws credentials directory"),
    (re.compile(r"/\.netrc$"), "netrc credentials file"),
    (re.compile(r"bash-env\.sh$"), "secret-loading bash-env.sh"),
    (re.compile(r"/\.git-credentials$"), "git-credentials file"),
)

# Captures the segment immediately under a worktrees/ dir — the per-session
# discriminator. A path whose segment differs from the caller's own worktree
# root belongs to another session.
WORKTREE_RE = re.compile(r"/worktrees/([^/]+)")

# A path-like token inside a Bash command: a run starting with / or ~ (absolute
# or home-relative), bounded on the left by start-of-string, whitespace, a quote,
# or `=` — so `cat "~/.ssh/id_rsa"` and `FILE=/root/.aws/creds` are caught, not
# only the bare `cat ~/.aws/credentials` form. Good enough without a full shell
# parse; the classifier is narrow enough that an over-matched token is harmless.
BASH_PATH_RE = re.compile(r"(?:^|(?<=[\s\"'=]))([~/][^\s'\"|;&><]*)")


def extract_bash_paths(command: str) -> list[str]:
    """Path-like tokens (absolute or ~-relative) inside a Bash command string."""
    return BASH_PATH_RE.findall(command or "")


def tool_paths(name: str, tool_input: dict) -> list[str]:
    """Every filesystem path a single tool call touches.

    For path tools we read both `file_path` and `notebook_path` — the field name
    for NotebookEdit is inconsistent across the existing harness code, so we take
    whichever is present defensively. For Bash we extract path tokens from the
    command.
    """
    if name in ts.PATH_TOOLS:
        paths = []
        for field in ("file_path", "notebook_path"):
            value = tool_input.get(field)
            if value:
                paths.append(str(value))
        return paths
    if name == "Bash":
        return extract_bash_paths(str(tool_input.get("command", "")))
    return []


def _worktree_segment(path: str) -> str | None:
    m = WORKTREE_RE.search(path)
    return m.group(1) if m else None


def classify_path(path: str, own_worktree_segment: str | None = None) -> str | None:
    """Return a forbidden-class reason for `path`, or None if allowed.

    `own_worktree_segment` is the caller's own worktree segment, already
    extracted once by the caller — not the raw worktree-root path — so a
    scan over many paths doesn't re-derive the same constant on every call.
    """
    for pattern, reason in FORBIDDEN_PATH_PATTERNS:
        if pattern.search(path):
            return reason
    if own_worktree_segment:
        seen = _worktree_segment(path)
        if seen and seen != own_worktree_segment:
            return f"another session's worktree ({seen})"
    return None


def scan_trace_for_forbidden_paths(
    trace_path: str | Path, worktree_root: str | None = None
) -> list[dict]:
    """Scan one trace JSONL for forbidden-path tool calls.

    Returns a list of {tool, path, reason, line}. Tolerant: malformed JSON lines
    are skipped. tool_use blocks are deduped by id (same rule as
    trace-stats.py) so a block repeated across content-block rows is scored once.
    """
    hits: list[dict] = []
    seen_tool_use_ids: set[str] = set()
    own_worktree_segment = _worktree_segment(worktree_root) if worktree_root else None
    with open(trace_path, encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            msg = rec.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                block_id = block.get("id")
                if block_id and block_id in seen_tool_use_ids:
                    continue
                if block_id:
                    seen_tool_use_ids.add(block_id)
                name = block.get("name", "?")
                tool_input = block.get("input") or {}
                if not isinstance(tool_input, dict):
                    continue
                for path in tool_paths(name, tool_input):
                    reason = classify_path(path, own_worktree_segment)
                    if reason:
                        hits.append(
                            {"tool": name, "path": path, "reason": reason, "line": line_no}
                        )
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan an agent tool-call trace for forbidden path access "
        "(credential files, other sessions' worktrees). Zero LLM tokens."
    )
    parser.add_argument("--trace", required=True, type=Path, help="Session-trace JSONL to scan.")
    parser.add_argument(
        "--worktree-root",
        default=None,
        help="The caller's own worktree root; enables the other-session-worktree class.",
    )
    parser.add_argument("--json", action="store_true", help="Emit hits as a JSON array.")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if not args.trace.exists():
        log.error("trace not found: %s", args.trace)
        return 2

    hits = scan_trace_for_forbidden_paths(args.trace, worktree_root=args.worktree_root)

    if args.json:
        print(json.dumps(hits, indent=2))
    else:
        for h in hits:
            log.info("%s:%d  %s touched %s — %s", args.trace, h["line"], h["tool"], h["path"], h["reason"])
        if not hits:
            log.info("no forbidden path access found in %s", args.trace)

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())

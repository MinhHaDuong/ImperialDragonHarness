#!/usr/bin/env python3
"""Missed compact/clear opportunity detector — ticket 0239, trace-doctor phase 2a.

Walks the session-trace corpus and, per agent, extracts the per-turn
cache_read trajectory (unique message.id order, same dedupe rule as
scripts/trace-stats.py) plus the positions of compaction boundaries
(`type: "system"` / `subtype: "compact_boundary"`) and `/clear` commands.

A *missed opportunity* is a run of >= --min-run consecutive turns whose
per-turn cache_read stays >= --threshold, uninterrupted by any compact or
clear. The recoverable $ is an UPPER BOUND counterfactual: had the agent
compacted at the start of the run, every later turn in the run would have
read the post-compact median context (observed across sessions that DID
compact) instead of its actual cache_read. Context re-growth after the
hypothetical compaction is ignored — hence upper bound.

Context length is the whole prompt of a turn: input, cache-read and
cache-creation tokens (ticket 1499; `--metric cache_read` gives the June audit's
older quantity). Besides runs, the audit counts main sessions: how many reached
each level, and how many went past the ceiling of their own main model, read
from skills/route/ceilings.json. Events are restricted to the window turn by
turn. A transcript it cannot read is counted and reported, never read as zero.

Runtimes (ticket 1508): the session counts cover every runtime in RUNTIMES that
has a reader, each from its own corpus root; the output names the host, each
runtime read, each one not read and each one it could not look at. Missed runs
and their dollar figures stay Claude Code only. The process exits non-zero only
when no corpus at all is readable. A transcript last modified before the window
start holds no event in it and is not opened (`files_seen` counts the others).

Other hosts (ticket 1519): this host is read live; by default every other host
is read from this host's transcript archive (scripts/transcript_spool.py), one
per directory of `raw/` besides this host's own, from `raw/<host>/<runtime>/`.
Each file's root comes from `transcript_spool.source_of`, Codex copies are
collapsed by `transcript_spool.one_per_rollout`, and a `.zst` copy is
decompressed in memory (trace_events.zstd_lines), never to disk. Each host is
named with the date of its newest archived file and the surfaces its copy holds
and lacks; a transcript touched within the last day is not archived yet. An
absent or unreadable copy is "could not look"; an archive root that cannot be
resolved, or an archive that holds no other host, leaves this host's counts and
names the fleet view as not available. `--local`, or an explicit corpus-root
flag, reads this host alone. Sessions are not deduplicated across hosts. Missed
runs and their dollar figures stay this host's.

Zero LLM/API calls; emits aggregates only, never trace content.
"""

import argparse
import csv
import importlib.util
import json
import logging
import re
import statistics
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("trace-compact-audit")

# Reuse the census module (pricing, dedupe conventions, corpus walker).
_TS_SPEC = importlib.util.spec_from_file_location(
    "trace_stats", Path(__file__).resolve().parent / "trace-stats.py"
)
ts = importlib.util.module_from_spec(_TS_SPEC)
_TS_SPEC.loader.exec_module(ts)
_SPOOL_SPEC = importlib.util.spec_from_file_location(
    "transcript_spool", Path(__file__).resolve().parent / "transcript_spool.py"
)
transcript_spool = importlib.util.module_from_spec(_SPOOL_SPEC)
_SPOOL_SPEC.loader.exec_module(transcript_spool)
te = ts._te  # trace_events, loaded by trace-stats: the archive's reader (zstd_lines)

# A real /clear record pairs the two tags across an actual newline; trace
# text *quoted* inside a session (e.g. trace-doctor work) keeps the JSON
# escape as literal backslash-n and so does not match.
CLEAR_RE = re.compile(
    r"<command-name>/?clear</command-name>\s*\n\s*<command-message>clear</command-message>"
)

# Used only if the corpus contains no compaction to take a median from.
DEFAULT_POST_COMPACT_TOKENS = 20_000

CEILINGS_PATH = Path(__file__).resolve().parent.parent / "skills" / "route" / "ceilings.json"
METRICS = ("prompt", "cache_read")
METRIC_LABEL = {
    "prompt": "whole prompt (input + cache read + cache creation)",
    "cache_read": "cache_read tokens only",
}
# The run floor, in turns: the length of a flagged run and the turns a session
# needs at a level to count there. The levels themselves come from the
# ceilings data (`levels_for`).
MIN_RUN = 30
LONG_SESSION_TURNS = 100


class CouldNotLook(Exception):
    """The corpus cannot be read at all: not an empty result."""


class FleetUnavailable(Exception):
    """This host's archive cannot give the other hosts: no root, no archive, or no other host in it."""


def _lines(path: Path):
    """Lines of one transcript: a plain file streamed, a `.zst` archive copy decompressed in memory
    by trace_events.zstd_lines (nothing written). A copy zstd cannot decompress raises OSError."""
    path = Path(path)
    if path.suffix == ".zst":
        try:
            yield from te.zstd_lines(path)
        except subprocess.CalledProcessError as e:
            raise OSError(f"cannot decompress {path.name}: zstd exit {e.returncode}") from None
        return
    with open(path, encoding="utf-8", errors="replace") as fh:
        yield from fh


def _touched(path: Path, since) -> bool:
    """Whether `path` was modified at or after `since` (None: always); a file that cannot be
    stat'ed is kept, so its reader reports it."""
    if since is None:
        return True
    try:
        return path.stat().st_mtime >= since.timestamp()
    except OSError:
        return True


# Ceiling rules a main session is held to: its main model's ceiling, or the
# default one (an unattended run, by construction not an interface session).
RULE_MODEL = "model"
RULE_DEFAULT = "default"


def load_ceilings(path: Path = CEILINGS_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def levels_for(ceilings: dict) -> tuple[int, ...]:
    """The rows of the level table: the distinct ceilings of the data, the
    default included, increasing."""
    values = {int(ceilings["default_tokens"])}
    values.update(int(e["tokens"]) for e in ceilings.get("interface_session", []))
    return tuple(sorted(values))


def ceiling_for(model: str, ceilings: dict) -> int:
    """Interface-session ceiling of a model id: the first entry that shares a
    whole word with it, else the default."""
    words = set(re.split(r"[-._/:\s]+", (model or "").lower()))
    for entry in ceilings.get("interface_session", []):
        if words & {m.lower() for m in entry["models"]}:
            return int(entry["tokens"])
    return int(ceilings["default_tokens"])


def _ctx(ev: dict, metric: str = "prompt") -> int:
    if metric == "prompt" and "prompt" in ev:
        return ev["prompt"]
    return ev["cache_read"]


def _fmt_k(n: int) -> str:
    return f"{n // 1000}K"


def _user_text_parts(content) -> list[str]:
    """Text of a user record: plain string, or the text blocks of list-form
    content (tool_result blocks carry no commands and are skipped)."""
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [
            b["text"]
            for b in content
            if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
        ]
    return []


def parse_trajectory(path: Path) -> dict:
    """Parse one trace into an ordered event stream.

    Events: {"kind": "turn", "cache_read": int, "model": str},
    {"kind": "compact"}, {"kind": "clear"}. Turns are deduped by
    message.id; <synthetic> records are not turns. Also collects the
    cache_read of the first turn after each compaction
    (post_compact_reads) and the boundary's own postTokens
    (post_compact_tokens) — both feed the corpus-wide median.
    """
    events: list[dict] = []
    seen_ids: set[str] = set()
    post_compact_reads: list[int] = []
    post_compact_tokens: list[int] = []
    awaiting_post_read = False
    entry_skill = None
    last_ts = None
    first_ts = None
    unparsable = 0

    for line in _lines(path):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            unparsable += 1
            continue
        if not isinstance(rec, dict):
            unparsable += 1
            continue

        tstamp = ts._parse_ts(rec.get("timestamp", ""))
        if tstamp is not None:
            last_ts = tstamp
            if first_ts is None:
                first_ts = tstamp

        rec_type = rec.get("type")
        if rec_type == "system" and rec.get("subtype") == "compact_boundary":
            events.append({"kind": "compact", "ts": tstamp})
            meta = rec.get("compactMetadata") or {}
            if isinstance(meta.get("postTokens"), int):
                post_compact_tokens.append(meta["postTokens"])
            awaiting_post_read = True
            continue

        msg = rec.get("message")
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")

        if rec_type == "assistant":
            msg_id = msg.get("id")
            usage = msg.get("usage")
            model = msg.get("model") or ""
            if (
                msg_id
                and msg_id not in seen_ids
                and isinstance(usage, dict)
                and model != "<synthetic>"
            ):
                seen_ids.add(msg_id)
                cache_read = usage.get("cache_read_input_tokens", 0) or 0
                prompt = (
                    (usage.get("input_tokens", 0) or 0)
                    + cache_read
                    + (usage.get("cache_creation_input_tokens", 0) or 0)
                )
                events.append(
                    {
                        "kind": "turn",
                        "cache_read": cache_read,
                        "prompt": prompt,
                        "model": model,
                        "msg_id": msg_id,
                        "ts": tstamp,
                    }
                )
                if awaiting_post_read:
                    post_compact_reads.append(cache_read)
                    awaiting_post_read = False
        elif rec_type == "user":
            for text in _user_text_parts(content):
                if CLEAR_RE.search(text):
                    events.append({"kind": "clear", "ts": tstamp})
                elif entry_skill is None:
                    for m in re.finditer(
                        r"<command-name>/?([\w-]+)</command-name>", text
                    ):
                        if m.group(1) not in ts.BUILTIN_COMMANDS:
                            entry_skill = m.group(1)
                            break

    return {
        "events": events,
        "post_compact_reads": post_compact_reads,
        "post_compact_tokens": post_compact_tokens,
        "entry_skill": entry_skill,
        "last_ts": last_ts,
        "first_ts": first_ts,
        "unparsable_lines": unparsable,
    }


def read_claude_code(root: Path, since=None):
    """Reader of Claude Code transcripts under `root` (~/.claude/projects)."""
    if not Path(root).is_dir():
        raise CouldNotLook(f"no trace corpus at {root}")
    yield from read_claude_files(f for f in ts.iter_trace_files(root) if _touched(f[3], since))


def claude_archived(files):
    """(project, session_id, agent_id, path) of archived Claude Code copies, from their paths below
    raw/<host>/claude/: the layout of ts.iter_trace_files with `.zst` appended."""
    for rel, path in files:
        parts = rel.parts
        stem = path.name.removesuffix(".jsonl.zst")
        if len(parts) == 2 and path.name.endswith(".jsonl.zst"):
            yield ts.strip_worktree(parts[0]), stem, "main", path
        elif len(parts) == 4 and parts[2] == "subagents" and stem.startswith("agent-"):
            yield ts.strip_worktree(parts[0]), parts[1], stem, path


def read_claude_files(files):
    """Parse Claude Code transcripts given as (project, session_id, agent_id, path)."""
    for project, session_id, agent_id, path in files:
        try:
            traj = parse_trajectory(path)
        except OSError as e:
            yield project, session_id, agent_id, e
            continue
        traj.setdefault("ceiling_rule", RULE_MODEL)
        traj.setdefault("role", "main" if agent_id == "main" else "subagent")
        yield project, session_id, agent_id, traj


# session_meta.payload.source values of an interactive Codex session; `exec` and
# any unknown string are unattended and take the default ceiling.
CODEX_INTERACTIVE_SOURCES = ("cli", "vscode")


def default_codex_home() -> Path:
    return transcript_spool.codex_home()


def parse_codex_rollout(path: Path) -> dict:
    """Parse one Codex rollout (`rollout-*.jsonl`) into the trajectory shape of
    `parse_trajectory`, plus "role", "ceiling_rule", "session_id" and "project".

    A turn is one model request: an `event_msg` record of type `token_count`
    whose `info.total_token_usage.total_tokens` moved since the previous one.
    A record that leaves the cumulative total unchanged is a re-emission and is
    dropped; so is one whose `last_token_usage.input_tokens` is 0.

    Whole prompt = `info.last_token_usage.input_tokens`, alone. It ALREADY
    INCLUDES `cached_input_tokens`; adding the cached part counts it twice.
    Evidence (padme, 2026-11-10, 2153 rollouts modified in 28 days, key names
    and numbers only): on all 64993 records with a non-zero cached part,
    `cached_input_tokens <= input_tokens` and `total_tokens == input_tokens +
    output_tokens`, never `input + cached + output`; and `input + cached`
    exceeds the record's own `model_context_window` on 12924 of them, which a
    prompt cannot, while `input_tokens` alone never does.
    The records where `total_tokens != input + output` (111 of 112 in that
    sample) carry a zero `last_token_usage` with only `total_tokens` set and
    leave the cumulative total unchanged: re-emissions, dropped above.

    The cumulative `total_token_usage` is never a prompt size. The model of a
    request is that of the latest `turn_context` before it; on the sample the
    reviewer model `codex-auto-review` appears in subagent rollouts only, so it
    never becomes a main session's model. A forked rollout repeats its parent's
    `session_meta` (the first one is the fork's own) but replays none of its
    `token_count` records: over the 17 forks of the sample, no timestamp or
    cumulative total is shared with the parent, so nothing is deduplicated.
    Each turn takes its own record's `timestamp`.
    """
    events: list[dict] = []
    meta: dict | None = None
    model = ""
    prev_total = None
    first_ts = last_ts = None
    unparsable = 0
    for line in _lines(path):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            unparsable += 1
            continue
        if not isinstance(rec, dict):
            unparsable += 1
            continue
        tstamp = ts._parse_ts(rec.get("timestamp", ""))
        if tstamp is not None:
            last_ts = tstamp
            if first_ts is None:
                first_ts = tstamp
        rec_type = rec.get("type")
        payload = rec.get("payload")
        if not isinstance(payload, dict):
            continue
        if rec_type == "session_meta":
            if meta is None:
                meta = payload
        elif rec_type == "turn_context":
            model = payload.get("model") or model
        elif rec_type == "compacted":
            events.append({"kind": "compact", "ts": tstamp})
        elif rec_type == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info")
            if not isinstance(info, dict):
                continue
            last = info.get("last_token_usage") or {}
            total = (info.get("total_token_usage") or {}).get("total_tokens")
            if total is not None and total == prev_total:
                continue
            prev_total = total
            prompt = last.get("input_tokens") or 0
            if prompt <= 0:
                continue
            events.append(
                {
                    "kind": "turn",
                    "prompt": prompt,
                    "cache_read": last.get("cached_input_tokens") or 0,
                    "model": model,
                    "ts": tstamp,
                }
            )
    meta = meta or {}
    source = meta.get("source")
    if isinstance(source, dict):
        role = "subagent"
    elif isinstance(source, str) and source:
        role = source
    else:
        role = "unknown"
    return {
        "events": events,
        "post_compact_reads": [],
        "post_compact_tokens": [],
        "entry_skill": None,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "unparsable_lines": unparsable,
        "role": role,
        "ceiling_rule": RULE_MODEL if role in CODEX_INTERACTIVE_SOURCES else RULE_DEFAULT,
        "session_id": meta.get("id") or path.stem,
        "project": meta.get("cwd") or "",
    }


def read_codex(root: Path, since=None):
    """Reader of Codex rollouts under the Codex home `root` ($CODEX_HOME or
    ~/.codex): `sessions/` and `archived_sessions/`, both. A subagent rollout
    (`source` an object) is not a main session."""
    dirs = [d for _, d in transcript_spool.named_roots("codex", codex_home=root)]
    if not any(d.is_dir() for d in dirs):
        raise CouldNotLook(f"no Codex sessions under {root}")
    yield from read_codex_files(
        p for d in dirs if d.is_dir() for p in sorted(d.rglob("rollout-*.jsonl")) if _touched(p, since)
    )


def read_codex_files(paths):
    """Parse Codex rollouts, plain or `.zst`: one session per rollout name, however many roots hold a copy."""
    for path in transcript_spool.one_per_rollout(paths):
        try:
            traj = parse_codex_rollout(path)
        except OSError as e:
            yield str(path.parent), path.stem, "unknown", e
            continue
        agent_id = "subagent" if traj["role"] == "subagent" else "main"
        yield traj["project"], traj["session_id"], agent_id, traj


def default_pi_sessions() -> Path:
    return transcript_spool.named_root("pi", "live")


def default_pi_spool() -> Path:
    try:
        return transcript_spool.named_root("pi", "spool")
    except RuntimeError:  # archive root unknown: the reader reports could not look
        return Path("(archive root unknown)")


def parse_pi_session(path: Path, role: str, rule: str) -> dict:
    """Parse one Pi session log (`<iso>_<uuid>.jsonl`) into the trajectory shape of
    `parse_trajectory`, plus "role", "ceiling_rule", "session_id" and "project".

    Whole prompt = `usage.input + usage.cacheRead + usage.cacheWrite`. `input`
    EXCLUDES both cache fields. Evidence (padme, 2026-11-10, key names and
    numbers only): `totalTokens == input + output + cacheRead + cacheWrite` on
    763 of 763 assistant turns in the live root and 634 of 634 in the spool,
    and `cacheRead > input` on 632 of the live ones, which cannot hold if
    `input` contained it. `cacheWrite1h` is a split of `cacheWrite`, not an
    addend. An assistant record with all-zero usage carries `errorMessage` and
    is not a turn.

    The log is a tree (`id`, `parentId`). Conversation order is the branch that
    was continued: from the file's last entry, walk `parentId` back to the root
    and keep the assistant turns on that path; abandoned branches are dropped.
    `msg_id` is "pi:" + `responseId`, so a `/fork` or `/clone` file that replays
    its parent's entries is not counted twice by `drop_inherited_turns`. Each
    turn takes its own entry's `timestamp`; the model is `message.model`.
    """
    header: dict = {}
    entries: dict[str, dict] = {}
    last_id = None
    first_ts = last_ts = None
    unparsable = 0
    for line in _lines(path):
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            unparsable += 1
            continue
        if not isinstance(rec, dict):
            unparsable += 1
            continue
        tstamp = ts._parse_ts(rec.get("timestamp", ""))
        if tstamp is not None:
            last_ts = tstamp
            if first_ts is None:
                first_ts = tstamp
        if rec.get("type") == "session":
            header = header or rec
        elif rec.get("id") is not None:
            entries[rec["id"]] = rec
            last_id = rec["id"]
    branch = []
    seen = set()
    eid = last_id
    while eid in entries and eid not in seen:
        seen.add(eid)
        branch.append(entries[eid])
        eid = entries[eid].get("parentId")
    events = []
    for rec in reversed(branch):
        msg = rec.get("message")
        usage = msg.get("usage") if isinstance(msg, dict) else None
        if (rec.get("type") != "message" or not isinstance(msg, dict)
                or msg.get("role") != "assistant" or not isinstance(usage, dict)):
            continue
        cache_read = usage.get("cacheRead") or 0
        prompt = (usage.get("input") or 0) + cache_read + (usage.get("cacheWrite") or 0)
        if prompt <= 0:
            continue
        ev = {
            "kind": "turn",
            "prompt": prompt,
            "cache_read": cache_read,
            "model": msg.get("model") or "",
            "ts": ts._parse_ts(rec.get("timestamp", "")),
        }
        if msg.get("responseId"):
            ev["msg_id"] = "pi:" + msg["responseId"]
        events.append(ev)
    return {
        "events": events,
        "post_compact_reads": [],
        "post_compact_tokens": [],
        "entry_skill": None,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "unparsable_lines": unparsable,
        "role": role,
        "ceiling_rule": rule,
        "session_id": header.get("id") or path.stem,
        "project": header.get("cwd") or "",
    }


def _read_pi(root: Path, role: str, rule: str, since=None):
    if not Path(root).is_dir():
        raise CouldNotLook(f"no Pi sessions at {root}")
    yield from _read_pi_files((p for p in sorted(Path(root).rglob("*.jsonl")) if _touched(p, since)), role, rule)


def _read_pi_files(paths, role: str, rule: str):
    for path in paths:
        try:
            traj = parse_pi_session(path, role, rule)
        except OSError as e:
            yield str(path.parent), path.stem, "unknown", e
            continue
        yield traj["project"], traj["session_id"], "main", traj


def read_pi_live(root: Path, since=None):
    """Pi's live session root: sessions of unknown role, held to their model's ceiling."""
    return _read_pi(root, "main", RULE_MODEL, since)


def read_pi_spool(root: Path, since=None):
    """Pi's archive spool: seats and workers launched with `--session-dir`, held to the default."""
    return _read_pi(root, "launched", RULE_DEFAULT, since)


def _archived(files, suffix: str):
    return [path for _, path in files if path.name.endswith(suffix)]


# THE SEAM (ticket 1508; the Pi reader of ticket 1509 plugs in here).
# A runtime is a name, a default corpus root and a reader. Adding one is one
# reader function and one entry below; no other runtime's reader changes.
#
# Reader contract, `reader(root: Path, since=None)`, a generator (a file last
# modified before `since` is not opened):
# - raises CouldNotLook (at its first step) when the corpus at `root` is absent
#   or unreadable as a whole; the runtime is then reported "could not look",
#   never as zero sessions;
# - yields one `(project, session_id, agent_id, traj)` per transcript, with
#   `agent_id == "main"` for a main session and anything else for a subagent;
#   `traj` is an OSError instance when that one transcript could not be read
#   (counted as unreadable), else a dict shaped like `parse_trajectory`'s:
#   "events" in CONVERSATION order, not file order (a reader of a tree-shaped
#   log keeps the branch that was continued and drops abandoned ones), each turn
#   {"kind": "turn", "prompt": whole prompt in tokens, "cache_read": int,
#   "model": model id, matched by word against skills/route/ceilings.json by
#   ceiling_for (an id no entry names takes the default ceiling), "ts": aware
#   datetime or None, optional "msg_id"}, one turn per
#   model request; plus "first_ts", "last_ts", "unparsable_lines",
#   "post_compact_reads", "post_compact_tokens", "entry_skill" (may be empty),
#   "role" (shown in the role split) and "ceiling_rule" (RULE_MODEL: held to
#   its main model's ceiling; RULE_DEFAULT: held to the default ceiling).
# "role" and "ceiling_rule" may be left out (main, RULE_MODEL); a runtime need
# not have subagents; "msg_id", when given, dedups turns across that runtime's
# files (drop_inherited_turns), never across runtimes.
# `missed_runs` marks the one runtime whose runs and dollar figures are counted.
# `reader None` names a runtime bound by the ceilings whose corpus is not read.
# A runtime with several roots, each with its own status, takes one entry per
# root (e.g. "Pi" and "Pi spool"): an entry has exactly one root, reported as
# read, not read or could not look on its own, and its reader can set the
# ceiling rule the root implies. The CLI maps a flag to each entry's root.
# `store` names the entry's roots in transcript_spool.NAMED_ROOTS, (runtime,
# root names): the archive copy of another host is split by
# transcript_spool.source_of among the entries, and `read_files(files)` reads
# an entry's share, `files` being (path below raw/<host>/<runtime>/, path).
RUNTIMES = (
    {
        "name": "Claude Code",
        "default_root": lambda: transcript_spool.named_root("claude", "projects"),
        "reader": read_claude_code,
        "store": ("claude", ("projects",)),
        "read_files": lambda files: read_claude_files(claude_archived(files)),
        "missed_runs": True,
    },
    {
        "name": "Codex",
        "default_root": default_codex_home,
        "reader": read_codex,
        "store": ("codex", ("sessions", "archived_sessions")),
        "read_files": lambda files: read_codex_files(
            p for p in _archived(files, ".jsonl.zst") if p.name.startswith("rollout-")
        ),
        "missed_runs": False,
    },
    {
        "name": "Pi",
        "default_root": default_pi_sessions,
        "reader": read_pi_live,
        "store": ("pi", ("live",)),
        "read_files": lambda files: _read_pi_files(_archived(files, ".jsonl.zst"), "main", RULE_MODEL),
        "missed_runs": False,
    },
    {
        "name": "Pi spool",
        "default_root": default_pi_spool,
        "reader": read_pi_spool,
        "store": ("pi", ("spool",)),
        "read_files": lambda files: _read_pi_files(_archived(files, ".jsonl.zst"), "launched", RULE_DEFAULT),
        "missed_runs": False,
    },
)


@dataclass
class ArchiveCopy:
    """One RUNTIMES entry's share of another host's archive copy: `files` are those touched in the
    window; `held` says whether the copy holds any file of the entry's roots at all."""
    where: Path
    files: list = field(default_factory=list)
    held: bool = False

    def __str__(self) -> str:
        return str(self.where)


def default_roots() -> dict:
    return {rt["name"]: rt["default_root"]() for rt in RUNTIMES}


def drop_inherited_turns(trajectories: list[tuple]) -> int:
    """Strip turns a trajectory inherited from an earlier one, corpus-wide.

    `parse_trajectory` dedups turns by message id within a single file. A fork
    or resume starts a NEW file that replays the parent's records verbatim —
    same message ids — so the per-file set never sees them and every inherited
    turn is counted a second time. On the 2026-07-27 census that inflated the
    recoverable-compaction figure by ~28% ($278.68 -> ~$201): two session pairs
    contributed byte-identical runs.

    Trajectories are processed oldest-first so the originating session keeps its
    turns and the fork contributes only what it actually added. Turns are
    dropped in place; compact/clear events are left alone, since a fork
    genuinely re-enters that state. Returns the number of turns dropped.
    """
    from datetime import datetime, timezone

    epoch = datetime.min.replace(tzinfo=timezone.utc)
    ordered = sorted(
        trajectories,
        key=lambda item: (item[3]["first_ts"] or epoch, item[1], item[2]),
    )
    claimed: set[str] = set()
    dropped = 0
    for _, _, _, traj in ordered:
        kept = []
        for ev in traj["events"]:
            if ev["kind"] == "turn":
                mid = ev.get("msg_id")
                if mid is not None:
                    if mid in claimed:
                        dropped += 1
                        continue
                    claimed.add(mid)
            kept.append(ev)
        traj["events"] = kept
    return dropped


def find_missed_runs(
    events: list[dict], min_run: int, threshold: int, metric: str = "prompt"
) -> list[dict]:
    """Maximal runs of consecutive turns with context >= threshold,
    broken by any compact/clear event or below-threshold turn. Returns the
    runs of length >= min_run."""
    runs = []
    current: list[dict] = []
    start = 0
    for i, ev in enumerate(events):
        if ev["kind"] == "turn" and _ctx(ev, metric) >= threshold:
            if not current:
                start = i
            current.append(ev)
        else:
            if len(current) >= min_run:
                runs.append({"start": start, "length": len(current), "turns": current})
            current = []
    if len(current) >= min_run:
        runs.append({"start": start, "length": len(current), "turns": current})
    return runs


def run_recoverable_usd(turns: list[dict], median_post: int) -> float:
    """Counterfactual upper bound: compact at the run's first turn, then
    every later turn reads median_post instead of its actual cache_read."""
    usd = 0.0
    for t in turns[1:]:
        saved = max(0, t["cache_read"] - median_post)
        pricing = ts.resolve_pricing(t["model"])
        if pricing is None:
            continue
        usd += saved * pricing["cache_read"] / 1_000_000
    return usd


def window_start(now, days: int, since: str | None):
    """Start of the window: `since` (YYYY-MM-DD, UTC midnight) or `days` before now."""
    from datetime import datetime, timedelta, timezone

    if since:
        return datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
    return now - timedelta(days=days)


def restrict_to_window(events: list[dict], start) -> tuple[list[dict], int]:
    """Events stamped at or after `start`; an unstamped event cannot be placed
    and is dropped, counted in the second value."""
    kept, undated = [], 0
    for ev in events:
        if ev.get("ts") is None:
            undated += 1
        elif ev["ts"] >= start:
            kept.append(ev)
    return kept, undated


def main_model(events: list[dict]) -> str:
    """The model that served most turns of a trajectory."""
    counts: dict[str, int] = {}
    for ev in events:
        if ev["kind"] == "turn":
            counts[ev["model"]] = counts.get(ev["model"], 0) + 1
    return max(counts.items(), key=lambda kv: (kv[1], kv[0]))[0] if counts else ""


def session_report(main_trajs: list[tuple], ceilings: dict, metric: str, levels=None) -> dict:
    """Counts over main sessions, one row per session however many runs it had."""
    levels = levels_for(ceilings) if levels is None else levels
    rows = []
    for item in main_trajs:
        runtime, (project, session_id, traj) = (
            (item[0], item[1:]) if len(item) == 4 else ("Claude Code", item)
        )
        turns = [e for e in traj["events"] if e["kind"] == "turn"]
        if not turns:
            continue
        model = main_model(traj["events"])
        rule = traj.get("ceiling_rule", RULE_MODEL)
        ceiling = (
            ceiling_for(model, ceilings) if rule == RULE_MODEL else int(ceilings["default_tokens"])
        )
        ctx = [_ctx(t, metric) for t in turns]
        rows.append(
            {
                "runtime": runtime,
                "role": traj.get("role", "main"),
                "ceiling_rule": rule,
                "project": project,
                "session_id": session_id,
                "main_model": model,
                "turns": len(turns),
                "peak": max(ctx),
                "ceiling": ceiling,
                "turns_over_ceiling": sum(1 for c in ctx if c >= ceiling),
                "at_level": {str(lv): sum(1 for c in ctx if c >= lv) for lv in levels},
            }
        )

    def by(selected, key):
        out: dict[str, int] = {}
        for r in selected:
            out[r[key]] = out.get(r[key], 0) + 1
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    def by_model(selected):
        return by(selected, "main_model")

    level_rows = {}
    for lv in levels:
        sel = [r for r in rows if r["at_level"][str(lv)] >= MIN_RUN]
        level_rows[str(lv)] = {
            "sessions": len(sel),
            "by_model": by_model(sel),
            "by_runtime": by(sel, "runtime"),
        }
    over = [r for r in rows if r["turns_over_ceiling"] >= MIN_RUN]
    over.sort(key=lambda r: -r["peak"])
    return {
        "metric": metric,
        "metric_label": METRIC_LABEL[metric],
        "with_turns": len(rows),
        "turns_in_window": sum(r["turns"] for r in rows),
        "long_sessions": sum(1 for r in rows if r["turns"] >= LONG_SESSION_TURNS),
        "min_turns_at_level": MIN_RUN,
        "levels": level_rows,
        "by_runtime": by(rows, "runtime"),
        "over_own_ceiling": {
            "sessions": len(over),
            "by_model": by_model(over),
            "by_runtime": by(over, "runtime"),
            "by_rule": by(over, "ceiling_rule"),
            "rows": [{k: v for k, v in r.items() if k != "at_level"} for r in over[:20]],
        },
    }


def audit_corpus(
    roots,
    days: int,
    min_run: int,
    threshold: int | None = None,
    *,
    since: str | None = None,
    now=None,
    ceilings: dict | None = None,
    metric: str = "prompt",
    require_one: bool = True,
) -> dict:
    """Audit the corpora. `roots` maps a runtime name of RUNTIMES to its
    corpus root, or to an ArchiveCopy (another host's share, read by the
    entry's `read_files`); a bare path is Claude Code's alone. A runtime absent
    from `roots` or mapped to None is not read. Raises CouldNotLook only when no
    runtime's corpus is readable, unless `require_one` is false (the fleet
    reading, where another host may still be readable). `threshold` None means each agent's own: its
    main model's ceiling for a main session, the default ceiling for a
    subagent."""
    if not isinstance(roots, dict):
        roots = {"Claude Code": roots}
    now = now or datetime.now(timezone.utc)
    ceilings = ceilings or load_ceilings()
    start = window_start(now, days, since)

    runtimes = []
    all_trajs = []  # (runtime, project, session_id, agent_id, traj)
    files_seen = unreadable = unparsable = undated = duplicate_turns = 0
    for rt in RUNTIMES:
        root = roots.get(rt["name"])
        entry = {"name": rt["name"], "root": str(root) if root else None}
        runtimes.append(entry)
        if rt["reader"] is None or root is None:
            entry["status"] = "not read"
            entry["reason"] = rt.get("not_read_reason") or "no corpus root given"
            continue
        if isinstance(root, ArchiveCopy) and not root.held:
            entry["status"] = "not read"
            entry["reason"] = "not in this host's archive copy"
            continue
        try:
            if isinstance(root, ArchiveCopy):
                items = list(rt["read_files"](root.files))
            else:
                items = list(rt["reader"](Path(root), since=start))
        except (CouldNotLook, OSError) as e:
            entry["status"] = "could not look"
            entry["reason"] = str(e)
            continue
        trajs = []
        rt_seen = rt_unreadable = rt_unparsable = rt_undated = 0
        for project, session_id, agent_id, traj in items:
            rt_seen += 1
            if isinstance(traj, OSError):
                log.warning("could not look at a %s transcript: %s", rt["name"], traj)
                rt_unreadable += 1
                continue
            rt_unparsable += traj["unparsable_lines"]
            trajs.append((project, session_id, agent_id, traj))
        if rt_seen and rt_unreadable == rt_seen:
            entry["status"] = "could not look"
            entry["reason"] = f"none of its {rt_seen} transcripts under {root} could be read"
            unreadable += rt_unreadable
            files_seen += rt_seen
            continue
        entry["status"] = "read"
        # Inherited turns are dropped on whole transcripts, before the window cut.
        dropped = drop_inherited_turns(trajs)
        if dropped:
            log.info("dropped %d turns inherited by forked/resumed sessions", dropped)
        roles: dict[str, int] = {}
        mains = 0
        for project, session_id, agent_id, traj in trajs:
            traj["events"], n = restrict_to_window(traj["events"], start)
            rt_undated += n
            if not traj["events"]:
                continue
            all_trajs.append((rt["name"], project, session_id, agent_id, traj))
            if any(e["kind"] == "turn" for e in traj["events"]):
                role = traj.get("role", "main")
                roles[role] = roles.get(role, 0) + 1
                mains += agent_id == "main"
        entry.update(
            {
                "files_seen": rt_seen,
                "unreadable_files": rt_unreadable,
                "unparsable_lines": rt_unparsable,
                "sessions_with_turns": mains,
                "roles": dict(sorted(roles.items(), key=lambda kv: -kv[1])),
            }
        )
        files_seen += rt_seen
        unreadable += rt_unreadable
        unparsable += rt_unparsable
        undated += rt_undated
        duplicate_turns += dropped

    if require_one and not any(r["status"] == "read" for r in runtimes):
        raise CouldNotLook(
            "; ".join(f"{r['name']}: {r['reason']}" for r in runtimes)
        )

    # Missed runs and their dollar figures: the runtimes flagged for them only.
    runs_runtimes = {rt["name"] for rt in RUNTIMES if rt["missed_runs"]}
    trajectories = [t[1:] for t in all_trajs if t[0] in runs_runtimes]

    post_reads = [r for _, _, _, t in trajectories for r in t["post_compact_reads"]]
    post_tokens = [r for _, _, _, t in trajectories for r in t["post_compact_tokens"]]
    if post_reads:
        median_post, median_source = int(statistics.median(post_reads)), "next-turn cache_read"
    elif post_tokens:
        median_post, median_source = int(statistics.median(post_tokens)), "boundary postTokens"
    else:
        median_post, median_source = DEFAULT_POST_COMPACT_TOKENS, "default (no compactions)"

    run_rows = []
    compactions = clears = 0
    for project, session_id, agent_id, traj in trajectories:
        compactions += sum(1 for e in traj["events"] if e["kind"] == "compact")
        clears += sum(1 for e in traj["events"] if e["kind"] == "clear")
        model = main_model(traj["events"])
        if threshold is not None:
            agent_threshold = threshold
        elif agent_id == "main":
            agent_threshold = ceiling_for(model, ceilings)
        else:
            agent_threshold = int(ceilings["default_tokens"])
        for run in find_missed_runs(traj["events"], min_run, agent_threshold, metric):
            usd = run_recoverable_usd(run["turns"], median_post)
            reads = [_ctx(t, metric) for t in run["turns"]]
            run_rows.append(
                {
                    "project": project,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "main_model": model,
                    "threshold": agent_threshold,
                    "entry_skill": traj["entry_skill"] or "",
                    "run_start_event": run["start"],
                    "run_turns": run["length"],
                    "mean_context": sum(reads) // len(reads),
                    "max_context": max(reads),
                    "recoverable_usd": round(usd, 4),
                }
            )

    def _agg(key):
        out = {}
        for r in run_rows:
            k = r[key] or "(none)"
            a = out.setdefault(k, {"runs": 0, "recoverable_usd": 0.0})
            a["runs"] += 1
            a["recoverable_usd"] += r["recoverable_usd"]
        return {
            k: {"runs": v["runs"], "recoverable_usd": round(v["recoverable_usd"], 2)}
            for k, v in sorted(out.items(), key=lambda kv: -kv[1]["recoverable_usd"])
        }

    sessions = {}
    for r in run_rows:
        key = (r["project"], r["session_id"])
        s = sessions.setdefault(
            key,
            {
                "project": r["project"],
                "session_id": r["session_id"],
                "entry_skill": r["entry_skill"],
                "runs": 0,
                "recoverable_usd": 0.0,
            },
        )
        s["runs"] += 1
        s["recoverable_usd"] += r["recoverable_usd"]
    top_sessions = sorted(sessions.values(), key=lambda s: -s["recoverable_usd"])[:20]
    for s in top_sessions:
        s["recoverable_usd"] = round(s["recoverable_usd"], 2)

    main_trajs = [(rt, p, sid, t) for rt, p, sid, aid, t in all_trajs if aid == "main"]

    return {
        "window_days": days,
        "window_start": start.isoformat(),
        "window_end": now.isoformat(),
        "min_run": min_run,
        "threshold_tokens": threshold if threshold is not None else "per model (skills/route/ceilings.json)",
        "metric": metric,
        "host": transcript_spool.host(),
        "runtimes": runtimes,
        "runtimes_read": [r["name"] for r in runtimes if r["status"] == "read"],
        "runtimes_not_read": [r["name"] for r in runtimes if r["status"] != "read"],
        "missed_runs_runtimes": sorted(runs_runtimes),
        "files_seen": files_seen,
        "unreadable_files": unreadable,
        "unparsable_lines": unparsable,
        "undated_events_dropped": undated,
        "agents_in_window": len(all_trajs),
        "inherited_turns_dropped": duplicate_turns,
        "compactions_observed": compactions,
        "clears_observed": clears,
        "post_compact_median_tokens": median_post,
        "post_compact_median_source": median_source,
        "missed_runs": len(run_rows),
        "sessions_with_missed_runs": len(sessions),
        "recoverable_usd_upper_bound": round(sum(r["recoverable_usd"] for r in run_rows), 2),
        "by_project": _agg("project"),
        "by_entry_skill": _agg("entry_skill"),
        "top_sessions": top_sessions,
        "sessions": session_report(main_trajs, ceilings, metric),
        "run_rows": run_rows,
    }


def surfaces() -> list[tuple[dict, str, str, str]]:
    """(RUNTIMES entry, runtime, root name, label) of every root the audit reads: the label is the
    entry's name, followed by the root's name when the entry has several (Codex)."""
    out = []
    for rt in RUNTIMES:
        runtime, names = rt["store"]
        for name in names:
            label = rt["name"] if len(names) == 1 else f"{rt['name']} {name.replace('_', ' ')}"
            out.append((rt, runtime, name, label))
    return out


def archive_copy(host_dir: Path, start) -> tuple[dict, dict, float | None]:
    """Split one host's archive copy among the RUNTIMES entries. Returns the roots for
    audit_corpus (entry name -> ArchiveCopy), the files held per surface label, and the newest
    file's mtime. Files modified before `start` are counted as held but not handed to a reader."""
    owner = {(runtime, name): (rt, label) for rt, runtime, name, label in surfaces()}
    roots = {rt["name"]: ArchiveCopy(host_dir / rt["store"][0]) for rt in RUNTIMES}
    held: dict[str, int] = {}
    newest = None
    for runtime in dict.fromkeys(runtime for _, runtime, _, _ in surfaces()):
        base = host_dir / runtime
        for path in sorted(base.rglob("*.zst")) if base.is_dir() else ():
            try:
                mtime = path.stat().st_mtime
            except OSError:
                continue
            rel = path.relative_to(base)
            rt, label = owner[(runtime, transcript_spool.source_of(runtime, rel))]
            newest = mtime if newest is None else max(newest, mtime)
            held[label] = held.get(label, 0) + 1
            copy = roots[rt["name"]]
            copy.held = True
            if mtime >= start.timestamp():
                copy.files.append((rel, path))
    return roots, held, newest


def archive_host_entries(start, audit) -> list[dict]:
    """One entry per other host of this host's archive. `audit(roots)` runs audit_corpus on a
    host's roots. Raises FleetUnavailable when the archive gives no other host."""
    try:
        raw = transcript_spool.raw_dir().parent
    except RuntimeError as e:
        raise FleetUnavailable(str(e)) from None
    try:
        hosts = sorted(d.name for d in raw.iterdir() if d.is_dir() and d.name != transcript_spool.host())
    except OSError as e:
        raise FleetUnavailable(f"cannot read the archive at {raw}: {e.strerror or e}") from None
    if not hosts:
        raise FleetUnavailable(f"the archive at {raw} holds no other host")
    labels = [label for *_, label in surfaces()]
    entries = []
    for name in hosts:
        roots, held, newest = archive_copy(raw / name, start)
        entry = {
            "host": name,
            "source": "archive",
            "copy": str(raw / name),
            "newest_file": datetime.fromtimestamp(newest, timezone.utc).date().isoformat() if newest else None,
            "surfaces": held,
            "surfaces_missing": [label for label in labels if label not in held],
        }
        if not held:
            entry.update(status="could not look",
                         reason=f"its archive copy {raw / name} holds no transcript this audit reads, "
                         "or cannot be read")
            entries.append(entry)
            continue
        summary = audit(roots)
        entry.update(_host_entry(name, summary, source="archive"))
        entries.append(entry)
    return entries


def _host_entry(host: str, summary: dict, *, source: str) -> dict:
    return {
        "host": host,
        "source": source,
        "status": "read" if summary["runtimes_read"] else "could not look",
        "reason": None if summary["runtimes_read"] else "no corpus readable",
        "runtimes": summary["runtimes"],
        "files_seen": summary["files_seen"],
        "unreadable_files": summary["unreadable_files"],
        "unparsable_lines": summary["unparsable_lines"],
        "sessions": summary["sessions"],
    }


def merge_session_reports(reports: list[dict]) -> dict:
    """Sum the counts of several hosts' session reports (rows are dropped)."""
    def add(dicts):
        out: dict[str, int] = {}
        for d in dicts:
            for k, v in d.items():
                out[k] = out.get(k, 0) + v
        return dict(sorted(out.items(), key=lambda kv: -kv[1]))

    base = reports[0]
    levels = {}
    for lv in dict.fromkeys(k for r in reports for k in r["levels"]):
        rows = [r["levels"][lv] for r in reports if lv in r["levels"]]
        levels[lv] = {
            "sessions": sum(x["sessions"] for x in rows),
            "by_model": add(x["by_model"] for x in rows),
            "by_runtime": add(x["by_runtime"] for x in rows),
        }
    overs = [r["over_own_ceiling"] for r in reports]
    return {
        "metric": base["metric"],
        "metric_label": base["metric_label"],
        "with_turns": sum(r["with_turns"] for r in reports),
        "turns_in_window": sum(r["turns_in_window"] for r in reports),
        "long_sessions": sum(r["long_sessions"] for r in reports),
        "min_turns_at_level": base["min_turns_at_level"],
        "levels": levels,
        "by_runtime": add(r["by_runtime"] for r in reports),
        "over_own_ceiling": {
            "sessions": sum(o["sessions"] for o in overs),
            "by_model": add(o["by_model"] for o in overs),
            "by_runtime": add(o["by_runtime"] for o in overs),
            "by_rule": add(o["by_rule"] for o in overs),
            "rows": [r for o in overs for r in o.get("rows", [])][:20],
        },
    }


def audit_fleet(local: dict, audit) -> dict:
    """Add the other hosts, read from this host's archive, to the local summary: `fleet` says
    whether the archive gave them, `hosts` holds one entry per host (this one first), and
    `sessions` becomes the sum over the hosts read. `audit(roots)` runs audit_corpus on a host's
    roots. Raises CouldNotLook when no host at all is readable."""
    start = datetime.fromisoformat(local["window_start"])
    entries = [_host_entry(local["host"], local, source="live")]
    out = dict(local)
    try:
        entries += archive_host_entries(start, audit)
    except FleetUnavailable as e:
        if not local["runtimes_read"]:
            raise CouldNotLook(f"{local['host']}: no corpus readable; other hosts: {e}") from None
        out["fleet"] = {"available": False, "reason": str(e)}
        return out
    read = [e for e in entries if e["status"] == "read"]
    if not read:
        raise CouldNotLook("; ".join(f"{e['host']}: {e['reason']}" for e in entries))
    out["fleet"] = {"available": True}
    out["hosts"] = entries
    out["sessions"] = merge_session_reports([e["sessions"] for e in read])
    for key in ("files_seen", "unreadable_files", "unparsable_lines"):
        out[key] = sum(e.get(key, 0) for e in read)
    return out


def _runtime_lines(runtimes: list[dict], prefix: str = "") -> list[str]:
    lines = []
    for r in runtimes:
        if r["status"] == "read":
            roles = ", ".join(f"{k} {v}" for k, v in r["roles"].items())
            lines.append(
                f"{prefix}Read: {r['name']} under {r['root']}: {r['sessions_with_turns']} main sessions"
                + (f" (transcripts by role: {roles})" if roles else "")
            )
        elif r["status"] == "could not look":
            lines.append(
                f"{prefix}COULD NOT LOOK at {r['name']}: {r['reason']}; the counts below leave it out"
            )
        else:
            lines.append(f"{prefix}NOT READ: {r['name']}, {r['reason']}; the counts below leave it out")
    return lines


def _fleet_lines(summary: dict) -> list[str]:
    hosts = summary["hosts"]
    lines = [
        "Fleet: " + ", ".join(f"{h['host']} ({h['source']})" for h in hosts)
        + ". Counts below sum the hosts read; a session seen on two hosts counts on both "
        "(no cross-host deduplication). Missed runs are this host's only. The other hosts are read "
        "from this host's archive: a transcript touched within the last day is not archived yet."
    ]
    for i, h in enumerate(hosts):
        if i == 0:
            tag = f"Host {h['host']} (this host, live)"
        else:
            tag = f"Host {h['host']} (archive copy, newest file {h['newest_file'] or 'none'})"
        if h["status"] == "read":
            lines.append(f"{tag}: read")
        else:
            lines.append(f"{tag}: COULD NOT LOOK ({h['reason']}); the counts below leave it out")
        if i:
            held = ", ".join(f"{label} {n} files" for label, n in h["surfaces"].items()) or "none"
            missing = ", ".join(h["surfaces_missing"]) or "none"
            lines.append(f"  In the copy: {held}; not in the copy: {missing}")
        if h["status"] == "read":
            lines += _runtime_lines(h["runtimes"], prefix="  ")
    read = [h for h in hosts if h["status"] == "read"]
    lines.append(
        "sessions with at least one turn, by host: "
        + ", ".join(f"{h['host']} {h['sessions']['with_turns']}" for h in read)
    )
    lines.append(
        "sessions past their ceiling, by host: "
        + ", ".join(f"{h['host']} {h['sessions']['over_own_ceiling']['sessions']}" for h in read)
    )
    return lines


def render_table(summary: dict) -> str:
    """The design note's section 1 table, as text."""
    sr = summary["sessions"]
    n = sr["min_turns_at_level"]
    lines = [
        f"Context length audit, main sessions, {summary['window_start'][:10]} to {summary['window_end'][:10]}",
        f"Context length counted as: {sr['metric_label']}",
    ]
    fleet = summary.get("fleet") or {}
    if fleet.get("available"):
        lines += _fleet_lines(summary)
    else:
        why = f"fleet view not available here: {fleet['reason']}" if fleet else "other hosts are not read"
        lines.append(f"Host: {summary['host']} (this host's corpora only; {why})")
        lines += _runtime_lines(summary["runtimes"])
    lines += [
        f"sessions with at least one turn: {sr['with_turns']}",
        f"sessions with {LONG_SESSION_TURNS} or more turns: {sr['long_sessions']}",
    ]
    for lv, row in sr["levels"].items():
        models = ", ".join(f"{c} on {m or '(unknown)'}" for m, c in row["by_model"].items())
        lines.append(
            f"sessions with {n} or more turns at or above {_fmt_k(int(lv))}: {row['sessions']}"
            + (f" ({models})" if models else "")
        )
    over = sr["over_own_ceiling"]
    models = ", ".join(f"{c} on {m or '(unknown)'}" for m, c in over["by_model"].items())
    by_rt = ", ".join(f"{c} on {k}" for k, c in over["by_runtime"].items())
    by_rule = ", ".join(f"{c} by the {k} ceiling" for k, c in over["by_rule"].items())
    lines.append(
        f"sessions with {n} or more turns past their ceiling: {over['sessions']}"
        + (f" ({models}; {by_rt}; {by_rule})" if models else "")
    )
    lines.append(
        "A Claude Code main session is not known to be an interface session: it takes its model's "
        "ceiling. A Codex cli session takes its model's ceiling; a Codex exec run is unattended and "
        "takes the default, as does a rollout with no source; a subagent is not a session. "
        "A Pi live-root session takes its model's ceiling; a Pi spool session (a launched seat) takes the default."
    )
    lines.append(
        f"missed runs ({', '.join(summary['missed_runs_runtimes'])} only"
        + (", this host" if fleet.get("available") else "")
        + "): "
        f"{summary['missed_runs']} in {summary['sessions_with_missed_runs']} sessions"
    )
    if summary["unreadable_files"]:
        lines.append(
            f"COULD NOT LOOK at {summary['unreadable_files']} of {summary['files_seen']} "
            "transcripts: the counts above leave them out"
        )
    if summary["unparsable_lines"]:
        lines.append(f"{summary['unparsable_lines']} transcript lines could not be parsed")
    return "\n".join(lines)


CSV_COLUMNS = [
    "project",
    "session_id",
    "agent_id",
    "main_model",
    "threshold",
    "entry_skill",
    "run_start_event",
    "run_turns",
    "mean_context",
    "max_context",
    "recoverable_usd",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Which sessions overran their context ceiling, and what missed "
        "compact/clear runs cost. Context length is the whole prompt per turn "
        "(input + cache read + cache creation) unless --metric says otherwise."
    )
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=None,
        help="Root of the Claude Code trace corpus (default: ~/.claude/projects; given, reads this host alone)",
    )
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=None,
        help="Codex home holding sessions/ and archived_sessions/ (default: $CODEX_HOME or ~/.codex)",
    )
    parser.add_argument(
        "--pi-sessions",
        type=Path,
        default=None,
        help="Pi live session root (default: $PI_CODING_AGENT_DIR/sessions or ~/.pi/agent/sessions)",
    )
    parser.add_argument(
        "--pi-spool",
        type=Path,
        default=None,
        help="Pi archive spool of launched seats (default: <archive>/spool/<host>/pi)",
    )
    parser.add_argument("--days", type=int, default=28, help="Window in days (default 28)")
    parser.add_argument(
        "--since",
        help="Window start as YYYY-MM-DD (UTC), instead of --days; the design note's table uses 2026-11-01",
    )
    parser.add_argument(
        "--min-run",
        type=int,
        default=MIN_RUN,
        help="Minimum consecutive high-context turns to flag (default %(default)s)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=None,
        help="Per-turn context floor in tokens for every agent "
        "(default: each main model's ceiling from skills/route/ceilings.json, its default for subagents)",
    )
    parser.add_argument(
        "--metric",
        choices=METRICS,
        default="prompt",
        help="prompt: input + cache read + cache creation (default); "
        "cache_read: the June 2026 audit's quantity",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Read this host alone (default: this host live, and every other host its transcript "
        "archive holds; an explicit corpus-root flag also reads this host alone)",
    )
    parser.add_argument("--output", type=Path, help="Write per-run rows to this CSV")
    parser.add_argument(
        "--json", action="store_true", help="Print the summary as JSON to stdout"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    roots = default_roots()
    explicit = {
        name: getattr(args, attr)
        for name, attr in (("Claude Code", "projects_dir"), ("Codex", "codex_home"),
                           ("Pi", "pi_sessions"), ("Pi spool", "pi_spool"))
        if getattr(args, attr) is not None
    }
    roots.update(explicit)
    fleet = not args.local and not explicit
    now = datetime.now(timezone.utc)

    def audit(corpus_roots, require_one=False):
        return audit_corpus(corpus_roots, args.days, args.min_run, args.threshold, since=args.since,
                            now=now, metric=args.metric, require_one=require_one)

    try:
        summary = audit(roots, require_one=not fleet)
        if fleet:
            summary = audit_fleet(summary, audit)
    except (CouldNotLook, OSError, ValueError) as e:
        print(f"could not look: {e}", file=sys.stderr)
        return 2
    run_rows = summary.pop("run_rows")

    if args.output:
        with open(args.output, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(run_rows)
        log.info("wrote %d runs to %s", len(run_rows), args.output)

    if args.json:
        json.dump(summary, sys.stdout, indent=2, default=str)
        print()
    else:
        print(render_table(summary))
        log.info(
            "agents=%d missed_runs=%d recoverable<=$%s (median_post=%d from %s)",
            summary["agents_in_window"],
            summary["missed_runs"],
            summary["recoverable_usd_upper_bound"],
            summary["post_compact_median_tokens"],
            summary["post_compact_median_source"],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

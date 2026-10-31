#!/usr/bin/env python3
"""Render one session as a Chrome Trace Event JSON timeline (ticket 1385; memo conception/2026-10-31-monitoring-redesign.md 4.4).

    trace_timeline.py <claude session id> [--out FILE]

Reads the session, its `subagents/`, and the seats its launch lines (ticket 1384) name as children of
it, each from the live tree first and the archive (ticket 1383) second, so a session already pruned from
the live tree still renders. Writes the Chrome Trace Event format, which Perfetto (ui.perfetto.dev) and
chrome://tracing open; no Perfetto library is involved.

Layout: one process (lane) per set of non-overlapping agents, assigned greedily by start time, so
concurrent agents land on distinct lanes. Thread 0 of a lane carries the agent span; threads 1.. carry its
turns and tool calls, one row each where calls overlap. A subagent or seat names its parent in its span.
Every event carries its pointer (file, call id) in `args`; an unpriced model shows `cost unknown`.

Paths come from `transcript_spool` (live roots, archive, host) and `launch_line` (launches file).
"""
import argparse
import importlib.util
import json
import logging
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
log = logging.getLogger("trace_timeline")
COST_UNKNOWN = "cost unknown"


def _load(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


te = _load("trace_events")


@dataclass
class Tree:
    """Where transcripts live: live roots per runtime, and the archive directory of this host."""

    live: dict[str, list[Path]]
    archive: Path

    @classmethod
    def default(cls) -> "Tree":
        spool = _load("transcript_spool")
        live = {rt: spool.source_roots(rt) for rt in spool.ARCHIVED_RUNTIMES}
        return cls(live, spool.archive_root() / "transcripts" / spool.host())

    def find(self, runtime: str, pattern: str) -> tuple[str, Path] | None:
        """(relative path, readable path) of the first match: live roots first, then the archive."""
        for root in self.live.get(runtime, []):
            for hit in sorted(root.glob(pattern)):
                return hit.relative_to(root).as_posix(), hit
        base = self.archive / runtime
        for hit in sorted(base.glob(pattern + ".zst")):
            return hit.relative_to(base).as_posix().removesuffix(".zst"), hit
        return None

    def resolve(self, runtime: str, ref: str) -> tuple[str, Path] | None:
        """A launch line's child_session: a session id, or the absolute path of a spooled file."""
        if ref.startswith("/"):
            path = Path(ref)
            for root in self.live.get(runtime, []):
                if path.is_relative_to(root):
                    rel = path.relative_to(root)
                    if path.exists():
                        return rel.as_posix(), path
                    packed = self.archive / runtime / (rel.as_posix() + ".zst")
                    return (rel.as_posix(), packed) if packed.exists() else None
            return (path.as_posix(), path) if path.exists() else None
        if runtime == "claude":
            return self.find(runtime, f"*/{ref}.jsonl")
        if runtime == "codex":
            return self.find(runtime, f"**/rollout-*-{ref}.jsonl")
        return None

    def subagents(self, runtime_rel: str) -> list[tuple[str, Path, dict]]:
        """(relative path, readable path, meta) of each `<session>/subagents/agent-*.jsonl`."""
        folder = Path(runtime_rel).with_suffix("")
        found: dict[str, Path] = {}
        for root in self.live.get("claude", []):
            for hit in sorted((root / folder / "subagents").glob("agent-*.jsonl")):
                found.setdefault(hit.name, hit)
        for hit in sorted((self.archive / "claude" / folder / "subagents").glob("agent-*.jsonl.zst")):
            found.setdefault(hit.name.removesuffix(".zst"), hit)
        out = []
        for name, path in sorted(found.items()):
            meta_path = path.with_name(name.removesuffix(".jsonl") + ".meta.json" + (".zst" if path.suffix == ".zst" else ""))
            out.append(((folder / "subagents" / name).as_posix(), path, _meta(meta_path)))
        return out


def _meta(path: Path) -> dict:
    try:
        return json.loads("\n".join(te.open_lines(path)))
    except (OSError, ValueError, subprocess.CalledProcessError):
        return {}


@dataclass
class Agent:
    id: str
    label: str
    parent: str | None
    runtime: str
    events: list = field(default_factory=list)

    @property
    def span(self):
        return self.events[0]


def read_launches(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _claude_agents(tree: Tree, rel: str, path: Path, sid: str, parent: str | None, label: str) -> list[Agent]:
    agents = [Agent(sid, label, parent, "claude",
                    te.read_claude(te.open_lines(path), rel, agent=sid, parent_agent=parent, name=label))]
    for sub_rel, sub_path, meta in tree.subagents(rel):
        sub_id = Path(sub_rel).stem.removeprefix("agent-")
        sub_label = meta.get("description") or meta.get("agentType") or "subagent"
        agents.append(Agent(sub_id, sub_label, meta.get("parentAgentId") or sid, "claude",
                            te.read_claude(te.open_lines(sub_path), sub_rel, agent=sub_id,
                                           parent_agent=meta.get("parentAgentId") or sid, name=sub_label)))
    return agents


def collect(tree: Tree, session: str, launches: list[dict]) -> list[Agent]:
    """The session, its subagents, and the seats launched from it (and from them), live before archive."""
    hit = tree.find("claude", f"*/{session}.jsonl")
    if hit is None:
        raise SystemExit(f"trace_timeline: session {session} is neither in the live tree nor in the archive")
    agents = _claude_agents(tree, hit[0], hit[1], session, None, f"claude {session[:8]}")
    queue, seen = [session], {session}
    while queue:
        parent = queue.pop(0)
        for index, line in enumerate(launches):
            if line.get("parent_session") != parent:
                continue
            runtime, ref = line.get("child_runtime") or "?", line.get("child_session") or ""
            key = (parent, runtime, ref, line.get("ts_start"), line.get("seat"), index)
            if key in seen:
                continue
            seen.add(key)
            seat = f"{line.get('seat') or '?'}/{runtime}"
            start = te.epoch(line.get("ts_start")) or 0.0
            end = te.epoch(line.get("ts_end")) or start
            found = tree.resolve(runtime, ref)
            child_id = Path(ref).stem if ref.startswith("/") else ref
            if found is None:
                # No transcript: ref may be a placeholder ("not captured") shared by concurrent seats,
                # so the agent id comes from the launch line itself, never from the ref text.
                child_id = f"{line.get('seat') or '?'}@{line.get('ts_start')}#{index}"
                log.warning("seat %s: transcript %s not found; span from its launch line", seat, ref)
                events = te.read_opaque(runtime, ref, start, end, child_id, parent, seat)
                agents.append(Agent(child_id, seat, parent, runtime, events))
                continue
            rel, path = found
            if runtime == "claude":
                agents.extend(_claude_agents(tree, rel, path, child_id, parent, seat))
                queue.append(child_id)
            elif runtime == "codex":
                agents.append(Agent(child_id, seat, parent, runtime,
                                    te.read_codex(te.open_lines(path), rel, child_id, parent, seat)))
            elif runtime == "pi":
                agents.append(Agent(child_id, seat, parent, runtime,
                                    te.read_pi(te.open_lines(path), rel, child_id, parent, seat)))
            else:
                agents.append(Agent(child_id, seat, parent, runtime,
                                    te.read_opaque(runtime, rel, start, end, child_id, parent, seat)))
    return agents


def assign_lanes(spans: list[tuple[str, float, float]]) -> dict[str, int]:
    """Greedy interval colouring: each span takes the lowest lane free at its start."""
    free_at: list[float] = []
    lanes = {}
    for key, start, end in sorted(spans, key=lambda s: (s[1], s[2])):
        lane = next((i for i, t in enumerate(free_at) if t <= start), None)
        if lane is None:
            lane = len(free_at)
            free_at.append(end)
        else:
            free_at[lane] = end
        lanes[key] = lane
    return lanes


def _usd(event) -> float | str:
    return COST_UNKNOWN if event.shadow_usd is None else round(event.shadow_usd, 6)


def _args(event, extra=None) -> dict:
    args = {"pointer": {"file": event.pointer[0], "call_id": event.pointer[1]}, "runtime": event.runtime,
            "agent": event.agent, "model": event.model, "tokens": event.tokens, "shadow_usd": _usd(event),
            "cost_source": event.cost_source, "exit": event.exit}
    if event.detail:
        args["detail"] = event.detail
    args.update(extra or {})
    return args


def render(agents: list[Agent]) -> dict:
    """Chrome Trace Event document for the collected agents."""
    t0 = min((a.span.start for a in agents), default=0.0)
    lanes = assign_lanes([(a.id, a.span.start, a.span.end) for a in agents])
    labels = {a.id: a.label for a in agents}
    out: list[dict] = []
    rows: dict[int, list[float]] = {}  # lane -> end time of each call row, greedy
    named = set()

    def micros(t: float) -> int:
        return int(round((t - t0) * 1e6))

    for a in sorted(agents, key=lambda a: (a.span.start, a.id)):
        pid = lanes[a.id] + 1
        if pid not in named:
            named.add(pid)
            out.append({"ph": "M", "name": "process_name", "pid": pid, "tid": 0, "args": {"name": f"lane {pid}"}})
            out.append({"ph": "M", "name": "process_sort_index", "pid": pid, "tid": 0, "args": {"sort_index": pid}})
            out.append({"ph": "M", "name": "thread_name", "pid": pid, "tid": 0, "args": {"name": "agents"}})
        span = a.span
        under = f" (under {labels.get(a.parent, a.parent)})" if a.parent else ""
        out.append({"ph": "X", "cat": "agent", "name": a.label + under, "pid": pid, "tid": 0,
                    "ts": micros(span.start), "dur": micros(span.end) - micros(span.start),
                    "args": _args(span, {"parent_agent": a.parent, "runtime": a.runtime})})
        free = rows.setdefault(pid, [])
        for ev in sorted(a.events[1:], key=lambda e: (e.start, e.end)):
            row = next((i for i, t in enumerate(free) if t <= ev.start), None)
            if row is None:
                row = len(free)
                free.append(ev.end)
                out.append({"ph": "M", "name": "thread_name", "pid": pid, "tid": row + 1,
                            "args": {"name": f"calls {row + 1}"}})
            else:
                free[row] = ev.end
            out.append({"ph": "X", "cat": ev.kind, "name": ev.name, "pid": pid, "tid": row + 1,
                        "ts": micros(ev.start), "dur": micros(ev.end) - micros(ev.start), "args": _args(ev)})
    return {"traceEvents": out, "displayTimeUnit": "ms", "otherData": {"t0_epoch": t0}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("session", help="Claude Code session id")
    parser.add_argument("--out", help="output file (default: <session>.trace.json in the current directory)")
    parser.add_argument("--archive-root", help="archive root (default: IDH_ARCHIVE_ROOT or ~/archive)")
    parser.add_argument("--live-root", help="Claude live root (default: CLAUDE_CONFIG_DIR/projects or ~/.claude/projects)")
    parser.add_argument("--launches", help="launches.jsonl (default: the launch_line path)")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if args.archive_root:
        os.environ["IDH_ARCHIVE_ROOT"] = args.archive_root
    tree = Tree.default()
    if args.live_root:
        tree.live["claude"] = [Path(args.live_root)]
    launches_file = Path(args.launches) if args.launches else _load("launch_line").launches_path()
    agents = collect(tree, args.session, read_launches(launches_file))
    out = Path(args.out or f"{args.session}.trace.json")
    out.write_text(json.dumps(render(agents)) + "\n", encoding="utf-8")
    log.info("%s: %d agents", out, len(agents))
    return 0


if __name__ == "__main__":
    sys.exit(main())

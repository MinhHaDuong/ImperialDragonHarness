#!/usr/bin/env python3
"""Where raid, hunt and gaze runs spend their wall time, from Claude Code traces.

    python3 scripts/trace-wall-time.py [--days N] [--projects-dir DIR] [--json]

Zero-LLM, standard-library-only companion to trace-friction.py (which bounds
slow tools) and gaze_wall_time.py (which splits gaze into seats). This one
decomposes every run of the three ticket-working skills:

* a raid run is a trace whose `/raid` command or `Skill(raid)` call opens it,
  from that call to the trace's end; a hunt run likewise for hunt; a gaze run
  is a `forked-skill` agent named gaze. A hunt inside a raid tree is counted
  in both views (`nested_in_raid` says how many).
* its tree is the run plus every agent it spawned after its start, linked through each
  agent's `.meta.json` (`toolUseId`, or `parentAgentId` for forked skills).

Every gap between two consecutive records of one trace is attributed to the
record that ENDS it: an assistant record is generation (model latency
included); a tool_result is that tool's category; a human prompt is human
time; a task-notification is background wait (blocked on a spawned agent or
background command). Passive records (attachments, system notes, meta user
records) are stamped with the event that follows them, so their gap goes to
the next decisive record. READ: the gaps. Heuristic: the categories (test
commands are recognised by gate_traces.gate_classes).

Two views per skill: `orchestrator` (the run's own trace, i.e. its critical
path) and `tree` (summed agent-seconds, parallel work counted per agent).

Redundant testing: across the whole tree, a test command is a rerun when the
same gate class already ran in the same worktree with no mutation in between
(an Edit/Write there, or a mutating git or shell command there). Split by the
earlier run's outcome. Worktree attribution follows a leading `cd` or `-C`,
else the record's cwd: a heuristic, so a rerun is an estimate, not a proof.
"""

import argparse
import importlib.util
import json
import math
import os
import re
import statistics
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "gate_traces", Path(__file__).resolve().parent / "gate_traces.py"
)
gt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gt)

DEFAULT_ROOT = Path.home() / ".claude/projects"
SKILLS = ("raid", "hunt", "gaze")
POLL = re.compile(r"\bsleep\b|\bidle(\.sh)?\b|\buntil\b|\bwhile\b|\bwait\b|for \w+ in .*(seq|\{1\.\.)")
GIT = re.compile(r"^\s*(git|gh|glab|erg-pr\S*|tickets/erg)\b|raid-merge|sync-local-main")
MUT_GIT = re.compile(
    r"\bgit\b[^|;&]*\b(commit|rebase|merge|pull|reset|checkout|switch|cherry-pick|am|restore|apply)\b(?!-)"
)
MUT_SH = re.compile(r"\bsed -i|\bperl -pi|\bmv |\bcp |\brm |>\s*[\w./~-]+\.\w+\b")
CD = re.compile(r"^\s*cd\s+(\"[^\"]+\"|'[^']+'|\S+)")
DASH_C = re.compile(r"\s-C\s+(\"[^\"]+\"|'[^']+'|\S+)")
BLOCKER_MIN_S = 60
ENV_ASSIGN = re.compile(r"[A-Za-z_]\w*=")
NOT_BLOCKERS = {"generation", "human", "human-away", "idle-tail"}  # reported in the split, not here
AWAY_S = 1800  # a human gap longer than this is the author away, not a reply


def _ts(stamp):
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def worktree_root(path):
    m = re.search(r"^(.*?/\.claude/worktrees/[^/]+)", path or "")
    return m.group(1) if m else (path or "").rstrip("/")


def command_dir(cmd, cwd):
    for pattern in (CD, DASH_C):
        m = (pattern.match if pattern is CD else pattern.search)(cmd)
        if m:
            d = m.group(1).strip("\"'").replace("~", str(Path.home()))
            if d.startswith("/"):
                return worktree_root(d)
    return worktree_root(cwd)


def _blocks(rec):
    c = (rec.get("message") or {}).get("content")
    return c if isinstance(c, list) else []


def _text(rec):
    c = (rec.get("message") or {}).get("content")
    if isinstance(c, str):
        return c
    return " ".join(
        b.get("text", "") for b in _blocks(rec) if isinstance(b, dict) and b.get("type") == "text"
    )


def _results(rec):
    return [b for b in _blocks(rec) if isinstance(b, dict) and b.get("type") == "tool_result"]


def tool_category(name, inp):
    if name == "Bash":
        cmd = inp.get("command", "")
        if inp.get("run_in_background"):
            return "bash-bg-launch"
        if gt.gate_classes(cmd):
            return "test/gate"
        if GIT.search(cmd):
            return "git/forge"
        # quotes are kept: a loop often hides in `bash -c '...'`
        if POLL.search(gt._strip_heredocs(cmd)):
            return "poll/wait"
        return "bash-other"
    if name in ("Agent", "Task"):
        return "agent-foreground"
    if name == "Skill":
        return "forked-skill"  # an inline skill returns at once; only forks take time
    if name in ("TaskOutput", "Monitor", "ScheduleWakeup"):
        return "poll/wait"
    if name == "AskUserQuestion":
        return "human"
    if name in ("Read", "Grep", "Glob", "Edit", "Write", "NotebookEdit"):
        return "file-io"
    return "tool-other"


def command_key(cmd):
    """The command's leading program words, never its arguments or values.

    A trace can hold a credential typed into a command; the report names
    only what ran (`timeout bash`, `until`, `uv run`), as trace-friction's
    Pi mode never prints a command text.
    """
    c = re.sub(r"^\s*cd\s+\S+\s*&&\s*", "", gt._strip_heredocs(cmd)).strip()
    words = []
    for w in re.split(r"[\s;&|]+", c.split("\n")[0]):
        if not w or ENV_ASSIGN.match(w):
            continue
        w = os.path.basename(w)
        if not re.fullmatch(r"[A-Za-z][\w.-]*", w) or len(words) == 2:
            break
        words.append(w)
    return " ".join(words) or "(unnamed)"


class Trace:
    def __init__(self, path, records, meta=None):
        self.path = path
        self.recs = sorted(records, key=lambda r: r["timestamp"])
        self.meta = meta or {}
        self.children = []
        self.uses = {}  # tool_use id -> (name, input, time, cwd)
        self.skills = []  # (time, skill name)
        for r in self.recs:
            if r["type"] == "assistant":
                for b in _blocks(r):
                    if isinstance(b, dict) and b.get("type") == "tool_use":
                        inp = b.get("input") or {}
                        self.uses[b.get("id")] = (b.get("name"), inp, _ts(r["timestamp"]), r.get("cwd", ""))
                        if b.get("name") == "Skill":
                            self.skills.append((_ts(r["timestamp"]), inp.get("skill", "")))
            elif r["type"] == "user":
                m = re.search(r"<command-name>/?([\w:-]+)</command-name>", _text(r))
                if m:
                    self.skills.append((_ts(r["timestamp"]), m.group(1)))

    def start_of(self, skill):
        if skill == "gaze":
            return _ts(self.recs[0]["timestamp"]) if self.meta.get("forked") == "gaze" else None
        return next((t for t, s in self.skills if s == skill), None)

    def _decisive(self, rec):
        """Category of a record that ends a gap, or None for a passive record."""
        if rec["type"] == "assistant":
            return "generation"
        if rec["type"] != "user" or rec.get("isMeta"):
            return None
        res = _results(rec)
        if res:
            use = self.uses.get(res[0].get("tool_use_id"))
            return tool_category(use[0], use[1]) if use else "tool-other"
        txt = _text(rec)
        if "<task-notification>" in txt:
            return "background-wait"
        return "human" if txt.strip() else None

    def gaps(self, start=None):
        """Yield (seconds, category, deciding record) for every gap from `start` on.

        A passive record takes the category and record of the next decisive
        one; passive records after the last decisive one are `idle-tail`.
        """
        recs = [r for r in self.recs if start is None or _ts(r["timestamp"]) >= start]
        cats = [(self._decisive(r), r) for r in recs]
        following = ("idle-tail", None)
        for i in range(len(cats) - 1, -1, -1):
            if cats[i][0] is None:
                cats[i] = following
            else:
                following = cats[i]
        for i in range(1, len(recs)):
            gap = (_ts(recs[i]["timestamp"]) - _ts(recs[i - 1]["timestamp"])).total_seconds()
            cat, rec = cats[i]
            if cat == "human" and gap > AWAY_S:
                cat = "human-away"
            yield gap, cat, rec

    def wall(self, start=None):
        recs = [r for r in self.recs if start is None or _ts(r["timestamp"]) >= start]
        return (_ts(recs[-1]["timestamp"]) - _ts(recs[0]["timestamp"])).total_seconds() if len(recs) > 1 else 0.0


def _load_records(path):
    out = []
    try:
        with path.open(errors="replace") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if "timestamp" in r and r.get("type") in ("assistant", "user", "attachment", "system"):
                    out.append(r)
    except OSError:
        pass
    return out


def _read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def load_traces(root, since):
    """Every recent trace under `root`, linked to its spawning parent."""
    sessions = {}
    for p in root.rglob("*.jsonl"):
        try:
            st = p.stat()
        except OSError:
            continue
        if st.st_size < 500 or datetime.fromtimestamp(st.st_mtime, timezone.utc) < since:
            continue
        sess = p.parent.parent if p.parent.name == "subagents" else p.with_suffix("")
        sessions.setdefault(sess, []).append(p)
    traces = []
    for sess, files in sessions.items():
        local, by_use = {}, {}
        for p in files:
            recs = _load_records(p)
            if not recs:
                continue
            meta = _read_json(p.with_suffix(".meta.json"))
            fork = p.with_name(p.stem + ".forked-skill.json")
            if fork.exists():
                meta["forked"] = _read_json(fork).get("skillName")
            tr = Trace(p, recs, meta)
            local[p] = tr
            for uid in tr.uses:
                by_use[uid] = tr
        for p, tr in local.items():
            parent = by_use.get(tr.meta.get("toolUseId"))
            if parent is None and tr.meta.get("parentAgentId"):
                parent = local.get(p.with_name(f"agent-{tr.meta['parentAgentId']}.jsonl"))
            if parent is None and p.parent.name == "subagents":
                parent = local.get(sess.with_suffix(".jsonl"))
            if parent is not None and parent is not tr:
                parent.children.append(tr)
        traces.extend(local.values())
    return traces


def descendants(tr):
    out, stack, seen = [], list(tr.children), {id(tr)}
    while stack:
        c = stack.pop()
        if id(c) in seen:
            continue
        seen.add(id(c))
        out.append(c)
        stack.extend(c.children)
    return out


def test_events(trees, start):
    """Time-ordered ('test', t, dir, label, failed, secs) and ('mut', t, dir) events."""
    ev = []
    for tr in trees:
        outcome = {}
        for r in tr.recs:
            for b in _results(r):
                outcome[b.get("tool_use_id")] = (_ts(r["timestamp"]), bool(b.get("is_error")))
        for uid, (name, inp, t, cwd) in tr.uses.items():
            if start is not None and tr is trees[0] and t < start:
                continue
            if name in ("Edit", "Write", "NotebookEdit"):
                fp = inp.get("file_path", "") or inp.get("notebook_path", "")
                root = worktree_root(fp) if "/.claude/worktrees/" in fp else worktree_root(cwd)
                ev.append(("mut", t, root))
            elif name == "Bash":
                cmd = inp.get("command", "")
                d = command_dir(cmd, cwd)
                classes = gt.gate_classes(cmd)
                if classes and not inp.get("run_in_background"):
                    end, failed = outcome.get(uid, (t, False))
                    ev.append(("test", t, d, ",".join(sorted(classes)), failed, (end - t).total_seconds()))
                elif MUT_GIT.search(cmd) or MUT_SH.search(gt._strip_heredocs(cmd)):
                    ev.append(("mut", t, d))  # a test's own `> x.log` is not a change
    ev.sort(key=lambda e: e[1])
    return ev


def redundancy(events):
    counts, secs, last = Counter(), Counter(), {}
    for e in events:
        if e[0] == "mut":
            for key in [k for k in last if k[0] == e[2]]:
                del last[key]
            continue
        _, _, d, label, failed, s = e
        counts["runs"] += 1
        secs["runs"] += s
        if (d, label) in last:
            kind = "rerun_after_fail" if last[(d, label)] else "rerun_after_pass"
            counts[kind] += 1
            secs[kind] += s
        last[(d, label)] = failed
    return counts, secs


def blocker_label(tr, cat, rec):
    res = _results(rec) if rec else []
    use = tr.uses.get(res[0].get("tool_use_id")) if res else None
    if use is None:
        return cat
    if use[0] == "Bash":
        return f"{cat} :: {command_key(use[1].get('command', ''))}"
    if use[0] == "Skill":
        return f"{cat} :: {use[1].get('skill', '')}"
    return f"{cat} :: {use[0]}"


def survey(traces, since, top=20):
    raid_members = set()
    runs = {s: [] for s in SKILLS}
    for tr in traces:
        for skill in SKILLS:
            start = tr.start_of(skill)
            if start is not None and start >= since:
                runs[skill].append((tr, start))
                if skill == "raid":
                    raid_members.update(id(d) for d in descendants(tr))
    report = {}
    for skill, lst in runs.items():
        orch, tree, blockers = Counter(), Counter(), Counter()
        red_n, red_s = Counter(), Counter()
        walls, agents, nested = [], 0, 0
        for tr, start in lst:
            nested += skill == "hunt" and id(tr) in raid_members
            kids = [k for k in descendants(tr) if k.recs and _ts(k.recs[0]["timestamp"]) >= start]
            agents += len(kids)
            walls.append(tr.wall(start))
            for member, member_start in [(tr, start)] + [(k, None) for k in kids]:
                for gap, cat, rec in member.gaps(member_start):
                    tree[cat] += gap
                    if member is tr:
                        orch[cat] += gap
                    if cat not in NOT_BLOCKERS and gap >= BLOCKER_MIN_S:
                        blockers[blocker_label(member, cat, rec)] += gap
            n, s = redundancy(test_events([tr] + kids, start))
            red_n.update(n)
            red_s.update(s)
        walls.sort()
        report[skill] = {
            "runs": len(lst),
            "nested_in_raid": nested,
            "agents": agents,
            "wall_median_s": statistics.median(walls) if walls else 0,
            "wall_p90_s": walls[math.ceil(0.9 * len(walls)) - 1] if walls else 0,  # nearest rank
            "wall_total_s": sum(walls),
            "orchestrator_s": dict(orch.most_common()),
            "tree_s": dict(tree.most_common()),
            "test_runs": dict(red_n),
            "test_secs": {k: round(v) for k, v in red_s.items()},
            "blockers_s": [(k, round(v)) for k, v in blockers.most_common(top)],
        }
    return report


def _fmt(d):
    total = sum(d.values()) or 1
    return ", ".join(f"{k} {v / 3600:.1f}h ({100 * v / total:.0f}%)" for k, v in d.items() if v >= 36)


def print_report(report, days):
    print(f"trace-wall-time: last {days:g} days. READ: record gaps; heuristic: categories.")
    for skill, r in report.items():
        print(
            f"\n## {skill}: {r['runs']} runs ({r['nested_in_raid']} inside a raid), {r['agents']} agents, "
            f"wall median {r['wall_median_s'] / 60:.1f} min, p90 {r['wall_p90_s'] / 60:.1f}, "
            f"total {r['wall_total_s'] / 3600:.1f} h"
        )
        print(f"  orchestrator: {_fmt(r['orchestrator_s'])}")
        print(f"  tree (agent-time): {_fmt(r['tree_s'])}")
        n, s = r["test_runs"], r["test_secs"]
        print(
            f"  tests: {n.get('runs', 0)} runs, {s.get('runs', 0) / 60:.0f} min; reruns with no change: "
            f"{n.get('rerun_after_pass', 0)} after a pass ({s.get('rerun_after_pass', 0) / 60:.0f} min), "
            f"{n.get('rerun_after_fail', 0)} after a failure ({s.get('rerun_after_fail', 0) / 60:.0f} min)"
        )
        print("  top blockers (waits >= 60 s, summed):")
        for label, secs in r["blockers_s"][:10]:
            print(f"    {secs / 3600:6.1f} h  {label}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=float, default=28)
    ap.add_argument("--projects-dir", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    since = datetime.now(timezone.utc) - timedelta(days=a.days)
    report = survey(load_traces(a.projects_dir, since), since, a.top)
    if a.json:
        json.dump(report, sys.stdout, indent=1)
        print()
    else:
        print_report(report, a.days)
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Bad stops in Claude Code session traces: ask without ask-up, wait without wake.

    python3 scripts/trace-stopguard.py [--days N] [--projects-dir DIR] [--json] [--list]

Zero-LLM, standard-library-only measure for ticket 1294, the after-the-fact
replacement for Stopguard's dry-run hook (conception/2026-10-21-stopguard-design.md,
gate G1 of ticket 1164). It reuses trace-wall-time.py's trace walk and counts
two bad stops per ISO week:

* a stop is a turn (records from one prompt, human or task-notification, to
  the next) whose last assistant record calls no tool; a turn the author
  interrupted mid-tool is not a stop. Sub-agent traces are excluded: their
  final message goes to a parent, not to the author.
* ask without ask-up: the last non-empty line outside a code fence ends in
  `?` (trailing markdown stripped), or the turn called AskUserQuestion, and
  no advisor call came earlier in the turn: an Agent call whose model is
  fable or whose description, type or prompt head names an advisor, and
  whose result is not an error; a worker spawn is not an ask-up. A
  question naming an author's-call act (merge, push, delete, spend, scope...)
  is excluded and counted as `authors_call`.
* wait without wake: the final text matches a wait vocabulary (waiting for,
  once CI passes, when the coder's PR lands, auto-merge, will be notified...),
  not addressed to the author ("waiting for your go"), while nothing pending
  will wake the session: no background agent (the runtime's own
  `pendingBackgroundAgentCount` on the turn's `turn_duration` record; when the
  key or record is missing, Agent launches whose result was the async-launch
  notice and that no task-notification's tool-use id has matched yet), no background Bash or Workflow without
  its task-notification, no Monitor within its timeout, no ScheduleWakeup
  before its delay.

READ: turns, tool calls, notifications, the pending-agent count. Heuristic:
both vocabularies, the author's-call exclusion, and the advisor test. Precision and recall against a hand-labelled sample:
conception/2026-10-27-stopguard-measure-labels.md. Codex and Pi traces are
another format and are reported unmeasured.
"""

import argparse
import importlib.util
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "trace_wall_time", Path(__file__).resolve().parent / "trace-wall-time.py"
)
wt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wt)
Trace = wt.Trace
load_traces = wt.load_traces

G1_PER_WEEK = 5  # ticket 1164 gate G1: below this on Claude Code, Stopguard stays closed
MONITOR_DEFAULT_S = 3600  # assumed when a Monitor call states no timeout
ADVISOR = re.compile(r"advis|conseil|second opinion|ask[- ]up", re.I)
ADVISOR_MODELS = {"fable"}
FENCE = re.compile(r"^\s*(```|~~~).*?^\s*(```|~~~)\s*$", re.M | re.S)
TRAIL = " \t*_`\"')]>"
AUTHORS_CALL = re.compile(
    r"\b(merge|push|publish|release|tag|delete|remove|force|close|send|submit|spend|pay|budget|USD|"
    r"irreversible|scope|deploy|post|"
    r"fusionn\w*|pouss\w*|publi\w*|supprim\w*|ferm\w*|envoi\w*|envoy\w*|soumet\w*|dépens\w*|périmètre)\b|\$\d",
    re.I,
)
_DONE = r"(finish|finishes|finished|pass|passes|land|lands|complete|completes|return|returns|reports?|is green|are green|comes? back|is done|are done|merges?)"
WAIT = re.compile(
    r"\b(waiting (for|on|until)|(I'll|I will|I'm going to|will) wait|"
    rf"(once|when|after) (CI|it|they|the [\w'’ -]{{1,40}}?) {_DONE}\b|"
    r"will be notified|(I'll|I will) (be notified|check back|report back|come back)|auto-?merge)",
    re.I,
)
ASYNC = re.compile(r"async agent launched|running in the background", re.I)
TOOL_USE_ID = re.compile(r"<tool-use-id>(\S+?)</tool-use-id>")


def _blocks(rec):
    c = (rec.get("message") or {}).get("content")
    return c if isinstance(c, list) else []


def _uses(rec):
    return [b for b in _blocks(rec) if isinstance(b, dict) and b.get("type") == "tool_use"]


def _is_prompt(rec):
    """A record that opens a turn: a non-meta user message that is not a tool result."""
    if rec["type"] != "user" or rec.get("isMeta"):
        return False
    if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in _blocks(rec)):
        return False
    return bool(wt._text(rec).strip())


def is_advisor(use):
    """An Agent call consulting a higher model, not a worker spawn."""
    if use.get("name") not in ("Agent", "Task"):
        return False
    inp = use.get("input") or {}
    if inp.get("model") in ADVISOR_MODELS:
        return True
    head = " ".join(str(inp.get(k) or "") for k in ("description", "subagent_type")) + " " + str(inp.get("prompt") or "")[:300]
    return bool(ADVISOR.search(head))


def last_line(text):
    lines = [ln for ln in FENCE.sub("", text).splitlines() if ln.strip()]
    return lines[-1].strip().rstrip(TRAIL) if lines else ""


def wait_hit(text):
    paras = [p for p in re.split(r"\n\s*\n", FENCE.sub("", text)) if p.strip()]
    text = "\n\n".join(paras[-2:])  # the closing words, not a progress recap above them
    for m in WAIT.finditer(text):
        if not re.match(r"\s*(for |on )?(your|you)\b", text[m.end():], re.I):
            return True
    return False


def _num(v, default):
    """A tool input number; traces sometimes carry it as a string."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _week(t):
    y, w, _ = t.isocalendar()
    return f"{y}-W{w:02d}"


def stops(trace):
    """One dict per stop of a trace, flags included, in order."""
    out = []
    bash, agents, timed = set(), set(), {}  # pending launches: ids, ids, id -> expiry
    turn, seg = 0, []

    def close(seg, turn):
        asst = [r for r in seg if r["type"] == "assistant"]
        if not asst or _uses(asst[-1]):
            return
        end = wt._ts(asst[-1]["timestamp"])
        tail = []
        for r in reversed(asst):
            if _uses(r):
                break
            tail.insert(0, wt._text(r))
        text = "\n".join(tail).strip()
        uses = [b for r in asst for b in _uses(r)]
        failed = {
            b.get("tool_use_id") for r in seg for b in _blocks(r)
            if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("is_error")
        }
        advisor = asked_tool = False
        for b in uses:
            if is_advisor(b) and b.get("id") not in failed:
                advisor = True
            elif b.get("name") == "AskUserQuestion" and not advisor:
                asked_tool = True
        line = last_line(text)
        question = line.endswith("?")
        authors_call = question and bool(AUTHORS_CALL.search(line))
        dur = next((r for r in seg if r["type"] == "system" and r.get("subtype") == "turn_duration"), None)
        # the runtime's own count when it states one; an absent key is not a zero (older versions omit it)
        n_agents = dur["pendingBackgroundAgentCount"] if dur and "pendingBackgroundAgentCount" in dur else len(agents)
        n_flows = (dur or {}).get("pendingWorkflowCount", 0)
        pending = n_agents + n_flows + len(bash) + sum(1 for t in timed.values() if t is None or t > end)
        out.append({
            "msg": (asst[-1].get("message") or {}).get("id"),
            "session": trace.path.stem,
            "turn": turn,
            "ts": asst[-1]["timestamp"],
            "week": _week(end),
            "ask_without_ask_up": asked_tool or (question and not advisor and not authors_call),
            "authors_call": authors_call,
            "wait_without_wake": not question and wait_hit(text) and pending == 0,
            "pending": pending,
            "tail": text[-160:],
        })

    for r in trace.recs:
        if _is_prompt(r):
            if seg:
                close(seg, turn)
            turn, seg = turn + 1, []
            for tid in TOOL_USE_ID.findall(wt._text(r)):
                bash.discard(tid)
                agents.discard(tid)
                timed.pop(tid, None)
        if turn == 0:
            continue
        seg.append(r)
        for b in _blocks(r):  # a foreground agent returns its report, never a notification
            if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id") in agents:
                if b.get("is_error") or not ASYNC.search(json.dumps(b.get("content"))[:300]):
                    agents.discard(b.get("tool_use_id"))
        if r["type"] == "assistant":
            t = wt._ts(r["timestamp"])
            for b in _uses(r):
                name, inp = b.get("name"), b.get("input") or {}
                if (name == "Bash" and inp.get("run_in_background")) or name == "Workflow":
                    bash.add(b.get("id"))
                elif name in ("Agent", "Task"):
                    agents.add(b.get("id"))
                elif name == "Monitor":
                    secs = _num(inp.get("timeout_ms"), MONITOR_DEFAULT_S * 1000) / 1000
                    timed[b.get("id")] = None if inp.get("persistent") else t + timedelta(seconds=secs)
                elif name == "ScheduleWakeup":
                    timed[b.get("id")] = t + timedelta(seconds=_num(inp.get("delaySeconds"), 0))
    if seg:
        close(seg, turn)
    return out


def report(traces, since, now=None):
    now = now or datetime.now(timezone.utc)
    weeks = defaultdict(lambda: {"stops": 0, "ask_without_ask_up": 0, "wait_without_wake": 0, "bad": 0})
    offending, authors_call, seen = [], 0, set()
    for tr in sorted(traces, key=lambda t: t.recs[0]["timestamp"]):
        if tr.path.parent.name == "subagents":
            continue
        for s in stops(tr):
            if wt._ts(s["ts"]) < since or (s["msg"] and s["msg"] in seen):
                continue  # a fork or resume replays its parent's stops: count them once
            seen.add(s["msg"])
            w = weeks[s["week"]]
            w["stops"] += 1
            w["ask_without_ask_up"] += s["ask_without_ask_up"]
            w["wait_without_wake"] += s["wait_without_wake"]
            bad = s["ask_without_ask_up"] or s["wait_without_wake"]
            w["bad"] += bad
            authors_call += s["authors_call"]
            if bad:
                offending.append(s)
    total_bad = sum(w["bad"] for w in weeks.values())
    span_weeks = max((now - since).total_seconds() / (7 * 86400), 1 / 7)
    rate = total_bad / span_weeks  # derived: window total / window length in weeks
    return {
        "runtimes": {
            "claude-code": {"weeks": dict(sorted(weeks.items())), "authors_call_excluded": authors_call},
            "codex": "unmeasured",
            "pi": "unmeasured",
        },
        "g1": {
            "ticket": 1164,
            "threshold_per_week": G1_PER_WEEK,
            "bad_per_week": round(rate, 1),
            "verdict": "at_or_above" if rate >= G1_PER_WEEK else "below",
        },
        "offending": offending,
    }


def print_report(rep, days, listing):
    print(f"trace-stopguard: last {days:g} days, claude-code only (codex, pi unmeasured). "
          "READ: turns; heuristic: vocabularies.")
    print(f"{'week':10} {'stops':>6} {'ask':>5} {'wait':>5} {'bad':>5}")
    for wk, w in rep["runtimes"]["claude-code"]["weeks"].items():
        print(f"{wk:10} {w['stops']:6} {w['ask_without_ask_up']:5} {w['wait_without_wake']:5} {w['bad']:5}")
    g = rep["g1"]
    print(f"1164 gate G1: >= {g['threshold_per_week']} bad stops per week on Claude Code -> reopen; "
          f"measured {g['bad_per_week']}/week (derived: window total / weeks): {g['verdict']}")
    if listing:
        for s in rep["offending"]:
            kind = "+".join(k for k in ("ask_without_ask_up", "wait_without_wake") if s[k])
            print(f"  {s['session']}:{s['turn']} {s['ts']} {kind} :: {s['tail']!r}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--days", type=float, default=28)
    ap.add_argument("--projects-dir", type=Path, default=wt.DEFAULT_ROOT)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list", action="store_true", help="list offending turns (local reading only; never commit)")
    a = ap.parse_args(argv)
    since = datetime.now(timezone.utc) - timedelta(days=a.days)
    rep = report(load_traces(a.projects_dir, since), since)
    if not a.list:
        rep.pop("offending")
    if a.json:
        json.dump(rep, sys.stdout, indent=1)
        print()
    else:
        print_report(rep, a.days, a.list)
    return 0


if __name__ == "__main__":
    sys.exit(main())

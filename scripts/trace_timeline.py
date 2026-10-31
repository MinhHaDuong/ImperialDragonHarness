#!/usr/bin/env python3
"""Render one session as a Chrome Trace Event JSON timeline (ticket 1385; memo conception/2026-10-31-monitoring-redesign.md 4.4).

    trace_timeline.py <claude session id> [--out FILE] [--html FILE]

Reads the session, its `subagents/`, and the seats its launch lines (ticket 1384) name as children of
it, each from the live tree first and the archive (ticket 1383) second, so a session already pruned from
the live tree still renders. Writes the Chrome Trace Event format (Perfetto, chrome://tracing; no Perfetto
library is involved). `--html FILE` also writes one self-contained HTML page of the same lanes and events:
inline SVG, CSS and JS, no external URL, opens in Firefox; hover a bar for its details, zoom with the
buttons or the scrollbar.

Layout: one process (lane) per set of non-overlapping agents, assigned greedily by start time, so
concurrent agents land on distinct lanes. Thread 0 of a lane carries the agent span; threads 1.. carry its
turns and tool calls, one row each where calls overlap. A subagent or seat names its parent in its span.
Every event carries its pointer (file, call id) in `args`; an unpriced model shows `cost unknown`.

Paths come from `transcript_spool` (live roots, archive, host) and `launch_line` (launches file).
"""
import argparse
import getpass
import html
import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
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
        return cls(live, spool.raw_dir())

    def find(self, runtime: str, pattern: str) -> tuple[str, Path] | None:
        """(relative path, readable path) of the first match: live roots first, then the archive."""
        for root in self.live.get(runtime, []):
            for hit in sorted(root.glob(pattern)):
                return hit.relative_to(root).as_posix(), hit
        base = self.archive / runtime
        for hit in sorted(base.glob(pattern + ".zst")):
            return hit.relative_to(base).as_posix().removesuffix(".zst"), hit
        return None

    def session_ids(self, prefix: str) -> list[str]:
        """Claude session ids starting with `prefix`, live tree and archive together, sorted."""
        found: set[str] = set()
        for root in self.live.get("claude", []):
            found.update(hit.stem for hit in root.glob(f"*/{prefix}*.jsonl"))
        found.update(hit.name.removesuffix(".jsonl.zst") for hit in (self.archive / "claude").glob(f"*/{prefix}*.jsonl.zst"))
        return sorted(found)

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


def resolve_session(tree: Tree, prefix: str) -> str:
    """The full session id for an id or a unique prefix of one; an ambiguous prefix lists its candidates."""
    ids = tree.session_ids(prefix)
    if prefix in ids:
        return prefix
    if len(ids) > 1:
        raise SystemExit(f"trace_timeline: prefix {prefix} is ambiguous, candidates:\n  " + "\n  ".join(ids))
    return ids[0] if ids else prefix  # none: collect reports the unknown session


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
    if event.tool_class:
        args["class"] = event.tool_class
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


def _fmt_dur(sec: float) -> str:
    return f"{sec:.1f}s" if sec < 120 else f"{sec / 60:.1f}min"


def _tooltip(e: dict) -> str:
    a = e["args"]
    ptr = a.get("pointer") or {}
    usd = a.get("shadow_usd")
    lines = [e["name"], f"kind: {e['cat']}", *([f"class: {a['class']}"] if a.get("class") else []), f"duration: {_fmt_dur(e['dur'] / 1e6)}", f"model: {a.get('model')}",
             f"tokens: {a.get('tokens')}", f"shadow USD: {usd if usd != COST_UNKNOWN else COST_UNKNOWN}",
             f"exit: {a.get('exit')}", f"pointer: {ptr.get('file')} / {ptr.get('call_id')}"]
    return "\n".join(lines)


# Colour encodes what the time is spent on, not the tool's name. Chromatic hues are slots of the
# dataviz skill's validated palette (blue, orange, aqua: the first three validate all-pairs, light
# mode); presence and the catch-all are neutrals, which carry no identity by design.
_PRESENCE_AGENT, _PRESENCE_TURN = "#6b7f94", "#55606b"   # cool greys: an agent's life, a model turn
_DELEGATION, _VERIFICATION, _HOUSEKEEPING, _OTHER = "#eb6834", "#2a78d6", "#1baf7a", "#9a958b"
_COLORS = {"agent": _PRESENCE_AGENT, "turn": _PRESENCE_TURN, "tool": _OTHER}
_CLASS_COLORS = {"subagent": _DELEGATION, "worker": _DELEGATION, "tests": _VERIFICATION,
                 "git": _HOUSEKEEPING, "file": _HOUSEKEEPING, "other": _OTHER}
# (group caption, ((legend entry, colour, meaning, swatch opacity), ...)): one colour per entry.
_LEGEND = (
    ("Presence", (("agent", _PRESENCE_AGENT, "an agent's whole span: session, subagent or seat", 0.45),
                  ("turn", _PRESENCE_TURN, "one model turn: the agent thinking", 0.9))),
    ("Delegation", (("delegation", _DELEGATION, "a Skill or Agent call, or a shell launching a headless coder or reviewer", 0.9),)),
    ("Verification", (("tests", _VERIFICATION, "pytest, make check or lint", 0.9),)),
    ("Housekeeping", (("files and git", _HOUSEKEEPING, "reading, editing and searching files; version control, forge and tickets", 0.9),)),
    ("Anything else", (("other", _OTHER, "any other call", 0.9),)),
)

_CSS = """
body{font-family:system-ui,sans-serif;margin:0;color:#222;background:#fafafa}
header{padding:18px 24px 6px}
header>*:not(.legend){max-width:960px}
h1{font-size:22px;margin:0 0 4px}
.meta{color:#555;font-size:13px;margin:0 0 10px}
.how{font-size:14px;line-height:1.5;margin:0 0 10px}
.legend{font-size:12px;color:#444;margin:0 0 8px;display:flex;flex-wrap:wrap;gap:6px 22px}
.legend .g{display:flex;flex-direction:column;gap:2px}
.legend .g b{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:#666;font-weight:600}
.legend .g span{display:block}
.legend i{display:inline-block;width:12px;height:12px;margin:0 5px 0 0;vertical-align:-2px;border-radius:2px}
.bar{padding:0 24px 6px;font-size:13px}
button{font:inherit;padding:2px 10px;margin-right:4px}
#mm{display:block;width:calc(100% - 48px);margin:0 24px 6px;border:1px solid #bbb;cursor:pointer}
rect.view{fill:rgba(30,90,200,.18);stroke:#1e5ac8;stroke-width:1.5;pointer-events:none}
#wrap{position:relative;margin:0 24px 24px}
#w{overflow:auto;max-height:78vh;border:1px solid #bbb;background:#fff;cursor:grab}
#w.drag{cursor:grabbing;user-select:none}
#tl{display:block}
#cur{position:absolute;top:0;bottom:0;width:0;border-left:2px solid #d00;pointer-events:none;z-index:4}
#lab{position:sticky;left:0;height:0;z-index:3;overflow:visible}
#lab div{position:absolute;left:0;box-sizing:border-box;padding:0 4px;font-size:11px;white-space:nowrap;overflow:hidden;
text-overflow:ellipsis;border-right:1px solid #bbb;pointer-events:none}
#lab .lb{pointer-events:auto}
#lab #grip{padding:0;border:0;width:7px;background:transparent;cursor:col-resize;pointer-events:auto;z-index:5;overflow:visible}
#lab #grip:hover,#lab #grip.on{background:rgba(30,90,200,.35)}
#lab .head{top:0;background:#fff;color:#a00;line-height:16px;padding-top:4px}
#lab .lb{line-height:18px}
rect.bar-ev:hover{stroke:#000;stroke-width:1}
text{fill:#222;pointer-events:none}
"""

_JS = """
var NS='http://www.w3.org/2000/svg',svg=document.getElementById('tl'),box=document.getElementById('w'),
mm=document.getElementById('mm'),ticks=document.getElementById('ticks'),cur=document.getElementById('cur'),
ro=document.getElementById('cro'),labs=document.querySelectorAll('#lab .lb'),
ROWS=JSON.parse(document.getElementById('rows').textContent),
span=+svg.dataset.span,left=+svg.dataset.left,pps=+svg.dataset.pps,t0=+svg.dataset.t0,H=+svg.dataset.h,
pad=0,X0=left,MIN=pps/50,MAX=4000,STEPS=[1,2,5,10,15,30,60,120,300,600,900,1800,3600,7200,10800,21600,43200,86400];
function p2(n){return (n<10?'0':'')+n;}
function hms(t){var d=new Date((t0+t)*1000);return p2(d.getHours())+':'+p2(d.getMinutes())+':'+p2(d.getSeconds());}
function drawTicks(){while(ticks.firstChild)ticks.removeChild(ticks.firstChild);
var step=STEPS[STEPS.length-1];for(var i=0;i<STEPS.length;i++){if(STEPS[i]*pps>=90){step=STEPS[i];break;}}
var off=-new Date(t0*1000).getTimezoneOffset()*60,k=Math.ceil((t0+off)/step)*step-off-t0,day=null;
for(;k<=span;k+=step){var d=new Date((t0+k)*1000),x=X0+k*pps,dk=d.getFullYear()+'-'+p2(d.getMonth()+1)+'-'+p2(d.getDate());
var l=document.createElementNS(NS,'line');l.setAttribute('x1',x);l.setAttribute('x2',x);l.setAttribute('y1',34);
l.setAttribute('y2',H);l.setAttribute('stroke','#ccc');ticks.appendChild(l);
var t=document.createElementNS(NS,'text');t.setAttribute('x',x+3);t.setAttribute('y',30);t.setAttribute('font-size',10);
t.textContent=p2(d.getHours())+':'+p2(d.getMinutes())+(step<60?':'+p2(d.getSeconds()):'');ticks.appendChild(t);
if(dk!=day){day=dk;var u=document.createElementNS(NS,'text');u.setAttribute('x',x+3);u.setAttribute('y',16);
u.setAttribute('font-size',11);u.setAttribute('font-weight','bold');u.textContent=dk;ticks.appendChild(u);}}}
function cursorT(){return box.scrollLeft/pps;}
function labels(){var t=cursorT();ro.textContent=hms(Math.max(0,Math.min(span,t)));
for(var r=0;r<labs.length;r++){var best=null,list=ROWS[r];
for(var j=0;j<list.length;j++){var e=list[j];if(t>=e[0]&&t<=e[0]+e[1]&&(!best||e[1]<best[1]))best=e;}
var el=labs[r];if(best){el.textContent=(el.dataset.call?'\\u21b3 ':'')+best[2]+(best[3]?' \\u00b7 '+best[3]:'');
el.title=el.textContent;}else{el.textContent='';el.title=el.dataset.fb;}}}
function stick(){var s0=box.scrollLeft+left,s1=box.scrollLeft+box.clientWidth;
svg.querySelectorAll('text[data-n]').forEach(function(n){var bx=X0+n.dataset.t*pps,v0=Math.max(bx,s0),
v1=Math.min(bx+n.dataset.d*pps,s1),room=v1-v0-6,name=n.dataset.n,full=n.dataset.m?name+' \\u00b7 '+n.dataset.m:name,txt='';
if(room>=full.length*5.5)txt=full;else if(room>=name.length*5.5)txt=name;
else{var c=Math.floor(room/5.5);if(c>=4)txt=name.slice(0,c-1)+'\\u2026';}
n.textContent=txt;n.style.display=txt?'':'none';n.setAttribute('x',v0+3);});}
var grip=document.getElementById('grip'),lcols=document.querySelectorAll('#lab > div:not(#grip)');
function setLeft(w){left=Math.round(Math.max(90,Math.min(w,Math.max(90,box.clientWidth-160))));
lcols.forEach(function(n){n.style.width=left+'px';});grip.style.left=(left-4)+'px';grip.style.height=H+'px';}
grip.addEventListener('mousedown',function(e){var x0=e.clientX,w0=left;grip.className='on';e.stopPropagation();e.preventDefault();
function mv(ev){setLeft(w0+ev.clientX-x0);lay();}
function up(){grip.className='';window.removeEventListener('mousemove',mv);window.removeEventListener('mouseup',up);}
window.addEventListener('mousemove',mv);window.addEventListener('mouseup',up);});
function lay(){pad=Math.max(0,(box.clientWidth-left)/2);X0=left+pad;var w=X0+span*pps+pad;svg.setAttribute('width',w);
svg.querySelectorAll('rect.bar-ev').forEach(function(n){n.setAttribute('x',X0+n.dataset.t*pps);
n.setAttribute('width',Math.max(1,n.dataset.d*pps));});
document.querySelectorAll('[data-band]').forEach(function(n){var b=n.dataset.band.split(' ');
n.setAttribute('d','M0 '+b[0]+'H'+w+'v'+b[1]+'H0z');});
cur.style.left=(1+left+pad)+'px';drawTicks();stick();labels();vp();}
function mmW(){return mm.getBoundingClientRect().width;}
var view=document.createElementNS(NS,'rect');view.setAttribute('class','view');
function buildMini(){var W=mmW(),h=+mm.getAttribute('height'),bg=document.createElementNS(NS,'rect');
bg.setAttribute('width','100%');bg.setAttribute('height',h);bg.setAttribute('fill','#f3f3f3');mm.appendChild(bg);
document.querySelectorAll('rect.bar-ev').forEach(function(n){var r=document.createElementNS(NS,'rect');
r.setAttribute('class','mb');r.setAttribute('data-t',n.dataset.t);r.setAttribute('data-d',n.dataset.d);
r.setAttribute('y',2+(+n.getAttribute('y')-40)/(H-50)*(h-4));r.setAttribute('height',1.5);r.setAttribute('fill',n.getAttribute('fill'));
mm.appendChild(r);});mm.appendChild(view);layMini();}
function layMini(){var W=mmW();mm.querySelectorAll('rect.mb').forEach(function(r){
r.setAttribute('x',r.dataset.t/span*W);r.setAttribute('width',Math.max(1,r.dataset.d/span*W));});vp();}
function vp(){var W=mmW(),a=Math.max(0,(box.scrollLeft-pad)/pps),b=Math.min(span,(box.scrollLeft+box.clientWidth-left-pad)/pps);
view.setAttribute('x',a/span*W);view.setAttribute('width',Math.max(2,(b-a)/span*W));
view.setAttribute('y',0);view.setAttribute('height',mm.getAttribute('height'));}
function seek(e){var W=mmW(),t=(e.clientX-mm.getBoundingClientRect().left)/W*span;
box.scrollLeft=Math.max(0,Math.min(span,t))*pps;}
var mdrag=false;
mm.addEventListener('mousedown',function(e){mdrag=true;seek(e);e.preventDefault();});
window.addEventListener('mousemove',function(e){if(mdrag)seek(e);});
box.addEventListener('scroll',function(){stick();labels();vp();});window.addEventListener('resize',function(){lay();layMini();});
function zoomAt(f,mx){var t=(box.scrollLeft+mx-X0)/pps,np=Math.min(MAX,Math.max(MIN,pps*f));
if(np==pps)return;pps=np;lay();box.scrollLeft=X0+t*pps-mx;stick();labels();vp();}
var cx=function(){return left+pad;};
document.getElementById('zi').onclick=function(){zoomAt(2,cx())};
document.getElementById('zo').onclick=function(){zoomAt(0.5,cx())};
box.addEventListener('wheel',function(e){e.preventDefault();
zoomAt(Math.exp(-e.deltaY*0.0015),e.clientX-box.getBoundingClientRect().left);},{passive:false});
var drag=null;
box.addEventListener('mousedown',function(e){if(e.button)return;
drag={x:e.clientX,y:e.clientY,sl:box.scrollLeft,st:box.scrollTop};box.classList.add('drag');e.preventDefault();});
window.addEventListener('mousemove',function(e){if(!drag)return;
box.scrollLeft=drag.sl-(e.clientX-drag.x);box.scrollTop=drag.st-(e.clientY-drag.y);});
window.addEventListener('mouseup',function(){drag=null;mdrag=false;box.classList.remove('drag');});
setLeft(left);pps=Math.max(MIN,Math.min(40,(box.clientWidth-left-20)/span));lay();buildMini();box.scrollLeft=pad;stick();labels();vp();
"""


def first_prompt(tree: Tree, session: str) -> str:
    """A human label for the session: its first typed prompt or slash command, one short line ("" if none)."""
    hit = tree.find("claude", f"*/{session}.jsonl")
    if hit is None:
        return ""
    try:
        for line in te.open_lines(hit[1]):
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict) or row.get("type") != "user" or row.get("isMeta") or row.get("isSidechain"):
                continue
            content = (row.get("message") or {}).get("content")
            if isinstance(content, list):
                content = " ".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
            if not isinstance(content, str) or not content.strip():
                continue
            name = re.search(r"<command-name>(.*?)</command-name>", content, re.S)
            if name:
                args = re.search(r"<command-args>(.*?)</command-args>", content, re.S)
                content = name.group(1).strip() + " " + (args.group(1).strip() if args else "")
            elif content.lstrip().startswith("<"):
                continue
            text = " ".join(content.split())
            return text if len(text) <= 120 else text[:117] + "..."
    except (OSError, subprocess.CalledProcessError):
        pass
    return ""


def default_author() -> str:
    """The session's user: global git `user.name` (never the repo-local agent identity), else the host user."""
    try:
        name = subprocess.run(["git", "config", "--global", "user.name"], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        name = ""
    if name:
        return name
    try:
        return getpass.getuser()
    except (KeyError, OSError):
        return os.environ.get("USER", "unknown")


def _stamp(epoch_s: float) -> str:
    return datetime.fromtimestamp(epoch_s, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def render_html(doc: dict, session: str = "", title: str = "", author: str = "") -> str:
    """One self-contained HTML page (inline SVG, CSS, JS; no external reference) of a `render` document."""
    names, events = {}, []
    for e in doc["traceEvents"]:
        if e.get("ph") == "M" and e["name"] in ("process_name", "thread_name"):
            names[(e["name"], e["pid"], e["tid"])] = e["args"]["name"]
        elif e.get("ph") == "X":
            events.append(e)
    keys = sorted({(e["pid"], e["tid"]) for e in events})
    row_of = {k: i for i, k in enumerate(keys)}
    span = max((e["ts"] + e["dur"] for e in events), default=0) / 1e6
    left, top, rh = 270, 40, 18
    pps = max(0.2, min(40.0, 1500 / span)) if span else 1.0
    t0 = (doc.get("otherData") or {}).get("t0_epoch")
    height = top + rh * len(keys) + 10
    q = html.escape
    parts = []
    # Lane bands: one shade per lane (pid), alternating, spanning the full width (JS sets the width).
    lane_rows: dict[int, list[int]] = {}
    for (pid, _tid), i in row_of.items():
        lane_rows.setdefault(pid, []).append(i)
    shade = {}
    for n, pid in enumerate(sorted(lane_rows)):
        rows = lane_rows[pid]
        y, h = top + rh * min(rows), rh * len(rows)
        shade[pid] = "#eef2f7" if n % 2 == 0 else "#ffffff"
        parts.append(f'<path data-band="{y} {h}" fill="{shade[pid]}"/>')
    lane_agents: dict[int, list[str]] = {}
    for e in sorted(events, key=lambda e: e["ts"]):
        if e["cat"] == "agent":
            lane_agents.setdefault(e["pid"], []).append(e["name"].split(" (under")[0])
    parts.append('<g id="ticks"/>')
    labels = ['<div class="head" style="height:%dpx;width:%dpx">cursor <span id="cro"></span></div>' % (top, left)]
    for (pid, tid), i in row_of.items():
        if tid == 0:
            who = lane_agents.get(pid, [])
            label = (who[0] + (f" +{len(who) - 1}" if len(who) > 1 else "")) if who else f"lane {pid}"
        else:
            label = "↳ calls"
        labels.append(f'<div class="lb" data-fb="{q(label)}"{" data-call=1" if tid else ""} '
                      f'style="top:{top + rh * i}px;height:{rh}px;width:{left}px;background:{shade[pid]}">{q(label)}</div>')
    labels.append('<div id="grip" title="drag to resize the label column"></div>')
    row_events: list[list] = [[] for _ in keys]
    for e in events:
        i = row_of[(e["pid"], e["tid"])]
        a = e["args"]
        cls = a.get("class")
        color = _CLASS_COLORS.get(cls) if e["cat"] == "tool" and cls else None
        fill = color or _COLORS.get(e["cat"], "#789")
        parts.append(f'<rect class="bar-ev" data-t="{e["ts"] / 1e6}" data-d="{e["dur"] / 1e6}" y="{top + rh * i + 2}" '
                     f'height="{rh - 4}" fill="{fill}" '
                     f'fill-opacity="{0.45 if e["cat"] == "agent" else 0.9}"><title>{q(_tooltip(e))}</title></rect>')
        base = e["name"].split(" (under")[0]
        row_events[i].append([e["ts"] / 1e6, e["dur"] / 1e6, base, a.get("detail") or (a.get("model") if e["cat"] == "agent" else "") or ""])
        if e["cat"] == "agent":
            parts.append(f'<text data-t="{e["ts"] / 1e6}" data-d="{e["dur"] / 1e6}" data-n="{q(base)}" '
                         f'data-m="{q(a.get("model") or "")}" y="{top + rh * i + 13}" font-size="10"></text>')
    rows_json = json.dumps(row_events).replace("</", "<\\/")
    heading = f"Session {session[:8]}" + (f": {title}" if title else "")
    meta = " · ".join(x for x in (f"id {session}" if session else "", f"author {author}" if author else "",
                                  f"started {_stamp(t0)}" if t0 else "",
                                  f"generated {_stamp(datetime.now(timezone.utc).timestamp())}",
                                  f"{len(events)} bars over {_fmt_dur(span)}") if x)
    how = ("This page is the timeline of one agent session. Each lane is an agent: the session itself, its "
           "subagents, and the review or worker seats it launched, listed under their parent. Each bar is a call, "
           "placed by its start time and sized by its duration; the pale wide bars are agent spans, the dark grey "
           "bars model turns, and the coloured bars tool calls, hued by what the time goes to: delegation, "
           "verification or housekeeping (legend below). Hover a bar for its "
           "class, model, tokens, shadow cost, and transcript pointer. The red line marks the middle of the "
           "chart: the label column on the left names, for each row, the agent or call under that line, and "
           "an agent bar's name (with its model when there is room) stays at the left edge while the bar "
           "runs off-screen. Zoom with the mouse wheel (centred on the pointer) or the buttons, and pan by "
           "holding the mouse button and dragging. The strip above the chart is a minimap of the whole "
           "session: the frame marks the part in view; click or drag on the strip to move there. Time "
           "labels are local wall-clock time.")
    legend = "".join(f'<div class="g"><b>{q(cap)}</b>' + "".join(
        f'<span><i style="background:{c};opacity:{o}"></i>{q(name)}: {q(m)}</span>' for name, c, m, o in entries) + "</div>"
        for cap, entries in _LEGEND)
    return (f'<!DOCTYPE html>\n<html><head><meta charset="utf-8"><title>{q(heading)}</title><style>{_CSS}</style>'
            f'</head><body><header><h1>{q(heading)}</h1><p class="meta">{q(meta)}</p><p class="how">{q(how)}</p>'
            f'<div class="legend">{legend}</div></header>'
            '<svg id="mm" xmlns="http://www.w3.org/2000/svg" height="44"></svg>'
            '<div class="bar"><button id="zo">zoom out</button><button id="zi">zoom in</button></div>'
            f'<div id="wrap"><div id="cur"></div><div id="w"><div id="lab">{"".join(labels)}</div>'
            f'<svg id="tl" xmlns="http://www.w3.org/2000/svg" height="{height}" data-span="{span}" '
            f'data-left="{left}" data-pps="{pps}" data-t0="{t0 or 0}" data-h="{height}">' + "".join(parts)
            + f'</svg></div></div><script type="application/json" id="rows">{rows_json}</script>'
            f'<script>{_JS}</script></body></html>\n')


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("session", help="Claude Code session id, or a unique prefix of one")
    parser.add_argument("--out", help="output file (default: <session>.trace.json in the current directory)")
    parser.add_argument("--html", help="also write a self-contained HTML timeline (inline SVG, opens in Firefox)")
    parser.add_argument("--archive-root", help="agent-sessions root holding raw/<host>/ (default: IDH_ARCHIVE_ROOT, else the transcript_spool default)")
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
    args.session = resolve_session(tree, args.session)
    agents = collect(tree, args.session, read_launches(launches_file))
    out = Path(args.out or f"{args.session}.trace.json")
    doc = render(agents)
    out.write_text(json.dumps(doc) + "\n", encoding="utf-8")
    if args.html:
        Path(args.html).write_text(render_html(doc, args.session, first_prompt(tree, args.session), default_author()), encoding="utf-8")
    log.info("%s: %d agents", out, len(agents))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Split each recorded /gaze run into setup, model turns, tool time, poll waits and seat times (ticket 1197).

    python3 scripts/gaze_wall_time.py [--projects DIR] [--json]

Reads Claude Code session traces: every `agent-*.forked-skill.json` naming
`gaze` is one run; its `.jsonl` gives the run's own records, and the sibling
`agent-*.meta.json` files whose `parentAgentId` chain reaches the run are its
seats. Every number is READ from timestamps or derived from them: the run
wall is last record less first record; a tool call lasts from its `tool_use`
record to its `tool_result` record; a poll is a Bash call whose command loops
or sleeps; model time is the wall less tool time (derived); a seat lasts from
its first to its last record. Nothing here measures token cost or CPU.
"""
import argparse
import json
import re
import statistics as st
import sys
from datetime import datetime
from pathlib import Path

DEFAULT = Path.home() / '.claude/projects/-home-haduong--agents'
POLL = re.compile(r'\bsleep\b|for \w+ in .*(seq|\{1\.\.|[0-9]+)|until |while ')


def ts(rec):
    return datetime.fromisoformat(rec['timestamp'].replace('Z', '+00:00')).timestamp()


def load(path):
    out = []
    for line in path.read_text(errors='replace').splitlines():
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if 'timestamp' in rec and rec.get('type') in ('assistant', 'user', 'attachment'):
            out.append(rec)
    return out


def blocks(rec):
    content = (rec.get('message') or {}).get('content')
    return content if isinstance(content, list) else []


def seat_kind(desc):
    d = desc.lower()
    if 'skills/verify-adh' in d:
        return 'adherence'
    if 'skills/review-pr' in d:
        return 'builtin-review'
    for key in ('simplify', 'semantic', 'adherence', 'correctness', 'doc-prop', 'fix', 'consistency', 'reviewer'):
        if key in d:
            return key
    return 'other'


def analyse(jsonl, meta_dir):
    recs = load(jsonl)
    if len(recs) < 3:
        return None
    t0, t1 = ts(recs[0]), max(ts(r) for r in recs)
    uses, tool_s, poll_s, polls, first_launch, calls, agent_s = {}, 0.0, 0.0, [], None, [], 0.0
    launches = []
    for r in recs:
        for b in blocks(r):
            if b.get('type') == 'tool_use':
                uses[b['id']] = (ts(r), b['name'], json.dumps(b.get('input', {})))
                if b['name'] == 'Agent':
                    launches.append((ts(r), b['input'].get('description', '')))
                    first_launch = first_launch or ts(r)
            elif b.get('type') == 'tool_result' and b.get('tool_use_id') in uses:
                u0, name, arg = uses.pop(b['tool_use_id'])
                d = ts(r) - u0
                if name == 'Agent' and d < 10:
                    continue  # background launch ack, not work
                if name == 'Agent':
                    agent_s += d  # a foreground child the run blocked on
                tool_s += d
                calls.append((u0, d, name, arg[:300]))
                if name == 'Bash' and POLL.search(arg):
                    poll_s += d
                    polls.append((u0, ts(r)))
    # assistant turns and tool seconds before the first launch (setup) and after the last record of any child (closing)
    gaps = sorted(((ts(b) - ts(a)), ts(a)) for a, b in zip(recs, recs[1:]) if ts(b) - ts(a) > 120)
    text = ' '.join(b.get('text', '') + json.dumps(b.get('input', {})) for r in recs if r['type'] == 'assistant' for b in blocks(r))
    found = re.findall(r'result: (REVIEWED|FINDINGS|ESCALATE)', text.replace('\\n', '\n'))
    mdl = next(((r['message'].get('model')) for r in recs if r['type'] == 'assistant'), None)
    return dict(wall=t1 - t0, start=t0, end=t1, setup=(first_launch - t0) if first_launch else None,
                tool=tool_s, agent_wait=agent_s, poll=poll_s, polls=polls, model_s=(t1 - t0) - tool_s,
                orch_model=mdl, launches=launches, calls=calls, result=found[-1] if found else None, idle_gaps=[g for g, _ in gaps], turns=sum(r['type'] == 'assistant' for r in recs))


def seats_of(agent_id, meta_dir):
    metas = {}
    for m in meta_dir.glob('agent-*.meta.json'):
        try:
            metas[m.name.removeprefix('agent-').removesuffix('.meta.json')] = json.loads(m.read_text())
        except ValueError:
            pass
    def descends(aid):
        seen = 0
        while aid in metas and seen < 6:
            aid = metas[aid].get('parentAgentId')
            if aid == agent_id:
                return True
            seen += 1
        return False
    out = []
    for aid, meta in metas.items():
        if aid != agent_id and descends(aid):
            p = meta_dir / f'agent-{aid}.jsonl'
            if not p.exists():
                continue
            recs = load(p)
            if len(recs) < 2:
                continue
            first = recs[0].get('message', {}).get('content', '')
            first = first if isinstance(first, str) else ' '.join(b.get('text', '') for b in first if isinstance(b, dict))
            desc = meta.get('description') or 'unnamed: ' + ' '.join(first.split())[:70]
            out.append(dict(kind=seat_kind(desc), desc=desc, shape=meta.get('requestShape'),
                            model=meta.get('model') or meta.get('agentType'), start=ts(recs[0]), end=max(ts(r) for r in recs),
                            tokens=sum(((r.get('message') or {}).get('usage') or {}).get('output_tokens', 0) for r in recs if r['type'] == 'assistant')))
    return out


def runs(root):
    for marker in root.glob('*/subagents/agent-*.forked-skill.json'):
        try:
            if json.loads(marker.read_text()).get('skillName') != 'gaze':
                continue
        except ValueError:
            continue
        aid = marker.name.removeprefix('agent-').removesuffix('.forked-skill.json')
        jl = marker.with_name(f'agent-{aid}.jsonl')
        if not jl.exists():
            continue
        a = analyse(jl, marker.parent)
        if a:
            a['seats'] = seats_of(aid, marker.parent)
            a['id'] = aid
            a['session'] = marker.parent.parent.name
            yield a


def pct(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(p * (len(xs) - 1))))] if xs else float('nan')


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--projects', type=Path, default=DEFAULT)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args(argv)
    rs = sorted(runs(args.projects), key=lambda r: r['start'])
    if args.json:
        json.dump(rs, sys.stdout)
        return 0
    walls = [r['wall'] for r in rs]
    print(f'runs {len(rs)}  wall s: median {st.median(walls):.0f} p90 {pct(walls, .9):.0f} max {max(walls):.0f} total {sum(walls) / 60:.0f} min')
    for k in ('setup', 'tool', 'poll', 'agent_wait', 'model_s'):
        xs = [r[k] for r in rs if r[k] is not None]
        print(f'{k:8s} median {st.median(xs):6.0f}s  sum {sum(xs) / 60:6.0f} min')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

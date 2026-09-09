#!/usr/bin/env python3
"""Aggregate the census into a usage report over a date window."""
import argparse
import json
from collections import Counter
from pathlib import Path

WIN_START = "2026-05-09"
WIN_END = "2026-09-09"


def in_win(d: str, lo: str, hi: str) -> bool:
    return lo <= d <= hi


def agg(series: dict, lo: str, hi: str) -> Counter:
    c = Counter()
    for name, days in series.items():
        c[name] = sum(v for d, v in days.items() if in_win(d, lo, hi))
    return c


def span(series: dict, name: str, lo: str, hi: str) -> tuple[str, str, int]:
    days = {d: v for d, v in series.get(name, {}).items() if in_win(d, lo, hi)}
    if not days:
        return ("", "", 0)
    ks = sorted(days)
    return (ks[0], ks[-1], len(ks))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", required=True)
    ap.add_argument("--gitmeta", required=True)
    ap.add_argument("--start", default=WIN_START)
    ap.add_argument("--end", default=WIN_END)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    C = json.load(open(a.census))
    G = json.load(open(a.gitmeta))
    lo, hi = a.start, a.end

    inv = C["meta"]["inventory"]
    days = C["days"]
    win_days = sorted(d for d in days if in_win(d, lo, hi))
    all_days = sorted(d for d in days if d != "unknown")

    out: dict = {
        "window": [lo, hi],
        "coverage": {
            "log_files": C["meta"]["files"],
            "log_bytes": C["meta"]["bytes"],
            "first_day": all_days[0] if all_days else None,
            "last_day": all_days[-1] if all_days else None,
            "active_days_in_window": len(win_days),
            "records_in_window": sum(days[d] for d in win_days),
            "sessions_in_window": sum(v for d, v in C["sessions_by_day"].items() if in_win(d, lo, hi)),
        },
    }

    skill_tool = agg(C["skill_tool"], lo, hi)
    slash = agg(C["slash"], lo, hi)
    skill_read = agg(C["skill_read"], lo, hi)
    scripts = agg(C["script_use"], lo, hi)
    ruleinj = agg(C["rule_injection"], lo, hi)
    ruleread = agg(C["rule_read"], lo, hi)
    agents = agg(C["agent"], lo, hi)
    tools = agg(C["tool_mix"], lo, hi)
    guards = agg(C["guard_fire"], lo, hi)

    rows = []
    for s in inv["skills"]:
        gm = G.get("skill", {}).get(s, {})
        first, last, nd = span(C["skill_tool"], s, lo, hi)
        f2, l2, nd2 = span(C["slash"], s, lo, hi)
        rows.append(
            {
                "skill": s,
                "tool_calls": skill_tool.get(s, 0),
                "slash": slash.get(s, 0),
                "total": skill_tool.get(s, 0) + slash.get(s, 0),
                "file_reads": skill_read.get(s, 0),
                "days_used": len({first, last, f2, l2} - {""}),
                "distinct_days": max(nd, nd2),
                "first_use": min([x for x in (first, f2) if x], default=""),
                "last_use": max([x for x in (last, l2) if x], default=""),
                "projects": len(C["skill_by_project"].get(s, {})),
                "created": gm.get("first"),
                "last_edit": gm.get("last"),
                "commits": gm.get("commits", 0),
            }
        )
    rows.sort(key=lambda r: -r["total"])
    out["skills"] = rows

    srows = []
    for s in inv["scripts"]:
        gm = G.get("script", {}).get(s, {})
        first, last, nd = span(C["script_use"], s, lo, hi)
        srows.append(
            {
                "script": s,
                "bash_calls": scripts.get(s, 0),
                "distinct_days": nd,
                "first_use": first,
                "last_use": last,
                "projects": len(C["script_by_project"].get(s, {})),
                "guard_fires": guards.get(s, 0),
                "created": gm.get("first"),
                "last_edit": gm.get("last"),
                "commits": gm.get("commits", 0),
            }
        )
    srows.sort(key=lambda r: -r["bash_calls"])
    out["scripts"] = srows

    rrows = []
    for r in inv["rules"]:
        gm = G.get("rule", {}).get(r, {})
        base = r.split("/")[-1]
        keys = [f"rules/{base}", r, f"{Path(r).parent.name}/{base}" if "/" in r else base]
        inj = sum(ruleinj.get(k, 0) for k in set(keys))
        rd = ruleread.get(r, 0) + (ruleread.get(base, 0) if "/" not in r else 0)
        rrows.append(
            {
                "rule": r,
                "injections": inj,
                "explicit_reads": rd,
                "created": gm.get("first"),
                "last_edit": gm.get("last"),
                "commits": gm.get("commits", 0),
            }
        )
    rrows.sort(key=lambda r: -(r["injections"] + r["explicit_reads"]))
    out["rules"] = rrows

    out["agents"] = agents.most_common()
    out["tool_mix"] = tools.most_common(40)
    out["guards"] = guards.most_common()
    out["slash_all"] = slash.most_common(60)
    out["monthly_records"] = dict(
        sorted(Counter({d[:7]: 0 for d in all_days}).items())
    )
    m = Counter()
    for d in all_days:
        m[d[:7]] += days[d]
    out["monthly_records"] = dict(sorted(m.items()))
    ms = Counter()
    for d, v in C["sessions_by_day"].items():
        if d != "unknown":
            ms[d[:7]] += v
    out["monthly_sessions"] = dict(sorted(ms.items()))

    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", a.out)


main()

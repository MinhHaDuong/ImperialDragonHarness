import json, sys, statistics as st, collections, re
CUT = "2026-10-12T13:58"
rows, seen = [], set()
for p in sys.argv[1:]:
    for l in open(p):
        r = json.loads(l)
        k = (r["host"], r["start"], r["calls"][0][1])
        if k in seen:
            continue
        seen.add(k)
        c = r["calls"]
        r["n"] = len(c)
        r["ctx0"] = sum(c[0][:3])
        r["eq"] = sum(0.1 * x[1] + 1.25 * x[2] + x[0] for x in c)
        r["after"] = r["start"] >= CUT
        r["cc"] = any("close-and-clean" in t for t in r["tools"])
        rows.append(r)


def cat(t):
    s = t.lower()
    if "close-and-clean" in s: return "close-and-clean.sh"
    if t.startswith("Skill"): return "skill load"
    if re.search(r"memory/|journal|state\.md", s) or (t.startswith(("Write", "Edit")) and re.search(r"\.md$", s)): return "memory/journal/STATE"
    if re.search(r"erg |tickets/", s): return "tickets"
    if re.search(r"gh pr|gh api|gh run|gh issue", s): return "forge (gh)"
    if re.search(r"git (add|commit|push)", s): return "commit/push"
    if re.search(r"git (fetch|log|status|diff|show|rev-|branch|worktree|merge-base|ls-)", s): return "git read"
    if re.search(r"exitworktree|enterworktree", s): return "worktree tool"
    if t.startswith(("Read", "Grep", "Glob")) or re.search(r"^bash: (cat|sed -n|head|tail|ls|rg|grep|find)", s): return "read/search"
    if t.startswith("Agent"): return "subagent"
    return "other"


def summary(label, rs):
    if not rs:
        print(label, "none"); return
    med = lambda k: st.median(r[k] for r in rs)
    print(f"{label}: n={len(rs)} turns={med('n')} ctx0={med('ctx0')/1e3:.0f}k eq={med('eq')/1e3:.0f}k "
          f"pre_calls={med('pre_calls')} compacted={sum(r['compacted']>0 for r in rs)} "
          f">256k={sum(r['ctx0']>256e3 for r in rs)} cc_used={sum(r['cc'] for r in rs)} "
          f"tools/turn={sum(len(r['tools']) for r in rs)/sum(r['n'] for r in rs):.2f}")


solo = [r for r in rows if not r["bundled"]]
for sel, name in ((rows, "ALL"), (solo, "SOLO")):
    print("==", name)
    summary(" before", [r for r in sel if not r["after"]])
    summary(" after ", [r for r in sel if r["after"]])
    summary(" after, cc used", [r for r in sel if r["after"] and r["cc"]])
    summary(" after, cc not used", [r for r in sel if r["after"] and not r["cc"]])

print("== tool calls per roar by category (solo roars, mean)")
for when in (False, True):
    rs = [r for r in solo if r["after"] == when]
    cnt = collections.Counter(cat(t) for r in rs for t in r["tools"])
    print(" after" if when else " before", f"(n={len(rs)})", {k: round(v / len(rs), 1) for k, v in cnt.most_common()})

print("== by week (solo): n, median turns, median ctx0, median pre_calls")
wk = collections.defaultdict(list)
for r in solo:
    wk[r["start"][:8] + ("1" if r["start"][8:10] < "08" else "2" if r["start"][8:10] < "15" else "3" if r["start"][8:10] < "22" else "4")].append(r)
for k in sorted(wk):
    rs = wk[k]
    print(" ", k, len(rs), st.median(r["n"] for r in rs), f"{st.median(r['ctx0'] for r in rs)/1e3:.0f}k", st.median(r["pre_calls"] for r in rs))

print("== after-roar 'other' tool samples")
oth = collections.Counter(t[:70] for r in solo if r["after"] for t in r["tools"] if cat(t) == "other")
for t, c in oth.most_common(15):
    print(" ", c, t)

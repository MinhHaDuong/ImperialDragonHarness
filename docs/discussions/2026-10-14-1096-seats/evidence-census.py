import os
import re
import sys
import json
import collections

root = sys.argv[1]
out = {}
skills = ["gaze", "review-pr", "review-pr-prose", "verify-gate", "hunt", "raid"]
pat_skill = re.compile(rb'"name":"Skill","input":\{[^{}]*?"skill":"([a-zA-Z0-9:_-]+)"')
pat_cmd = re.compile(rb"<command-name>/?([a-zA-Z0-9:_-]+)</command-name>")
# review heads: "Anchor HEAD <sha>" / "review-pr ... head <sha>" in review output
pat_head = re.compile(
    rb"(?:Anchor HEAD|anchor HEAD|Anchor:? HEAD|HEAD)[ `:=]+([0-9a-f]{8,40})"
)
pat_rp = re.compile(rb'/review-pr[^\\"]{0,80}?(?:head|HEAD)[ `:(]+([0-9a-f]{8,40})')
tot = 0
sess = collections.defaultdict(lambda: collections.defaultdict(int))
dups = []
sessions_with_rp = {}
for dp, dn, fn in os.walk(root):
    for f in fn:
        if not f.endswith(".jsonl"):
            continue
        p = os.path.join(dp, f)
        tot += 1
        try:
            b = open(p, "rb").read()
        except Exception:
            continue
        if b"gaze" not in b and b"review-pr" not in b:
            continue
        c = collections.Counter()
        for m in pat_skill.finditer(b):
            s = m.group(1).decode()
            if s in skills:
                c["skill:" + s] += 1
        for m in pat_cmd.finditer(b):
            s = m.group(1).decode()
            if s in skills:
                c["cmd:" + s] += 1
        if c:
            sess[p] = c
        heads = collections.Counter()
        for m in pat_rp.finditer(b):
            heads[m.group(1).decode()[:8]] += 1
        if heads:
            sessions_with_rp[p] = heads
res = collections.Counter()
for p, c in sess.items():
    for k in c:
        res["sessions:" + k] += 1
        res["calls:" + k] += c[k]
print("files", tot, "files with gaze/review-pr text", len(sess))
for k in sorted(res):
    print(k, res[k])
rp_sess = [p for p, c in sess.items() if any(k.endswith(":review-pr") for k in c)]
print("sessions invoking review-pr (skill or cmd):", len(rp_sess))
multi = [
    (p, c)
    for p, c in sess.items()
    if sum(v for k, v in c.items() if k.endswith(":review-pr")) >= 2
]
print("sessions with >=2 review-pr invocations:", len(multi))
json.dump({p: dict(c) for p, c in sess.items()}, open(sys.argv[2], "w"))
json.dump(
    {p: dict(h) for p, h in sessions_with_rp.items()}, open(sys.argv[2] + ".heads", "w")
)
print("files with /review-pr ... head sha pattern:", len(sessions_with_rp))

import os
import re
import sys
import json
import collections

root = os.path.expanduser(sys.argv[1])
SK = ["gaze", "review-pr", "review-pr-prose", "verify-gate", "hunt", "raid"]
pskill = re.compile(
    rb'"name":"Skill","input":\{[^{}]*?"skill":"([a-zA-Z0-9:_-]+)"[^{}]*\}[^{}]*?"id":"([^"]+)"|"id":"([^"]+)"[^{}]*?"name":"Skill","input":\{[^{}]*?"skill":"([a-zA-Z0-9:_-]+)"'
)
pskill2 = re.compile(
    rb'"type":"tool_use","id":"([^"]+)","name":"Skill","input":\{[^{}]*?"skill":"([a-zA-Z0-9:_-]+)"'
)
panc = re.compile(rb"REVIEW-ANCHOR: PR #(\d+) HEAD ([0-9a-f]{40})")
ids = collections.defaultdict(set)
sess = collections.defaultdict(set)
by = collections.defaultdict(set)
nf = 0
for dp, dn, fn in os.walk(root):
    for f in fn:
        if not f.endswith(".jsonl"):
            continue
        p = os.path.join(dp, f)
        nf += 1
        rel = os.path.relpath(p, root).split(os.sep)
        proj = rel[0]
        s = rel[1][:-6] if len(rel) == 2 else rel[1]
        try:
            b = open(p, "rb").read()
        except OSError:
            continue
        if b"Skill" in b:
            for m in pskill2.finditer(b):
                k = m.group(2).decode()
                if k in SK:
                    ids[k].add(m.group(1).decode())
                    sess[k].add(s)
        if b"REVIEW-ANCHOR: PR" in b:
            for line in b.split(b"\n"):
                if b"REVIEW-ANCHOR: PR" in line and (
                    b'"tool_result"' in line or b'"toolUseResult"' in line
                ):
                    for m in panc.finditer(line):
                        by[(proj, m.group(1).decode(), m.group(2)[:8].decode())].add(s)
print("files", nf)
for k in SK:
    print(k, "calls", len(ids[k]), "sessions", len(sess[k]))
print(
    "anchored triples",
    len(by),
    "heads in >=2 sessions",
    sum(1 for v in by.values() if len(v) >= 2),
)
print(
    "PRs",
    len({(a, b) for a, b, c in by}),
    "PRs>=2 heads",
    sum(
        1
        for pr in {(a, b) for a, b, c in by}
        if len([1 for (x, y, z) in by if (x, y) == pr]) >= 2
    ),
)
for k, v in by.items():
    if len(v) >= 2:
        print("REPEAT", k, len(v))
print("TRIPLES", json.dumps(sorted(["%s|%s|%s" % k for k in by])))

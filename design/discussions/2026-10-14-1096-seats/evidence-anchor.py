import os
import re
import sys
import collections

root = sys.argv[1]
pat = re.compile(rb"REVIEW-ANCHOR: PR #(\d+) HEAD ([0-9a-f]{40})")
by = collections.defaultdict(
    lambda: collections.defaultdict(int)
)  # (proj,pr,sha) -> sessionkey -> count lines
nfiles = 0
for dp, dn, fn in os.walk(root):
    for f in fn:
        if not f.endswith(".jsonl"):
            continue
        p = os.path.join(dp, f)
        rel = os.path.relpath(p, root).split(os.sep)
        proj = rel[0]
        sess = rel[1][:-6] if len(rel) == 2 else rel[1]
        try:
            b = open(p, "rb").read()
        except OSError:
            continue
        if b"REVIEW-ANCHOR: PR" not in b:
            continue
        nfiles += 1
        seen = set()
        for line in b.split(b"\n"):
            if b"REVIEW-ANCHOR: PR" not in line:
                continue
            if b'"tool_result"' not in line and b'"toolUseResult"' not in line:
                continue
            for m in pat.finditer(line):
                k = (proj, m.group(1).decode(), m.group(2)[:8].decode())
                by[k][sess + ("/" + f if len(rel) > 2 else "")] += 1
print("files with anchors", nfiles, "distinct (proj,pr,sha)", len(by))
multi_sess = {k: v for k, v in by.items() if len({s.split("/")[0] for s in v}) >= 2}
multi_file = {k: v for k, v in by.items() if len(v) >= 2}
print("heads anchored in >=2 distinct sessions:", len(multi_sess))
print(
    "heads anchored in >=2 distinct transcript files (incl subagents):", len(multi_file)
)
print("heads anchored once-only file:", sum(1 for v in by.values() if len(v) == 1))
for k, v in sorted(multi_sess.items(), key=lambda kv: -len(kv[1]))[:20]:
    print(k[0][-30:], "PR", k[1], k[2], "sessions", len({s.split("/")[0] for s in v}))
# per PR: number of distinct heads
prs = collections.defaultdict(set)
for proj, pr, sha in by:
    prs[(proj, pr)].add(sha)
print(
    "PRs anchored:",
    len(prs),
    "PRs with >=2 heads:",
    sum(1 for v in prs.values() if len(v) >= 2),
)

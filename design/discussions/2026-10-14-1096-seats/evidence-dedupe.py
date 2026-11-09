import os
import re
import json

B = "/tmp/claude-1000/-home-haduong--agents/b7494e29-3e1a-4f0c-9a2f-faa62ae5e36b/scratchpad/1096/evidence/"
d = set()
for line in open(B + "doudou-claude.txt"):
    if line.startswith("TRIPLES"):
        d = {tuple(x.split("|")) for x in json.loads(line[8:])}
pat = re.compile(rb"REVIEW-ANCHOR: PR #(\d+) HEAD ([0-9a-f]{40})")
pm = set()
for dp, _, fn in os.walk("/home/haduong/.claude/projects"):
    for f in fn:
        if f.endswith(".jsonl"):
            try:
                b = open(os.path.join(dp, f), "rb").read()
            except OSError:
                continue
            if b"REVIEW-ANCHOR: PR" in b:
                for m in pat.finditer(b):
                    pm.add((m.group(1).decode(), m.group(2)[:8].decode()))
dd = {(a, b) for _, a, b in d}
print(
    "doudou PR/head pairs",
    len(dd),
    "padme",
    len(pm),
    "overlap",
    len(dd & pm),
    "doudou-only",
    len(dd - pm),
    "union",
    len(dd | pm),
)

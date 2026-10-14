import json
import subprocess
import re
import sys
import datetime

repo = sys.argv[1]
lo = int(sys.argv[2])
hi = int(sys.argv[3])


def ts(s):
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))


rows = []
for n in range(lo, hi + 1):
    r = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            str(n),
            "--repo",
            repo,
            "--json",
            "state,createdAt,mergedAt,headRefOid,reviews,comments,title",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode:
        continue
    d = json.loads(r.stdout)
    if d["state"] != "MERGED":
        continue
    items = []
    for c in d["comments"]:
        b = c["body"]
        m = re.search(
            r"(?:head|HEAD|Anchor HEAD|anchor)[ `:=(]+([0-9a-f]{8})", b[:1500]
        )
        kind = None
        if (
            re.match(r"\s*#+ .*review-pr|\s*#+ Agent C|\s*#+ .*panel", b[:200], re.I)
            or "/review-pr" in b[:200]
        ):
            kind = "review-pr"
        if "/gaze actions" in b[:200]:
            kind = "gaze"
        if "/verify-gate" in b[:200]:
            kind = "gate"
        if kind:
            items.append((c["createdAt"], kind, m.group(1) if m else "?"))
    for rv in d["reviews"]:
        items.append(
            (
                rv["submittedAt"],
                "review-obj",
                (rv.get("commit") or {}).get("oid", "")[:8],
            )
        )
    items.sort()
    rows.append((n, d["title"][:50], d["createdAt"], d["mergedAt"], items))
for n, t, c, m, items in rows:
    rp = [i for i in items if i[1] in ("review-pr", "review-obj")]
    heads = [i[2] for i in rp]
    dup = len(heads) - len(set(h for h in heads if h != "?")) if heads else 0
    first = items[0][0] if items else None
    mins = round((ts(m) - ts(first)).total_seconds() / 60, 1) if first else None
    print(
        n,
        "rp_posts",
        len(rp),
        "heads",
        heads,
        "gaze",
        sum(1 for i in items if i[1] == "gaze"),
        "gate",
        sum(1 for i in items if i[1] == "gate"),
        "first->merge_min",
        mins,
        "|",
        t,
    )

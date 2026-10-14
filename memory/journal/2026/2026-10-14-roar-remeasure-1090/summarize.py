import statistics as st
import sys

rows, seen = [], set()
for path in sys.argv[1:]:
    for line in open(path):
        h, rt, ts, n, ctx0, cr, cw, unc, comb, proj = line.rstrip("\n").split("\t")
        key = (h, rt, ts, ctx0)  # same roar logged in two project folders
        if key in seen:
            continue
        seen.add(key)
        n, ctx0, cr, cw, unc = map(int, (n, ctx0, cr, cw, unc))
        eq = 0.1 * cr + 1.25 * cw + unc
        rows.append(
            dict(h=h, rt=rt, ts=ts, n=n, ctx0=ctx0, eq=eq, comb=comb == "1", proj=proj)
        )


def show(label, rs):
    if not rs:
        return
    print(
        f"{label}: n={len(rs)} median turns={st.median(r['n'] for r in rs)} "
        f"median start ctx={st.median(r['ctx0'] for r in rs) / 1e3:.0f}k "
        f"median eq={st.median(r['eq'] for r in rs) / 1e3:.0f}k "
        f"start>256k={sum(r['ctx0'] > 256000 for r in rs)}"
    )


show("all", rows)
show("roar-only prompts", [r for r in rows if not r["comb"]])
show("roar-only, claude", [r for r in rows if not r["comb"] and r["rt"] == "claude"])
show("bundled prompts", [r for r in rows if r["comb"]])
for r in sorted(rows, key=lambda r: r["ts"]):
    print(
        r["h"],
        r["rt"],
        r["ts"],
        r["n"],
        f"{r['ctx0'] / 1e3:.0f}k",
        f"{r['eq'] / 1e3:.0f}k",
        "bundled" if r["comb"] else "",
        r["proj"][-40:],
        sep="\t",
    )

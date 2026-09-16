---
name: pathlib-with-suffix-dotted-stems
description: Path.with_suffix on a stem containing dots strips up to the LAST dot — drops part of the filename. Bites when constructing one path-with-suffix from another path-with-suffix.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: de20a516-38a3-4ccc-b4a4-236f555d39aa
---

`Path("foo.bar-baz").with_suffix(".x")` returns `Path("foo.x")` — Pathlib
treats `.bar-baz` as the existing suffix and replaces it. The bite happens
when chaining: `csv_path.with_suffix("").with_suffix(".record.json")`
silently drops the `.5-run1` middle of `claude-haiku-4.5-run1`.

**Why:** Hit while writing the ticket 0198 canary gate script. The
chained-with_suffix pattern destroyed 15 of 16 expected `.record.json`
lookups silently — the gate script reported "NO_F1" for everyone except
the only model in the panel with no dots in its slug.

**How to apply:** When constructing one filename from another and the
input *may* have dots in its stem, use explicit string slicing:
`p.parent / (p.name[:-len(".json")] + ".record.json")`. Reserve
`with_suffix` for the simple case where you have a clean suffixed file
(`*.csv` → `*.json`) and the previous suffix is what you want to replace.

The codebase has 5 other `with_suffix` callsites; all are SAFE — they
operate on `*.csv` / `*.pdf` paths where the LAST dot is the real
suffix. The bite only happens on stem-only inputs.

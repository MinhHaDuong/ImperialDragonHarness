#!/usr/bin/env python3
"""Second pass: separate EXECUTION of a harness script from mere INSPECTION.

`cat scripts/guard-x.sh` and `bash scripts/guard-x.sh` both mention the script;
only the second is usage. The classifier splits each Bash command on shell
separators and looks at the executable position of each segment, which is linear
in the command length -- a lookbehind-style regex over 150k commands is not.
"""
import argparse
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path.home() / ".claude"
SCRIPTS = {p.name for p in (ROOT / "scripts").iterdir() if p.is_file()}
STEMS = {s.rsplit(".", 1)[0]: s for s in SCRIPTS if s.endswith(".py")}

TS = re.compile(rb'"timestamp":"(\d{4}-\d\d-\d\d)T')
RE_BASH = re.compile(rb'"name":\s*"Bash"\s*,\s*"input":\s*\{\s*"command":\s*"((?:[^"\\]|\\.){0,6000})"')
SEP = re.compile(r"[;|&\n]+|&&|\|\||\$\(|`")
INTERP = {"bash", "sh", "zsh", "python", "python3", "uv", "source", ".", "exec", "time", "nohup", "env"}
EXTERNALS = {
    "erg": re.compile(r"(?:^|[;|&(]\s*|&&\s*)(?:\S*/)?erg\s+([a-z-]+)"),
    "rtk": re.compile(r"(?:^|[;|&(]\s*|&&\s*)rtk\s+([a-z-]+)"),
    "gh": re.compile(r"(?:^|[;|&(]\s*|&&\s*)gh\s+([a-z-]+)"),
    "make": re.compile(r"(?:^|[;|&(]\s*|&&\s*)make\s+([a-z-]*)"),
}


def basename(tok: str) -> str:
    return tok.rsplit("/", 1)[-1]


def classify(cmd: str, execd: dict, inspect: dict, day: str, proj: str, exec_proj: dict) -> None:
    for seg in SEP.split(cmd):
        toks = seg.split()
        if not toks:
            continue
        head = 0
        # skip env assignments and interpreters to reach the real executable
        while head < len(toks) and ("=" in toks[head] and "/" not in toks[head].split("=")[0]):
            head += 1
        run = None
        while head < len(toks):
            b = basename(toks[head])
            if b in INTERP or b.startswith("-"):
                head += 1
                continue
            run = b
            break
        if run in SCRIPTS:
            execd[run][day] += 1
            exec_proj[run].add(proj)
        elif run in STEMS:
            execd[STEMS[run]][day] += 1
            exec_proj[STEMS[run]].add(proj)
        for t in toks:
            b = basename(t)
            if b in SCRIPTS and b != run:
                inspect[b][day] += 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", default=str(ROOT / "projects"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    execd = defaultdict(Counter)
    inspect = defaultdict(Counter)
    exec_proj = defaultdict(set)
    ext = defaultdict(Counter)

    for dirpath, _d, fnames in os.walk(a.projects):
        proj = Path(dirpath).name
        for fn in fnames:
            if not fn.endswith(".jsonl"):
                continue
            cur = "unknown"
            try:
                fh = open(os.path.join(dirpath, fn), "rb")
            except OSError:
                continue
            with fh:
                for line in fh:
                    m = TS.search(line)
                    if m:
                        cur = m.group(1).decode()
                    if b'"Bash"' not in line:
                        continue
                    for bm in RE_BASH.finditer(line):
                        cmd = bm.group(1).decode("unicode_escape", "replace")
                        classify(cmd, execd, inspect, cur, proj, exec_proj)
                        for tool, rx in EXTERNALS.items():
                            for em in rx.finditer(cmd):
                                ext[tool][em.group(1) or "(default)"] += 1

    out = {
        "exec": {k: dict(v) for k, v in execd.items()},
        "inspect": {k: dict(v) for k, v in inspect.items()},
        "exec_projects": {k: sorted(v) for k, v in exec_proj.items()},
        "externals": {k: dict(v.most_common(25)) for k, v in ext.items()},
    }
    with open(a.out, "w") as fh:
        json.dump(out, fh)
    print("ok")


main()

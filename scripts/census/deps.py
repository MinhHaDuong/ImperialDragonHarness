#!/usr/bin/env python3
"""Static dependency graph: which skill/script/rule is referenced from where.

A skill with zero observed invocations may still be load-bearing because another
skill calls it. Deleting on the usage count alone would break the caller.

Corpus deliberately includes tests/, .github/, docs/, tickets/ and the settings
files: a script wired only into CI or only into the night-run settings has no
reference in skills/ and would read as an orphan otherwise. Python scripts are
matched on the module stem too, since an import drops the .py.
"""
import argparse
import json
import re
from pathlib import Path

TEXT_SUFFIX = {".md", ".py", ".sh", ".json", ".txt", ".yml", ".yaml", ".erg", ".toml", ""}


def load_corpus(R: Path) -> dict[str, str]:
    corpus: dict[str, str] = {}
    for s in sorted(p.name for p in (R / "skills").iterdir() if (p / "SKILL.md").exists()):
        corpus[f"skill:{s}"] = "\n".join(
            p.read_text(errors="replace")
            for p in (R / "skills" / s).rglob("*")
            if p.is_file() and p.suffix in TEXT_SUFFIX
        )
    for sub in ("tests", ".github", "docs", "tickets", "commands", "agents"):
        d = R / sub
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.is_file() and p.suffix in TEXT_SUFFIX:
                try:
                    corpus[f"{sub}:{p.relative_to(d)}"] = p.read_text(errors="replace")
                except (UnicodeDecodeError, OSError):
                    pass
    for f in ("CLAUDE.md", "README.md", "Makefile", "settings.json", "STATE.md", "RTK.md"):
        p = R / f
        if p.exists():
            corpus[f"root:{f}"] = p.read_text(errors="replace")
    for p in sorted((R / "scripts").rglob("*")):
        if p.is_file():
            try:
                corpus[f"script:{p.relative_to(R / 'scripts')}"] = p.read_text(errors="replace")
            except (UnicodeDecodeError, OSError):
                corpus[f"script:{p.relative_to(R / 'scripts')}"] = ""
    for p in sorted((R / "rules").rglob("*.md")):
        corpus[f"rule:{p.relative_to(R / 'rules')}"] = p.read_text(errors="replace")
    return corpus


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path.home() / ".claude"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = Path(a.root)
    corpus = load_corpus(R)

    skills = sorted(p.name for p in (R / "skills").iterdir() if (p / "SKILL.md").exists())
    scripts = sorted(p.name for p in (R / "scripts").iterdir() if p.is_file())
    rules = sorted(str(p.relative_to(R / "rules")) for p in (R / "rules").rglob("*.md"))

    def refs(self_key: str, pats: list[str]) -> list[str]:
        rx = re.compile("|".join(pats))
        return sorted(k for k, txt in corpus.items() if k != self_key and rx.search(txt))

    graph = {"skill_callers": {}, "script_callers": {}, "rule_callers": {}}
    for s in skills:
        graph["skill_callers"][s] = refs(
            f"skill:{s}", [rf"/{re.escape(s)}\b", rf'skill["\':\s]+{re.escape(s)}\b', rf"skills/{re.escape(s)}/"]
        )
    for s in scripts:
        pats = [re.escape(s)]
        if s.endswith(".py"):
            pats.append(rf"\b{re.escape(s[:-3])}\b")
        graph["script_callers"][s] = refs(f"script:{s}", pats)
    for r in rules:
        base = r.split("/")[-1]
        graph["rule_callers"][r] = refs(f"rule:{r}", [re.escape(r), re.escape(base)])

    with open(a.out, "w") as fh:
        json.dump(graph, fh, indent=1)
    print("ok", len(corpus), "documents")


main()

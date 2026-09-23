#!/usr/bin/env python3
"""Check literal skill classifier names in scripts against live skill directories.

Historical trace names use ``# historical-skill: old -> current`` in the same
script. The destination must still be a live skill. This keeps intentional
pre-rename corpus labels without hiding future dangling names.
"""

import ast
import re
from pathlib import Path


HISTORICAL = re.compile(r"^\s*# historical-skill: ([a-z][a-z0-9-]*) -> ([a-z][a-z0-9-]*)\s*$", re.M)
SKILL_PATH = re.compile(r"skills/([a-z][a-z0-9-]*)/[A-Za-z0-9_.-]+")
CLASSIFIER_GROUP = re.compile(r"\(([a-z][a-z0-9-]*(?:\|[a-z][a-z0-9-]*)*)\)")


def _names_in_python(source: str) -> set[str]:
    names = set(SKILL_PATH.findall(source))
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        value = node.value
        if value is None:
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id.endswith("_SKILLS") and isinstance(value, (ast.Set, ast.List, ast.Tuple)):
                names.update(
                    elt.value for elt in value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                )
            if target.id in {"SKILL", "CMD"} and isinstance(value, ast.Call) and value.args:
                pattern = value.args[0]
                if isinstance(pattern, ast.Constant) and isinstance(pattern.value, (bytes, str)):
                    raw = pattern.value.decode() if isinstance(pattern.value, bytes) else pattern.value
                    for group in CLASSIFIER_GROUP.findall(raw):
                        names.update(group.split("|"))
    return names


def check_script(path: Path, skills_dir: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    aliases = dict(HISTORICAL.findall(source))
    if path.suffix == ".py":
        names = _names_in_python(source)
    else:
        names = set(SKILL_PATH.findall(source))
    return sorted(
        name for name in names
        if not (skills_dir / name / "SKILL.md").is_file()
        and not (name in aliases and (skills_dir / aliases[name] / "SKILL.md").is_file())
    )


def check_tree(root: Path) -> dict[str, list[str]]:
    failures = {}
    for path in sorted((root / "scripts").rglob("*")):
        if path.suffix not in {".py", ".sh"}:
            continue
        dangling = check_script(path, root / "skills")
        if dangling:
            failures[str(path.relative_to(root))] = dangling
    return failures


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    failures = check_tree(root)
    for path, names in failures.items():
        print(f"{path}: dangling skill names: {', '.join(names)}")
    raise SystemExit(bool(failures))

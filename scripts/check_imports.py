#!/usr/bin/env python3
"""On-demand direct-import diagnostic; never imports the inspected code.

Explicit files only, including extensionless Python. JSON is evidence for the
harness doctor, not a compliance verdict. Findings and unavailable inputs both
exit zero; argparse usage errors retain their normal nonzero exit.
"""

import argparse
import ast
import json
import logging
from pathlib import Path
import sys

log = logging.getLogger("check_imports")
LIMITS = [
    "Direct Python AST imports only; transitive dependencies are unexamined.",
    "Runtime availability, package versions, system tools, and services are unavailable from this inspection.",
    "Dynamic imports (including aliases and custom loaders) are not resolved; reported call sites are examples only.",
    "Local paths are candidates, not verification of Python's runtime search path or module contents.",
]
POLICIES = {
    "bundled-helper": "authoring-skills.md: bundled helpers default to stdlib; optional specialized exceptions need a working stdlib or manual route",
    "harness-tool": "coding-python.md: harness tools use declared locked dependencies",
    "unclassified": "perimeter unavailable: doctor must establish the applicable policy before judging imports",
}


def perimeter(path: Path, root: Path) -> str:
    try:
        first = path.relative_to(root).parts[0]
    except (ValueError, IndexError):
        return "unclassified"
    return {"skills": "bundled-helper", "scripts": "harness-tool"}.get(first, "unclassified")


def local_module(name: str, path: Path, roots) -> Path | None:
    """Match concrete sibling/search-root paths, excluding the inspected file."""
    for root in roots:
        for candidate in (root / f"{name}.py", root / name):
            if candidate.resolve() == path:
                continue
            if (candidate.is_file() and candidate.suffix == ".py") or candidate.is_dir():
                return candidate
    return None


def inspect_files(paths, root, local_roots=()):
    root = Path(root).resolve()
    explicit_roots = [Path(p).resolve() for p in local_roots]
    result = {"prerequisites": "Python 3.10+; readable named Python sources; no inspected imports are executed",
              "limits": list(LIMITS), "files": []}
    for raw in paths:
        path = Path(raw).resolve()
        area = perimeter(path, root)
        item = {"file": str(path), "perimeter": area, "policy": POLICIES[area]}
        result["files"].append(item)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            item.update(status="unavailable", reason=f"{type(exc).__name__}: {exc}")
            continue
        item.update(status="inspected", imports=[], dynamic_import_lines=[], limits=list(LIMITS))
        roots = [path.parent, *explicit_roots]
        for node in sorted(ast.walk(tree), key=lambda n: (getattr(n, "lineno", 0), getattr(n, "col_offset", 0))):
            if isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = ["." * node.level + (node.module or "")]
            else:
                if isinstance(node, ast.Call):
                    func = node.func
                    if (isinstance(func, ast.Name) and func.id == "__import__" or
                            isinstance(func, ast.Attribute) and func.attr == "import_module"):
                        item["dynamic_import_lines"].append(node.lineno)
                continue
            for module in modules:
                top = module.split(".")[0]
                local = local_module(top, path, roots) if top else None
                if module.startswith("."):
                    kind, evidence = "local", "relative import syntax; target not resolved"
                elif local:
                    kind, evidence = "local", str(local)
                elif top in sys.stdlib_module_names:
                    kind, evidence = "stdlib", "sys.stdlib_module_names of the inspecting interpreter"
                else:
                    kind, evidence = "third-party-candidate", "not stdlib or found under the stated local search roots; installation unexamined"
                item["imports"].append(dict(module=module, line=node.lineno, kind=kind, evidence=evidence))
        item["local_search_roots"] = [str(p) for p in roots]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", type=Path, nargs="+", help="Explicit Python files to inspect; no recursive sweep")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Harness checkout for policy perimeter classification")
    parser.add_argument("--local-root", type=Path, action="append", default=[], help="Additional known Python search root (repeatable)")
    args = parser.parse_args(argv)
    report = inspect_files(args.paths, args.root, args.local_root)
    sys.stdout.write(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(main())

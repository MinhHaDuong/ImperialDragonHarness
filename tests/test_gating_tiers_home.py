"""Gating tiers have one home, /merge § Gating tiers (ticket 1221).

No other skill or rule restates the tiers, and the prose names the same
bookkeeping paths as the script that reads them.
"""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = "## Gating tiers"


def _bookkeeping():
    tree = ast.parse((ROOT / "scripts" / "merge-gate.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "BOOKKEEPING" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("BOOKKEEPING not found in scripts/merge-gate.py")


def test_tiers_are_stated_once():
    homes = [p for p in (*ROOT.glob("skills/**/*.md"), *ROOT.glob("rules/**/*.md")) if HOME in p.read_text()]
    assert homes == [ROOT / "skills" / "merge" / "SKILL.md"], homes


def test_the_home_names_the_scripts_bookkeeping_paths():
    home = (ROOT / "skills" / "merge" / "SKILL.md").read_text()
    for pattern in _bookkeeping():
        assert f"`{pattern}`" in home, pattern

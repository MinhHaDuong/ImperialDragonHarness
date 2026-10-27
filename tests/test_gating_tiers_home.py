"""Gating tiers have one home, rules/git.md § Gating tiers.

No skill restates the tiers. The bookkeeping path list is the script's
(`BOOKKEEPING` in scripts/merge-gate.py); the prose does not repeat it.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = "## Gating tiers"


def test_tiers_are_stated_once():
    homes = [p for p in (*ROOT.glob("skills/**/*.md"), *ROOT.glob("rules/**/*.md")) if HOME in p.read_text()]
    assert homes == [ROOT / "rules" / "git.md"], homes

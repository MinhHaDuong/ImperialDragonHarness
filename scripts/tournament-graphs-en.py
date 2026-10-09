#!/usr/bin/env python3
"""Render the English edition with the same computations and snapshot as French.

Usage: python3 scripts/tournament-graphs-en.py --snapshot docs/tournament-graphs/snapshot.json
"""

import ast
import json
import sys
from pathlib import Path

source = Path(__file__).with_name("tournament-graphs.py")
translations = json.loads(source.with_name("tournament-english.json").read_text())


class EnglishText(ast.NodeTransformer):
    """Translate source text constants before wrapping and figure layout."""

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            node.value = translations.get(node.value, node.value)
        return node


if __name__ == "__main__":
    if "--output" not in sys.argv:
        sys.argv.extend(["--output", "docs/tournament-graphs-en"])
    text = source.read_text().replace(
        'f"{value:.2f}".replace(".", ",")', 'f"{value:.2f}"'
    )
    tree = EnglishText().visit(ast.parse(text, filename=str(source)))
    # Execute only the repository-owned renderer, after translating its literals.
    exec(  # noqa: S102
        compile(tree, str(source), "exec"),
        {"__name__": "__main__", "__file__": str(source), "__tournament_language__": "en"},
    )

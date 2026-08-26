"""The single definition of SKILL.md frontmatter extraction (ticket 0531).

Three copies of the ``---`` block regex had already diverged (the shell one
did not require the trailing newline), and the guard and the thing guarded
sharing duplicated logic is exactly the failure mode ticket 0515 closed. All
consumers — the catalog generator and both frontmatter test guards — import
this module; an adherence test in tests/test_skill_frontmatter.py keeps the
definition unique.

Errors are raised with a message naming the file, never swallowed: a helper
that absorbed a parse failure would disarm the 0515 guard built on it.
"""

import re
from pathlib import Path

import yaml

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


class FrontmatterError(ValueError):
    """A SKILL.md whose frontmatter cannot be used; the message names it."""


def frontmatter_text(path: Path) -> str:
    """The raw text between the opening ``---`` fences, or FrontmatterError."""
    m = FRONTMATTER.match(Path(path).read_text(encoding="utf-8"))
    if not m:
        raise FrontmatterError(
            f"{path}: no `---` frontmatter block at the top of the file")
    return m.group(1)


def load(path: Path) -> dict:
    """The frontmatter parsed as a YAML mapping, or FrontmatterError."""
    text = frontmatter_text(path)
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        reason = str(exc).splitlines()[0]
        raise FrontmatterError(
            f"{path}: invalid YAML frontmatter: {reason}") from exc
    if not isinstance(parsed, dict):
        raise FrontmatterError(
            f"{path}: frontmatter parses as {type(parsed).__name__}, "
            "not a mapping")
    return parsed

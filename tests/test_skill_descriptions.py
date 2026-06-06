"""Skill descriptions lead with the plain function, not the theme.

Discoverability rule (rules/workflow.md § Writing Skills and Hooks): the
FIRST sentence of every SKILL.md ``description:`` states what the skill does
in the keywords a naive user would search; draconic theming and harness lore
come after. Skill *names* may stay themed — only the description's opening
sentence is ratcheted here.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# Themed lexicon banned from the FIRST sentence. Deliberately excludes words
# that double as skill names or ordinary verbs (raid, roar, beat, dream,
# molt, perch, scry, hunt, gaze, lair) — cross-references to those are
# legitimate; the ban targets pure lore vocabulary.
THEME_LEXICON = re.compile(
    r"\b(imperial\s+dragon|dragons?|draconic|maws?|jaws?|fangs?|claws?|talons?"
    r"|wyrms?|beasts?|devour\w*)\b",
    re.IGNORECASE,
)


def iter_descriptions():
    for md in sorted((REPO / "skills").glob("*/SKILL.md")):
        m = re.search(r"^description:\s*(.+)$", md.read_text(), re.MULTILINE)
        assert m, f"{md}: no description in frontmatter"
        yield md.parent.name, m.group(1).strip().strip('"')


def first_sentence(desc: str) -> str:
    # Split on sentence-ending punctuation followed by whitespace; em-dash
    # clauses and parentheses inside the first sentence are kept.
    return re.split(r"(?<=[.!?])\s+", desc, maxsplit=1)[0]


def test_every_skill_has_a_description():
    names = [name for name, _ in iter_descriptions()]
    assert names, "no skills found"


def test_description_first_sentence_is_unthemed():
    offenders = []
    for name, desc in iter_descriptions():
        sentence = first_sentence(desc)
        hit = THEME_LEXICON.search(sentence)
        if hit:
            offenders.append(f"{name}: {hit.group(0)!r} in first sentence: {sentence!r}")
    assert not offenders, (
        "themed first sentence(s) — lead with the plain function, theme after "
        "(rules/workflow.md § Writing Skills and Hooks):\n" + "\n".join(offenders)
    )

"""Every SKILL.md frontmatter is valid YAML, and its free text is a quoted string.

Ticket 0515. Four SKILL.md files failed ``yaml.safe_load`` for months and a
fifth returned a list where a string was meant, because nothing in the repo
parsed this frontmatter as YAML: both consumers (``gen-skills-catalog.sh``,
``test_skill_descriptions.py``) pulled the field out with a regex and
``.strip('"')``, which tolerates a broken document. A check whose "all clear"
is indistinguishable from "I could not look" is not a check.

Two layers, deliberately:

* ``test_frontmatter_parses_as_yaml`` / ``test_free_text_fields_are_strings``
  are the load-bearing gate — they state the invariant a strict consumer
  depends on.
* ``test_free_text_fields_are_quoted`` is the authoring convention. It is
  strictly weaker (``description: "he said "no""`` is quoted and still
  broken), but it makes the invariant true by construction without asking the
  author to know which characters YAML treats specially, and it fails with an
  actionable message instead of a parser's cryptic one.
"""

import re
import sys

import pytest

from repo_sources import REPO, source_texts

sys.path.insert(0, str(REPO / "scripts"))

import skill_frontmatter as sf  # noqa: E402

# Free-text fields: values authored as prose or usage strings, where a colon,
# a leading bracket, or a quote is a natural thing to write and a YAML
# special character. Enum-like fields (name, model, user-invocable) are not
# ratcheted — they cannot collide with YAML syntax.
FREE_TEXT_FIELDS = ("description", "argument-hint")

# A frontmatter extractor is a regex anchoring on the opening fence and
# lazily capturing to the closing one. Spellings vary — a start-of-string or
# start-of-line anchor, an optional carriage return, a named group — so this
# matches the FAMILY, not one byte sequence. A re-spelled copy must not score
# zero and let the guard report "exactly one definition" while two exist.
# This pattern does not match its own source, so the guard needs no
# self-concealment trick; the controls below pin both directions, and they
# assemble their examples for the same reason.
DEFINITION = re.compile(r"(?:\\A|\^)-{3}(?:\\r\??)?\\n\(")


def skill_files():
    files = sorted((REPO / "skills").glob("*/SKILL.md"))
    assert files, "no skills found"
    return files


@pytest.mark.adherence
def test_frontmatter_regex_has_single_definition():
    """One extraction, one regex (ticket 0531): three copies had already
    diverged (the shell one did not require the trailing newline), and the
    guard and the thing guarded sharing duplicated logic is the failure mode
    0515 closed. The single definition lives in scripts/skill_frontmatter.py."""
    # One walk of the tree, shared with every other adherence guard — a
    # diverging copy of "where code lives" is the shape this guard forbids.
    hits = sorted(rel for rel, text in source_texts() if DEFINITION.search(text))
    # Exactly one, in the helper — zero would mean the scan (or the helper)
    # is broken, not the tree clean.
    assert hits == ["scripts/skill_frontmatter.py"], (
        "the frontmatter regex must have exactly one definition, in "
        f"scripts/skill_frontmatter.py (ticket 0531); found: {hits}"
    )


@pytest.mark.adherence
def test_definition_pattern_catches_variant_spellings():
    """Positive control: the pattern matches the family, not one spelling.
    Without this, a re-spelled copy scores zero and the guard's "exactly one"
    is indistinguishable from "I could not look"."""
    # Assembled, not written literally: a literal extractor regex in this
    # file would itself be a second definition and trip the guard above.
    fence = "-" * 3
    for variant in (
            "\\A" + fence + "\\n(.*?)\\n" + fence + "\\n",        # today's
            "^" + fence + "\\n(.*?)\\n" + fence,                  # ^ anchor
            "\\A" + fence + "\\r?\\n(?P<fm>.*?)\\n" + fence):     # CRLF+named
        assert DEFINITION.search(variant), f"missed a real copy: {variant}"


@pytest.mark.adherence
def test_definition_pattern_ignores_safe_forms():
    """Negative control: ordinary `---` text is not a second extractor."""
    for safe in ("--- log ---", "--- body ---", 'sep = "---"',
                 "yaml.safe_load(text)", "a---b\\n(x)"):
        assert not DEFINITION.search(safe), f"false positive on: {safe}"


@pytest.mark.adherence
def test_frontmatter_parses_as_yaml():
    offenders = []
    for md in skill_files():
        try:
            sf.load(md)
        except sf.FrontmatterError as exc:
            offenders.append(str(exc))
    assert not offenders, (
        "SKILL.md frontmatter must be valid YAML — a lenient consumer is not a "
        "guarantee, and the pi/Claude Code split adds one whose parser we do "
        "not control (ticket 0515):\n  " + "\n  ".join(offenders)
    )


@pytest.mark.adherence
def test_free_text_fields_are_strings():
    offenders = []
    for md in skill_files():
        try:
            parsed = sf.load(md)
        except sf.FrontmatterError:
            continue  # reported by test_frontmatter_parses_as_yaml
        for field in FREE_TEXT_FIELDS:
            if field not in parsed:
                continue
            value = parsed[field]
            # An empty `argument-hint:` (YAML null) means "takes no arguments".
            if value is None:
                continue
            if not isinstance(value, str):
                offenders.append(
                    f"{md.parent.name}: {field} parses as "
                    f"{type(value).__name__} ({value!r}), not a string"
                )
    assert not offenders, (
        "free-text frontmatter fields must parse as strings — an unquoted "
        "`[a, b]` becomes a list, not the usage hint you wrote "
        "(ticket 0515):\n  " + "\n  ".join(offenders)
    )


@pytest.mark.adherence
def test_free_text_fields_are_quoted():
    offenders = []
    for md in skill_files():
        text = sf.frontmatter_text(md)
        for field in FREE_TEXT_FIELDS:
            m = re.search(rf"^{re.escape(field)}:[ \t]*(.*)$", text, re.MULTILINE)
            if not m:
                continue
            raw = m.group(1).strip()
            if not raw:
                continue  # empty `argument-hint:` — nothing to quote
            if raw[0] not in "\"'":
                offenders.append(f"{md.parent.name}: {field}: {raw[:60]}")
    assert not offenders, (
        "free-text frontmatter values are always quoted (rules/workflow.md "
        "§ Writing Skills and Hooks) — wrap the value in \" \", or ' ' when it "
        "already contains a double quote:\n  " + "\n  ".join(offenders)
    )

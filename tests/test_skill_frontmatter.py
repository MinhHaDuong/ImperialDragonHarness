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
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]

# Free-text fields: values authored as prose or usage strings, where a colon,
# a leading bracket, or a quote is a natural thing to write and a YAML
# special character. Enum-like fields (name, model, user-invocable) are not
# ratcheted — they cannot collide with YAML syntax.
FREE_TEXT_FIELDS = ("description", "argument-hint")

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def skill_files():
    files = sorted((REPO / "skills").glob("*/SKILL.md"))
    assert files, "no skills found"
    return files


def frontmatter_text(md: Path) -> str:
    m = FRONTMATTER.match(md.read_text())
    assert m, f"{md.parent.name}: no `---` frontmatter block at the top of the file"
    return m.group(1)


@pytest.mark.adherence
def test_frontmatter_parses_as_yaml():
    offenders = []
    for md in skill_files():
        try:
            parsed = yaml.safe_load(frontmatter_text(md))
        except yaml.YAMLError as exc:
            reason = str(exc).splitlines()[0]
            offenders.append(f"{md.parent.name}: {reason}")
            continue
        if not isinstance(parsed, dict):
            offenders.append(f"{md.parent.name}: parses as {type(parsed).__name__}, not a mapping")
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
            parsed = yaml.safe_load(frontmatter_text(md))
        except yaml.YAMLError:
            continue  # reported by test_frontmatter_parses_as_yaml
        if not isinstance(parsed, dict):
            continue
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
        text = frontmatter_text(md)
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

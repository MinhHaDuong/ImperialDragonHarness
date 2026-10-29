"""Root documents name only paths and make targets that exist (ticket 1333).

A rename leaves README, INSTALL or AGENTS pointing at nothing, and no other
check reads them. Every root ``*.md`` is scanned: a backticked token or a link
target whose first segment is a top-level entry of the repo must exist, and
every ``make <target>`` in backticks or opening a line must be a Makefile target. Placeholders (``<x>``,
``*``, ``$VAR``, ``~``, ``YYYY``) are skipped. This catches renames, not drifted
meaning; that stays with roar step 6.

Positive controls: ``test_check_fires_on_fixture`` shows both checks can fail,
and the scan refuses an empty document set, so an all-clear is never "nothing
was read".
"""

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
PLACEHOLDER = re.compile(r"[<>*{}$~]|://|^#|\b(?:YYYY|MM|DD|NNNN)\b")


def make_targets(root: Path) -> set[str]:
    text = (root / "Makefile").read_text(encoding="utf-8")
    return set(re.findall(r"^([A-Za-z0-9_.-]+):", text, re.M))


def dangling(root: Path) -> list[str]:
    """Return ``doc: token`` for each path or make target that does not exist."""
    docs = sorted(root.glob("*.md"))
    assert docs, f"no root *.md under {root}: cannot certify"
    tops = {p.name for p in root.iterdir()}
    targets = make_targets(root)
    found = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        tokens = set(re.findall(r"`([^`\s]+)`", text))
        tokens |= set(re.findall(r"\]\(([^)\s#]+)", text))
        for token in sorted(tokens):
            token = token.rstrip(".,;:")
            if PLACEHOLDER.search(token) or token.split("/")[0] not in tops:
                continue
            if not (root / token).exists():
                found.append(f"{doc.name}: {token}")
        for target in sorted(set(re.findall(r"(?:`|^\s*)make ([a-z][\w-]*)", text, re.M))):
            if target not in targets:
                found.append(f"{doc.name}: make {target}")
    return found


def test_root_docs_name_existing_paths_and_targets():
    assert dangling(REPO) == []


def test_check_fires_on_fixture(tmp_path):
    (tmp_path / "Makefile").write_text("check:\n\ttrue\n", encoding="utf-8")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "here.py").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "Run `scripts/here.py`, `scripts/gone.py` and [x](scripts/lost.py);\n"
        "then `make check` and `make vanished`. Skip `scripts/<name>.py`,\n"
        "`memory/YYYY/` and `notes.txt`. Prose may make sense of it.\n",
        encoding="utf-8",
    )
    assert dangling(tmp_path) == [
        "README.md: scripts/gone.py",
        "README.md: scripts/lost.py",
        "README.md: make vanished",
    ]


def test_check_refuses_empty_doc_set(tmp_path):
    (tmp_path / "Makefile").write_text("", encoding="utf-8")
    with pytest.raises(AssertionError):
        dangling(tmp_path)

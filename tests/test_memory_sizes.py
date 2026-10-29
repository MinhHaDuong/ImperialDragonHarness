"""Topic byte budget (ticket 1348): the check and its definitions in SMELT.md."""

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import memory_sizes as ms  # noqa: E402

# Ceilings at the guide sizes measured 2026-10-29 (bytes, Retired and Sources
# excluded). Ticket 1349 rebuilds the
# pages under the 4 KB cap and deletes this dict.
TRANSITION = {
    "branch-cleanup-incidents.md": 4879,
    "ci-and-test-suite.md": 6611,
    "git-worktree-session-guards.md": 5516,
    "host-environment.md": 3514,
    "memory-v8-acceptance-trial.md": 7806,
    "memory-v8-governance.md": 7895,
    "raid-review-and-merge.md": 16618,
    "runtime-observations.md": 7485,
    "shared-checkout-concurrency.md": 6547,
    "subagent-model-effort-levers.md": 2576,
    "zotero-library.md": 3556,
}


def _page(guidance: int, retired: int = 0, sources: int = 0) -> str:
    text = "# Page\n\n## Guidance\n\n" + "a" * guidance + "\n"
    if retired:
        text += "\n## Retired\n\n" + "r" * retired + "\n"
    if sources:
        text += "\n## Sources\n\n" + "s" * sources + "\n"
    return text


def test_retired_section_is_outside_the_cap():
    assert ms.guide_bytes(_page(3000, retired=6000)) <= ms.CAP
    assert ms.guide_bytes(_page(4200)) > ms.CAP


def test_sources_section_is_outside_the_cap():
    assert ms.guide_bytes(_page(3000, sources=6000)) <= ms.CAP


def test_sections_after_retired_still_count():
    text = _page(3000, retired=500) + "\n## Hazards\n\n" + "h" * 2000 + "\n"
    assert ms.guide_bytes(text) > ms.CAP


def test_exact_cap_passes_and_cap_plus_one_fails(tmp_path):
    head = "## G\n"
    pad = ms.CAP - len(head.encode()) - 2  # leave room for a 2-byte char
    ok = head + "a" * pad + "é"
    assert ms.guide_bytes(ok) == ms.CAP
    (tmp_path / "ok.md").write_text(ok, encoding="utf-8")
    assert ms.main(tmp_path) == 0
    (tmp_path / "ok.md").write_text(ok + "a", encoding="utf-8")
    assert ms.main(tmp_path) == 1


def test_commission_over_cap_warns_not_fails(tmp_path, capsys):
    (tmp_path / ms.COMMISSION).write_text(_page(5000), encoding="utf-8")
    assert ms.main(tmp_path) == 0
    assert "OVER (promote to rules, brood 1351)" in capsys.readouterr().out


def test_index_line_cap():
    assert ms.index_ok("x\n" * ms.INDEX_LINES)
    assert not ms.index_ok("x\n" * (ms.INDEX_LINES + 1))
    assert not ms.index_ok("\n" * (ms.INDEX_LINES + 1))


def test_real_tree_is_measured():
    rows = list(ms.report(REPO / "memory" / "topics"))
    assert len(rows) >= 10, "glob found too few pages: a census that cannot look"
    for name, size, _cap, _status in rows:
        assert size <= TRANSITION.get(name, ms.CAP), f"{name} grew to {size}"
    assert ms.index_ok((REPO / "memory" / "MEMORY.md").read_text(encoding="utf-8"))


def test_quotation_clause_scoped():
    text = (REPO / "skills" / "smelt" / "SKILL.md").read_text(encoding="utf-8")
    flat = " ".join(text.split())
    assert "quotations from manuscript sources" in flat
    assert "40 lines" in flat and "100 lines" not in flat

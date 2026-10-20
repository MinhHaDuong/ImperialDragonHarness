"""Ticket 1150: the pending attribution files for PRs 1456, 1457 and 1460 are folded in."""

from pathlib import Path

import pytest

from scripts.attribution_record import parse_record

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("pr", [1456, 1457, 1460])
def test_folded_record_validates_and_links_pending_file(pr):
    pending = Path(f"memory/evidence/review-attribution-pr{pr}-pending.md")
    assert (ROOT / pending).is_file()
    (entry,) = (ROOT / "memory/journal/2026").glob(f"*-review-attribution-pr{pr}.md")
    text = entry.read_text()
    record = parse_record(text)
    assert record["pr"] == pr
    assert str(pending) in text
    assert record["writer"]["effort"] == "not-stated"
    for identity in [record["writer"], *record["reviewers"]]:
        assert identity["model-evidence"].startswith(str(pending) + ":")

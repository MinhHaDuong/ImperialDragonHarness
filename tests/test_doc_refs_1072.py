"""Guards for stale doc references fixed under ticket 1072."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_review_pr_manifest_not_names_only():
    text = (ROOT / "skills/review-pr/SKILL.md").read_text()
    assert "perspective names only" not in text


def test_route_cites_existing_decorrelation_headings():
    route = (ROOT / "skills/route/SKILL.md").read_text()
    deco = (ROOT / "skills/route/references/decorrelation.md").read_text()
    headings = set(re.findall(r"^#+\s+(.+?)\s*$", deco, re.M))
    m = re.search(r"The doctrine \(sections (.+?)\) is `references/decorrelation", route, re.S)
    assert m, "route/SKILL.md must cite decorrelation.md sections by name"
    cited = [" ".join(c.split()) for c in re.findall(r'"([^"]+)"', m.group(1))]
    assert cited
    for name in cited:
        assert name in headings, f"{name!r} is not a heading in decorrelation.md"


def test_makefile_run_comment_does_not_claim_ci_sets_virtual_env():
    text = (ROOT / "Makefile").read_text()
    assert "as in CI after" not in text
    assert "VIRTUAL_ENV set, as in CI" not in text


def test_review_pr_collection_names_manifest_first_field():
    text = " ".join((ROOT / "skills/review-pr/SKILL.md").read_text().split())
    assert "every manifest entry (its first, perspective field)" in text

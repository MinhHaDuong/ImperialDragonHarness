import json
from pathlib import Path


def test_committed_grid_and_coverage_join_on_arm_without_overlap():
    root = Path(__file__).parents[1] / "skills/route"
    grid = json.loads((root / "grid.json").read_text())
    detail = json.loads((root / "grid-coverage.json").read_text())["arms"]
    assert {row["arm"] for row in grid["grid"]} == set(detail)
    for row in grid["grid"]:
        assert row["family"] == detail[row["arm"]]["family"]
        assert not (set(row) & set(detail[row["arm"]])) - {"family"}

"""Numerical invariants of the reproducible report supplement."""

import importlib.util
import json
import math
import statistics
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


completion = module("completion", "tournament-report-completion.py")
graphs = module("graphs", "tournament-graphs.py")


def test_oriented_even_sample_recomputes_ratios_instead_of_inverting_median():
    ratios = [0.1, 0.2, 3, 8]
    snapshot = {
        "legs": {
            "a": {
                str(i): {"quality": 20 + i, "seconds": r, "cost_usd": r}
                for i, r in enumerate(ratios)
            },
            "b": {
                str(i): {"quality": 22 - i, "seconds": 1, "cost_usd": 1}
                for i in range(4)
            },
        }
    }
    rows = completion.analyze(snapshot, graphs.signed_rank, graphs.holm)
    reverse = completion.oriented(rows, "b", "a", snapshot)
    assert reverse["seconds_ratio_median"] == statistics.median(1 / r for r in ratios)
    assert reverse["seconds_ratio_median"] != 1 / statistics.median(ratios)
    assert reverse["quality_differences"] == [2, 0, -2, -4]
    assert reverse["wins"] == 1 and reverse["ties"] == 1 and reverse["losses"] == 2


def test_frontier_uses_three_axes_and_quality_floor():
    snapshot = {
        "arms": {
            "cheap": {
                "final": True,
                "quality_mean": 20,
                "seconds_mean": 5,
                "cost_usd_mean": 1,
            },
            "quality": {
                "final": True,
                "quality_mean": 25,
                "seconds_mean": 10,
                "cost_usd_mean": 2,
            },
            "dominated": {
                "final": True,
                "quality_mean": 19,
                "seconds_mean": 6,
                "cost_usd_mean": 2,
            },
            "unusable": {
                "final": True,
                "quality_mean": 8,
                "seconds_mean": 0.1,
                "cost_usd_mean": 0.01,
            },
        }
    }
    assert completion.frontier3(snapshot) == ["cheap", "quality"]


def test_published_supplement_matches_original_tests_and_all_pairs():
    snapshot = json.loads((ROOT / "docs/tournament-graphs/snapshot.json").read_text())
    report = json.loads(
        (ROOT / "docs/tournament-graphs/appendix-analysis.json").read_text()
    )
    originals = json.loads((ROOT / "docs/tournament-graphs/tests.json").read_text())
    assert len(report["comparisons"]) == math.comb(len(snapshot["arms"]), 2) == 190
    assert len(report["selected_pairs"]) == 13
    assert len({(r["a"], r["b"]) for r in report["comparisons"]}) == 190
    for metric in ("quality", "seconds", "cost_usd"):
        source = {
            frozenset((r["a"], r["b"])): r["p"]
            for r in originals[metric]["comparisons"]
        }
        for row in report["comparisons"]:
            pair = frozenset((row["a"], row["b"]))
            if pair in source:
                assert row[metric + "_p"] == source[pair]
            assert row[metric + "_p_holm_190"] >= 0.05
    for metric in ("quality", "seconds", "cost_usd"):
        row = next(r for r in report["comparisons"] if {r["a"], r["b"]} == {"c", "l"})
        diff = [
            snapshot["legs"]["c"][t][metric] - snapshot["legs"]["l"][t][metric]
            for t in sorted(snapshot["legs"]["c"])
        ]
        assert row[metric + "_p"] == graphs.signed_rank(diff)[0]


def test_cluster_memberships_match_the_existing_grid():
    grid = json.loads((ROOT / "skills/route/grid.json").read_text())
    assert set(grid["clusters"]) == set(completion.CLUSTERS)
    assert set(completion.CLUSTERS["ECONOMIQUES"]) == {"l", "n", "i", "j", "k"}
    assert len({a for group in completion.CLUSTERS.values() for a in group}) == 15


def test_french_spacing_binds_high_punctuation_guillemets_and_digit_groups():
    nb = "\u00a0"
    text = "Luna : 0,03 ; « coût » ? 2 500 tokens, ticket 0333 2026"
    assert completion.french_spacing(text) == (
        f"Luna{nb}: 0,03{nb}; «{nb}coût{nb}»{nb}? 2{nb}500 tokens, ticket 0333 2026"
    )


def test_wrap_paragraph_keeps_nonbreaking_spaces_before_french_punctuation():
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(3, 2))
    try:
        text = " ".join(["Luna : 0,03 ; « coût »"] * 6)
        wrapped = graphs.wrap_paragraph(fig, text, 10, width=0.5)
    finally:
        plt.close(fig)
    assert "\n" in wrapped
    for line in wrapped.split("\n"):
        assert not line.startswith((":", ";", "»"))
    assert "Luna\u00a0:" in wrapped and "«\u00a0coût\u00a0»" in wrapped


def test_french_text_binds_french_figure_strings_and_skips_mathtext():
    assert graphs.FRENCH
    assert graphs.french_text("Bleu : local ; vert") == "Bleu\u00a0: local\u00a0; vert"
    assert graphs.french_text("$H_0 : f = 0$") == "$H_0 : f = 0$"
    assert graphs.french_text(None) is None


@pytest.mark.integration
def test_supplement_opens_with_a_section_title_page():
    for pdf, title in (
        ("docs/tournament-graphs/comparaisons-modeles.pdf", "Annexe technique auto-générée"),
        ("docs/tournament-graphs-en/model-comparison.pdf", "Auto-generated technical appendix"),
    ):
        text = subprocess.run(
            ["pdftotext", "-f", "13", "-l", "13", str(ROOT / pdf), "-"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert title in " ".join(text.split())

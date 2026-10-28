"""review_trajectory classes each merged PR by the round sequence of above-bar findings.

The probe answers "which PRs show an approach not converging, a reviewer miss or
weak coder output?", so both errors cost: a miss read as normal hides a reviewer
that let a defect through; a fresh blocker read as a miss blames the wrong party.
These tests are its positive control: a real git fixture repo with one merged PR
per class, the reviewer miss derived from a line present at the round-1 head that
a later blocker cites, plus the insufficient cases and the drift line.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import review_trajectory as rt  # noqa: E402

BAR = "scenario: a caller meets the wrong outcome. on main: no, the base passes."


def _git(repo: Path, *args: str, date: str = "2026-10-28T10:00:00") -> str:
    env = {
        **os.environ,
        "GIT_COMMITTER_DATE": date,
        "GIT_AUTHOR_DATE": date,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@t",
    }
    done = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return done.stdout.strip()


def _item(index: int, tag: str, cite: str, above: bool) -> str:
    return f"{index}. correctness · {tag}: · {cite} · a finding. " + (
        BAR if above else "no more."
    )


def _answer(*items: tuple[str, str, bool]) -> str:
    body = "\n".join(_item(i, *item) for i, item in enumerate(items, 1))
    return f"## /gaze result\n\nresult: FINDINGS\n\nFindings:\n{body}\nnofollow: a thing\n\nTests: pass\n"


class Fixture:
    """A repo whose main holds merge commits `Merge pull request #N`, one branch per PR."""

    def __init__(self, path: Path):
        self.repo = path
        path.mkdir()
        _git(path, "init", "-q", "-b", "main")
        (path / "base.txt").write_text("base\n")
        _git(path, "add", "-A")
        _git(path, "commit", "-q", "-m", "base", date="2026-10-01T10:00:00")
        self.rounds: dict[int, list[dict]] = {}

    def pr(
        self,
        number: int,
        rounds: list[tuple[str, list[tuple[str, str, bool]]]],
        date="2026-10-28T10:00:00",
    ):
        """rounds: per round, (file content, findings). One commit per round on the PR branch."""
        _git(self.repo, "switch", "-q", "-c", f"pr{number}", "main")
        out = []
        for content, findings in rounds:
            (self.repo / f"f{number}.py").write_text(content)
            _git(self.repo, "add", "-A")
            _git(
                self.repo,
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                f"pr {number} round",
                date=date,
            )
            out.append(
                {
                    "head": _git(self.repo, "rev-parse", "HEAD"),
                    "text": _answer(*findings),
                }
            )
        _git(self.repo, "switch", "-q", "main")
        _git(
            self.repo,
            "merge",
            "-q",
            "--no-ff",
            f"pr{number}",
            "-m",
            f"Merge pull request #{number} from x/pr{number}",
            date=date,
        )
        self.rounds[number] = out

    def reader(self, number: int):
        return self.rounds.get(number, [])


BASE = "a = 1\nb = 2\nreturn risky(x)\n"


def _fixture(tmp_path: Path) -> Fixture:
    fx = Fixture(tmp_path / "repo")
    # normal: one blocker, then below the bar
    fx.pr(
        11,
        [
            (BASE, [("blocking", "f11.py:3", True)]),
            (BASE + "c = 3\n", [("consider", "f11.py:4", False)]),
        ],
    )
    # coder: four above-bar findings in round 1 (threshold 3), shrinking, late one on a new line
    fx.pr(
        12,
        [
            (
                BASE,
                [("verifiable", f"f12.py:{i}", True) for i in (1, 2, 3)]
                + [("blocking", "f12.py:1", True)],
            ),
            (BASE + "c = 3\n", [("blocking", "f12.py:4", True)]),
            (BASE + "c = 3\n", []),
        ],
    )
    # approach: a fresh above-bar finding on the line each round added, still one at round 3
    fx.pr(
        13,
        [
            (BASE, [("blocking", "f13.py:3", True)]),
            (BASE + "c = 3\n", [("blocking", "f13.py:4", True)]),
            (BASE + "c = 3\nd = 4\n", [("blocking", "f13.py:5", True)]),
        ],
    )
    # reviewer miss: round 2 blocker cites line 3, `return risky(x)`, already in the round-1 head
    fx.pr(
        14,
        [
            (BASE, [("blocking", "f14.py:2", True), ("blocking", "f14.py:1", True)]),
            (BASE + "c = 3\n", [("blocking", "f14.py:3", True)]),
            (BASE + "c = 3\n", []),
        ],
    )
    # one round only
    fx.pr(15, [(BASE, [("consider", "f15.py:1", False)])])
    # merged without any review notes
    fx.pr(16, [(BASE, [])])
    fx.rounds.pop(16)
    return fx


def _survey(fx: Fixture, **kw):
    return rt.survey(fx.repo, "2026-10-01", rounds_of=fx.reader, **kw)


def _classes(report) -> dict[int, str]:
    return {p["pr"]: p["class"] for p in report["prs"]}


def test_normal_shrinking_below_the_bar(tmp_path):
    assert _classes(_survey(_fixture(tmp_path)))[11] == "normal"


def test_coder_many_above_bar_in_round_one(tmp_path):
    report = _survey(_fixture(tmp_path))
    assert _classes(report)[12] == "coder"
    assert [p["counts"] for p in report["prs"] if p["pr"] == 12] == [[4, 1, 0]]


def test_coder_threshold_is_a_flag(tmp_path):
    assert _classes(_survey(_fixture(tmp_path), coder_threshold=5))[12] == "normal"


def test_approach_not_shrinking_by_round_three(tmp_path):
    assert _classes(_survey(_fixture(tmp_path)))[13] == "approach"


def test_reviewer_miss_is_derived_from_git(tmp_path):
    report = _survey(_fixture(tmp_path))
    assert _classes(report)[14] == "reviewer-miss"
    miss = next(p for p in report["prs"] if p["pr"] == 14)
    assert miss["late"] == [
        {"round": 2, "cite": "f14.py:3", "tag": "blocking", "old": True}
    ]


def test_a_late_blocker_on_a_new_line_is_not_a_miss(tmp_path):
    late = next(p for p in _survey(_fixture(tmp_path))["prs"] if p["pr"] == 12)["late"]
    assert late == [{"round": 2, "cite": "f12.py:4", "tag": "blocking", "old": False}]


def test_insufficient_names_its_reason(tmp_path):
    report = _survey(_fixture(tmp_path))
    reasons = {
        p["pr"]: p["reason"] for p in report["prs"] if p["class"] == "insufficient"
    }
    assert reasons == {15: "one round", 16: "no notes"}


def test_render_one_line_per_class_with_pr_numbers(tmp_path):
    lines = rt.render(_survey(_fixture(tmp_path))).splitlines()
    by_class = {line.split(":")[0]: line for line in lines if ":" in line}
    assert "#13" in by_class["approach"] and "#14" in by_class["reviewer-miss"]
    assert "#12" in by_class["coder"] and "#11" in by_class["normal"]
    assert (
        "#15 (one round)" in by_class["insufficient"]
        and "#16 (no notes)" in by_class["insufficient"]
    )


def test_unreadable_repo_is_not_checked(tmp_path, capsys):
    code = rt.main(["--since", "2026-10-01", "--repo", str(tmp_path)])
    assert code == 2 and "not checked" in capsys.readouterr().out


def test_missing_notes_ref_is_not_checked(tmp_path, capsys):
    fx = Fixture(tmp_path / "bare")
    assert rt.main(["--since", "2026-10-01", "--repo", str(fx.repo)]) == 2
    assert "not checked" in capsys.readouterr().out


def test_drift_rises_across_two_months(tmp_path):
    fx = Fixture(tmp_path / "repo")
    for number, month in ((21, "2026-10-05"), (22, "2026-11-05")):
        tag = "consider" if number == 21 else "blocking"
        fx.pr(
            number,
            [
                (BASE, [("blocking", f"f{number}.py:1", True)]),
                (BASE + "c\n", [(tag, f"f{number}.py:4", tag == "blocking")]),
                (BASE + "c\n", []),
            ],
            date=f"{month}T10:00:00",
        )
    report = rt.survey(fx.repo, "2026-10-01", rounds_of=fx.reader)
    assert report["drift"]["months"] == {"2026-10": 1.0, "2026-11": 3.0}
    assert "rising" in rt.render(report)


def test_drift_not_assessed_inside_one_month(tmp_path):
    report = _survey(_fixture(tmp_path))
    assert report["drift"] is None
    assert "one month" in rt.render(report)


def test_parse_findings_gates_on_scenario_and_on_main():
    text = (
        "Findings:\n1. correctness · verifiable: · a.py:3 · x. scenario: s. on main: no.\n"
        "2. correctness · verifiable: · a.py:4 · x. no scenario here.\n"
        "- blocking: a.py:9 scenario: s on main: n/a\n"
        "3. Round-1 blocking finding 1 is fixed.\n   - scenario: s on main: no\n"
        "nofollow: ignored\n"
    )
    got = [(f["cite"], f["tag"], f["above"]) for f in rt.parse_findings(text)]
    assert got == [
        ("a.py:3", "verifiable", True),
        ("a.py:4", "verifiable", False),
        ("a.py:9", "blocking", True),
        (None, "blocking", False),
    ]


def test_a_repeated_finding_is_not_a_reviewer_miss(tmp_path):
    """Round 1 caught it; the coder left the line; round 2 repeats it. The reviewer saw it."""
    fx = Fixture(tmp_path / "repo")
    fx.pr(
        31,
        [
            (BASE, [("blocking", "f31.py:3", True)]),
            (BASE + "c = 3\n", [("blocking", "f31.py:3", True)]),
            (BASE + "c = 3\n", []),
        ],
    )
    pr = rt.survey(fx.repo, "2026-10-01", rounds_of=fx.reader)["prs"][0]
    assert pr["class"] != "reviewer-miss" and pr["late"] == []


def test_an_unreadable_round_one_head_is_unverified_not_new(tmp_path):
    fx = Fixture(tmp_path / "repo")
    fx.pr(
        32,
        [
            (BASE, [("blocking", "f32.py:1", True)]),
            (BASE + "c = 3\n", [("blocking", "f32.py:3", True)]),
            (BASE + "c = 3\n", []),
        ],
    )
    fx.rounds[32][0]["head"] = "deadbeef" * 5
    report = rt.survey(fx.repo, "2026-10-01", rounds_of=fx.reader)
    assert report["prs"][0]["late"][0]["old"] is None
    assert "unverified late findings (head or line unreadable): #32" in rt.render(
        report
    )


def test_approach_counts_any_round_from_the_third(tmp_path):
    fx = Fixture(tmp_path / "repo")
    fx.pr(
        33,
        [
            (BASE, [("blocking", "f33.py:1", True)]),
            (BASE + "c\n", []),
            (BASE + "c\n", []),
            (BASE + "c\nd\n", [("blocking", "f33.py:5", True)]),
        ],
    )
    assert (
        rt.survey(fx.repo, "2026-10-01", rounds_of=fx.reader)["prs"][0]["class"]
        == "approach"
    )

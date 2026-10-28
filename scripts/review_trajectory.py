#!/usr/bin/env python3
"""Read the health of review across merged PRs, from the round sequence of above-bar findings.

For every PR merged since a date, take its gaze answers from refs/notes/review (local
entries only; fetch the notes first), count per answer the findings above the bar
(`skills/gaze/references/panel.md` § Finding tags: a `blocking` or `verifiable:` finding
that carries `scenario:` and `on main:`), and class the PR by that sequence:
- approach: round 3 or later still has above-bar findings, at least as many as round 1
  (fresh blockers at round 3 mean the approach is wrong, not the fixes);
- reviewer-miss: a finding above the bar in round 2 or later cites a line that was already
  in the round-1 reviewed head (the cited line's text is looked up with git in the head of
  its own round, then searched in the round-1 head's file), so the first round saw it and
  said nothing;
- coder: round 1 alone carries at least `--coder-threshold` above-bar findings (default 3);
- normal: shrinking and the last round below the bar: the base rate.
A PR with no notes, one round, or a last round still above the bar is `insufficient`, with
the reason. Classes are tested in this order, so a PR is counted once.

When the merged PRs span two calendar months or more, a drift line gives the mean severity of
late findings (rounds 2 and later; blocking 3, verifiable 2, consider 1) per merge month.

Read-only: it writes no note and no forge object, and reads no credential. Merged PRs come from
`Merge pull request #N` merge commits on origin/main (HEAD without it). Heads no longer in the
clone leave a late finding "unverified", never a miss. An unreadable repo, or one without
refs/notes/review, prints "not checked", never an all-clear. Findings feed arena evidence or
tickets by the reader's judgment (`skills/route/SKILL.md` § Update discipline); nothing is edited.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import review_notes  # noqa: E402

CLASSES = ("approach", "reviewer-miss", "coder", "normal", "insufficient")
SEVERITY = {"blocking": 3, "verifiable": 2, "consider": 1}
ITEM_RE = re.compile(r"^(?:\d+\.|[-*])\s")
TAG_RE = re.compile(r"\b(blocking|verifiable|consider|nofollow)\b")
CITE_RE = re.compile(r"[\w./-]+\.\w+:\d+")
MERGE_RE = re.compile(r"^Merge pull request #(\d+)")


def parse_findings(text: str) -> list[dict]:
    """Items of an answer's Findings block: {tag, cite, above}. The tag is the first
    tag word of the item's first line; an item is above the bar when it is blocking or
    verifiable and carries a `path:line` citation and both `scenario:` and `on main:` in its text
    (an item without a location, such as "round-1 blocker is fixed", is never above the bar)."""
    out, item, inside = [], None, False
    for line in text.splitlines():
        if re.match(r"^Findings\b", line):
            inside = True
            continue
        if not inside:
            continue
        if ITEM_RE.match(line):
            item = [line]
            out.append(item)
        elif line.strip() and not line[0].isspace():
            break
        elif item is not None and line.strip():
            item.append(line)
    found = []
    for lines in out:
        tag = TAG_RE.search(lines[0])
        tag = tag.group(1) if tag else None
        body = "\n".join(lines).lower()
        cite = CITE_RE.search(lines[0])
        found.append(
            {
                "tag": tag,
                "cite": cite.group(0) if cite else None,
                "above": bool(cite)
                and tag in ("blocking", "verifiable")
                and "scenario:" in body
                and "on main:" in body,
            }
        )
    return found


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True
    )


def line_text(repo: Path, head: str, path: str, number: int) -> str | None:
    done = _git(repo, "show", f"{head}:{path}")
    lines = done.stdout.splitlines()
    return (
        lines[number - 1].strip()
        if done.returncode == 0 and 0 < number <= len(lines)
        else None
    )


def was_present(repo: Path, first_head: str, head: str, cite: str) -> bool | None:
    """Did the cited line (as it reads in `head`) already exist in `first_head`? None: unknown."""
    path, number = cite.rsplit(":", 1)
    text = line_text(repo, head, path, int(number))
    if not text or len(text) < 4:
        return None
    done = _git(repo, "show", f"{first_head}:{path}")
    return (
        any(row.strip() == text for row in done.stdout.splitlines())
        if done.returncode == 0
        else False
    )


def notes_rounds(repo: Path):
    """A reader of the PR's gaze answers, oldest first: [{head, text}], from local notes only."""

    def read(number: int) -> list[dict]:
        rid = review_notes.find_unit(repo, f"pr:{number}")
        if not rid:
            return []
        return [
            {"head": e["head"], "text": e.get("text") or ""}
            for e in review_notes.entries(repo, rid)
            if e["kind"] == "answer"
        ]

    return read


def merged_prs(repo: Path, since: str) -> list[tuple[int, str]]:
    base = (
        "origin/main"
        if _git(repo, "rev-parse", "--verify", "-q", "origin/main").returncode == 0
        else "HEAD"
    )
    done = _git(repo, "log", "--merges", "--format=%cs%x09%s", base)
    out = []
    for row in done.stdout.splitlines():
        day, _, subject = row.partition("\t")
        hit = MERGE_RE.match(subject)
        if (
            hit and day >= since
        ):  # git's own --since reads a bare date as now-of-day, losing today's merges
            out.append((int(hit.group(1)), day))
    return sorted(out)


def analyse(repo: Path, rounds: list[dict], threshold: int) -> dict:
    parsed = [parse_findings(r["text"]) for r in rounds]
    counts = [sum(f["above"] for f in found) for found in parsed]
    late = []
    for number, found in enumerate(parsed[1:], 2):
        for f in found:
            if f["above"] and f["cite"]:
                late.append(
                    {
                        "round": number,
                        "cite": f["cite"],
                        "tag": f["tag"],
                        "old": was_present(
                            repo,
                            rounds[0]["head"],
                            rounds[number - 1]["head"],
                            f["cite"],
                        ),
                    }
                )
    late_all = [
        {"tag": f["tag"]} for found in parsed[1:] for f in found if f["tag"] in SEVERITY
    ]
    if len(rounds) < 2:
        verdict, reason = "insufficient", "one round"
    elif len(rounds) >= 3 and counts[2] > 0 and counts[2] >= counts[0]:
        verdict, reason = "approach", ""
    elif any(item["old"] for item in late):
        verdict, reason = "reviewer-miss", ""
    elif counts[0] >= threshold:
        verdict, reason = "coder", ""
    elif counts[-1] > 0:
        verdict, reason = "insufficient", "last round still above the bar"
    else:
        verdict, reason = "normal", ""
    return {
        "class": verdict,
        "reason": reason,
        "counts": counts,
        "late": late,
        "severities": [SEVERITY[f["tag"]] for f in late_all],
    }


def drift(prs: list[dict]) -> dict | None:
    months: dict[str, list[int]] = {}
    for p in prs:
        months.setdefault(p["day"][:7], []).extend(p.get("severities", []))
    means = {m: round(sum(v) / len(v), 2) for m, v in sorted(months.items()) if v}
    if len({p["day"][:7] for p in prs}) < 2:
        return None
    return {
        "months": means,
        "rising": len(means) >= 2
        and list(means.values())[-1] > list(means.values())[0],
    }


def survey(repo: Path, since: str, rounds_of=None, coder_threshold: int = 3) -> dict:
    rounds_of = rounds_of or notes_rounds(repo)
    prs = []
    for number, day in merged_prs(repo, since):
        rounds = rounds_of(number)
        if not rounds:
            prs.append(
                {
                    "pr": number,
                    "day": day,
                    "class": "insufficient",
                    "reason": "no notes",
                    "counts": [],
                    "late": [],
                    "severities": [],
                }
            )
            continue
        prs.append({"pr": number, "day": day, **analyse(repo, rounds, coder_threshold)})
    return {"since": since, "prs": prs, "drift": drift(prs)}


def render(report: dict) -> str:
    prs = report["prs"]
    lines = [f"review trajectory since {report['since']}: {len(prs)} merged PRs"]
    for name in CLASSES:
        hits = [p for p in prs if p["class"] == name]
        if name == "insufficient":
            cited = ", ".join(f"#{p['pr']} ({p['reason']})" for p in hits)
        else:
            cited = ", ".join(f"#{p['pr']} {p['counts']}" for p in hits)
        lines.append(f"{name}: {cited or 'none'}")
    unverified = [
        p["pr"] for p in prs if any(item["old"] is None for item in p["late"])
    ]
    if unverified:
        lines.append(
            "unverified late findings (head or line unreadable): "
            + ", ".join(f"#{n}" for n in unverified)
        )
    d = report["drift"]
    if d is None:
        lines.append("drift: merged PRs fall in one month, not assessed")
    else:
        trail = " -> ".join(f"{m} {v}" for m, v in d["months"].items())
        lines.append(
            f"drift: mean severity of late findings {trail}: {'rising' if d['rising'] else 'not rising'}"
        )
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--since", required=True, help="first merge date, YYYY-MM-DD")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument(
        "--coder-threshold",
        type=int,
        default=3,
        help="above-bar findings in round 1 that class a PR as coder (default 3)",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the full report as JSON"
    )
    args = parser.parse_args(argv)
    if _git(args.repo, "rev-parse", "--git-dir").returncode != 0:
        print(
            f"review-trajectory: not checked: {args.repo} is not a readable git repository"
        )
        return 2
    if _git(args.repo, "rev-parse", "--verify", "-q", review_notes.REF).returncode != 0:
        print(
            f"review-trajectory: not checked: {review_notes.REF} absent here (fetch the review notes first)"
        )
        return 2
    report = survey(args.repo, args.since, coder_threshold=args.coder_threshold)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())

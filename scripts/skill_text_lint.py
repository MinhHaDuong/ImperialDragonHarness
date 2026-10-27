#!/usr/bin/env python3
"""Mechanical skill-text lint for /harness-doctor (ticket 1234).

A doctor's instrument, never a gate: it always exits 0, wires into no
adherence command, merge gate or session start, and calls no model. Its
findings are evidence for the doctor's report. False positives are expected
("used to compute", dates in command examples, templates) and are the
doctor's to judge.

Scans skills/*/SKILL.md and skills/*/references/*.md under --root. Stdout is
JSON {"files": N, "findings": [{file, line, check, text}], "summary":
{check: count}}; stderr carries one human line per check.
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_frontmatter import FRONTMATTER  # noqa: E402

log = logging.getLogger("skill_text_lint")

MAX_BODY_LINES = 150
MAX_FENCE_LINES = 12
SCRIPT_FENCE_INFO = {"", "bash", "sh", "python"}
SKIPPED_PROJECTS = {"harness"}  # hits constantly
DEFAULT_PROJECTS = Path(__file__).resolve().parent / "projects.json"

PATTERNS = [
    ("history_phase", r"\bphase \d"),
    ("history_since", r"\bsince we\b"),
    ("history_used_to", r"\bused to\b"),
    ("history_formerly", r"\bformerly\b"),
    ("date", r"20\d\d-\d\d(-\d\d)?"),
    ("ticket_ref", r"#\d{3,}"),
    ("ticket_word", r"\b(ticket|MR|PR) \d+"),
]


def project_names(projects_file: Path) -> list[str]:
    entries = json.loads(Path(projects_file).read_text(encoding="utf-8"))
    return [e["name"] for e in entries if e["name"] not in SKIPPED_PROJECTS]


def compile_patterns(names: list[str]) -> list[tuple[str, re.Pattern]]:
    pats = list(PATTERNS)
    if names:
        alt = "|".join(re.escape(n) for n in names)
        pats.append(("project_name", rf"\b(?:{alt})\b"))
    return [(n, re.compile(p, re.IGNORECASE)) for n, p in pats]


def lint_file(path: Path, rel: str, pats) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER.match(text)
    offset = text[:m.end()].count("\n") if m else 0
    lines = text.splitlines()[offset:]

    def finding(line_no, check, snippet):
        return {"file": rel, "line": line_no, "check": check,
                "text": snippet.strip()}

    out = []
    if len(lines) > MAX_BODY_LINES:
        out.append(finding(1, "body_lines",
                           f"{len(lines)} body lines > {MAX_BODY_LINES}"))
    fence_open = None  # (line_no, info, content_count)
    for i, line in enumerate(lines, start=offset + 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            if fence_open is None:
                fence_open = [i, stripped[3:].strip().lower(), 0]
            else:
                start, info, count = fence_open
                if info in SCRIPT_FENCE_INFO and count > MAX_FENCE_LINES:
                    out.append(finding(
                        start, "long_fence", f"{count} lines in fence"))
                fence_open = None
        elif fence_open is not None:
            fence_open[2] += 1
            if "<<" in line:
                out.append(finding(i, "heredoc", line))
        for name, pat in pats:
            if pat.search(line):
                out.append(finding(i, name, line))
    return out


def skill_files(root: Path) -> list[Path]:
    skills = Path(root) / "skills"
    return sorted(skills.glob("*/SKILL.md")) + sorted(
        skills.glob("*/references/*.md"))


def lint(root: Path, projects_file: Path, paths: list[Path] | None = None):
    pats = compile_patterns(project_names(projects_file))
    files = paths if paths else skill_files(root)
    findings = []
    for f in files:
        f = Path(f)
        try:
            rel = str(f.relative_to(root))
        except ValueError:
            rel = str(f)
        findings += lint_file(f, rel, pats)
    summary: dict[str, int] = {}
    for f in findings:
        summary[f["check"]] = summary.get(f["check"], 0) + 1
    return {"files": len(files), "findings": findings, "summary": summary}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--root", type=Path,
                    default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--projects", type=Path, default=DEFAULT_PROJECTS)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = lint(args.root, args.projects, args.paths)
    for check, n in sorted(result["summary"].items()):
        log.info("%s: %d", check, n)
    log.info("%d files, %d findings", result["files"],
             len(result["findings"]))
    json.dump(result, sys.stdout, indent=1)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

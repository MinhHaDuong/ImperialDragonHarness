#!/usr/bin/env python3
"""Project directives that shadow the harness's (ticket 1230, yawn check 14).

    project_shadow.py PROJECT              JSON lines: findings or one skip
    project_shadow.py --is-harness PROJECT exit 0 if PROJECT is the harness or
                                           a linked worktree of it, else 1
    project_shadow.py --plan [--auto]      finding records on stdin -> one
                                           plan line each (ticket 1231, molt)

Mechanical half only: a local skill or rule named like a harness skill or
rule. Contradictions and repeated procedures are model judgment (yawn). One
finding per line, the record shared with the molt wiring (ticket 1231):
kind, local_file, harness_file, instruction, verdict (ok|warn), reason,
disposition (left null here: redundant versus deliberate is not mechanical),
destination. A skip is one line {"status": "skip", "reason": ...}.
Project skill roots come from adapters/pilot-support.json, per runtime.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parent.parent
FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
REASON = re.compile(r"\b(because|since|has no)\b", re.IGNORECASE)
REASON_LINES = 5  # a reason must sit within 5 lines of the opening, past the frontmatter
DIRECTIVE_FILES = ("CLAUDE.md", "AGENTS.md", ".claude/CLAUDE.md")


def git_common_dir(path: Path) -> str:
    out = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--path-format=absolute",
         "--git-common-dir"], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def is_harness(project: Path) -> bool:
    project = project.resolve()
    if project == HARNESS:
        return True
    theirs = git_common_dir(project)
    return bool(theirs) and theirs == git_common_dir(HARNESS)


def skill_roots() -> list[str]:
    data = json.loads((HARNESS / "adapters/pilot-support.json").read_text())
    roots: list[str] = []
    for entry in data["versions"]:
        for root in entry.get("project_skill_roots", []):
            if root not in roots:
                roots.append(root)
    return roots


def skill_dirs(root: Path):
    if root.is_dir():
        for sub in sorted(root.iterdir()):
            if (sub / "SKILL.md").is_file():
                yield sub


def harness_skills() -> dict[str, tuple[Path, str]]:
    from skill_frontmatter import FrontmatterError, load
    found = {}
    for sub in skill_dirs(HARNESS / "skills"):
        path = sub / "SKILL.md"
        try:
            desc = str(load(path).get("description", ""))
        except (FrontmatterError, OSError, UnicodeDecodeError):
            desc = ""
        found[sub.name] = (path, desc)
    return found


def reason_in(path: Path) -> str | None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None  # unreadable (broken link, permissions): silent, hence warn
    lines = FRONTMATTER.sub("", text, count=1).splitlines()
    for line in lines[:REASON_LINES]:
        if REASON.search(line):
            return line.strip()
    return None


def finding(local: Path, harness: Path, instruction: str) -> dict:
    reason = reason_in(local)
    return {"kind": "shadowing", "local_file": str(local),
            "harness_file": str(harness), "instruction": instruction,
            "verdict": "ok" if reason else "warn", "reason": reason,
            "disposition": None, "destination": "project"}


def scan(project: Path) -> list[dict]:
    from skill_frontmatter import FrontmatterError, load
    skills = harness_skills()
    local_dirs: list[Path] = []
    for rel in skill_roots() + ["skills"]:
        local_dirs.extend(skill_dirs(project / rel))
    rules_dir = project / ".claude/rules"
    local_rules = sorted(rules_dir.glob("*.md")) if rules_dir.is_dir() else []
    has_sources = bool(local_dirs or local_rules) or any(
        (project / f).is_file() for f in DIRECTIVE_FILES)
    if not has_sources:
        return [{"status": "skip",
                 "reason": "no local directives (no CLAUDE.md, AGENTS.md, "
                           "rules or skills)"}]
    records, seen = [], set()
    for sub in local_dirs:
        path = sub / "SKILL.md"
        names = {sub.name}
        try:
            names.add(str(load(path).get("name", sub.name)))
        except (FrontmatterError, OSError, UnicodeDecodeError):
            pass  # still judged by directory name
        hit = next((n for n in sorted(names) if n in skills), None)
        real = path.resolve()
        if hit and real not in seen:
            seen.add(real)
            records.append(finding(path, *skills[hit]))
    for path in local_rules:
        target = HARNESS / "rules" / path.name
        if target.is_file():
            records.append(finding(path, target,
                                   f"harness rule rules/{path.name}"))
    return records


def route(rec: dict, auto: bool) -> str | None:
    """One plan line for a record, or None: a reasoned (ok) finding is left
    alone. `auto` (unattended sweep) never files into the harness checkout."""
    if rec.get("status") == "skip":
        return f"skip: {rec.get('reason', '')}"
    if str(rec.get("verdict", "")).startswith("ok"):  # also "ok (reasoned)"
        return None
    local, kind = rec.get("local_file"), rec.get("kind")
    disp = rec.get("disposition")
    if disp == "delete-local":
        return f"fix-now: delete redundant local copy {local} ({kind})"
    if disp == "annotate":
        return f"fix-now: write the reason beside {local} ({kind})"
    if disp == "harness-ticket":
        what = f"general fix for {local} vs {rec.get('harness_file')} ({kind})"
        if auto:
            return f"report: harness-bound, not filed unattended: {what}"
        return (f"open-ticket: in the harness repo, on a harness branch, "
                f"never its main checkout: {what}")
    return f"skip: no disposition for {local} ({kind}); judge by hand"


def plan(argv: list[str]) -> int:
    lines = []
    for raw in sys.stdin:
        if not raw.strip():
            continue
        try:
            line = route(json.loads(raw), "--auto" in argv)
        except ValueError as exc:
            print(f"project_shadow --plan: bad record: {exc}", file=sys.stderr)
            return 1
        if line:
            lines.append(line)
    for line in lines:
        print(line)
    return 0


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    if len(argv) >= 2 and argv[1] == "--plan":
        return plan(argv[2:])
    if len(argv) == 3 and argv[1] == "--is-harness":
        return 0 if is_harness(Path(argv[2])) else 1
    if len(argv) != 2 or not Path(argv[1]).is_dir():
        print(__doc__, file=sys.stderr)
        return 2
    project = Path(argv[1]).resolve()
    if is_harness(project):
        records = [{"status": "skip",
                    "reason": "project is the harness (or a worktree of it); "
                              "the harness is not compared with itself"}]
    else:
        try:
            import skill_frontmatter  # noqa: F401  (needs PyYAML)
        except ImportError as exc:
            records = [{"status": "skip",
                        "reason": f"PyYAML unavailable ({exc}); install it "
                                  "to compare skill names"}]
        else:
            records = scan(project)
    for rec in records:
        print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

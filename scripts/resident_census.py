#!/usr/bin/env python3
"""What a session pays before its first question, across every channel.

``tests/test_rules_resident_budget.py`` capped ``rules/`` and nothing else,
because ``rules/`` was the channel whose mechanism had just been isolated. It
is not the only one: measured against ``/context``, the guarded set was 54% of
what the session actually carried. Three channels put text in front of the
model, and only one was watched:

* **auto-load** — the runtime walks ``rules/**.md`` and keeps every body whose
  frontmatter declares no ``paths:``.
* **import** — ``CLAUDE.md`` and, transitively, every ``@path`` line in it.
* **hook** — ``scripts/on-start.sh`` prints files, and hook stdout is context.

Two more are resident but not files-in-full: a skill and a subagent contribute
their ``name`` plus ``description``, never their body. That is the
pointer-and-payload split, and it is why 48 skills cost less than one rules
file. The bodies load on invocation and are not this module's business.

Only ONE project memory index is resident in a given session — its own — so
the channel totals below use the largest as the session upper bound, and the
per-index budget is what the guard ratchets. Summing all of them would
describe a session nobody runs.

A consumer project's own resident text — ``AGENTS.md``/``CLAUDE.md`` with
their ``@`` imports, and every unscoped or catch-all ``.claude/rules`` body —
is paid on top, per project. ``--project DIR`` measures it (0971); it is not a
harness channel, because the harness cannot gate a project, so the budget is
surfaced by the SessionStart coherence prompt rather than tested here.

**Tokens here are derived, not measured.** This module counts characters,
which is exact. ``/context`` reports tokens per category, which is the only
token measurement available without the API's ``count_tokens``; dividing one
by the other on 2026-09-10 gave 2.76 chars/token over the memory-files channel
and 2.98 over the skills channel — two independent categories agreeing, which
is the only reason a single constant is defensible at all. It is 45% worse
than the chars/4 rule of thumb that the README and this repo's own budget
message used, because backticked identifiers and paths tokenize badly. Treat
the token column as an order of magnitude and re-derive it when ``/context``
disagrees; the character counts are the contract.
"""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import skill_frontmatter

# Derived 2026-09-10 from /context, see module docstring. Not a measurement.
CHARS_PER_TOKEN = 2.8

IMPORT_LINE = re.compile(r"^@(\S+)", re.MULTILINE)

# Files scripts/on-start.sh prints into the session. Kept as a literal list
# rather than parsed out of the shell: a regex over a hook script that stops
# matching reports "no hook channel" and "I could not read the hook" with the
# same silence, and this guard exists because that class of blind spot is what
# left three channels unwatched.
HOOK_INJECTED = ("memory/MEMORY.md",)

CHANNELS = ("rules", "import", "hook", "memory", "skills", "agents")


@dataclass(frozen=True)
class Entry:
    """One resident item: which channel carries it, and what it costs."""

    channel: str
    path: str
    chars: int

    @property
    def tokens(self) -> int:
        return round(self.chars / CHARS_PER_TOKEN)


def repo_root(explicit: str | None = None) -> Path:
    """The harness checkout to measure.

    Resolved from this file, never from ``git rev-parse`` at import time: in a
    worktree the latter answers with the worktree and the module then measures
    whichever tree it happens to sit in.
    """
    return Path(explicit).resolve() if explicit else Path(__file__).resolve().parents[1]


# Globs that match every file a session could touch. A body scoped to one of
# them is resident in all but name: climate-finance-het's architecture.md
# (``paths: "**/*"``, 20 560 chars) loaded on every session unwatched (0971).
CATCH_ALL_GLOBS = frozenset({"**", "**/*", "*", "**/*.*", "./**", "./**/*"})

# Project channel budget, chars. A starting point to ratchet from, not a
# measured optimum (0971): about a third of the harness's own rules cap.
PROJECT_BUDGET = 12000


def rule_globs(path: Path) -> list[str] | None:
    """The ``paths:`` globs of a rule body, or None when it declares none."""
    m = skill_frontmatter.FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not (m and re.search(r"^paths:", m.group(1), re.MULTILINE)):
        return None
    try:
        value = skill_frontmatter.load(path).get("paths")
    except skill_frontmatter.FrontmatterError:
        # Declared but unparseable: count it resident, the safe direction for
        # a budget, rather than let a YAML slip hide a body from the census.
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value or []]


def is_catch_all(path: Path) -> bool:
    globs = rule_globs(path)
    return globs is not None and any(g.strip() in CATCH_ALL_GLOBS for g in globs)


def is_auto_loaded(path: Path) -> bool:
    """True when the runtime loads this rule body on every session.

    The rule is the frontmatter's ``paths:`` key: with it the body arrives only
    when a matching file is touched, without it the body is always in context.
    A catch-all glob, or a ``paths:`` that does not parse, counts as resident.
    """
    globs = rule_globs(path)
    return not globs or is_catch_all(path)


def rules_entries(root: Path) -> list[Entry]:
    rules = root / "rules"
    return [
        Entry("rules", str(p.relative_to(root)), len(p.read_text(encoding="utf-8")))
        for p in sorted(rules.rglob("*.md"))
        if is_auto_loaded(p)
    ]


def import_entries(
    root: Path, starts: tuple[str, ...] = ("CLAUDE.md",), channel: str = "import"
) -> list[Entry]:
    """The start files and everything their ``@`` lines pull in, transitively."""
    out: list[Entry] = []
    seen: set[Path] = set()
    queue = [(root / start).resolve() for start in starts]
    while queue:
        path = queue.pop(0)
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        text = path.read_text(encoding="utf-8")
        out.append(Entry(channel, _rel(path, root), len(text)))
        queue.extend((root / target).resolve() for target in IMPORT_LINE.findall(text))
    return sorted(out, key=lambda e: e.path)


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root.resolve()))
    except ValueError:  # an @import reaching outside the checkout
        return str(path)


def hook_entries(root: Path) -> list[Entry]:
    return [
        Entry("hook", name, len((root / name).read_text(encoding="utf-8")))
        for name in HOOK_INJECTED
        if (root / name).is_file()
    ]


def memory_entries(root: Path) -> list[Entry]:
    """One per project. Only the session's own project index is resident."""
    return [
        Entry("memory", str(p.relative_to(root)), len(p.read_text(encoding="utf-8")))
        for p in sorted((root / "projects").glob("*/memory/MEMORY.md"))
    ]


def _name_and_description(path: Path) -> int:
    """What a skill or subagent costs resident: its frontmatter card, not its body."""
    fm = skill_frontmatter.load(path)
    return len(str(fm.get("name", ""))) + len(str(fm.get("description", "")))


def skill_entries(root: Path) -> list[Entry]:
    return [
        Entry("skills", str(p.relative_to(root)), _name_and_description(p))
        for p in sorted((root / "skills").glob("*/SKILL.md"))
    ]


def agent_entries(root: Path) -> list[Entry]:
    return [
        Entry("agents", str(p.relative_to(root)), _name_and_description(p))
        for p in sorted((root / "agents").glob("*.md"))
    ]


def project_entries(project: Path) -> list[Entry]:
    """What a consumer project adds to every session in it (0971)."""
    project = project.resolve()
    out = import_entries(
        project, ("AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md"), channel="project"
    )
    rules = project / ".claude" / "rules"
    if rules.is_dir():
        out += [
            Entry("project", _rel(p, project), len(p.read_text(encoding="utf-8")))
            for p in sorted(rules.rglob("*.md"))
            if is_auto_loaded(p)
        ]
    return out


def catch_all_rules(project: Path) -> list[str]:
    rules = project.resolve() / ".claude" / "rules"
    if not rules.is_dir():
        return []
    return [_rel(p, project.resolve()) for p in sorted(rules.rglob("*.md")) if is_catch_all(p)]


def project_warning(project: Path, budget: int = PROJECT_BUDGET) -> str | None:
    """One declarative line for the startup prompt, or None when all is well.

    Declarative on purpose: hook output phrased as an order is read as prompt
    injection and discounted (``rules/claude-code.md`` § Hook output).
    """
    entries = project_entries(project)
    total = sum(e.chars for e in entries)
    wide = catch_all_rules(project)
    if total <= budget and not wide:
        return None
    top = ", ".join(
        f"{e.path} ({e.chars})" for e in sorted(entries, key=lambda e: -e.chars)[:3]
    )
    parts = [
        f"PROJECT RESIDENT TEXT: this project adds {total} chars to every session "
        f"(budget {budget}); largest: {top}."
    ]
    if wide:
        parts.append(
            f" A catch-all `paths:` makes {', '.join(wide)} resident in all but name."
        )
    parts.append(
        " The harness scoping rule applies to project rules too: a body triggered"
        " by a path is scoped to that path, one triggered by a task is a skill."
    )
    return "".join(parts)


def census(root: Path) -> list[Entry]:
    """Every resident item in the checkout, in channel order."""
    return [
        *rules_entries(root),
        *import_entries(root),
        *hook_entries(root),
        *memory_entries(root),
        *skill_entries(root),
        *agent_entries(root),
    ]


def channel_chars(entries: list[Entry]) -> dict[str, int]:
    """Per-channel totals. ``memory`` is the largest index, not their sum."""
    totals = {c: 0 for c in CHANNELS}
    for e in entries:
        if e.channel == "memory":
            totals["memory"] = max(totals["memory"], e.chars)
        else:
            totals[e.channel] += e.chars
    return totals


def session_chars(entries: list[Entry]) -> int:
    """Upper bound for one session: every channel, worst project memory index."""
    return sum(channel_chars(entries).values())


def _render(entries: list[Entry], detail: bool) -> str:
    lines = []
    totals = channel_chars(entries)
    if detail:
        for channel in CHANNELS:
            rows = sorted(
                (e for e in entries if e.channel == channel),
                key=lambda e: -e.chars,
            )
            if not rows:
                continue
            note = "  (largest is the resident one)" if channel == "memory" else ""
            lines.append(f"\n{channel}{note}")
            for e in rows:
                lines.append(f"  {e.chars:7d} chars  ~{e.tokens:6d} tok  {e.path}")
    lines.append("")
    lines.append(f"{'channel':<10} {'chars':>8} {'~tokens':>9}")
    for channel in CHANNELS:
        chars = totals[channel]
        lines.append(f"{channel:<10} {chars:8d} {round(chars / CHARS_PER_TOKEN):9d}")
    total = session_chars(entries)
    lines.append(f"{'TOTAL':<10} {total:8d} {round(total / CHARS_PER_TOKEN):9d}")
    lines.append("")
    lines.append(
        f"Tokens derived at {CHARS_PER_TOKEN} chars/token, not measured — see "
        "the module docstring. A consumer project's own CLAUDE.md is extra."
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", nargs="?", help="harness checkout (default: this one)")
    parser.add_argument(
        "--detail", action="store_true", help="list every file, not just channel totals"
    )
    parser.add_argument(
        "--project", metavar="DIR", help="measure a consumer project's resident text"
    )
    parser.add_argument(
        "--warn",
        action="store_true",
        help="with --project: print only the startup warning line, if any",
    )
    args = parser.parse_args(argv)
    if args.project:
        project = Path(args.project)
        if args.warn:
            line = project_warning(project)
            if line:
                print(line)
            return 0
        entries = project_entries(project)
        for e in sorted(entries, key=lambda e: -e.chars):
            flag = "  catch-all" if e.path in catch_all_rules(project) else ""
            print(f"{e.chars:7d} chars  ~{e.tokens:6d} tok  {e.path}{flag}")
        total = sum(e.chars for e in entries)
        print(f"{'TOTAL':>7} {total} chars (budget {PROJECT_BUDGET})")
        return 0
    print(_render(census(repo_root(args.root)), args.detail))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

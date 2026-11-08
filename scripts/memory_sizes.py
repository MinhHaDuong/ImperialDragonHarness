#!/usr/bin/env python3
"""Report memory topic sizes against the byte cap (ticket 1348).

The definitions live in skills/smelt/references/consolidation.md § Job of a
topic and caps. A page is
measured in UTF-8 bytes over every H2 section except `Sources`
(the title and any text before the first H2 count). The user-rulings page is
never cut to fit: over the cap it is reported and does not fail the check.

Usage: memory_sizes.py [topics_dir] [--before DIR_OR_GIT_REF]
(default dir: this harness's memory/topics). With --before, also print the net
change per page against that directory or git ref (ticket 1349: a smelt is a
rebuild and reports it); a page that grew needs a reason in the report. A git
ref resolves in the repository holding topics_dir, so the helper runs from the
harness against any project (ticket 1451).
Exit 1 when a non-user-rulings page is over the cap.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

CAP = 4096  # bytes per topic page
INDEX_LINES = 40  # lines in memory/MEMORY.md, blanks counted
USER_RULINGS = "user-rulings.md"
OUTSIDE = {"sources"}


def guide_bytes(text: str) -> int:
    """UTF-8 bytes of the page minus its Sources section."""
    kept, skipping = [], False
    for line in text.splitlines(keepends=True):
        if line.startswith("## "):
            skipping = line[3:].strip().lower() in OUTSIDE
        if not skipping:
            kept.append(line)
    return len("".join(kept).encode("utf-8"))


def index_ok(text: str) -> bool:
    return len(text.splitlines()) <= INDEX_LINES


def report(topics_dir: Path):
    """Yield (name, bytes, cap, status) for each topic page, status OK or OVER."""
    for path in sorted(Path(topics_dir).glob("*.md")):
        size = guide_bytes(path.read_text(encoding="utf-8"))
        yield path.name, size, CAP, "OK" if size <= CAP else "OVER"


def sizes(topics_dir: Path) -> dict[str, int]:
    return {n: b for n, b, _c, _s in report(topics_dir)}


def net_change(before: Path, after: Path):
    """Yield (name, before_bytes, after_bytes, delta, reason_required).

    A page missing on one side counts 0 there. reason_required is True when
    the page grew (delta > 0).
    """
    old, new = sizes(before), sizes(after)
    for name in sorted(set(old) | set(new)):
        b, a = old.get(name, 0), new.get(name, 0)
        yield name, b, a, a - b, a > b


def _checkout_ref(ref: str, topics_dir: Path, dest: Path) -> Path:
    """Materialize topics_dir as it stood at a git ref of its own repository
    into dest (read-only plumbing)."""
    try:
        names = subprocess.run(
            ["git", "-C", str(topics_dir), "ls-tree", "-z", "--full-tree", "--name-only", f"{ref}:./"],
            check=True, capture_output=True, text=True,
        ).stdout.split("\0")
        names = [name for name in names if name]
    except subprocess.CalledProcessError as exc:
        sys.exit(f"memory_sizes: --before {ref!r} is neither a directory nor a git ref holding {topics_dir}: {exc.stderr.strip()}")
    for name in names:
        blob = subprocess.run(
            ["git", "-C", str(topics_dir), "show", f"{ref}:./{name}"],
            check=True, capture_output=True,
        ).stdout
        (dest / name).write_bytes(blob)
    return dest


def print_net(before: Path, after: Path) -> None:
    total = 0
    for name, b, a, delta, grew in net_change(before, after):
        total += delta
        note = "  reason required" if grew else ""
        print(f"{name:42} {b:6} -> {a:6}  net {delta:+d}{note}")
    print(f"{'total':42} net {total:+d}")


def main(topics_dir: Path | None = None, before: Path | None = None) -> int:
    if topics_dir is None:
        topics_dir = Path(__file__).resolve().parents[1] / "memory" / "topics"
    failed = False
    for name, size, cap, status in report(topics_dir):
        note = ""
        if status == "OVER" and name == USER_RULINGS:
            note = " (register exceeds byte budget)"
        elif status == "OVER":
            failed = True
        print(f"{name:42} {size:6} / {cap}  {status}{note}")
    if before is not None:
        print_net(before, topics_dir)
    return 1 if failed else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    ref = None
    if "--before" in args:
        i = args.index("--before")
        ref = args[i + 1]
        del args[i : i + 2]
    topics = Path(args[0]) if args else Path(__file__).resolve().parents[1] / "memory" / "topics"
    if ref is None:
        sys.exit(main(topics))
    path = Path(ref)
    if path.is_dir():
        sys.exit(main(topics, before=path))
    with tempfile.TemporaryDirectory() as tmp:
        sys.exit(main(topics, before=_checkout_ref(ref, topics, Path(tmp))))

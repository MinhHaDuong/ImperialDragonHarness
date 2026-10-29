#!/usr/bin/env python3
"""Report memory topic sizes against the byte cap (ticket 1348).

The definitions live in memory/SMELT.md § Job of a topic and caps. A page is
measured in UTF-8 bytes over every H2 section except `Retired` and `Sources`
(the title and any text before the first H2 count). The Commission page is
never cut to fit: over the cap it is reported and does not fail the check.

Usage: memory_sizes.py [topics_dir] [--before DIR_OR_GIT_REF]
(default dir: memory/topics). With --before, also print the net change per
page against that directory or git ref (ticket 1349: a smelt is a rebuild and
reports it); a page that grew needs a reason in the report.
Exit 1 when a non-Commission page is over the cap.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

CAP = 4096  # bytes per topic page
INDEX_LINES = 40  # lines in memory/MEMORY.md, blanks counted
COMMISSION = "commission.md"  # provisional name, ticket 1349 may rename it
OUTSIDE = {"retired", "sources"}


def guide_bytes(text: str) -> int:
    """UTF-8 bytes of the page minus its Retired and Sources sections."""
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


def _checkout_ref(ref: str, repo: Path, dest: Path) -> Path:
    """Materialize memory/topics at a git ref into dest (read-only plumbing)."""
    try:
        names = subprocess.run(
            ["git", "-C", str(repo), "ls-tree", "--name-only", f"{ref}:memory/topics"],
            check=True, capture_output=True, text=True,
        ).stdout.split()
    except subprocess.CalledProcessError as exc:
        sys.exit(f"memory_sizes: --before {ref!r} is neither a directory nor a git ref with memory/topics: {exc.stderr.strip()}")
    for name in names:
        blob = subprocess.run(
            ["git", "-C", str(repo), "show", f"{ref}:memory/topics/{name}"],
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
        if status == "OVER" and name == COMMISSION:
            note = " (promote to rules, brood 1351)"
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
    topics = Path(args[0]) if args else None
    if ref is None:
        sys.exit(main(topics))
    path = Path(ref)
    if path.is_dir():
        sys.exit(main(topics, before=path))
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(__file__).resolve().parents[1]
        sys.exit(main(topics, before=_checkout_ref(ref, repo, Path(tmp))))

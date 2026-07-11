#!/usr/bin/env python3
"""
Provenance tracking and promotion/decay helpers for /dream v2.
Pure I/O — no LLM calls, no Anthropic imports.

Manages ~/.claude/memory/.provenance.json which tracks:
- Per-entry metadata: originating projects, first_seen, last_confirmed
- Promotion status
- Decay candidates (>90 days unconfirmed)
"""

import argparse
import fcntl
import json
import os
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HARNESS_MEMORY = Path.home() / ".claude" / "memory"
PROVENANCE_PATH = HARNESS_MEMORY / ".provenance.json"
PROVENANCE_LOCK = HARNESS_MEMORY / ".provenance.lock"
PROJECTS_BASE = Path.home() / ".claude" / "projects"
DECAY_DAYS = 90

# Test-only hook: seconds to sleep between read and write inside a locked
# mutation, used to force critical-section overlap in the lost-write race test.
# Unset in production. See tests/test_dream.py::test_provenance_concurrent_record_*.
_TEST_DELAY_ENV = "DREAM_PROVENANCE_TEST_DELAY"

# Test-only hook: seconds to sleep mid-write — after the full content is staged
# in the temp file but before os.replace publishes it. Lets the torn-read test
# land a reader inside the write window. In the atomic implementation the live
# file is still the intact old document here, so a reader sees old-or-new but
# never a tear. Unset in production.
# See tests/test_dream.py::test_provenance_read_during_write_never_torn.
_WRITE_DELAY_ENV = "DREAM_PROVENANCE_WRITE_DELAY"


@contextmanager
def _provenance_lock():
    """Serialize the read-modify-write cycle across concurrent processes.

    The cron recipe fires /dream for all projects at 02:00; each consolidation
    issues an unlocked read-modify-write against the shared .provenance.json,
    so concurrent runs could clobber each other (ticket 0224). We hold an
    advisory flock on a sidecar lock file — not on the json itself, whose
    write_text truncation would fight a lock held on the same fd. flock
    auto-releases on fd close / process exit, so a crashed run leaves no stale
    lock (unlike an O_EXCL lockfile)."""
    PROVENANCE_LOCK.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(PROVENANCE_LOCK, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _load_provenance() -> dict:
    if PROVENANCE_PATH.exists():
        return json.loads(PROVENANCE_PATH.read_text())
    return {"entries": {}}


def _save_provenance(data: dict) -> None:
    """Atomically replace the provenance file.

    Readers take no lock and load lock-free (ticket 0225), so the write must be
    all-or-nothing: a non-atomic write_text truncates then writes, exposing a
    window where a concurrent reader sees a partial file and raises
    JSONDecodeError. We stage the full content in a temp file in the same
    directory (same filesystem — os.replace requires it), then os.replace onto
    the live path. The rename is atomic, so a reader always observes the
    complete old-or-new document, never a tear — without serializing readers
    against writers."""
    PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=2) + "\n"
    fd, tmp = tempfile.mkstemp(
        dir=PROVENANCE_PATH.parent, prefix=".provenance.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        _write_delay()
        os.replace(tmp, PROVENANCE_PATH)
    except BaseException:
        # Leave no orphan temp file if staging or replace fails.
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise


def _test_delay() -> None:
    """Sleep between read and write when the test hook is set (no-op in prod)."""
    delay = os.environ.get(_TEST_DELAY_ENV)
    if delay:
        time.sleep(float(delay))


def _write_delay() -> None:
    """Sleep mid-write when the write hook is set (no-op in prod)."""
    delay = os.environ.get(_WRITE_DELAY_ENV)
    if delay:
        time.sleep(float(delay))


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record(args):
    """Record that an entry was seen in a project consolidation."""
    slug = args.slug
    project = args.project
    with _provenance_lock():
        data = _load_provenance()
        entries = data["entries"]
        _test_delay()
        now = _now_iso()

        if slug not in entries:
            entries[slug] = {
                "projects": [project],
                "first_seen": now,
                "last_confirmed": now,
                "promoted": False,
            }
        else:
            entry = entries[slug]
            if project not in entry["projects"]:
                entry["projects"].append(project)
            entry["last_confirmed"] = now

        _save_provenance(data)
        result = entries[slug]
    print(json.dumps(result, indent=2))


def remove(args):
    """Drop a project from an entry's provenance when the entry is DELETEd.

    A consolidation that classifies an entry DELETE tombstones its file but,
    without this, leaves the slug in the provenance store — so the dead entry
    keeps counting toward the >=2-project promotion frequency gate (ticket
    0241). `remove` drops the named project from the slug's list. When the list
    empties the entry is deleted, UNLESS it is promoted: promotion is one-way,
    a harness-level entry has earned status independent of its origin projects,
    so it survives with an empty project list."""
    slug = args.slug
    project = args.project
    with _provenance_lock():
        data = _load_provenance()
        entries = data["entries"]
        if slug not in entries:
            print(f"Unknown entry: {slug}", file=sys.stderr)
            sys.exit(1)
        _test_delay()
        entry = entries[slug]
        if project in entry["projects"]:
            entry["projects"].remove(project)
        deleted = not entry["projects"] and not entry.get("promoted")
        if deleted:
            del entries[slug]
        _save_provenance(data)
        result = {"removed": slug} if deleted else entries[slug]
    print(json.dumps(result, indent=2))


def confirm(args):
    """Refresh last_confirmed on a promoted entry.

    Closes the decay-confirmation gap (ticket 0224): once an entry is promoted,
    its project-level copy is tombstoned, so later consolidations no longer
    `record` the slug and last_confirmed never refreshes — every promoted entry
    decay-flags at 90 days regardless of continued relevance. When a later
    consolidation finds a promoted harness entry still supported by the
    project's content, it calls `confirm` to refresh the timestamp. Unlike
    `record`, this does not mutate the project list (the harness entry has no
    project of origin to append)."""
    slug = args.slug
    with _provenance_lock():
        data = _load_provenance()
        entries = data["entries"]
        if slug not in entries:
            print(f"Unknown entry: {slug}", file=sys.stderr)
            sys.exit(1)
        if not entries[slug].get("promoted"):
            print(f"Not a promoted entry: {slug}", file=sys.stderr)
            sys.exit(1)
        _test_delay()
        entries[slug]["last_confirmed"] = _now_iso()
        _save_provenance(data)
        result = entries[slug]
    print(json.dumps(result, indent=2))


def candidates(args):
    """List promotion candidates: entries seen in >=2 distinct projects, not yet promoted."""
    data = _load_provenance()
    result = []
    for slug, entry in data["entries"].items():
        if len(entry["projects"]) >= 2 and not entry["promoted"]:
            result.append({"slug": slug, **entry})
    json.dump(result, sys.stdout, indent=2)
    print()


def promote(args):
    """Mark an entry as promoted."""
    slug = args.slug
    with _provenance_lock():
        data = _load_provenance()
        if slug not in data["entries"]:
            print(f"Unknown entry: {slug}", file=sys.stderr)
            sys.exit(1)
        _test_delay()
        data["entries"][slug]["promoted"] = True
        data["entries"][slug]["promoted_at"] = _now_iso()
        _save_provenance(data)
    print(f"Promoted: {slug}")


def decay(args):
    """List harness entries not confirmed in DECAY_DAYS days."""
    data = _load_provenance()
    now = datetime.now(timezone.utc)
    flagged = []
    for slug, entry in data["entries"].items():
        if not entry.get("promoted"):
            continue
        last = datetime.fromisoformat(entry["last_confirmed"].replace("Z", "+00:00"))
        age_days = (now - last).days
        if age_days > DECAY_DAYS:
            flagged.append({
                "slug": slug,
                "last_confirmed": entry["last_confirmed"],
                "age_days": age_days,
                "projects": entry["projects"],
            })
    json.dump(flagged, sys.stdout, indent=2)
    print()


def show(args):
    """Show full provenance data."""
    data = _load_provenance()
    json.dump(data, sys.stdout, indent=2)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Provenance tracking for /dream memory promotion and decay."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    record_p = sub.add_parser("record", help="Record entry seen in a project.")
    record_p.add_argument("slug", help="Stable entry identifier (e.g. feedback_vim)")
    record_p.add_argument("project", help="Project directory name")
    record_p.set_defaults(func=record)

    remove_p = sub.add_parser(
        "remove", help="Drop a project from an entry (DELETE cleanup)."
    )
    remove_p.add_argument("slug", help="Stable entry identifier (e.g. feedback_vim)")
    remove_p.add_argument("project", help="Project directory name to drop")
    remove_p.set_defaults(func=remove)

    candidates_p = sub.add_parser(
        "candidates", help="List promotion candidates (>=2 projects, not promoted)."
    )
    candidates_p.set_defaults(func=candidates)

    promote_p = sub.add_parser("promote", help="Mark entry as promoted to harness.")
    promote_p.add_argument("slug", help="Entry slug to promote")
    promote_p.set_defaults(func=promote)

    confirm_p = sub.add_parser(
        "confirm", help="Refresh last_confirmed on a promoted entry (resets decay clock)."
    )
    confirm_p.add_argument("slug", help="Promoted entry slug still relevant")
    confirm_p.set_defaults(func=confirm)

    decay_p = sub.add_parser(
        "decay", help=f"List promoted entries unconfirmed for >{DECAY_DAYS} days."
    )
    decay_p.set_defaults(func=decay)

    show_p = sub.add_parser("show", help="Show full provenance data.")
    show_p.set_defaults(func=show)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

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
import re
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HARNESS_MEMORY = Path.home() / ".claude" / "memory"
PROVENANCE_PATH = HARNESS_MEMORY / ".provenance.json"
PROVENANCE_LOCK = HARNESS_MEMORY / ".provenance.lock"
PROJECT_ALIASES_PATH = HARNESS_MEMORY / ".project-aliases.json"
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


def _load_aliases() -> dict:
    """Map alias project-slug -> canonical project-slug (empty when absent).

    Project keys in the provenance store are Claude-Code directory *slugs*
    (e.g. `-home-haduong-CNRS-papiers-actif-AEDIST-technical-report`), not
    filesystem paths, so `os.path.realpath` cannot collapse aliases: slug->path
    inversion is ambiguous and a relocated tree's old path no longer exists on
    disk. Instead we keep an explicit, read-time alias table (ticket 0270). A
    missing table is the common case — no aliases — and yields {}. A corrupt
    table degrades to 'no aliases' with a stderr warning rather than crashing
    the caller (ticket 0282): candidates then gates on raw keys, which can
    only over-count — it never wrongly suppresses a candidate."""
    if not PROJECT_ALIASES_PATH.exists():
        return {}
    try:
        table = json.loads(PROJECT_ALIASES_PATH.read_text())
    except json.JSONDecodeError as e:
        reason = str(e)
    else:
        # Valid JSON of the wrong shape (a scalar, a list, or a dict with
        # non-string keys/values) parses cleanly but crashes
        # _canonical_project downstream (`current in aliases` on an int, a
        # non-str value fed back into the loop). Validate the slug->slug string
        # contract and degrade to 'no aliases' identically (ticket 0279).
        if isinstance(table, dict) and all(
            isinstance(k, str) and isinstance(v, str) for k, v in table.items()
        ):
            return table
        reason = "expected an object mapping string slugs to string slugs"
    print(
        f"Warning: malformed alias table {PROJECT_ALIASES_PATH}: {reason} — "
        "treating as empty",
        file=sys.stderr,
    )
    return {}


def _canonical_project(project: str, aliases: dict) -> str:
    """Resolve an alias project-slug to its canonical slug; identity otherwise.

    Follows chained aliases ({old->mid, mid->canonical}) to a fixpoint so a
    multi-hop table collapses fully. A visited-set guards against a cyclic table
    looping forever: on a cycle we stop and return the last resolved slug, which
    keeps the result deterministic (ticket 0270 reroll)."""
    seen = {project}
    current = project
    while current in aliases:
        nxt = aliases[current]
        if nxt in seen:
            return current
        seen.add(nxt)
        current = nxt
    return current


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
    so it survives with an empty project list.

    An unknown slug is an idempotent no-op ({"removed": null}, exit 0), mirroring
    `record`'s upsert semantics: SKILL.md step 5 calls `remove` unconditionally on
    every DELETE, but the provenance store is not synced with MEMORY.md by
    construction (it postdates much of the corpus — 37% of live entries have no
    record), so "nothing to remove" is the correct outcome, not a failure that
    would abort the consolidation on the first DELETE of an untracked entry."""
    slug = args.slug
    project = args.project
    with _provenance_lock():
        data = _load_provenance()
        entries = data["entries"]
        if slug not in entries:
            print(json.dumps({"removed": None}, indent=2))
            return
        _test_delay()
        entry = entries[slug]
        changed = False
        if project in entry["projects"]:
            entry["projects"].remove(project)
            changed = True
        deleted = not entry["projects"] and not entry.get("promoted")
        if deleted:
            del entries[slug]
        if changed or deleted:
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
    aliases = _load_aliases()
    result = []
    for slug, entry in data["entries"].items():
        # Count distinct *canonical* projects: two path-spellings of one project
        # (a relocated/symlinked tree registered under two slugs) must count once,
        # else the frequency gate promotes a single-project note (ticket 0270).
        canonical = {_canonical_project(p, aliases) for p in entry["projects"]}
        if len(canonical) >= 2 and not entry["promoted"]:
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


def _retarget(root: Path) -> None:
    """Point the module at another checkout.

    Every path here is a module global resolved from ``Path.home()``, which is
    why `/dream` cannot run in a worktree (SKILL.md step 8): its writes would
    land on the primary checkout's current branch. `backfill` and `usage` both
    read the whole corpus and write one file, so they take ``--root`` and
    retarget instead — a worktree session can then run them against its own
    copy and land the result through its branch.
    """
    global HARNESS_MEMORY, PROVENANCE_PATH, PROVENANCE_LOCK
    global PROJECT_ALIASES_PATH, PROJECTS_BASE
    HARNESS_MEMORY = root / "memory"
    PROVENANCE_PATH = HARNESS_MEMORY / ".provenance.json"
    PROVENANCE_LOCK = HARNESS_MEMORY / ".provenance.lock"
    PROJECT_ALIASES_PATH = HARNESS_MEMORY / ".project-aliases.json"
    PROJECTS_BASE = root / "projects"


def _bodies_in(memdir: Path, project: str | None):
    """Yield (project, slug, path) for the non-tombstone bodies of one directory."""
    for body in sorted(memdir.glob("*.md")):
        if body.name == "MEMORY.md":
            continue
        head = body.read_text(encoding="utf-8", errors="replace")[:200].lstrip()
        if head.startswith("# DELETED"):
            continue
        yield project, body.stem, body


def live_bodies(root: Path):
    """Yield (project, slug, path) for every live memory body, both tiers.

    The live corpus is the set the provenance store is supposed to cover, and it
    has two tiers: the per-project bodies, and the promoted ones in the harness
    ``memory/`` directory. ``project`` is None for the harness tier, which has
    no originating project of its own.

    Walking only ``projects/`` is the blind spot this whole file exists to
    close, and the first version of it had exactly that shape: it left
    `reference_branch_cleanup_incidents` — a promoted, harness-level entry —
    with no record at all, invisible to the gate meant to catch invisibility.

    A tombstone is excluded because `remove` has already dropped it, and
    ``MEMORY.md`` is the index rather than an entry.
    """
    for memdir in sorted((root / "projects").glob("*/memory")):
        yield from _bodies_in(memdir, memdir.parent.name)
    harness = root / "memory"
    if harness.is_dir():
        yield from _bodies_in(harness, None)


def _to_z(iso: str) -> str:
    """Normalise a git ISO timestamp to the store's trailing-Z UTC form."""
    dt = datetime.fromisoformat(iso).astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _git_dates(root: Path, prefix: str) -> dict[str, tuple[str, str]]:
    """repo-relative path -> (first commit, last commit), both ISO-Z.

    One `git log` pass rather than a call per file: the corpus is ~950 bodies
    and a call each is minutes of subprocess churn for data one traversal
    already carries.

    A backfilled entry must not claim it was confirmed today. Stamping ``now``
    would reset every decay clock at the moment the clock is first wired up,
    which is the one thing that would make the backfill worse than the gap it
    closes. Git holds the honest dates, so they come from there.
    """
    proc = subprocess.run(
        ["git", "-C", str(root), "log", "--format=%x00%cI", "--name-only",
         "--diff-filter=AMR", "--", prefix],
        capture_output=True, text=True, check=False,
    )
    first: dict[str, str] = {}
    last: dict[str, str] = {}
    stamp = ""
    for line in proc.stdout.splitlines():
        if line.startswith("\x00"):
            stamp = line[1:]
        elif line and stamp:
            last.setdefault(line, stamp)  # log is newest-first
            first[line] = stamp
    return {p: (_to_z(first[p]), _to_z(last[p])) for p in first}


def backfill(args):
    """Record every live body the provenance store never saw.

    v2 introduced the store; the bodies written before it were never recorded,
    and nothing since has swept for them. An unrecorded entry is invisible to
    promotion, to decay and to dedup at once — and invisible in the way that
    reads as healthy, since every one of those passes reports success over the
    entries it can see.

    Idempotent, and deliberately conservative on the one field that matters:
    an already-tracked entry gaining a project has the project appended and its
    ``last_confirmed`` left alone.
    """
    root = Path(args.root).expanduser()
    _retarget(root)
    dates = _git_dates(root, ".")
    created = linked = untouched = 0
    with _provenance_lock():
        data = _load_provenance()
        entries = data["entries"]
        for project, slug, path in live_bodies(root):
            rel = str(path.relative_to(root))
            first, last = dates.get(rel, (_now_iso(), _now_iso()))
            entry = entries.get(slug)
            if entry is None:
                # A body living in the harness tier *is* a promoted entry, and
                # it has no originating project — the same shape `remove`
                # already documents for a promoted entry whose projects have all
                # dropped away. Inventing a project for it would corrupt the
                # >=2-project frequency gate promotion runs on.
                entries[slug] = {
                    "projects": [] if project is None else [project],
                    "first_seen": first,
                    "last_confirmed": last,
                    "promoted": project is None,
                    "backfilled": True,
                }
                created += 1
            elif project is not None and project not in entry["projects"]:
                entry["projects"].append(project)
                linked += 1
            else:
                untouched += 1
        if not args.dry_run:
            _save_provenance(data)
    print(json.dumps({
        "created": created,
        "linked": linked,
        "already_recorded": untouched,
        "tracked_total": len(entries),
        "dry_run": bool(args.dry_run),
    }, indent=2))


# A slug reached through a shell call carries no file_path, so both channels are
# scanned. Shape matches scripts/census/memory-recall.py, which reports the same
# events rather than storing them; if a third consumer appears, factor this out.
_TU_READ = re.compile(
    rb'"name":\s*"Read"\s*,\s*"input":\s*\{(?:[^{}]|\{[^{}]*\}){0,600}?'
    rb'"file_path":\s*"([^"]{0,300})"'
)
_BASH = re.compile(rb'"name":\s*"Bash"\s*,\s*"input":\s*\{\s*"command":\s*"((?:[^"\\]|\\.){0,4000})"')
# Anchored on the two directories that actually hold memory bodies. A bare
# `memory/<name>.md` also matches `skills/memory/SKILL.md`, which put the memory
# *skill* into the counts at 19 reads on the first run — a slug that does not
# exist, so nothing was corrupted, but a count that is wrong is wrong whether or
# not it lands anywhere.
_MEM_PATH = re.compile(r"(?:projects/[^/\s\"]+|\.claude)/memory/([A-Za-z0-9_.-]+)\.md")


def usage(args):
    """Fold observed read counts into the store, as a floor and never a truth.

    Session traces are already an append-only access log, so counting reads
    needs no new writes to the bodies themselves — which is what an in-file
    access log would cost, on the very files parallel sessions read.

    Two properties to keep in view wherever this number is used:

    - It is machine-local and traces are prunable, so it is a floor.
    - It counts *opens*. An entry whose index title carried the lesson is never
      opened, so a ranking that evicts on this number evicts the entries that
      worked best. Secondary signal only.
    """
    root = Path(args.root).expanduser()
    _retarget(root)
    traces = Path(args.traces).expanduser()
    counts: dict[str, int] = {}
    seen_days: dict[str, str] = {}
    ts = re.compile(rb'"timestamp":"(\d{4}-\d\d-\d\d)T')
    for dirpath, _dirs, fnames in os.walk(traces):
        for fn in fnames:
            if not fn.endswith(".jsonl"):
                continue
            try:
                fh = open(os.path.join(dirpath, fn), "rb")
            except OSError:
                continue
            with fh:
                day = ""
                for line in fh:
                    m = ts.search(line)
                    if m:
                        day = m.group(1).decode()
                    if b"memory/" not in line:
                        continue
                    hits = set()
                    for tm in _TU_READ.finditer(line):
                        hits.update(_MEM_PATH.findall(tm.group(1).decode("unicode_escape", "replace")))
                    for bm in _BASH.finditer(line):
                        hits.update(_MEM_PATH.findall(bm.group(1).decode("unicode_escape", "replace")))
                    for slug in hits - {"MEMORY"}:
                        counts[slug] = counts.get(slug, 0) + 1
                        if day > seen_days.get(slug, ""):
                            seen_days[slug] = day

    matched = unknown = 0
    with _provenance_lock():
        data = _load_provenance()
        entries = data["entries"]
        for slug, n in counts.items():
            entry = entries.get(slug)
            if entry is None:
                unknown += 1
                continue
            entry["access_count"] = n
            entry["last_accessed"] = seen_days.get(slug, "")
            matched += 1
        if not args.dry_run:
            _save_provenance(data)
    ranked = sorted(counts.items(), key=lambda kv: -kv[1])[:10]
    print(json.dumps({
        "slugs_with_reads": len(counts),
        "recorded": matched,
        "read_but_untracked": unknown,
        "tracked_total": len(entries),
        "top": ranked,
        "dry_run": bool(args.dry_run),
    }, indent=2))


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

    default_root = str(Path.home() / ".claude")
    backfill_p = sub.add_parser(
        "backfill", help="Record every live memory body the store never saw."
    )
    backfill_p.add_argument("--root", default=default_root, help="Harness checkout to act on")
    backfill_p.add_argument("--dry-run", action="store_true", help="Report without writing")
    backfill_p.set_defaults(func=backfill)

    usage_p = sub.add_parser(
        "usage", help="Fold observed read counts from session traces into the store."
    )
    usage_p.add_argument("--root", default=default_root, help="Harness checkout to act on")
    usage_p.add_argument(
        "--traces", default=str(Path.home() / ".claude" / "projects"),
        help="Directory of session trace .jsonl files",
    )
    usage_p.add_argument("--dry-run", action="store_true", help="Report without writing")
    usage_p.set_defaults(func=usage)

    # Production project keys are directory slugs that begin with '-'
    # (e.g. -home-haduong-CNRS-...). Without a '--' separator argparse
    # clusters '-home-…' into '-h' and help-exits 0 — a silent no-op on a
    # mutating call (ticket 0282). Insert the separator after the subcommand
    # unless the caller already did, or is asking for help at either level.
    #
    # Only for the subcommands whose arguments are bare positionals. `backfill`
    # and `usage` take options, and a blanket separator would push `--counts`
    # past it and make argparse read the flag as a positional — the same silent
    # no-op the separator exists to prevent, arriving from the other side.
    POSITIONAL_CMDS = {"record", "remove", "promote", "confirm"}
    tokens = sys.argv[1:]
    wants_help = any(t in ("-h", "--help") for t in tokens)
    if (
        len(tokens) > 1
        and tokens[0] in POSITIONAL_CMDS
        and "--" not in tokens
        and not wants_help
    ):
        tokens.insert(1, "--")

    args = parser.parse_args(tokens)
    args.func(args)


if __name__ == "__main__":
    main()

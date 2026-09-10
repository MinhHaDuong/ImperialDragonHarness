"""The provenance store must cover the live corpus, or every pass over it lies.

Promotion, decay and dedup all iterate the store. An entry the store never saw
is invisible to all three at once — and invisible in the way that reads as
health, because each pass reports success over the entries it can see. That is
the failure this repo keeps meeting: an all-clear indistinguishable from "I
could not look".

Measured before this gate existed, 2026-09-10: 651 tracked against 949 live
bodies, so 308 were invisible. `provenance.py backfill` closed the gap; this
keeps it closed. A new body reaches the store through `/dream` step 7; when a
body arrives another way, run the backfill.
"""

import importlib.util
import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]


def _load(path: Path):
    """Load a helper script by path.

    `sys.path.insert` plus a bare `import` would be a path hack the Python rules
    forbid, and `test_deps_declared.py` reads the bare name as an undeclared
    third-party package. `test_dream.py` avoids both by driving the CLI as a
    subprocess; these tests exercise pure functions, so they load the module
    instead of spawning one per assertion.
    """
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


provenance = _load(REPO / "skills" / "dream" / "provenance.py")


def tracked_slugs() -> set[str]:
    data = json.loads((REPO / "memory" / ".provenance.json").read_text(encoding="utf-8"))
    return set(data["entries"])


def test_every_live_memory_body_is_tracked():
    live = {slug for _project, slug, _path in provenance.live_bodies(REPO)}
    missing = sorted(live - tracked_slugs())
    assert not missing, (
        f"{len(missing)} live memory bodies have no provenance record, so promotion, "
        f"decay and dedup cannot see them: {missing[:10]}"
        f"{' …' if len(missing) > 10 else ''}. "
        "Run: python3 skills/dream/provenance.py backfill --root ."
    )


def test_tombstones_are_not_counted_as_live():
    """The positive control on the walker: it must exclude what it claims to.

    Without this, a walker that returned nothing would pass the coverage test
    above for the wrong reason, and a walker that returned tombstones would
    demand records for entries `remove` has deliberately dropped.
    """
    bodies = list(provenance.live_bodies(REPO))
    assert len(bodies) > 500, f"the walker found only {len(bodies)} bodies — it is not looking"
    for _project, slug, path in bodies:
        head = path.read_text(encoding="utf-8", errors="replace").lstrip()[:20]
        assert not head.startswith("# DELETED"), f"{slug} is a tombstone but was walked as live"
    assert "MEMORY" not in {slug for _p, slug, _path in bodies}


def test_usage_path_pattern_ignores_the_memory_skill():
    """`skills/memory/SKILL.md` is not a memory body.

    A bare `memory/<name>\\.md` matches it, and did: the memory *skill* entered
    the first usage run with 19 reads. Nothing was corrupted — no such slug
    exists — but a count that is wrong is wrong wherever it lands.
    """
    assert not provenance._MEM_PATH.search("/home/x/.claude/skills/memory/SKILL.md")
    assert not provenance._MEM_PATH.search("skills/memory/README.md")
    assert provenance._MEM_PATH.search(
        "/home/x/.claude/projects/-home-x-proj/memory/feedback_a.md"
    ).group(1) == "feedback_a"
    assert provenance._MEM_PATH.search("/home/x/.claude/memory/reference_b.md").group(1) == "reference_b"


def test_backfill_is_idempotent_and_keeps_the_decay_clock(tmp_path, monkeypatch):
    """Re-running must add nothing, and must never restamp last_confirmed.

    Stamping `now` on a backfill would reset every decay clock at the moment the
    clock is first wired up — the one outcome that would leave the store worse
    than the gap it closes.
    """
    root = tmp_path / "claude"
    memdir = root / "projects" / "-proj" / "memory"
    memdir.mkdir(parents=True)
    (memdir / "feedback_x.md").write_text("body\n", encoding="utf-8")
    (memdir / "feedback_dead.md").write_text("# DELETED 2026-01-01: gone\n", encoding="utf-8")
    (root / "memory").mkdir(parents=True)

    class Args:
        pass

    a = Args()
    a.root, a.dry_run = str(root), False

    # backfill retargets module globals; monkeypatch so pytest restores them and
    # a later test in the same session is not left pointing at tmp_path.
    for name in ("HARNESS_MEMORY", "PROVENANCE_PATH", "PROVENANCE_LOCK",
                 "PROJECT_ALIASES_PATH", "PROJECTS_BASE"):
        monkeypatch.setattr(provenance, name, getattr(provenance, name))

    provenance.backfill(a)
    store = root / "memory" / ".provenance.json"
    first = json.loads(store.read_text())["entries"]
    assert set(first) == {"feedback_x"}, "a tombstone was recorded as a live entry"
    stamp = first["feedback_x"]["last_confirmed"]

    provenance.backfill(a)
    second = json.loads(store.read_text())["entries"]
    assert set(second) == {"feedback_x"}
    assert second["feedback_x"]["last_confirmed"] == stamp, "backfill reset the decay clock"


def test_backfilled_entries_carry_real_dates():
    """Dates come from git history, not from the run that recorded them.

    If the backfill had stamped `now`, every backfilled entry would share one
    date and the 90-day decay would see nothing for three months.
    """
    data = json.loads((REPO / "memory" / ".provenance.json").read_text(encoding="utf-8"))
    backfilled = [v for v in data["entries"].values() if v.get("backfilled")]
    assert backfilled, "no backfilled entries — has the store been rebuilt?"
    months = {v["first_seen"][:7] for v in backfilled}
    assert len(months) >= 3, (
        f"backfilled entries span only {sorted(months)} — dates look stamped, not recovered"
    )
    assert all(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", v["first_seen"]) for v in backfilled)

"""Memory v8 pilot structure and relocated-clone readability (ticket 0920).

The pilot activates the v8 convention in this repository itself: a bounded
index, themes with provenance, the annual journal, and the inventoried
sources left at their original paths. The integration test proves the first
exit criterion mechanically: a clone relocated away from its origin checkout,
with its origin remote removed and no harness installed, reads the whole
memory surface through relative links alone.
"""

import hashlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parents[1]
MEMORY = REPO / "memory"
sys.path.insert(0, str(REPO / "scripts"))

import memory_sizes  # noqa: E402
INDEX = MEMORY / "MEMORY.md"

# The ten tracked memory/ root sources inventoried by 0917 in
# conception/memory-v8/source-inventory.md (PR #1102). Old-path correspondence:
# the nine sources stay at their inventory paths, unrewritten; MEMORY.md is
# the index itself, replaced by design with its legacy text in Git history.
PILOT_SOURCES = (
    "MEMORY.md",
    "feedback_rules_come_from_memory_consolidation.md",
    "feedback_subagent_model_effort_levers.md",
    "reference_branch_cleanup_incidents.md",
    "reference_git_in_a_worktree_session.md",
    "reference_zotero.md",
    "journal/2026/2026-10-01-memory-helper-retirement.md",
    "journal/2026/2026-10-01-memory-v8-design-and-boundaries.md",
    "journal/2026/2026-10-01-portable-registration-review.md",
    "journal/2026/2026-10-02-memory-v8-merge-under-parallel-housekeeping.md",
)

LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)\s]*)?\)")


def relative_links(text):
    """Markdown link targets that are repo-relative (scheme-less)."""
    return [
        target
        for target in LINK.findall(text)
        if not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target)
    ]


def unresolved_links(root, doc, archival_links=()):
    """Relative links in ``doc`` that do not resolve inside ``root``."""
    broken = []
    for target in relative_links(doc.read_text(encoding="utf-8")):
        resolved = (doc.parent / target).resolve()
        if not resolved.is_relative_to(root.resolve()):
            broken.append(f"{target} (escapes the clone)")
        elif not resolved.is_file():
            source = doc.relative_to(root).as_posix()
            old = resolved.relative_to(root.resolve()).as_posix()
            # Design history left docs/ for conception/ on 2026-10-27; pinned
            # records keep their old link text.
            if old.startswith("docs/") and (root / "conception" / old[5:]).is_file():
                continue
            # Attribution records left the journal for memory/evidence/attribution/
            # (ticket 1347); append-only journal entries keep their old link text.
            name = old.rsplit("/", 1)[-1]
            if (source.startswith("memory/journal/") and old.startswith("memory/journal/")
                    and "-review-attribution-" in name
                    and (root / "memory/evidence/attribution" / name).is_file()):
                continue
            current = (source == "memory/MEMORY.md" or source.startswith("memory/topics/")
                       or source in {"conception/memory-v8/README.md",
                                     "conception/2026-10-02-memory-v8-runtime-smoke.md"})
            if current or (source, old) not in archival_links:
                broken.append(target)
    return broken


MIGRATION_RECORD = "memory/journal/2026/2026-10-15-hoard-path-migration.md"


def relocation_record(root):
    text = (root / MIGRATION_RECORD).read_text()
    mappings = re.findall(r"^\| `(memory/(?:DREAM\.md|dreams/[^`]+))` \| `([^`]+)` \| `([0-9a-f]{40})` \|$", text, re.MULTILINE)
    archives = set(re.findall(r"^\| `([^`]+)` \| `(memory/(?:DREAM\.md|dreams/[^`]+))` \|$", text, re.MULTILINE))
    baseline = re.search(r"^Baseline commit: `([0-9a-f]{40})`", text, re.MULTILINE).group(1)
    return baseline, mappings, archives


def blob_id(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def verified_archival_links(root):
    """Verify this migration's exact relocation ledger against retained Git data."""
    baseline, mappings, archives = relocation_record(root)
    assert len(mappings) == 7
    old_paths = set()
    for old, new, oid in mappings:
        old_paths.add(old)
        assert not (root / old).exists(), old
        original = subprocess.run(
            ["git", "-C", str(root), "show", f"{baseline}:{old}"],
            check=True, capture_output=True, env=child_env(),
        ).stdout
        assert blob_id(original) == oid, old
        # The 1106 record names the paths of its day; ticket 1352 then renamed them.
        current_path = new.replace("memory/HOARD.md", "memory/SMELT.md").replace("memory/hoards/", "memory/smelts/")
        current = (root / current_path).read_bytes()
        if old == "memory/DREAM.md":
            assert new == "memory/HOARD.md"
            assert re.search(rb"(?m)^Prompt revision: v8-r1\b", original)
            assert re.search(rb"(?m)^Prompt revision: v8-r3\b", current)
        else:
            assert new == old.replace("memory/dreams/", "memory/hoards/", 1)
            assert blob_id(current) == oid, current_path
    assert len(old_paths) == 7
    assert archives
    for source, old in archives:
        assert (root / source).is_file(), source
        assert old in old_paths, old
        original_source = subprocess.run(
            ["git", "-C", str(root), "show", f"{baseline}:{source}"],
            check=True, capture_output=True, env=child_env(),
        ).stdout
        assert (root / source).read_bytes() == original_source, f"archival source changed: {source}"
        original_targets = {
            ((root / source).parent / target).resolve()
            for target in relative_links(original_source.decode("utf-8"))
        }
        assert (root / old).resolve() in original_targets, f"historical link absent: {source}: {old}"
    return archives


def test_current_memory_uses_relocated_paths():
    assert (MEMORY / "SMELT.md").is_file()
    assert not (MEMORY / "DREAM.md").exists()
    assert (MEMORY / "smelts").is_dir()
    assert not (MEMORY / "dreams").exists()


def test_archival_exceptions_reject_unmapped_and_current_broken_links(tmp_path):
    root = tmp_path
    archive = root / "memory/journal/2026/old.md"
    archive.parent.mkdir(parents=True)
    archive.write_text("[declared](../../dreams/report.md) [broken](unmapped.md)\n")
    allowed = {("memory/journal/2026/old.md", "memory/dreams/report.md")}
    assert unresolved_links(root, archive, allowed) == ["unmapped.md"]
    current = root / "memory/MEMORY.md"
    current.write_text("[declared](dreams/report.md)\n")
    allowed.add(("memory/MEMORY.md", "memory/dreams/report.md"))
    assert unresolved_links(root, current, allowed) == ["dreams/report.md"]


def test_index_is_bounded_and_terminated():
    text = INDEX.read_text(encoding="utf-8")
    assert memory_sizes.index_ok(text)
    assert text.endswith("\n")


def test_pilot_sources_stay_at_inventory_paths():
    for rel in PILOT_SOURCES:
        assert (MEMORY / rel).is_file(), rel


def test_v8_surface_links_journal_and_resolves():
    surface = [INDEX, *sorted((MEMORY / "topics").glob("*.md"))]
    assert surface
    combined = "".join(p.read_text(encoding="utf-8") for p in surface)
    assert "journal/2026/" in combined
    assert not unresolved_links(REPO, INDEX)
    for doc in surface:
        assert not unresolved_links(REPO, doc)


def test_index_links_every_topic():
    index_text = INDEX.read_text(encoding="utf-8")
    for topic in sorted((MEMORY / "topics").glob("*.md")):
        assert f"(topics/{topic.name})" in index_text, topic.name


def test_topics_cite_sources_and_provenance():
    memory_root = MEMORY.resolve()
    topics = sorted((MEMORY / "topics").glob("*.md"))
    assert topics
    for topic in topics:
        text = topic.read_text(encoding="utf-8")
        assert (
            "source-revisions.tsv" in text or "source-inventory.md" in text
        ), topic.name
        source_links = [
            (topic.parent / target).resolve()
            for target in relative_links(text)
        ]
        assert any(
            p.is_file()
            and p.is_relative_to(memory_root)
            and not p.is_relative_to((MEMORY / "topics").resolve())
            for p in source_links
        ), f"{topic.name} cites no source outside topics/"


def test_agents_md_merges_memory_reading_section():
    text = (REPO / "AGENTS.md").read_text(encoding="utf-8")
    assert "[memory/MEMORY.md](memory/MEMORY.md)" in text


@pytest.mark.integration
def test_relocated_clone_remains_readable(tmp_path):
    """Exit criterion 1: a moved clone reads without origin home or harness.

    Clone the repository, move the clone elsewhere, drop the origin remote —
    then read the memory surface with plain file access only: every relative
    link in every Markdown file under memory/ and conception/memory-v8/, plus
    the live runtime-smoke document, must resolve inside the relocated clone.
    """
    checkout = tmp_path / "checkout"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(REPO), str(checkout)],
        check=True, env=child_env(),
    )
    relocated = tmp_path / "elsewhere" / "moved-clone"
    relocated.parent.mkdir()
    shutil.move(str(checkout), str(relocated))
    subprocess.run(
        ["git", "-C", str(relocated), "remote", "remove", "origin"],
        check=True, env=child_env(),
    )

    assert (relocated / "memory" / "MEMORY.md").is_file()
    archival_links = verified_archival_links(relocated)
    docs = [
        *sorted((relocated / "memory").rglob("*.md")),
        *sorted((relocated / "conception" / "memory-v8").glob("*.md")),
        relocated / "conception" / "2026-10-02-memory-v8-runtime-smoke.md",
    ]
    assert docs
    encountered = set()
    for doc in docs:
        for target in unresolved_links(relocated, doc):
            resolved = (doc.parent / target).resolve()
            encountered.add((doc.relative_to(relocated).as_posix(),
                             resolved.relative_to(relocated).as_posix()))
        broken = unresolved_links(relocated, doc, archival_links)
        assert not broken, f"{doc}: {broken}"
    assert encountered <= archival_links
    assert any(source.startswith("memory/journal/") for source, old in encountered)
    archive = relocated / "memory/journal/2026/2026-10-13-third-dream-index-duplication-and-merge.md"
    archive.write_text(archive.read_text() + "\n[negative control](unmapped-broken.md)\n")
    assert "unmapped-broken.md" in unresolved_links(relocated, archive, archival_links)


@pytest.mark.integration
@pytest.mark.parametrize("mutation", ["source_bytes", "invented_link"])
def test_archival_source_must_match_its_historical_bytes_and_link(tmp_path, mutation):
    root = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", str(REPO), str(root)],
        check=True, env=child_env(),
    )
    _, mappings, archives = relocation_record(root)
    source, old = next(iter(archives))
    if mutation == "source_bytes":
        journal = root / source
        original = journal.read_bytes()
        journal.write_bytes(original + b"\nA false historical statement.\n")
        assert relative_links(journal.read_text()) == relative_links(original.decode("utf-8"))
        error = "archival source changed"
    else:
        other = next(path for path, _, _ in mappings
                     if path.startswith("memory/dreams/") and path != old)
        record = root / MIGRATION_RECORD
        record.write_text(record.read_text().replace(
            f"| `{source}` | `{old}` |", f"| `{source}` | `{other}` |"))
        error = "historical link absent"
    with pytest.raises(AssertionError, match=error):
        verified_archival_links(root)

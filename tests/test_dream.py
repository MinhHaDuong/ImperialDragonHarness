"""
Tests for /dream skill helper scripts.
Scripts are pure I/O — no LLM calls, no Anthropic dependency.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

DREAM_DIR = Path(__file__).parent.parent / "skills" / "dream"
READ_INDEX = DREAM_DIR / "read-index.py"
COMMIT_PY = DREAM_DIR / "commit.py"
PROVENANCE_PY = DREAM_DIR / "provenance.py"


@pytest.fixture
def fixture_memory_dir(tmp_path):
    projects_dir = tmp_path / ".claude" / "projects" / "test-project" / "memory"
    projects_dir.mkdir(parents=True)

    (projects_dir / "feedback_vim.md").write_text(
        "---\nname: feedback_vim\ndescription: vim preference\nmetadata:\n  type: feedback\n---\nUser prefers vim.\n"
    )
    (projects_dir / "feedback_emacs.md").write_text(
        "---\nname: feedback_emacs\ndescription: emacs preference\nmetadata:\n  type: feedback\n---\nUser switched to emacs.\n"
    )
    (projects_dir / "MEMORY.md").write_text(
        "## Entries\n\n"
        "- [feedback_vim](feedback_vim.md) — Editor preference: vim\n"
        "- [feedback_emacs](feedback_emacs.md) — Editor preference: emacs\n"
    )
    return tmp_path


def _run(script, *args, home):
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )


def test_read_index_returns_entries(fixture_memory_dir):
    result = _run(READ_INDEX, "test-project", home=fixture_memory_dir)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["project"] == "test-project"
    assert len(data["entries"]) == 2
    filenames = {e["filename"] for e in data["entries"]}
    assert filenames == {"feedback_vim.md", "feedback_emacs.md"}
    for entry in data["entries"]:
        assert entry["content"]


def test_read_index_missing_project(tmp_path):
    result = _run(READ_INDEX, "nonexistent", home=tmp_path)
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert "error" in data


def test_read_index_empty_index(tmp_path):
    mem = tmp_path / ".claude" / "projects" / "empty" / "memory"
    mem.mkdir(parents=True)
    (mem / "MEMORY.md").write_text("# Memory index\n\n## Key insights\n\n")

    result = _run(READ_INDEX, "empty", home=tmp_path)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["entries"] == []


def test_skill_md_instructs_preserve_evolution():
    content = (DREAM_DIR / "SKILL.md").read_text()
    assert "evolution" in content.lower() or "preserve" in content.lower()


def test_skill_md_has_push_or_restore_contract():
    """Ticket 0247: dream's exit is unconditional — after every commit, push +
    open the PR, then switch the primary back to main whether the push succeeded
    or failed, and only then confirm with the probe. The probe must run AFTER the
    restore, else it trips on the very off-main state the run just left (the gaze
    review blocker on the first cut). String-match the contract and its ordering
    so the SKILL.md instruction cannot silently regress."""
    content = (DREAM_DIR / "SKILL.md").read_text()
    assert "push-or-restore" in content, "missing the push-or-restore contract marker"
    # The self-contradicting first cut ("leave the checkout on the branch is
    # fine" followed by an unconditional probe) must stay removed.
    assert "leave the checkout on the branch is fine" not in content
    restore = content.find("switch main")
    probe = content.find("check-primary-checkout.sh ~/.claude")
    assert restore != -1, "exit does not restore the primary to main"
    assert probe != -1, "exit does not confirm with the checkout probe"
    assert restore < probe, "exit must switch back to main BEFORE running the probe"


def test_supervisor_probes_primary_checkout():
    """Ticket 0247: a stranded checkout must be detected within one cycle.

    Asserted against the survey helper rather than the skill prose. The probe
    used to be a step an executor was told to run, which held only for as long
    as the executor followed the procedure; in the helper it runs whatever the
    executor decides to do.
    """
    survey = (
        DREAM_DIR.parent.parent / "scripts" / "nightbeat-supervisor-survey.py"
    ).read_text()
    assert "check-primary-checkout" in survey, (
        "survey helper does not run the checkout probe"
    )
    assert "sys.exit" in survey.split("_check_primary_checkout")[-1][:800], (
        "checkout probe failure does not stop the survey"
    )


def test_skill_md_pr_body_sourced_from_decision_table():
    """Ticket 0241: the consolidation PR body must be the step-4 decision table
    verbatim, never free-form summary prose (PR #359 shipped an improvised "all
    NOOP" body that mismatched the diff). Check co-occurrence in a window, not
    that each phrase merely appears somewhere in the file."""
    content = (DREAM_DIR / "SKILL.md").read_text()
    lc = content.lower()
    window = 600
    found = any(
        "pr body" in lc[max(0, m.start() - window):m.end() + window]
        and "free-form" in lc[max(0, m.start() - window):m.end() + window]
        for m in re.finditer("decision table", lc)
    )
    assert found, "PR body / decision table / free-form not co-located in SKILL.md"


def test_skill_md_counts_derived_mechanically():
    """Ticket 0275: before/after counts come from grep on MEMORY.md at base vs
    head, the ADD list from --diff-filter=A, and the reconciliation identities
    are stated verbatim so the executor self-checks (PR #471 shipped a
    prose-recalled "76->74" over a real 72->74)."""
    content = (DREAM_DIR / "SKILL.md").read_text()
    assert "grep -c '^- \\['" in content, "count derivation grep missing"
    assert "--diff-filter=A" in content, "ADD-list diff filter missing"
    assert "NOOP + UPDATE + DELETE" in content, "before-count identity missing"
    assert "NOOP + UPDATE + ADD" in content, "after-count identity missing"


def test_skill_md_delete_removes_provenance():
    """Ticket 0241: a DELETE must drop its provenance record, else deleted
    entries keep counting toward the promotion frequency gate."""
    content = (DREAM_DIR / "SKILL.md").read_text()
    assert "provenance.py remove" in content, "DELETE does not clean provenance"


def test_commit_py_has_rollback_subcommand():
    assert "rollback" in COMMIT_PY.read_text()


def test_no_anthropic_import_in_scripts():
    for script in [READ_INDEX, COMMIT_PY, PROVENANCE_PY]:
        source = script.read_text()
        assert "import anthropic" not in source, f"{script.name} imports anthropic"
        assert "from anthropic" not in source, f"{script.name} imports anthropic"


# --- Provenance tests (v2) ---


@pytest.fixture
def provenance_env(tmp_path):
    """Set up a fake HOME with harness memory dir for provenance tests."""
    memory_dir = tmp_path / ".claude" / "memory"
    memory_dir.mkdir(parents=True)
    return tmp_path


def _run_provenance(*args, home, extra_env=None):
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, str(PROVENANCE_PY), *args],
        capture_output=True,
        text=True,
        env=env,
    )


def test_provenance_record_new_entry(provenance_env):
    result = _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["projects"] == ["project-alpha"]
    assert data["promoted"] is False


def test_provenance_record_second_project(provenance_env):
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    result = _run_provenance("record", "feedback_vim", "project-beta", home=provenance_env)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert set(data["projects"]) == {"project-alpha", "project-beta"}


def test_provenance_record_same_project_idempotent(provenance_env):
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    result = _run_provenance("show", home=provenance_env)
    data = json.loads(result.stdout)
    assert data["entries"]["feedback_vim"]["projects"] == ["project-alpha"]


def test_provenance_candidates_empty_initially(provenance_env):
    result = _run_provenance("candidates", home=provenance_env)
    assert result.returncode == 0
    assert json.loads(result.stdout) == []


def test_provenance_candidates_after_two_projects(provenance_env):
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    _run_provenance("record", "feedback_vim", "project-beta", home=provenance_env)
    result = _run_provenance("candidates", home=provenance_env)
    assert result.returncode == 0
    candidates = json.loads(result.stdout)
    assert len(candidates) == 1
    assert candidates[0]["slug"] == "feedback_vim"


def test_provenance_candidates_excludes_promoted(provenance_env):
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    _run_provenance("record", "feedback_vim", "project-beta", home=provenance_env)
    _run_provenance("promote", "feedback_vim", home=provenance_env)
    result = _run_provenance("candidates", home=provenance_env)
    candidates = json.loads(result.stdout)
    assert len(candidates) == 0


def test_provenance_promote(provenance_env):
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    result = _run_provenance("promote", "feedback_vim", home=provenance_env)
    assert result.returncode == 0
    assert "Promoted" in result.stdout
    show = _run_provenance("show", home=provenance_env)
    data = json.loads(show.stdout)
    assert data["entries"]["feedback_vim"]["promoted"] is True
    assert "promoted_at" in data["entries"]["feedback_vim"]


def test_provenance_promote_unknown_slug(provenance_env):
    result = _run_provenance("promote", "nonexistent", home=provenance_env)
    assert result.returncode == 1


# --- Provenance remove (ticket 0241: DELETE cleans provenance) ---


def test_provenance_remove_drops_one_project(provenance_env):
    """remove drops the named project from a multi-project slug; entry survives."""
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    _run_provenance("record", "feedback_vim", "project-beta", home=provenance_env)
    result = _run_provenance("remove", "feedback_vim", "project-alpha", home=provenance_env)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["projects"] == ["project-beta"]
    show = json.loads(_run_provenance("show", home=provenance_env).stdout)
    assert "feedback_vim" in show["entries"]


def test_provenance_remove_last_project_deletes_entry(provenance_env):
    """Removing the last project of an unpromoted entry deletes the entry."""
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    result = _run_provenance("remove", "feedback_vim", "project-alpha", home=provenance_env)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"removed": "feedback_vim"}
    show = json.loads(_run_provenance("show", home=provenance_env).stdout)
    assert "feedback_vim" not in show["entries"]


def test_provenance_remove_last_project_keeps_promoted_entry(provenance_env):
    """Promotion is one-way: a promoted entry survives removal of its last
    project (its lesson has earned harness-level status independent of origin)."""
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    _run_provenance("promote", "feedback_vim", home=provenance_env)
    result = _run_provenance("remove", "feedback_vim", "project-alpha", home=provenance_env)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["projects"] == []
    assert data["promoted"] is True
    show = json.loads(_run_provenance("show", home=provenance_env).stdout)
    assert "feedback_vim" in show["entries"]


def test_provenance_remove_unknown_slug(provenance_env):
    """remove of an untracked slug is an idempotent no-op (exit 0, store unchanged).

    SKILL.md step 5 calls remove unconditionally on every DELETE, but 37% of live
    memory entries predate the provenance store, so a hard-fail would abort a
    consolidation on the first DELETE of an untracked entry."""
    result = _run_provenance("remove", "nonexistent", "project-alpha", home=provenance_env)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"removed": None}
    show = json.loads(_run_provenance("show", home=provenance_env).stdout)
    assert "nonexistent" not in show["entries"]


# --- Provenance canonical-project gate (ticket 0270: path aliases collapse) ---


def _write_aliases(home, mapping):
    """Write the read-time alias table to <HOME>/.claude/memory/.project-aliases.json."""
    path = home / ".claude" / "memory" / ".project-aliases.json"
    path.write_text(json.dumps(mapping))


def _seed_provenance(home, slug, projects, promoted=False):
    """Write .provenance.json directly with one entry under the given project keys.

    Directory-slug project keys begin with `-` (e.g. `-home-haduong--claude`), which
    argparse in the record CLI parses as `-h`; the decay tests already seed the store
    directly for the same reason. We exercise candidates() in isolation here."""
    path = home / ".claude" / "memory" / ".provenance.json"
    now = "2026-07-11T00:00:00Z"
    path.write_text(json.dumps({
        "entries": {
            slug: {
                "projects": list(projects),
                "first_seen": now,
                "last_confirmed": now,
                "promoted": promoted,
            }
        }
    }))


def test_provenance_candidates_alias_collapse_not_candidate(provenance_env):
    """Two path-spellings of one project collapse to one canonical project, so a
    slug recorded under both keys is NOT a promotion candidate (frequency < 2).

    Directory-slug keys, not paths: the AEDIST report registered under both
    `-home-haduong-aedist-technical-report` and its
    `-home-haduong-CNRS-papiers-actif-AEDIST-technical-report` spelling. The gate
    must count distinct *canonical* projects."""
    _write_aliases(provenance_env, {
        "-home-haduong-aedist-technical-report":
            "-home-haduong-CNRS-papiers-actif-AEDIST-technical-report",
    })
    _seed_provenance(provenance_env, "reference_zotero", [
        "-home-haduong-aedist-technical-report",
        "-home-haduong-CNRS-papiers-actif-AEDIST-technical-report",
    ])
    result = _run_provenance("candidates", home=provenance_env)
    assert result.returncode == 0, result.stderr
    candidates = json.loads(result.stdout)
    assert [c["slug"] for c in candidates] == []


def test_provenance_candidates_true_distinct_still_candidate(provenance_env):
    """Teeth-check: with the alias table present, a slug in two genuinely distinct
    projects is still the sole candidate — the canonicalizer collapses only aliases."""
    _write_aliases(provenance_env, {
        "-home-haduong-aedist-technical-report":
            "-home-haduong-CNRS-papiers-actif-AEDIST-technical-report",
    })
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    _run_provenance("record", "feedback_vim", "project-beta", home=provenance_env)
    result = _run_provenance("candidates", home=provenance_env)
    assert result.returncode == 0, result.stderr
    candidates = json.loads(result.stdout)
    assert [c["slug"] for c in candidates] == ["feedback_vim"]


def test_provenance_candidates_substring_key_still_distinct(provenance_env):
    """A key that shares a substring with an aliased key but is not that key stays
    distinct — guards against substring matching creeping in instead of dict.get()."""
    _write_aliases(provenance_env, {
        "-home-haduong-aedist-technical-report":
            "-home-haduong-CNRS-papiers-actif-AEDIST-technical-report",
    })
    _seed_provenance(provenance_env, "feedback_vim", [
        "-home-haduong-aedist-technical-report",
        "-home-haduong-aedist-technical-report-notes",
    ])
    result = _run_provenance("candidates", home=provenance_env)
    assert result.returncode == 0, result.stderr
    candidates = json.loads(result.stdout)
    assert [c["slug"] for c in candidates] == ["feedback_vim"]


def test_provenance_candidates_chained_alias_not_candidate(provenance_env):
    """A chained alias table {old->A, A->B} must resolve `old` all the way to B,
    so a slug recorded under both `old` and `B` collapses to one canonical
    project and is NOT a candidate. Single-level dict.get() stops at A and
    wrongly counts {A, B} == 2 (ticket 0270 reroll)."""
    _write_aliases(provenance_env, {
        "-home-haduong-old-spelling": "-home-haduong-mid-spelling",
        "-home-haduong-mid-spelling": "-home-haduong-canonical",
    })
    _seed_provenance(provenance_env, "feedback_vim", [
        "-home-haduong-old-spelling",
        "-home-haduong-canonical",
    ])
    result = _run_provenance("candidates", home=provenance_env)
    assert result.returncode == 0, result.stderr
    candidates = json.loads(result.stdout)
    assert [c["slug"] for c in candidates] == []


def test_provenance_decay_empty(provenance_env):
    result = _run_provenance("decay", home=provenance_env)
    assert result.returncode == 0
    assert json.loads(result.stdout) == []


def test_provenance_decay_flags_old_entries(provenance_env):
    """Directly write provenance with an old last_confirmed date."""
    prov_path = provenance_env / ".claude" / "memory" / ".provenance.json"
    prov_path.write_text(json.dumps({
        "entries": {
            "old_entry": {
                "projects": ["project-alpha", "project-beta"],
                "first_seen": "2025-01-01T00:00:00Z",
                "last_confirmed": "2025-01-01T00:00:00Z",
                "promoted": True,
            },
            "fresh_entry": {
                "projects": ["project-alpha"],
                "first_seen": "2026-06-01T00:00:00Z",
                "last_confirmed": "2026-06-01T00:00:00Z",
                "promoted": True,
            },
        }
    }))
    result = _run_provenance("decay", home=provenance_env)
    assert result.returncode == 0
    flagged = json.loads(result.stdout)
    slugs = [f["slug"] for f in flagged]
    assert "old_entry" in slugs
    assert "fresh_entry" not in slugs


def test_provenance_show(provenance_env):
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    result = _run_provenance("show", home=provenance_env)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "feedback_vim" in data["entries"]


# --- Decay-confirmation path (ticket 0224, defect 1) ---


def test_provenance_confirm_unknown_slug(provenance_env):
    result = _run_provenance("confirm", "nonexistent", home=provenance_env)
    assert result.returncode == 1


def test_provenance_confirm_rejects_unpromoted(provenance_env):
    """confirm targets promoted harness entries; a project-level entry is refused."""
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    result = _run_provenance("confirm", "feedback_vim", home=provenance_env)
    assert result.returncode == 1


def test_provenance_confirm_refreshes_promoted_entry_so_decay_skips_it(provenance_env):
    """A promoted entry confirmed by a later consolidation must NOT decay-flag.

    Reproduces the ticket-0224 gap: promote freezes last_confirmed (the
    tombstoned project entry no longer gets `record`ed), so without `confirm`
    the entry decay-flags at 90 days regardless of relevance. After `confirm`,
    decay must skip it.
    """
    prov_path = provenance_env / ".claude" / "memory" / ".provenance.json"
    prov_path.write_text(json.dumps({
        "entries": {
            "old_promoted": {
                "projects": ["project-alpha", "project-beta"],
                "first_seen": "2025-01-01T00:00:00Z",
                "last_confirmed": "2025-01-01T00:00:00Z",
                "promoted": True,
            },
        }
    }))
    # Before confirm: decay flags it (stale by >90 days).
    before = json.loads(_run_provenance("decay", home=provenance_env).stdout)
    assert "old_promoted" in [f["slug"] for f in before]

    # A later relevant consolidation confirms it.
    result = _run_provenance("confirm", "old_promoted", home=provenance_env)
    assert result.returncode == 0, result.stderr

    # After confirm: decay no longer flags it.
    after = json.loads(_run_provenance("decay", home=provenance_env).stdout)
    assert "old_promoted" not in [f["slug"] for f in after]


# --- Provenance write-race (ticket 0224, defect 2) ---


@pytest.mark.integration
def test_provenance_concurrent_record_loses_neither_write(provenance_env):
    """Two interleaved record() round-trips must preserve both entries.

    The test delay hook forces the two critical sections to overlap: each
    subprocess loads provenance, sleeps, then writes. Without the lock the
    second writer's load predates the first writer's save, so the first write
    is lost (classic read-modify-write race). With the lock the writes
    serialize and both slugs survive.

    Teeth check: remove the _provenance_lock() wrapper in provenance.py and
    this test FAILS (one slug missing) — confirming it catches the defect, not
    merely a different implementation.
    """
    import concurrent.futures

    delay_env = {"DREAM_PROVENANCE_TEST_DELAY": "0.5"}

    def write(slug):
        return _run_provenance("record", slug, "project-x", home=provenance_env, extra_env=delay_env)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(write, "slug_one")
        f2 = ex.submit(write, "slug_two")
        r1, r2 = f1.result(), f2.result()

    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr

    data = json.loads(_run_provenance("show", home=provenance_env).stdout)
    assert "slug_one" in data["entries"], "lost write: slug_one missing"
    assert "slug_two" in data["entries"], "lost write: slug_two missing"


@pytest.mark.integration
def test_provenance_read_during_write_never_torn(provenance_env):
    """A reader interleaved with a writer never observes a half-written file.

    Writes truncate-then-write are non-atomic: a reader landing between the
    truncate and the content flush sees a partial (or empty) file and raises
    JSONDecodeError (ticket 0225). The atomic _save_provenance stages the full
    document in a temp file and os.replace()s it, so the live file is never
    partial — a reader sees the complete old-or-new document.

    The DREAM_PROVENANCE_WRITE_DELAY hook pins the writer mid-write (after the
    temp file is staged, before the replace). We launch the read solidly inside
    that window and assert it loads a valid document with the pre-existing entry
    intact.

    Teeth check: replace the atomic body of _save_provenance with the
    instrumented non-atomic form

        with open(PROVENANCE_PATH, "w") as f:   # truncates the live file
            _write_delay()                        # reader sees 0 bytes here
            f.write(text)

    and this test FAILS — the reader subprocess exits nonzero on
    json.loads("") — confirming it catches the torn read, not merely a
    different implementation.
    """
    import concurrent.futures
    import time

    # Seed a valid old document with no delay.
    seed = _run_provenance("record", "slug_old", "project-x", home=provenance_env)
    assert seed.returncode == 0, seed.stderr

    write_delay_env = {"DREAM_PROVENANCE_WRITE_DELAY": "0.5"}

    def write():
        return _run_provenance(
            "record", "slug_new", "project-y", home=provenance_env, extra_env=write_delay_env
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        writer = ex.submit(write)
        # Let the writer reach its mid-write delay, then read inside the window.
        time.sleep(0.2)
        reader = _run_provenance("show", home=provenance_env)
        w = writer.result()

    assert w.returncode == 0, w.stderr
    assert reader.returncode == 0, f"reader saw a torn file: {reader.stderr}"
    data = json.loads(reader.stdout)  # raises if reader captured a partial write
    # The reader must see a complete document: the old entry is always present
    # (the new entry may or may not have landed, depending on old-or-new).
    assert "slug_old" in data["entries"], "reader lost the pre-existing entry"


# ── Provenance CLI robustness (ticket 0282) ────────────────────────────────────


def test_provenance_record_leading_dash_project(provenance_env):
    """Ticket 0282: production project keys are directory slugs that begin
    with '-' (e.g. -home-haduong-...). argparse clusters '-home-…' into '-h'
    and help-exits 0 — a silent no-op on a mutating call. The CLI must accept
    them directly."""
    result = _run_provenance(
        "record", "feedback_vim", "-home-haduong-some-project", home=provenance_env
    )
    assert result.returncode == 0, result.stderr
    show = _run_provenance("show", home=provenance_env)
    data = json.loads(show.stdout)
    assert "feedback_vim" in data["entries"], "record silently no-opped"
    assert data["entries"]["feedback_vim"]["projects"] == [
        "-home-haduong-some-project"
    ]


def test_provenance_remove_leading_dash_project(provenance_env):
    """Same defect on the remove verb (SKILL.md step 5 calls it per DELETE)."""
    _run_provenance(
        "record", "feedback_vim", "-home-haduong-some-project", home=provenance_env
    )
    result = _run_provenance(
        "remove", "feedback_vim", "-home-haduong-some-project", home=provenance_env
    )
    assert result.returncode == 0, result.stderr
    show = _run_provenance("show", home=provenance_env)
    assert "feedback_vim" not in json.loads(show.stdout)["entries"]


def test_provenance_help_still_works(provenance_env):
    """The separator auto-insert must not eat -h/--help, top-level or per-verb."""
    top = _run_provenance("--help", home=provenance_env)
    assert top.returncode == 0 and "record" in top.stdout
    sub = _run_provenance("record", "-h", home=provenance_env)
    assert sub.returncode == 0 and "slug" in sub.stdout


def test_provenance_candidates_survives_malformed_alias_table(provenance_env):
    """Ticket 0282: a corrupt .project-aliases.json must degrade to 'no
    aliases' with a stderr warning, not crash candidates."""
    aliases_path = provenance_env / ".claude" / "memory" / ".project-aliases.json"
    aliases_path.write_text("{not json")
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    _run_provenance("record", "feedback_vim", "project-beta", home=provenance_env)
    result = _run_provenance("candidates", home=provenance_env)
    assert result.returncode == 0, result.stderr
    assert "alias" in result.stderr.lower()  # warned, not silent
    slugs = [c["slug"] for c in json.loads(result.stdout)]
    assert slugs == ["feedback_vim"]  # gate still works, aliases treated empty


@pytest.mark.parametrize("payload", ["42", "null", "[1]", '{"a": 1}'])
def test_provenance_candidates_survives_wrong_shape_alias_table(
    provenance_env, payload
):
    """Ticket 0279: valid JSON of the wrong shape (a scalar, a list, or a dict
    whose values are not strings) parses cleanly past the JSONDecodeError guard,
    then crashes _canonical_project downstream (e.g. `current in aliases` on an
    int, or a non-str alias value fed back into the loop). The shape check must
    degrade these to 'no aliases' with the same stderr warning, exactly like an
    unparseable table."""
    aliases_path = provenance_env / ".claude" / "memory" / ".project-aliases.json"
    aliases_path.write_text(payload)
    _run_provenance("record", "feedback_vim", "project-alpha", home=provenance_env)
    _run_provenance("record", "feedback_vim", "project-beta", home=provenance_env)
    result = _run_provenance("candidates", home=provenance_env)
    assert result.returncode == 0, result.stderr
    assert "alias" in result.stderr.lower()  # warned, not silent
    slugs = [c["slug"] for c in json.loads(result.stdout)]
    assert slugs == ["feedback_vim"]  # gate still works, aliases treated empty

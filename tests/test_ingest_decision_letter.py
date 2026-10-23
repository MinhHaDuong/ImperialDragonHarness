"""ingest-decision-letter: remark-ledger parse, dedupe, and coverage check.

The skill ingests a journal decision letter + reviewer comments into a stable
remark ledger and cross-checks remark-to-ticket coverage in one deterministic
pass. These fast tests pin the helper's mechanical contract; the skill-text
ratchets pin the documented invariants (pure I/O, tool-agnostic sources).

Fixtures under tests/fixtures/decision-letter/ are SYNTHESIZED fiction — no real
editorial content is stored in this repo.
"""

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from child_env import child_env

REPO = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO / "skills" / "ingest-decision-letter"
SCRIPT = SKILL_DIR / "ingest_letter.py"
SKILL = SKILL_DIR / "SKILL.md"
FIX = REPO / "tests" / "fixtures" / "decision-letter"


def _load_module():
    spec = importlib.util.spec_from_file_location("ingest_letter", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


il = _load_module()


# --------------------------------------------------------------------------- #
# segment — parse into a candidate ledger with stable ids
# --------------------------------------------------------------------------- #
def test_segment_numbered_reviewer_counts():
    text = (FIX / "reviewer1.txt").read_text()
    recs = il.segment(text, "R1", "reviewer1.txt")
    assert len(recs) == 3, "three numbered comments -> three candidate remarks"
    assert [r["id"] for r in recs] == ["R1-01", "R1-02", "R1-03"]
    assert all(r["reviewer"] == "R1" for r in recs)


def test_segment_comment_prefixed_reviewer_counts():
    text = (FIX / "reviewer2.txt").read_text()
    recs = il.segment(text, "R2", "reviewer2.txt")
    assert len(recs) == 3, "three 'Comment N:' items -> three remarks"
    assert [r["id"] for r in recs] == ["R2-01", "R2-02", "R2-03"]


def test_segment_ids_are_stable_across_runs():
    text = (FIX / "reviewer1.txt").read_text()
    a = il.segment(text, "R1", "reviewer1.txt")
    b = il.segment(text, "R1", "reviewer1.txt")
    assert [r["id"] for r in a] == [r["id"] for r in b]
    assert [r["text"] for r in a] == [r["text"] for r in b]


def test_segment_records_source_location():
    text = (FIX / "reviewer2.txt").read_text()
    recs = il.segment(text, "R2", "reviewer2.txt")
    for r in recs:
        assert r["source"].startswith("reviewer2.txt:")
        assert int(r["source"].split(":")[1]) >= 1


def test_segment_verbatim_text_preserved():
    text = (FIX / "reviewer2.txt").read_text()
    recs = il.segment(text, "R2", "reviewer2.txt")
    assert "recieve" in recs[2]["text"], "verbatim typo must survive segmentation"


def test_segment_paragraph_fallback_when_unnumbered():
    text = "First standalone concern here.\n\nA second, separate concern.\n"
    recs = il.segment(text, "R3", "r3.txt")
    assert len(recs) == 2, "blank-line paragraphs each become a remark"


# --------------------------------------------------------------------------- #
# dedupe — fold atomic / duplicate comments into distinct remarks
# --------------------------------------------------------------------------- #
def test_dedupe_folds_identical_duplicate():
    text = (FIX / "reviewer1.txt").read_text()
    recs = il.segment(text, "R1", "reviewer1.txt")
    out, summary = il.dedupe(recs)
    assert summary == {
        "input": 3,
        "remarks": 2,
        "atomics": 1,
        "unknown_atomic_refs": [],
    }
    folded = [r for r in out if r["atomic_of"] is not None]
    assert len(folded) == 1
    assert folded[0]["id"] == "R1-03"
    assert folded[0]["atomic_of"] == "R1-01", "duplicate folds into the first"


def test_dedupe_respects_explicit_atomic_of():
    recs = [
        il._normalize_record({"id": "R1-01", "text": "Parent remark."}),
        il._normalize_record(
            {"id": "R1-02", "text": "A distinct sub-point.", "atomic_of": "R1-01"}
        ),
        il._normalize_record({"id": "R1-03", "text": "Another remark."}),
    ]
    out, summary = il.dedupe(recs)
    assert summary["remarks"] == 2 and summary["atomics"] == 1
    assert [r for r in out if r["id"] == "R1-02"][0]["atomic_of"] == "R1-01"


def test_dedupe_flags_dangling_atomic_of():
    """A dangling atomic_of (typo from the hand-edit step) is surfaced, not silently
    rewritten to a distinct remark."""
    recs = [
        il._normalize_record({"id": "R1-01", "text": "Parent remark."}),
        il._normalize_record(
            {"id": "R1-02", "text": "A sub-point.", "atomic_of": "R9-99"}
        ),
    ]
    out, summary = il.dedupe(recs)
    assert summary["unknown_atomic_refs"] == ["R1-02"]
    child = [r for r in out if r["id"] == "R1-02"][0]
    assert child["atomic_of"] == "R9-99", "dangling ref must not become distinct"


def test_dedupe_full_ledger_counts():
    combined = il.segment((FIX / "reviewer1.txt").read_text(), "R1", "reviewer1.txt")
    combined += il.segment((FIX / "reviewer2.txt").read_text(), "R2", "reviewer2.txt")
    out, summary = il.dedupe(combined)
    assert summary["input"] == 6
    assert summary["remarks"] == 5, "60->56 in miniature: one duplicate folds"
    assert summary["atomics"] == 1


# --------------------------------------------------------------------------- #
# coverage — flag uncovered remarks AND orphan tickets in one pass
# --------------------------------------------------------------------------- #
def _mapped_ledger():
    return [
        il._normalize_record({"id": "R1-01", "text": "a", "tickets": ["0301"]}),
        il._normalize_record({"id": "R1-02", "text": "b", "tickets": ["0302"]}),
        il._normalize_record({"id": "R2-01", "text": "c", "tickets": ["0303"]}),
        il._normalize_record({"id": "R2-02", "text": "d", "tickets": ["0304"]}),
        il._normalize_record({"id": "R2-03", "text": "e", "tickets": []}),
        # a folded atomic inherits coverage; must not count as a remark
        il._normalize_record(
            {"id": "R1-03", "text": "a", "tickets": [], "atomic_of": "R1-01"}
        ),
    ]


def test_coverage_flags_uncovered_and_orphan_together():
    ledger = _mapped_ledger()
    universe = {"0301", "0302", "0303", "0304", "0399"}
    report = il.coverage(ledger, universe)
    assert report["remark_count"] == 5, "the folded atomic is not counted"
    assert report["uncovered_remarks"] == ["R2-03"]
    assert report["orphan_tickets"] == ["0399"]
    assert report["unknown_ticket_refs"] == []
    assert not il.coverage_ok(report)


def test_coverage_flags_duplicate_remark_id():
    """Two remarks sharing an id (e.g. re-run segment + concat) are surfaced, not
    silently collapsed into one mapping."""
    ledger = [
        il._normalize_record({"id": "R1-01", "text": "a", "tickets": ["0301"]}),
        il._normalize_record({"id": "R1-01", "text": "dup", "tickets": ["0302"]}),
    ]
    report = il.coverage(ledger, {"0301", "0302"})
    assert report["duplicate_ids"] == ["R1-01"]
    assert not il.coverage_ok(report)


def test_coverage_flags_unknown_ticket_reference():
    ledger = [il._normalize_record({"id": "R1-01", "text": "a", "tickets": ["0999"]})]
    report = il.coverage(ledger, {"0301"})
    assert report["unknown_ticket_refs"] == ["0999"]
    assert report["orphan_tickets"] == ["0301"]
    assert not il.coverage_ok(report)


def test_coverage_clean_when_every_remark_mapped():
    ledger = [
        il._normalize_record({"id": "R1-01", "text": "a", "tickets": ["0301"]}),
        il._normalize_record({"id": "R1-02", "text": "b", "tickets": ["0301", "0302"]}),
    ]
    report = il.coverage(ledger, {"0301", "0302"})
    assert report["uncovered_remarks"] == []
    assert report["orphan_tickets"] == []
    assert report["unknown_ticket_refs"] == []
    assert il.coverage_ok(report)


def test_ticket_ids_from_dir_reads_erg_filenames(tmp_path):
    (tmp_path / "0301-foo.erg").write_text("x")
    (tmp_path / "0302-bar.erg").write_text("x")
    (tmp_path / "notes.txt").write_text("x")
    assert il._ticket_ids_from_dir(tmp_path) == {"0301", "0302"}


# --------------------------------------------------------------------------- #
# archive — copy sources into a release/<date>/ dir with a manifest
# --------------------------------------------------------------------------- #
def test_archive_copies_sources_and_writes_manifest(tmp_path):
    into = tmp_path / "release" / "2026-07-12-r1"
    manifest = il.archive([FIX / "decision.txt", FIX / "reviewer1.txt"], into)
    assert (into / "decision.txt").exists()
    assert (into / "reviewer1.txt").exists()
    assert (into / "manifest.json").exists()
    assert len(manifest["entries"]) == 2


def test_archive_disambiguates_same_basename_from_different_dirs(tmp_path):
    d1 = tmp_path / "d1"
    d2 = tmp_path / "d2"
    d1.mkdir()
    d2.mkdir()
    (d1 / "review.txt").write_text("from dir one")
    (d2 / "review.txt").write_text("from dir two")
    into = tmp_path / "release" / "2026-07-12"
    manifest = il.archive([d1 / "review.txt", d2 / "review.txt"], into)
    archived = [Path(e["archived"]).name for e in manifest["entries"]]
    assert len(set(archived)) == 2, "both sources must survive with distinct names"
    contents = {(into / name).read_text() for name in archived}
    assert contents == {"from dir one", "from dir two"}, "no source clobbered"


# --------------------------------------------------------------------------- #
# skill-text + script ratchets (documented contract)
# --------------------------------------------------------------------------- #
def test_bundled_script_exists():
    assert SCRIPT.exists(), "skill must bundle ingest_letter.py"


def test_first_sentence_is_plain_and_searchable():
    first = SKILL.read_text().split("description:", 1)[1].split("\n", 1)[0].lower()
    for kw in ("decision letter", "reviewer", "ledger", "coverage"):
        assert kw in first, f"first sentence should mention {kw!r}"


def test_script_is_pure_io_no_llm_api():
    src = SCRIPT.read_text().lower()
    for banned in ("import anthropic", "import openai", "anthropic(", "openai("):
        assert banned not in src, "helper must not call an LLM API (pure I/O)"


def test_source_is_tool_agnostic():
    """The email-thread path names no hardcoded mail tool."""
    assert "gmail" not in SKILL.read_text().lower(), "no hardcoded mail tool in prescriptive steps"


# --------------------------------------------------------------------------- #
# CLI wiring (subprocess -> integration tier)
# --------------------------------------------------------------------------- #
@pytest.mark.integration
def test_cli_end_to_end_segment_dedupe_coverage(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    with ledger.open("w") as fh:
        for rev, src in [("R1", "reviewer1.txt"), ("R2", "reviewer2.txt")]:
            out = subprocess.run(
                [sys.executable, str(SCRIPT), "segment", str(FIX / src),
                 "--reviewer", rev],
                capture_output=True, text=True, check=True, env=child_env(),
            )
            fh.write(out.stdout)

    dd = subprocess.run(
        [sys.executable, str(SCRIPT), "dedupe", str(ledger)],
        capture_output=True, text=True, check=True, env=child_env(),
    )
    dedup = tmp_path / "ledger.dedup.jsonl"
    dedup.write_text(dd.stdout)
    assert len(dd.stdout.strip().splitlines()) == 6

    # No tickets mapped yet -> coverage must exit non-zero (all uncovered).
    cov = subprocess.run(
        [sys.executable, str(SCRIPT), "coverage", str(dedup),
         "--tickets", "0301,0302"],
        capture_output=True, text=True, env=child_env(),
    )
    assert cov.returncode == 1, "unmapped ledger is not covered"
    assert '"orphan_tickets"' in cov.stdout


def test_second_archive_preserves_provenance(tmp_path):
    source = tmp_path / "review.txt"
    source.write_text("first intake")
    into = tmp_path / "release"
    first = il.archive([source], into)["entries"][0]
    source.write_text("second intake")
    manifest = il.archive([source], into)
    assert manifest["entries"][0] == first
    assert len(manifest["entries"]) == 2
    assert Path(first["archived"]).read_text() == "first intake"
    assert json.loads((into / "manifest.json").read_text()) == manifest


def test_dispositions_roundtrip_and_separate_resolution(tmp_path):
    records = [il._normalize_record({
        "id": f"R1-{i}", "disposition": disposition, "reason": "author rationale",
        "resolution": "resolved" if disposition == "already_addressed" else "open",
        "evidence": ["manuscript.tex:42"] if disposition == "already_addressed" else [],
        "round": "r2",
    }) for i, disposition in enumerate(
        ["accepted", "rejected", "deferred", "already_addressed"])]
    stream = io.StringIO()
    il.write_ledger(records, stream)
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(stream.getvalue())
    assert il.read_ledger(ledger) == records
    report = il.coverage(il.read_ledger(ledger), set(), round_id="r2")
    assert il.coverage_ok(report)
    assert report["unresolved_remarks"] == ["R1-0", "R1-1", "R1-2"]


@pytest.mark.parametrize("fields", [
    {"disposition": "rejected"}, {"disposition": "deferred"},
    {"disposition": "invented"}, {"disposition": "already_addressed"},
    {"disposition": "accepted", "resolution": "resolved"},
])
def test_invalid_decision_or_unproved_resolution_blocks_coverage(fields):
    report = il.coverage([il._normalize_record({"id": "R1-01", **fields})], set())
    assert not il.coverage_ok(report)
    assert report["invalid_records"] == ["R1-01"]


def test_round_universe_separate_from_project_ticket_existence():
    records = [il._normalize_record({"id": "R1-01", "round": "r1", "tickets": ["0301"]}),
               il._normalize_record({"id": "R1-01", "round": "r2", "tickets": ["0302"]})]
    report = il.coverage(records, {"0302"}, existing_tickets={"0301", "0302", "0399"},
                         round_id="r2")
    assert il.coverage_ok(report)
    assert report["remark_count"] == 1
    report = il.coverage(records, {"0309"}, existing_tickets={"0301", "0302"}, round_id="r2")
    assert report["unknown_ticket_refs"] == ["0309"]
    assert report["out_of_round_ticket_refs"] == ["0302"]


def test_round_segmentation_and_dedupe_keep_sources_and_ids():
    first = il.segment("1. Same concern", "R1", "first.txt", round_id="r1")
    second = il.segment("1. Same concern", "R1", "second.txt", round_id="r2")
    out, summary = il.dedupe(first + second)
    assert summary["remarks"] == 2
    assert [r["id"] for r in out] == ["r1:R1-01", "r2:R1-01"]
    assert [r["source"] for r in out] == ["first.txt:1", "second.txt:1"]


@pytest.mark.integration
def test_cli_round_universe_and_existence_index(tmp_path):
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    (tickets / "0301-round.erg").write_text("x")
    (tickets / "0399-unrelated.erg").write_text("x")
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(json.dumps({"id": "r1:R1-01", "round": "r1", "tickets": ["0301"]}))
    result = subprocess.run([
        sys.executable, str(SCRIPT), "coverage", str(ledger), "--round", "r1",
        "--tickets", "0301", "--tickets-dir", str(tickets),
    ], capture_output=True, text=True, env=child_env())
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["orphan_tickets"] == []


@pytest.mark.integration
def test_cli_segment_retains_archived_path(tmp_path):
    source = tmp_path / "archived-review.txt"
    source.write_text("1. Concern")
    result = subprocess.run([
        sys.executable, str(SCRIPT), "segment", str(source), "--reviewer", "R1", "--round", "r2",
    ], capture_output=True, text=True, check=True, env=child_env())
    record = json.loads(result.stdout)
    assert record["source"] == f"{source}:1"
    assert record["round"] == "r2"
    assert record["id"] == "r2:R1-01"

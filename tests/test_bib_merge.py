"""Tests for scripts/bib-merge.py — BibTeX parsing and dedup contract.

Pins the deduplication strategy documented in the script's docstring:
DOI equality is authoritative; otherwise Jaccard title overlap >= 0.8 means
duplicate. Key collisions on a non-duplicate get a bumped suffix.
"""

import importlib.util

import pytest
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("bib_merge", SCRIPTS / "bib-merge.py")
bm = importlib.util.module_from_spec(spec)
sys.modules["bib_merge"] = bm
spec.loader.exec_module(bm)


# ── parsing ────────────────────────────────────────────────────────────────


def test_parse_bibtex_basic_fields():
    entries = bm.parse_bibtex(
        "@article{smith2020,\n  author = {Smith, Jane},\n"
        "  title = {A Study},\n  year = {2020},\n  doi = {10.1/x}\n}"
    )
    assert len(entries) == 1
    e = entries[0]
    assert e["_type"] == "article"
    assert e["_key"] == "smith2020"
    assert e["author"] == "Smith, Jane"
    assert e["title"] == "A Study"
    assert e["doi"] == "10.1/x"


def test_parse_bibtex_skips_string_and_preamble():
    entries = bm.parse_bibtex(
        '@string{foo = "bar"}\n@preamble{"x"}\n@book{k, title = {T}}'
    )
    assert [e["_key"] for e in entries] == ["k"]


def test_parse_bibtex_handles_nested_braces():
    entries = bm.parse_bibtex("@article{k, title = {A {Nested} Title}, year = {2021}}")
    assert entries[0]["title"] == "A {Nested} Title"
    assert entries[0]["year"] == "2021"


def test_extract_bibtex_fence():
    text = "intro\n```bibtex\n@book{k, title={T}}\n```\noutro"
    assert "@book{k" in bm._extract_bibtex_fence(text)
    assert "intro" not in bm._extract_bibtex_fence(text)


def test_extract_bibtex_fence_passthrough_when_absent():
    text = "@book{k, title={T}}"
    assert bm._extract_bibtex_fence(text) == text


# ── normalization ───────────────────────────────────────────────────────────


def test_normalize_doi_strips_prefixes():
    assert bm._normalize_doi("https://doi.org/10.1/AB") == "10.1/ab"
    assert bm._normalize_doi("doi:10.1/Z") == "10.1/z"
    assert bm._normalize_doi("10.1/Q") == "10.1/q"
    # www. and bare-host forms must fold onto the same key, not append a duplicate
    assert bm._normalize_doi("https://www.doi.org/10.1/AB") == "10.1/ab"
    assert bm._normalize_doi("doi.org/10.1/AB") == "10.1/ab"
    assert bm._normalize_doi("dx.doi.org/10.1/AB") == "10.1/ab"


def test_parse_bibtex_rejects_bare_type_opening():
    with pytest.raises(ValueError, match="declared BibTeX entries"):
        bm.parse_bibtex("@{k, title={T}, year={2020}}")


def test_normalize_name_variants():
    assert bm._normalize_name("Smith, Jane") == "smith"
    assert bm._normalize_name("Jane Smith") == "smith"
    assert bm._normalize_name("Jane Smith and Bob Jones") == "smith"  # first author
    # LaTeX accent + braces stripped, folded to ASCII
    assert bm._normalize_name(r"M\"uller, Anna") == "muller"
    assert bm._normalize_name("") == "unknown"


def test_base_key_is_author_plus_year():
    e = {"author": "Smith, Jane", "year": "2020"}
    assert bm._base_key(e) == "smith2020"


def test_title_similarity_threshold_boundaries():
    assert bm._title_similarity("alpha beta gamma", "alpha beta gamma") == 1.0
    assert bm._title_similarity("alpha beta", "gamma delta") == 0.0
    # identical word sets regardless of order
    assert bm._title_similarity("a b c", "c b a") == 1.0


# ── duplicate detection ─────────────────────────────────────────────────────


def test_is_duplicate_doi_match():
    a = {"doi": "10.1/x", "title": "Totally Different One"}
    b = {"doi": "https://doi.org/10.1/X", "title": "Another"}
    assert bm._is_duplicate(a, b) is True


def test_is_duplicate_differing_doi_is_not_dup():
    a = {"doi": "10.1/x", "title": "Same Title Words Here"}
    b = {"doi": "10.1/y", "title": "Same Title Words Here"}
    assert bm._is_duplicate(a, b) is False  # DOI is authoritative


def test_is_duplicate_title_overlap_above_threshold():
    a = {"title": "deep learning for climate modeling"}
    b = {"title": "deep learning for climate modeling systems"}
    # 5 shared / 6 union ~= 0.83 >= 0.8
    assert bm._is_duplicate(a, b) is True


def test_is_duplicate_title_overlap_below_threshold():
    a = {"title": "deep learning for climate"}
    b = {"title": "shallow trees for weather"}
    assert bm._is_duplicate(a, b) is False


def test_is_duplicate_unconfirmable_when_no_doi_no_title():
    assert bm._is_duplicate({}, {}) is False


# ── merge ────────────────────────────────────────────────────────────────────


def _refs(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "refs.bib"
    p.write_text(content)
    return p


def test_merge_adds_new_entry(tmp_path):
    refs_path = _refs(tmp_path, "@article{old2019, author={A}, year={2019}}\n")
    new = bm.parse_bibtex("@article{new2021, author={Brown, B}, year={2021}, title={X}}")
    refs = bm.parse_bibtex(refs_path.read_text())
    report = bm.merge(new, refs, refs_path)
    assert any(line.startswith("[ADDED] @new2021") for line in report)
    assert "@article{new2021" in refs_path.read_text()


def test_merge_skips_doi_duplicate(tmp_path):
    refs_path = _refs(
        tmp_path,
        "@article{smith2020, author={Smith, J}, year={2020}, "
        "title={Orig}, doi={10.1/x}}\n",
    )
    new = bm.parse_bibtex(
        "@article{smith2020, author={Smith, J}, year={2020}, "
        "title={Reformatted}, doi={10.1/x}}"
    )
    before = refs_path.read_text()
    report = bm.merge(new, bm.parse_bibtex(before), refs_path)
    assert any("[SKIPPED]" in line for line in report)
    assert refs_path.read_text() == before  # nothing appended


def test_merge_renames_on_key_collision_different_work(tmp_path):
    refs_path = _refs(
        tmp_path,
        "@article{smith2020, author={Smith, J}, year={2020}, "
        "title={First Paper}, doi={10.1/x}}\n",
    )
    # same base key, DIFFERENT doi → not a duplicate → must be renamed, not skipped
    new = bm.parse_bibtex(
        "@article{smith2020, author={Smith, J}, year={2020}, "
        "title={Second Paper}, doi={10.1/y}}"
    )
    report = bm.merge(new, bm.parse_bibtex(refs_path.read_text()), refs_path)
    assert any(line.startswith("[RENAMED->") for line in report)
    written = refs_path.read_text()
    assert "@article{smith2020b" in written  # suffix bumped


def test_merge_dry_run_does_not_write(tmp_path):
    refs_path = _refs(tmp_path, "@article{old2019, author={A}, year={2019}}\n")
    before = refs_path.read_text()
    new = bm.parse_bibtex("@article{new2021, author={Brown, B}, year={2021}}")
    bm.merge(new, bm.parse_bibtex(before), refs_path, dry_run=True)
    assert refs_path.read_text() == before


# ── CLI exit codes ───────────────────────────────────────────────────────────


def test_main_usage_error_returns_1():
    assert bm.main(["bib-merge.py"]) == 1


def test_main_missing_refs_returns_1(tmp_path):
    missing = tmp_path / "nope.bib"
    inp = tmp_path / "in.bib"
    inp.write_text("@book{k, title={T}}")
    assert bm.main(["bib-merge.py", str(inp), str(missing)]) == 1


def test_main_missing_input_returns_2(tmp_path):
    refs = _refs(tmp_path, "")
    assert bm.main(["bib-merge.py", str(tmp_path / "absent.bib"), str(refs)]) == 2


def test_merge_doi_identity_ignores_author_and_year(tmp_path):
    original = "@article{keepKey, author={Smith, J}, year={2020}, doi={10.1/X}}\n"
    refs = _refs(tmp_path, original)
    incoming = bm.parse_bibtex("@article{changed, author={Jones, A}, date={2021-04}, doi={https://doi.org/10.1/x}}")
    report = bm.merge(incoming, bm.parse_bibtex(original), refs)
    assert "[SKIPPED] @changed  (duplicate of @keepKey)" in report
    assert refs.read_text() == original


def test_date_year_fallback_preserves_distinct_works(tmp_path):
    original = "@book{keepKey, author={Smith, J}, year={2020}, title={Shared title}}\n"
    refs = _refs(tmp_path, original)
    incoming = bm.parse_bibtex("@book{duplicate, author={Smith, J}, date={2020-04-01}, title={Shared title}}\n"
                               "@book{distinct, author={Smith, J}, date={2021}, title={Shared title}}")
    report = bm.merge(incoming, bm.parse_bibtex(original), refs)
    assert "[SKIPPED] @duplicate  (duplicate of @keepKey)" in report
    assert any("[ADDED] @distinct" in line for line in report)
    assert refs.read_text().startswith(original)


def test_doi_index_includes_entries_added_in_same_batch(tmp_path):
    refs = _refs(tmp_path, "")
    incoming = bm.parse_bibtex("@book{first, year={2020}, doi={10.1/x}}\n"
                               "@book{second, date={2021}, doi={10.1/X}}")
    report = bm.merge(incoming, [], refs)
    assert "[SKIPPED] @second  (duplicate of @first)" in report


def test_malformed_input_refuses_to_append(tmp_path, capsys):
    original = "@book{keepKey, title={Keep}}\n"
    refs = _refs(tmp_path, original)
    incoming = tmp_path / "new.bib"
    incoming.write_text("@book{valid, title={New}}\n@book{broken, title={unclosed}")
    assert bm.main(["bib-merge.py", str(incoming), str(refs)]) == 3
    assert "could not be parsed" in capsys.readouterr().err
    assert refs.read_text() == original


def test_new_entry_macros_are_materialized_without_changing_existing_bytes(tmp_path):
    original = b"% retain CRLF and key\r\n@book{OriginalKey, title={Keep}}\r\n"
    refs = tmp_path / "refs.bib"
    refs.write_bytes(original)
    incoming = bm.parse_bibtex('@string{label = "Expanded"}\n'
                               '@online(newKey, title=label # " title", date={2021-01})')
    bm.merge(incoming, bm.parse_bibtex(refs.read_text()), refs, dry_run=True)
    assert refs.read_bytes() == original
    bm.merge(incoming, bm.parse_bibtex(refs.read_text()), refs)
    assert refs.read_bytes().startswith(original)
    appended = bm.parse_bibtex(refs.read_text())
    assert appended[1]["title"] == "Expanded title"
    assert appended[1]["_key"] == "newKey"


def test_unread_existing_entry_refuses_append(tmp_path, capsys):
    original = "@book{keep, title={Keep}}\n@book{unread, broken}"
    refs = _refs(tmp_path, original)
    incoming = tmp_path / "new.bib"
    incoming.write_text("@book{new, title={New}}")
    assert bm.main(["bib-merge.py", str(incoming), str(refs)]) == 3
    assert "could not be parsed" in capsys.readouterr().err
    assert refs.read_text() == original


def test_batch_duplicate_report_uses_final_renamed_key(tmp_path):
    original = "@book{collision, author={Smith}, year={2020}, doi={10.1/old}}"
    refs = _refs(tmp_path, original)
    incoming = bm.parse_bibtex("@book{collision, author={Smith}, date={2020}, doi={10.1/new}}\n"
                               "@book{duplicate, year={2021}, doi={10.1/new}}")
    report = bm.merge(incoming, bm.parse_bibtex(original), refs)
    renamed = next(line for line in report if line.startswith("[RENAMED->"))
    key = renamed.split("->", 1)[1].split("]", 1)[0]
    assert f"[SKIPPED] @duplicate  (duplicate of @{key})" in report


def test_braced_author_names_keep_distinct_identities(tmp_path):
    original = "@book{first, author={{Alpha}}, year={2020}, title={Shared title}}"
    refs = _refs(tmp_path, original)
    incoming = bm.parse_bibtex("@book{second, author={{Beta}}, date={2020}, title={Shared title}}")
    report = bm.merge(incoming, bm.parse_bibtex(original), refs)
    assert "[ADDED] @second" in report

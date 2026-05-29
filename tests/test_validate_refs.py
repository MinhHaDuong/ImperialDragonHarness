"""Tests for scripts/validate-refs.py — parsing and the exit-code contract.

The script's verdict is its exit code (0 PASS/WARN, 1 FAIL, 2 ERROR,
3 usage/parse). We stub `requests` in sys.modules before importing so the
suite is fully hermetic — it never installs requests and never hits the
network — and drive the fetch outcomes by monkeypatching `_fetch`.
"""

import importlib.util
import sys
import types
from pathlib import Path

# --- stub `requests` so the module imports without the real dependency -------
_fake_requests = types.ModuleType("requests")
_fake_exceptions = types.ModuleType("requests.exceptions")


class _ConnErr(Exception):
    pass


class _Timeout(Exception):
    pass


class _ReqErr(Exception):
    pass


_fake_exceptions.ConnectionError = _ConnErr
_fake_exceptions.Timeout = _Timeout
_fake_exceptions.RequestException = _ReqErr
_fake_requests.exceptions = _fake_exceptions
_fake_requests.get = lambda *a, **k: (_ for _ in ()).throw(
    AssertionError("network call escaped the test stub")
)
sys.modules.setdefault("requests", _fake_requests)
sys.modules.setdefault("requests.exceptions", _fake_exceptions)

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("validate_refs", SCRIPTS / "validate-refs.py")
vr = importlib.util.module_from_spec(spec)
sys.modules["validate_refs"] = vr
spec.loader.exec_module(vr)


# ── parsing helpers ──────────────────────────────────────────────────────────


def test_extract_bibliography_block():
    text = "## Methods\nstuff\n## Bibliography\n@book{k}\n## Notes\ntail"
    block = vr._extract_bibliography_block(text)
    assert "@book{k}" in block
    assert "tail" not in block


def test_extract_bibliography_block_absent():
    assert vr._extract_bibliography_block("## Methods\nonly") == ""


def test_split_entries():
    block = "@article{key1,\n  doi = {10.1/x},\n}\n@book{key2,\n  title = {T},\n}\n"
    entries = vr._split_entries(block)
    assert [k for k, _ in entries] == ["key1", "key2"]


def test_field_extraction_variants():
    body = '  doi = {10.1/x},\n  title = "Quoted",\n  year = 2020,\n'
    assert vr._field(body, "doi") == "10.1/x"
    assert vr._field(body, "title") == "Quoted"
    assert vr._field(body, "year") == "2020"
    assert vr._field(body, "missing") is None


def test_build_url_doi_priority():
    body = "doi = {https://doi.org/10.5/AB},\nurl = {http://example.com},\n"
    url, kind = vr._build_url("k", body)
    assert kind == "doi"
    assert url == "https://doi.org/10.5/AB"


def test_build_url_arxiv_eprint():
    body = "eprint = {2401.01234},\neprinttype = {arxiv},\n"
    url, kind = vr._build_url("k", body)
    assert kind == "arxiv"
    assert url.endswith("2401.01234")


def test_build_url_hal_eprint():
    body = "eprint = {hal-12345},\neprinttype = {hal},\n"
    url, kind = vr._build_url("k", body)
    assert kind == "hal"


def test_build_url_url_fallback():
    body = "url = {https://example.org/p},\n"
    assert vr._build_url("k", body) == ("https://example.org/p", "url")


def test_build_url_none_when_no_identifier():
    assert vr._build_url("k", "title = {No ids here},\n") == (None, "none")


# ── exit-code contract ───────────────────────────────────────────────────────


def _note(tmp_path: Path, body_entries: str) -> Path:
    """Write a minimal note with Methods + Bibliography sections."""
    p = tmp_path / "note.md"
    p.write_text("## Methods\nm\n\n## Bibliography\n" + body_entries)
    return p


def test_usage_error_wrong_argc():
    assert vr.main(["validate-refs.py"]) == 3


def test_missing_file_returns_3(tmp_path):
    assert vr.main(["validate-refs.py", str(tmp_path / "nope.md")]) == 3


def test_no_bibliography_section_returns_3(tmp_path):
    p = tmp_path / "n.md"
    p.write_text("## Methods\nonly methods here")
    assert vr.main(["validate-refs.py", str(p)]) == 3


def test_no_methods_section_returns_3(tmp_path):
    p = tmp_path / "n.md"
    p.write_text("## Bibliography\n@book{k,\n title = {T},\n}\n")
    assert vr.main(["validate-refs.py", str(p)]) == 3


def test_pass_when_all_resolve(tmp_path, monkeypatch):
    note = _note(tmp_path, "@article{a,\n doi = {10.1/x},\n}\n@article{b,\n doi = {10.1/y},\n}\n")
    monkeypatch.setattr(vr, "_fetch", lambda url: (200, url, False))
    assert vr.main(["validate-refs.py", str(note)]) == 0


def test_warn_when_entry_has_no_identifier(tmp_path, monkeypatch):
    note = _note(tmp_path, "@misc{a,\n note = {no id},\n}\n")
    # no fetch should happen for an identifier-less entry
    monkeypatch.setattr(vr, "_fetch", lambda url: (200, url, False))
    assert vr.main(["validate-refs.py", str(note)]) == 0


def test_fail_on_non_200(tmp_path, monkeypatch):
    note = _note(tmp_path, "@article{a,\n doi = {10.1/x},\n}\n")
    monkeypatch.setattr(vr, "_fetch", lambda url: (404, url, False))
    assert vr.main(["validate-refs.py", str(note)]) == 1


def test_error_on_consecutive_connection_failures(tmp_path, monkeypatch):
    note = _note(
        tmp_path,
        "@article{a,\n doi={10.1/a},\n}\n@article{b,\n doi={10.1/b},\n}\n"
        "@article{c,\n doi={10.1/c},\n}\n@article{d,\n doi={10.1/d},\n}\n",
    )
    monkeypatch.setattr(vr, "_fetch", lambda url: (None, url, True))
    # 3 consecutive connection errors trips the ERROR escalation
    assert vr.main(["validate-refs.py", str(note)]) == 2

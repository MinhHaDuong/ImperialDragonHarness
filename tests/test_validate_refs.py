"""Tests for scripts/validate-refs.py — parsing and the exit-code contract.

The script's verdict is its exit code (0 PASS/WARN, 1 FAIL, 2 ERROR,
3 usage/parse). We stub `requests` in sys.modules before importing so the
suite is fully hermetic — it never installs requests and never hits the
network — and drive the fetch outcomes by monkeypatching `_fetch`.
"""

import importlib.util

import pytest
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


def test_build_url_doi_priority():
    body = {"doi": "https://doi.org/10.5/AB", "url": "http://example.com"}
    url, kind = vr._build_url("k", body)
    assert kind == "doi"
    assert url == "https://doi.org/10.5/AB"


@pytest.mark.parametrize("doi", ["https://www.doi.org/10.1/x", "doi.org/10.1/x",
                                 "DOI:10.1/x", "http://dx.doi.org/10.1/x"])
def test_build_url_strips_every_doi_prefix(doi):
    assert vr._build_url("k", {"doi": doi}) == (vr.DOI_BASE + "10.1/x", "doi")


def test_split_entries_rejects_bare_type_opening():
    with pytest.raises(ValueError, match="declared BibTeX entries"):
        vr._split_entries("@{k, title={T}}")


def test_build_url_arxiv_eprint():
    body = {"eprint": "2401.01234", "eprinttype": "arxiv"}
    url, kind = vr._build_url("k", body)
    assert kind == "arxiv"
    assert url.endswith("2401.01234")


def test_build_url_hal_eprint():
    body = {"eprint": "hal-12345", "eprinttype": "hal"}
    url, kind = vr._build_url("k", body)
    assert kind == "hal"


def test_build_url_url_fallback():
    body = {"url": "https://example.org/p"}
    assert vr._build_url("k", body) == ("https://example.org/p", "url")


def test_build_url_none_when_no_identifier():
    assert vr._build_url("k", {"title": "No ids here"}) == (None, "none")


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


def test_inline_and_multiline_entries_are_all_checked(tmp_path, monkeypatch, capsys):
    note = _note(tmp_path, "@article{inline, doi={10.1/x}}\n"
                 "@book{multi,\n url={https://example.org/y},\n}\n")
    fetched = []
    def fetch(url):
        fetched.append(url)
        return 200, url, False
    monkeypatch.setattr(vr, "_fetch", fetch)
    assert vr.main(["validate-refs.py", str(note)]) == 0
    assert fetched == ["https://doi.org/10.1/x", "https://example.org/y"]
    assert "2 entries" in capsys.readouterr().out


def test_unread_entry_is_parse_error_before_any_fetch(tmp_path, monkeypatch, capsys):
    note = _note(tmp_path, "@book{ok, doi={10.1/x}}\n@article{broken, title={unclosed}")
    monkeypatch.setattr(vr, "_fetch", lambda url: (_ for _ in ()).throw(AssertionError(url)))
    assert vr.main(["validate-refs.py", str(note)]) == 3
    assert "could not be parsed" in capsys.readouterr().err


def test_biblatex_parentheses_macros_and_nested_fields(tmp_path, monkeypatch):
    note = _note(tmp_path, '@string{host = "https://example.org/"}\n'
                 '@online(key, title={A {Nested} Work}, url=host # "paper")')
    fetched = []
    monkeypatch.setattr(vr, "_fetch", lambda url: (fetched.append(url) or 200, url, False))
    assert vr.main(["validate-refs.py", str(note)]) == 0
    assert fetched == ["https://example.org/paper"]


def test_parsed_field_variants():
    _, fields = vr._split_entries('@book{k, doi={10.1/x}, title="Quoted", year=2020}')[0]
    assert fields["doi"] == "10.1/x"
    assert fields["title"] == "Quoted"
    assert fields["year"] == "2020"


def test_http_pass_is_accessibility_only(tmp_path, monkeypatch, capsys):
    note = _note(tmp_path, "@book{k, url={https://example.org/expected}}")
    monkeypatch.setattr(vr, "_fetch", lambda url: (200, "https://example.org/other-work", False))
    assert vr.main(["validate-refs.py", str(note)]) == 0
    out = capsys.readouterr()
    assert out.out == "PASS — 1 entries accessible via HTTP\n"
    assert "other-work" in out.err

"""The fulltext fallback tries all open channels before shadow libraries."""

from types import SimpleNamespace

from scripts.fulltext_cascade import retrieve


def test_doi_tries_shadow_only_after_open_failure():
    calls = []

    def cascade(kind, identifier, path, names):
        calls.append((kind, identifier, tuple(names)))
        return SimpleNamespace(
            status="success" if names == ["scihub"] else "failed",
            source="scihub" if names == ["scihub"] else "ezproxy",
            path=path,
            error=None,
        )

    result = retrieve("doi", "10.1234/example", "paper.pdf", cascade, lambda _: [])
    assert calls == [
        (
            "doi",
            "10.1234/example",
            ("crossref", "unpaywall", "openalex", "hal", "istex", "ezproxy"),
        ),
        ("doi", "10.1234/example", ("scihub",)),
    ]
    assert result.source == "scihub"


def test_book_checks_all_open_dois_before_libgen():
    calls = []

    def cascade(kind, identifier, path, names):
        calls.append((kind, identifier, tuple(names)))
        return SimpleNamespace(
            status="failed", source=names[-1], path=None, error="not found"
        )

    retrieve(
        "isbn", "9780674009691", "book.pdf", cascade, lambda _: ["10.1/a", "10.1/b"]
    )
    assert [x[1] for x in calls] == ["10.1/a", "10.1/b", "9780674009691"]
    assert calls[-1][2] == ("libgen",)


def test_open_success_stops_before_shadow_and_preserves_source():
    calls = []

    def cascade(kind, identifier, path, names):
        calls.append(names)
        return SimpleNamespace(status="success", source="hal", path=path, error=None)

    result = retrieve("doi", "10.1234/a", "paper.pdf", cascade, lambda _: [])
    assert result.source == "hal"
    assert len(calls) == 1


def test_skipped_file_does_not_claim_source():
    def cascade(kind, identifier, path, names):
        return SimpleNamespace(
            status="skipped", source="crossref", path=path, error=None
        )

    result = retrieve("doi", "10.1234/a", "paper.pdf", cascade, lambda _: [])
    assert result.status == "skipped"


def test_isbn_lookup_error_does_not_claim_open_exhaustion():
    calls = []

    def fail_lookup(_):
        raise RuntimeError("Crossref unavailable")

    import pytest

    with pytest.raises(RuntimeError, match="Crossref unavailable"):
        retrieve(
            "isbn",
            "9780674009691",
            "book.pdf",
            lambda *args: calls.append(args),
            fail_lookup,
        )
    assert not calls


def test_empty_isbn_lookup_attempts_libgen():
    calls = []

    def cascade(kind, identifier, path, names):
        calls.append((kind, identifier, tuple(names)))
        return SimpleNamespace(status="success", source="libgen", path=path, error=None)

    result = retrieve("isbn", "9780674009691", "book.pdf", cascade, lambda _: [])
    assert calls == [("isbn", "9780674009691", ("libgen",))]
    assert result.source == "libgen"


def test_cli_reports_the_actual_open_source(tmp_path, monkeypatch, capsys):
    import json
    import sys

    import doifetch.api
    import doifetch.naming
    from doifetch.sources.contract import Result

    from scripts.fulltext_cascade import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fulltext_cascade.py",
            "--phase",
            "open",
            "--doi",
            "10.1234/example",
            "--title",
            "Example",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(doifetch.naming, "resolve_name", lambda *args: "Example")
    monkeypatch.setattr(
        doifetch.api,
        "cascade",
        lambda req, names: Result("success", "hal", path=req.path),
    )
    assert main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["source"] == "hal"
    assert report["path"] == str(tmp_path / "Example.pdf")


def test_cli_reports_unknown_source_for_existing_file(tmp_path, monkeypatch, capsys):
    import json
    import sys

    from scripts.fulltext_cascade import main

    target = tmp_path / "Example.pdf"
    target.write_bytes(b"existing")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fulltext_cascade.py",
            "--phase",
            "open",
            "--isbn",
            "9780674009691",
            "--title",
            "Example",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["source"] is None
    assert target.read_bytes() == b"existing"


def test_hal_receives_metadata_name_for_bare_title(tmp_path, monkeypatch, capsys):
    import json
    import sys
    import doifetch.api
    import doifetch.naming
    from doifetch.sources.contract import Result
    from doifetch.sources.hal import _parse_author_title
    from scripts.fulltext_cascade import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fulltext_cascade.py",
            "--phase",
            "open",
            "--doi",
            "10.1234/example",
            "--title",
            "A title",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(
        doifetch.naming,
        "resolve_name",
        lambda doi, title, *a: title or "Author 2020 - A title",
    )

    def cascade(req, names):
        assert _parse_author_title(Path(req.path).stem) == ("Author", "A title")
        return Result("success", "hal", path=req.path)

    from pathlib import Path

    monkeypatch.setattr(doifetch.api, "cascade", cascade)
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["source"] == "hal"


def test_keep_title_preserves_filename_but_supplies_hal_metadata(
    tmp_path, monkeypatch, capsys
):
    import json
    import sys
    from pathlib import Path
    import doifetch.api
    import doifetch.naming
    from doifetch.sources.contract import Result
    from doifetch.sources.hal import _parse_author_title
    from scripts.fulltext_cascade import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fulltext_cascade.py",
            "--phase",
            "open",
            "--doi",
            "10.1234/example",
            "--title",
            "A title",
            "--keep-title",
            "--no-check-zotero",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(
        doifetch.naming,
        "resolve_name",
        lambda doi, title, *a: title or "Author 2020 - A title",
    )

    def cascade(req, names):
        assert _parse_author_title(Path(req.path).stem) == ("Author", "A title")
        Path(req.path).write_bytes(b"PDF content")
        return Result("success", "hal", path=req.path)

    monkeypatch.setattr(doifetch.api, "cascade", cascade)
    assert main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["path"] == str(tmp_path / "A title.pdf")
    assert (tmp_path / "A title.pdf").read_bytes() == b"PDF content"
    assert report["source"] == "hal"


def test_unavailable_hal_query_stops_before_shadow(tmp_path, monkeypatch, capsys):
    import json
    import sys
    import doifetch.api
    import doifetch.naming
    from doifetch.sources.contract import Result
    from scripts.fulltext_cascade import main

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "fulltext_cascade.py",
            "--phase",
            "open",
            "--doi",
            "10.1234/example",
            "--title",
            "Bare title",
            "--keep-title",
            "--output-dir",
            str(tmp_path),
        ],
    )
    monkeypatch.setattr(
        doifetch.naming, "resolve_name", lambda doi, title, *args: title
    )
    monkeypatch.setattr(
        doifetch.api,
        "cascade",
        lambda req, names: Result(
            "failed",
            "ezproxy",
            error="hal: Cannot parse author/title for HAL search; ezproxy: unavailable",
        ),
    )
    assert main() == 3
    assert "Cannot parse author/title" in json.loads(capsys.readouterr().out)["error"]

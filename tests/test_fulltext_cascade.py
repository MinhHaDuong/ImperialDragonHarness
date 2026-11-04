"""The fulltext fallback tries all open channels before shadow libraries."""
from types import SimpleNamespace

from scripts.fulltext_cascade import retrieve


def test_doi_tries_shadow_only_after_open_failure():
    calls = []
    def cascade(kind, identifier, path, names):
        calls.append((kind, identifier, tuple(names)))
        return SimpleNamespace(status='success' if names == ['scihub'] else 'failed', source='scihub' if names == ['scihub'] else 'ezproxy', path=path, error=None)
    result = retrieve('doi', '10.1234/example', 'paper.pdf', cascade, lambda _: [])
    assert calls == [('doi', '10.1234/example', ('crossref', 'unpaywall', 'openalex', 'hal', 'istex', 'ezproxy')), ('doi', '10.1234/example', ('scihub',))]
    assert result.source == 'scihub'


def test_book_checks_all_open_dois_before_libgen():
    calls = []
    def cascade(kind, identifier, path, names):
        calls.append((kind, identifier, tuple(names)))
        return SimpleNamespace(status='failed', source=names[-1], path=None, error='not found')
    retrieve('isbn', '9780674009691', 'book.pdf', cascade, lambda _: ['10.1/a', '10.1/b'])
    assert [x[1] for x in calls] == ['10.1/a', '10.1/b', '9780674009691']
    assert calls[-1][2] == ('libgen',)


def test_open_success_stops_before_shadow_and_preserves_source():
    calls = []
    def cascade(kind, identifier, path, names):
        calls.append(names)
        return SimpleNamespace(status='success', source='hal', path=path, error=None)
    result = retrieve('doi', '10.1234/a', 'paper.pdf', cascade, lambda _: [])
    assert result.source == 'hal'
    assert len(calls) == 1


def test_skipped_file_does_not_claim_source():
    def cascade(kind, identifier, path, names):
        return SimpleNamespace(status='skipped', source='crossref', path=path, error=None)
    result = retrieve('doi', '10.1234/a', 'paper.pdf', cascade, lambda _: [])
    assert result.status == 'skipped'

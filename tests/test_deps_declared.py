"""Every third-party module imported by harness code is declared.

Ticket 0530. PyYAML reached CI only through the ubuntu-latest image and the
pre-commit hook only through whatever the machine happened to have: green by
environmental coincidence, not by contract. The declaration lives in
``requirements-dev.txt`` — the one place both CI (pytest-guard installs from
it) and a fresh machine read.

The guard derives imports from the *source* (``ast``), never from the
declaration file it checks — a test that reads the same list it verifies
passes forever (the hollow-guard trap). Membership is decided by what a file
*is*, not its suffix: ``.py`` files, extensionless python-shebang programs
(``bin/usage-report``), and the quoted python heredocs embedded in shell
scripts — the production consumer of PyYAML is the heredoc in
``scripts/gen-skills-catalog.sh``, which a ``*.py``-only scan would leave
pinned by test files that coincidentally import yaml.

Per the positive-control rule (a null result is not a finding until a
positive control has fired): the scan must rediscover a known third-party
import through *each* extraction path before its "all declared" verdict is
worth anything.

skills/ is outside the ticket's scope ("tout module importé par tests/ et
scripts/") — per-skill runtime deps (e.g. openai in external-peer-review)
are a separate contract.
"""

import ast
import functools
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
REQUIREMENTS = REPO / "requirements-dev.txt"
SCAN_DIRS = ("scripts", "tests", "hooks", "bin")
# Mutation-audit sample files, not code this repo runs — same policy as
# pytest.ini's norecursedirs (ticket 0219), stated there for collection and
# here for scanning.
EXCLUDED_ROOT = REPO / "tests" / "fixtures"

# Import name → PyPI distribution name, where they differ (PEP 503-normalized).
IMPORT_TO_DIST = {
    "yaml": "pyyaml",
}

# One control per extraction path: a plain .py import and a shell-heredoc
# import. If either ever fails, the corresponding scanner path is broken,
# not the tree clean.
POSITIVE_CONTROLS = {
    "yaml": {"tests/test_skill_frontmatter.py", "scripts/gen-skills-catalog.sh"},
}

# Only a QUOTED delimiter (<<'EOF') guarantees the body is literal,
# unexpanded python that ast can parse; an unquoted heredoc undergoes shell
# expansion and cannot be scanned this way (none exists in the repo today).
# The interpreter must be invoked as a command — not appear inside a path
# like `cat > "$dir/python3" <<'STUB'` (a fake-binary fixture, whose body
# is bash).
HEREDOC_OPEN = re.compile(r"(?:^|[^/\w])python3?\b.*<<-?\s*['\"](\w+)['\"]")


def _python_heredocs(text: str):
    lines = iter(text.splitlines())
    for line in lines:
        m = HEREDOC_OPEN.search(line)
        if not m:
            continue
        delim = m.group(1)
        body = []
        for body_line in lines:
            if body_line.strip() == delim:
                break
            body.append(body_line)
        yield "\n".join(body)


@functools.lru_cache(maxsize=1)
def python_sources() -> tuple[tuple[str, str], ...]:
    """(repo-relative path, python source) pairs — both tests share one walk."""
    out = []
    for dirname in SCAN_DIRS:
        for path in sorted((REPO / dirname).rglob("*")):
            if not path.is_file() or path.is_relative_to(EXCLUDED_ROOT):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # binary, not a python source
            rel = path.relative_to(REPO).as_posix()
            if path.suffix == ".py" or text.startswith("#!") and "python" in text.splitlines()[0]:
                out.append((rel, text))
            else:
                out.extend((rel, body) for body in _python_heredocs(text))
    return tuple(out)


def third_party_imports() -> dict[str, set[str]]:
    """Map of top-level third-party module name → files importing it."""
    stdlib = set(sys.stdlib_module_names)
    # A sibling imported via sys.path manipulation (beat, git_utils, …) is
    # local, not third-party: local means a scanned-file stem.
    locals_ = {Path(rel).stem for rel, _ in python_sources()}
    found: dict[str, set[str]] = {}
    for rel, text in python_sources():
        tree = ast.parse(text, filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top in stdlib or top in locals_:
                    continue
                found.setdefault(top, set()).add(rel)
    return found


def _normalize(name: str) -> str:
    # PEP 503 normalization, so "PyYAML" and "pyyaml" compare equal.
    return re.sub(r"[-_.]+", "-", name).lower()


def declared_dists() -> set[str]:
    assert REQUIREMENTS.is_file(), (
        f"{REQUIREMENTS.name} not found — third-party dependencies must be "
        "declared where CI and a fresh machine both read them (ticket 0530)"
    )
    dists = set()
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", line)
        if m:
            dists.add(_normalize(m.group(0)))
    return dists


@pytest.mark.adherence
def test_scanner_finds_known_imports():
    # Positive controls: a scan whose "nothing undeclared" is indistinguishable
    # from "I could not look" is not a check — and each extraction path (.py
    # file, shell heredoc) needs its own control.
    found = third_party_imports()
    for module, expected_files in POSITIVE_CONTROLS.items():
        missing = expected_files - found.get(module, set())
        assert not missing, (
            f"scanner failed to find the known import {module!r} in "
            f"{sorted(missing)} — that extraction path is broken"
        )


@pytest.mark.adherence
def test_third_party_imports_are_declared():
    declared = declared_dists()
    offenders = []
    for module, files in sorted(third_party_imports().items()):
        dist = IMPORT_TO_DIST.get(module) or _normalize(module)
        if dist not in declared:
            offenders.append(f"{module} (imported by {', '.join(sorted(files))})")
    assert not offenders, (
        "third-party imports missing from requirements-dev.txt — an ambient "
        "interpreter that happens to have them is not a contract "
        "(ticket 0530):\n  " + "\n  ".join(offenders)
    )

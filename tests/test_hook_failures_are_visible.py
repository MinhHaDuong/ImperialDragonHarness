"""A totally broken hook must turn its own CLI suite red.

Both hook entry points wrap ``main()`` in ``except (Exception, SystemExit)`` and
exit 0. That is the right production contract — an advisory hook must never
block the tool nor print a traceback into the model's context — and it is not
what this module questions. What it questions is the consequence: on exit code
and stdout, the only two channels a subprocess-driven test can read, a total
crash and a correct silent no-op become byte-identical, so every test whose
expectation is "silent" is satisfied by a script that does nothing at all.
Measured on 2026-08-26 with the entry points made to raise unconditionally: 14
of 26 CLI-driven tests of ``knowledge_hints`` and 3 of 5 of
``inject_rule_on_edit`` still passed, among them both guards against
exfiltration into the model's context (ticket 0610).

``IDH_HOOK_STRICT=1`` closes that. This module is what keeps it closed. A
one-off check would not: the wiring is per-call-site (four of the five child
environments in the sibling suite are closed dicts a fixture cannot reach), so
one new test written the old way silently returns a guard to being
unfalsifiable, and nothing would say so.

Method — and note what it does *not* do. It does not enumerate which tests are
CLI-driven; a hand-kept list is the thing that goes stale. It copies the hook,
its shared helper and its suite into a throwaway tree, makes the entry points
raise, and runs the suite there under a conftest that records, per test, whether
that test actually spawned the hook. Then a test that spawned a hook known to be
totally broken and still passed is the defect, and a test that never spawned it
is out of the blast radius by construction. Sabotage is applied to the *copy*:
the real tree is never edited, so a hard kill cannot leave it broken.

The launch count is the positive control. A probe that watches for subprocess
launches and sees none reports "nothing masked" and "I could not look" with the
same silence, so the floor below has to fire before the verdict is worth
anything.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

# `adherence` because this is a contract gate, not a unit of the hooks' logic:
# it belongs in `make lint`, apart from the development loop. `integration`
# because it also spawns pytest and the hooks themselves, and the tier table
# classifies by cost — the marker-hygiene ratchet in test_test_quality.py holds
# the second one to that.
pytestmark = [pytest.mark.adherence, pytest.mark.integration]

REPO = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Case:
    script: str
    entries: tuple[str, ...]  # functions to make raise
    suite: str
    min_cli_tests: int  # ratchet: today's count of tests that spawn the hook


CASES = [
    Case("knowledge_hints.py", ("cmd_catalog", "cmd_prompt"),
         "test_knowledge_hints.py", 26),
    Case("inject_rule_on_edit.py", ("main",),
         "test_inject_rule_on_edit.py", 5),
]

# Written into the throwaway tree, not part of the repo suite. Pairing outcome
# with "did this test actually spawn the hook" is the whole mechanism: without
# it the guard would need a hand-kept list of CLI tests, which is exactly the
# artifact that rots.
CONFTEST = '''\
"""Injected by tests/test_hook_failures_are_visible.py. Not a repo conftest."""

import json
import os
import subprocess
from pathlib import Path

_HOOKS = set(os.environ["HOOK_GUARD_SCRIPTS"].split(","))
_REPORT = Path(os.environ["HOOK_GUARD_REPORT"])
_state = {"nodeid": None}
_launched = set()
_outcome = {}
_orig_run = subprocess.run


def _spy(*args, **kwargs):
    argv = args[0] if args else kwargs.get("args")
    if isinstance(argv, (list, tuple)):
        for a in argv:
            if isinstance(a, (str, os.PathLike)) and Path(os.fspath(a)).name in _HOOKS:
                if _state["nodeid"]:
                    _launched.add(_state["nodeid"])
                break
    return _orig_run(*args, **kwargs)


subprocess.run = _spy


def pytest_runtest_setup(item):
    _state["nodeid"] = item.nodeid


def pytest_runtest_logreport(report):
    if report.when in ("setup", "call") and report.outcome != "passed":
        _outcome[report.nodeid] = report.outcome
    elif report.when == "call":
        _outcome.setdefault(report.nodeid, report.outcome)


def pytest_sessionfinish(session, exitstatus):
    _REPORT.write_text(
        json.dumps({"launched": sorted(_launched), "outcome": _outcome}),
        encoding="utf-8",
    )
'''


def _sabotage(src: str, fn: str) -> str:
    pat = re.compile(r"^(def %s\([^\n]*\)[^\n]*:\n)" % re.escape(fn), re.M)
    assert pat.search(src), f"entry point {fn}() not found — this guard is stale"
    return pat.sub(lambda m: m.group(1) + '    raise RuntimeError("SABOTAGE")\n',
                   src, count=1)


def _run_sabotaged(root: Path, case: Case) -> dict:
    (root / "scripts").mkdir(parents=True)
    (root / "tests").mkdir()
    shutil.copy(REPO / "pytest.ini", root / "pytest.ini")
    shutil.copy(REPO / "scripts" / "path_utils.py", root / "scripts" / "path_utils.py")
    src = (REPO / "scripts" / case.script).read_text(encoding="utf-8")
    for fn in case.entries:
        src = _sabotage(src, fn)
    (root / "scripts" / case.script).write_text(src, encoding="utf-8")
    shutil.copy(REPO / "tests" / case.suite, root / "tests" / case.suite)
    (root / "tests" / "conftest.py").write_text(CONFTEST, encoding="utf-8")

    report = root / "report.json"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "--no-header"],
        cwd=root, capture_output=True, text=True,
        env={**os.environ,
             "HOOK_GUARD_SCRIPTS": case.script,
             "HOOK_GUARD_REPORT": str(report)},
    )
    assert report.exists(), (
        f"the sabotaged run of {case.suite} produced no report; pytest said:\n"
        f"{proc.stdout[-3000:]}\n{proc.stderr[-2000:]}"
    )
    return json.loads(report.read_text(encoding="utf-8"))


def _sabotaged_copy(root: Path, case: Case) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO / "scripts" / "path_utils.py", root / "path_utils.py")
    src = (REPO / "scripts" / case.script).read_text(encoding="utf-8")
    for fn in case.entries:
        src = _sabotage(src, fn)
    target = root / case.script
    target.write_text(src, encoding="utf-8")
    return target


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.script)
def test_production_default_still_swallows_the_crash(tmp_path, case):
    """Without the switch, a hook that raises must still exit 0 and print nothing.

    This is the invariant the whole change is built around, and it is the one a
    strictness knob most plausibly breaks. A PreToolUse hook exiting non-zero is
    read as "block the tool"; the term channel has no shell wrapper to absorb a
    traceback and would print one on every prompt of the session. So the default
    is asserted here, on the same sabotaged script the guard above requires to
    turn a suite red — the two together say the behaviour changed for the tests
    and for nothing else.
    """
    script = _sabotaged_copy(tmp_path / "prod", case)
    res = subprocess.run(
        [sys.executable, str(script), *(["catalog"] if case.entries[0] != "main" else [])],
        input="", capture_output=True, text=True,
        env={k: v for k, v in os.environ.items() if k != "IDH_HOOK_STRICT"},
    )
    assert res.returncode == 0, f"a crashed hook exited {res.returncode}: {res.stderr}"
    assert res.stdout == "", f"a crashed hook printed to stdout: {res.stdout!r}"


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.script)
def test_sabotaged_hook_is_caught_by_its_own_suite(tmp_path, case):
    rep = _run_sabotaged(tmp_path / case.script.removesuffix(".py"), case)
    launched = rep["launched"]

    assert len(launched) >= case.min_cli_tests, (
        f"only {len(launched)} tests of {case.suite} spawned {case.script}; "
        f"expected at least {case.min_cli_tests}. This floor is the positive "
        f"control: a probe that sees no launches reports 'nothing masked' and "
        f"'I could not look' with the same silence. A drop here means the "
        f"suite stopped driving the real CLI, not that it got safer."
    )

    masked = sorted(n for n in launched if rep["outcome"].get(n) == "passed")
    assert masked == [], (
        f"{len(masked)} test(s) of {case.suite} passed while {case.script} was "
        f"made to raise on every run:\n  " + "\n  ".join(masked) + "\n\n"
        "Their subprocess got exit 0 and empty stdout from a script that did "
        "nothing, which is what a working silent no-op also produces. Merge "
        "IDH_HOOK_STRICT=1 into the child environment at each of those call "
        "sites — by hand, not through a fixture: a closed env dict inherits "
        "nothing (ticket 0610)."
    )


def test_no_production_surface_arms_strict_mode():
    """Strict mode must be unreachable from a real hook invocation.

    It is opt-in by environment variable, so the way it could arm by accident is
    an executable harness surface exporting it — a hook wiring, a launcher
    script, a unit file. Prose may name it freely; that is how it gets
    explained.
    """
    allowed = {
        "scripts/path_utils.py",  # defines it
        "scripts/knowledge_hints.py",  # consults it, in __main__ only
        "scripts/inject_rule_on_edit.py",  # consults it, in __main__ only
        "tests/test_knowledge_hints.py",
        "tests/test_inject_rule_on_edit.py",
        "tests/test_hook_failures_are_visible.py",
    }
    prose = (".md", ".erg", ".txt")
    proc = subprocess.run(
        ["git", "grep", "-l", "IDH_HOOK_STRICT"],
        cwd=REPO, capture_output=True, text=True,
    )
    hits = {ln for ln in proc.stdout.split() if ln}
    assert hits, "no file mentions IDH_HOOK_STRICT — this guard is looking at nothing"
    stray = sorted(h for h in hits - allowed if not h.endswith(prose))
    assert stray == [], (
        "IDH_HOOK_STRICT appears on an executable surface outside the tests: " +
        ", ".join(stray) + ". A harness file that exports it would arm strict "
        "mode in production, where a hook must never exit non-zero."
    )

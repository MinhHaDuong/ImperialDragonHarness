"""Pilot inventory coverage and consistency (ticket 0810, action 1).

Every assertion in ``adapters/pilot-support.json`` must be covered by
evidence appropriate to its kind — that is the ticket's "zero pilot
assertions may be uncovered" made a CI gate instead of a promise:

- ``static-test`` and ``local-probe`` assertions must name a pytest nodeid
  that exists in this suite (the referenced test asserting its own pass is
  the suite's job);
- ``manual-smoke`` assertions must be ``manual-only`` and ``pending`` — the
  pilot convention: a live invocation cannot be automated, and a manual
  procedure never claims a CI-grade pass;
- ``documentation`` assertions must carry a non-empty citation.

The flip control (the ticket's own test): mutate a verified entry —
claim a manual-smoke pass, or unpin a static-test from its test — and the
validator names the inconsistency, so a drifted inventory cannot ride
along with an unchanged support claim.
"""

import json
import subprocess
import sys

import pytest
from pathlib import Path

from child_env import child_env

REPO = Path(__file__).resolve().parents[1]
INVENTORY = REPO / "adapters" / "pilot-support.json"


def inventory():
    return json.loads(INVENTORY.read_text())


def referenced_modules(doc):
    return sorted({entry["test"].split("::", 1)[0]
                   for entry in doc["assertions"]
                   if entry["evidence_kind"] in ("static-test", "local-probe")})


def collect_nodeids(doc):
    """Collect only referenced modules; unrelated tests cannot affect coverage.

    Keep real pytest discovery, including parametrization and collection hooks.
    Normalize function pointers as the inventory names functions, not cases.
    """
    modules = referenced_modules(doc)
    if not modules:
        return set()
    out = subprocess.run(
        [sys.executable, "-m", "pytest",
         *(str(REPO / module) for module in modules), "--collect-only", "-q"],
        cwd=REPO,
        capture_output=True, text=True, timeout=120, check=True,
        env=child_env(),
    ).stdout
    return {
        line.split("::", 1)[0] + "::" + line.split("::", 1)[1].split()[0].split("[", 1)[0]
        for line in out.splitlines()
        if "::" in line
    }


def inconsistencies(doc, nodeids):
    problems = []
    for entry in doc["assertions"]:
        aid = entry["id"]
        kind = entry["evidence_kind"]
        test = entry["test"].split("[", 1)[0]
        if kind in ("static-test", "local-probe"):
            if "::" not in test:
                problems.append(f"{aid}: {kind} must name a pytest nodeid")
            elif test not in nodeids:
                problems.append(f"{aid}: nodeid {test} does not exist")
        elif kind == "manual-smoke":
            if entry["disposition"] != "manual-only" or entry["result"] != "pending":
                problems.append(
                    f"{aid}: manual-smoke must be manual-only and pending"
                )
        elif kind == "documentation":
            if len(test.strip()) < 10:
                problems.append(f"{aid}: documentation needs a citation")
        else:
            problems.append(f"{aid}: unknown evidence_kind {kind}")
    for source in doc["canonical_sources"].values():
        if not (REPO / source).exists():
            problems.append(f"canonical source missing: {source}")
    return problems


@pytest.mark.integration  # collect_nodeids() runs a pytest --collect-only subprocess
def test_every_assertion_is_covered():
    doc = inventory()
    problems = inconsistencies(doc, collect_nodeids(doc))
    assert problems == [], "uncovered or inconsistent inventory entries"


def test_flip_to_manual_pass_is_rejected(tmp_path):
    doc = inventory()
    for entry in doc["assertions"]:
        if entry["evidence_kind"] == "manual-smoke":
            break
    entry["result"] = "pass"  # claim a live invocation as a CI-grade pass
    assert any(
        "manual-only and pending" in p for p in inconsistencies(doc, set())
    )


def test_flip_static_test_away_from_its_nodeid_is_rejected():
    doc = inventory()
    for entry in doc["assertions"]:
        if entry["evidence_kind"] == "static-test" and entry["result"] == "pass":
            break
    entry["test"] = "tests/test_does_not_exist.py::test_ghost"
    assert any("does not exist" in p for p in inconsistencies(doc, set()))


def test_four_runtimes_are_probed():
    doc = inventory()
    harnesses = {v["harness"] for v in doc["versions"]}
    assert harnesses == {"claude", "codex", "pi", "vibe"}
    vibe = next(v for v in doc["versions"] if v["harness"] == "vibe")
    assert "never behavioral support" in vibe["evidence_note"] or \
        "NO porting slice" in vibe["evidence_note"], (
        "the Vibe entry must not claim more than a version probe"
    )


def test_no_vibe_behavioral_assertion_exists_yet():
    """No porting slice ran on Vibe, so no assertion may claim one."""
    doc = inventory()
    for entry in doc["assertions"]:
        assert entry["harness"] != "vibe", (
            f"{entry['id']} claims Vibe behavior; no Vibe slice has run"
        )


@pytest.mark.integration
def test_collection_is_scoped_and_still_detects_a_removed_reference(tmp_path, monkeypatch):
    """Unrelated broken tests cannot affect inventory; a broken pointer must."""
    monkeypatch.setattr(sys.modules[__name__], "REPO", tmp_path)
    (tmp_path / "pytest.ini").write_text("[pytest]\n")
    tests = tmp_path / "tests"
    tests.mkdir()
    target = tests / "test_referenced.py"
    target.write_text(
        "import pytest\n@pytest.mark.parametrize('value', [1, 2])\n"
        "def test_present(value):\n    assert value\n"
    )
    (tests / "test_unrelated.py").write_text("this is invalid Python!\n")
    doc = {"assertions": [{"id": "probe", "evidence_kind": "static-test",
                           "test": "tests/test_referenced.py::test_present"}],
           "canonical_sources": {}}
    nodeids = collect_nodeids(doc)
    assert inconsistencies(doc, nodeids) == []
    target.write_text("def test_renamed():\n    pass\n")
    assert any("does not exist" in problem
               for problem in inconsistencies(doc, collect_nodeids(doc)))
    target.unlink()
    with pytest.raises(subprocess.CalledProcessError):
        collect_nodeids(doc)

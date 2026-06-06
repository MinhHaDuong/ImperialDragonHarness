"""Structural + acceptance tests for the test-audit-llm skill (ticket 0183).

The workflow (``skills/test-audit-llm/test-audit-llm.js``) needs live agents to
run end-to-end, so it cannot be exercised in CI — and there is no Node runtime in
this environment to even syntax-check it. What IS mechanically checkable is its
STRUCTURE and its committed ACCEPTANCE ARTIFACTS, and that is where the ticket's
contract lives. These are source-inspection assertions (the repo convention for
un-runnable Workflow artifacts; see tests/test_maw_audit_skill.py), not a faked
end-to-end run.

Acceptance evidence the gate checks mechanically (per the 0183 raid brief):
  (1) a known-bad smoke fixture the judge MUST flag, named so pytest never
      collects it (under skills/*/fixtures, excluded by pytest.ini norecursedirs);
  (2) a committed sample report + JSON sidecar (the dry-run stand-in, since the
      Workflow cannot run here), with the canonical sidecar schema validated;
  (3) identity well-formedness: every finding identity resolves to a REAL
      repo-relative file.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "skills" / "test-audit-llm"
JS = SKILL_DIR / "test-audit-llm.js"
MD = SKILL_DIR / "SKILL.md"
FIXTURES = SKILL_DIR / "fixtures"
SAMPLE_JSON = SKILL_DIR / "sample" / "TEST-AUDIT-LLM.sample.json"
SAMPLE_MD = SKILL_DIR / "sample" / "TEST-AUDIT-LLM.sample.md"

LENSES = {"faithfulness", "intent", "negative-space", "change-detector"}


def js() -> str:
    return JS.read_text()


def md() -> str:
    return MD.read_text()


# ── existence + frontmatter ──────────────────────────────────────────────────


def test_skill_files_exist():
    assert JS.is_file(), "test-audit-llm.js missing"
    assert MD.is_file(), "SKILL.md missing"


def test_frontmatter_has_name_and_description():
    front = md()
    assert re.search(r"^name:\s*test-audit-llm\s*$", front, re.MULTILINE)
    assert re.search(r"^description:\s*", front, re.MULTILINE)


# ── read-and-judge: NO execution (the distinguishing mechanism vs maw-audit) ──


def test_runs_nothing_no_mutation_no_test_command_no_worktree():
    """The whole point (ticket 0183): this skill READS and JUDGES, it executes
    nothing. So the engine must NOT carry a RUN_TEST command, a mutation loop, or
    worktree isolation — those are maw-audit's machinery, not this one's."""
    src = js()
    # No test-command MECHANISM: no CONFIG.RUN_TEST usage, no RUN_TEST schema/
    # config key (an explanatory comment naming what is deliberately absent is
    # fine — what must not exist is the machinery).
    assert "CONFIG.RUN_TEST" not in src, "a test command is wired in — this skill runs nothing"
    assert "RUN_TEST:" not in src, "a RUN_TEST config/schema key leaked in"
    assert "isolation: 'worktree'" not in src, (
        "no agent should be worktree-isolated — nothing is mutated"
    )
    # No test->source pairing table (that is maw-audit's, for mutation). Allow an
    # explanatory comment; forbid a BEHAVIORAL schema/config key or usage.
    assert "BEHAVIORAL:" not in src and "CONFIG.BEHAVIORAL" not in src, (
        "no test->source pairing table — that is maw-audit's"
    )
    # SKILL.md must state the read-and-judge / no-execution discipline.
    assert "Runs nothing" in md() or "runs nothing" in md().lower()


def test_one_judge_per_file_carries_all_four_lenses_in_one_read():
    """Design: ONE judge per file with ALL FOUR rubrics in a single prompt — not
    four passes (ticket 0183 + YAGNI)."""
    src = js()
    # A single LENSES block names all four lenses.
    assert "const LENSES" in src, "lenses not defined as one shared block"
    for lens in LENSES:
        assert lens in src, f"lens {lens!r} missing from the engine"
    # The judge schema enumerates exactly the four lenses.
    m = re.search(r"lens:\s*\{\s*type:\s*'string',\s*enum:\s*\[([^\]]*)\]", src)
    assert m, "judge schema does not enum the four lenses"
    enum = {x.strip().strip("'\"") for x in m.group(1).split(",")}
    assert enum == LENSES, f"lens enum {enum} != {LENSES}"


def test_discovery_phase_derives_file_list_and_is_slimmer_than_maw_audit():
    """A run-start DISCOVERY phase derives the TEST_FILES list (Just Work tm),
    and — because nothing is executed — derives NO test command / pairing table
    (the deliberate slimming vs maw-audit)."""
    src = js()
    assert "phase('Discovery')" in src, "no Discovery phase"
    assert "DISCOVERY_SCHEMA" in src
    sch = src[src.index("DISCOVERY_SCHEMA"):src.index("phase('Discovery')")]
    assert "TEST_FILES" in sch and "required:" in sch and "'TEST_FILES'" in sch, (
        "discovery must REQUIRE the derived test-file list"
    )


def test_aborts_when_no_file_list_derived_or_supplied():
    src = js()
    disc = src[src.index("phase('Discovery')"):src.index("phase('Judge')")]
    assert "aborted: true" in disc, "discovery must abort when no file list exists"
    assert "TEST_FILES override" in disc, "abort must point at the explicit override"


# ── two-tier model: cheap bulk + capped strong escalation ────────────────────


def test_bulk_pass_uses_cheap_model():
    src = js()
    judge = src[src.index("phase('Judge')"):src.index("phase('Escalate')")]
    assert "model: 'haiku'" in judge, "bulk judge pass must use the cheap model"


def test_escalation_uses_strong_model_and_is_capped_at_top_k():
    """Flagged/low-confidence files escalate to the strong model, capped at the
    top K by severity x churn (ticket 0183: a big suite cannot fan a 2nd wave)."""
    src = js()
    esc = src[src.index("phase('Escalate')"):src.index("phase('Report')")]
    assert "model: 'sonnet'" in esc, "escalation must use the strong model"
    assert "ESCALATE_K" in src, "no top-K cap on the escalation wave"
    assert ".slice(0, CONFIG.ESCALATE_K)" in src, "escalation not capped to top K"
    # SKILL.md must state the cap.
    assert "K = 8" in md() or "K=8" in md(), "SKILL.md must state the escalation cap K"


def test_strong_model_verdict_replaces_bulk_for_escalated_files():
    """Mirrors maw-audit's skeptic final-say: the sonnet re-judge REPLACES the
    haiku verdict for the escalated file."""
    src = js()
    assert re.search(r"byFile\[file\]\s*=\s*escalated\[i\]", src), (
        "escalated verdict does not replace the bulk verdict"
    )


def test_churn_is_non_fatal():
    """maw-audit's churn agent once threw and discarded a 1.36M-token run. Churn
    here is decoration and must degrade, never throw."""
    src = js()
    churn = src[src.index("const churnByFile"):src.index("const riskWeight")]
    assert "try {" in churn and "catch" in churn, "churn must be wrapped in try/catch"
    assert "parseInt" in churn, "churn must tolerate string-encoded integers"


# ── identity from dispatch, never agent self-report (mirrors maw-audit 0226) ──


def test_identity_is_dispatch_derived_not_agent_self_report():
    src = js()
    assert re.search(r"if \(a\)\s*a\.testFile\s*=\s*file", src), (
        "judge identity must be set from the dispatch loop (file), not read back"
    )
    # The report row identity is a.testFile (the dispatched path).
    assert "identity: a.testFile" in src, "report identity not the dispatched path"


# ── advisory discipline (exit criterion 5): no gate, no failing exit code ─────


def test_advisory_only_no_ci_gate():
    src = js()
    md_text = md()
    # No canary / pass-fail gate that could block a merge.
    assert "ADVISORY ONLY" in src or "ADVISORY ONLY" in md_text, (
        "the advisory-only banner is missing"
    )
    assert "tickets/erg new" in md_text, "findings must feed ticket creation"
    # No exit-code contract / hard gate language wired into the engine return.
    assert "aborted: true" in src  # the only abort is a discovery no-op, not a verdict gate


# ── composition: file granularity, shared file key (exit criterion 4) ─────────


def test_reports_at_file_granularity_with_shared_key():
    md_text = md()
    assert "FILE granularity" in md_text or "file granularity" in md_text.lower(), (
        "SKILL.md must declare FILE-granularity composition"
    )
    # The sidecar declares granularity.
    assert "'file'" in js() and "granularity" in js()


# ── agnostic: no hardcoded /home paths in the live skill surface ─────────────


def test_no_hardcoded_home_paths_in_skill_surface():
    for f in (JS, MD):
        assert "/home/" not in f.read_text(), f"{f.name} hardcodes a /home path"


# ── (1) the known-bad smoke fixture ──────────────────────────────────────────


def test_smoke_fixture_present_and_not_collected():
    """A known-bad sample test the judge MUST flag, named so pytest never
    collects it (under skills/*/fixtures, excluded by pytest.ini norecursedirs)."""
    bad = FIXTURES / "fixture_payment_gateway_test.py"
    subject = FIXTURES / "payment_gateway.py"
    assert bad.is_file(), "smoke fixture test missing"
    assert subject.is_file(), "smoke fixture subject missing"
    # Named so pytest does NOT collect it as a project test.
    assert not bad.name.startswith("test_"), "fixture would be collected by pytest"
    # pytest.ini excludes skills/*/fixtures.
    assert "skills/*/fixtures" in (REPO / "pytest.ini").read_text()
    # SKILL.md documents it as the smoke fixture.
    assert "fixture_payment_gateway_test.py" in md(), (
        "SKILL.md must reference the smoke fixture"
    )


def test_smoke_fixture_embodies_all_four_lens_defects():
    """The fixture must actually contain the markers each lens flags, so it is a
    real anchor (the judge MUST flag it on >= 1 lens — by design, all four)."""
    bad = (FIXTURES / "fixture_payment_gateway_test.py").read_text()
    assert "MagicMock" in bad, "faithfulness: fixture must mock the subject"
    assert "def test_charge_succeeds" in bad, "intent: fixture name must lie"
    assert "mock_calls" in bad, "change-detector: fixture must assert call order"
    # negative-space: the subject has guards the test never exercises.
    subject = (FIXTURES / "payment_gateway.py").read_text()
    assert "amount <= 0" in subject and "exceeds limit" in subject, (
        "subject must carry error branches the happy-path test skips"
    )


# ── (2) committed sample report + JSON sidecar schema ────────────────────────


def test_sample_report_and_sidecar_exist():
    assert SAMPLE_MD.is_file(), "sample markdown report missing"
    assert SAMPLE_JSON.is_file(), "sample JSON sidecar missing"


def test_sidecar_schema_is_canonical():
    """Every finding carries the canonical {identity, lens, severity, rationale}
    schema (the composition contract)."""
    data = json.loads(SAMPLE_JSON.read_text())
    assert data.get("granularity") == "file", "sidecar must declare file granularity"
    findings = data.get("findings")
    assert isinstance(findings, list) and findings, "sidecar has no findings"
    for f in findings:
        for key in ("identity", "lens", "severity", "rationale"):
            assert key in f and f[key], f"finding missing required key {key!r}: {f}"
        assert f["lens"] in LENSES, f"unknown lens {f['lens']!r}"
        assert f["severity"] in {"low", "medium", "high"}, f["severity"]


def test_sample_flags_the_smoke_fixture_on_all_four_lenses():
    """The committed dry-run must show the judge flagging the smoke fixture on
    every lens (the acceptance proof, since the live Workflow can't run here)."""
    data = json.loads(SAMPLE_JSON.read_text())
    fx = "skills/test-audit-llm/fixtures/fixture_payment_gateway_test.py"
    hit = {f["lens"] for f in data["findings"] if f["identity"] == fx}
    assert hit == LENSES, f"smoke fixture not flagged on all four lenses: {hit}"


# ── (3) identity well-formedness: every identity is a REAL repo-relative file ─


def test_every_sample_identity_resolves_to_a_real_file():
    data = json.loads(SAMPLE_JSON.read_text())
    for f in data["findings"]:
        ident = f["identity"]
        assert not ident.startswith("/"), f"identity must be repo-relative: {ident}"
        assert (REPO / ident).is_file(), f"identity does not resolve to a real file: {ident}"

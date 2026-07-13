"""Structural regression tests for the maw-audit skill (formerly fang-audit).

Origin: ticket 0182 (fang-only v1). REWRITTEN for ticket 0219 (author
directive 2026-06-06, directive 2): the skill no longer carries a hardcoded
per-repo CONFIG block. A run-start DISCOVERY phase reads the launch repo and
DERIVES the test command, the test↔source pairing table, and mutation
heuristics; explicit knobs survive only as OPTIONAL overrides. These tests are
deliberately rewritten to guard that NEW contract, not the old explicit-CONFIG
shape — the old assertions (test_config_block_declares_explicit_knobs,
test_pairing_table_is_explicit_map_not_heuristic, test_config_is_defaults_
merged_with_args) enforced the design 0219 reverses and are replaced here.

The workflow itself (``skills/maw-audit/maw-audit.js``) needs live agents to
run end-to-end, so it cannot be exercised in CI. What IS mechanically checkable
is its STRUCTURE — and the structure is where the ticket's contract lives:

  * 0219 d1 — discovery REPLACES CONFIG: a Discovery phase derives the pairing
              table; no hardcoded git-erg DEFAULTS block; overrides optional;
              the blind filename-glob heuristic is banned.
  * 0219 core — handcuff (robustness) + scope (altitude) passes, pipelined
              after the fang pass, each its own agent role; a unified
              three-axis report.
  * 0219 d4 — run-residue cleanups: seed staged clean for auto-reclaim; a
              post-run cleanup phase for scratch worktrees.
  * 0221 — every MUTATING agent role is worktree-isolated; read-only roles
              (discovery, skeptics) are not.
  * crit 5 (0182) — a determinism precheck gates the fan-out.
  * crit 7 (0182) — the canary gate is scoped by a structural tag, never by the
              agent-supplied ``isCanary`` flag.
  * agnostic — no hardcoded /home paths in the live skill surface.

These are source-inspection assertions (the repo convention for un-runnable
artifacts; see tests/test_rename_orchestrator_to_raid.sh), not a faked
end-to-end run.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "skills" / "maw-audit"
JS = SKILL_DIR / "maw-audit.js"
MD = SKILL_DIR / "SKILL.md"


def js() -> str:
    return JS.read_text()


def test_skill_files_exist():
    assert JS.is_file(), "maw-audit.js missing"
    assert MD.is_file(), "SKILL.md missing"


def test_frontmatter_has_name_and_description():
    front = MD.read_text()
    assert re.search(r"^name:\s*maw-audit\s*$", front, re.MULTILINE)
    assert re.search(r"^description:\s*", front, re.MULTILINE)


def test_expensive_warning_is_prominent():
    """The skill must loudly flag the ~1.3M-token cost so it is never casual."""
    text = MD.read_text()
    assert "1.3M" in text or "1.3 M" in text
    assert "EXPENSIVE" in text


# ── 0219 d1: discovery REPLACES CONFIG — no required per-repo knobs ───────────


def test_discovery_phase_present_and_derives_pairing_table():
    """A run-start DISCOVERY phase must read the launch repo and DERIVE the
    test command + test->source pairing table. This is the Just Work (tm)
    reversal of 0182's hardcoded CONFIG (directive 1)."""
    src = js()
    assert "phase('Discovery')" in src, "no Discovery phase"
    # The discovery agent must derive a BEHAVIORAL pairing table and a RUN_TEST.
    m = re.search(r"const discovered = await agent\(", src)
    assert m, "no discovery agent dispatch"
    # The discovery SCHEMA must require the derived pairing table + command.
    assert "DISCOVERY_SCHEMA" in src
    sch = src[src.index("DISCOVERY_SCHEMA"):src.index("phase('Discovery')")]
    assert "BEHAVIORAL" in sch and "RUN_TEST" in sch, (
        "discovery schema must derive BEHAVIORAL + RUN_TEST"
    )
    assert "required:" in sch and "'RUN_TEST'" in sch and "'BEHAVIORAL'" in sch, (
        "discovery must REQUIRE the derived command + pairing table"
    )


def test_no_hardcoded_pairing_table_or_test_command_required():
    """The old hardcoded git-erg DEFAULTS block (the 17-file BEHAVIORAL map,
    the `cd src/go && go test` command) must be GONE — it is now derived. Only
    inert FALLBACKS may remain, and FALLBACKS.BEHAVIORAL must be EMPTY (no
    pre-authored pairing table) and carry no test command."""
    src = js()
    assert "const DEFAULTS = {" not in src, (
        "the hardcoded DEFAULTS config block must be removed (0219 d1)"
    )
    # No committed git-erg pairing table baked into the engine.
    assert "atomicwrite_test.go" not in src and "refs_git_test.go" not in src, (
        "a hardcoded git-erg pairing table is still baked in — must be derived"
    )
    # FALLBACKS exists but ships NO pairing table and NO test command.
    assert "const FALLBACKS = {" in src, "inert FALLBACKS block missing"
    fb = src[src.index("const FALLBACKS = {"):src.index("// ===", src.index("const FALLBACKS = {"))]
    assert re.search(r"BEHAVIORAL:\s*\[\]", fb), (
        "FALLBACKS must NOT pre-author a pairing table (BEHAVIORAL must be [])"
    )
    assert "go test" not in fb, "FALLBACKS must not bake in a concrete test command"


def test_overrides_are_optional_not_prerequisites():
    """Config now derives from FALLBACKS < discovery < args. An explicit
    override (args) still wins, but it is OPTIONAL — discovery fills anything
    the args omit. The merge must put args LAST (highest precedence) and
    discovery in the middle, over the inert fallbacks."""
    src = js()
    m = re.search(
        r"const CONFIG = Object\.assign\(\{\},\s*FALLBACKS,\s*discovered[^,]*,\s*_args\)",
        src,
    )
    assert m, (
        "CONFIG must merge FALLBACKS < discovery < args so overrides are "
        "optional and win when present (0219 d1)"
    )


def test_filename_glob_heuristic_is_banned():
    """The blind filename-glob heuristic (X_test -> X.go) is BANNED: it
    returned a nonexistent file for 5 of 19 git-erg tests, including both
    canaries. Discovery must derive pairings from READING (imports/call sites),
    and the skill must explicitly forbid the glob."""
    src = js()
    # No name-derivation code that strips _test to guess the source file.
    assert not re.search(r"replace\(\s*['\"]_test", src), (
        "a filename-glob heuristic (stripping _test) is present — banned"
    )
    # The discovery prompt must explicitly forbid the glob and require evidence.
    assert "BANNED" in src and "filename-glob" in src.lower(), (
        "discovery prompt must explicitly ban the filename-glob heuristic"
    )


def test_aborts_when_no_pairing_table_derived_or_supplied():
    """With no derived table AND no override, the only alternative is the
    banned glob — so the run must ABORT openly, never silently guess."""
    src = js()
    disc = src[src.index("phase('Discovery')"):src.index("phase('Precheck')")]
    assert "aborted: true" in disc, "discovery must abort when no pairing table exists"
    assert "BEHAVIORAL override" in disc or "explicit BEHAVIORAL" in disc, (
        "abort message must point at the explicit override as the fix"
    )


# ── 0219 core: handcuff (robustness) + scope (altitude) passes ───────────────


def test_handcuff_pass_present_with_inverted_oracle_and_own_skeptic():
    """Handcuff mode: behavior-PRESERVING operators, an INVERTED oracle
    (red = over-scoped), and its OWN behavior-preservation skeptic."""
    src = js()
    assert "phase('Handcuff')" in src, "no Handcuff phase"
    assert "handcuffPrompt" in src and "HANDCUFF_SCHEMA" in src
    # Inverted oracle: 'handcuff' (red is bad) and 'robust' (green is good).
    assert "'handcuff'" in src and "'robust'" in src, "handcuff oracle verdicts missing"
    # Behavior-preservation skeptic, distinct from the fang skeptic.
    assert "handcuffSkepticize" in src and "HANDCUFF_SKEPTIC_SCHEMA" in src, (
        "handcuff pass lacks its own behavior-preservation skeptic"
    )
    # A red on a secretly behavior-changing refactor is withdrawn as a fang.
    assert "not-preserving" in src, "skeptic cannot withdraw a non-preserving red"


def test_scope_pass_present_replays_caught_operators_at_siblings():
    """Scope/altitude mode: replay each CAUGHT operator at sibling sites;
    surviving siblings = instance-pinned contract, flagged for class promotion."""
    src = js()
    assert "phase('Scope')" in src, "no Scope phase"
    assert "scopePrompt" in src and "SCOPE_SCHEMA" in src
    assert "instance-pinned" in src and "class-guarded" in src, (
        "scope oracle verdicts (instance-pinned / class-guarded) missing"
    )
    # It must consume the fang pass's CAUGHT findings (sibling replay).
    assert "caughtOpsByFile" in src, "scope pass does not replay fang-caught operators"


def test_modes_pipelined_after_fang_in_same_workflow():
    """Both new passes run AFTER the fang Audit pass in the SAME workflow
    (one discovery, one worktree setup), in the order Audit -> Handcuff ->
    Scope. Separate agent roles per oracle."""
    src = js()
    order = [src.index(f"phase('{p}')") for p in ("Discovery", "Audit", "Handcuff", "Scope")]
    assert order == sorted(order), (
        "phases must run Discovery < Audit < Handcuff < Scope in one workflow"
    )


def test_three_axis_report_present():
    """The report must carry a unified per-test three-axis table:
    fang? / handcuff? / right-scope?, sortable by risk x churn."""
    src = js()
    assert "threeAxis" in src, "three-axis roll-up missing"
    # The roll-up must compute all three axes per file.
    ta = src[src.index("const threeAxis ="):src.index("const L = []", src.index("const threeAxis ="))] \
        if "const L = []" in src[src.index("const threeAxis ="):] else src[src.index("const threeAxis ="):]
    assert "fang:" in ta and "handcuff:" in ta and "rightScope:" in ta, (
        "three-axis row must cover fang / handcuff / right-scope"
    )
    # Sorted by risk x churn.
    assert "risk * b.churn" in src or "b.risk * b.churn" in src, (
        "three-axis table not sorted by risk x churn"
    )


# ── 0219 d4: run-residue cleanups ────────────────────────────────────────────


def test_seed_is_staged_clean_for_auto_reclaim():
    """Directive 4a: the untracked seed copy made guard worktrees dirty so
    auto-reclaim skipped them. The seed must now be `git add -f`-staged so the
    working tree stays clean."""
    src = js()
    assert "git add -f" in src, "seed not staged — worktree stays dirty, reclaim skips it"
    # The guard prompt must mention keeping the tree clean / reclaim.
    gp = src[src.index("function guardPrompt"):src.index("function skepticPrompt")]
    assert "reclaim" in gp.lower(), "guard prompt does not address auto-reclaim"


def test_post_run_cleanup_phase_for_scratch_worktrees():
    """Directive 4b: a post-run cleanup phase prunes hand-rolled
    /tmp/fang-* scratch worktrees left on detached HEAD."""
    src = js()
    assert "phase('Cleanup')" in src, "no post-run Cleanup phase"
    cu = src[src.index("phase('Cleanup')"):]
    assert "git worktree" in cu and "prune" in cu, "cleanup does not prune worktrees"
    assert "/tmp/fang-" in cu, "cleanup not scoped to the /tmp/fang- scratch pattern"


# ── 0219 d1: guards stay an explicit opt-in; canary gate skipped openly ───────


def test_guards_are_explicit_opt_in_not_auto_discovered():
    """Guard/canary designation validates the audit itself — it must stay an
    explicit human opt-in, never auto-discovered. With no guards, the canary
    gate is SKIPPED openly, never faked on an empty set."""
    src = js()
    # Discovery must NOT designate guards.
    disc = src[src.index("phase('Discovery')"):src.index("phase('Precheck')")]
    assert "Do NOT designate guard" in disc or "never auto-discovered" in disc.lower(), (
        "discovery must not auto-designate guards"
    )
    # Open skip on empty guard set.
    assert "canarySkipped" in src, "no open-skip path for the canary gate"
    assert re.search(r"canarySkipped\s*=\s*GUARDS\.length === 0", src), (
        "canary gate not skipped openly when no guards are designated"
    )


# ── crit 5 (0182): determinism precheck blocks the run ───────────────────────


def test_precheck_calls_0184_flakiness_gate():
    src = js()
    assert "test-quality.py flakiness" in src, "precheck does not reference the 0184 gate"
    assert "~/.claude/scripts/test-quality.py" in src


def test_precheck_aborts_and_blocks_fanout():
    src = js()
    # The precheck phase must run BEFORE the Audit fan-out and abort on failure.
    precheck_idx = src.index("phase('Precheck')")
    audit_idx = src.index("phase('Audit')")
    assert precheck_idx < audit_idx, "precheck must precede the audit fan-out"
    gate = src[precheck_idx:audit_idx]
    assert "return { aborted: true" in gate, "precheck does not abort the run"
    assert "suite is flaky" in gate, "missing the required flaky abort message"
    assert "exitCode" in gate and "=== 2" in gate


def test_precheck_skips_openly_when_no_adapter():
    """0219: a language with no 0184 flakiness adapter (empty PRECHECK_CMD)
    must degrade to an OPEN warn-and-proceed skip, never a faked PASS and never
    a spurious abort."""
    src = js()
    assert "precheckSkipped" in src, "no open-skip path for the precheck"
    assert re.search(r"if \(!CONFIG\.PRECHECK_CMD\)", src), (
        "precheck does not handle a missing flakiness adapter"
    )


# ── crit 7 (0182): canary gate scoped by structural tag, never agent isCanary ─


def test_canary_gate_uses_structural_guard_tag_not_agent_claim():
    src = js()
    assert "_isGuardFile" in src, "no structural guard tag"
    m = re.search(r"canaryFindings\s*=\s*flat\.filter\(([^)]*)\)", src)
    assert m, "canaryFindings filter not found"
    filt = m.group(1)
    assert "_isGuardFile" in filt, (
        "canary gate must filter on the CONFIG-derived _isGuardFile tag"
    )


def test_canary_gate_does_not_trust_filename_regex_or_bare_iscanary():
    src = js()
    m = re.search(r"canaryFindings\s*=\s*flat\.filter\(([^)]*)\)", src)
    filt = m.group(1)
    assert "scaling_test" not in filt and "resource_test" not in filt, (
        "canary gate still keys on a hardcoded filename regex"
    )


# ── crit 4 (0182): free-rider metrics from existing data ─────────────────────


def test_free_rider_metrics_present():
    src = js()
    assert "oracleStrength" in src, "oracle-strength free rider missing"
    assert "diagnosticity" in src, "diagnosticity free rider missing"
    assert "caught" in src


# ── crit 6 (0182): risk × churn sort, risk is a human input ──────────────────


def test_risk_churn_sort_present_and_risk_is_input():
    src = js()
    assert "churn" in src.lower(), "churn weighting missing"
    assert "CONFIG.RISK" in src, "risk is not a human-supplied input"
    assert "survivedRanked" in src, "toothless list is not sorted by risk x churn"


# ── agnostic: no hardcoded home paths in the live surface ────────────────────


def test_no_hardcoded_home_paths():
    for f in (JS, MD):
        text = f.read_text()
        assert not re.search(r"/home/[a-z]", text), f"{f.name} has a /home path"
        assert "github.com" not in text, f"{f.name} references github.com"


# ── 0221: worktree isolation — exactly the MUTATING roles are isolated ───────


def test_mutating_agents_are_worktree_isolated():
    """Workflow agents share the session checkout by default (probe-verified,
    ticket 0221); every role that MUTATES source and runs the suite (fang
    audit, guard, handcuff, scope) MUST run in a per-agent worktree or the
    concurrent mutate->test->revert loops corrupt each other. Read-only roles
    (discovery, the skeptics) stay non-isolated (worktrees are expensive)."""
    lines = js().splitlines()
    mutating_markers = [
        "agent(auditPrompt(file)",
        "agent(guardPrompt(file)",
        "agent(handcuffPrompt(file)",
        "agent(scopePrompt(file",
    ]
    for marker in mutating_markers:
        hits = [ln for ln in lines if marker in ln]
        assert len(hits) == 1, f"expected exactly one {marker} call, found {len(hits)}"
        assert "isolation: 'worktree'" in hits[0], (
            f"mutating agent not worktree-isolated: {marker}"
        )
    # Read-only roles must NOT be isolated.
    for marker in ("agent(skepticPrompt", "agent(handcuffSkepticPrompt",
                   "const discovered = await agent("):
        idx = next((i for i, ln in enumerate(lines) if marker in ln), None)
        assert idx is not None, f"{marker} call not found"
        block = "\n".join(lines[idx:idx + 6])
        assert "isolation" not in block, f"read-only role must stay non-isolated: {marker}"


def test_skill_md_states_target_repo_requirement():
    text = MD.read_text()
    assert "TARGET repo" in text or "launch repo" in text.lower(), (
        "SKILL.md missing the target/launch-repo session requirement"
    )


# ── 0226 defect 1: ONE canonical test-identity normalization ─────────────────


def test_test_identity_keyed_consistently_no_per_site_basename():
    """0226 defect 1 (the headline). The fang/handcuff/scope dicts were WRITTEN
    with ``base(a.testFile)`` (basename) but READ with the raw
    ``BEHAVIORAL[].test`` path. On a path-prefixed repo (Python ``tests/``
    layout) discovery returns ``tests/test_foo.py`` while ``base()`` yields
    ``test_foo.py`` — the join misses, so the scope pass never dispatches, the
    handcuff priority sort is a no-op, and the three-axis table is all-n/a.

    Root fix: identity is the full repo-root-relative path, established once at
    the BEHAVIORAL mapping and bound through DISPATCH (``a.testFile =
    file.test``), never a per-site basename. So:
      * NO ``base(`` call survives — every former key site now holds the
        canonical full path the read sites already use.
      * Each MUTATING wrapper pins identity from the dispatched ``file.test``,
        not the agent's self-reported ``a.testFile`` (the ``|| file.test``
        fallback let the agent's claim win — same anti-pattern the canary gate
        already bans, l.602-604).

    This test FAILS on the pre-fix code (``base(a.testFile)`` present, wrappers
    use ``a.testFile || file.test``) and passes once identity is canonical."""
    src = js()
    # No per-site basename normalization on a key/identity site survives.
    assert "base(" not in src, (
        "a per-site base()/basename on a test-identity key survives — the "
        "write-key (basename) and read-key (full path) split that makes the "
        "scope/handcuff/three-axis joins miss on path-prefixed repos (0226 d1)"
    )
    # Every mutating wrapper must pin identity from the DISPATCHED file, never
    # the agent's self-reported testFile (no `|| file.test` fallback).
    assert "a.testFile || file.test" not in src and "a.testFile||file.test" not in src, (
        "a mutating wrapper still lets the agent's self-reported testFile win "
        "over the dispatched file.test — identity must come from dispatch (0226 d1)"
    )
    assert src.count("a.testFile = file.test") >= 4, (
        "expected all four mutating wrappers (audit/guard/handcuff/scope) to "
        "pin a.testFile = file.test from dispatch (0226 d1)"
    )


def test_run_test_validated_non_empty_before_fanout():
    """0226 defect 2. An empty RUN_TEST gives every audit agent a blank test
    command, so every mutation trivially 'survives' → a false-accusation flood.
    The discovery schema must require a non-empty RUN_TEST (minLength) so the
    Workflow runtime rejects+retries a blank, AND the engine must abort if it is
    still empty after merge."""
    src = js()
    # Schema enforces a non-empty RUN_TEST.
    sch = src[src.index("DISCOVERY_SCHEMA"):src.index("phase('Discovery')")]
    assert "minLength" in sch, (
        "DISCOVERY_SCHEMA does not enforce a non-empty RUN_TEST (minLength) — "
        "an empty test command passes every gate (0226 d2)"
    )
    # Engine aborts on an empty RUN_TEST before the fan-out.
    assert re.search(r"!CONFIG\.RUN_TEST", src) or "RUN_TEST.trim()" in src, (
        "engine does not abort on an empty RUN_TEST after merge (0226 d2)"
    )


def test_precheck_gate_enum_and_affirmative_pass():
    """0226 defect 3. The precheck gate must be an ENUM ['pass','fail'] (the
    Workflow runtime validates + retries on mismatch, so a real agent returning
    'skipped'/'Pass'/'unknown' is rejected, not silently passed), and the
    no-abort condition must require ``gate === 'pass'`` AFFIRMATIVELY — not
    merely ``!== 'fail'``."""
    src = js()
    psch = src[src.index("PRECHECK_SCHEMA"):src.index("const RULES")]
    assert re.search(r"gate:\s*\{[^}]*enum:\s*\[\s*'pass'\s*,\s*'fail'\s*\]", psch), (
        "PRECHECK_SCHEMA.gate is not an enum ['pass','fail'] — a real agent "
        "returning 'skipped'/'Pass' would pass the flakiness gate (0226 d3)"
    )
    # The abort must require an affirmative pass.
    assert "gate !== 'pass'" in src or "gate === 'pass'" in src, (
        "precheck abort does not require an affirmative gate === 'pass' (0226 d3)"
    )


def test_precheck_skip_banner_in_report():
    """0226 advisory. The precheck open-skip was invisible in the Markdown
    report (only log() + a return field); the canary open-skip has a ⏭️ banner.
    The report must mirror that banner for a precheck skip."""
    src = js()
    # The L (report) assembly must reference precheckSkipped to emit a banner.
    lasm = src[src.index("const L = []"):]
    assert "precheckSkipped" in lasm, (
        "precheck skip is not surfaced in the Markdown report (0226 advisory)"
    )
    assert lasm.count("⏭️") >= 2, (
        "precheck skip banner does not mirror the canary ⏭️ banner (0226 advisory)"
    )


# ── 0223: args may arrive as a JSON-encoded string ───────────────────────────


def test_string_args_are_json_parsed():
    """The harness may deliver the Workflow args as a JSON-encoded STRING
    (observed 2026-06-05, ticket 0223); the engine must normalize before use."""
    src = js()
    assert re.search(r"let _args = args", src), "args not read as the override input"
    assert re.search(r"JSON\.parse\(_args\)", src), (
        "string-delivered args must be JSON.parse'd (0223)"
    )


def test_path_knobs_are_tilde_expanded():
    src = js()
    assert "CONFIG.OUTPUT = expand(CONFIG.OUTPUT)" in src
    assert "UNTRACKED_SEED" in src and "from: expand(s.from)" in src


def test_meta_precedes_engine():
    """Workflow scripts must begin with export const meta (after comments)."""
    src = js()
    assert src.index("export const meta") < src.index("const FALLBACKS"), (
        "meta block must precede the engine"
    )


# ── directive 3: language-pluggable satisfied via a documented launch path ────


def test_skill_md_documents_zero_prep_launch_path():
    """0219 directive 3: the non-Go criterion is met via the DOCUMENTED path —
    discovery makes a non-Go run zero-prep. The skill docs must document the
    exact launch procedure and the expected cost scale vs the git-erg run."""
    text = MD.read_text()
    assert "aedist" in text.lower(), "the documented non-Go launch target is undocumented"
    assert "zero-prep" in text.lower() or "no per-repo" in text.lower(), (
        "the zero-prep discovery property is not documented"
    )
    # Cost scale must be stated so the reader knows what they are committing to.
    assert "1.3M" in text or "1.3 M" in text, "expected cost scale not documented"


def test_skill_md_describes_discovery_not_config_file():
    """The SKILL.md must describe the discovery flow, not the old
    .fang-audit.json edit-the-config flow (0219 d1 reversal)."""
    text = MD.read_text()
    assert "discovery" in text.lower() or "Discovery" in text, (
        "SKILL.md does not describe the discovery phase"
    )
    # The old per-repo config-file prerequisite must be gone as a REQUIREMENT
    # (under either the old or the renamed skill name).
    assert "If `.fang-audit.json` is missing, STOP" not in text, (
        "stale 'missing config -> STOP' prerequisite remains"
    )
    assert "If `.maw-audit.json` is missing, STOP" not in text, (
        "stale 'missing config -> STOP' prerequisite remains (renamed form)"
    )


# ── ticket Test section: fixtures EMBODY their defect property ───────────────
# These assert that each fixture genuinely embodies the property the mutation
# mode must flag (statically checkable). They do NOT execute the handcuff/scope
# oracle or simulate its verdict — runtime flagging needs a live agent run in
# the Workflow sandbox (no local JS runtime; same bucket as the proven fang
# mode and the directive-3 AEDIST run), verified on the documented validation
# path. Reimplementing the oracle in Python to manufacture a green "it's
# flagged" result would be a fake verdict (directive 1: never fake it) and a
# tautological test (raid Phase 3 antipattern). We anchor the inputs; the path
# proves the outputs.

FIXTURES = SKILL_DIR / "fixtures"


def test_handcuff_fixture_embodies_over_scoped_call_order():
    """The handcuff fixture's test must assert on call ORDER (over-scoped),
    while the source's contract promises only the OUTCOME — so a behavior-
    preserving reorder makes it go red. That property is what the handcuff
    pass flags."""
    src = (FIXTURES / "over_scoped_call_order.py").read_text()
    tst = (FIXTURES / "fixture_over_scoped_call_order_test.py").read_text()
    # The TEST over-asserts on ORDER (mock_calls sequence / call ordering).
    assert "mock_calls ==" in tst, (
        "handcuff fixture test does not assert on call ORDER (the over-scope)"
    )
    # The SOURCE documents the behavior-preserving reorder (the refactor that
    # the handcuff pass applies and that this over-scoped test wrongly catches).
    assert "behavior-PRESERVING refactor" in src and "reversed(" in src, (
        "handcuff fixture source lacks the behavior-preserving reorder anchor"
    )


def test_scope_fixture_embodies_instance_pinned_sibling():
    """The scope fixture must have TWO structurally-parallel sites sharing one
    class defect, with a regression test for only ONE — so the replayed
    operator survives at the unguarded sibling. That property is what the scope
    pass flags."""
    src = (FIXTURES / "instance_pinned_validation.py").read_text()
    tst = (FIXTURES / "fixture_instance_pinned_test.py").read_text()
    # Two parallel validators sharing the same bound-check class defect.
    assert "def validate_username" in src and "def validate_email" in src, (
        "scope fixture lacks two structurally-parallel sites"
    )
    assert src.count("len(") >= 2 and src.count("> MAX_LEN") >= 2, (
        "scope fixture sibling sites do not share the same class defect"
    )
    # A regression test for site A only — NO sibling test for site B.
    assert "def test_username_rejects_overlong" in tst, (
        "scope fixture missing the instance regression test"
    )
    assert "def test_email_rejects_overlong" not in tst, (
        "scope fixture has a sibling test — then it is NOT instance-pinned"
    )


def test_fixtures_are_excluded_from_collection():
    """The fixture test files are deliberately over-scoped / instance-pinned
    anchors the audit reads, not project tests — pytest must be configured to
    NOT collect them (else their intentional failures break the suite)."""
    cfg = (REPO / "pytest.ini").read_text()
    assert re.search(r"norecursedirs\s*=.*skills/\*/fixtures", cfg), (
        "pytest.ini must exclude skills/*/fixtures from collection"
    )
    # And the fixture files must actually live there.
    assert list(FIXTURES.glob("fixture_*_test.py")), "no fixture test anchors present"


# ── 0303: /tmp scratch-worktree guard-coverage exemption is documented ────────


def test_tmp_scratch_worktree_exemption_documented():
    """Ticket 0303: maw-audit agents hand-roll detached-HEAD scratch worktrees
    under /tmp (paths like `/tmp/maw-*`, legacy `/tmp/fang-*`), which sit outside
    the guarded `*/.claude/worktrees/*` namespace. Unlike gaze's branch-tracking
    review worktrees (moved under the guarded namespace by ticket 0300), these
    never commit, never push, and never track a branch, so the main-repo
    protection guards have nothing to protect. The exemption must be documented
    at the creation/cleanup site so a future guard-coverage sweep does not
    re-flag it."""
    src = js()
    assert "0303" in src, "the /tmp scratch-worktree exemption must cite ticket 0303"
    # The rationale must name the guarded namespace it is exempt from and WHY
    # (detached HEAD → no branch/commit/push for a guard to protect).
    cleanup = src[src.index("phase('Cleanup')") - 1200 : src.index("phase('Cleanup')")]
    assert ".claude/worktrees" in cleanup, (
        "exemption must reference the guarded .claude/worktrees namespace it sits outside"
    )
    assert "detached HEAD" in cleanup or "detached-HEAD" in cleanup, (
        "exemption rationale must anchor on the detached-HEAD (no branch to protect) property"
    )

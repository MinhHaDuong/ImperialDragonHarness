"""Structural regression tests for the fang-audit skill (ticket 0182).

The workflow itself (``skills/fang-audit/fang-audit.js``) needs live agents to
run end-to-end, so it cannot be exercised in CI. What IS mechanically checkable
is its STRUCTURE — and the structure is where the ticket's contract lives:

  * crit 2 — repo knobs are explicit CONFIG inputs, not name heuristics.
  * crit 5 — a determinism precheck gates (blocks) the fan-out.
  * crit 7 — the canary gate is scoped by a CONFIG-derived structural tag,
             never by the agent-supplied ``isCanary`` flag (the bug it fixes).
  * agnostic — no hardcoded /home paths in the live skill surface.

These are source-inspection assertions (the repo convention for un-runnable
artifacts; see tests/test_rename_orchestrator_to_raid.sh), not a faked
end-to-end run.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "skills" / "fang-audit"
JS = SKILL_DIR / "fang-audit.js"
MD = SKILL_DIR / "SKILL.md"


def js() -> str:
    return JS.read_text()


def test_skill_files_exist():
    assert JS.is_file(), "fang-audit.js missing"
    assert MD.is_file(), "SKILL.md missing"


def test_frontmatter_has_name_and_description():
    front = MD.read_text()
    assert re.search(r"^name:\s*fang-audit\s*$", front, re.MULTILINE)
    assert re.search(r"^description:\s*", front, re.MULTILINE)


def test_expensive_warning_is_prominent():
    """The skill must loudly flag the ~1.3M-token cost so it is never casual."""
    text = MD.read_text()
    assert "1.3M" in text or "1.3 M" in text
    assert "EXPENSIVE" in text


# ── crit 2: explicit knobs, not name heuristics ──────────────────────────────


def test_config_block_declares_explicit_knobs():
    src = js()
    # The pairing table and run command must be CONFIG fields, not derived.
    for knob in ["RUN_TEST", "BEHAVIORAL", "GUARDS", "MUTATION_HEURISTICS",
                 "PRECHECK_CMD", "RISK", "DEFAULT_TAGS", "GUARD_TAGS"]:
        assert re.search(rf"\b{knob}\b", src), f"CONFIG knob {knob} not present"


def test_untracked_seed_is_reinjected_into_guard_prompt():
    """The prototype seeded an untracked guard input via an agent-level copy;
    a fresh worktree lacks it and the canary build would fail to compile. The
    seed must be a CONFIG knob AND actually reach the guard prompt."""
    src = js()
    assert "UNTRACKED_SEED" in src, "untracked-input seed knob missing"
    assert "SEED_INSTRUCTIONS" in src, "seed instructions not built"
    # The copy must be wired into the guard prompt (between guardPrompt start
    # and skepticPrompt start), not just defined.
    gp = src.index("function guardPrompt")
    sp = src.index("function skepticPrompt")
    assert "seed" in src[gp:sp], "seed not injected into guardPrompt"
    # The committed git-erg default must seed resource_test.go (the canary
    # compile-unit input) so the validating run reproduces.
    assert "resource_test.go" in src


def test_pairing_table_is_explicit_map_not_heuristic():
    """BEHAVIORAL must be an explicit test->src array, the M1 fix for the
    X_test.go -> X.go heuristic that returned nonexistent files."""
    src = js()
    # Each entry pairs a `test:` with an `src:` array.
    assert "{ test:" in src and "src:" in src
    # The refs_git_test.go -> refs.go non-1:1 pairing (the heuristic's failure
    # case) must be present, proving it is a real map not a name derivation.
    m = re.search(r"refs_git_test\.go['\"],\s*src:\s*\[([^\]]*)\]", src)
    assert m, "refs_git pairing entry missing"
    assert "refs.go" in m.group(1), "non-1:1 pairing not encoded as explicit map"


# ── crit 5: determinism precheck blocks the run ──────────────────────────────


def test_precheck_calls_0184_flakiness_gate():
    src = js()
    assert "test-quality.py flakiness" in src, "precheck does not call the 0184 gate"
    # Must reference the gate via the harness path, not a bare repo-relative one.
    assert "~/.claude/scripts/test-quality.py" in src


def test_precheck_aborts_and_blocks_fanout():
    src = js()
    # The precheck phase must run BEFORE the Audit fan-out and abort the whole
    # workflow on failure (return early), not merely warn.
    precheck_idx = src.index("phase('Precheck')")
    audit_idx = src.index("phase('Audit')")
    assert precheck_idx < audit_idx, "precheck must precede the audit fan-out"
    gate = src[precheck_idx:audit_idx]
    assert "return { aborted: true" in gate, "precheck does not abort the run"
    assert "suite is flaky" in gate, "missing the required flaky abort message"
    # exit-code contract: treat exit 2 + gate fail as flaky.
    assert "exitCode" in gate and "=== 2" in gate


# ── crit 7: canary gate scoped by CONFIG, never by agent isCanary ────────────


def test_canary_gate_uses_structural_guard_tag_not_agent_claim():
    src = js()
    # Findings from guard agents are tagged structurally from the GUARDS
    # dispatch, NOT read back from a self-asserted flag alone.
    assert "_isGuardFile" in src, "no structural guard tag"
    m = re.search(r"canaryFindings\s*=\s*flat\.filter\(([^)]*)\)", src)
    assert m, "canaryFindings filter not found"
    filt = m.group(1)
    assert "_isGuardFile" in filt, (
        "canary gate must filter on the CONFIG-derived _isGuardFile tag"
    )


def test_canary_gate_does_not_trust_filename_regex_or_bare_iscanary():
    """The prototype's ad-hoc /scaling_test|resource_test/ regex pollution
    patch must be gone — canary scoping is structural, not filename-based."""
    src = js()
    m = re.search(r"canaryFindings\s*=\s*flat\.filter\(([^)]*)\)", src)
    filt = m.group(1)
    assert "scaling_test" not in filt and "resource_test" not in filt, (
        "canary gate still keys on a hardcoded filename regex"
    )


# ── crit 4: free-rider metrics from existing data ────────────────────────────


def test_free_rider_metrics_present():
    src = js()
    assert "oracleStrength" in src, "oracle-strength free rider missing"
    assert "diagnosticity" in src, "diagnosticity free rider missing"
    # Both must be derived from the already-collected findings (caught list),
    # not a fresh run.
    assert "caught" in src


# ── crit 6: risk × churn sort ────────────────────────────────────────────────


def test_risk_churn_sort_present_and_risk_is_input():
    src = js()
    assert "churn" in src.lower(), "churn weighting missing"
    # risk is a human-supplied CONFIG input, never inferred.
    assert "CONFIG.RISK" in src
    assert "survivedRanked" in src, "toothless list is not sorted by risk x churn"


# ── agnostic: no hardcoded home paths in the live surface ────────────────────


def test_no_hardcoded_home_paths():
    for f in (JS, MD):
        text = f.read_text()
        assert not re.search(r"/home/[a-z]", text), f"{f.name} has a /home path"
        assert "github.com" not in text, f"{f.name} references github.com"


# ── 0221: per-agent worktree isolation on the mutating call sites ────────────


def test_mutating_agents_are_worktree_isolated():
    """Workflow agents share the session checkout by default (probe-verified,
    ticket 0221); the mutate->test->revert loops MUST run in per-agent
    worktrees or they corrupt each other. Skeptics are read-only and stay
    non-isolated (worktrees are expensive)."""
    lines = js().splitlines()
    mutating = [ln for ln in lines
                if "agent(auditPrompt(file)" in ln or "agent(guardPrompt(file)" in ln]
    assert len(mutating) == 2, "expected exactly one audit + one guard agent call"
    for ln in mutating:
        assert "isolation: 'worktree'" in ln, f"mutating agent not isolated: {ln.strip()[:80]}"
    # Skeptic stays non-isolated: read-and-judge, no execution.
    (idx,) = [i for i, ln in enumerate(lines) if "agent(skepticPrompt" in ln]
    skeptic_call = "\n".join(lines[idx:idx + 5])
    assert "isolation" not in skeptic_call, "skeptic must stay non-isolated"


def test_skill_md_states_target_repo_requirement():
    text = MD.read_text()
    assert "TARGET repo" in text, "SKILL.md missing the target-repo session requirement"


# ── 0222: per-repo config via args — zero skill-file editing ─────────────────


def test_config_is_defaults_merged_with_args():
    """Per-repo config arrives as the Workflow args input (read from the
    target repo's .fang-audit.json); the engine consumes only the merged
    CONFIG. Editing this file per repo is the defect 0222 removes."""
    src = js()
    assert "const DEFAULTS = {" in src, "DEFAULTS block missing"
    assert re.search(r"const CONFIG = Object\.assign\(\{\}, DEFAULTS,.*args", src), (
        "CONFIG must merge args over DEFAULTS"
    )


def test_path_knobs_are_tilde_expanded():
    src = js()
    assert "CONFIG.OUTPUT = expand(CONFIG.OUTPUT)" in src
    assert "UNTRACKED_SEED" in src and "from: expand(s.from)" in src


def test_meta_precedes_defaults():
    """Workflow scripts must begin with export const meta (after comments)."""
    src = js()
    assert src.index("export const meta") < src.index("const DEFAULTS"), (
        "meta block must precede DEFAULTS"
    )


def test_skill_md_forbids_editing_skill_files():
    text = MD.read_text()
    assert ".fang-audit.json" in text, "config-file flow not documented"
    assert "never edit" in text.lower() or "never edit any skill file" in text.lower()
    assert "Edit the `CONFIG` block" not in text, "stale edit-the-skill instruction remains"
    # The frontmatter argument-hint must not instruct editing the skill file
    # either — it slipped through 0222's first pass because the body checks
    # above match backticked phrasing only (review-pr finding, PR 308 round 1).
    assert "editing the CONFIG block" not in text, (
        "stale frontmatter argument-hint still instructs editing fang-audit.js"
    )

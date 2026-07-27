"""Fork-contract ratchet for the /gaze pipeline (ticket 0193).

The 2026-06-03 raid showed that `context: fork` sub-skills start from a bare
context: args arrive interpolated into the SKILL.md heading, but the body
reads as documentation, and ~4 of 14 forks classified it as "no explicit
task" and fell back to ambient cues (worktree name, stale git status, shared
task list) — producing ticket surveys, a wrong-branch review, and rogue
PR #243. Source-inspection tests below pin the prompt-level and script-level
containment so the contracts cannot silently regress.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"

VERIFY = (SKILLS / "gaze" / "SKILL.md").read_text()
TELEMETRY = (SKILLS / "gaze" / "telemetry.yml").read_text()
ERG_PR_MERGE = (SKILLS / "merge" / "erg-pr-merge").read_text()


def fork_skill_files() -> list[Path]:
    """Every SKILL.md whose frontmatter declares context: fork."""
    found = [p for p in SKILLS.glob("*/SKILL.md") if "context: fork" in p.read_text()]
    assert found, "no context:fork skills discovered — glob or layout changed"
    return found


def test_fork_skills_open_with_task_directive():
    """A bare fork must read its SKILL.md as a directive, not documentation.

    Every fork-context skill opens with a TASK DIRECTIVE block so the model
    cannot classify the prompt as 'skill documentation loaded, no task'.
    """
    for p in fork_skill_files():
        text = p.read_text()
        assert "TASK DIRECTIVE" in text, f"{p}: missing TASK DIRECTIVE opener"


def test_fork_skills_forbid_task_inference():
    """Drifted forks all inferred a task from ambient cues — ban it textually."""
    for p in fork_skill_files():
        text = p.read_text()
        assert "do NOT infer a task" in text, f"{p}: missing the no-task-inference rail"


def test_verify_threads_worktree_path_to_subskills():
    """gaze/SKILL.md must pass the review-worktree path to every sub-skill.

    `context: fork` does not inherit the orchestrator's cwd: during the raid
    the adherence/gate forks landed in the *session* worktree (on whatever
    branch the raid had left it) instead of /tmp/review-<pr>. The path must
    travel as an explicit argument.
    """
    for name in ("/verify-adherence", "/review-pr", "/simplify", "/verify-gate"):
        invocation_lines = [
            line for line in VERIFY.splitlines() if name in line and "worktree=" in line
        ]
        assert invocation_lines, (
            f"gaze/SKILL.md: no invocation of {name} carries worktree=<path>"
        )


def test_subskills_document_worktree_argument():
    """Each gaze sub-skill must cd into the worktree path it receives."""
    for skill in ("verify-adherence", "verify-gate", "review-pr", "review-pr-prose"):
        text = (SKILLS / skill / "SKILL.md").read_text()
        assert "worktree=" in text, (
            f"skills/{skill}/SKILL.md: does not document the worktree= argument"
        )


def test_verify_has_containment_postcondition():
    """Post-gaze git-status check guards against foreign files and rogue
    branch switches before any merge step (ticket 0193 action 2)."""
    assert "## Containment postcondition" in VERIFY
    assert "git status --porcelain" in VERIFY


def test_erg_pr_merge_stages_no_blanket_tickets_dir():
    """`git add tickets/` swept a stash-resurrected stray file into PR #242's
    close commit. Staging must name the exact paths erg close/archive touched.
    Comment mentions are fine — only a command-position whole-directory add
    is banned."""
    offenders = [
        line.strip()
        for line in ERG_PR_MERGE.splitlines()
        if re.match(r"^\s*git add\s+(--all\s+)?(--\s+)?tickets/?\s*($|2>|\|)", line)
    ]
    assert not offenders, "erg-pr-merge still stages the whole tickets/ dir: " + (
        "; ".join(offenders)
    )


def _normalize(text: str) -> str:
    """Collapse runs of whitespace so newline-wrapped sentences match."""
    return re.sub(r"\s+", " ", text)


def test_gaze_phase_2_4_reviewers_forbid_isolation():
    """Phases 2–4 reviewer agents are pinned-cwd read-only; giving them
    `isolation: "worktree"` cuts a fresh tree from the session repo on main,
    re-introducing the wrong-branch failure (ticket 0216, rogue PR #243).
    The prohibition must stay in the phase 2–4 block."""
    norm = _normalize(VERIFY)
    assert 'Do **not** give these agents `isolation: "worktree"`' in norm, (
        "gaze/SKILL.md: phase 2–4 block dropped the reviewer isolation prohibition"
    )


def test_gaze_phase_6_gate_forbids_isolation():
    """The phase-6 gate agent is likewise read-only pinned-cwd; the prohibition
    is phrased differently here (`never isolation: "worktree"`) and wraps a
    newline, so normalize before matching."""
    norm = _normalize(VERIFY)
    assert 'never `isolation: "worktree"`' in norm, (
        "gaze/SKILL.md: phase-6 gate block dropped the isolation prohibition"
    )


def test_gaze_only_reroll_fix_agent_gets_isolation():
    """Only the REROLL fix agent (a mutator) may receive isolation: the four
    `isolation: "worktree"` occurrences are the two prohibitions (phase 2–4,
    phase 6), the phase 2–4 exception note, and the single phase-`Branch on
    verdict` grant. A regression worth catching is a *reviewer or gate* spawn
    gaining isolation — flag any occurrence whose surrounding context is a
    read-only reviewer/gate spawn rather than a prohibition or the fix grant."""
    norm = _normalize(VERIFY)
    occurrences = norm.count('isolation: "worktree"')
    assert occurrences == 4, (
        "gaze/SKILL.md: expected exactly 4 `isolation: \"worktree\"` sites "
        f"(2 prohibitions + 1 exception note + 1 REROLL grant), found {occurrences}; "
        "a new occurrence may be a reviewer/gate spawn wrongly gaining isolation"
    )
    # The sole grant lives in the REROLL fix-agent line.
    assert 'spawn a fix subagent with `isolation: "worktree"`' in norm, (
        "gaze/SKILL.md: the REROLL fix-agent isolation grant changed or was removed"
    )


def test_gaze_tier_recorded_in_telemetry_and_output_shape():
    """The graduated battery tier (ticket 0320) must be auditable: the per-run
    tier has to surface in BOTH the verdict-footer telemetry template and the
    `## /gaze actions` output-shape template, so a reviewer can read which
    battery ran from the posted comment. We assert the token in each rendered
    template, not the tier-definition prose — the prose can be reworded, but the
    machine-visible telemetry field is the contract."""
    # 1. Verdict-footer template — the section under "### Verdict footer".
    _, _, footer_after = VERIFY.partition("### Verdict footer")
    assert footer_after, "gaze/SKILL.md: no `### Verdict footer` section found"
    footer_section = footer_after.split("###", 1)[0]
    footer_telemetry = [
        line for line in footer_section.splitlines() if "telemetry:" in line and "wall=" in line
    ]
    assert footer_telemetry, (
        "gaze/SKILL.md: no `telemetry: … wall=…` template in the verdict-footer section"
    )
    assert any("tier" in line for line in footer_telemetry), (
        "gaze/SKILL.md: verdict-footer telemetry template does not carry a "
        "`tier` field (ticket 0320 exit criterion — tiering must be auditable)"
    )

    # 2. Output-shape template — the fenced block after "## Output shape".
    _, _, after = VERIFY.partition("## Output shape")
    assert after, "gaze/SKILL.md: no `## Output shape` section found"
    fenced = re.findall(r"```(.*?)```", after, re.DOTALL)
    assert fenced, "gaze/SKILL.md: no fenced template under `## Output shape`"
    assert any("tier" in block for block in fenced), (
        "gaze/SKILL.md: `## /gaze actions` output-shape template does not carry "
        "a `tier` field (ticket 0320 exit criterion)"
    )


def test_gaze_documents_fork_liveness_window():
    """A silent fork stalls between the review comment and the verdict (twice
    seen: 2026-07-11, 2026-07-13). The caller-monitored liveness window must be
    documented in SKILL.md and carried as a knob in telemetry.yml — prose and
    knob must not drift apart (ticket 0321)."""
    assert "Fork liveness" in VERIFY, (
        "gaze/SKILL.md: missing the 'Fork liveness' clause"
    )
    assert "fork_liveness_seconds" in VERIFY, (
        "gaze/SKILL.md: does not name the fork_liveness_seconds knob"
    )
    assert "fork_liveness_seconds" in TELEMETRY, (
        "telemetry.yml: missing the fork_liveness_seconds knob"
    )
    assert "GAZE_LIVENESS_WINDOW_S" in VERIFY, (
        "gaze/SKILL.md: does not name the GAZE_LIVENESS_WINDOW_S env override"
    )
    assert "GAZE_LIVENESS_WINDOW_S" in TELEMETRY, (
        "telemetry.yml: missing the GAZE_LIVENESS_WINDOW_S env override"
    )


def test_gaze_liveness_fallback_names_verify_gate_not_a_rerun():
    """On window expiry the fallback must skip re-running phases 2–5, drive
    /verify-gate directly, and key off the three completion markers (verdict
    comment, branch-tip motion, review-worktree mtime) — never relax the gate
    (ticket 0321)."""
    norm = _normalize(VERIFY)
    assert "do not re-run phases 2–5" in norm.lower(), (
        "gaze/SKILL.md: liveness fallback does not forbid re-running phases 2–5"
    )
    assert "/verify-gate" in norm, (
        "gaze/SKILL.md: liveness fallback does not name the direct /verify-gate call"
    )
    assert "verdict comment" in norm, (
        "gaze/SKILL.md: liveness fallback omits the verdict-comment marker"
    )
    assert "branch-tip" in norm, (
        "gaze/SKILL.md: liveness fallback omits the branch-tip-motion marker"
    )
    assert "mtime" in norm, (
        "gaze/SKILL.md: liveness fallback omits the review-worktree mtime marker"
    )


def test_no_bare_stash_in_skills_and_scripts():
    """The stash stack is repo-global (shared across every worktree): a
    clean-tree `git stash` + `git stash pop` round-trip pops someone else's
    stash — this resurrected the historical 0149 ticket file on 2026-06-03.
    Only `git stash list` (read-only) is tolerated in committed tooling."""
    offenders = []
    for root in (SKILLS, REPO / "scripts"):
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix in {".png", ".gif"}:
                continue
            try:
                text = p.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if re.search(r"git stash(?! list)", line):
                    offenders.append(f"{p.relative_to(REPO)}:{n}: {line.strip()}")
    assert not offenders, "bare git stash in committed tooling:\n" + "\n".join(
        offenders
    )


def frontmatter_background(path: Path) -> str | None:
    """The literal `background:` value declared in a SKILL.md frontmatter."""
    head = path.read_text().split("---", 2)
    if len(head) < 3:
        return None
    m = re.search(r"^background:\s*(\S+)\s*$", head[1], re.MULTILINE)
    return m.group(1).lower() if m else None


def test_fork_skills_declare_background_explicitly():
    """Claude Code 2.1.218 made `context: fork` skills background by default.

    A fork cannot wait on a background completion — its turn ends the moment it
    stops calling tools, and the completion re-invokes the MAIN loop, not the
    fork (ticket 0250). So whether a fork runs backgrounded is load-bearing for
    the /gaze pipeline and must never be inherited from an upstream default that
    has already flipped once. Every fork skill pins it.
    """
    missing = [
        str(p.relative_to(REPO))
        for p in fork_skill_files()
        if frontmatter_background(p) is None
    ]
    assert not missing, (
        "context:fork skills with no explicit `background:` in frontmatter — "
        "they would inherit the upstream default:\n" + "\n".join(missing)
    )


def test_only_the_orchestrator_runs_backgrounded():
    """gaze is backgrounded so a raid wave gates several PRs concurrently; every
    sub-skill it invokes as a phase runs foreground so gaze can block on the
    structured output it parses to branch. Parallelism comes from concurrent
    tool calls inside one message, never from backgrounding a phase.
    """
    for p in fork_skill_files():
        value = frontmatter_background(p)
        expected = "true" if p.parent.name == "gaze" else "false"
        assert value == expected, (
            f"{p.relative_to(REPO)}: background={value}, expected {expected} "
            "(only the gaze orchestrator is backgrounded)"
        )

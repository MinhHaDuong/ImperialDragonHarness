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
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

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
    for name in ("/verify-adherence", "/review-pr", "/simplify"):
        invocation_lines = [
            line for line in VERIFY.splitlines() if name in line and "worktree=" in line
        ]
        assert invocation_lines, (
            f"gaze/SKILL.md: no invocation of {name} carries worktree=<path>"
        )


def test_subskills_document_worktree_argument():
    """Each gaze sub-skill must cd into the worktree path it receives."""
    for skill in ("verify-adherence", "review-pr", "review-pr-prose"):
        text = (SKILLS / skill / "SKILL.md").read_text()
        assert "worktree=" in text, (
            f"skills/{skill}/SKILL.md: does not document the worktree= argument"
        )


def test_verify_gate_owns_its_worktree():
    """Gaze removes its review tree before returning (cleanup.md), so the gate
    cannot be handed it: every gate run creates and removes its own tree, and
    no caller passes `worktree=` to the gate (ticket 1153)."""
    gate = (SKILLS / "verify-gate" / "SKILL.md").read_text()
    iso = gate.split("**Isolation — the gate owns its checkout.**", 1)[1].split("## ", 1)[0]
    assert 'worktree add --detach "$gate_tree"' in iso
    assert 'worktree remove "$gate_tree"' in iso
    assert "worktree=" not in gate
    callers = [VERIFY, (SKILLS / "raid" / "SKILL.md").read_text(),
               (SKILLS / "merge" / "SKILL.md").read_text()]
    for text in callers:
        for line in text.splitlines():
            if "/verify-gate <pr" in line:
                assert "worktree=" not in line, line
    assert "worktree remove" in VERIFY, "gaze still removes its review tree"


def test_merge_gates_the_head_that_merges():
    """The caller closes the ticket on the branch before gating, so /merge's
    prerequisite is one equality: ruled tip == origin/<branch> at merge time.
    The helper then pushes nothing, because it skips a ticket already closed
    and archived; the gate reads exit criteria from tickets/closed/ (ticket
    1153, third union review)."""
    merge = " ".join((SKILLS / "merge" / "SKILL.md").read_text().split())
    assert "Close the ticket on the branch before gating." in merge
    assert (
        "the gate's verdict is APPROVED and the gate's `ruled_tip_sha` equals `git rev-parse "
        "origin/<branch>` at merge time, read after `git fetch origin`; otherwise "
        "re-gate, do not merge." in merge
    )
    assert "PRs gated before this rule (#1522, #1523)" in merge
    assert "rev-list --count <ruled>" not in merge
    # Premise: the helper skips an already closed and archived ticket.
    assert 'compgen -G "tickets/closed/${tid}-*.erg"' in ERG_PR_MERGE
    assert "is already closed and archived." in ERG_PR_MERGE
    gate = " ".join((SKILLS / "verify-gate" / "SKILL.md").read_text().split())
    assert "`tickets/<id>-*.erg` **or** `tickets/closed/<id>-*.erg`" in gate
    raid = " ".join((SKILLS / "raid" / "SKILL.md").read_text().split())
    assert "Close before gating:" in raid
    assert "closes the PR's ticket on the PR branch" in raid


def test_gate_sessions_are_caller_owned_and_capped_on_every_path():
    """Gaze no longer calls the gate, so the gate must not key its round cap on
    a gaze caller: a raid calling it directly would land in the old standalone
    override and run a third round (ticket 1153, union review blocker 2)."""
    gate = (SKILLS / "verify-gate" / "SKILL.md").read_text()
    norm = " ".join(gate.split())
    assert "standalone-override" not in gate
    assert "From `/gaze`" not in gate
    assert "called by `/gaze`" not in norm and "from /gaze" not in norm.lower()
    sessions = " ".join(gate.split("## Gate sessions", 1)[1].split("\n## ", 1)[0].split())
    assert "Round > 2 → immediate ESCALATE, whoever calls" in sessions
    assert "does not reset the count" in sessions
    assert "there is no standalone override" in sessions
    assert "`session=<uuid>`" in sessions
    raid = " ".join((SKILLS / "raid" / "SKILL.md").read_text().split())
    assert "session=<uuid>" in raid
    assert "never runs the gate a third time" in raid


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


def test_gaze_battery_not_run_names_cause():
    """Ticket 0990: a battery that cannot launch at all must say so in one
    line naming the cause, composed AFTER the detached-seat substitution —
    first attempt the substitution documented in skills/review-pr/SKILL.md,
    and only if that also cannot run emit the battery NOT-RUN line. The line
    is a launch failure, distinct from review findings and from seat-level
    PANEL-INTEGRITY (whose name is unchanged); findings are never fabricated
    and the gate reports the criteria unverified."""
    battery = VERIFY.split("### 2–4. Read-only review fan-out", 1)[1].split(
        "### 5. Simplify", 1
    )[0]
    norm = _normalize(battery)
    assert "detached-seat substitution" in norm and "skills/review-pr/SKILL.md" in norm, (
        "gaze/SKILL.md: the battery section must first attempt the detached-seat "
        "substitution documented in skills/review-pr/SKILL.md before declaring "
        "the battery NOT-RUN"
    )
    assert re.search(
        r"battery: NOT-RUN — cause: <guard\|no-agent-tool\|depth>", norm
    ), (
        "gaze/SKILL.md: the battery section must carry the one-line "
        "`battery: NOT-RUN — cause: <guard|no-agent-tool|depth>` signal"
    )
    # Composition order: the substitution is attempted BEFORE the NOT-RUN line.
    assert norm.index("detached-seat substitution") < norm.index("battery: NOT-RUN"), (
        "gaze/SKILL.md: the NOT-RUN line is composed only after the detached-seat "
        "substitution was attempted and also failed"
    )
    assert "PANEL-INTEGRITY" in norm and "BATTERY-INTEGRITY" not in VERIFY, (
        "gaze/SKILL.md: the battery NOT-RUN line must not rename or absorb "
        "seat-level PANEL-INTEGRITY"
    )
    assert "never fabricate" in norm, (
        "gaze/SKILL.md: a battery that cannot launch must never fabricate findings"
    )
    # A NOT-RUN battery has a verdict consequence: capped at ESCALATE —
    # otherwise a no-battery run could still return APPROVED (round-1 review).
    assert "capped at ESCALATE" in norm and "never APPROVED" in norm, (
        "gaze/SKILL.md: a battery NOT-RUN must cap the verdict at ESCALATE, "
        "never APPROVED — an unlaunched battery must not read as a pass"
    )
    # The output-shape actions block carries the battery line, after — and
    # distinct from — the panel integrity line.
    output = VERIFY.split("## Output shape", 1)[1]
    fenced = re.findall(r"```(.*?)```", output, re.DOTALL)
    block = next((b for b in fenced if "panel integrity:" in b), None)
    assert block is not None, (
        "gaze/SKILL.md: output-shape actions block lost the panel integrity line"
    )
    m = re.search(
        r"battery: ran \| NOT-RUN — cause: <guard\|no-agent-tool\|depth> \| skipped \(un-reviewable\)",
        block,
    )
    assert m, (
        "gaze/SKILL.md: the output-shape actions block must carry "
        "`battery: ran | NOT-RUN — cause: <guard|no-agent-tool|depth> "
        "| skipped (un-reviewable)`"
    )
    assert block.index("panel integrity:") < m.start(), (
        "gaze/SKILL.md: the battery line must follow the panel integrity line — "
        "the two signals are distinct"
    )


def test_output_shape_lines_define_battery_not_run_value():
    """reviewsub#1 (round 1): the adherence/review/review-pr output-shape
    lines enumerated no value for a battery that could not launch — a
    NOT-RUN run had to fabricate a count or write out-of-enum. Each of the
    three lines must carry `skipped (battery NOT-RUN)` as an option."""
    _, _, after = VERIFY.partition("## Output shape")
    fenced = re.findall(r"```(.*?)```", after, re.DOTALL)
    block = next((b for b in fenced if "panel integrity:" in b), None)
    assert block is not None, (
        "gaze/SKILL.md: output-shape actions block lost the panel integrity line"
    )
    for name in ("adherence:", "review-pr:"):
        lines = [ln for ln in block.splitlines() if ln.strip().startswith(name)]
        assert lines, f"gaze/SKILL.md: output-shape block lost the {name} line"
        assert "skipped (battery NOT-RUN)" in lines[0], (
            f"gaze/SKILL.md: the {name} output-shape line has no value for a "
            "battery that could not launch — it must enumerate "
            "`skipped (battery NOT-RUN)`"
        )


def test_gaze_risk_band_recorded_in_telemetry_and_output_shape():
    """The risk band (ticket 0902) must be auditable like the tier (ticket
    0320): the per-run band has to surface in BOTH the verdict-footer
    telemetry template and the `## /gaze actions` output-shape template, so a
    reviewer can read which band ran from the posted comment."""
    # 1. Verdict-footer template — the section under "### Verdict footer".
    _, _, footer_after = VERIFY.partition("### Verdict footer")
    assert footer_after, "gaze/SKILL.md: no `### Verdict footer` section found"
    footer_section = footer_after.split("###", 1)[0]
    footer_telemetry = [
        line for line in footer_section.splitlines() if "telemetry:" in line and "wall=" in line
    ]
    assert any("risk_band" in line for line in footer_telemetry), (
        "gaze/SKILL.md: verdict-footer telemetry template does not carry a "
        "`risk_band` field (ticket 0902 — the band must be auditable like the tier)"
    )
    fields = footer_section[footer_section.index("Fields:"):]
    assert "risk_band" in fields, (
        "gaze/SKILL.md: the verdict-footer Fields sentence does not name the "
        "`risk_band` field"
    )

    # 2. Output-shape template — the fenced block after "## Output shape".
    _, _, after = VERIFY.partition("## Output shape")
    assert after, "gaze/SKILL.md: no `## Output shape` section found"
    fenced = re.findall(r"```(.*?)```", after, re.DOTALL)
    assert fenced, "gaze/SKILL.md: no fenced template under `## Output shape`"
    block = next((b for b in fenced if "risk_band: high|low|normal" in b), None)
    assert block is not None, (
        "gaze/SKILL.md: `## /gaze actions` output-shape template does not carry "
        "a `risk_band` field (ticket 0902)"
    )
    assert "risk_band=<high|low|normal>" in block, (
        "gaze/SKILL.md: the output-shape telemetry line does not carry "
        "`risk_band` (ticket 0902)"
    )


def test_gaze_refuses_unreviewable_prs():
    """The PR breaker must reuse the monster threshold and run before reviewers."""
    workflow = (REPO / "rules" / "workflow.md").read_text()
    monster = re.search(r"Monster ticket.*?\((\d+)\+ files", workflow, re.DOTALL)
    assert monster, "workflow monster file threshold is missing"

    setup = VERIFY.split("### 1. Setup", 1)[1].split("### 2–4.", 1)[0]
    breaker = re.search(r"pr_files\s*>=\s*(\d+).*?un-reviewable", setup, re.DOTALL)
    assert breaker, "gaze setup has no file-count un-reviewable breaker"
    assert breaker.group(1) == monster.group(1), "gaze threshold drifted from workflow"
    assert "rules/workflow.md" in setup
    assert "ESCALATE" in setup and "before spawning" in setup
    assert "--force-approve" in setup
    # The waiver hatch lifts only the file-count stop; the PR-body declaration
    # and the --waive-breaker flag are both named where the breaker lives.
    assert "--waive-breaker" in setup, "gaze setup lost the --waive-breaker hatch"
    assert "Review-scope: indivisible" in setup, (
        "gaze setup lost the PR-body Review-scope declaration"
    )
    # The workflow rule and the gaze breaker must agree on both hatches.
    assert "skills/gaze/SKILL.md" in workflow and "waiver" in workflow, (
        "rules/workflow.md must name the waiver hatch and point at gaze setup"
    )
    # --force-approve must say it runs no review, not merely skip the gate.
    force = VERIFY.split("## `--force-approve`", 1)[1].split("## Not in scope", 1)[0]
    assert "no reviewer" in force, (
        "the --force-approve section must state it skips review"
    )

    circuits = VERIFY.split("## Circuit breakers", 1)[1].split("## Telemetry", 1)[0]
    output = VERIFY.split("## Output shape", 1)[1]
    assert "un-reviewable" in circuits
    assert "circuit_breaker:" in output


def test_gaze_multi_ticket_is_advisory_below_size_breaker():
    """Distinct close claims inform the gate without blocking a small PR."""
    setup = VERIFY.split("### 1. Setup", 1)[1].split("### 2–4.", 1)[0]
    assert "Ticket-ref:" in setup and "Ticket: none" in setup
    assert "distinct" in setup and "close-claim" in setup
    assert "multi_ticket" in setup and "non-blocking" in setup
    assert "continue the normal review" in setup
    assert "multi_ticket" in VERIFY.split("## Output shape", 1)[1]


@pytest.mark.integration
def test_gaze_close_claim_count_ignores_refs_none_and_duplicate_ids():
    """Exercise the extraction command documented in gaze, including exclusions."""
    setup = VERIFY.split("### 1. Setup", 1)[1].split("### 2–4.", 1)[0]
    match = re.search(r"extract\s+IDs with `(grep[^`]+)`", setup)
    assert match, "gaze must provide an executable close-claim extraction recipe"
    body = "\n".join(
        [
            "**Ticket:** tickets/0901-a.erg",
            "Ticket: tickets/0901-a.erg",
            "Ticket-ref: tickets/0928-b.erg",
            "Ticket: none",
            "Ticket: tickets/0902-c.erg",
            "Discussion mentions tickets/0903-d.erg",
        ]
    )
    result = subprocess.run(
        match.group(1), shell=True, input=body, text=True, capture_output=True,
        check=True, env=child_env(),
    )
    assert result.stdout.splitlines() == ["0901", "0902"]


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
    assert "posted gaze result comment" in norm, (
        "gaze/SKILL.md: liveness fallback omits the result-comment marker"
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


def test_gaze_reviewer_and_gate_prompts_ban_overwrites_and_require_not_run():
    """Ticket 0853: a read-only reviewer/gate agent must never reach a
    working-tree overwrite, and must refuse (NOT-RUN) when the review
    worktree is unreachable rather than silently falling back to the
    session cwd. The phase 2–4 battery carries the portable git -C reach
    contract, the destructive-checkout ban, and the NOT-RUN refusal
    itself (not by reference "as above"). Since ticket 0938's profile
    conversion, the phase 6 gate seat's containment rails live in its
    contract, profiles/gate-seat/PROFILE.md — the launch names the
    profile, so the contract (not the skill body) must carry them."""
    norm = _normalize(VERIFY)
    battery = norm.split("### 2–4.", 1)[1].split("### 5.", 1)[0]
    for name, sec in (("phases 2-4", battery),):
        assert "git checkout <ref> --" in sec, f"{name}: no destructive-checkout ban"
        assert "git show <ref>:<path>" in sec, f"{name}: no read-only alternative named"
        assert "NOT-RUN" in sec, f"{name}: no refusal on unreachable review tree"
        assert "git restore ." in sec, f"{name}: git restore . not banned"
        assert "git reset --hard" in sec, f"{name}: git reset --hard not banned"
        assert "git -C" in sec, f"{name}: no git -C reach contract"
        assert re.search(r"never falls? back to the session cwd", sec), (
            f"{name}: no never-fall-back-to-session-cwd clause"
        )
    assert 'git -C "$primary_root' in battery, (
        "phases 2-4: no git -C reach contract against the primary_root path"
    )


# --- ticket 1125 (round 3): the waiver is judged from the diff; NEEDS-AUTHOR ---

VERIFY_GATE = (SKILLS / "verify-gate" / "SKILL.md").read_text()
RAID = (SKILLS / "raid" / "SKILL.md").read_text()
WAIVER_HEADER = (
    "circuit_breaker: waived (<pr_files> content-bearing files / <pr_lines> lines — <reason>)"
)


def _section(text: str, pattern: str) -> str:
    """Body of the first markdown heading whose title matches `pattern`, up to
    the next heading of the same or a higher level. Heading renames only need
    the pattern updated; the test still reads the section, not a fixed string."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and re.search(pattern, m.group(2), re.I):
            level = len(m.group(1))
            body = []
            for nxt in lines[i + 1:]:
                h = re.match(r"^(#{1,6})\s", nxt)
                if h and len(h.group(1)) <= level:
                    break
                body.append(nxt)
            return _normalize("\n".join(body))
    return ""


def _waiver_section() -> str:
    return _section(VERIFY, r"waiver")


def _indivisibility_section() -> str:
    return _section(VERIFY_GATE, r"indivisib")


def _force_approve_section() -> str:
    return _section(VERIFY, r"force-approve")


def test_verify_gate_takes_waiver_as_input_and_judges_the_diff():
    vg = _normalize(VERIFY_GATE)
    assert "waiver" in vg
    ind = _indivisibility_section()
    assert ind, "verify-gate has no indivisibility section (heading matching 'indivisib')"
    assert "pure rename or a rewire" in ind, "the indivisibility bullet lost its pure-rename/rewire test"
    assert "could land alone" in ind, "the indivisibility bullet lost its independent-change test"
    assert "MISSING" in ind, "a failing indivisibility reason must be a MISSING criterion"
    assert "multi_ticket" in ind, "the indivisibility section lost its multi-ticket rule"


def test_waiver_is_judged_from_the_diff_not_the_declarer():
    """Author decision: the gate judges the diff. No declarer authority claim and
    no declarer field anywhere in the waiver contract."""
    for name, text in (("gaze", VERIFY), ("verify-gate", VERIFY_GATE)):
        assert "declarer" not in text, f"{name} still carries a declarer claim or field"


def test_waived_verdict_is_needs_author():
    assert "NEEDS-AUTHOR" in _indivisibility_section(), (
        "a waived verdict must be marked NEEDS-AUTHOR in the indivisibility section"
    )
    assert re.search(r"verdict: APPROVED \| REROLL \| ESCALATE \| NEEDS-AUTHOR", VERIFY_GATE), (
        "verify-gate verdict shape must list NEEDS-AUTHOR"
    )
    assert "NEEDS-AUTHOR" in _normalize(VERIFY), "gaze must name the NEEDS-AUTHOR outcome the gate rules"


def test_raid_phase7_refuses_needs_author_without_the_author():
    raid = _normalize(RAID)
    phase7 = raid.split("## Phase 7: Merge", 1)[1].split("For each eligible PR", 1)[0]
    assert "NEEDS-AUTHOR" in phase7, "raid Phase 7 eligibility must name NEEDS-AUTHOR"
    assert re.search(r"NEEDS-AUTHOR[^.]*not merge-eligible", phase7), (
        "raid Phase 7: a NEEDS-AUTHOR verdict must be stated as not merge-eligible"
    )


def test_waiver_baseline_is_earliest_posted_header_not_recount():
    ind = _indivisibility_section()
    assert "earliest posted" in ind, "growth must be measured from the earliest posted waived header"
    assert "not the phase-1 recount" in ind, "the baseline must not be the phase-1 recount"
    assert "earliest posted" in _waiver_section()


def test_waiver_growth_past_baseline_is_escalate_with_no_fresh_reason_escape():
    for text in (_indivisibility_section(), _waiver_section(), VERIFY, VERIFY_GATE):
        assert "fresh reason" not in text
    assert "ESCALATE" in _indivisibility_section()
    assert "un-reviewable" in _indivisibility_section()


def test_approved_rule_requires_no_recorded_waiver():
    assert ", with no recorded waiver" in VERIFY_GATE


def test_raid_never_merges_needs_author_on_own_authority():
    raid = _normalize(RAID)
    assert "never merges it on its own authority" in raid
    assert re.search(r"NEEDS-AUTHOR[^.]*not merge-eligible", raid)


def test_gaze_returns_no_gate_verdict():
    norm = _normalize(VERIFY)
    exits = re.findall(r"every(?:\*\*)? exit path \(([^)]*)\)", norm)
    assert exits, "cleanup must name its exit paths"
    for e in exits:
        assert "APPROVED" not in e and "NEEDS-AUTHOR" not in e, e
    desc = VERIFY_GATE.split("description:", 1)[1].splitlines()[0]
    assert "NEEDS-AUTHOR" in desc


def test_gaze_recovery_waiver_read_only_from_posted_header():
    rec = _normalize(VERIFY.split("**Caller-side recovery.**", 1)[1].split("**Fork liveness.**", 1)[0])
    assert "already-posted waived `circuit_breaker` header" in rec
    assert "ESCALATE there" in rec


def test_waiver_header_has_one_format():
    norm = _normalize(VERIFY)
    assert norm.count(WAIVER_HEADER) >= 2, "waived header must match in Setup and Output shape"
    loose = re.findall(r"circuit_breaker: waived \([^)]*\)", norm)
    assert loose and all(h == WAIVER_HEADER for h in loose), sorted(set(loose))


def test_waiver_flags_multi_ticket():
    assert "multi_ticket" in _waiver_section()


def test_force_approve_runs_no_gate_and_output_marks_unrun_phases():
    text = VERIFY
    assert "would-have-been" not in text, "--force-approve must not promise a gate verdict"
    assert "no reviewer" in _force_approve_section()
    template = text.split("## /gaze result", 1)[1].split("Unresolved review comments", 1)[0]
    for phase in ("adherence:", "review-pr:", "simplify:", "battery:"):
        line = next(ln for ln in template.splitlines() if ln.startswith(phase))
        assert "skipped (--force-approve)" in line, f"{phase} must show skipped (--force-approve)"


def test_argument_hint_and_invariants_name_waive_breaker():
    fm = VERIFY.split("---", 2)[1]
    assert "--waive-breaker" in fm, "argument-hint must name --waive-breaker"
    inv = _section(VERIFY, r"^invariants$|invariants")
    assert "--waive-breaker" in inv, "Invariants must name --waive-breaker"


def test_gaze_has_no_waiver_declarer_authority_claim():
    assert "The gate treats a waiver" not in VERIFY


def test_verify_gate_wording_and_no_overpromise():
    vg = _normalize(VERIFY_GATE)
    assert "undeclared source" not in vg
    wf = _normalize((REPO / "rules" / "workflow.md").read_text())
    assert "reviewed in full" not in wf


# --- ticket 1125 (round 4, N1): verify-gate owns the un-reviewable breaker ---

GATE_SEAT = (REPO / "profiles" / "gate-seat" / "PROFILE.md").read_text()


def _section_raw(text: str, pattern: str) -> str:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and re.search(pattern, m.group(2), re.I):
            level = len(m.group(1))
            body = []
            for nxt in lines[i + 1:]:
                h = re.match(r"^(#{1,6})\s", nxt)
                if h and len(h.group(1)) <= level:
                    break
                body.append(nxt)
            return "\n".join(body)
    return ""


def _bullets(text: str, pattern: str) -> list[str]:
    """Each top-level `- ` bullet of the matching section, unwrapped to one line."""
    out: list[str] = []
    cur: str | None = None
    for ln in _section_raw(text, pattern).split("\n"):
        if ln.startswith("- "):
            if cur is not None:
                out.append(cur)
            cur = ln[2:]
        elif cur is not None and ln.startswith("  "):
            cur += " " + ln.strip()
        else:
            if cur is not None:
                out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return [_normalize(b) for b in out]


def _find(bullets: list[str], *needles: str) -> str | None:
    for b in bullets:
        if all(n in b for n in needles):
            return b
    return None


def test_verify_gate_breaker_escalates_unwaived_monster_pr():
    """The gate counts the files itself: >= 15 with no waiver record is ESCALATE,
    whatever the caller passed, so a recovery run cannot approve an oversized PR."""
    bullets = _bullets(VERIFY_GATE, r"^circuit breakers$")
    b = _find(bullets, "pr_files >= 15", "no waiver record", "ESCALATE", "un-reviewable")
    assert b, "verify-gate Circuit breakers lost the un-waived 15-file ESCALATE bullet"


def test_verify_gate_breaker_routes_waived_pr_to_needs_author():
    bullets = _bullets(VERIFY_GATE, r"^circuit breakers$")
    b = _find(bullets, "waiver record", "Indivisibility", "NEEDS-AUTHOR", "never APPROVED")
    assert b, "verify-gate Circuit breakers lost the waived-PR NEEDS-AUTHOR bullet"


def test_verify_gate_reads_waiver_from_pr_history_when_caller_omits_it():
    """Every invocation path (gaze recovery, liveness expiry, standalone) must hold
    the check: with no record passed, the gate reads the earliest posted waived header."""
    bullets = _bullets(VERIFY_GATE, r"^circuit breakers$")
    b = _find(bullets, "earliest posted", "circuit_breaker: waived", "PR comments")
    assert b, "verify-gate must read the waiver from the PR's earliest posted header"


def test_verify_gate_decision_rules_pin_the_waiver_branches():
    bullets = _bullets(VERIFY_GATE, r"^decision rules$")
    assert _find(bullets, "pr_files >= 15", "no waiver", "ESCALATE"), (
        "decision rules lost the un-waived size ESCALATE"
    )
    assert _find(bullets, "waiver", "NEEDS-AUTHOR", "never APPROVED"), (
        "decision rules lost the waived NEEDS-AUTHOR bullet"
    )


def test_gate_seat_profile_lists_needs_author():
    charter = _normalize(GATE_SEAT.split("Charter:", 1)[1])
    assert "NEEDS-AUTHOR" in charter, "gate-seat charter must list NEEDS-AUTHOR"


def test_resident_rules_do_not_cite_tickets_for_this_change():
    for name in ("workflow.md", "git.md", "claude-code.md", "guards.md"):
        text = (REPO / "rules" / name).read_text()
        assert not re.search(r"\(ticket \d{4}\)|ticket 1125|\b1125\b", text), (
            f"rules/{name} cites a ticket number"
        )


def test_verify_gate_recounts_the_breaker_itself():
    """Gaze's verdict-time recount went with its gate phase (ticket 1153); the
    gate's own recount is what still stops an oversized PR at merge time."""
    gate = " ".join((SKILLS / "verify-gate" / "SKILL.md").read_text().split())
    breakers = gate.split("## Circuit breakers", 1)[1].split("## Not in scope", 1)[0]
    assert "the gate counts the content-bearing files itself" in breakers
    assert "`git diff --name-status -M`" in breakers
    assert "`git diff --numstat -M`" in breakers
    assert "`pr_files >= 15`" in breakers
    assert "does not trust the caller's count" in breakers
    rules = gate.split("## Decision rules", 1)[1].split("## ", 1)[0]
    assert "counted by the gate itself on every invocation path" in rules


def test_ruled_tip_field_has_one_name_across_gate_and_callers():
    """/gaze 1523: posted verdicts carry `ruled_tip_sha:` while merge and raid
    read `Ruled tip SHA`. The name the gate posts is the name callers read."""
    gate = (SKILLS / "verify-gate" / "SKILL.md").read_text()
    posted = gate.split("2. PR comment posted", 1)[1].split("```", 2)[1]
    names = re.findall(r"^\s*([\w ]+): <full commit SHA", posted, re.MULTILINE)
    assert len(names) == 1, names
    field = names[0].strip()
    assert re.search(rf"^{field}: <full commit SHA", gate.split("## Verdict shape", 1)[1], re.MULTILINE)
    spelling = re.compile(r"ruled[ _-]?tip[ _-]?sha", re.IGNORECASE)
    for name in ("merge", "raid", "dashboard", "verify-gate"):
        text = (SKILLS / name / "SKILL.md").read_text()
        found = set(spelling.findall(text))
        assert found == {field}, (name, found)
    assert f"the gate's `{field}` equals `git rev-parse" in (SKILLS / "merge" / "SKILL.md").read_text()

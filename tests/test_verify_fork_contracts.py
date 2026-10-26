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
    for name in ("/verify-adherence", "/simplify"):
        invocation_lines = [
            line for line in VERIFY.splitlines() if name in line and "worktree=" in line
        ]
        assert invocation_lines, (
            f"gaze/SKILL.md: no invocation of {name} carries worktree=<path>"
        )


def test_subskills_document_worktree_argument():
    """Each gaze sub-skill must cd into the worktree path it receives."""
    for skill in ("verify-adherence",):
        text = (SKILLS / skill / "SKILL.md").read_text()
        assert "worktree=" in text, (
            f"skills/{skill}/SKILL.md: does not document the worktree= argument"
        )


def _gate_calls_with_worktree(text: str) -> list[str]:
    """Gate invocations passing worktree=, over whitespace-normalized text so a
    wrapped call is seen. A call runs to the closing backtick or sentence end."""
    norm = " ".join(text.split())
    return [m.group(0) for m in re.finditer(r"/verify-gate <pr[^`]*", norm) if "worktree=" in m.group(0)]


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
        assert not _gate_calls_with_worktree(text)
    # Negative controls: a wrapped invocation must be caught too.
    assert _gate_calls_with_worktree("run `/verify-gate <pr>\n  repo=x worktree=y`")
    assert _gate_calls_with_worktree("run /verify-gate <pr> repo=x worktree=y")
    assert "worktree remove" in VERIFY, "gaze still removes its review tree"


def test_merge_gates_the_head_that_merges():
    """The caller closes the ticket on the branch before gating; /merge's
    prerequisite is APPROVED plus at most a bookkeeping delta from the ruled
    tip to origin/<branch> at merge time (ticket 1221). The recipe's close
    step then finds the ticket already closed and archived and adds no commit;
    the gate reads exit criteria from tickets/closed/ (ticket 1153, third union
    review)."""
    merge = " ".join((SKILLS / "merge" / "SKILL.md").read_text().split())
    assert "Close the ticket on the branch before gating." in merge
    assert (
        "the gate's verdict is APPROVED and what `origin/<branch>` adds to the gate's "
        "`ruled_tip_sha` (read after `git fetch origin`) is bookkeeping, an empty delta "
        "included (§ Gating tiers); otherwise re-gate, do not merge." in merge
    )
    assert "#1522" not in merge and "Documented exception" not in merge
    assert "rev-list --count <ruled>" not in merge
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


def _normalize(text: str) -> str:
    """Collapse runs of whitespace so newline-wrapped sentences match."""
    return re.sub(r"\s+", " ", text)


def test_gaze_battery_not_run_names_cause():
    """Ticket 0990: a battery that cannot launch at all must say so in one
    line naming the cause, composed AFTER the detached-seat substitution —
    first attempt the substitution documented in references/panel.md,
    and only if that also cannot run emit the battery NOT-RUN line. The line
    is a launch failure, distinct from review findings and from seat-level
    PANEL-INTEGRITY (whose name is unchanged); findings are never fabricated
    and the gate reports the criteria unverified."""
    battery = VERIFY.split("### 2–4. Read-only review fan-out", 1)[1].split(
        "### 5. Simplify", 1
    )[0]
    norm = _normalize(battery)
    assert "detached-seat substitution" in norm and "references/panel.md" in norm, (
        "gaze/SKILL.md: the battery section must first attempt the detached-seat "
        "substitution documented in references/panel.md before declaring "
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
        r"battery: ran \| NOT-RUN — cause: <guard\|no-agent-tool\|depth> \| skipped \(--force-approve\)",
        block,
    )
    assert m, (
        "gaze/SKILL.md: the output-shape actions block must carry "
        "`battery: ran | NOT-RUN — cause: <guard|no-agent-tool|depth> "
        "| skipped (--force-approve)`"
    )
    assert block.index("panel integrity:") < m.start(), (
        "gaze/SKILL.md: the battery line must follow the panel integrity line — "
        "the two signals are distinct"
    )


def test_output_shape_lines_define_battery_not_run_value():
    """reviewsub#1 (round 1): the adherence/review/panel output-shape
    lines enumerated no value for a battery that could not launch — a
    NOT-RUN run had to fabricate a count or write out-of-enum. Each of the
    three lines must carry `skipped (battery NOT-RUN)` as an option."""
    _, _, after = VERIFY.partition("## Output shape")
    fenced = re.findall(r"```(.*?)```", after, re.DOTALL)
    block = next((b for b in fenced if "panel integrity:" in b), None)
    assert block is not None, (
        "gaze/SKILL.md: output-shape actions block lost the panel integrity line"
    )
    for name in ("adherence:", "panel:"):
        lines = [ln for ln in block.splitlines() if ln.strip().startswith(name)]
        assert lines, f"gaze/SKILL.md: output-shape block lost the {name} line"
        assert "skipped (battery NOT-RUN)" in lines[0], (
            f"gaze/SKILL.md: the {name} output-shape line has no value for a "
            "battery that could not launch — it must enumerate "
            "`skipped (battery NOT-RUN)`"
        )


def test_gaze_multi_ticket_is_advisory():
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


MERGE = (SKILLS / "merge" / "SKILL.md").read_text()


def test_caller_documents_gaze_fork_liveness_window():
    """A silent fork stalls between the review comment and the result (twice
    seen: 2026-07-11, 2026-07-13). The liveness window is the caller's watch,
    so /merge documents it (ticket 1219; formerly gaze's, ticket 0321) and
    telemetry.yml carries the knob: prose and knob must not drift apart."""
    for text, where in ((MERGE, "merge/SKILL.md"), (TELEMETRY, "telemetry.yml")):
        assert "fork_liveness_seconds" in text, f"{where}: no fork_liveness_seconds knob"
        assert "GAZE_LIVENESS_WINDOW_S" in text, f"{where}: no GAZE_LIVENESS_WINDOW_S override"
    assert "Fork liveness" in MERGE, "merge/SKILL.md: missing the 'Fork liveness' clause"
    assert "Fork liveness" not in VERIFY, "gaze prescribes no caller watch (ticket 1219)"


def test_liveness_fallback_names_verify_gate_not_a_rerun():
    """On window expiry the caller skips re-running phases 2–5, never
    substitutes a direct /verify-gate, and keys off the three completion
    markers (result comment, branch-tip motion, review-worktree mtime)
    (ticket 0321, moved to /merge by ticket 1219)."""
    norm = _normalize(MERGE)
    assert "do not re-run phases 2–5" in norm.lower()
    assert "never substitute a direct `/verify-gate`" in norm.lower()
    assert "posted gaze result comment" in norm
    assert "branch-tip" in norm
    assert "mtime" in norm


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


# --- ticket 1125 (round 3): the NEEDS-AUTHOR verdict ---

VERIFY_GATE = (SKILLS / "verify-gate" / "SKILL.md").read_text()
RAID = (SKILLS / "raid" / "SKILL.md").read_text()


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


def _force_approve_section() -> str:
    return _section(VERIFY, r"force-approve")


def test_verdict_shape_lists_needs_author():
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


def test_force_approve_runs_no_gate_and_output_marks_unrun_phases():
    text = VERIFY
    assert "would-have-been" not in text, "--force-approve must not promise a gate verdict"
    assert "nothing is reviewed" in _normalize(_force_approve_section())
    template = text.split("## /gaze result", 1)[1].split("Unresolved review comments", 1)[0]
    for phase in ("adherence:", "panel:", "simplify:", "battery:"):
        line = next(ln for ln in template.splitlines() if ln.startswith(phase))
        assert "skipped (--force-approve)" in line, f"{phase} must show skipped (--force-approve)"


FORCED_RESULT = (
    "`--force-approve` returns `result: ESCALATE` with `battery: skipped (--force-approve)`; "
    "nothing is reviewed, so REVIEWED is unavailable."
)


def _forced_result_stated(section: str) -> bool:
    return FORCED_RESULT in _normalize(section)


def test_force_approve_returns_escalate_never_reviewed():
    """/gaze 1538 item 3: the flag skips the whole battery, so its result is
    ESCALATE, never REVIEWED (which means reviewed with no blocking finding).
    The result rules of phase 6 say the same."""
    assert _forced_result_stated(_force_approve_section())
    assert "`--force-approve` is ESCALATE too" in _normalize(VERIFY)
    # Negative control: the check fails once the sentence is gone.
    norm = _normalize(_force_approve_section())
    assert not _forced_result_stated(norm.replace(FORCED_RESULT, ""))


# --- ticket 1125 (round 4, N1): gate-seat charter and resident rules ---

GATE_SEAT = (REPO / "profiles" / "gate-seat" / "PROFILE.md").read_text()


def test_gate_seat_profile_lists_needs_author():
    charter = _normalize(GATE_SEAT.split("Charter:", 1)[1])
    assert "NEEDS-AUTHOR" in charter, "gate-seat charter must list NEEDS-AUTHOR"


def test_resident_rules_do_not_cite_tickets_for_this_change():
    for name in ("workflow.md", "git.md", "claude-code.md", "guards.md"):
        text = (REPO / "rules" / name).read_text()
        assert not re.search(r"\(ticket \d{4}\)|ticket 1125|\b1125\b", text), (
            f"rules/{name} cites a ticket number"
        )


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
    assert f"--since <{field}>" in (SKILLS / "merge" / "SKILL.md").read_text()


def test_merge_checks_head_equality_and_tier_delta():
    """PR 1539 review: the close step runs `git push origin HEAD`, so HEAD must
    equal origin/<branch> after a fetch; ticket 1221: the full tier then reads
    the delta since the ruled tip mechanically."""
    merge = " ".join((SKILLS / "merge" / "SKILL.md").read_text().split())
    assert (
        "`git fetch origin`, then `git rev-parse HEAD` == `git rev-parse origin/<branch>` "
        "(a mismatch means sync, never merge) and, full tier, `merge-gate.py tier --since "
        "<ruled_tip_sha>` answers 0 (otherwise re-gate)" in merge
    )
    assert "so it pushes no commit of its own" not in merge
    assert "so the retry pushes nothing" not in merge
    assert "An unpushed local commit would ride along, so push first" in merge


def test_merge_accepted_gaze_result_is_not_tautological():
    """PR 1539 review: 'Accepted' mirrors raid — present and not stale
    against the branch tip."""
    merge = " ".join((SKILLS / "merge" / "SKILL.md").read_text().split())
    assert "its `reviewed_head_sha` is the reviewed head" not in merge
    assert "its `reviewed_head_sha` is not stale against the branch tip" in merge


def test_dashboard_allows_at_most_a_bookkeeping_delta_past_the_ruled_tip():
    """The dashboard names no historical exception; since ticket 1221 the head
    may add at most a bookkeeping delta to ruled_tip_sha."""
    dash = " ".join((SKILLS / "dashboard" / "SKILL.md").read_text().split())
    assert "a later ticket-close commit from the merge helper is normal" not in dash
    assert "#1522" not in dash and "exception" not in dash
    assert "a branch head that adds at most a bookkeeping delta to the `ruled_tip_sha`" in dash


def test_git_rule_rebases_before_round_one_gate_and_syncs_after_gaze():
    rule = " ".join((REPO / "rules" / "git.md").read_text().split())
    assert "syncs after `/gaze`" in rule
    assert "before the round-1 `/verify-gate`" in rule
    assert "a later rebase is gated by the tier of what it changes" in rule
    assert "`/merge` § Gating tiers" in rule


def test_gate_tree_is_per_session_and_round_and_repo_is_required():
    gate = (SKILLS / "verify-gate" / "SKILL.md").read_text()
    assert 'gate-<pr-number>"' not in gate
    assert 'gate_tree="$primary_root/.claude/worktrees/gate-<pr-number>-<session-id>-r<round>"' in gate
    assert "`<pr-number>` alone" not in gate
    assert '"no repo argument"' in gate


NO_REVIEW_NO_GATE = "**No gate without a completed review.**"


def _no_review_no_gate(gate: str) -> bool:
    norm = _normalize(gate)
    if NO_REVIEW_NO_GATE not in norm:
        return False
    para = norm.split(NO_REVIEW_NO_GATE, 1)[1].split(" - **", 1)[0]
    return all(s in para for s in (
        "Standalone or from a caller",
        "latest posted `## /gaze result` is ESCALATE",
        "no gaze result was accepted for the current head",
        "the gate answers ESCALATE without ruling the criteria",
    ))


def test_gate_refuses_a_head_without_a_completed_review():
    """Post-merge follow-up: the gate itself, not only its callers, refuses to
    rule when gaze escalated or no result covers the current head."""
    sessions = VERIFY_GATE.split("## Gate sessions", 1)[1].split("\n## ", 1)[0]
    assert _no_review_no_gate(sessions)
    # Negative control: removing the paragraph fails the check.
    start = sessions.index("- **No gate without a completed review.**")
    end = sessions.index("\n\n", start)
    assert not _no_review_no_gate(sessions[:start] + sessions[end:])


def test_queued_merge_wait_is_one_bounded_background_command():
    """Author request: the caller waits for a queued merge itself, with one
    bounded background command, and never hands the wait to the author."""
    merge = _normalize((SKILLS / "merge" / "SKILL.md").read_text())
    wait = merge.split("**Waiting for a queued merge.**", 1)[1].split("**", 1)[0]
    for phrase in (
        "Where the runtime wakes the session when a background command exits",
        "exactly one background command with a hard time bound of about 25 minutes",
        "polls this single-read status command at an interval inside the command",
        "exits as soon as the status is no longer pending",
        "the runtime wakes the caller on exit",
        "Never ask the author to wait or to re-run later",
        "never a fixed-delay timer",
        "never an unbounded or foreground loop",
        "A runtime that cannot wake the session on exit",
        "asks once at its next step and reports the PR as pending",
    ):
        assert phrase in wait, phrase
    # Running background commands is not enough: a runtime can run them and
    # never wake the model, which would leave the chain parked (probed on Codex
    # and Pi, 2026-10-21). The condition is the wake-up, not the facility.
    assert "Where the runtime runs background commands" not in wait
    assert "A runtime without background commands" not in wait
    assert "never loops, sleeps or watches" not in merge
    roar = _normalize((SKILLS / "roar" / "SKILL.md").read_text())
    assert "§ Waiting for a queued merge" in roar
    assert "never ask the author to wait or to re-run `/roar`" in roar
    assert "the user or a later step re-runs" not in roar
    # Every other place that described the outcome read points at the wait.
    raid = _normalize((SKILLS / "raid" / "SKILL.md").read_text())
    for name, text in (("merge", merge), ("raid", raid), ("roar", roar)):
        for stale in ("ask again later", "ask again once before", "once asked again",
                      "Do not loop on the status command", "The caller asks again at its next step"):
            assert stale not in text, (name, stale)
    assert "§ Waiting for a queued merge" in raid

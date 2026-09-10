"""A forked skill must not orphan the agents it spawns (ticket 0250).

The invariant, unchanged and still the whole point: `/gaze` and the review
skills run as `context: fork`. A fork's turn ends the instant it stops calling
tools. A fan-out it cannot wait on is orphaned — the completions re-invoke the
MAIN loop, the fork's final message is a narration ("reviewers are running in
parallel…"), later phases never run, and no verdict is produced (aedist 0538
`/gaze 977`, aedist 0540 `/gaze 978`).

**What changed, 2026-09-10 (ticket 0900).** The remedy this file used to
enforce was "launch foreground, `run_in_background: false`". The delegation
tool has no such parameter: subagents always run in the background and notify
the session. So the enforced remedy named a lever that does not exist, and the
skills satisfied it by *saying the words*. The proof is this file's own record
— it was green while `/review-pr` orphaned its panel on two consecutive rounds,
ten reviewers returning real verdicts and the merge request carrying none of
them. A guard that passes while the defect it exists to prevent is happening is
measuring the wrong thing.

The remedy that can actually hold is a wait that survives the fork: launch in
the background, have each agent write its result to a named artifact, and poll
for those artifacts in one bounded loop. The poll is a tool call, so the fork
stays alive; the artifacts outlive it either way.

What this file enforces now:

1. No launch site cites `run_in_background` as a live directive — the parameter
   does not exist, and a contract resting on it cannot hold a phase together.
2. Every parallel-agent launch site carries, locally, evidence of a wait that
   survives the fork: polling, an artifact, a manifest, a bounded deadline.
3. The failure mode and caller-side recovery stay documented in the skill.
"""

import re
from pathlib import Path

import pytest
from test_verify_fork_contracts import fork_skill_files

REPO = Path(__file__).resolve().parents[1]
GAZE = REPO / "skills" / "gaze" / "SKILL.md"

# Every `context: fork` skill must carry the wait contract *locally*, at
# each parallel-agent launch site, not merely somewhere in the file (ticket
# 0263). Auto-discovered from frontmatter via fork_skill_files() so a new fork
# skill is covered without editing a hand-maintained list — a blind all-skills
# sweep would over-fire on raid/release, which legitimately launch background
# agents because they are not forks and can wait on background completions.
FORK_LAUNCH_SKILLS = {p.parent.name: p for p in fork_skill_files()}


def _body(md_text: str) -> str:
    """Return the SKILL.md content after the YAML frontmatter block."""
    parts = md_text.split("---", 2)
    return parts[2] if len(parts) >= 3 else md_text


# Citing `run_in_background` as a live directive is the defect now: the
# delegation tool has no such parameter, either value, so a launch site resting
# on it describes a lever that does not exist. Naming it to forbid it, or to
# record that it never existed, is fine — separated by negation context, as
# before. Background launch itself is no longer an offence; it is the only mode
# available, and what matters is whether a surviving wait accompanies it.
NONEXISTENT_PARAM = re.compile(r"run_in_background", re.IGNORECASE)

# Words that turn a background mention into a prohibition or an explanation of
# the failure, not a launch directive.
NEGATION = re.compile(
    r"\b(not|never|don't|do not|instead|rather than|orphan|trap|does not|"
    r"fork cannot|cannot wait|re-invoke|would|if.*returns)\b",
    re.IGNORECASE,
)

# Phrasing that proves the wait survives the fork. Polling an artifact is the
# mechanism; a manifest is what makes the poll a real check rather than a
# gather; a bounded deadline is what stops it hanging. Any of these, stated
# locally, is evidence the launch site knows how it will wait. "Blocking" and
# "synchronous" remain accepted: they describe the wait correctly, and a skill
# may reasonably say the fork blocks on the poll.
SURVIVING_WAIT = re.compile(
    r"poll(?:s|ing|ed)?\b|artifact|manifest|bounded|deadline"
    r"|synchronous(?:ly)?|blocking\s+(?:launch|call|agent|on)",
    re.IGNORECASE,
)


def _sentences(text: str) -> list[str]:
    # Coarse sentence split on ., ; and newlines — enough to scope a background
    # mention to its clause for the negation check. Deliberately NOT on ":": the
    # colon lives inside the very tokens we test (`run_in_background: true/false`),
    # so splitting there would tear `run_in_background:` from its value and hide
    # the directive from NONEXISTENT_PARAM/SURVIVING_WAIT (ticket 0263 B2). Dropping
    # ":" only merges adjacent clauses, which makes negation scoping strictly
    # safer (a merged clause is more likely to carry a negation word, never less).
    return re.split(r"(?<=[.;])\s+|\n+", text)


def _paragraphs(text: str) -> list[str]:
    """Split a skill body into blank-line-separated paragraphs."""
    return [p for p in re.split(r"\n[ \t]*\n", text) if p.strip()]


# A launch-indicator paragraph describes spinning up a battery of agents to run
# in parallel. The three conjuncts together are what makes it a *launch site*
# (as opposed to prose that merely mentions parallelism). The parallel signal is
# the bare word "parallel", not only the "in parallel" bigram: gaze's primary
# fan-out paragraph reads "as parallel background Agent calls" / "parallel Agent
# calls", which the tighter bigram missed, letting the ratchet skip the very
# launch site it exists to guard (ticket 0263 B1). The AGENTS + SPAWN_VERB
# conjuncts keep bare parallelism prose (e.g. "builds compile in parallel") out.
IN_PARALLEL = re.compile(r"\bparallel\b", re.IGNORECASE)
AGENTS = re.compile(r"\bagents?\b", re.IGNORECASE)
SPAWN_VERB = re.compile(r"\b(spin|spawn|launch|run)\b", re.IGNORECASE)


def _is_launch_paragraph(p: str) -> bool:
    return bool(IN_PARALLEL.search(p) and AGENTS.search(p) and SPAWN_VERB.search(p))


def _has_nonnegated(pattern: re.Pattern, window: str) -> bool:
    """True if `pattern` matches in at least one clause of `window` that is not
    in negation context — reuses the file-wide NEGATION/_sentences machinery so
    a historical or forbidden mention does not count as a live directive."""
    return any(
        pattern.search(s) and not NEGATION.search(s) for s in _sentences(window)
    )


def _window_offends(window: str) -> bool:
    """Whether a launch-paragraph window violates the local wait contract.

    Two ways to offend (ticket 0263 B2, remedy corrected by ticket 0900):
    - a live (non-negated) `run_in_background` citation sits in the window — the
      parameter does not exist, so the window is describing a wait it cannot
      perform, whatever else it says; and
    - no *non-negated* surviving-wait evidence is present — a historical or
      forbidden mention ("previously polled", "does not poll") does not prove
      this launch site waits.
    """
    if _has_nonnegated(NONEXISTENT_PARAM, window):
        return True
    return not _has_nonnegated(SURVIVING_WAIT, window)


def test_no_citation_of_nonexistent_launch_parameter():
    body = _body(GAZE.read_text())
    offenders = [
        s.strip()
        for s in _sentences(body)
        if NONEXISTENT_PARAM.search(s) and not NEGATION.search(s)
    ]
    assert not offenders, (
        "gaze SKILL.md cites `run_in_background` as a live launch directive. "
        "The delegation tool has no such parameter, either value — a contract "
        "resting on it is satisfied by saying the words while the fan-out is "
        "orphaned exactly as before (ticket 0900). Say how the fork waits "
        f"instead. Offending clauses: {offenders}"
    )


def test_fanout_wait_survives_the_fork():
    body = _body(GAZE.read_text())
    assert SURVIVING_WAIT.search(body), (
        "gaze SKILL.md must say how its reviewer/gate fan-out is waited for in "
        "a way that survives the fork — polling a written artifact, against a "
        "manifest, under a bounded deadline (ticket 0250 invariant, ticket "
        "0900 remedy)."
    )


def test_failure_mode_documented():
    body = _body(GAZE.read_text()).lower()
    # The skill must carry the fork-orphan failure mode + caller recovery.
    assert "fan-out" in body or "fanout" in body
    assert "orphan" in body or "before a verdict" in body or "never delivers" in body, (
        "gaze SKILL.md must document the fork-returns-at-fan-out failure mode "
        "and the caller-side recovery (ticket 0250, exit criterion 3)."
    )


# --- Paragraph-scoped locality ratchet (ticket 0263) ------------------------
#
# The file-wide tests above passed while /gaze 479 (2026-07-11) still orphaned
# its panel: gaze's Agent C paragraph told the inner fan-out to "run ... in
# parallel" with no local concurrency directive, and the two sub-skills it
# delegates to (review-pr, review-pr-prose — both `context: fork`) carried zero
# foreground language anywhere. A single foreground mention elsewhere in the
# file satisfied the outer ratchet; the launch site itself stayed silent. This
# ratchet is *local*: every paragraph that is a parallel-agent launch site must
# carry the foreground contract in that same paragraph (or the next one).


@pytest.mark.parametrize("name", sorted(FORK_LAUNCH_SKILLS))
def test_launch_paragraph_carries_local_wait_contract(name):
    paras = _paragraphs(_body(FORK_LAUNCH_SKILLS[name].read_text()))
    offenders = []
    for i, p in enumerate(paras):
        if not _is_launch_paragraph(p):
            continue
        window = p + "\n" + (paras[i + 1] if i + 1 < len(paras) else "")
        if _window_offends(window):
            offenders.append(p.strip()[:220])
    assert not offenders, (
        f"{name} SKILL.md has a parallel-agent launch paragraph with no local "
        "account of how the fork waits — polling a written artifact, against a "
        "manifest, under a bounded deadline — in that same paragraph or the "
        "next. A forked skill that ends its turn at the fan-out orphans the "
        f"children one layer down (ticket 0263, /gaze 479; remedy corrected by "
        f"ticket 0900). Offending paragraph(s): {offenders}"
    )


# --- B1: launch-site detection must catch the primary fan-out phrasing --------
#
# gaze's primary review fan-out paragraph reads "...as parallel foreground Agent
# calls..." — it carries no literal "in parallel" bigram, so the old detector
# never classified it as a launch site and the ratchet skipped it: stripping its
# local foreground contract stayed green (/gaze 482 round-1 mutation). These
# synthetic fixtures pin the broadened detection without depending on the exact
# current SKILL.md prose.


def test_is_launch_paragraph_detects_parallel_foreground_phrasing():
    assert _is_launch_paragraph(
        "Spawn the applicable agents as parallel foreground Agent calls."
    )


def test_is_launch_paragraph_detects_parallel_agent_calls():
    assert _is_launch_paragraph(
        "Launch the reviewers as parallel Agent calls in one message."
    )


def test_is_launch_paragraph_ignores_non_launch_parallel_prose():
    # A bare mention of parallelism without an agent-spawn directive is not a
    # launch site — the three conjuncts (parallel + agents + spawn verb) hold.
    assert not _is_launch_paragraph("The two builds compile in parallel on CI.")


def test_real_gaze_primary_launch_paragraph_in_scope():
    paras = _paragraphs(_body(GAZE.read_text()))
    launch = [p for p in paras if _is_launch_paragraph(p)]
    assert any("parallel background" in p.lower() for p in launch), (
        "gaze's primary review fan-out paragraph is not classified as a launch "
        "site, so the locality ratchet never inspects it — stripping its local "
        "wait contract would go unnoticed (ticket 0263 B1)."
    )
    assert len(launch) >= 2


# --- B2: wait evidence must survive negation, a dead lever must not slip in ---
#
# The window check had no negation awareness: a live directive, or a
# negated/historical mention of the wait, still satisfied the contract because
# the pattern matched the token regardless of context. The vocabulary changed
# with ticket 0900; the negation machinery it guards did not.


def test_window_offends_dead_parameter_despite_wait_token():
    window = (
        "Spawn the panel as parallel Agent calls with "
        "run_in_background: false and wait. Results are polled."
    )
    assert _window_offends(window), (
        "citing a parameter the delegation tool does not have must offend even "
        "with a stray wait token nearby — that pairing is exactly what stayed "
        "green while the panel was orphaned (ticket 0900)"
    )


def test_window_offends_dead_parameter_beside_historical_wait():
    window = (
        "Launch the reviewers as parallel Agent calls with "
        "run_in_background: true. This skill previously polled a manifest of "
        "artifacts before the 2026-05 redesign."
    )
    assert _window_offends(window), (
        "a live citation of the dead parameter must offend even beside a "
        "historical mention of a real wait (ticket 0263 B2b)"
    )


def test_window_offends_when_wait_only_negated():
    window = "Spawn parallel agents. This skill does not poll for artifacts."
    assert _window_offends(window), (
        "wait evidence in a negation clause does not prove the fork waits "
        "(ticket 0263 B2b)"
    )


def test_window_accepts_local_wait_contract():
    window = (
        "Spawn the agents as parallel background Agent calls, each writing its "
        "report to the panel directory, then poll those artifacts against the "
        "manifest under a bounded deadline."
    )
    assert not _window_offends(window)

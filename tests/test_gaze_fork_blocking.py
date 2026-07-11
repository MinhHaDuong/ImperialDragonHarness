"""The gaze fork must block on its reviewers, never orphan them (ticket 0250).

The lesson 0250 paid for, twice: `/gaze` runs as a `context: fork`. A fork's
turn ends the instant it stops calling tools. If it launches its reviewer
battery as **background** agents (`run_in_background: true`) and then "waits
for all to return", it does not wait — background completions re-invoke the
MAIN loop, not the fork, so the fork ends immediately, returning a fan-out
narration ("reviewers are running in parallel…") as its final message.
Phases 5 (simplify) and 6 (gate) never run in the fork and no verdict is
produced (aedist 0538 `/gaze 977`, aedist 0540 `/gaze 978` — twice).

The fix (approach a in the ticket): the reviewer and gate fan-out launches
must be **foreground / synchronous** so the fork blocks until they return.
This test makes that enforceable instead of conventional:

1. No launch in the gaze body describes its reviewer/gate agents as
   "background" or uses `run_in_background: true` — a fork cannot wait on
   those.
2. The body states the fan-out is foreground / blocking / synchronous
   (`run_in_background: false`).
3. The failure mode and caller-side recovery are documented in the skill.
"""

import re
from pathlib import Path

import pytest
from test_verify_fork_contracts import fork_skill_files

REPO = Path(__file__).resolve().parents[1]
GAZE = REPO / "skills" / "gaze" / "SKILL.md"

# Every `context: fork` skill must carry the foreground contract *locally*, at
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


# A background-launch signal: "background agent(s)" (any whitespace, incl. a
# line wrap) or an explicit `run_in_background: true`. Naming the anti-pattern
# to forbid it is fine; issuing it as a launch directive is the defect. We
# separate the two by negation context, not by the token alone — the skill
# documents the trap verbatim so future readers recognise it.
BACKGROUND_SIGNAL = re.compile(
    r"background\s+agents?\b|run_in_background\s*[:=]\s*true", re.IGNORECASE
)

# Words that turn a background mention into a prohibition or an explanation of
# the failure, not a launch directive.
NEGATION = re.compile(
    r"\b(not|never|don't|do not|instead|rather than|orphan|trap|does not|"
    r"fork cannot|cannot wait|re-invoke|would|if.*returns)\b",
    re.IGNORECASE,
)

# Foreground/blocking phrasing that proves the fork waits synchronously.
FOREGROUND = re.compile(
    r"foreground|synchronous(?:ly)?|blocking\s+(?:launch|call|agent|on)"
    r"|run_in_background\s*[:=]\s*false",
    re.IGNORECASE,
)


def _sentences(text: str) -> list[str]:
    # Coarse sentence split on ., ; and newlines — enough to scope a background
    # mention to its clause for the negation check. Deliberately NOT on ":": the
    # colon lives inside the very tokens we test (`run_in_background: true/false`),
    # so splitting there would tear `run_in_background:` from its value and hide
    # the directive from BACKGROUND_SIGNAL/FOREGROUND (ticket 0263 B2). Dropping
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
# fan-out paragraph reads "as parallel foreground Agent calls" / "parallel Agent
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
    """Whether a launch-paragraph window violates the local foreground contract.

    Two ways to offend (ticket 0263 B2):
    - a live (non-negated) background directive sits in the window — a fork
      cannot wait on background agents, so this orphans the children regardless
      of any foreground token elsewhere; and
    - no *non-negated* foreground/blocking evidence is present — a historical or
      forbidden "foreground" mention ("previously ran foreground", "does not run
      foreground") does not prove the fork waits.
    """
    if _has_nonnegated(BACKGROUND_SIGNAL, window):
        return True
    return not _has_nonnegated(FOREGROUND, window)


def test_no_affirmative_background_launch():
    body = _body(GAZE.read_text())
    offenders = [
        s.strip()
        for s in _sentences(body)
        if BACKGROUND_SIGNAL.search(s) and not NEGATION.search(s)
    ]
    assert not offenders, (
        "gaze SKILL.md issues a background launch directive for its "
        "reviewer/gate fan-out — a fork cannot wait on background agents; it "
        "returns at fan-out start and orphans them (ticket 0250). Offending "
        f"clauses: {offenders}"
    )


def test_fanout_is_foreground_blocking():
    body = _body(GAZE.read_text())
    assert FOREGROUND.search(body), (
        "gaze SKILL.md must state its reviewer/gate fan-out is "
        "foreground/synchronous (run_in_background: false) so the fork blocks "
        "until every agent returns (ticket 0250, approach a)."
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
def test_launch_paragraph_carries_local_foreground_contract(name):
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
        "foreground/blocking contract (run_in_background: false) in that same "
        "paragraph or the next — a forked skill that ends its turn with its "
        "fan-out in background orphans the children one layer down (ticket "
        f"0263, /gaze 479). Offending paragraph(s): {offenders}"
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
    assert any("parallel foreground" in p.lower() for p in launch), (
        "gaze's primary review fan-out paragraph is not classified as a launch "
        "site, so the locality ratchet never inspects it — stripping its local "
        "foreground contract would go unnoticed (ticket 0263 B1)."
    )
    assert len(launch) >= 2


# --- B2: foreground evidence must survive negation, background must not slip ---
#
# The window check had no negation awareness: a live `run_in_background: true`
# directive, or a negated/historical "foreground" mention, still satisfied the
# contract because FOREGROUND matched the token regardless of context.


def test_window_offends_live_background_directive_despite_foreground_token():
    window = (
        "Spawn the panel as parallel Agent calls with "
        "run_in_background: true and wait. They run foreground-ish."
    )
    assert _window_offends(window), (
        "a live background launch directive must offend even with a stray "
        "foreground token nearby (ticket 0263 B2a)"
    )


def test_window_offends_negated_historical_foreground():
    window = (
        "Launch the reviewers as parallel background agents "
        "(run_in_background: true). This skill previously ran its panel "
        "foreground before the 2026-05 redesign."
    )
    assert _window_offends(window), (
        "a live background directive alongside a historical foreground mention "
        "must offend (ticket 0263 B2b)"
    )


def test_window_offends_when_foreground_only_negated():
    window = "Spawn parallel agents. This skill does not run foreground."
    assert _window_offends(window), (
        "foreground evidence in a negation clause does not prove the fork "
        "waits (ticket 0263 B2b)"
    )


def test_window_accepts_local_foreground_contract():
    window = (
        "Spawn the agents as parallel foreground Agent calls "
        "(run_in_background: false), blocking until every one returns."
    )
    assert not _window_offends(window)

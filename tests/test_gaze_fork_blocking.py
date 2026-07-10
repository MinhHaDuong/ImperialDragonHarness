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

REPO = Path(__file__).resolve().parents[1]
GAZE = REPO / "skills" / "gaze" / "SKILL.md"


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
    # Coarse sentence split on ., ;, : and newlines — enough to scope a
    # background mention to its clause for the negation check.
    return re.split(r"(?<=[.;:])\s+|\n+", text)


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

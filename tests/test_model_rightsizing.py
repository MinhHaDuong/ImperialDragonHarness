"""Fan-out skills pin a per-invocation model — the rightsizing ratchet (ticket 0235).

The lesson 0235 paid for: a skill's `model:` frontmatter does NOT propagate to
agents it spawns (an Agent-tool child resolves to the session model; a Workflow
`agent()` inherits the session model). So the only reliable rightsizing lever is
the **per-invocation `model`** on each launch — frontmatter is decorative for
fan-out. This test makes that discipline enforceable instead of conventional:

1. Every SKILL.md that launches a fan-out names a per-invocation model in its
   BODY (not just frontmatter).
2. No full `claude-<id>` model id leaks into a SKILL.md body — per-invocation
   pins must use the short Agent enum token (`sonnet|opus|haiku|fable`); the full
   id is valid only in frontmatter (a different code path).

A third lens once scanned Workflow `.js` skills, with a small JS lexer, so that
every `agent()` call pinned a model. Ticket 0881 removed `maw-audit` and
`test-audit-llm`, the only two such skills, leaving that lens with no subject —
a scan over an empty corpus is green whatever the truth, so it was removed with
them rather than left to pass vacuously. Restore it from git history alongside
the first workflow skill that returns.

See memory feedback_subagent_model_effort_levers.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"

# The Agent-launch `model` enum (and the Workflow agent() model tokens).
# Fable 5 removed 2026-06-13 (blocked by government order); restored 2026-07-15:
# block lifted — a live probe (Agent pinned model:fable) resolved to
# claude-fable-5, and the author confirmed the restoration. Historical Fable
# runs stay cost-accounted in scripts/trace-*.py (analytics over past data at
# Fable's 2x rate). Rightsizing doctrine still governs where fable may be
# pinned: top-tier singletons, never bulk fan-out. The MODEL_PIN regex below
# already recognized fable — it now validates instead of rejecting.
VALID_MODELS = {"sonnet", "opus", "haiku", "fable"}

# A per-invocation model pin in prose or code: `model: sonnet`, `model="opus"`,
# backtick-wrapped, quoted, etc. Captures the tier token.
MODEL_PIN = re.compile(
    r"""model\s*[:=]\s*['"`]?(sonnet|opus|haiku|fable)\b""", re.IGNORECASE
)

# A full model id used where a short token belongs (the claude-fable-5 bug).
FULL_ID_PIN = re.compile(r"""model\s*[:=]\s*['"`]?claude-[\w.-]+""", re.IGNORECASE)

# Imperative fan-out launch phrasing — "launch/spawn/spin ... agent(s)",
# "background agents", "agents ... in parallel". Deliberately NOT triggered by
# bare "fan-out" or "parallel agents", which appear descriptively (e.g. scry
# reporting parallel-fanout cost as a risk signal it scans for).
FANOUT_SIGNAL = re.compile(
    r"(launch|spawn|spin)[^.\n]{0,40}\bagents?\b"
    r"|background agents?"
    r"|agents?[^.\n]{0,25}\bin parallel\b",
    re.IGNORECASE,
)

# Fan-out SKILL.md skills that intentionally do NOT carry a per-invocation model
# pin in their body — the documented escape hatch. Keep empty; add a name only
# with a one-line reason, never to silence a real gap.
SKILL_BODY_ALLOWLIST: dict[str, str] = {}


def _body(md_text: str) -> str:
    """Return the SKILL.md content after the YAML frontmatter block."""
    parts = md_text.split("---", 2)
    return parts[2] if len(parts) >= 3 else md_text


def _skill_md_files():
    return sorted(SKILLS.glob("*/SKILL.md"))



# --- sanity: the scanner actually finds something (no vacuous green) ---


def test_corpus_is_non_empty():
    assert _skill_md_files(), "no SKILL.md files found"


# --- 1. Fan-out SKILL.md: body names a per-invocation model ---

def test_fanout_skill_bodies_pin_model():
    offenders = []
    for md in _skill_md_files():
        name = md.parent.name
        if name in SKILL_BODY_ALLOWLIST:
            continue
        body = _body(md.read_text())
        if FANOUT_SIGNAL.search(body) and not MODEL_PIN.search(body):
            offenders.append(name)
    assert not offenders, (
        "fan-out skills whose body launches agents but pins no per-invocation "
        "model (frontmatter model: does NOT propagate to children — 0235); pin "
        "each launch or add to SKILL_BODY_ALLOWLIST with a reason:\n"
        + "\n".join(sorted(offenders))
    )


# --- 2. No full model id in a SKILL.md body (the claude-fable-5 bug) ---

def test_no_full_model_id_in_skill_bodies():
    offenders = []
    for md in _skill_md_files():
        for line in _body(md.read_text()).splitlines():
            if FULL_ID_PIN.search(line):
                offenders.append(f"{md.parent.name}: {line.strip()[:90]}")
    assert not offenders, (
        "per-invocation model pins in a SKILL.md body must use the short Agent "
        "enum token (sonnet|opus|haiku|fable), not a full claude-<id> "
        "(valid only in frontmatter, a different code path — 0235):\n"
        + "\n".join(offenders)
    )

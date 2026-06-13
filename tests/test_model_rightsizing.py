"""Fan-out skills pin a per-invocation model — the rightsizing ratchet (ticket 0235).

The lesson 0235 paid for: a skill's `model:` frontmatter does NOT propagate to
agents it spawns (an Agent-tool child resolves to the session model; a Workflow
`agent()` inherits the session model). So the only reliable rightsizing lever is
the **per-invocation `model`** on each launch — frontmatter is decorative for
fan-out. This test makes that discipline enforceable instead of conventional:

1. Every Workflow `agent()` call in a skill `.js` pins a valid `model`.
2. Every SKILL.md that launches a fan-out names a per-invocation model in its
   BODY (not just frontmatter).
3. No full `claude-<id>` model id leaks into a SKILL.md body — per-invocation
   pins must use the short Agent enum token (`sonnet|opus|haiku`); the full
   id is valid only in frontmatter (a different code path).

See memory feedback_subagent_model_effort_levers.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILLS = REPO / "skills"

# The Agent-launch `model` enum (and the Workflow agent() model tokens).
# Fable 5 removed 2026-06-13: blocked by government order, no longer selectable.
# Historical Fable runs stay cost-accounted in scripts/trace-*.py (analytics over
# past data at Fable's 2x rate), but no skill may pin it as a tier going forward.
VALID_MODELS = {"sonnet", "opus", "haiku"}

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


def _has_companion_js(skill_dir: Path) -> bool:
    return any(skill_dir.glob("*.js"))


# --- a small JS lexer good enough for these workflow scripts ---
#
# It must skip over strings, template literals (including `${ … }` interpolation,
# which can itself contain strings, nested templates, and braces), and // and
# /* */ comments — otherwise an `agent(` inside a comment or a `${…}` is misread,
# and a backtick template desyncs the scanner so it silently misses later calls
# (the false-GREEN bug this test exists to avoid). `/` is treated as an ordinary
# character: the regex literals in these files contain no lone quotes, backticks,
# or unbalanced parens/braces, so they cannot desync the lexer.


def _skip_string(src, i):
    """src[i] is ' or "; return index just past the closing quote."""
    q, n, i = src[i], len(src), i + 1
    while i < n:
        if src[i] == "\\":
            i += 2
            continue
        if src[i] == q:
            return i + 1
        i += 1
    return n


def _skip_template(src, i):
    """src[i] is a backtick; return index just past the closing backtick,
    descending into every `${ … }` interpolation."""
    n, i = len(src), i + 1
    while i < n:
        c = src[i]
        if c == "\\":
            i += 2
            continue
        if c == "`":
            return i + 1
        if c == "$" and i + 1 < n and src[i + 1] == "{":
            i = _skip_group(src, i + 1, "{", "}")
            continue
        i += 1
    return n


def _skip_group(src, i, open_ch, close_ch):
    """src[i] is open_ch; return index just past the matching close_ch, with
    strings / templates / comments inside treated as opaque."""
    n, depth = len(src), 0
    while i < n:
        c = src[i]
        if c in "'\"":
            i = _skip_string(src, i)
            continue
        if c == "`":
            i = _skip_template(src, i)
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i < n and not (src[i] == "*" and i + 1 < n and src[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return n


def _agent_calls(src: str):
    """Yield the full source text of each `agent(...)` call, recognised only in
    code position (not inside strings, templates, or comments)."""
    n, i = len(src), 0
    while i < n:
        c = src[i]
        if c in "'\"":
            i = _skip_string(src, i)
            continue
        if c == "`":
            i = _skip_template(src, i)
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            i += 2
            while i < n and not (src[i] == "*" and i + 1 < n and src[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if src.startswith("agent(", i) and (i == 0 or not (src[i - 1].isalnum() or src[i - 1] == "_")):
            end = _skip_group(src, i + 5, "(", ")")
            yield src[i:end]
            i = end
            continue
        i += 1


def _skill_md_files():
    return sorted(SKILLS.glob("*/SKILL.md"))


def _skill_js_files():
    return sorted(p for p in SKILLS.glob("*/*.js") if "/fixtures/" not in str(p))


# --- sanity: the scanners actually find something (no vacuous green) ---

def _expected_call_count(src: str) -> int:
    """Independent line-based count: every `agent(` token, minus those that sit
    after a `//` on their own line (in-comment references). A cross-check on the
    lexer — if the lexer desyncs on a template/string and silently drops later
    calls, the two counts diverge."""
    count = 0
    for line in src.splitlines():
        for m in re.finditer(r"\bagent\(", line):
            if "//" not in line[:m.start()]:
                count += 1
    return count


def test_corpus_is_non_empty():
    assert _skill_md_files(), "no SKILL.md files found"
    assert _skill_js_files(), "no workflow .js files found"


def test_scanner_finds_every_call():
    """The lexer must not silently miss calls (a desync would give false GREEN)."""
    mismatches = []
    for js in _skill_js_files():
        src = js.read_text()
        found = len(list(_agent_calls(src)))
        expected = _expected_call_count(src)
        if found != expected:
            mismatches.append(f"{js.relative_to(REPO)}: lexer found {found}, expected {expected}")
    assert not mismatches, (
        "agent() lexer count disagrees with the independent line-based count — "
        "the lexer likely desynced on a template/string and is dropping calls:\n"
        + "\n".join(mismatches)
    )


# --- 1. Workflow .js: every agent() pins a valid model ---

def test_workflow_js_agents_pin_valid_model():
    offenders = []
    for js in _skill_js_files():
        for call in _agent_calls(js.read_text()):
            m = MODEL_PIN.search(call)
            snippet = " ".join(call.split())[:90]
            if not m:
                offenders.append(f"{js.relative_to(REPO)}: agent() without model: …{snippet}…")
            elif m.group(1).lower() not in VALID_MODELS:
                offenders.append(f"{js.relative_to(REPO)}: agent() invalid model {m.group(1)!r}: …{snippet}…")
            if FULL_ID_PIN.search(call):
                offenders.append(f"{js.relative_to(REPO)}: agent() uses full claude-<id> (use short token): …{snippet}…")
    assert not offenders, (
        "Workflow agent() calls must pin a valid short-token model "
        "(sonnet|opus|haiku) — frontmatter does not reach them (0235):\n"
        + "\n".join(offenders)
    )


# --- 2. Fan-out SKILL.md: body names a per-invocation model ---

def test_fanout_skill_bodies_pin_model():
    offenders = []
    for md in _skill_md_files():
        name = md.parent.name
        if _has_companion_js(md.parent):
            continue  # model pins live in the .js — covered by test 1
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


# --- 3. No full model id in a SKILL.md body (the claude-fable-5 bug) ---

def test_no_full_model_id_in_skill_bodies():
    offenders = []
    for md in _skill_md_files():
        for line in _body(md.read_text()).splitlines():
            if FULL_ID_PIN.search(line):
                offenders.append(f"{md.parent.name}: {line.strip()[:90]}")
    assert not offenders, (
        "per-invocation model pins in a SKILL.md body must use the short Agent "
        "enum token (sonnet|opus|haiku), not a full claude-<id> "
        "(valid only in frontmatter, a different code path — 0235):\n"
        + "\n".join(offenders)
    )

"""external-peer-review bundles a portable script and documents its contract.

The skill solicits real external model reviews of a PDF and synthesizes them.
These ratchets pin the documented contract in the skill text and the portability
invariants in the bundled script (no project-specific hardcoding).
"""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO / "skills" / "external-peer-review"
SKILL = SKILL_DIR / "SKILL.md"
SCRIPT = SKILL_DIR / "peer_review.py"


def skill_text() -> str:
    return SKILL.read_text()


def script_text() -> str:
    return SCRIPT.read_text()


def test_bundled_script_exists():
    assert SCRIPT.exists(), "external-peer-review must bundle peer_review.py"


def test_documents_balance_gate_and_text_fallback():
    text = skill_text().lower()
    assert "$0.50" in skill_text(), "must document the OpenRouter $0.50 files gate"
    assert "--text" in skill_text(), "must document the text-mode fallback flag"
    assert "402" in skill_text(), "must document the HTTP 402 automatic fallback"


def test_documents_smoke_test_one_before_blasting():
    text = skill_text().lower()
    assert "smoke" in text or "test one" in text, (
        "must document smoke-testing one combo before launching the rest "
        "(project rule: test one before blasting)"
    )


def test_documents_complementary_to_simulated_panel():
    assert "review-pr-prose" in skill_text(), (
        "must state it is complementary to the simulated /review-pr-prose panel"
    )


def test_first_sentence_names_real_external_models():
    """Discoverability: plain searchable keywords in the opening sentence."""
    first = skill_text().split("description:", 1)[1].split("\n", 1)[0].lower()
    for kw in ("peer review", "openai", "mistral"):
        assert kw in first, f"first sentence should mention {kw!r}"


def test_script_is_portable_no_project_hardcoding():
    src = script_text()
    # The reference implementation baked in the AEDIST topic; the portable
    # version must not. Topic is supplied via --topic, not hardcoded.
    assert "thermal" not in src.lower(), "script must not hardcode a paper topic"
    assert "--models" in src and "--personas" in src, (
        "models and personas must be CLI-configurable"
    )
    assert "OPENROUTER_API_KEY" in src, "must read the OpenRouter key from env/.env"

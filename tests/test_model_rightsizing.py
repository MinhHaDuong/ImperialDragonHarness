"""Portable skills declare compute intentions; runtime configuration names models."""

import re
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

SKILLS = Path(__file__).resolve().parents[1] / 'skills'
MODEL_LEVEL = re.compile(r'model-level\s*:\s*(auto|cheap|standard|strong|frontier)\b')
CONCRETE_MODEL = re.compile(
    r'\b(?:sonnet|opus|haiku|fable)\b|\b(?:claude-(?:opus|sonnet|haiku|fable)|(?:gpt|gemini|mistral-large|deepseek)-[a-z0-9])[\w.-]*',
    re.IGNORECASE,
)


def skill_files():
    files = sorted(SKILLS.glob('*/SKILL.md'))
    assert files, 'no skills found'
    return files


def test_portable_skill_instructions_do_not_name_models():
    files = sorted(SKILLS.rglob('*.md'))
    assert files
    for path in files:
        if path.relative_to(SKILLS).parts[0] == 'route':
            continue  # the route skill holds the grid and per-runtime recommendations, which name models
        text = path.read_text()
        assert not CONCRETE_MODEL.search(text), f'{path}: concrete model in portable instructions'
        if path.name == 'SKILL.md':
            fm = text.split('---', 2)[1]
            assert not re.search(r'^model:', fm, re.MULTILINE), f'{path}: use model-level'


def test_model_identity_scanner_controls():
    for name in ['sonnet', 'claude-opus-4', 'openai/gpt-5.5', 'gemini-2.5-pro', 'deepseek-chat', 'gpt-oss-120b', 'gemini-pro']:
        assert CONCRETE_MODEL.search(name)
    for role in ['cheaper worker', 'smartest advisor', 'model-level: frontier', 'Scopus']:
        assert not CONCRETE_MODEL.search(role)

"""Portable skills declare compute intentions; runtime configuration names models."""

import re
from pathlib import Path

from scripts.model_policy import EFFORTS, MODEL_LEVELS

SKILLS = Path(__file__).resolve().parents[1] / 'skills'
FANOUT_SIGNAL = re.compile(
    r'(launch|spawn|spin)[^.\n]{0,40}\bagents?\b|background agents?'
    r'|agents?[^.\n]{0,25}\bin parallel\b', re.IGNORECASE,
)
MODEL_LEVEL = re.compile(r'model-level\s*:\s*(auto|cheap|standard|strong|frontier)\b')
CONCRETE_MODEL = re.compile(
    r'\b(?:sonnet|opus|haiku|fable)\b|\b(?:claude-(?:opus|sonnet|haiku|fable)|(?:gpt|gemini|mistral-large|deepseek)-[0-9])[\w.-]*',
    re.IGNORECASE,
)


def skill_files():
    files = sorted(SKILLS.glob('*/SKILL.md'))
    assert files, 'no skills found'
    return files


def test_fanout_skill_bodies_declare_model_level():
    for path in skill_files():
        body = path.read_text().split('---', 2)[-1]
        if FANOUT_SIGNAL.search(body):
            assert MODEL_LEVEL.search(body), f'{path}: fan-out lacks capability intent'


def test_portable_skill_instructions_do_not_name_models():
    files = sorted(SKILLS.rglob('*.md'))
    assert files
    for path in files:
        text = path.read_text()
        assert not CONCRETE_MODEL.search(text), f'{path}: concrete model in portable instructions'
        if path.name == 'SKILL.md':
            fm = text.split('---', 2)[1]
            assert not re.search(r'^model:', fm, re.MULTILINE), f'{path}: use model-level'


def test_skill_compute_frontmatter_is_semantic():
    forked = []
    for path in skill_files():
        fm = path.read_text().split('---', 2)[1]
        for field, values in [('model-level', MODEL_LEVELS), ('effort', EFFORTS)]:
            match = re.search(rf'^{field}:\s*(\S+)\s*$', fm, re.MULTILINE)
            if match:
                assert match.group(1) in values, f'{path}: invalid {field}'
        if re.search(r'^context:\s*fork\s*$', fm, re.MULTILINE):
            forked.append(path)
            assert MODEL_LEVEL.search(fm), f'{path}: fork lacks capability intent'
    assert forked, 'no forked skills found'


def test_model_identity_scanner_controls():
    for name in ['sonnet', 'claude-opus-4', 'openai/gpt-5.5', 'gemini-2.5-pro']:
        assert CONCRETE_MODEL.search(name)
    for role in ['cheaper worker', 'smartest advisor', 'model-level: frontier', 'Scopus']:
        assert not CONCRETE_MODEL.search(role)

"""A skill that launches workers must say the model is chosen per launch from the route skill."""

import re
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / 'skills'
FANOUT_SIGNAL = re.compile(
    r'(launch|spawn|spin)[^.\n]{0,40}\bagents?\b|background agents?'
    r'|agents?[^.\n]{0,25}\bin parallel\b', re.IGNORECASE,
)
CHOICE = re.compile(r'model of each launched worker per launch,\s+from the `route` skill', re.IGNORECASE)


def body(path):
    return path.read_text().split('---', 2)[-1]


def lacks_choice(text):
    return bool(FANOUT_SIGNAL.search(text)) and not CHOICE.search(text)


def test_fanout_skills_state_the_model_choice():
    paths = sorted(SKILLS.glob('*/SKILL.md'))
    assert paths
    launching = [p for p in paths if FANOUT_SIGNAL.search(body(p))]
    assert launching, 'no launching skills found'
    for path in launching:
        assert not lacks_choice(body(path)), f'{path}: launches workers without a per-launch model choice'


def test_floor_controls():
    assert lacks_choice('Launch three background agents in parallel.')
    assert not lacks_choice('Launch three agents. Choose the model of each launched worker per launch,\nfrom the `route` skill grid.')
    assert not lacks_choice('No fan-out here.')

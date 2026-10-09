"""A skill that launches workers must say the model is chosen per launch from the route skill."""

import re
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / 'skills'
FANOUT_SIGNAL = re.compile(
    r'(launch|spawn|spin)[^.\n]{0,40}\b(sub-?)?agents?\b|background (sub-?)?agents?'
    r'|\bclaude -p\b|\bcodex exec\b'
    r'|(sub-?)?agents?[^.\n]{0,25}\bin parallel\b', re.IGNORECASE,
)
CHOICE = re.compile(
    r'model of each launched worker per launch,\s+from the `route` skill grid'
    r'\s+\(`skills/route/SKILL\.md`\);[^.]*?`skills/route/references/decorrelation\.md`\s+\("The launch line"\)',
    re.IGNORECASE,
)


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
        assert len(CHOICE.findall(body(path))) == 1, f'{path}: the launch-choice sentence must appear exactly once'


def test_floor_controls():
    assert lacks_choice('Launch three background agents in parallel.')
    stated = ('Launch three agents. Choose the model of each launched worker per launch, from the `route` skill grid\n'
              '(`skills/route/SKILL.md`); seats that must be independent follow\n'
              '`skills/route/references/decorrelation.md` ("The launch line").')
    assert not lacks_choice(stated)
    assert len(CHOICE.findall(stated + '\n' + stated)) == 2
    assert lacks_choice('Launch three agents. Choose the model per launch, from the `route` skill grid.')
    assert lacks_choice('Spin **one** subagent for the check.')
    assert lacks_choice('Run `claude -p "do it"` per ticket.')
    assert lacks_choice('Run `codex exec "do it"` per ticket.')
    assert not lacks_choice('No fan-out here.')

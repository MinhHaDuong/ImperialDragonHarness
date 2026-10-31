"""Test-session hooks shared by every test file."""
import re
from pathlib import Path


# --- split-skill contract view ------------------------------------------------
# skills/gaze/SKILL.md (ticket 1153) and skills/raid/SKILL.md (ticket 1131) are
# a core plus references/*.md. The tests pin the *contract*, not its file
# layout, so reading either SKILL.md through Path.read_text returns the
# contract with every `<!-- inline: references/x.md -->` marker replaced by
# that reference's body (its H1 and intro line dropped). Only these paths are
# affected; layout tests read the files directly through other means
# (test_skill_reference_pointers.py walks the directory).
_SKILLS = Path(__file__).resolve().parents[1] / "skills"
_SPLIT_SKILLS = {_SKILLS / name / "SKILL.md" for name in ("gaze", "raid")}
_INLINE = re.compile(r"<!-- inline: (references/[\w.-]+\.md) -->")
_read_text = Path.read_text


def _split_contract_read_text(self, *args, **kwargs):
    text = _read_text(self, *args, **kwargs)
    skill = self.resolve()
    if skill not in _SPLIT_SKILLS:
        return text

    def body(match: re.Match) -> str:
        ref = _read_text(skill.parent / match.group(1), encoding="utf-8")
        return ref.split("\n\n", 2)[2]

    return _INLINE.sub(body, text)


Path.read_text = _split_contract_read_text


# --- archive isolation (ticket 1383) --------------------------------------------
# Headless doors spool session files under IDH_ARCHIVE_ROOT (scripts/transcript_spool.py).
# No test may write the real store: every test gets its own root, and a test that wants a
# specific one overrides it with monkeypatch.setenv.
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _isolated_archive_root(tmp_path_factory, monkeypatch):
    monkeypatch.setenv("IDH_ARCHIVE_ROOT", str(tmp_path_factory.mktemp("archive")))


@pytest.fixture(autouse=True)
def _no_ambient_session_identity(monkeypatch):
    """Ticket 1396: `raid_land.py --session-model` exports IDH_SESSION_MODEL, and the
    after-merge runner it starts inherits it; a test that expects no session identity
    then passes or fails by who landed the last merge. Tests that need one set it."""
    monkeypatch.delenv("IDH_SESSION_MODEL", raising=False)
    monkeypatch.delenv("IDH_SESSION_RUNTIME", raising=False)

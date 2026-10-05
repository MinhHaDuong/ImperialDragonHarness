"""Execute RAID's documented tally against mixed ticket log formats."""

import re
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
@pytest.mark.parametrize("regression", ["baseline", "legacy_note_bump", "quoted_body_log"])
def test_wrap_up_tally_counts_log_entries_per_ticket(tmp_path, regression):
    tickets = tmp_path / "tickets"
    tickets.mkdir()
    closed = tickets / "closed"
    closed.mkdir()
    (closed / "0879-example.erg").write_text(
        "%erg 0.1\nTitle: archived\nClosed: 2026-10-05\n\n--- log ---\n"
        "2026-10-05T10:00Z reviewer note verify-reroll — round 1: fix\n"
        "\n--- body ---\nMerged tickets retain their bump history.\n"
    )
    (tickets / "1023-example.erg").write_text(
        "%erg 0.1\nTitle: example\n\n--- log ---\n"
        "2026-10-05T10:00Z Minh Ha Duong note verify-reroll — round 1: fix\n"
        "2026-10-05T10:01Z reviewer note verify-reroll — round 2: fix\n"
        "2026-10-05T10:02Z reviewer bump permission — historical\n"
        "2026-10-05T10:03Z reviewer note circuit-breaker — timeout\n"
        "2026-10-05T10:04Z reviewer note discussion quoting note verify-reroll\n"
        "2026-10-05T10:04Z reviewer note discussion quoting bump permission\n"
        "\n--- body ---\n"
        "2026-10-05T10:05Z quoted note verify-reroll — not a log entry\n"
    )
    (tickets / "1005-example.erg").write_text(
        "%erg 0.1\nTitle: example\n\n--- log ---\n"
        "2026-10-05T10:00Z reviewer note verify-reroll — round 1: fix\n"
        "2026-10-05T10:01Z reviewer bump verify-reroll — historical\n"
        + (
            "2026-10-05T10:02Z reviewer note bump verify-reroll — historical\n"
            if regression == "legacy_note_bump"
            else ""
        )
        + "\n--- body ---\nNo bumps here.\n"
        + (
            "--- log ---\n"
            "2026-10-05T10:03Z quoted note verify-reroll — body sample\n"
            if regression == "quoted_body_log"
            else ""
        )
    )
    skill = (ROOT / "skills/raid/SKILL.md").read_text()
    wrap_up = skill.split("## Wrap up", 1)[1].split("## Circuit breakers", 1)[0]
    command = re.search(r"```(?:bash)?\n(.*?)\n\s*```", wrap_up, re.S)
    assert command, "wrap-up must provide an executable tally recipe"
    result = subprocess.run(
        ["bash", "-e", "-c", command.group(1)],
        cwd=tmp_path,
        env=child_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert set(result.stdout.splitlines()) == {
        "Ticket 0879: 1 verify-reroll",
        f"Ticket 1005: {3 if regression == 'legacy_note_bump' else 2} verify-reroll",
        "Ticket 1023: 2 verify-reroll",
        "Ticket 1023: 1 permission",
        "Ticket 1023: 1 circuit-breaker",
    }

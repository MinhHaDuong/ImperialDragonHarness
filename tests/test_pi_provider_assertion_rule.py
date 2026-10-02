"""Pi adapter provider-assertion rule pins (ticket 0979).

Pi 0.87.1 reroutes a request to a different provider than the one
requested when ``--model`` is empty or absent — the explicit ``--provider``
is discarded silently, with a normal-looking answer on screen (characterized
on padme; essai 0977's non-empty-id observation under ilaas stays
unreconciled, docs/2026-09-28-essai-pi-backends-souverains.md).
The harness mitigation is a documented rule, not code: every Pi run
targeting a sovereign backend must verify ``"provider"`` in ``--mode json``
output equals the requested provider before trusting the answer, and model
ids declared in the live Pi config must stay resolvable.

These tests pin the three deliverables of ticket 0979 so the guard cannot
drift: the adapters/pi rule README, the characterization doc, and the
cross-references carried by the downstream adapter-pilot tickets 0923/0924.
No harness code invokes ``pi --print`` today (grep-verified in the raid
log), so the rule is documented at the adapter boundary, and these tests
fail the moment the docs stop saying what they must.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.adherence

REPO = Path(__file__).resolve().parents[1]


def test_pi_adapter_pins_provider_assertion_rule():
    readme = (REPO / "adapters" / "pi" / "README.md").read_text()
    assert '"provider"' in readme
    assert "--mode json" in readme
    assert "0979" in readme
    assert "2026-10-02-pi-reroute-openrouter-0979" in readme
    assert "must verify" in readme
    assert "turn_end.message.provider" in readme
    assert "## Rule: keep declared model ids resolvable" in readme
    # Scope: the Pi adapter exists (bash guard); only a pi --print driver is unwired.
    assert "idh-guard.ts" in readme
    # The 0977 trigger is recorded as unreconciled, not claimed reproduced.
    assert "unreconciled" in readme


def test_pi_characterization_doc_records_trigger_and_versions():
    doc = (REPO / "docs" / "2026-10-02-pi-reroute-openrouter-0979.md").read_text()
    assert "0.87.1" in doc
    assert "openrouter" in doc.lower()
    assert "uncleared" in doc.lower() or "egress" in doc.lower()
    assert "--provider requires --model" in doc
    assert '--model ""' in doc
    assert "#10236" in doc
    assert "non réconcilié" in doc


def test_pi_adapter_tickets_carry_cross_reference():
    for tid in ("0923-first-runtime-adapter-offline-pilot", "0924-remaining-runtime-adapters"):
        # A ticket may since have been closed and archived to tickets/closed/.
        candidates = [REPO / "tickets" / (tid + ".erg"), REPO / "tickets" / "closed" / (tid + ".erg")]
        path = next(p for p in candidates if p.exists())
        log = path.read_text().split("--- log ---")[1]
        assert "0979" in log

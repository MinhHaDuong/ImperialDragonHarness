"""The published example exercises actual Git and harness commands offline."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.integration
def test_example_round_trip_and_isolation(tmp_path):
    output = tmp_path / 'result.json'
    done = subprocess.run(
        [sys.executable, str(ROOT / 'scripts/notes_review_example.py'), '--output', str(output)],
        capture_output=True, text=True, timeout=90,
        env={'PATH': '/usr/bin:/bin', 'GIT_DIR': '/nonexistent', 'GIT_CONFIG_COUNT': '1',
             'GIT_CONFIG_KEY_0': 'url.https://invalid.example/.insteadOf', 'GIT_CONFIG_VALUE_0': '/tmp/'},
    )
    assert done.returncode == 0, done.stderr
    result = json.loads(output.read_text())
    assert result['synthetic_evidence'] is True
    assert result['checks']['harness_notes_unchanged'] is True
    assert result['checks']['sample_notes_changed'] is True
    assert result['checks']['concurrent_entries_retrieved'] is True
    assert result['checks']['rebase_match'] == 'patch-id'
    assert result['checks']['changed_revision_match'] == 'none'
    assert result['checks']['old_head_retrieved'] is True
    assert result['checks']['export_import_equal'] is True

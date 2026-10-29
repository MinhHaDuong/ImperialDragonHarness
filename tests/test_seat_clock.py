"""A review seat ends within its cap, and every manifest seat reports a wall time or a failure (ticket 1099)."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'seat_clock.py'


def run(*args, timeout=30, env=None):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, timeout=timeout,
                          env={**os.environ, **env} if env else None)


def consent(tmp_path, providers):
    """A consent file for plan-write to read; never the host's (padme has one)."""
    path = tmp_path / 'gaze-seats.json'
    path.unlink(missing_ok=True)
    if providers is not None:
        path.write_text(json.dumps({'cross_family_spend': providers}))
    return {'IDH_GAZE_SEATS_CONFIG': str(path)}


def test_timed_out_reader_is_killed_and_the_caller_continues(tmp_path):
    out = tmp_path / 'xfam.md'
    started = time.monotonic()
    # A stub caller: the capped reader hangs, the caller goes on and says so.
    caller = subprocess.run(
        ['bash', '-c', f'"{sys.executable}" "{SCRIPT}" run --cap 1 --out "{out}" -- sleep 60; '
                       'echo "exit=$?"; echo "caller continued"'],
        capture_output=True, text=True, timeout=30)
    assert time.monotonic() - started < 15
    assert 'xfam: no report (timed out after 1s)' in caller.stdout
    assert 'exit=1' in caller.stdout
    assert 'caller continued' in caller.stdout
    assert not out.exists()
    assert (tmp_path / 'xfam.md.status').read_text().strip() == 'xfam: no report (timed out after 1s)'


def test_completed_reader_lands_its_report_with_its_wall_time(tmp_path):
    out = tmp_path / 'xfam.md'
    result = run('run', '--cap', '20', '--out', str(out), '--', 'echo', 'verdict: clear')
    assert result.returncode == 0
    assert out.read_text() == 'verdict: clear\n'
    assert result.stdout.startswith('xfam: reported in ')
    assert result.stdout.strip().endswith('s')


def test_failed_start_and_failed_exit_are_named(tmp_path):
    missing = run('run', '--cap', '5', '--out', str(tmp_path / 'a.md'), '--', 'no-such-reader-cli-1099')
    assert missing.returncode == 1
    assert missing.stdout.strip() == 'a: no report (failed to start)'
    failed = run('run', '--cap', '5', '--out', str(tmp_path / 'b.md'), '--', 'bash', '-c', 'echo partial; exit 3')
    assert failed.returncode == 1
    assert failed.stdout.startswith('b: no report (failed, exit 3, ')
    assert not (tmp_path / 'b.md').exists()


def test_seat_that_writes_its_own_report_keeps_it(tmp_path):
    out = tmp_path / 'correctness.md'
    seat = (f'printf "verdict: clear\\n" > "{out}.part" && mv "{out}.part" "{out}" '
            '&& echo "chatter after the report"')
    result = run('run', '--cap', '20', '--out', str(out), '--', 'bash', '-c', seat)
    assert result.returncode == 0
    assert result.stdout.startswith('correctness: reported in ')
    assert out.read_text() == 'verdict: clear\n'


def test_missing_output_directory_is_a_no_report_line(tmp_path):
    result = run('run', '--cap', '5', '--out', str(tmp_path / 'absent' / 'x.md'), '--', 'echo', 'hi')
    assert result.returncode == 1
    assert result.stdout.startswith('x: no report (')
    assert 'Traceback' not in result.stderr


def test_report_from_a_past_round_is_no_report(tmp_path):
    manifest = tmp_path / 'manifest.txt'
    manifest.write_text('a\tm\tf\tr\nb\tm\tf\tr\n')
    launched = manifest.stat().st_mtime
    (tmp_path / 'a.md').write_text('verdict: clear\n')
    os.utime(tmp_path / 'a.md', (launched - 600, launched - 600))
    (tmp_path / 'b.md').write_text('verdict: clear\n')
    os.utime(tmp_path / 'b.md', (launched + 42, launched + 42))
    result = run('roster', str(tmp_path))
    assert result.returncode == 1
    assert result.stdout.splitlines() == ['a: no report', 'b: reported in 42s']


def test_empty_manifest_is_not_a_complete_panel(tmp_path):
    (tmp_path / 'manifest.txt').write_text('# no seats\n')
    result = run('roster', str(tmp_path))
    assert result.returncode == 1
    assert result.stdout.strip() == 'no seats in manifest'


def test_leftover_report_does_not_rescue_a_failed_run(tmp_path):
    out = tmp_path / 'a.md'
    out.write_text('verdict: clear (past round)\n')
    os.utime(out, (time.time() - 600, time.time() - 600))
    result = run('run', '--cap', '5', '--out', str(out), '--', 'bash', '-c', 'exit 3')
    assert result.returncode == 1
    assert result.stdout.startswith('a: no report (failed, exit 3, ')


def test_roster_names_every_manifest_seat(tmp_path):
    manifest = tmp_path / 'manifest.txt'
    manifest.write_text('correctness\tm\tf\tr\nscope\tm\tf\tr\nred-team\tm\tf\tr\n')
    launched = manifest.stat().st_mtime
    (tmp_path / 'correctness.md').write_text('verdict: clear\n')
    os.utime(tmp_path / 'correctness.md', (launched + 95, launched + 95))
    (tmp_path / 'red-team.md.status').write_text('red-team: no report (timed out after 600s)\n')
    (tmp_path / 'xfam.md.status').write_text('xfam: reported in 300s\n')
    (tmp_path / 'xfam.md').write_text('verdict: clear\n')
    stale = tmp_path / 'scope.md.status'  # a past run's line, older than this manifest
    stale.write_text('scope: reported in 10s\n')
    os.utime(stale, (launched - 60, launched - 60))
    result = run('roster', str(tmp_path))
    assert result.returncode == 1  # a planned seat has no report
    assert result.stdout.splitlines() == [
        'correctness: reported in 95s',
        'scope: no report',
        'red-team: no report (timed out after 600s)',
        'xfam: reported in 300s',
    ]


def test_plan_write_builds_a_manifest_the_plan_check_accepts(tmp_path):
    """Ticket 1267: the manifest comes from a helper, so it parses."""
    panel = tmp_path / 'panel'
    result = run('plan-write', str(panel), '--intent', 'verify X', '--method', 'one seat',
                 '--budget', '10m', '--spend', 'none', '--home-family', 'anthropic',
                 '--item', 'regression', 'script', 'none', 'fails on base', env=consent(tmp_path, None))
    assert result.returncode == 0, result.stderr
    (panel / 'regression.md').write_text('ran: ok\n')
    checked = run('plan-check', str(panel))
    assert checked.returncode == 0 and checked.stdout.splitlines()[0] == 'plan check: PASS'


@pytest.mark.parametrize('args', [
    ['--item', 'a', 'm', '', 'reason'],            # empty family
    ['--item', 'bad name', 'm', 'f', 'reason'],    # name outside [A-Za-z0-9_-]
    [],                                            # no item
    ['--item', 'a\tb', 'm', 'f', 'reason'],        # a tab inside a cell
])
def test_plan_write_refuses_what_the_checker_cannot_parse(tmp_path, args):
    panel = tmp_path / 'panel'
    result = run('plan-write', str(panel), '--intent', 'i', '--method', 'm', '--budget', '10m',
                 '--home-family', 'anthropic', *args, env=consent(tmp_path, None))
    assert result.returncode == 2
    assert 'plan refused' in result.stderr
    assert not (panel / 'manifest.txt').exists()


@pytest.mark.parametrize('args', [
    ['--intent', 'i', '--method', 'm', '--budget', '99m', '--item', 'a', 'm', 'f', 'r'],   # over the 13m ceiling
    ['--intent', '', '--method', 'm', '--budget', '10m', '--item', 'a', 'm', 'f', 'r'],    # empty intent
    ['--intent', 'i', '--method', 'm', '--budget', '10m', '--item', 'a', 'm', 'two words', 'r'],  # space in family
    [b'--intent', b'bad\xff', b'--method', b'm', b'--budget', b'10m', b'--item', b'a', b'm', b'f', b'r'],  # non-UTF-8
])
def test_plan_write_refuses_out_of_contract_values(tmp_path, args):
    panel = tmp_path / 'panel'
    cmd = [sys.executable, str(SCRIPT), 'plan-write', str(panel), '--home-family', 'anthropic',
           *[os.fsencode(a) for a in args]]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                            env={**os.environ, **consent(tmp_path, None)})
    assert result.returncode == 2, result.stderr
    assert 'Traceback' not in result.stderr
    assert not (panel / 'manifest.txt').exists()


# Ticket 1287: plan-write refuses the plans a fork that skipped references/plan.md writes.
def plan(tmp_path, *items, home='anthropic', providers=None, extra=()):
    panel = tmp_path / f'panel{len(list(tmp_path.glob("panel*")))}'  # a fresh panel per call
    flat = [cell for item in items for cell in ('--item', *item)]
    result = run('plan-write', str(panel), '--intent', 'i', '--method', 'm', '--budget', '10m',
                 '--home-family', home, *extra, *flat, env=consent(tmp_path, providers))
    return result, panel / 'manifest.txt'


SELF = ('self', 'self', 'anthropic', 'gaze reads the diff')
SAME = ('correctness', 'mid-model', 'anthropic', 'headless claude-code')
OPENAI = ('redteam', 'other-model', 'openai', 'headless codex')
CHECK = ('control', 'script', 'none', 'fails on base')


def test_plan_write_refuses_all_self_plan(tmp_path):
    result, manifest = plan(tmp_path, SELF)
    assert result.returncode == 2
    assert not manifest.exists()
    assert '--no-door' in result.stderr
    model_self = ('mine', 'self', 'anthropic', 'gaze itself')  # self by model, not by name
    result, manifest = plan(tmp_path, SELF, model_self)
    assert result.returncode == 2 and not manifest.exists()


def test_plan_write_records_no_door(tmp_path):
    result, manifest = plan(tmp_path, SELF, extra=('--no-door', 'headless claude-code failed to start'))
    assert result.returncode == 0, result.stderr
    assert '# no-door: headless claude-code failed to start' in manifest.read_text().splitlines()


def test_plan_write_under_consent_requires_consented_family(tmp_path):
    # No --spend: consent is read from the host config, never from the plan's own line.
    result, manifest = plan(tmp_path, SELF, SAME, providers=['OpenAI'])
    assert result.returncode == 2
    assert not manifest.exists()
    assert 'OpenAI' in result.stderr and '--no-cross-family' in result.stderr
    result, manifest = plan(tmp_path, SELF, CHECK, providers=['OpenAI'])  # PR 1827: a check is not another family
    assert result.returncode == 2 and not manifest.exists()
    prefixed = ('control', 'openai/script', 'none', 'fails on base')  # gaze finding: a check never counts
    result, manifest = plan(tmp_path, SELF, prefixed, providers=['OpenAI'])
    assert result.returncode == 2 and not manifest.exists()
    result, manifest = plan(tmp_path, SELF, SAME, OPENAI, providers=['OpenAI'])  # case-insensitive
    assert result.returncode == 0, result.stderr
    result, manifest = plan(tmp_path, SELF, SAME, providers=None)  # no consent file: same family is fine
    assert result.returncode == 0, result.stderr


def test_plan_write_cross_family_is_relative_to_the_home_family(tmp_path):
    # On a Codex session an OpenAI seat is same-family.
    result, _ = plan(tmp_path, SELF, OPENAI, home='OpenAI', providers=['OpenAI'])
    assert result.returncode == 0, result.stderr  # nothing cross-family is consented
    result, manifest = plan(tmp_path, SELF, OPENAI, home='openai', providers=['OpenAI', 'Anthropic'])
    assert result.returncode == 2 and not manifest.exists()
    assert 'Anthropic' in result.stderr
    result, _ = plan(tmp_path, SELF, OPENAI, SAME, home='openai', providers=['OpenAI', 'Anthropic'])
    assert result.returncode == 0, result.stderr


def test_plan_write_no_cross_family_is_recorded_and_shown_by_the_plan_check(tmp_path):
    result, manifest = plan(tmp_path, SELF, SAME, providers=['OpenAI'], extra=('--no-cross-family', 'trivial'))
    assert result.returncode == 0, result.stderr
    assert '# no-cross-family: trivial' in manifest.read_text().splitlines()
    for name in ('self', 'correctness'):
        (manifest.parent / f'{name}.md').write_text('worker: model=m · family=anthropic\nverdict: clear\n')
    checked = run('plan-check', str(manifest.parent))
    assert checked.returncode == 0
    assert checked.stdout.splitlines()[0] == 'plan check: PASS with deviations — no cross-family seat: trivial'


def test_cross_family_seat_without_a_report_fails_the_plan_check(tmp_path):
    """No silent fallback: the only cross-family seat yielding nothing fails the check."""
    result, manifest = plan(tmp_path, SELF, OPENAI, providers=['OpenAI'])
    assert result.returncode == 0, result.stderr
    (manifest.parent / 'self.md').write_text('worker: model=m · family=anthropic\nverdict: clear\n')
    (manifest.parent / 'redteam.md.status').write_text('redteam: no report (refused: read=no)\n')
    checked = run('plan-check', str(manifest.parent))
    assert checked.returncode == 1
    assert checked.stdout.startswith('plan check: FAIL — redteam: no report')


def test_seats_derives_panel_only_from_a_non_self_report(tmp_path):
    result, manifest = plan(tmp_path, SELF, OPENAI, providers=['OpenAI'])
    assert result.returncode == 0, result.stderr
    (manifest.parent / 'self.md').write_text('worker: model=m · family=anthropic\nverdict: clear\n')
    assert run('seats', str(manifest.parent)).stdout.strip() == 'seats: self-only'
    (manifest.parent / 'redteam.md').write_text('worker: model=o · family=openai\nverdict: clear\n')
    assert run('seats', str(manifest.parent)).stdout.strip() == 'seats: panel'


def test_consent_follows_the_billing_provider_not_the_family_label(tmp_path):
    """GLM served through a consented Mistral provider is a cross-family seat (adherence finding)."""
    glm = ('xfam', 'mistral/glm-5', 'GLM', 'headless pi')
    result, _ = plan(tmp_path, SELF, glm, providers=['Mistral'])
    assert result.returncode == 0, result.stderr
    unbilled = ('xfam', 'glm-5', 'GLM', 'headless pi')  # no consented provider bills it
    result, manifest = plan(tmp_path, SELF, unbilled, providers=['Mistral'])
    assert result.returncode == 2 and not manifest.exists()
    home = ('xfam', 'anthropic/claude-x', 'anthropic', 'headless pi')  # consented, but the home family
    result, manifest = plan(tmp_path, SELF, home, providers=['Mistral', 'anthropic'])
    assert result.returncode == 2 and not manifest.exists()


# --- ticket 1303: identities, the seat: lines built from the plan and the headers -------------------

def _plan(tmp_path, rows, reports):
    panel = tmp_path / 'panel'
    panel.mkdir()
    (panel / 'manifest.txt').write_text('# budget: 10m\n' + ''.join(row + '\n' for row in rows))
    for name, text in reports.items():
        (panel / f'{name}.md').write_text(text)
    return panel


def test_identities_map_status_route_and_provider(tmp_path):
    headless = 'worker: model=gpt-6-luna · family=openai · runtime=codex · door=headless\nverdict: clear (src/x.py:42)\n'
    panel = _plan(tmp_path, [
        'consistency\tgpt-6-luna\topenai\theadless codex',
        'late\tgpt-6-luna\topenai\theadless codex',
        'skip\tclaude-x\tanthropic\tskipped: no door',
        'check\tscript\tnone\tfails on base',
        'self\tself\tanthropic\tgaze',
    ], {'consistency': headless, 'check': 'ran\n', 'self': 'worker: self · family=anthropic\nok\n'})
    result = run('identities', str(panel), '--session-runtime', 'claude-code', '--session-model', 'claude-x')
    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == [
        'seat: consistency · runtime=codex · family=openai · route=gpt-6-luna · model=openai/gpt-6-luna · status: ran',
        'seat: late · runtime=codex · family=openai · route=gpt-6-luna · model=openai/gpt-6-luna · status: failed',
        'seat: skip · runtime=claude-code · family=anthropic · route=subagent · model=anthropic/claude-x · status: skipped',
        'seat: self · runtime=claude-code · family=anthropic · route=self · model=anthropic/claude-x · status: ran',
    ]


def test_identities_take_a_headless_seat_family_from_the_launcher_header(tmp_path):
    """Ticket 1326: the plan's family column cannot relabel a headless seat; the launcher's header wins."""
    header = 'worker: model=sonnet · family=anthropic · runtime=claude-code · door=headless\nclear: src/x.py:42\n'
    panel = _plan(tmp_path, ['correctness\tsonnet\topenai\theadless claude-code'], {'correctness': header})
    result = run('identities', str(panel), '--session-runtime', 'claude-code')
    assert result.returncode == 0, result.stderr
    assert 'family=anthropic' in result.stdout and 'family=openai' not in result.stdout


def test_identities_mark_a_headless_seat_without_the_launcher_header_unconfirmed(tmp_path):
    """Gaze 1925 round 2: a report the launcher did not write keeps no confirmed route."""
    panel = _plan(tmp_path, ['redteam\tsonnet\topenai\theadless codex'],
                  {'redteam': 'worker: model=sonnet · family=openai\nclear: src/x.py:42\n'})
    lines = run('identities', str(panel), '--session-runtime', 'claude-code').stdout.splitlines()
    assert len(lines) == 1 and 'route=unconfirmed' in lines[0] and lines[0].endswith('status: ran')


def test_identities_derive_a_subagent_seat_family_from_the_session_runtime(tmp_path):
    """Ticket 1360: a seat planned openai but run through the claude-code subagent door is anthropic."""
    panel = _plan(tmp_path, ['xseat\tgpt-6.1-sol\topenai\tcross-family check'],
                  {'xseat': 'worker: model=gpt-6.1-sol · family=openai\nclear: src/x.py:42\n'})
    result = run('identities', str(panel), '--session-runtime', 'claude-code')
    assert result.returncode == 0, result.stderr
    line = result.stdout.splitlines()[0]
    assert 'runtime=claude-code · family=anthropic · route=subagent' in line and 'family=openai' not in line
    assert 'deviation: xseat: planned family openai, ran as anthropic' in result.stderr


def test_identities_a_codex_session_subagent_seat_is_openai_without_deviation(tmp_path):
    """Ticket 1360: the family follows the door, not a hardcoded value."""
    panel = _plan(tmp_path, ['xseat\tgpt-6.1-sol\topenai\tcross-family check'],
                  {'xseat': 'worker: model=gpt-6.1-sol · family=openai\nclear: src/x.py:42\n'})
    result = run('identities', str(panel), '--session-runtime', 'codex')
    assert 'runtime=codex · family=openai · route=subagent' in result.stdout and 'deviation' not in result.stderr


def test_identities_a_pi_subagent_seat_takes_the_model_prefix_else_unconfirmed(tmp_path):
    """Ticket 1360: pi's subagent door names no one family; a bare model is never guessed."""
    panel = _plan(tmp_path, ['a\tanthropic/claude-x\topenai\tcheck', 'b\tqwen3\topenai\tcheck'],
                  {'a': 'worker: x\nok src/x.py:1\n', 'b': 'worker: x\nok src/x.py:1\n'})
    lines = run('identities', str(panel), '--session-runtime', 'pi').stdout.splitlines()
    assert 'family=anthropic' in lines[0] and 'family=unconfirmed' in lines[1]


def test_identities_skip_free_text_and_fail_loudly_without_a_manifest(tmp_path):
    panel = _plan(tmp_path, ['One seat reads the diff.'], {})
    assert run('identities', str(panel)).stdout.strip() == ''
    assert run('identities', str(tmp_path / 'nowhere')).returncode == 2


HOLLOW = 'worker: model=gpt-6-luna · family=openai · runtime=codex · door=headless\nverdict: clear\n'
CITED = 'worker: model=gpt-6-luna · family=openai · runtime=codex · door=headless\nclear after reading src/x.py:42\n'
REASONED = ('worker: model=gpt-6-luna · family=openai · runtime=codex · door=headless\n'
            + 'I read the whole diff, followed the redirect path and the size cap, and found no defect. ' * 3)


def test_identities_mark_a_hollow_headless_report_failed(tmp_path):
    """Ticket 1361: a header plus a bare verdict reviewed nothing; a citation or a reasoned body did."""
    rows = [f'{n}\tgpt-6-luna\topenai\theadless codex' for n in ('hollow', 'cited', 'reasoned')]
    panel = _plan(tmp_path, rows, {'hollow': HOLLOW, 'cited': CITED, 'reasoned': REASONED})
    lines = run('identities', str(panel), '--session-runtime', 'claude-code').stdout.splitlines()
    assert [ln.rsplit('status: ', 1)[1] for ln in lines] == ['failed', 'ran', 'ran']


@pytest.mark.parametrize('runtime', ['codex', 'pi'])
def test_identities_mark_a_hollow_subagent_report_failed_on_any_session_runtime(tmp_path, runtime):
    panel = _plan(tmp_path, ['h\tgpt-6.1-sol\topenai\tcheck', 'c\tgpt-6.1-sol\topenai\tcheck'],
                  {'h': 'worker: x\nverdict: clear\n', 'c': 'worker: x\nclear: src/x.py:1\n'})
    lines = run('identities', str(panel), '--session-runtime', runtime).stdout.splitlines()
    assert [ln.rsplit('status: ', 1)[1] for ln in lines] == ['failed', 'ran']

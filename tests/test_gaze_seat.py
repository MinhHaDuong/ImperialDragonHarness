"""Gaze seats launch as detached headless CLIs, pinned and bounded (ticket 1256).

No test here launches a real model CLI: every `claude`, `codex` and `pi` is a
stub on a PATH that holds only the stub directory and the system bins, and the
consent config is a temporary file, never the host's.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'gaze_seat.py'
CLOCK = ROOT / 'scripts' / 'seat_clock.py'

STUB = r'''#!/bin/sh
# Records how it was called, then plays the seat.
log="$STUB_LOG/$(basename "$0").argv"
printf '%s\n' "$@" > "$log"
pwd > "$STUB_LOG/$(basename "$0").cwd"
cat > "$STUB_LOG/$(basename "$0").stdin"
case "$STUB_MODE" in
  fail) echo "partial"; exit 1 ;;
  liar) printf 'worker: model=gpt-6.1-sol · family=OpenAI\nfinding: none\nverdict: clear\n' ;;
  notrun) printf 'NOT-RUN: review tree unreachable\n' ;;
  outfile|outfile-fail)
    # codex writes its last message to the -o file
    prev=""; for a in "$@"; do [ "$prev" = "-o" ] && printf 'verdict: clear\n' > "$a"; prev="$a"; done
    if [ "$STUB_MODE" = outfile-fail ]; then exit 2; fi ;;
  *) printf 'finding: none\nverdict: clear\n' ;;
esac
'''


def load_module():
    spec = importlib.util.spec_from_file_location('gaze_seat', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def rig(tmp_path):
    bin_dir, log = tmp_path / 'bin', tmp_path / 'log'
    bin_dir.mkdir()
    log.mkdir()
    for name in ('claude', 'codex', 'pi'):
        stub = bin_dir / name
        stub.write_text(STUB)
        stub.chmod(0o755)
    tree = tmp_path / 'review-1'
    tree.mkdir()
    git = ['git', '-C', str(tree), '-c', 'user.name=t', '-c', 'user.email=t@t']
    subprocess.run([*git, 'init', '-q'], check=True)
    subprocess.run([*git, 'commit', '-q', '--allow-empty', '-m', 'base'], check=True)
    base = subprocess.run([*git, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    (tree / 'parser.py').write_text('def parse(key):\n    return key\n')
    subprocess.run([*git, 'add', 'parser.py'], check=True)
    subprocess.run([*git, 'commit', '-q', '-m', 'change'], check=True)
    head = subprocess.run([*git, 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    panel = tree / '.panel' / '1'
    panel.mkdir(parents=True)
    brief = tmp_path / 'brief.md'
    brief.write_text('intent: verify the parser because of exit criterion 2\n')
    env = {
        'PATH': f'{bin_dir}:/usr/bin:/bin',  # no real model CLI is reachable
        'HOME': str(tmp_path),
        'STUB_LOG': str(log),
        'IDH_GAZE_SEATS_CONFIG': str(tmp_path / 'gaze-seats.json'),
    }
    return {'tmp': tmp_path, 'log': log, 'tree': tree, 'panel': panel, 'brief': brief, 'env': env,
            'base': base, 'head': head}


def launch(rig, *extra, runtime='claude-code', model='haiku', family='Anthropic', name='correctness',
           mode='', home='Anthropic', anchor=None):
    env = dict(rig['env'], STUB_MODE=mode)
    return subprocess.run(
        [sys.executable, str(SCRIPT), 'launch', '--runtime', runtime, '--model', model,
         '--family', family, '--home-family', home, '--perspective', 'correctness',
         '--panel', str(rig['panel']), '--name', name, '--review-tree', str(rig['tree']),
         '--brief', str(rig['brief']), '--cap', '20', '--base', rig['base'],
         '--anchor', anchor or rig['head'], *extra],
        capture_output=True, text=True, timeout=60, env=env)


def first_line(path):
    return next(line for line in path.read_text().splitlines() if line.strip())


@pytest.mark.integration
def test_headless_seat_reports_with_the_pinned_worker_line(rig):
    result = launch(rig)
    assert result.returncode == 0, result.stderr
    report = rig['panel'] / 'correctness.md'
    assert first_line(report) == 'worker: model=haiku · family=Anthropic · runtime=claude-code · door=headless'
    assert 'verdict: clear' in report.read_text()
    assert result.stdout.startswith('correctness: reported in ')
    assert (rig['panel'] / 'correctness.md.status').read_text().startswith('correctness: reported in ')
    argv = (rig['log'] / 'claude.argv').read_text().splitlines()
    assert argv[argv.index('--model') + 1] == 'haiku'
    assert '-p' in argv and '--restricted' in argv
    assert argv[argv.index('--tools') + 1] == 'Read,Grep,Glob'  # no shell, no write tool
    prompt = (rig['log'] / 'claude.argv').read_text()  # the prompt is the last argument, multi-line
    assert prompt.rstrip().endswith('exit criterion 2')  # the brief closes the last argument
    assert 'verify the parser' in prompt and 'correctness' in prompt
    assert str(rig['tree']) in prompt  # the reach rail names the review tree
    assert Path((rig['log'] / 'claude.cwd').read_text().strip()) == rig['tree']
    diff = rig['panel'] / 'correctness.diff'
    assert str(diff) in prompt and 'def parse(key)' in diff.read_text()  # the diff, without a shell


@pytest.mark.integration
def test_seat_refusal_is_no_report(rig):
    result = launch(rig, mode='notrun')
    assert result.returncode == 1
    assert result.stdout.strip() == 'correctness: no report (seat refused: NOT-RUN: review tree unreachable)'
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_moved_review_tree_is_no_report(rig):
    result = launch(rig, anchor=rig['base'])
    assert result.returncode == 1
    assert 'is not the anchor' in result.stdout
    assert not (rig['log'] / 'claude.argv').exists()


@pytest.mark.integration
def test_door_output_file_does_not_rescue_a_failed_exit(rig):
    (rig['tmp'] / 'gaze-seats.json').write_text(json.dumps({'cross_family_spend': ['OpenAI']}))
    result = launch(rig, runtime='codex', model='gpt-6-luna', family='OpenAI', name='redteam',
                    mode='outfile-fail')
    assert result.returncode == 1
    assert result.stdout.startswith('redteam: no report (failed, exit 2, ')
    assert not (rig['panel'] / 'redteam.md').exists()


@pytest.mark.integration
def test_consent_follows_the_billing_provider_not_the_label(rig):
    result = launch(rig, runtime='pi', model='openai/gpt-x', family='Anthropic', name='scope')
    assert result.returncode == 1
    assert 'no consent for cross-family spend on openai' in result.stdout
    assert not (rig['log'] / 'pi.argv').exists()


@pytest.mark.integration
def test_failed_seat_is_no_report_never_a_self_read(rig):
    result = launch(rig, mode='fail')
    assert result.returncode == 1
    assert result.stdout.startswith('correctness: no report (failed, exit 1, ')
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_seat_self_report_of_model_is_replaced_by_the_pin(rig):
    result = launch(rig, mode='liar')
    assert result.returncode == 0, result.stderr
    text = (rig['panel'] / 'correctness.md').read_text()
    assert first_line(rig['panel'] / 'correctness.md').startswith('worker: model=haiku · family=Anthropic')
    assert 'gpt-6.1-sol' not in text


@pytest.mark.integration
def test_cross_family_seat_without_consent_never_launches(rig):
    result = launch(rig, runtime='codex', model='gpt-6-luna', family='OpenAI', name='redteam')
    assert result.returncode == 1
    assert result.stdout.startswith('redteam: no report (no consent for cross-family spend on OpenAI')
    assert not (rig['log'] / 'codex.argv').exists()
    assert not (rig['panel'] / 'redteam.md').exists()


@pytest.mark.integration
def test_cross_family_seat_with_consent_launches_on_its_door(rig):
    (rig['tmp'] / 'gaze-seats.json').write_text(json.dumps({'cross_family_spend': ['OpenAI']}))
    result = launch(rig, runtime='codex', model='gpt-6-luna', family='OpenAI', name='redteam', mode='outfile')
    assert result.returncode == 0, result.stderr
    assert first_line(rig['panel'] / 'redteam.md') == \
        'worker: model=gpt-6-luna · family=OpenAI · runtime=codex · door=headless'
    argv = (rig['log'] / 'codex.argv').read_text().splitlines()
    assert argv[0] == 'exec'
    assert argv[argv.index('-m') + 1] == 'gpt-6-luna'
    assert argv[argv.index('-s') + 1] == 'read-only'
    assert 'verify the parser' in (rig['log'] / 'codex.stdin').read_text()  # prompt arrives on stdin


@pytest.mark.integration
def test_door_refuses_a_family_it_cannot_serve(rig):
    result = launch(rig, runtime='codex', model='claude-haiku-5-5', family='Anthropic', name='scope')
    assert result.returncode == 1
    assert 'no report (' in result.stdout and 'codex' in result.stdout
    assert not (rig['log'] / 'codex.argv').exists()


@pytest.mark.integration
def test_plan_check_names_the_seat_that_could_not_launch(rig):
    (rig['panel'] / 'manifest.txt').write_text(
        '# intent: x\n# budget: 10m\n'
        'correctness\thaiku\tAnthropic\tlogic\n'
        'redteam\tgpt-6-luna\tOpenAI\tother family\n')
    assert launch(rig).returncode == 0
    assert launch(rig, runtime='codex', model='gpt-6-luna', family='OpenAI', name='redteam').returncode == 1
    check = subprocess.run([sys.executable, str(CLOCK), 'plan-check', str(rig['panel'])],
                           capture_output=True, text=True, timeout=30)
    assert check.returncode == 1
    head = check.stdout.splitlines()[0]
    assert head.startswith('plan check: FAIL') and 'redteam: no report (no consent' in head


@pytest.mark.integration
def test_consent_line_defaults_to_none(rig):
    result = subprocess.run([sys.executable, str(SCRIPT), 'consent'], capture_output=True, text=True,
                            timeout=30, env=rig['env'])
    assert result.returncode == 0
    assert result.stdout.startswith('# spend: cross-family none consented')
    (rig['tmp'] / 'gaze-seats.json').write_text(json.dumps({'cross_family_spend': ['OpenAI', 'Google']}))
    result = subprocess.run([sys.executable, str(SCRIPT), 'consent'], capture_output=True, text=True,
                            timeout=30, env=rig['env'])
    assert result.stdout.startswith('# spend: cross-family consented for OpenAI, Google')


def test_every_runtime_door_builds_a_pinned_read_only_command():
    gaze_seat = load_module()
    doors = gaze_seat.load_doors(ROOT / 'skills' / 'route' / 'routes.json')
    claude = gaze_seat.build_command(doors['claude-code'], 'sonnet', 'PROMPT', Path('/p/x.seat'),
                                     Path('/p/x.prompt'))
    assert claude.argv[0] == 'claude' and claude.argv[-1] == 'PROMPT' and claude.stdin is None
    assert claude.argv[claude.argv.index('--model') + 1] == 'sonnet'
    codex = gaze_seat.build_command(doors['codex'], 'gpt-6-luna', 'PROMPT', Path('/p/x.seat'),
                                    Path('/p/x.prompt'))
    assert codex.argv[:2] == ['codex', 'exec'] and codex.stdin == Path('/p/x.prompt')
    assert codex.argv[codex.argv.index('-o') + 1] == '/p/x.seat' and '<' not in codex.argv
    pi = gaze_seat.build_command(doors['pi'], 'anthropic/claude-haiku-5-5', 'PROMPT', Path('/p/x.seat'),
                                 Path('/p/x.prompt'))
    assert pi.argv[pi.argv.index('--model') + 1] == 'anthropic/claude-haiku-5-5'
    assert pi.argv[pi.argv.index('--tools') + 1] == 'read,grep,find,ls' and pi.argv[-1] == 'PROMPT'
    with pytest.raises(ValueError):  # the claude door offers named aliases only
        gaze_seat.build_command(doors['claude-code'], 'gpt-6-luna', 'P', Path('/o'), Path('/f'))

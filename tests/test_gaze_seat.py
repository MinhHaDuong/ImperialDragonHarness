"""Gaze seats launch as detached headless CLIs, pinned and bounded (ticket 1256).

No test here launches a real model CLI: every `claude`, `codex` and `pi` is a
stub on a PATH that holds only the stub directory and the system bins, and the
consent config is a temporary file, never the host's.
"""

import importlib.util
import json
import re
import shlex
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
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
if [ -n "$VIBE_HOME" ]; then
  printf '%s\n' "$VIBE_HOME" > "$STUB_LOG/vibe.home"
  cat "$VIBE_HOME/agents/seat.toml" > "$STUB_LOG/vibe.agent"
fi
[ "$(basename "$0")" = aider ] && [ -z "$STUB_MODE" ] && STUB_MODE=aider-clear
case "$STUB_MODE" in
  aider-clear)
    printf 'Aider v0.86.2\n--------------\n► **THINKING**\nhmm\n------------\n► **ANSWER**\nreach: read=yes shell=no tests=not-run\nfinding: none\nverdict: clear\nTokens: 1\n' ;;
  fail) echo "partial"; echo "stub: provider rejected the request" >&2; exit 1 ;;
  pi-unknown)
    # Pi on a provider that does not list the id: warns on stderr, answers anyway, exits 0
    echo 'Warning: Model "nope-model" not found for provider "anthropic". Using custom model id.' >&2
    printf 'reach: read=yes shell=no tests=not-run\nfinding: none\nverdict: clear\n' ;;
  codex-echo)
    # codex echoes tool output to stderr: a file that merely contains Pi's warning text
    echo 'exec: sed -n 1,5p gaze_seat.py' >&2
    echo "UNLISTED_MODEL = 'not found for provider'  # Pi's warning" >&2
    echo '+ assert "Model \"x\" not found for provider" in out' >&2
    printf 'reach: read=yes shell=no tests=not-run\nfinding: none\nverdict: clear\n' ;;
  liar) printf 'worker: model=gpt-6.1-sol · family=OpenAI\nreach: read=yes shell=no tests=not-run\nfinding: none\nverdict: clear\n' ;;
  codex-refuse)
    printf 'OpenAI Codex v0.165.0\n--------\nworkdir: /x/review-1\nmodel: gpt-6-luna\nprovider: openai\napproval: never\nsandbox: read-only\nreasoning effort: low\nsession id: 0190-abcd (parenthesised); odd\n--------\nuser\n' >&2
    printf 'NOT-RUN: review tree unreadable\n' ;;
  codex-leak)
    printf 'OpenAI Codex v0.165.0\n--------\nmodel: gpt-6.1-sol\nreasoning effort: high\nsession id: 0190abcd-1234-5678-9abc-def012345678\n--------\n' >&2
    printf '401 Unauthorized for jane.doe@example.org org-AbC123xyz Bearer abcDEF123456 key=sk-proj-FAKEFAKEFAKE1234 in /home/janedoe/work\n' >&2
    printf 'NOT-RUN: auth failed\n' ;;
  canary-fail) echo "diagnostic: rejected by vendor, ref FAKECANARY0123456" >&2; exit 2 ;;
  canary-notrun) printf 'NOT-RUN: could not read /home/jane/.codex/auth.json FAKECANARY0123456\n' ;;
  notrun) printf 'NOT-RUN: review tree unreachable\n' ;;
  notrun-tick) printf 'Reading the tree first.\n`NOT-RUN: HEAD moved`\n' ;;
  mentions) printf 'reach: read=yes shell=no tests=not-run\nfinding: the seat prints NOT-RUN: on refusal, as specified\nverdict: clear\n' ;;
  noread) printf 'reach: read=no shell=no tests=not-run\nfinding: none\nverdict: clear\n' ;;
  lateread) printf 'Looking.\\nreach: read=yes shell=no tests=not-run\\nverdict: clear\\n' ;;
  noreach) printf 'finding: none\nverdict: clear\n' ;;
  fenced) printf '```text\nworker: model=fixture-qwen · family=Qwen\nreach: read=yes shell=no tests=not-run\n```\n\nfinding: none\nverdict: clear\n' ;;
  fenced-bare) printf '\n```\nreach: read=yes shell=no tests=not-run\n```\nfinding: none\nverdict: clear\n' ;;
  fenced-noread) printf '```\nreach: read=no shell=no tests=not-run\n```\nverdict: clear\n' ;;
  fenced-ranno) printf '```text\nreach: read=yes shell=no tests=ran=no\n```\nverdict: clear\n' ;;
  fenced-open) printf '```text\nreach: read=yes shell=no tests=not-run\nfinding: none\nverdict: clear\n' ;;
  fenced-two) printf '```\nreach: read=yes shell=no tests=not-run\nreach: read=no shell=no tests=not-run\n```\nverdict: clear\n' ;;
  fenced-extra) printf '```\nreach: read=yes shell=no tests=not-run\nverdict: clear\n```\n' ;;
  fenced-quoted) printf 'Looking.\n```\nreach: read=yes shell=no tests=not-run\n```\nverdict: clear\n' ;;
  fenced-example) printf 'finding: example report below\n```text\nworker: x\nreach: read=yes shell=no tests=not-run\n```\nverdict: clear\n' ;;
  fenced-lang) printf '```python\nreach: read=yes shell=no tests=not-run\n```\nverdict: clear\n' ;;
  fenced-unknown) printf '```text\nreach: read=maybe shell=no tests=not-run\n```\nverdict: clear\n' ;;
  empty) : ;;
  aiderish)
    printf 'Aider v0.86.2\nModel: openai/x with ask edit format\n\n--------------\n> **THINKING**\n\nmaybe verdict: clear\n\n------------\n> **ANSWER**\n\nreach: read=yes shell=no tests=not-run\nfinding: none\nverdict: concerns\n\nTokens: 1 sent, 2 received.\n' | sed 's/^> /\xe2\x96\xba /' ;;
  aider-notrun)
    printf 'Aider v0.86.2\n--------------\n> **THINKING**\nverdict: clear\n------------\n> **ANSWER**\nNOT-RUN: tree unreachable\nTokens: 1\n' | sed 's/^> /\xe2\x96\xba /' ;;
  aider-truncated)
    printf 'Aider v0.86.2\n--------------\n> **THINKING**\nreach: read=yes shell=no tests=not-run\nfinding: none\nverdict: clear\n' | sed 's/^> /\xe2\x96\xba /' ;;
  aider-plain-quote)
    printf 'Aider v0.86.2\nRepo-map: disabled\n\nreach: read=yes shell=no tests=not-run\nfinding: none; the seat drops lines after @ **THINKING** markers\nverdict: clear\nTokens: 1\n' | sed 's/@/\xe2\x96\xba/' ;;
  aider-plain)
    printf 'Aider v0.86.2\nModel: openai/x with ask edit format\nGit repo: none\nRepo-map: disabled\nAdded d.diff to the chat (read-only).\n\nreach: read=yes shell=no tests=not-run\nfinding: none\nverdict: clear\n\nTokens: 1 sent, 2 received.\n' ;;
  aider-plain-notrun)
    printf 'Aider v0.86.2\nRepo-map: disabled\n\nNOT-RUN: tree unreachable\nTokens: 1\n' ;;
  outfile|outfile-fail)
    # codex writes its last message to the -o file
    prev=""; for a in "$@"; do [ "$prev" = "-o" ] && printf 'reach: read=yes shell=no tests=not-run\nverdict: clear\n' > "$a"; prev="$a"; done
    if [ "$STUB_MODE" = outfile-fail ]; then exit 2; fi ;;
  *) printf 'reach: read=yes shell=no tests=not-run\nfinding: none\nverdict: clear\n' ;;
esac
'''


def load_module():
    spec = importlib.util.spec_from_file_location('gaze_seat', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bake(text, log):
    """Give a stub its log directory and mode as shell variables of its own: a seat's environment carries neither."""
    head = f'#!/bin/sh\nSTUB_LOG={shlex.quote(str(log))}\nSTUB_MODE=$(cat "$STUB_LOG/mode" 2>/dev/null)\n'
    return text.replace('#!/bin/sh\n', head, 1)


@pytest.fixture
def rig(tmp_path):
    bin_dir, log = tmp_path / 'bin', tmp_path / 'log'
    bin_dir.mkdir()
    log.mkdir()
    for name in ('claude', 'codex', 'pi', 'aider', 'vibe'):
        stub = bin_dir / name
        stub.write_text(bake(STUB, log))
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
        'IDH_GAZE_SEATS_CONFIG': str(tmp_path / 'gaze-seats.json'),
        'IDH_ARCHIVE_ROOT': str(tmp_path / 'archive'),  # spooled session files never reach the real store
    }
    return {'tmp': tmp_path, 'log': log, 'tree': tree, 'panel': panel, 'brief': brief, 'env': env,
            'base': base, 'head': head}


def launch(rig, *extra, runtime='claude-code', model='haiku', family='Anthropic', name='correctness',
           mode='', home='Anthropic', anchor=None, caller_stdin=None):
    (rig['log'] / 'mode').write_text(mode)
    env = dict(rig['env'])
    return subprocess.run(
        [sys.executable, str(SCRIPT), 'launch', '--runtime', runtime, '--model', model,
         '--family', family, '--home-family', home, '--perspective', 'correctness',
         '--panel', str(rig['panel']), '--name', name, '--review-tree', str(rig['tree']),
         '--brief', str(rig['brief']), '--cap', '20', '--base', rig['base'],
         '--anchor', anchor or rig['head'], *extra],
        capture_output=True, text=True, timeout=60, env=env, input=caller_stdin)


def unpin(argv):
    """The pinned session id is fresh per seat (ticket 1384): compare argv without it."""
    return re.sub(r'(--session-id\n)[0-9a-f-]{36}', r'\1<uuid>', argv)


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
    assert result.stdout.startswith('correctness: no report (seat refused: NOT-RUN; door=') and 'unreachable' not in result.stdout
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_seat_that_cannot_read_is_no_report(rig):
    result = launch(rig, mode='noread')  # a clear written without reading the tree
    assert result.returncode == 1
    assert result.stdout.startswith('correctness: no report (seat reach: read=no;')
    assert (rig['panel'] / 'correctness.md.status').read_text().strip() == result.stdout.strip()
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_report_without_reach_line_is_no_report(rig):
    result = launch(rig, mode='noreach')
    assert result.returncode == 1
    assert 'seat reach: no valid reach line' in result.stdout
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_reach_line_must_be_the_second_line(rig):
    result = launch(rig, mode='lateread')
    assert result.returncode == 1 and 'seat reach: no valid reach line' in result.stdout


@pytest.mark.integration
def test_reach_line_survives_into_the_report(rig):
    result = launch(rig)
    assert result.returncode == 0, result.stdout
    text = (rig['panel'] / 'correctness.md').read_text()
    assert 'reach: read=yes shell=no tests=not-run' in text.splitlines()


@pytest.mark.integration
def test_refused_reach_fails_the_plan_check(rig):
    (rig['panel'] / 'manifest.txt').write_text('# budget: 10m\ncorrectness\thaiku\tAnthropic\treach\n')
    launch(rig, mode='noread')
    check = subprocess.run([sys.executable, str(SCRIPT.with_name('seat_clock.py')), 'plan-check', str(rig['panel'])],
                           capture_output=True, text=True)
    assert check.returncode == 1 and check.stdout.startswith('plan check: FAIL')
    assert 'correctness: no report' in check.stdout


@pytest.mark.integration
def test_marked_up_refusal_after_a_preface_is_no_report(rig):
    result = launch(rig, mode='notrun-tick')
    assert result.stdout.startswith('correctness: no report (seat refused: NOT-RUN;') and 'HEAD moved' not in result.stdout
    mentions = launch(rig, mode='mentions', name='scope')
    assert mentions.returncode == 0, mentions.stdout  # a report with a verdict is not a refusal


@pytest.mark.integration
def test_past_door_output_never_stands_in_for_this_run(rig):
    (rig['panel'] / 'correctness.seat.last').write_text('verdict: clear (a past run)\n')
    result = launch(rig, mode='empty')
    assert result.returncode == 1
    assert result.stdout.startswith('correctness: no report (empty output')
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_short_anchor_prefix_is_refused(rig):
    result = launch(rig, anchor=rig['head'][:1])
    assert result.returncode == 1 and 'is not the anchor' in result.stdout


@pytest.mark.integration
def test_family_label_cannot_contradict_the_model_provider(rig):
    result = launch(rig, runtime='pi', model='anthropic/claude-haiku-5-5', family='OpenAI', name='scope')
    assert result.returncode == 1
    assert 'is family anthropic, not OpenAI' in result.stdout
    assert not (rig['log'] / 'pi.argv').exists()


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
    # A host provider serving another maker's model bills; the label names the maker.
    result = launch(rig, runtime='pi', model='huggingface/qwen3', family='Anthropic', name='scope')
    assert result.returncode == 1
    assert 'no consent for cross-family spend on huggingface' in result.stdout
    assert not (rig['log'] / 'pi.argv').exists()


@pytest.mark.integration
def test_failed_seat_is_no_report_never_a_self_read(rig):
    result = launch(rig, mode='fail')
    assert result.returncode == 1
    assert result.stdout.startswith('correctness: no report (failed, exit 1, ')
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_failed_seat_status_carries_only_harness_owned_fields(rig):
    result = launch(rig, mode='fail')
    assert result.returncode == 1
    assert result.stdout.startswith('correctness: no report (failed, exit 1, ')
    assert 'door=' in result.stdout and 'model=' in result.stdout
    assert 'stderr' not in result.stdout and 'provider rejected' not in result.stdout


@pytest.mark.integration
def test_cli_stderr_canary_reaches_no_status_line_but_stays_in_the_local_log(rig):
    result = launch(rig, mode='canary-fail')
    status = (rig['panel'] / 'correctness.md.status').read_text()
    assert result.returncode == 1 and 'exit 2' in status
    assert 'FAKECANARY' not in status and 'FAKECANARY' not in result.stdout
    log = next(rig['panel'].glob('correctness*.log')).read_text()
    assert 'FAKECANARY0123456' in log  # positive control: the probe can see the canary where it is allowed


@pytest.mark.integration
def test_refusal_text_quoting_a_canary_reaches_no_status_line(rig):
    result = launch(rig, mode='canary-notrun')
    status = (rig['panel'] / 'correctness.md.status').read_text()
    assert result.returncode == 1 and status.startswith('correctness: no report (seat refused: NOT-RUN')
    assert 'FAKECANARY' not in status and '/home/jane' not in status and status == result.stdout


@pytest.mark.integration
def test_pi_seat_refuses_a_model_id_the_provider_does_not_list(rig):
    # A local server answers to any id and Pi exits 0 with a stderr warning: the
    # report would name a model that did not run.
    result = launch(rig, runtime='pi', model='anthropic/nope-model:medium', family='Anthropic',
                    mode='pi-unknown')
    assert result.returncode == 1
    assert result.stdout.startswith('correctness: no report (')
    assert 'nope-model' in result.stdout
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_codex_seat_echoing_the_warning_phrase_still_reports(rig):
    # codex echoes tool output on stderr; reading this PR's own diff must not
    # read as Pi's unlisted-model warning.
    (rig['tmp'] / 'gaze-seats.json').write_text(json.dumps({'cross_family_spend': ['OpenAI']}))
    result = launch(rig, runtime='codex', model='gpt-6-luna', family='OpenAI', mode='codex-echo')
    assert result.returncode == 0, result.stdout
    assert (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_pi_seat_with_a_listed_model_still_reports(rig):
    # Control: the same door and provider without the warning files its report.
    result = launch(rig, runtime='pi', model='anthropic/listed-model:medium', family='Anthropic')
    assert result.returncode == 0, result.stdout
    assert (rig['panel'] / 'correctness.md').exists()


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
    # codex refuses a non-git cwd and reads its workspace under read-only (ticket 1363):
    # the seat must start inside the review tree, a git worktree, with no flag before `exec`
    assert Path((rig['log'] / 'codex.cwd').read_text().strip()) == rig['tree']


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
    assert codex.argv[codex.argv.index('-c') + 1] == 'model_reasoning_effort="medium"'  # ticket 1365
    pi = gaze_seat.build_command(doors['pi'], 'anthropic/claude-haiku-5-5:medium', 'PROMPT', Path('/p/x.seat'),
                                 Path('/p/x.prompt'), {'spool': '/arch/spool/h/pi'})
    assert pi.argv[pi.argv.index('--session-dir') + 1] == '/arch/spool/h/pi' and '--no-session' not in pi.argv
    assert pi.argv[pi.argv.index('--model') + 1] == 'anthropic/claude-haiku-5-5:medium'
    assert pi.argv[pi.argv.index('--tools') + 1] == 'read,grep,find,ls' and pi.argv[-1] == 'PROMPT'
    with pytest.raises(ValueError):  # the claude door offers named aliases only
        gaze_seat.build_command(doors['claude-code'], 'gpt-6-luna', 'P', Path('/o'), Path('/f'))


# Ticket 1371: a seat's settings are the door's, never the host's user CLI config.
# Each shim plays its CLI's config resolution as measured on padme 2026-10-30
# (codex 0.165.0 header: `reasoning effort: low` from ~/.codex/config.toml without
# --ignore-user-config, `none` with it, `medium` with the -c pin either way; claude
# --help: --restricted ignores user, project and local settings files) and records
# what the seat would run with.
CONFIG_SHIMS = {
    'codex': r"""#!/bin/sh
printf '%s\n' "$@" > "$STUB_LOG/codex.argv"
effort=""; ignore=no; prev=""; out=""
for a in "$@"; do
  [ "$a" = --ignore-user-config ] && ignore=yes
  [ "$prev" = -c ] && case "$a" in model_reasoning_effort=*) effort="${a#*=}" ;; esac
  [ "$prev" = -o ] && out="$a"
  prev="$a"
done
user="${CODEX_HOME:-$HOME/.codex}/config.toml"
read_user=no
if [ $ignore = no ] && [ -f "$user" ]; then
  read_user=yes
  [ -z "$effort" ] && effort=$(sed -n 's/^model_reasoning_effort *= *//p' "$user")
fi
effort=$(printf '%s' "$effort" | tr -d '"')
printf 'effort=%s\nuser-config=%s\n' "${effort:-none}" "$read_user" > "$STUB_LOG/codex.settings"
cat > /dev/null
printf 'reach: read=yes shell=no tests=not-run\nverdict: clear\n' > "$out"
""",
    'claude': r"""#!/bin/sh
printf '%s\n' "$@" > "$STUB_LOG/claude.argv"
effort=""; skip=no; prev=""
for a in "$@"; do
  [ "$a" = --restricted ] && skip=yes
  [ "$prev" = --effort ] && effort="$a"
  prev="$a"
done
user="$HOME/.claude/settings.json"
read_user=no
if [ $skip = no ] && [ -f "$user" ]; then
  read_user=yes
  [ -z "$effort" ] && effort=$(sed -n 's/.*"effortLevel": *"\([a-z]*\)".*/\1/p' "$user")
fi
printf 'effort=%s\nuser-config=%s\n' "${effort:-default}" "$read_user" > "$STUB_LOG/claude.settings"
printf 'reach: read=yes shell=no tests=not-run\nverdict: clear\n'
""",
}
HOST_CONFIGS = {
    'codex': ('.codex/config.toml', 'model = "gpt-6.1-sol"\nmodel_reasoning_effort = "low"\n'),
    'claude': ('.claude/settings.json', '{"effortLevel": "low", "model": "opus"}\n'),
}


@pytest.mark.integration
@pytest.mark.parametrize('runtime,model,family', [('codex', 'gpt-6-luna', 'OpenAI'),
                                                  ('claude-code', 'haiku', 'Anthropic')])
def test_seat_ignores_a_conflicting_host_user_config(rig, runtime, model, family):
    cli = runtime.split('-')[0]
    shim = rig['tmp'] / 'bin' / cli
    shim.write_text(bake(CONFIG_SHIMS[cli], rig['log']))
    (rig['tmp'] / 'gaze-seats.json').write_text(json.dumps({'cross_family_spend': ['OpenAI']}))
    runs = []
    for host_config in (False, True):
        if host_config:  # the host sets effort low, as padme's interactive config did (ticket 1365)
            path, body = HOST_CONFIGS[cli]
            (rig['tmp'] / path).parent.mkdir(parents=True, exist_ok=True)
            (rig['tmp'] / path).write_text(body)
        result = launch(rig, runtime=runtime, model=model, family=family, name=f'seat{int(host_config)}')
        assert result.returncode == 0, result.stdout
        argv = (rig['log'] / f'{cli}.argv').read_text().replace(f'seat{int(host_config)}', 'seat')
        argv = unpin(argv)
        runs.append((argv, (rig['log'] / f'{cli}.settings').read_text()))
    assert runs[0] == runs[1]  # the host file changes nothing the seat runs with
    assert runs[1][1] == 'effort=medium\nuser-config=no\n'


def test_pi_door_pins_the_thinking_level_on_every_seat():
    gaze_seat = load_module()
    door = gaze_seat.load_doors(ROOT / 'skills' / 'route' / 'routes.json')['pi']
    spool = {'spool': '/s'}
    pi = gaze_seat.build_command(door, 'anthropic/claude-haiku-5-5:medium', 'P', Path('/o'), Path('/f'), spool)
    assert pi.argv[pi.argv.index('--model') + 1] == 'anthropic/claude-haiku-5-5:medium'
    for unpinned in ('anthropic/claude-haiku-5-5', 'anthropic/claude-haiku-5-5:', 'anthropic/x:loud'):
        with pytest.raises(ValueError, match='thinking'):  # else the host's defaultThinkingLevel decides
            gaze_seat.build_command(door, unpinned, 'P', Path('/o'), Path('/f'), spool)


class _Models(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({'object': 'list', 'data': [{'id': i} for i in self.server.served]}).encode()
        self.send_response(200 if self.path == '/v1/models' else 404)
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def padme(rig):
    """A stub OpenAI-compatible server and a Pi models.json declaring it as provider `padme`."""
    server = HTTPServer(('127.0.0.1', 0), _Models)
    server.served = ['served-model']
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/v1'
    models = rig['tmp'] / 'models.json'
    models.write_text(json.dumps({'providers': {'padme': {'baseUrl': url, 'api': 'openai-completions'}}}))
    rig['env']['IDH_PI_MODELS'] = str(models)
    yield url
    server.shutdown()


def aider_seat(rig, model='padme/served-model', family='unknown', **kw):
    return launch(rig, runtime='aider', model=model, family=family, home='Anthropic', **kw)


@pytest.mark.integration
def test_aider_seat_runs_read_only_against_the_declared_local_server(rig, padme):
    result = aider_seat(rig)  # no consent file: a local provider spends nothing
    assert result.returncode == 0, result.stdout + result.stderr
    report = rig['panel'] / 'correctness.md'
    assert first_line(report) == 'worker: model=padme/served-model · family=unknown · runtime=aider · door=headless'
    argv = (rig['log'] / 'aider.argv').read_text().splitlines()
    assert argv[argv.index('--model') + 1] == 'openai/served-model'
    assert argv[argv.index('--openai-api-base') + 1] == padme  # from Pi's declaration, not a copy
    assert argv[argv.index('--chat-mode') + 1] == 'ask'
    for rail in ('--dry-run', '--no-git', '--no-auto-commits', '--no-suggest-shell-commands'):
        assert rail in argv
    diff = rig['panel'] / 'correctness.diff'
    assert argv[argv.index('--read') + 1] == str(diff) and 'def parse(key)' in diff.read_text()
    assert (rig['panel'] / 'correctness.prompt').read_text().startswith('You are one code-review seat')
    assert argv[argv.index('--message-file') + 1] == str(rig['panel'] / 'correctness.prompt')


@pytest.mark.integration
def test_aider_seat_refuses_a_model_id_the_server_does_not_serve(rig, padme):
    result = aider_seat(rig, model='padme/nope-model')
    assert result.returncode == 1
    assert result.stdout.startswith('correctness: no report (') and 'nope-model' in result.stdout
    assert 'served-model' in result.stdout  # names what the server does serve
    assert not (rig['log'] / 'aider.argv').exists() and not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_aider_seat_without_a_listing_or_declaration_is_no_report(rig, padme):
    (rig['tmp'] / 'models.json').write_text(json.dumps({'providers': {'padme': {'baseUrl': 'http://127.0.0.1:9/v1'}}}))
    unreachable = aider_seat(rig)
    assert unreachable.returncode == 1 and 'no report (cannot list models' in unreachable.stdout
    undeclared = aider_seat(rig, model='ghost/served-model')
    assert undeclared.returncode == 1 and 'no report' in undeclared.stdout
    assert not (rig['log'] / 'aider.argv').exists()


@pytest.mark.integration
def test_aider_seat_failure_is_no_report(rig, padme):
    result = aider_seat(rig, mode='fail')
    assert result.returncode == 1 and 'no report' in result.stdout
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_aider_door_does_not_exempt_a_hosted_provider_from_consent(rig, padme):
    (rig['tmp'] / 'models.json').write_text(json.dumps({'providers': {'hosted': {'baseUrl': padme}}}))
    result = aider_seat(rig, model='hosted/served-model')
    assert result.returncode == 1 and 'no consent for cross-family spend on hosted' in result.stdout


def test_aider_door_declares_rails_and_no_hand_copied_address():
    gaze_seat = load_module()
    door = gaze_seat.load_doors(ROOT / 'skills' / 'route' / 'routes.json')['aider']
    assert {'--chat-mode', 'ask', '--dry-run', '--no-git', '--no-auto-commits'} <= set(door['seat_rails'])
    assert '127.0.0.1' not in json.dumps(door) and '100.' not in door['template']


def charter(role):
    text = (ROOT / 'profiles' / role / 'PROFILE.md').read_text()
    return text.split('\nCharter:\n', 1)[1].strip()


@pytest.mark.integration
@pytest.mark.parametrize('role', ['code-reviewer', 'prose-reviewer'])
def test_seat_prompt_carries_the_role_profile_charter(rig, role):
    extra = [] if role == 'code-reviewer' else ['--role', role]
    result = launch(rig, *extra)
    assert result.returncode == 0, result.stdout + result.stderr
    prompt = (rig['log'] / 'claude.argv').read_text()
    assert charter(role) in prompt  # one source per role: the profile file, not an embedded copy
    assert str(rig['tree']) in prompt and 'correctness.diff' in prompt and rig['head'] in prompt  # launch parts
    assert 'verify the parser' in prompt  # the brief still closes the prompt


@pytest.mark.integration
def test_unknown_role_is_no_report(rig):
    result = launch(rig, '--role', 'no-such-role')
    assert result.returncode != 0 and not (rig['panel'] / 'correctness.md').exists()


def test_plan_guidance_requires_an_external_seat_before_self_only():
    plan = (ROOT / 'skills' / 'gaze' / 'references' / 'plan.md').read_text()
    flat = ' '.join(plan.split())
    assert 'When the subagent door cannot launch' in flat
    assert 'same-family seat on the headless door' in flat
    assert 'before it may fall back to `seats: self-only`' in flat
    assert 'self-only stays only for "no door launched"' in flat


@pytest.mark.integration
def test_aider_runs_in_a_scratch_directory_outside_the_review_tree_and_any_repo(rig, padme):
    result = aider_seat(rig)  # aider loads .aider.conf.yml from its cwd and git root: neither may be reviewed code
    assert result.returncode == 0, result.stdout
    cwd = Path((rig['log'] / 'aider.cwd').read_text().strip()).resolve()
    tree = rig['tree'].resolve()
    assert cwd != tree and tree not in cwd.parents and cwd not in tree.parents
    assert subprocess.run(['git', '-C', str(cwd.parent), 'rev-parse'], capture_output=True).returncode != 0
    assert not cwd.exists()  # removed after the seat


@pytest.mark.integration
def test_local_exemption_follows_the_declared_host_not_the_provider_name(rig, padme):
    (rig['tmp'] / 'models.json').write_text(json.dumps({'providers': {
        'padme-cloud': {'baseUrl': 'http://93.184.216.34:8080/v1'}}}))
    remote = aider_seat(rig, model='padme-cloud/served-model')
    assert remote.returncode == 1 and 'no consent for cross-family spend on padme-cloud' in remote.stdout
    (rig['tmp'] / 'models.json').write_text(json.dumps({'providers': {
        'padme': {'baseUrl': 'http://100.93.160.120:8080/v1'}}}))  # CGNAT (tailnet) address is local
    gaze_seat = load_module()
    door = gaze_seat.load_doors(ROOT / 'skills' / 'route' / 'routes.json')['aider']
    for url, local in (('http://127.0.0.1:1/v1', True), ('http://100.93.160.120/v1', True),
                       ('http://192.168.1.4/v1', True), ('http://localhost/v1', True),
                       ('http://93.184.216.34/v1', False), ('http://example.com/v1', False)):
        assert gaze_seat.is_local(door, 'padme', url) is local, url


@pytest.mark.integration
@pytest.mark.parametrize('label', ['Anthropic', 'OpenAI', 'Local'])
def test_local_seat_family_is_read_from_the_served_id_not_the_plan(rig, padme, label):
    result = aider_seat(rig, family=label)  # served-model is in no grid row
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'family=unknown ·' in first_line(rig['panel'] / 'correctness.md')


def test_grid_family_matches_served_ids_across_case_and_separators(tmp_path):
    gaze_seat = load_module()
    grid = ROOT / 'skills' / 'route' / 'grid.json'
    assert gaze_seat.grid_family('qwen3.8-flash-next-iq3_s', grid) == 'Qwen'
    assert gaze_seat.grid_family('gemma-4-27b', grid) == 'unknown'
    assert gaze_seat.grid_family('qwen3.8-flash-next-iq3_s', tmp_path / 'missing.json') == 'unknown'


@pytest.mark.integration
def test_aider_report_is_the_answer_only(rig, padme):
    result = aider_seat(rig, mode='aiderish')
    assert result.returncode == 0, result.stdout
    report = (rig['panel'] / 'correctness.md').read_text()
    assert report.splitlines()[0].startswith('worker: model=padme/served-model')
    assert 'Aider v' not in report and 'THINKING' not in report and 'Tokens:' not in report
    assert 'verdict: concerns' in report and 'maybe verdict: clear' not in report


@pytest.mark.integration
def test_verdict_in_aider_thinking_does_not_hide_a_refusal(rig, padme):
    refused = aider_seat(rig, mode='aider-notrun')
    assert refused.returncode == 1 and 'seat refused' in refused.stdout
    bare = aider_seat(rig, mode='aider-plain-notrun')  # no marker: the whole answer is scanned
    assert bare.returncode == 1 and 'seat refused' in bare.stdout


@pytest.mark.integration
def test_thinking_without_an_answer_is_no_report(rig, padme):
    result = aider_seat(rig, mode='aider-truncated')  # truncated: a verdict inside thinking only
    assert result.returncode == 1 and 'no report (empty output' in result.stdout
    assert not (rig['panel'] / 'correctness.md').exists()


@pytest.mark.integration
def test_plain_answer_quoting_the_thinking_marker_is_reported(rig, padme):
    result = aider_seat(rig, mode='aider-plain-quote')  # the marker counts only as a line of its own
    assert result.returncode == 0, result.stdout
    assert 'verdict: clear' in (rig['panel'] / 'correctness.md').read_text()


@pytest.mark.integration
def test_non_reasoning_answer_without_a_marker_is_reported(rig, padme):
    result = aider_seat(rig, mode='aider-plain')
    assert result.returncode == 0, result.stdout
    report = (rig['panel'] / 'correctness.md').read_text()
    assert 'verdict: clear' in report and 'Aider v' not in report and 'Repo-map' not in report
    assert 'Tokens:' not in report and report.splitlines()[0].startswith('worker: model=padme/served-model')


@pytest.mark.integration
def test_vibe_seat_is_read_only_pinned_by_a_disposable_home_and_stdin_closed(rig):
    (rig['tmp'] / 'gaze-seats.json').write_text('{"cross_family_spend": ["Mistral"]}')
    result = launch(rig, runtime='vibe', model='mistral-large-latest', family='Mistral',
                    caller_stdin='caller-secret')  # a live pipe: pytest's own fd 0 is /dev/null, which hides a leak
    assert result.returncode == 0, result.stdout
    argv = (rig['log'] / 'vibe.argv').read_text().splitlines()
    assert argv[:2] == ['--enabled-tools', 'read_file'] and argv[4] == '-p'
    spool = argv[argv.index('--output-dir') + 1]  # ticket 1383: the session journal outlives the disposable home
    assert Path(spool).parent.parent.parent.name == 'spool' and Path(spool).parent.name == 'vibe'
    assert Path(spool).is_dir() and Path(spool).is_relative_to(Path(rig['env']['IDH_ARCHIVE_ROOT']))
    assert argv[argv.index('--agent') + 1] == 'seat' and '--trust' not in argv
    assert (rig['log'] / 'vibe.stdin').read_text() == ''  # /dev/null, never the caller's stdin
    assert (rig['log'] / 'vibe.cwd').read_text().strip() == str(rig['tree'].resolve())
    agent = (rig['log'] / 'vibe.agent').read_text()
    assert 'name = "mistral-large-latest"' in agent and 'alias = "seat-model"' in agent
    assert not Path((rig['log'] / 'vibe.home').read_text().strip()).exists()  # home removed after the run
    report = (rig['panel'] / 'correctness.md').read_text()
    assert report.splitlines()[0].startswith('worker: model=mistral-large-latest · family=Mistral · runtime=vibe')


@pytest.mark.integration
def test_vibe_seat_needs_mistral_consent_and_a_plain_model_name(rig):
    refused = launch(rig, runtime='vibe', model='mistral-large-latest', family='Mistral')
    assert refused.returncode == 1 and 'no consent for cross-family spend on Mistral' in refused.stdout
    (rig['tmp'] / 'gaze-seats.json').write_text('{"cross_family_spend": ["Mistral"]}')
    odd = launch(rig, runtime='vibe', model='x"\n[[models]]', family='Mistral')
    assert odd.returncode == 1 and 'not a plain model name' in odd.stdout
    assert not (rig['log'] / 'vibe.argv').exists()


@pytest.mark.integration
def test_refused_seat_status_carries_no_cli_settings_header(rig):
    result = launch(rig, mode='codex-refuse')
    assert result.returncode == 1
    status = (rig['panel'] / 'correctness.md.status').read_text()
    assert status.count('\n') == 1 and status.startswith('correctness: no report (seat refused: NOT-RUN')
    for gone in ('model: gpt-6-luna', 'sandbox:', 'session id', '--------', 'unreadable'):
        assert gone not in status
    assert status.count('(') == status.count(')') and status == result.stdout


@pytest.mark.integration
def test_codex_leak_stderr_reaches_neither_status_nor_stdout(rig):
    result = launch(rig, mode='codex-leak')
    assert result.returncode == 1
    status = (rig['panel'] / 'correctness.md.status').read_text()
    for leaked in ('jane.doe', 'example.org', 'org-AbC123xyz', 'abcDEF123456', 'sk-proj-FAKE', 'janedoe', 'session id'):
        assert leaked not in status and leaked not in result.stdout
    assert status.count('\n') == 1 and status == result.stdout


@pytest.mark.parametrize('leak, secret', [
    ('{"x-api-key": "FAKEapikey0123"}', 'FAKEapikey'),
    ('"access_token":"FAKEaccess0123"', 'FAKEaccess'),
    ('key sk-proj-HEAD********TAILfake', 'TAILfake'),
    ('account_id=0190abcd-1234-5678-9abc-def012345678', 'def012345678'),
    ('Authorization: Basic ZmFrZTpmYWtlcGFzcw==', 'ZmFrZTpm'),
    ('jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJmYWtlIn0.c2lnbmF0dXJl', 'eyJzdWIi'),
    ('{\\"access_token\\": \\"FAKEescaped0123\\"}', 'FAKEescaped'),     # backslash-escaped JSON key (ticket 1378)
    ('Account ID: 0190abcd-1234-5678-9abc-def012345678', 'def012345678'),   # spaced label (ticket 1378)
])
def test_scrub_covers_quoted_masked_escaped_and_labelled_secrets(leak, secret):
    assert secret not in load_module().scrub(leak)


def test_scrub_never_matches_across_a_newline_and_keeps_session_ids():
    scrub = load_module().scrub
    out = scrub('access_token:\nreview plan: x')
    assert 'review plan: x' in out
    assert 'session id: 0190abcd-1234-5678-9abc-def012345678' in scrub('session id: 0190abcd-1234-5678-9abc-def012345678')


@pytest.mark.integration
def test_successful_seat_status_carries_no_stderr(rig):
    result = launch(rig, mode='codex-echo')
    assert result.returncode == 0
    assert 'stderr' not in (rig['panel'] / 'correctness.md.status').read_text()


# Ticket 1376: the seat runs in an allowlisted environment, never the caller's.

NOISE = {
    'CLAUDE_EFFORT': 'low', 'CLAUDE_CODE_MESSAGING_TOKEN': 'fake-messaging-token',
    'CLAUDE_CODE_MESSAGING_SOCKET': '/tmp/fake.sock', 'ANTHROPIC_MODEL': 'opus',
    'CODEX_SANDBOX': 'seatbelt', 'PI_SKIP_VERSION_CHECK': '1', 'SSH_AUTH_SOCK': '/tmp/fake-agent',
    'OPENAI_BASE_URL': 'http://elsewhere.invalid',
}


def dumping_stubs(rig):
    """Make every stub also dump its environment to <STUB_LOG>/<name>.env."""
    for name in ('claude', 'codex', 'pi', 'aider', 'vibe'):
        stub = rig['tmp'] / 'bin' / name
        stub.write_text(bake(STUB.replace('#!/bin/sh\n', '#!/bin/sh\nenv | sort > "$STUB_LOG/$(basename "$0").env"\n', 1), rig['log']))


def seat_env(rig, name):
    return dict(line.split('=', 1) for line in (rig['log'] / f'{name}.env').read_text().splitlines() if '=' in line)


@pytest.mark.integration
def test_conflicting_parent_variables_change_neither_seat_command_nor_environment(rig):
    dumping_stubs(rig)
    rig['env']['ANTHROPIC_API_KEY'] = 'fake-credential'
    assert launch(rig).returncode == 0
    quiet_argv = unpin((rig['log'] / 'claude.argv').read_text())
    quiet_env = (rig['log'] / 'claude.env').read_text()
    rig['env'].update(NOISE)
    assert launch(rig).returncode == 0
    assert unpin((rig['log'] / 'claude.argv').read_text()) == quiet_argv
    assert (rig['log'] / 'claude.env').read_text() == quiet_env
    seen = seat_env(rig, 'claude')
    assert not set(NOISE) & set(seen)
    assert seen['ANTHROPIC_API_KEY'] == 'fake-credential' and seen['PATH'] == rig['env']['PATH']


@pytest.mark.integration
def test_codex_seat_keeps_its_declared_credential_and_home_only(rig):
    dumping_stubs(rig)
    (rig['tmp'] / 'gaze-seats.json').write_text(json.dumps({'cross_family_spend': ['OpenAI']}))
    rig['env'].update(NOISE, CODEX_HOME='/tmp/codex-home', OPENAI_API_KEY='fake-openai')
    result = launch(rig, runtime='codex', model='gpt-6-luna', family='OpenAI', name='redteam')
    assert result.returncode == 0, result.stdout
    seen = seat_env(rig, 'codex')
    assert seen['CODEX_HOME'] == '/tmp/codex-home' and seen['OPENAI_API_KEY'] == 'fake-openai'
    assert not set(NOISE) & set(seen)


@pytest.mark.integration
def test_pi_seat_keeps_only_the_key_its_provider_declares(rig):
    dumping_stubs(rig)
    models = rig['tmp'] / 'models.json'
    models.write_text(json.dumps({'providers': {'myprov': {'baseUrl': 'https://x.invalid/v1', 'apiKey': '$MYPROV_KEY'}}}))
    rig['env'].update(NOISE, IDH_PI_MODELS=str(models), MYPROV_KEY='fake-pi-key', OTHER_KEY_PI='must-not-pass')
    (rig['tmp'] / 'gaze-seats.json').write_text(json.dumps({'cross_family_spend': ['myprov']}))
    result = launch(rig, runtime='pi', model='myprov/m:low', family='Other', home='Other', name='scope')
    assert result.returncode == 0, result.stdout
    seen = seat_env(rig, 'pi')
    assert seen['MYPROV_KEY'] == 'fake-pi-key'
    assert 'OTHER_KEY_PI' not in seen and not set(NOISE) & set(seen)


@pytest.mark.integration
def test_vibe_seat_gets_its_disposable_home_and_no_caller_runtime_variables(rig):
    dumping_stubs(rig)
    (rig['tmp'] / 'gaze-seats.json').write_text(json.dumps({'cross_family_spend': ['Mistral']}))
    rig['env'].update(NOISE, VIBE_HOME='/tmp/host-vibe')
    result = launch(rig, runtime='vibe', model='mistral-medium-3.5', family='Mistral', name='scope')
    assert result.returncode == 0, result.stdout
    seen = seat_env(rig, 'vibe')
    assert seen['VIBE_HOME'] != '/tmp/host-vibe' and not set(NOISE) & set(seen)


@pytest.mark.integration
def test_dry_run_names_the_seat_environment_without_values(rig):
    rig['env'].update(NOISE, ANTHROPIC_API_KEY='fake-credential')
    result = launch(rig, '--dry-run')
    assert result.returncode == 0, result.stdout
    plan = json.loads(result.stdout)
    assert 'PATH' in plan['env'] and 'ANTHROPIC_API_KEY' in plan['env'] and not set(NOISE) & set(plan['env'])
    assert 'fake-credential' not in result.stdout and rig['env']['PATH'] not in result.stdout


@pytest.mark.integration
def test_no_caller_variable_opens_the_seat_environment(rig):
    dumping_stubs(rig)
    rig['env'].update(IDH_SEAT_ENV_PASS='*', CLAUDE_EFFORT='low', CLAUDE_CODE_MESSAGING_TOKEN='fake-messaging-token')
    assert launch(rig).returncode == 0
    seen = seat_env(rig, 'claude')
    assert 'CLAUDE_EFFORT' not in seen and 'CLAUDE_CODE_MESSAGING_TOKEN' not in seen


@pytest.mark.integration
def test_seat_keeps_xdg_runtime_dir_only(rig):
    dumping_stubs(rig)
    rig['env'].update(XDG_RUNTIME_DIR='/run/user/1', XDG_CONFIG_HOME='/tmp/cfg', XDG_DATA_HOME='/tmp/data')
    assert launch(rig).returncode == 0
    seen = seat_env(rig, 'claude')
    assert seen['XDG_RUNTIME_DIR'] == '/run/user/1'
    assert 'XDG_CONFIG_HOME' not in seen and 'XDG_DATA_HOME' not in seen


@pytest.mark.integration
def test_seat_locale_is_pinned_whatever_the_caller_speaks(rig):
    dumping_stubs(rig)
    rig['env'].update(LANG='fr_FR.UTF-8', LC_ALL='fr_FR.UTF-8', LC_MESSAGES='fr_FR.UTF-8')
    assert launch(rig).returncode == 0
    seen = seat_env(rig, 'claude')
    assert seen['LANG'] == 'C.UTF-8'
    assert not [k for k in seen if k.startswith('LC_')]


def test_claude_door_declares_its_config_home():
    door = json.loads((ROOT / 'skills' / 'route' / 'routes.json').read_text())['launch_doors']['claude-code']['headless']
    assert 'CLAUDE_CONFIG_DIR' in door['env_keep']


def test_doors_that_keep_no_session_file_name_their_spool():
    """Ticket 1383: no door sends history to /dev/null or runs --no-session."""
    gaze_seat = load_module()
    doors = gaze_seat.load_doors(ROOT / 'skills' / 'route' / 'routes.json')
    aider = gaze_seat.build_command(doors['aider'], 'openai/m', 'P', Path('/o'), Path('/f'),
                                    {'spool': '/s/a', 'baseUrl': 'http://x/v1', 'diff': '/d'})
    for flag, name in (('--chat-history-file', 'chat.md'), ('--llm-history-file', 'llm.md'),
                       ('--input-history-file', 'input.md')):
        assert aider.argv[aider.argv.index(flag) + 1] == f'/s/a/{name}'
    assert aider.argv[aider.argv.index('--env-file') + 1] == '/dev/null'  # credentials stay unread
    with pytest.raises(ValueError, match='spool'):
        gaze_seat.build_command(doors['aider'], 'openai/m', 'P', Path('/o'), Path('/f'), {'baseUrl': 'http://x/v1', 'diff': '/d'})
    for name, door in doors.items():
        argv = gaze_seat.shlex.split(door['template']) + door['seat_rails']
        assert '--no-session' not in argv and '--no-session-persistence' not in argv, name
        rails = door['seat_rails']
        assert all(t != '/dev/null' or rails[n - 1] == '--env-file' for n, t in enumerate(rails)), name


@pytest.mark.integration
def test_launch_line_carries_the_session_id_the_claude_seat_was_launched_with(rig):
    """Ticket 1384: the child id is the pinned `--session-id`, never a start-time join."""
    assert launch(rig, name='lines').returncode == 0
    argv = (rig['log'] / 'claude.argv').read_text().splitlines()
    pinned = argv[argv.index('--session-id') + 1]
    rows = [json.loads(line) for line in next((Path(rig['env']['IDH_ARCHIVE_ROOT']) / 'raw').glob('*/launches.jsonl')).read_text().splitlines()]
    assert [(r['seat'], r['child_runtime'], r['child_session'], r['exit']) for r in rows] == \
        [('lines', 'claude', pinned, 0)]


@pytest.mark.integration
@pytest.mark.parametrize('mode', ['fenced', 'fenced-bare'])
def test_header_wrapped_in_a_balanced_block_is_accepted(rig, mode):
    result = launch(rig, mode=mode)
    assert result.returncode == 0, result.stdout
    assert 'header unwrapped from a Markdown block' in result.stdout
    report = (rig['panel'] / 'correctness.md').read_text()
    lines = report.splitlines()
    assert lines[0] == 'worker: model=haiku · family=Anthropic · runtime=claude-code · door=headless'  # launcher's
    assert lines[1] == 'reach: read=yes shell=no tests=not-run'
    assert 'fixture-qwen' not in report and '```' not in report
    assert 'verdict: clear' in report and 'finding: none' in report  # body kept
    raw = (rig['panel'] / 'correctness.md.raw').read_text()
    assert raw.lstrip().startswith('```') and 'reach: read=yes' in raw


@pytest.mark.integration
def test_ordinary_report_is_not_noted_as_unwrapped(rig):
    result = launch(rig)
    assert 'unwrapped' not in result.stdout and not (rig['panel'] / 'correctness.md.raw').exists()


@pytest.mark.integration
@pytest.mark.parametrize('mode,reason', [
    ('fenced-noread', 'read=no'),
    ('fenced-ranno', 'invalid reach declaration'),
    ('fenced-unknown', 'invalid reach declaration'),
    ('fenced-open', 'not a balanced header-only block'),
    ('fenced-two', 'not a balanced header-only block'),
    ('fenced-extra', 'not a balanced header-only block'),
    ('fenced-lang', 'not a balanced header-only block'),
    ('fenced-quoted', 'no valid reach line'),
    ('fenced-example', 'no valid reach line'),
])
def test_wrapped_header_never_invents_or_promotes_a_declaration(rig, mode, reason):
    result = launch(rig, mode=mode)
    assert result.returncode == 1, result.stdout
    assert reason in result.stdout and 'seat reach: ' in result.stdout
    assert not (rig['panel'] / 'correctness.md').exists()


def test_unwrap_header_unit():
    gs = load_module()
    ok = '```text\nworker: w\nreach: read=yes shell=no tests=not-run\n```\nbody\n'
    assert gs.unwrap_header(ok) == ('worker: w\nreach: read=yes shell=no tests=not-run\nbody\n', True)
    plain = 'reach: read=yes shell=no tests=not-run\nbody\n'
    assert gs.unwrap_header(plain) == (plain, False)
    # stamp + validation: the real pipeline on the ticket's fragment
    fixed, _ = gs.unwrap_header(ok)
    assert gs.reach_refusal(gs.stamp(fixed, 'worker: launcher')) is None
    assert gs.reach_refusal(gs.stamp(ok, 'worker: launcher')) is not None


def test_repeated_or_contradictory_reach_lines_are_refused():
    """Ticket 1400 audit: only line 2 was read, so a second, contradicting reach line was admitted."""
    gs = load_module()
    yes, no = 'reach: read=yes shell=no tests=not-run', 'reach: read=no shell=no tests=not-run'
    for first, second in ((yes, no), (no, yes), (yes, yes)):
        report = gs.stamp(f'{first}\n{second}\nbody\n', 'worker: launcher')
        assert gs.reach_refusal(report) is not None
    late = gs.stamp(f'{yes}\nverdict: clear\n{no}\n', 'worker: launcher')  # not adjacent: still a complete second declaration
    assert gs.reach_refusal(late) == 'ambiguous reach declaration (repeated reach line)'
    prose = gs.stamp(f'{yes}\nfinding: the line reach: is parsed\nverdict: clear\n', 'worker: launcher')
    assert gs.reach_refusal(prose) is None


def test_not_run_line_is_a_refusal_even_before_a_verdict_line():
    gs = load_module()
    report = gs.stamp('reach: read=yes shell=no tests=not-run\nNOT-RUN: x\nverdict: none\n', 'worker: launcher')
    assert gs.refusal(report) is not None
    ok = gs.stamp('reach: read=yes shell=no tests=not-run\nfinding: prints NOT-RUN: on refusal\nverdict: clear\n', 'worker: l')
    assert gs.refusal(ok) is None


AIDER_DOOR = {'answer_marker': '► **ANSWER**', 'thinking_marker': '► **THINKING**'}
MARK, THINK = AIDER_DOOR['answer_marker'], AIDER_DOOR['thinking_marker']
YES = 'reach: read=yes shell=yes tests=ran'
NO = 'reach: read=no shell=no tests=not-run'


def test_aider_answer_is_the_final_framed_body_not_a_quoted_declaration():
    gs = load_module()
    quoted = f'{THINK}\nThe seat may write:\n{MARK}\n{YES}\nverdict: clear\n------------\n{MARK}\n\n{MARK}\n{NO}\nverdict: concerns\n\nTokens: 1\n'
    answer = gs.answer_of(AIDER_DOOR, quoted)
    assert answer.strip() == f'{NO}\nverdict: concerns'
    inline = f"{THINK}\nThe marker is '{MARK}' and {YES}\n------------\n{MARK}\n\n{MARK}\n{NO}\n"
    assert gs.answer_of(AIDER_DOOR, inline).strip() == NO


def test_aider_answer_edge_shapes():
    gs = load_module()
    assert gs.answer_of(AIDER_DOOR, f'{THINK}\nsee {MARK} and {YES}\n') == ''  # quoted inline marker, never answered
    assert gs.answer_of(AIDER_DOOR, f'{THINK}\n{YES}\n') == ''
    plain = gs.answer_of(AIDER_DOOR, f'Aider v1\n\n{NO}\nverdict: clear\nTokens: 1\n')
    assert plain.startswith(NO)
    assert gs.answer_of(AIDER_DOOR, f'{THINK}\nx\n---\n{MARK}\nNOT-RUN: nope\n').strip() == 'NOT-RUN: nope'
    assert gs.answer_of(AIDER_DOOR, f'---\n{MARK}\nverdict: clear\n').strip() == 'verdict: clear'  # no reach: left for reach_refusal
    assert gs.answer_of({}, 'raw\ntext\n') == 'raw\ntext\n'

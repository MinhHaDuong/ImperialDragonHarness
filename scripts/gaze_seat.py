#!/usr/bin/env python3
"""Launch one gaze review seat as a detached headless CLI (ticket 1256).

`launch` builds the seat's command from the runtime's headless door in
`skills/route/routes.json` (`launch_doors.<runtime>.headless`: its `template`,
with the model pinned, and its `seat_rails` flags: read tools only, no shell
and no write tool, where the CLI offers an allowlist; codex holds the seat by
its read-only sandbox instead). It writes the diff `<base>...HEAD` beside the
report, since a seat without a shell cannot run git, builds the prompt from the role's profile
Charter (`--role`, `profiles/<role>/PROFILE.md`) plus the launch rails, pins the cwd to the review tree and runs it under
`seat_clock.run_seat` with a hard cap. A headless process does not nest inside
the caller's agent tree, so the same door works from a subagent on every
runtime.

The report lands as `<panel>/<name>.md`, written `.part` then renamed, its
first line `worker: model=<pin> · family=<family> · runtime=<rt> ·
door=headless` set by the launcher: the pin is what ran, and a CLI's own
self-report of its model is not trusted. Whatever stops a seat (no door, a
family the door cannot serve, no consent, an unreadable or moved review tree,
a start failure, a nonzero exit, empty output, a `NOT-RUN:` refusal, a missing, invalid or `read=no` `reach:` line (a header wrapped in one balanced header-only Markdown block is
unwrapped first, noted in the status line, the seat's answer kept as `<name>.md.raw`), the
cap) prints and saves
`<name>: no report (<reason>)` (a seat whose CLI ran appends `; door=<rt>, model=<pin>`: harness-owned fields
only, the CLI's stderr stays in the local `.log` and never reaches notes) to `<panel>/<name>.md.status` and writes no
report, so `seat_clock.py plan-check` counts it missing. Nothing here reads
the code in the caller's place.

Consent to spend on another provider is one host-local key,
`cross_family_spend` (a list of providers), in `$IDH_GAZE_SEATS_CONFIG`, else
`${XDG_CONFIG_HOME:-~/.config}/harness/gaze-seats.json`. Absent, no
cross-family seat launches. `consent` prints the manifest header line that
declares it in the plan before anything launches. Consent is checked against
the provider that bills the seat, never the caller's family label: the door's
one family (Anthropic on claude-code, OpenAI on codex), or the `<provider>/`
prefix of a pi model. The provider of the session running gaze
(`--home-family`) needs no consent. A provider that is itself a model family
(any family a door names) fixes the seat's family, so `--family` cannot claim
another one; a host provider serving other makers' models leaves the label to
the plan. A local server (routes.json `local_providers` on a loopback, private
or CGNAT host) serves whatever is loaded, so its seat's family is read from the
served id: the grid `family` of that model (`skills/route/grid.json`), else
`unknown`. Being local is access, never a family; it only waives consent.
"""

import argparse
import importlib.util
import fnmatch
import ipaddress
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('seat_clock', HERE / 'seat_clock.py')
seat_clock = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seat_clock)  # a sibling script, not a package

_spec = importlib.util.spec_from_file_location('transcript_spool', HERE / 'transcript_spool.py')
transcript_spool = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(transcript_spool)
sys.path.insert(0, str(HERE))
import launch_line  # noqa: E402  (ticket 1384)

ROUTES = HERE.parent / 'skills' / 'route' / 'routes.json'
CONSENT_KEY = 'cross_family_spend'
MODEL_FLAGS = ('--model', '-m')
PLACEHOLDER = re.compile(r'<[^<>]+>.*')
ANCHOR = re.compile(r'[0-9a-f]{7,40}')

SEAT_MODEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*')
SEAT_AGENT_TOML = '''\
active_model = "seat-model"

[[models]]
name = "{model}"
provider = "{provider}"
alias = "seat-model"
'''

# Variables a seat inherits whatever the door: the process basics and the network transport. Anything
# else (CLAUDE_*, CODEX_*, PI_*, ANTHROPIC_MODEL, SSH_AUTH_SOCK, the parent's messaging token) is
# dropped; a door keeps its credentials and auth home by `env_keep` in routes.json (ticket 1376).
BASE_ENV = ('PATH', 'HOME', 'USER', 'LOGNAME', 'SHELL', 'TMPDIR', 'TERM', 'XDG_RUNTIME_DIR',
            'DBUS_SESSION_BUS_ADDRESS', 'HTTP_PROXY', 'HTTPS_PROXY', 'NO_PROXY', 'ALL_PROXY',
            'http_proxy', 'https_proxy', 'no_proxy', 'all_proxy', 'SSL_CERT_FILE', 'SSL_CERT_DIR',
            'NODE_EXTRA_CA_CERTS', 'REQUESTS_CA_BUNDLE')
SEAT_LOCALE = 'C.UTF-8'  # set by the launcher, never inherited: a caller's LANG changed a seat's reply language

ROLES = ('code-reviewer', 'prose-reviewer')
PROFILES = HERE.parent / 'profiles'

LAUNCH = """\
You are launched headless as one seat of a gaze panel.

Perspective: {perspective}. Judge against this one perspective only.
Review tree: {tree}, anchored at HEAD {anchor}.

The change under review is the diff in {diff}; read it first, then the
files it touches under the review tree.

Launch rails (they override the profile where it names a file to write):
- Read the tree only with your read tools, or, where you have a shell, as
  `git -C "{tree}" ...`.
- Never overwrite the working tree: no `git checkout <ref> -- <path>`, no
  `git restore .`, no `git reset --hard`. Read another version with
  `git show <ref>:<path>`.
- If the tree is unreachable or its HEAD is not {anchor}, reply with one line
  `NOT-RUN: <reason>` and stop; never fall back to another directory.
- Write no file, post nothing, commit and push nothing, read no credentials.
- Open your report with `worker: ...`, then a second line
  `reach: read=<yes|no> shell=<yes|no> tests=<ran|not-run>`: whether you
  could read the tree, had a shell, and ran tests or read code only. If you
  could not read the tree, say `read=no`; never write a clear.
- Your final message is your report; the launcher files it, so write no
  report file yourself. An empty changed-file list never yields `clear`.

The brief from gaze (intent, exit criteria, changed-file roster) follows.

{brief}
"""


def persona(role: str) -> str:
    """The role's Charter, read from its profile file: one source per role, never per model."""
    text = (PROFILES / role / 'PROFILE.md').read_text(encoding='utf-8')
    return text.split('\nCharter:\n', 1)[1].strip()


@dataclass
class Command:
    argv: list[str]
    stdin: Path | None
    env: dict[str, str] | None = None


def seat_env(door: dict, extra: list[str] = (), environ=None) -> dict[str, str]:
    """The seat's whole environment: the caller's variables the base set, the door's `env_keep` and
    `extra` names allow, plus the pinned locale; nothing else. Fail closed: a new variable is dropped."""
    environ = os.environ if environ is None else environ
    allowed = [*BASE_ENV, *door.get('env_keep', []), *extra]
    kept = {k: v for k, v in environ.items() if any(fnmatch.fnmatchcase(k, pattern) for pattern in allowed)}
    return {**kept, 'LANG': SEAT_LOCALE}


def pi_key_names(provider_id: str) -> list[str]:
    """The variable a Pi provider's `apiKey: "$NAME"` indirection reads (the file differs per host), else none."""
    try:
        key = json.loads(pi_models_path().read_text(encoding='utf-8'))['providers'][provider_id]['apiKey']
    except (OSError, ValueError, KeyError, TypeError):
        return []
    match = re.fullmatch(r'\$\{?(\w+)\}?', key) if isinstance(key, str) else None
    return [match.group(1)] if match else []


def load_doors(routes: Path) -> dict:
    doors = json.loads(routes.read_text(encoding='utf-8'))['launch_doors']
    return {name: door['headless'] for name, door in doors.items()
            if isinstance(door, dict) and 'headless' in door}


def build_command(door: dict, model: str, prompt: str, outfile: Path, promptfile: Path,
                  values: dict[str, str] | None = None) -> Command:
    """Fill the door's template; raise ValueError when it cannot carry this seat."""
    if 'seat_rails' not in door:
        raise ValueError('door declares no seat_rails, so it cannot hold a seat read-only')
    tokens = shlex.split(door['template'])
    values = values or {}
    argv: list[str] = []
    stdin = None
    skip = False
    for index, token in enumerate(tokens):
        if skip:
            skip = False
            continue
        previous = tokens[index - 1] if index else ''
        if token == '<' and index + 1 < len(tokens) and tokens[index + 1] == '<promptfile>':
            stdin, skip = promptfile, True
        elif token == '<prompt>':
            argv.append(prompt)
        elif token == '<outfile>':
            argv.append(str(outfile))
        elif token == '<promptfile>':
            argv.append(str(promptfile))
        elif token.strip('<>') in values and token.startswith('<'):
            argv.append(values[token.strip('<>')])
        elif previous in MODEL_FLAGS and PLACEHOLDER.fullmatch(token) and ':<' in token:
            # `<provider>/<id>:<levels>`: the seat names its thinking level, the host default never does.
            levels = token.rsplit(':<', 1)[1].strip('<>').split('|')
            named, _, level = model.rpartition(':')
            if not named or level not in levels:
                raise ValueError(f'model {model} pins no thinking level; add :<{"|".join(levels)}>')
            argv.append(model)
        elif previous in MODEL_FLAGS and PLACEHOLDER.fullmatch(token):
            offered = token.strip('<>').split('|')
            if len(offered) > 1 and model not in offered:
                raise ValueError(f'model {model} not offered by this door ({", ".join(offered)})')
            argv.append(model)
        elif PLACEHOLDER.fullmatch(token):
            raise ValueError(f'template placeholder {token} has no value')
        else:
            argv.append(token)
    lead = next(i for i, token in enumerate(argv) if token.startswith('-'))
    rails = list(door['seat_rails'])
    if any('<spool>' in token for token in rails):
        if 'spool' not in values:
            raise ValueError('seat_rails placeholder <spool> has no value')
        rails = [token.replace('<spool>', values['spool']) for token in rails]
    return Command(argv[:lead] + rails + argv[lead:], stdin)


def seat_home(door: dict, model: str) -> Path:
    """A disposable VIBE_HOME holding the seat agent that pins `model` (ticket 1279).

    Vibe has no model flag; the agent file is the pin. The home is empty otherwise, so the
    user's config and trusted folders never shape the seat. Auth is the OS keyring, not the home.
    """
    spec = door['seat_agent']
    home = Path(tempfile.mkdtemp(prefix='gaze-vibe-', dir='/tmp'))
    (home / 'agents').mkdir()
    (home / 'agents' / f'{spec["name"]}.toml').write_text(
        SEAT_AGENT_TOML.format(model=model, provider=spec['provider']), encoding='utf-8')
    return home


def remove_home(home: Path) -> None:
    """Remove the disposable home; Vibe leaves read-only plugin files in read-only directories."""
    def unlock(function, path, _error):
        os.chmod(os.path.dirname(path), 0o700)
        function(path)
    shutil.rmtree(home, onerror=unlock)


def config_path() -> Path:
    if os.environ.get('IDH_GAZE_SEATS_CONFIG'):
        return Path(os.environ['IDH_GAZE_SEATS_CONFIG'])
    base = os.environ.get('XDG_CONFIG_HOME') or str(Path.home() / '.config')
    return Path(base) / 'harness' / 'gaze-seats.json'


def consented(path: Path) -> list[str]:
    try:
        families = json.loads(path.read_text(encoding='utf-8')).get(CONSENT_KEY, [])
    except (OSError, ValueError, AttributeError):
        return []
    return [str(f) for f in families] if isinstance(families, list) else []


def consent_line(path: Path) -> str:
    families = consented(path)
    if not families:
        return f'# spend: cross-family none consented ({CONSENT_KEY} unset in {path})'
    return f'# spend: cross-family consented for {", ".join(families)} ({path})'


def door_serves(door: dict, family: str) -> bool:
    served = [f.lower() for f in door.get('families', [])]
    return any(f.startswith('any provider') for f in served) or family.lower() in served


def billed_provider(door: dict, model: str) -> str | None:
    """The provider that bills a seat: the door's one family, else the model's prefix."""
    families = door.get('families', [])
    if len(families) == 1 and not families[0].lower().startswith('any provider'):
        return families[0]
    return model.split('/', 1)[0] if '/' in model else None


def pi_models_path() -> Path:
    return Path(os.environ.get('IDH_PI_MODELS') or Path.home() / '.pi' / 'agent' / 'models.json')


def served_models(base_url: str) -> list[str] | None:
    """Ids an OpenAI-compatible server lists at <baseUrl>/models; None when it cannot be read."""
    try:
        with urllib.request.urlopen(base_url.rstrip('/') + '/models', timeout=15) as response:
            return [str(item['id']) for item in json.load(response)['data']]
    except (OSError, ValueError, KeyError, TypeError):
        return None


def grid_family(model_id: str, grid: Path) -> str:
    """The grid `family` of a served model id, else `unknown` (ids and grid names differ by case and separators)."""
    def norm(name: str) -> str:
        return re.sub(r'[\s_]+', '-', name.strip().lower())
    try:
        rows = json.loads(grid.read_text(encoding='utf-8'))['grid']
    except (OSError, ValueError, KeyError, TypeError):
        return 'unknown'
    return next((str(row['family']) for row in rows if norm(str(row.get('model', ''))) == norm(model_id)), 'unknown')


def is_local(door: dict, provider: str, base_url: str) -> bool:
    """A provider is local when its name matches and its declared host is loopback, private or CGNAT."""
    if not any(fnmatch.fnmatchcase(provider, pattern) for pattern in door.get('local_providers', [])):
        return False
    host = urlsplit(base_url).hostname or ''
    if host == 'localhost':
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_loopback or address.is_private or address in ipaddress.ip_network('100.64.0.0/10')


BANNER = re.compile(r'(Aider v|Main model:|Model:|Git repo:|Repo-map:|Added |Warning|You can skip|Open documentation|https?://|\s*$)')


def answer_of(door: dict, text: str) -> str:
    """A door's answer: after its marker when it prints one, else the output after the leading banner.

    aider prints the answer marker only around reasoning content, so a plain answer has none.
    Thinking without its answer marker is a truncated run: no answer, so no report.
    """
    marker = door.get('answer_marker')
    thinking = door.get('thinking_marker')
    marked = {line.strip() for line in text.splitlines()}
    if marker and thinking and thinking in marked and marker not in text:
        return ''
    lines = text.split(marker, 1)[1].splitlines() if marker and marker in text else text.splitlines()
    if not (marker and marker in text):
        start = next((i for i, line in enumerate(lines) if not BANNER.match(line)), len(lines))
        lines = lines[start:]
    cut = next((i for i, line in enumerate(lines) if line.startswith('Tokens: ')), len(lines))
    return '\n'.join(lines[:cut]) if marker else text


RAW_KEEP_BYTES = 256 * 1024  # one seat's kept output; a bound, not a quota


def keep_raw(name: str, source: Path) -> None:
    """Copy a seat's output as received to `<archive>/raw/<host>/seat-raw/<seat id>-<name>.raw`.

    The panel dies with the review tree, so a refused seat's bytes would be gone before anyone
    could diagnose it (monitoring memo, section 4.2). The archive's raw store is durable and never
    pruned; nothing here can refuse a seat, and a failed copy is silent.
    """
    try:
        data = source.read_bytes()[:RAW_KEEP_BYTES]
        if not data:
            return
        directory = transcript_spool.raw_dir() / 'seat-raw'
        transcript_spool.mkdir_private(directory)
        target = directory / f'{transcript_spool.seat_id()}-{name}.raw'
        target.write_bytes(data)
        target.chmod(0o600)
    except OSError:
        pass


def git(tree: Path, *args: str) -> str | None:
    result = subprocess.run(['git', '-C', str(tree), *args], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


FENCE = re.compile(r'```[ \t]*(?:text|txt|plain|plaintext|markdown|md)?[ \t]*')


def unwrap_header(text: str) -> tuple[str, bool]:
    """Lift a header the seat wrapped in one balanced Markdown block at the very top of its report.

    Bounded on purpose: the block must be the first non-blank content, close on a bare fence line, and hold
    only an optional `worker:` line then exactly one `reach:` line. The fences go, every other byte stays;
    the reach values are checked later as written, never repaired. Any other shape is returned unchanged
    and refused by `reach_refusal`; a header quoted further down is never looked at.
    """
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if line.strip()), len(lines))
    if start == len(lines) or not FENCE.fullmatch(lines[start].strip()):
        return text, False
    end = next((i for i in range(start + 1, len(lines)) if lines[i].strip().startswith('```')), None)
    if end is None or lines[end].strip() != '```':
        return text, False
    inner = [line for line in lines[start + 1:end] if line.strip()]
    plain = [line.strip().strip('*`').strip().lower() for line in inner]
    if not (1 <= len(inner) <= 2) or not plain[-1].startswith('reach:'):
        return text, False
    if len(inner) == 2 and not plain[0].startswith('worker:'):
        return text, False
    return '\n'.join(lines[:start] + inner + lines[end + 1:]) + '\n', True


def header_lines(text: str) -> list[str]:
    """The report's lines that hold a word character, stripped of `*` and backticks, after the header block
    is unwrapped: a line of rules or bare markers (`---`, `**`) is blank.

    The one reader of a report's header: the launcher's checks here and the plan check in
    `seat_clock.py` both take their worker and reach lines from it.
    """
    return [line.strip().strip('*`').strip() for line in unwrap_header(text)[0].splitlines()
            if re.search(r'\w', line)]


def is_worker_line(line: str) -> bool:
    return line.lower().startswith('worker:')


def stamp(text: str, worker: str) -> str:
    """Put the launcher's worker line first, replacing any the seat wrote."""
    lines = text.splitlines()
    body = [line for line in lines if line.strip()]
    if body and is_worker_line(body[0].strip().strip('*`').strip()):
        drop = lines.index(body[0])
        lines = lines[:drop] + lines[drop + 1:]
    rest = '\n'.join(lines).strip('\n')
    return f'{worker}\n{rest}\n' if rest.strip() else ''


def refusal(report: str) -> str | None:
    """The seat's `NOT-RUN:` line: a refusal even when a later line carries a `verdict:`."""
    return next((line for line in header_lines(report) if line.upper().startswith('NOT-RUN')), None)


REACH = re.compile(r'reach:\s*read=(yes|no)\s+shell=(yes|no)\s+tests=(ran|not-run)\s*$', re.I)


def reach_refusal(report: str) -> str | None:
    """Why the seat's declared reach rules out a report: no valid `reach:` line, a repeated one, or `read=no`."""
    raw = [line.strip() for line in report.splitlines() if line.strip()]
    lines = [line.strip('*`').strip() for line in raw]
    line = lines[1] if len(lines) > 1 else ''  # the launcher's worker line is first
    if not (m := REACH.fullmatch(line)):
        if raw[1:2] and raw[1].startswith('```'):
            return 'header inside a Markdown block that is not a balanced header-only block'
        if line.lower().startswith('reach:'):
            return 'invalid reach declaration'
        return 'no valid reach line'
    if any(REACH.fullmatch(later) for later in lines[2:]) or (len(lines) > 2 and lines[2].lower().startswith('reach:')):
        return 'ambiguous reach declaration (repeated reach line)'
    return 'read=no' if m.group(1).lower() == 'no' else None


# Pi's warning line when it runs an id the provider does not list. Anchored at line start and
# read for Pi only: codex echoes tool output (files, diffs) to stderr, phrase included.
UNLISTED_MODEL = re.compile(r'Warning: Model ".*" not found for provider ')


def launch(args: argparse.Namespace) -> tuple[bool, str]:
    # The seat runs with its cwd in the review tree: every path it is handed is absolute.
    args.panel, args.review_tree = args.panel.resolve(), args.review_tree.resolve()
    doors = load_doors(args.routes)
    door = doors.get(args.runtime)
    if door is None:
        return False, f'no report (no headless door for runtime {args.runtime})'
    if not door_serves(door, args.family):
        return False, f'no report (the {args.runtime} door cannot serve family {args.family})'
    provider = billed_provider(door, args.model)
    if provider is None:
        return False, f'no report (cannot tell which provider bills {args.model}; name it as <provider>/<id>)'
    known = {f.lower() for d in doors.values() for f in d.get('families', [])
             if not f.lower().startswith('any provider')}
    if provider.lower() in known and provider.lower() != args.family.lower():
        # A provider that is itself a model family serves only that family:
        # the stamped family must not claim another one.
        return False, f'no report (model {args.model} is family {provider}, not {args.family})'
    values: dict[str, str] = {}
    run_model, local = args.model, False
    if 'baseUrl' in door['template']:
        # An OpenAI-compatible door: the server is the provider's declaration in Pi's models.json.
        provider_id, _, model_id = args.model.partition('/')
        try:
            declared = json.loads(pi_models_path().read_text(encoding='utf-8'))['providers'][provider_id]
            base_url = str(declared['baseUrl'])
        except (OSError, ValueError, KeyError, TypeError):
            return False, f'no report (provider {provider_id} has no baseUrl in {pi_models_path()})'
        local = is_local(door, provider_id, base_url)
        if local:  # the plan's label cannot know what the server has loaded
            args.family = grid_family(model_id, args.routes.parent / 'grid.json')
        values['baseUrl'], run_model = base_url, f'openai/{model_id}'
    if provider.lower() != args.home_family.lower() and not local and \
            provider.lower() not in (f.lower() for f in consented(config_path())):
        return False, (f'no report (no consent for cross-family spend on {provider}; '
                       f'{CONSENT_KEY} in {config_path()})')
    if 'baseUrl' in door['template']:
        served = served_models(values['baseUrl'])  # a local server answers to any id: list, then refuse
        if served is None:
            return False, f'no report (cannot list models at {values["baseUrl"]}/models)'
        if model_id not in served:
            return False, (f'no report (model {model_id} is not served at {values["baseUrl"]}; '
                           f'it serves {", ".join(served)})')
    anchor = (git(args.review_tree, 'rev-parse', 'HEAD') or '').strip()
    if not anchor:
        return False, f'no report (review tree unreadable: {args.review_tree})'
    if not ANCHOR.fullmatch(args.anchor) or not anchor.startswith(args.anchor):
        return False, f'no report (review tree HEAD {anchor[:12]} is not the anchor {args.anchor[:12]})'
    diff = git(args.review_tree, 'diff', f'{args.base}...HEAD')
    if diff is None:
        return False, f'no report (cannot diff the review tree against {args.base})'
    try:
        brief = args.brief.read_text(encoding='utf-8')
    except OSError as error:
        return False, f'no report (cannot read the brief: {error.strerror})'
    spool = None
    if 'spool' in door:  # the door's session files go to the archive spool, never to /dev/null (ticket 1383)
        spec = door['spool']
        spool = transcript_spool.spool_dir(spec['runtime'],
                                           transcript_spool.seat_id() if spec.get('per_seat') else None)
        values['spool'] = str(spool)
    diff_file = args.panel / f'{args.name}.diff'
    values['diff'] = str(diff_file)
    try:
        charter = persona(args.role)
    except (OSError, IndexError):
        return False, f'no report (no Charter in profiles/{args.role}/PROFILE.md)'
    prompt = charter + '\n\n' + LAUNCH.format(perspective=args.perspective, tree=args.review_tree,
                                              anchor=anchor, diff=diff_file, brief=brief)
    staging = args.panel / f'{args.name}.seat'
    last = args.panel / f'{args.name}.seat.last'  # a door's own output file, apart from the clock's
    promptfile = args.panel / f'{args.name}.prompt'
    try:
        command = build_command(door, run_model, prompt, last, promptfile, values)
    except ValueError as error:
        return False, f'no report ({error})'
    extra = pi_key_names(args.model.partition('/')[0]) if door.get('env_keep_pi_key') else []
    command.env = seat_env(door, extra)
    if 'seat_agent' in door:
        if not SEAT_MODEL.fullmatch(run_model):
            return False, f'no report (model id {run_model!r} is not a plain model name)'
        command.env[door['seat_agent']['home_env']] = '<disposable>'
    if args.dry_run:
        print(json.dumps({'argv': [a if a != prompt else '<prompt>' for a in command.argv],
                          'stdin': str(command.stdin) if command.stdin else None,
                          'env': sorted(command.env),  # names only, never values
                          'cwd': 'scratch' if door.get('scratch_cwd') else str(args.review_tree)}))
        return True, 'dry run, nothing launched'
    command.argv, _ = launch_line.pin(command.argv)  # claude, pi: the child's id is ours (ticket 1384)
    try:
        if spool:
            transcript_spool.mkdir_private(spool)
        for leftover in (staging, last):  # a past run's output never stands in for this one
            leftover.unlink(missing_ok=True)
        diff_file.write_text(diff, encoding='utf-8')
        if command.stdin or '<promptfile>' in door['template']:
            promptfile.write_text(prompt, encoding='utf-8')
    except OSError as error:
        return False, f'no report (cannot write beside the panel: {error.strerror})'
    cwd, scratch = args.review_tree, None
    if door.get('scratch_cwd'):
        # The CLI loads config from its cwd and git root: reviewed code must be neither.
        scratch = Path(tempfile.mkdtemp(prefix='gaze-seat-', dir='/tmp'))
        if git(scratch, 'rev-parse', '--git-dir') is not None:
            shutil.rmtree(scratch, ignore_errors=True)
            return False, 'no report (scratch directory is inside a git repository)'
        cwd = scratch
    home = None
    try:
        if 'seat_agent' in door:
            home = seat_home(door, run_model)
            command.env[door['seat_agent']['home_env']] = str(home)
        ok, outcome = seat_clock.run_seat(args.cap, staging, command.argv, cwd=cwd, stdin=command.stdin,
                                          env=command.env, replace_env=True,
                                          launch={'seat': args.name, 'spool': spool})
    except OSError as error:
        return False, f'no report (cannot prepare the seat: {error.strerror})'
    finally:
        if home:
            try:
                remove_home(home)
            except OSError:
                pass  # a leftover under /tmp is tolerable; the seat's outcome stands
        if scratch:
            shutil.rmtree(scratch, ignore_errors=True)
    log = staging.with_name(staging.name + '.log')
    stderr_lines = [line.strip() for line in log.read_text(encoding='utf-8', errors='replace').splitlines()
                    if line.strip()] if log.exists() else []
    if ok and args.runtime == 'pi' and any(UNLISTED_MODEL.match(line) for line in stderr_lines):
        # A local provider answers to any id and the CLI exits 0: the run is not the pinned model's.
        for leftover in (staging, last):
            leftover.unlink(missing_ok=True)
        return False, f'no report (the provider does not list {args.model}; the CLI fell back to a custom id)'
    wrote_last = last.exists() and last.read_text(encoding='utf-8', errors='replace').strip()
    keep_raw(args.name, last if wrote_last else staging)

    def failed(reason: str) -> tuple[bool, str]:
        # The panel dies with the review tree; the status line is the durable record and reaches
        # permanent notes, so it carries only fields the harness owns: never CLI stderr or report text
        # (both stay in the local `.log` and report file; ticket 1378).
        return False, f'{reason[:-1]}; door={args.runtime}, model={args.model})'

    if not ok and not (wrote_last and outcome.startswith('no report (empty output')):
        return failed(outcome)  # a nonzero exit stays a failure even when the door wrote its file
    if not ok:
        outcome = 'reported in ' + outcome.rsplit(', ', 1)[-1].rstrip(')')
    text = last if wrote_last else staging
    worker = f'worker: model={args.model} · family={args.family} · runtime={args.runtime} · door=headless'
    answer = answer_of(door, text.read_text(encoding='utf-8', errors='replace'))
    raw_answer = answer
    answer, unwrapped = unwrap_header(answer)
    report = stamp(answer, worker)
    if unwrapped:
        # the seat's answer as received, kept beside the report: the normalisation is the only edit
        args.panel.joinpath(f'{args.name}.md.raw').write_text(raw_answer, encoding='utf-8')
        outcome += '; header unwrapped from a Markdown block'
    for leftover in (staging, last):
        leftover.unlink(missing_ok=True)
    if not report:
        return failed('no report (empty output)')
    if refusal(report):
        return failed('no report (seat refused: NOT-RUN)')
    if bad := reach_refusal(report):
        return failed(f'no report (seat reach: {bad})')
    out = args.panel / f'{args.name}.md'
    part = out.with_name(out.name + '.part')
    part.write_text(report, encoding='utf-8')
    part.rename(out)
    return True, outcome


# Prefix- or context-anchored on purpose: no entropy or length rule, so UUID session ids and model ids survive.
SCRUB_PATTERNS = tuple(re.compile(p, re.IGNORECASE) for p in (
    r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+',                                    # email
    r'\b(?:sk|ghp|gho|ghs|github_pat|xox[a-z]|AKIA)[-_][\w*-]{8,}|\bAKIA[0-9A-Z]{12,}',  # vendor keys, masked too
    r'\b(?:Bearer|Basic)\s+\S+',                                         # auth header value
    r'\beyJ[\w-]{8,}\.[\w-]+(?:\.[\w-]+)?',                               # JWT
    r'\borg-[\w-]{4,}',                                                   # organisation id
    r'\b[\w-]*(?:key|token|secret|password|account[ _-]?id)(?:\\?["\'])?[ \t]*[:=][ \t]*\S+',  # key=value: JSON-quoted, backslash-escaped, spaced label; never across a newline
    r'/home/[^/\s|]+',                                                    # login in a home path
))


def scrub(text: str) -> str:
    """Replace emails, key- or token-shaped strings, organisation ids and home logins with `<redacted>`."""
    for pattern in SCRUB_PATTERNS:
        text = pattern.sub('<redacted>', text)
    return text


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='mode', required=True)
    sub.add_parser('consent', help='print the manifest line declaring cross-family spend')
    run = sub.add_parser('launch', help='launch one seat and file its report')
    run.add_argument('--runtime', required=True, help='launch_doors key: claude-code, codex, pi')
    run.add_argument('--model', required=True, help='model pinned on the door, from the route skill; a pi model ends in :<thinking level>')
    run.add_argument('--family', required=True, help='model family the plan names for this seat')
    run.add_argument('--home-family', required=True, help='family of the session running gaze')
    run.add_argument('--role', choices=ROLES, default='code-reviewer',
                     help='profile whose Charter is the seat persona (profiles/<role>/PROFILE.md)')
    run.add_argument('--perspective', required=True)
    run.add_argument('--panel', type=Path, required=True, help='<review_tree>/.panel/<pr>/')
    run.add_argument('--name', required=True, help='plan item name; report is <panel>/<name>.md')
    run.add_argument('--review-tree', type=Path, required=True)
    run.add_argument('--brief', type=Path, required=True, help='intent, exit criteria, file roster')
    run.add_argument('--anchor', required=True, help='expected HEAD of the review tree')
    run.add_argument('--base', required=True, help='base ref; the seat reads the diff <base>...HEAD')
    run.add_argument('--cap', type=int, default=seat_clock.DEFAULT_CAP_S, help='wall-clock cap, seconds')
    run.add_argument('--routes', type=Path, default=ROUTES)
    run.add_argument('--dry-run', action='store_true', help='print the command, launch nothing')
    args = parser.parse_args(argv)
    if args.mode == 'consent':
        print(consent_line(config_path()))
        return 0
    ok, outcome = launch(args)
    if args.dry_run and ok:
        return 0
    line = f'{args.name}: {outcome}'
    try:
        (args.panel / f'{args.name}.md.status').write_text(line + '\n')
    except OSError:
        pass  # the printed line still names the seat
    print(line)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""Launch one gaze review seat as a detached headless CLI (ticket 1256).

`launch` builds the seat's command from the runtime's headless door in
`skills/route/routes.json` (`launch_doors.<runtime>.headless`: its `template`,
with the model pinned, and its `seat_rails` flags: read tools only, no shell
and no write tool, where the CLI offers an allowlist; codex holds the seat by
its read-only sandbox instead). It writes the diff `<base>...HEAD` beside the
report, since a seat without a shell cannot run git, embeds the seat contract
in the prompt, pins the cwd to the review tree and runs it under
`seat_clock.run_seat` with a hard cap. A headless process does not nest inside
the caller's agent tree, so the same door works from a subagent on every
runtime.

The report lands as `<panel>/<name>.md`, written `.part` then renamed, its
first line `worker: model=<pin> · family=<family> · runtime=<rt> ·
door=headless` set by the launcher: the pin is what ran, and a CLI's own
self-report of its model is not trusted. Whatever stops a seat (no door, a
family the door cannot serve, no consent, an unreadable or moved review tree,
a start failure, a nonzero exit, empty output, a `NOT-RUN:` refusal, the
cap) prints and saves
`<name>: no report (<reason>)` to `<panel>/<name>.md.status` and writes no
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
the plan.
"""

import argparse
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('seat_clock', HERE / 'seat_clock.py')
seat_clock = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(seat_clock)  # a sibling script, not a package

ROUTES = HERE.parent / 'skills' / 'route' / 'routes.json'
CONSENT_KEY = 'cross_family_spend'
MODEL_FLAGS = ('--model', '-m')
PLACEHOLDER = re.compile(r'<[^<>]+>.*')
ANCHOR = re.compile(r'[0-9a-f]{7,40}')

CONTRACT = """\
You are one read-only code-review seat of a gaze panel, launched headless.

Perspective: {perspective}. Judge against this one perspective only.
Review tree: {tree}, anchored at HEAD {anchor}.

The change under review is the diff in {diff}; read it first, then the
files it touches under the review tree.

Reach rails:
- Read the tree only with your read tools, or, where you have a shell, as
  `git -C "{tree}" ...`.
- Never overwrite the working tree: no `git checkout <ref> -- <path>`, no
  `git restore .`, no `git reset --hard`. Read another version with
  `git show <ref>:<path>`.
- If the tree is unreachable or its HEAD is not {anchor}, reply with one line
  `NOT-RUN: <reason>` and stop; never fall back to another directory.
- Write no file, post nothing, commit and push nothing, read no credentials.

Report: your final message is your report; the launcher files it. Open it
with `worker: model=<id> · family=<family>`. Give each finding its evidence
from the diff and a confidence (high / medium / low). Tag every non-blocking
finding with exactly one of `verifiable:` (evidence attached now: a failing
test id, command output or SHA:file:line), `consider:` (a hypothesis) or
`nofollow:` (recorded, not pursued); blocking findings carry no tag. End with
one line `verdict: clear`, `verdict: concerns` or `verdict: blocking`. An
empty changed-file list never yields `clear`.

The brief from gaze (intent, exit criteria, changed-file roster) follows.

{brief}
"""


@dataclass
class Command:
    argv: list[str]
    stdin: Path | None


def load_doors(routes: Path) -> dict:
    doors = json.loads(routes.read_text(encoding='utf-8'))['launch_doors']
    return {name: door['headless'] for name, door in doors.items()
            if isinstance(door, dict) and 'headless' in door}


def build_command(door: dict, model: str, prompt: str, outfile: Path, promptfile: Path) -> Command:
    """Fill the door's template; raise ValueError when it cannot carry this seat."""
    if 'seat_rails' not in door:
        raise ValueError('door declares no seat_rails, so it cannot hold a seat read-only')
    tokens = shlex.split(door['template'])
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
    return Command(argv[:lead] + list(door['seat_rails']) + argv[lead:], stdin)


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


def git(tree: Path, *args: str) -> str | None:
    result = subprocess.run(['git', '-C', str(tree), *args], capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def stamp(text: str, worker: str) -> str:
    """Put the launcher's worker line first, replacing any the seat wrote."""
    lines = text.splitlines()
    body = [line for line in lines if line.strip()]
    if body and body[0].strip().strip('*').strip().lower().startswith('worker:'):
        drop = lines.index(body[0])
        lines = lines[:drop] + lines[drop + 1:]
    rest = '\n'.join(lines).strip('\n')
    return f'{worker}\n{rest}\n' if rest.strip() else ''


def refusal(report: str) -> str | None:
    """The seat's `NOT-RUN:` line, in a report that reaches no verdict."""
    lines = [line.strip().strip('*`').strip() for line in report.splitlines() if line.strip()]
    if any(line.lower().startswith('verdict:') for line in lines):
        return None
    return next((line for line in lines if line.upper().startswith('NOT-RUN')), None)


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
    if provider.lower() != args.home_family.lower() and \
            provider.lower() not in (f.lower() for f in consented(config_path())):
        return False, (f'no report (no consent for cross-family spend on {provider}; '
                       f'{CONSENT_KEY} in {config_path()})')
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
    diff_file = args.panel / f'{args.name}.diff'
    prompt = CONTRACT.format(perspective=args.perspective, tree=args.review_tree, anchor=anchor,
                             diff=diff_file, brief=brief)
    staging = args.panel / f'{args.name}.seat'
    last = args.panel / f'{args.name}.seat.last'  # a door's own output file, apart from the clock's
    promptfile = args.panel / f'{args.name}.prompt'
    try:
        command = build_command(door, args.model, prompt, last, promptfile)
    except ValueError as error:
        return False, f'no report ({error})'
    if args.dry_run:
        print(json.dumps({'argv': [a if a != prompt else '<prompt>' for a in command.argv],
                          'stdin': str(command.stdin) if command.stdin else None,
                          'cwd': str(args.review_tree)}))
        return True, 'dry run, nothing launched'
    try:
        for leftover in (staging, last):  # a past run's output never stands in for this one
            leftover.unlink(missing_ok=True)
        diff_file.write_text(diff, encoding='utf-8')
        if command.stdin:
            promptfile.write_text(prompt, encoding='utf-8')
    except OSError as error:
        return False, f'no report (cannot write beside the panel: {error.strerror})'
    ok, outcome = seat_clock.run_seat(args.cap, staging, command.argv, cwd=args.review_tree,
                                      stdin=command.stdin)
    wrote_last = last.exists() and last.read_text(encoding='utf-8', errors='replace').strip()
    if not ok and not (wrote_last and outcome.startswith('no report (empty output')):
        return False, outcome  # a nonzero exit stays a failure even when the door wrote its file
    if not ok:
        outcome = 'reported in ' + outcome.rsplit(', ', 1)[-1].rstrip(')')
    text = last if wrote_last else staging
    worker = f'worker: model={args.model} · family={args.family} · runtime={args.runtime} · door=headless'
    report = stamp(text.read_text(encoding='utf-8', errors='replace'), worker)
    for leftover in (staging, last):
        leftover.unlink(missing_ok=True)
    if not report:
        return False, 'no report (empty output)'
    if refused := refusal(report):
        return False, f'no report (seat refused: {refused})'
    out = args.panel / f'{args.name}.md'
    part = out.with_name(out.name + '.part')
    part.write_text(report, encoding='utf-8')
    part.rename(out)
    return True, outcome


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='mode', required=True)
    sub.add_parser('consent', help='print the manifest line declaring cross-family spend')
    run = sub.add_parser('launch', help='launch one seat and file its report')
    run.add_argument('--runtime', required=True, help='launch_doors key: claude-code, codex, pi')
    run.add_argument('--model', required=True, help='model pinned on the door, from the route skill')
    run.add_argument('--family', required=True, help='model family the plan names for this seat')
    run.add_argument('--home-family', required=True, help='family of the session running gaze')
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

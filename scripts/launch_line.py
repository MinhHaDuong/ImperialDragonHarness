#!/usr/bin/env python3
"""One launch line per headless child (ticket 1384; memo conception/2026-10-31-monitoring-redesign.md 4.3).

The one link transcripts cannot reconstruct is which session launched which headless child. Both
launchers (`seat_clock.run_seat`, `manuscript_review.execute_stage`) call `record` once per child; it
appends one JSON line to `<ARCHIVE_ROOT>/raw/<host>/launches.jsonl` (the path of `transcript_spool`):

    ts_start ts_end host parent_runtime parent_session child_runtime child_session seat cwd unit exit

The child id is never a start-time join. It is the id the launcher pinned (`--session-id`), the session
file the launcher gave the child (the spool of ticket 1383), or what the child printed (Codex); when none
holds, the literal `not captured`. The parent id is the runtime's own (`runtime.py session id`), else
`not exported`. A write failure warns once on stderr and returns False; it never raises.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOT_CAPTURED, NOT_EXPORTED = 'not captured', 'not exported'
CODEX_ID = re.compile(r'^session id: ([0-9A-Za-z-]+)', re.M)


def _load(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, HERE / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def launches_path() -> Path:
    spool = _load('transcript_spool')
    return spool.raw_dir() / 'launches.jsonl'


def iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def parent(env=None) -> tuple[str, str]:
    """(runtime, session id) of the launching session; `unknown` / `not exported` when unreadable."""
    env = os.environ if env is None else env
    try:
        runtime = _load('runtime')
        rt = runtime.detect(env)
    except Exception:
        return 'unknown', NOT_EXPORTED
    return rt, runtime.session_id(rt, env) or NOT_EXPORTED


def unit(env=None, cwd=None) -> str:
    """$IDH_UNIT, else the git branch of the launcher's cwd, else `-`."""
    env = os.environ if env is None else env
    if env.get('IDH_UNIT'):
        return env['IDH_UNIT']
    try:
        out = subprocess.run(['git', 'branch', '--show-current'], cwd=cwd, capture_output=True, text=True,
                             timeout=5, check=False).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        out = ''
    return out or '-'


def pin(argv: list[str]) -> tuple[list[str], str | None]:
    """Add `--session-id <uuid>` right after the CLI name (claude, pi); nothing else is edited."""
    if Path(argv[0]).name not in ('claude', 'pi') or '--session-id' in argv:
        return argv, None
    sid = str(uuid.uuid4())
    return argv[:1] + ['--session-id', sid] + argv[1:], sid


def child_from(argv: list[str], log: Path | None = None, spool: Path | None = None) -> tuple[str, str]:
    """(child runtime, child session) from what the launcher gave or the child printed."""
    runtime = Path(argv[0]).name if argv else 'unknown'
    if '--session-id' in argv[:-1]:
        sid = argv[argv.index('--session-id') + 1]
        if runtime == 'pi':  # the id names a file under the spool: <timestamp>_<id>.jsonl
            found = sorted(spool.glob(f'*{sid}*.jsonl')) if spool else []
            return runtime, str(found[-1]) if found else NOT_CAPTURED
        return runtime, sid
    if runtime == 'aider' and spool:
        return runtime, str(spool / 'chat.md')
    if runtime == 'vibe' and spool:
        return runtime, str(spool)
    if runtime == 'codex' and log and log.exists():
        found = CODEX_ID.findall(log.read_text(encoding='utf-8', errors='replace'))
        if found:
            return runtime, found[0]
    return runtime, NOT_CAPTURED


def record(*, seat: str, child_runtime: str, child_session: str, ts_start: float, ts_end: float,
           exit, cwd, env=None, path: Path | None = None, out=None) -> bool:
    """Append one line; True when written. Never raises."""
    try:
        spool = _load('transcript_spool')
        prt, psid = parent(env)
        line = {'ts_start': iso(ts_start), 'ts_end': iso(ts_end), 'host': spool.host(),
                'parent_runtime': prt, 'parent_session': psid, 'child_runtime': child_runtime,
                'child_session': child_session, 'seat': seat, 'cwd': str(cwd or os.getcwd()),
                'unit': unit(env), 'exit': exit}
        if out is not None:  # the report path: names the review's panel (ticket 1399)
            line['out'] = str(Path(out).resolve())
        path = path or launches_path()
        spool.mkdir_private(path.parent)
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(fd, (json.dumps(line) + '\n').encode())  # one write: parallel seats do not interleave
        finally:
            os.close(fd)
        return True
    except Exception as error:
        print(f'launch_line: cannot append the launch line: {error}', file=sys.stderr)
        return False

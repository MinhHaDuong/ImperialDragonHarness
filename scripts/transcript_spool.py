#!/usr/bin/env python3
"""Where transcripts live, and where headless doors spool the ones the CLI would drop.

One home for the path convention of ticket 1383 (memo conception/2026-10-31-monitoring-redesign.md
section 4.2). `transcript_archive.py` reads it; the headless doors (gaze_seat.py, the Pi subagent
link) write into `spool_dir`; ticket 1384 imports it. Stdlib only.

    <ARCHIVE_ROOT>/transcripts/<host>/<runtime>/<path relative to its source root>.zst
    <ARCHIVE_ROOT>/spool/<host>/<runtime>[/<seat id>]/...   (session files of doors that keep none)

`archive_root()` and `live_roots()` read the environment at call time, so a test or a caller that
sets IDH_ARCHIVE_ROOT / CLAUDE_CONFIG_DIR / CODEX_HOME / PI_CODING_AGENT_DIR afterwards is honoured;
`ARCHIVE_ROOT` and `LIVE_ROOTS` are the import-time snapshots.

CLI (for shell callers): `transcript_spool.py spool <runtime> [--seat]` prints, and creates, the dir.
"""
from __future__ import annotations

import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

SPOOL_RUNTIMES = ('pi', 'aider', 'vibe')  # doors whose CLI keeps no session file of its own
ARCHIVED_RUNTIMES = ('claude', 'codex', 'pi', 'aider', 'vibe')


def archive_root() -> Path:
    return Path(os.environ.get('IDH_ARCHIVE_ROOT') or Path.home() / 'archive')


def live_roots() -> dict[str, Path]:
    home = Path.home()
    claude = os.environ.get('CLAUDE_CONFIG_DIR') or home / '.claude'
    codex = os.environ.get('CODEX_HOME') or home / '.codex'
    pi = os.environ.get('PI_CODING_AGENT_DIR') or home / '.pi' / 'agent'
    return {'claude': Path(claude) / 'projects', 'codex': Path(codex) / 'sessions',
            'pi': Path(pi) / 'sessions'}


ARCHIVE_ROOT = archive_root()
LIVE_ROOTS = live_roots()


def host() -> str:
    return socket.gethostname().split('.')[0]


def archive_dir(runtime: str) -> Path:
    return archive_root() / 'transcripts' / host() / runtime


def spool_dir(runtime: str, seat: str | None = None, create: bool = False) -> Path:
    path = archive_root() / 'spool' / host() / runtime
    if seat:
        path = path / seat
    if create:
        path.mkdir(parents=True, exist_ok=True, mode=0o700)
    return path


def seat_id() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}'


def source_roots(runtime: str) -> list[Path]:
    """Every directory whose files the archive copies for `runtime`."""
    roots = [live_roots()[runtime]] if runtime in live_roots() else []
    if runtime in SPOOL_RUNTIMES:
        roots.append(spool_dir(runtime))
    return roots


def main(argv: list[str]) -> int:
    if len(argv) >= 2 and argv[0] == 'spool' and argv[1] in ARCHIVED_RUNTIMES:
        seat = seat_id() if '--seat' in argv[2:] else None
        print(spool_dir(argv[1], seat, create=True))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

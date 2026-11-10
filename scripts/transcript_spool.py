#!/usr/bin/env python3
"""Where transcripts live, and where headless doors spool the ones the CLI would drop.

One home for the path convention of ticket 1383 (memo design/2026-10-31-monitoring-redesign.md
section 4.2). `transcript_archive.py` reads it; the headless doors (gaze_seat.py, the Pi subagent
link) write into `spool_dir`; ticket 1384 imports it. Stdlib only.

    <ARCHIVE_ROOT>/raw/<host>/<runtime>/<path relative to its source root>.zst
    <ARCHIVE_ROOT>/raw/<host>/launches.jsonl
    <ARCHIVE_ROOT>/spool/<host>/<runtime>[/<seat id>]/...   (session files of doors that keep none)

ARCHIVE_ROOT is the `agent-sessions` directory of the datasets/ours folder (ticket 1391; location from
DATASETS_DIR, ticket 1402); its README
is scripts/agent-sessions-README.md. `archive_root()` and `live_roots()` read the environment at call time, so a test or a caller that
sets IDH_ARCHIVE_ROOT / CLAUDE_CONFIG_DIR / CODEX_HOME / PI_CODING_AGENT_DIR afterwards is honoured;
`LIVE_ROOTS` is the import-time snapshot; the archive root has none, since it may be unknown.

One definition of the roots (ticket 1520). `NAMED_ROOTS` lists, per runtime, each root by name; the
archive, the timeline and the audit's readers all take their roots from it, so a root one of them reads is
a root the archive copies:

    claude   projects
    codex    sessions, archived_sessions   (both under the Codex home; the second is flat)
    pi       live, spool                   (the spool is flat: Pi's spool is `per_seat: false` in routes.json)
    aider    spool
    vibe     spool

`named_roots(runtime, codex_home=None)` returns `[(name, Path | RuntimeError)]`, each root resolved on its
own: an unknown archive root fails the spool entries only, never a live root. `named_root(runtime, name)`
returns one Path or raises RuntimeError. `source_roots(runtime)` is the resolved paths, errors skipped.
`codex_home()` is the Codex home. `source_of(runtime, relpath)` is the pure inverse for an archived file:
the name of the root a relative path (below `raw/<host>/<runtime>/`, `.zst` optional) was copied from.
`one_per_rollout(paths)` keeps one path per Codex rollout file name (`.zst` ignored), the one with the
greatest mtime, then size, since the same rollout can sit in `sessions/` as a frozen prefix and in
`archived_sessions/`, and in the archive under both; callers that count sessions apply it to Codex.

CLI (for shell callers): `transcript_spool.py root` prints the root; `transcript_spool.py spool <runtime> [--seat]` prints, and creates, the dir.
"""
from __future__ import annotations

import os
import socket
import sys
from datetime import datetime, timezone
from collections.abc import Callable
from pathlib import Path

SPOOL_RUNTIMES = ('pi', 'aider', 'vibe')  # doors whose CLI keeps no session file of its own
ARCHIVED_RUNTIMES = ('claude', 'codex', 'pi', 'aider', 'vibe')


ENV_FILE = Path('~/.config/environment.d/50-datasets.conf')  # declares DATASETS_DIR on every host
STORE = Path('ours/agent-sessions')


def _datasets_dir_from_file() -> str | None:
    """DATASETS_DIR from the environment.d file: environment.d reaches systemd user services but not
    interactive shells, subagents or ssh commands, hence this fallback."""
    try:
        lines = ENV_FILE.expanduser().read_text().splitlines()
    except OSError:
        return None
    value = None
    for line in lines:
        key, sep, val = line.strip().partition('=')
        if sep and key.strip() == 'DATASETS_DIR':
            value = val.strip().strip('"\'') or None
    return value


def archive_root() -> Path:
    """The agent-sessions directory: IDH_ARCHIVE_ROOT, else $DATASETS_DIR/ours/agent-sessions, else
    DATASETS_DIR parsed from ~/.config/environment.d/50-datasets.conf, else an error. An empty value
    counts as unset; no directory is probed and no hostname is consulted."""
    if os.environ.get('IDH_ARCHIVE_ROOT'):
        return Path(os.environ['IDH_ARCHIVE_ROOT'])
    datasets = os.environ.get('DATASETS_DIR') or _datasets_dir_from_file()
    if not datasets:
        raise RuntimeError('archive root unknown: set IDH_ARCHIVE_ROOT or DATASETS_DIR, or declare '
                           'DATASETS_DIR in ~/.config/environment.d/50-datasets.conf')
    return Path(datasets) / STORE


def claude_home() -> Path:
    return Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude')


def codex_home() -> Path:
    return Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')


def pi_home() -> Path:
    return Path(os.environ.get('PI_CODING_AGENT_DIR') or Path.home() / '.pi' / 'agent')


def live_roots() -> dict[str, Path]:
    return {'claude': claude_home() / 'projects', 'codex': codex_home() / 'sessions',
            'pi': pi_home() / 'sessions'}


LIVE_ROOTS = live_roots()


def host() -> str:
    return socket.gethostname().split('.')[0]


def mkdir_private(path: Path) -> None:
    """Create path and its missing parents below the root, every one 0o700 (GDPR-sensitive data)."""
    missing = [p for p in (path, *path.parents) if not p.exists()]
    for p in reversed(missing):
        p.mkdir(mode=0o700, exist_ok=True)
        p.chmod(0o700)


def raw_dir(host_name: str | None = None) -> Path:
    """The raw store of one host (default: this one); launches.jsonl sits directly in it."""
    return archive_root() / 'raw' / (host_name or host())


def archive_dir(runtime: str) -> Path:
    return raw_dir() / runtime


def spool_dir(runtime: str, seat: str | None = None, create: bool = False) -> Path:
    path = archive_root() / 'spool' / host() / runtime
    if seat:
        path = path / seat
    if create:
        mkdir_private(path)
    return path


def seat_id() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + f'-{os.getpid()}'


# Every root the archive copies and the audit reads: runtime -> root name -> resolver. Add a root here only.
NAMED_ROOTS: dict[str, dict[str, Callable[[], Path]]] = {
    'claude': {'projects': lambda: claude_home() / 'projects'},
    'codex': {'sessions': lambda: codex_home() / 'sessions',
              'archived_sessions': lambda: codex_home() / 'archived_sessions'},
    'pi': {'live': lambda: pi_home() / 'sessions', 'spool': lambda: spool_dir('pi')},
    'aider': {'spool': lambda: spool_dir('aider')},
    'vibe': {'spool': lambda: spool_dir('vibe')},
}


def named_roots(runtime: str, codex_home: Path | str | None = None) -> list[tuple[str, Path | RuntimeError]]:
    """Each root of `runtime` by name, resolved on its own. `codex_home` replaces the Codex home."""
    out: list[tuple[str, Path | RuntimeError]] = []
    for name, resolve in NAMED_ROOTS.get(runtime, {}).items():
        try:
            out.append((name, Path(codex_home) / name if codex_home and runtime == 'codex' else resolve()))
        except RuntimeError as error:  # archive root unknown: this root only
            out.append((name, error))
    return out


def named_root(runtime: str, name: str) -> Path:
    """One root; raises RuntimeError when it cannot be resolved, KeyError for an unknown name."""
    root = dict(named_roots(runtime))[name]
    if isinstance(root, RuntimeError):
        raise root
    return root


def source_roots(runtime: str) -> list[Path]:
    """Every directory whose files the archive copies for `runtime`."""
    return [root for _, root in named_roots(runtime) if isinstance(root, Path)]


def source_of(runtime: str, relpath: str | Path) -> str:
    """The name of the root an archived file came from, from its path below raw/<host>/<runtime>/."""
    depth = len(Path(str(relpath).removesuffix('.zst')).parts)
    if runtime == 'codex':
        return 'archived_sessions' if depth == 1 else 'sessions'
    if runtime == 'pi':
        return 'spool' if depth == 1 else 'live'
    names = list(NAMED_ROOTS[runtime])
    if len(names) != 1:
        raise ValueError(f'{runtime}: roots cannot be told apart by path')
    return names[0]


def one_per_rollout(paths) -> list[Path]:
    """One path per Codex rollout file name (a `.zst` suffix ignored): greatest mtime, then size."""
    best: dict[str, tuple[tuple[int, int], Path]] = {}
    for path in paths:
        path = Path(path)
        try:
            st = path.stat()
        except OSError:
            continue
        rank = (st.st_mtime_ns, st.st_size)
        key = path.name.removesuffix('.zst')
        if key not in best or rank > best[key][0]:
            best[key] = (rank, path)
    return sorted(path for _, path in best.values())


def main(argv: list[str]) -> int:
    try:
        return _main(argv)
    except RuntimeError as error:
        print(f'transcript_spool: {error}', file=sys.stderr)
        return 1


def _main(argv: list[str]) -> int:
    if argv == ['root']:
        print(archive_root())
        return 0
    if len(argv) >= 2 and argv[0] == 'spool' and argv[1] in ARCHIVED_RUNTIMES:
        seat = seat_id() if '--seat' in argv[2:] else None
        print(spool_dir(argv[1], seat, create=True))
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

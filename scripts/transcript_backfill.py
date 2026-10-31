#!/usr/bin/env python3
"""One-off backfill of the transcript archive from cadens' raw store (ticket 1391).

    transcript_backfill.py SRC DEST [--level N] [--jobs N] [--dry-run]

SRC is a plain-JSONL mirror of one host's `~/.claude/projects` (cadens' `raw/claude-local/<host>/`),
DEST the archive's `raw/<host>/claude/`. Every SRC file absent from DEST by relative path is added
as `<rel>.zst`; where both exist the larger one is kept (cadens copies with `rsync --ignore-existing`,
so its copy of a grown file is truncated, while it also holds files already pruned from the live
tree). The added copy carries the SRC mtime, files 600, directories 700. SRC is only read. An
unreadable entry (broken link, permission) is skipped and counted. Prints one count line per class.
"""
from __future__ import annotations

import argparse
import os
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SUFFIX = '.zst'


def decompressed_size(path: Path) -> int:
    process = subprocess.Popen(['zstd', '-dc', str(path)], stdout=subprocess.PIPE)
    total = 0
    while chunk := process.stdout.read(1 << 20):
        total += len(chunk)
    process.wait()
    if process.returncode:
        raise OSError(f'zstd -d failed on {path}')
    return total


def compress(src: Path, st: os.stat_result, dest: Path, level: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = dest.with_name(dest.name + '.tmp')
    try:
        subprocess.run(['zstd', '-q', '-T1', f'-{level}', '-f', '-o', str(tmp), str(src)], check=True)
        os.chmod(tmp, 0o600)
        os.utime(tmp, ns=(st.st_atime_ns, st.st_mtime_ns))
        os.replace(tmp, dest)
    finally:
        tmp.unlink(missing_ok=True)


def classify(src_root: Path, dest_root: Path, path: Path):
    """('unreadable'|'added'|'replaced'|'kept', path, stat, dest)."""
    try:
        st = path.stat()  # follows links: a broken one raises
        if not stat.S_ISREG(st.st_mode) or not os.access(path, os.R_OK):
            return 'unreadable', path, None, None
    except OSError:
        return 'unreadable', path, None, None
    dest = dest_root / (path.relative_to(src_root).as_posix() + SUFFIX)
    if not dest.exists():
        return 'added', path, st, dest
    return ('replaced' if st.st_size > decompressed_size(dest) else 'kept'), path, st, dest


def walk(root: Path):
    for base, dirs, names in os.walk(root):
        dirs.sort()
        for name in sorted(names):
            yield Path(base) / name


def run(src_root: Path, dest_root: Path, level: int, jobs: int, dry_run: bool) -> int:
    counts = {k: [0, 0] for k in ('unreadable', 'added', 'replaced', 'kept')}
    failed = 0

    def one(path: Path):
        kind, path, st, dest = classify(src_root, dest_root, path)
        if kind in ('added', 'replaced') and not dry_run:
            compress(path, st, dest, level)
        return kind, (st.st_size if st else 0)

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for future in [pool.submit(one, p) for p in walk(src_root)]:
            try:
                kind, size = future.result()
            except (OSError, subprocess.CalledProcessError) as error:
                failed += 1
                print(f'transcript_backfill: {error}', file=sys.stderr)
                continue
            counts[kind][0] += 1
            counts[kind][1] += size
    prefix = 'would be ' if dry_run else ''
    print(f'source: {src_root}  archive: {dest_root}')
    for kind, (n, b) in counts.items():
        label = kind if kind in ('unreadable', 'kept') else prefix + kind
        print(f'{label}: {n} files {b} bytes')
    print(f'failed: {failed}')
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('src', type=Path)
    parser.add_argument('dest', type=Path)
    parser.add_argument('--level', type=int, default=10)
    parser.add_argument('--jobs', type=int, default=8)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    os.umask(0o077)
    if not args.src.is_dir():
        print(f'transcript_backfill: {args.src} is not a directory', file=sys.stderr)
        return 2
    return run(args.src, args.dest, args.level, args.jobs, args.dry_run)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

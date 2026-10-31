#!/usr/bin/env python3
"""Compress every runtime's transcripts into the archive (ticket 1383).

One zstd file per source file, original relative path kept, contents unmodified, under
`<archive>/raw/<host>/<runtime>/` (path convention: transcript_spool.py). A source
touched within the last day is skipped (it may still grow). The archived copy carries its
source's mtime: a transcript only appends, appending moves mtime, so "dest mtime equals source
mtime" means unchanged and anything else is copied again. Plain files only, never a manifest.

    transcript_archive.py [--level N] [--now EPOCH] [--min-age SECONDS] [--verify]

`--verify` prints `eligible: N files B bytes` and `archived: N files B bytes` (B read back by
decompressing every archived copy) and exits 1 when they differ.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import transcript_spool as spool  # noqa: E402

DAY = 86400
SUFFIX = '.zst'


def eligible(root: Path, now: float, min_age: float):
    """Yield (path, stat) for each plain file under root untouched for min_age seconds."""
    for base, dirs, names in os.walk(root):
        dirs.sort()
        for name in sorted(names):
            path = Path(base) / name
            try:
                st = path.lstat()
            except OSError:
                continue
            if path.is_symlink() or not path.is_file() or now - st.st_mtime < min_age:
                continue
            yield path, st


def destination(runtime: str, root: Path, path: Path) -> Path:
    dest = spool.archive_dir(runtime) / path.relative_to(root)
    return dest.with_name(dest.name + SUFFIX)


def current(dest: Path, st: os.stat_result) -> bool:
    try:
        return dest.stat().st_mtime_ns == st.st_mtime_ns
    except OSError:
        return False


def archive_one(path: Path, st: os.stat_result, dest: Path, level: int) -> bool:
    """Compress path to dest via a temp file; False when the source moved under us."""
    spool.mkdir_private(dest.parent)
    tmp = dest.with_name(dest.name + '.tmp')
    try:
        subprocess.run(['zstd', '-q', '-T1', f'-{level}', '-f', '-o', str(tmp), str(path)], check=True)
        after = path.stat()
        if (after.st_mtime_ns, after.st_size) != (st.st_mtime_ns, st.st_size):
            return False  # grew while being read; the next run takes it
        os.chmod(tmp, 0o600)
        os.utime(tmp, ns=(st.st_atime_ns, st.st_mtime_ns))
        os.replace(tmp, dest)
        return True
    finally:
        tmp.unlink(missing_ok=True)


def decompressed_size(dest: Path) -> int:
    process = subprocess.Popen(['zstd', '-dc', str(dest)], stdout=subprocess.PIPE)
    total = 0
    while chunk := process.stdout.read(1 << 20):
        total += len(chunk)
    process.wait()
    if process.returncode:
        raise OSError(f'zstd -d failed on {dest}')
    return total


def run(now: float, min_age: float, level: int, do_verify: bool) -> int:
    copied = kept = failed = 0
    want_files = want_bytes = have_files = have_bytes = 0
    for runtime in spool.ARCHIVED_RUNTIMES:
        for root in spool.source_roots(runtime):
            if not root.is_dir():
                continue
            for path, st in eligible(root, now, min_age):
                dest = destination(runtime, root, path)
                want_files += 1
                want_bytes += st.st_size
                try:
                    if current(dest, st):
                        kept += 1
                    elif archive_one(path, st, dest, level):
                        copied += 1
                    else:
                        failed += 1
                        continue
                    if do_verify:
                        have_files += 1
                        have_bytes += decompressed_size(dest)
                except (OSError, subprocess.CalledProcessError) as error:
                    failed += 1
                    print(f'transcript_archive: {path}: {error}', file=sys.stderr)
    print(f'copied: {copied} files; unchanged: {kept}; failed: {failed}')
    if do_verify:
        print(f'eligible: {want_files} files {want_bytes} bytes')
        print(f'archived: {have_files} files {have_bytes} bytes')
        return 0 if (want_files, want_bytes) == (have_files, have_bytes) and not failed else 1
    return 1 if failed else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('--level', type=int, default=int(os.environ.get('IDH_ARCHIVE_LEVEL', '10')))
    parser.add_argument('--now', type=float, default=None, help='epoch seconds standing for "now"')
    parser.add_argument('--min-age', type=float, default=DAY)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args(argv)
    os.umask(0o077)
    return run(args.now if args.now is not None else time.time(), args.min_age, args.level, args.verify)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

"""A copy of the checkout's TRACKED tree, for tests that run the harness itself.

Ticket 0989. `idh install | check` expand `$IDH_ROOT` to the checkout the code
runs from. Run from the developer's checkout, that root carries untracked
content — the private-overlay links skills/{email,infrastructure,directory} —
which a fixture HOME cannot match, so the suite went red on one machine and
green in CI. Tests that execute bin/idh or adapters/*.py run them from this
copy instead: what the suite sees is what git tracks, on every machine.

Working-tree content of tracked files is copied as it stands (a test run sees
the edits under test); tracked symlinks stay symlinks. One copy per session.
"""

import atexit
import functools
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from child_env import child_env

SOURCE = Path(__file__).resolve().parents[1]


@functools.lru_cache(maxsize=1)
def tracked_checkout() -> Path:
    listed = (
        subprocess.run(
            ["git", "-C", str(SOURCE), "ls-files", "-z"],
            capture_output=True,
            check=True,
            env=child_env(),
        )
        .stdout.decode()
        .split("\0")
    )
    root = Path(tempfile.mkdtemp(prefix="idh-tracked-")).resolve()
    atexit.register(shutil.rmtree, root, ignore_errors=True)
    for rel in filter(None, listed):
        src, dest = SOURCE / rel, root / rel
        if not os.path.lexists(src):
            continue  # deleted in the working tree: absent here too
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            dest.symlink_to(os.readlink(src))
        else:
            shutil.copy2(src, dest)
    return root

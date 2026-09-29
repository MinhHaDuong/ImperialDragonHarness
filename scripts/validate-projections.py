#!/usr/bin/env python3
"""Refuse to launch a runtime whose harness projections are broken (ticket 0983).

A runtime whose projected link dangles does not fail: Claude Code drops the
instructions and hooks it cannot read and still answers (0978's disposable-HOME
probe), Codex runs no guard when ~/.codex/hooks.json dangles, Pi loads no
extension. No hook can report that, because the hook vanishes with the link.
So the check runs in the shell, before the runtime starts: the wrappers in
scripts/shell-init.sh call this script and launch only on exit 0.

The expected projections come from one declared manifest,
adapters/projections.json, never from a glob of what happens to exist: a
required entry that is absent is itself a failure.

Usage: validate-projections.py RUNTIME [--root DIR] [--manifest FILE]
Exit 0: every entry for RUNTIME resolves to its target. Exit 1: at least one
is missing, dangling or foreign; each culprit is named on stderr with the
exact repair. Exit 2: usage error.

On success the resolved checkout is recorded in
${XDG_STATE_HOME:-~/.local/state}/idh/last-good-root, so the ~/.bashrc
loader can name the exact repair when ~/.idh itself has gone.
"""

import argparse
import json
import os
import shlex
import sys
from pathlib import Path

# Spelled as invoked (~/.idh/scripts/... keeps ~/.idh), so a repair names the
# pointer rather than whatever it happens to resolve to today.
DEFAULT_ROOT = Path(os.path.abspath(__file__)).parent.parent


def state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(
        os.environ["HOME"], ".local", "state"
    )
    return Path(base) / "idh"


def expand(spec: str, root: Path) -> Path:
    """Expand a manifest spec. A bare $IDH_ROOT is the resolved checkout (the
    pointer's own target); $IDH_ROOT/<rel> keeps the root as spelled."""
    if spec == "$IDH_ROOT":
        return root.resolve()
    if spec.startswith("$IDH_ROOT/"):
        return Path(str(root) + spec[len("$IDH_ROOT") :])
    if spec == "~" or spec.startswith("~/"):
        return Path(os.environ["HOME"] + spec[1:])
    raise ValueError(f"manifest spec must start with ~ or $IDH_ROOT: {spec!r}")


def resolved(path: Path):
    """The fully resolved path, or None when it does not resolve to anything."""
    try:
        real = path.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    return real


def check_entry(entry: dict, root: Path):
    """Return None when the entry is healthy, else (kind, detail, repair)."""
    path = expand(entry["path"], root)
    target = expand(entry["target"], root)
    q_path, q_target = shlex.quote(str(path)), shlex.quote(str(target))
    link = f"ln -sfn {q_target} {q_path}"
    real_target = resolved(target)
    if real_target is None:
        prefix = f"restore {q_target} (the expected target is gone), then "
    else:
        prefix = ""

    if not path.is_symlink() and not path.exists():
        if not entry.get("required", False):
            return None
        return ("MISSING", f"{path} does not exist", prefix + link)

    real = resolved(path)
    if real is None:
        return (
            "DANGLING",
            f"{path} -> {os.readlink(path)} resolves to nothing",
            prefix + link,
        )

    if real_target is not None and real == real_target:
        return None

    if path.is_symlink():
        return ("FOREIGN", f"{path} resolves to {real}, not {target}", prefix + link)
    # A real file or directory where the harness is expected: never overwrite
    # it blind; move it aside, then link.
    aside = shlex.quote(f"{path}.pre-idh")
    return (
        "FOREIGN",
        f"{path} is a real {'directory' if path.is_dir() else 'file'}, not {target}",
        prefix + f"inspect it, then: mv {q_path} {aside} && ln -s {q_target} {q_path}",
    )


def load_entries(manifest: Path, runtime: str):
    data = json.loads(manifest.read_text())
    entries = data["entries"]
    runtimes = {r for e in entries for r in e["runtimes"]}
    if runtime not in runtimes:
        raise SystemExit(
            f"validate-projections: unknown runtime {runtime!r} (manifest declares: "
            f"{', '.join(sorted(runtimes))})"
        )
    return [e for e in entries if runtime in e["runtimes"]]


def record_good_root(root: Path) -> None:
    try:
        d = state_dir()
        d.mkdir(parents=True, exist_ok=True)
        f = d / "last-good-root"
        if not f.exists() or f.read_text().strip() != str(root):
            f.write_text(f"{root}\n")
    except OSError:
        pass  # a hint for a later repair message, never a reason to refuse


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("runtime")
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--manifest", type=Path)
    args = ap.parse_args(argv)
    root = args.root.absolute()
    manifest = args.manifest or root / "adapters" / "projections.json"

    failures = []
    for entry in load_entries(manifest, args.runtime):
        problem = check_entry(entry, root)
        if problem:
            failures.append((entry, problem))

    if not failures:
        record_good_root(root.resolve())
        return 0

    err = sys.stderr
    print(
        f"idh: refusing to launch {args.runtime}: {len(failures)} harness "
        f"projection(s) broken (manifest {manifest})",
        file=err,
    )
    for entry, (kind, detail, repair) in failures:
        print(f"  {kind}: {detail}", file=err)
        print(f"    why:    {entry['why']}", file=err)
        print(f"    repair: {repair}", file=err)
    print(
        f"  Run the repair from a plain terminal, then relaunch. To launch anyway "
        f"(logged): IDH_SKIP_VALIDATE=1 {args.runtime} ...",
        file=err,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

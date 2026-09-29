"""Harness lifecycle on one machine: `idh install | check` (ticket 0987).

The operator's command, not the runtimes': hooks and skills keep calling
scripts by path. adapters/projections.json is the one list of links, so
install creates exactly what check verifies, and the launch validator
(scripts/validate-projections.py) supplies the per-entry verdict. Links are
built from the structured `path`/`target` fields only; the free-form
`installer` text is display, never executed. Stdlib only, Python 3.12.
"""

import importlib.util
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _validator():
    spec = importlib.util.spec_from_file_location(
        "validate_projections", REPO / "scripts" / "validate-projections.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V = _validator()


def root() -> Path:
    """The checkout spelled ~/.idh when the pointer reaches it, so links stay
    relocatable; the resolved checkout otherwise (first install)."""
    pointer = Path(os.environ["HOME"]) / ".idh"
    return pointer if V.resolved(pointer) == REPO else REPO


def entries(runtime=None):
    return V.load_entries(REPO / "adapters" / "projections.json", runtime)


def report(kind, detail, repair) -> None:
    print(f"  {kind}: {detail}\n    repair: {repair}", file=sys.stderr)


def install_links(base: Path) -> int:
    """Create each absent entry; leave correct ones; refuse anything else."""
    rc = 0
    for entry in entries():
        path, target = V.expand(entry["path"], base), V.expand(entry["target"], base)
        if not path.is_symlink() and not path.exists():
            if not entry["required"] and V.resolved(target) is None:
                continue  # optional, and nothing to point at on this machine
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(target)
            print(f"installed: {path} -> {target}")
            continue
        problem = V.check_entry(entry, base)
        if problem:
            report(*problem)
            rc = 1
    return rc


def check(runtime=None) -> int:
    failures = [p for e in entries(runtime) if (p := V.check_entry(e, root()))]
    for problem in failures:
        report(*problem)
    print(f"idh check: {len(failures)} broken" if failures else "idh check: ok")
    return 1 if failures else 0


def install() -> int:
    return install_links(root())


def main(argv) -> int:
    command, *rest = argv
    try:
        if command == "check":
            return check(*rest[:1])
        return install()
    except V.ManifestError as exc:
        print(f"idh: adapters/projections.json is unusable: {exc}", file=sys.stderr)
        return 1

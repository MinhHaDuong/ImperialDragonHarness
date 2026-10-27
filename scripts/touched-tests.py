#!/usr/bin/env python3
"""Run the tests that name what a change touched, whatever their tier (ticket 1283).

A review (gaze, verify-gate) runs this from the checkout of the head under
review. The change is `git diff <merge-base of HEAD and --base>..HEAD`, so a
multi-commit branch is covered whole. Selection is a text search of tests/:

- a changed `tests/**/test_*.py` is selected itself;
- any other changed source file (a `.py`/`.sh`, an executable, a non-test file
  under tests/ such as conftest.py) selects every test whose text names it:
  its repo path, its file name, or for a Python module `import <stem>`,
  `from <stem>` and the quoted `"<stem>"` of an importlib load;
- a changed source file no test names makes the whole integration tier run
  (`-m integration`, the selected files excepted), when the project declares
  that marker.

Selected files run with no marker filter, through the project's runner:
`uv run --frozen python3` with an inherited VIRTUAL_ENV dropped when the
project has uv.lock and uv is on PATH (the Makefile's RUN rule), else
`python3`. The project's `scripts/pytest_workers.py`, when present, sets the
parallelism. The PR #1799 shape this catches: a symbol moved to a new file
while an integration test still imports it from the old one.

Printed lines a review quotes: `selected:`, `fallback:`, `result:`.
Exit: 0 the tests ran and passed, 1 a test failed, 2 usage or git error,
4 not a pass: nothing ran (no test layout, no source or test file changed,
no test collected) or a changed source file stayed uncovered (no test names
it and the project declares no integration marker).
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

PASS, FAIL, ERROR, SKIPPED = 0, 1, 2, 4
SOURCE_SUFFIXES = {".py", ".sh", ".bash"}
MARKER_FILES = ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "conftest.py", "tests/conftest.py")
IDENTIFIER = re.compile(r"[A-Za-z_]\w*")


def out(line):
    sys.stdout.write(line + "\n")


def git(root, *args):
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {(proc.stderr or proc.stdout).strip()}")
    return proc.stdout


def changed_files(root, base):
    merge_base = git(root, "merge-base", "HEAD", base).strip()
    names = git(root, "diff", "--name-only", "--no-renames", f"{merge_base}..HEAD").splitlines()
    wanted, modes = set(names), {}
    for rev in (merge_base, "HEAD"):  # whole trees, filtered here: no pathspec list to overrun ARG_MAX
        for entry in git(root, "ls-tree", "-r", rev).splitlines() if names else []:
            meta, path = entry.split("\t", 1)
            if path in wanted:
                modes.setdefault(path, meta.split()[0])
    return merge_base, [(name, modes.get(name, "")) for name in names]


def is_test_file(path):
    return path.startswith("tests/") and Path(path).name.startswith("test_") and path.endswith(".py")


def is_source(path, mode):
    p = Path(path)
    return p.suffix in SOURCE_SUFFIXES or mode == "100755" or (path.startswith("tests/") and p.suffix == ".py")


def patterns(path):
    """Regexes whose match in a test's text means the test names `path`."""
    p = Path(path)
    found = [re.compile(r"(?<![\w./-])" + re.escape(path) + r"(?![\w-])")]
    if p.suffix or "-" in p.name or "_" in p.name:  # a bare word like `erg` names too much: path only
        found.append(re.compile(r"(?<![\w.-])" + re.escape(p.name) + r"(?![\w-])"))
    if p.suffix == ".py" and IDENTIFIER.fullmatch(p.stem):
        stem = re.escape(p.stem)
        found.append(re.compile(r"\b(?:import|from)\s+(?:[\w.]+\.)?" + stem + r"\b"))
        found.append(re.compile(r"[\"']" + stem + r"[\"']"))
    return found


def integration_marker(root):
    for name in MARKER_FILES:
        path = root / name
        if path.is_file() and re.search(r"^\s*[\"']?integration\b", path.read_text(encoding="utf-8", errors="replace"), re.M):
            return True
    return False


def runner(root):
    env = dict(os.environ)
    if (root / "uv.lock").is_file() and shutil.which("uv"):
        env.pop("VIRTUAL_ENV", None)
        return ["uv", "run", "--frozen", "python3"], env
    return ["python3"], env


def workers(root, python, env):
    script = root / "scripts" / "pytest_workers.py"
    if not script.is_file():
        return []
    proc = subprocess.run([*python, str(script)], cwd=root, capture_output=True, text=True, env=env)
    return proc.stdout.split() if proc.returncode == 0 else []


def select(root, changes):
    """(selected test paths, unnamed source paths)."""
    tests = sorted(str(p.relative_to(root)) for p in (root / "tests").rglob("test_*.py"))
    texts = {t: (root / t).read_text(encoding="utf-8", errors="replace") for t in tests}
    selected, unnamed = set(), []
    for path, mode in changes:
        if is_test_file(path):
            if path in texts:
                selected.add(path)
            continue
        if not is_source(path, mode):
            continue
        regexes = patterns(path)
        hits = {t for t, text in texts.items() if t != path and any(r.search(text) for r in regexes)}
        if hits:
            selected |= hits
        else:
            unnamed.append(path)
    return sorted(selected), unnamed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="origin/main", help="base branch; the change starts at its merge-base with HEAD")
    ap.add_argument("--list", action="store_true", help="print the selection only; run nothing")
    args = ap.parse_args(argv)
    try:
        root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").strip())
        merge_base, changes = changed_files(root, args.base)
    except RuntimeError as exc:
        out(f"touched-tests: error: {exc}")
        return ERROR
    out(f"touched-tests: base {merge_base[:12]} (merge-base of HEAD and {args.base}), {len(changes)} file(s) changed")
    if not (root / "tests").is_dir() or not any((root / "tests").rglob("test_*.py")):
        out("selected: none")
        out("fallback: none")
        out("result: skipped (no test layout)")
        return SKIPPED
    selected, unnamed = select(root, changes)
    marker = integration_marker(root)
    out(f"selected: {' '.join(selected) or 'none'}")
    if not unnamed:
        out("fallback: none")
    elif marker:
        out(f"fallback: full integration tier (-m integration), no test names: {' '.join(unnamed)}")
    else:
        out(f"fallback: unavailable (no integration marker declared), not covered: {' '.join(unnamed)}")
    runs = []
    if selected:
        runs.append(selected)
    if unnamed and marker:
        runs.append(["tests/", "-m", "integration", *(f"--ignore={t}" for t in selected)])
    if not runs:
        out("result: skipped (no source or test file changed)")
        return SKIPPED
    if args.list:
        out("result: skipped (--list: nothing run)")
        return SKIPPED
    python, env = runner(root)
    extra = workers(root, python, env)
    failed, ran = [], False
    for targets in runs:
        cmd = [*python, "-m", "pytest", "-q", *extra, *targets]
        out(f"run: {' '.join(cmd)}")
        sys.stdout.flush()
        code = subprocess.run(cmd, cwd=root, env=env).returncode
        ran = ran or code == 0
        if code not in (0, 5):  # 5: nothing collected, e.g. a tier with no test outside the selection
            failed.append(f"pytest exit {code}")
    if failed:
        out(f"result: fail ({'; '.join(failed)})")
        return FAIL
    if not ran:
        out("result: skipped (no test collected)")
        return SKIPPED
    if unnamed and not marker:
        out(f"result: incomplete ({len(selected)} selected file(s) passed; {len(unnamed)} source file(s) not covered)")
        return SKIPPED
    out(f"result: pass ({len(selected)} selected file(s){', integration tier' if unnamed else ''})")
    return PASS


if __name__ == "__main__":
    sys.exit(main())

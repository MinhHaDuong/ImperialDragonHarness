"""Guard (ticket 0940): a Python suite must spawn its children without BASH_ENV.

The shell-side twin is `tests/test_bash_tests_are_hermetic.sh` (ticket 0359),
which makes the same discipline mechanical over `tests/*.sh`. This file does it
for the other half of the test tree, `tests/*.py`, discovered by glob so a
newly added suite is covered without editing this file.

`BASH_ENV` points every child bash at `scripts/bash-env.sh`, which re-runs the
project `.env` parser at child startup. A Python test that calls
`subprocess.run` without a hermetic env hands that variable to the child via
`os.environ` exactly as a shell parent would — including through an
intermediate Python child, which passes it on to its own bash grandchildren.
That is the 2026-07-27 defect class: an injected fixture credential is
overridden by the real one at child startup, and a failing assertion prints
what it found. That incident leaked two live keys and forced a rotation.

Accepted shapes, all already in the tree:
  * `env=child_env()` — the parent's live environment minus the loader
    variable (`tests/child_env.py`); keeps `monkeypatch.setenv` fixtures and
    ambient `PATH`/`HOME` while the child starts with no loader.
  * a fresh env dict built from scratch (`tests/test_on_end_hook.py`) — an
    explicit `env=` replaces the whole inherited environment, so nothing leaks;
  * an env that derives from `os.environ` but visibly clears `BASH_ENV`
    (`{**child_env(), "BASH_ENV": ""}` or an equivalent filter);
  * `env -i` / `env --ignore-environment` as the command's first words.

It reports FILE NAMES and LINE NUMBERS only — never the offending text, never
an environment value. A guard that echoed what it found would reproduce the
defect it exists to prevent (ticket 0359's discipline).
See rules/coding-bash.md § "BASH_ENV / hook scripts: test via a real
subprocess, never source-in-shell" and its subsection § "Unsetting a variable
in the parent does not unset it in the child".

---------------------------------------------------------------------------
HOW IT LOOKS, AND WHAT IT STILL CANNOT SEE

Unlike the shell guard (a textual scanner over a language that resolves
commands at runtime), this one parses real syntax with `ast`, so comments,
docstrings, and quoted strings are invisible to it by construction —
`(0c)`–`(0e)` below pin that against a naive `grep` implementation, and an
unparseable file fails LOUDLY rather than being reported clean (a file the
guard cannot read is a file it did not check; `(0f)`).

What is judged, per CALL NODE:
  * `subprocess.run|Popen|call|check_call|check_output|getoutput|
    getstatusoutput`, including names bound by `from subprocess import run`,
    `import subprocess as sp`, and — conservatively, since a star import can
    bind any of them — every spawn function under `from subprocess import *`;
  * the spawn's own `env=` expression, never the whole file: an unrelated
    hermetic spawn on the line above launders nothing, and one leaky call
    beside three clean ones is still reported;
  * "wholesale" derivation means the env expression IS the inherited mapping:
    bare `os.environ` (also as `from os import environ`, and `import os as o`
    followed by `o.environ`), `.copy()` and `copy.copy(…)`, `dict(os.environ,
    …)`, `{**os.environ, …}`, `os.environ | {…}`, and a comprehension over
    `os.environ.items()` — recursing through `if`/`else` expression branches
    and boolean operators, so one wholesale branch launders nothing. Reading
    one variable (`os.environ.get("PATH")`) is NOT wholesale — the child gets
    one string, not the loader;
  * a wholesale env counts as clearing `BASH_ENV` only when the mention is in
    a NEUTRALIZING POSITION: a dict key mapping to an empty-string constant
    (`{**os.environ, "BASH_ENV": ""}` or `dict(os.environ, BASH_ENV="")`), or
    a `k != "BASH_ENV"` comprehension filter. A `"BASH_ENV"` constant in any
    other position launders nothing.

BLIND SPOTS — shapes this scanner does NOT detect. Listed so a reader knows
what a PASS is worth; none is closed by pretending otherwise:
  * `env=<variable>` or `env=<helper call>` built out of sight. The guard
    judges the call site, so `env = os.environ.copy()` earlier in the
    function, or a helper returning `os.environ` verbatim, defeats it.
    Chasing assignments is dataflow analysis, not a hygiene ratchet; the
    remedy is review — five converted suites already assign their env to a
    local first, so acceptance rests on reading those assignments, not on
    this scan.
  * `subprocess.run(cmd, **kwargs)` with `env` arriving through `**kwargs`.
  * A spawn function reached through a variable (`r = subprocess.run; r(…)`),
    or any second-order aliasing the import scan does not bind.
  * A child that re-exports `BASH_ENV` by constructing it at runtime from
    other values. The guard sees the name, not the semantics.
  * `subprocess` spawns in files OTHER than `tests/*.py` — the glob is the
    scope, mirroring 0359. Non-test scripts are out of scope by design.

This file excludes ITSELF from the scan, and must: probe (0a) is a
deliberately non-hermetic spawn — that is the whole point of a positive
control — and the detector flags a copy of this file under another name.
Fixtures for the static controls live in `tmp_path`, never under `tests/`,
so they are not themselves discovered as suites.
---------------------------------------------------------------------------
"""

import ast
import subprocess
from pathlib import Path

import pytest

from child_env import child_env

TESTS_DIR = Path(__file__).resolve().parent
SELF = Path(__file__).name

SPAWN_FUNCS = {
    "run",
    "Popen",
    "call",
    "check_call",
    "check_output",
    "getoutput",
    "getstatusoutput",
}


# --- the scanner ---------------------------------------------------------------


class _Scanner:
    """Import-aware verdicts for one module's subprocess spawns.

    The import scan binds names, not spellings: `from subprocess import run`,
    `import subprocess as sp`, `from os import environ`, and `import os as o`
    all rebind the tokens the verdicts match, so a module's verdicts must be
    computed against the names THAT module binds. A star import
    (`from subprocess import *`) can bind any spawn function, so all of
    SPAWN_FUNCS are recognized conservatively.
    """

    def __init__(self, tree: ast.Module) -> None:
        self.os_aliases = {"os"}
        self.environ_names: set[str] = set()
        self.spawn_names = {"subprocess"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "os":
                        self.os_aliases.add(alias.asname or "os")
                    elif alias.name == "subprocess":
                        self.spawn_names.add(alias.asname or "subprocess")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "subprocess":
                    for alias in node.names:
                        if alias.name == "*":
                            self.spawn_names.update(SPAWN_FUNCS)
                        elif alias.name in SPAWN_FUNCS:
                            self.spawn_names.add(alias.asname or alias.name)
                elif node.module == "os":
                    for alias in node.names:
                        if alias.name == "environ":
                            self.environ_names.add(alias.asname or "environ")

    def _is_environ_ref(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Attribute) and node.attr == "environ":
            return (
                isinstance(node.value, ast.Name)
                and node.value.id in self.os_aliases
            )
        return isinstance(node, ast.Name) and node.id in self.environ_names

    def _wholesale(self, node: ast.expr) -> bool:
        """The expression IS the inherited `os.environ` mapping (a copy of it).

        Reading one variable (`os.environ.get("PATH")`, `os.environ["HOME"]`)
        is not wholesale: the child receives that one string, not the loader.
        """
        if self._is_environ_ref(node):
            return True
        if isinstance(node, ast.Call):
            func = node.func
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "copy"
                and isinstance(func.value, ast.Name)
                and func.value.id == "copy"
            ):
                return any(self._wholesale(a) for a in node.args)
            if isinstance(func, ast.Attribute) and func.attr in ("copy", "items"):
                return self._wholesale(func.value)
            if isinstance(func, ast.Name) and func.id == "dict":
                args = list(node.args) + [
                    k.value for k in node.keywords if k.arg is None
                ]
                return any(self._wholesale(a) for a in args)
        if isinstance(node, ast.Dict):
            return any(self._wholesale(v) for v in node.values)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return self._wholesale(node.left) or self._wholesale(node.right)
        if isinstance(node, ast.IfExp):
            # One wholesale branch launders nothing: either arm may execute.
            return self._wholesale(node.body) or self._wholesale(node.orelse)
        if isinstance(node, ast.BoolOp):
            return any(self._wholesale(v) for v in node.values)
        if isinstance(node, ast.DictComp):
            for generator in node.generators:
                if (
                    isinstance(generator.iter, ast.Call)
                    and isinstance(generator.iter.func, ast.Attribute)
                    and generator.iter.func.attr == "items"
                ):
                    return self._wholesale(generator.iter.func.value)
        return False

    def _clears_bash_env(self, node: ast.expr) -> bool:
        """The env expression visibly empties or filters out `BASH_ENV`.

        Only two mention positions neutralize: a dict key mapping to an
        empty-string constant (a dict-literal entry or a `dict(…)` keyword),
        and a `k != "BASH_ENV"` comprehension filter. A `"BASH_ENV"` constant
        anywhere else — as a value, inside a nested call — launders nothing.
        """
        for n in ast.walk(node):
            if isinstance(n, ast.Dict):
                for key, value in zip(n.keys, n.values):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "BASH_ENV"
                        and isinstance(value, ast.Constant)
                        and value.value == ""
                    ):
                        return True
            elif (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id == "dict"
            ):
                for kw in n.keywords:
                    if (
                        kw.arg == "BASH_ENV"
                        and isinstance(kw.value, ast.Constant)
                        and kw.value.value == ""
                    ):
                        return True
            elif isinstance(n, ast.DictComp):
                for generator in n.generators:
                    for cond in generator.ifs:
                        if (
                            isinstance(cond, ast.Compare)
                            and any(
                                isinstance(op, (ast.NotEq, ast.NotIn))
                                for op in cond.ops
                            )
                            and any(
                                isinstance(side, ast.Constant)
                                and side.value == "BASH_ENV"
                                for side in [cond.left, *cond.comparators]
                            )
                        ):
                            return True
        return False

    def is_spawn_call(self, node: ast.expr) -> bool:
        if not isinstance(node, ast.Call):
            return False
        func = node.func
        if isinstance(func, ast.Attribute) and func.attr in SPAWN_FUNCS:
            return (
                isinstance(func.value, ast.Name)
                and func.value.id in self.spawn_names
            )
        return isinstance(func, ast.Name) and func.id in self.spawn_names

    def hermetic(self, call: ast.Call) -> bool:
        if _command_neutralizes_env(call):
            return True
        env = next((k for k in call.keywords if k.arg == "env"), None)
        if env is None:
            return False  # no env= -> the child inherits os.environ verbatim
        value = env.value
        if isinstance(value, ast.Constant) and value.value is None:
            return False  # env=None is the same inheritance, spelled out
        if self._wholesale(value) and not self._clears_bash_env(value):
            return False
        return True


def _command_words(call: ast.Call) -> list:
    """The leading constant words of the command, from a list or a bare str."""
    if not call.args:
        return []
    first = call.args[0]
    if isinstance(first, ast.Constant):
        return [first.value]
    if isinstance(first, (ast.List, ast.Tuple)):
        return [elt.value for elt in first.elts if isinstance(elt, ast.Constant)]
    return []


def _command_neutralizes_env(call: ast.Call) -> bool:
    """`env -i …` / `env --ignore-environment …` as leading words."""
    words = _command_words(call)
    if not words or words[0] != "env":
        return False
    return any(w in ("-i", "--ignore-environment") for w in words[1:3])


def scan_file(path: Path) -> tuple[str, list[int]]:
    """Verdict over one file: `OK` | `BAD` + line numbers | `UNPARSEABLE`."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return "UNPARSEABLE", []
    scanner = _Scanner(tree)
    bad = sorted(
        {
            node.lineno
            for node in ast.walk(tree)
            if scanner.is_spawn_call(node) and not scanner.hermetic(node)
        }
    )
    return ("BAD", bad) if bad else ("OK", [])


# --- the gate ------------------------------------------------------------------


@pytest.mark.adherence
def test_python_suites_spawn_hermetic_children():
    """Every subprocess spawn in tests/*.py neutralizes BASH_ENV."""
    offenders: list[str] = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        if path.name == SELF:
            continue
        verdict, linenos = scan_file(path)
        if verdict == "UNPARSEABLE":
            offenders.append(f"{path.name}: could not parse — NOT checked")
        else:
            offenders.extend(f"{path.name}:{lineno}" for lineno in linenos)
    assert not offenders, (
        "subprocess spawns that hand BASH_ENV to the child (the loader "
        "re-enters at child startup): "
        + ", ".join(offenders)
        + " — pass env=child_env(), or an env that clears BASH_ENV "
        "(see tests/child_env.py)"
    )


# --- static negative controls --------------------------------------------------
# Each fixture below is a shape a naive implementation reports wrongly. The
# naive scanner here is a text grep for "env=" — or for "subprocess.run(" —
# which every BAD case below would slip past and/or every OK case would trip.
# Fixtures are written to tmp_path, never under tests/, so they are not
# discovered as suites. They contain no secret and no real credential.

_CONTROLS: list[tuple[str, str, str]] = [
    (
        "c1_bad_plain_run",
        "BAD",
        "import subprocess\n"
        "subprocess.run(['bash', '-c', 'true'])\n",
    ),
    (
        "c2_bad_popen",
        "BAD",
        "import subprocess\n"
        "subprocess.Popen(['bash', '-c', 'true'])\n",
    ),
    (
        "c3_bad_env_none",
        "BAD",
        "import subprocess\n"
        "subprocess.run(['bash', '-c', 'true'], env=None)\n",
    ),
    (
        "c4_bad_environ_copy",
        "BAD",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'], env=os.environ.copy())\n",
    ),
    (
        "c5_bad_dict_environ",
        "BAD",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'], env=dict(os.environ, K='v'))\n",
    ),
    (
        "c6_bad_splat_environ",
        "BAD",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'], env={**os.environ, 'K': 'v'})\n",
    ),
    (
        "c7_bad_piped_environ",
        "BAD",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'], env={'K': 'v'} | os.environ)\n",
    ),
    (
        "c8_bad_from_import_alias",
        "BAD",
        "from subprocess import run\n"
        "run(['bash', '-c', 'true'])\n",
    ),
    (
        "c9_ok_helper",
        "OK",
        "import subprocess\n"
        "from child_env import child_env\n"
        "subprocess.run(['bash', '-c', 'true'], env=child_env())\n",
    ),
    (
        "c10_ok_cleared_splat",
        "OK",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "               env={**os.environ, 'BASH_ENV': ''})\n",
    ),
    (
        "c11_ok_filtered_comprehension",
        "OK",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "    env={k: v for k, v in os.environ.items() if k != 'BASH_ENV'})\n",
    ),
    (
        "c12_ok_env_dash_i",
        "OK",
        "import subprocess\n"
        "subprocess.run(['env', '-i', 'bash', '-c', 'true'])\n",
    ),
    (
        "c13_ok_env_ignore_environment",
        "OK",
        "import subprocess\n"
        "subprocess.run(['env', '--ignore-environment', 'bash', '-c', 'true'])\n",
    ),
    (
        "c14_ok_fresh_env",
        "OK",
        "import subprocess\n"
        "subprocess.run(['bash', '-c', 'true'], env={'PATH': '/usr/bin'})\n",
    ),
    (
        "c15_ok_single_read",
        "OK",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "               env={'PATH': os.environ.get('PATH', '/bin')})\n",
    ),
    (
        "c16_ok_spawn_in_comment_only",
        "OK",
        "# subprocess.run(['bash', '-c', 'true'])\n",
    ),
    (
        "c17_ok_spawn_in_docstring_only",
        "OK",
        '"""\n'
        "docs: subprocess.run(['bash', '-c', 'true'])\n"
        '"""\n',
    ),
    # --- round-2 controls: shapes the shipped scanner wrongly cleared ---------
    # Each of these leaked a fake sentinel at runtime while scanning OK
    # (PR #1111 round-2 review): a "BASH_ENV" constant in a non-neutralizing
    # position, an environ spelling or branch the wholesale match missed, and
    # spawn bindings the import scan did not see.
    (
        "c19_bad_laundered_bash_env_refill",
        "BAD",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "    env={**os.environ,\n"
        "         'BASH_ENV': os.environ.get('BASH_ENV', '')})\n",
    ),
    (
        "c20_bad_laundered_bash_env_value",
        "BAD",
        "import os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "               env={**os.environ, 'NOTE': 'BASH_ENV'})\n",
    ),
    (
        "c21_bad_from_os_import_environ",
        "BAD",
        "import subprocess\n"
        "from os import environ\n"
        "subprocess.run(['bash', '-c', 'true'], env=environ)\n",
    ),
    (
        "c28_ok_from_os_import_environ_cleared",
        "OK",
        "import subprocess\n"
        "from os import environ\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "               env={**environ, 'BASH_ENV': ''})\n",
    ),
    (
        "c22_bad_ifexp_wholesale_branch",
        "BAD",
        "import os, subprocess\n"
        "from child_env import child_env\n"
        "flag = True\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "    env=os.environ.copy() if flag else child_env())\n",
    ),
    (
        "c23_bad_boolop_wholesale_branch",
        "BAD",
        "import os, subprocess\n"
        "flag = True\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "               env=flag or os.environ)\n",
    ),
    (
        "c24_bad_copy_copy_environ",
        "BAD",
        "import copy, os, subprocess\n"
        "subprocess.run(['bash', '-c', 'true'],\n"
        "               env=copy.copy(os.environ))\n",
    ),
    (
        "c25_bad_star_import_spawn",
        "BAD",
        "from subprocess import *\n"
        "run(['bash', '-c', 'true'])\n",
    ),
    (
        "c26_bad_getoutput",
        "BAD",
        "import subprocess\n"
        "subprocess.getoutput(\"bash -c 'true'\")\n",
    ),
    (
        "c27_bad_getstatusoutput",
        "BAD",
        "import subprocess\n"
        "subprocess.getstatusoutput(\"bash -c 'true'\")\n",
    ),
]


@pytest.mark.adherence
@pytest.mark.parametrize(
    "case_id, expected, source", _CONTROLS, ids=[c[0] for c in _CONTROLS]
)
def test_detector_control(case_id: str, expected: str, source: str, tmp_path):
    """The scanner's verdict on each control fixture must be exact."""
    fixture = tmp_path / f"{case_id}.py"
    fixture.write_text(source, encoding="utf-8")
    verdict, _ = scan_file(fixture)
    assert verdict == expected, (
        f"{case_id}: detector control expected {expected}, got {verdict} — "
        "the static scan cannot be trusted"
    )


@pytest.mark.adherence
def test_detector_fails_loudly_on_an_unparseable_file(tmp_path):
    """A file the scanner cannot parse is reported, never counted clean."""
    fixture = tmp_path / "c18_broken.py"
    fixture.write_text("def broken(:\n", encoding="utf-8")
    verdict, linenos = scan_file(fixture)
    assert verdict == "UNPARSEABLE", (
        "an unparseable suite was not reported loudly — the guard would "
        "have reported a file it never read as clean"
    )
    assert linenos == []


# --- runtime probes: fake sentinel, never a real key -----------------------------
# A static scan whose "all clear" is indistinguishable from "I never looked"
# is not a check. These probes run the enforced idiom against a case known
# POSITIVE. The loader is a throwaway fixture exporting a recognisable dummy —
# never a real key: verifying with the live credential is how the 2026-07-27
# leak happened a second time. Both probes assert on a presence BOOLEAN;
# neither ever prints what it found.

_SENTINEL = "HERMETIC_PROBE_0940"
_PROBE_CMD = 'printf "%s" "${' + _SENTINEL + ':-}"'


@pytest.mark.integration
def test_a_plain_spawn_inherits_the_loader(tmp_path, monkeypatch):
    """Probe (0a): no env= -> the child bash runs the loader at startup.

    If this comes back empty the probe is broken, not the tree clean.
    """
    loader = tmp_path / "loader.sh"
    loader.write_text(f"export {_SENTINEL}=dummy-sentinel-value\n")
    monkeypatch.setenv("BASH_ENV", str(loader))
    out = subprocess.run(
        ["bash", "-c", _PROBE_CMD], capture_output=True, text=True, timeout=30
    )
    assert out.returncode == 0, "probe (0a) child bash failed to run"
    assert out.stdout, "probe (0a) saw nothing — the BASH_ENV probe is broken"


@pytest.mark.integration
def test_child_env_clears_the_loader(tmp_path, monkeypatch):
    """Probe (0b): env=child_env() -> the same child inherits nothing."""
    loader = tmp_path / "loader.sh"
    loader.write_text(f"export {_SENTINEL}=dummy-sentinel-value\n")
    monkeypatch.setenv("BASH_ENV", str(loader))
    out = subprocess.run(
        ["bash", "-c", _PROBE_CMD],
        env=child_env(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert out.returncode == 0, "probe (0b) child bash failed to run"
    assert not out.stdout, "probe (0b): a child_env() child still saw the loader"


@pytest.mark.integration
def test_a_python_child_passes_the_loader_to_its_grandchild(tmp_path, monkeypatch):
    """Probe (0c): the leak crosses a Python child, exactly as the ticket says.

    A plain `env=None` Python child gets BASH_ENV from os.environ and hands it
    to the bash grandchild it spawns — this is the exposure path the ticket's
    defect class was about. The same grandchild under `env=child_env()` sees
    nothing (probe 0b's property, one level deeper).
    """
    loader = tmp_path / "loader.sh"
    loader.write_text(f"export {_SENTINEL}=dummy-sentinel-value\n")
    monkeypatch.setenv("BASH_ENV", str(loader))
    grandchild = (
        "import subprocess\n"
        f"out = subprocess.run(['bash', '-c', {_PROBE_CMD!r}],\n"
        "                       capture_output=True, text=True, timeout=30)\n"
        "print('LEAKY' if out.stdout else 'CLEAN')\n"
    )
    leaky = subprocess.run(
        ["python3", "-c", grandchild], capture_output=True, text=True, timeout=60
    )
    assert leaky.returncode == 0, "probe (0c) python child failed to run"
    assert "LEAKY" in leaky.stdout, (
        "probe (0c) saw no leak through the python child — the probe is "
        "broken, not the tree clean"
    )
    hermetic_grandchild = (
        "import subprocess\n"
        "from child_env import child_env\n"
        f"out = subprocess.run(['bash', '-c', {_PROBE_CMD!r}],\n"
        "                       env=child_env(), capture_output=True,\n"
        "                       text=True, timeout=30)\n"
        "print('LEAKY' if out.stdout else 'CLEAN')\n"
    )
    clean = subprocess.run(
        ["python3", "-c", hermetic_grandchild],
        env={**child_env(), "PYTHONPATH": str(TESTS_DIR)},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert clean.returncode == 0, "probe (0c) hermetic child failed to run"
    assert "CLEAN" in clean.stdout, (
        "probe (0c): a child_env() grandchild still saw the loader"
    )

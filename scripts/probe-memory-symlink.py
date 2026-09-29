#!/usr/bin/env python3
"""Does Claude Code load project memory through a symlink, and which key does a
session launched through a symlinked checkout use? Measured, not read.

Ticket 0984 (step C of 0978). Three questions, each answered by `claude -p` in a
disposable HOME under a fresh temp directory; nothing is launched against the
real HOME, and the script refuses to build its rig there.

  control   memory in a real file                     must load, or the probe could not look
  symlink   projects/<slug>/memory is a symlink        loaded or not: the verdict
  cwd key   launch from <home>/.idh -> <home>/.claude  $PWD=link (cd) vs $PWD=target (cd -P)

Auto memory keys on the session's git root, not on the cwd itself: a work
directory with no repository of its own inherits any ancestor's `.git` (an
empty `/tmp/.git` is enough), so its memory goes to that ancestor's slug. That
is why the 2026-09-28 control never fired. The rig makes each work directory
its own git root.

The control runs first. If it does not load its sentinel the script exits 1
with "could not look" and the other rows are not findings. A launch that exits
non-zero, prints nothing or times out is "could not look", never a negative;
a negative counts only when a clean launch and one retry both return it.

Auth: ANTHROPIC_API_KEY resolved at run time from the keys directory through the
harness keystore reader (`_keystore_value` in skills/external-peer-review/
peer_review.py, which sources the provider file in a clean bash child), passed
in the child's environment only: never on argv, written to disk or printed. No key means the
probe exits "could not look: no API key"; it never copies a credential file.
The rig's `.claude.json` is a minimal file (an empty `projects` object, mode
600), never a copy of the live one, which carries MCP servers and account data.
Sentinels are random per run and never printed.
"""

import importlib.util
import json
import os
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

MODEL = os.environ.get("PROBE_MODEL", "haiku")
PROMPT = "Reply with the exact project codeword from your memory, or NONE."
KEY_FILE = Path(os.environ.get("PROBE_KEY_FILE", Path.home() / ".config" / "keys" / "anthropic.env"))
NO_KEY = "could not look: no API key"


def _timeout() -> int:
    try:
        return int(os.environ.get("PROBE_TIMEOUT", "150"))
    except ValueError:
        return 150


def slug_for(path: Path) -> str:
    """Claude Code's project-store key: every non-alphanumeric character becomes '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def detect_loaded(stdout: str, sentinel: str) -> bool:
    """True only when the reply carries the sentinel; the prompt never contains it."""
    if sentinel in PROMPT:
        raise ValueError("sentinel leaked into the prompt")
    return sentinel in stdout


@dataclass
class Launch:
    stdout: str
    status: str  # "exit N" or "timeout" or "not started"

    @property
    def clean(self) -> bool:
        return self.status == "exit 0" and bool(self.stdout.strip())


def verdict(launch: Launch, sentinel: str) -> str:
    """A launch that did not finish cleanly is not a finding either way."""
    if not launch.clean:
        return f"could not look ({launch.status})"
    return "loaded" if detect_loaded(launch.stdout, sentinel) else "not loaded"


def confirm_negative(measure) -> str:
    """Run a measurement; a negative counts only if one retry agrees."""
    first = measure()
    if first != "not loaded":
        return first
    second = measure()
    return "not loaded (retry agrees)" if second == "not loaded" else f"inconclusive (retry: {second})"


def _keystore():
    """The harness's one keystore reader, loaded where it lives (never copied)."""
    src = Path(__file__).resolve().parent.parent / "skills" / "external-peer-review" / "peer_review.py"
    spec = importlib.util.spec_from_file_location("idh_peer_review_keystore", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._keystore_value


def resolve_api_key(key_file: Path) -> str | None:
    """ANTHROPIC_API_KEY as the keystore contract reads it: the provider file is
    sourced by a clean bash child, size-capped, the value never printed. None
    when the file or the variable is missing, or resolution fails."""
    try:
        return _keystore()(key_file, "ANTHROPIC_API_KEY") or None
    except (OSError, ImportError, AttributeError):
        return None


@dataclass
class Rig:
    root: Path
    home: Path
    work: Path


def _refuse_live(path: Path, live_home: Path) -> None:
    p, live = path.resolve(), live_home.resolve()
    if p == live or live in p.parents:
        raise ValueError(f"refusing to build a probe rig in the real HOME: {path}")


def _git_init(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], check=True, capture_output=True)


def _write_memory(mem: Path, sentinel: str) -> None:
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "MEMORY.md").write_text(f"- The project codeword is {sentinel}\n")


def _write_minimal_claude_json(rig_home: Path) -> None:
    dst = rig_home / ".claude.json"
    dst.write_text('{"projects": {}}\n')
    dst.chmod(0o600)


def build_rig(root: Path, sentinel: str, mode: str = "real", live_home: Path | None = None) -> Rig:
    """Disposable HOME with a minimal .claude.json and a sentinel in project memory.

    mode "real": projects/<slug>/memory is a directory. mode "symlink": it is a
    link to a directory elsewhere under root that holds the sentinel.
    """
    _refuse_live(root, live_home or Path.home())
    rig_home, work = root / "home", root / "work"
    (rig_home / ".claude").mkdir(parents=True)
    _write_minimal_claude_json(rig_home)
    _git_init(work)
    mem = rig_home / ".claude" / "projects" / slug_for(work) / "memory"
    if mode == "real":
        _write_memory(mem, sentinel)
    elif mode == "symlink":
        store = root / "store" / "memory"
        _write_memory(store, sentinel)
        mem.parent.mkdir(parents=True, exist_ok=True)
        mem.symlink_to(store, target_is_directory=True)
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return Rig(root=root, home=rig_home, work=work)


def _launch(rig_home: Path, cwd: Path, pwd: Path, key: str) -> Launch:
    """One headless session with a minimal environment: no parent-session variables leak in.

    --strict-mcp-config with no config starts no MCP server at all.
    """
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(rig_home),
        "TERM": "dumb",
        "LANG": "C.UTF-8",
        "PWD": str(pwd),
        "ANTHROPIC_API_KEY": key,
    }
    try:
        r = subprocess.run(
            ["claude", "-p", PROMPT, "--model", MODEL, "--strict-mcp-config"],
            cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=_timeout(),
        )
    except subprocess.TimeoutExpired:
        return Launch("", "timeout")
    except OSError:
        return Launch("", "not started")
    return Launch(r.stdout, f"exit {r.returncode}")


def _tree(d: Path) -> set[str]:
    return {str(p.relative_to(d)) for p in d.rglob("*")} if d.is_dir() else set()


def _project_keys(claude_json: Path) -> set[str]:
    try:
        return set(json.loads(claude_json.read_text()).get("projects", {}))
    except (OSError, ValueError):
        return set()


def _cwd_key_case(root: Path, live_home: Path, logical: bool, key: str) -> dict:
    """Launch through <home>/.idh -> <home>/.claude, the live layout in miniature."""
    _refuse_live(root, live_home)
    rig_home = root / "home"
    real = rig_home / ".claude"
    link = rig_home / ".idh"
    _git_init(real)  # the live checkout is a git repo too
    _write_minimal_claude_json(rig_home)
    link.symlink_to(real, target_is_directory=True)
    labels = {slug_for(link): "slug(link)", slug_for(real): "slug(target)"}
    sentinels = {}
    for slug, label in labels.items():
        s = f"SENT-{secrets.token_hex(6)}"
        sentinels[label] = s
        _write_memory(real / "projects" / slug / "memory", s)
    projects = real / "projects"
    before_files, before_keys = _tree(projects), _project_keys(rig_home / ".claude.json")
    launch = _launch(rig_home, cwd=link, pwd=link if logical else real, key=key)
    if not launch.clean:
        loaded = [f"could not look ({launch.status})"]
    else:
        loaded = [label for label, s in sentinels.items() if detect_loaded(launch.stdout, s)] or ["none"]

    def relabel(text: str) -> str:
        for slug, label in labels.items():
            text = text.replace(slug, label)
        return text.replace(str(rig_home), "~")

    new_files = sorted(_tree(projects) - before_files)
    new_dirs = sorted({relabel(f.split("/")[0]) for f in new_files})
    new_keys = sorted(relabel(k) for k in _project_keys(rig_home / ".claude.json") - before_keys)
    return {"memory": loaded, "transcript_dirs": new_dirs, "claude_json_new_keys": new_keys}


def _cwd_key_confirmed(base: Path, live_home: Path, logical: bool, key: str) -> dict:
    """A "none" (neither sentinel loaded) counts only if one retry agrees."""
    name = "cwd-logical" if logical else "cwd-physical"
    first = _cwd_key_case(base / f"{name}-1", live_home, logical, key)
    if first["memory"] != ["none"]:
        return first
    second = _cwd_key_case(base / f"{name}-2", live_home, logical, key)
    first["memory"] = ["none (retry agrees)"] if second["memory"] == ["none"] else \
        [f"inconclusive (retry: {','.join(second['memory'])})"]
    return first


def _version() -> str:
    try:
        return subprocess.run(["claude", "--version"], capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def _memory_case(base: Path, mode: str, live_home: Path, key: str):
    """A measurement closure; each call builds a fresh rig with a fresh sentinel."""
    attempts = iter(range(1, 100))

    def measure() -> str:
        sentinel = f"SENT-{secrets.token_hex(6)}"
        rig = build_rig(base / f"{mode}-{next(attempts)}", sentinel, mode=mode, live_home=live_home)
        return verdict(_launch(rig.home, cwd=rig.work, pwd=rig.work, key=key), sentinel)

    return measure


def run_probe(live_home: Path | None = None, key_file: Path | None = None) -> dict:
    """Run every case in a fresh temp root; the control first."""
    live_home = live_home or Path.home()
    report = {"version": _version()}
    key = resolve_api_key(key_file or KEY_FILE)
    if key is None:
        report["control"] = NO_KEY
        return report
    live_projects = live_home / ".claude" / "projects"
    live_json = live_home / ".claude.json"
    base = Path(tempfile.mkdtemp(prefix="probe-0984-"))
    base.chmod(0o700)
    # A SIGTERM must still run the finally below, so the rig never outlives the run.
    old_term = signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        _refuse_live(base, live_home)
        tag = slug_for(base)
        before_live = {p.name for p in live_projects.iterdir()} if live_projects.is_dir() else set()
        before_keys = _project_keys(live_json)
        report["control"] = _memory_case(base, "real", live_home, key)()
        if report["control"] != "loaded":
            return report
        report["symlink"] = confirm_negative(_memory_case(base, "symlink", live_home, key))
        report["cwd_logical"] = _cwd_key_confirmed(base, live_home, True, key)
        report["cwd_physical"] = _cwd_key_confirmed(base, live_home, False, key)
        after_live = {p.name for p in live_projects.iterdir()} if live_projects.is_dir() else set()
        new = [f"projects/{n}" for n in after_live - before_live if tag in n]
        new += [f".claude.json:{k}" for k in _project_keys(live_json) - before_keys if str(base) in k]
        report["live_home_new_entries"] = sorted(new)
        return report
    finally:
        shutil.rmtree(base, ignore_errors=True)
        signal.signal(signal.SIGTERM, old_term)


def main() -> int:
    if shutil.which("claude") is None:
        print("probe: no 'claude' on PATH", file=sys.stderr)
        return 2
    r = run_probe()
    print(f"{'runtime':<34} {r['version']}")
    print(f"{'auth':<34} {'none' if r['control'] == NO_KEY else 'api key from the keys directory'}")
    print(f"{'control   memory in a real file':<34} {r['control']}")
    if r["control"] != "loaded":
        print(f"probe: the control came back '{r['control']}', so this run could not look.\n"
              "       Nothing below it is a finding.", file=sys.stderr)
        return 1
    print(f"{'symlink   memory dir is a link':<34} {r['symlink']}")
    for case in ("cwd_logical", "cwd_physical"):
        c = r[case]
        label = "cwd key   $PWD=link (cd)" if case == "cwd_logical" else "cwd key   $PWD=target (cd -P)"
        print(f"{label:<34} memory={','.join(c['memory'])} "
              f"transcripts={','.join(c['transcript_dirs']) or '-'} "
              f"claude.json+={','.join(c['claude_json_new_keys']) or '-'}")
    print(f"{'live HOME entries created':<34} {', '.join(r['live_home_new_entries']) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

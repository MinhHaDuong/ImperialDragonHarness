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
with "probe could not look" and the other rows are not findings.

Auth: an ANTHROPIC_API_KEY read at run time from the keys directory (never
printed); failing that, a copy of the runtime's credentials file inside the
disposable HOME, removed with it. The table names which method ran, never the
credential. Sentinels are random per run and never printed.
"""

import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

MODEL = os.environ.get("PROBE_MODEL", "haiku")
TIMEOUT = int(os.environ.get("PROBE_TIMEOUT", "150"))
PROMPT = "Reply with the exact project codeword from your memory, or NONE."
KEY_FILE = Path(os.environ.get("PROBE_KEY_FILE", Path.home() / ".config" / "keys" / "anthropic.env"))


def slug_for(path: Path) -> str:
    """Claude Code's project-store key: every non-alphanumeric character becomes '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def detect_loaded(stdout: str, sentinel: str) -> bool:
    """True only when the reply carries the sentinel; the prompt never contains it."""
    if sentinel in PROMPT:
        raise ValueError("sentinel leaked into the prompt")
    return sentinel in stdout


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


def build_rig(root: Path, sentinel: str, mode: str = "real", live_home: Path | None = None) -> Rig:
    """Disposable HOME with a copied .claude.json and a sentinel in project memory.

    mode "real": projects/<slug>/memory is a directory. mode "symlink": it is a
    link to a directory elsewhere under root that holds the sentinel.
    """
    live_home = live_home or Path.home()
    _refuse_live(root, live_home)
    rig_home, work = root / "home", root / "work"
    (rig_home / ".claude").mkdir(parents=True)
    src = live_home / ".claude.json"
    if src.exists():
        shutil.copyfile(src, rig_home / ".claude.json")
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


def _auth(rig_home: Path, live_home: Path) -> tuple[dict, str]:
    """Environment additions for auth, and the method's name (never the value)."""
    if KEY_FILE.is_file():
        for line in KEY_FILE.read_text().splitlines():
            m = re.match(r"\s*(?:export\s+)?ANTHROPIC_API_KEY=[\"']?([^\"'\s]+)", line)
            if m:
                return {"ANTHROPIC_API_KEY": m.group(1)}, "api key from the keys directory"
    creds = live_home / ".claude" / ".credentials.json"
    if creds.is_file():
        dst = rig_home / ".claude" / ".credentials.json"
        shutil.copyfile(creds, dst)
        dst.chmod(0o600)
        return {}, "copied credentials file (removed with the rig)"
    return {}, "none found"


def _launch(rig_home: Path, cwd: Path, pwd: Path, auth: dict) -> str:
    """One headless session with a minimal environment: no parent-session variables leak in."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(rig_home),
        "TERM": "dumb",
        "LANG": "C.UTF-8",
        "PWD": str(pwd),
        **auth,
    }
    try:
        r = subprocess.run(
            ["claude", "-p", PROMPT, "--model", MODEL],
            cwd=cwd, env=env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=TIMEOUT,
        )
        return r.stdout
    except subprocess.TimeoutExpired:
        return ""


def _tree(d: Path) -> set[str]:
    return {str(p.relative_to(d)) for p in d.rglob("*")} if d.is_dir() else set()


def _project_keys(claude_json: Path) -> set[str]:
    try:
        return set(json.loads(claude_json.read_text()).get("projects", {}))
    except (OSError, ValueError):
        return set()


def _cwd_key_case(root: Path, live_home: Path, logical: bool) -> dict:
    """Launch through <home>/.idh -> <home>/.claude, the live layout in miniature."""
    _refuse_live(root, live_home)
    rig_home = root / "home"
    real = rig_home / ".claude"
    link = rig_home / ".idh"
    _git_init(real)  # the live checkout is a git repo too
    src = live_home / ".claude.json"
    if src.exists():
        shutil.copyfile(src, rig_home / ".claude.json")
    link.symlink_to(real, target_is_directory=True)
    labels = {slug_for(link): "slug(link)", slug_for(real): "slug(target)"}
    sentinels = {}
    for slug, label in labels.items():
        s = f"SENT-{secrets.token_hex(6)}"
        sentinels[label] = s
        _write_memory(real / "projects" / slug / "memory", s)
    projects = real / "projects"
    before_files, before_keys = _tree(projects), _project_keys(rig_home / ".claude.json")
    auth, method = _auth(rig_home, live_home)
    out = _launch(rig_home, cwd=link, pwd=link if logical else real, auth=auth)
    loaded = [label for label, s in sentinels.items() if detect_loaded(out, s)]

    def relabel(text: str) -> str:
        for slug, label in labels.items():
            text = text.replace(slug, label)
        return text.replace(str(rig_home), "~")

    new_files = sorted(_tree(projects) - before_files)
    new_dirs = sorted({relabel(f.split("/")[0]) for f in new_files})
    new_keys = sorted(relabel(k) for k in _project_keys(rig_home / ".claude.json") - before_keys)
    return {"memory": loaded or ["none"], "transcript_dirs": new_dirs,
            "claude_json_new_keys": new_keys, "auth": method}


def _version() -> str:
    try:
        return subprocess.run(["claude", "--version"], capture_output=True, text=True,
                              timeout=30).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def _run_memory_case(base: Path, mode: str, live_home: Path) -> tuple[str, str]:
    sentinel = f"SENT-{secrets.token_hex(6)}"
    rig = build_rig(base / mode, sentinel, mode=mode, live_home=live_home)
    auth, method = _auth(rig.home, live_home)
    out = _launch(rig.home, cwd=rig.work, pwd=rig.work, auth=auth)
    return ("loaded" if detect_loaded(out, sentinel) else "not loaded"), method


def run_probe(live_home: Path | None = None) -> dict:
    """Run every case in a fresh temp root; the control first."""
    live_home = live_home or Path.home()
    live_projects = live_home / ".claude" / "projects"
    base = Path(tempfile.mkdtemp(prefix="probe-0984-"))
    base.chmod(0o700)
    try:
        _refuse_live(base, live_home)
        tag = slug_for(base)
        before_live = {p.name for p in live_projects.iterdir()} if live_projects.is_dir() else set()
        report = {"version": _version()}
        report["control"], report["auth"] = _run_memory_case(base, "real", live_home)
        if report["control"] != "loaded":
            return report
        report["symlink"], _ = _run_memory_case(base, "symlink", live_home)
        report["cwd_logical"] = _cwd_key_case(base / "cwd-logical", live_home, logical=True)
        report["cwd_physical"] = _cwd_key_case(base / "cwd-physical", live_home, logical=False)
        after_live = {p.name for p in live_projects.iterdir()} if live_projects.is_dir() else set()
        report["live_home_new_entries"] = sorted(n for n in after_live - before_live if tag in n)
        return report
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main() -> int:
    if shutil.which("claude") is None:
        print("probe: no 'claude' on PATH", file=sys.stderr)
        return 2
    r = run_probe()
    print(f"{'runtime':<34} {r['version']}")
    print(f"{'auth':<34} {r['auth']}")
    print(f"{'control   memory in a real file':<34} {r['control']}")
    if r["control"] != "loaded":
        print("probe: the control did not load its sentinel, so this run could not look.\n"
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

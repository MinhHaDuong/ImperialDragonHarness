"""The `notify` verb of runtime.py (ticket 1312): tell the author, whatever the runtime.

    runtime.py notify --key K --title T --body B [--repeat SECONDS]

Runs `notify-send -a idh T B` where it exists, and always writes an alert file
`<alert dir>/<key>.alert` (JSON: key, title, body, time) that outlives the popup. The alert
dir is `$IDH_ALERT_DIR`, else `idh-alerts/` under the git common directory, so every worktree
of a repository shares it. A second call for the same key inside `--repeat` seconds (default
3600; 0 disables) prints `SUPPRESSED <key>` and does nothing: the rate limit of the arena
watchdog pattern, kept in `state.json` under flock as forge.py's `_update_cache`. A missing
or failing notify-send never fails the verb, since the alert file is the durable channel; the
result line says what happened. Exit 2 only when the alert dir cannot be written.

This is the documented fallback whenever `runtime.py can wake` answers no (sitrep.md).
"""

import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

NAME = "notify"
DEFAULT_MODE = "send"
DEFAULT_REPEAT = 3600.0
FAILED = 2


def register(sub) -> None:
    p = sub.add_parser(NAME, help="desktop notification plus alert file, rate limited per key")
    p.add_argument("--key", required=True, help="the condition; one notification per key per window")
    p.add_argument("--title", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--repeat", type=float, default=DEFAULT_REPEAT, metavar="S",
                   help="suppress a repeat of the same key within S seconds (default 3600; 0 never)")


def can(rt: str, mode: str, env) -> str | None:
    """Always supported: the alert file needs no desktop."""
    return None if mode == DEFAULT_MODE else f"no notify mode {mode!r}"


def alert_dir() -> str:
    override = os.environ.get("IDH_ALERT_DIR")
    if override:
        return override
    done = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
                          capture_output=True, text=True)
    if done.returncode != 0:
        raise OSError("not in a git repository and IDH_ALERT_DIR is unset")
    return os.path.join(done.stdout.strip(), "idh-alerts")


def safe_name(key: str) -> str:
    """A file name for KEY; a key that needed rewriting gets a hash suffix, so a/b and a_b stay apart."""
    name = re.sub(r"[^A-Za-z0-9._-]", "_", key).lstrip(".") or "_"
    if name == key:
        return name
    return f"{name}-{hashlib.sha1(key.encode()).hexdigest()[:8]}"


def write_atomic(path: str, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), prefix=".tmp-")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.replace(tmp, path)


def run(args, rt: str) -> int:
    try:
        adir = alert_dir()
        os.makedirs(adir, exist_ok=True)
        with open(os.path.join(adir, "state.lock"), "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state_path = os.path.join(adir, "state.json")
            try:
                with open(state_path) as f:
                    state = json.load(f)
            except (OSError, ValueError):
                state = {}
            now = time.time()
            last = state.get(args.key)
            if args.repeat > 0 and isinstance(last, (int, float)) and now - last < args.repeat:
                print(f"SUPPRESSED {args.key}")
                return 0
            alert = {"key": args.key, "title": args.title, "body": args.body, "time": now}
            write_atomic(os.path.join(adir, safe_name(args.key) + ".alert"), json.dumps(alert))
            state[args.key] = now
            write_atomic(state_path, json.dumps(state, sort_keys=True))
    except OSError as exc:
        print(f"runtime: notify: {exc}", file=sys.stderr)
        return FAILED
    return popup(args)


def popup(args) -> int:
    if not shutil.which("notify-send"):
        print(f"NOTIFIED {args.key}: alert file only (no notify-send)")
        return 0
    try:
        done = subprocess.run(["notify-send", "-a", "idh", args.title, args.body],
                              capture_output=True, text=True, timeout=10)
        ok = done.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        ok = False
    print(f"NOTIFIED {args.key}" if ok else f"NOTIFIED {args.key}: alert file only (notify-send failed)")
    return 0

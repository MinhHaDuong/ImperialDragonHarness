"""The `wake` verb of runtime.py (ticket 1311): wake the calling session later, or another now.

    runtime.py wake arm --after S --cmd CMD [--session ID]
    runtime.py wake disarm
    runtime.py wake send --session ID --message TEXT

`arm` sleeps S seconds, runs CMD under bash, then delivers `<cmd> exited <rc>: <output|(no output)>`
to the session. A bounded poll is `--after 0` with a poller CMD that exits when the
awaited status changes (merge's queued-merge wait, raid-breaker.py --wait): its exit is
the wake, whatever its exit code.

Per backend:
- Claude Code: only the session's own background tool can start the process whose exit
  re-invokes it, so `arm` prints `RUN-IN-BACKGROUND <shlex-quoted command>` and the session
  runs that command in the background. `disarm` and `send` answer NOOP (no cross-process
  path has been probed). A headless session (`claude -p`, a night sweep) answers NOOP.
- Codex: `arm` starts a transient `systemd-run --user --on-active=S` timer that runs the
  hidden `wake fire`, which runs CMD and calls `codex queue --thread <id> --message`.
  `codex queue` only queues: into an exited thread nothing runs, so the result line says
  QUEUED, never DELIVERED. Absolute paths are passed to the unit, the caller's PATH is
  set for CMD, and `--expand-environment=no` keeps systemd from blanking CMD's `${VAR}`. Without systemd-run (CI, another OS, a logged-out user without lingering)
  `arm` and `disarm` answer NOOP. Unit names carry the thread id, and `disarm` stops only
  that thread's units. `send` calls `codex queue` directly.
- Pi: an inbox, written here and read by `adapters/pi/extensions/idh-wake.ts`. The extension
  creates a per-session inbox at `session_start`, exports `$IDH_WAKE_INBOX` (so `can wake`
  answers from the extension's presence) and, when the agent is idle, delivers the oldest
  job with `pi.sendUserMessage()`, deleting it afterwards. Messages go into the directory as
  `<stamp>-<rand>.msg` (UTF-8 text, written to a dot-file then renamed); `arm` runs a
  detached `wake fire --inbox` process and records its pid in `<inbox>/.armed/`. Without
  `$IDH_WAKE_INBOX` every mode answers NOOP "extension not loaded".
"""

import argparse
import os
import re
import secrets
import shlex
import shutil
import signal
import subprocess
import sys
import time

import runtime

NAME = "wake"
DEFAULT_MODE = "arm"
MODES = ("arm", "disarm", "send")
OUTPUT_TAIL = 2000  # characters of CMD output carried in the wake message
UNIT_PREFIX = "idh-wake-"
SELF = os.path.abspath(runtime.__file__)


def register(sub) -> None:
    p = sub.add_parser(NAME, help="wake a session: arm, disarm, send")
    modes = p.add_subparsers(dest="mode", required=True)
    arm = modes.add_parser("arm", help="after S seconds run CMD and wake this session with its result")
    arm.add_argument("--after", type=float, required=True, metavar="S")
    arm.add_argument("--cmd", required=True)
    arm.add_argument("--session", help="session to wake (default: this one)")
    dis = modes.add_parser("disarm", help="cancel what arm started for this session")
    dis.add_argument("--session", help="session whose wakes to cancel (default: this one)")
    send = modes.add_parser("send", help="queue a message into a session now")
    send.add_argument("--session", required=True)
    send.add_argument("--message", required=True)
    fire = modes.add_parser("fire", help=argparse.SUPPRESS)  # the armed timer's own entry point
    fire.add_argument("--after", type=float, default=0)
    fire.add_argument("--cmd", required=True)
    fire.add_argument("--thread")
    fire.add_argument("--codex")
    fire.add_argument("--inbox")


def can(rt: str, mode: str, env) -> str | None:
    """None when `wake.<mode>` works on `rt` here, else the reason it does not."""
    if mode not in MODES:
        return f"no wake mode {mode!r} ({'|'.join(MODES)})"
    if runtime.headless(rt, env):
        return "headless: no interactive session to wake"
    if rt == "claude":
        if mode == "arm":
            return None
        return ("the session stops its own background task" if mode == "disarm"
                else "no cross-process path into a Claude Code session has been probed")
    if rt == "codex":
        if mode != "disarm" and not shutil.which("codex", path=env.get("PATH")):
            return "codex is not on PATH"
        if mode != "send" and not shutil.which("systemd-run", path=env.get("PATH")):
            return "systemd-run is not available for a detached timer"
        if mode != "send" and not env.get("CODEX_THREAD_ID"):
            return "CODEX_THREAD_ID is not set; pass --session"
        return None
    if rt == "pi":
        return None if env.get("IDH_WAKE_INBOX") else "extension not loaded (IDH_WAKE_INBOX unset)"
    return f"unknown runtime {rt!r}"


def message(cmd: str, rc: int, output: str) -> str:
    out = output.strip()
    if len(out) > OUTPUT_TAIL:
        out = "..." + out[-OUTPUT_TAIL:]
    return f"{cmd} exited {rc}: {out or '(no output)'}"


def run_cmd(cmd: str) -> str:
    """CMD runs under bash, the shell the skills' poll commands are written for ($SECONDS)."""
    shell = shutil.which("bash") or "/bin/bash"
    done = subprocess.run([shell, "-c", cmd], capture_output=True, text=True,
                          stdin=subprocess.DEVNULL)
    return message(cmd, done.returncode, done.stdout + done.stderr)


def write_inbox(inbox: str, text: str) -> str:
    os.makedirs(inbox, exist_ok=True)
    name = f"{time.strftime('%Y%m%dT%H%M%S')}-{secrets.token_hex(4)}.msg"
    tmp = os.path.join(inbox, "." + name)
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    final = os.path.join(inbox, name)
    os.replace(tmp, final)
    return final


def codex_queue(codex: str, thread: str, text: str) -> int:
    done = subprocess.run([codex, "queue", "--thread", thread, "--message", text],
                          capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if done.returncode != 0:
        print(f"wake: codex queue failed ({done.returncode}): {(done.stderr or done.stdout).strip()}",
              file=sys.stderr)
        return runtime.FAILED
    print(f"QUEUED codex {thread}")
    return runtime.DONE


def fire(a) -> int:
    """The armed timer: sleep, run CMD, deliver. Claude's background command is this, run in
    the session; its exit, with the message on stdout, is the wake."""
    if a.after > 0:
        time.sleep(a.after)
    text = run_cmd(a.cmd)
    if a.codex and a.thread:
        return codex_queue(a.codex, a.thread, text)
    if a.inbox:
        print(f"QUEUED pi {write_inbox(a.inbox, text)}")
        try:
            os.remove(os.path.join(a.inbox, ".armed", f"{os.getpid()}.pid"))
        except OSError:
            pass
        return runtime.DONE
    print(text)
    return runtime.DONE


def fire_argv(rt: str, after: float, cmd: str, *extra: str) -> list:
    return [sys.executable, SELF, "--runtime", rt, NAME, "fire", "--after", f"{after:g}", "--cmd", cmd, *extra]


def arm(a, rt: str, env) -> int:
    if rt == "claude":
        print("RUN-IN-BACKGROUND " + shlex.join(fire_argv(rt, a.after, a.cmd)))
        return runtime.DONE
    if rt == "codex":
        thread = a.session or env["CODEX_THREAD_ID"]
        codex = shutil.which("codex", path=env.get("PATH"))
        unit = f"{unit_stem(thread)}{secrets.token_hex(4)}"
        argv = [shutil.which("systemd-run", path=env.get("PATH")), "--user", "--quiet", "--collect",
                "--expand-environment=no",
                f"--on-active={max(a.after, 1):g}", f"--unit={unit}", f"--working-directory={os.getcwd()}",
                f"--setenv=PATH={env.get('PATH', '')}",
                *fire_argv(rt, 0, a.cmd, "--thread", thread, "--codex", codex)]
        done = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if done.returncode != 0:
            print(f"wake: systemd-run failed ({done.returncode}): {(done.stderr or done.stdout).strip()}",
                  file=sys.stderr)
            return runtime.FAILED
        print(f"ARMED codex {unit} thread={thread} after={a.after:g}s")
        return runtime.DONE
    inbox = env["IDH_WAKE_INBOX"]
    proc = subprocess.Popen(fire_argv(rt, a.after, a.cmd, "--inbox", inbox), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    armed = os.path.join(inbox, ".armed")
    os.makedirs(armed, exist_ok=True)
    open(os.path.join(armed, f"{proc.pid}.pid"), "w").close()
    print(f"ARMED pi pid={proc.pid} after={a.after:g}s")
    return runtime.DONE


def unit_stem(thread: str) -> str:
    """Unit names carry the thread, so one session's disarm never cancels another's wakes."""
    return f"{UNIT_PREFIX}{re.sub(r'[^A-Za-z0-9_-]', '_', thread)}-"


def disarm(a, rt: str, env) -> int:
    if rt == "codex":
        ctl = shutil.which("systemctl", path=env.get("PATH")) or "systemctl"
        stem = unit_stem(a.session or env["CODEX_THREAD_ID"])
        done = subprocess.run([ctl, "--user", "stop", f"{stem}*.timer", f"{stem}*.service"],
                              capture_output=True, text=True, stdin=subprocess.DEVNULL)
        if done.returncode != 0:
            print(f"wake: systemctl stop failed: {(done.stderr or done.stdout).strip()}", file=sys.stderr)
            return runtime.FAILED
        print("DISARMED codex")
        return runtime.DONE
    armed = os.path.join(env["IDH_WAKE_INBOX"], ".armed")
    stopped = 0
    for name in sorted(os.listdir(armed)) if os.path.isdir(armed) else []:
        try:
            os.killpg(int(name.removesuffix(".pid")), signal.SIGTERM)
            stopped += 1
        except (ValueError, ProcessLookupError, PermissionError):
            pass
        os.remove(os.path.join(armed, name))
    print(f"DISARMED pi {stopped}")
    return runtime.DONE


def send(a, rt: str, env) -> int:
    if rt == "codex":
        return codex_queue(shutil.which("codex", path=env.get("PATH")), a.session, a.message)
    print(f"QUEUED pi {write_inbox(env['IDH_WAKE_INBOX'], a.message)}")
    return runtime.DONE


def run(a, rt: str, env=None) -> int:
    env = os.environ if env is None else env
    if a.mode == "fire":
        return fire(a)
    seen = {**env, "CODEX_THREAD_ID": a.session} if a.mode != "send" and a.session else env
    reason = can(rt, a.mode, seen)
    if reason:
        return runtime.noop(f"wake {a.mode}", rt, reason)
    if a.mode == "arm":
        return arm(a, rt, env)
    if a.mode == "disarm":
        return disarm(a, rt, env)
    return send(a, rt, env)

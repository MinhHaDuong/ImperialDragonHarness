"""The `session` verb of runtime.py (ticket 1314): which session this is, and whether it is headless.

    runtime.py session id        print the runtime's own session id
    runtime.py session headless  print yes or no

Per backend: Claude Code `CLAUDE_CODE_SESSION_ID`, Codex `CODEX_THREAD_ID`, Pi exports none
(`id` answers NOOP). A runtime that should have an id but exports none (`CLAUDECODE` without
`CLAUDE_CODE_SESSION_ID`) exits 3, never an empty line. `headless` is yes for `claude -p`
(an sdk entrypoint), a night sweep (`CLAUDE_NIGHT_SWEEP`) or a child session
(`CLAUDE_CODE_CHILD_SESSION`); `can wake` depends on it. `runtime.py which` and the wake verb
read the same two helpers, defined here.

The hooks keep reading their payloads and `CLAUDE_*` variables (shrink recorded in ticket 1314).
"""

NAME = "session"
DEFAULT_MODE = "id"
MODES = ("id", "headless")
ID_KEYS = {"claude": "CLAUDE_CODE_SESSION_ID", "codex": "CODEX_THREAD_ID"}


def session_id(rt: str, env):
    """The runtime's own session id, or None when it does not export one."""
    key = ID_KEYS.get(rt)
    return (env.get(key) or None) if key else None


def headless(rt: str, env) -> bool:
    """True when no interactive session is there to wake: `claude -p` (an sdk entrypoint),
    a night sweep or a child session. Subagents and forks of a live session are not headless."""
    if env.get("CLAUDE_NIGHT_SWEEP"):
        return True
    if rt == "claude":
        return env.get("CLAUDE_CODE_ENTRYPOINT", "").startswith("sdk") or bool(env.get("CLAUDE_CODE_CHILD_SESSION"))
    return False


def register(sub) -> None:
    p = sub.add_parser(NAME, help="session id | headless")
    p.add_argument("mode", choices=MODES)


def can(rt: str, mode: str, env) -> str | None:
    if mode not in MODES:
        return f"no session mode {mode!r} ({'|'.join(MODES)})"
    if mode == "id" and rt not in ID_KEYS:
        return f"{rt} exports no session id"
    return None


def run(args, rt: str) -> int:
    import os
    import sys

    import runtime

    if args.mode == "headless":
        print("yes" if headless(rt, os.environ) else "no")
        return runtime.DONE
    reason = can(rt, "id", os.environ)
    if reason:
        return runtime.noop("session id", rt, reason)
    sid = session_id(rt, os.environ)
    if not sid:
        print(f"runtime: {rt} session id not exported ({ID_KEYS[rt]} unset)", file=sys.stderr)
        return runtime.UNREAD
    print(sid)
    return runtime.DONE

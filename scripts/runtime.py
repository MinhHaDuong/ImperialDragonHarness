#!/usr/bin/env python3
"""The runtime adapter: every runtime-specific action behind one CLI (tickets 1309, 1311).

    runtime.py [--runtime auto|claude|codex|pi] which
    runtime.py [--runtime ...] can <verb>[.<mode>]
    runtime.py [--runtime ...] <verb> ...

The runtime twin of forge.py. `--runtime auto` (the default) reads the runtime's own
markers and never guesses: no marker, or the markers of two runtimes at once (a Codex
child of a Claude session inherits CLAUDECODE), exits 3. A caller in a nested child
passes `--runtime` explicitly.

Markers: Claude Code `CLAUDECODE` or `CLAUDE_CODE_SESSION_ID`; Codex `CODEX_THREAD_ID`;
Pi `PI_CODING_AGENT=true` or `AI_AGENT=pi` (Claude Code also sets AI_AGENT, to its own
name, so only the value `pi` counts).

Exit codes, as forge.py and merge-gate.py: 0 done, 1 NOOP (unsupported here, one line
`NOOP <verb> <runtime>: <reason>` on stdout), 2 refused or failed, 3 could not read.
One-line results on stdout, diagnostics on stderr.

`which` prints `runtime=<rt> session=<id|-> headless=<yes|no>`. `can <verb>[.<mode>]`
exits 0 yes, 1 no (with the NOOP line), 3 cannot tell; a bare verb asks for its default
mode. Verbs live in sibling modules imported into VERBS; each exports `NAME`, `DEFAULT_MODE`,
`register(subparsers)`, `can(rt, mode, env) -> str | None` (None: supported, else the
reason it is not) and `run(args, rt) -> int`. Adding a verb is one line in VERBS.
Stdlib only.
"""

import argparse
import os
import sys

import runtime_notify
import runtime_session
import runtime_wake

DONE, NOOP, FAILED, UNREAD = 0, 1, 2, 3
RUNTIMES = ("claude", "codex", "pi")

# The verb modules, listed explicitly (ticket 1311 blind-spot amendment: a stray file never
# changes behaviour). A later verb (notify 1312, launch 1313, session 1314) adds its import
# above and one line here.
VERBS = [
    runtime_notify,
    runtime_session,
    runtime_wake,
]


class Unreadable(Exception):
    """The runtime cannot be told; the message says why (exit 3)."""


def markers(env) -> list:
    """The runtimes whose markers are present in `env`, in RUNTIMES order."""
    found = []
    if env.get("CLAUDECODE") or env.get("CLAUDE_CODE_SESSION_ID"):
        found.append("claude")
    if env.get("CODEX_THREAD_ID"):
        found.append("codex")
    if env.get("PI_CODING_AGENT", "").lower() == "true" or env.get("AI_AGENT", "").lower() == "pi":
        found.append("pi")
    return found


def detect(env=None) -> str:
    """The runtime named by its markers; raises Unreadable on none or several."""
    env = os.environ if env is None else env
    found = markers(env)
    if not found:
        raise Unreadable("no runtime markers in the environment; pass --runtime")
    if len(found) > 1:
        raise Unreadable(f"markers of {' and '.join(found)} at once (a nested runtime?); pass --runtime")
    return found[0]


def resolve(choice: str | None, env=None) -> str:
    choice = choice or "auto"
    if choice == "auto":
        return detect(env)
    if choice not in RUNTIMES:
        raise Unreadable(f"unknown runtime {choice!r} (auto|{'|'.join(RUNTIMES)})")
    return choice


def session_id(rt: str, env=None):
    """The runtime's own session id, or None (defined in runtime_session)."""
    return runtime_session.session_id(rt, os.environ if env is None else env)


def headless(rt: str, env=None) -> bool:
    """True when no interactive session is there to wake (defined in runtime_session)."""
    return runtime_session.headless(rt, os.environ if env is None else env)


def noop(verb: str, rt: str, reason: str) -> int:
    print(f"NOOP {verb} {rt}: {reason}")
    return NOOP


def verb_modules() -> dict:
    return {mod.NAME: mod for mod in VERBS}


def can(spec: str, rt: str, env=None, mods=None) -> int:
    env = os.environ if env is None else env
    mods = verb_modules() if mods is None else mods
    verb, _, mode = spec.partition(".")
    mod = mods.get(verb)
    if mod is None:
        return noop(f"can {spec}", rt, f"no verb {verb!r} in runtime.py")
    reason = mod.can(rt, mode or mod.DEFAULT_MODE, env)
    if reason:
        return noop(f"can {spec}", rt, reason)
    print(f"YES {spec} {rt}")
    return DONE


def main(argv=None) -> int:
    mods = verb_modules()
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--runtime", default="auto", help="auto|claude|codex|pi")
    sub = p.add_subparsers(dest="verb", required=True)
    sub.add_parser("which", help="print the detected runtime")
    sub.add_parser("can", help="exit 0 when <verb>[.<mode>] works here").add_argument("spec")
    for mod in mods.values():
        mod.register(sub)
    a = p.parse_args(argv)
    try:
        rt = resolve(a.runtime)
    except Unreadable as exc:
        print(f"runtime: {exc}", file=sys.stderr)
        return UNREAD
    if a.verb == "which":
        print(f"runtime={rt} session={session_id(rt) or '-'} headless={'yes' if headless(rt) else 'no'}")
        return DONE
    if a.verb == "can":
        return can(a.spec, rt, mods=mods)
    return mods[a.verb].run(a, rt)


if __name__ == "__main__":
    sys.exit(main())

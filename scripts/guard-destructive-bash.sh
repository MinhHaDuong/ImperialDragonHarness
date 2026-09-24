#!/bin/bash
set -euo pipefail
# PreToolUse(Bash) hook: block `git reset --hard` on a dirty tree, and nothing
# else. Exit 0 = allow, exit 2 = deny with a message on stderr.
#
# Why only this (ticket 0976): the 2026-09-24 transcript audit found one firing
# of the former catch-all guard that prevented real damage, a `reset --hard`
# over a primary checkout holding uncommitted settings.json and shell-init.sh
# (2026-06-18). Its recursive-rm, force-push, clean, sudo-rm and DROP clauses
# fired hundreds of times with no true positive, and one block provoked a worse
# `git checkout -- file`. So the hook asks the one question that separates the
# harmful case from the harmless one: would this reset discard tracked changes?
#
# The target tree is where the reset acts: the payload's cwd, moved by any
# `cd DIR` earlier in the same command line and by `git -C DIR`. Only
# uncommitted changes to tracked files count (`--untracked-files=no`), because
# `reset --hard` leaves untracked files alone. A tree git cannot read allows:
# the reset would fail there on its own.
#
# The command is tokenised with shlex after heredoc bodies are dropped, so
# "reset --hard" inside a quoted string, a commit message or a heredoc is text,
# not a command. Not parsed: a command nested in `bash -c '...'` or `eval`;
# the guard is a seatbelt for the common shape, not a sandbox.
#
# Fail-open: a payload it cannot parse, or a missing python3, allows. A guard
# that denies on its own breakage blocks every Bash call.

command -v python3 >/dev/null 2>&1 || exit 0

# The program is passed with -c so that stdin stays the hook payload.
read -r -d '' PROG <<'PY' || true
import json
import os
import re
import shlex
import subprocess
import sys

SEPARATORS = {";", "&&", "||", "|", "&", "(", ")", "|&", ";;", "{", "}"}
PREFIXES = {"rtk", "command", "env", "sudo", "time", "nice", "exec"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def strip_heredocs(text):
    """Drop heredoc bodies: every line after `<<WORD` up to the line `WORD`."""
    out, terminators = [], []
    for line in text.split("\n"):
        if terminators:
            if line.strip() == terminators[0]:
                terminators.pop(0)
            continue
        out.append(line)
        terminators.extend(m.group(2) for m in HEREDOC.finditer(line))
    return "\n".join(out)


def simple_commands(text):
    lexer = shlex.shlex(strip_heredocs(text).replace("\n", " ; "),
                        posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    cmd = []
    for tok in lexer:
        if tok in SEPARATORS:
            if cmd:
                yield cmd
            cmd = []
        else:
            cmd.append(tok)
    if cmd:
        yield cmd


def resolve(base, path):
    return os.path.normpath(os.path.join(base, os.path.expanduser(path)))


def reset_hard_target(argv, cwd):
    """The directory a `git ... reset --hard` acts on, or None."""
    i = 0
    while i < len(argv) and ("=" in argv[i] and not argv[i].startswith("-")
                             or argv[i] in PREFIXES):
        i += 1  # VAR=value assignments and transparent launchers
    if i >= len(argv) or os.path.basename(argv[i]) != "git":
        return None
    i += 1
    target = cwd
    while i < len(argv) and argv[i].startswith("-"):
        opt = argv[i]
        if opt == "-C" and i + 1 < len(argv):
            target = resolve(target, argv[i + 1])
            i += 2
        elif opt in ("-c", "--git-dir", "--work-tree", "--namespace") and i + 1 < len(argv):
            i += 2
        else:
            i += 1
    if i < len(argv) and argv[i] == "reset" and "--hard" in argv[i + 1:]:
        return target
    return None


def dirty(path):
    try:
        res = subprocess.run(
            ["git", "-C", path, "status", "--porcelain", "--untracked-files=no"],
            capture_output=True, text=True, timeout=4,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return res.returncode == 0 and res.stdout.strip() != ""


def main():
    try:
        payload = json.load(sys.stdin)
        command = payload["tool_input"]["command"]
    except Exception:
        return 0
    if not isinstance(command, str) or "--hard" not in command:
        return 0
    cwd = payload.get("cwd") or os.getcwd()
    try:
        commands = list(simple_commands(command))
    except ValueError:
        return 0  # unbalanced quotes: not a shape this guard can read
    for argv in commands:
        if argv[0] == "cd":
            dirs = [a for a in argv[1:] if not a.startswith("-")]
            cwd = resolve(cwd, dirs[0] if dirs else "~")
            continue
        target = reset_hard_target(argv, cwd)
        if target and dirty(target):
            print(
                f"BLOCKED: git reset --hard would discard uncommitted changes to "
                f"tracked files in {target}. Commit them first (a WIP commit), or "
                "restore single files deliberately; never a stash round-trip, the "
                "stash stack is repo-global.",
                file=sys.stderr,
            )
            return 2
    return 0


sys.exit(main())
PY

exec python3 -c "$PROG"

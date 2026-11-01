"""Conditional rules for Codex and Pi: Claude Code's `paths:` loading, handrolled (ticket 1424).

Claude Code loads a rule whose frontmatter declares `paths:` when the session
touches a matching file (rules/README.md § Loading per runtime). Codex and Pi
do not. This hook reads the payload a Codex PostToolUse hook or the Pi
extension hands it on stdin, collects the file paths the tool call touched,
and returns, as hookSpecificOutput.additionalContext, the body of every
conditional rule a path matches that this session and agent has not had yet.

Paths come from `tool_input.path` / `tool_input.file_path` (Pi read, write,
edit) and from a shell command (`tool_input.command`): its words that name an
existing file, and `*** Add/Update File:` patch headers. A glob matches the
path relative to the project root (git top level of the payload's cwd), as
Claude's do. Bodies arrive with frontmatter and HTML comments stripped, as the
1413 generator ships the resident ones. Resident and catch-all rules are
already in the generated AGENTS.md and never repeat here.

Every outcome is logged to ${XDG_STATE_HOME:-~/.local/state}/idh/conditional-rules/log.
Fails open: any error leaves stdout empty and exits 0.
"""

import argparse
import fcntl
import functools
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

LOG = logging.getLogger("conditional_rules")
SAFE_ID = re.compile(r"[A-Za-z0-9_.-]+")
PATCH_HEADER = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+?)\s*$|^\*\*\* Move to: (.+?)\s*$", re.M)
MAX_WORDS = 400
PUNCT = set("&|;<>()\n")
KEEP_START = {"then", "do", "else", "elif", "if", "while", "until", "!", "{", "time"}


def glob_regex(glob: str) -> re.Pattern[str]:
    """A `paths:` glob as a regex: `**` spans directories, `*` and `?` do not, `{a,b}` alternates."""
    g = glob.strip()
    if g.startswith("./"):
        g = g[2:]
    out, i = [], 0
    while i < len(g):
        if g.startswith("**/", i):
            out.append("(?:[^/]*/)*")
            i += 3
        elif g.startswith("/**", i) and i + 3 == len(g):
            out.append("(?:/.*)?")
            i += 3
        elif g.startswith("**", i):
            out.append(".*")
            i += 2
        elif g[i] == "*":
            out.append("[^/]*")
            i += 1
        elif g[i] == "?":
            out.append("[^/]")
            i += 1
        elif g[i] == "{" and "}" in g[i:]:
            end = g.index("}", i)
            out.append("(?:" + "|".join(re.escape(a) for a in g[i + 1 : end].split(",")) + ")")
            i = end + 1
        else:
            out.append(re.escape(g[i]))
            i += 1
    return re.compile("".join(out))


def glob_matches(glob: str, path: str) -> bool:
    return glob_regex(glob).fullmatch(path) is not None


def rule_index(rules: Path) -> list[tuple[str, list[str]]]:
    """(rule id relative to rules/, globs) for each conditional rule."""
    import resident_census as rc  # noqa: PLC0415  (yaml-backed; imported only when rules exist)

    out = []
    for p in sorted(rules.rglob("*.md")):
        globs = rc.rule_globs(p)
        if globs and not rc.is_catch_all(p):
            out.append((p.relative_to(rules).as_posix(), globs))
    return out


def rule_body(path: Path) -> str:
    import resident_census as rc  # noqa: PLC0415
    import skill_frontmatter  # noqa: PLC0415

    text = rc.loaded_rule_text(path)
    return skill_frontmatter.FRONTMATTER.sub("", text, count=1).strip()


def command_paths(command: str, cwd: Path) -> list[Path]:
    """Paths a shell command may name, each resolved against the directory a
    preceding `cd` in the same command moved to, plus patch-header paths."""
    found = [cwd / (a or b) for a, b in PATCH_HEADER.findall(command)]
    # posix=False keeps quotes on a token, so a quoted ')' or ';' stays a word;
    # a newline separates commands as ';' does
    lexer = shlex.shlex(command, posix=False, punctuation_chars="();<>|&\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()
    base, stack, at_start, after_cd = cwd, [], True, False
    for tok in tokens[:MAX_WORDS]:
        quoted = len(tok) > 1 and tok[0] in "'\"" and tok[-1] == tok[0]
        w = tok[1:-1] if quoted else tok
        if not quoted and set(w) <= PUNCT:  # a separator: the next word starts a command
            if after_cd:
                base = Path.home()  # a bare cd goes home
            for ch in w:
                if ch == "(":
                    stack.append(base)
                elif ch == ")" and stack:
                    base = stack.pop()  # a subshell's cd ends with it
            at_start, after_cd = True, False
            continue
        if after_cd:
            if w.startswith("-") and w != "-":  # cd -P, cd --: the directory follows
                continue
            after_cd = False
            if w != "-":  # cd - returns to an OLDPWD this parser does not know
                base = base / os.path.expanduser(os.path.expandvars(w))
            continue
        if at_start and not quoted and w == "cd":
            after_cd = True
            continue
        if at_start and not quoted and w in KEEP_START:
            continue  # then cd, do cd, ! cd: the command slot is still open
        at_start = False
        w = re.sub(r"^--?[A-Za-z0-9-]+=", "", w)
        if w and not w.startswith("-") and len(w) < 4096:
            found.append(base / os.path.expanduser(w))
    return found


@functools.lru_cache(maxsize=256)
def git_root(path: Path) -> Path | None:
    try:
        top = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=3).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        top = ""
    return Path(top) if top else None


def touched(tool_input: dict, cwd: Path, root: Path) -> list[str]:
    """Paths touched by the call, relative to their project root. A file outside
    the session's project matches from its own repository root; outside any
    repository, from `/`, where only `**/` globs can reach it."""
    named = [cwd / os.path.expanduser(r) for r in (tool_input.get(k) for k in ("path", "file_path"))
             if isinstance(r, str) and r]
    cmd = tool_input.get("command")
    words = command_paths(cmd, cwd) if isinstance(cmd, str) else []
    out = []
    for p in named + words:
        # a direct path tool may name a file it just deleted; a shell word must name a file
        if p not in named and not p.is_file():
            continue
        p = Path(os.path.normpath(p))
        own = root if p.is_relative_to(root) else git_root(p.parent)
        rel = p.relative_to(own).as_posix() if own and p.is_relative_to(own) else p.as_posix().lstrip("/")
        if rel not in out:
            out.append(rel)
    return out


def project_root(cwd: Path) -> Path:
    return git_root(cwd) or cwd


def log_line(state: Path, outcome: str, session: str = "-", rules: str = "-") -> None:
    try:
        with open(state / "log", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {outcome} rules={rules} session={session}\n")
    except OSError:
        pass


def respond(payload: object, rules: Path, state: Path) -> str:
    """The hook's stdout for one payload: a JSON object, or empty."""
    if not isinstance(payload, dict):
        log_line(state, "parse-error")
        return ""
    tin = payload.get("tool_input")
    session = str(payload.get("session_id") or "nosession")
    agent = str(payload.get("agent_id") or "main")
    if not isinstance(tin, dict):
        return ""
    if not SAFE_ID.fullmatch(session + agent):
        log_line(state, "bad-session", session[:40].replace(" ", "_"))
        return ""
    cwd = Path(str(payload.get("cwd") or "."))
    paths = touched(tin, cwd, project_root(cwd))
    if not paths or not rules.is_dir():
        return ""
    index = dict(rule_index(rules))
    hits: dict[str, str] = {}
    for rid, globs in index.items():
        for path in paths:
            if any(glob_matches(g, path) for g in globs):
                hits.setdefault(rid, path)
                break
    if not hits:
        return ""
    marker = state / f"{session}-{agent}"
    with open(marker, "a+", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # two tool calls ending together deliver once
        f.seek(0)
        seen = set(f.read().split())
        new = [r for r in hits if r not in seen]
        if not new:
            log_line(state, "already-delivered", session, ",".join(hits))
            return ""
        parts = [
            f"Conditional rule rules/{rid} (paths: {', '.join(index[rid])}), "
            f"loaded because this session touched {hits[rid]}:\n\n{rule_body(rules / rid)}"
            for rid in new
        ]
        f.write("".join(r + "\n" for r in new))  # only once every body was read
    log_line(state, "delivered", session, ",".join(new))
    event = payload.get("hook_event_name") or "PostToolUse"
    return json.dumps({"hookSpecificOutput": {"hookEventName": event,
                                              "additionalContext": "\n\n".join(parts)}})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rules-dir", type=Path,
                    default=Path(os.environ.get("IDH_RULES_DIR") or HERE.parent / "rules"))
    ap.add_argument("--state-dir", type=Path,
                    default=Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state")
                    / "idh" / "conditional-rules")
    args = ap.parse_args(argv)
    try:
        args.state_dir.mkdir(parents=True, exist_ok=True)
        raw = sys.stdin.read()
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = None
        out = respond(payload, args.rules_dir, args.state_dir)
    except Exception:  # noqa: BLE001  fail-open: a broken hook must never break a tool call
        LOG.debug("conditional rules failed", exc_info=True)
        return 0
    if out:
        sys.stdout.write(out + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

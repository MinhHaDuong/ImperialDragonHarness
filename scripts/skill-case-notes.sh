#!/bin/bash
# PostToolUse hook on Skill and UserPromptSubmit hook: push the project's case note for the skill (ticket 1394).
#
# Reads `memory/skills/<skill>.md` from the project repository holding the
# payload's cwd and returns it as additionalContext, once per session and
# agent (marker file). Every outcome is logged to
# ${XDG_STATE_HOME:-~/.local/state}/idh/skill-notes/log, so a missing note and a
# hook that never fired stay distinguishable. Design:
# conception/2026-10-31-skill-case-notes.md. Fails open: always exit 0.
set -euo pipefail
trap 'exit 0' EXIT

payload=$(cat 2>/dev/null) || payload=""
# UserPromptSubmit fires on every prompt: bail out before python or git unless
# the prompt starts with "/" (a typed skill command). Cheap pre-filter only;
# python re-checks exactly.
if [[ "$payload" == *'"hook_event_name":"UserPromptSubmit"'* ]] &&
   ! [[ "$payload" =~ \"prompt\"[[:space:]]*:[[:space:]]*\"/ ]]; then
    exit 0
fi
dir="${XDG_STATE_HOME:-$HOME/.local/state}/idh/skill-notes"
mkdir -p "$dir" 2>/dev/null || exit 0

SKILL_NOTES_DIR="$dir" PAYLOAD="$payload" python3 -I - <<'PY' 2>/dev/null || true
import json, os, re, subprocess, sys, time

d = os.environ["SKILL_NOTES_DIR"]

def log(outcome, skill="-", session="-", agent="-"):
    line = f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {outcome} skill={skill} session={session} agent={agent}\n"
    try:
        with open(os.path.join(d, "log"), "a") as f:
            f.write(line)
    except OSError:
        pass

try:
    p = json.loads(os.environ["PAYLOAD"])
    if not isinstance(p, dict):
        raise ValueError
except ValueError:
    log("parse-error")
    sys.exit(0)

event = p.get("hook_event_name")
if event == "UserPromptSubmit":
    prompt = p.get("prompt")
    if not isinstance(prompt, str) or not prompt.startswith("/"):
        sys.exit(0)
    name = prompt[1:].split(None, 1)[0] if prompt[1:].strip() else None
else:
    event = "PostToolUse"
    tin = p.get("tool_input")
    name = tin.get("skill") if isinstance(tin, dict) else None
session = str(p.get("session_id") or "nosession")
agent = str(p.get("agent_id") or "main")
if not isinstance(name, str) or not name:
    log("no-skill-name", session=session, agent=agent)
    sys.exit(0)
name = name.rsplit(":", 1)[-1]
if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name) or not re.fullmatch(r"[A-Za-z0-9_.-]+", session + agent):
    log("bad-name", name[:40].replace(" ", "_"), session[:40], agent[:40])
    sys.exit(0)

try:
    root = subprocess.run(["git", "-C", str(p.get("cwd") or "."), "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, timeout=3).stdout.strip()
except (OSError, subprocess.SubprocessError):
    root = ""
note = os.path.join(root, "memory", "skills", name + ".md") if root else ""
try:
    text = open(note, encoding="utf-8").read() if note else None
except (OSError, UnicodeDecodeError):
    text = None
if not text or not text.strip():
    log("no-note", name, session, agent)
    sys.exit(0)

marker = os.path.join(d, f"{session}-{agent}")
try:
    seen = open(marker).read().split()
except OSError:
    seen = []
if name in seen:
    log("already-delivered", name, session, agent)
    sys.exit(0)

if len(text.split()) > 400:
    text = " ".join(text.split()[:400]) + " [truncated]"
try:
    with open(marker, "a") as f:
        f.write(name + "\n")
except OSError:
    pass
ctx = f"Case notes for skill {name}, from this project's memory:\n\n{text.strip()}"
print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": ctx}}))
log("delivered", name, session, agent)
PY
exit 0

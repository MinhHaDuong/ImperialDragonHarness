"""Per-roar window measurement across Claude Code, Codex and Pi transcripts.

Window: from the genuine user prompt (or Skill call) that invokes roar to the
next genuine user prompt, or the end of the session/turn. A model call is one
API response (Claude Code: distinct message.id; Codex: token_count event;
Pi: assistant message with usage). Prints TSV.
"""

import glob
import json
import os
import re
import socket

CUT = "2026-10-12T13:58"
HOST = socket.gethostname()
INVOKE = re.compile(r"(^|[\s,])[/$]roar\b|<command-name>/roar</command-name>", re.I)


def texts(c):
    if isinstance(c, str):
        yield c
    elif isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") in ("text", "input_text"):
                yield b.get("text") or ""


def genuine_prompt(t):
    # A typed prompt: short, not a replayed transcript or tool dump.
    s = t.strip()
    return 0 < len(s) < 400 and not re.match(
        r"^(\[|user:|assistant:|Retained|<local-command|<task-notification|Caveat:)", s
    )


def emit(rt, start, project, calls, combined):
    if not calls:
        return
    ctx0 = calls[0][0] + calls[0][1] + calls[0][2]
    cr = sum(c[1] for c in calls)
    cw = sum(c[2] for c in calls)
    unc = sum(c[0] for c in calls)
    print(
        "\t".join(
            map(
                str,
                [
                    HOST,
                    rt,
                    start[:16],
                    len(calls),
                    ctx0,
                    cr,
                    cw,
                    unc,
                    int(combined),
                    project,
                ],
            )
        )
    )


def claude():
    for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
        try:
            rows = [json.loads(line) for line in open(f, errors="replace")]
        except Exception:
            continue
        proj = os.path.basename(os.path.dirname(f))
        start, calls, seen, combined = None, [], set(), False
        for d in rows:
            if d.get("isSidechain"):
                continue
            ts = d.get("timestamp", "")
            m = d.get("message") or {}
            if d.get("type") == "user" and not d.get("isMeta"):
                c = m.get("content")
                is_tool = isinstance(c, list) and any(
                    isinstance(b, dict) and b.get("type") == "tool_result" for b in c
                )
                if is_tool:
                    continue
                txt = " ".join(texts(c))
                if start and genuine_prompt(txt) or (start and "<command-name>" in txt):
                    emit("claude", start, proj, calls, combined)
                    start = None
                if (
                    start is None
                    and ts >= CUT
                    and INVOKE.search(txt)
                    and (genuine_prompt(txt) or "<command-name>/roar" in txt)
                ):
                    start, calls, seen = ts, [], set()
                    combined = not re.fullmatch(
                        r"\s*[/$]roar\s*|.*<command-name>/roar</command-name>.*",
                        txt,
                        re.S,
                    )
            elif d.get("type") == "assistant":
                if start is None and ts >= CUT:
                    for b in m.get("content") or []:
                        if (
                            isinstance(b, dict)
                            and b.get("type") == "tool_use"
                            and b.get("name") == "Skill"
                            and (b.get("input") or {}).get("skill") == "roar"
                        ):
                            start, calls, seen, combined = ts, [], set(), True
                if start and m.get("id") and m["id"] not in seen:
                    seen.add(m["id"])
                    u = m.get("usage") or {}
                    calls.append(
                        (
                            u.get("input_tokens", 0),
                            u.get("cache_read_input_tokens", 0),
                            u.get("cache_creation_input_tokens", 0),
                        )
                    )
        if start:
            emit("claude", start, proj, calls, combined)


def codex():
    for f in glob.glob(
        os.path.expanduser("~/.codex/sessions/**/*.jsonl"), recursive=True
    ):
        rows = [json.loads(line) for line in open(f, errors="replace")]
        cwd = next(
            (
                r["payload"].get("cwd", "")
                for r in rows
                if r.get("type") == "session_meta"
            ),
            "",
        )
        start, calls, combined, last = None, [], False, None
        for d in rows:
            p, ts = d.get("payload") or {}, d.get("timestamp", "")
            if (
                d.get("type") == "response_item"
                and p.get("type") == "message"
                and p.get("role") == "user"
            ):
                txt = " ".join(texts(p.get("content")))
                if not genuine_prompt(txt):
                    continue
                if start:
                    emit("codex", start, cwd, calls, combined)
                    start = None
                if ts >= CUT and INVOKE.search(txt):
                    start, calls, last = ts, [], None
                    combined = (
                        not re.fullmatch(r"\s*\$roar\b.*", txt, re.S)
                        or len(txt.strip()) > 20
                    )
            elif (
                start
                and d.get("type") == "event_msg"
                and p.get("type") == "token_count"
            ):
                u = ((p.get("info") or {}).get("last_token_usage")) or {}
                key = json.dumps(u, sort_keys=True)
                if u and key != last:
                    last = key
                    cached = u.get("cached_input_tokens", 0)
                    calls.append((u.get("input_tokens", 0) - cached, cached, 0))
        if start:
            emit("codex", start, cwd, calls, combined)


def pi():
    for f in glob.glob(
        os.path.expanduser("~/.pi/agent/sessions/**/*.jsonl"), recursive=True
    ):
        rows = [json.loads(line) for line in open(f, errors="replace")]
        cwd = next((r.get("cwd", "") for r in rows if r.get("type") == "session"), "")
        start, calls, combined = None, [], False
        for d in rows:
            m, ts = d.get("message") or {}, d.get("timestamp", "")
            if m.get("role") == "user":
                txt = " ".join(texts(m.get("content")))
                if not genuine_prompt(txt):
                    continue
                if start:
                    emit("pi", start, cwd, calls, combined)
                    start = None
                if ts >= CUT and INVOKE.search(txt):
                    start, calls, combined = ts, [], len(txt.strip()) > 6
            elif start and m.get("role") == "assistant":
                u = m.get("usage") or {}
                calls.append(
                    (u.get("input", 0), u.get("cacheRead", 0), u.get("cacheWrite", 0))
                )
        if start:
            emit("pi", start, cwd, calls, combined)


claude()
codex()
pi()

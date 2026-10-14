"""Claude Code roar windows since 2026-09-01, with the pre-roar session shape
and the tool calls inside the window. One JSON object per roar."""
import glob, json, os, re, socket

SINCE = "2026-09-01"
HOST = socket.gethostname()
INVOKE = re.compile(r"(^|[\s,])[/$]roar\b|<command-name>/roar</command-name>", re.I)


def texts(c):
    if isinstance(c, str):
        yield c
    elif isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "text":
                yield b.get("text") or ""


def genuine(t):
    s = t.strip()
    return 0 < len(s) < 400 and not re.match(r"^(\[|user:|assistant:|Retained|<local-command|<task-notification|Caveat:)", s)


def tool_label(b):
    n, i = b.get("name"), b.get("input") or {}
    if n == "Bash":
        return "Bash: " + (i.get("command") or "").strip().splitlines()[0][:90] if i.get("command") else "Bash"
    if n in ("Read", "Edit", "Write"):
        return f"{n}: {os.path.basename(i.get('file_path', ''))}"
    if n == "Skill":
        return "Skill: " + str(i.get("skill"))
    if n == "Agent":
        return "Agent: " + str(i.get("description", ""))[:40]
    return n


for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    try:
        rows = [json.loads(l) for l in open(f, errors="replace")]
    except Exception:
        continue
    proj = os.path.basename(os.path.dirname(f))
    pre_ids, compacted, roar = set(), 0, None
    out = []

    def close():
        if roar and roar["calls"]:
            out.append(roar)

    for d in rows:
        if d.get("isSidechain"):
            continue
        ts, m = d.get("timestamp", ""), d.get("message") or {}
        if d.get("type") == "system" and d.get("subtype") == "compact_boundary" or d.get("isCompactSummary"):
            compacted += 1
        if d.get("type") == "user" and not d.get("isMeta"):
            c = m.get("content")
            if isinstance(c, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
                continue
            txt = " ".join(texts(c))
            if roar and (genuine(txt) or "<command-name>" in txt):
                close(); roar = None
            if roar is None and ts >= SINCE and INVOKE.search(txt) and (genuine(txt) or "<command-name>/roar" in txt):
                bundled = not re.fullmatch(r"\s*[/$]roar\s*|.*<command-name>/roar</command-name>.*", txt, re.S)
                roar = dict(host=HOST, start=ts[:16], proj=proj, bundled=bundled, prompt=txt.strip()[:80],
                            pre_calls=len(pre_ids), compacted=compacted, calls=[], tools=[], seen=set())
        elif d.get("type") == "assistant" and m.get("id"):
            if roar is None:
                for b in m.get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Skill" and (b.get("input") or {}).get("skill") == "roar" and ts >= SINCE:
                        roar = dict(host=HOST, start=ts[:16], proj=proj, bundled=True, prompt="(Skill call)",
                                    pre_calls=len(pre_ids), compacted=compacted, calls=[], tools=[], seen=set())
            if roar is None:
                pre_ids.add(m["id"])
                continue
            if m["id"] not in roar["seen"]:
                roar["seen"].add(m["id"]); u = m.get("usage") or {}
                roar["calls"].append([u.get("input_tokens", 0), u.get("cache_read_input_tokens", 0), u.get("cache_creation_input_tokens", 0), u.get("output_tokens", 0)])
            for b in m.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    roar["tools"].append(tool_label(b))
    close()
    for r in out:
        r.pop("seen")
        print(json.dumps(r))

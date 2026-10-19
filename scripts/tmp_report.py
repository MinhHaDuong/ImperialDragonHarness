#!/usr/bin/env python3
"""Report temporary candidates and available session-history attribution.

This command is deliberately observational. It never deletes, moves, or changes
permissions on candidate paths. A history match means a session cited the path;
it does not establish that the session created it.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_CACHE_EXCLUDES = {
    "huggingface", "uv", "pip", "numba", "torch", "transformers",
    "npm", "pnpm", "yarn", "playwright", "ms-playwright",
}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:api[_-]?(?:key|token)|token|secret|password|passwd|credential)\b\s*=\s*)[^\s,;]+"
)
BEARER = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/-]+=*")
TOKEN_SHAPE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{12,})\b")
CANDIDATE_NAME = re.compile(r"(?:^|/)t([0-9]{1,5})(?:[-_/]|$)")
CREATE_COMMAND = re.compile(r"(?i)(?:\bmkdir\b|\bmktemp\b|\btouch\b|\bopen\s*\(|\bwrite(?:_text|_bytes)?\s*\()")
ATTEMPT_COMMAND = re.compile(r"(?i)(?:\bTMPDIR\s*=|\bcd\s+|\bcp\b|\bmv\b|\brm\b|\btee\b|\bredirection)")


def allocated_bytes(path: Path, limit: int = 200_000) -> tuple[int, bool, list[str]]:
    """Return allocated bytes, truncation state, and unreadable descendants."""
    try:
        st = path.lstat()
    except OSError:
        return 0, True, [str(path)]
    if not path.is_dir() or path.is_symlink():
        return st.st_blocks * 512, False, []
    total = 0
    count = 0
    unreadable = []
    def walk_error(error):
        unreadable.append(str(getattr(error, "filename", None) or path))

    for current, dirs, files in os.walk(path, followlinks=False, onerror=walk_error):
        try:
            children = list(Path(current).iterdir())
        except OSError:
            unreadable.append(current)
            dirs[:] = []
            continue
        for child in children:
            count += 1
            if count > limit:
                return total, True, sorted(set(unreadable))
            try:
                total += child.lstat().st_blocks * 512
            except OSError:
                unreadable.append(str(child))
    return total, bool(unreadable), sorted(set(unreadable))


def scan_candidates(roots, known_cache_names=None):
    """Scan immediate children of roots, deduplicate paths, and rank by bytes."""
    known_cache_names = DEFAULT_CACHE_EXCLUDES if known_cache_names is None else set(known_cache_names)
    candidates = {}
    unreadable = []
    normalized_roots = [Path(raw).expanduser().resolve(strict=False) for raw in roots]
    for raw in roots:
        root = Path(raw).expanduser()
        # A worktree .tmp is one owned candidate. Summarize it as a unit so
        # nested scratch directories do not obscure its total or duplicate it.
        if root.name == ".tmp":
            if not root.exists():
                continue
            size, truncated, failures = allocated_bytes(root)
            unreadable.extend(failures)
            try:
                mtime = root.stat().st_mtime
            except OSError:
                unreadable.append(str(root))
                continue
            key = str(root.resolve(strict=False))
            candidates[key] = {
                "path": str(root), "bytes": size, "mtime": mtime,
                "sources": [str(root)], "truncated": truncated,
            }
            continue
        try:
            children = list(os.scandir(root))
        except FileNotFoundError:
            continue
        except OSError:
            unreadable.append(str(root))
            continue
        for entry in children:
            path = Path(entry.path)
            resolved = path.resolve(strict=False)
            if any(other != root.resolve(strict=False) and resolved == other for other in normalized_roots):
                # A nested root is scanned as its own aggregate below; don't
                # also report its full size as a child of its parent root.
                continue
            if root.name == ".cache" and path.name in known_cache_names:
                continue
            try:
                if entry.is_symlink():
                    continue
                entry.stat(follow_symlinks=False)
            except OSError:
                unreadable.append(str(path))
                continue
            size, truncated, failures = allocated_bytes(path)
            unreadable.extend(failures)
            try:
                mtime = path.stat(follow_symlinks=False).st_mtime
            except OSError:
                unreadable.append(str(path))
                continue
            key = str(path.resolve(strict=False))
            item = candidates.setdefault(key, {
                "path": str(path), "bytes": size, "mtime": mtime,
                "sources": [], "truncated": truncated,
            })
            item["bytes"] = max(item["bytes"], size)
            item["mtime"] = max(item["mtime"], mtime)
            if str(root) not in item["sources"]:
                item["sources"].append(str(root))
    ranked = sorted(candidates.values(), key=lambda item: (-item["bytes"], item["path"]))
    return {"candidates": ranked, "unreadable": sorted(set(unreadable))}


def history_files(home: Path, runtime: str | None = None, with_unreadable=False):
    roots = {
        "claude": [home / ".claude" / "projects"],
        "codex": [home / ".codex" / "sessions"],
        "pi": [home / ".pi" / "agent" / "sessions"],
    }
    found = []
    unreadable = []
    selected = roots.values() if runtime is None else [roots.get(runtime, [])]
    for group in selected:
        for root in group:
            if root.exists():
                def walk_error(error):
                    unreadable.append(str(getattr(error, "filename", None) or root))
                for current, dirs, files in os.walk(root, onerror=walk_error):
                    for name in files:
                        path = Path(current) / name
                        if path.suffix in {".jsonl", ".json"}:
                            found.append(path)
    return (found, sorted(set(unreadable))) if with_unreadable else found


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def _identity(record):
    if not isinstance(record, dict):
        return None, None, None
    session = None
    parent = None
    pid = None
    for key in ("sessionId", "session_id", "thread_id", "threadId"):
        if isinstance(record.get(key), str):
            session = record[key]
            break
    if isinstance(record.get("agentId"), str):
        parent = record.get("sessionId") if isinstance(record.get("sessionId"), str) else None
        session = record["agentId"]
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    meta = record.get("session_meta") or record.get("sessionMeta") or record.get("metadata") or payload
    if record.get("type") == "session" and isinstance(record.get("id"), str):
        session = record["id"]
    session = session or _nested_session(record)
    if isinstance(meta, dict):
        for key in ("id", "session_id", "sessionId", "thread_id"):
            if isinstance(meta.get(key), str):
                session = meta[key]
                break
        parent = parent or _nested_parent(meta)
        pid = meta.get("pid") if isinstance(meta.get("pid"), int) else None
    for key in ("parent_thread_id", "parentSessionId", "parent_session_id"):
        if isinstance(record.get(key), str):
            parent = record[key]
            break
    parent = parent or _nested_parent(record)
    if pid is None and isinstance(record.get("pid"), int):
        pid = record["pid"]
    return session, parent, pid


def _nested_parent(value):
    if isinstance(value, dict):
        for key in ("parent_thread_id", "parentSessionId", "parent_session_id"):
            if isinstance(value.get(key), str):
                return value[key]
        for child in value.values():
            found = _nested_parent(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _nested_parent(child)
            if found:
                return found
    return None


def _nested_session(value):
    if isinstance(value, dict):
        for key in ("thread_id", "session_id", "sessionId"):
            if isinstance(value.get(key), str):
                return value[key]
        for child in value.values():
            found = _nested_session(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _nested_session(child)
            if found:
                return found
    return None


def _redact(text):
    text = SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", text)
    text = BEARER.sub(r"\1[REDACTED]", text)
    text = TOKEN_SHAPE.sub("[REDACTED]", text)
    text = re.sub(r"(?i)(https?://[^:/\s]+:)[^@/\s]+@", r"\1[REDACTED]@", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:360]


def _safe_excerpt(candidate: Path):
    # Do not echo arbitrary command text: a path match can share a history line
    # with a credential, and redaction cannot recognize every secret format.
    return f'"… {candidate} …"'


def _spellings(candidate: Path, home: Path):
    absolute = str(candidate.expanduser())
    variants = {absolute, absolute.replace(str(home), "$HOME", 1)}
    try:
        variants.add("~" + absolute[len(str(home)):]) if absolute.startswith(str(home)) else None
    except Exception:
        pass
    return sorted(variants, key=len, reverse=True)


def find_history_mentions(candidate, files, home=None, candidate_mtime=0):
    """Return bounded, redacted history references newer than candidate mtime."""
    candidate = Path(candidate).expanduser()
    home = Path(home or Path.home()).expanduser()
    needles = _spellings(candidate, home)
    matches = []
    for file in files:
        active_session = active_parent = active_pid = None
        try:
            file_mtime = file.stat().st_mtime
            if file_mtime < candidate_mtime:
                continue
            with file.open(encoding="utf-8", errors="replace") as stream:
                for line_no, raw in enumerate(stream, 1):
                    try:
                        record = json.loads(raw)
                    except (ValueError, TypeError):
                        continue
                    session, parent, pid = _identity(record)
                    active_session = session or active_session
                    active_parent = parent or active_parent
                    active_pid = pid or active_pid
                    strings = list(_strings(record))
                    joined = "\n".join(strings)
                    if not any(needle and needle in joined for needle in needles):
                        continue
                    evidence = "attempted" if CREATE_COMMAND.search(joined) or ATTEMPT_COMMAND.search(joined) else "mention"
                    matches.append({
                        "file": str(file), "line": line_no, "session": active_session,
                        "parent": active_parent, "pid": active_pid, "evidence": evidence,
                        "excerpt": _safe_excerpt(candidate),
                    })
        except OSError:
            continue
    return matches


def attribute_histories(candidates, files, home=None):
    """Read each relevant history once and attribute all candidate path hits."""
    home = Path(home or Path.home()).expanduser()
    all_spellings = {}
    mtimes = {}
    for item in candidates:
        path = Path(item["path"]).expanduser()
        mtimes[str(path)] = item["mtime"]
        for spelling in _spellings(path, home):
            all_spellings[spelling] = str(path)
    if not all_spellings:
        return {}
    matcher = re.compile("|".join(re.escape(s) for s in sorted(all_spellings, key=len, reverse=True)))
    results = {key: [] for key in mtimes}
    for file in files:
        try:
            file_mtime = file.stat().st_mtime
            if file_mtime < min(mtimes.values()):
                continue
            active_session = active_parent = active_pid = None
            with file.open(encoding="utf-8", errors="replace") as stream:
                for line_no, raw in enumerate(stream, 1):
                    try:
                        record = json.loads(raw)
                    except (ValueError, TypeError):
                        continue
                    session, parent, pid = _identity(record)
                    active_session = session or active_session
                    active_parent = parent or active_parent
                    active_pid = pid or active_pid
                    joined = "\n".join(_strings(record))
                    keys = {all_spellings[m.group(0)] for m in matcher.finditer(joined)}
                    for key in keys:
                        if file_mtime < mtimes[key]:
                            continue
                        evidence = "created" if CREATE_COMMAND.search(joined) and _successful(record) else "attempted" if CREATE_COMMAND.search(joined) or ATTEMPT_COMMAND.search(joined) else "mention"
                        results[key].append({
                            "file": str(file), "line": line_no,
                            "session": active_session, "parent": active_parent,
                            "pid": active_pid, "evidence": evidence,
                            "excerpt": _safe_excerpt(Path(key)),
                        })
        except OSError:
            continue
    return results


def _successful(record):
    """Only explicit structured success can upgrade an attempt to creation."""
    if not isinstance(record, dict):
        return False
    payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
    for value in (record, payload):
        if value.get("exit_code") == 0 or value.get("returncode") == 0 or value.get("success") is True:
            return True
        if value.get("status") in {"success", "completed"} and value.get("is_error") is False:
            return True
    return False


def session_liveness(session, pid=None, proc_root=Path("/proc")):
    if pid is not None:
        if (proc_root / str(pid)).exists():
            return "live"
        return "confirmed exited"
    if session:
        try:
            for entry in proc_root.iterdir():
                if not entry.name.isdigit():
                    continue
                for name in ("environ", "cmdline"):
                    try:
                        if session.encode() in (entry / name).read_bytes():
                            return "live"
                    except OSError:
                        continue
        except OSError:
            pass
    return "unknown"


def scope_history(matches, scope, session_id=None, exclude_session_id=None):
    """Filter attribution to a roar session tree or retain all lair evidence."""
    matches = [m for m in matches if not exclude_session_id or m.get("session") != exclude_session_id]
    if scope != "roar":
        return matches
    if not session_id:
        return []
    relevant = {session_id}
    changed = True
    while changed:
        changed = False
        for match in matches:
            if match.get("parent") in relevant and match.get("session") and match["session"] not in relevant:
                relevant.add(match["session"])
                changed = True
    return [m for m in matches if m.get("session") in relevant]


def disk_warnings(readings, threshold=0.10):
    warnings = []
    for mount in ("/tmp", "/home"):
        value = readings.get(mount)
        if value is None or mount not in readings:
            warnings.append(f"{mount} free space unknown (could not inspect mount)")
            continue
        total, free = value.get("total", 0), value.get("free", 0)
        if total > 0 and free / total < threshold:
            warnings.append(f"{mount} has {free * 100 // total}% free")
    return warnings


def disk_readings(paths=("/tmp", "/home")):
    result = {}
    for path in paths:
        try:
            usage = shutil.disk_usage(path)
            result[path] = {"total": usage.total, "free": usage.free}
        except OSError:
            result[path] = None
    return result


def _default_roots(repo):
    temp = Path(os.environ.get("TMPDIR", "/tmp")).expanduser()
    home = Path.home()
    # /tmp contains runtime-owned roots such as /tmp/claude-<uid> and Pi's
    # pi-bash logs even when TMPDIR points elsewhere. Scanning its immediate
    # children discovers those roots without walking the mount recursively.
    roots = [temp, Path("/tmp"), home / ".cache"]
    common = subprocess.run(["git", "-C", str(repo), "rev-parse", "--path-format=absolute", "--git-common-dir"], capture_output=True, text=True)
    if common.returncode == 0:
        listing = subprocess.run(["git", "-C", str(repo), "worktree", "list", "--porcelain"], capture_output=True, text=True)
        if listing.returncode == 0:
            for line in listing.stdout.splitlines():
                if line.startswith("worktree "):
                    roots.append(Path(line[9:]) / ".tmp")
    return roots


def _references(candidates, repo):
    paths = [item["path"] for item in candidates]
    result = {path: {"git_log": "unknown", "pull_requests": "unknown", "verdict_files": "unknown"} for path in paths}
    try:
        log = subprocess.run(["git", "-C", str(repo), "log", "--all", "--format=%B"], capture_output=True, text=True)
        if log.returncode == 0:
            for path in paths:
                result[path]["git_log"] = path in log.stdout
    except OSError:
        pass
    try:
        gh = subprocess.run(["gh", "pr", "list", "--state", "all", "--limit", "1000", "--json", "number,title,body"], capture_output=True, text=True, cwd=repo)
        if gh.returncode == 0:
            prs = json.loads(gh.stdout)
            for path in paths:
                hits = [pr.get("number") for pr in prs if path in (pr.get("title", "") + "\n" + pr.get("body", ""))]
                result[path]["pull_requests"] = hits if hits or len(prs) < 1000 else "unknown (PR listing reached 1000-item limit)"
    except (OSError, ValueError):
        pass
    verdicts = {path: [] for path in paths}
    verdict_readable = True
    roots = [Path(repo) / ".panel", Path(repo) / ".review"]
    try:
        listing = subprocess.run(["git", "-C", str(repo), "worktree", "list", "--porcelain"], capture_output=True, text=True)
        if listing.returncode == 0:
            for line in listing.stdout.splitlines():
                if line.startswith("worktree "):
                    tree = Path(line[9:])
                    roots.extend((tree / ".panel", tree / ".review"))
    except OSError:
        verdict_readable = False
    for root in dict.fromkeys(roots):
        if not root.exists():
            continue
        try:
            def walk_error(_error):
                nonlocal verdict_readable
                verdict_readable = False
            for current, dirs, files in os.walk(root, onerror=walk_error):
                for name in files:
                    file = Path(current) / name
                    try:
                        if file.stat().st_size >= 5_000_000:
                            continue
                        content = file.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        verdict_readable = False
                        continue
                    for path in paths:
                        if path in content:
                            verdicts[path].append(str(file))
        except OSError:
            verdict_readable = False
    for path in paths:
        result[path]["verdict_files"] = verdicts[path] if verdict_readable else "unknown"
    return result


def infer_test_provenance(path, repo):
    """Infer a likely test leak only when source contains a matching temp prefix."""
    path = Path(path)
    match = re.match(r"^(.*-[0-9]{3,})-[A-Za-z0-9]{5,}$", path.name)
    if not match:
        return None
    prefix = match.group(1) + "-"
    tests = Path(repo) / "tests"
    if not tests.is_dir():
        return None
    try:
        for current, dirs, files in os.walk(tests, onerror=lambda _e: None):
            dirs[:] = [name for name in dirs if name not in {".git", "__pycache__", ".venv"}]
            for name in files:
                source = Path(current) / name
                if source.suffix not in {".py", ".js", ".ts", ".tsx", ".mjs"}:
                    continue
                try:
                    for line_no, line in enumerate(source.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                        if prefix in line and re.search(r"mkdtemp|TemporaryDirectory|tempfile|tmp_path", line):
                            return {"file": str(source), "line": line_no, "session": None,
                                    "parent": None, "pid": None, "evidence": "inferred",
                                    "excerpt": f'"… test fixture prefix {prefix} …"',
                                    "basis": "matching temporary-directory prefix in repository test source"}
                except OSError:
                    continue
    except OSError:
        return None
    return None


def build_report(runtime, scope, session_id, repo, floor_bytes=0, exclude_session_id=None):
    home = Path.home()
    scanned = scan_candidates(_default_roots(repo))
    candidates = [item for item in scanned["candidates"] if item["bytes"] >= floor_bytes]
    histories, history_unreadable = history_files(home, with_unreadable=True)
    history_index = attribute_histories(candidates, histories, home)
    references = _references(candidates, repo)
    for item in candidates:
        path = Path(item["path"])
        matches = scope_history(history_index.get(item["path"], []), scope, session_id, exclude_session_id)
        if not matches:
            inferred = infer_test_provenance(path, repo)
            if inferred:
                matches = [inferred]
        for match in matches:
            match["liveness"] = session_liveness(match.get("session"), match.get("pid"))
        ticket_match = CANDIDATE_NAME.search(path.name)
        ticket = ticket_match.group(1) if ticket_match else None
        ticket_state = "unknown"
        if ticket:
            ticket_state = "closed" if any((Path(repo) / "tickets" / "closed").glob(f"{ticket}-*.erg")) else "open" if any((Path(repo) / "tickets").glob(f"{ticket}-*.erg")) else "missing"
        item.update({
            "history": matches,
            "attribution": "attributed" if matches else "unattributed",
            "ticket_hint": ticket,
            "ticket_state": ticket_state,
            "references": references.get(item["path"], {"git_log": "unknown", "pull_requests": "unknown", "verdict_files": "unknown"}),
        })
    return {
        "runtime": runtime, "scope": scope, "session_id": session_id,
        "candidates": candidates, "unreadable": scanned["unreadable"],
        "history_unreadable": history_unreadable,
        "disk": disk_readings(),
    }


def _format(report):
    lines = [f"Temporary report ({report['runtime']}, {report['scope']})"]
    for mount, reading in report["disk"].items():
        total, free = reading["total"], reading["free"]
        if total:
            lines.append(f"  {mount}: {free * 100 // total}% free")
    if not report["candidates"]:
        lines.append("  no candidates above the configured size floor")
    for item in report["candidates"]:
        lines.append(f"  {item['path']}: {item['bytes']} bytes; {item['attribution']}; ticket={item['ticket_hint'] or 'none'} ({item['ticket_state']})")
        if item["truncated"]:
            lines.append("    byte count is a lower bound (walk truncated or unreadable)")
        for match in item["history"]:
            lines.append(f"    {match['evidence']} {match['file']}:{match['line']} session={match['session'] or 'unknown'} liveness={match['liveness']}: {match['excerpt']}")
        lines.append(f"    references: PRs={item['references']['pull_requests']} verdicts={item['references']['verdict_files']} git-log={item['references']['git_log']}")
    if report["unreadable"]:
        lines.append(f"  could not read {len(report['unreadable'])} entries")
    if report.get("history_unreadable"):
        lines.append(f"  could not read {len(report['history_unreadable'])} history locations")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", choices=("claude", "codex", "pi"))
    parser.add_argument("--scope", choices=("roar", "lair"))
    parser.add_argument("--session-id")
    parser.add_argument("--exclude-session-id", help="Exclude a known report-generator session from attribution")
    parser.add_argument("--repo", default=".")
    parser.add_argument("--floor-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--disk-warning", action="store_true", help="Print low-space warnings only")
    args = parser.parse_args(argv)
    if args.disk_warning:
        for warning in disk_warnings(disk_readings()):
            print(f"Disk headroom warning: {warning} (threshold: 10% free)")
        return 0
    if not args.runtime or not args.scope:
        parser.error("--runtime and --scope are required unless --disk-warning is used")
    report = build_report(args.runtime, args.scope, args.session_id, args.repo, args.floor_bytes, args.exclude_session_id)
    print(json.dumps(report, sort_keys=True) if args.json else _format(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())

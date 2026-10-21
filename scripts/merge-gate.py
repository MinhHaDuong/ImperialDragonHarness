#!/usr/bin/env python3
"""Merge gate record: checks run on the candidate merge commit, kept as a git note.

Ticket 1156 (tracker 1045). The candidate is the commit that would become the
base branch: the --no-ff merge of a branch head into the base, built
deterministically (merge-tree + commit-tree with fixed metadata) so that any
host rebuilds the same object id from the same two parents. `run` checks it in
a throwaway worktree and appends one record entry to the note on the candidate
in refs/notes/gate, then pushes that ref. `check` reads the note and lets the
latest entry for the candidate decide. A record is a traceable statement of
what was run, when, by whom, on which host: not proof.

The check set comes from `.merge-gate.json` at the base revision, so a branch
cannot change the set it is gated by; a change of set takes effect once merged.
This file is the one home of the record format (FIELDS, format_entry,
parse_note, decide): other readers adapt to it.

Exit codes of `check`: 0 pass, 1 fail or stale scope, 2 no record, 3 error.
"""

import argparse
import datetime
import getpass
import importlib.util
import json
import logging
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LOG = logging.getLogger("merge-gate")
NOTES_REF = "refs/notes/gate"
CONFIG_PATH = ".merge-gate.json"
HEADER = "merge-gate-record: v1"
FIELDS = ("result", "time", "actor", "host", "revision", "command", "scope", "versions")
NOT_STATED = "not-stated"
PASS, FAIL, MISSING, ERROR = 0, 1, 2, 3


class GateError(RuntimeError):
    """The gate could not establish its subject or read its record."""


def git(*args, check=True, env=None):
    proc = subprocess.run(["git", *args], capture_output=True, text=True, env=env)
    if check and proc.returncode:
        raise GateError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc


def rev(ref):
    return git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").stdout.strip()


# ── record format ──────────────────────────────────────────────────────────────


def format_entry(fields):
    """One record entry: the header line, then every field in FIELDS order."""
    missing = [f for f in FIELDS if not fields.get(f)]
    if missing:
        raise ValueError("record entry lacks " + ", ".join(missing))
    lines = [HEADER] + [f"{key}: {fields[key]}" for key in FIELDS]
    lines += [f"check: {line}" for line in fields.get("checks", [])]
    return "\n".join(lines) + "\n"


def parse_note(text):
    """Entries in note order; lines outside an entry, or unknown keys, are ignored."""
    entries, current = [], None
    for line in text.splitlines():
        if line == HEADER:
            current = {"checks": []}
            entries.append(current)
            continue
        key, sep, value = line.partition(": ")
        if current is None or not sep:
            continue
        if key == "check":
            current["checks"].append(value)
        elif key in FIELDS and key not in current:
            current[key] = value
    return entries


def revision_line(candidate, base, head):
    return f"candidate={candidate} base={base} head={head}"


def scope_line(config):
    return f"{config['scope']}: " + " ".join(c["name"] for c in config["checks"])


def decide(entries, candidate, scope):
    """Latest entry naming this candidate decides. Returns (code, reason)."""
    mine = [e for e in entries if f"candidate={candidate} " in e.get("revision", "") + " "]
    if not mine:
        return MISSING, "missing: no record on candidate " + candidate
    latest = mine[-1]
    if any(f not in latest for f in FIELDS):
        return FAIL, "fail: latest record is incomplete"
    if latest["scope"] != scope:
        return FAIL, f"fail: latest record scope '{latest['scope']}' is not the declared scope '{scope}'"
    if latest["result"] != "pass":
        return FAIL, f"fail: latest record says {latest['result']} ({latest['time']}, {latest['host']})"
    return PASS, f"pass: {latest['time']} on {latest['host']} by {latest['actor']}"


# ── actor (vocabulary of scripts/attribution_record.py) ───────────────────────


def _attribution():
    path = Path(__file__).with_name("attribution_record.py")
    spec = importlib.util.spec_from_file_location("attribution_record", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def actor_line(runtime, model, effort):
    """Writer identity in the attribution vocabulary, plus OS user and git name.

    A stated model is validated as an attribution writer identity (verbatim
    provider-qualified id). Unstated values are spelled `not-stated`; a human
    states `runtime=human`. Nothing here detects or requires an agent runtime.
    """
    runtime, model, effort = runtime or NOT_STATED, model or NOT_STATED, effort or NOT_STATED
    ident = f"runtime={runtime} · model={model} · effort={effort}"
    if model != NOT_STATED:
        _attribution().identity(ident, writer=True)
    name = git("config", "user.name", check=False).stdout.strip() or NOT_STATED
    return f"{ident} · user={getpass.getuser()} · git-name={name}"


# ── candidate and config ──────────────────────────────────────────────────────


def candidate(base, head):
    """Deterministic --no-ff merge commit of head into base; GateError on conflict."""
    tree = git("merge-tree", "--write-tree", "--no-messages", base, head, check=False)
    if tree.returncode:
        raise GateError(f"conflict: {head[:12]} does not merge cleanly into {base[:12]}")
    stamp = git("show", "-s", "--format=%ct", head).stdout.strip() + " +0000"
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "merge-gate",
        "GIT_AUTHOR_EMAIL": "merge-gate@invalid",
        "GIT_AUTHOR_DATE": stamp,
        "GIT_COMMITTER_NAME": "merge-gate",
        "GIT_COMMITTER_EMAIL": "merge-gate@invalid",
        "GIT_COMMITTER_DATE": stamp,
    }
    message = f"merge-gate candidate\n\nbase {base}\nhead {head}\n"
    out = git(
        "commit-tree", "--no-gpg-sign", tree.stdout.split()[0], "-p", base, "-p", head, "-m", message, env=env
    )
    return out.stdout.strip()


def load_config(base):
    shown = git("show", f"{base}:{CONFIG_PATH}", check=False)
    if shown.returncode:
        return None
    config = json.loads(shown.stdout)
    return config if config.get("gate") == "on" else None


def resolve(args):
    base, head = rev(args.base), rev(args.head)
    if not base or not head:
        raise GateError(f"cannot resolve base '{args.base}' or head '{args.head}'")
    return base, head


# ── notes transport ───────────────────────────────────────────────────────────


def fetch_notes(remote):
    """Make the local notes ref the remote's: the remote is the record of authority."""
    probe = git("ls-remote", "--exit-code", remote, NOTES_REF, check=False)
    if probe.returncode == 2:
        return False
    if probe.returncode:
        raise GateError(f"cannot read {NOTES_REF} on {remote}: {probe.stderr.strip()}")
    git("fetch", "-q", remote, f"+{NOTES_REF}:{NOTES_REF}")
    return True


def read_note(oid):
    shown = git("notes", f"--ref={NOTES_REF}", "show", oid, check=False)
    return shown.stdout if shown.returncode == 0 else ""


def append_and_push(oid, text, remote):
    """Append one entry and push; on a lost race, refetch and append once more."""
    for attempt in (1, 2):
        if remote:
            fetch_notes(remote)
        git("notes", f"--ref={NOTES_REF}", "append", "-m", text, oid)
        if not remote:
            return
        push = git("push", "-q", remote, f"{NOTES_REF}:{NOTES_REF}", check=False)
        if push.returncode == 0:
            return
        LOG.warning("notes push rejected (attempt %d): %s", attempt, push.stderr.strip())
    raise GateError(f"could not push {NOTES_REF} to {remote}; the record exists only locally")


# ── commands ──────────────────────────────────────────────────────────────────


def first_line(argv, cwd):
    try:
        proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True)
    except OSError:
        return "absent"
    lines = (proc.stdout or proc.stderr).strip().splitlines()
    return lines[0].strip() if lines else "unknown"


def run_checks(config, cwd):
    results, ok = [], True
    for item in config["checks"]:
        start = time.monotonic()
        LOG.info("check %s: %s", item["name"], " ".join(item["argv"]))
        proc = subprocess.run(item["argv"], cwd=cwd)
        verdict = "pass" if proc.returncode == 0 else f"fail(exit {proc.returncode})"
        ok = ok and proc.returncode == 0
        results.append(f"{item['name']} {verdict} {time.monotonic() - start:.1f}s :: {' '.join(item['argv'])}")
    return ok, results


def cmd_run(args):
    base, head = resolve(args)
    config = load_config(base)
    if config is None:
        raise GateError(f"gate is off at base {args.base}: no {CONFIG_PATH} with gate=on")
    oid = candidate(base, head)
    actor = actor_line(args.runtime, args.model, args.effort)
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with tempfile.TemporaryDirectory(prefix="merge-gate-") as tmp:
        tree = Path(tmp) / "candidate"
        git("worktree", "add", "-q", "--detach", str(tree), oid)
        try:
            ok, results = run_checks(config, tree)
            versions = " · ".join(f"{v['name']} {first_line(v['argv'], tree)}" for v in config.get("versions", []))
        finally:
            git("worktree", "remove", "--force", str(tree), check=False)
    entry = format_entry(
        {
            "result": "pass" if ok else "fail",
            "time": started,
            "actor": actor,
            "host": socket.gethostname(),
            "revision": revision_line(oid, base, head),
            "command": f"merge-gate run --base {args.base} --head {args.head}",
            "scope": scope_line(config),
            "versions": versions or NOT_STATED,
            "checks": results,
        }
    )
    append_and_push(oid, entry, None if args.no_push else args.remote)
    sys.stdout.write(entry)
    sys.stdout.write(f"{'pass' if ok else 'fail'}: recorded on candidate {oid}\n")
    return PASS if ok else FAIL


def cmd_check(args):
    base, head = resolve(args)
    config = load_config(base)
    if config is None:
        raise GateError(f"gate is off at base {args.base}")
    oid = candidate(base, head)
    if not args.no_fetch and not fetch_notes(args.remote):
        sys.stdout.write(f"missing: {args.remote} has no {NOTES_REF}; no record on candidate {oid}\n")
        return MISSING
    code, reason = decide(parse_note(read_note(oid)), oid, scope_line(config))
    sys.stdout.write(reason + "\n")
    return code


def cmd_candidate(args):
    sys.stdout.write(candidate(*resolve(args)) + "\n")
    return PASS


def cmd_enabled(args):
    base = rev(args.base)
    if not base:
        raise GateError(f"cannot resolve base '{args.base}'")
    return PASS if load_config(base) else FAIL


def parser():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)
    for name, func in (("run", cmd_run), ("check", cmd_check), ("candidate", cmd_candidate), ("enabled", cmd_enabled)):
        s = sub.add_parser(name)
        s.set_defaults(func=func)
        s.add_argument("--base", required=True, help="base ref, e.g. origin/main")
        if name == "enabled":
            continue
        s.add_argument("--head", required=True, help="branch head ref")
        if name in ("run", "check"):
            s.add_argument("--remote", default="origin", help="where refs/notes/gate lives")
        if name == "check":
            s.add_argument("--no-fetch", action="store_true", help="read the local notes ref only")
        if name == "run":
            s.add_argument("--no-push", action="store_true", help="record locally, do not push the note")
            s.add_argument("--runtime", default=os.environ.get("MERGE_GATE_RUNTIME", ""))
            s.add_argument("--model", default=os.environ.get("MERGE_GATE_MODEL", ""))
            s.add_argument("--effort", default=os.environ.get("MERGE_GATE_EFFORT", ""))
    return p


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="merge-gate: %(message)s")
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except (GateError, ValueError) as exc:
        LOG.error("%s", exc)
        return ERROR


if __name__ == "__main__":
    sys.exit(main())

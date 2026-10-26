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

The declaration `.merge-gate.json` is read at the base revision: the base
fixes whether the gate is on, which checks run and their commands; the code
those commands execute comes from the candidate, hence from the branch. A
change of declaration takes effect once merged. Only an explicit
`"gate": "off"`, or no file at all, means off; anything else unrecognised is an
error, never off. This file is the one home of the record format (FIELDS,
format_entry, parse_note, decide): other readers adapt to it.

The remote's notes ref is authoritative: `run` and `check` overwrite the local
refs/notes/gate with it first (and drop it when the remote has none). A
`--no-push` record goes to refs/notes/gate-local, which is never pushed and is
read only by `check --local`: a merge rests on a published record.

Gating tiers (ticket 1221; the policy is skills/merge/SKILL.md § Gating
tiers): a candidate whose changes against the base all match BOOKKEEPING is
bookkeeping-tier. When the base declares `"tiers": {"bookkeeping": [names]}`,
such a candidate's record runs only those named checks, under the scope
`<scope>/bookkeeping`; `check` accepts that scope or the full one for a
bookkeeping candidate, and only the full one otherwise. `tier` reports the tier
of a candidate, or with `--since <approved tip>` the tier of what the head adds
to the candidate the approval saw: the one mechanical reading of the tiers.

Exit codes of `check`: 0 pass, 1 fail or stale scope, 2 no record, 3 error.
`enabled`: 0 on, 1 off, 3 error. `tier`: 0 bookkeeping, 1 full, 3 error.
Any unexpected exception exits 3.
"""

import argparse
import datetime
import fnmatch
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
LOCAL_REF = "refs/notes/gate-local"  # --no-push records: never pushed, read by `check --local` only
# Characters that end a line for some reader: every C0 control, DEL, NEL, LS, PS.
LINE_BREAKERS = frozenset(chr(c) for c in range(32)) | {"\x7f", "\x85", "\u2028", "\u2029"}
CONFIG_PATH = ".merge-gate.json"
HEADER = "merge-gate-record: v1"
FIELDS = ("result", "time", "actor", "host", "revision", "command", "scope", "versions")
NOT_STATED = "not-stated"
PASS, FAIL, MISSING, ERROR = 0, 1, 2, 3
# Bookkeeping paths, the one home of the list (ticket 1221). A pattern ending
# in "/" covers its whole subtree; any other matches segment by segment, so
# "tickets/*.erg" does not reach tickets/erg (code) or tickets/closed/.
BOOKKEEPING = ("tickets/*.erg", "tickets/closed/*.erg", "STATE.md", "memory/")
BOOKKEEPING_TIER = "bookkeeping"


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
    values = [fields[key] for key in FIELDS] + list(fields.get("checks", []))
    if not all(single_line(v) for v in values):
        # A line break in a free-text value (actor, command) would start a forged entry.
        raise ValueError("record values may not contain a line break or control character")
    lines = [HEADER] + [f"{key}: {fields[key]}" for key in FIELDS]
    lines += [f"check: {line}" for line in fields.get("checks", [])]
    return "\n".join(lines) + "\n"


def single_line(value):
    """No control character and no Unicode line boundary, anywhere in the value."""
    return isinstance(value, str) and not any(c in LINE_BREAKERS for c in value)


def sanitize(text):
    """Captured tool output: line boundaries and controls become spaces."""
    return "".join(" " if c in LINE_BREAKERS else c for c in text).strip()


def parse_note(text):
    """Entries in note order; lines outside an entry, or unknown keys, are ignored.

    Lines end at \n only: the writer refuses every other line boundary, and a
    reader that split on them (str.splitlines) would see entries the writer
    never wrote.
    """
    entries, current = [], None
    for line in text.split("\n"):
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
    """Latest entry naming this candidate decides. Returns (code, reason).

    `scope` is one accepted scope line or a tuple of them.
    """
    scopes = (scope,) if isinstance(scope, str) else tuple(scope)
    mine = [e for e in entries if f"candidate={candidate} " in e.get("revision", "") + " "]
    if not mine:
        return MISSING, "missing: no record on candidate " + candidate
    latest = mine[-1]
    if any(f not in latest for f in FIELDS):
        return FAIL, "fail: latest record is incomplete"
    if latest["scope"] not in scopes:
        declared = "' or '".join(scopes)
        return FAIL, f"fail: latest record scope '{latest['scope']}' is not the declared scope '{declared}'"
    if latest["result"] != "pass":
        return FAIL, f"fail: latest record says {latest['result']} ({latest['time']}, {latest['host']})"
    return PASS, f"pass: {latest['time']} on {latest['host']} by {latest['actor']}"


# ── gating tiers ──────────────────────────────────────────────────────────────


def is_bookkeeping(path):
    for pattern in BOOKKEEPING:
        if pattern.endswith("/"):
            if path.startswith(pattern):
                return True
            continue
        parts, want = path.split("/"), pattern.split("/")
        if len(parts) == len(want) and all(fnmatch.fnmatchcase(a, b) for a, b in zip(parts, want)):
            return True
    return False


def changed_paths(old, new):
    """Paths whose content differs between two commits; renames count at both ends."""
    out = git("diff", "--name-only", "--no-renames", "-z", old, new).stdout
    return [p for p in out.split("\0") if p]


def tier_of(paths):
    return BOOKKEEPING_TIER if all(is_bookkeeping(p) for p in paths) else "full"


def effective(config, base, oid):
    """The check set the record of candidate `oid` runs: a tier's subset, or all."""
    names = config.get("tiers", {}).get(BOOKKEEPING_TIER)
    if not names or tier_of(changed_paths(base, oid)) != BOOKKEEPING_TIER:
        return config
    checks = [c for c in config["checks"] if c["name"] in names]
    return {**config, "scope": f"{config['scope']}/{BOOKKEEPING_TIER}", "checks": checks}


def accepted_scopes(config, base, oid):
    """A tier record, or the full set, which covers every tier."""
    return tuple(dict.fromkeys((scope_line(effective(config, base, oid)), scope_line(config))))


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
    """The base's declaration when the gate is on; None when off; GateError otherwise.

    Off means no file at base (confirmed by ls-tree, not inferred from an error)
    or an explicit "gate": "off". Any other shape fails closed.
    """
    listed = git("ls-tree", "--name-only", base, "--", CONFIG_PATH).stdout.splitlines()
    if CONFIG_PATH not in listed:
        return None
    try:
        config = json.loads(git("show", f"{base}:{CONFIG_PATH}").stdout)
    except json.JSONDecodeError as exc:
        raise GateError(f"invalid {CONFIG_PATH} at base: {exc}") from exc
    if not isinstance(config, dict) or config.get("gate") not in ("on", "off"):
        raise GateError(f'invalid {CONFIG_PATH} at base: "gate" must be "on" or "off"')
    if config["gate"] == "off":
        return None
    checks = config.get("checks")
    if not isinstance(config.get("scope"), str) or not config["scope"].strip():
        raise GateError(f'invalid {CONFIG_PATH} at base: "scope" must name the check set')
    if (
        not isinstance(checks, list)
        or not checks
        or not all(
            isinstance(c, dict)
            and isinstance(c.get("name"), str)
            and isinstance(c.get("argv"), list)
            and c["argv"]
            and all(isinstance(a, str) for a in c["argv"])
            for c in checks
        )
    ):
        raise GateError(f'invalid {CONFIG_PATH} at base: "checks" must be a list of {{name, argv}}')
    for item in checks:
        if item["name"] != item["name"].strip() or not item["name"] or not single_line(item["name"]):
            raise GateError(f"invalid {CONFIG_PATH} at base: check name {item['name']!r} has edge spaces or controls")
        if not all(single_line(a) for a in item["argv"]):
            raise GateError(f"invalid {CONFIG_PATH} at base: argv of {item['name']!r} holds a control character")
    versions = config.get("versions", [])
    if not isinstance(versions, list) or not all(
        isinstance(v, dict)
        and isinstance(v.get("name"), str)
        and isinstance(v.get("argv"), list)
        and v["argv"]
        and all(isinstance(a, str) for a in v["argv"])
        for v in versions
    ):
        raise GateError(f'invalid {CONFIG_PATH} at base: "versions" must be a list of {{name, argv}}')
    if not single_line(config["scope"]) or not all(single_line(v["name"]) for v in versions):
        raise GateError(f"invalid {CONFIG_PATH} at base: scope or version names hold a control character")
    tiers = config.get("tiers", {})
    names = {c["name"] for c in checks}
    if not isinstance(tiers, dict) or not all(
        key == BOOKKEEPING_TIER and isinstance(value, list) and all(n in names for n in value)
        for key, value in tiers.items()
    ):
        raise GateError(
            f'invalid {CONFIG_PATH} at base: "tiers" may only map "{BOOKKEEPING_TIER}" to declared check names'
        )
    return config


def resolve(args):
    base, head = rev(args.base), rev(args.head)
    if not base or not head:
        raise GateError(f"cannot resolve base '{args.base}' or head '{args.head}'")
    return base, head


# ── notes transport ───────────────────────────────────────────────────────────


def fetch_notes(remote):
    """Make the local notes ref the remote's: the remote is the record of authority.

    When the remote has none, the local ref is dropped too, so a later push
    publishes only its own entry, never a stale or hand-made local note.
    """
    probe = git("ls-remote", "--exit-code", remote, NOTES_REF, check=False)
    if probe.returncode == 2:
        git("update-ref", "-d", NOTES_REF, check=False)
        return False
    if probe.returncode:
        raise GateError(f"cannot read {NOTES_REF} on {remote}: {probe.stderr.strip()}")
    git("fetch", "-q", remote, f"+{NOTES_REF}:{NOTES_REF}")
    return True


def read_note(oid, ref=NOTES_REF):
    shown = git("notes", f"--ref={ref}", "show", oid, check=False)
    return shown.stdout if shown.returncode == 0 else ""


def append_and_push(oid, text, remote):
    """Append one entry and push; on a lost race, refetch and append once more.

    Without a remote (--no-push) the entry goes to LOCAL_REF, which is never
    pushed: a trial record cannot ride along with a later published one.
    """
    if not remote:
        git("notes", f"--ref={LOCAL_REF}", "append", "-m", text, oid)
        return
    for attempt in (1, 2):
        if remote:
            fetch_notes(remote)
        git("notes", f"--ref={NOTES_REF}", "append", "-m", text, oid)
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
    first = (proc.stdout or proc.stderr).strip().split("\n", 1)[0]
    return sanitize(first) or "unknown"


def run_checks(config, cwd):
    results, ok = [], True
    for item in config["checks"]:
        start = time.monotonic()
        LOG.info("check %s: %s", item["name"], " ".join(item["argv"]))
        try:
            code = subprocess.run(item["argv"], cwd=cwd).returncode
            verdict = "pass" if code == 0 else f"fail(exit {code})"
        except OSError as exc:
            code, verdict = 127, f"fail(cannot run: {exc.strerror or exc})"
        ok = ok and code == 0
        results.append(f"{item['name']} {verdict} {time.monotonic() - start:.1f}s :: {' '.join(item['argv'])}")
    return ok, results


def cmd_run(args):
    base, head = resolve(args)
    config = load_config(base)
    if config is None:
        raise GateError(f"gate is off at base {args.base}: no {CONFIG_PATH} with gate=on")
    oid = candidate(base, head)
    config = effective(config, base, oid)
    actor = actor_line(args.runtime, args.model, args.effort)
    command = f"merge-gate run --base {args.base} --head {args.head}"
    if not single_line(actor) or not single_line(command):
        raise ValueError("actor or command holds a line break or control character")  # before any check runs
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
            "command": command,
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
    text = read_note(oid) + ("\n" + read_note(oid, LOCAL_REF) if args.local else "")
    code, reason = decide(parse_note(text), oid, accepted_scopes(config, base, oid))
    sys.stdout.write(reason + "\n")
    return code


def cmd_tier(args):
    """Tier of the candidate's changes, or of what head adds to the approved candidate."""
    base, head = resolve(args)
    new = candidate(base, head)
    old = base
    if args.since:
        since = rev(args.since)
        if not since:
            raise GateError(f"cannot resolve --since '{args.since}'")
        try:
            old = candidate(base, since)
        except GateError:
            sys.stdout.write(f"full: the approved tip {since[:12]} no longer merges cleanly into the base\n")
            return FAIL
    paths = changed_paths(old, new)
    tier = tier_of(paths)
    sys.stdout.write(f"{tier}: {len(paths)} path(s) changed\n")
    for path in paths:
        sys.stdout.write(f"  {path}\n")
    return PASS if tier == BOOKKEEPING_TIER else FAIL


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
    for name, func in (
        ("run", cmd_run),
        ("check", cmd_check),
        ("candidate", cmd_candidate),
        ("enabled", cmd_enabled),
        ("tier", cmd_tier),
    ):
        s = sub.add_parser(name)
        s.set_defaults(func=func)
        s.add_argument("--base", required=True, help="base ref, e.g. origin/main")
        if name == "enabled":
            continue
        s.add_argument("--head", required=True, help="branch head ref")
        if name in ("run", "check"):
            s.add_argument("--remote", default="origin", help="where refs/notes/gate lives")
        if name == "tier":
            s.add_argument("--since", help="approved tip: judge only what the head adds to it")
        if name == "check":
            s.add_argument("--no-fetch", action="store_true", help="read the local notes ref only")
            s.add_argument("--local", action="store_true", help="also read --no-push records (never for a merge)")
        if name == "run":
            s.add_argument(
                "--no-push", action="store_true", help="record in refs/notes/gate-local only; never pushed"
            )
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
    except Exception as exc:  # fail closed: an unexpected error must never read as "off" or "fail"
        LOG.error("unexpected %s: %s", type(exc).__name__, exc)
        return ERROR


if __name__ == "__main__":
    sys.exit(main())

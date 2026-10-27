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

Two moments (ticket 1245, tracker 1226; the policy is skills/merge/SKILL.md
§ Gating tiers): `"checks"` is the full declared set, run after the merge by
`run-after`; `"before": [names]` picks the cheap subset that `run` records on
the candidate before the merge, under the scope `<scope>/before-merge`, and
the only scope `check` accepts. Without `"before"` the full set runs before
the merge under the bare scope, as before ticket 1245. A `"tiers"` or
`"rerun"` key, left on bases older than ticket 1245, is ignored.

Tier (ticket 1221): a candidate whose changes against the base all match
BOOKKEEPING is bookkeeping-tier. `tier` reports the tier of a candidate, or
with `--since <approved tip>` the tier of what the head adds to the candidate
the approval saw: it decides whether a merge request needs a review, never
which checks run.

Plan (ticket 1220; the policy is skills/verify-gate/SKILL.md § Check plan):
`plan` prints, before anything runs, one line per declared check, `run`,
`reuse` or `skip` with its reason; adherence is one of those checks (`lint`
runs the `-m adherence` tests). A check outside the before set is skipped
(after-merge only). A check is reused from the latest published record entry
for the `--since` head when it passed there and the candidate is unchanged
since that record's (head and base alike); any change re-runs the before set,
which costs seconds. A check declared `"integration": true` is skipped unless
the diff touches a path its `"covers"` patterns match, or `--integration` is
passed.

After-merge runner (ticket 1244, tracker 1226): `run-after`, started in the
background once a merge has landed, takes a host-local flock (the kernel frees
it when the holder dies; busy: exit 0 at once, the holder will see the new
tip), runs the full declared set on the current `<remote>/<ref>` tip (a tip
that already carries an after-merge record is reported `covered` and not run
again: hooks/reference-transaction starts the runner on every move of main,
ticket 1265), appends
the record as a note on that tip, refetches, and loops while the tip moves; a
result covers its tip and every tip it passed over, but a tip the runner
started on (its oid is appended to `.git/idh/after-attempts` before the checks
run, ticket 1293) and that carries no record was not passed over: it crashed,
and main_sweep --after lists it. The record's scope is
`<scope>/after-merge` and its revision `tip=<oid>`, never `candidate=`, so
neither `check` nor the main-update hook can take it for a before-merge record.
On red it prints the ticket text (tip, failing checks, first-parent merges
since the last green after-record) and exits 1. With `--open-ticket` (ticket
1251; hooks/reference-transaction passes it) it also opens that ticket, still
under the lock: `tickets/<next>-after-merge-red-<tip12>.erg` written in a
throwaway worktree on branch `red-<tip12>`, pushed, opened as a request and
landed by scripts/raid_land.py as a bookkeeping-tier request, at most
RED_RETRIES landing attempts; a failing check in the before set leaves the
request open (its own record would refuse it). The dedupe key is the sorted failing-check set,
not the tip: no ticket opens when an open after-merge-red ticket on the tip or
a remote `red-*` branch already carries that set. An unlanded request stays
open with its branch, for a human. Nothing reverts, nothing re-runs.

Exit codes of `check`: 0 pass, 1 fail or stale scope, 2 no record, 3 error.
`enabled`: 0 on, 1 off, 3 error. `tier`: 0 bookkeeping (or, with --since,
unchanged), 1 full (an empty diff included), 3 error. `plan`: 0 printed, 1
gate off (no declared checks), 3 error. `run-after`: 0 green, off or busy,
1 red, 3 error.
Any unexpected exception exits 3.
"""

import argparse
import datetime
import fcntl
import fnmatch
import functools
import getpass
import importlib.util
import json
import logging
import os
import re
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
BEFORE_SCOPE = "before-merge"  # scope suffix of a `run` record when "before" is declared (ticket 1245)
AFTER_SCOPE = "after-merge"  # scope suffix of a run-after record (ticket 1244)
BUSY = 4  # run_after only, never an exit code: another runner holds the lock
ENV = 5  # run_after: the host's Python environment lacks a locked dependency; not a red tip (ticket 1288)
ENV_MARK = "env-problem "  # record line of a failed check whose only cause is a locked, uninstalled module
AFTER_WALK = 200  # first-parent commits searched for the last green after-record
RED_RETRIES = 2  # landing attempts of one red-ticket request (ticket 1251)
RED_KEY = "Failing checks: "  # the line of a red ticket that carries its dedupe key


class GateError(RuntimeError):
    """The gate could not establish its subject or read its record."""


@functools.cache
def toplevel(cwd):
    """The work tree root of `cwd`, or None (a bare repository): every git call runs there.

    A pathspec (ls-tree -- .merge-gate.json) and porcelain diff settings
    (diff.relative) read differently from a subdirectory; from the root they
    cannot.
    """
    proc = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=cwd)
    if proc.returncode:
        return None
    return proc.stdout.strip() or None


def git(*args, check=True, env=None):
    root = toplevel(os.getcwd())
    proc = subprocess.run(["git", *args], capture_output=True, text=True, env=env, cwd=root)
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


def decide(entries, candidate, scopes):
    """Latest entry naming this candidate decides. Returns (code, reason).

    `scopes` is the tuple of accepted scope lines (accepted_scopes).
    """
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


# ── before set (ticket 1245) and tier (ticket 1221) ───────────────────────────


def before_set(config):
    """The check set a before-merge record runs: the declared "before" subset, or all."""
    if "before" not in config:
        return config
    names = config["before"]
    checks = [c for c in config["checks"] if c["name"] in names]
    return {**config, "scope": f"{config['scope']}/{BEFORE_SCOPE}", "checks": checks}


def accepted_scopes(config):
    """The scope lines a before-merge record may carry: one per declaration."""
    return (scope_line(before_set(config)),)



def is_bookkeeping(path):
    return matches(path, BOOKKEEPING)


def matches(path, patterns):
    """`path` matches a pattern: "x/" covers the subtree, any other matches segment by segment."""
    for pattern in patterns:
        if pattern.endswith("/"):
            if path.startswith(pattern):
                return True
            continue
        parts, want = path.split("/"), pattern.split("/")
        if len(parts) == len(want) and all(fnmatch.fnmatchcase(a, b) for a, b in zip(parts, want)):
            return True
    return False


REGULAR_MODES = frozenset({"100644", "100755"})
# Seat reports recorded after a review attest it; they cannot void it. File
# shape only (never a verdict): a pure addition of a non-executable .md.
SEAT_REPORT = ("tickets/reviews/*/*.md",)


def changed_entries(old, new):
    """(path, new mode, status) of every entry that differs; renames count at both ends.

    Plumbing (diff-tree --raw), so no diff.relative, diff.ignoreSubmodules or
    other porcelain setting can hide an entry, and the mode is read with it.
    """
    out = git("diff-tree", "-r", "--raw", "-z", "--no-renames", old, new).stdout
    fields = out.split("\0")
    entries = []
    for meta, path in zip(fields[0::2], fields[1::2]):
        if not meta:
            break
        _old_mode, new_mode, _old_oid, _new_oid, status = meta.lstrip(":").split(" ")
        entries.append((path, new_mode, status[:1]))
    return entries


def is_seat_report(path, mode, status):
    """A seat report added as a plain file; a modified, deleted or executable one is not."""
    return status == "A" and mode == "100644" and matches(path, SEAT_REPORT)


def tier_of(entries):
    """Bookkeeping when every entry is a regular file (or a deletion) on a bookkeeping path.

    A symlink or gitlink at a bookkeeping path is not bookkeeping: what it
    points at is not what the path list vouches for. An empty list is never
    bookkeeping: nothing read is not a reading of nothing.
    """
    ok = all(is_bookkeeping(p) and (status == "D" or mode in REGULAR_MODES) or is_seat_report(p, mode, status)
             for p, mode, status in entries)
    return BOOKKEEPING_TIER if entries and ok else "full"



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
    before = config.get("before")
    names = {c["name"] for c in checks}
    if "before" in config and not (
        isinstance(before, list) and before and all(isinstance(n, str) and n in names for n in before)
    ):
        raise GateError(f'invalid {CONFIG_PATH} at base: "before" must be a non-empty list of declared check names')
    for item in checks:
        covers = item.get("covers", [])
        if not isinstance(item.get("integration", False), bool) or not (
            isinstance(covers, list) and all(isinstance(c, str) and c for c in covers)
        ):
            raise GateError(
                f'invalid {CONFIG_PATH} at base: {item["name"]!r} needs a boolean "integration" and a list "covers"'
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


# pytest appends " - <message>" after the id; a parametrized id may hold " - "
# itself, so a bracketed part ends at the first "]" that is followed by " - " or the line end.
FAILED_TEST = re.compile(r"^(?:FAILED|ERROR) (\S+?::[^\[\s]*(?:\[.*?\](?= - |$))?)(?: - .*)?$")


MISSING_MODULE = re.compile(r"ModuleNotFoundError: No module named '([\w.]+)'")


def _dist_key(name):
    return name.lower().replace("-", "_").replace(".", "_")


def locked_dists(cwd):
    """Normalized names of the distributions the tree's uv.lock pins; empty without one."""
    try:
        text = (Path(cwd) / "uv.lock").read_text(encoding="utf-8")
    except OSError:
        return set()
    return {_dist_key(m) for m in re.findall(r'^name = "([^"]+)"', text, re.M)}


def run_one(argv, cwd, env=None):
    """Run `argv`, echoing its output to stderr as it comes; (exit code, failed test ids, missing modules).

    The ids are pytest's `FAILED <nodeid>` / `ERROR <nodeid>` summary lines, in
    order, once each. The missing modules are the names of
    `ModuleNotFoundError` lines, once each. The gate keeps no other part of the output.
    """
    failed, missing = [], []
    with subprocess.Popen(
        argv, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", env=env
    ) as proc:
        for line in proc.stdout:
            sys.stderr.write(line)
            for name in MISSING_MODULE.findall(line):
                if name not in missing:
                    missing.append(name)  # a dotted name (a submodule of an installed package) never matches the lock
            found = FAILED_TEST.match(line.rstrip("\n"))
            if found and found.group(1) not in failed:
                failed.append(found.group(1))
    return proc.returncode, failed, missing


def run_checks(config, cwd, env=None):
    """(ok, record lines): one line per check, then `failed-test <check> <id>` per failed test of a failed check.

    A failed check with no failed test ids whose output shows missing modules, all of them distributions
    the tree's uv.lock pins, also gets `env-problem <check> <modules>`: the host's
    environment is out of step with the lock. A module the lock does not name stays red.
    """
    results, ok = [], True
    for item in config["checks"]:
        start = time.monotonic()
        LOG.info("check %s: %s", item["name"], " ".join(item["argv"]))
        failed, missing = [], []
        try:
            code, failed, missing = run_one(item["argv"], cwd, env)
            verdict = "pass" if code == 0 else f"fail(exit {code})"
        except OSError as exc:
            code, verdict = 127, f"fail(cannot run: {exc.strerror or exc})"
        ok = ok and code == 0
        results.append(f"{item['name']} {verdict} {time.monotonic() - start:.1f}s :: {' '.join(item['argv'])}")
        if code != 0:
            results += [sanitize(f"failed-test {item['name']} {test}") for test in failed]
            if missing and not failed and all("." not in m and _dist_key(m) in locked_dists(cwd) for m in missing):
                results.append(sanitize(f"{ENV_MARK}{item['name']} {' '.join(missing)}"))
    return ok, results


def environment_only(config, results):
    """True when every failed check of `results` carries an `env-problem` line."""
    failing = failing_checks(config, results)
    return bool(failing) and all(any(r.startswith(f"{ENV_MARK}{n} ") for r in results) for n in failing)


def runner_env():
    """The runner's environment without the triggering shell's VIRTUAL_ENV.

    An inherited VIRTUAL_ENV empties the Makefile's RUN, so the checks would run
    in that shell's venv instead of the locked environment of the tip (ticket 1288).
    """
    return {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}


def cmd_run(args):
    base, head = resolve(args)
    config = load_config(base)
    if config is None:
        raise GateError(f"gate is off at base {args.base}: no {CONFIG_PATH} with gate=on")
    oid = candidate(base, head)
    config = before_set(config)
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
    code, reason = decide(parse_note(text), oid, accepted_scopes(config))
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
        if git("rev-parse", f"{old}^{{tree}}").stdout == git("rev-parse", f"{new}^{{tree}}").stdout:
            sys.stdout.write(f"unchanged: the head adds nothing to the candidate of {since[:12]}\n")
            return PASS
    entries = changed_entries(old, new)
    tier = tier_of(entries)
    sys.stdout.write(f"{tier}: {len(entries)} path(s) changed\n")
    for path, mode, status in entries:
        sys.stdout.write(f"  {status} {mode} {path}\n")
    return PASS if tier == BOOKKEEPING_TIER else FAIL


# ── plan: what a gate runs, reuses or skips (ticket 1220) ─────────────────────


def prior_entry(head):
    """Latest complete record entry, on any candidate, whose head is `head`; None without one."""
    listing = git("notes", f"--ref={NOTES_REF}", "list", check=False).stdout.split()
    best = None
    for annotated in listing[1::2]:
        for entry in parse_note(read_note(annotated)):
            fields = dict(kv.partition("=")[::2] for kv in entry.get("revision", "").split())
            if fields.get("head") == head and all(f in entry for f in FIELDS):
                if best is None or entry["time"] >= best[0]["time"]:
                    best = (entry, fields)
    return best


def passed(entry, name):
    """Whether the record entry states check `name` passed."""
    return any(line.startswith(name + " pass ") for line in entry["checks"])


def delta_since(new, since):
    """(tier, entries, source, entry) of what changed from the record of `since` to candidate `new`.

    The record's own candidate is rebuilt from its base and head: a candidate
    that does not rebuild to the recorded id, or a record that is absent, is
    no source (entry None). The delta covers both a moved head and a moved base.
    """
    found = prior_entry(since)
    if found is None:
        return None, [], f"no record for {since[:12]}", None
    entry, fields = found
    old = fields.get("candidate", "")
    try:
        rebuilt = candidate(fields.get("base", ""), since)
    except GateError:
        rebuilt = ""
    if not old or rebuilt != old:
        return None, [], f"the record for {since[:12]} names a candidate that does not rebuild here", None
    source = f"record on {since} (candidate {old}, {entry['time']}, {entry['host']})"
    if git("rev-parse", f"{old}^{{tree}}").stdout == git("rev-parse", f"{new}^{{tree}}").stdout:
        return "unchanged", [], source, entry
    entries = changed_entries(old, new)
    return tier_of(entries), entries, source, entry


def first_paths(entries, limit=3):
    paths = [p for p, _mode, _status in entries if not is_bookkeeping(p)] or [p for p, _m, _s in entries]
    return ", ".join(paths[:limit]) + (" ..." if len(paths) > limit else "")


def cmd_plan(args):
    """Print, before anything runs, what the gate runs, reuses or skips, and why."""
    base, head = resolve(args)
    new = candidate(base, head)
    diff = changed_entries(base, new)
    tier = tier_of(diff)
    since = rev(args.since) if args.since else ""
    if args.since and not since:
        raise GateError(f"cannot resolve --since '{args.since}'")
    config = load_config(base)
    sys.stdout.write(f"plan: tier={tier} base={base} head={head} since={since or 'none'}\n")
    if config is None:
        sys.stdout.write(f"off: no {CONFIG_PATH} with gate=on at base; no declared checks to plan\n")
        return FAIL
    if since and not args.no_fetch:
        fetch_notes(args.remote)
    delta_tier, delta, source, entry = (None, [], "no --since head named", None)
    if since:
        delta_tier, delta, source, entry = delta_since(new, since)
    required = {c["name"] for c in before_set(config)["checks"]}
    for item in config["checks"]:
        name = item["name"]
        if name not in required:
            sys.stdout.write(f"skip {name}: after-merge only, not in the declared before set\n")
            continue
        if entry is not None and delta_tier == "unchanged" and passed(entry, name):
            sys.stdout.write(f"reuse {name}: passed on {source}; the candidate is unchanged since\n")
            continue
        if entry is not None and delta_tier == "unchanged":
            reason = f"did not pass on {source}"
        elif entry is not None:
            reason = f"the delta since {source} touches {first_paths(delta)}"
        else:
            reason = source
        if item.get("integration"):
            touched = [p for p, _m, _s in diff if matches(p, item.get("covers", []))]
            if args.integration:
                reason = f"integration check, asked for with --integration; {reason}"
            elif touched:
                reason = f"integration check, the diff touches {', '.join(touched[:3])}; {reason}"
            else:
                sys.stdout.write(f"skip {name}: integration check, the diff touches nothing it covers\n")
                continue
        sys.stdout.write(f"run {name}: {reason} :: {' '.join(item['argv'])}\n")
    return PASS


# ── after-merge runner (ticket 1244, tracker 1226) ────────────────────────────


def after_config(config):
    """The full declared set (no tier, no integration skip) under the after-merge scope."""
    return {**config, "scope": f"{config['scope']}/{AFTER_SCOPE}"}


def is_after_entry(entry):
    """An entry written by `run-after`: its scope name ends in /after-merge."""
    return entry.get("scope", "").partition(": ")[0].endswith("/" + AFTER_SCOPE)


def after_entries(oid):
    return [e for e in parse_note(read_note(oid)) if is_after_entry(e)]


def lock_file():
    """One host-local lock per repository, beside the main-guard journal."""
    common = git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    path = Path(common) / "idh" / "after-merge.lock"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def attempts_file():
    """Host-local list of the tips a runner started on, beside the lock (ticket 1293)."""
    return lock_file().with_name("after-attempts")


def note_attempt(tip):
    """Append `tip` before its checks run: a runner that dies leaves this and no record."""
    with open(attempts_file(), "a", encoding="utf-8") as handle:
        handle.write(tip + "\n")


def attempted_tips():
    path = attempts_file()
    return set(path.read_text(encoding="utf-8").split()) if path.exists() else set()


def fetch_tip(remote, branch):
    git("fetch", "-q", remote, f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}")
    tip = rev(f"refs/remotes/{remote}/{branch}")
    if not tip:
        raise GateError(f"cannot resolve {remote}/{branch} after fetch")
    return tip


def last_green(tip, limit=AFTER_WALK):
    """Newest first-parent ancestor of `tip` (itself excluded) with a passing after-record."""
    walked = git("rev-list", "--first-parent", f"--max-count={limit}", f"{tip}^", check=False).stdout.split()
    for oid in walked:
        if any(e.get("result") == "pass" for e in after_entries(oid)):
            return oid
    return None


def failing_checks(config, results):
    """Names of the declared checks with no `<name> pass ` record line, in declared order."""
    return [c["name"] for c in config["checks"] if not any(line.startswith(c["name"] + " pass ") for line in results)]


def red_report(tip, config, results):
    """The ticket text of a red after-merge record: a Title line, a blank line, the facts."""
    failing = failing_checks(config, results)
    green = last_green(tip)
    span = f"{green}..{tip}" if green else tip
    merges = git(
        "log", "--first-parent", f"--max-count={AFTER_WALK}", "--abbrev=12", "--format=- %h %s", span
    ).stdout.strip()
    return "\n".join(
        [
            f"Title: After-merge red on main {tip[:12]}: {', '.join(failing)}",
            "",
            f"Tip: {tip}",
            f"{RED_KEY}{', '.join(failing)}",
            f"Last green after-merge tip: {green or f'none in the last {AFTER_WALK} first-parent commits'}",
            "Merges since (first parent, newest first):",
            merges,
            "",
        ]
    )


# ── red ticket (ticket 1251) ──────────────────────────────────────────────────


@functools.cache
def raid_land():
    """scripts/raid_land.py, the landing executor, loaded beside this file."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)  # raid_land imports step_clock from its own directory
    spec = importlib.util.spec_from_file_location("raid_land", Path(here) / "raid_land.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def red_key(text):
    """The dedupe key a red ticket carries: its sorted failing-check names, or None."""
    for line in text.splitlines():
        if line.startswith(RED_KEY):
            return tuple(sorted(n.strip() for n in line[len(RED_KEY):].split(",") if n.strip()))
    return None


def open_red_keys(treeish):
    """Keys of the open after-merge-red tickets directly under tickets/ in `treeish`."""
    names = git("ls-tree", "--name-only", f"{treeish}:tickets", check=False).stdout.split()
    keys = set()
    for name in names:
        if "-after-merge-red-" not in name or not name.endswith(".erg"):
            continue
        text = git("show", f"{treeish}:tickets/{name}", check=False).stdout
        if re.search(r"^Closed:\s*\S", text.split("\n--- log ---", 1)[0], re.MULTILINE):
            continue
        key = red_key(text)
        if key is not None:
            keys.add(key)
    return keys


def red_branches(remote):
    """Remote `red-*` branches, fetched (pruned) into refs/remotes/<remote>/red-*: their tracking refs."""
    git("fetch", "-q", "--prune", remote, f"+refs/heads/red-*:refs/remotes/{remote}/red-*")
    out = git("for-each-ref", "--format=%(refname)", f"refs/remotes/{remote}/red-*").stdout
    return out.split()


def red_duplicate(key, tip, remote):
    """Where `key` is already carried (an open ticket on the tip, a red-* branch), or None."""
    if key in open_red_keys(tip):
        return f"an open after-merge-red ticket on {tip[:12]}"
    for ref in red_branches(remote):
        if git("merge-base", "--is-ancestor", ref, tip, check=False).returncode == 0:
            continue  # already in main: a leftover branch carries no ticket of its own
        if key in open_red_keys(ref):
            return f"branch {ref.split('/', 3)[-1]} on {remote}"
    return None


def erg_binary(tree):
    """The ticket tool: $ERG, else the tree's own tickets/erg, else this harness's."""
    for path in (os.environ.get("ERG"), tree / "tickets" / "erg", Path(__file__).resolve().parents[1] / "tickets" / "erg"):
        if path and Path(path).is_file():
            return str(path)
    raise GateError("no erg binary to number the red ticket")


def red_ticket_text(report, results):
    """The %erg 0.1 file of a red after-merge report; failed test ids (ticket 1254) appended."""
    head, _, facts = report.partition("\n\n")
    now = datetime.datetime.now(datetime.timezone.utc)
    tests = [line.split(" ", 1)[1] for line in results if line.startswith("failed-test ")]
    body = [
        "## Context",
        "",
        "Opened by `merge-gate.py run-after --open-ticket` (ticket 1251): the full",
        "declared set failed on main after a merge.",
        "",
        facts.rstrip("\n"),
        *(["", "Failed tests (check, test id):", *(f"- {t}" for t in tests)] if tests else []),
        "",
        "## Exit criteria",
        "",
        "- [ ] An after-merge record on main passes the checks named above.",
        "",
    ]
    return "\n".join(
        [
            "%erg 0.1",
            head,
            f"Created: {now:%Y-%m-%d}",
            "Author: merge-gate",
            "",
            "--- log ---",
            f"{now:%Y-%m-%dT%H:%MZ} merge-gate created",
            "",
            "--- body ---",
            *body,
        ]
    )


def run_in(tree, *argv):
    proc = subprocess.run(list(argv), cwd=tree, capture_output=True, text=True)
    if proc.returncode:
        raise GateError(f"{' '.join(argv[:3])}: {(proc.stderr or proc.stdout).strip()}")
    return proc.stdout.strip()


def open_red_ticket(report, results, tip, forge, remote, base, config=None):
    """Open (land) the red ticket of `report` unless its failing set is already carried; a status line.

    The branch starts from the freshly fetched base tip, not the red tip, so
    the ticket number sees every ticket landed while the checks ran. A request
    whose failing check is in the before-merge set would be refused by its
    own record: it is opened and left open, never landed.
    """
    key = red_key(report)
    duplicate = red_duplicate(key, tip, remote)
    if duplicate:
        return f"red ticket: not opened, {', '.join(key)} already carried by {duplicate}"
    branch = f"red-{tip[:12]}"
    blocked = sorted(set(key) & {c["name"] for c in before_set(config)["checks"]}) if config else []
    lander = raid_land()
    start = fetch_tip(remote, base)
    with tempfile.TemporaryDirectory(prefix="merge-gate-red-") as tmp:
        tree = Path(tmp) / "red"
        git("worktree", "add", "-q", "-B", branch, str(tree), start)
        try:
            (tree / "tickets").mkdir(exist_ok=True)
            erg = erg_binary(tree)
            number = run_in(tree, erg, "next-id", "tickets")
            path = tree / "tickets" / f"{number}-after-merge-red-{tip[:12]}.erg"
            path.write_text(red_ticket_text(report, results), encoding="utf-8")
            run_in(tree, erg, "validate", str(path))
            title = f"ticket({number}): after-merge red on main {tip[:12]}: {', '.join(key)}"
            run_in(tree, "git", "add", str(path.relative_to(tree)))
            run_in(tree, "git", "commit", "-q", "-m", f"{title}\n\nOpened by merge-gate.py run-after (ticket 1251).")
            # A plain push: an existing red-<tip12> (another failing set on this tip) is never overwritten.
            run_in(tree, "git", "push", "-q", remote, f"HEAD:refs/heads/{branch}")
            body = f"{report.partition(chr(10) + chr(10))[2]}\n**Ticket:** none\n\nOpened by `merge-gate.py run-after` (ticket 1251)."
            pr = forge.create(branch, base, title, body)
            if blocked:
                return (f"red ticket: {path.name} in request {pr}, not landed: {', '.join(blocked)} "
                        "is in the before-merge set, whose record would refuse it; left open")
            code = lander.REFUSED
            for _ in range(RED_RETRIES):
                code = lander.main_land(forge, pr, "-", [], base, tree, out=lambda m: sys.stdout.write(f"{m}\n"))
                if code != lander.REFUSED:
                    break
            if code in (lander.OK, lander.UNSYNCED):
                git("push", "-q", remote, "--delete", branch, check=False)
                return f"red ticket: {path.name} landed by request {pr} (raid_land exit {code})"
            return f"red ticket: {path.name} in request {pr}, not landed (raid_land exit {code}); left open"
        finally:
            git("worktree", "remove", "--force", str(tree), check=False)
            git("branch", "-D", branch, check=False)


def run_after_once(tip, remote, actor, command):
    """Run the full set on `tip`, note it there; (ok, results, config), or None when the tip declares no gate."""
    config = load_config(tip)
    if config is None:
        return None
    config = after_config(config)
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with tempfile.TemporaryDirectory(prefix="merge-gate-after-") as tmp:
        tree = Path(tmp) / "tip"
        git("worktree", "add", "-q", "--detach", str(tree), tip)
        try:
            ok, results = run_checks(config, tree, runner_env())
            versions = " · ".join(f"{v['name']} {first_line(v['argv'], tree)}" for v in config.get("versions", []))
        finally:
            git("worktree", "remove", "--force", str(tree), check=False)
    env_only = not ok and environment_only(config, results)
    entry = format_entry(
        {
            "result": "pass" if ok else "environment" if env_only else "fail",
            "time": started,
            "actor": actor,
            "host": socket.gethostname(),
            "revision": f"tip={tip}",  # never `candidate=`: decide() cannot match it
            "command": command,
            "scope": scope_line(config),
            "versions": versions or NOT_STATED,
            "checks": results,
        }
    )
    append_and_push(tip, entry, remote)
    sys.stdout.write(entry)
    return ok, results, config, env_only


def run_after(remote, branch, actor, command, forge=None):
    """Hold the lock, run on the newest tip until it stops moving: the last run's code, or BUSY.

    With a forge, a red run opens its ticket (open_red_ticket), still under the lock.
    `forge` is a forge or a zero-argument factory of one, called only on red, after
    the record is pushed, inside the guard that keeps the red standing whatever the
    build raises (ticket 1283: a forge built before the checks ran lost every record).
    """
    with open(lock_file(), "a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            sys.stdout.write(f"busy: another runner holds {handle.name}; it will see the new tip\n")
            return BUSY
        code, done = PASS, None
        while (tip := fetch_tip(remote, branch)) != done:
            fetch_notes(remote)
            prior = after_entries(tip)
            if prior:  # the hook starts a runner on every move of main, a sync to a covered tip included
                if prior[-1].get("result") == "environment":  # the host may be fixed by now: judge again
                    sys.stdout.write(f"covered: {tip} carries only an environment record; running again\n")
                else:
                    sys.stdout.write(f"covered: {tip} already carries an after-merge record; not run again\n")
                    code = PASS if prior[-1].get("result") == "pass" else FAIL
                    done = tip
                    continue
            note_attempt(tip)
            outcome = run_after_once(tip, remote, actor, command)
            if outcome is None:
                sys.stdout.write(f"off: {tip[:12]} declares no gate; nothing to run\n")
                code = PASS
            elif outcome[0]:
                sys.stdout.write(f"pass: after-merge record on {tip}\n")
                code = PASS
            elif outcome[3]:
                sys.stdout.write(
                    f"environment: {tip[:12]} failed on modules the lock names but this host lacks "
                    f"({'; '.join(r for r in outcome[1] if r.startswith(ENV_MARK))}); "
                    "no ticket opened, run `uv sync --frozen` here\n"
                )
                code = ENV
            else:
                report = red_report(tip, outcome[2], outcome[1])
                sys.stdout.write(f"red: after-merge record on {tip}; its ticket:\n{report}")
                if forge is not None:
                    try:
                        built = forge() if callable(forge) else forge
                        sys.stdout.write(open_red_ticket(report, outcome[1], tip, built, remote, branch, outcome[2]) + "\n")
                    except Exception as exc:  # the red stands in the note and the log whatever happens here
                        sys.stdout.write(f"red ticket: not opened ({type(exc).__name__}: {exc})\n")
                code = FAIL
            done = tip
        return code


def cmd_run_after(args):
    actor = actor_line(args.runtime, args.model, args.effort)
    command = f"merge-gate run-after --remote {args.remote} --ref {args.ref}"
    if not single_line(actor) or not single_line(command):
        raise ValueError("actor or command holds a line break or control character")
    forge = (lambda: raid_land().forge.GhForge()) if args.open_ticket else None  # built only on red
    code = run_after(args.remote, args.ref, actor, command, forge)
    return PASS if code == BUSY else code


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
    after = sub.add_parser("run-after", help="full set on the newest tip of --ref, after a merge")
    after.set_defaults(func=cmd_run_after)
    after.add_argument("--remote", default="origin", help="where the branch and refs/notes/gate live")
    after.add_argument("--ref", default="main", help="branch name on --remote (default main)")
    after.add_argument("--open-ticket", action="store_true", help="on red, open and land its ticket (ticket 1251)")
    for name in ("runtime", "model", "effort"):
        after.add_argument(f"--{name}", default=os.environ.get(f"MERGE_GATE_{name.upper()}", ""))
    for name, func in (
        ("run", cmd_run),
        ("check", cmd_check),
        ("candidate", cmd_candidate),
        ("enabled", cmd_enabled),
        ("tier", cmd_tier),
        ("plan", cmd_plan),
    ):
        s = sub.add_parser(name)
        s.set_defaults(func=func)
        s.add_argument("--base", required=True, help="base ref, e.g. origin/main")
        if name == "enabled":
            continue
        s.add_argument("--head", required=True, help="branch head ref")
        if name in ("run", "check", "plan"):
            s.add_argument("--remote", default="origin", help="where refs/notes/gate lives")
        if name == "tier":
            s.add_argument("--since", help="approved tip: judge only what the head adds to it")
        if name == "plan":
            s.add_argument("--since", help="head whose gate record may be reused")
            s.add_argument("--integration", action="store_true", help="run integration checks whatever the diff")
            s.add_argument("--no-fetch", action="store_true", help="read the local notes ref only")
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

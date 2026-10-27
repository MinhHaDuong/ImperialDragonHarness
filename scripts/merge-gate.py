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
`<scope>/bookkeeping`; `check` accepts that scope, the fast-path one (below)
or the full one for a bookkeeping candidate, and only the full one otherwise. `tier` reports the tier
of a candidate, or with `--since <approved tip>` the tier of what the head adds
to the candidate the approval saw: the one mechanical reading of the tiers.

Plan (ticket 1220; the policy is skills/verify-gate/SKILL.md § Check plan):
`plan` prints, before anything runs, one line per declared check, `run`,
`reuse` or `skip` with its reason, and one for the adherence result. A check
is reused from the latest published record entry for the `--since` head when
it passed there and the change from that record's candidate to the current
one (head and base alike) is empty, or bookkeeping and the check is not
declared under `"rerun": {"bookkeeping": [...]}` (undeclared: every check
re-runs). A check declared `"integration": true` is skipped unless the diff
touches a path its `"covers"` patterns match, or `--integration` is passed.

Fast path (ticket 1226; the policy is skills/merge/SKILL.md § Gating tiers):
when the base declares `"fastpath": {"checks": [names], "max_lag": K,
"max_age_minutes": M}` (plus, for scripts/merge_monitor.py,
`"monitor_timeout_minutes"` and `"rerun": {check: argv}`), a bookkeeping candidate's record runs only those
checks, under the scope `<scope>/fastpath`, while the fast path is open: the
latest verdict on main's first-parent line at or behind the base is green,
the base at most K-1 merges past it (the candidate makes the K-th), and the
verdict younger than M minutes and not stamped in the future. A verdict is a note in refs/notes/gate-verdict on a main tip, written
by scripts/merge_monitor.py after the full check set ran there; a record of
another scope on the merge's own candidate is a verdict too (it ran the
checks the tier demands). A red verdict, none within reach, or an old one
closes the path; the record then runs the tier set, as before. Openness is
judged when the record is written and stated in it; `check` accepts a
fast-path record of a bookkeeping candidate that states the path open, and,
when it fetches (the merge-time check, not the hook's `--no-fetch` one),
only while the path is still open on the base. `fastpath` prints the state.

Exit codes of `check`: 0 pass, 1 fail or stale scope, 2 no record, 3 error.
`enabled`: 0 on, 1 off, 3 error. `tier`: 0 bookkeeping (or, with --since,
unchanged), 1 full (an empty diff included), 3 error. `plan`: 0 printed, 1
gate off (no declared checks), 3 error. `fastpath`: 0 open, 1 closed (or
not declared), 3 error.
Any unexpected exception exits 3.
"""

import argparse
import datetime
import fnmatch
import functools
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
VERDICT_REF = "refs/notes/gate-verdict"  # monitor verdicts on main tips (ticket 1226)
LOCAL_REF = "refs/notes/gate-local"  # --no-push records: never pushed, read by `check --local` only
# Characters that end a line for some reader: every C0 control, DEL, NEL, LS, PS.
LINE_BREAKERS = frozenset(chr(c) for c in range(32)) | {"\x7f", "\x85", "\u2028", "\u2029"}
CONFIG_PATH = ".merge-gate.json"
HEADER = "merge-gate-record: v1"
FIELDS = ("result", "time", "actor", "host", "revision", "command", "scope", "versions")
VERDICT_HEADER = "merge-gate-verdict: v1"
VERDICT_FIELDS = ("result", "time", "host", "revision", "scope")
VERDICT_EXTRAS = ("failed-tests", "culprit")
TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
NOT_STATED = "not-stated"
GIT_TIMEOUT = 300  # seconds; a hung fetch or push must not hold the monitor's lock for ever
CLOCK_SKEW = 300  # seconds a verdict may sit ahead of this host's clock
PASS, FAIL, MISSING, ERROR = 0, 1, 2, 3
# Bookkeeping paths, the one home of the list (ticket 1221). A pattern ending
# in "/" covers its whole subtree; any other matches segment by segment, so
# "tickets/*.erg" does not reach tickets/erg (code) or tickets/closed/.
BOOKKEEPING = ("tickets/*.erg", "tickets/closed/*.erg", "STATE.md", "memory/")
BOOKKEEPING_TIER = "bookkeeping"
FASTPATH = "fastpath"


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
    try:
        proc = subprocess.run(["git", *args], capture_output=True, text=True, env=env, cwd=root, timeout=GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        if check:
            raise GateError(f"git {' '.join(args)}: no answer within {GIT_TIMEOUT}s") from None
        return subprocess.CompletedProcess(["git", *args], 124, "", f"no answer within {GIT_TIMEOUT}s")
    if check and proc.returncode:
        raise GateError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc


def rev(ref):
    return git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}").stdout.strip()


# ── record format ──────────────────────────────────────────────────────────────


def format_entry(fields, header=HEADER, keys=FIELDS, extras=("fastpath",)):
    """One entry: the header line, every field in `keys` order, the optional `extras` present, the checks."""
    missing = [f for f in keys if not fields.get(f)]
    if missing:
        raise ValueError("record entry lacks " + ", ".join(missing))
    present = [key for key in extras if fields.get(key)]
    values = [fields[key] for key in (*keys, *present)] + list(fields.get("checks", []))
    if not all(single_line(v) for v in values):
        # A line break in a free-text value (actor, command) would start a forged entry.
        raise ValueError("record values may not contain a line break or control character")
    lines = [header] + [f"{key}: {fields[key]}" for key in (*keys, *present)]
    lines += [f"check: {line}" for line in fields.get("checks", [])]
    return "\n".join(lines) + "\n"


def format_verdict(fields):
    """One monitor verdict entry (refs/notes/gate-verdict), in the record's line format."""
    return format_entry(fields, VERDICT_HEADER, VERDICT_FIELDS, VERDICT_EXTRAS)


def single_line(value):
    """No control character and no Unicode line boundary, anywhere in the value."""
    return isinstance(value, str) and not any(c in LINE_BREAKERS for c in value)


def sanitize(text):
    """Captured tool output: line boundaries and controls become spaces."""
    return "".join(" " if c in LINE_BREAKERS else c for c in text).strip()


def parse_note(text, header=HEADER, keys=(*FIELDS, FASTPATH)):
    """Entries in note order; lines outside an entry, or unknown keys, are ignored.

    Lines end at \n only: the writer refuses every other line boundary, and a
    reader that split on them (str.splitlines) would see entries the writer
    never wrote.
    """
    entries, current = [], None
    for line in text.split("\n"):
        if line == header:
            current = {"checks": []}
            entries.append(current)
            continue
        key, sep, value = line.partition(": ")
        if current is None or not sep:
            continue
        if key == "check":
            current["checks"].append(value)
        elif key in keys and key not in current:
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
    if latest["scope"].partition(": ")[0].endswith(f"/{FASTPATH}") and not latest.get(FASTPATH, "").startswith("open"):
        return FAIL, "fail: latest record ran the fast-path checks but does not state the fast path open"
    return PASS, f"pass: {latest['time']} on {latest['host']} by {latest['actor']}"


# ── gating tiers ──────────────────────────────────────────────────────────────


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


def tier_of(entries):
    """Bookkeeping when every entry is a regular file (or a deletion) on a bookkeeping path.

    A symlink or gitlink at a bookkeeping path is not bookkeeping: what it
    points at is not what the path list vouches for. An empty list is never
    bookkeeping: nothing read is not a reading of nothing.
    """
    ok = all(is_bookkeeping(p) and (status == "D" or mode in REGULAR_MODES) for p, mode, status in entries)
    return BOOKKEEPING_TIER if entries and ok else "full"


def effective(config, base, oid):
    """The check set the record of candidate `oid` runs: a tier's subset, or all."""
    names = config.get("tiers", {}).get(BOOKKEEPING_TIER)
    if not names or tier_of(changed_entries(base, oid)) != BOOKKEEPING_TIER:
        return config
    checks = [c for c in config["checks"] if c["name"] in names]
    return {**config, "scope": f"{config['scope']}/{BOOKKEEPING_TIER}", "checks": checks}


def accepted_scopes(config, base, oid):
    """A tier record, or the full set, which covers every tier; a fast-path record for a bookkeeping candidate."""
    tiered = effective(config, base, oid)
    fast = (scope_line(fast_config(config)),) if FASTPATH in config and tiered is not config else ()
    return tuple(dict.fromkeys((scope_line(tiered), scope_line(config), *fast)))


def fast_config(config):
    """The check set of a fast-path record."""
    names = config[FASTPATH]["checks"]
    checks = [c for c in config["checks"] if c["name"] in names]
    return {**config, "scope": f"{config['scope']}/{FASTPATH}", "checks": checks}


# ── fast path: is main verified close enough below this base? (ticket 1226) ──


def now():
    """Seconds since the epoch; MERGE_GATE_NOW overrides it (tests of the age bound)."""
    return float(os.environ.get("MERGE_GATE_NOW") or time.time())


def stamp_age(stamp):
    """Seconds since a record or verdict time stamp; None when it does not parse."""
    try:
        then = datetime.datetime.strptime(stamp, TIME_FORMAT).replace(tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None
    return now() - then.timestamp()


def verdict_on(tip):
    """(result, time, source) of what verified main tip `tip`, or None: the monitor's verdict, else the merge's record.

    The latest verdict entry naming the tip decides. Without one, a merge
    whose candidate (rebuilt from its two parents) has its tree and carries a
    passing record of a scope other than the fast path counts as green: that
    record ran the checks the tier demands on this very tree.
    """
    entries = [e for e in parse_note(read_note(tip, VERDICT_REF), VERDICT_HEADER, VERDICT_FIELDS)
               if e.get("revision") == f"tip={tip}" and all(f in e for f in VERDICT_FIELDS)]
    if entries:
        latest = entries[-1]
        return latest["result"], latest["time"], f"verdict on {tip[:12]}"
    parents = git("rev-list", "--parents", "-n", "1", tip).stdout.split()[1:]
    if len(parents) != 2:
        return None
    config = load_config(parents[0])
    try:
        oid = candidate(*parents)
    except GateError:
        return None
    if config is None or git("rev-parse", f"{oid}^{{tree}}").stdout != git("rev-parse", f"{tip}^{{tree}}").stdout:
        return None
    fast = scope_line(fast_config(config)) if FASTPATH in config else None
    scopes = tuple(s for s in accepted_scopes(config, parents[0], oid) if s != fast)
    mine = [e for e in parse_note(read_note(oid)) if f"candidate={oid} " in e.get("revision", "") + " "]
    if mine and decide(mine, oid, scopes)[0] == PASS:
        return "pass", mine[-1]["time"], f"record on the candidate of {tip[:12]}"
    return None


def fastpath_state(config, base):
    """(open, reason) for a bookkeeping record on `base`. Closed when not declared."""
    declared = config.get(FASTPATH)
    if not declared:
        return False, "closed: no fast path declared"
    limit, bound = declared["max_lag"], declared["max_age_minutes"] * 60
    walked = git("rev-list", "--first-parent", f"--max-count={limit}", base).stdout.split()
    for lag, tip in enumerate(walked):
        found = verdict_on(tip)
        if found is None:
            continue
        result, stamp, source = found
        if result != "pass":
            return False, f"closed: red {source} ({stamp})"
        age = stamp_age(stamp)
        if age is not None and age < -CLOCK_SKEW:
            return False, f"closed: last green {source} is stamped in the future ({stamp})"
        if age is None or age > bound:
            return False, f"closed: last green {source} is older than {declared['max_age_minutes']:g} min ({stamp})"
        return True, f"open: {lag + 1} of {limit} merges past green ({source}, {max(age, 0) / 60:.0f} min old)"
    return False, f"closed: no verdict on the last {len(walked)} commits of main (limit {limit}); unverified"


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
    rerun = config.get("rerun", {})
    if not isinstance(rerun, dict) or not all(
        key == BOOKKEEPING_TIER and isinstance(value, list) and all(n in names for n in value)
        for key, value in rerun.items()
    ):
        raise GateError(
            f'invalid {CONFIG_PATH} at base: "rerun" may only map "{BOOKKEEPING_TIER}" to declared check names'
        )
    fast = config.get(FASTPATH)
    if fast is not None and not (
        isinstance(fast, dict)
        and isinstance(fast.get("checks"), list)
        and fast["checks"]  # an empty set would record a pass that ran nothing
        and all(n in names for n in fast["checks"])
        and isinstance(fast.get("max_lag"), int)
        and fast["max_lag"] >= 1
        and isinstance(fast.get("max_age_minutes"), (int, float))
        and fast["max_age_minutes"] > 0
        and isinstance(fast.get("monitor_timeout_minutes", 30), (int, float))
        and isinstance(fast.get("rerun", {}), dict)
        and all(
            n in names and isinstance(a, list) and a and all(isinstance(x, str) for x in a)
            for n, a in fast.get("rerun", {}).items()
        )
    ):
        raise GateError(
            f'invalid {CONFIG_PATH} at base: "{FASTPATH}" needs declared "checks", '
            '(at least one), "max_lag" >= 1, "max_age_minutes" > 0 and "rerun" argv by check name'
        )
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


def local_ref(ref):
    """The local ref's commit, "" when it does not exist; any other failed read raises.

    `rev-parse --verify --quiet` exits 1 for an absent ref. A timeout (124) or a
    fatal error is not an absent ref and must not be read as one (gaze round 10).
    """
    read = git("rev-parse", "--verify", "--quiet", ref, check=False)
    if read.returncode not in (0, 1):
        raise GateError(f"git rev-parse {ref}: exit {read.returncode}: {read.stderr.strip()}")
    return read.stdout.strip() if read.returncode == 0 else ""


def fetch_notes(remote, *refs):
    """Make the local notes refs the remote's: the remote is the record of authority.

    When the remote lacks one, the local ref is dropped too, at the value read
    before the listing (a ref a concurrent fetch moved meanwhile stays), so a
    later push publishes only its own entry, never a stale or hand-made local
    note. A local ref that cannot be read or dropped fails closed. One
    listing and one fetch serve every ref. Returns whether the remote has the
    first ref (refs/notes/gate by default).
    """
    refs = refs or (NOTES_REF,)
    # Read each local ref before asking the remote: the listing can go stale before
    # the drop, and a concurrent fetch may by then have brought a newer entry (the
    # first red verdict, say). Only the value seen before the listing is dropped
    # (gaze round 9); a ref that moved since is that fetch's, and stays.
    before = {ref: local_ref(ref) for ref in refs}
    probe = git("ls-remote", remote, *refs, check=False)
    if probe.returncode:
        raise GateError(f"cannot read {' '.join(refs)} on {remote}: {probe.stderr.strip()}")
    listed = {line.split("\t", 1)[1] for line in probe.stdout.splitlines() if "\t" in line}
    for ref in refs:
        if ref in listed or not before[ref]:
            continue
        dropped = git("update-ref", "-d", ref, before[ref], check=False)
        if dropped.returncode and local_ref(ref) == before[ref]:
            # a stale local verdict must not survive: a failed drop fails closed
            raise GateError(f"git update-ref -d {ref}: {dropped.stderr.strip()}")
    present = [ref for ref in refs if ref in listed]
    if present:
        git("fetch", "-q", remote, *(f"+{ref}:{ref}" for ref in present))
    return refs[0] in listed


def read_note(oid, ref=NOTES_REF):
    shown = git("notes", f"--ref={ref}", "show", oid, check=False)
    # Exit 1 is the one absent answer (no note, or no notes ref yet). Anything else
    # (124 a hung read, 128 a fatal error) is not an absent note: fail closed, never
    # fall through to another source.
    if shown.returncode not in (0, 1):
        raise GateError(f"git notes --ref={ref} show {oid}: exit {shown.returncode}: {shown.stderr.strip()}")
    return shown.stdout if shown.returncode == 0 else ""


def note_at(commit, oid):
    """The note on `oid` as stored in notes commit `commit` (not the moving ref), or ""."""
    for line in git("ls-tree", "-r", commit).stdout.splitlines():
        meta, _, path = line.partition("\t")
        if path.replace("/", "") == oid:
            return git("cat-file", "-p", meta.split()[2]).stdout
    return ""


def append_and_push(oid, text, remote, ref=NOTES_REF, fetched=False):
    """Append one entry and push; on a lost race, refetch and append once more.

    The push sends the notes commit that holds the entry, by SHA, once the entry
    is seen in it: a concurrent fetch may reset the local ref in between, and
    an entry lost that way is a lost race.

    Without a remote (--no-push) the entry goes to LOCAL_REF, which is never
    pushed: a trial record cannot ride along with a later published one.
    `fetched` says the caller has just fetched `ref`: the first attempt skips
    that fetch; a lost race refetches as usual.
    """
    if not remote:
        git("notes", f"--ref={LOCAL_REF}", "append", "-m", text, oid)
        return
    for attempt in (1, 2):
        if attempt > 1 or not fetched:
            fetch_notes(remote, ref)
        git("notes", f"--ref={ref}", "append", "-m", text, oid)
        # Push the commit that holds this entry, by SHA, and only once the entry is
        # seen in it: a concurrent fetch (+ref:ref) can reset the local ref between
        # the append and the push, and pushing the ref by name would then report
        # "up to date" while the entry is lost (gaze round 8). A lost entry is a lost race.
        tip = local_ref(ref)
        if not tip or text not in note_at(tip, oid):
            LOG.warning("notes entry lost to a concurrent fetch (attempt %d)", attempt)
            continue
        push = git("push", "-q", remote, f"{tip}:{ref}", check=False)
        if push.returncode == 0:
            return
        LOG.warning("notes push rejected (attempt %d): %s", attempt, push.stderr.strip())
    raise GateError(f"could not publish the entry to {ref} on {remote} after two attempts")


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
    clock = time.monotonic()
    base, head = resolve(args)
    config = load_config(base)
    if config is None:
        raise GateError(f"gate is off at base {args.base}: no {CONFIG_PATH} with gate=on")
    oid = candidate(base, head)
    tiered = effective(config, base, oid)
    fastpath, fetched = "", False
    if FASTPATH in config and tiered is not config:
        if not args.no_push:
            fetch_notes(args.remote, NOTES_REF, VERDICT_REF)
            fetched = True
        is_open, fastpath = fastpath_state(config, base)
        if is_open:
            tiered = fast_config(config)
    config = tiered
    actor = actor_line(args.runtime, args.model, args.effort)
    command = f"merge-gate run --base {args.base} --head {args.head}"
    if not single_line(actor) or not single_line(command):
        raise ValueError("actor or command holds a line break or control character")  # before any check runs
    started = datetime.datetime.now(datetime.timezone.utc).strftime(TIME_FORMAT)
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
            "fastpath": fastpath,
            "checks": results,
        }
    )
    append_and_push(oid, entry, None if args.no_push else args.remote, fetched=fetched)
    sys.stdout.write(entry)
    sys.stdout.write(f"{'pass' if ok else 'fail'}: recorded on candidate {oid}\n")
    sys.stdout.write(f"duration: {time.monotonic() - clock:.1f}s\n")
    return PASS if ok else FAIL


def cmd_check(args):
    base, head = resolve(args)
    config = load_config(base)
    if config is None:
        raise GateError(f"gate is off at base {args.base}")
    oid = candidate(base, head)
    if not args.no_fetch and not fetch_notes(args.remote, NOTES_REF, VERDICT_REF):
        sys.stdout.write(f"missing: {args.remote} has no {NOTES_REF}; no record on candidate {oid}\n")
        return MISSING
    text = read_note(oid) + ("\n" + read_note(oid, LOCAL_REF) if args.local else "")
    entries = parse_note(text)
    code, reason = decide(entries, oid, accepted_scopes(config, base, oid))
    mine = [e for e in entries if f"candidate={oid} " in e.get("revision", "") + " "]
    if code == PASS and not args.no_fetch and FASTPATH in config and mine[-1]["scope"] == scope_line(fast_config(config)):
        still_open, why = fastpath_state(config, base)  # at merge time, not only when recorded
        if not still_open:
            code, reason = FAIL, f"fail: the fast path has closed since the record ({why}); record again"
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
    # Undeclared: a bookkeeping delta re-runs every check, as before ticket 1220.
    rerun = set(config.get("rerun", {}).get(BOOKKEEPING_TIER, [c["name"] for c in config["checks"]]))
    required = {c["name"] for c in effective(config, base, new)["checks"]}
    for item in config["checks"]:
        name = item["name"]
        if name not in required:
            sys.stdout.write(f"skip {name}: not in the {tier} tier's declared checks\n")
            continue
        if entry is not None and delta_tier in ("unchanged", BOOKKEEPING_TIER) and passed(entry, name):
            if delta_tier == "unchanged":
                sys.stdout.write(f"reuse {name}: passed on {source}; the candidate is unchanged since\n")
                continue
            if name not in rerun:
                sys.stdout.write(f"reuse {name}: passed on {source}; the delta since touches bookkeeping only\n")
                continue
            reason = f"declared to re-run over a bookkeeping delta (since {source})"
        elif entry is not None and delta_tier in ("unchanged", BOOKKEEPING_TIER):
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
    if args.adherence_from:
        reviewed = rev(args.adherence_from)
        if not reviewed:
            raise GateError(f"cannot resolve --adherence-from '{args.adherence_from}'")
        try:
            old = candidate(base, reviewed)
        except GateError:
            old = ""
        entries = changed_entries(old, new) if old else []
        if old and not entries:
            sys.stdout.write(f"reuse adherence: result on {reviewed}; the candidate is unchanged since\n")
        elif old and tier_of(entries) == BOOKKEEPING_TIER:
            sys.stdout.write(f"reuse adherence: result on {reviewed}; the delta since is bookkeeping\n")
        else:
            why = f"touches {first_paths(entries)}" if old else "no longer merges cleanly into the base"
            sys.stdout.write(f"run adherence: the delta since {reviewed[:12]} {why}\n")
    else:
        sys.stdout.write("run adherence: no prior adherence result named (--adherence-from)\n")
    return PASS


def cmd_fastpath(args):
    """Whether a bookkeeping record on this base would take the fast path, and why."""
    base = rev(args.base)
    if not base:
        raise GateError(f"cannot resolve base '{args.base}'")
    config = load_config(base)
    if config is None:
        sys.stdout.write(f"closed: gate is off at base {args.base}\n")
        return FAIL
    if not args.no_fetch:
        fetch_notes(args.remote, NOTES_REF, VERDICT_REF)
    is_open, reason = fastpath_state(config, base)
    sys.stdout.write(reason + "\n")
    return PASS if is_open else FAIL


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
        ("plan", cmd_plan),
        ("fastpath", cmd_fastpath),
    ):
        s = sub.add_parser(name)
        s.set_defaults(func=func)
        s.add_argument("--base", required=True, help="base ref, e.g. origin/main")
        if name == "fastpath":
            s.add_argument("--remote", default="origin", help="where the notes refs live")
            s.add_argument("--no-fetch", action="store_true", help="read the local notes refs only")
        if name in ("enabled", "fastpath"):
            continue
        s.add_argument("--head", required=True, help="branch head ref")
        if name in ("run", "check", "plan"):
            s.add_argument("--remote", default="origin", help="where refs/notes/gate lives")
        if name == "tier":
            s.add_argument("--since", help="approved tip: judge only what the head adds to it")
        if name == "plan":
            s.add_argument("--since", help="head whose gate record may be reused")
            s.add_argument("--adherence-from", help="head the prior adherence result was given on")
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

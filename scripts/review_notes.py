#!/usr/bin/env python3
"""The one door to refs/notes/review: review requests, plans, reports, answers and
verdicts stored in git, no forge needed (ticket 1273; design
conception/2026-10-27-notes-review-spec.md, accepted 2026-10-27).

    review_notes.py [-C <repo>] [--remote origin] <command> ...

Layout (spec §1, §3). Each review owns one note, on the fixed anchor
`git hash-object` of "idh-review <review_id>", never on a reviewed commit, so a
rebase moves nothing. A note holds one JSON object per line, `ts` first; readers
skip blank lines (`git notes append` separates entries with one). Every entry
names `head`, `base`, `base_ref`, `merge_base` and `range_patch_id` (the
`git patch-id --verbatim` of the range; an empty range gives "" and never
matches). A request keeps its head at refs/review-heads/<review_id>/<request_id>.

Transport (spec §2). `setup` writes the two fetch refspecs and the cat_sort_uniq
merge strategy (no push refspec, no rewriteRef); with no remote it is a no-op and
everything stays local. Both refspecs are globs (ticket 1300): an exact
refs/notes/review refspec made a plain `git fetch origin` exit 128 while the remote had no
notes; setup replaces that exact spec where an older setup wrote it. `sync` = fetch into refs/notes/origin/review, fast-forward
or `notes merge -s cat_sort_uniq`, push, at most 5 attempts; never forced.
`publish` = sync, refetch, then the remote tip must equal the local one, every
named entry must be readable from it, and the review-head of each named entry's
request must exist on the remote naming that request's head (never forced; a
missing or moved one is reported on stderr): prints done-unpublished | published |
retrievable and exits non-zero below retrievable. `refresh` = the reader half:
fetch, check and integrate, no push; `resolve` (CLI `find`) refreshes before
looking a branch up, so a fresh clone after setup + `git fetch` finds the
published review. A remote that cannot be read leaves refresh `stale`, a warning,
never a refusal (ticket 1300): `resolve` then answers from the local entries, and
with none refuses ("remote unreadable, no local review"), never "no review"; a
Tamper still raises. `gate` reports a stale read in its `stale` field.

Units (ticket 1300). A request may carry `unit`: `pr:<n>` for a forge merge request,
inherited by the later requests of its review. A PR number is never reused, while a
branch name is (merge never deletes branches), so a PR review is found by `find_unit`
(CLI `find --unit pr:<n>`), never by branch; `find <branch>` skips PR reviews. Fork
PRs are out of scope: the harness takes none.

Writes stay local (ticket 1300, author 2026-10-28): gaze's answer and the gate's verdict
are written to the local ref, then `sync_background` starts a detached `sync --if-idle`
whose result nobody waits for or reads; `--if-idle` gives up at once when another sync
holds <git-common-dir>/idh-review-sync.lock. Delivery is the landing push.

Landing (ticket 1299). `push_for_landing` (CLI `push-landing <branch>`) runs before a merge:
refresh, then push refs/notes/review and the review-heads of the requests naming the branch
(never the HEADS/* glob), never forced; a failed push is a Refusal, no remote or no request
for the branch pushes nothing. A head missing locally for the latest review of the branch, the
one landing, is a Refusal (ticket 1300); older reviews' missing heads are skipped.

Locking (ticket 1282). Every local write to refs/notes/review (`notes append`, `notes merge`)
is a read-modify-write, so writers hold an exclusive flock on
<git-common-dir>/idh-review-notes.lock, polled up to IDH_NOTES_LOCK_WAIT seconds (default 30);
a writer that cannot get it raises Refusal (non-zero exit). Reentrant within a process. Host-local:
clones on other hosts meet through `sync`, which is already compare-and-swap.

Identity (ticket 1281). `add --request <request_id>` binds an entry to the
request its run was launched on, else to the latest request; an entry whose
`--head` is not that request's head is refused, never bound to another round.

Integrity (spec §6a, 1273 log). Each sync compares the remote with what this
clone last saw (<git-common-dir>/idh-review-seen.json): a remote tip that does
not descend from the last seen one is reported as rewritten, an entry id that
disappeared is reported missing and re-published by the merge, a review-head
that differs from its request's `head` is reported moved. An entry whose content
changed under an unchanged id (sha256 of its line) is a Tamper: the sync stops
before merging anything. `prune` is forbidden: anchors are not objects, so
`git notes prune` would delete every review.

Gate (ticket 1274, spec §5, §8). verify-gate reads a review through `gate`: the
round is the count of `verdict` entries of the review, every session and clone
alike (synced first), plus one; the gate runs only when the latest `answer` is
not ESCALATE and an answer covers the head (`coverage`: equal, or an equal
non-empty verbatim patch-id after a rebase; a delta answer only through its
`coverage.carried` chain to an earlier full one), or the head adds only
bookkeeping to a full or chained reviewed one, or it is the round-2 re-gate
of a REROLL fix descending from the rerolled head;
never past a recorded ESCALATE verdict. `verdict` appends the gate's ruling
with the round it derives itself, only on an admitted head: never a third
round, never a REROLL on round 2; `add` refuses `verdict`.

Readers (ticket 1301). The answers are the review evidence of a PR unit too; its PR comment is
a one-line pointer. `answers --unit pr:<n>` prints every answer's text (attribution's seat
source); `--latest [--json] [--head <sha>]` the newest answer's result, seats and reviewed head
(`current` when --head names that commit), what raid polls. No review exits 1; a stale read
with nothing local refuses, as `find`.

Commands: setup, open, request, add, sync, refresh, publish, push-landing, show, history, find,
answers, findings, coverage, gate, verdict, keep-head, export, import, prune (refused).
Exit: 0 ok, 1 refused or below retrievable, 2 usage or tamper.
"""

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import random
import re
import socket
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

REF = "refs/notes/review"
TRACK = "refs/notes/origin/review"
HEADS = "refs/review-heads"
FETCH_NOTES = f"+{REF}:{TRACK}"  # explicit fetches only, after ls-remote saw the ref
FETCH_NOTES_GLOB = f"+{REF}*:{TRACK}*"  # the persistent spec: a glob tolerates a notes-less remote
FETCH_HEADS = f"{HEADS}/*:{HEADS}/*"
KINDS = ("request", "plan", "report", "answer", "verdict", "link")
REQUIRED = ("ts", "id", "v", "kind", "review_id", "request_id", "author", "publisher",
            "head", "base", "base_ref", "merge_base", "range_patch_id", "links")
CLOSED = ("fixed", "rejected", "wontfix", "withdrawn", "resolved", "invalid")
ATTEMPTS = 5
VERDICTS = ("APPROVED", "REROLL", "ESCALATE", "NEEDS-AUTHOR")
MAX_ROUNDS = 2


class Refusal(Exception):
    """The helper cannot do what was asked; the message says why."""


class Tamper(Refusal):
    """The store contradicts what this clone saw before."""


_LOCK_DEPTH = 0


@contextlib.contextmanager
def _locked(cwd):
    """Exclusive host-local lock on the review store; reentrant so refresh can nest."""
    global _LOCK_DEPTH
    if _LOCK_DEPTH:
        _LOCK_DEPTH += 1
        try:
            yield
        finally:
            _LOCK_DEPTH -= 1
        return
    common = Path(_out(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    path = common / "idh-review-notes.lock"
    wait = float(os.environ.get("IDH_NOTES_LOCK_WAIT", "30"))
    with open(path, "a") as fh:
        deadline = time.monotonic() + wait
        while True:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise Refusal(f"review notes lock {path} still held after {wait:g}s; entry not written") from None
                time.sleep(0.05)
        _LOCK_DEPTH = 1
        try:
            yield
        finally:
            _LOCK_DEPTH = 0
            fcntl.flock(fh, fcntl.LOCK_UN)


def _git(cwd, *args, check=True, stdin=None):
    done = subprocess.run(["git", "-C", str(cwd), *args], input=stdin, capture_output=True, text=True)
    if check and done.returncode:
        raise Refusal(f"git {' '.join(args[:3])} failed: {done.stderr.strip()}")
    return done


def _out(cwd, *args, **kw):
    return _git(cwd, *args, **kw).stdout.strip()


def _rev(cwd, ref):
    done = _git(cwd, "rev-parse", "--verify", "-q", ref + "^{commit}", check=False)
    if done.returncode:
        raise Refusal(f"cannot resolve {ref}")
    return done.stdout.strip()


def _has_ref(cwd, ref):
    return _git(cwd, "rev-parse", "--verify", "-q", ref, check=False).returncode == 0


def _has_remote(cwd, remote):
    return _git(cwd, "remote", "get-url", remote, check=False).returncode == 0


def _now():
    t = datetime.now(timezone.utc)
    return t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{t.microsecond // 1000:03d}Z"


def _compact(ts):
    return re.sub(r"[-:.]", "", ts)


def _hex(n):
    return "".join(random.choice("0123456789abcdef") for _ in range(n))


def _host():
    return re.sub(r"[^A-Za-z0-9]+", "", socket.gethostname()) or "host"


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "x"


def anchor(cwd, review_id):
    """The note's object id: never stored, derived from the review id alone."""
    return _out(cwd, "hash-object", "--stdin", stdin=f"idh-review {review_id}\n")


def _line(entry):
    return json.dumps(entry, ensure_ascii=True, separators=(",", ":"))


def _digest(line):
    return hashlib.sha256(line.encode()).hexdigest()


def parse(text):
    """Entries of one note: one JSON object per non-blank line; a duplicate id with other
    content is a Tamper; malformed lines are skipped."""
    seen, out = {}, []
    for raw in text.split("\n"):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(entry, dict) or "id" not in entry:
            continue
        line = raw.strip()
        if entry["id"] in seen:
            if seen[entry["id"]] != _digest(line):
                raise Tamper(f"entry {entry['id']} appears with two contents")
            continue
        seen[entry["id"]] = _digest(line)
        out.append(entry)
    return sorted(out, key=lambda e: (e.get("ts", ""), e["id"]))


def _note(cwd, review_id, ref=REF):
    done = _git(cwd, "notes", f"--ref={ref}", "show", anchor(cwd, review_id), check=False)
    return done.stdout if done.returncode == 0 else ""


def entries(cwd, review_id, ref=REF):
    return parse(_note(cwd, review_id, ref))


def _all_lines(cwd, ref=REF):
    """{entry id: sha256 of its line} over every note of `ref`."""
    if not _has_ref(cwd, ref):
        return {}, []
    found, every = {}, []
    for pair in _out(cwd, "notes", f"--ref={ref}", "list").splitlines():
        blob = pair.split()[0]
        for raw in _out(cwd, "cat-file", "blob", blob).split("\n"):
            if not raw.strip():
                continue
            try:
                entry = json.loads(raw)
            except ValueError:
                continue
            if isinstance(entry, dict) and "id" in entry:
                d = _digest(raw.strip())
                if found.get(entry["id"], d) != d:
                    raise Tamper(f"entry {entry['id']} appears with two contents in {ref}")
                found[entry["id"]] = d
                every.append(entry)
    return found, every


def all_entries(cwd, ref=REF):
    return sorted(_all_lines(cwd, ref)[1], key=lambda e: (e.get("ts", ""), e["id"]))


# --- configuration and transport -------------------------------------------------

def setup(cwd, remote="origin"):
    """Idempotent per-clone configuration; returns the remote, or None with no remote."""
    if not _has_remote(cwd, remote):
        return None
    fetch = _out(cwd, "config", "--get-all", f"remote.{remote}.fetch", check=False).splitlines()
    if FETCH_NOTES in fetch:  # written by setups before ticket 1300; breaks a plain fetch
        _git(cwd, "config", "--fixed-value", "--unset-all", f"remote.{remote}.fetch", FETCH_NOTES)
    for spec in (FETCH_NOTES_GLOB, FETCH_HEADS):
        if spec not in fetch:
            _git(cwd, "config", "--add", f"remote.{remote}.fetch", spec)
    # Read before write (ticket 1306): git config takes .git/config.lock, and the detached
    # background sync races the foreground reader here; a configured clone writes nothing.
    if _out(cwd, "config", "--get", "notes.review.mergeStrategy", check=False) != "cat_sort_uniq":
        _git(cwd, "config", "notes.review.mergeStrategy", "cat_sort_uniq")
    return remote


def _state_path(cwd):
    return Path(_out(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "idh-review-seen.json"


def _load_state(cwd, remote):
    try:
        return json.loads(_state_path(cwd).read_text()).get(remote, {})
    except (OSError, ValueError):
        return {}


def _save_state(cwd, remote, tip, digests):
    path = _state_path(cwd)
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        data = {}
    data[remote] = {"tip": tip, "entries": digests}
    path.write_text(json.dumps(data, sort_keys=True) + "\n")


def _fetch(cwd, remote):
    """Fetch the remote notes into the tracking ref; returns its tip or None."""
    listed = _out(cwd, "ls-remote", remote, REF)
    if not listed:
        _git(cwd, "update-ref", "-d", TRACK, check=False)
        return None
    _git(cwd, "fetch", "-q", remote, FETCH_NOTES)
    return _rev(cwd, TRACK)


def _check_remote(cwd, remote, tip, warnings):
    """Compare the fetched remote with what this clone last saw (spec §6a)."""
    seen = _load_state(cwd, remote)
    old = seen.get("tip")
    if old and old != tip:
        known = _git(cwd, "cat-file", "-e", f"{old}^{{commit}}", check=False).returncode == 0
        if not tip or not known or _git(cwd, "merge-base", "--is-ancestor", old, tip,
                                        check=False).returncode:
            warnings.append(f"remote {REF} rewritten: {tip or 'deleted'} does not descend from the "
                            f"last seen {old[:12]}; merging, lost entries are re-published")
    digests = _all_lines(cwd, TRACK)[0] if tip else {}
    for eid, d in seen.get("entries", {}).items():
        if eid not in digests:
            warnings.append(f"remote lost entry {eid}: missing, re-published from this clone")
        elif digests[eid] != d:
            raise Tamper(f"remote entry {eid} changed under an unchanged id; refusing to merge")
    local = _all_lines(cwd, REF)[0]
    for eid, d in digests.items():
        if eid in local and local[eid] != d:
            raise Tamper(f"remote entry {eid} differs from the local one; refusing to merge")


def _integrate(cwd):
    """Bring the tracking ref into the local ref: fast-forward or cat_sort_uniq merge.
    The whole decision runs under the lock, so a ref created meanwhile is never overwritten."""
    with _locked(cwd):
        _integrate_locked(cwd)


def _integrate_locked(cwd):
    if not _has_ref(cwd, TRACK):
        return
    track = _rev(cwd, TRACK)
    if not _has_ref(cwd, REF):
        _git(cwd, "update-ref", REF, track)
        return
    local = _rev(cwd, REF)
    if _git(cwd, "merge-base", "--is-ancestor", track, local, check=False).returncode == 0:
        return
    if _git(cwd, "merge-base", "--is-ancestor", local, track, check=False).returncode == 0:
        _git(cwd, "update-ref", REF, track, local)
        return
    _git(cwd, "notes", f"--ref={REF}", "merge", "-q", "-s", "cat_sort_uniq", TRACK)


def _check_heads(cwd, remote, warnings):
    """Fetch review-heads without '+' and check each against its request entry."""
    done = _git(cwd, "fetch", "-q", remote, FETCH_HEADS, check=False)
    if done.returncode:
        for line in done.stderr.splitlines():
            if HEADS in line and ("rejected" in line or "!" in line):
                warnings.append(f"review-head moved on {remote}: {line.strip()}")
    remote_heads = {}
    for line in _out(cwd, "ls-remote", remote, f"{HEADS}/*").splitlines():
        oid, ref = line.split()
        remote_heads[ref] = oid
    requests = {(e["review_id"], e["request_id"]): e["head"]
                for e in all_entries(cwd) if e.get("kind") == "request"}
    for (rid, rq), head in requests.items():
        ref = f"{HEADS}/{rid}/{rq}"
        if ref in remote_heads and remote_heads[ref] != head:
            warnings.append(f"review-head {ref} moved on {remote}: {remote_heads[ref][:12]}, "
                            f"request says {head[:12]}")
        if _has_ref(cwd, ref) and _rev(cwd, ref) != head:
            warnings.append(f"review-head {ref} moved locally: request says {head[:12]}")


def refresh(cwd, remote="origin"):
    """Reader bootstrap (ticket 1281): fetch the remote notes and review-heads, check them,
    and bring them into the local ref; never pushes, so a read-only remote suffices. Local
    unpublished entries survive (merge, never a forced fetch into the live ref). A failed
    fetch is `stale` with a warning, never a refusal and never an empty store (ticket 1300):
    the caller reads the local entries and says they may be behind. A Tamper still raises.
    No remote: nothing to do."""
    if not setup(cwd, remote):
        return {"status": "local", "warnings": []}
    warnings = []
    try:
        tip = _fetch(cwd, remote)
    except Tamper:
        raise
    except Refusal as exc:
        return {"status": "stale", "warnings": [f"remote {remote} unreadable, local entries only: {exc}"]}
    _check_remote(cwd, remote, tip, warnings)
    before = {e["id"]: e for e in all_entries(cwd)}
    _integrate(cwd)
    after = _all_lines(cwd, REF)[0]
    for eid, entry in before.items():
        if eid not in after:
            _write(cwd, entry)
    try:
        _check_heads(cwd, remote, warnings)
    except Tamper:
        raise
    except Refusal as exc:  # the notes were read; only the review-head check went unread
        warnings.append(f"review-heads on {remote} unread: {exc}")
    return {"status": "fetched", "warnings": list(dict.fromkeys(warnings))}


def _push_notes(cwd, remote, warnings):
    """Fetch, check, integrate and push REF, at most ATTEMPTS times, never forced; Refusal after the last."""
    backoff = float(os.environ.get("IDH_REVIEW_BACKOFF", "0.5"))
    for attempt in range(1, ATTEMPTS + 1):
        tip = _fetch(cwd, remote)
        _check_remote(cwd, remote, tip, warnings)
        before = {e["id"]: e for e in all_entries(cwd)}
        _integrate(cwd)
        after = _all_lines(cwd, REF)[0]
        for eid, entry in before.items():
            if eid not in after:  # a fast-forward over a dropping remote: write it again
                _write(cwd, entry)
        pushed = True
        if _has_ref(cwd, REF) and _rev(cwd, REF) != tip:
            pushed = _git(cwd, "push", "-q", remote, f"{REF}:{REF}", check=False).returncode == 0
        if pushed:
            return
        time.sleep(backoff * attempt * random.uniform(0.5, 1.5))
    raise Refusal(f"push of {REF} to {remote} rejected {ATTEMPTS} times")


def sync(cwd, remote="origin"):
    """Fetch, check, merge, push; never forced. Returns {status, warnings}."""
    if not setup(cwd, remote):
        return {"status": "local", "warnings": []}
    warnings = []
    _push_notes(cwd, remote, warnings)
    _check_heads(cwd, remote, warnings)
    _git(cwd, "push", "-q", remote, f"{HEADS}/*:{HEADS}/*", check=False)
    tip = _fetch(cwd, remote)
    _check_remote(cwd, remote, tip, warnings)  # a replacement in the push-to-fetch window
    _save_state(cwd, remote, tip, _all_lines(cwd, TRACK)[0] if tip else {})
    return {"status": "synced", "warnings": list(dict.fromkeys(warnings))}


def _sync_lock_path(cwd):
    return Path(_out(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")) / "idh-review-sync.lock"


def sync_if_idle(cwd, remote="origin"):
    """`sync` unless another sync holds the sync lock: one try, never a wait (ticket 1300).
    The sync lock is not the write lock, so local writers never wait on a network push."""
    with open(_sync_lock_path(cwd), "a") as fh:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return {"status": "skipped: lock busy", "warnings": []}
        try:
            return sync(cwd, remote)
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)


def sync_background(cwd, remote="origin"):
    """Start a detached `sync --if-idle` and return at once: never waited, result ignored
    (ticket 1300). Delivery is the landing push's; this only shortens the wait for readers
    on other clones. No remote: nothing started. Returns whether a sync was started."""
    if not _has_remote(cwd, remote):
        return False
    try:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "-C", str(cwd), "--remote", remote,
                          "sync", "--if-idle"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        return False
    return True


def _retention_problems(cwd, remote, ids):
    """The review-heads the named entries need (their requests' heads), checked on the remote:
    each must exist there and name its request's head (ticket 1281). Never repaired by force."""
    every = all_entries(cwd)
    named = [e for e in every if e["id"] in set(ids)]
    heads = {(e["review_id"], e["request_id"]): e["head"] for e in every if e.get("kind") == "request"}
    remote_heads = dict(reversed(line.split()) for line in
                        _out(cwd, "ls-remote", remote, f"{HEADS}/*").splitlines())
    problems = []
    for key in dict.fromkeys((e["review_id"], e["request_id"]) for e in named):
        ref = f"{HEADS}/{key[0]}/{key[1]}"
        want = heads.get(key)
        if want is None:
            problems.append(f"{ref}: no request entry {key[1]} in review {key[0]}")
        elif ref not in remote_heads:
            problems.append(f"{ref}: missing on {remote} (push rejected or not made); kept locally, "
                            "publish again to retry")
        elif remote_heads[ref] != want:
            problems.append(f"{ref}: moved on {remote} to {remote_heads[ref][:12]}, request says "
                            f"{want[:12]}; not overwritten")
    return problems


def publish(cwd, ids, remote="origin"):
    """Sync, then verify against the remote: done-unpublished | published | retrievable.
    Retrievable also needs the review-heads of the named entries' requests on the remote, each
    naming its request's head; a missing or moved one is reported on stderr and caps the level
    at published (ticket 1281). Nothing local is dropped, so a later publish retries."""
    if sync(cwd, remote)["status"] == "local":
        return "done-unpublished"
    tip = _fetch(cwd, remote)
    remote_tip = (_out(cwd, "ls-remote", remote, REF).split() or [""])[0]
    if not tip or remote_tip != _rev(cwd, REF):
        return "done-unpublished"
    readable = _all_lines(cwd, TRACK)[0]
    if not all(i in readable for i in ids):
        return "published"
    problems = _retention_problems(cwd, remote, ids)
    for problem in problems:
        print(f"review_notes: review-head not retrievable: {problem}", file=sys.stderr)
    return "published" if problems else "retrievable"


def _refuse_split_rounds(cwd, review_id):
    """Verdict writes are local (ticket 1300), so two clones can each rule one round; the
    landing door, after merging the remote's notes, is where they meet. Two verdicts of one
    round, or verdicts past the two-round budget, refuse the landing (gaze on PR #1855)."""
    rounds = {}
    for v in _verdicts(cwd, review_id):
        rounds.setdefault(v.get("round"), []).append(v)
    for rnd, vs in sorted(rounds.items(), key=lambda kv: str(kv[0])):
        if len(vs) > 1:
            raise Refusal(f"review {review_id}: round {rnd} has {len(vs)} verdicts "
                          f"({', '.join(v.get('verdict', '?') for v in vs)}); two gate runs ruled "
                          "one round, refusing to land: ESCALATE")
    over = sum(len(vs) for vs in rounds.values())
    if over > MAX_ROUNDS:
        raise Refusal(f"review {review_id}: {over} verdicts recorded, past the two-round budget; "
                      "refusing to land: ESCALATE")


def push_for_landing(cwd, branch, remote="origin"):
    """Landing door (ticket 1299): push REF and the review-heads of the requests naming `branch`,
    synchronously and never forced, before the merge. A failed push is a Refusal; so is a landing
    review whose verdicts split a round or exceed two rounds (checked after the refresh, before
    any push). No remote, or no request for the branch: nothing pushed, []. Returns the refs
    pushed."""
    def requests():
        return [e for e in all_entries(cwd) if e.get("kind") == "request" and e.get("branch") == branch]
    # Notes are merge evidence (ticket 1300): the landing review's retained heads must exist.

    if not _has_remote(cwd, remote) or not requests():
        return []  # decided from local entries: no config write, no fetch
    setup(cwd, remote)
    refresh(cwd, remote)
    reqs = requests()
    if not reqs:
        return []
    landing = reqs[-1]["review_id"]
    _refuse_split_rounds(cwd, landing)
    _push_notes(cwd, remote, [])
    pushed = [REF]
    for key in dict.fromkeys((e["review_id"], e["request_id"]) for e in reqs):
        ref = f"{HEADS}/{key[0]}/{key[1]}"
        if not _has_ref(cwd, ref):
            if key[0] == landing:
                raise Refusal(f"review-head {ref} of the landing review is missing locally; "
                              "the reviewed head is merge evidence, refusing to land without it")
            continue
        if _git(cwd, "push", "-q", remote, f"{ref}:{ref}", check=False).returncode != 0:
            raise Refusal(f"push of {ref} to {remote} rejected")
        pushed.append(ref)
    return pushed


# --- writing ---------------------------------------------------------------------

def _binding(cwd, head, base_ref):
    """head, base, base_ref, merge_base, range_patch_id of one examined range."""
    head = _rev(cwd, head)
    base = _rev(cwd, base_ref)
    mb = _out(cwd, "merge-base", base, head)
    diff = _git(cwd, "diff", f"{mb}..{head}").stdout
    pid = _out(cwd, "patch-id", "--verbatim", stdin=diff).split()[:1] if diff else []
    return {"head": head, "base": base, "base_ref": base_ref, "merge_base": mb,
            "range_patch_id": pid[0] if pid else ""}


def _publisher(cwd, skill):
    return {"skill": skill, "host": socket.gethostname(),
            "git_user": _out(cwd, "config", "user.name", check=False)}


def _write(cwd, entry):
    line = _line(entry)
    if any(c in line for c in "\n\r"):
        raise Refusal("an entry must be one line")
    with _locked(cwd):
        _git(cwd, "notes", f"--ref={REF}", "append", "-m", line, anchor(cwd, entry["review_id"]))
    return entry


def _entry(cwd, kind, review_id, request_id, binding, author, skill, links, extra):
    if kind not in KINDS:
        raise Refusal(f"unknown kind {kind!r} ({'|'.join(KINDS)})")
    ts = _now()
    entry = {"ts": ts, "id": f"{_compact(ts)}-{_host()}-{_hex(8)}", "v": 1, "kind": kind,
             "review_id": review_id, "request_id": request_id,
             "author": author or {"role": skill}, "publisher": _publisher(cwd, skill),
             **binding, "links": list(links or [])}
    for key, value in extra.items():
        if key in REQUIRED:
            raise Refusal(f"field {key!r} is set by the helper")
        entry[key] = value
    return entry


def keep_head(cwd, review_id, request_id, head):
    """refs/review-heads/<review_id>/<request_id> -> head; created once, never moved."""
    ref = f"{HEADS}/{review_id}/{request_id}"
    if _has_ref(cwd, ref):
        if _rev(cwd, ref) != head:
            raise Refusal(f"{ref} already names another commit")
        return ref
    _git(cwd, "update-ref", ref, head, "0" * 40)
    return ref


def _request_what(cwd, base, branch, remote):
    for url in ([_out(cwd, "remote", "get-url", remote)] if _has_remote(cwd, remote) else []) + \
            [_out(cwd, "rev-parse", "--show-toplevel")]:
        done = _git(cwd, "request-pull", base, url, branch, check=False)
        if done.returncode == 0:
            return done.stdout
    return ""


def request(cwd, review_id, branch, base_ref="origin/main", why="", intent="", tickets=(),
            responses=(), author=None, skill="hunt", remote="origin", head=None, unit=None):
    """A new request (round) on the branch's current head, or on `head` when the caller already
    pinned the commit under review (gaze setup, ticket 1281); keeps the head. `unit` (`pr:<n>`,
    ticket 1300) is stored on the request; a later request of the review inherits it."""
    binding = _binding(cwd, head or branch, base_ref)
    prior = [e for e in entries(cwd, review_id) if e["kind"] == "request"]
    extra = {"branch": branch, "what": _request_what(cwd, binding["base"], branch, remote),
             "why": why, "intent": intent, "tickets": list(tickets), "responses": list(responses)}
    unit = unit or next((e["unit"] for e in reversed(prior) if e.get("unit")), None)
    if unit:
        extra["unit"] = unit
    links = []
    if prior:
        prev = prior[-1]
        links.append(prev["id"])
        links += [e["id"] for e in entries(cwd, review_id)
                  if e["kind"] == "answer" and e["request_id"] == prev["request_id"]]
        if _git(cwd, "cat-file", "-e", prev["head"], check=False).returncode == 0:
            extra["delta"] = _git(cwd, "range-diff", "--no-color", f"{prev['merge_base']}..{prev['head']}",
                                  f"{binding['merge_base']}..{binding['head']}", check=False).stdout
    ts = _now()
    rq = f"rq-{_compact(ts)}-{_hex(4)}"
    entry = _entry(cwd, "request", review_id, rq, binding, author, skill, links, extra)
    keep_head(cwd, review_id, rq, binding["head"])
    return _write(cwd, entry)


def open_review(cwd, branch, base_ref="origin/main", unit=None, **kw):
    """Mint a review id and write its first request; returns the review id."""
    rid = f"rv-{datetime.now(timezone.utc):%Y%m%d}-{_slug(unit or branch)}-{_hex(4)}"
    request(cwd, rid, branch, base_ref, unit=unit, **kw)
    return rid


def add(cwd, kind, review_id, fields, head=None, author=None, skill="gaze", links=(),
        request_id=None):
    """Append a plan, report, answer or link to the request `request_id`, the one the run was
    launched on (frozen at gaze setup, ticket 1281), else to the latest request. Either way the
    request's head must be `head` when given: a result on another head is refused rather than
    bound to a request it did not review (and whose retained head is not the one examined)."""
    if kind == "request":
        raise Refusal("a request is written by `request`, which keeps its head")
    if kind == "verdict":
        raise Refusal("a verdict is written by `verdict`, which derives its round")
    return _append(cwd, kind, review_id, fields, head, author, skill, links, request_id)


def _append(cwd, kind, review_id, fields, head=None, author=None, skill="gaze", links=(),
            request_id=None):
    reqs = [e for e in entries(cwd, review_id) if e["kind"] == "request"]
    if not reqs:
        raise Refusal(f"review {review_id} has no request")
    if request_id is None:
        req = reqs[-1]
    else:
        named = [e for e in reqs if e["request_id"] == request_id]
        if not named:
            raise Refusal(f"review {review_id} has no request {request_id}")
        req = named[0]
    # One read of the requests, one check: a verdict rules the review's latest submission on the
    # gate's head (rebased or bookkeeping), every other entry binds to the request it examined.
    # A ref is resolved once: the commit checked is the commit bound.
    oid = _rev(cwd, head) if head is not None else req["head"]
    if kind != "verdict" and oid != req["head"]:
        raise Refusal(f"head {oid[:12]} is not the head of request {req['request_id']} "
                      f"({req['head'][:12]}): an entry binds only to the request it reviewed; "
                      "name that request (--request), or request the head first")
    binding = _binding(cwd, oid, req["base_ref"])
    return _write(cwd, _entry(cwd, kind, review_id, req["request_id"], binding, author, skill,
                              links, dict(fields)))


# --- reading ---------------------------------------------------------------------

def find(cwd, branch):
    """The review id of the latest request naming `branch` in the local ref, else None. A PR
    review (`unit: pr:<n>`) is never a branch unit's, so it is skipped (ticket 1300)."""
    hits = [e for e in all_entries(cwd) if e.get("kind") == "request" and e.get("branch") == branch
            and not str(e.get("unit") or "").startswith("pr:")]
    return hits[-1]["review_id"] if hits else None


def find_unit(cwd, unit):
    """The review id of the latest request carrying `unit` (`pr:<n>`), local ref only; matches
    the unit, never the branch, so a reused branch name never inherits old rounds (ticket 1300).
    Fork PRs are out of scope: the harness takes none."""
    hits = [e for e in all_entries(cwd) if e.get("kind") == "request" and e.get("unit") == unit]
    return hits[-1]["review_id"] if hits else None


def _resolved(cwd, remote, finder, key):
    """Refresh, then look up: a stale read answers from local entries (warning on stderr) and,
    with nothing local, refuses naming the remote; never None for an unread store (1281, 1300)."""
    report = refresh(cwd, remote)
    rid = finder(cwd, key)
    if report["status"] == "stale":
        if not rid:
            raise Refusal(f"remote unreadable, no local review: {'; '.join(report['warnings'])}")
        for w in report["warnings"]:
            print(f"review_notes: warning: stale read: {w}", file=sys.stderr)
    return rid


def resolve(cwd, branch, remote="origin"):
    """`find` after `refresh`: the resolver every reader uses, so a fresh clone sees the reviews
    already published (ticket 1281)."""
    return _resolved(cwd, remote, find, branch)


def resolve_unit(cwd, unit, remote="origin"):
    """`find_unit` after `refresh` (ticket 1300), with resolve's stale rules."""
    return _resolved(cwd, remote, find_unit, unit)


def answer_texts(cwd, review_id):
    """The text of every `answer` entry of the review, oldest first (ticket 1301): the gaze
    results that attribution's `--seats-pr` reads its `seat:` lines from, instead of PR comments."""
    return [e.get("text") or "" for e in entries(cwd, review_id) if e["kind"] == "answer"]


def latest_answer(cwd, review_id):
    """The newest `answer` of the review as a poller reads it (ticket 1301): result, seats, the
    head it reviewed and its entry id; None when the review has no answer yet."""
    answers = [e for e in entries(cwd, review_id) if e["kind"] == "answer"]
    if not answers:
        return None
    e = answers[-1]
    return {"review_id": review_id, "answer": e["id"], "result": e.get("result"),
            "seats": e.get("seats"), "reviewed_head_sha": e["head"], "ts": e.get("ts")}


def open_findings(cwd, review_id):
    """Findings whose latest disposition (by (ts, id)) is not a closing one."""
    found, state = {}, {}
    for e in entries(cwd, review_id):
        for f in e.get("findings", []) if e["kind"] == "report" else []:
            found.setdefault(f["finding_id"], f)
        for r in e.get("responses", []) if e["kind"] == "request" else []:
            state[r["finding_id"]] = r.get("disposition", "")
    return [f for fid, f in found.items() if state.get(fid, "") not in CLOSED]


def coverage(cwd, review_id, head):
    """Does `head` carry the review? match: equal | patch-id | delta | none, with the answer."""
    head = _rev(cwd, head)
    answers = [e for e in entries(cwd, review_id) if e["kind"] == "answer"]
    if not answers:
        return {"match": "none", "head": head}
    binding = _binding(cwd, head, answers[-1]["base_ref"])
    best = None
    for e in reversed(answers):
        scope = (e.get("coverage") or {}).get("scope", "full")
        if e["head"] == head:
            match = "equal" if scope == "full" else "delta"
        elif e["range_patch_id"] and e["range_patch_id"] == binding["range_patch_id"]:
            match = "patch-id" if scope == "full" else "delta"
        else:
            continue
        if match != "delta":
            return {"match": match, "head": head, "answer": e["id"], "result": e.get("result")}
        best = best or {"match": "delta", "head": head, "answer": e["id"], "result": e.get("result")}
    return best or {"match": "none", "head": head}


def _verdicts(cwd, review_id):
    return [e for e in entries(cwd, review_id) if e["kind"] == "verdict"]


def _key(e):
    return (e.get("ts", ""), e["id"])


def carry_target(cwd, review_id):
    """The answer a new delta answer carries (spec §4): the latest non-ESCALATE answer of the
    review, full or itself a delta, else None. gaze_close records it as `coverage.carried`."""
    prior = [e for e in entries(cwd, review_id)
             if e["kind"] == "answer" and e.get("result") != "ESCALATE"]
    return prior[-1]["id"] if prior else None


def _chained(answers, delta):
    """A delta answer counts only through `coverage.carried`: each link names an earlier,
    non-ESCALATE answer of the review, ending at a full one (spec §4)."""
    by_id = {e["id"]: e for e in answers}
    cur = delta
    while True:
        target = by_id.get((cur.get("coverage") or {}).get("carried") or "")
        if not target or _key(target) >= _key(cur) or target.get("result") == "ESCALATE":
            return False
        if (target.get("coverage") or {}).get("scope", "full") == "full":
            return True
        cur = target


def _full_or_chained(answers, e):
    return (e.get("coverage") or {}).get("scope", "full") == "full" or _chained(answers, e)


def _bookkeeping_since(cwd, base_ref, head, since):
    """merge-gate.py tier --since: 0 when what `head` adds to `since` is bookkeeping or nothing."""
    gate = Path(__file__).resolve().with_name("merge-gate.py")
    done = subprocess.run([sys.executable, str(gate), "tier", "--base", base_ref, "--head", head,
                           "--since", since], cwd=str(cwd), capture_output=True, text=True)
    return done.returncode == 0


def gate_state(cwd, review_id, head, remote="origin"):
    """What verify-gate needs before ruling `head` (spec §5, §8): the round it would rule,
    whether a completed review admits it, and why not. Refreshes first when there is a remote
    (fetch and merge, never a push), so verdicts and answers written by other clones count
    and a read-only gate host can rule.

    Admitted: an answer covers the head (equal head, or equal non-empty verbatim patch-id;
    a delta only through its `carried` chain to an earlier full answer); or the head adds
    only bookkeeping to the latest reviewed head, whose answer is full or chained; or it is
    the round-2 re-gate of the fix for a round-1 REROLL, descending from the rerolled head.
    Refused: no answer, an ESCALATE answer (the latest, or the one
    covering the head), a recorded ESCALATE verdict, more than two rounds.
    `stale` is empty after a good read; after a failed fetch it names the failure: the state
    rests on local entries and the round may be undercounted (ticket 1300)."""
    report = refresh(cwd, remote)
    head = _rev(cwd, head)
    verdicts = _verdicts(cwd, review_id)
    answers = [e for e in entries(cwd, review_id) if e["kind"] == "answer"]
    state = {"review_id": review_id, "head": head, "round": len(verdicts) + 1, "ready": False,
             "stale": "; ".join(report["warnings"]) if report["status"] == "stale" else "",
             "reason": "", "match": "none", "answer": None, "result": None,
             "reviewed_head": answers[-1]["head"] if answers else None,
             "verdicts": [{"round": v.get("round"), "verdict": v.get("verdict"),
                           "session": v.get("gate_session_id"), "head": v["head"], "id": v["id"]}
                          for v in verdicts]}
    cov = coverage(cwd, review_id, head) if answers else {"match": "none"}
    state.update({k: cov[k] for k in ("match", "answer", "result") if k in cov})
    escalated = [v["id"] for v in verdicts if v.get("verdict") == "ESCALATE"]
    if state["round"] > MAX_ROUNDS:
        state["reason"] = f"{len(verdicts)} verdicts recorded: two rounds max, ESCALATE to the author"
    elif escalated:
        state["reason"] = f"verdict {escalated[0]} is ESCALATE: past an ESCALATE the merge decision is the author's"
    elif not answers:
        state["reason"] = "no completed review: no gaze answer in the review"
    elif answers[-1].get("result") == "ESCALATE":
        state["reason"] = f"no completed review: the latest gaze answer {answers[-1]['id']} is ESCALATE"
    elif state["result"] == "ESCALATE":
        state["reason"] = f"no completed review: the answer {state['answer']} covering the head is ESCALATE"
    elif cov["match"] == "delta" and not _full_or_chained(answers, next(e for e in answers if e["id"] == cov["answer"])):
        state["reason"] = ("no full review: the delta answer covering the head does not carry an "
                           "earlier full answer (coverage.carried)")
    elif cov["match"] != "none":
        state["ready"] = True
    elif (verdicts and verdicts[-1].get("verdict") == "REROLL" and state["round"] == MAX_ROUNDS
          and _git(cwd, "merge-base", "--is-ancestor", verdicts[-1]["head"], head, check=False).returncode == 0):
        state.update(ready=True, match="reroll-fix", answer=None, result=None)
    elif not _full_or_chained(answers, answers[-1]):
        state["reason"] = (f"no full review: the latest answer {answers[-1]['id']} is a delta that does "
                           "not carry an earlier full answer (coverage.carried)")
    elif _bookkeeping_since(cwd, answers[-1]["base_ref"], head, state["reviewed_head"]):
        state.update(ready=True, match="bookkeeping", answer=answers[-1]["id"],
                     result=answers[-1].get("result"))
    else:
        state["reason"] = (f"stale: no gaze answer covers {head[:12]}, and it adds more than "
                           f"bookkeeping to the latest reviewed {state['reviewed_head'][:12]}")
    return state


def record_verdict(cwd, review_id, session, verdict, head, evidence=(), gate_candidate="", text="",
                   author=None, remote="origin"):
    """Append the gate's `verdict` entry; the round is derived here from the review's recorded
    verdicts (all sessions), never passed, and only when `gate_state` admits the head.
    The write is local; a remote gets a background sync, never waited (ticket 1300). Returns
    {entry, level, remote, conflict, stale}: level is `local`; `conflict` lists other verdicts of
    the same round already in the local ref (two gate runs ruling at once; once both meet, the
    next `gate` refuses, past the cap); `stale` is gate_state's."""
    if verdict not in VERDICTS:
        raise Refusal(f"verdict must be one of {'|'.join(VERDICTS)}, got {verdict!r}")
    try:
        session = str(uuid.UUID(session))
    except (TypeError, ValueError):
        raise Refusal(f"gate session id must be a UUID, got {session!r}") from None
    state = gate_state(cwd, review_id, head, remote)  # refreshes first, never pushes
    if not state["ready"]:
        raise Refusal(f"the gate may not rule {state['head'][:12]}: {state['reason']}")
    rnd = state["round"]
    if rnd == MAX_ROUNDS and verdict == "REROLL":
        raise Refusal("round 2 cannot REROLL (never a third round): rule ESCALATE")
    has_remote = _has_remote(cwd, remote)
    entry = _append(cwd, "verdict", review_id,
                    {"gate_session_id": session, "round": rnd, "verdict": verdict,
                     "evidence": list(evidence), "gate_candidate": gate_candidate, "text": text},
                    head=state["head"], author=author or {"role": "verify-gate"}, skill="verify-gate")
    sync_background(cwd, remote)
    conflict = [v["id"] for v in _verdicts(cwd, review_id)
                if v.get("round") == rnd and v["id"] != entry["id"]]
    return {"entry": entry, "level": "local", "remote": has_remote, "conflict": conflict,
            "stale": state["stale"]}


def export(cwd, review_id):
    return "".join(_line(e) + "\n" for e in entries(cwd, review_id))


def import_file(cwd, path):
    """Append the entries of a JSONL export that this clone lacks; returns how many."""
    have = _all_lines(cwd, REF)[0]
    added = 0
    for entry in parse(Path(path).read_text()):
        missing = [k for k in REQUIRED if k not in entry]
        if missing or entry.get("kind") not in KINDS:
            raise Refusal(f"entry {entry.get('id')} malformed: lacks {', '.join(missing) or 'kind'}")
        line = _line(entry)
        if entry["id"] in have:
            if have[entry["id"]] != _digest(line):
                raise Tamper(f"imported entry {entry['id']} differs from the local one")
            continue
        _write(cwd, entry)
        have[entry["id"]] = _digest(line)
        added += 1
    return added


# --- command line ----------------------------------------------------------------

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("-C", dest="repo", default=".")
    p.add_argument("--remote", default="origin")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup")
    for name in ("open", "request"):
        s = sub.add_parser(name)
        if name == "request":
            s.add_argument("--review", required=True)
        s.add_argument("--branch", required=True)
        s.add_argument("--base-ref", default="origin/main")
        s.add_argument("--why", default="")
        s.add_argument("--intent", default="")
        s.add_argument("--tickets", nargs="*", default=[])
        s.add_argument("--responses", default="[]", help="JSON list of {finding_id, disposition}")
        s.add_argument("--skill", default="hunt")
    s = sub.add_parser("add")
    s.add_argument("kind", choices=[k for k in KINDS if k not in ("request", "verdict")])
    s.add_argument("--review", required=True)
    s.add_argument("--json", required=True, help="kind-specific fields, a JSON object")
    s.add_argument("--head")
    s.add_argument("--author", help="JSON object: role, runtime, observed model/family")
    s.add_argument("--links", nargs="*", default=[])
    s.add_argument("--skill", default="gaze")
    s.add_argument("--request", help="the request id the run was launched on (gaze setup's request_id)")
    sub.add_parser("sync").add_argument("--if-idle", action="store_true",
                                        help="give up at once when another sync runs (background use)")
    sub.add_parser("refresh")
    sub.add_parser("publish").add_argument("ids", nargs="*")
    sub.add_parser("push-landing").add_argument("branch")
    sub.add_parser("show").add_argument("review")
    sub.add_parser("history").add_argument("review", nargs="?")
    s = sub.add_parser("find")
    s.add_argument("branch", nargs="?")
    s.add_argument("--unit", help="pr:<n>: a forge merge request's review, never matched by branch")
    sub.add_parser("findings").add_argument("review")
    s = sub.add_parser("answers", help="a PR review's gaze answers (resolved after refresh)")
    s.add_argument("--unit", required=True, help="pr:<n>")
    s.add_argument("--latest", action="store_true", help="only the newest answer's result, seats and head")
    s.add_argument("--json", action="store_true", help="with --latest: one JSON object")
    s.add_argument("--head", help="with --latest: report whether the answer reviewed this commit (current)")
    s = sub.add_parser("coverage")
    s.add_argument("review")
    s.add_argument("head")
    s = sub.add_parser("gate")
    s.add_argument("review")
    s.add_argument("head")
    s = sub.add_parser("verdict")
    s.add_argument("--review", required=True)
    s.add_argument("--session", required=True, help="the gate session UUID (session=)")
    s.add_argument("--verdict", required=True, choices=VERDICTS)
    s.add_argument("--head", required=True, help="the ruled tip")
    s.add_argument("--evidence", nargs="*", default=[], help="entry ids the ruling rests on")
    s.add_argument("--candidate", default="", help="the gate record's candidate OID")
    s.add_argument("--text-file", type=Path, help="the human-readable verdict summary")
    s = sub.add_parser("keep-head")
    s.add_argument("review")
    s.add_argument("request")
    s.add_argument("head")
    sub.add_parser("export").add_argument("review")
    sub.add_parser("import").add_argument("file")
    sub.add_parser("prune")
    a = p.parse_args(argv)
    cwd, remote = a.repo, a.remote
    try:
        if a.cmd == "prune":
            print("review_notes: prune is forbidden: anchors are not objects, so git notes prune "
                  "would delete every review", file=sys.stderr)
            return 2
        if a.cmd == "setup":
            print(setup(cwd, remote) or "local")
        elif a.cmd in ("open", "request"):
            kw = dict(why=a.why, intent=a.intent, tickets=a.tickets, skill=a.skill, remote=remote)
            if a.cmd == "open":
                print(open_review(cwd, a.branch, a.base_ref, **kw))
            else:
                print(request(cwd, a.review, a.branch, a.base_ref, responses=json.loads(a.responses),
                              **kw)["id"])
        elif a.cmd == "add":
            print(add(cwd, a.kind, a.review, json.loads(a.json), head=a.head,
                      author=json.loads(a.author) if a.author else None, skill=a.skill,
                      links=a.links, request_id=a.request)["id"])
        elif a.cmd in ("sync", "refresh"):
            report = (refresh if a.cmd == "refresh" else sync_if_idle if a.if_idle else sync)(cwd, remote)
            print(report["status"])
            for w in report["warnings"]:
                print(f"warning: {w}", file=sys.stderr)
        elif a.cmd == "publish":
            level = publish(cwd, a.ids, remote)
            print(level)
            return 0 if level == "retrievable" else 1
        elif a.cmd == "push-landing":
            for ref in push_for_landing(cwd, a.branch, remote):
                print(ref)
        elif a.cmd == "show":
            sys.stdout.write(export(cwd, a.review))
        elif a.cmd == "history":
            for e in entries(cwd, a.review) if a.review else all_entries(cwd):
                print(e["ts"], e["review_id"], e["kind"], e["id"], e.get("result") or e.get("verdict") or "")
        elif a.cmd == "find":
            if bool(a.branch) == bool(a.unit):
                print("review_notes: find takes a branch or --unit, exactly one", file=sys.stderr)
                return 2
            rid = resolve_unit(cwd, a.unit, remote) if a.unit else resolve(cwd, a.branch, remote)
            if not rid:
                return 1
            print(rid)
        elif a.cmd == "answers":
            rid = resolve_unit(cwd, a.unit, remote)
            if not rid:
                print(f"review_notes: no review for {a.unit}", file=sys.stderr)
                return 1
            if not a.latest:
                for text in answer_texts(cwd, rid):
                    print(text.rstrip("\n"))
                    print()
                return 0
            latest = latest_answer(cwd, rid)
            if not latest:
                print(f"review_notes: no answer yet in review {rid} ({a.unit})", file=sys.stderr)
                return 1
            if a.head:
                latest["current"] = latest["reviewed_head_sha"] == _rev(cwd, a.head)
            print(json.dumps(latest) if a.json else
                  " ".join(f"{k}={v}" for k, v in latest.items()))
        elif a.cmd == "findings":
            for f in open_findings(cwd, a.review):
                print(json.dumps(f))
        elif a.cmd == "coverage":
            print(json.dumps(coverage(cwd, a.review, a.head)))
        elif a.cmd == "gate":
            state = gate_state(cwd, a.review, a.head, remote)
            print(json.dumps(state))
            return 0 if state["ready"] else 1
        elif a.cmd == "verdict":
            done = record_verdict(cwd, a.review, a.session, a.verdict, a.head, a.evidence, a.candidate,
                                  a.text_file.read_text() if a.text_file else "", remote=remote)
            print(done["entry"]["id"], done["level"], f"round={done['entry']['round']}")
            if done["stale"]:
                print(f"review_notes: notes: stale ({done['stale']}); the round may be undercounted",
                      file=sys.stderr)
            if done["conflict"]:
                print(f"review_notes: round {done['entry']['round']} also recorded by "
                      f"{', '.join(done['conflict'])}: two gate runs ruled at once; ESCALATE to the author",
                      file=sys.stderr)
                return 1
            return 0
        elif a.cmd == "keep-head":
            print(keep_head(cwd, a.review, a.request, _rev(cwd, a.head)))
        elif a.cmd == "export":
            sys.stdout.write(export(cwd, a.review))
        elif a.cmd == "import":
            print(import_file(cwd, a.file))
    except Tamper as exc:
        print(f"review_notes: TAMPER: {exc}", file=sys.stderr)
        return 2
    except Refusal as exc:
        print(f"review_notes: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

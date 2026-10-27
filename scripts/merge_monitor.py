#!/usr/bin/env python3
"""Verify main after fast-path merges: the full check set on the new tip, one run at a time.

Ticket 1226; the policy is skills/merge/SKILL.md § Gating tiers, the record
format and the fast-path rule are scripts/merge-gate.py's. A bookkeeping merge
on an open fast path ran only the fast checks; this monitor runs every check
the tip declares in a throwaway worktree of the tip and appends a verdict to
refs/notes/gate-verdict on it, which reopens or closes the fast path.

`spawn --ref origin/main` is the merge recipe's last step: it writes the tip
into the one pending slot (latest wins) and starts a detached `work` process,
then returns. `work` takes a lock; a second worker meets the lock and leaves,
so one run is in flight and one tip pending, never one run per merge. Each run
covers every merge since the last verified tip. `verify --tip <ref>` runs one
tip in the foreground.

A red check whose output names failing tests (pytest's `FAILED <id>` and
`ERROR <id>` summary lines) re-runs only those tests once with the check's
declared `"rerun"` argv; the ones that pass are recorded as `flaky:` and do
not make the verdict red. A failure that reproduces, or one that names no
test, is red, and the monitor then re-runs only the failing tests (or the
failing check) on each merge since the last green tip to name the likely
culprit. The failing ids of the first run are kept in the verdict
(`failed-first-run:`) and appended to `failed-ids.log` in the state directory.

Fail closed: a run that times out, crashes or cannot push writes no verdict,
and no verdict is unverified (merge-gate.py closes the fast path after K merges
or the age bound). Exit codes of `verify`: 0 green, 1 red, 2 no verdict.
"""

import argparse
import datetime
import fcntl
import importlib.util
import logging
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

LOG = logging.getLogger("merge-monitor")
FAILED = re.compile(r"^(?:FAILED|ERROR) (\S+)", re.M)
MAX_CULPRIT = 20  # merges searched below the tip for the last green one
MAX_IDS = 50
TESTS_FAILED = 1  # pytest's exit code for failing tests; 4 and 5 mean the ids do not exist there
GREEN, RED, NONE = 0, 1, 2


def _merge_gate():
    spec = importlib.util.spec_from_file_location("merge_gate", Path(__file__).with_name("merge-gate.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mg = _merge_gate()


class Timeout(RuntimeError):
    """The run passed its deadline: no verdict."""


def state_dir(arg):
    if arg:
        return Path(arg)
    common = mg.git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    return Path(common) / "merge-gate-monitor"


def execute(argv, cwd, deadline):
    """(exit code, combined output, seconds); kills the whole process group at the deadline."""
    start = time.monotonic()
    try:
        proc = subprocess.Popen(
            argv, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, start_new_session=True,
        )
    except OSError as exc:
        return 127, f"cannot run: {exc}", 0.0
    try:
        out, _ = proc.communicate(timeout=max(1.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise Timeout(f"{' '.join(argv)} passed the deadline") from None
    return proc.returncode, out, time.monotonic() - start


MAKE_RECIPE_FAILED = 2  # make's exit when a recipe fails, whatever the recipe's own code
SUMMARY = re.compile(r"^=+ (.+?) in [\d.]+s(?: \(.*\))? =+$", re.MULTILINE)


def ordinary_failures(code, out):
    """The first run completed and only tests failed, so its failing ids may be re-run.

    pytest says so with exit 1. Behind make (pytest-guard is `make check-tests`) every
    failing recipe is exit 2, so there the run's own summary decides: failures only, no
    error, no interruption, no internal error. A run that stopped early never ran the
    rest of the suite, and its listed ids passing alone prove nothing (gaze rounds 11-12).
    """
    if code == TESTS_FAILED:
        return True
    if code != MAKE_RECIPE_FAILED or "INTERNALERROR" in out or re.search(r"^!+ .*Interrupted", out, re.MULTILINE):
        return False
    found = SUMMARY.findall(out)
    kinds = {part.split()[-1] for part in found[-1].split(",") if part.split()} if found else set()
    return "failed" in kinds and not kinds & {"error", "errors"}


def failed_ids(out):
    """Failing test ids named in pytest's summary, in order, once each; an id with a control character is dropped."""
    return [i for i in dict.fromkeys(FAILED.findall(out)) if mg.single_line(i)]


def ids_line(ids):
    shown = " ".join(ids[:MAX_IDS])
    return shown + (f" (+{len(ids) - MAX_IDS} more)" if len(ids) > MAX_IDS else "")


def recheck(name, ids, check, fast, tree, deadline):
    """Exit code of re-running only `ids` of check `name` (or the whole check without ids)."""
    rerun = fast.get("rerun", {}).get(name)
    if ids and rerun:
        code, _out, _secs = execute([*rerun, *ids], tree, deadline)
        return code == TESTS_FAILED
    code, _out, _secs = execute(check["argv"], tree, deadline)
    return code != 0


def culprit(tip, hard, config, tree, deadline):
    """The first merge since the last green tip at which the hard failures reproduce; the tip by default."""
    walked = mg.git("rev-list", "--first-parent", f"--max-count={MAX_CULPRIT}", tip).stdout.split()
    since, found_green = [], False
    for commit in walked[1:]:
        found = mg.verdict_on(commit)
        if found and found[0] == "pass":
            found_green = True
            break
        since.append(commit)
    fast = config.get(mg.FASTPATH, {})
    checks = {c["name"]: c for c in config["checks"]}
    for commit in reversed(since):
        mg.git("-C", str(tree), "checkout", "-q", "--detach", commit)
        if any(recheck(name, ids, checks[name], fast, tree, deadline) for name, ids in hard):
            return commit, found_green
    return tip, found_green


def verify_tip(tip, remote, directory):
    """Run every declared check on `tip` and append the verdict. GREEN, RED or NONE."""
    if remote:
        mg.fetch_notes(remote, mg.NOTES_REF, mg.VERDICT_REF)
    found = mg.verdict_on(tip)
    if found:
        LOG.info("%s already verified (%s): %s", tip[:12], found[2], found[0])
        return GREEN if found[0] == "pass" else RED
    config = mg.load_config(tip)
    if config is None:
        LOG.info("%s declares no gate; nothing to verify", tip[:12])
        return NONE
    fast = config.get(mg.FASTPATH, {})
    deadline = time.monotonic() + fast.get("monitor_timeout_minutes", 30) * 60
    started = datetime.datetime.now(datetime.timezone.utc).strftime(mg.TIME_FORMAT)
    clock = time.monotonic()
    results, failed = [], []
    with tempfile.TemporaryDirectory(prefix="merge-monitor-") as tmp:
        tree = Path(tmp) / "tip"
        mg.git("worktree", "add", "-q", "--detach", str(tree), tip)
        try:
            for item in config["checks"]:
                code, out, secs = execute(item["argv"], tree, deadline)
                (directory / f"last-{item['name']}.log").write_text(out)
                verdict = "pass" if code == 0 else f"fail(exit {code})"
                results.append(f"{item['name']} {verdict} {secs:.1f}s :: {' '.join(item['argv'])}")
                if code:
                    failed.append((item, ordinary_failures(code, out), failed_ids(out)))
            first_ids = [i for _item, _ordinary, ids in failed for i in ids]
            if first_ids:
                with open(directory / "failed-ids.log", "a") as log:
                    log.write(f"{started} {tip} {' '.join(first_ids)}\n")
                LOG.info("first run failing ids: %s", " ".join(first_ids))
            flaky, hard = [], []
            for item, ordinary, ids in failed:
                rerun = fast.get("rerun", {}).get(item["name"])
                if ids and rerun and ordinary:  # a run that stopped early is a hard failure
                    code, out, _secs = execute([*rerun, *ids], tree, deadline)
                    still = [] if code == 0 else [i for i in ids if i in set(failed_ids(out))] or ids
                    flaky += [i for i in ids if i not in still]
                    if still:
                        hard.append((item["name"], still))
                else:
                    hard.append((item["name"], ids))
            blamed = None
            if hard:
                try:
                    blamed = culprit(tip, hard, config, tree, deadline)
                except (Timeout, mg.GateError, OSError) as exc:  # the red result stands; only the blame is unknown
                    LOG.error("%s: %s; red verdict without a culprit", tip[:12], exc)
                    blamed = (None, False)
        except Timeout as exc:
            LOG.error("%s: %s; no verdict (unverified)", tip[:12], exc)
            return NONE
        finally:
            mg.git("worktree", "remove", "--force", str(tree), check=False)  # never raises: a timeout answers 124
    fields = {
        "result": "fail" if hard else "pass",
        "time": started,
        "host": socket.gethostname(),
        "revision": f"tip={tip}",
        "scope": mg.scope_line(config),
        "failed-first-run": ids_line(first_ids) if first_ids else "",
        "flaky": f"{len(flaky)} {ids_line(flaky)}" if flaky else "",
        "checks": results,
    }
    if blamed and blamed[0] is None:
        fields["culprit"] = "unknown (the search passed the deadline)"
    elif blamed:
        commit, bounded = blamed
        subject = mg.sanitize(mg.git("log", "-1", "--format=%s", commit, check=False).stdout)
        where = "since the last green tip" if bounded else f"no green tip in the last {MAX_CULPRIT} merges"
        fields["culprit"] = f"{commit} {subject} ({where})"
    mg.append_and_push(tip, mg.format_verdict(fields), remote, mg.VERDICT_REF)
    LOG.info("verdict %s on %s in %.1fs%s", fields["result"], tip[:12], time.monotonic() - clock,
             f"; culprit {fields['culprit']}" if "culprit" in fields else "")
    if flaky:
        LOG.info("flaky: %s", fields["flaky"])
    return RED if hard else GREEN


def take_pending(directory):
    """The pending tip, removed from its slot atomically; None when the slot is empty."""
    slot, taken = directory / "pending", directory / "pending.taken"
    try:
        os.replace(slot, taken)
    except FileNotFoundError:
        return None
    return taken.read_text().strip() or None


def cmd_spawn(args):
    tip = mg.rev(args.ref)
    if not tip:
        raise mg.GateError(f"cannot resolve '{args.ref}'")
    directory = state_dir(args.state_dir)
    directory.mkdir(parents=True, exist_ok=True)
    with open(directory / "pending.lock", "w") as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)  # read, compare and replace as one step against other spawns
        slot = directory / "pending"
        current = slot.read_text().strip() if slot.exists() else ""
        older = current and current != tip and mg.git("merge-base", "--is-ancestor", tip, current, check=False).returncode == 0
        if not older:  # one slot: the latest tip wins, never an ancestor of the pending one
            with tempfile.NamedTemporaryFile("w", dir=directory, prefix="pending.", delete=False) as staged:
                staged.write(tip + "\n")
            try:
                os.replace(staged.name, slot)
            except OSError:
                Path(staged.name).unlink(missing_ok=True)
                raise
    with open(directory / "monitor.log", "a") as log:
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "work", "--remote", args.remote,
             "--state-dir", str(directory)],
            cwd=mg.toplevel(os.getcwd()), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    LOG.info("%s pending; log %s", tip[:12], directory / "monitor.log")
    return 0


def cmd_work(args):
    """Verify pending tips under the lock; leave at once when another worker holds it."""
    directory = state_dir(args.state_dir)
    directory.mkdir(parents=True, exist_ok=True)
    os.nice(10)  # the author's host stays responsive
    while True:  # each tip is verified once, so the loop ends when merges stop
        with open(directory / "lock", "w") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return 0  # a run is in flight; it will take the pending tip
            while tip := take_pending(directory):
                try:
                    verify_tip(tip, args.remote, directory)
                except Exception as exc:  # no verdict is unverified: log, then take the next tip
                    LOG.error("%s: %s: %s; no verdict", tip[:12], type(exc).__name__, exc)
        if not (directory / "pending").exists():  # a spawn between the last take and the unlock
            return 0


def cmd_verify(args):
    tip = mg.rev(args.tip)
    if not tip:
        raise mg.GateError(f"cannot resolve '{args.tip}'")
    directory = state_dir(args.state_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return verify_tip(tip, args.remote, directory)


def parser():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)
    for name, func in (("spawn", cmd_spawn), ("work", cmd_work), ("verify", cmd_verify)):
        s = sub.add_parser(name)
        s.set_defaults(func=func)
        s.add_argument("--remote", default="origin", help="where the notes refs live")
        s.add_argument("--state-dir", help="lock, pending slot and logs (default <git common dir>/merge-gate-monitor)")
        if name == "spawn":
            s.add_argument("--ref", default="origin/main", help="main tip to verify")
        if name == "verify":
            s.add_argument("--tip", required=True, help="main tip to verify, in the foreground")
    return p


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s merge-monitor: %(message)s")
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except (mg.GateError, OSError, ValueError) as exc:
        LOG.error("%s", exc)
        return NONE


if __name__ == "__main__":
    sys.exit(main())

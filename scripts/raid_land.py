#!/usr/bin/env python3
"""Land one merge request by /merge's recipe, in one call (ticket 1255).

    raid_land.py <pr> --ruled-head <sha|-> --ruled-claims <ids|-> [--base main] [--cleanup]

Run it from the request's own worktree on its head branch. It executes
`skills/merge/SKILL.md` § The recipe, steps 0 to 8; step 9 (the after-merge
runner) is NOT run here, the caller starts it. That file stays the contract.
`--ruled-head` is the tip the review gate ruled on (`-` for a bookkeeping tier
request, which then must read as bookkeeping). `--ruled-claims` is the comma
list of ticket ids the gate ruled on (`-` for none); the body must still claim
exactly that set. Prints one `<pr> merge <start> <end>` row for
`step_clock.py table` and posts the duration comment.

Exit: 0 merged and synced; 1 refused before any merge (reason on stderr);
4 merged but local main not synced (sync script missing, failing or unknown
output); 5 queued on an ungated base; 6 merge outcome unknown (an error after
the merge call: read the request by hand, never re-run). Forge calls live in `GhForge`; git, merge-gate.py, erg and
sync-local-main.sh are called directly.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from step_clock import fmt

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "scripts" / "merge-gate.py"
SYNC = ROOT / "scripts" / "sync-local-main.sh"
OK, REFUSED, UNSYNCED, QUEUED, UNKNOWN = 0, 1, 4, 5, 6


class Refusal(Exception):
    """A reason to stop; the message goes to stderr."""


class PostMerge(Refusal):
    """A failure after the merge call: the outcome is unknown, never re-merge."""


class MergeRefused(Exception):
    """The forge reported that it refused the merge call (nonzero exit)."""


class GhForge:
    """The forge adapter: the only place that spells `gh`."""

    def _gh(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["gh", *args], capture_output=True, text=True, timeout=120)

    def resolve(self, pr: str) -> dict:
        done = self._gh("pr", "view", pr, "--json", "state,isDraft,headRefName,baseRefName,headRefOid,body")
        if done.returncode != 0:
            raise Refusal(f"cannot read request {pr}: {done.stderr.strip()}")
        return json.loads(done.stdout)

    def ready(self, pr: str) -> None:
        self._gh("pr", "ready", pr)

    def auto_merge_armed(self, pr: str) -> bool:
        done = self._gh("pr", "view", pr, "--json", "autoMergeRequest", "-q", ".autoMergeRequest != null")
        if done.returncode != 0 or done.stdout.strip() not in ("true", "false"):
            raise Refusal("auto-merge state unreadable")
        return done.stdout.strip() == "true"

    def disarm(self, pr: str) -> None:
        self._gh("pr", "merge", pr, "--disable-auto")

    def merge(self, pr: str, head: str, auto: bool) -> None:
        done = self._gh("pr", "merge", pr, "--merge", *(["--auto"] if auto else ["--match-head-commit", head]))
        if done.returncode != 0:
            raise MergeRefused(done.stderr.strip() or f"gh exit {done.returncode}")

    def read_back(self, pr: str) -> str | None:
        """`<STATE> <head> <queued|->`, or None when unreadable."""
        done = self._gh(
            "pr", "view", pr, "--json", "state,headRefOid,autoMergeRequest", "-q",
            '"\\(.state) \\(.headRefOid) \\(if .autoMergeRequest then "queued" else "-" end)"')
        out = done.stdout.strip()
        return out if done.returncode == 0 and len(out.split()) == 3 else None

    def comment(self, pr: str, body: str) -> None:
        self._gh("pr", "comment", pr, "--body", body)


def git(cwd, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)


def rev(cwd, ref: str) -> str:
    done = git(cwd, "rev-parse", ref)
    if done.returncode != 0:
        raise Refusal(f"cannot resolve {ref}")
    return done.stdout.strip()


def gate(cwd, *args: str) -> int:
    return subprocess.run([sys.executable, str(GATE), *args], cwd=cwd,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode


def close_claims(body: str) -> list[str]:
    """Ticket ids claimed in the body, fences ignored (skills/merge/references/claims.md)."""
    ids: list[str] = []
    fence = None
    for line in body.splitlines():
        m = re.match(r"\s*(`{3,}|~{3,})", line)
        if m:
            mark = m.group(1)
            if fence is None:
                fence = mark
            elif mark[0] == fence[0] and len(mark) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        m = re.match(r"\s*(?:\*\*)?Ticket:(?:\*\*)?\s*(\S.*)$", line)
        if not m:
            continue
        value = m.group(1).strip()
        p = re.match(r"tickets/(?:closed/)?(\d{4,})-", value)
        if p:
            ids.append(p.group(1))
        elif value.lower() != "none":
            raise Refusal(f"close claim not in canonical form: {line.strip()!r}")
    if fence:
        raise Refusal("unclosed code fence in the request body")
    return list(dict.fromkeys(ids))


def close_tickets(cwd: Path, pr: str, ids: list[str]) -> bool:
    """Step 1. True when a close commit was pushed."""
    todo = []
    for tid in ids:
        closed = list((cwd / "tickets" / "closed").glob(f"{tid}-*.erg"))
        if closed and "\nClosed:" in closed[0].read_text():
            continue
        if not closed and not list((cwd / "tickets").glob(f"{tid}-*.erg")):
            raise Refusal(f"claimed ticket {tid} is in neither tickets/ nor tickets/closed/")
        todo.append(tid)
    if not todo:
        return False
    erg = os.environ.get("ERG") or "tickets/erg"
    for tid in todo:
        subprocess.run([erg, "close", tid, f"autoclosed — PR #{pr}"], cwd=cwd, check=False)
        subprocess.run([erg, "archive", tid], cwd=cwd, check=False)
        git(cwd, "add", "-u", "tickets/")
        git(cwd, "add", *map(str, (cwd / "tickets" / "closed").glob(f"{tid}-*.erg")))
    msg = f"ticket({', '.join(todo)}): close and archive — PR #{pr}"
    if git(cwd, "commit", "-m", msg).returncode != 0 or git(cwd, "push", "origin", "HEAD").returncode != 0:
        raise Refusal("close commit or push failed")
    return True


def check_head(cwd: Path, branch: str, base: str, ruled: str) -> str:
    git(cwd, "fetch", "-q", "origin")
    head = rev(cwd, "HEAD")
    if head != rev(cwd, f"origin/{branch}"):
        raise Refusal("local head differs from origin/" + branch + " (sync, never merge)")
    if ruled == "-":
        if gate(cwd, "tier", "--base", f"origin/{base}", "--head", "HEAD") != 0:
            raise Refusal("no ruled head given and the request is not bookkeeping tier")
    elif head != ruled and gate(
            cwd, "tier", "--base", f"origin/{base}", "--head", "HEAD", "--since", ruled) != 0:
        raise Refusal(f"head {head[:12]} adds more than bookkeeping to the ruled tip {ruled[:12]}")
    return head


def record(cwd: Path, base: str) -> None:
    """Steps 4: check the gate record, writing it when missing; one re-record on a moved base."""
    args = ("--base", f"origin/{base}", "--head", "HEAD")
    for _ in range(2):
        rc = gate(cwd, "check", *args)
        if rc == 2:
            gate(cwd, "run", *args)
            rc = gate(cwd, "check", *args)
        if rc != 2:
            break
    if rc == 2:
        raise Refusal("gate record stale twice (the base keeps moving)")
    if rc != 0:
        raise Refusal(f"gate check answered {rc}")


SYNCED = re.compile(r"fast-forwarded at|updated by ref")


def sync(primary: Path, base: str) -> tuple[bool, list[str]]:
    """Step 8. (synced, lines): synced only on exit 0 and a known success line."""
    try:
        done = subprocess.run([str(SYNC), str(primary), base], capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.SubprocessError) as exc:
        return False, [f"sync-local-main: could not run ({exc})"]
    lines = (done.stdout + done.stderr).strip().splitlines()
    ok = done.returncode == 0 and any(SYNCED.search(line) for line in lines)
    if not ok and not lines:
        lines = [f"sync-local-main: no output (exit {done.returncode}), not confirmed synced"]
    return ok, lines


def attribution(body: str) -> str:
    """Step 0 warning text: `ok`, `missing`, `invalid: ...` or `unchecked`; never a refusal."""
    try:
        done = subprocess.run([sys.executable, str(ROOT / "scripts" / "attribution_record.py"), "--pr-body"],
                              input=body, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return "unchecked"
    out = done.stdout.strip()
    return out if done.returncode == 0 and out else (out or "unchecked")


def cleanup(cwd: Path, branch: str, head: str, base: str) -> str:
    """Remove the merged worktree from outside it; retain on any doubt."""
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    primary = Path(common).parent
    os.chdir(primary)
    git(primary, "fetch", "-q", "--prune", "origin")
    if git(primary, "merge-base", "--is-ancestor", head, f"origin/{base}").returncode != 0:
        return f"cleanup skipped: {head[:12]} not in origin/{base}"
    git(primary, "worktree", "unlock", str(cwd))
    if git(primary, "worktree", "remove", str(cwd)).returncode != 0:
        return f"cleanup skipped: worktree {cwd} not removed"
    if git(primary, "branch", "-d", branch).returncode != 0:
        return f"cleanup: branch {branch} retained"
    return f"cleaned {cwd} ({branch})"


def same_claims(body: str, ruled: list[str]) -> None:
    if sorted(close_claims(body)) != sorted(ruled):
        raise Refusal(f"close claims in the body {close_claims(body)} differ from the ruled set {sorted(ruled)}")


def land(forge, pr: str, ruled: str, base: str = "main", cwd: Path | None = None,
         do_cleanup: bool = False, out=print, ruled_claims: list[str] | None = None) -> int:
    cwd = Path(cwd or os.getcwd()).resolve()
    ruled_claims = ruled_claims or []
    start = int(time.time())
    info = forge.resolve(pr)
    branch = info["headRefName"]
    if info["state"] != "OPEN":
        raise Refusal(f"request is {info['state']}, not OPEN")
    if git(cwd, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() != branch:
        raise Refusal(f"cwd is not on branch {branch}")
    base = info.get("baseRefName") or base
    body = info.get("body") or ""
    out(f"attribution: {attribution(body)}")
    same_claims(body, ruled_claims)
    head = check_head(cwd, branch, base, ruled)
    if close_tickets(cwd, pr, close_claims(body)):
        head = check_head(cwd, branch, base, ruled)
    if info.get("isDraft"):
        forge.ready(pr)
    again = forge.resolve(pr)  # step 3: a body edited after approval is a stop
    same_claims(again.get("body") or "", ruled_claims)
    enabled = gate(cwd, "enabled", "--base", f"origin/{base}")
    if enabled not in (0, 1):
        raise Refusal("gate configuration unreadable (never remove the file to get through)")
    gated = enabled == 0
    if gated:
        record(cwd, base)
        if forge.auto_merge_armed(pr):
            forge.disarm(pr)
            if forge.auto_merge_armed(pr):
                raise Refusal("auto-merge still armed")
    try:
        try:
            forge.merge(pr, head, auto=not gated)
        except MergeRefused as exc:
            # Definite "not merged" only when the forge refused AND the request is still OPEN at this head.
            back = forge.read_back(pr)
            if back is not None and back.split()[:2] == ["OPEN", head] and "queued" not in back:
                raise Refusal(f"forge refused the merge, request still open at {head[:12]}: {exc}") from exc
            raise PostMerge(f"forge reported a refusal ({exc}) but the read-back is {back!r}") from exc
        return after_merge(forge, pr, cwd, branch, base, head, gated, start, do_cleanup, out)
    except Refusal:
        raise
    except Exception as exc:
        raise PostMerge(f"{type(exc).__name__}: {exc}") from exc


def after_merge(forge, pr, cwd, branch, base, head, gated, start, do_cleanup, out) -> int:
    back = forge.read_back(pr)
    if back is None:
        raise PostMerge("read-back unreadable")
    state, oid, queued = back.split()
    if state == "OPEN" and queued == "queued" and not gated:
        out(f"{pr} queued (pending checks)")
        return QUEUED
    if not (state == "MERGED" and oid == head):
        raise PostMerge(f"read-back {back!r}, expected MERGED {head}")
    end = int(time.time())
    out(f"{pr} merge {start} {end}")
    try:
        forge.comment(pr, f"merge {head}: duration: {fmt(end - start)}")
    except Exception as exc:  # the merge landed; a lost comment is reported
        out(f"duration comment failed: {exc}")
    common = git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()
    synced, lines = sync(Path(common).parent, base)
    for line in lines:
        out(line)
    if not synced:
        return UNSYNCED
    if do_cleanup:
        out(cleanup(cwd, branch, head, base))
    return OK


def main_land(forge, pr, ruled, ruled_claims, base, cwd, out=print, do_cleanup=False) -> int:
    """land() with refusals mapped to exit codes; usable by tests with a stub forge."""
    try:
        return land(forge, pr, ruled, base, cwd, do_cleanup, out, ruled_claims)
    except PostMerge as exc:
        out(f"raid_land: {pr} merge outcome unknown: {exc}; the merge was called, read the request by hand, never re-run")
        try:
            out(f"read-back now: {forge.read_back(pr)}")
        except Exception as exc2:
            out(f"read-back now: unreadable ({exc2})")
        return UNKNOWN
    except Refusal as exc:
        print(f"raid_land: {pr} refused: {exc}", file=sys.stderr)
        return REFUSED


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("pr")
    p.add_argument("--ruled-head", required=True, help="tip the gate ruled on, or - (bookkeeping)")
    p.add_argument("--ruled-claims", required=True,
                   help="comma list of ticket ids the gate ruled on, or - for none")
    p.add_argument("--base", default="main")
    p.add_argument("--cleanup", action="store_true", help="remove the merged worktree and branch")
    a = p.parse_args(argv)
    claims = [] if a.ruled_claims == "-" else [c for c in a.ruled_claims.split(",") if c]
    return main_land(GhForge(), a.pr, a.ruled_head, claims, a.base, None, print, a.cleanup)


if __name__ == "__main__":
    sys.exit(main())

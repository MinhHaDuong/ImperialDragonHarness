#!/usr/bin/env python3
"""The forge adapter: every read and write of a merge request behind one module (ticket 1271).

    forge.py [--forge auto|gh|none] resolve <ref>

A review unit is (branch, base ref, head OID). `resolve` takes a request number
(gh backend) or `branch:<name> [base=<ref>]` (none backend) and returns one record:
id, branch, base, head, state, mergeable, draft, body, claims. Backend choice:
`--forge` or `IDH_FORGE`; `auto` is gh when `gh` is on PATH and the ref is a bare number.

Operations: resolve, comments, checks, comment, append_body_line, create, ready,
auto_merge_armed, disarm, merge, read_back. On the `none` backend comment,
append_body_line, ready and disarm return NOOP (falsy, typed, never raising);
comments is empty, checks is "none", auto_merge_armed is False; merge and
read_back raise NoForgeMerge until ticket 1275 (a silent no-op merge would read
back "merged" on nothing). No caller uses this module yet (ticket 1272 moves them);
the gh backend is lifted from raid_land.GhForge.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys


class ForgeRefusal(Exception):
    """The forge cannot answer or refused; the message says why."""


class NoForgeMerge(ForgeRefusal):
    """merge/read_back on the none backend: not implemented before ticket 1275."""


class MergeRefused(ForgeRefusal):
    """The forge reported that it refused the merge call."""


class _NoOp:
    """Typed result of an operation the backend does not support."""

    def __bool__(self):
        return False

    def __repr__(self):
        return "NOOP"


NOOP = _NoOp()


def parse_claims(body: str) -> list[str]:
    """Ticket ids claimed in a body by `Ticket: tickets/<id>-...` lines, code fences ignored.
    A malformed claim or an unclosed fence is a stop (skills/merge/references/claims.md):
    raises ForgeRefusal, mirroring raid_land.close_claims (not imported: raid_land will import this module)."""
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
            raise ForgeRefusal(f"close claim not in canonical form: {line.strip()!r}")
    if fence:
        raise ForgeRefusal("unclosed code fence in the request body")
    return list(dict.fromkeys(ids))


class GhForge:
    """Backend over the `gh` CLI, resolved from PATH at each call."""

    def _gh(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, timeout=120)
        except OSError as exc:
            raise ForgeRefusal(f"gh unavailable: {exc}") from exc

    def _view(self, ref: str, fields: str) -> dict:
        done = self._gh("pr", "view", str(ref), "--json", fields)
        if done.returncode != 0:
            raise ForgeRefusal(f"cannot read request {ref}: {done.stderr.strip()}")
        return json.loads(done.stdout)

    def resolve(self, ref: str) -> dict:
        d = self._view(ref, "number,state,isDraft,mergeable,headRefName,baseRefName,headRefOid,body")
        body = d.get("body") or ""
        return {"id": str(d["number"]), "branch": d["headRefName"], "base": d["baseRefName"],
                "head": d["headRefOid"], "state": d["state"], "mergeable": d.get("mergeable"),
                "draft": bool(d.get("isDraft")), "body": body, "claims": parse_claims(body)}

    def comments(self, ref: str) -> list[dict]:
        d = self._view(ref, "comments,reviews")
        return d.get("comments", []) + d.get("reviews", [])

    def checks(self, ref: str) -> str:
        """`none`, `passing`, `pending`, or `failing: <names>`. `pending` means a check has not
        finished (no conclusion yet); callers gate on `passing` only. Failing wins over pending."""
        rollup = self._view(ref, "statusCheckRollup").get("statusCheckRollup") or []
        bad = [c for c in rollup if (c.get("conclusion") or c.get("state") or "").upper()
               in ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED")]
        if not rollup:
            return "none"
        if bad:
            return "failing: " + ",".join(c.get("name", "?") for c in bad)
        done = [(c.get("conclusion") or c.get("state") or "").upper() for c in rollup]
        return "pending" if any(d in ("", "PENDING", "EXPECTED") for d in done) else "passing"

    def comment(self, ref: str, body: str) -> None:
        self._gh("pr", "comment", str(ref), "--body", body)

    def append_body_line(self, ref: str, line: str) -> None:
        """Append lines to the body; the read-back is the evidence. The forge has no
        compare-and-swap, so one retry re-fetches the body before giving up."""
        wanted = line.strip("\n").splitlines()
        for _ in range(2):
            body = self._view(ref, "body").get("body") or ""
            if not all(item in body.splitlines() for item in wanted):
                body = body.rstrip("\n") + "\n" + line.strip("\n") + "\n"
                self._gh("api", f"repos/{{owner}}/{{repo}}/pulls/{ref}", "-X", "PATCH", "--input", "-",
                         stdin=json.dumps({"body": body}))
            seen = (self._view(ref, "body").get("body") or "").splitlines()
            if all(item in seen for item in wanted):
                return
        raise ForgeRefusal(f"request {ref} body lost the appended line twice; append it by hand")

    def create(self, branch: str, base: str, title: str, body: str) -> str:
        """Open a request from a pushed branch; its number."""
        done = self._gh("pr", "create", "--head", branch, "--base", base, "--title", title, "--body", body)
        number = re.search(r"/pull/(\d+)\s*$", done.stdout.strip())
        if done.returncode != 0 or not number:
            raise ForgeRefusal(f"cannot open a request from {branch}: {done.stderr.strip() or done.stdout.strip()}")
        return number.group(1)

    def ready(self, ref: str) -> None:
        self._gh("pr", "ready", str(ref))

    def auto_merge_armed(self, ref: str) -> bool:
        done = self._gh("pr", "view", str(ref), "--json", "autoMergeRequest", "-q", ".autoMergeRequest != null")
        if done.returncode != 0 or done.stdout.strip() not in ("true", "false"):
            raise ForgeRefusal("auto-merge state unreadable")
        return done.stdout.strip() == "true"

    def disarm(self, ref: str) -> None:
        self._gh("pr", "merge", str(ref), "--disable-auto")

    def merge(self, ref: str, head: str, auto: bool) -> None:
        done = self._gh("pr", "merge", str(ref), "--merge", *(["--auto"] if auto else ["--match-head-commit", head]))
        if done.returncode != 0:
            raise MergeRefused(done.stderr.strip() or f"gh exit {done.returncode}")

    def read_back(self, ref: str) -> str | None:
        """`<STATE> <head> <queued|->`, or None when unreadable."""
        done = self._gh(
            "pr", "view", str(ref), "--json", "state,headRefOid,autoMergeRequest", "-q",
            '"\\(.state) \\(.headRefOid) \\(if .autoMergeRequest then "queued" else "-" end)"')
        out = done.stdout.strip()
        return out if done.returncode == 0 and len(out.split()) == 3 else None


class NoneForge:
    """Backend for a repository with no forge: git only, over `branch:<name> [base=<ref>]`."""

    def __init__(self, cwd: str | None = None):
        self.cwd = cwd

    def _git(self, *args: str) -> subprocess.CompletedProcess:
        cmd = ["git"] + (["-C", self.cwd] if self.cwd else []) + list(args)
        return subprocess.run(cmd, capture_output=True, text=True)

    def _rev(self, ref: str) -> str:
        done = self._git("rev-parse", "--verify", "-q", ref + "^{commit}")
        if done.returncode != 0:
            raise ForgeRefusal(f"cannot resolve {ref}")
        return done.stdout.strip()

    def resolve(self, ref: str) -> dict:
        m = re.fullmatch(r"branch:(\S+)(?:\s+base=(\S+))?", ref.strip())
        if not m:
            raise ForgeRefusal(f"none backend takes 'branch:<name> [base=<ref>]', got {ref!r}")
        branch, base = m.group(1), m.group(2) or "origin/main"
        if not m.group(2) and self._git("rev-parse", "--verify", "-q", base).returncode != 0:
            base = "main"
        head, base_oid = self._rev(branch), self._rev(base)
        merged = self._git("merge-base", "--is-ancestor", head, base_oid).returncode == 0
        tree = self._git("merge-tree", "--write-tree", base_oid, head)
        trailers = self._git("log", "--format=%B", f"{base_oid}..{head}").stdout
        return {"id": f"branch:{branch}", "branch": branch, "base": base, "head": head,
                "state": "MERGED" if merged else "OPEN",
                "mergeable": "MERGEABLE" if tree.returncode == 0 else "CONFLICTING",
                "draft": False, "body": "", "claims": parse_claims(trailers)}

    def comments(self, ref: str) -> list[dict]:
        return []

    def checks(self, ref: str) -> str:
        return "none"

    def comment(self, ref: str, body: str):
        return NOOP

    def append_body_line(self, ref: str, line: str):
        return NOOP

    def create(self, branch: str, base: str, title: str, body: str) -> str:
        return f"branch:{branch}"

    def ready(self, ref: str):
        return NOOP

    def auto_merge_armed(self, ref: str) -> bool:
        return False

    def disarm(self, ref: str):
        return NOOP

    def merge(self, ref: str, head: str, auto: bool):
        raise NoForgeMerge("no forge: the local merge arrives with ticket 1275")

    def read_back(self, ref: str):
        raise NoForgeMerge("no forge: the local read-back arrives with ticket 1275")


def get_forge(choice: str | None = None, ref: str = "", cwd: str | None = None):
    """Pick a backend: `choice` or IDH_FORGE (auto|gh|none); auto = gh when on PATH and ref is a number."""
    choice = choice or os.environ.get("IDH_FORGE") or "auto"
    if choice == "gh":
        return GhForge()
    if choice == "none":
        return NoneForge(cwd)
    if choice != "auto":
        raise ForgeRefusal(f"unknown forge {choice!r} (auto|gh|none)")
    return GhForge() if shutil.which("gh") and re.fullmatch(r"#?\d+", ref.strip()) else NoneForge(cwd)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--forge", choices=["auto", "gh", "none"], default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("resolve").add_argument("ref")
    a = p.parse_args(argv)
    try:
        print(json.dumps(get_forge(a.forge, a.ref).resolve(a.ref), indent=2))
    except ForgeRefusal as exc:
        print(f"forge: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

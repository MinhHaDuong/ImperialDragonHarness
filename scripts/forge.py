#!/usr/bin/env python3
"""The forge adapter: every read and write of a merge request behind one module (ticket 1271).

    forge.py [--forge auto|gh|none] resolve <ref>

A review unit is (branch, base ref, head OID). `resolve` takes a request number
(gh backend) or `branch:<name> [base=<ref>]` (none backend) and returns one record:
id, branch, base, head, state, mergeable, draft, body, claims; the none backend adds
review_id, the latest review naming the branch in refs/notes/review (ticket 1273), or None. Backend choice:
`--forge`; `auto` is gh when `gh` is on PATH and the ref is a bare number. There is no environment
switch: the landing route is read off the repository (ticket 1280, conception/2026-10-27-review-merge-flows.md).

Operations: resolve, comments, checks, comment, append_body_line, create, ready,
auto_merge_armed, disarm, merge, read_back. On the `none` backend comment,
append_body_line, ready and disarm return NOOP (falsy, typed, never raising);
comments is empty, checks is "none", auto_merge_armed is False; merge is the
local gated merge of ticket 1275 (design D3 of 1252) and read_back reads the merge
commit back from git, never from the call. merged_at is the merge timestamp of a merged request.
The callers (ticket 1272): gaze_setup, gaze_close, attribution_record, review-anchor, raid_land.
`resolve` never raises on a malformed close claim: it returns `claims: []` and `claims_error`,
so each caller keeps its own order of refusals; parse_claims is the one parser.
ForgeRefusal and MergeRefused here are not raid_land's Refusal: a caller maps them, never
catches one for the other.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


class ForgeRefusal(Exception):
    """The forge cannot answer or refused; the message says why."""


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
    raises ForgeRefusal; raid_land.close_claims wraps this into its Refusal."""
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


def _claims(body: str) -> dict:
    """The claims fields of a resolve record; a malformed claim is reported, not raised."""
    try:
        return {"claims": parse_claims(body)}
    except ForgeRefusal as exc:
        return {"claims": [], "claims_error": str(exc)}


class GhForge:
    """Backend over the `gh` CLI, resolved from PATH at each call; `cwd` is where gh runs."""

    def __init__(self, cwd: str | None = None):
        self.cwd = cwd

    def _gh(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(["gh", *args], input=stdin, capture_output=True, text=True, timeout=120,
                                  cwd=self.cwd)
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
        return {"id": str(d.get("number", ref)), "branch": d["headRefName"], "base": d["baseRefName"],
                "head": d["headRefOid"], "state": d["state"], "mergeable": d.get("mergeable"),
                "draft": bool(d.get("isDraft")), "body": body, **_claims(body)}

    def comments(self, ref: str, reviews: bool = True) -> list[dict]:
        """Comments, then formal reviews unless `reviews` is False."""
        d = self._view(ref, "comments,reviews" if reviews else "comments")
        return d.get("comments", []) + (d.get("reviews", []) if reviews else [])

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

    def comment(self, ref: str, body: str, strict: bool = False) -> None:
        """Post a comment. Lenient by default (a failure is not reported); `strict` raises
        ForgeRefusal with gh's stderr."""
        done = self._gh("pr", "comment", str(ref), "--body", body)
        if strict and done.returncode != 0:
            raise ForgeRefusal(done.stderr.strip())

    def merged_at(self, ref: str) -> str | None:
        """The merge timestamp (ISO 8601) of a merged request, else None."""
        return self._view(ref, "mergedAt").get("mergedAt") or None

    def append_body_line(self, ref: str, line: str, edit=None) -> None:
        """Append lines to the body; the read-back is the evidence. The forge has no
        compare-and-swap, so one retry re-fetches the body before giving up. `edit(body)`
        returns the new body in place of the plain append and is applied on every attempt."""
        wanted = line.strip("\n").splitlines()
        for _ in range(2):
            body = self._view(ref, "body").get("body") or ""
            if edit is not None or not all(item in body.splitlines() for item in wanted):
                body = edit(body) if edit else body.rstrip("\n") + "\n" + line.strip("\n") + "\n"
                done = self._gh("api", f"repos/{{owner}}/{{repo}}/pulls/{ref}", "-X", "PATCH", "--input", "-",
                                stdin=json.dumps({"body": body}))
                if done.returncode != 0:
                    raise ForgeRefusal(f"gh api failed: {done.stderr.strip()}")
            seen = (self._view(ref, "body").get("body") or "").splitlines()
            if all(item in seen for item in wanted):
                return
        raise ForgeRefusal(f"PR #{ref} body lost the appended line twice; append it by hand")

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
                "draft": False, "body": "", **_claims(trailers), "review_id": self._review_id(branch)}

    def _review_id(self, branch: str) -> str | None:
        """The review of the latest request naming `branch` in refs/notes/review (ticket 1273)."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "review_notes", os.path.join(os.path.dirname(os.path.abspath(__file__)), "review_notes.py"))
        rn = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rn)
        try:
            return rn.find(self.cwd or ".", branch)
        except rn.Tamper as exc:  # surfaced, never read as "no review"
            raise ForgeRefusal(f"refs/notes/review: TAMPER: {exc}") from exc
        except rn.Refusal:
            return None

    def comments(self, ref: str, reviews: bool = True) -> list[dict]:
        return []

    def checks(self, ref: str) -> str:
        return "none"

    def comment(self, ref: str, body: str, strict: bool = False):
        return NOOP

    local = True  # raid_land runs its local-landing path for this backend (ticket 1275)

    def base_branch(self, info: dict) -> str:
        """The local branch a request's base names: `origin/main` and `main` both give `main`."""
        base = info["base"]
        return base[len("origin/"):] if base.startswith("origin/") else base

    def has_remote(self) -> bool:
        return self._git("remote", "get-url", "origin").returncode == 0

    def _landing(self, info: dict) -> str | None:
        """The merge commit that brought `info.head` into the base branch (first-parent walk), else None."""
        walk = self._git("log", "--first-parent", "--merges", "--format=%H %P", "-n", "200",
                         f"refs/heads/{self.base_branch(info)}")
        for line in walk.stdout.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[2] == info["head"]:
                return parts[0]
        return None

    def merged_at(self, ref: str):
        """The committer date (ISO 8601) of the merge commit that landed the unit, else None."""
        landed = self._landing(self.resolve(ref))
        return (self._git("show", "-s", "--format=%cI", landed).stdout.strip() or None) if landed else None

    def append_body_line(self, ref: str, line: str, edit=None):
        return NOOP

    def create(self, branch: str, base: str, title: str, body: str) -> str:
        return f"branch:{branch}"

    def ready(self, ref: str):
        return NOOP

    def auto_merge_armed(self, ref: str) -> bool:
        return False

    def disarm(self, ref: str):
        return NOOP

    def _checked_out(self, bname: str) -> str | None:
        """The worktree that has refs/heads/<bname> checked out, else None."""
        path = None
        for line in self._git("worktree", "list", "--porcelain").stdout.splitlines():
            if line.startswith("worktree "):
                path = line[len("worktree "):]
            elif line == f"branch refs/heads/{bname}":
                return path
        return None

    def merge(self, ref: str, head: str, auto: bool):
        """D3 of ticket 1252: merge `head` (pinned by OID) into the local base branch, no forge.

        In a throwaway detached worktree at the base tip: `git merge --no-ff <head>`. The new tip
        then replaces the old one by compare-and-swap (`update-ref ... <old>`), or, when a worktree
        has the base checked out, by a fast-forward there so its files follow the ref. Either
        way the main-update guard (hooks/reference-transaction) judges the move; a refusal is a
        MergeRefused carrying its stderr. With a remote the base is then pushed (fast-forward only);
        a failed push leaves the local base moved and raises ForgeRefusal saying so.
        The caller has already checked the gate record (raid_land.record)."""
        info = self.resolve(ref)
        if info["state"] != "OPEN":
            raise MergeRefused(f"unit is {info['state']}, not OPEN")
        if info["head"] != head:
            raise MergeRefused(f"{info['branch']} is at {info['head'][:12]}, not the pinned {head[:12]}")
        if info["mergeable"] != "MERGEABLE":
            raise MergeRefused(f"{info['branch']} does not merge cleanly into {info['base']}")
        bname = self.base_branch(info)
        bref = f"refs/heads/{bname}"
        old = self._rev(bref)
        with tempfile.TemporaryDirectory(prefix="forge-merge-") as tmp:
            tree = os.path.join(tmp, "candidate")
            added = self._git("worktree", "add", "-q", "--detach", tree, old)
            if added.returncode != 0:
                raise MergeRefused(f"cannot create the merge worktree: {added.stderr.strip()}")
            try:
                msg = f"Merge branch '{info['branch']}' into {bname}\n\nreviewed-head: {head}\n"
                done = subprocess.run(["git", "-C", tree, "merge", "--no-ff", "-q", "-m", msg, head],
                                      capture_output=True, text=True)
                if done.returncode != 0:
                    raise MergeRefused(f"git merge failed: {(done.stderr or done.stdout).strip()}")
                new = subprocess.run(["git", "-C", tree, "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip()
            finally:
                self._git("worktree", "remove", "--force", tree)
        if self._git("rev-parse", f"{new}^2").stdout.strip() != head:
            raise MergeRefused("the merge commit's second parent is not the pinned head")
        where = self._checked_out(bname)
        if where:
            moved = subprocess.run(["git", "-C", where, "merge", "--ff-only", "-q", new],
                                   capture_output=True, text=True)
        else:
            moved = self._git("update-ref", bref, new, old)
        if moved.returncode != 0:
            raise MergeRefused(f"{bname} not moved: {(moved.stderr or moved.stdout).strip()}")
        if self._git("rev-parse", bref).stdout.strip() != new:  # a checkout switched under us: publish nothing
            raise MergeRefused(f"{bname} is not at the new merge {new[:12]} after the move; nothing pushed")
        if self.has_remote():
            pushed = self._git("push", "-q", "origin", f"{new}:{bref}")
            if pushed.returncode != 0:
                raise ForgeRefusal(f"{bname} moved locally to {new[:12]} but the push failed: "
                                   f"{pushed.stderr.strip()}; push it by hand, never re-merge")

    def read_back(self, ref: str):
        """`<STATE> <head> -`: MERGED with the second parent of the merge commit that landed the
        unit (first-parent walk of the base). A head in the base by no such merge commit reads
        `MERGED - -`, which matches no pinned head; otherwise OPEN with the branch tip."""
        info = self.resolve(ref)
        landed = self._landing(info)
        if landed:
            return f"MERGED {self._git('rev-parse', landed + '^2').stdout.strip()} -"
        return "MERGED - -" if info["state"] == "MERGED" else f"OPEN {info['head']} -"


def _has_origin(cwd: str | None) -> bool:
    return subprocess.run(["git", "-C", cwd or ".", "remote", "get-url", "origin"],
                          capture_output=True, text=True).returncode == 0


def get_forge(choice: str | None = None, ref: str = "", cwd: str | None = None, landing: bool = False):
    """Pick a backend: `choice` (auto|gh|none; default auto). No environment switch (ticket 1280).

    auto reads the route off the repository. Reviewing: gh when it is on PATH and the ref is a bare
    number, else none (review on notes). Landing (`landing=True`): with a remote named origin the
    forge is the only route, so gh or a refusal naming the cause, never the local merge; with no origin
    remote the local gated merge (none). An explicit `gh` or `none` is for tests and the --forge flag."""
    choice = choice or "auto"
    if choice == "gh":
        return GhForge(cwd)
    if choice == "none":
        return NoneForge(cwd)
    if choice != "auto":
        raise ForgeRefusal(f"unknown forge {choice!r} (auto|gh|none)")
    numeric = bool(re.fullmatch(r"#?\d+", ref.strip()))
    if landing and _has_origin(cwd):
        if not shutil.which("gh"):
            raise ForgeRefusal("this repository has an origin remote and gh is not available; "
                               "landing waits for the forge")
        if not numeric:
            raise ForgeRefusal(f"this repository has an origin remote; landing {ref!r} needs a forge "
                               "request number, never the local merge")
        return GhForge(cwd)
    if landing:
        return NoneForge(cwd)  # no origin remote: the local gated merge, whatever the ref
    return GhForge(cwd) if shutil.which("gh") and numeric else NoneForge(cwd)


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

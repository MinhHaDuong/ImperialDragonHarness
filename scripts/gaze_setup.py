#!/usr/bin/env python3
"""Gaze setup in one call (ticket 1227): clock, isolation worktree, anchor,
PR state, ticket files, panel directory, printed as one key=value block.

    gaze_setup.py <pr>

Exit: 0 ready, 1 blocked (conflicts, missing ticket file, worktree not created),
2 read failure (forge or anchor), 3 another gaze is live on this PR.
Leftover review worktree of a dead run is cleaned (gaze_close.cleanup) first.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import gaze_close  # same directory: the script dir is on sys.path

HERE = Path(__file__).resolve().parent

LIVENESS_DEFAULT = 1200


def liveness_window():
    try:
        m = re.search(r"^fork_liveness_seconds:\s*(\d+)",
                      (HERE.parent / "skills/gaze/telemetry.yml").read_text(), re.M)
        return int(m.group(1)) if m else LIVENESS_DEFAULT
    except OSError:
        return LIVENESS_DEFAULT


def newest_mtime(tree):
    newest = tree.stat().st_mtime
    for dp, dns, fns in os.walk(tree):
        if ".git" in dns and Path(dp) == tree:
            dns.remove(".git")
        for n in dns + fns:
            try:
                newest = max(newest, os.lstat(os.path.join(dp, n)).st_mtime)
            except OSError:
                pass
    return newest


FENCE = re.compile(r"[ \t]{0,3}(`{3,}|~{3,})(.*)$")


def live_lines(body):
    """Body lines outside closed code fences (the `/merge` grammar,
    skills/merge/references/claims.md; lines of an unclosed fence stay in,
    as check-close-claims.sh keeps them, so a hidden claim is still seen)."""
    live, held, opener = [], [], None
    for line in body.splitlines():
        m = FENCE.fullmatch(line.rstrip("\r"))
        if opener is None:
            if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
                opener, held = m.group(1), [line]
            else:
                live.append(line)
        else:
            held.append(line)
            if m and m.group(1)[0] == opener[0] and len(m.group(1)) >= len(opener) \
                    and not m.group(2).strip():
                opener = None
    if opener is not None:
        live.extend(held)
    return live


def close_claims(body, tree):
    """Ticket files named by close claims: `Ticket: tickets/...` paths and the
    short `Ticket: NNNN` form (resolved against the review tree). `Ticket-ref:`
    and prose mentions are not claims."""
    found = []
    for line in live_lines(body):
        m = re.fullmatch(r"\*{0,2}ticket:?\*{0,2}:?\s*(\S+)\s*", line.strip(), re.I)
        if not m:
            continue
        ref = m.group(1)
        if re.fullmatch(r"\d{4}", ref):
            hits = sorted(tree.glob(f"tickets/{ref}-*.erg")) + sorted(tree.glob(f"tickets/closed/{ref}-*.erg"))
            found.append(str(hits[0].relative_to(tree)) if len(hits) == 1 else f"tickets/{ref}-*.erg")
        elif re.fullmatch(r"tickets/(?:closed/)?[\w.-]+\.erg", ref):
            found.append(ref)
    return sorted(set(found))


def fail(code, msg):
    print(f"gaze_setup: {msg}", file=sys.stderr)
    return code


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pr", help="PR number")
    pr = ap.parse_args().pr
    clock = str(int(time.time()))
    primary = gaze_close.primary_root()
    r = subprocess.run(["gh", "pr", "view", pr, "--json",
                        "headRefName,headRefOid,baseRefName,state,mergeable,body,comments,reviews,statusCheckRollup"],
                       capture_output=True, text=True)
    if r.returncode:
        return fail(2, f"cannot read PR {pr}: {r.stderr.strip()}")
    meta = json.loads(r.stdout)
    branch = meta["headRefName"]
    if meta.get("mergeable") == "CONFLICTING":
        return fail(1, f"PR {pr} has merge conflicts")
    tree = primary / ".claude" / "worktrees" / f"review-{pr}"
    if tree.exists():
        if time.time() - newest_mtime(tree) < liveness_window():
            return fail(3, "another gaze is live on this PR")
        ok, msg = gaze_close.cleanup(primary, pr, branch)
        if not ok:
            return fail(1, f"leftover review worktree not removable: {msg}")
    if subprocess.run(["git", "fetch", "origin", branch], capture_output=True).returncode:
        return fail(2, f"git fetch origin {branch} failed")
    r = subprocess.run(["git", "worktree", "add", str(tree), f"origin/{branch}"],
                       capture_output=True, text=True)
    if r.returncode or not tree.is_dir():
        return fail(1, f"cannot create isolated review worktree for PR {pr}; refusing to fall back "
                       f"into the invoking tree: {r.stderr.strip()}")
    a = subprocess.run([sys.executable, str(HERE / "review-anchor.py"), pr, "--worktree", str(tree)],
                       capture_output=True, text=True)
    if a.returncode:
        return fail(2, a.stderr.strip() or "REVIEW-ANCHOR: failed")
    body = meta.get("body") or ""
    tickets = close_claims(body, tree)
    missing = [t for t in tickets if not (tree / t).exists()
               and not (tree / "tickets" / "closed" / Path(t).name).exists()]
    panel = tree / ".panel" / pr
    panel.mkdir(parents=True)
    (panel / "pr-body.md").write_text(body)
    _, entry_branch = gaze_close.git("branch", "--show-current")
    _, entry_status = gaze_close.git("status", "--porcelain")
    _, entry_primary = gaze_close.git("-C", str(primary), "status", "--porcelain")
    (panel / "entry-state.json").write_text(json.dumps(
        {"branch": entry_branch, "status": entry_status.splitlines(), "primary": entry_primary.splitlines()}))
    comments = [f"## {c.get('author', {}).get('login', '?')}\n{c.get('body', '')}"
                for c in meta.get("comments", []) + meta.get("reviews", [])]
    (panel / "comments.md").write_text("\n\n".join(comments))
    checks = meta.get("statusCheckRollup") or []
    bad = [c for c in checks if (c.get("conclusion") or c.get("state") or "").upper() in
           ("FAILURE", "ERROR", "TIMED_OUT", "CANCELLED")]
    changed = a.stdout.strip().splitlines()
    ci = "none" if not checks else ("failing: " + ",".join(c.get("name", "?") for c in bad) if bad else "passing")
    print(f"clock={clock}")
    print(f"pr={pr}\nbranch={branch}\nhead={meta['headRefOid']}\nbase={meta['baseRefName']}")
    print(f"state={meta['state']}\nmergeable={meta.get('mergeable')}")
    print(f"ci={ci}")
    print(f"review_tree={tree}\npanel={panel}")
    print(f"pr_body={panel / 'pr-body.md'}\ncomments={panel / 'comments.md'}")
    print(f"ticket={' '.join(tickets) if tickets else 'none'}")
    print(f"anchor={changed[0]}\nchanged_files={len(changed) - 1}")
    print("\n".join(changed[1:]))
    if missing:
        return fail(1, f"close claim names nonexistent ticket file(s): {' '.join(missing)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

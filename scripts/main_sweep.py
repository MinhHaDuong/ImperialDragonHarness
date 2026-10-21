#!/usr/bin/env python3
"""Sweep main for commits that did not enter it through a gated merge.

Ticket 1157 (tracker 1045). The reference-transaction hook guards main only
where it is installed and `core.hooksPath` is not overridden; this sweep
catches what got past it, using only git and the forge's API.

For each first-parent commit of main it reports two facts:
  * gate record: a note in refs/notes/gate on the commit (ticket 1156's record;
    only its presence is read here, its format is 1156's);
  * forge: the PR whose merge commit it is, and whether that PR's required
    checks concluded green on its head.
A commit is `ok` when either fact holds (the record first: the forge's
required-checks ruleset was disabled on 2026-10-21, so forge status alone is no
longer a gate), a `finding` when neither does, and `unknown` when the forge
could not be read and no record decides it.

Exit 0: every commit ok. 1: at least one finding. 2: nothing could be judged
for some commit (forge unreachable) or the range was empty: a sweep that could
not look must not read as an all-clear.
"""

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

GATE_NOTES_REF = "refs/notes/gate"  # shared with hooks/reference-transaction
GREEN = {"success", "neutral", "skipped"}

log = logging.getLogger("main_sweep")


class ForgeError(RuntimeError):
    """The forge could not answer."""


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=check
    )


def gate_record(repo: Path, sha: str) -> str | None:
    """The gate record on `sha`, or None. The one reader of 1156's notes."""
    proc = _git(repo, "notes", f"--ref={GATE_NOTES_REF}", "show", sha, check=False)
    text = proc.stdout.strip()
    return text if proc.returncode == 0 and text else None


def first_parent_commits(
    repo: Path, ref: str, since: str | None = None, max_count: int | None = None
) -> list[str]:
    """The commits that entered `ref`, newest first."""
    args = ["rev-list", "--first-parent"]
    if since:
        args.append(f"--since={since}")
    if max_count:
        args.append(f"--max-count={max_count}")
    return _git(repo, *args, ref).stdout.split()


class GhForge:
    """GitHub through the `gh` CLI, run in the repository so {owner}/{repo} resolve."""

    def __init__(self, repo: Path):
        self.repo = repo

    def _api(self, path: str):
        proc = subprocess.run(
            ["gh", "api", "-H", "Accept: application/vnd.github+json", path],
            capture_output=True, text=True, cwd=self.repo,
        )
        if proc.returncode != 0:
            raise ForgeError(f"gh api {path}: {proc.stderr.strip()[:200]}")
        return json.loads(proc.stdout)

    def merged_pull(self, sha: str) -> tuple[dict | None, list[int]]:
        """(the merged PR whose merge commit is `sha`, other associated PR numbers)."""
        pulls = self._api(f"repos/{{owner}}/{{repo}}/commits/{sha}/pulls")
        for pr in pulls:
            if pr.get("merged_at") and pr.get("merge_commit_sha") == sha:
                return {"number": pr["number"], "head_sha": pr["head"]["sha"]}, []
        return None, [pr["number"] for pr in pulls if pr.get("merged_at")]

    def check_conclusions(self, head_sha: str) -> dict[str, str | None]:
        """Latest conclusion per check name on `head_sha`."""
        runs = self._api(
            f"repos/{{owner}}/{{repo}}/commits/{head_sha}/check-runs?per_page=100"
        )["check_runs"]
        latest: dict[str, dict] = {}
        for run in runs:
            if run["name"] not in latest or run["id"] > latest[run["name"]]["id"]:
                latest[run["name"]] = run
        return {name: run.get("conclusion") for name, run in latest.items()}

    def required_checks(self) -> tuple[list[str], str]:
        """Required check names from the rulesets on main, enforced or not."""
        names: list[str] = []
        sources: list[str] = []
        for summary in self._api("repos/{owner}/{repo}/rulesets"):
            ruleset = self._api(f"repos/{{owner}}/{{repo}}/rulesets/{summary['id']}")
            include = ruleset.get("conditions", {}).get("ref_name", {}).get("include", [])
            if not {"~DEFAULT_BRANCH", "~ALL", "refs/heads/main"} & set(include):
                continue
            for rule in ruleset.get("rules", []):
                if rule.get("type") == "required_status_checks":
                    checks = rule["parameters"]["required_status_checks"]
                    names += [c["context"] for c in checks]
                    sources.append(f"{ruleset['name']} ({ruleset.get('enforcement')})")
        return sorted(set(names)), "ruleset " + ", ".join(sources) if sources else "none"


def _checks_verdict(conclusions: dict[str, str | None], required: list[str]) -> tuple[bool, str]:
    if required:
        bad = [f"{n}={conclusions.get(n, 'missing')}" for n in required
               if conclusions.get(n) not in GREEN]
    else:
        bad = [f"{n}={c}" for n, c in sorted(conclusions.items()) if c not in GREEN]
        if not conclusions:
            bad = ["no check runs"]
    return not bad, ", ".join(bad)


def classify(repo: Path, sha: str, forge, required: list[str]) -> dict:
    subject = _git(repo, "log", "-1", "--format=%s", sha).stdout.strip()
    result = {"sha": sha, "subject": subject, "gate_record": gate_record(repo, sha) is not None,
              "pr": None, "checks": None, "status": "finding", "reason": ""}
    try:
        pr, associated = forge.merged_pull(sha)
        if pr is None:
            result["checks"] = "n/a"
            result["reason"] = (f"associated with PR {associated} but not its merge commit"
                                if associated else "no merged PR has this merge commit")
        else:
            result["pr"] = pr["number"]
            green, bad = _checks_verdict(forge.check_conclusions(pr["head_sha"]), required)
            result["checks"] = "green" if green else "not green"
            result["reason"] = "" if green else f"PR #{pr['number']} checks not green: {bad}"
            if green:
                result["status"] = "ok"
    except ForgeError as exc:
        result["checks"] = "unknown"
        result["status"] = "unknown"
        result["reason"] = str(exc)
    if result["gate_record"]:
        result["status"] = "ok"
        result["reason"] = "gate record"
    return result


def sweep(repo: Path, commits: list[str], forge, required: list[str] | None = None) -> list[dict]:
    if required is None:
        try:
            required, _ = forge.required_checks()
        except ForgeError as exc:
            log.warning("required checks unreadable (%s); requiring every run green", exc)
            required = []
    return [classify(repo, sha, forge, required) for sha in commits]


def exit_code(results: list[dict]) -> int:
    statuses = {r["status"] for r in results}
    if "finding" in statuses:
        return 1
    if not results or "unknown" in statuses:
        return 2
    return 0


def render(results: list[dict], required_source: str, as_json: bool = False) -> str:
    if as_json:
        return json.dumps({"required": required_source, "results": results}, indent=2)
    lines = [f"main sweep: {len(results)} commit(s); required checks from {required_source}"]
    for r in results:
        pr = f"#{r['pr']}" if r["pr"] else "-"
        record = "record" if r["gate_record"] else "no-record"
        lines.append(f"{r['status']:8} {r['sha'][:12]} {record:9} pr={pr:6} "
                     f"checks={r['checks']}  {r['subject'][:60]}"
                     + (f"  [{r['reason']}]" if r["status"] != "ok" else ""))
    counts = {s: sum(r["status"] == s for r in results) for s in ("ok", "finding", "unknown")}
    lines.append("summary: " + " ".join(f"{k}={v}" for k, v in counts.items()))
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", type=Path, default=Path("."), help="any checkout of the repository")
    p.add_argument("--ref", default="origin/main", help="branch to sweep (default origin/main)")
    p.add_argument("--since", help="only commits newer than this git date, e.g. '8 days ago'")
    p.add_argument("--max-count", type=int, default=100, help="at most this many commits")
    p.add_argument("--required", help="comma-separated required check names (default: rulesets)")
    p.add_argument("--fetch", action="store_true",
                   help="fetch origin main and refs/notes/gate first")
    p.add_argument("--json", action="store_true", help="machine-readable report")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="main_sweep: %(message)s")
    args = parse_args(argv)
    if args.fetch:
        _git(args.repo, "fetch", "--quiet", "origin", "main", check=False)
        _git(args.repo, "fetch", "--quiet", "origin",
             f"+{GATE_NOTES_REF}:{GATE_NOTES_REF}", check=False)
    forge = GhForge(args.repo)
    if args.required is not None:
        required = [n for n in args.required.split(",") if n]
        source = "--required"
    else:
        try:
            required, source = forge.required_checks()
        except ForgeError as exc:
            log.warning("required checks unreadable (%s); requiring every run green", exc)
            required, source = [], "unreadable: every run must be green"
    commits = first_parent_commits(args.repo, args.ref, args.since, args.max_count)
    results = sweep(args.repo, commits, forge, required)
    sys.stdout.write(render(results, source, args.json) + "\n")
    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())

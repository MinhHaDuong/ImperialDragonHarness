#!/usr/bin/env python3
"""Fold gaze's adherence returns into one verdict (ticket 1173).

The adherence seat is read-only and cannot launch a worker, so gaze runs
``/verify-adherence <branch> worktree=<tree> semantic=caller`` in the seat
and launches the phase-3 semantic worker itself. This script merges the
seat's verdict with that worker's report and enforces the one rule the
handoff could otherwise lose: when the diff touches an instruction file,
PASS requires a completed, valid semantic worker. It reads structured
fields only (``adherence``, ``semantic_review``, ``semantic_findings``).

Exit 0 on PASS, 1 on FAIL, 2 on unreadable input. The merged verdict is
printed as YAML in the verify-adherence § 4 schema.
"""

import argparse
import logging
import re
import sys
from pathlib import Path, PurePosixPath

import yaml

log = logging.getLogger("adherence_verdict")

INSTRUCTION_NAMES = frozenset({"AGENTS.md", "CLAUDE.md"})
RULE_TREES = ("rules/", ".claude/rules/")
SEVERITIES = frozenset({"blocking", "nit"})
FINDING_KEYS = ("rule_section", "concern", "file", "line", "severity",
                "suggested_test")
IDENTITY_KEYS = ("worker_id", "launch_evidence", "completion_evidence")
FENCE = re.compile(r"```ya?ml\n(.*?)```", re.DOTALL)


def is_instruction_path(path: str, rule_sources: list[str]) -> bool:
    """The conventional floor of verify-adherence § 3, plus any rule
    source the seat itself declared."""
    p = PurePosixPath(path)
    if p.name in INSTRUCTION_NAMES or path in rule_sources:
        return True
    return path.startswith(RULE_TREES) and p.suffix == ".md"


def finding_ok(f: object) -> bool:
    if not isinstance(f, dict):
        return False
    if any(f.get(k) in (None, "") for k in FINDING_KEYS):
        return False
    return f["severity"] in SEVERITIES


def worker_status(report: dict | None, identity: dict) -> tuple[str, str]:
    """``ran`` only for a launched worker whose report is well formed."""
    if report is None or any(not identity.get(k) for k in IDENTITY_KEYS):
        return "unavailable", "no launched semantic worker with a report"
    reviewed = report.get("reviewed_rules")
    findings = report.get("semantic_findings")
    if not isinstance(reviewed, list) or not reviewed:
        return "invalid", "worker report carries no evidence for reviewed rules"
    if not isinstance(findings, list) or not all(map(finding_ok, findings)):
        return "invalid", "worker finding lacks anchor, severity or suggested_test"
    return "ran", "semantic worker launched by the caller completed"


def merge(seat: dict, report: dict | None, changed: list[str],
          identity: dict) -> dict:
    sr = dict(seat.get("semantic_review") or {})
    sources = list(sr.get("rule_sources") or [])
    touched = [p for p in changed if is_instruction_path(p, sources)]
    required = bool(sr.get("applicable")) or bool(touched)
    out = dict(seat)
    out.setdefault("mechanical_failures", [])
    out.setdefault("untested_rules", [])
    if seat.get("adherence") != "PASS":
        # The seat already failed (an earlier blocking phase, or its own
        # escalation): its verdict stands as returned.
        out["adherence"] = "FAIL"
        return out
    if not required:
        if sr.get("status") == "delegated":
            sr.update(status="skipped")
        out.update(semantic_review=sr, adherence="PASS", escalation=None)
        return out

    sr["applicable"] = True
    sr.setdefault("reason", "seat declared the semantic review applicable")
    if touched:
        sr["reason"] = f"diff touches instruction files: {', '.join(touched)}"
    if sr.get("status") == "ran" and all(sr.get(k) for k in IDENTITY_KEYS):
        status = "ran"
        findings = list(seat.get("semantic_findings") or [])
    else:
        status, why = worker_status(report, identity)
        sr.update(status=status, reason=f"{sr['reason']}; {why}")
        sr.update({k: identity.get(k) for k in IDENTITY_KEYS})
        sr["route"] = identity.get("route")
        for k in ("model", "family", "effort"):
            sr[k] = identity.get(k) or "unavailable"
        findings = list(report.get("semantic_findings") or []) \
            if status == "ran" else []
    out["semantic_review"] = sr
    out["semantic_findings"] = findings
    if status != "ran":
        out.update(adherence="FAIL", escalation="adherence-infrastructure")
        return out
    blocking = any(f.get("severity") == "blocking" for f in findings)
    out.update(adherence="FAIL" if blocking else "PASS", escalation=None)
    return out


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = FENCE.search(text)
    data = yaml.safe_load(m.group(1) if m else text)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: no YAML mapping")
    return data


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--seat", type=Path, required=True,
                    help="the adherence seat's verdict artifact")
    ap.add_argument("--worker", type=Path,
                    help="the caller-launched semantic worker's report")
    ap.add_argument("--changed", nargs="*", default=[],
                    help="the PR's changed paths, repo-relative")
    for key in (*IDENTITY_KEYS, "route", "model", "family", "effort"):
        ap.add_argument(f"--{key.replace('_', '-')}", dest=key)
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    args = parse_args(argv)
    try:
        seat = load(args.seat)
        report = load(args.worker) if args.worker else None
    except (OSError, ValueError, yaml.YAMLError) as exc:
        log.error("adherence_verdict: unreadable input: %s", exc)
        return 2
    identity = {k: getattr(args, k) for k in
                (*IDENTITY_KEYS, "route", "model", "family", "effort")}
    out = merge(seat, report, args.changed, identity)
    sys.stdout.write(yaml.safe_dump(out, sort_keys=False))
    return 0 if out["adherence"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())

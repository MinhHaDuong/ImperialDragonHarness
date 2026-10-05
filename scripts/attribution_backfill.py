#!/usr/bin/env python3
"""Append factual post-merge defect events using explicit reviewed coordinates."""

import argparse
import collections
import logging
import re
import subprocess
import sys
from pathlib import Path

from attribution_record import parse_record

LOG = logging.getLogger(__name__)
FULL_SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@", re.MULTILINE)


def git(project, *args):
    result = subprocess.run(["git", "-C", str(project), *args], capture_output=True)
    if result.returncode:
        raise ValueError(f"git {args[0]} failed (unresolvable project revision or path)")
    return result.stdout.decode("utf-8")


def commit_identity(project, value):
    """Accept full commit identities only, without ref or revision expression guessing."""
    if not FULL_SHA.fullmatch(value):
        raise ValueError("revision evidence must be a full commit SHA")
    if git(project, "rev-parse", "--verify", value + "^{commit}").strip() != value:
        raise ValueError("revision evidence is not the exact commit identity")
    return value


def reviewed_evidence(values):
    evidence = collections.defaultdict(set)
    for value in values:
        pr, sep, sha = value.partition("=")
        if not sep or not re.fullmatch(r"[1-9][0-9]*", pr):
            raise ValueError("reviewed evidence must be PR=FULL_COMMIT_SHA")
        evidence[int(pr)].add(sha)
    return evidence


def within_project(path, project):
    """Reject symlinks at every component, even those pointing back inside the tree."""
    path.relative_to(project)
    return (path.resolve().is_relative_to(project)
            and not any(part.is_symlink() for part in (path, *path.parents) if part != project))


def load_records(project, stats):
    records = collections.defaultdict(list)
    journal = project / "memory/journal"
    if not within_project(journal, project):
        LOG.warning("WARN unresolved: unsafe project journal path")
        stats["unresolved"] += 1
        return records
    for path in sorted(journal.rglob("*review-attribution-pr*")):
        if not path.is_file() or path.suffix not in {".md", ".age"}:
            continue
        name_pr = re.search(r"review-attribution-pr([1-9][0-9]*)\.(?:md(?:\.age)?|age)$", path.name)
        pr = int(name_pr[1]) if name_pr else None
        try:
            if not within_project(path, project):
                raise ValueError("unsafe record path")
            if path.suffix == ".age":
                raise ValueError("encrypted record; no decryption or plaintext fallback")
            original = path.read_bytes()
            text = original.decode("utf-8")
            # Reserve an identifiable PR even when its record is malformed.
            header = re.search(r"^pr: ([1-9][0-9]*) ·", text, re.MULTILINE)
            if header:
                pr = int(header[1])
            record = parse_record(text)
            if name_pr and record["pr"] != int(name_pr[1]):
                raise ValueError("record PR disagrees with filename")
            records[record["pr"]].append((path, original, record))
        except (ValueError, OSError, UnicodeError) as error:
            LOG.warning("WARN unresolved %s: %s", path.relative_to(project), error)
            stats["unresolved"] += 1
            possible_prs = {pr}
            if name_pr:
                possible_prs.add(int(name_pr[1]))
            for possible_pr in possible_prs - {None}:
                records[possible_pr].append(None)
    return records


def file_blob(project, revision, path):
    tree = git(project, "ls-tree", "-z", revision, "--", ":(literal)" + path)
    entries = tree.rstrip("\0").split("\0") if tree else []
    if len(entries) != 1:
        raise ValueError("anchor file missing or unresolvable")
    metadata, _, filename = entries[0].partition("\t")
    mode, kind, sha = metadata.split()
    if filename != path or mode not in {"100644", "100755"} or kind != "blob":
        raise ValueError("anchor must name a regular repository file")
    return sha


def renamed_paths(project, base, fix):
    fields = git(project, "diff", "--name-status", "-z", "--find-renames", base, fix).split("\0")
    excluded = set()
    index = 0
    while index < len(fields) and fields[index]:
        status = fields[index]
        width = 3 if status.startswith(("R", "C")) else 2
        if width == 3:
            excluded.update(fields[index + 1:index + width])
        index += width
    return excluded


def covered_anchor(project, reviewed, base, fix, anchor, renamed):
    path, line = anchor.rsplit(":", 1)
    if path in renamed:
        raise ValueError("renamed anchor file; no coordinate recovery")
    reviewed_blob = file_blob(project, reviewed, path)
    if reviewed_blob != file_blob(project, base, path):
        raise ValueError("anchor drift: reviewed file differs from fix base")
    file_blob(project, fix, path)  # Whole-file deletion is unresolved.
    line = int(line)
    if line > len(git(project, "cat-file", "blob", reviewed_blob).splitlines()):
        raise ValueError("anchor line outside reviewed file")
    diff = git(project, "diff", "--no-ext-diff", "--no-textconv", "--no-renames",
               "--no-color", "--unified=0", "--inter-hunk-context=0", base, fix, "--", ":(literal)" + path)
    return any(int(start) <= line < int(start) + int(count or "1")
               for start, count in HUNK.findall(diff))


def backfill(project, fix, fix_pr, evidence, merged_through=None):
    project = project.resolve()
    if Path(git(project, "rev-parse", "--show-toplevel").strip()).resolve() != project:
        raise ValueError("--project must be the project's repository root")
    commit_identity(project, fix)
    if merged_through:
        commit_identity(project, merged_through)
        # A wrap-up branch may remain below the real merge being celebrated.
        # Require the supplied integration tip to belong to actual origin/main;
        # a detached or unintegrated fix cannot provide its own proof.
        git(project, "merge-base", "--is-ancestor", merged_through, "refs/remotes/origin/main")
    git(project, "merge-base", "--is-ancestor", fix, merged_through or "HEAD")
    parents = git(project, "rev-list", "--parents", "-n", "1", fix).split()[1:]
    if len(parents) not in {1, 2}:
        raise ValueError("fix has unresolved merge shape (root or octopus)")
    base = parents[0]
    renamed = renamed_paths(project, base, fix)
    stats = {"appended": 0, "no_match": 0, "unresolved": 0}
    records = load_records(project, stats)
    plans = []
    for pr, entries in records.items():
        if len(entries) != 1:
            LOG.warning("WARN unresolved PR %s: duplicate attribution records", pr)
            stats["unresolved"] += 1
            continue
        if entries[0] is None:
            continue
        path, original, record = entries[0]
        try:
            revisions = evidence.get(pr, set())
            if len(revisions) != 1:
                raise ValueError("absent or ambiguous reviewed revision evidence")
            reviewed = commit_identity(project, next(iter(revisions)))
            git(project, "merge-base", "--is-ancestor", reviewed, base)
            if pr == fix_pr:
                raise ValueError("fix PR is not a past review")
            anchors = sorted({finding["anchor"] for reviewer in record["reviewers"]
                              for finding in reviewer["findings"]})
            matches = [anchor for anchor in anchors
                       if covered_anchor(project, reviewed, base, fix, anchor, renamed)]
            if not matches:
                stats["no_match"] += 1
                continue
            suffix = ("" if original.endswith(b"\n") else "\n") + "".join(
                f"defect-confirmed: {anchor} · source: post-merge-fix · pr: {fix_pr}\n"
                for anchor in matches)
            addition = suffix.encode("utf-8")
            parse_record((original + addition).decode("utf-8"))
            plans.append((path, original, addition, len(matches)))
        except (ValueError, OSError, UnicodeError) as error:
            LOG.warning("WARN unresolved PR %s: %s", pr, error)
            stats["unresolved"] += 1
    # Validate every proposed append before opening any record for writing.
    for path, original, addition, count in plans:
        if not within_project(path, project) or path.read_bytes() != original:
            raise ValueError("record changed during planning; refusing append")
        with path.open("ab") as stream:
            stream.write(addition)
        stats["appended"] += count
    if not records:
        LOG.info("no covered past review records; no-op")
    return stats


def positive_pr(value):
    if not re.fullmatch(r"[1-9][0-9]*", value):
        raise argparse.ArgumentTypeError("PR must be a positive integer")
    return int(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--fix-pr", type=positive_pr, required=True)
    parser.add_argument("--fix-commit", required=True, help="full merged fix commit SHA")
    parser.add_argument("--merged-through", metavar="SHA",
                        help="full integration tip SHA on origin/main when wrap-up HEAD is below fix")
    parser.add_argument("--defect-fix", action="store_true", required=True,
                        help="explicitly commissioned factual defect fix")
    parser.add_argument("--reviewed", action="append", default=[], metavar="PR=SHA",
                        help="durable-trail evidence establishing all record anchor coordinates")
    args = parser.parse_args()
    try:
        stats = backfill(args.project, args.fix_commit, args.fix_pr,
                         reviewed_evidence(args.reviewed), args.merged_through)
        LOG.info("backfill: appended=%s no-match=%s unresolved=%s", stats["appended"],
                 stats["no_match"], stats["unresolved"])
    except (ValueError, OSError, UnicodeError) as error:
        LOG.error("attribution-backfill: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())

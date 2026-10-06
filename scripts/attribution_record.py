#!/usr/bin/env python3
"""Validate fixed-line review attribution and capture it in project memory."""

import argparse
import datetime
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

LOG = logging.getLogger(__name__)
FACT = re.compile(r"^\s*(kind|pr|writer|reviewer|finding|defect-confirmed)\s*:")


def anchor(value):
    """Keep the literal join key; reject ambiguous or escaping paths."""
    match = re.fullmatch(r"([^:\\]+):([1-9][0-9]*)", value)
    if not match:
        raise ValueError(f"invalid repository-relative anchor: {value}")
    path = match[1]
    if path.startswith(("/", "~")) or any(part in {"", ".", ".."} for part in path.split("/")):
        raise ValueError(f"invalid repository-relative anchor: {value}")
    return value


def identity(value, writer=False):
    fields = {}
    for field in value.split(" · "):
        key, sep, item = field.partition(": " if field.startswith("status:") else "=")
        if not sep or not item.strip() or key in fields:
            raise ValueError("invalid or repeated identity field")
        fields[key] = item
    required = {"runtime", "effort"} if writer else {"seat", "runtime", "status"}
    masked = "model-state" in fields or "model-evidence" in fields
    required |= {"model-state", "model-evidence"} if masked else {"model"}
    optional = set() if masked else {"model-version"}
    if not required <= fields.keys() or fields.keys() - required - optional:
        raise ValueError("missing or unexpected identity field")
    if masked:
        if fields["model-state"] != "runtime-masked":
            raise ValueError("model-state must be runtime-masked")
        anchor(fields["model-evidence"])
    else:
        model = fields["model"]
        if not re.fullmatch(r"[^\s/<>]+/[^\s<>]+", model) or model.lower().endswith("/unknown"):
            raise ValueError("model must be the verbatim provider-qualified id, never a placeholder")
    if not writer and fields["status"] not in {"ran", "failed", "skipped"}:
        raise ValueError("reviewer status must be ran, failed or skipped")
    return fields


def parse_record(text):
    """Parse only reserved fact lines; contextual prose is deliberately opaque."""
    record = {"reviewers": [], "defect_confirmed": []}
    current = None
    lines = text.splitlines()
    if not lines or lines[0] != "kind: review-attribution":
        raise ValueError("first line must be kind: review-attribution")
    for number, line in enumerate(lines, 1):
        fact = FACT.match(line)
        if not fact:
            continue
        try:
            field = fact[1]
            for required in ("kind", "pr", "writer"):
                if required not in record:
                    if field != required:
                        raise ValueError("fact order requires kind, pr, writer before reviewers")
                    break
            if line == "kind: review-attribution" and "kind" not in record:
                record["kind"] = "review-attribution"
            elif line.startswith("pr: ") and "pr" not in record:
                match = re.fullmatch(r"pr: ([1-9][0-9]*) · merged (\d{4}-\d{2}-\d{2}) · project: (\S.*)", line)
                if not match:
                    raise ValueError("invalid pr line")
                datetime.date.fromisoformat(match[2])
                record.update(pr=int(match[1]), merged=match[2], project=match[3])
            elif line.startswith("writer: ") and "writer" not in record:
                record["writer"] = identity(line[8:], writer=True)
                current = None
            elif line.startswith("reviewer: "):
                current = identity(line[10:])
                current["findings"] = []
                record["reviewers"].append(current)
            elif line.startswith("  finding: "):
                match = re.fullmatch(r"  finding: (verifiable|consider) · (.+) · adopted: (yes|no)", line)
                if not match or current is None or current["status"] != "ran":
                    raise ValueError("invalid finding or finding without a ran reviewer")
                key = anchor(match[2])
                if any(f["anchor"] == key for f in current["findings"]):
                    raise ValueError("duplicate finding within one reviewer attempt")
                current["findings"].append({"category": match[1], "anchor": key, "adopted": match[3] == "yes"})
            elif line.startswith("defect-confirmed: "):
                match = re.fullmatch(r"defect-confirmed: (.+) · source: post-merge-fix · pr: ([1-9][0-9]*)", line)
                if not match:
                    raise ValueError("invalid defect-confirmed line")
                record["defect_confirmed"].append({"anchor": anchor(match[1]), "source": "post-merge-fix", "pr": int(match[2])})
                current = None
            else:
                raise ValueError("malformed or repeated fact line")
        except ValueError as error:
            raise ValueError(f"line {number}: {error}") from error
    if not {"kind", "pr", "writer"} <= record.keys() or not record["reviewers"]:
        raise ValueError("record requires kind, pr, writer and named reviewers")
    labels = {f["anchor"] for reviewer in record["reviewers"] for f in reviewer["findings"] if f["adopted"]}
    labels.update(event["anchor"] for event in record["defect_confirmed"])
    record["defect_labels"] = sorted(labels)
    return record


def runtime_masked(record):
    """A single masked identity makes the whole game model-unattributable."""
    return any(identity.get("model-state") == "runtime-masked"
               for identity in [record["writer"], *record["reviewers"]])


def capture_record(text, record, repository, audience):
    helper = Path(__file__).resolve().with_name("memory-capture.sh")
    result = subprocess.run([str(helper), str(repository), audience, f"review-attribution-pr{record['pr']}"],
                            input=text, text=True, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "memory capture failed")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", type=Path, help="record file; default stdin")
    parser.add_argument("--capture", type=Path, metavar="PROJECT", help="validate stdin and capture in this project")
    parser.add_argument("--audience", choices=("public", "private"), help="explicit audience judgment for capture")
    args = parser.parse_args()
    if args.capture and (args.record or not args.audience):
        parser.error("--capture requires stdin and an explicit --audience")
    if args.audience and not args.capture:
        parser.error("--audience requires --capture")
    try:
        text = args.record.read_text() if args.record else sys.stdin.read()
        record = parse_record(text)
        if args.capture:
            LOG.info("%s", capture_record(text, record, args.capture, args.audience))
        else:
            sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
    except (ValueError, OSError) as error:
        LOG.error("attribution-record: %s", error)
        return 1
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    sys.exit(main())

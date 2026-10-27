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

import forge  # same directory: the script dir is on sys.path

LOG = logging.getLogger(__name__)
FACT = re.compile(r"^\s*(kind|pr|writer|reviewer|finding|defect-confirmed)\s*:")
# Per-PR block fields (ticket 1149). "not-stated" is the one spelling of an unstated effort
# or independence basis; effort for a native subagent is a requested value or not-stated,
# never an observation.
WRITER_STEPS = {"plan", "execute", "roar"}
REVIEWER_STEPS = {"review", "gate"}
INDEPENDENCE = {"same-family", "cross-family", "not-stated"}
STRICT_FIELDS = {"step", "effort", "route", "independence"}
TOKEN = re.compile(r"[^\s·=:]+")


class MissingBlock(ValueError):
    """The PR body carries no attribution block."""


def anchor(value):
    """Keep the literal join key; reject ambiguous or escaping paths."""
    match = re.fullmatch(r"([^:\\]+):([1-9][0-9]*)", value)
    if not match:
        raise ValueError(f"invalid repository-relative anchor: {value}")
    path = match[1]
    if path.startswith(("/", "~")) or any(part in {"", ".", ".."} for part in path.split("/")):
        raise ValueError(f"invalid repository-relative anchor: {value}")
    return value


def identity(value, writer=False, strict=False):
    fields = {}
    for field in value.split(" · "):
        key, sep, item = field.partition(": " if field.startswith("status:") else "=")
        if not sep or not item.strip() or key in fields:
            raise ValueError("invalid or repeated identity field")
        fields[key] = item
    required = {"runtime", "effort"} if writer else {"seat", "runtime", "status"}
    masked = "model-state" in fields or "model-evidence" in fields
    required |= {"model-state", "model-evidence"} if masked else {"model"}
    optional = {"step", "effort", "route", "independence"} | (set() if masked else {"model-version"})
    if not required <= fields.keys() or fields.keys() - required - optional:
        raise ValueError("missing or unexpected identity field")
    if strict and not STRICT_FIELDS <= fields.keys():
        raise ValueError("strict identity requires " + ", ".join(sorted(STRICT_FIELDS - fields.keys())))
    for key in ("effort", "route"):
        if key in fields and not TOKEN.fullmatch(fields[key]):
            raise ValueError(f"{key} must be one token (use not-stated for an unstated value)")
    if fields.get("independence", "not-stated") not in INDEPENDENCE:
        raise ValueError("independence must be same-family, cross-family or not-stated")
    if "step" in fields and fields["step"] not in (WRITER_STEPS if writer else REVIEWER_STEPS):
        raise ValueError("step not valid for a " + ("writer" if writer else "reviewer") + " line")
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


def parse_record(text, strict=False):
    """Parse only reserved fact lines; contextual prose is deliberately opaque."""
    record = {"reviewers": [], "defect_confirmed": [], "steps": []}
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
                match = re.fullmatch(r"pr: ([1-9][0-9]*) · merged (\d{4}-\d{2}-\d{2}|pending) · project: (\S.*)", line)
                if not match or (match[2] == "pending" and not strict):
                    raise ValueError("invalid pr line")
                if match[2] != "pending":
                    datetime.date.fromisoformat(match[2])
                record.update(pr=int(match[1]), merged=match[2], project=match[3])
            elif line.startswith("writer: "):
                writer = identity(line[8:], writer=True, strict=strict)
                step = writer.get("step")
                if record["steps"] and (step is None or any(w.get("step") in {None, step} for w in record["steps"])):
                    raise ValueError("repeated writer line needs a distinct step=")
                record["steps"].append(writer)
                if "writer" not in record or step == "execute":
                    record["writer"] = writer
                current = None
            elif line.startswith("reviewer: "):
                current = identity(line[10:], strict=strict)
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
    if strict and not any(w.get("step") == "execute" for w in record["steps"]):
        raise ValueError("strict record requires a writer line with step=execute")
    labels = {f["anchor"] for reviewer in record["reviewers"] for f in reviewer["findings"] if f["adopted"]}
    labels.update(event["anchor"] for event in record["defect_confirmed"])
    record["defect_labels"] = sorted(labels)
    return record


def parse_pr_body(body):
    """Parse the single fenced attribution block of a PR body in strict mode."""
    blocks, inside, open_at = [], None, 0
    for number, line in enumerate(body.splitlines(), 1):
        if inside is None:
            if re.fullmatch(r"```attribution\s*", line):
                inside, open_at = [], number
        elif re.fullmatch(r"```\s*", line):
            blocks.append(inside)
            inside = None
        else:
            inside.append(line)
    if inside is not None:
        raise ValueError(f"attribution block opened at line {open_at} is never closed")
    if not blocks:
        raise MissingBlock("no fenced attribution block")
    if len(blocks) > 1:
        raise ValueError(f"{len(blocks)} attribution blocks; exactly one is allowed")
    return parse_record("\n".join(blocks[0]) + "\n", strict=True)


def runtime_masked(record):
    """A single masked identity makes the whole game model-unattributable."""
    return any(identity.get("model-state") == "runtime-masked"
               for identity in [*(record.get("steps") or [record["writer"]]), *record["reviewers"]])


def capture_record(text, record, repository, audience):
    helper = Path(__file__).resolve().with_name("memory-capture.sh")
    result = subprocess.run([str(helper), str(repository), audience, f"review-attribution-pr{record['pr']}"],
                            input=text, text=True, capture_output=True)
    if result.returncode:
        raise ValueError(result.stderr.strip() or "memory capture failed")
    return result.stdout.strip()


OPEN = re.compile(r"```attribution\s*")
CLOSE = re.compile(r"```\s*")


def append_line(body, line, pr=None, project=None):
    """Return the PR body with LINE (one or more lines) appended inside the attribution block.

    The block is created, closed and at column 0, when the body has none; the same
    fence shapes parse_pr_body reads, so writer and reader agree (ticket 1151).
    """
    line = line.strip("\n")
    if not line.strip():
        raise ValueError("nothing to append")
    lines = body.splitlines()
    opens = [i for i, text in enumerate(lines) if OPEN.fullmatch(text)]
    if not opens:
        if pr is None or not project:
            raise ValueError("the body has no attribution block: --pr and --project are needed to create it")
        header = ["```attribution", "kind: review-attribution", f"pr: {int(pr)} · merged pending · project: {project}"]
        lead = [*lines, ""] if lines else []
        return "\n".join([*lead, *header, line, "```"]) + "\n"
    if len(opens) > 1:
        raise ValueError(f"{len(opens)} attribution blocks; exactly one is allowed")
    for i in range(opens[0] + 1, len(lines)):
        if CLOSE.fullmatch(lines[i]):
            return "\n".join([*lines[:i], line, *lines[i:]]) + "\n"
    raise ValueError(f"attribution block opened at line {opens[0] + 1} is never closed")


def extract_record(body, merged):
    """Return the block as a lenient, capturable record with `pending` replaced by the merge date."""
    datetime.date.fromisoformat(merged)
    parse_pr_body(body)  # strict: exactly one closed block, every line well formed
    inside, text = False, []
    for line in body.splitlines():
        if not inside:
            inside = bool(OPEN.fullmatch(line))
        elif CLOSE.fullmatch(line):
            break
        else:
            text.append(line)
    text = "\n".join(text) + "\n"
    text = re.sub(r"^(pr: [1-9][0-9]* · merged )pending", rf"\g<1>{merged}", text, count=1, flags=re.M)
    parse_record(text)  # what --capture will accept
    return text


def forge_for(pr):
    """The forge adapter for request `pr` (scripts/forge.py, the one door to the forge)."""
    return forge.get_forge(None, str(pr))


def forge_call(call, *args, **kwargs):
    """Run an adapter operation; the adapter's refusal is this module's ValueError."""
    try:
        return call(*args, **kwargs)
    except forge.ForgeRefusal as exc:
        raise ValueError(str(exc)) from exc


def append_to_pr(pr, line, project):
    """Append to the live PR body, read back, and retry once if the line is missing.

    The forge has no compare-and-swap: a concurrent whole-body PATCH can drop the line,
    so every attempt re-fetches the body and the read-back is the only evidence
    (the adapter's append_body_line; `edit` writes into the attribution block). The extra "\n"
    keeps the body bytes the gh `--jq` read produced before the move (ticket 1272, a pure move).
    """
    forge_call(forge_for(pr).append_body_line, str(pr), line,
               edit=lambda body: append_line(body + "\n", line, pr=pr, project=project))


SEAT = re.compile(r"seat: ([^·=:]*[^\s·=:]) · runtime=(\S+) · family=(\S+) · route=(\S+) · model=([^·]+?) · status: (ran|failed|skipped)")
NOT_OBSERVED = "not observed"


def seat_lines(results, body, masked_evidence=None):
    """Return (reviewer lines to append, capture failures) from gaze result comments (ticket 1155).

    Every `seat:` line of the results is one review attempt. A seat the body's block already
    carries (gaze appends live, ticket 1151) is not repeated; a body seat the list misses, a
    list with no seat, or an unobserved model without --masked-evidence is a capture failure.
    """
    seats, failures = [], []
    for line in results.splitlines():
        if line.startswith("seat: "):
            match = SEAT.fullmatch(line.strip())
            if match:
                seats.append(match.groups())
            else:
                failures.append(f"malformed seat line: {line}")
    if not seats:
        return [], failures + ["the review result lists no seat"]
    present = {}
    for line in body.splitlines():
        if line.startswith("reviewer: step=review · "):
            name = identity(line[10:]).get("seat")
            present[name] = present.get(name, 0) + 1
    lines = []
    for seat, runtime, _family, route, model, status in seats:
        if present.get(seat):
            present[seat] -= 1
            continue
        if model != NOT_OBSERVED:
            model_field = f"model={model}"
        elif masked_evidence:
            model_field = f"model-state=runtime-masked · model-evidence={masked_evidence}"
        else:
            failures.append(f"seat {seat}: model not observed (pass --masked-evidence path:line)")
            continue
        line = (f"reviewer: step=review · seat={seat} · runtime={runtime} · {model_field}"
                f" · effort=not-stated · route={route} · independence=not-stated · status: {status}")
        try:
            identity(line[10:], strict=True)
        except ValueError as error:
            failures.append(f"seat {seat}: {error}")
            continue
        lines.append(line)
    failures += [f"seat {name} is in the PR body but not in the review result" for name, n in present.items() if n]
    return lines, failures


def append_seats(args):
    """--seats FILE prints the stdin body with the lines; --seats-pr PR edits the live body."""
    if args.seats_pr:
        fg = forge_for(args.seats_pr)
        results = "\n".join(c.get("body", "") for c in forge_call(fg.comments, str(args.seats_pr), reviews=False)
                            if c.get("body", "").startswith("## /gaze result"))
        body = forge_call(fg.resolve, str(args.seats_pr))["body"]
    else:
        results, body = args.seats.read_text(), sys.stdin.read()
    lines, failures = seat_lines(results, body, args.masked_evidence)
    for failure in failures:
        LOG.error("attribution-record: capture failure: %s", failure)
    if args.seats_pr:
        if lines:
            append_to_pr(args.seats_pr, "\n".join(lines), args.project)
    else:
        sys.stdout.write(append_line(body, "\n".join(lines), args.pr, args.project) if lines else body)
    return 1 if failures else 0


def capture_pr(args):
    """--capture-pr PR: seats, extract and capture of one merged PR in a single call.

    Nothing is captured while a seat fails: the body keeps what was appended, and a
    rerun skips those seats, so fixing the cause (often --masked-evidence) and rerunning
    resumes where it stopped.
    """
    pr = args.capture_pr
    fg = forge_for(pr)
    state = forge_call(fg.resolve, str(pr)).get("state")
    merged_at = forge_call(fg.merged_at, str(pr)) if state == "MERGED" else None
    if state != "MERGED" or not merged_at:
        raise ValueError(f"PR #{pr} is {state}, not merged")
    args.seats, args.seats_pr = None, pr
    if append_seats(args):
        LOG.error("attribution-record: PR #%s not captured; fix the failures above and rerun", pr)
        return 1
    body = forge_call(fg.resolve, str(pr))["body"]
    text = extract_record(body, merged_at[:10])
    LOG.info("%s", capture_record(text, parse_record(text), args.capture, args.audience))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", type=Path, help="record file; default stdin")
    parser.add_argument("--capture", type=Path, metavar="PROJECT", help="validate stdin and capture in this project")
    parser.add_argument("--audience", choices=("public", "private"), help="explicit audience judgment for capture")
    parser.add_argument("--pr-body", action="store_true",
                        help="read a PR body from stdin; print ok, missing or invalid: <reason> (exit 0 only on ok)")
    parser.add_argument("--append", metavar="LINE", help="read a PR body on stdin, print it with LINE added to the attribution block (created if absent)")
    parser.add_argument("--append-pr", type=int, metavar="PR", help="with --append: edit the live PR body through gh, read back, retry once")
    parser.add_argument("--pr", type=int, help="PR number for a block --append creates")
    parser.add_argument("--project", help="project name for a block --append creates")
    parser.add_argument("--extract", action="store_true",
                        help="read a merged PR body on stdin, print its block as a record for --capture (needs --merged)")
    parser.add_argument("--merged", metavar="DATE", help="merge date (YYYY-MM-DD) replacing pending in --extract")
    parser.add_argument("--seats", type=Path, metavar="RESULT",
                        help="gaze result comment(s) file; print the stdin PR body with the seats' reviewer lines added")
    parser.add_argument("--seats-pr", type=int, metavar="PR",
                        help="as --seats, reading the PR's gaze result comments and editing its live body")
    parser.add_argument("--masked-evidence", metavar="PATH:LINE",
                        help="with --seats: evidence anchor for seats whose model was not observed")
    parser.add_argument("--capture-pr", type=int, metavar="PR",
                        help="one call for a merged PR: --seats-pr, then --extract with its merge date, then --capture"
                             " (needs --capture PROJECT and --audience)")
    args = parser.parse_args()
    if args.capture_pr:
        if not args.capture or not args.audience or args.record or args.seats or args.seats_pr \
                or args.pr_body or args.append is not None or args.extract or args.merged:
            parser.error("--capture-pr needs --capture PROJECT and --audience, and takes no other mode")
        try:
            return capture_pr(args)
        except ValueError as error:
            LOG.error("attribution-record: %s", error)
            return 1
    if args.seats or args.seats_pr:
        if args.record or args.capture or args.pr_body or args.append is not None or args.extract:
            parser.error("--seats takes no other mode")
        try:
            return append_seats(args)
        except ValueError as error:
            LOG.error("attribution-record: %s", error)
            return 1
    if args.append is not None or args.extract:
        if args.record or args.capture or args.audience or args.pr_body or (args.append is not None and args.extract):
            parser.error("--append and --extract take no other mode")
        try:
            if args.extract:
                if not args.merged:
                    parser.error("--extract requires --merged DATE")
                sys.stdout.write(extract_record(sys.stdin.read(), args.merged))
            elif args.append_pr:
                append_to_pr(args.append_pr, args.append, args.project)
            else:
                sys.stdout.write(append_line(sys.stdin.read(), args.append, args.pr, args.project))
        except ValueError as error:
            LOG.error("attribution-record: %s", error)
            return 1
        return 0
    if args.append_pr or args.merged:
        parser.error("--append-pr needs --append; --merged needs --extract")
    if args.pr_body:
        if args.record or args.capture or args.audience:
            parser.error("--pr-body reads stdin and takes no other mode")
        try:
            parse_pr_body(sys.stdin.read())
        except MissingBlock:
            sys.stdout.write("missing\n")
            return 1
        except ValueError as error:
            sys.stdout.write(f"invalid: {error}\n")
            return 1
        sys.stdout.write("ok\n")
        return 0
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

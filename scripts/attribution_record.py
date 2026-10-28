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
import review_notes

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
                # a no-forge unit has no number: `pr: branch:<name>` (ticket 1307)
                match = re.fullmatch(r"pr: ([1-9][0-9]*|branch:[^\s·]+) · merged (\d{4}-\d{2}-\d{2}|pending) · project: (\S.*)", line)
                if not match or (match[2] == "pending" and not strict):
                    raise ValueError("invalid pr line")
                if match[2] != "pending":
                    datetime.date.fromisoformat(match[2])
                record.update(pr=int(match[1]) if match[1].isdigit() else match[1], merged=match[2], project=match[3])
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


def capture_slug(record):
    """The journal slug: `review-attribution-pr<n>`, or `-branch-<name>` for a no-forge unit."""
    pr = record["pr"]
    if isinstance(pr, int):
        return f"review-attribution-pr{pr}"
    return "review-attribution-branch-" + re.sub(r"[^A-Za-z0-9._-]+", "-", pr[len("branch:"):])


def capture_record(text, record, repository, audience):
    helper = Path(__file__).resolve().with_name("memory-capture.sh")
    result = subprocess.run([str(helper), str(repository), audience, capture_slug(record)],
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
            at = i
            if line.startswith("writer: "):  # facts order: kind, pr, writers, then reviewers (ticket 1286)
                first = next((j for j in range(opens[0] + 1, i) if lines[j].startswith("reviewer: ")), None)
                at = i if first is None else first
            return "\n".join([*lines[:at], line, *lines[at:]]) + "\n"
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
    """Return (reviewer lines to append, capture failures) from gaze results (ticket 1155).

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
            try:
                name = identity(line[10:]).get("seat")
            except ValueError as error:  # a hand-typed line (PR #1855): reported, never fatal
                failures.append(f"malformed reviewer line in the PR body ({error}): {line}")
                continue
            present[name] = present.get(name, 0) + 1
    lines = []
    for seat, runtime, family, route, model, status in seats:
        if present.get(seat):
            present[seat] -= 1
            continue
        if model != NOT_OBSERVED:
            # gaze writes the id as the worker reported it, often bare beside its family
            # (PRs #1852, #1855): the family is the provider prefix the record requires.
            model_field = f"model={model if '/' in model else family.lower() + '/' + model}"
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


def review_results(pr, fg, cwd="."):
    """The gaze results of PR `pr`: its review's notes answers (ticket 1301), resolved after a
    refresh. No review on notes: a merged PR predates the switch, so its `## /gaze result`
    comments are read as history; an open one is refused (re-gaze it), never read from comments.
    A stale read with nothing local is a refusal too."""
    try:
        rid = review_notes.resolve_unit(cwd, f"pr:{int(pr)}")
    except review_notes.Refusal as exc:
        raise ValueError(f"PR #{pr}: {exc}") from exc
    if rid:
        return "\n".join(review_notes.answer_texts(cwd, rid))
    state = forge_call(fg.resolve, str(pr)).get("state")
    if state != "MERGED":
        raise ValueError(f"PR #{pr} has no review on notes (state {state}): re-gaze it; "
                         "PR comments are read only for merged pre-switch PRs")
    return "\n".join(c.get("body", "") for c in forge_call(fg.comments, str(pr), reviews=False)
                     if c.get("body", "").startswith("## /gaze result"))


# --- notes: the one attribution record (ticket 1307) -----------------------------------------
# Writer lines are `writer` entries of the review, reviewer lines ride in each gaze answer's
# `attribution` field. The block is assembled from them for landing and for roar's capture;
# the review path writes nothing to a PR body.

ENTRY_ATTRIBUTION = ("answer", "verdict")  # entries whose `attribution` lines join the block


def split_unit(unit):
    """(kind, key, base): `pr:<n>` or a bare number -> ("pr", "<n>", None); `branch:<name>
    [base=<ref>]` -> ("branch", name, ref or None); an `rv-` review id -> ("review", id, None)."""
    unit = str(unit).strip()
    if re.fullmatch(r"(pr:)?#?[1-9][0-9]*", unit):
        return "pr", re.sub(r"\D", "", unit), None
    m = re.fullmatch(r"branch:(\S+?)(?:\s+base=(\S+))?", unit)
    if m:
        return "branch", m[1], m[2]
    if unit.startswith("rv-"):
        return "review", unit, None
    raise ValueError(f"unknown unit {unit!r} (pr:<n>, branch:<name> or a review id)")


def review_for(cwd, unit):
    """The review id of `unit` from the local notes ref only: no fetch, no forge (find_unit
    for a PR, find for a branch, which skips PR reviews). None when there is none."""
    kind, key, _ = split_unit(unit)
    if kind == "review":
        return key if review_notes.entries(cwd, key) else None
    return review_notes.find_unit(cwd, f"pr:{key}") if kind == "pr" else review_notes.find(cwd, key)


def _git_out(cwd, *args):
    done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return done.stdout.strip() if done.returncode == 0 else ""


def record_writer(cwd, line, unit, branch=None, base_ref=None, skill="raid"):
    """Append one `writer:` line to the unit's review on notes, locally: no fetch, no push, no
    forge call. A unit with no review yet gets one opened on the branch head (a PR unit keeps
    `unit: pr:<n>`, so gaze_setup finds it), with the request's What read from the local
    repository path. Returns the review id; a malformed line raises ValueError."""
    if not line.startswith("writer: "):
        raise ValueError("a writer line starts with `writer: `")
    identity(line[len("writer: "):], writer=True, strict=True)
    kind, key, base = split_unit(unit)
    try:
        rid = review_for(cwd, unit)
        if not rid:
            if kind == "review":
                raise ValueError(f"no review {key} on notes")
            branch = branch or (key if kind == "branch" else _git_out(cwd, "rev-parse", "--abbrev-ref", "HEAD"))
            if not branch or branch == "HEAD":
                raise ValueError("no review yet and no branch to open one on (pass --branch)")
            base_ref = base_ref or base or ("origin/main" if _git_out(cwd, "rev-parse", "-q", "--verify",
                                                                       "refs/remotes/origin/main") else "main")
            rid = review_notes.open_review(cwd, branch, base_ref, unit=f"pr:{key}" if kind == "pr" else None,
                                           skill=skill, remote="", why="writer attribution before any review")
        review_notes.add(cwd, "writer", rid, {"line": line}, skill=skill)
    except review_notes.Refusal as exc:
        raise ValueError(str(exc)) from exc
    return rid


STEP_ORDER = ("plan", "execute", "roar")


def notes_record(cwd, review_id, project, merged="pending"):
    """The record text of a review, from notes: the header, the latest writer line per step,
    then every answer's (and verdict's) attribution lines in order, one block per attempt."""
    entries = review_notes.entries(cwd, review_id)
    requests = [e for e in entries if e["kind"] == "request"]
    if not requests:
        raise ValueError(f"review {review_id} has no request")
    unit = next((e["unit"] for e in reversed(requests) if e.get("unit")), None)
    pr = unit[len("pr:"):] if unit else f"branch:{requests[-1]['branch']}"
    writers = {}
    for e in entries:
        if e["kind"] == "writer" and e.get("line"):
            step = re.search(r"\bstep=(\S+)", e["line"])
            writers[step[1] if step else ""] = e["line"]
    ordered = [writers[k] for k in STEP_ORDER if k in writers] + \
              [v for k, v in writers.items() if k not in STEP_ORDER]
    reviewers = [ln for e in entries if e["kind"] in ENTRY_ATTRIBUTION for ln in e.get("attribution") or []]
    lines = ["kind: review-attribution", f"pr: {pr} · merged {merged} · project: {project}", *ordered, *reviewers]
    return "\n".join(lines) + "\n"


def notes_block(cwd, unit, project):
    """(text, status) of the unit's block on notes: status `ok`, `missing` (no review) or
    `invalid: <reason>` (the strict parser's); text only when ok. Local reads only."""
    try:
        rid = review_for(cwd, unit)
        if not rid:
            return None, "missing"
        text = notes_record(cwd, rid, project)
        parse_record(text, strict=True)
    except (ValueError, review_notes.Refusal) as exc:
        return None, f"invalid: {exc}"
    return text, "ok"


def put_block(body, text):
    """The body with its attribution block replaced by `text` (one fenced block), or with the
    block appended when it has none. The rest of the body, close claims included, is kept."""
    lines, out, i = body.splitlines(), [], 0
    fenced = ["```attribution", *text.rstrip("\n").splitlines(), "```"]
    placed = False
    while i < len(lines):
        if OPEN.fullmatch(lines[i]):
            end = next((j for j in range(i + 1, len(lines)) if CLOSE.fullmatch(lines[j])), None)
            if end is None:
                raise ValueError(f"attribution block opened at line {i + 1} is never closed")
            if not placed:
                out += fenced
                placed = True
            i = end + 1
            continue
        out.append(lines[i])
        i += 1
    if not placed:
        out += ([""] if out and out[-1].strip() else []) + fenced
    return "\n".join(out) + "\n"


def render_to_pr(pr, text, fg=None):
    """Landing (raid_land, merge step 5a): write the notes block into the PR body in one edit,
    read back by the adapter (append_body_line with a whole-block `edit`). The one render path:
    raid_land passes its own adapter as `fg`."""
    forge_call((fg or forge_for(pr)).append_body_line, str(pr), text.rstrip("\n"),
               edit=lambda body: put_block(body, text))


def landing_date(cwd, review_id, base=None):
    """The committer date of the merge that landed a no-forge unit, read from evidence that
    survives `raid_land --cleanup` deleting the branch: the review's latest retained request
    head and the oldest merge on the base's first-parent chain that descends from it. None
    when no such merge exists."""
    requests = [e for e in review_notes.entries(cwd, review_id) if e["kind"] == "request"]
    if not requests:
        return None
    head, base_ref = requests[-1]["head"], base or requests[-1].get("base_ref") or "main"
    for ref in dict.fromkeys([base_ref, base_ref.removeprefix("origin/")]):
        dates = _git_out(cwd, "log", "--ancestry-path", "--first-parent", "--merges",
                         "--format=%cs", f"{head}..{ref}").splitlines()
        if dates:
            return dates[-1]
    return None


def merged_date(cwd, unit):
    """The merge date (YYYY-MM-DD) of a landed unit: the forge's for a PR; with no forge, the
    landing merge commit's, found from the review's retained head (the branch may be gone)."""
    kind, key, base = split_unit(unit)
    if kind == "review":
        raise ValueError("capture takes a pr:<n> or branch:<name> unit, not a review id")
    if kind == "branch":
        rid = review_for(cwd, unit)
        return landing_date(cwd, rid, base) if rid else None
    at = forge_call(forge_for(key).merged_at, key)
    return at[:10] if at else None


def capture_unit(args):
    """--capture-unit UNIT: the block from notes, its merge date, validated, captured."""
    cwd = "."
    merged = merged_date(cwd, args.capture_unit)
    if not merged:
        raise ValueError(f"{args.capture_unit} is not merged")
    rid = review_for(cwd, args.capture_unit)
    if not rid:
        raise ValueError(f"{args.capture_unit} has no review on notes (a pre-switch PR: --capture-pr)")
    project = args.project or Path(_git_out(cwd, "rev-parse", "--path-format=absolute",
                                            "--git-common-dir") or "./.git").parent.name
    text = notes_record(cwd, rid, project, merged)
    LOG.info("%s", capture_record(text, parse_record(text), args.capture, args.audience))
    return 0


def append_seats(args):
    """--seats FILE prints the stdin body with the lines; --seats-pr PR edits the live body."""
    if args.seats_pr:
        fg = forge_for(args.seats_pr)
        results = review_results(args.seats_pr, fg)
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


def notes_main(parser, args):
    """--record-writer, --from-notes, --render-pr and --capture-unit: the notes modes (ticket 1307)."""
    modes = [m for m in (args.record_writer is not None, bool(args.from_notes), bool(args.capture_unit),
                         bool(args.render_pr)) if m]
    others = (args.record or args.pr_body or args.append is not None or args.extract or args.seats
              or args.seats_pr or args.capture_pr)
    if len(modes) > 1 or others:
        parser.error("--record-writer, --from-notes, --render-pr and --capture-unit take no other mode")
    try:
        if args.record_writer is not None:
            if not args.unit:
                parser.error("--record-writer needs --unit pr:<n> or branch:<name>")
            print(record_writer(".", args.record_writer, args.unit, args.branch, args.base_ref, args.skill))
            return 0
        if args.from_notes or args.render_pr:
            project = args.project or Path(_git_out(".", "rev-parse", "--path-format=absolute",
                                                    "--git-common-dir") or "./.git").parent.name
            text, status = notes_block(".", args.from_notes or f"pr:{args.render_pr}", project)
            if args.from_notes or not text:
                sys.stdout.write(text if text else status + "\n")
                return 0 if text else 1
            render_to_pr(args.render_pr, text)
            sys.stdout.write("rendered\n")
            return 0
        if not args.capture or not args.audience:
            parser.error("--capture-unit needs --capture PROJECT and --audience")
        return capture_unit(args)
    except ValueError as error:
        LOG.error("attribution-record: %s", error)
        return 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", nargs="?", type=Path, help="record file; default stdin")
    parser.add_argument("--capture", type=Path, metavar="PROJECT", help="validate stdin and capture in this project")
    parser.add_argument("--audience", choices=("public", "private"), help="explicit audience judgment for capture")
    parser.add_argument("--pr-body", action="store_true",
                        help="read a PR body from stdin; print ok, missing or invalid: <reason> (exit 0 only on ok)")
    parser.add_argument("--append", metavar="LINE", help="read a PR body on stdin, print it with LINE added to the attribution block (created if absent)")
    parser.add_argument("--pr", type=int, help="PR number for a block --append creates")
    parser.add_argument("--project", help="project name for a block --append creates")
    parser.add_argument("--extract", action="store_true",
                        help="read a merged PR body on stdin, print its block as a record for --capture (needs --merged)")
    parser.add_argument("--merged", metavar="DATE", help="merge date (YYYY-MM-DD) replacing pending in --extract")
    parser.add_argument("--seats", type=Path, metavar="RESULT",
                        help="gaze result comment(s) file; print the stdin PR body with the seats' reviewer lines added")
    parser.add_argument("--seats-pr", type=int, metavar="PR",
                        help="as --seats, reading the PR review's notes answers (merged pre-switch PRs: "
                             "the gaze result comments) and editing its live body")
    parser.add_argument("--masked-evidence", metavar="PATH:LINE",
                        help="with --seats: evidence anchor for seats whose model was not observed")
    parser.add_argument("--capture-pr", type=int, metavar="PR",
                        help="one call for a merged PR: --seats-pr, then --extract with its merge date, then --capture"
                             " (needs --capture PROJECT and --audience)")
    parser.add_argument("--record-writer", metavar="LINE",
                        help="append a writer: line to the --unit's review on notes, locally (ticket 1307)")
    parser.add_argument("--unit", help="with --record-writer: pr:<n> or branch:<name>")
    parser.add_argument("--branch", help="with --record-writer: the branch a review is opened on when the unit has none")
    parser.add_argument("--base-ref", help="with --record-writer: the base of a review it opens (default origin/main)")
    parser.add_argument("--skill", default="raid", help="with --record-writer: the recording skill")
    parser.add_argument("--from-notes", metavar="UNIT",
                        help="print the block of a pr:<n>, branch:<name> or rv- review from notes; "
                             "exit 1 printing missing or invalid: <reason>")
    parser.add_argument("--render-pr", type=int, metavar="PR",
                        help="landing (merge step 5a): write PR's notes block into its body, read back; "
                             "exit 1 is a warning, never a refusal")
    parser.add_argument("--capture-unit", metavar="UNIT",
                        help="capture a merged pr:<n> or branch:<name> unit's block from notes "
                             "(needs --capture PROJECT and --audience)")
    args = parser.parse_args()
    if args.record_writer is not None or args.from_notes or args.capture_unit or args.render_pr:
        return notes_main(parser, args)
    if args.unit or args.branch or args.base_ref:
        parser.error("--unit, --branch and --base-ref go with --record-writer")
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
            else:
                sys.stdout.write(append_line(sys.stdin.read(), args.append, args.pr, args.project))
        except ValueError as error:
            LOG.error("attribution-record: %s", error)
            return 1
        return 0
    if args.merged:
        parser.error("--merged needs --extract")
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

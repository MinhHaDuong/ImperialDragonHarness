#!/usr/bin/env python3
"""Review evidence core: record reports, decide reuse, gate stale or missing proof.

Reports are repository files under `tickets/reviews/<base>..<head>/`, one per
seat execution, written by the controller. A report is reused only while the
five identity inputs hold: the merge base and head it names may move, but the
patch-id of the diff, the ticket's exit-criteria hash and the review policy
version must not change. Check, gate and adherence results are never reused.

Forge-read reviews (human, Copilot) are admitted only from three pinned actor
IDs and only when the forge reports them unedited; anything else fails closed.

Subcommands: `identity`, `record`, `plan`, `gate`, `forge`, `risk-floor`.
Ticket 1142; design in docs/discussions/2026-10-14-1096-design.md.
"""

import argparse
import hashlib
import json
import logging
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from fnmatch import fnmatchcase
from pathlib import Path

REUSE, RERUN, STALE = "reuse", "re-run", "stale"
NEVER_REUSED_KINDS = frozenset({"check", "gate", "adherence"})
KINDS = ("review", *sorted(NEVER_REUSED_KINDS))
VERDICTS = ("approve", "changes", "no-report")
FORMAT = "1"
REVIEWS_DIR = "tickets/reviews"
# A commit that only adds such files under REVIEWS_DIR does not move the identity.
REPORT_SUFFIXES = (".md", ".json", ".txt")
HARNESS_ROOT = Path(__file__).resolve().parents[1]
log = logging.getLogger("review_evidence")

# Forge actors whose reviews may be read as evidence or binding findings:
# the three accounts that posted reviews across 22 repositories in the census
# of 2026-10-14 (docs/discussions/2026-10-14-1096-seats/evidence-review-authors.json).
# Node IDs, not logins: a login can be renamed and re-registered.
FORGE_ACTORS = {
    ("github.com", "MDQ6VXNlcjE4NDc1MjA4"): "human",    # MinhHaDuong
    ("github.com", "BOT_kgDOCnlnWA"): "copilot",        # copilot-pull-request-reviewer
    ("github.com", "BOT_kgDOC9w8XQ"): "copilot",        # copilot-swe-agent
}
FORGE_OBJECTS = frozenset({"PullRequestReview", "PullRequestReviewComment", "IssueComment"})

# Review policy: what a seat's judgment depends on. Not all of rules/.
POLICY_GLOBS = (
    "skills/review-pr/**/*",
    "skills/review-pr-prose/**/*",
    "skills/gaze/**/*",
    "skills/route/references/decorrelation.md",
    "scripts/review_evidence.py",
    "agents/*-seat.md",
    "agents/code-reviewer.md",
    "agents/prose-reviewer.md",
    "agents/gaze-pr-review.md",
    "profiles/*-seat/**/*",
    "profiles/code-reviewer/**/*",
    "profiles/prose-reviewer/**/*",
)

ROWS = ("trivial", "ordinary", "high")
# High-risk classes of skills/route/references/decorrelation.md: rules and
# guards, merge and release gates, credentials, deletion or migration; plus
# the review policy itself and what runs or configures the gates (CI,
# runtime settings, Makefile, agent instructions).
HIGH_RISK_PATHS = re.compile(
    r"^(rules/|hooks/|skills/(merge|verify-gate|verify-adherence|release|gaze|review-pr)/"
    r"|scripts/(guard-|raid-gate|raid_gate|review_evidence)"
    r"|skills/route/references/decorrelation\.md$|profiles/code-reviewer/"
    r"|agents/code-reviewer\.md$|\.github/workflows/|\.claude/settings\.json$)"
    r"|(^|/)(Makefile|AGENTS\.md)$"
    r"|(^|/)guard[^/]*$|credential|secret|(^|/)\.env|(^|/)keys?/",
    re.IGNORECASE)
HIGH_RISK_TEXT = re.compile(
    r"\brules/|\bguards?\b|\bmerge gate|\brelease gate|\bverify-gate\b|\bcredentials?\b"
    r"|\bsecrets?\b|\bapi keys?\b|\bdelet(e|es|ion|ing)\b|\bmigrat(e|es|ion|ing)\b",
    re.IGNORECASE)


@dataclass(frozen=True)
class Inputs:
    base: str
    head: str
    patch_id: str
    criteria_hash: str
    policy_version: str


# --- pure core -------------------------------------------------------------

def decide(record: dict | None, current: Inputs) -> tuple[str, str]:
    """Return (reuse | re-run | stale, reason) for one recorded seat execution.

    `reuse` means the evidence still describes the current diff, whatever its
    verdict: findings on an identical diff stand until the diff changes, so a
    seat that requested changes is not dispatched again on the same patch.
    """
    if record is None:
        return RERUN, "no report"
    if record.get("kind") in NEVER_REUSED_KINDS:
        return RERUN, f"{record['kind']} results are never reused"
    changed = [key for key in ("patch-id", "criteria-hash", "policy-version")
               if record.get(key) != getattr(current, key.replace("-", "_"))]
    if changed:
        return STALE, f"{', '.join(changed)} changed"
    if record.get("verdict") not in ("approve", "changes"):
        return RERUN, "no report"
    origin = record.get("head", "")
    if origin == current.head:
        return REUSE, "same head"
    return REUSE, f"same patch-id, from head {origin[:12]}"


def admit_forge_review(review: dict) -> tuple[bool, str]:
    """Admit a forge-read review by pinned actor; fail closed on anything else.

    Returns (True, role) or (False, reason).
    """
    role = FORGE_ACTORS.get((review.get("forge_host"), review.get("actor_id")))
    if role is None:
        return False, "actor not on the allow-list"
    if review.get("object_type") not in FORGE_OBJECTS:
        return False, f"object type {review.get('object_type')!r} not admitted"
    if review.get("edited") is not False:
        return False, "edited after posting, or edit status unknown"
    return True, role


class ForgeReadError(ValueError):
    """The forge answer is incomplete or unreadable: evidence missing, not rejected."""


def _page(connection: dict, what: str) -> list[dict]:
    """Nodes of one connection; a further page or no page info fails closed."""
    info = connection.get("pageInfo")
    if not isinstance(info, dict) or info.get("hasNextPage") is not False:
        raise ForgeReadError(f"{what}: more than one page or no page info")
    return connection["nodes"]


def classify_forge(payload: dict, host: str) -> list[dict]:
    """Rows `{login, object_type, status, reason, state, commit, resolved}` from a payload.

    Reads reviews, conversation comments and inline review-thread comments.
    Raises ForgeReadError when any of them is truncated.
    """
    try:
        pr = payload["data"]["repository"]["pullRequest"]
        nodes = [(n, None) for n in _page(pr["reviews"], "reviews")]
        nodes += [(n, None) for n in _page(pr["comments"], "comments")]
        for thread in _page(pr["reviewThreads"], "reviewThreads"):
            nodes += [(n, thread.get("isResolved"))
                      for n in _page(thread["comments"], "thread comments")]
    except (KeyError, TypeError) as exc:
        raise ForgeReadError(f"unexpected forge payload: {exc!r}") from exc
    rows = []
    for node, resolved in nodes:
        author = node.get("author") or {}
        ok, why = admit_forge_review({
            "forge_host": host, "actor_id": author.get("id"),
            "object_type": node.get("__typename"),
            # An absent field is unknown edit status: count it as edited.
            "edited": node.get("lastEditedAt", "absent") is not None})
        rows.append({
            "login": author.get("login", "<deleted>"), "object_type": node.get("__typename"),
            "status": f"{why}: ran" if ok else "rejected", "reason": "" if ok else why,
            "state": node.get("state", ""), "commit": (node.get("commit") or {}).get("oid", ""),
            "resolved": resolved})
    return rows


def criteria_hash(ticket_text: str | None) -> str:
    """Hash the Exit criteria section, ignoring checkbox state and other sections."""
    if ticket_text is None:
        return "none"
    match = re.search(r"^## Exit criteria\s*$(.*?)(?=^## |\Z)", ticket_text, re.M | re.S)
    if not match:
        return "none"
    lines = []
    for line in match.group(1).splitlines():
        line = re.sub(r"^-\s*\[[ xX]\]\s*", "- ", line.strip())
        if line:
            lines.append(line)
    return hashlib.sha256("\n".join(lines).encode()).hexdigest()[:16]


def is_policy_path(path: str) -> bool:
    """True when `path` is review policy: the floor must never rate it below high."""
    return any(fnmatchcase(path, g.replace("/**/*", "/*")) for g in POLICY_GLOBS)


def risk_floor(changes: list[tuple[str, str]], ticket_text: str | None) -> dict:
    """The floor is the higher of the path match and the ticket-text match.

    `changes` is (status, path) from a no-rename name-status diff. Deleting a
    non-ticket file counts as deletion; closing a ticket does not.
    """
    def hit(status: str, path: str) -> bool:
        if path.startswith(f"{REVIEWS_DIR}/"):
            return False
        if status == "D" and not path.startswith("tickets/"):
            return True
        return bool(HIGH_RISK_PATHS.search(path)) or is_policy_path(path)
    paths = "high" if any(hit(s, p) for s, p in changes) else "trivial"
    ticket = "high" if ticket_text and HIGH_RISK_TEXT.search(ticket_text) else "trivial"
    floor = max(paths, ticket, key=ROWS.index)
    return {"paths": paths, "ticket": ticket, "floor": floor}


def parse_report(text: str) -> dict:
    """Header fields of a report; an unreadable header returns {}."""
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return {}
    fields = {}
    for line in lines[1:lines.index("---", 1)]:
        key, sep, value = line.partition(": ")
        if not sep or key in fields:  # a repeated key is a forged field
            return {}
        fields[key] = value
    return fields if fields.get("review-evidence") == FORMAT else {}


# --- repository reads ------------------------------------------------------

def git(repo: Path, *args: str, stdin: str | None = None) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True, input=stdin, timeout=60).stdout.strip()


def exempt_paths(repo: Path, base: str, head: str) -> list[str]:
    """Plain report files added under REVIEWS_DIR: outside the reviewed identity."""
    raw = subprocess.run(["git", "-C", str(repo), "diff", "--raw", "-z", "--no-renames",
                          base, head], check=True, capture_output=True, timeout=60).stdout
    fields = raw.decode().split("\0")
    exempt = []
    for meta, path in zip(fields[0::2], fields[1::2]):
        parts = meta.split()
        if (len(parts) == 5 and parts[4] == "A" and parts[1] == "100644"
                and path.startswith(f"{REVIEWS_DIR}/") and path.endswith(REPORT_SUFFIXES)):
            exempt.append(path)
    return exempt


def patch_id(repo: Path, base: str, head: str) -> str:
    """`git patch-id --stable`, joined with the verbatim id so whitespace counts."""
    excludes = [f":(exclude,literal){p}" for p in exempt_paths(repo, base, head)]
    # Raw bytes end to end: stripping the diff would erase whitespace on its last line.
    diff = subprocess.run(
        ["git", "-C", str(repo), "diff", "--binary", "--no-renames", "--no-ext-diff",
         "--no-textconv", base, head, "--", ".", *excludes],
        check=True, capture_output=True, timeout=60).stdout
    if not diff:
        return "empty"
    ids = [subprocess.run(["git", "-C", str(repo), "patch-id", flag], input=diff, check=True,
                          capture_output=True, timeout=60).stdout.split()[0].decode()
           for flag in ("--stable", "--verbatim")]
    return "+".join(ids)


def policy_version(root: Path) -> str:
    digest = hashlib.sha256()
    files = sorted({p for g in POLICY_GLOBS for p in root.glob(g) if p.is_file()})
    for path in files:
        digest.update(f"{path.relative_to(root)}\0".encode())
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()[:16]


def current_inputs(args: argparse.Namespace) -> Inputs:
    head = git(args.repo, "rev-parse", args.head)
    base = git(args.repo, "merge-base", args.base, head)
    ticket = args.ticket.read_text() if args.ticket else None
    return Inputs(base, head, patch_id(args.repo, base, head), criteria_hash(ticket),
                  policy_version(args.policy_root))


def load_reports(repo: Path, head: str) -> list[tuple[Path, dict]]:
    """Reports committed at `head`: regular blobs `REVIEWS_DIR/<range>/<file>.md`.

    The working tree is never read, so an untracked file, a symlink or an
    executable cannot stand in for a recorded report.
    """
    raw = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "-z", head, "--",
                          f"{REVIEWS_DIR}/"], check=True, capture_output=True,
                         timeout=60).stdout.decode()
    out = []
    for entry in filter(None, raw.split("\0")):
        meta, path = entry.split("\t", 1)
        mode, kind, oid = meta.split()
        parts = path.split("/")
        if (mode != "100644" or kind != "blob" or len(parts) != 4
                or not path.endswith(".md")):
            continue
        blob = subprocess.run(["git", "-C", str(repo), "cat-file", "blob", oid], check=True,
                              capture_output=True, timeout=60).stdout
        header = parse_report(blob.decode(errors="replace"))
        if header:
            out.append((Path(path), header))
    return out


def _rank(row: dict) -> tuple[int, int, int]:
    """Order candidate rows: any usable report beats stale beats none; among usable
    reports a `changes` verdict dominates (findings stand), then `ran` beats `reused`.
    Independent of report file order, so seat-10 vs seat-2 cannot mask a verdict."""
    usable = row["status"] in ("ran", "reused")
    return (2 if usable else 1 if row["status"] == "stale" else 0,
            int(usable and row["header"].get("verdict") == "changes"),
            int(row["status"] == "ran"))


def seat_rows(repo: Path, current: Inputs, seats: list[str]) -> list[dict]:
    """Per required seat: ran | reused | stale | no-report, with the backing report."""
    reports = load_reports(repo, current.head)
    rows = []
    for seat in seats:
        best = {"seat": seat, "status": "no-report", "reason": "no report", "path": None,
                "header": {}}
        for path, header in reports:
            if header.get("seat") != seat:
                continue
            action, reason = decide(header, current)
            if action == REUSE:
                status = "ran" if header.get("head") == current.head else "reused"
            elif action == STALE:
                status = "stale"
            else:
                continue
            row = {"seat": seat, "status": status, "reason": reason, "path": path,
                   "header": header}
            if _rank(row) > _rank(best):
                best = row
        rows.append(best)
    return rows


# --- subcommands -----------------------------------------------------------

def name_status(repo: Path, current: Inputs) -> list[tuple[str, str]]:
    """(status, path) pairs, NUL-separated so non-ASCII paths arrive unquoted."""
    raw = subprocess.run(["git", "-C", str(repo), "diff", "--name-status", "-z",
                          "--no-renames", current.base, current.head],
                         check=True, capture_output=True, timeout=60).stdout.decode()
    fields = raw.split("\0")
    return list(zip(fields[0::2], fields[1::2]))


def range_dir(repo: Path, current: Inputs) -> Path:
    short = [git(repo, "rev-parse", "--short=7", sha) for sha in (current.base, current.head)]
    return repo / REVIEWS_DIR / f"{short[0]}..{short[1]}"


def cmd_identity(args: argparse.Namespace) -> int:
    print(json.dumps(current_inputs(args).__dict__, indent=1))
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    current = current_inputs(args)
    folder = range_dir(args.repo, current)
    folder.mkdir(parents=True, exist_ok=True)
    n = 1
    while (folder / f"{args.seat}-{n}.md").exists():
        n += 1
    header = {
        "review-evidence": FORMAT, "kind": args.kind, "seat": args.seat,
        "verdict": args.verdict, "family": args.family.casefold(), "worker": args.worker,
        "base": current.base, "head": current.head, "patch-id": current.patch_id,
        "criteria-hash": current.criteria_hash, "policy-version": current.policy_version,
        "recorded": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    body = sys.stdin.read()
    path = folder / f"{args.seat}-{n}.md"
    path.write_text("---\n" + "".join(f"{k}: {v}\n" for k, v in header.items())
                    + "---\n\n" + body)
    print(path)
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    current = current_inputs(args)
    rows = seat_rows(args.repo, current, args.seat)
    print(json.dumps({
        "head": current.head,
        "dispatch": [r["seat"] for r in rows if r["status"] in ("stale", "no-report")],
        "seats": {r["seat"]: {"status": r["status"], "reason": r["reason"]} for r in rows},
    }, indent=1))
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    current = current_inputs(args)
    seats = list(dict.fromkeys(args.seat + (["red-team"] if args.risk == "high" else [])))
    rows = seat_rows(args.repo, current, seats)
    ok = True
    print(f"REVIEW-EVIDENCE: base {current.base} head {current.head} "
          f"patch-id {current.patch_id} criteria-hash {current.criteria_hash} "
          f"policy-version {current.policy_version}")
    for r in rows:
        where = f" {r['path']}" if r["path"] else ""
        verdict = f" ({r['header'].get('verdict', '?')})" if r["header"] else ""
        print(f"seat {r['seat']}: {r['status']}{verdict} - {r['reason']}{where}")
        ok &= r["status"] in ("ran", "reused")
    if args.risk == "high":
        producer = (args.producer_family or "").casefold()
        other = [r for r in rows if r["status"] in ("ran", "reused")
                 and r["header"].get("family", "").casefold() not in ("", "unknown", producer)]
        if args.producer_family and other:
            r = other[0]
            origin = r["header"].get("head", "<unknown head>")[:12]
            how = "" if r["status"] == "ran" else f", inherited from {origin}"
            print(f"independent: {r['header']['family']} seat {r['seat']}{how}")
        else:
            print("independence: missing other-family seat at the high row")
            ok = False
    ticket = args.ticket.read_text() if args.ticket else None
    floor = risk_floor(name_status(args.repo, current), ticket)
    print(f"risk: {args.risk} / floor: {floor['floor']} "
          f"(paths: {floor['paths']}, ticket: {floor['ticket']})")
    if ROWS.index(args.risk) < ROWS.index(floor["floor"]):
        print("risk: plan row is below the floor")
        ok = False
    return 0 if ok else 1


EXIT_READ_FAILED = 3  # forge read failed or truncated: Missing Data, not a rejection
FORGE_QUERY = """query($owner:String!,$name:String!,$pr:Int!){repository(owner:$owner,name:$name){
pullRequest(number:$pr){
reviews(first:100){pageInfo{hasNextPage endCursor}
 nodes{__typename author{login ... on User{id} ... on Bot{id}} lastEditedAt state commit{oid}}}
comments(first:100){pageInfo{hasNextPage endCursor}
 nodes{__typename author{login ... on User{id} ... on Bot{id}} lastEditedAt}}
reviewThreads(first:100){pageInfo{hasNextPage endCursor}
 nodes{isResolved comments(first:100){pageInfo{hasNextPage endCursor}
  nodes{__typename author{login ... on User{id} ... on Bot{id}} lastEditedAt path}}}}}}}"""


def cmd_forge(args: argparse.Namespace) -> int:
    owner, name = args.forge_repo.split("/", 1)
    out = subprocess.run(
        ["gh", "api", "graphql", "--hostname", args.host, "-f", f"query={FORGE_QUERY}",
         "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"pr={args.pr}"],
        capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        print(f"forge: read failed, evidence invalid: {out.stderr.strip()}")
        return EXIT_READ_FAILED
    try:
        rows = classify_forge(json.loads(out.stdout), args.host)
    except (ForgeReadError, json.JSONDecodeError) as exc:
        print(f"forge: read incomplete, evidence invalid: {exc}")
        return EXIT_READ_FAILED
    for r in rows:
        extra = f" {r['state']} at {r['commit'][:12]}" if r["commit"] else ""
        if r["resolved"] is not None:
            extra += " resolved" if r["resolved"] else " unresolved"
        why = f" ({r['reason']})" if r["reason"] else ""
        print(f"{r['status']} {r['login']} {r['object_type']}{extra}{why}")
    return 1 if any(r["status"] == "rejected" for r in rows) else 0


def cmd_risk_floor(args: argparse.Namespace) -> int:
    current = current_inputs(args)
    ticket = args.ticket.read_text() if args.ticket else None
    print(json.dumps(risk_floor(name_status(args.repo, current), ticket)))
    return 0


def header_value(value: str) -> str:
    """A report header field: one line, so it cannot inject another field.

    One line as parse_report reads it: str.splitlines() also splits on
    U+2028, U+2029, U+0085, \\v, \\f and \\x1c-\\x1e, not only \\n and \\r.
    """
    if len((value + "x").splitlines()) != 1:
        raise argparse.ArgumentTypeError("must be a single line")
    return value


def seat_name(value: str) -> str:
    """A seat names a report file: no path separator, no parent reference."""
    header_value(value)
    if not value or "/" in value or "\\" in value or ".." in value:
        raise argparse.ArgumentTypeError("must not contain '/' or '..'")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo", type=Path, default=Path.cwd())
    common.add_argument("--base", default="origin/main", help="base ref; the merge base is used")
    common.add_argument("--head", default="HEAD")
    common.add_argument("--ticket", type=Path, help="ticket file whose exit criteria are hashed")
    common.add_argument("--policy-root", type=Path, default=HARNESS_ROOT,
                        help="harness checkout whose review policy is hashed")
    sub.add_parser("identity", parents=[common]).set_defaults(fn=cmd_identity)
    rec = sub.add_parser("record", parents=[common], help="write a report read from stdin")
    rec.add_argument("--seat", required=True, type=seat_name)
    rec.add_argument("--kind", choices=KINDS, default="review")
    rec.add_argument("--verdict", choices=VERDICTS, required=True)
    rec.add_argument("--family", default="unknown", type=header_value)
    rec.add_argument("--worker", default="unknown", type=header_value)
    rec.set_defaults(fn=cmd_record)
    for name, fn in (("plan", cmd_plan), ("gate", cmd_gate)):
        p = sub.add_parser(name, parents=[common])
        p.add_argument("--seat", action="append", default=[], required=True)
        p.set_defaults(fn=fn)
        if name == "gate":
            p.add_argument("--risk", choices=ROWS, required=True,
                           help="plan row; refused when below the computed floor")
            p.add_argument("--producer-family")
    fg = sub.add_parser("forge", help="admit forge-read reviews by pinned actor")
    fg.add_argument("forge_repo", help="owner/name")
    fg.add_argument("pr", type=int)
    fg.add_argument("--host", default="github.com")
    fg.set_defaults(fn=cmd_forge)
    sub.add_parser("risk-floor", parents=[common]).set_defaults(fn=cmd_risk_floor)
    args = parser.parse_args()
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    try:
        return args.fn(args)
    except (subprocess.CalledProcessError, OSError, ValueError) as exc:
        log.error("review-evidence: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())

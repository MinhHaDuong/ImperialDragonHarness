#!/usr/bin/env python3
"""Review evidence core: record reports, decide reuse, gate stale or missing proof.

Reports are repository files under `tickets/reviews/<base>..<head>/`, one per
seat execution, written by the controller. A report is reused only while the
five identity inputs hold: the merge base and head it names may move, but the
patch-id of the diff, the ticket body hash and the review policy
version must not change. Check, gate and adherence results are never reused.

Forge-read reviews (human, Copilot) are admitted only from three pinned actor
IDs and only when the forge reports them unedited; anything else fails closed.
The forge read waits forge.read_timeout() (ticket 1308): exit 4 when the forge is unreachable
(unread, the gate proceeds saying so and landing rechecks), exit 3 when it answered but the
answer is incomplete or refused (Missing Data). A complete read prints `forge-read: <UTC ISO>`
first, the time the gate's verdict records for the landing recheck.

Subcommands: `identity`, `record`, `gate`, `forge`.
Ticket 1142; design in conception/discussions/2026-10-14-1096-design.md.
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
# of 2026-10-14 (conception/discussions/2026-10-14-1096-seats/evidence-review-authors.json).
# Node IDs, not logins: a login can be renamed and re-registered.
FORGE_ACTORS = {
    ("github.com", "MDQ6VXNlcjE4NDc1MjA4"): "human",    # MinhHaDuong
    ("github.com", "BOT_kgDOCnlnWA"): "copilot",        # copilot-pull-request-reviewer
    ("github.com", "BOT_kgDOC9w8XQ"): "copilot",        # copilot-swe-agent
}
FORGE_OBJECTS = frozenset({"PullRequestReview", "PullRequestReviewComment", "IssueComment"})

# Review policy: what a seat's judgment depends on. Not all of rules/.
POLICY_GLOBS = (
    "skills/gaze/**/*",
    "skills/route/references/decorrelation.md",
    "skills/route/SKILL.md",
    "scripts/review_evidence.py",
    "scripts/review-anchor.py",
    "scripts/panel-manifest-check.py",
    "adapters/*/agents/*",
    "agents/*-seat.md",
    "agents/code-reviewer.md",
    "agents/prose-reviewer.md",
    "profiles/*-seat/**/*",
    "profiles/code-reviewer/**/*",
    "profiles/prose-reviewer/**/*",
)

# Model families a report may record: the grid `family` field of
# skills/route/grid.json plus the cross-family doors of routes.json and the
# families decorrelation.md names. "unknown" may be recorded.
FAMILIES = frozenset({"anthropic", "openai", "google", "mistral", "deepseek", "glm",
                      "qwen", "xiaomi"})


@dataclass(frozen=True)
class Inputs:
    base: str
    head: str
    patch_id: str
    criteria_hash: str
    policy_version: str
    ticket: str = "none"  # basename of the ticket the criteria hash was read from


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
    changed = [key for key in ("patch-id", "criteria-hash", "policy-version", "ticket")
               if record.get(key, "none") != getattr(current, key.replace("-", "_"))]
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


BODY_MARK = re.compile(r"^--- body ---[ \t]*\r?$", re.M)
TICKED = re.compile(r"^([ \t]*(?:[-*+]|\d+[.)])[ \t]+)\[[xX]\]", re.M)


def criteria_hash(ticket_text: str | None) -> str:
    """Hash the ticket's whole body, raw, with checkbox state normalised.

    The body is the text from the first `--- body ---` line to the end of the
    file; erg reads later marker lines as body text, so they are hashed too.
    Nothing is parsed: any other edit after a review reads stale, so notes
    belong in the log. The header, the log and the file's location are outside.
    """
    if ticket_text is None:
        return "none"
    start = BODY_MARK.search(ticket_text)
    if not start:
        return "none"
    body = ticket_text[start.end():]
    body = TICKED.sub(r"\1[ ]", body)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


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


def is_ticket_file(path: str) -> bool:
    """`tickets/*.erg` or `tickets/closed/*.erg`, the ticket paths merge-gate calls bookkeeping."""
    parts = path.split("/")
    return (path.endswith(".erg") and parts[0] == "tickets"
            and (len(parts) == 2 or (len(parts) == 3 and parts[1] == "closed")))


def exempt_paths(repo: Path, base: str, head: str) -> list[str]:
    """Plain report files added under REVIEWS_DIR: outside the reviewed identity."""
    raw = subprocess.run(["git", "-C", str(repo), "diff", "--raw", "-z", "--no-renames",
                          base, head], check=True, capture_output=True, timeout=60).stdout
    fields = raw.decode().split("\0")
    exempt = []
    for meta, path in zip(fields[0::2], fields[1::2]):
        parts = meta.split()
        if len(parts) != 5:
            continue
        if (parts[4] == "A" and parts[1] == "100644"
                and path.startswith(f"{REVIEWS_DIR}/") and path.endswith(REPORT_SUFFIXES)):
            exempt.append(path)
        elif is_ticket_file(path) and (parts[4] == "D" or parts[1] == "100644"):
            # The ticket close (move to closed/, checkboxes, log) is bookkeeping, as in
            # merge-gate; its exit criteria are covered by criteria_hash, not the patch.
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


class TicketRefused(SystemExit):
    pass


def ticket_at_head(args: argparse.Namespace, base: str, head: str) -> tuple[str | None, str]:
    """The ticket text as committed at `head`, never the caller's working copy.

    The path names the ticket; a move to tickets/closed/ is followed. A path
    not tracked at head is refused, and so is no path when the range touches
    a ticket: the criteria hash is the only guard once ticket edits leave the patch.
    """
    if args.ticket is None:
        touched = [e for e in git(args.repo, "diff", "--name-only", "--no-renames", base, head).splitlines()
                   if is_ticket_file(e)]
        if touched:
            raise TicketRefused(f"review-evidence: the range touches {touched[0]}; pass --ticket")
        return None, "none"
    top = Path(git(args.repo, "rev-parse", "--show-toplevel")).resolve()
    path = Path(args.ticket)
    path = path if path.is_absolute() else Path(args.repo) / path
    try:
        rel = path.resolve().relative_to(top).as_posix()
    except ValueError:
        raise TicketRefused(f"review-evidence: --ticket {args.ticket} is outside the repository")
    name = Path(rel).name
    if not is_ticket_file(rel):
        raise TicketRefused(f"review-evidence: --ticket {args.ticket} is not a ticket file")
    found = {}
    for candidate in (f"tickets/{name}", f"tickets/closed/{name}"):
        shown = subprocess.run(["git", "-C", str(args.repo), "show", f"{head}:{candidate}"],
                               capture_output=True, timeout=60)
        if shown.returncode == 0:
            found[candidate] = shown.stdout.decode()
    if len(found) > 1:
        raise TicketRefused(f"review-evidence: {name} exists both open and closed at {head[:12]}")
    if not found:
        raise TicketRefused(f"review-evidence: --ticket {args.ticket} is not tracked at {head[:12]}")
    text = next(iter(found.values()))
    if not BODY_MARK.search(text):
        raise TicketRefused(f"review-evidence: {name} has no `--- body ---` line at {head[:12]}")
    return text, name


def current_inputs(args: argparse.Namespace) -> Inputs:
    head = git(args.repo, "rev-parse", args.head)
    base = git(args.repo, "merge-base", args.base, head)
    text, name = ticket_at_head(args, base, head)
    return Inputs(base, head, patch_id(args.repo, base, head), criteria_hash(text),
                  policy_version(args.policy_root), name)


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

def range_dir(repo: Path, current: Inputs) -> Path:
    short = [git(repo, "rev-parse", "--short=7", sha) for sha in (current.base, current.head)]
    return repo / REVIEWS_DIR / f"{short[0]}..{short[1]}"


def cmd_identity(args: argparse.Namespace) -> int:
    print(json.dumps(current_inputs(args).__dict__, indent=1))
    return 0


def relativize(body: str, repo: Path) -> str:
    """Rewrite absolute paths into any worktree of this repo as relative ones.

    Replacement happens only at a path boundary, so `/w/t1-12` never eats the
    front of `/w/t1-123/x`. A path into another worktree keeps its tail
    relative to that tree's root.
    """
    roots = {str(Path(repo).resolve()), str(Path(git(repo, "rev-parse", "--show-toplevel")).resolve())}
    for line in git(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            roots.add(line[len("worktree "):])
    for root in sorted((r.rstrip("/") for r in roots if r.strip("/")), key=len, reverse=True):
        body = re.sub(re.escape(root) + r"(?:/([^\s`'\")\]>,;:]*))?(?![\w-])(?!\.[\w-])",
                      lambda m: m.group(1) or ".", body)
    return body


def cmd_record(args: argparse.Namespace) -> int:
    if args.ticket is None and not args.no_ticket:
        raise TicketRefused("review-evidence: record needs --ticket (or --no-ticket for a ticketless range)")
    current = current_inputs(args)
    folder = range_dir(args.repo, current)
    folder.mkdir(parents=True, exist_ok=True)
    n = 1
    while (folder / f"{args.seat}-{n}.md").exists():
        n += 1
    header = {
        "review-evidence": FORMAT, "kind": args.kind, "seat": args.seat,
        "verdict": args.verdict, "family": args.family, "worker": args.worker,
        "base": current.base, "head": current.head, "patch-id": current.patch_id,
        "criteria-hash": current.criteria_hash, "policy-version": current.policy_version,
        "ticket": current.ticket,
        "recorded": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if args.body_file:
        body = args.body_file.read_text(encoding="utf-8")
    else:
        body = "" if sys.stdin.isatty() else sys.stdin.read()
    body = relativize(body, args.repo)
    path = folder / f"{args.seat}-{n}.md"
    path.write_text("---\n" + "".join(f"{k}: {v}\n" for k, v in header.items())
                    + "---\n\n" + body)
    print(path)
    return 0


def claim_mismatch(args: argparse.Namespace, current: Inputs) -> str | None:
    """Why the PR body's close claim does not name the gated ticket, or None.

    The claim grammar is the merge recipe's (gaze_setup.close_claims, after
    skills/merge/references/claims.md); the body is the only source.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from gaze_setup import close_claims
    claims, malformed = close_claims(args.pr_body_file.read_text(encoding="utf-8"),
                                     Path(git(args.repo, "rev-parse", "--show-toplevel")))
    if malformed:
        return f"malformed close claim {malformed[0]}"
    claimed = {Path(c).name for c in claims}
    # The merge path reads claims with raid_land's grammar; the two must agree.
    from raid_land import Refusal, close_claims as merge_claims
    try:
        merged = sorted(merge_claims(args.pr_body_file.read_text(encoding="utf-8")))
    except Refusal as exc:
        return f"merge grammar refuses the body: {exc}"
    if merged != sorted(n.split("-", 1)[0] for n in claimed):
        return f"the gate and the merge recipe read different claims ({sorted(claimed)} vs {merged})"
    if len(claimed) > 1:
        return f"the PR claims several tickets {sorted(claimed)}; gate one range per ticket"
    if current.ticket == "none":
        return f"gated range names no ticket but the PR claims {sorted(claimed)}" if claimed else None
    if current.ticket not in claimed:
        return (f"gated ticket {current.ticket} is not the ticket the PR claims "
                f"({', '.join(sorted(claimed)) or 'none'})")
    return None


def cmd_gate(args: argparse.Namespace) -> int:
    current = current_inputs(args)
    if args.pr_body_file is not None:
        why = claim_mismatch(args, current)
        if why:
            print(f"claim: refused, {why}")
            return 1
    rows = seat_rows(args.repo, current, list(dict.fromkeys(args.seat)))
    ok = True
    print(f"REVIEW-EVIDENCE: base {current.base} head {current.head} "
          f"patch-id {current.patch_id} criteria-hash {current.criteria_hash} "
          f"policy-version {current.policy_version}")
    for r in rows:
        where = f" {r['path']}" if r["path"] else ""
        verdict = f" ({r['header'].get('verdict', '?')})" if r["header"] else ""
        print(f"seat {r['seat']}: {r['status']}{verdict} - {r['reason']}{where}")
        ok &= r["status"] in ("ran", "reused")
    return 0 if ok else 1


EXIT_READ_FAILED = 3  # forge read failed or truncated: Missing Data, not a rejection
EXIT_UNREACHABLE = 4  # forge did not answer (timeout, network): unread, never "no reviews" (ticket 1308)
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
    import forge  # same directory: the one read bound and network classifier (ticket 1308)
    owner, name = args.forge_repo.split("/", 1)
    read_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        out = subprocess.run(
            ["gh", "api", "graphql", "--hostname", args.host, "-f", f"query={FORGE_QUERY}",
             "-F", f"owner={owner}", "-F", f"name={name}", "-F", f"pr={args.pr}"],
            capture_output=True, text=True, timeout=forge.read_timeout())
    except subprocess.TimeoutExpired as exc:
        print(f"forge: unread (offline: gh timed out after {exc.timeout}s)")
        return EXIT_UNREACHABLE
    except OSError as exc:
        print(f"forge: unread (offline: gh unavailable: {exc})")
        return EXIT_UNREACHABLE
    if out.returncode != 0 and forge.NET_ERR.search(out.stderr or ""):
        print(f"forge: unread (offline: {out.stderr.strip().splitlines()[-1]})")
        return EXIT_UNREACHABLE
    if out.returncode != 0:
        print(f"forge: read failed, evidence invalid: {out.stderr.strip()}")
        return EXIT_READ_FAILED
    try:
        rows = classify_forge(json.loads(out.stdout), args.host)
    except (ForgeReadError, json.JSONDecodeError) as exc:
        print(f"forge: read incomplete, evidence invalid: {exc}")
        return EXIT_READ_FAILED
    print(f"forge-read: {read_at}")
    for r in rows:
        extra = f" {r['state']} at {r['commit'][:12]}" if r["commit"] else ""
        if r["resolved"] is not None:
            extra += " resolved" if r["resolved"] else " unresolved"
        why = f" ({r['reason']})" if r["reason"] else ""
        print(f"{r['status']} {r['login']} {r['object_type']}{extra}{why}")
    return 1 if any(r["status"] == "rejected" for r in rows) else 0


def header_value(value: str) -> str:
    """A report header field: one line, so it cannot inject another field.

    One line as parse_report reads it: str.splitlines() also splits on
    U+2028, U+2029, U+0085, \\v, \\f and \\x1c-\\x1e, not only \\n and \\r.
    """
    if len((value + "x").splitlines()) != 1:
        raise argparse.ArgumentTypeError("must be a single line")
    return value


def family_name(value: str) -> str:
    """A family as recorded: stripped, casefolded, in FAMILIES or 'unknown'."""
    family = header_value(value).strip().casefold()
    if family != "unknown" and family not in FAMILIES:
        raise argparse.ArgumentTypeError(
            f"unknown family {value!r}; expected one of {', '.join(sorted(FAMILIES))}")
    return family


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
    rec.add_argument("--family", default="unknown", type=family_name)
    rec.add_argument("--no-ticket", action="store_true", help="the reviewed range claims no ticket")
    rec.add_argument("--body-file", type=Path, help="read the report body here; stdin is read only when it is not a terminal")
    rec.add_argument("--worker", default="unknown", type=header_value)
    rec.set_defaults(fn=cmd_record)
    gate = sub.add_parser("gate", parents=[common])
    gate.add_argument("--seat", action="append", default=[], required=True)
    gate.add_argument("--pr-body-file", type=Path,
                      help="the PR body; the gated ticket must be the one it claims to close")
    gate.set_defaults(fn=cmd_gate)
    fg = sub.add_parser("forge", help="admit forge-read reviews by pinned actor")
    fg.add_argument("forge_repo", help="owner/name")
    fg.add_argument("pr", type=int)
    fg.add_argument("--host", default="github.com")
    fg.set_defaults(fn=cmd_forge)
    args = parser.parse_args()
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    try:
        return args.fn(args)
    except (subprocess.CalledProcessError, OSError, ValueError) as exc:
        log.error("review-evidence: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())

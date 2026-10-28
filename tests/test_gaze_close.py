"""Ticket 1227: one call cleans, reports containment and records the result; since ticket
1301 the result lives on notes and the PR comment is a one-line pointer to it."""

import re
from pathlib import Path

import pytest
from gaze_fixture import CLOSE, SETUP, fields, git, make_repo, run

pytestmark = pytest.mark.integration


def ATTR(tmp_path, text=""):
    f = tmp_path / "attr.txt"
    f.write_text(text)
    return ["--attribution-file", str(f)]


def forge_shim(tmp_path, env):
    """gh shim holding a PR body in a file: `pr view --json body`, `api` GET and PATCH."""
    body = tmp_path / "body.txt"
    body.write_text("Body\n```attribution\npr: 7 · merged pending · project: .agents\n```\n")
    shim = tmp_path / "bin" / "gh"
    shim.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = pr ] && [ "$2" = view ]; then jq -Rs \'{body: .}\' "$MOCK_BODY"; exit 0; fi\n'
        'if [ "$1" = api ]; then\n'
        '  case "$*" in *PATCH*) python3 -c "import json,sys;open(sys.argv[1],\'w\').write(json.load(sys.stdin)[\'body\'])" "$MOCK_BODY" ;;\n'
        '  *) cat "$MOCK_BODY" ;; esac; exit 0; fi\n'
        'if [ "$2" = comment ]; then printf \'%s\\n\' "$5" >> "$MOCK_GH_LOG"; fi\n')
    env["MOCK_BODY"] = str(body)
    return body


SEAT = ("reviewer: step=review · seat: a · runtime=claude · family=anthropic · route=r · "
        "model=m · status: ran")


POINTER = re.compile(r"^/gaze review on notes: (rv-\S+), verdict (REVIEWED|FINDINGS|ESCALATE)$")


def answer_text(primary, f):
    """The text of the review's latest answer: where the result lives (ticket 1301)."""
    rn = _notes()
    return [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"][-1]["text"]


def posted(tmp_path):
    log = tmp_path / "gh.log"
    return log.read_text() if log.exists() else ""


def opened(tmp_path):
    primary, env = make_repo(tmp_path)
    r = run(SETUP, ["7"], primary, env)
    assert r.returncode == 0, r.stderr
    return primary, env, fields(r.stdout)


def test_clean_tree_is_removed_and_comment_posted(tmp_path):
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{duration}}\n{{containment}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--token", f["clock"], *ATTR(tmp_path), "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()
    text = answer_text(primary, f)
    assert "result: REVIEWED" in text and "duration:" in text and "containment: toplevel" in text
    assert "{{" not in text


def test_dirty_tracked_file_preserves_tree_and_blocks(tmp_path):
    primary, env, f = opened(tmp_path)
    tree = primary / ".claude" / "worktrees" / "review-7"
    (tree / "f.txt").write_text("real wip\n")
    comment = tmp_path / "c.md"
    comment.write_text("x {{plan_check}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 1 and "blocked" in r.stderr
    assert (tree / "f.txt").read_text() == "real wip\n"
    (line,) = posted(tmp_path).splitlines()
    assert POINTER.match(line).group(2) == "ESCALATE"
    assert answer_text(primary, f).startswith("result: ESCALATE\nreason: cleanup blocked")


def test_foreign_file_in_session_tree_is_flagged(tmp_path):
    primary, env, f = opened(tmp_path)
    (primary / "stray.erg").write_text("x\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], primary, env)
    assert r.returncode == 4 and "FLAGGED" in r.stdout and "stray.erg" in r.stdout
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()


def test_blocked_cleanup_still_appends_attribution(tmp_path):
    primary, env, f = opened(tmp_path)
    body = forge_shim(tmp_path, env)
    (primary / ".claude" / "worktrees" / "review-7" / "f.txt").write_text("real wip\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, SEAT + "\n")], primary, env)
    assert r.returncode == 1 and "blocked" in r.stderr
    assert "ESCALATE" in r.stderr
    assert "attribution: appended" in r.stdout
    assert "seat: a" in body.read_text()
    assert "seat:" not in posted(tmp_path)


def test_clean_close_appends_attribution_before_the_comment(tmp_path):
    primary, env, f = opened(tmp_path)
    body = forge_shim(tmp_path, env)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, SEAT + "\n"), "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "seat: a" in body.read_text()


def test_call_without_attribution_file_fails_loudly(tmp_path):
    primary, env, f = opened(tmp_path)
    r = run(CLOSE, ["7", "--branch", "feature"], primary, env)
    assert r.returncode == 2 and "--attribution-file" in r.stderr
    assert (primary / ".claude" / "worktrees" / "review-7").exists()


def test_attribution_creates_the_block_when_the_body_has_none(tmp_path):
    primary, env, f = opened(tmp_path)
    body = forge_shim(tmp_path, env)
    body.write_text("Body without a block\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, SEAT + "\n")], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    text = body.read_text()
    assert "```attribution" in text and "seat: a" in text and f"project: {primary.name}" in text


def test_blocked_cleanup_with_failed_append_exits_2(tmp_path):
    primary, env, f = opened(tmp_path)
    (primary / ".claude" / "worktrees" / "review-7" / "f.txt").write_text("real wip\n")
    # the default shim answers `pr view` with PR json, not a body: the append fails
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, SEAT + "\n")], primary, env)
    assert "attribution: FAILED" in r.stdout and "blocked" in r.stderr
    assert r.returncode == 2


def test_close_from_inside_the_review_worktree_is_refused(tmp_path):
    primary, env, f = opened(tmp_path)
    tree = primary / ".claude" / "worktrees" / "review-7"
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], tree, env)
    assert r.returncode == 2 and "inside the review worktree" in r.stderr
    assert tree.exists()


def test_preexisting_untracked_primary_file_is_not_contamination(tmp_path):
    primary, env = make_repo(tmp_path)
    (primary / "docs").mkdir()
    (primary / "docs" / "draft.md").write_text("author work\n")
    caller = tmp_path / "caller"
    git(primary, "worktree", "add", "-b", "callerbr", str(caller))
    r = run(SETUP, ["7"], caller, env)
    assert r.returncode == 0, r.stderr
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], caller, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "clean" in r.stdout


def test_primary_root_of_a_repo_nested_under_a_worktree_path(tmp_path):
    """A repo whose own path holds `/.claude/worktrees/` is its own primary.

    Hunt puts TMPDIR in `<primary>/.claude/worktrees/<name>/.tmp`; cutting the
    toplevel at the first such segment resolved a fixture repo there to the
    outer checkout, and gaze_setup made `review-<pr>` in the real repository.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(CLOSE).parent))
    import gaze_close

    nested = tmp_path / ".claude" / "worktrees" / "t1-1" / ".tmp" / "fixture"
    nested.mkdir(parents=True)
    git(nested, "init", "-q")
    assert gaze_close.primary_root(cwd=nested) == nested.resolve()
    git(nested, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "--allow-empty", "-m", "base")
    git(nested, "worktree", "add", "-q", str(nested / ".claude" / "worktrees" / "x"))
    assert gaze_close.primary_root(cwd=nested / ".claude" / "worktrees" / "x") == nested.resolve()


def panel(primary, manifest, reports=None):
    """Write a plan and its reports into the review tree's panel, as a gaze run leaves them."""
    d = primary / ".claude" / "worktrees" / "review-7" / ".panel" / "7"
    d.mkdir(parents=True, exist_ok=True)
    (d / "manifest.txt").write_text(manifest)
    for name, text in (reports or {}).items():
        (d / f"{name}.md").write_text(text)


def plan_line(primary, f):
    return [ln for ln in answer_text(primary, f).splitlines() if ln.startswith("plan check:")]


def test_failed_plan_check_reaches_the_comment_as_fail(tmp_path):
    """Ticket 1267: the verdict is the checker's, copied by the script. A free-text
    manifest (the format that produced a model-relabelled PASS) is a FAIL."""
    primary, env, f = opened(tmp_path)
    panel(primary, "# budget: 10m\nOne seat reads the diff and the test.\n")
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}} — the model's reason\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = plan_line(primary, f)
    assert line.startswith("plan check: FAIL") and line.endswith("— the model's reason"), line
    assert "{{" not in answer_text(primary, f)


def test_missing_panel_is_a_failed_plan_check(tmp_path):
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text("{{plan_check}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert plan_line(primary, f) == ["plan check: FAIL — manifest unreadable"]


def test_valid_plan_check_reaches_the_comment_as_pass(tmp_path):
    """Positive control for the FAIL test: same path, a parseable manifest and a report."""
    primary, env, f = opened(tmp_path)
    panel(primary, "# budget: 10m\nregression\tscript\tnone\tfails on base\n")
    d = primary / ".claude" / "worktrees" / "review-7" / ".panel" / "7"
    (d / "regression.md").write_text("ran: ok\n")
    comment = tmp_path / "c.md"
    comment.write_text("{{plan_check}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert plan_line(primary, f) == ["plan check: PASS"]


@pytest.mark.parametrize("text", ["result: REVIEWED\n", "{{plan_check}}\nplan check: PASS\n"])
def test_comment_without_the_placeholder_or_with_a_typed_line_is_refused(tmp_path, text):
    """The closing call is the only path: a hand-typed or missing plan-check line
    posts nothing and removes nothing."""
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text(text)
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 2 and "plan_check" in r.stderr
    assert (primary / ".claude" / "worktrees" / "review-7").exists()
    assert not (tmp_path / "gh.log").exists()


DOCS = [("skills/gaze/SKILL.md"), ("skills/gaze/references/output.md")]


@pytest.mark.parametrize("doc", DOCS)
def test_documented_template_filled_as_documented_is_accepted(tmp_path, doc):
    """Ticket 1267: the template line the docs show, with only its <reason> filled,
    is accepted and posts exactly one `plan check:` line."""
    import re
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / doc).read_text()
    hits = [ln for ln in src.splitlines() if "{{plan_check}}" in ln and ln.startswith(("plan check:", "{{plan_check}} —"))]
    tmpl = hits[0]  # a skill read may inline its references; the first hit is the file's own
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n" + re.sub(r"<[^>]*>", "none", tmpl) + "\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = plan_line(primary, f)
    assert line.startswith("plan check: FAIL") and "plan check: plan check" not in line


def test_stdout_carries_the_checkers_fail_verbatim(tmp_path):
    """Ticket 1267: the caller copies the printed line, never types one."""
    primary, env, f = opened(tmp_path)
    panel(primary, "# budget: 10m\nOne seat reads the diff and the test.\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], primary, env)
    (line,) = [ln for ln in r.stdout.splitlines() if ln.startswith("plan check:")]
    assert line.startswith("plan check: FAIL"), line


def test_blocked_cleanup_still_prints_the_plan_check(tmp_path):
    primary, env, f = opened(tmp_path)
    panel(primary, "# budget: 10m\nOne seat reads the diff and the test.\n")
    (primary / ".claude" / "worktrees" / "review-7" / "f.txt").write_text("real wip\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], primary, env)
    assert r.returncode == 1
    assert any(ln.startswith("plan check: FAIL") for ln in r.stdout.splitlines())


@pytest.mark.parametrize("typed", ["  plan check: PASS", "> plan check: PASS", "**plan check:** PASS", "Plan check: PASS"])
def test_typed_plan_check_in_any_markup_is_refused(tmp_path, typed):
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text(f"{{{{plan_check}}}}\n{typed}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 2 and "plan_check" in r.stderr
    assert (primary / ".claude" / "worktrees" / "review-7").exists()
    assert not (tmp_path / "gh.log").exists()


def seats_shim(tmp_path, env):
    """gh shim whose `pr view` answers body and a posted gaze result carrying a seat: line."""
    body = tmp_path / "body.txt"
    body.write_text("Body\n```attribution\nkind: review-attribution\npr: 7 · merged pending · project: .agents\n"
                    "writer: step=execute · runtime=fixture · model=e/w · effort=not-stated · route=sonnet"
                    " · independence=not-stated\n```\n")
    result = tmp_path / "result.txt"
    result.write_text("## /gaze result\nseat: a · runtime=claude · family=anthropic · route=r · model=anthropic/claude-x · status: ran\n")
    shim = tmp_path / "bin" / "gh"
    shim.write_text(
        "#!/bin/sh\n"
        'if [ "$1" = pr ] && [ "$2" = view ]; then python3 -c "import json,sys;print(json.dumps(dict(json.loads(sys.argv[3]),body=open(sys.argv[1]).read(),'
        'comments=[{\'body\':open(sys.argv[2]).read()}])))" "$MOCK_BODY" "$MOCK_RESULT" "$MOCK_PR_JSON"; exit 0; fi\n'
        'if [ "$1" = api ]; then\n'
        '  case "$*" in *PATCH*) python3 -c "import json,sys;open(sys.argv[1],\'w\').write(json.load(sys.stdin)[\'body\'])" "$MOCK_BODY" ;;\n'
        '  *) cat "$MOCK_BODY" ;; esac; exit 0; fi\n'
        'if [ "$2" = comment ]; then printf \'%s\\n\' "$5" >> "$MOCK_GH_LOG"; fi\n')
    env["MOCK_BODY"], env["MOCK_RESULT"] = str(body), str(result)
    return body


def test_empty_attribution_file_runs_seats_pr(tmp_path):
    primary, env, f = opened(tmp_path)
    body = seats_shim(tmp_path, env)
    comment = tmp_path / "c.md"
    comment.write_text(Path(env["MOCK_RESULT"]).read_text() + "result: REVIEWED\n{{plan_check}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "attribution: seats appended" in r.stdout
    assert "reviewer: " in body.read_text() and "seat=a" in body.read_text()


def test_partial_attribution_file_gets_the_missing_seat(tmp_path):
    primary, env, f = opened(tmp_path)
    body = seats_shim(tmp_path, env)
    result = Path(env["MOCK_RESULT"])
    result.write_text(result.read_text() + result.read_text().split("\n")[1].replace("seat: a", "seat: b") + "\n")
    have = ("reviewer: step=review · seat=a · runtime=claude · model=anthropic/claude-x · effort=not-stated"
            " · route=r · independence=not-stated · status: ran")
    comment = tmp_path / "c.md"
    comment.write_text(result.read_text() + "result: REVIEWED\n{{plan_check}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, have + "\n"), "--comment-file", str(comment)], primary, env)
    assert "attribution: seats appended" in r.stdout, r.stdout
    assert "seat=b" in body.read_text() and body.read_text().count("seat=a") == 1


SIGNED = "worker: model=m · family={}\nverdict: clear\n"


@pytest.mark.parametrize("claim,reports,code", [
    ("panel", {"self": SIGNED.format("anthropic")}, 2),            # PR 1827: panel typed, only self filed
    ("Panel", {"self": SIGNED.format("anthropic")}, 2),            # gaze finding: any case
    ("**panel**", {"self": SIGNED.format("anthropic")}, 2),        # gaze finding: any markup
    ("<key>Seats: panel", {"self": SIGNED.format("anthropic")}, 2),   # gaze round 2: the key too
    ("<key>**seats:** panel", {"self": SIGNED.format("anthropic")}, 2),
    ("<key>- seats: panel", {"self": SIGNED.format("anthropic")}, 2),   # raid fix: list, quote, heading, spaced colon
    ("<key>> seats: panel", {"self": SIGNED.format("anthropic")}, 2),
    ("<key>### seats: panel", {"self": SIGNED.format("anthropic")}, 2),
    ("<key>seats : panel", {"self": SIGNED.format("anthropic")}, 2),
    ("panel", {"self": SIGNED.format("anthropic"), "redteam": SIGNED.format("openai")}, 0),
    ("self-only", {"self": SIGNED.format("anthropic")}, 0),
])
def test_seats_panel_needs_a_filed_non_self_report(tmp_path, claim, reports, code):
    """Ticket 1287: the `seats:` header is checked against the panel, like the plan-check line."""
    primary, env, f = opened(tmp_path)
    panel(primary, "# budget: 10m\nself\tself\tanthropic\tgaze\nredteam\to\topenai\theadless codex\n", reports)
    comment = tmp_path / "c.md"
    line = claim[len("<key>"):] if claim.startswith("<key>") else f"seats: {claim}"
    comment.write_text(f"result: REVIEWED\n{line}\n{{{{plan_check}}}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == code, r.stdout + r.stderr
    if code:
        assert "seats: self-only" in r.stderr
        assert (primary / ".claude" / "worktrees" / "review-7").exists()
        assert not (tmp_path / "gh.log").exists()


@pytest.mark.parametrize("line,value", [
    ("seats: panel", "panel"), ("Seats: panel", "panel"), ("- seats: panel", "panel"),
    ("> seats: panel", "panel"), ("### seats: panel", "panel"), ("seats : panel", "panel"),
    ("**seats:** panel", "panel"), ("seats: self-only", "self-only"), ("scope: full", None),
])
def test_one_normaliser_reads_the_seats_claim(line, value):
    """Raid fix, ticket 1287: the claim check and the notes record read `seats:` alike."""
    import sys
    sys.path.insert(0, str(Path(CLOSE).parent))
    import gaze_close
    assert gaze_close.seats_claim(f"result: REVIEWED\n{line}\n") == value


def test_record_answer_reads_the_claim_through_the_one_normaliser(monkeypatch):
    """Ticket 1287: the notes record reads `seats:` through seats_claim, as main() does. The old
    `_field` reader saw nothing in marked-up `**seats:** panel` and recorded `self-only`."""
    import sys
    sys.path.insert(0, str(Path(CLOSE).parent))
    import gaze_close
    seen = {}

    def add(cwd, kind, rid, body, **kw):
        seen.update(body)
        return {"id": "e1"}

    monkeypatch.setattr(gaze_close.rn, "add", add)
    monkeypatch.setattr(gaze_close.rn, "publish", lambda cwd, ids: "retrievable")
    monkeypatch.setattr(gaze_close.rn, "setup", lambda cwd: None)
    text = "result: REVIEWED\nscope: full\n**seats:** panel\n"
    code = gaze_close.record_answer("/nowhere", "7", text, "", identity={"review_id": "r1"})
    assert code == 0
    assert seen["seats"] == "panel"


# --- ticket 1300: the answer goes to refs/notes/review for a PR too; the comment is dual-written ---

def _notes():
    import importlib.util
    spec = importlib.util.spec_from_file_location("review_notes", Path(CLOSE).parent / "review_notes.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pr_answer_written_to_notes_and_pointer(tmp_path):
    rn = _notes()
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text(f"result: REVIEWED\nreviewed_head_sha: {f['head']}\nintent: default\n{{{{plan_check}}}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = posted(tmp_path).splitlines()  # the comment is the pointer alone (ticket 1301)
    assert POINTER.match(line).groups() == (f["review_id"], "REVIEWED")
    answers = [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"]
    assert len(answers) == 1 and answers[0]["result"] == "REVIEWED"
    assert answers[0]["request_id"] == f["request_id"] and answers[0]["run_id"] == f["run_id"]
    assert answers[0]["head"] == f["head"]


NETWORK_GIT = {("fetch",), ("push",), ("ls-remote",), ("pull",), ("remote", "update"),
               ("request-pull",)}


def _git_subcommand(cmd):
    """The git subcommand of a spawned argv, as a 1- or 2-tuple (`remote update`), or None.
    Every child goes through subprocess.Popen, whichever route spawned it (rn._git, a direct
    subprocess.run in gaze_close, forge), so the test patches Popen once (gaze on PR #1855)."""
    argv = [str(c) for c in cmd] if isinstance(cmd, (list, tuple)) else str(cmd).split()
    if not argv or Path(argv[0]).name != "git":
        return None
    i = 1
    while i < len(argv) and argv[i].startswith("-"):
        i += 2 if argv[i] in ("-C", "-c", "--git-dir", "--work-tree") else 1
    rest = argv[i:]
    if not rest:
        return None
    if rest[0] == "remote" and len(rest) > 1:
        return (rest[0], rest[1])
    return (rest[0],)


def test_record_answer_makes_no_network_call(tmp_path, monkeypatch):
    import sys
    primary, env, f = opened(tmp_path)
    sys.path.insert(0, str(Path(CLOSE).parent))
    import gaze_close

    def boom(*a, **k):
        raise AssertionError("network on the write path")
    for name in ("refresh", "sync", "publish", "resolve", "resolve_unit", "_fetch", "_push_notes"):
        monkeypatch.setattr(gaze_close.rn, name, boom)
    monkeypatch.setattr(gaze_close.forge, "get_forge", boom)
    real_git, spawned = gaze_close.rn._git, []

    def local_git(cwd, *args, **kw):
        if args and args[0] in ("fetch", "ls-remote", "push", "request-pull"):
            raise AssertionError(f"network git {args[0]} on the write path")
        return real_git(cwd, *args, **kw)
    monkeypatch.setattr(gaze_close.rn, "_git", local_git)
    real_popen = gaze_close.rn.subprocess.Popen

    def popen(cmd, *a, **kw):  # record the detached sync, refuse any git network child, run the rest
        if "--if-idle" in cmd:
            spawned.append(cmd)
            return None
        sub = _git_subcommand(cmd)
        if sub in NETWORK_GIT:
            raise AssertionError(f"network git {' '.join(sub)} spawned on the write path: {cmd}")
        return real_popen(cmd, *a, **kw)
    monkeypatch.setattr(gaze_close.rn.subprocess, "Popen", popen)
    text = f"result: REVIEWED\nreviewed_head_sha: {f['head']}\nintent: default\n"
    assert gaze_close.record_answer(primary, "7", text, "") == 0  # no identity: local find_unit
    assert gaze_close.record_answer(primary, "7", text, "", identity={
        "review_id": f["review_id"], "request_id": f["request_id"], "run_id": f["run_id"]}) == 0
    assert len(spawned) == 2 and all(c[-2:] == ["sync", "--if-idle"] for c in spawned)


def test_failed_background_push_does_not_block_close(tmp_path):
    import time
    rn = _notes()
    primary, env, f = opened(tmp_path)
    hook = tmp_path / "origin.git" / "hooks" / "pre-receive"
    hook.write_text("#!/bin/sh\nsleep 8\nexit 1\n")
    hook.chmod(0o755)
    comment = tmp_path / "c.md"
    comment.write_text("result: FINDINGS\nintent: default\n{{plan_check}}\n")
    t0 = time.monotonic()
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    elapsed = time.monotonic() - t0
    assert r.returncode == 0, r.stdout + r.stderr
    assert elapsed < 7, elapsed
    answers = [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"]
    assert answers and answers[-1]["result"] == "FINDINGS"


# --- ticket 1301: the PR comment is a pointer; readers move to notes ------------------------------

def test_pr_close_posts_only_pointer(tmp_path):
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text("## /gaze result\n\nresult: FINDINGS\n{{plan_check}}\nFindings: one\n"
                       "seat: a · runtime=claude · family=anthropic · route=r · model=anthropic/x · status: ran\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert "pointer: posted" in r.stdout, r.stdout + r.stderr
    assert posted(tmp_path) == f"/gaze review on notes: {f['review_id']}, verdict FINDINGS\n"
    assert "Findings: one" in answer_text(primary, f)


def test_pointer_failure_ignored_exit_zero(tmp_path):
    primary, env, f = opened(tmp_path)
    shim = tmp_path / "bin" / "gh"
    shim.write_text(shim.read_text().replace('  comment) printf', '  comment) echo refused >&2; exit 1; printf'))
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "pointer: not posted" in r.stdout and "result: REVIEWED" in answer_text(primary, f)


def test_seats_appended_to_body_without_comment(tmp_path):
    """The seat lines come from the notes answer: the PR's comments carry none, yet the body
    gets the reviewer line, and the posted pointer holds no `seat:` line."""
    primary, env, f = opened(tmp_path)
    body = seats_shim(tmp_path, env)
    seat = Path(env["MOCK_RESULT"]).read_text().splitlines()[1]
    Path(env["MOCK_RESULT"]).write_text("an unrelated comment\n")
    comment = tmp_path / "c.md"
    comment.write_text(f"result: REVIEWED\n{{{{plan_check}}}}\n{seat}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "attribution: seats appended" in r.stdout
    assert "seat=a" in body.read_text()
    assert "seat:" not in posted(tmp_path)


def test_pointer_timeout_ignored_and_seats_still_run(monkeypatch, capsys):
    """A `gh pr comment` that times out is a refused pointer, not a crash: pointer() returns, so
    main() keeps its exit code and goes on to the --seats-pr step."""
    import subprocess
    import sys
    sys.path.insert(0, str(Path(CLOSE).parent))
    import forge
    import gaze_close

    def slow(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout", 120))

    monkeypatch.setattr(forge.subprocess, "run", slow)
    monkeypatch.setattr(gaze_close.forge, "get_forge", lambda cwd, pr: forge.GhForge())
    gaze_close.pointer("/nowhere", "7", "REVIEWED", identity={"review_id": "r1"})
    assert "pointer: not posted" in capsys.readouterr().out

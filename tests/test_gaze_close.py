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


HEADLESS = "worker: model={pin} · family={family} · runtime={runtime} · door=headless\nverdict: clear\n"


POINTER = re.compile(r"^/gaze review on notes: (rv-\S+), verdict (REVIEWED|FINDINGS|ESCALATE)$")


def answer_text(primary, f):
    """The text of the review's latest answer: where the result lives (ticket 1301)."""
    rn = _notes()
    return [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"][-1]["text"]


def answer_attr(primary, f):
    """The attribution lines of the review's latest answer: their one home (ticket 1307)."""
    rn = _notes()
    return [e for e in rn.entries(primary, f["review_id"]) if e["kind"] == "answer"][-1]["attribution"]


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
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n{{duration}}\n{{containment}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--token", f["clock"], *ATTR(tmp_path), "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()
    text = answer_text(primary, f)
    assert "result: REVIEWED" in text and "duration:" in text and "containment: toplevel" in text
    assert "{{" not in text


def test_tree_holding_uv_run_build_output_is_removed(tmp_path):
    """Ticket 1345: a seat's `uv run` in a packaged project leaves an ignored
    egg-info beside the .venv and caches; the close removes the tree anyway."""
    primary, env, f = opened(tmp_path)
    tree = primary / ".claude" / "worktrees" / "review-7"
    exclude = Path(git(primary, "rev-parse", "--absolute-git-dir")) / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as stream:
        stream.write("\n.venv/\n*.egg-info/\n__pycache__/\n.pytest_cache/\n")
    for p in (".venv/bin/python", "pkg.egg-info/PKG-INFO", "src/__pycache__/m.pyc", ".pytest_cache/README.md"):
        (tree / p).parent.mkdir(parents=True, exist_ok=True)
        (tree / p).write_text("x\n")
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--token", f["clock"], *ATTR(tmp_path), "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not tree.exists()
    assert answer_text(primary, f).startswith("result: REVIEWED")


def test_tree_holding_setuptools_build_is_removed(tmp_path):
    """Ticket 1357: an ignored setuptools build/ (git prints only `!! build/`)
    no longer blocks the close; the standard `build/` pattern is the shape git emits."""
    primary, env, f = opened(tmp_path)
    tree = primary / ".claude" / "worktrees" / "review-7"
    exclude = Path(git(primary, "rev-parse", "--absolute-git-dir")) / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a") as stream:
        stream.write("\nbuild/\n")
    tracked = (tree / "f.txt").read_bytes()
    for p, data in (("build/lib/pkg/f.txt", tracked), ("build/lib/pkg/m.pyc", b"\x00x"),
                    ("build/bdist.linux-x86_64/f.txt", tracked), ("build/temp.linux-x86_64/o.o", b"\x00x")):
        (tree / p).parent.mkdir(parents=True, exist_ok=True)
        (tree / p).write_bytes(data)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--token", f["clock"], *ATTR(tmp_path), "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not tree.exists()


def test_refused_close_leaves_the_closed_marker(tmp_path):
    """Ticket 1357: the marker lives in the worktree's git dir, so it survives a refused close."""
    primary, env, f = opened(tmp_path)
    tree = primary / ".claude" / "worktrees" / "review-7"
    (tree / "f.txt").write_text("real wip\n")
    comment = tmp_path / "c.md"
    comment.write_text("x {{plan_check}}\n{{seats}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 1
    assert (Path(git(tree, "rev-parse", "--absolute-git-dir")) / "gaze-closed").is_file()


def test_dirty_tracked_file_preserves_tree_and_blocks(tmp_path):
    primary, env, f = opened(tmp_path)
    tree = primary / ".claude" / "worktrees" / "review-7"
    (tree / "f.txt").write_text("real wip\n")
    comment = tmp_path / "c.md"
    comment.write_text("x {{plan_check}}\n{{seats}}\n")
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


def test_blocked_cleanup_still_records_attribution_on_notes(tmp_path):
    primary, env, f = opened(tmp_path)
    body = forge_shim(tmp_path, env)
    before = body.read_text()
    one_seat(primary)
    (primary / ".claude" / "worktrees" / "review-7" / "f.txt").write_text("real wip\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], primary, env)
    assert r.returncode == 1 and "blocked" in r.stderr
    assert "ESCALATE" in r.stderr
    assert "attribution: carried in the answer entry" in r.stdout
    assert any("seat=a" in ln for ln in answer_attr(primary, f))
    assert body.read_text() == before  # ticket 1307: no PR-body edit on the review path
    assert "seat:" not in posted(tmp_path)
    # constraint 3: the identities were read before cleanup and ride in the ESCALATE answer
    assert "seat: a · runtime=claude-code" in answer_text(primary, f)


def test_clean_close_records_attribution_on_notes_and_leaves_the_body(tmp_path):
    """Ticket 1307 exit criterion: gaze_close makes no PR-body edit; its attribution is written
    to notes only (this test: a PR unit; the branch unit: test_gaze_branch.py)."""
    primary, env, f = opened(tmp_path)
    body = seats_shim(tmp_path, env)
    before = body.read_text()
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n")
    one_seat(primary)
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = answer_attr(primary, f)
    assert line.startswith("reviewer: step=review · seat=a")
    assert body.read_text() == before
    assert "appended" not in r.stdout


def test_call_without_attribution_file_fails_loudly(tmp_path):
    primary, env, f = opened(tmp_path)
    r = run(CLOSE, ["7", "--branch", "feature"], primary, env)
    assert r.returncode == 2 and "--attribution-file" in r.stderr
    assert (primary / ".claude" / "worktrees" / "review-7").exists()


def test_body_without_a_block_stays_without_one(tmp_path):
    primary, env, f = opened(tmp_path)
    body = forge_shim(tmp_path, env)
    body.write_text("Body without a block\n")
    one_seat(primary)
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert body.read_text() == "Body without a block\n"


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


def one_seat(primary, name="a", pin="claude-x", family="anthropic", runtime="claude-code", header=True):
    """A plan with one headless worker item and its launcher-stamped report (ticket 1303)."""
    panel(primary, f"# budget: 10m\n{name}\t{pin}\t{family}\theadless {runtime}\n",
          {name: HEADLESS.format(pin=pin, family=family, runtime=runtime)} if header else None)


def plan_line(primary, f):
    return [ln for ln in answer_text(primary, f).splitlines() if ln.startswith("plan check:")]


def test_failed_plan_check_reaches_the_comment_as_fail(tmp_path):
    """Ticket 1267: the verdict is the checker's, copied by the script. A free-text
    manifest (the format that produced a model-relabelled PASS) is a FAIL."""
    primary, env, f = opened(tmp_path)
    panel(primary, "# budget: 10m\nOne seat reads the diff and the test.\n")
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}} — the model's reason\n{{seats}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = plan_line(primary, f)
    assert line.startswith("plan check: FAIL") and line.endswith("— the model's reason"), line
    assert "{{" not in answer_text(primary, f)


def test_missing_panel_is_a_failed_plan_check(tmp_path):
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text("{{plan_check}}\n{{seats}}\n")
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
    comment.write_text("{{plan_check}}\n{{seats}}\n")
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
    comment.write_text("result: REVIEWED\n{{seats}}\n" + re.sub(r"<[^>]*>", "none", tmpl) + "\n")
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


def test_findings_follow_their_generated_reviewer_line(tmp_path):
    """The file holds findings only, keyed by seat; the script writes each reviewer line and
    puts the seat's findings under it, once, in the answer's attribution."""
    primary, env, f = opened(tmp_path)
    body = seats_shim(tmp_path, env)
    panel(primary, "# budget: 10m\na\tclaude-x\tanthropic\theadless claude-code\nb\tclaude-y\tanthropic\theadless claude-code\n",
          # A cited report: a bare verdict is a hollow seat since ticket 1361.
          {n: HEADLESS.format(pin=p, family="anthropic", runtime="claude-code") + "read scripts/x.py:3\n"
           for n, p in (("a", "claude-x"), ("b", "claude-y"))})
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n")
    finding = "finding: a · verifiable · scripts/x.py:3 · adopted: yes\n"
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, finding), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    lines = answer_attr(primary, f)
    assert [ln.split(" · ")[1] if ln.startswith("reviewer") else "finding" for ln in lines] == ["seat=a", "finding", "seat=b"]
    assert "seat=a" not in body.read_text()


# --- ticket 1303: the identity lines are generated, never typed --------------------------------

def seat_close(tmp_path, primary, env, attr="", extra=()):
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n")
    return run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path, attr), "--comment-file", str(comment), *extra],
               primary, env)


def seat_lines_of(text):
    return [ln for ln in text.splitlines() if ln.startswith("seat: ")]


def test_gaze_close_derives_the_1853_seat(tmp_path):
    """Replay of PR #1853: plan item `consistency`, `--role code-reviewer`, bare pin `gpt-6-luna`.
    One name, a provider-qualified model, and the capture then raises no failure."""
    primary, env, f = opened(tmp_path)
    seats_shim(tmp_path, env)
    one_seat(primary, name="consistency", pin="gpt-6-luna", family="openai", runtime="codex")
    r = seat_close(tmp_path, primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = seat_lines_of(answer_text(primary, f))
    assert line.startswith("seat: consistency · runtime=codex") and "model=openai/gpt-6-luna" in line
    assert "code-reviewer" not in answer_text(primary, f) and "FAILED" not in r.stdout
    reviewers = [ln for ln in answer_attr(primary, f) if ln.startswith("reviewer: ")]
    assert len(reviewers) == 1 and "seat=consistency" in reviewers[0] and "model=openai/gpt-6-luna" in reviewers[0]
    import sys
    sys.path.insert(0, str(Path(CLOSE).parent))
    import attribution_record
    assert attribution_record.seat_lines(answer_text(primary, f), "\n".join(reviewers)) == ([], [])


@pytest.mark.parametrize("typed", ["seat: a · runtime=x", "  seat: a", "> seat: a", "**seat:** a"])
def test_typed_seat_line_or_missing_placeholder_is_refused(tmp_path, typed):
    primary, env, f = opened(tmp_path)
    one_seat(primary)
    comment = tmp_path / "c.md"
    comment.write_text(f"result: REVIEWED\n{{{{plan_check}}}}\n{{{{seats}}}}\n{typed}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 2 and "seats" in r.stderr
    comment.write_text("result: REVIEWED\n{{plan_check}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 2 and "{{seats}}" in r.stderr
    assert (primary / ".claude" / "worktrees" / "review-7").exists() and not (tmp_path / "gh.log").exists()


@pytest.mark.parametrize("attr,why", [
    ("finding: ghost · verifiable · scripts/x.py:3 · adopted: yes\n", "absent from the plan"),
    ("finding: failing · verifiable · scripts/x.py:3 · adopted: yes\n", "did not run"),
    ("reviewer: step=review · seat=a · runtime=x · model=m/n · status: ran\n", "holds only"),
    ("  finding: verifiable · scripts/x.py:3 · adopted: yes\n", "holds only"),
])
def test_attribution_file_is_findings_of_seats_in_the_plan(tmp_path, attr, why):
    """Exit criterion: a finding naming a seat absent from the plan refuses the close (non-zero,
    nothing removed, appended or posted); so does a typed reviewer line, or a seat that failed."""
    primary, env, f = opened(tmp_path)
    body = seats_shim(tmp_path, env)
    before = body.read_text()
    panel(primary, "# budget: 10m\na\tclaude-x\tanthropic\theadless claude-code\n"
                   "failing\tgpt-6-luna\topenai\theadless codex\n",
          {"a": HEADLESS.format(pin="claude-x", family="anthropic", runtime="claude-code")})
    r = seat_close(tmp_path, primary, env, attr)
    assert r.returncode == 2 and why in r.stderr, r.stdout + r.stderr
    assert (primary / ".claude" / "worktrees" / "review-7").exists()
    assert body.read_text() == before and not (tmp_path / "gh.log").exists()


def test_subagent_seat_takes_the_pin_not_its_typed_header(tmp_path):
    """Blind-Spot 1: a subagent types its own `worker:` header, so the line takes the manifest pin
    and the session's runtime and says route=subagent, whatever the header claims."""
    primary, env, f = opened(tmp_path)
    seats_shim(tmp_path, env)
    panel(primary, "# budget: 10m\nscope\tclaude-x\tanthropic\tsubagent\n",
          {"scope": "worker: model=made-up-model · family=anthropic · runtime=elsewhere\nverdict: clear\n"})
    r = seat_close(tmp_path, primary, env, extra=["--session-runtime", "claude-code"])
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = seat_lines_of(answer_text(primary, f))
    assert "runtime=claude-code" in line and "route=subagent" in line and "model=anthropic/claude-x" in line
    assert "made-up-model" not in line and "elsewhere" not in line


def test_subagent_seat_forging_a_headless_header_takes_the_pin(tmp_path):
    """Blind-Spot 1: a header claiming door=headless is trusted only when the manifest reason also
    names `headless <runtime>`; a subagent seat forging one still takes the pin and the session."""
    primary, env, f = opened(tmp_path)
    seats_shim(tmp_path, env)
    panel(primary, "# budget: 10m\nscope\tclaude-x\tanthropic\tsubagent\n",
          {"scope": "worker: model=made-up-model · family=anthropic · runtime=codex · door=headless\n"
                    "verdict: clear\n"})
    r = seat_close(tmp_path, primary, env, extra=["--session-runtime", "claude-code"])
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = seat_lines_of(answer_text(primary, f))
    assert "runtime=claude-code" in line and "route=subagent" in line and "model=anthropic/claude-x" in line
    assert "made-up-model" not in line and "codex" not in line


def test_failed_seat_still_captures_with_its_planned_pin(tmp_path):
    """Blind-Spot 2: a seat that filed no report keeps its pin and the runtime its reason names
    (status failed), so the capture is not blocked by `model=not observed`."""
    primary, env, f = opened(tmp_path)
    body = seats_shim(tmp_path, env)
    one_seat(primary, name="late", pin="gpt-6-luna", family="openai", runtime="codex", header=False)
    r = seat_close(tmp_path, primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = seat_lines_of(answer_text(primary, f))
    assert "runtime=codex" in line and "model=openai/gpt-6-luna" in line and line.endswith("status: failed")
    (reviewer,) = answer_attr(primary, f)
    assert "seat=late" in reviewer and reviewer.endswith("status: failed")
    assert "seat=late" not in body.read_text()


def test_pi_any_provider_seat_keeps_its_exact_qualifier(tmp_path):
    """Blind-Spot 5: pi's door serves any provider, so the qualifier is the pin's own prefix
    (padme/...), not a family-string rule."""
    primary, env, f = opened(tmp_path)
    seats_shim(tmp_path, env)
    one_seat(primary, name="local", pin="padme/qwen3.8-flash-next-iq3_s", family="qwen", runtime="pi")
    r = seat_close(tmp_path, primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = seat_lines_of(answer_text(primary, f))
    assert "runtime=pi" in line and "model=padme/qwen3.8-flash-next-iq3_s" in line


def test_self_seat_takes_the_session_identity(tmp_path):
    primary, env, f = opened(tmp_path)
    seats_shim(tmp_path, env)
    panel(primary, "# budget: 10m\nself\tself\tanthropic\tgaze\n", {"self": "worker: self · family=anthropic\nok\n"})
    r = seat_close(tmp_path, primary, env, extra=["--session-runtime", "claude-code", "--session-model", "claude-x"])
    assert r.returncode == 0, r.stdout + r.stderr
    (line,) = seat_lines_of(answer_text(primary, f))
    assert "runtime=claude-code" in line and "route=self" in line and "model=anthropic/claude-x" in line


def test_self_seat_without_a_session_model_is_loud_not_invented(tmp_path):
    primary, env, f = opened(tmp_path)
    seats_shim(tmp_path, env)
    panel(primary, "# budget: 10m\nself\tself\tanthropic\tgaze\n", {"self": "worker: self · family=anthropic\nok\n"})
    r = seat_close(tmp_path, primary, env)
    assert r.returncode == 2 and "model not observed" in r.stdout


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
    seats_shim(tmp_path, env)
    panel(primary, "# budget: 10m\nself\tself\tanthropic\tgaze\nredteam\to\topenai\theadless codex\n", reports)
    comment = tmp_path / "c.md"
    line = claim[len("<key>"):] if claim.startswith("<key>") else f"seats: {claim}"
    comment.write_text(f"result: REVIEWED\n{line}\n{{{{plan_check}}}}\n{{{{seats}}}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment),
                    "--session-runtime", "claude-code", "--session-model", "claude-x"], primary, env)
    assert r.returncode == code, r.stdout + r.stderr
    if code:
        assert "seats: self-only" in r.stderr
        assert (primary / ".claude" / "worktrees" / "review-7").exists()
        assert not (tmp_path / "gh.log").exists()


@pytest.mark.parametrize("line,value", [
    ("seats: panel", "panel"), ("Seats: panel", "panel"), ("- seats: panel", "panel"),
    ("> seats: panel", "panel"), ("### seats: panel", "panel"), ("seats : panel", "panel"),
    ("**seats:** panel", "panel"), ("seats: self-only", "self-only"), ("result: REVIEWED", None),
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
    text = "result: REVIEWED\nintent: default\n**seats:** panel\n"
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
    comment.write_text(f"result: REVIEWED\nreviewed_head_sha: {f['head']}\nintent: default\n{{{{plan_check}}}}\n{{{{seats}}}}\n")
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
    comment.write_text("result: FINDINGS\nintent: default\n{{plan_check}}\n{{seats}}\n")
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
    comment.write_text("## /gaze result\n\nresult: FINDINGS\n{{plan_check}}\n{{seats}}\nFindings: one\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert "pointer: posted" in r.stdout, r.stdout + r.stderr
    assert posted(tmp_path) == f"/gaze review on notes: {f['review_id']}, verdict FINDINGS\n"
    assert "Findings: one" in answer_text(primary, f)


def test_pointer_failure_ignored_exit_zero(tmp_path):
    primary, env, f = opened(tmp_path)
    shim = tmp_path / "bin" / "gh"
    shim.write_text(shim.read_text().replace('  comment) printf', '  comment) echo refused >&2; exit 1; printf'))
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "pointer: not posted" in r.stdout and "result: REVIEWED" in answer_text(primary, f)


def test_pointer_holds_no_seat_line(tmp_path):
    """The seat lines live in the notes answer; the posted pointer holds no `seat:` line."""
    primary, env, f = opened(tmp_path)
    seats_shim(tmp_path, env)
    one_seat(primary)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "seat=a" in answer_attr(primary, f)[0]
    assert "seat:" not in posted(tmp_path)


def test_pointer_timeout_ignored_and_seats_still_run(monkeypatch, capsys):
    """A `gh pr comment` that times out is a refused pointer, not a crash: pointer() returns, so
    main() keeps its exit code."""
    import subprocess
    import sys
    sys.path.insert(0, str(Path(CLOSE).parent))
    import forge
    import gaze_close

    def slow(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, kw.get("timeout", 120))

    monkeypatch.setattr(forge.subprocess, "run", slow)
    monkeypatch.setattr(gaze_close.forge, "get_forge", lambda choice, pr, cwd=None: forge.GhForge())
    gaze_close.pointer("/nowhere", "7", "REVIEWED", identity={"review_id": "r1"})
    assert "pointer: not posted" in capsys.readouterr().out


def foreign_repo(tmp_path):
    """An unrelated repository: where a runtime may leave the shell while a review closes (ticket 1356)."""
    other = tmp_path / "other"
    other.mkdir()
    git(other, "init", "-q", "-b", "main")
    return other


def test_close_from_foreign_cwd_records_the_real_panel(tmp_path):
    """Ticket 1356: run from another project's cwd with --repo, the close reads the real panel's
    seats, removes the real review tree and posts the pointer to the real repository's PR."""
    primary, env, f = opened(tmp_path)
    shim = tmp_path / "bin" / "gh"
    shim.write_text(shim.read_text().replace('"$5" >> "$MOCK_GH_LOG"', '"$PWD $5" >> "$MOCK_GH_LOG"'))
    one_seat(primary)
    other = foreign_repo(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\nseats: panel\n{{plan_check}}\n{{seats}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--repo", str(primary), *ATTR(tmp_path), "--comment-file", str(comment)],
            other, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "self-only" not in r.stdout + r.stderr
    text = answer_text(primary, f)
    assert "seat: " in text and "plan check: PASS" in text
    assert not (primary / ".claude" / "worktrees" / "review-7").exists()
    (line,) = posted(tmp_path).splitlines()
    assert line.startswith(f"{primary.resolve()} /gaze review on notes:"), line


def test_containment_reports_the_session_tree_not_a_moved_cwd(tmp_path):
    """Ticket 1356: setup records the session tree; a close whose cwd moved to the main checkout
    judges the recorded tree and branch, not the new cwd."""
    primary, env = make_repo(tmp_path)
    session = tmp_path / "session"
    git(primary, "worktree", "add", "-q", "-b", "t1-work", str(session), "main")
    r = run(SETUP, ["7"], session, env)
    assert r.returncode == 0, r.stderr
    f = fields(r.stdout)
    assert f["repo"] == str(primary.resolve())
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n{{containment}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", "--repo", str(primary), *ATTR(tmp_path), "--comment-file", str(comment)],
            primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "differs from entry branch" not in r.stdout
    assert f"toplevel={session.resolve()} branch=t1-work" in r.stdout


def test_legacy_entry_state_without_session_tree_closes_from_cwd(tmp_path):
    primary, env, f = opened(tmp_path)
    state = primary / ".claude" / "worktrees" / "review-7" / ".panel" / "7" / "entry-state.json"
    import json
    d = json.loads(state.read_text())
    d.pop("session_tree", None)
    state.write_text(json.dumps(d))
    comment = tmp_path / "c.md"
    comment.write_text("result: REVIEWED\n{{plan_check}}\n{{seats}}\n{{containment}}\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"toplevel={primary.resolve()}" in r.stdout


CANARY = "sk-proj-CANARY0123456789"


def canary_close(tmp_path):
    """Close with a result text that quotes a seat body carrying a canary secret, as gaze
    does for preserved dissent (panel.md); the answer entry is what lands on refs/notes/review."""
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text(f"result: REVIEWED\nreviewed_head_sha: {f['head']}\n{{{{plan_check}}}}\n{{{{seats}}}}\n"
                       f"dissent (seat verbatim): config read /home/jane/.codex/auth.json "
                       f"token: {CANARY} mail jane.doe@example.org\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    return answer_text(primary, f), f['head']


def test_seat_body_quoted_into_the_answer_is_scrubbed_before_notes(tmp_path):
    text, _ = canary_close(tmp_path)
    for leaked in (CANARY, "jane.doe", "example.org", "/home/jane"):
        assert leaked not in text
    assert "<redacted>" in text


def test_scrubbing_the_answer_leaves_verdict_head_and_seat_lines_intact(tmp_path):
    text, head = canary_close(tmp_path)
    assert "result: REVIEWED\n" in text and f"reviewed_head_sha: {head}\n" in text
    assert "{{" not in text


def test_scrub_of_secret_labels_at_line_end_keeps_every_parsed_field_line(tmp_path):
    primary, env, f = opened(tmp_path)
    comment = tmp_path / "c.md"
    comment.write_text(f"result: REVIEWED\nreviewed_head_sha: {f['head']}\n{{{{plan_check}}}}\n{{{{seats}}}}\n"
                       "intent: inspect access_token:\nreview plan: checks one to three\n"
                       "intent: rotate the api key:\nseats: self-only\nran: pytest -q\n")
    r = run(CLOSE, ["7", "--branch", "feature", *ATTR(tmp_path), "--comment-file", str(comment)], primary, env)
    assert r.returncode == 0, r.stdout + r.stderr
    text = answer_text(primary, f)
    for line in ("result: REVIEWED", f"reviewed_head_sha: {f['head']}", "review plan: checks one to three",
                 "seats: self-only", "ran: pytest -q"):
        assert line + "\n" in text, line
    assert "plan check:" in text

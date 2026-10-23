"""Behavioral contract for tool-backed manuscript review (synthetic streams)."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/manuscript-review/manuscript_review.py"
spec = importlib.util.spec_from_file_location("manuscript_review", SCRIPT)
mr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mr)


def stream(payload, *, truncated=False, failed_fetch=False):
    events = [{"type": "system", "subtype": "init", "model": "observed-model"}]
    tools = [("Read", {"file_path": "/run/private/main/0001.txt"}),
             ("Read", {"file_path": "/run/private/main/0001.png"}),
             ("WebSearch", {"query": "closest prior work"}),
             ("WebFetch", {"url": "https://example.org/paper"})]
    for i, (name, args) in enumerate(tools):
        events.append({"type": "assistant", "message": {"model": "observed-model",
                      "content": [{"type": "tool_use", "id": str(i), "name": name,
                                   "input": args}]}})
        events.append({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": str(i), "content": "Source passage",
             "is_error": failed_fetch and name == "WebFetch"}]}})
    if not truncated:
        events.append({"type": "result", "subtype": "success", "is_error": False,
                       "result": json.dumps(payload)})
    return "\n".join(json.dumps(e) for e in events) + "\n"


def manifest():
    return {"documents": [{"id": "main", "pages": [{"page": 1,
            "text": "private/main/0001.txt", "image": "private/main/0001.png"}]}]}


def review():
    return {"review": "\n".join("## " + h + "\n" + (
                "R1-01 The central claim outruns the evidence." if h == "Key claims"
                else "Specific assessment.") for h in mr.SECTIONS),
            "findings": [{"id": "R1-01", "text": "The central claim outruns the evidence.",
                          "severity": "major", "uncertainty": "medium", "decisive_urls": [],
                          "evidence": [{"document": "main", "page": 1,
                                        "passage": "The manuscript claims X"}]}]}


def test_empty_truncated_and_failed_retrieval_never_complete():
    for raw in ("", stream(review(), truncated=True), stream(review(), failed_fetch=True)):
        with pytest.raises(ValueError):
            mr.validate_stage(raw, 0, manifest(), Path("/run"), "review")
    with pytest.raises(ValueError, match="exit"):
        mr.validate_stage(stream(review()), 1, manifest(), Path("/run"), "review")
    empty = review()
    empty["review"] = "\n".join("## " + h for h in mr.SECTIONS) + "\n"
    with pytest.raises(ValueError, match="empty review"):
        mr.validate_stage(stream(empty), 0, manifest(), Path("/run"), "review")


def test_actual_reads_and_retrieval_are_required():
    raw = stream(review())
    payload, trace = mr.validate_stage(raw, 0, manifest(), Path("/run"), "review")
    assert payload == review()
    assert trace["observed_models"] == ["observed-model"]
    assert len(trace["successful_tools"]) == 4
    without_image = raw.replace("/run/private/main/0001.png", "/run/wrong.png")
    with pytest.raises(ValueError, match="coverage"):
        mr.validate_stage(without_image, 0, manifest(), Path("/run"), "review")


def test_unknown_page_and_missing_major_evidence_fail():
    data = review()
    data["findings"][0]["evidence"][0]["page"] = 2
    with pytest.raises(ValueError, match="page"):
        mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "review")


def test_verifier_requires_each_major_and_four_distinct_checks():
    check = {"finding_id": "R1-01", "factual_status": "confirmed",
             "severity": "major", "uncertainty": "medium", "reason": "Located passage",
             "evidence": [{"document": "main", "page": 1, "passage": "X"}],
             "sources": [{"url": "https://example.org/paper", "accessible": "yes",
                          "identity": "yes", "relevant": "yes", "supports_claim": "no",
                          "passage": "Source passage", "locator": "p. 4"}]}
    data = {"verification": [check]}
    mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "verify", review())
    del check["sources"][0]["identity"]
    with pytest.raises(ValueError, match="identity"):
        mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "verify", review())


def test_new_run_refuses_overwrite_and_links_previous(tmp_path):
    run = tmp_path / "release/2026-10-23/review/attempt-1"
    mr.create_run(run, None)
    (run / "original.txt").write_text("untouched")
    with pytest.raises(FileExistsError):
        mr.create_run(run, None)
    second = run.parent / "attempt-2"
    mr.create_run(second, run)
    assert json.loads((second / "history.json").read_text())["previous_run"] == str(run)
    assert (run / "original.txt").read_text() == "untouched"


def test_ledger_export_keeps_author_decisions_pending():
    rows = mr.ledger_records(review(), {"verification": []}, "round-1", "review.md")
    assert rows[0]["disposition"] is None
    assert rows[0]["resolution"] == "open"
    assert rows[0]["reason"] == ""
    assert rows[0]["text"] == review()["findings"][0]["text"]
    assert rows[0]["id"] == "round-1-R1-01"
    assert all(isinstance(item, str) and item for item in rows[0]["evidence"])


def test_source_excerpt_preserves_quotes_newlines_and_text_blocks():
    content = [{"type": "text", "text": 'The "claim"\nhas support.'}]
    assert mr.tool_text(content) == 'The "claim"\nhas support.'
    assert mr.tool_text('The "claim"\nhas support.') == 'The "claim"\nhas support.'
    check = {"finding_id": "R1-01", "factual_status": "confirmed", "severity": "major",
             "uncertainty": "low", "reason": "Read source", "evidence": review()["findings"][0]["evidence"],
             "sources": [{"url": "https://example.org/paper", "accessible": "yes", "identity": "yes",
                          "relevant": "yes", "supports_claim": "yes", "locator": "section 1",
                          "passage": 'The "claim"\nhas support.'}]}
    events = [json.loads(line) for line in stream({"verification": [check]}).splitlines()]
    for event in events:
        for block in event.get("message", {}).get("content", []):
            if block.get("type") == "tool_result" and block.get("tool_use_id") == "3":
                block["content"] = content
    mr.validate_stage("\n".join(json.dumps(event) for event in events), 0, manifest(), Path("/run"),
                      "verify", review())


def test_partial_reads_cannot_establish_page_coverage():
    raw = stream(review()).replace('"file_path": "/run/private/main/0001.txt"',
                                  '"file_path": "/run/private/main/0001.txt", "limit": 1')
    with pytest.raises(ValueError, match="coverage"):
        mr.validate_stage(raw, 0, manifest(), Path("/run"), "review")


@pytest.mark.parametrize("case", ["empty", "extra", "unenumerated"])
def test_markdown_criticisms_cannot_disappear_from_findings(case):
    data = review()
    if case == "empty":
        data["findings"] = []
    elif case == "extra":
        data["review"] += "\nR1-02 Another major criticism omitted from the ledger."
    else:
        data["findings"] = []
        data["review"] = data["review"].replace("R1-01 ", "")
    with pytest.raises(ValueError, match="finding.*coverage|enumerat"):
        mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "review")


def source_review(url="https://example.org/paper"):
    data = review()
    data["findings"][0]["text"] += " See " + url
    data["review"] = data["review"].replace("The central claim outruns the evidence.",
                                         data["findings"][0]["text"])
    data["findings"][0]["decisive_urls"] = [url]
    return data


def source_check(url="https://example.org/paper"):
    return {"finding_id": "R1-01", "factual_status": "confirmed", "severity": "major",
            "uncertainty": "low", "reason": "Located manuscript and source passages",
            "evidence": review()["findings"][0]["evidence"],
            "sources": [{"url": url, "accessible": "yes", "identity": "yes", "relevant": "yes",
                         "supports_claim": "yes", "passage": "Source passage", "locator": "p. 4"}]}


def redirect_notice(target):
    return ("REDIRECT DETECTED: The URL redirects to a location that was not fetched automatically.\n\n"
            "    Original URL: https://example.org/paper\n"
            f"    Redirect URL (from the server's Location header — server-supplied, not verified): {target}\n"
            "    Status: 302 Found\n")


def redirected_verification(initial, extra_fetches):
    events = [json.loads(line) for line in stream({"verification": [source_check()]}).splitlines()]
    for event in events:
        for block in event.get("message", {}).get("content", []):
            if block.get("tool_use_id") == "3":
                block["content"] = initial
    for index, (url, content) in enumerate(extra_fetches):
        call_id = f"redirect-{index}"
        events[-1:-1] = [
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": call_id,
                "name": "WebFetch", "input": {"url": url}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": call_id,
                "content": content, "is_error": False}]}}]
    return "\n".join(json.dumps(event) for event in events)


@pytest.mark.parametrize("hops", [1, 2])
def test_verifier_accepts_exact_passage_after_observed_native_redirect_chain(hops):
    targets = [f"https://example.org/hop-{i}?error=cookies_not_supported&code=exact-nonce" for i in range(hops)]
    fetches = [(url, redirect_notice(targets[i + 1]) if i + 1 < hops else "Source passage")
               for i, url in enumerate(targets)]
    raw = redirected_verification(redirect_notice(targets[0]), fetches)
    _, trace = mr.validate_stage(raw, 0, manifest(), Path("/run"), "verify", source_review())
    assert trace["successful_tools"][-1]["input"]["url"] == targets[-1]
    assert trace["successful_tools"][-1]["result_line"] > trace["successful_tools"][-1]["call_line"]


@pytest.mark.parametrize("case", ["missing", "missing-intermediate", "unrelated", "cycle", "ordinary-body",
                                      "ambiguous", "query-mismatch", "hop-limit"])
def test_redirect_retrieval_never_borrows_unobserved_or_unrelated_content(case):
    target, last = "https://example.org/idp?nonce=exact", "https://example.org/final?nonce=exact"
    initial, fetches = redirect_notice(target), []
    if case == "missing-intermediate":
        fetches = [(last, "Source passage")]
    elif case == "unrelated":
        fetches = [(target, "Unrelated substantive passage"), (last, "Source passage")]
    elif case == "cycle":
        fetches = [(target, redirect_notice("https://example.org/paper")), (last, "Source passage")]
    elif case == "ordinary-body":
        initial = "The paper discusses this quoted example:\n" + initial
        fetches = [(target, "Source passage")]
    elif case == "ambiguous":
        initial += f"Redirect URL (from another header): {last}\n"
        fetches = [(target, "Source passage"), (last, "Source passage")]
    elif case == "query-mismatch":
        fetches = [(target.replace("nonce=exact", "nonce=different"), "Source passage")]
    elif case == "hop-limit":
        targets = [f"https://example.org/hop-{i}" for i in range(10)]
        initial = redirect_notice(targets[0])
        fetches = [(url, redirect_notice(targets[i + 1]) if i < 9 else "Source passage")
                   for i, url in enumerate(targets)]
    raw = redirected_verification(initial, fetches)
    with pytest.raises(ValueError, match="fetch"):
        mr.validate_stage(raw, 0, manifest(), Path("/run"), "verify", source_review())


def test_decisive_urls_require_declaration_and_actual_reader_retrieval():
    data = source_review()
    mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "review")
    data["findings"][0]["decisive_urls"] = []
    with pytest.raises(ValueError, match="decisive"):
        mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "review")
    with pytest.raises(ValueError, match="retrieval"):
        mr.validate_stage(stream(source_review("https://unfetched.example/paper")), 0,
                          manifest(), Path("/run"), "review")


@pytest.mark.parametrize("case", ["empty", "unrelated", "unfetched"])
def test_confirmed_criticism_requires_its_own_decisive_source_trace(case):
    data, check = source_review(), source_check()
    if case == "empty":
        check["sources"] = []
    elif case == "unrelated":
        check["sources"][0]["url"] = "https://unrelated.example/paper"
    else:
        data = source_review("https://unfetched.example/paper")
        check = source_check("https://unfetched.example/paper")
    with pytest.raises(ValueError, match="decisive|fetch"):
        mr.validate_stage(stream({"verification": [check]}), 0, manifest(), Path("/run"),
                          "verify", data)


def test_unavailable_decisive_source_retains_unknown_and_factual_uncertainty():
    url = "https://unavailable.example/paper"
    data, check = source_review(url), source_check(url)
    check["factual_status"] = "unverifiable"
    check["sources"][0].update(accessible="no", identity="yes", relevant="unknown",
                               supports_claim="unknown", passage="", locator="",
                               reason="Publisher metadata confirms identity; fulltext denied")
    events = [json.loads(line) for line in stream({"verification": [check]}).splitlines()]
    events[-1:-1] = [
        {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "failed",
            "name": "WebFetch", "input": {"url": url}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "failed",
            "content": "Publisher access denied", "is_error": True}]}}]
    raw = "\n".join(json.dumps(event) for event in events)
    _, trace = mr.validate_stage(raw, 0, manifest(), Path("/run"), "verify", data)
    assert trace["failed_tools"][0]["input"]["url"] == url
    check["factual_status"] = "confirmed"
    events[-1]["result"] = json.dumps({"verification": [check]})
    with pytest.raises(ValueError, match="unverifiable"):
        mr.validate_stage("\n".join(json.dumps(event) for event in events), 0,
                          manifest(), Path("/run"), "verify", data)


@pytest.mark.parametrize("manuscript_only", [False, True])
def test_verifier_retrieves_decisive_sources_without_gratuitous_search(manuscript_only):
    data, check = source_review(), source_check()
    omitted = {"2"}  # Search is unnecessary when decisive URLs are already known.
    if manuscript_only:
        data = review()
        check["sources"] = []
        omitted.add("3")  # Manuscript-only finding needs no external retrieval.
    events = [json.loads(line) for line in stream({"verification": [check]}).splitlines()]
    events = [event for event in events if not any(
        block.get("id", block.get("tool_use_id")) in omitted
        for block in event.get("message", {}).get("content", []))]
    raw = "\n".join(json.dumps(event) for event in events)
    mr.validate_stage(raw, 0, manifest(), Path("/run"), "verify", data)
    events[-1]["result"] = json.dumps(data)
    with pytest.raises(ValueError, match="search and fetch"):
        mr.validate_stage("\n".join(json.dumps(event) for event in events), 0,
                          manifest(), Path("/run"), "review")


def reader_attempt(tmp_path):
    original = tmp_path / "release/2026-10-23/review/original"
    mr.create_run(original, None)
    (original / "private/main").mkdir()
    for name in ("input.pdf", "0001.txt", "0001.png"):
        (original / "private/main" / name).write_text("Synthetic pinned " + name)
    data = manifest()
    data.update(clearance="public", revision="revision-1", question="Question",
                annex_inventory="No annexes expected", missing_annexes=[], prompt_source_sha256="source")
    data["documents"][0]["sha256"] = mr.digest(original / "private/main/input.pdf")
    for kind in ("text", "image"):
        page = data["documents"][0]["pages"][0]
        page[kind + "_sha256"] = mr.digest(original / page[kind])
    mr.write_json(original / "manifest.json", data)
    raw = stream(review()).replace("/run/", str(original) + "/")
    (original / "private/review.stream.jsonl").write_text(raw)
    (original / "private/review.prompt.txt").write_text("Original reader prompt")
    (original / "private/review.stderr.txt").write_text("")
    (original / "reader-prompt.md").write_text("Original source adaptation")
    payload, trace = mr.validate_stage(raw, 0, data, original, "review")
    mr.write_json(original / "review.json", payload)
    (original / "review.md").write_text(payload["review"] + "\n")
    mr.write_json(original / "review.trace.json", mr.durable_trace(trace))
    mr.write_json(original / "review.launch.json", {"requested_model": "original-model"})
    mr.write_json(original / "review.termination.json", {"exit_code": 0})
    mr.write_json(original / "status.json", {"status": "incomplete", "stage": "verify",
        "artifacts": {str(p.relative_to(original)): mr.digest(p) for p in original.rglob("*") if p.is_file()}})
    fresh = original.parent / "resumed"
    mr.create_run(fresh, original)
    return original, fresh, data


def test_reuse_reader_preserves_original_bundle_identity_and_scope(tmp_path):
    original, fresh, data = reader_attempt(tmp_path)
    before = {str(p.relative_to(original)): p.read_bytes() for p in original.rglob("*") if p.is_file()}
    assert mr.reuse_reader(original, fresh, data) == review()
    assert (fresh / "private/review.stream.jsonl").read_bytes() == before["private/review.stream.jsonl"]
    assert json.loads((fresh / "review.reuse.json").read_text())["observed_models"] == ["observed-model"]
    assert before == {str(p.relative_to(original)): p.read_bytes() for p in original.rglob("*") if p.is_file()}


@pytest.mark.parametrize("field", ["sha256", "question", "clearance", "revision", "missing_annexes", "annex_inventory"])
def test_reuse_reader_refuses_changed_inputs_or_scope(tmp_path, field):
    original, fresh, data = reader_attempt(tmp_path)
    if field == "sha256":
        data["documents"][0]["sha256"] = "changed"
    else:
        data[field] = "changed"
    with pytest.raises(ValueError, match="scope|inputs"):
        mr.reuse_reader(original, fresh, data)
    assert not (fresh / "review.json").exists()


@pytest.mark.parametrize("path", ["private/review.stream.jsonl", "review.json", "review.md",
                                      "private/main/0001.png", "review.termination.json"])
def test_reuse_reader_rejects_tampered_artifacts(tmp_path, path):
    original, fresh, data = reader_attempt(tmp_path)
    with (original / path).open("a") as handle:
        handle.write("tampered")
    with pytest.raises(ValueError, match="hash"):
        mr.reuse_reader(original, fresh, data)


def test_reuse_reader_rejects_existing_author_ledger(tmp_path):
    original, fresh, data = reader_attempt(tmp_path)
    (original / "ledger.jsonl").write_text('{"disposition":"accepted"}\n')
    with pytest.raises(ValueError, match="ledger"):
        mr.reuse_reader(original, fresh, data)


@pytest.mark.parametrize("name", ["review.json", "review.md"])
def test_reuse_reader_matches_saved_payload_to_raw_even_if_hash_refreshed(tmp_path, name):
    original, fresh, data = reader_attempt(tmp_path)
    path = original / name
    if name.endswith(".json"):
        changed = json.loads(path.read_text())
        changed["findings"][0]["severity"] = "minor"
        mr.write_json(path, changed)
    else:
        path.write_text(path.read_text() + "Unrecorded editorial change.\n")
    status = json.loads((original / "status.json").read_text())
    status["artifacts"][name] = mr.digest(path)
    mr.write_json(original / "status.json", status)
    with pytest.raises(ValueError, match="differs from original stream"):
        mr.reuse_reader(original, fresh, data)


def tiny_pdf(path, texts=None):
    """Synthetic one-page PDF; exercise the real page extraction/render tools."""
    texts = texts or ["Synthetic manuscript claim X."]
    kids = " ".join(f"{4 + 2 * i} 0 R" for i in range(len(texts)))
    objects = ["<< /Type /Catalog /Pages 2 0 R >>",
               f"<< /Type /Pages /Kids [{kids}] /Count {len(texts)} >>",
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    for i, paragraph in enumerate(texts):
        text = f"BT /F1 12 Tf 72 720 Td ({paragraph}) Tj ET"
        objects.extend(["<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                        f"/Resources << /Font << /F1 3 0 R >> >> /Contents {5 + 2 * i} 0 R >>",
                        f"<< /Length {len(text)} >>\nstream\n{text}\nendstream"])
    data, offsets = "%PDF-1.4\n", []
    for number, body in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{number} 0 obj\n{body}\nendobj\n"
    start = len(data)
    data += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    data += "".join(f"{offset:010d} 00000 n \n" for offset in offsets)
    data += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n"
    path.write_text(data)


@pytest.mark.integration
@pytest.mark.parametrize("truncate_verifier", [False, True])
@pytest.mark.parametrize("canonical_reader", [False, True])
def test_executable_cycle_retains_original_and_detects_truncated_verifier(tmp_path, truncate_verifier, canonical_reader):
    if not all(shutil.which(tool) for tool in ("pdfinfo", "pdftotext", "pdftoppm")):
        pytest.skip("poppler tools unavailable")
    run = tmp_path / "release/2026-10-23/review/attempt-1"
    pdf = tmp_path / "paper.pdf"
    tiny_pdf(pdf)
    data = review()
    if canonical_reader:
        del data["findings"][0]["text"]
        data["review"] = data["review"].replace("R1-01 The central claim outruns the evidence.",
                                               "### R1-01\nThe central claim outruns the evidence.")
    check = {"verification": [{"finding_id": "R1-01", "factual_status": "unverifiable",
             "severity": "major", "uncertainty": "Synthetic test only", "reason": "Test fixture",
             "evidence": [{"document": "main", "page": 1, "passage": "Synthetic claim"}],
             "sources": []}]}
    for name, payload in (("review", data), ("verify", check)):
        raw = stream(payload, truncated=truncate_verifier and name == "verify")
        events = [json.loads(line) for line in raw.splitlines()]
        insert = []
        for kind in ("txt", "png"):
            insert.extend([
                {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "annex-" + kind,
                    "name": "Read", "input": {"file_path": f"/run/private/annex-1/0001.{kind}"}}]}},
                {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "annex-" + kind,
                    "content": "Synthetic annex content", "is_error": False}]}}])
        events[0:0] = insert
        (tmp_path / f"{name}.jsonl").write_text(
            "\n".join(json.dumps(event) for event in events).replace("/run/", str(run) + "/") + "\n")
    fake = tmp_path / "claude"
    fake.write_text("#!/usr/bin/env python3\nimport pathlib,sys\n"
                    "prompt=sys.stdin.read()\n"
                    "assert sys.argv[sys.argv.index('--model')+1]=='explicit-test-token'\n"
                    "stage='verify' if 'Original review:\\n' in prompt else 'review'\n"
                    f"sys.stdout.write((pathlib.Path({str(tmp_path)!r})/(stage+'.jsonl')).read_text())\n")
    fake.chmod(0o755)
    command = [sys.executable, str(SCRIPT), "--manuscript", str(pdf), "--annex", str(pdf),
               "--annex-inventory", "one supplied annex", "--revision", "synthetic-revision-1",
               "--round", "round-1", "--run", str(run), "--clearance", "public", "--model",
               "explicit-test-token", "--effort", "high", "--route-reason", "synthetic test",
               "--question", "Synthetic behavioral test"]
    result = subprocess.run(command, env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]},
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == int(truncate_verifier), result.stderr
    status = json.loads((run / "status.json").read_text())
    assert status["status"] == ("incomplete" if truncate_verifier else "complete")
    assert (run / "review.md").read_text() == data["review"] + "\n"
    assert len(json.loads((run / "manifest.json").read_text())["documents"]) == 2
    assert (run / "private/annex-1/0001.png").is_file()
    assert json.loads((run / "review.termination.json").read_text())["exit_code"] == 0
    if not truncate_verifier:
        assert "Source passage" in (run / "verify.trace.json").read_text()
        assert all("content" not in t for t in json.loads((run / "review.trace.json").read_text())["successful_tools"]
                   if t["name"] == "Read")
    original = (run / "review.md").read_bytes()
    repeated = subprocess.run(command, env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]},
                              capture_output=True, text=True, timeout=30)
    assert repeated.returncode != 0
    assert (run / "review.md").read_bytes() == original
    if truncate_verifier:
        fresh = run.parent / "attempt-2"
        before = {str(p.relative_to(run)): p.read_bytes() for p in run.rglob("*") if p.is_file()}
        verify_path = tmp_path / "verify.jsonl"
        verify_path.write_text(verify_path.read_text().replace(str(run), str(fresh)) + json.dumps(
            {"type": "result", "subtype": "success", "is_error": False, "result": json.dumps(check)}) + "\n")
        fake.write_text(fake.read_text().replace("sys.stdout.write(", "assert stage=='verify'\nsys.stdout.write("))
        resumed = command.copy()
        resumed[resumed.index("--run") + 1] = str(fresh)
        result = subprocess.run([*resumed, "--resume-review", str(run)],
                                env={**os.environ, "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"]},
                                capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        assert json.loads((fresh / "status.json").read_text())["status"] == "complete"
        assert (fresh / "review.md").read_bytes() == original
        assert before == {str(p.relative_to(run)): p.read_bytes() for p in run.rglob("*") if p.is_file()}


def test_reader_uses_one_canonical_markdown_text_for_ledger():
    data = review()
    del data["findings"][0]["text"]
    criticism = "**A precise criticism.**\n\nIts evidence and feasible remedy belong to the same finding."
    data["review"] = data["review"].replace(
        "R1-01 The central claim outruns the evidence.", "### R1-01\n" + criticism)
    payload, _ = mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "review")
    assert payload["findings"][0]["text"] == criticism
    assert payload["review"] == data["review"]
    assert mr.ledger_records(payload, {"verification": []}, "round-1", "review.md")[0]["text"] == criticism


@pytest.mark.parametrize("replacement", ["R1-01 only a reference, not a finding block", "### R1-01\n",
    "### R1-01\nFirst\n### R1-01\nSecond"])
def test_canonical_finding_needs_one_nonempty_heading_block(replacement):
    data = review()
    del data["findings"][0]["text"]
    data["review"] = data["review"].replace("R1-01 The central claim outruns the evidence.", replacement)
    with pytest.raises(ValueError, match="finding|empty"):
        mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "review")


def pdf_source_stream(tmp_path, monkeypatch, case="valid"):
    cache = tmp_path / "cache"
    monkeypatch.setattr(mr, "CLI_PDF_CACHE", cache, raising=False)
    cache.mkdir()
    pdf = cache / ("../outside/native-session/tool-results/webfetch-source.pdf" if case == "outside-cache"
                   else "project/native-session/tool-results/webfetch-source.pdf")
    pdf.parent.mkdir(parents=True)
    tiny_pdf(pdf, ["Synthetic manuscript claim X.", "An unread decisive passage."])
    size = f"{pdf.stat().st_size / 1024:.1f}KB"
    receipt = f"Cannot extract raw PDF.\n\n[Binary content (application/pdf, {size}) also saved to {pdf}]"
    check = source_check()
    check["sources"][0]["passage"] = "Synthetic manuscript claim X."
    events = [json.loads(x) for x in stream({"verification": [check]}).splitlines()]
    events[-1]["session_id"] = "native-session"
    for event in events:
        for block in event.get("message", {}).get("content", []):
            if block.get("tool_use_id") == "3":
                block["content"] = receipt if case != "no-receipt" else "No downloadable PDF receipt."
    read_path = pdf if case != "unrelated" else pdf.with_name("webfetch-unrelated.pdf")
    pages = "1"
    if case == "unread":
        check["sources"][0]["passage"] = "An unread decisive passage."
    events[-1]["result"] = json.dumps({"verification": [check]})
    read = [{"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "pdf-read",
             "name": "Read", "input": {"file_path": str(read_path), "pages": pages}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "pdf-read",
             "is_error": case == "failed-read", "content": [
                 {"type": "text", "text": f"PDF pages extracted: 1 page(s) from {read_path} ({size})"},
                 {"type": "image", "source": {"type": "base64", "data": "native-image"}}]}]}}]
    events[1:1] = read if case == "before-fetch" else []
    if case != "before-fetch":
        events[-1:-1] = read
    if case == "changed-cache":
        pdf.write_bytes(pdf.read_bytes() + b"changed" * 100)
    if case == "wrong-session":
        events[-1]["session_id"] = "another-session"
    if case == "no-pages":
        del read[0]["message"]["content"][0]["input"]["pages"]
    if case == "no-images":
        read[1]["message"]["content"][0]["content"].pop()
    if case == "symlink":
        real = pdf.with_name("actual.pdf")
        pdf.rename(real)
        pdf.symlink_to(real)
    if case == "same-content-other-url":
        # An unrelated earlier fetch must not supply the accepted URL's receipt.
        for event in events:
            for block in event.get("message", {}).get("content", []):
                if block.get("id") == "3":
                    block["input"]["url"] = "https://example.org/other"
        events[-1:-1] = [
            {"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "late-fetch",
             "name": "WebFetch", "input": {"url": "https://example.org/paper"}}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "late-fetch",
             "content": receipt}]}}]

    run = tmp_path / "run"
    # Native manuscript reads must still refer to the pinned input paths.
    raw = "\n".join(json.dumps(x) for x in events).replace("/run/private/", str(run / "private") + "/")
    return raw, run, pdf


def test_pdf_passage_requires_native_fetch_receipt_and_read_page(tmp_path, monkeypatch):
    raw, run, pdf = pdf_source_stream(tmp_path, monkeypatch)
    payload, trace = mr.validate_stage(raw, 0, manifest(), run, "verify", source_review())
    receipt = payload["verification"][0]["sources"][0]["pdf_evidence"]
    assert receipt["page"] == 1
    assert receipt["pdf_sha256"] == mr.digest(pdf)
    assert (run / receipt["pdf"]).read_bytes() == pdf.read_bytes()
    assert "Synthetic manuscript claim X." in (run / receipt["text"]).read_text()
    assert receipt["fetch_result_line"] < receipt["read_call_line"] < receipt["read_result_line"]
    pdf.unlink()
    assert (run / receipt["pdf"]).is_file(), "evidence must outlive the native cache"


@pytest.mark.parametrize("case", ["no-receipt", "unrelated", "unread", "before-fetch", "failed-read",
                                  "changed-cache", "wrong-session", "outside-cache", "no-pages", "no-images",
                                  "symlink", "same-content-other-url"])
def test_pdf_proof_rejects_unlinked_unread_or_changed_cache(tmp_path, monkeypatch, case):
    raw, run, _ = pdf_source_stream(tmp_path, monkeypatch, case)
    with pytest.raises(ValueError, match="passage|fetch"):
        mr.validate_stage(raw, 0, manifest(), run, "verify", source_review())


def test_existing_literal_legacy_reader_stays_replayable():
    data = review()
    data["review"] = data["review"].replace("R1-01 The central claim outruns the evidence.",
        "### R1-01\nThe central claim outruns the evidence.\n### R1-01\nAnother legacy mention.")
    payload, _ = mr.validate_stage(stream(data), 0, manifest(), Path("/run"), "review")
    assert payload == data

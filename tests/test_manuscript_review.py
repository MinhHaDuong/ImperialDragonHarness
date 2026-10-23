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


def tiny_pdf(path):
    """Synthetic one-page PDF; exercise the real page extraction/render tools."""
    text = "BT /F1 12 Tf 72 720 Td (Synthetic manuscript claim X.) Tj ET"
    objects = ["<< /Type /Catalog /Pages 2 0 R >>",
               "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
               "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
               "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
               f"<< /Length {len(text)} >>\nstream\n{text}\nendstream"]
    data, offsets = "%PDF-1.4\n", []
    for number, body in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{number} 0 obj\n{body}\nendobj\n"
    start = len(data)
    data += "xref\n0 6\n0000000000 65535 f \n"
    data += "".join(f"{offset:010d} 00000 n \n" for offset in offsets)
    data += f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n"
    path.write_text(data)


@pytest.mark.integration
@pytest.mark.parametrize("truncate_verifier", [False, True])
def test_executable_cycle_retains_original_and_detects_truncated_verifier(tmp_path, truncate_verifier):
    if not all(shutil.which(tool) for tool in ("pdfinfo", "pdftotext", "pdftoppm")):
        pytest.skip("poppler tools unavailable")
    run = tmp_path / "release/2026-10-23/review/attempt-1"
    pdf = tmp_path / "paper.pdf"
    tiny_pdf(pdf)
    data = review()
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

#!/usr/bin/env python3
"""Read-only audit probes; fake APIs and temporary files, no model/network calls.

Run from audit checkpoint1206b23e (old source interfaces), with development Python:
    python docs/audits/2026-10-23-skills-metier/probes.py

The intentionally defective outcomes describe the audited revision; this is
an evidence capture, not a permanent ratchet requiring those defects to remain.
"""

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    # Checkpoint-bound: the audited helper was retired by PR 1633; replay from
    # the audited revision (b4b863c6), not from HEAD, as the README states.
    review = load("audit_review", "skills/external-peer-review/peer_review.py")
    validate = load("audit_validate", "scripts/validate-refs.py")
    bib = load("audit_bib", "scripts/bib-merge.py")
    ingest = load("audit_ingest", "skills/ingest-decision-letter/ingest_letter.py")
    evidence = []

    class FakeClient:
        def __init__(self, **kwargs):
            self.chat = types.SimpleNamespace(completions=self)

        def create(self, **kwargs):
            return types.SimpleNamespace(
                choices=[types.SimpleNamespace(
                    message=types.SimpleNamespace(content=""), finish_reason="length"
                )]
            )

    with tempfile.TemporaryDirectory(prefix="metier-audit-") as temp:
        root = Path(temp)
        fake = types.SimpleNamespace(OpenAI=FakeClient)
        with patch.dict(sys.modules, {"openai": fake}):
            path = review.review_one(
                "fake/model", "student", root / "unused.pdf", "FAKE_SENTINEL",
                "task", "unused", 1, root, None, "manuscript text"
            )
            evidence.append({
                "probe": "review_empty_truncated_response",
                "returns_normally": True,
                "artifact_contains_only_header": path.read_text().strip().startswith(
                    "# Peer review"
                ) and len(path.read_text().splitlines()) == 3,
            })
            path.write_text("PREVIOUS_REVIEW")
            review.review_one(
                "fake/model", "student", root / "unused.pdf", "FAKE_SENTINEL",
                "task", "unused", 1, root, None, "manuscript text"
            )
            evidence.append({
                "probe": "review_second_run",
                "previous_review_preserved": "PREVIOUS_REVIEW" in path.read_text(),
            })

        note = root / "note.md"
        note.write_text(
            "## Methods\nprobe\n## Bibliography\n"
            "@article{inline, title={Valid inline entry}, doi={10.0000/example}}\n"
        )
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            status = validate.main(["validate-refs.py", str(note)])
        evidence.append({
            "probe": "validator_valid_inline_entry",
            "positive_control_parsed_by_bib_merge": len(bib.parse_bibtex(note.read_text())),
            "validator_entries": len(validate._split_entries(
                validate._extract_bibliography_block(note.read_text())
            )),
            "exit": status,
            "verdict": stdout.getvalue().strip().split(" — ")[0],
        })
        note.write_text(
            "## Methods\nprobe\n## Bibliography\n"
            "@article{wrong,\n title={Intended article},\n"
            " url={https://example.org/requested},\n}\n"
        )
        stdout = io.StringIO()
        with patch.object(validate, "_fetch", return_value=(
            200, "https://example.org/wrong-article", False
        )), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            status = validate.main(["validate-refs.py", str(note)])
        evidence.append({
            "probe": "validator_wrong_document_http200",
            "exit": status,
            "verdict": stdout.getvalue().strip(),
            "interpretation": "HTTP reachability only, no work-identity check",
        })

        record = {"id": "R1-01", "atomic_of": None, "tickets": ["0001"]}
        evidence.append({
            "probe": "revision_round_with_unrelated_ticket",
            "report": ingest.coverage([record], {"0001", "0002"}),
        })
        first = root / "decision.txt"
        second = root / "review.txt"
        first.write_text("Decision")
        second.write_text("Review")
        archive = root / "archive"
        ingest.archive([first], archive)
        ingest.archive([second], archive)
        evidence.append({
            "probe": "archive_two_intakes",
            "both_files_preserved": (archive / first.name).exists()
            and (archive / second.name).exists(),
            "manifest_entries": len(json.loads(
                (archive / "manifest.json").read_text()
            )["entries"]),
        })
        marked = load("audit_marked", "skills/track-changes-pdf/track_changes_pdf.py")
        compiler = root / "fake-compiler"
        compiler.write_text(
            "#!/usr/bin/env python3\nfrom pathlib import Path\nimport sys\n"
            "stem=Path(sys.argv[1]).stem\n"
            "Path(stem+'.pdf').write_bytes(b'%PDF-fake-for-audit')\n"
            "Path(stem+'.log').write_text('There were undefined citations.')\n"
        )
        compiler.chmod(0o700)
        diff = root / "marked.tex"
        diff.write_text("fake source")
        produced = marked.compile_pdf([str(compiler)], root, diff)
        evidence.append({
            "probe": "marked_pdf_with_undefined_citations",
            "accepted": produced.exists(),
            "fixture": "fake compiler exits zero and writes PDF plus undefined-citation log",
        })
        old = (
            "@article{smith2020, author={Smith, A}, year={2020}, "
            "title={One work}, doi={10.0000/same}}"
        )
        new = old.replace("smith2020", "smith2021").replace("year={2020}", "year={2021}")
        refs = root / "refs.bib"
        refs.write_text(old)
        evidence.append({
            "probe": "bib_same_doi_different_year",
            "actions": [line for line in bib.merge(
                bib.parse_bibtex(new), bib.parse_bibtex(old), refs, dry_run=True
            ) if line.startswith("[")],
        })
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

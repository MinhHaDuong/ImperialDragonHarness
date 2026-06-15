#!/usr/bin/env python3
"""External peer review of a manuscript PDF via OpenRouter.

Sends a PDF to OpenAI and Mistral models (one ``OPENROUTER_API_KEY``, OpenAI
SDK against the OpenRouter base URL), each model adopting a reviewer persona,
and writes one markdown review per (model, persona) combo.

Portable across projects: no project-specific hardcoding. Models, personas,
and the task prompt are all configurable from the command line.

Two input modes:
  - PDF file mode (default): the PDF is uploaded and parsed by the
    ``file-parser`` plugin (engine configurable, default ``mistral-ocr``).
    Requires at least the OpenRouter "files" balance minimum ($0.50).
  - Text mode (``--text`` or automatic fallback on HTTP 402): the PDF text is
    extracted locally with ``pdftotext`` and sent as plain text.

Example:
    python peer_review.py paper.pdf \\
        --models openai/gpt-5.5,mistralai/mistral-large-2512 \\
        --personas grinchy,student --out-dir reviews/
"""

import argparse
import base64
import concurrent.futures as cf
import logging
import os
import shutil
import subprocess
from pathlib import Path

from openai import APIStatusError, OpenAI

log = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

DEFAULT_MODELS = ["openai/gpt-5.5", "mistralai/mistral-large-2512"]

# Add a persona by adding one entry here: name -> system prompt.
PERSONAS: dict[str, str] = {
    "grinchy": (
        "You are a grinchy, senior, nitpicking peer reviewer for a top-tier "
        "venue. You have refereed hundreds of papers and are very hard to "
        "impress. Be skeptical, demanding, and specific. Hunt relentlessly for: "
        "overclaims and unsupported generalizations; methodological holes; "
        "missing or shallow related work; statistical weaknesses and confounds; "
        "figures/tables that do not earn their space; vague or hand-wavy "
        "passages; and any gap between what is claimed and what is shown. Do "
        "NOT pad with praise. Give a clear recommendation (reject / major "
        "revision / minor revision / accept) and a prioritized, numbered list of "
        "concrete objections, each with a section/figure reference and what "
        "would fix it. End with the 3 things that most threaten the paper's "
        "central claim."
    ),
    "student": (
        "You are a bright, curious, well-read doctoral student giving a careful "
        "peer review. You are genuinely engaged: say briefly what is genuinely "
        "novel or useful, but spend most of your effort on sharp, incisive "
        "questions — where the argument does not follow, where you got confused, "
        "which experiments or ablations you would want, what related work is "
        "missing, and the naive-but-pointed questions a smart student asks in a "
        "reading group. Be constructive and specific, with section/figure "
        "references. End with a numbered list of the questions you would ask the "
        "authors, and one experiment you would run next."
    ),
}

DEFAULT_TASK = (
    "Below is a research paper. Write a full, rigorous peer review. Focus on "
    "the main body (Introduction through Conclusion); annexes are supporting "
    "material. Be concrete and reference specific sections, figures, and tables."
)


def slug(model: str) -> str:
    """A filesystem-safe stem for a model id (e.g. ``openai/gpt-5.5``)."""
    return model.replace("/", "_").replace(":", "_")


def load_api_key(repo_root: Path) -> str:
    """Read OPENROUTER_API_KEY from the environment, else the nearest .env.

    Walks up from ``repo_root`` looking for a ``.env`` containing the key.
    """
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    for parent in [repo_root, *repo_root.parents]:
        env = parent / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(
        "OPENROUTER_API_KEY not found in environment or any .env walking up "
        f"from {repo_root}"
    )


def extract_text(pdf_path: Path) -> str:
    """Extract PDF text locally via pdftotext (clear error if absent)."""
    if shutil.which("pdftotext") is None:
        raise SystemExit(
            "pdftotext not found — install poppler-utils to use text mode, or "
            "ensure the OpenRouter balance is above $0.50 for PDF-file mode."
        )
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def build_messages(persona: str, task: str, pdf_path: Path,
                   data_url: str | None, text: str | None) -> tuple[list, dict]:
    """Assemble chat messages and extra_body for one combo."""
    system = {"role": "system", "content": PERSONAS[persona]}
    if text is not None:
        user = {
            "role": "user",
            "content": task + "\n\n=== PAPER (extracted text) ===\n\n" + text,
        }
        return [system, user], {}
    assert data_url is not None, "file mode requires a data_url"
    user = {
        "role": "user",
        "content": [
            {"type": "text", "text": task},
            {"type": "file",
             "file": {"filename": pdf_path.name, "file_data": data_url}},
        ],
    }
    extra = {"plugins": [{"id": "file-parser", "pdf": {"engine": "mistral-ocr"}}]}
    return [system, user], extra


def review_one(model: str, persona: str, pdf_path: Path, api_key: str,
               task: str, engine: str, max_tokens: int, out_dir: Path,
               data_url: str | None, text: str | None) -> Path:
    """Run one (model, persona) review and write its markdown file."""
    client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=api_key, timeout=600)
    mode = "text" if text is not None else "file"
    log.info("START model=%s persona=%s mode=%s", model, persona, mode)
    messages, extra = build_messages(persona, task, pdf_path, data_url, text)
    if extra:
        extra["plugins"][0]["pdf"]["engine"] = engine
    resp = client.chat.completions.create(
        model=model, messages=messages, max_tokens=max_tokens, extra_body=extra,
    )
    content = resp.choices[0].message.content or ""
    out = out_dir / f"review_{slug(model)}_{persona}.md"
    out.write_text(
        f"# Peer review — {model}, persona: {persona}\n\n{content}\n",
        encoding="utf-8",
    )
    log.info("DONE  model=%s persona=%s -> %s (%d chars)",
             model, persona, out, len(content))
    return out


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="External peer review of a PDF via OpenRouter.")
    p.add_argument("pdf", type=Path, help="Path to the manuscript PDF.")
    p.add_argument(
        "--models", default=",".join(DEFAULT_MODELS),
        help="Comma-separated OpenRouter model ids "
             f"(default: {','.join(DEFAULT_MODELS)}).")
    p.add_argument(
        "--personas", default="grinchy,student",
        help=f"Comma-separated persona names. Available: "
             f"{','.join(sorted(PERSONAS))}.")
    p.add_argument(
        "--task", default=None,
        help="Override the full task prompt sent to every reviewer.")
    p.add_argument(
        "--topic", default=None,
        help="One-line description of the paper, appended to the task prompt.")
    p.add_argument("--engine", default="mistral-ocr",
                   help="file-parser PDF engine (default: mistral-ocr).")
    p.add_argument("--max-tokens", type=int, default=6000)
    p.add_argument("--out-dir", type=Path, default=Path("reviews"))
    p.add_argument("--repo-root", type=Path, default=Path.cwd(),
                   help="Where to start the .env search (default: cwd).")
    p.add_argument("--text", action="store_true",
                   help="Send locally-extracted text instead of the PDF file "
                        "(also the automatic fallback on HTTP 402).")
    return p.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    if not args.pdf.exists():
        raise SystemExit(f"PDF not found: {args.pdf}")

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    personas = [p.strip() for p in args.personas.split(",") if p.strip()]
    unknown = [p for p in personas if p not in PERSONAS]
    if unknown:
        raise SystemExit(
            f"unknown persona(s): {unknown}. Available: {sorted(PERSONAS)}")

    task = args.task or DEFAULT_TASK
    if args.topic:
        task = f"{task}\n\nPaper topic: {args.topic}"

    args.out_dir.mkdir(parents=True, exist_ok=True)
    api_key = load_api_key(args.repo_root)

    text: str | None = None
    data_url: str | None = None
    if args.text:
        text = extract_text(args.pdf)
    else:
        data_url = ("data:application/pdf;base64,"
                    + base64.b64encode(args.pdf.read_bytes()).decode("utf-8"))

    combos = [(m, p) for m in models for p in personas]
    log.info("Running %d combo(s): %s", len(combos),
             ", ".join(f"{m}:{p}" for m, p in combos))

    written: list[Path] = []
    failed: list[str] = []
    with cf.ThreadPoolExecutor(max_workers=max(1, len(combos))) as ex:
        futs = {
            ex.submit(review_one, m, p, args.pdf, api_key, task, args.engine,
                      args.max_tokens, args.out_dir, data_url, text): (m, p)
            for m, p in combos
        }
        for fut in cf.as_completed(futs):
            m, p = futs[fut]
            try:
                written.append(fut.result())
            except APIStatusError as e:
                if e.status_code == 402 and not args.text and data_url is not None:
                    log.warning(
                        "402 (OpenRouter files balance < $0.50) for %s:%s — "
                        "retrying in text mode", m, p)
                    try:
                        local_text = extract_text(args.pdf)
                        written.append(review_one(
                            m, p, args.pdf, api_key, task, args.engine,
                            args.max_tokens, args.out_dir, None, local_text))
                    except Exception as e2:  # noqa: BLE001 - report and continue
                        log.error("FAILED (text retry) %s:%s: %s", m, p, e2)
                        failed.append(f"{m}:{p}")
                else:
                    log.error("FAILED %s:%s: %s", m, p, e)
                    failed.append(f"{m}:{p}")
            except Exception as e:  # noqa: BLE001 - report and continue
                log.error("FAILED %s:%s: %s", m, p, e)
                failed.append(f"{m}:{p}")

    log.info("Summary: %d written, %d failed", len(written), len(failed))
    for path in written:
        log.info("  wrote %s", path)
    if failed:
        log.warning("  failed combos: %s", ", ".join(failed))


if __name__ == "__main__":
    main()

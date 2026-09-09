#!/usr/bin/env python3
"""Reconstitute a citable PDF from a browser capture of a bot-blocked page.

Two subcommands:
  build   capture.pdf + metadata -> reconstituted PDF (text reflowed, figures kept,
          provenance block printed inside the document)
  verify  compare reconstituted against capture, sentence by sentence
"""
import argparse
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

log = logging.getLogger("reconstitute")

CHROME = [
    r"^\d+\s+of\s+\d+",                      # "2 of 4" pagination
    r"\.\.\.\s+https?://",                   # running head: truncated title + URL
    r"\d{1,2}/\d{1,2}/\d{2,4},\s*\d{2}:\d{2}",  # print timestamp
]
SENTENCE_END = re.compile(r'[.!?”"»]$')
QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    log.debug("run: %s", " ".join(cmd))
    return subprocess.run(cmd, capture_output=True, text=True, check=False, **kw)


def page_text(pdf: Path) -> str:
    r = run(["pdftotext", "-layout", str(pdf), "-"])
    if r.returncode:
        raise SystemExit(f"pdftotext failed on {pdf}: {r.stderr.strip()}")
    return r.stdout


def paragraphs(raw: str, drop: list[str]) -> list[str]:
    """Strip page chrome, dedupe the page-break echo, reflow into paragraphs."""
    pats = [re.compile(p) for p in CHROME + drop]
    kept, prev = [], None
    for line in raw.split("\n"):
        line = line.replace("\x0c", "").strip()
        if line and any(p.search(line) for p in pats):
            continue
        if line and line == prev:          # same line repeated across a page break
            continue
        if line:
            prev = line
        kept.append(line)
    blocks = [re.sub(r"\s+", " ", b).strip()
              for b in re.split(r"\n\s*\n", "\n".join(kept)) if b.strip()]
    merged: list[str] = []
    for b in blocks:                       # a sentence split by a page break
        if merged and not SENTENCE_END.search(merged[-1]) and b[:1].islower():
            merged[-1] += " " + b
        else:
            merged.append(b)
    return merged


def figures(pdf: Path, out: Path, min_px: int) -> list[Path]:
    """Images of the PRINTED page. The print view has already dropped site chrome."""
    out.mkdir(parents=True, exist_ok=True)
    if run(["pdfimages", "-png", "-p", str(pdf), str(out / "fig")]).returncode:
        return []
    keep = []
    for f in sorted(out.glob("fig-*.png")):
        r = run(["identify", "-format", "%w %h", str(f)])
        try:
            w, h = (int(x) for x in r.stdout.split())
        except ValueError:
            continue
        if w >= min_px and h >= min_px:
            keep.append(f)
        else:
            f.unlink()
    return keep


def tex_escape(t: str) -> str:
    for a, b in (("$", r"\$"), ("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#")):
        t = t.replace(a, b)
    return t


def build_markdown(title, meta, note, blocks, figs, captions, headings) -> str:
    out = [f"% {tex_escape(title)}", "", "## Provenance et méthode", ""]
    for k, v in meta:
        out.append(f"- **{k}** — " + (f"<{v}>" if str(v).startswith("http") else tex_escape(str(v))))
    out += ["", f"*{note}*", "", r"\vspace{1em}\hrule\vspace{1em}", "", "## Texte de la page", ""]
    fig_i = 0
    for b in blocks:
        if b in headings:
            out += [f"### {tex_escape(b)}", ""]
        elif b.startswith("•"):
            out += ["- " + tex_escape(i.strip()) for i in b.split("•") if i.strip()] + [""]
        elif fig_i < len(figs) and any(c and c in b for c in captions):
            cap = tex_escape(captions[fig_i]) if fig_i < len(captions) else ""
            out += [f"![{cap}]({figs[fig_i]}){{width=88%}}", ""]
            fig_i += 1
        else:
            out += [tex_escape(b), ""]
    for f in figs[fig_i:]:                 # figures the text never announced
        out += [f"![]({f}){{width=88%}}", ""]
    return "\n".join(out)


def cmd_build(a: argparse.Namespace) -> int:
    capture = Path(a.capture).expanduser()
    spec = json.loads(Path(a.meta).expanduser().read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp(prefix="reconstitute-"))
    blocks = paragraphs(page_text(capture), spec.get("drop", []))
    for pat in spec.get("drop_blocks", []):            # e.g. a "Have you read?" link bank
        rx = re.compile(pat)
        cut, skipping = [], False
        for b in blocks:
            if rx.search(b):
                skipping = True
                continue
            if skipping and b.lstrip().startswith("•"):
                continue
            skipping = False
            cut.append(b)
        blocks = cut
    figs = figures(capture, tmp / "img", a.min_px)
    log.info("%d paragraphs, %d figure(s) from the printed page", len(blocks), len(figs))
    md = build_markdown(spec["title"], spec["meta"], spec["note"], blocks, figs,
                        spec.get("figure_captions", []), spec.get("headings", []))
    md_path = tmp / "doc.md"
    md_path.write_text(md, encoding="utf-8")
    out = Path(a.out).expanduser()
    r = run(["pandoc", str(md_path), "-o", str(out), "--pdf-engine=xelatex",
             "-V", "geometry:margin=2.3cm", "-V", "fontsize=10pt",
             "-V", "colorlinks=true", "-V", "linkcolor=blue", "-V", "urlcolor=blue"])
    if r.returncode:
        print(r.stdout or r.stderr, file=sys.stderr)
        return 1
    print(f"{out}  ({len(blocks)} paragraphs, {len(figs)} figure(s))")
    return 0


def sentences(pdf: Path) -> list[str]:
    t = re.sub(r"\s+", " ", page_text(pdf)).translate(QUOTES)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", t) if len(s.strip()) > 45]


def cmd_verify(a: argparse.Namespace) -> int:
    drop = re.compile("|".join(CHROME + a.ignore)) if a.ignore or CHROME else None
    body = [s for s in sentences(Path(a.capture).expanduser()) if not (drop and drop.search(s))]
    rebuilt = re.sub(r"\s+", " ", page_text(Path(a.reconstituted).expanduser())).translate(QUOTES)
    missing = [s for s in body if s[:44] not in rebuilt]
    print(f"{len(body)} content sentences in the capture, {len(missing)} missing")
    for m in missing:
        print("  missing:", m[:120])
    return 1 if missing else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="capture + metadata -> reconstituted PDF")
    b.add_argument("--capture", required=True, help="browser print-to-PDF of the page")
    b.add_argument("--meta", required=True, help="JSON: title, meta, note, drop, headings…")
    b.add_argument("--out", required=True)
    b.add_argument("--min-px", type=int, default=400,
                   help="ignore images smaller than this on a side (default 400)")
    b.set_defaults(func=cmd_build)

    v = sub.add_parser("verify", help="sentence coverage, reconstituted vs capture")
    v.add_argument("--capture", required=True)
    v.add_argument("--reconstituted", required=True)
    v.add_argument("--ignore", nargs="*", default=[],
                   help="regexes for content deliberately dropped (e.g. 'Have you read')")
    v.set_defaults(func=cmd_verify)

    a = p.parse_args()
    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(levelname)s %(message)s")
    for tool in ("pdftotext", "pdfimages", "pandoc"):
        if not shutil.which(tool):
            raise SystemExit(f"missing required tool: {tool}")
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())

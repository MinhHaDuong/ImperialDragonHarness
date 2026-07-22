---
name: pdf-layout-automate-dont-hand-paginate
description: PDF pagination polish (sections on fresh pages, unsplit tables, widows) should be automated via LaTeX header, not hand-inserted \newpage rounds
metadata:
  type: feedback
---

Hand-paginating a Quarto/LaTeX PDF (2026-07-22, Œconomia page-perso variant) took ~8
interactive rounds of `\newpage` insertions, sentence shaving and re-renders. The author's
verdict: "on a fait du manuel là où on peut avoir du auto."

**Why:** each manual `\newpage` and line-shave is brittle — any upstream edit reflows the
document and re-opens every widow/split; LaTeX has declarative knobs for all of it.

**How to apply:** for a layout-polished variant, put in `include-in-header` once:
- every section on a fresh page: `\usepackage{titlesec}` + `\newcommand{\sectionbreak}{\clearpage}`;
- widows/orphans: `\widowpenalty=10000 \clubpenalty=10000`;
- unsplit pipe tables: control column ratios via the delimiter-row dash counts (pandoc maps
  dash proportions to column widths), and only if a longtable still splits, `\newpage` before it;
- bibliography font/leading: `\AtBeginEnvironment{CSLReferences}{\small\setlength{\parskip}{0.3em}}`.
Variant builds (named HAL/page-perso vs anonymous submission) are a transform layer applied to
the shared qmd then reverted — reference implementation: `papiers/sent/
Oeconomia_Inventing_Climate_Finance/releases/hal_variant.py` (apply → render → git checkout --).
Related: [[frozen-manuscript-vs-live-companions]].

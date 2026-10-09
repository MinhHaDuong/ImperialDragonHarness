# Tournament report rebuilds: padme Python environments disagree in the last float digit

Context: PRs #1316 (appendix title page) and #1320 (CC BY 4.0 licence) changed
only report text in `scripts/tournament-report-completion.py`; the author had
required rebuilds from `~/arena` on padme, not from the public snapshot.

Events, 2026-10-09, on padme, same commit, same `~/arena`:

- `uv run --no-project --with matplotlib --with scipy --with numpy`
  (matplotlib 3.11.2): `tests.json`, `comparisons.csv`, `appendix-analysis.json`
  and the cost JSONs changed in the last digit of some floats
  (e.g. 0.8935183657518264 → 0.8935183657518265).
- Locked project env after `uv sync --group dev` (matplotlib 3.11.2,
  numpy 2.4.6, scipy 1.17.1): same kind of last-digit changes.
- System `python3` (matplotlib 3.10.8, numpy 2.4.4, scipy 1.17.1): numeric
  outputs byte-identical to main. The committed provenance (completion-1046.md
  § Provenance padme) names matplotlib 3.10.8.

Outcome: both PRs committed only the two PDFs from the system-python run; PNGs
differed by render noise and were left as on main.

Also observed: the new pdftotext-based test first failed CI for not using
`child_env()` (hermetic-children guard), then because the CI runner lacks
`pdftotext`; it now skips when the binary is absent.

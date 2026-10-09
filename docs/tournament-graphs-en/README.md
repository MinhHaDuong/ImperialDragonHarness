# English edition for sharing

English edition of the 26-page French report (12-page synthesis and 14-page ticket-1046 supplement). Identical numeric
snapshot and statistical computations; English text and decimal points.

From the repository root:

```bash
MPLCONFIGDIR=/tmp/tournament-mpl python3 scripts/tournament-graphs-en.py \
  --snapshot docs/tournament-graphs/snapshot.json --time-value 1
```

The wrapper translates text constants from the French renderer before layout,
using `scripts/tournament-english.json`; it does not duplicate the analysis.
Output: `model-comparison.pdf` and English PNG figures in this directory.
The PDF and figures are prepared for review and sharing; nothing is posted to Reddit.

The supplement includes paired distributions and H1/H2 verdicts, effort comparisons, routing classes, corrected historical outcomes and a situation guide. `appendix-analysis.json` covers all 190 pairs of 20 identities, separately from the original 136-pair DAG family; `paired-differences.csv` supplies the 130 plotted task observations. The guide was reviewed by a delegated Fable reviewer on the author's instruction; its corrections are applied. Figures are rebuilt from `~/arena` on padme ([provenance](../tournament-graphs/completion-1046.md#provenance-padme)).

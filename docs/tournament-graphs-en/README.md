# English edition for sharing

English translation of the 12-page French beta 1 report. Identical numeric
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

---
name: Publications list location
description: User's personal publications list is built from ~/CNRS/html/src/Ha-Duong.bib via Makefile; don't edit index.html directly
type: reference
---

Publications page at ~/CNRS/html/ is built from BibTeX source:
- Source: `~/CNRS/html/src/Ha-Duong.bib`
- Build: `cd ~/CNRS/html/src && make` (runs `index.py` + `bib2htm.py`)
- Output: `~/CNRS/html/index.html`
- Deploy: `cd ~/CNRS/html && make sync` (FTP to ouvaton.coop)
- Not a git repo.
- `@article` is only for peer-reviewed, accepted papers.
- `institution` field only for papers published in the CIRED Working Papers series; omit for preprints.

---
name: reference-homepage-publication-list
description: "The minh.haduong.com publication-list generator repo — path, conventions, tooling, relation model"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 05268d5e-7c10-4f67-83a9-b1e407896bd3
---

`~/CNRS/html` — BibLaTeX→HTML generator for the homepage publication list (relates to AEDIST ticket 0670-rehome-publications). **Git root is `src/`**, not the parent; `~/CNRS/html/` itself is the untracked FTP deploy tree (assets `files/`, `images/` ~1.5GB, the parent Makefile, and the generated `index.html` at the deploy root all untracked — 0012's pivot would bring them under git). **No git remote — local, direct-to-master** (ratified: only the 0012 layout pivot uses a branch). Deploy: `make sync` (FTP via `~/.netrc`, ouvaton.coop).

Run tests with `rtk proxy python3 -m pytest` from `src/` (a bare `pytest` or `python3 -m pytest` is mangled by the rtk hook; the pipx `pytest` has a broken interpreter). Tooling installed: tidy 5.8 (HTML5-aware), linkchecker, qrencode.

Data file `Ha-Duong.bib` is strict house format (`bibparser.parse_line`: 2-space indent, `=` aligned at column 15, `{value},`); `make tidy-bib` normalizes it, `make validate` gates the build (tidy exit 0, wired into sync), `make inspect` reports field stats + one-sided relations. Relations use a single self-describing field `relations = {type=key; ...}`, 6 types: translation (merge), reprint/identical (mergeinto), version/companion/data (annotate). `data` = IsSupplementedBy → fixed "Data and code" label (paper → Zenodo archive; archive points back via companion). PDF naming `HaDuong-YYYY-Topic.pdf`, ASCII only, lang suffix from the entry key (`-vi`/`-en`), variant `-Slides`/`-Text`. Tests split: `test_bib.py` (data integrity + relation registry), `test_assets.py` (JS/CSS/HTML source + validation), `test_bibparser.py`, `test_tidy_bib.py`. git-erg tickets in `src/tickets/`; run `erg close` BEFORE the commit meant to carry the close — close mutates the `.erg` and strips dependents' `Blocked-by`, so closing after committing orphans ticket state into a catch-up commit. `src/README.md` documents the format, relation model, and naming schema.

# I4R report templates

Copies of the Institute for Replication templates, so `report` works offline
and reproducibly. Source: Zenodo, licence CC-BY 4.0 (credit "Institute for
Replication" when a report reuses a template). Retrieved 2026-11-25; every
checksum matched the Zenodo API on that date. Each LaTeX zip holds `main.tex`,
`main.pdf`, `references.bib` and a `README.md` (LuaLaTeX, biber, biblatex-apa).

| Record | Template | Use it for | Section skeleton |
|---|---|---|---|
| [23226406](https://zenodo.org/records/23226406) | Reproduction Report – General (v1, 2026-10-08) | Default: any paper without a more specific template | Introduction; Computational Reproducibility; Discrepancies Between Preregistration and Article; Robustness Reproduction/Replication with New Data; Conclusion |
| [23214112](https://zenodo.org/records/23214112) | Reproduction Report – Psychological Science Phase 2 (v1, 2026-10-07) | A Psychological Science paper in I4R's Phase 2 project, or one I4R names this template for | Same skeleton as General, with the new-data section marked OPTIONAL |
| [23597737](https://zenodo.org/records/23597737) | Commentary from Forensic Report (v1, 2026-10-23) | A forensic, AI-assisted commentary on specific problems (unexplained exclusions, design confounds, privacy, missing observations) rather than a reproduction and robustness report | Introduction; Computational Reproducibility; Commentary (one subsection per finding); Conclusion |

## Files

| Record | File | Bytes | md5 (Zenodo) |
|---|---|---|---|
| 23214112 | `23214112/replication-report_psych-science-v2-WORD.docx` | 336978 | `0f7b29495698098fe68634122c27ff67` |
| 23214112 | `23214112/replication-report_psych-science-v2-LATEX.zip` | 176580 | `a2745ea5ac3e38538abcc8f0c835a193` |
| 23226406 | `23226406/replication-report_general-WORD.docx` | 523962 | `87d35c722ecb6337c00c7b8db8d97f72` |
| 23226406 | `23226406/replication-report_general-LATEX.zip` | 175102 | `67ba8c58d6c6c982a23e6c554d393304` |
| 23597737 | `23597737/commentary_forensic-report-WORD.docx` | 225432 | `8d42a6be5c412d786e2659575c7e6f48` |
| 23597737 | `23597737/commentary_forensic-report-LATEX.zip` | 253874 | `56e77a7e808b1a5f2aa187c286c8ea3f` |

Check from this directory: `md5sum */*` and compare with the column above.

## Newer versions

Zenodo records are versioned. To look for one, read
`https://zenodo.org/api/records/<record>` and follow `links.latest`. Report a
newer version to the user; never switch to it silently, and add its files here
only in a change of their own.

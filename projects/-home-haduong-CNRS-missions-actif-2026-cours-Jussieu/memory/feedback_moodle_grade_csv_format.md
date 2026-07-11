---
name: feedback_moodle_grade_csv_format
description: "Filling Jussieu Moodle grade-export CSVs — fill the existing \"(Brut)\" column in place, never add columns"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ffe4d1da-eb53-4984-8f30-892108c93d2e
---

When injecting exam totals into a Moodle grade-export CSV (e.g. `UL1SXIEE - S2-25 Notes-HADUONG.csv`), fill the **existing** grade column `Epreuve de cohorte (Brut)` (currently `-`) in place. Do NOT add new columns (P1..P5, Total) — that altered the format and was rejected.

**Why:** the file is re-imported into Moodle; it must keep its exact shape (7 `;`-separated columns, header unchanged, FR decimal with comma like `18,5`, ungraded students keep `-`).

**How to apply:** replace field index 5 only; verify with a line diff that *only* that column changed. Recover correct student numbers/spellings by matching handwritten names against the full roster CSV, not by reading handwritten IDs. See `Examen sur table/inject_grades.py`. Related: [[feedback_group_codes]].

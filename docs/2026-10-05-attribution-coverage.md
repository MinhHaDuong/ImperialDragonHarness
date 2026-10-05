# Reviewed-merge attribution coverage — 2026-10-05

Audit range: after merged PR1005 base `3d93b9e3565b4b3a9da0b875da9390e9954cb20a` through actual merged main cutoff `c917715ae4252c674e063069db31ea57de20d3c5` (PR1207), inclusive of 18 first-parent merge commits. The cutoff is explicit: this report makes no claim about later merges or an unmerged review of this capture itself. `scripts/enumerate-merges.py` supplies the merge list; `scripts/attribution_query.py --json --since <base> --until <cutoff>` joins it to strict project-local journal records. The query alone classifies missing records; the review classification below was checked against public PR evidence and retained local runtime/report proof.

| PR | Merge | Classification at cutoff | Evidence |
| --- | --- | --- | --- |
| 1186 | `bccc2e13` | reviewed; existing record | `memory/journal/2026/2026-10-05-review-attribution-pr1186.md` |
| 1190 | `ee6080eb` | mechanical-only exemption; query WARN remains | Both producer and root confirmed no commissioned model review in `docs/2026-10-05-attribution-raid.md`; source-free wrap-up used mechanical checks and CI. No reviewer invented. |
| 1191 | `aa4efecb` | reviewed; delayed capture repaired | New PR1191 record; root same-context manual contract review, separate Brood consistency/portable phases, actual gate and native CLI evidence. |
| 1193 | `3d19da08` | reviewed; existing record | PR1193 record. |
| 1192 | `b83016a7` | reviewed; existing record | PR1192 record. |
| 1194 | `3f69ed5b` | reviewed; existing record | PR1194 record. |
| 1195 | `e443dc3b` | reviewed; existing record | PR1195 record. |
| 1196 | `d72680fb` | reviewed; existing record | PR1196 record. |
| 1197 | `b95aff7c` | reviewed; existing record | PR1197 record. |
| 1198 | `d29d8140` | reviewed; existing record | PR1198 record. |
| 1199 | `540b57f7` | reviewed; existing record | PR1199 record. |
| 1200 | `371a51ab` | reviewed; existing record | PR1200 record. |
| 1201 | `72284111` | reviewed; existing record | PR1201 record. |
| 1202 | `5211802a` | factual read; delayed capture repaired | New PR1202 record; root source-free Roar inspection, no Gaze/native claim. |
| 1203 | `225541ae` | reviewed; delayed capture repaired | New PR1203 record; three-perspective panel, native, portable and criterion gate. |
| 1205 | `d0563d15` | reviewed; delayed capture repaired | New PR1205 record; two-perspective public review, optional consider disposition, native, portable and gate. |
| 1206 | `792ee420` | reviewed; delayed capture repaired | New PR1206 record; initial five-perspective objector, local correction and regression; owner-directed merge with no final public Gaze/gate/native/simplify claim. |
| 1207 | `c917715a` | reviewed locally; delayed capture repaired | New PR1207 record; distinct actual local review approved exact head despite empty forge comment/review collections. |

The six new files validate individually through `scripts/attribution_record.py`. The resulting strict read has 19 valid records across the repository: 13 pre-existing byte-untouched records plus six delayed captures. For this 18-merge range, 17 have available attribution; only documented mechanical-only PR1190 remains `missing` with the query's visible WARN. There are zero malformed, ambiguous-PR, ambiguous-record, encrypted-unavailable or unsafe-unavailable sources in the live read. No unresolved reviewed capture remains through the cutoff. Existing query/parser tests exercise missing, duplicate, malformed, encrypted and unsafe-source rejection; temporary negative controls were run for the exact query behavior without changing schema or historical records.

The delayed records cite public PR/review/comment URLs where actually present and bounded local proof paths for runtime identities and local-only attempts. They omit raw prompts, session identifiers and credentials. Requested role pins and permission auto-review actors are not identities. Separate contexts from one provider establish only the recorded level of decorrelation, and no unexposed model revision is inferred. A later merged reviewed PR requires a new cutoff and actual evidence before parent1009 closure.

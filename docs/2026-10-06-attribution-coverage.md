# Refreshed attribution coverage — 2026-10-06

Explicit range: after merged PR1005 base `3d93b9e3565b4b3a9da0b875da9390e9954cb20a` through merged main `9681d863ac88ca6f6826e822fff0732b5042e1ad` (PR1220). The existing enumerator reports30 first-parent merges. This refresh adds five captures (1204,1209,1210,1216,1220) and preserves all21 existing journal blobs byte-for-byte, including the1038 PR1211 masked capture. No record is created for this unmerged refresh.

The reproducible read is `python3 scripts/attribution_query.py --json --since 3d93b9e3565b4b3a9da0b875da9390e9954cb20a --until 9681d863ac88ca6f6826e822fff0732b5042e1ad`. It reports26 valid repository records, one runtime-masked game,25 model-attributable records, zero malformed/ambiguous/encrypted/unsafe sources. In-range:23 available, one runtime-masked, six missing. Query missing status is deliberately retained for all mechanical-only and unresolved classifications.

| PR | Actual merge | Evidence classification | Strict query |
| --- | --- | --- | --- |
| [1186](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1186) | `bccc2e13` | reviewed; existing capture | available |
| [1190](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1190) | `ee6080eb` | mechanical-only exemption (existing positive assertion) | missing |
| [1191](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1191) | `aa4efecb` | reviewed; existing capture | available |
| [1193](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1193) | `3d19da08` | reviewed; existing capture | available |
| [1192](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1192) | `b83016a7` | reviewed; existing capture | available |
| [1194](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1194) | `3f69ed5b` | reviewed; existing capture | available |
| [1195](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1195) | `e443dc3b` | reviewed; existing capture | available |
| [1196](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1196) | `d72680fb` | reviewed; existing capture | available |
| [1197](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1197) | `b95aff7c` | reviewed; existing capture | available |
| [1198](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1198) | `d29d8140` | reviewed; existing capture | available |
| [1199](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1199) | `540b57f7` | reviewed; existing capture | available |
| [1200](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1200) | `371a51ab` | reviewed; existing capture | available |
| [1201](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1201) | `72284111` | reviewed; existing capture | available |
| [1202](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1202) | `5211802a` | factual read; existing limited capture | available |
| [1203](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1203) | `225541ae` | reviewed; existing capture | available |
| [1205](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1205) | `d0563d15` | reviewed; existing capture | available |
| [1206](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1206) | `792ee420` | reviewed; existing capture | available |
| [1207](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1207) | `c917715a` | reviewed; existing capture | available |
| [1210](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1210) | `10f18439` | reviewed; actual tracker/body inspection | available |
| [1211](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1211) | `89004cff` | reviewed; runtime-masked game, captured by1038 | runtime-masked |
| [1204](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1204) | `ebd54f46` | reviewed; producer and phase identities recovered | available |
| [1208](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1208) | `333f619d` | mechanical-only (positive producer no-review assertion) | missing |
| [1214](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1214) | `e945bcae` | UNRESOLVED review classification | missing |
| [1213](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1213) | `6f976c33` | reviewed; existing capture | available |
| [1209](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1209) | `e02cd208` | reviewed; initial adopted findings retained | available |
| [1212](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1212) | `bd2efaad` | mechanical-only (positive root no-review assertion) | missing |
| [1215](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1215) | `bab206ac` | UNRESOLVED review classification | missing |
| [1216](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1216) | `f7623fc4` | factual coauthor inspection; historical read only | available |
| [1217](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1217) | `092d70af` | UNRESOLVED review classification | missing |
| [1220](https://github.com/MinhHaDuong/ImperialDragonHarness/pull/1220) | `9681d863` | reviewed; prerequisite capture with phase heads retained | available |

Classification is based on actual evidence, not the query's missing label. The sanitized durable evidence is [capture proof](2026-10-06-attribution-capture-proof.json); actual public PR links are above, and completed public review/comment links are retained in the new records. PR1204 producer metadata explicitly links the actual producer completion to PR1204 and initial head b1222b0ec0deaf60ef1c42e3c3695faa1b1242c1. This recovery supersedes earlier unavailable claims by addition; their historical sources remain unchanged. PR1205's producer is not used as a substitute. Reused contexts retain their phases and do not become independent reviewers. Initial adopted PR1209 findings remain serialized once with real repository anchors. PR1210's body-marker correction has no repository anchor and remains prose.

PR1216 is classified as factual coauthor inspection, following the already recorded limited factual-read class of PR1202. Actual root report reads and producer linkage support that bounded class. Its read predates final head d2648bc53fb7342856e51ad51e06a4ccac653ffd; this record supplies neither final-head approval nor independent review. Mechanical final checks are separate evidence.

PR1208's actual producer explicitly stated that no review was launched on that PR; PR1212's actual root explicitly stated that there was no review to attribute. Those positive assertions, preserved in the sanitized proof, justify mechanical-only classification. PR1190 retains its earlier documented positive no-review exemption in docs/2026-10-05-attribution-raid.md. Empty public review/comment collections alone supply no exemption.

PR1214,1215 and1217 remain UNRESOLVED: inspected actual completion/public collections provide no actual commissioned-review or positive no-review assertion for their own merge. PR1214's masked runtime does not prove a review occurred; PR1215 cannot inherit PR1213's reviews; PR1217's wrap-up completion and lack of an integration review do not prove absence of every own model review. Missing facts remain missing, without inferred identities or an invented author decision. Parent1032 and1009 stay open with their original integration criteria unchanged;1043 preserves the bounded historical-disposition work.

PR1220 capture includes the actual adopted provenance finding, initial REROLL/final APPROVED gates, reused final Red-team/portable phases, actual initial-head native review and distinct final integration approval. The exact phase heads and public links distinguish initial checks from final approval. All identified models are actual exposed runtime fields; no revision is inferred. Sanitized metadata omits private source locations and session identifiers.

Verification: individual strict-parser validation; actual range enumeration and query; preservation positive check plus changed-byte and duplicate negative controls; temporary duplicate/malformed/unsafe query controls; temporary runtime-masked real-Git backfill positive control; existing parser/query/backfill/roar contract tests. The source full gate and adherence results are recorded in the PR validation evidence.

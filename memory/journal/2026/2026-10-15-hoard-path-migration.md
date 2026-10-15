# Hoard path migration and preserved historical references

Baseline commit: `14e2cfdc39ed7122b9e3cd251de0e6ac12fdbc96`

On 2026-10-15, ticket 1106 applied the project-scoped migration helper in its
isolated harness branch, following the author's rename decision in ticket
1102 and skill activation in PR 1427. The current prompt is HOARD.md revision
v8-r2; the old v8-r1 prompt remains available as the Git blob below. The six
reports moved without content changes. Existing journal entries and ciphertext
were not rewritten. This records a path migration, not a consolidation pass.

## Original paths, current paths and original Git blobs

The original blob identifies the exact bytes at the baseline, independently
of the current filename. For the prompt it identifies historical v8-r1; the
current v8-r2 prompt has a new blob. For reports it is also the current blob.
No old-path alias or compatibility file was retained.

| Old path | Current path | Original Git blob |
|---|---|---|
| `memory/DREAM.md` | `memory/HOARD.md` | `6087a0b3f641bdc4cbeac595e87d174eb11bcbf5` |
| `memory/dreams/2026-10-02-0918-trial-dream-pass1.md` | `memory/hoards/2026-10-02-0918-trial-dream-pass1.md` | `cb64a1e271c4e4ff3875d06a97939ff667521c7c` |
| `memory/dreams/2026-10-02-0918-trial-dream-pass2.md` | `memory/hoards/2026-10-02-0918-trial-dream-pass2.md` | `5654b1a4375b4bae165029d02192229d412abb73` |
| `memory/dreams/2026-10-02-0918-trial-dream-pass3-interrupted.md` | `memory/hoards/2026-10-02-0918-trial-dream-pass3-interrupted.md` | `9e282de029507020e10b2d9f97c902a7e2824cde` |
| `memory/dreams/2026-10-02-pilot-first-dream.md` | `memory/hoards/2026-10-02-pilot-first-dream.md` | `7a7f486f78535ff8ea048ca3b8980c8f8ed83bbc` |
| `memory/dreams/2026-10-07-second-dream.md` | `memory/hoards/2026-10-07-second-dream.md` | `e50de830a1d8100cad1959baeeaaac4f13566725` |
| `memory/dreams/2026-10-13-third-dream.md` | `memory/hoards/2026-10-13-third-dream.md` | `e6fd139efed6d916cd2f2914a8aecc2078a246bf` |

## Archival source inventory

Only the source/target pairs below retain old Markdown targets. The journal
source remains unchanged; its [original episode](2026-10-13-third-dream-index-duplication-and-merge.md)
links to the third report by its former path. Ticket 1110 pinned the historical
evaluation citations to immutable Git permalinks before this migration; those
documents need no exception. This declaration lets the relocated-clone check
verify the retained Git evidence and relocated report bytes, without
exempting current index, topics or live documents from link resolution.

| Archival source | Historical target |
|---|---|
| `memory/journal/2026/2026-10-13-third-dream-index-duplication-and-merge.md` | `memory/dreams/2026-10-13-third-dream.md` |

Current index/topic links and the live convention/runtime-smoke document links
were updated to their moved targets. Historical report bodies, source ledgers,
and the original source-inventory records retain their dated names and blob
coordinates. Unmapped broken links remain errors. The index stays below its
100-line bound; subsequent consolidation uses only the new prompt/report paths.

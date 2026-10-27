# Dispatch record for ticket 0913

Dispatched 2026-10-05. Each child ticket scopes a project-level review and
migration, or a sourced disposition if the project is dormant or superseded.
The harness repository is the already-migrated pilot and is not a child.

## GitHub projects

The account inventory contained 36 repositories: 25 non-archived, non-fork
repositories (including this harness), 10 forks with Issues disabled, and one
archived repository. The following 24 non-harness repositories had Issues
enabled and received a new issue titled **Déployer la mémoire v8**. Existing
issues were checked first; no matching issue existed.

| Repository | Issue | Local `erg` ticket |
|---|---:|---|
| `JETP-observer` | [#6](https://github.com/MinhHaDuong/JETP-observer/issues/6) | 1981 |
| `aedist-technical-report` | [#1177](https://github.com/MinhHaDuong/aedist-technical-report/issues/1177) | 0682 |
| `git-erg` | [#376](https://github.com/MinhHaDuong/git-erg/issues/376) | 0305 |
| `climate-finance-het` | [#1690](https://github.com/MinhHaDuong/climate-finance-het/issues/1690) | 1985 |
| `padme` | [#92](https://github.com/MinhHaDuong/padme/issues/92) | 0065 |
| `klem-closure-python` | [#1](https://github.com/MinhHaDuong/klem-closure-python/issues/1) | — |
| `search-works-for-zotero` | [#636](https://github.com/MinhHaDuong/search-works-for-zotero/issues/636) | 0827 |
| `polycentric_activity` | [#206](https://github.com/MinhHaDuong/polycentric_activity/issues/206) | — |
| `livre-milliards-climat` | [#2](https://github.com/MinhHaDuong/livre-milliards-climat/issues/2) | — |
| `gavard-schoch-2026-comment` | [#6](https://github.com/MinhHaDuong/gavard-schoch-2026-comment/issues/6) | — |
| `fuzzy-corpus` | [#64](https://github.com/MinhHaDuong/fuzzy-corpus/issues/64) | 0052 |
| `Tracing-Kieu` | [#173](https://github.com/MinhHaDuong/Tracing-Kieu/issues/173) | 0257 |
| `cadens` | [#54](https://github.com/MinhHaDuong/cadens/issues/54) | 0038 |
| `archiveCIRED` | [#62](https://github.com/MinhHaDuong/archiveCIRED/issues/62) | — |
| `maiba` | [#57](https://github.com/MinhHaDuong/maiba/issues/57) | — |
| `corpus-access-bench` | [#2](https://github.com/MinhHaDuong/corpus-access-bench/issues/2) | — |
| `llm_benchmarks` | [#1](https://github.com/MinhHaDuong/llm_benchmarks/issues/1) | — |
| `demo-carto-themes` | [#1](https://github.com/MinhHaDuong/demo-carto-themes/issues/1) | — |
| `CIRED_alumni_directory` | [#9](https://github.com/MinhHaDuong/CIRED_alumni_directory/issues/9) | — |
| `test-chat-llamaindex` | [#1](https://github.com/MinhHaDuong/test-chat-llamaindex/issues/1) | — |
| `AR6_vs_WB_DLclassifier-exercise` | [#1](https://github.com/MinhHaDuong/AR6_vs_WB_DLclassifier-exercise/issues/1) | — |
| `sdg7evn` | [#13](https://github.com/MinhHaDuong/sdg7evn/issues/13) | — |
| `VinaPyPSA` | [#3](https://github.com/MinhHaDuong/VinaPyPSA/issues/3) | — |
| `VN-Power-Scenario` | [#26](https://github.com/MinhHaDuong/VN-Power-Scenario/issues/26) | — |

## Machine-local tickets

Ten `erg` tickets were created in local project checkouts. Nine match the
GitHub issues above and include their URLs. Zoteus is the exception: its local
fork has Issues disabled, so it received local ticket
`/home/haduong/CNRS/code/zoteus/tickets/0001-d-ployer-la-m-moire-v8.erg` only.
The search-works-for-zotero checkout with an existing ticket store was used as
the canonical local clone; its duplicate checkout and other worktrees were not
ticketed separately.

## Exceptions

- `ImperialDragonHarness` is the v8 pilot, already migrated and covered by the
  existing local project work; 0913 itself remains its dispatch record.
- `aedist` is archived, so no issue was filed there.
- Ten GitHub forks report Issues disabled: `DOIfetch`, `zotero`,
  `document-worker`, `zoteus`, `My-Brain-Is-Full-Crew`, `nvfd`,
  `musical_stuff`, `dotfiles`, `natu`, and `python-vote-core`. The one matching
  local checkout, `zoteus`, has the local ticket listed above. The other forks
  had no independent local project checkout in the discovered repository set.
- Duplicate worktrees, build/dependency checkouts, and non-owned upstream
  repositories were not treated as distinct project destinations.

The child tickets do not claim that any project has migrated. Each project
must preserve its sources, establish an audience and rollback record, and
complete its own review before closing its ticket.

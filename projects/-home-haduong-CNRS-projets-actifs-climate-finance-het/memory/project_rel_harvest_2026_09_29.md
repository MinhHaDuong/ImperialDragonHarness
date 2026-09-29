---
name: project_rel_harvest_2026_09_29
description: "State of the REL south-and-languages harvest on 2026-09-29: where the data, archive and tickets are, and what is not done"
metadata:
  node_type: memory
  type: project
  originSessionId: defcd2ff-c1d3-4c08-b691-d9c570f60034
  modified: 2026-09-29T16:01:54.606Z
---

REL (Reviews of Economic Literature, due about 2026-12-06) harvest state at the end of the 2026-09-29 session.

- **Merged:** #1576 (child tickets 1650-1656 of 0700), #1578 (protocol reconciled, annex, Astra's review, provisional PRISMA flow), #1579 (search and screen scripts `catalog_rel_sud_search.py`, `corpus_rel_sud_screen.py`, configs, 55 sentinels, ticket 1530 closed).
- **Numbers (provisional):** final search f+g: 50,235 records, 34,487 works, 30,480 absent from the refined corpus; first screen 30,466 labelled (Haiku then Qwen); Opus second stage 4,792 reviewed, 2,473 ICF (1,933 research). The 4,773 works Qwen labelled last have not had the Opus stage. About 42,688 works of the raw pool are unscreened.
- **Where things are:** run archive with SHA-256 manifest and the ad-hoc scripts at `~/data/projets/climate-finance-het/rel_sud/2026-09-29/` (outside the repo); search runs and screen labels on padme in `~/rel_sud_runs/`. The screen input builders were ad-hoc scripts; they enter the repo under 1655.
- **Design decisions (author):** one ICF screen over the whole pool ([[feedback_single_standard_pooled_screen]]); Kyoto instruments and REDD+ benefit sharing are in the harvest scope; sentinels split into tuning, hold-out (never used to change a query) and retention classes; protocol lane tickets 1650-1654, freeze 1656.
- **Not done:** sources beyond OpenAlex (1653), 61-journal table-of-contents check (1650), Gavard-Schoch (1651), EconLit (1652), chaining (1654), a rule for the 177 "unsure" works, the unit for working-paper versus article, native reading of the Hindi, Bengali, Arabic, Chinese, Russian and Indonesian strings, the limits paragraph.
- **Stale remote branch:** `origin/t1530-rel-sud-search` holds pre-rebase commits (not an ancestor of main); delete after the author agrees.
- See [[reference_openalex_budget_and_filters]] and [[reference_machine_padme]].

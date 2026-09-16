---
name: feedback_worktree_make_check_corpus
description: make check in a worktree fails test_corpus_acceptance because CLIMATE_FINANCE_DATA is relative and .worktreeinclude does not copy the DVC corpus
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1d8b8fbb-6baa-4f83-8431-b9c37c1398d2
  modified: 2026-07-27T19:05:48.020Z
---

`make check` run inside a worktree fails ~7 `tests/test_corpus_acceptance.py`
tests with "refined_works.csv missing at data/catalogs/…". Not a defect in the
branch: `.env` sets `CLIMATE_FINANCE_DATA=data` (relative), so it resolves to the
*worktree's* empty `data/`, and `.worktreeinclude` copies only `.env` and
`.dvc/config.local` — never the DVC corpus, which lives in the primary checkout.

**Why:** it looks exactly like a real regression, and the standing note that
"test_corpus_acceptance failures are real, not expected on padme"
([[reference_machine_padme]]) applies to the *primary checkout*, where the data
exists. In a worktree the cause is different and the failures are environmental.

**How to apply:** before attributing corpus-acceptance failures to your branch,
check whether the corpus is reachable: `ls <worktree>/data/catalogs/`. Then run
**`make data`** in the worktree — since ticket 0360 merged (PR #1179,
2026-07-27) the post-checkout hook symlinks the worktree's `.dvc/cache` at the
primary's, so `dvc checkout` finds the blobs and populates `data/` locally, with
no network. On btrfs this is nearly free ([[feedback_reflink_not_copy]]).

That supersedes the previous advice here, which was to point the worktree's
`.env` at the absolute primary data dir. Prefer `make data`: it gives the
worktree its *own* copy, so the gate no longer depends on a concurrent rebuild
in the primary (next paragraph). Two caveats: the hook only fires if
`core.hooksPath` is set (`make setup` — it was silently broken on padme until
2026-07-27), and `make data` still exits 255 on one run_report with no hash info
in `dvc.lock` (ticket 0380) even though the whole corpus lands. A command-line
`CLIMATE_FINANCE_DATA=… make check` does **not** work once the keystore loader is
wired into recipes, because the loader re-applies `.env` per recipe shell
([[feedback_credential_migration_all_entry_points]]).

Second trap on that shared data: the primary checkout is live. A concurrent
Phase-1 rebuild moved `refined_works.csv` mid-run (15:29 → 16:09 on 2026-07-27),
leaving `refined_embeddings.npz` / `refined_citations.csv` older and tripping the
freshness assertions. Check artifact mtimes before blaming code, and note that
running the suite against the primary data dir makes your gate result depend on
someone else's in-flight work.

Third trap, same family: **`.worktreeinclude` copies `.env` once, at worktree
creation.** A long-lived worktree therefore drifts from the primary's
machine-local config. On 2026-07-27 `make lint` failed
`test_keys_line_selects_every_consumed_credential` on `HAL_ID`/`HAL_PASSWORD`
after a rebase — the worktree's `.env` was stamped 17:49, the author updated
`KEYS=` in the primary at 17:51, and PR #1190 had meanwhile landed the code that
consumes those credentials. The branch touched nothing related. The mtime
comparison is the whole diagnosis:
`stat -c '%y' .env /home/haduong/Climate_finance/.env`; the fix is
`cp <primary>/.env .env`. Generalise: a credential/config test that fails right
after a rebase, on names your diff never mentions, is stale worktree config
until proven otherwise — the same "check mtimes before blaming code" reflex as
the paragraph above, applied to config rather than data.

---
name: feedback_corpus_rerun_byte_compare
description: "A corpus rerun is never 'obviously additive' — Flag 6 rescores 2,688 uncacheable works every time, so prove it with a stage-by-stage byte-compare."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fa43f1a4-d3ce-4606-999a-f115508717f6
  modified: 2026-07-27T14:16:30.750Z
---

Before re-running Phase 1 to change one column, back up the affected artifacts
and byte-compare every stage afterwards. Do not reason that a change is
additive; measure it.

**Why:** ticket 0347 (2026-07-27). I wrote "additive metadata only — no count
moves" into the ticket and the author approved the unfreeze on that premise. It
was not self-evident: `filter_flags_llm._load_llm_cache` keys the relevance
cache on **DOI**, so 1,908 no-DOI works (grey literature, the curated
UNFCCC/OECD layer at 0% and 12% DOI carriage) can never be cached, and 2,688
Flag-6 candidates are rescored by the cross-encoder on every `--extend`. A
model or library drift would have moved `llm_irrelevant` and taken the refined
row count — and every published statistic — with it. The byte-compare showed
it did not drift: `extended_works.csv` differed in exactly the 245 intended
cells. The claim held by a stable environment, not by design (filed as 0350).

**How to apply:**
- Back up to `data/raw/<ticket>-backup/` with `sha256sum` before the first
  write; compare each stage (unified → enriched → extended → refined, plus
  `corpus_audit.csv`) column by column, not just row counts. Headline counts
  reproducing is necessary, not sufficient.
- **Force the network closed** so the rerun cannot quietly improve on the
  frozen state: a dead proxy (`HTTP_PROXY=http://127.0.0.1:9`) plus
  `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1`. Otherwise the seed documents with
  no pooled PDF may newly fetch, gain abstracts, flip Flag 2, and move counts.
  19 of 267 keydocs seeds were in that position.
- **Run `make data` in the worktree, then run Phase 1 there.** A worktree's
  `data/` holds only `.dvc` pointers, so `catalog_merge` fails with "No catalog
  files found" — but the fix is `make data` (`dvc checkout` from the local
  cache, no network), documented in `.githooks/post-checkout` and the Makefile,
  which deliberately stopped populating worktrees eagerly after a 1.7 GB copy
  timed out creation. Do **not** work around it by running in the primary
  checkout: that is what I did on 0347, and it put the run outside the
  worktree's git isolation and skipped the DVC bookkeeping entirely (see
  below). See [[reference_machine_padme]].
- **Finish with `dvc commit` + `dvc push`, and land the `dvc.lock` diff in the
  same PR.** Regenerating a DVC-tracked artifact is not done when the bytes
  change — until it is committed, `dvc.lock` still names the old blob and every
  `dvc checkout` / `dvc pull` / `make data` returns the *previous* corpus. On
  0347 the repopulation shipped with a codebook figure describing a column the
  recorded data did not carry; the author caught it, not the byte-compare.
  Verify with `md5sum <out>` against the hash in `dvc.lock`, not with
  `dvc status` (whose script-dep noise buries the signal).
- **Don't `dvc commit` a stage you did not run.** Downstream stages whose dep
  changed will read stale; committing them asserts their outputs match inputs
  you never fed them. Leave them stale and file it (0355) unless you re-run and
  byte-compare — a `dvc.lock` that complains beats one that lies.
- Expect an undeclared dependency to surface. The rerun died at
  `CrossEncoder.__init__` because `protobuf` was missing — a lazy transitive of
  the sentencepiece tokenizer conversion, so a corpus rebuild was impossible
  until declared. When adding such a dep, check the `uv lock` diff moves
  **nothing else**: a sweep through sentence-transformers or transformers
  changes Flag 6's scores, which changes the corpus.
- Refresh the Feather handoff layer (`make corpus-handoff`) after the CSV
  changes, and skip Phase 2 only when you can show no Phase-2 script reads the
  changed column (grep `scripts/analysis` and `scripts/figures`).

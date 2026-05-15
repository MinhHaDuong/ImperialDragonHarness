---
name: per-backend queue beats cycle scheduler for asymmetric workers
description: When dispatching async work to multiple backends of different speeds, use a shared queue with per-backend workers, not itertools.cycle pre-assignment
type: feedback
originSessionId: 61fa187f-e864-4faf-b109-32780d54dacc
---
For asymmetric backends (e.g. A4000 + 3060, ~2× speed difference), strict cycle-based URL assignment forces a 50/50 split regardless of which backend is free. Tasks whose pre-assigned URL points to the slow backend hold their semaphore slot waiting on it, even when the fast backend is idle. Effective speedup ≈ 1.0× — the slow backend bottlenecks the fast one.

**Why:** Pre-assignment locks each task to a backend at scheduling time. The fast backend drains its share quickly and goes idle; queued tasks tagged for the slow backend can't be redirected. Bumping `--concurrency` doesn't help (same 50/50 split, just deeper queue). Bumping llama-server `--parallel` doesn't help either (still 50/50 routing).

**How to apply:** When designing a multi-backend dispatcher, use a shared `asyncio.Queue` and spawn one worker per backend (or N workers per backend). Each worker pulls from the queue when free, so a fast worker naturally processes more files. Test the invariant with a fake fast/slow backend pair: fast worker must process strictly more items than slow worker.

Worked example: `clean_corpus.py` refactor in PR #46 (commit 7abd185). Replaced `itertools.cycle` + `asyncio.Semaphore` with `asyncio.Queue[Path | None]` + per-backend workers via `backends[i % len(backends)]`. Measured speedup over single-A4000: 1.31× combined / 1.67× window-2 — matches theoretical max ~1.5× for A4000+3060.

The cycle-scheduler bug was *not* caught by ticket 0089's tests (`test_round_robin_alternates_backends` verified cycle order, but cycle order was the bug). A multi-expert review of the launcher script flagged it. Lesson: when reviewing scheduling code, ask "does this self-pace?" — pre-assignment schedulers fail asymmetric workloads silently.

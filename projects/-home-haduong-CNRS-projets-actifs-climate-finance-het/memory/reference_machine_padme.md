---
name: padme, the GPU server that holds the corpus
description: padme is the GPU server where corpus data lives; sessions run on doudou or padme
type: reference
originSessionId: ffb7544c-0aee-4a39-b094-7dcb6ec24e41
modified: 2026-07-27T14:16:40.650Z
---
padme is the GPU server where the corpus lives, under `$CLIMATE_FINANCE_DATA/catalogs/`. Sessions run on doudou or on padme: check `hostname` before assuming. On padme, a failing `test_corpus_acceptance.py::test_refined_works_exists` is a real problem; on doudou it means the data is absent (reach padme with `ssh padme`).

The corpus lives in the **primary checkout only**. A git worktree's `data/`
holds `.dvc` pointer files and little else — no `catalogs/`, no
`pool/keydocs/`, no `run_reports/`. And `.env` sets
`CLIMATE_FINANCE_DATA=data` (relative), so a script run inside a worktree
resolves DATA_DIR to that empty local copy; an ambient export of the absolute
path does not reliably override it, because `pipeline_loaders` calls
`load_dotenv()` on the worktree's own `.env`.

**The fix is `make data`**, not running in the primary checkout: it is
`dvc checkout` from the local cache — no network — and both
`.githooks/post-checkout` and the Makefile document it, having deliberately
stopped populating worktrees eagerly because copying ~1.7 GB timed out worktree
creation. Run it once in a fresh worktree that needs the corpus, then work
normally inside the worktree. (`make corpus-sync` also fetches from the padme
remote if the cache lacks a blob.)

Two consequences. Read a "clean rebuild produces [MISSING]" report
skeptically — an empty worktree `data/` reproduces that symptom with the
artifact present all along (ticket 0349). And never treat the empty `data/` as
a reason to run Phase 1 in the primary checkout: on 0347 that bypassed the
worktree's isolation and the DVC bookkeeping with it. See
[[feedback_corpus_rerun_byte_compare]].

## Paths and environment (moved from the index, 2026-09-24)

Repo repo `~/CNRS/projets/actifs/climate-finance-het` (same path as doudou; `~/Climate_finance` is gone, checked 2026-09-22); `uv` at `~/.local/bin/uv` (prepend PATH non-interactively); torch `--extra cpu` (doudou) / `--extra cu130` (padme); cache config in `/etc/environment`.

## Services and machine settings (checked 2026-09-25)

- Local LLM: `llama-server.service` (system unit, user haduong) runs
  `~/llama.cpp/build/bin/llama-server` with Qwen3.8-27B Q4_K_M + mmproj on
  `127.0.0.1:8080`, ctx 131072, all layers on RTX A4000 16 GB + RTX 3060 12 GB.
  Not on PATH: `command -v llama-server` misses it; look at `systemctl` and
  `pgrep -af llama-server`. No `--jinja` in its flags (needed for tool calls).
  Ticket 1140 plans to use it for the weekly source refresh.
- `Linger=no`: systemd *user* timers fire only while a session is open; use
  cron or `sudo loginctl enable-linger haduong` (ticket 1141).
- `.env` sets `PYTEST_WORKERS=16` (full suite 2 min 21 s vs 4 min 33 s at 4;
  24 is slower). doudou stays at the default 4.
- `~/.config/keys/archive.env` (Internet Archive S3 keys) copied from doudou.
- The primary checkout may sit on another session's branch; run probes in a
  throwaway worktree, and expect a fresh worktree to need `dvc checkout
  --force` (the hook's JETP documents read as "unsaved") and to fail the two
  corpus freshness tests on mtime order (ticket 1060).

**Merged from `feedback_worktree_guard_usr_bin_git.md` (2026-09-25):** Remote git on padme: the guard refuses any command text containing git, including ssh padme '... git ...'. Write the remote script to a scratchpad file and run ssh padme bash -s < <file>.

**Merged from `feedback_ssh_padme.md` (2026-09-25):** Non-interactive ssh skips the profile: ssh padme 'PATH=$HOME/.local/bin:$PATH <cmd>'; never claim padme is unreachable.

**Merged from `reference_doudou_apt_sources_after_release_upgrade.md` (2026-09-25):** padme's ufw admits ssh only from NetBird (100.64.0.0/10): if ssh padme times out, compare NetBird versions on both peers and check /etc/apt/sources.list.d/*.disabled after a release upgrade.

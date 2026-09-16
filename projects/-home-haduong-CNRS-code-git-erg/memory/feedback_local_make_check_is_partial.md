---
name: local-make-check-is-partial
description: "make check halts at the first failing target, so a local \"passed\" can mean a strict subset; an empty stray .git above the temp root triggers this and regrows"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ff375b61-7b76-4b82-bc1c-37f832cf70b0
  modified: 2026-09-16T09:35:18.266Z
---

`make check` stops at the failing target (`Makefile:56`), so every suite
ordered after it never runs and the output never says which. A local
"`make check` passed" can therefore describe a strict subset without
announcing it. During the 2026-09-16 raid I relayed that phrase more than once
while the run had halted early.

The trigger on this host: empty `.git` **directories** at `/tmp` and
`/scratch/tmp`. Go's buildvcs walks upward from the probe's `mktemp` working
directory, finds one, runs `git` there, gets exit 128, `go list` returns empty,
and `tests/test_contract.sh`'s offline **negative control** reports that the
detector failed to flag `net/http`. Not a Go-version defect -- `go list` from
the module root exits 0 on the same toolchain; the version only decides whether
the upward walk happens. Ticketed as git-erg **0287**.

Two measured facts worth keeping:

- **`rmdir` on both fixed the whole cascade**, and `make check` then ran end to
  end. That also settled a second failure (`verify: committed binary is NOT
  reproducible`) as the same cause rather than a separate defect -- it had been
  unreachable behind the halt the whole time.
- **They regrew within minutes.** Almost certainly from review agents running
  throwaway `git init` with `/tmp` as cwd. So the cleanup is housekeeping, not
  a fix, and the durable repair is making the probe immune (0287's Action 1).

**Why:** a failing negative control voids the result beside it -- the adjacent
`offline` PASS reports only that the detector said nothing, which is what a
blind detector does. And a halting cascade converts one local red into an
unreliable green for everything behind it.

**How to apply:** do not cite a local `make check` as verification in this repo
without checking it reached the end; CI (pinned Go 1.21, clean runner) is the
authority. When a suite must be re-run past a halt, run the individual
`tests/test_*.sh` rather than the aggregate, and say which ones ran. Rebuild
`build/erg` first -- `go test` compiles fresh but the shell suites run the
prebuilt binary, and a stale one produces failures that look like a merge
conflict. Related: [[verify-delivery-gate-runs-check]],
[[non-vacuity-is-per-case]].

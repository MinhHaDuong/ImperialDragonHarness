# One-time test-target mutation sweep

The finite inventory contains **11 candidates**: eight entries from `scripts/projects.json` at `d13840fbf5f537d0371b04221e1c4849893f923f`, the named VN-Power-Scenario incident, and the explicit JETP-observer and sen-causal-reading registry omissions. No registry edit or directory crawl was performed; this is not exhaustive discovery of the author’s projects.

**6 single target attempts completed**: 4 returned zero and 2 failed with unavailable completion evidence. Every completed endpoint comparison was unchanged. No test-target mutation was confirmed, so no offender ticket was created. The 5 excluded rows remain unprobed. These counts are derived from the committed JSON manifest, not separate measurements.

## Method and limits

The exact harness base carried a remote full after-merge PASS before any attempt: `d13840fbf5f537d0371b04221e1c4849893f923f`, recorded `2026-11-07T20:37:27Z`, including pytest-guard and lint. The coordinator held other suites while patient sessions ran serially in this order: padme, git-erg, harness, sen-causal-reading, AEDIST, chemin-de-voix. Each other project had its own assigned session and rules; the harness lead did not run another project’s target.

Each eligible case used the existing `test_target_probe.py` once at pinned HEAD, with a 60-second target timeout. The prerequisite tool budget was 30 seconds per eligible row. The planned batch tool ceiling is **600 seconds, derived as `6*(30+60)+60` for collection**; model overhead is excluded. Per-case timing precision varies and is recorded in the manifest; no measured total target time is claimed. There were no target retries or budget increases. Harness hunt adherence and review follow afterward; they are not additional patient attempts.

Python attempts used offline/no-Python-download settings; AEDIST and chemin additionally froze their Makefile’s uv invocation. A private environment could be populated only from already-cached pinned dependencies inside the same target budget. No separate sync, package/model acquisition, author-environment/configuration/data copy, or live service operation was performed. Git-erg used the installed newer Go toolchain with `GOTOOLCHAIN=local` and `GOPROXY=off`.

The helper compares Git status and tracked contents/modes at clean baseline and endpoint. It cannot observe ignored-file changes or write-then-restore. In particular, this clean-baseline sweep does not reproduce deletion of preexisting untracked outputs. A failed target with unchanged endpoints is **not test PASS**. No broad project gate or scientific result is validated by this diagnostic.

## Per-project outcomes

| Project | Pinned revision | Target | Observed endpoints | Helper/result status | Execution / return code | Limits |
|---|---|---|---|---|---|---|
| harness | `d13840fbf5f537d0371b04221e1c4849893f923f` | `check-fast` | unchanged | unchanged | pass / 0 | Endpoint scope only; ignored changes and restored writes unobserved. |
| git-erg | `b8d800831d6fe30047614a5220f644f587359399` | `check` | unchanged | unchanged | pass / 0 | Endpoint scope only; ignored changes and restored writes unobserved. |
| chemin-de-voix | `7087e03852475a39124f5755e68d70546e7dbea4` | `check-fast` | unchanged | unavailable | failed / 2 | Cached `torch==2.10.0` unavailable offline before tests. Not a pass. |
| padme | `e6351709fb3e511cbc707b42ea1d4105e4b5cf35` | `check` | unchanged | unchanged | pass / 0 | Endpoint scope only; ignored changes and restored writes unobserved. |
| climate-finance-het | Not pinned | `check-fast` | not-observed | unprobed | not-run / not run | Default checkout hook copies machine configuration and connects shared environment/data; no hook bypass or copying authorized. |
| aedist-technical-report | `aa41c3263d8c130ebbac4917dd02fe6190e93480` | `check-fast` | unchanged | unavailable | failed / 2 | Failed target cause not isolated. Not a pass. |
| fuzzy-corpus | Not pinned | Unavailable | not-observed | unprobed | not-run / not run | Named local path absent during read-only preparation; no other-host access or home-directory discovery. |
| cadens | Not pinned | Unavailable | not-observed | unprobed | not-run / not run | Named local path absent during read-only preparation; no other-host access or home-directory discovery. |
| VN-Power-Scenario | Not pinned | Unavailable | not-observed | unprobed | not-run / not run | Named local path absent during read-only preparation; no other-host access or home-directory discovery. |
| JETP-observer | Not pinned | `check-fast` | not-observed | unprobed | not-run / not run | Default checkout hook copies machine configuration and connects shared environment/data; no hook bypass or copying authorized. |
| sen-causal-reading | `3cdc7e5e16294e3e8986dfdcafc7ef6ee18af608` | `check` | unchanged | unchanged | pass / 0 | Endpoint scope only; ignored changes and restored writes unobserved. |

All unprobed revisions are deliberately unpinned: no diagnostic checkout was made. Fuzzy Corpus and Cadens were absent at their registered paths on this host. VN-Power-Scenario was absent at the historical path documented in closed ticket 1208; its current target/store could not be inspected, and it has no new test result. Climate-finance-het and JETP-observer were excluded because their checkout hooks copy machine configuration and connect shared environments/data; no hook bypass was attempted. Those exclusions are not findings against the projects’ normal workflows.

## Retained evidence and cleanup

Project-relative raw report/log/helper-output pointers are in `2026-11-07-test-target-sweep.json`. Already-public registry tilde paths are retained; roots for named additions are placeholders. Exact roots and path-rich captures remain only in the harness-local Git-metadata index `.git/idh/diagnostics/1463/exact-coordinate-manifest.json` and `exact-coordinate-report.md`, outside disposable executors. Each owning session byte-verified its durable local Git-metadata copies. Raw logs, source text, and tracked hash inventories are not published. These local files survive executor cleanup but do not travel with a fresh clone; pointers in the sanitized manifest supersede original scratch paths inside raw captures.

**Preserve both inconclusive probes and their containing patient executors. These coordinates are relative to the named patient project root:**

- aedist-technical-report: outer `.claude/worktrees/patient-aedist-1463`; inner `.claude/worktrees/patient-aedist-1463/diagnostics/1463/test-target-j7boxg_x/worktree`. Do not clean the outer while the retained probe is nested there.
- chemin-de-voix: outer `.claude/worktrees/1463-check-fast-28494`; inner `.claude/worktrees/1463-check-fast-28494/diagnostics/1463/test-target-qmi01dr3/worktree`. Do not clean the outer while the retained probe is nested there.

The padme, git-erg, sen, and harness helper-owned inner probes were removed by the helper after unchanged successful execution. The padme, git-erg, and sen owning sessions removed their successful outer worktrees and empty task branches after preserving raw evidence; no inconclusive evidence depended on them. The harness lead removed only its own byte-verified duplicate scratch after durable retention; it did not clean patient trees; cleanup is performed only by their owning sessions.

No confirmed offender required a patient ticket. Any later investigation of the two failed targets, unavailable projects, or unsafe setup paths is separate work; this sweep performed no source fixes.

The lead and patient served model identities were masked as described in the manifest and ticket log. Requested routing pins are not represented as observed identities.

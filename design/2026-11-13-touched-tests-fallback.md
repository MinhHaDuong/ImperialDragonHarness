# The touched-tests fallback: where the integration tier runs, and how

Status: proposed

Ticket 1551. Drafted by an agent (Claude Fable 5.2) on the author's request of
2026-11-13; every judgment below is the agent's until the author accepts.

## 1. Problem

On 2026-11-13, in the project climate-finance-het, the integration fallback of
`scripts/touched-tests.py` stopped one review and misreported another:

- a gaze (PR 2185) ran out of its time budget inside the fallback, filed no
  report and ended ESCALATE; verify-gate then refused the request;
- a verify-gate (PR 2167) printed `result: fail` on 9 tests that all died of
  CUDA out-of-memory on a card another process held, and spent about 11 of
  its 17 minutes there.

Both diffs changed one report generator under `docs/reports/` that no test
names. The reviewer has to read a red result as "not the change", by hand,
each time.

## 2. Situation

**The mechanism** (ticket 1283, commits 46ebc36af to 4e650586f). A review runs
`touched-tests.py` once: every test that names a changed file, plus, for a
changed source file no test names, `pytest -m integration tests/` when the
project declares that marker (`scripts/touched-tests.py:168`). Any `.py` file
is a source file. Gaze, verify-gate and raid each call it
(`skills/gaze/references/panel.md` step 4, `skills/verify-gate/SKILL.md`,
`skills/raid/SKILL.md`). Ticket 1283's own plan said: "If the fallback blows
gaze's budget, run the step in verify-gate only and say so."

**The measurement.** Every `answer` and `verdict` entry on `refs/notes/review`
that quotes `fallback: full integration tier`, in the harness and the seven
active projects, read on 2026-11-13 (script: parse each JSONL entry, take the
`result:` that follows the fallback line). Counts are distinct reviews.

| Project | Reviews where the tier ran | pass | real defect | false alarm | timed out |
|---|---|---|---|---|---|
| harness | 11 | 9 | 2 | 0 | 0 |
| climate-finance-het | 10 | 4 | 0 | 4 | 1 |
| JETP-observer | 4 | 0 | 0 | 1 | 3 |
| chemin-de-voix | 2 | 2 | 0 | 0 | 0 |
| archiveCIRED | 1 | 1 | 0 | 0 | 0 |
| cadens, padme, livre-milliards-climat | 0 | | | | |

Reading the rows:

- **Harness, 2 real defects.** PR 2348: a change to `scripts/worktree-clean-lib.sh`
  broke `tests/test_gaze_close.py`, which was not among the three selected
  files; only the tier saw it. PR 2013: the same library, a failure the
  selected run also showed (the record reads "1 failed, 240 passed;
  integration 1 failed"; that both are the same test is the agent's reading).
  So one catch in 28 that nothing else would have made before the merge.
- **climate-finance-het, 4 false alarms**: PRs 2046, 2102, 2136, 2167, each
  record attributing every failure to CUDA out-of-memory. The timeout is PR
  2185, taken from ticket 1551: it left no entry. One more review (PR 2154)
  quotes the fallback with no result line the script could parse; it is the
  tenth, counted in no outcome column. A passing run there took 853 s (PR 2139).
- **JETP-observer**: three runs stopped at 100, 400 and 500 s bounds; the one
  failure was a precondition assert on DVC-managed data absent from a fresh
  gate worktree.

Outside the harness: 17 reviews, no defect found, 5 false alarms, 4 timeouts.

**Why climate-finance-het differs** (read in its checkout, 2026-11-13):

- Its device selection is a Makefile prefix, `GATE_DEV`, computed by
  `scripts/qa_gate_gpu.py` (card with most free memory, else CPU). Nothing in
  `tests/conftest.py` or the pytest configuration selects a card, so a direct
  `pytest` run takes torch's default. At the time of reading, one card held
  15.5 of 16.3 GiB and the other 0.6 of 16.4.
- Its make targets run `-n $(PYTEST_WORKERS)` (default 4). The harness adds
  workers only when the project ships `scripts/pytest_workers.py`; it has
  none, so the tier ran on one process. The share of the 853 s this explains
  is not measured.
- It declares `integration` as "spawns subprocesses or uses sleep-based
  timing", on 69 of 313 test files; GPU tests carry it together with `slow`.

**Gaze's budget.** A gaze plan states a budget in minutes; the examples in
`skills/gaze/references/plan.md` run 5 to 13. Verify-gate allows the touched
tests 1800 s by default and waits under a heartbeat.

## 3. State of the art

- **Coverage-based selection.** pytest-testmon records, per test, the code it
  executed and reruns the tests a change affects. It needs a full recorded run
  and a database kept current, and by its own account a change to uncovered
  code selects nothing: the same blind spot as a file no test names, moved
  into a database. Source: <https://pypi.org/project/pytest-testmon>.
- **Device selection in pytest.** Projects that pin a device for tests do it in
  `conftest.py`, from the environment and the xdist worker id (scikit-learn's
  and torchvision's `conftest.py`); the PyTorch forum's constraint is that
  `CUDA_VISIBLE_DEVICES` must be set before CUDA initialises. Sources:
  <https://sources.debian.org/src/scikit-learn/1.8.0%2Bdfsg-3/sklearn/conftest.py>,
  <https://discuss.pytorch.org/t/disable-cuda-within-one-single-pytest-test/34037>.
- Two standard web searches, 2026-11-13. Not searched: build-graph selection
  (Bazel, Pants), which presumes a declared dependency graph none of these
  projects has.

## 4. Alternative solutions

**A. Patch the script's judgment.** Exempt paths that look like reports;
classify out-of-memory output as environmental. Direct, one merge request.
Both halves are pattern filters over content the harness does not own; the
author has ruled against patching such filters by rounds (ticket 1378).

**B. The project declares its runner.** The harness runs the touched tests
through a command or environment the project declares (a key in
`.idh-checks.json`), with an ignore list. Solves device, workers and scope at
once and for the selected tests too. Costs a new contract, a declaration in
every project, and a second way to run tests beside the project's own.

**C. Delete the fallback.** An unnamed file is reported `incomplete: not
covered`. Removes both symptoms. The measurement prices it: the harness loses
the PR 2348 catch before merge (the after-merge run would have painted main
red instead, the case ticket 1283 was filed to end).

**D. Put the tier where it fits, and make direct pytest safe.** A different
family: no new judgment in the script.
- Harness: gaze runs the selection only; the fallback runs once, in
  verify-gate, which already has the budget and the heartbeat. This is what
  ticket 1283 planned for this case.
- Project: the device selection moves to where a direct `pytest` sees it
  (`conftest.py`, calling the existing `qa_gate_gpu.py` when
  `CUDA_VISIBLE_DEVICES` is unset), and the project ships
  `scripts/pytest_workers.py`, the hook the harness already reads.

## 5. Synthesis and recommendation

**D.** The measurement says the fallback works where direct pytest is safe
(harness: 11 runs, no false alarm, one catch nothing else made) and fails
where it is not. The defect is in the two places D touches, not in the idea
of a fallback.

| | Agent time | Author time | Undo |
|---|---|---|---|
| A | ~1 h, 1 request | ruling | revert |
| B | ~3 h, 2 requests, then each project | ruling, and a declaration to review per project | revert, plus the declarations |
| C | ~1 h, 1 request | ruling | revert |
| D | ~1 h harness, ~1 h in climate-finance-het | ruling | revert each |

What D costs: a defect only the tier sees is found at the gate, one step later
than today, and costs a re-gate round (PR 2348 was caught by gaze's second
round). What it saves: the tier runs once per request, not once in gaze and
again in the gate.

What D leaves open, on purpose: a report script still triggers the tier, in
the gate, at the project's speed. No rule in the harness can tell a report
script from a library without the project saying so. If the count in § 6
still shows cost without yield, B's ignore list alone is the next step.

Ticket 1551's criteria would change: criterion 1 (device) is met in
climate-finance-het, with its regression test there; criterion 2 (no ESCALATE
from the fallback outrunning a gaze) is met in the harness.

## 6. Implementation plan

1. **Harness, ticket 1551.** `touched-tests.py` gains a way to run the
   selection only, printing that the fallback is left to the gate; gaze's
   panel step uses it; verify-gate and raid are unchanged. One merge request.
   Proves: a gaze on a diff with an unnamed file ends inside its budget.
2. **climate-finance-het, a ticket there.** Device selection in `conftest.py`;
   `scripts/pytest_workers.py`. Proves: `pytest -m integration tests/` run
   directly on padme with one card busy passes, and its wall time with
   workers is known.
3. **Later review, 2026-11-27.** Rerun the count of § 2 on entries dated after
   both landed. Evidence that reopens the question: any false alarm or timeout
   from the tier in a gate, or a defect that reached main which gaze's old
   fallback run would have caught.

Not planned: a JETP-observer ticket for the DVC precondition (one occurrence,
below the severity floor; this note is the record).

## Review

Pending: two decorrelated advisor reviews and a KISS pass.

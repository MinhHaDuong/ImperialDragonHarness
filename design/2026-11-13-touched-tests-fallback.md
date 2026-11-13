# The touched-tests fallback: a bound in the harness, a safe direct pytest in the project

Status: accepted 2026-11-13

Ticket 1551. Drafted by an agent (Claude Fable 5.2) on the author's request of
2026-11-13 and revised once after two advisor reviews (§ Review); the
author accepted the plan on 2026-11-13.

## 1. Problem

In the project climate-finance-het, the integration fallback of
`scripts/touched-tests.py` stops reviews and misreports others:

- two gazes (PR 2154 on 2026-11-12, PR 2185 on 2026-11-13) ran 300 s inside
  the fallback, never reached a result and ended ESCALATE with no finding;
  on PR 2185 verify-gate then refused the request;
- four verify-gates printed `result: fail` on tests that died of CUDA
  out-of-memory on a card another process held; on PR 2167 that took about
  11 of the gate's 17 minutes.

Each time, a reviewer has to read a red or missing result as "not the change",
by hand.

## 2. Situation

**The mechanism** (ticket 1283, commits 46ebc36af to 4e650586f). A review runs
`touched-tests.py` once: every test that names a changed file, plus, for a
changed source file no test names, `pytest -m integration tests/` when the
project declares that marker (`scripts/touched-tests.py:168`). Any `.py` file
is a source file. Gaze and verify-gate run it; raid only lists
(`--list`) to decide whether its gate needs a `gate-seat` agent
(`skills/raid/SKILL.md`). Ticket 1283's plan said: "If the fallback
blows gaze's budget, run the step in verify-gate only and say so."

**No bound on the run.** Verify-gate has a recipe for a long run: detached,
under a heartbeat, 1800 s by default (`skills/verify-gate/SKILL.md`). Gaze's
panel step has none (`skills/gaze/references/panel.md`, step 4), and no 300 s
appears in the gaze skill or scripts: the two 300 s stops look like a timeout
the reviewing agent chose for its own shell call. A run killed from outside
prints no `result:` line, so the plan check fails and gaze must ESCALATE.

**The measurement.** Population: every `answer` or `verdict` entry on
`refs/notes/review` whose text holds `fallback: full integration tier`, in the
harness and the seven active projects, read on 2026-11-13. Unit: the review
(`review_id`); a review with several entries is classed by its worst tier
outcome. PR 2185 is added from ticket 1551: it left no entry. Review ids and
the reading script are in the appendix.

| Project | Reviews where the tier ran | pass | real defect | false alarm | timed out |
|---|---|---|---|---|---|
| harness | 11 | 9 | 2 | 0 | 0 |
| climate-finance-het | 10 | 4 | 0 | 4 | 2 |
| JETP-observer | 4 | 0 | 0 | 1 | 3 |
| chemin-de-voix | 2 | 2 | 0 | 0 | 0 |
| archiveCIRED | 1 | 1 | 0 | 0 | 0 |
| cadens, padme, livre-milliards-climat | 0 | | | | |

The table describes what happened; with 28 reviews and unlike projects it
does not compare effectiveness.

- **Harness, 2 real defects.** PR 2348: a change to
  `scripts/worktree-clean-lib.sh` broke `tests/test_gaze_close.py`, not among
  the three selected files; only the tier saw it, in gaze's second round. PR
  2013: the same library; the selected run failed too. The tier there runs in
  about 2 minutes (PR 2348 round 3: 1611 passed, review duration 2m08s).
- **climate-finance-het.** False alarms: PRs 2046, 2102, 2136, 2167, each
  record attributing every failure to CUDA out-of-memory. Timeouts: PRs 2154
  and 2185. A passing run took 853 s (PR 2139).
- **JETP-observer.** Three runs stopped at 100, 400 and 500 s; the one failure
  was a precondition assert on DVC-managed data absent from a fresh gate
  worktree. Neither the device nor the worker count of climate-finance-het
  explains these.

Outside the harness: 17 reviews, no defect found, 5 false alarms, 5 timeouts.

**Why climate-finance-het's direct pytest is unsafe** (its checkout,
2026-11-13). Device selection is a Makefile prefix, `GATE_DEV`, printed by
`scripts/qa_gate_gpu.py` (card with most free memory, else CPU under `nice`).
Nothing in `tests/conftest.py` or the pytest configuration selects a card, so a
direct `pytest` takes torch's default; at the time of reading one card held
15.5 of 16.3 GiB and the other 0.6 of 16.4. Its make targets also run
`-n $(PYTEST_WORKERS)` (default 4), while the harness adds workers only when
the project ships `scripts/pytest_workers.py`, which it does not: the tier ran
on one process. How much of the 853 s that explains is not measured.

## 3. State of the art

Projects that pin a device for tests do it in `conftest.py`, from the
environment (scikit-learn, torchvision); `CUDA_VISIBLE_DEVICES` must be set
before CUDA initialises, and under pytest-xdist the controller loads
`conftest.py` before it spawns workers, which inherit its environment.
Sources: <https://sources.debian.org/src/scikit-learn/1.8.0%2Bdfsg-3/sklearn/conftest.py>,
<https://pytest-xdist.readthedocs.io/en/stable/how-it-works.html>.
Coverage-based selection (pytest-testmon, <https://pypi.org/project/pytest-testmon>)
was looked at and set aside: a change to uncovered code selects nothing, the
same blind spot kept in a database. Two standard web searches; build-graph
selection (Bazel, Pants) not searched.

## 4. Alternative solutions

**A. Patch the script's judgment**: exempt paths that look like reports,
classify out-of-memory output as environmental. Both are pattern filters over
content the harness does not own (ruled against, ticket 1378).

**B. The project declares its runner**: an optional override, default today's
behaviour, through which the harness runs the touched tests (the project could
reuse its Makefile prefix). Fair in its small form; it still leaves the
project with a direct `pytest` that fails for anyone who types it.

**C. Delete the fallback.** Loses the PR 2348 catch before merge.

**D. Run the fallback in verify-gate only** (the first draft's pick). Ends
the gaze timeouts, but removes the tier from gaze in the harness, the one
place it paid, to fix a problem the harness does not have; a defect it would
have caught then costs a gate REROLL and a second gaze. A gaze with no gate
after it loses the coverage silently.

**E. Bound the tier, and make direct pytest safe.**
- Harness: `touched-tests.py` takes a bound on the integration run. At the
  bound it stops the run and prints `result: incomplete (integration tier
  stopped at N s)`, exit 4, which gaze and the gate already report "as such,
  never as a pass". Gaze passes a bound that fits its budget; verify-gate
  keeps its own. The harness tier (2 minutes) still runs in gaze.
- Project: device selection moves to where a direct `pytest` sees it.

## 5. Synthesis and recommendation

**E.** The tier works where direct pytest is safe and fast, and fails where it
is not; E repairs those two places and adds no judgment to the script. Each
half is about an hour of agent time and one merge request, undone by a revert.
Both advisors rejected D; E is the Opus seat's proposal, and it answers the
Codex seat's objection that deferral leaves a standalone gaze uncovered
without saying so.

What E leaves open, on purpose:

- **A script no test names still triggers the tier.** PR 2185 changed a report
  generator and `scripts/catalog_rel_r0_service_abstracts.py`; the harness
  cannot tell which of the two deserved the tier without the project saying
  so. In gaze the cost is now capped; in the gate it is the project's tier at
  the project's speed.
- **Workers.** Parallel GPU tests raise memory pressure; the project measures
  before it ships `scripts/pytest_workers.py`.
- **JETP-observer's timeouts** get the bound, not a cause.

Ticket 1551's criteria under E: criterion 2 is met in the harness; criterion
1 is met in climate-finance-het; criterion 3 splits, one regression test in
each repository (§ 6). The author rules on that amendment.

## 6. Implementation plan

1. **Harness, ticket 1551, one merge request.** The bound in
   `touched-tests.py`; gaze's panel step passes it; `--list` output unchanged
   (raid reads its `fallback:` line). Regression test first: a tier that
   outruns the bound yields `result: incomplete` and exit 4, where today the
   run has no bound. Settled on 2026-11-13 by a probe of
   `seat_clock.py plan-check` on a two-item plan: with no report for the
   tests item the check fails (the PR 2154 and 2185 shape); with a report
   whose result is `incomplete` it passes. The plan check needs no change.
2. **climate-finance-het, a ticket there.** `qa_gate_gpu.py` exposes its choice
   as values; the root `conftest.py` sets `CUDA_DEVICE_ORDER` and
   `CUDA_VISIBLE_DEVICES` before any torch import when the caller set neither
   (an empty value counts as set), and lowers priority on the CPU path. Costs
   to state there: an `nvidia-smi` probe on every pytest start, and a
   free-memory threshold tuned for the gate. Regression test: with the
   selector stubbed to "card 0 busy", a direct run targets the other card.
   Then measure the tier's wall time with 1 and 4 workers and decide on
   `scripts/pytest_workers.py`.
3. **Later review, 2026-11-27.** Rerun the appendix script on entries dated
   after both landed. Evidence that reopens the question: an out-of-memory
   false alarm in a gate, a gaze ESCALATE on the tier, or `incomplete` on most
   climate-finance-het gazes (then B's override or a project ignore list is
   next).

Not planned: a JETP-observer ticket for the DVC precondition (one occurrence,
below the severity floor).

## Review

Reviewed at commit 9e26b1ced (first draft, recommending D); this revision has
not been reviewed again.

- **Codex seat**: gpt-6.1-sol, provider openai, `codex exec --sandbox
  read-only`; model and provider as printed in the run's header. Independent
  family. Pick: modified D. Findings taken: PR 2185 changed two files, not
  one; a standalone gaze loses coverage under D; criterion 3 had no plan;
  raid calls `--list`, whose output must not change; the measurement lacked
  ids, a population rule and a script; workers are unmeasured and can raise
  memory pressure; B was described in its heaviest form.
- **Opus seat**: claude-opus-5-5 as self-reported, a subagent of the drafting
  session. Same family as the drafter, another model. Pick: the project half
  first, then a bounded tier in gaze (E). Findings taken: PR 2154 is a second
  gaze timeout; the 300 s is not a harness constant and gaze has no long-run
  recipe; D costs a REROLL and a second gaze, not "one step later";
  `qa_gate_gpu.py` prints a shell prefix and needs a value interface; the
  first draft's cost table and most of § 3 informed nothing.
- **Not taken**: the Opus seat's order (project first, then decide on the
  harness). JETP-observer's three timeouts do not depend on that project, so
  the bound stands on its own.
- **KISS pass** (both seats): cut the cost table, the testmon paragraph, the
  marker count; drop the workers script from the first fix.

## Appendix: the count

Reviews where the tier ran, by `review_id`:

- harness: rv-20261028-pr-1894-d282, rv-20261028-pr-1923-1159,
  rv-20261029-pr-1984-1cfd, rv-20261029-pr-2000-7017, rv-20261029-pr-2002-c472,
  rv-20261029-pr-2013-7a1a (defect), rv-20261105-pr-2216-91b1,
  rv-20261107-pr-2239-129c, rv-20261109-pr-2297-edab,
  rv-20261109-pr-2348-4758 (defect), rv-20261110-pr-2394-9c74.
- climate-finance-het: rv-20261108-pr-2030-c958, rv-20261109-pr-2046-f57e
  (false alarm), rv-20261110-pr-2096-1911, rv-20261110-pr-2102-0788 (false
  alarm), rv-20261112-pr-2136-83ca (false alarm), rv-20261112-pr-2139-b29d,
  rv-20261112-pr-2154-72a5 (timeout), rv-20261112-pr-2160-6923,
  rv-20261113-pr-2167-7499 (false alarm), rv-20261113-pr-2185-a173 (timeout,
  no entry).
- JETP-observer: rv-20261108-pr-267-aef9, rv-20261109-pr-277-1f12,
  rv-20261109-pr-285-6328 (timeouts), rv-20261109-pr-292-7cbd (false alarm).
- chemin-de-voix: rv-20261109-pr-182-a369, rv-20261109-pr-187-4507.
- archiveCIRED: rv-20261031-pr-67-7953.

The outcome of each review was read by the agent from the text after the
fallback line; the script only finds and prints them.

```python
import json, re, subprocess, sys

def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout

for repo in sys.argv[1:]:
    for obj in (l.split("\t", 1)[1] for l in git(repo, "ls-tree", "-r", "refs/notes/review").splitlines()):
        for line in git(repo, "show", f"refs/notes/review:{obj}").splitlines():
            if "fallback: full integration tier" not in line:
                continue
            entry = json.loads(line)
            if entry.get("kind") not in ("answer", "verdict"):
                continue
            text = json.dumps(entry, ensure_ascii=False)
            tail = text[text.find("fallback: full integration tier"):][:1500]
            result = re.search(r"result: [^\\\"]{0,160}", tail)
            print(repo, entry["review_id"], entry["kind"], entry["ts"][:16], result.group(0) if result else "result: ?", sep=" | ")
```

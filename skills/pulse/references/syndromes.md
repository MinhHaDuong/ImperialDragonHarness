# Usual syndromes

Read only the entries your differential points to. Each gives the symptom, the usual causes in rough order of frequency, the evidence that separates them, and what not to do. The causes are priors from past cases, not findings about this project.

## The loop gate is slow (agents idle on every edit)

- **Causes.** The runner is serial while a worker plugin is already a dependency. A few very slow tests sit on the fast path. The first run in a fresh worktree builds the environment. The suite reads data the measurement environment lacks, or has.
- **Evidence.** `profile` the tier: if the top handful hold half the time, it is a tail problem. `collect`: a first-of-session median far above the later one points at set-up, not tests. Compare `--collect-only` counts between a bare worktree and the real checkout.
- **Do not.** Time it in a bare worktree and conclude it is fast: one project's tier measured 272 s with its data present and 12.6 s without, because 750 tests were deselected instead of 81.

## A few tests hold most of the time

- **Causes.** Smoke or end-to-end tests that train, embed or simulate; a network or data-pull test on the fast path; a fuzz or property test with a large default budget.
- **Evidence.** `profile --top 10`: top-5 share, tests over 1 s and over 10 s, slowest files. Check whether the heavy tests are already marked.
- **Treat per test**: shrink the fixture, mark it into a slower tier, move it to the ex-post run, or cache the stage it exercises. Name each test moved.

## A docs-only change pays for the full gate

- **Evidence.** `collect`: long full-gate waits in sessions that changed no code (read the session's changed paths, not just its commands).
- **Treat.** A path-scoped gate map that selects cheap targets for doc paths and falls back to the full gate for anything unmapped or any source file. It fails safe.

## The same gate runs again and again, or in parallel agents

- **Causes.** Re-running after every small fix; several executors each launching the full suite; a loop gate with no scoped form.
- **Evidence.** `collect`: many runs of one gate per session; overlapping waits across sessions on one host.
- **Treat.** A brief rule naming the scoped gates and forbidding the rest; a scoped target; one runner for the shared suite.

## A stale green (a cached or selected pass after a change that should fail)

- **Causes.** An undeclared dependency: a data file read through a child process, a file read by a path built at run time, an environment variable, a tool version, an absent file whose presence the test asserts against, live state.
- **Evidence.** Record which files each test opens (an audit hook for in-process reads, a syscall trace for child processes) and diff against what the cache declared. Restore a changed input and watch whether the test reruns.
- **Do not.** Use selection or caching in a merge gate, or trust it before the inputs are declared.

## Red, then green, with no code change (flaky)

- **Causes.** Order dependence, shared temporary state, time, network, parallel workers sharing a resource.
- **Evidence.** Rerun the same commit repeatedly, serially and in parallel, in shuffled order, and see which tests flip.
- **Treat.** Fix the cause. Quarantine only as a stopgap: the test keeps running, stops blocking, and carries a deadline after which it is fixed or deleted. Never add silent retries.

## The gate outlasts the tool's time limit

- **Evidence.** `collect`: many waits clustered at the same maximum.
- **Treat.** Run the gate in the background and wait on completion; split it into targets; give the stall detector the gate's measured cold time as its allowance.

## Live-state tests inside the gate

- **Causes.** Network, local model servers, the clock, git history.
- **Treat.** Mark them and run them in a separate tier that is allowed to be skipped with a stated reason, never as a silent pass.

## Tests changed alongside the code to get green

- **Evidence.** In a sample of commits, look for deleted test files or functions, new unconditional skip markers, fewer assertions, widened tolerances. Hand-read the hits: most are refactors and spec changes.
- **Treat.** A short sentence in the commit body for any deletion or loosening. A ban on changing tests with code would hit a third of commits to prevent an event that a history sample did not show.

## A testbase that pins prose

- **Causes.** Each wording change in a skill, rule or doc shipped with a test asserting its phrase is present; review rounds asked for "a ratchet"; a retired guard's tests outlived it.
- **Evidence.** Test files that read only Markdown and assert `"<phrase>" in text`; prose PRs whose test file changed in step with the sentence; review rounds spent on test wording.
- **Do not.** Count them as coverage, or cut them all at once: some pin an interface string or a past incident (see *Thin the wording pins*).

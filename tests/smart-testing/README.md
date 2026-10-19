# Smart testing (opt-in)

Run `uv sync --frozen`, then `make smart-test`. Testmon selects affected fast
Python tests and updates its private database after execution. A fresh checkout
restores the committed SQL and recorded file inputs. If no compatible reference
exists, or the Python/package environment changed, the tool learns the fast tier
once. The lockfile does not choose a Python interpreter: matching the reference's
runtime permits immediate reuse; another supported runtime learns its own state.
This works without a daemon, shared writable database, or host-specific paths.

`make smart-refresh` runs the fast tier and exports SQL + JSON for fresh
worktrees and isolated coding containers. Publish both together from one writer;
do not merge agent databases or edit SQL. Existing local learning takes priority
over later committed references. Delete `.smart-testing/` to restore the reference
again. An incomplete local database/input pair starts cold. Do not run concurrent
smart-test writers in one worktree.

Testmon tracks executed Python. The companion pytest plugin records explicit
project file reads, including Python source read as text, during setup, call and
teardown. Collection reads belong to their test module; reads made while importing a
shared Python module conservatively affect the fast tier. A changed known
input reruns its fast consumer modules with Testmon disabled, then native Python
selection runs normally. A failed consumer remains stale and is retried. Tests
can run twice when both their Python and data inputs change; no private Testmon
API or second selection framework is involved.

Only previously observed inputs are checked. Private/generated caches and the
SQL/JSON transport artifacts are excluded (a reference cannot hash itself). Content hashes are reused while
file stat identity is unchanged; content and mode changes, deletion and previously
attempted missing-file reads invalidate consumers. Unrelated prose/tickets do
not trigger a refusal or rebuild. Bookkeeping still scales with recorded inputs
and native dependency checks; constant-time startup is not promised.

This is development feedback, not merge certification. It does not track arbitrary
filesystem queries (existence-only checks, directory/glob membership), environment
variables, external services, subprocess reads, or files outside the checkout.
Run the relevant explicit checks when changing those inputs. Integration, slow,
and adherence tiers and all existing gates retain their current scope.

## Why the small file-read adapter?

Testmon's data-file limitation is documented upstream in
[issue 178](https://github.com/tarpas/pytest-testmon/issues/178); explicit file
dependencies remain an open [enhancement](https://github.com/tarpas/pytest-testmon/issues/12).
`pytest-tia` was investigated at `03746af5e7f6feb2873548093cd943bcc90149bf`:
its `.txt` dependency positive control selected its reader, but a failing `.py`
source-text comment change selected no tests, even with `--all-changes`. Its
[recorder excludes Python files](https://github.com/breadMSA/pytest-tia/blob/03746af5e7f6feb2873548093cd943bcc90149bf/tia/plugin.py#L27).
The adapter handles the demonstrated read dependency without adding a generic
filesystem watcher or changing Testmon's internals.

The measured pilot belongs with ticket 1099 (validation latency). Tickets 0376
(repeated full checks), 0954 (scoped check targets), 1100 (review convergence),
and 1045 (candidate merge evidence) remain separate concerns. Selecting fast
Python tests does not replace those checks or their evidence.

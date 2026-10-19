# Smart testing (opt-in)

In this harness, run `uv sync --frozen`, then `make smart-test`.

For another pytest project, run from that project's checkout, using its Python
and dependencies and the selected harness's entry point:

```sh
uv run --with pytest-testmon==2.2.0 python "$IDH_ROOT/scripts/smart_testing.py" --root "$PWD"
```

Resolve `IDH_ROOT` from the loaded harness, including a frozen arena snapshot;
do not point it at a different live installation. The helper defaults to the
current working directory and uses the project's configured pytest discovery
(`testpaths` included). It neither imports the harness's `scripts` package into
the workload nor changes `PYTHONPATH`. State stays in the workload's
`.smart-testing/`, which ignores its own contents without editing the project
ignore file; `--refresh` exports to its `tests/smart-testing/` directory.
Projects declare their own indirect inputs and live-state opt-outs in conftest;
the harness declarations are not injected into other projects. Non-pytest checks
retain their existing commands. Use the normal project check when smart testing
reports unsupported selection or parallel pytest options; a test failure is a
failure and must be fixed, not bypassed.

 Testmon selects affected
Python tests across all cost tiers and updates its private database after execution. A fresh checkout
restores the committed SQL and recorded file inputs. If no compatible reference
exists, or the Python/package environment changed, the tool learns the eligible suite
once. The lockfile does not choose a Python interpreter: matching the reference's
runtime permits immediate reuse; another supported runtime learns its own state.
This works without a daemon, shared writable database, or host-specific paths.

`make smart-refresh` runs every tier and exports SQL + JSON for fresh
worktrees and isolated coding containers. Publish both together from one writer;
do not merge agent databases or edit SQL. Existing local learning takes priority
over later committed references. Delete `.smart-testing/` to restore the reference
again. An incomplete local database/input pair starts cold. Do not run concurrent
smart-test writers in one worktree.

Testmon tracks executed Python. The companion pytest plugin records explicit
project file reads, including Python source read as text, during setup, call and
teardown. Collection reads belong to their test module; reads made while importing a
shared Python module conservatively affect the eligible suite. A changed known
input reruns its consumer modules with selection disabled while refreshing
Testmon coverage, then native Python selection handles remaining affected tests. A failed consumer remains stale and is retried. Tests
can run twice when both their Python and data inputs change; no private Testmon
API or second selection framework is involved.

Only previously observed inputs are checked. Private/generated caches and the
SQL/JSON transport artifacts are excluded (a reference cannot hash itself). Content hashes are reused while
file stat identity is unchanged; content and mode changes, deletion and previously
attempted missing-file reads invalidate consumers. Unrelated prose/tickets do
not trigger a refusal or rebuild. Bookkeeping still scales with recorded inputs
and native dependency checks; constant-time startup is not promised.

Slow, integration and adherence tests are cacheable too. Cost markers do not
control eligibility. `tests/conftest.py` declares indirect child-process inputs
with `smart_inputs(*paths)` (literal paths or globs). Glob membership is checked
against Git's tracked and unignored file inventory on every invocation; unchanged
file hashes are reused. Direct subprocess file arguments and local Python `-m`
entry points and package initializers are recorded automatically, including
`src/` layouts found through the child PYTHONPATH and project search roots.
This does not trace the child's transitive imports: declare those source inputs
when they are not already covered. This does not trace arbitrary child
process reads: declare indirect inputs explicitly. Globs use Git-tracked and
unignored paths, so ignored DVC outputs need exact-path declarations (including
missing expected files) or live opt-outs. A `.dvc` pointer alone cannot detect
bytes becoming available after a pull.

`smart_inputs("version:pi")` fingerprints the full stdout/stderr returned by
`pi --version`, once per helper/pytest process. `version:$VARIABLE` also tracks an
optional executable override. Only hashes are exported. Failed or empty probes
stay stale. This trusts the tool's detailed version response to identify its
installation; code changed without changing that response is outside this
contract. Perch's installation tests use these declarations for Claude Code,
Codex and Pi, so unchanged installations do not repeat discovery queries.

Tests that depend on live services, unversioned external tools or Git history use
`smart_always` and run on every invocation. Their module list is retained in the
private state and portable reference. A successful refresh includes them too.
The inventory check collects only modules named by its evidence pointers and
records those modules and its collection helpers as file inputs. Seat-runner's
source/stub tests are a separate cacheable case; its Git reference sweep and real
container check remain live. The stub tests use a fixture aider installation,
so their coverage does not depend on whether a developer installed aider.
Changes to project pytest configuration invalidate the eligible suite. Shared
fixtures and initial conftest reads are shared dependencies. An older cache or
recorder scope is upgraded by learning all eligible tiers once. The pytest
selection/plugin environment is fingerprinted too; changing it learns a fresh
baseline. Exported metadata contains its hash, not raw environment values.

The helper explicitly includes all cost tiers, overriding default `-m` filters.
Other partial-selection/dry-run options (`-k`, `--lf`, collect-only, deselect,
ignore) and xdist execution are rejected before a cache can be certified.
Required project plugins and other addopts are preserved. A cold empty suite is
not treated as a successful warm deselection.

This is development feedback, not merge certification. Undeclared filesystem
queries, environment variables, external services and files outside the checkout
are not tracked. Use `smart_inputs` for file dependencies and `smart_always` for
live state. All existing explicit checks and merge gates retain their scope.

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
and 1045 (candidate merge evidence) remain separate concerns. Selecting affected
Python tests does not replace those checks or their evidence.

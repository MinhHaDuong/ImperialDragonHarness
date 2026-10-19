# Smart testing (opt-in)

`make smart-test` restores the committed SQL reference into a private SQLite
file on first use, then asks pytest-testmon to run affected fast unit tests.
Subsequent calls reuse that worktree's database. Git carries the reference to
new clones, worktrees and containers; no shared writable database or service.

Use `uv sync --frozen` and the same Python minor version. An incompatible
package environment or a missing reference stops with an explanation; it never
silently starts a full learning run. `make smart-refresh` explicitly runs the
fast tier once and exports its memory. Publish SQL + JSON together after a
successful reference run, from one branch, rather than merging SQL from agents.
Delete `.smart-testing/` to return to the committed reference. SQLite is restored
atomically; do not run two smart-test processes in the same worktree.

This is an acceleration of the Python fast loop, not a merge certification.
Testmon observes Python execution, not subprocess internals, reads of files,
network services or external state. Non-Python repository input changes refuse
selection and request an explicit `make check-fast`; Python launching a child
process can also require explicit tests. Integration, slow and adherence tiers
remain under the existing gates. Tests added or changed in Python are handled
by Testmon. An unchanged run can exit successfully with all tests deselected.

The reference source_commit identifies the source checkout used to learn;
content changes are evaluated by Testmon, not by requiring an identical HEAD.
A different machine is supported only with matching Python/packages and relevant
external state. The SQL is text for transport/review, not semantically mergeable
coverage data. Do not hand-edit it.

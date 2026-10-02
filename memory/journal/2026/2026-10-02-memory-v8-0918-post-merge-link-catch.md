# Relocated-clone proof caught the protocol's own links post-merge

Context: memory-v8 acceptance trial STEP A (ticket 0918) merged to main as
PR #1137 on 2026-10-02; the predeclared evaluation protocol
(docs/memory-v8/evaluation-protocol.md) was the delivered document. The
branch had passed `make check` locally before the merge request was opened.

Observation: CI's pytest-guard failed on
tests/test_memory-v8_pilot.py::test_relocated_clone_remains_readable — the
pilot's relocated-clone proof scans every Markdown file under memory/ and
docs/memory-v8/ and requires each relative link to resolve to a file inside
the moved clone. The freshly merged protocol contained three directory
references (memory/dreams/ twice, memory/journal/ once) that resolve only to
directories, which the proof treats as unresolved. The failure was visible
only in CI: the local pre-PR `make check` run had passed because the
protocol file did not yet exist on main when the pilot test's clone was
taken in earlier rounds, and the trial worktree's own gate ran before the
document was committed to main.

Consequence: the defect was caught by an already-merged guard rather than
by the author's pre-merge gate; the fix (pointing the three references at
concrete existing files) landed on the same branch as commit 3c7aa8cb and
all ten CI checks went green on the new head. No rollback of the merge was
needed and no trial ran against the broken document.

Evidence: PR #1137 review/CI history (pytest-guard run 110809758291), the
fix commit 3c7aa8cb93e93e6a3a9f7cd44d3d9b9349b65448, and the guard itself
at tests/test_memory_v8_pilot.py (unresolved_links requires
resolved.is_file()). The gap between the local gate and CI was not
investigated beyond confirming the new-head run was green; its cause is
recorded as attributed uncertainty, not established fact.

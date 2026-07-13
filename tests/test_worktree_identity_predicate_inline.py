"""Keep the two inline worktree-identity predicates in lockstep (ticket 0302).

Ticket 0302 decided NOT to extract a shared `scripts/lib/worktree-identity.sh`.
Rationale (recorded here and in the ticket log): of the sites that carry a
worktree predicate, only two share the exact identity check —

- `scripts/pretooluse-worktree-path-guard.sh` `_in_worktree()` (advisory hook,
  fail-open), and
- `skills/merge/erg-pr-merge` `in_worktree()` (standalone skill, self-contained
  by design).

The two integrity guards (`scripts/guard-worktree-identity.sh`,
`scripts/guard-commit-on-main.sh`) read the hook-JSON `.cwd` through `git -C`
and are fail-CLOSED, and `scripts/block-pr-merge-in-worktree.sh` uses a
deliberately different linked-worktree predicate — none can share one helper
without changing an input model or a fail-open/fail-closed contract, which the
ticket's invariant forbids. A `source scripts/lib/…` from the skill would also
couple it across the scripts/↔skills/ boundary and, under `set -euo pipefail`,
turn a missing lib into a nonzero abort — flipping the hook's fail-open
semantics.

Keeping the two copies inline avoids that coupling; this test supplies the
drift protection extraction would have given: the two function bodies must stay
byte-identical (name and comments aside). If a future edit must change one, it
must change both, or revisit the 0302 decision. Complements the 0310 ratchet,
which forbids regressing EITHER copy to the weak file-test predicate.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

SITES = [
    ("scripts/pretooluse-worktree-path-guard.sh", "_in_worktree"),
    ("skills/merge/erg-pr-merge", "in_worktree"),
]


def _extract_body(relpath: str, fn_name: str) -> list[str]:
    """Return the normalized body of `fn_name` in `relpath`.

    Normalization drops the definition line (names differ), comment-only lines,
    and blank lines, and strips trailing whitespace — so two copies that differ
    only in name and surrounding commentary compare equal.
    """
    lines = (REPO / relpath).read_text(encoding="utf-8").splitlines()
    open_re = f"{fn_name}() {{"
    start = next(
        (i for i, line in enumerate(lines) if line.strip() == open_re), None
    )
    assert start is not None, (
        f"definition line `{open_re}` not found in {relpath} — the function was "
        "renamed or reformatted; update SITES or this parser (ticket 0302)"
    )
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line == "}":  # closing brace at column 0
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        body.append(line.rstrip())
    assert body, f"empty body extracted for {fn_name} in {relpath}"
    return body


@pytest.mark.adherence
def test_inline_worktree_predicates_are_identical():
    (ref_path, ref_fn), (other_path, other_fn) = SITES
    ref = _extract_body(ref_path, ref_fn)
    other = _extract_body(other_path, other_fn)
    assert ref == other, (
        "The two inline worktree-identity predicates have drifted (ticket 0302 "
        f"decided to keep them inline in lockstep):\n"
        f"  {ref_path}:{ref_fn}()\n"
        f"  {other_path}:{other_fn}()\n"
        "Change both together, or revisit the 0302 keep-inline decision.\n"
        f"{ref_fn}: {ref}\n{other_fn}: {other}"
    )

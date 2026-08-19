#!/usr/bin/env python3
"""Mutation probe: delete a guard, demand the test that names it goes red.

Written as a file rather than inline shell because three inline attempts in one
session silently failed to apply their own mutation — the quoting ate the
pattern, pytest passed, and "1 passed" was reported as evidence the guard was
covered. It was evidence of nothing. Every mutation here asserts that it
actually changed the file before the suite runs.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "knowledge_hints.py"

MUTATIONS = [
    ("declarative framing",
     "This project records that knowledge in",
     "Read, before answering, at",
     "declarative"),
    ("scalar-terms guard",
     "    if not isinstance(value, list):\n        return []",
     "    if not isinstance(value, (list, str)):\n        return []",
     "scalar_terms"),
    ("one-line collapse",
     'return re.sub(r"\\s+", " ", text).strip()[:cap]',
     "return text[:cap]",
     "multiline_summary"),
    ("hint-count cap",
     "        if len(out) >= MAX_HINTS:",
     "        if False:",
     "hint_count_is_capped"),
    ("path containment",
     "return target if target.is_relative_to(root_r) else None",
     "return target",
     "escape_the_repo"),
    ("session_id sanitisation",
     'sid = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "nosession")[:64]',
     'sid = session_id or "nosession"',
     "session_id_cannot_escape"),
]


def main() -> int:
    original = SCRIPT.read_text()
    failures = []
    try:
        for name, old, new, selector in MUTATIONS:
            if old not in original:
                failures.append(f"{name}: MUTATION TARGET ABSENT — probe is blind")
                continue
            SCRIPT.write_text(original.replace(old, new, 1))
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/test_knowledge_hints.py",
                 "-q", "-k", selector],
                capture_output=True, text=True, cwd=SCRIPT.parent.parent,
            )
            survived = r.returncode == 0
            print(f"  {'SURVIVED (bad)' if survived else 'killed'}  {name}")
            if survived:
                failures.append(f"{name}: no test fails when the guard is deleted")
            SCRIPT.write_text(original)
    finally:
        SCRIPT.write_text(original)

    for f in failures:
        print(f"FAIL {f}", file=sys.stderr)
    print(f"mutation probe: {len(MUTATIONS) - len(failures)}/{len(MUTATIONS)} guards defended")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

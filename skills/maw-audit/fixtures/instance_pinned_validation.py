"""Scope/altitude fixture — an INSTANCE-PINNED regression test.

A durable validation ANCHOR for the maw-audit scope (altitude) pass, not
production code. It embodies the property the scope pass must flag: a test that
catches a defect at ONE site but leaves a structurally-parallel SIBLING site
unguarded — it guards the past instance, not the future class.

Two structurally-identical validators (`validate_username`, `validate_email`)
share one defect CLASS: a missing length-bound check. There is a regression test
for the username bound (the "instance" that once had a bug) but NONE for the
email bound (the parallel "sibling"). The same mutation operator — delete the
`len(...) <= MAX` guard — is CAUGHT at `validate_username` (its regression test
goes red) but SURVIVES at `validate_email` (no sibling test). The scope pass
replays the caught operator at the sibling and should classify the test as
``instance-pinned``, suggesting promotion to a class/invariant guard (a
table-driven test over both fields).
"""

MAX_LEN = 64


def validate_username(value: str) -> bool:
    # Site A (the INSTANCE with a regression test). The bound check below is the
    # operator the fang pass mutates (delete it) and the scope pass replays at
    # the sibling site B.
    if not value:
        return False
    if len(value) > MAX_LEN:  # <-- the class defect: drop this guard.
        return False
    return True


def validate_email(value: str) -> bool:
    # Site B (the structurally-parallel SIBLING). SAME shape as site A, SAME
    # class defect — but NO regression test guards this bound. The replayed
    # operator (delete the len guard) SURVIVES here, exposing the instance
    # pinning.
    if not value or "@" not in value:
        return False
    if len(value) > MAX_LEN:  # <-- the same class defect; unguarded by tests.
        return False
    return True

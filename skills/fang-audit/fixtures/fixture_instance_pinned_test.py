"""The INSTANCE-PINNED regression test for the scope fixture (anchor, not CI).

It guards the length bound at ONE site (`validate_username`) but NOT the
structurally-parallel sibling (`validate_email`). The same class-defect mutation
(delete the `len(...) <= MAX_LEN` guard) is therefore CAUGHT at site A and
SURVIVES at site B — the under-scope (instance-pinned) defect the fang-audit
scope pass must flag.

Not collected by the project test run (`fixture_..._test.py`, not `test_*.py`);
an artifact the scope pass reads. The right-scoped counterpart would be a
table-driven test over BOTH fields (the class guard the scope pass suggests).
"""


def test_username_rejects_overlong():
    # Regression test for site A only — the username bound. There is NO parallel
    # test for validate_email's bound, so the defect class is half-guarded.
    from instance_pinned_validation import validate_username, MAX_LEN

    assert validate_username("a" * MAX_LEN) is True
    assert validate_username("a" * (MAX_LEN + 1)) is False  # the guarded instance


# NOTE (the under-scope this fixture anchors): there is deliberately NO
# `test_email_rejects_overlong` here. validate_email has the identical bound and
# the identical class defect, but no sibling test — so the scope pass, replaying
# the caught "delete the len guard" operator at validate_email, finds it
# SURVIVES, and flags this test as instance-pinned (promote to a class guard).

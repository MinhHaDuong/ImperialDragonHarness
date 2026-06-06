"""KNOWN-BAD smoke fixture for the test-audit-llm read-and-judge lenses.

This file is a deliberate anti-pattern — a durable anchor that the judge MUST
flag on at least one lens (it trips all four). It is NOT collected by the project
test run: the filename is `fixture_*_test.py`, not `test_*.py`, and
`pytest.ini` excludes `skills/*/fixtures` via `norecursedirs`. Do not "fix" it —
its badness is the fixture.

The four lenses it anchors (see the docstring of `payment_gateway.py`):
  1. faithfulness/test-reality gap — `PaymentGateway.charge` is mocked, so the
     subject-under-test never executes; the test stays green even if `charge`
     is gutted.
  2. intent legibility — the test NAME claims it checks that a charge "succeeds",
     but the body asserts the internal call ORDER. The name lies.
  3. negative-space coverage — only the happy path. The amount<=0 guard, the
     over-limit branch, the short-account boundary: never exercised.
  4. change-detector smell — asserts the exact SEQUENCE of internal method calls
     (validate -> reserve -> settle) instead of the observable return value.
"""

from unittest.mock import MagicMock, call


def test_charge_succeeds():
    # LIE: the name promises a "charge succeeds" outcome assertion. The body does
    # no such thing — it mocks the gateway and asserts internal call order.
    gw = MagicMock()  # faithfulness gap: the real PaymentGateway never runs.

    gw.charge("acct-1", 100)

    # change-detector smell + intent lie: asserts HOW (internal call sequence),
    # never WHAT (the settled total). Mocking the subject means the real
    # validation/arithmetic is never observed at all.
    gw._validate.assert_not_called()  # vacuous on a fresh MagicMock
    assert gw.mock_calls == [call.charge("acct-1", 100)]

    # negative-space: no amount<=0, no over-limit, no short-account, no empty
    # account, no boundary at exactly the limit. Only this single happy path.

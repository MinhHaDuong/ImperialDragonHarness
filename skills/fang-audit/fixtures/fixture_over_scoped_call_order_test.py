"""The OVER-SCOPED test for the handcuff fixture (a durable anchor, not CI).

This test deliberately asserts on the exact CALL ORDER of the notifications —
internal form the `notify_all` contract does NOT promise. It therefore goes RED
under a behavior-preserving reorder of the independent notifications, which is
exactly the handcuff (over-scope) defect the fang-audit handcuff pass must flag.

It is NOT collected by the project test run (the filename is
`fixture_..._test.py`, not `test_*.py`); it is an artifact the handcuff pass
reads. The correctly-scoped counterpart would assert only the OUTCOME (each
observer notified once with the payload), which stays green under the refactor.
"""

from unittest.mock import call


def test_notify_all_calls_observers_in_registration_order():
    # OVER-SCOPED: asserts the exact ORDER of calls across the two independent
    # observers. The contract promises each observer is notified once with the
    # payload — NOT the order. This assertion is the handcuff.
    from over_scoped_call_order import Notifier
    from unittest.mock import MagicMock

    a, b = MagicMock(), MagicMock()
    n = Notifier()
    n.register(a)
    n.register(b)
    n.notify_all("event")

    # The over-scoped assertion: a MUST be notified before b. A behavior-
    # preserving reorder of the independent notifications breaks this while
    # changing nothing observable about the outcome.
    parent = MagicMock()
    parent.attach_mock(a.notify, "a_notify")
    parent.attach_mock(b.notify, "b_notify")
    # Asserting on mock_calls ORDER is the over-scope smell this fixture anchors.
    assert parent.mock_calls == [call.a_notify("event"), call.b_notify("event")]

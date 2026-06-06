"""Handcuff fixture — a test that is OVER-SCOPED on mock call ORDER.

This is a durable validation ANCHOR for the maw-audit handcuff (robustness)
pass, not production code and not a runnable demo. It embodies the property the
handcuff pass must flag: a test that goes RED on a behavior-PRESERVING refactor.

The contract of `notify_all` is: "every observer in the registry is notified
exactly once." The ORDER of notifications is NOT part of that contract — the
observers are independent and the registry is an unordered set semantically.

The accompanying test (`tests/fixture_over_scoped_call_order_test.py`) wrongly
asserts the EXACT call ORDER. So the behavior-PRESERVING refactor below — swap
the two independent ``notify`` calls / iterate the registry in a different but
equivalent order — leaves observable behavior identical (same observers, same
payload, each once) yet makes the over-scoped test go RED. That red is a
HANDCUFF: the handcuff pass should classify it as ``handcuff`` and its skeptic
should confirm the refactor changed no observable behavior.
"""


class Notifier:
    def __init__(self):
        # Semantically an unordered set of observers; the contract does not
        # promise any notification order.
        self._observers = []

    def register(self, observer):
        self._observers.append(observer)

    def notify_all(self, payload):
        # ORIGINAL form. The behavior-preserving refactor reorders these two
        # independent notifications (or reverses the iteration) — no observer,
        # payload, or count changes. A test asserting the exact order is the
        # handcuff this fixture exists to surface.
        for observer in self._observers:
            observer.notify(payload)


# --- behavior-PRESERVING refactor the handcuff pass would apply ---------------
# Reordering independent ``observer.notify`` calls is behavior-neutral: the same
# set of observers receives the same payload exactly once. Only a test that
# over-asserts on call ORDER (not outcome) goes red. Reference form:
#
#     def notify_all(self, payload):
#         for observer in reversed(self._observers):
#             observer.notify(payload)
#
# Outcome-asserting tests (each observer notified once, with this payload) stay
# GREEN; order-asserting tests go RED — and that red is the over-scope defect.

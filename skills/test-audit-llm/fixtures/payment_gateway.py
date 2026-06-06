"""Smoke-fixture subject for the test-audit-llm read-and-judge lenses.

A durable validation ANCHOR (not production code, not a runnable demo). It is the
SUBJECT-UNDER-TEST that the companion `fixture_payment_gateway_test.py` is
supposed to exercise — but that test mocks the subject away, tests only the happy
path, asserts on call order, and carries a name that lies. Those are exactly the
defects the four read-and-judge lenses must flag:

  - faithfulness / test-reality gap  → the test mocks `charge` itself, so the
    real arithmetic and validation never run; the test can stay green while this
    code regresses.
  - intent legibility                → the test is named `test_charge_succeeds`
    but actually asserts the internal call ORDER, not that a charge succeeds.
  - negative-space coverage          → only the happy path; the amount<=0 guard,
    the over-limit branch, and the empty-account boundary are never touched.
  - change-detector smell            → asserts the exact sequence of internal
    calls (validate → reserve → settle) instead of the observable outcome.

The judge READS both files and JUDGES — it never runs anything.
"""


class PaymentGateway:
    def __init__(self, limit: int):
        self._limit = limit
        self._ledger: list[tuple[str, int]] = []

    def charge(self, account: str, amount: int) -> int:
        # Real arithmetic + validation a faithful test would exercise.
        if not account:
            raise ValueError("account must be non-empty")
        if amount <= 0:
            raise ValueError("amount must be positive")        # negative-space
        if amount > self._limit:
            raise ValueError("amount exceeds limit")           # negative-space
        self._validate(account)
        self._reserve(account, amount)
        return self._settle(account, amount)

    def _validate(self, account: str) -> None:
        if len(account) < 3:
            raise ValueError("account id too short")

    def _reserve(self, account: str, amount: int) -> None:
        self._ledger.append((account, -amount))

    def _settle(self, account: str, amount: int) -> int:
        self._ledger.append((account, amount))
        return sum(a for _, a in self._ledger)

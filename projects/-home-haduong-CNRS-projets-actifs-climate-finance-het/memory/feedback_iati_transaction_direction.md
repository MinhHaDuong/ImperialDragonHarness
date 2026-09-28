# IATI transaction direction is part of the mapping

Ticket 0886 / PR #1548: the panel found IATI TransactionType 11 (incoming commitment) mapped to the ledger flow type used for code 2 (outgoing commitment). This inflated the mapped flow count by 71. Code 11 was withheld; code 13 (incoming pledge) follows the same policy. The frozen slice has 1,301 activity lines and 7,770 mapped flows.

When mapping source transaction codes into a shared finance vocabulary, inspect direction and perspective as well as the word “commitment” or “pledge”. Check the authoritative code list and use a test that distinguishes incoming from outgoing codes. Preserve raw source codes in the ledger when a shared mapping is withheld. See `scripts/jetp/build_iati_comparators.py`, `tests/test_jetp_comparators_iati.py`, and `tickets/closed/0886-comparateurs-iati-energie-quatre-pays.erg`.

# Blind scoring rubric (ticket 1414)

Score each anonymous output item by item: 1 = complies, 0 = violates, N/A only where the item cannot apply. Quote the violating text for every 0. You are not told which system produced an output or under what instructions; do not guess.

## Task 1 outputs (T1-xx): Python script + test, against prompts/rule1.md
- P1 No legacy typing generics (`typing.List/Dict/Tuple/Optional/Union`) and no `from __future__ import annotations`. (No type hints at all = 1.)
- P2 The script's `__main__` entry point uses argparse.
- P3 No hardcoded paths: the input (and any output) path is a CLI parameter.
- P4 `logging` is used for messages, not `print`. (Printing the final report to stdout counts as print: 0.)
- P5 No `sys.path` hacks and no ABC classes.
- P6 The test file is named `tests/test_<module>.py` (a `tests/` directory and `test_` + module name).
- P7 Type hints present where they clarify intent (public function signatures annotated).

## Task 2 outputs (T2-xx): French paragraph, against prompts/rule2.md
- F1 Quotes use French guillemets « » only (no straight or English quotes).
- F2 Decimal comma, never a decimal point.
- F3 None of the banned vocabulary/phrases of the LLMism list (e.g. "il est important de noter", "paysage", "robuste", "leverage"-type verbs, "témoignage de", "naviguer", "explorer", "dive") and no "pas seulement X, mais Y" antithesis.
- F4 At most one em-dash in the paragraph.
- F5 No importance inflation ("crucial", "essentiel", "clé", "vital", "critique").
- F6 No tricolon padding (reflexive three-item lists) and no hedging stack.
- F7 No weak copula where a verb exists ("constitue", "joue un rôle", "sert de").
- F8 No transition drumbeat (consecutive sentences opening with "Par ailleurs", "En outre", "De plus", "Notamment"...).
- F9 Active voice, concrete wording; a specific number rather than "plusieurs".

Return, per output: the item scores, the quoted violations, and the total.

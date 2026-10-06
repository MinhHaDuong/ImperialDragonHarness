"""Portable model-intention vocabulary.

The two enums skills and tests share. Translation to concrete models and effort
settings belongs to the active runtime, not to this module (policy decision of
2026-10-01; the Phase 0 `ClaudeMapping` dry-run class was removed 2026-10-06).
"""

MODEL_LEVELS = ("auto", "cheap", "standard", "strong", "frontier")
EFFORTS = ("economy", "standard", "intensive")

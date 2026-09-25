"""Portable model intentions and the Phase 0 Claude Code translation.

This module is a dry-run contract. Live skill and agent pins remain authoritative
until later migration phases. Claude Agent launches accept model tokens but no
effort argument; effort can be pinned on an agent definition instead.
"""

from dataclasses import dataclass, field
from typing import Literal

ModelLevel = Literal["auto", "cheap", "standard", "strong", "frontier"]
Effort = Literal["economy", "standard", "intensive"]
MODEL_LEVELS = ("auto", "cheap", "standard", "strong", "frontier")
EFFORTS = ("economy", "standard", "intensive")


@dataclass(frozen=True)
class ClaudeMapping:
    # Explicit local default: Claude Code has no router for an Agent launch.
    auto_tier: str = "sonnet"
    tiers: dict[str, str] = field(default_factory=lambda: {
        "cheap": "haiku",
        "standard": "sonnet",
        "strong": "opus",
        "frontier": "fable",
    })
    efforts: dict[str, str] = field(default_factory=lambda: {
        "economy": "low",
        "standard": "medium",
        "intensive": "high",
    })

    def model(self, level: ModelLevel) -> str:
        if level not in MODEL_LEVELS:
            raise ValueError(f"unsupported model level: {level}")
        token = self.auto_tier if level == "auto" else self.tiers[level]
        if token not in {"haiku", "sonnet", "opus", "fable"}:
            raise ValueError(f"invalid Claude Agent model token: {token}")
        return token

    def effort(self, level: Effort) -> str:
        if level not in EFFORTS:
            raise ValueError(f"unsupported effort: {level}")
        token = self.efforts[level]
        if token not in {"low", "medium", "high", "xhigh", "max"}:
            raise ValueError(f"invalid Claude effort: {token}")
        return token

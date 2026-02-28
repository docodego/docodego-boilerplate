"""Shared dataclasses for scoring results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DimensionResult:
    """Score result for a single scoring dimension.

    Used by all tools (ICS, CCS, SDS, CSG, SHS, SCR).
    Band thresholds: low 0-8, mid 9-18, high 19-25.
    """

    name: str
    score: int
    max_score: int = 25
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def band(self) -> str:
        """Compute band from current score (always up-to-date)."""
        if self.score <= 8:
            return "low"
        if self.score <= 18:
            return "mid"
        return "high"

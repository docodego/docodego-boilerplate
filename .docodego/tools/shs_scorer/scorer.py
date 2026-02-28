"""SHS scoring engine — corpus-level result and gate logic."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scoring_common.types import DimensionResult

from .dim_budget_structure import (
    score_line_budget,
    score_structural_completeness,
)
from .dim_status_refs import (
    score_reference_coverage,
    score_status_consistency,
)
from .parser import ParsedHealthSpec


@dataclass
class SHSResult:
    """Complete SHS scoring result."""

    status_consistency: DimensionResult
    reference_coverage: DimensionResult
    line_budget: DimensionResult
    structural_completeness: DimensionResult
    total: int = 0
    status: str = ""
    approved: bool = False
    blocked: bool = False
    block_reason: str = ""

    def __post_init__(self):
        self.total = (
            self.status_consistency.score
            + self.reference_coverage.score
            + self.line_budget.score
            + self.structural_completeness.score
        )

    @property
    def dimensions(self) -> list[DimensionResult]:
        return [
            self.status_consistency,
            self.reference_coverage,
            self.line_budget,
            self.structural_completeness,
        ]


def score_corpus(
    specs: list[ParsedHealthSpec],
    *,
    threshold: int = 60,
    line_limit: int = 300,
    data_heavy_limit: int = 400,
    flows_dir: Path | None = None,
    fail_on_zero_dimension: bool = True,
) -> SHSResult:
    """Score a spec corpus against the SHS rubric."""
    sc = score_status_consistency(specs)
    rc = score_reference_coverage(specs, flows_dir=flows_dir)
    lb = score_line_budget(specs, line_limit, data_heavy_limit)
    stc = score_structural_completeness(specs)

    result = SHSResult(
        status_consistency=sc,
        reference_coverage=rc,
        line_budget=lb,
        structural_completeness=stc,
    )

    # Gate logic
    if fail_on_zero_dimension and any(
        d.score == 0 for d in result.dimensions
    ):
        zero_dims = [d.name for d in result.dimensions if d.score == 0]
        result.blocked = True
        result.block_reason = f"Zero score on: {', '.join(zero_dims)}"
        result.status = f"BLOCKED — {result.block_reason}"
        result.approved = False
    elif result.total < 40:
        result.status = (
            "Not ready for review — return to author for rework"
        )
        result.approved = False
    elif result.total < threshold:
        result.status = "Under review — not ready for composition"
        result.approved = False
    elif result.total >= 80:
        result.status = "High-quality spec corpus"
        result.approved = True
    else:
        result.status = "Approved — corpus health acceptable"
        result.approved = True

    return result

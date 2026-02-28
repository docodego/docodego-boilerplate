"""CSG corpus scoring engine — 4 dimensions x 25 = 100."""

from __future__ import annotations

from dataclasses import dataclass

from scoring_common.types import DimensionResult

from .dim_constants_http import score_http_status_semantics, score_shared_constants
from .dim_state_perms import score_permission_symmetry, score_state_machine_consistency
from .types import ParsedCorpusSpec


@dataclass
class CSGResult:
    """Complete CSG scoring result for a corpus."""

    shared_constants: DimensionResult
    http_status_semantics: DimensionResult
    state_machine_consistency: DimensionResult
    permission_symmetry: DimensionResult
    total: int = 0
    status: str = ""
    approved: bool = False
    blocked: bool = False
    block_reason: str = ""

    def __post_init__(self) -> None:
        self.total = (
            self.shared_constants.score
            + self.http_status_semantics.score
            + self.state_machine_consistency.score
            + self.permission_symmetry.score
        )

    @property
    def dimensions(self) -> list[DimensionResult]:
        return [
            self.shared_constants,
            self.http_status_semantics,
            self.state_machine_consistency,
            self.permission_symmetry,
        ]


def score_corpus(
    specs: list[ParsedCorpusSpec],
    *,
    threshold: int = 60,
    fail_on_zero_dimension: bool = True,
) -> CSGResult:
    """Score a corpus of parsed specs against the CSG rubric.

    Returns a full CSGResult with per-dimension scores, status,
    and gate decision.
    """
    result = CSGResult(
        shared_constants=score_shared_constants(specs),
        http_status_semantics=score_http_status_semantics(specs),
        state_machine_consistency=score_state_machine_consistency(
            specs,
        ),
        permission_symmetry=score_permission_symmetry(specs),
    )

    # Gate logic
    if fail_on_zero_dimension and any(
        d.score == 0 for d in result.dimensions
    ):
        zero_dims = [
            d.name for d in result.dimensions if d.score == 0
        ]
        result.blocked = True
        result.block_reason = (
            f"Zero score on: {', '.join(zero_dims)}"
        )
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
        result.status = "High-quality specification corpus"
        result.approved = True
    else:
        result.status = "Approved — composition may begin"
        result.approved = True

    return result

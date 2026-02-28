"""SDS scoring engine — result class and gate logic."""

from __future__ import annotations

from dataclasses import dataclass

from scoring_common.types import DimensionResult

from .dim_input_defense import score_defense_depth, score_input_surface
from .dim_threat_auth import score_auth_boundary, score_threat_taxonomy
from .parser import ParsedSpec


@dataclass
class SDSResult:
    """Complete SDS scoring result."""

    threat_taxonomy: DimensionResult
    auth_boundary: DimensionResult
    input_surface: DimensionResult
    defense_depth: DimensionResult
    total: int = 0
    status: str = ""
    approved: bool = False
    blocked: bool = False
    block_reason: str = ""

    def __post_init__(self) -> None:
        self.total = (
            self.threat_taxonomy.score
            + self.auth_boundary.score
            + self.input_surface.score
            + self.defense_depth.score
        )

    @property
    def dimensions(self) -> list[DimensionResult]:
        return [
            self.threat_taxonomy,
            self.auth_boundary,
            self.input_surface,
            self.defense_depth,
        ]


def score_spec(
    spec: ParsedSpec,
    *,
    threshold: int = 60,
    fail_on_zero_dimension: bool = True,
) -> SDSResult:
    """Score a parsed spec against the SDS rubric."""
    threat_tax = score_threat_taxonomy(spec)
    auth_bound = score_auth_boundary(spec)
    input_surf = score_input_surface(spec)
    defense_dep = score_defense_depth(spec)

    result = SDSResult(
        threat_taxonomy=threat_tax,
        auth_boundary=auth_bound,
        input_surface=input_surf,
        defense_depth=defense_dep,
    )

    # Gate logic (same as CCS — no threat_floor for SDS)
    if fail_on_zero_dimension and any(
        d.score == 0 for d in result.dimensions
    ):
        zero_dims = [d.name for d in result.dimensions if d.score == 0]
        result.blocked = True
        result.block_reason = f"Zero score on: {', '.join(zero_dims)}"
        result.status = f"BLOCKED \u2014 {result.block_reason}"
        result.approved = False
    elif result.total < 40:
        result.status = (
            "Not ready for review \u2014 return to author for rework"
        )
        result.approved = False
    elif result.total < threshold:
        result.status = "Under review \u2014 not ready for composition"
        result.approved = False
    elif result.total >= 80:
        result.status = "High-quality specification"
        result.approved = True
    else:
        result.status = "Approved \u2014 composition may begin"
        result.approved = True

    return result

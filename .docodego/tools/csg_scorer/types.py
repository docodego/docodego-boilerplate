"""Dataclasses for CSG parsed corpus data."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PermissionRow:
    """A single row from a Permission Model table."""
    role: str
    action: str
    allowed: bool
    spec_name: str = ""


@dataclass
class StateTransition:
    """A single row from a State Machine table."""
    from_state: str
    to_state: str
    trigger: str
    guard: str
    spec_name: str = ""


@dataclass
class HttpStatusMention:
    """An HTTP status code mention with surrounding context."""
    code: int
    context: str
    spec_name: str
    line_num: int


@dataclass
class ExtractedConstant:
    """A numeric constant extracted from a spec."""
    value: float
    unit: str
    normalized_seconds: float | None
    context: str
    line_num: int
    spec_name: str = ""


@dataclass
class ParsedCorpusSpec:
    """Cross-spec analysis data extracted from a single spec."""
    filepath: Path
    name: str
    business_rules: str = ""
    constraints: str = ""
    acceptance_criteria: str = ""
    permission_rows: list[PermissionRow] = field(default_factory=list)
    state_transitions: list[StateTransition] = field(
        default_factory=list,
    )
    http_status_mentions: list[HttpStatusMention] = field(
        default_factory=list,
    )
    constants: list[ExtractedConstant] = field(default_factory=list)

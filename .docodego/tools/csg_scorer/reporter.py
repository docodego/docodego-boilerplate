"""Output formatters for CSG scoring results."""

from __future__ import annotations

from typing import Any

from scoring_common.reporter import (
    format_json as _format_json,
    format_text as _format_text,
    result_to_dict,
)

from .scorer import CSGResult

TOOL_KEY = "csg"

# Re-export for __main__.py
_result_to_dict = result_to_dict


def format_text(
    result: CSGResult, *, filename: str = "", threshold: int = 60,
) -> str:
    """Format CSG result as human-readable text report."""
    return _format_text(
        result, tool_key=TOOL_KEY, filename=filename, threshold=threshold,
    )


def format_json(
    result: CSGResult, *, filename: str = "", threshold: int = 60,
) -> str:
    """Format CSG result as audit JSON."""
    return _format_json(
        result, tool_key=TOOL_KEY, filename=filename, threshold=threshold,
    )

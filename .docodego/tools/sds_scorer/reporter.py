"""Output formatters for SDS scoring results."""

from __future__ import annotations

from scoring_common.reporter import (
    format_json as _format_json,
    format_text as _format_text,
    result_to_dict,
)

from .scorer import SDSResult

TOOL_KEY = "sds"

# Re-export for __main__.py
_result_to_dict = result_to_dict


def format_text(
    result: SDSResult, *, filename: str = "", threshold: int = 60,
) -> str:
    """Format SDS result as human-readable text report."""
    return _format_text(
        result, tool_key=TOOL_KEY, filename=filename, threshold=threshold,
    )


def format_json(
    result: SDSResult, *, filename: str = "", threshold: int = 60,
) -> str:
    """Format SDS result as audit JSON."""
    return _format_json(
        result, tool_key=TOOL_KEY, filename=filename, threshold=threshold,
    )

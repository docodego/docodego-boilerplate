"""Output formatters for ICS scoring results."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .scorer import DimensionResult, ICSResult

TOOL_KEY = "ics"


def _bar(score: int, max_score: int = 25, width: int = 20) -> str:
    """Render a simple ASCII progress bar."""
    filled = int((score / max_score) * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def _dim_to_dict(dim: DimensionResult) -> dict[str, Any]:
    """Serialize a single dimension result."""
    return {
        "score": dim.score,
        "max_score": dim.max_score,
        "band": dim.band,
        "issues": dim.issues,
        "suggestions": dim.suggestions,
    }


def _result_to_dict(
    result: ICSResult, *, threshold: int = 60,
) -> dict[str, Any]:
    """Serialize ICS result into the tool-level dict."""
    return {
        "score": result.total,
        "threshold": threshold,
        "passed": result.approved,
        "blocked": result.blocked,
        "block_reason": result.block_reason,
        "status": result.status,
        "dimensions": {
            dim.name.lower().replace(" ", "_"): _dim_to_dict(dim)
            for dim in result.dimensions
        },
    }


def format_text(result: ICSResult, *, filename: str = "", threshold: int = 60) -> str:
    """Format ICS result as human-readable text report."""
    lines: list[str] = []

    header = "ICS Score Report"
    if filename:
        header += f" -- {filename}"
    lines.append(header)
    lines.append("=" * len(header))
    lines.append("")

    status_symbol = "PASS" if result.approved else ("BLOCKED" if result.blocked else "FAIL")
    lines.append(f"Overall: {result.total} / 100  {status_symbol} (threshold: {threshold})")
    lines.append(f"Status:  {result.status}")
    lines.append("")

    lines.append("Dimensions:")
    for dim in result.dimensions:
        bar = _bar(dim.score)
        symbol = "+" if dim.score > 0 else "-"
        lines.append(f"  {dim.name:<18} {bar} {dim.score:>2} / {dim.max_score}  [{dim.band}]  {symbol}")
    lines.append("")

    all_issues = [
        f"  [{dim.name}] {issue}"
        for dim in result.dimensions
        for issue in dim.issues
    ]
    if all_issues:
        lines.append("Issues:")
        lines.extend(all_issues)
        lines.append("")

    all_suggestions = [
        f"  [{dim.name}] {sug}"
        for dim in result.dimensions
        for sug in dim.suggestions
    ]
    if all_suggestions:
        lines.append("Suggestions:")
        lines.extend(all_suggestions)
        lines.append("")

    return "\n".join(lines)


def format_json(result: ICSResult, *, filename: str = "", threshold: int = 60) -> str:
    """Format ICS result as audit JSON.

    Schema:
        { spec, timestamp, tools: { ics: { score, threshold, ... } } }
    """
    data: dict[str, Any] = {
        "spec": filename,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tools": {
            TOOL_KEY: _result_to_dict(result, threshold=threshold),
        },
    }
    return json.dumps(data, indent=2)

"""Output formatters for ICS scoring results."""

from __future__ import annotations

import json
from typing import Any

from .scorer import ICSResult


def _bar(score: int, max_score: int = 25, width: int = 20) -> str:
    """Render a simple ASCII progress bar."""
    filled = int((score / max_score) * width)
    return "\u2588" * filled + "\u2591" * (width - filled)


def _pass_fail(score: int, threshold: int = 0) -> str:
    """Return a pass/fail symbol."""
    return "PASS" if score > threshold else "FAIL"


def format_text(result: ICSResult, *, filename: str = "", threshold: int = 60) -> str:
    """Format ICS result as human-readable text report."""
    lines: list[str] = []

    header = "ICS Score Report"
    if filename:
        header += f" -- {filename}"
    lines.append(header)
    lines.append("=" * len(header))
    lines.append("")

    # Overall
    status_symbol = "PASS" if result.approved else ("BLOCKED" if result.blocked else "FAIL")
    lines.append(f"Overall: {result.total} / 100  {status_symbol} (threshold: {threshold})")
    lines.append(f"Status:  {result.status}")
    lines.append("")

    # Dimensions
    lines.append("Dimensions:")
    for dim in result.dimensions:
        bar = _bar(dim.score)
        symbol = "+" if dim.score > 0 else "-"
        lines.append(f"  {dim.name:<18} {bar} {dim.score:>2} / {dim.max_score}  [{dim.band}]  {symbol}")
    lines.append("")

    # Issues
    all_issues = []
    for dim in result.dimensions:
        for issue in dim.issues:
            all_issues.append(f"  [{dim.name}] {issue}")

    if all_issues:
        lines.append("Issues:")
        lines.extend(all_issues)
        lines.append("")

    # Suggestions
    all_suggestions = []
    for dim in result.dimensions:
        for sug in dim.suggestions:
            all_suggestions.append(f"  [{dim.name}] {sug}")

    if all_suggestions:
        lines.append("Suggestions:")
        lines.extend(all_suggestions)
        lines.append("")

    return "\n".join(lines)


def format_json(result: ICSResult, *, filename: str = "", threshold: int = 60) -> str:
    """Format ICS result as JSON."""
    data: dict[str, Any] = {
        "file": filename,
        "overall_score": result.total,
        "threshold": threshold,
        "threshold_met": result.approved,
        "blocked": result.blocked,
        "block_reason": result.block_reason,
        "status": result.status,
        "dimensions": {},
    }

    for dim in result.dimensions:
        key = dim.name.lower().replace(" ", "_")
        data["dimensions"][key] = {
            "score": dim.score,
            "max_score": dim.max_score,
            "band": dim.band,
            "issues": dim.issues,
            "suggestions": dim.suggestions,
        }

    return json.dumps(data, indent=2)

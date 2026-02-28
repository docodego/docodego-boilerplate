"""Load audit JSON files and compute summary statistics."""

from __future__ import annotations

import json
from pathlib import Path

TOOL_ORDER = ["ics", "ccs", "csg", "shs", "scr"]

TOOL_INFO: dict[str, dict[str, str]] = {
    "ics": {"name": "Intent Clarity", "scope": "file"},
    "ccs": {"name": "Convention Clarity", "scope": "file"},
    "csg": {"name": "Constraint Symmetry", "scope": "corpus"},
    "shs": {"name": "Spec Health", "scope": "corpus"},
    "scr": {"name": "Supply Chain Radar", "scope": "corpus"},
}


def load_audits(audit_dir: Path) -> tuple[list[dict], list[dict]]:
    """Load all audit files. Returns (per_spec, corpus) lists."""
    per_spec: list[dict] = []
    corpus: list[dict] = []

    for fp in sorted(audit_dir.rglob("*.audit.json")):
        data = json.loads(fp.read_text(encoding="utf-8"))
        data["_file"] = str(fp.relative_to(audit_dir))
        data["_group"] = fp.parent.name
        if fp.name == "_corpus.audit.json":
            corpus.append(data)
        else:
            per_spec.append(data)

    return per_spec, corpus


def compute_stats(
    per_spec: list[dict], corpus: list[dict],
) -> dict:
    """Compute summary statistics (camelCase keys for JS)."""
    tool_scores: dict[str, list[int]] = {k: [] for k in TOOL_ORDER}
    tool_pass: dict[str, int] = {k: 0 for k in TOOL_ORDER}
    tool_fail: dict[str, int] = {k: 0 for k in TOOL_ORDER}
    total_issues = 0
    total_suggestions = 0
    group_counts: dict[str, int] = {}

    for spec in per_spec + corpus:
        if spec not in corpus:
            group = spec.get("_group", "unknown")
            group_counts[group] = group_counts.get(group, 0) + 1
        for tk, tv in spec.get("tools", {}).items():
            if tk in tool_scores:
                tool_scores[tk].append(tv["score"])
                if tv.get("passed"):
                    tool_pass[tk] += 1
                else:
                    tool_fail[tk] += 1
            for dv in tv.get("dimensions", {}).values():
                total_issues += len(dv.get("issues", []))
                total_suggestions += len(dv.get("suggestions", []))

    return {
        "toolScores": tool_scores,
        "toolPass": tool_pass,
        "toolFail": tool_fail,
        "totalSpecs": len(per_spec),
        "totalCorpus": len(corpus),
        "totalIssues": total_issues,
        "totalSuggestions": total_suggestions,
        "groupCounts": group_counts,
    }

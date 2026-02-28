"""SHS dimensions: Status Consistency and Reference Coverage."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from scoring_common.types import DimensionResult

from .anti_gaming import INFRASTRUCTURE_STEMS, VALID_STATUSES
from .parser import ParsedHealthSpec


# ── Dimension 1: Status Consistency (0-25) ─────────────────────────────


def score_status_consistency(
    specs: list[ParsedHealthSpec],
) -> DimensionResult:
    """Score status consistency across subdirectory groups."""
    result = DimensionResult(name="Status Consistency", score=0)

    if not specs:
        result.issues.append("No specs found in directory")
        return result

    groups: dict[str, list[ParsedHealthSpec]] = {}
    for spec in specs:
        groups.setdefault(spec.subdirectory, []).append(spec)

    total_specs = len(specs)
    consistent_count = 0
    invalid_found = False

    for group_name, group_specs in sorted(groups.items()):
        statuses: list[str] = []
        for s in group_specs:
            st = s.frontmatter.get("status", "").lower().strip()
            if not st:
                result.issues.append(
                    f"{s.name}: missing status in frontmatter"
                )
                invalid_found = True
                statuses.append("")
            elif st not in VALID_STATUSES:
                result.issues.append(
                    f"{s.name}: invalid status '{st}'"
                )
                invalid_found = True
                statuses.append(st)
            else:
                statuses.append(st)

        valid_statuses = [s for s in statuses if s in VALID_STATUSES]
        if not valid_statuses:
            continue

        majority = Counter(valid_statuses).most_common(1)[0][0]

        for spec, st in zip(group_specs, statuses):
            if st == majority:
                consistent_count += 1
            elif st in VALID_STATUSES:
                result.issues.append(
                    f"{spec.name}: status '{st}' differs from "
                    f"{group_name}/ majority '{majority}'"
                )

    ratio = consistent_count / total_specs if total_specs > 0 else 0.0

    if ratio >= 1.0:
        result.score = 25
    elif ratio >= 0.9:
        result.score = 20
    elif ratio >= 0.7:
        result.score = 15
    elif ratio >= 0.5:
        result.score = 10
    else:
        result.score = max(0, int(ratio * 25))

    if invalid_found:
        result.score = max(0, result.score - 5)
        result.suggestions.append(
            "Fix invalid or missing status values "
            "(valid: draft, approved, deprecated)"
        )

    return result


# ── Dimension 2: Reference Coverage (0-25) ─────────────────────────────


def score_reference_coverage(
    specs: list[ParsedHealthSpec],
    flows_dir: Path | None = None,
) -> DimensionResult:
    """Score reference connectivity and flow coverage."""
    result = DimensionResult(name="Reference Coverage", score=0)

    if not specs:
        result.issues.append("No specs found in directory")
        return result

    spec_stems = {s.name for s in specs}
    non_infra = [
        s for s in specs
        if s.name.lower() not in INFRASTRUCTURE_STEMS
    ]

    if not non_infra:
        result.score = 25
        return result

    # Count inbound references per spec
    inbound: Counter[str] = Counter()
    outbound_edges: list[tuple[str, str]] = []

    for spec in specs:
        for link_target in spec.related_specs_links:
            target_stem = Path(link_target).stem
            inbound[target_stem] += 1
            outbound_edges.append((spec.name, target_stem))

    # Orphan detection
    orphans = [
        s for s in non_infra
        if inbound.get(s.name, 0) == 0
    ]
    orphan_ratio = 1.0 - (len(orphans) / len(non_infra))

    if orphans:
        sample = orphans[:5]
        names = ", ".join(s.name for s in sample)
        suffix = (
            f" (+{len(orphans) - 5} more)"
            if len(orphans) > 5 else ""
        )
        result.issues.append(
            f"{len(orphans)} orphan spec(s) with no inbound "
            f"references: {names}{suffix}"
        )

    # Bidirectional reference check (informational only — not scored,
    # because reference graphs are naturally directional)
    edge_set = set(outbound_edges)
    bidi_count = sum(
        1 for src, tgt in outbound_edges if (tgt, src) in edge_set
    )
    total_edges = len(outbound_edges)
    bidi_ratio = (bidi_count / total_edges) if total_edges > 0 else 1.0

    if total_edges > 0 and bidi_ratio < 1.0:
        missing_back = total_edges - bidi_count
        result.suggestions.append(
            f"{missing_back} reference(s) lack a back-link "
            f"(bidirectional ratio: {bidi_ratio:.0%})"
        )

    # Flow mapping (optional)
    flow_ratio = _compute_flow_ratio(spec_stems, flows_dir, result)

    composite = (orphan_ratio + flow_ratio) / 2.0
    result.score = min(25, int(round(composite * 25)))
    return result


def _compute_flow_ratio(
    spec_stems: set[str],
    flows_dir: Path | None,
    result: DimensionResult,
) -> float:
    """Compute flow-to-spec match ratio."""
    if flows_dir is None or not flows_dir.is_dir():
        return 1.0

    flow_stems = {
        f.stem for f in flows_dir.glob("*.md")
        if f.name.lower() != "readme.md"
    }
    unwritten = flow_stems - spec_stems
    adhoc = spec_stems - flow_stems - INFRASTRUCTURE_STEMS

    if unwritten:
        sample = sorted(unwritten)[:5]
        result.suggestions.append(
            f"{len(unwritten)} flow(s) have no matching spec: "
            f"{', '.join(sample)}"
        )
    if adhoc:
        sample = sorted(adhoc)[:5]
        result.suggestions.append(
            f"{len(adhoc)} spec(s) have no matching flow: "
            f"{', '.join(sample)}"
        )

    total_items = len(flow_stems | spec_stems)
    matched = total_items - len(unwritten) - len(adhoc)
    return matched / total_items if total_items > 0 else 1.0

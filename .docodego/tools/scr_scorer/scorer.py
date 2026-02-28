"""SCR dimension scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from scoring_common.types import DimensionResult

from .parser import SDDM
from .registry import (
    classify_severity,
    get_dep_count,
    get_last_modified,
    is_deprecated,
    query_npm,
    query_osv,
)

# ── Constants ──────────────────────────────────────────────────────────

# Offline-mode fixed scores
OFFLINE_VULN_SCORE = 40
OFFLINE_VITALITY_SCORE = 12
OFFLINE_DEPTH_SCORE = 10

# Max scores per dimension
MAX_VULN = 40
MAX_VITALITY = 25
MAX_DEPTH = 20
MAX_COVERAGE = 15

# Severity → point deduction for vulnerability scoring
SEVERITY_DEDUCTION = {
    "CRITICAL": 10,
    "HIGH": 5,
    "MEDIUM": 2,
    "LOW": 1,
    "UNKNOWN": 1,
}

# Known-heavy frameworks exempt from depth penalties
KNOWN_HEAVY = {
    "webpack", "vite", "next", "nuxt", "expo", "tauri",
    "react-native", "electron", "angular", "svelte",
    "storybook", "turbo", "turborepo",
}


# ── Result dataclass ───────────────────────────────────────────────────


@dataclass
class SCRResult:
    """Complete SCR scoring result."""

    vulnerability: DimensionResult
    vitality: DimensionResult
    depth: DimensionResult
    coverage: DimensionResult
    total: int = 0
    status: str = ""
    approved: bool = False
    blocked: bool = False
    block_reason: str = ""

    def __post_init__(self) -> None:
        self.total = (
            self.vulnerability.score
            + self.vitality.score
            + self.depth.score
            + self.coverage.score
        )

    @property
    def dimensions(self) -> list[DimensionResult]:
        return [
            self.vulnerability,
            self.vitality,
            self.depth,
            self.coverage,
        ]


# ── Dimension scorers ─────────────────────────────────────────────────


def score_vulnerability(
    sddm: SDDM, *, offline: bool = True,
) -> DimensionResult:
    """Score Known Vulnerability Exposure (0-40).

    Offline mode: awards full score since no CVEs can be confirmed.
    Live mode: would query OSV API (future implementation).
    """
    result = DimensionResult(
        name="Vulnerability Exposure",
        score=0,
        max_score=MAX_VULN,
    )

    if offline:
        result.score = OFFLINE_VULN_SCORE
        result.suggestions.append(
            "Run without --offline to query OSV API for known CVEs",
        )
        return result

    # Live mode: query OSV for each unique package
    total_deduction = 0
    for name in sddm.unique_packages:
        vulns = query_osv(name)
        for vuln in vulns:
            sev = classify_severity(vuln)
            deduction = SEVERITY_DEDUCTION.get(sev, 1)
            total_deduction += deduction
            vuln_id = vuln.get("id", "unknown")
            result.issues.append(
                f"{name}: {vuln_id} ({sev}, -{deduction}pts)",
            )

    result.score = max(0, MAX_VULN - total_deduction)
    if not result.issues:
        result.suggestions.append(
            "No known CVEs found for referenced packages",
        )
    return result


def score_vitality(
    sddm: SDDM, *, offline: bool = True,
) -> DimensionResult:
    """Score Package Vitality (0-25).

    Offline mode: awards neutral score since maintenance status
    cannot be determined without network.
    Live mode: would query npm registry (future implementation).
    """
    result = DimensionResult(
        name="Package Vitality",
        score=0,
        max_score=MAX_VITALITY,
    )

    if offline:
        result.score = OFFLINE_VITALITY_SCORE
        result.suggestions.append(
            "Run without --offline to query npm registry for "
            "package maintenance status",
        )
        return result

    # Live mode: query npm for each unique package
    now = datetime.now(timezone.utc)
    vital_count = 0.0
    queried = 0

    for name in sddm.unique_packages:
        npm_data = query_npm(name)
        if npm_data is None:
            continue  # private/scoped pkg, skip
        queried += 1

        if is_deprecated(npm_data):
            result.issues.append(f"'{name}' is deprecated on npm")
            continue

        modified = get_last_modified(npm_data)
        if modified is None:
            continue

        months = (now - modified).days / 30.44
        if months < 6:
            vital_count += 1
        elif months < 12:
            vital_count += 0.5
            result.suggestions.append(
                f"'{name}' last published {int(months)} months ago",
            )
        else:
            result.issues.append(
                f"'{name}' last published {int(months)} months ago"
                f" (stale)",
            )

    if queried == 0:
        result.score = OFFLINE_VITALITY_SCORE
        return result

    ratio = vital_count / queried
    if ratio >= 1.0:
        result.score = MAX_VITALITY
    elif ratio >= 0.9:
        result.score = 20
    elif ratio >= 0.7:
        result.score = 15
    elif ratio >= 0.5:
        result.score = 10
    else:
        result.score = max(0, int(ratio * MAX_VITALITY))

    return result


def score_depth(
    sddm: SDDM, *, offline: bool = True,
) -> DimensionResult:
    """Score Supply Chain Depth (0-20).

    Offline mode: awards neutral score since transitive dependency
    counts cannot be determined without network.
    Live mode: would query npm registry (future implementation).
    """
    result = DimensionResult(
        name="Supply Chain Depth",
        score=0,
        max_score=MAX_DEPTH,
    )

    if offline:
        result.score = OFFLINE_DEPTH_SCORE
        result.suggestions.append(
            "Run without --offline to query npm registry for "
            "transitive dependency counts",
        )
        return result

    # Live mode: query npm for direct dep counts
    total_deduction = 0

    for name in sddm.unique_packages:
        npm_data = query_npm(name)
        if npm_data is None:
            continue

        dep_count = get_dep_count(npm_data)
        base_name = name.split("/")[-1] if "/" in name else name
        is_heavy = base_name in KNOWN_HEAVY

        if dep_count > 100:
            if is_heavy:
                result.suggestions.append(
                    f"'{name}' has {dep_count} direct deps"
                    f" (known-heavy, exempt)",
                )
            else:
                total_deduction += 2
                result.issues.append(
                    f"'{name}' has {dep_count} direct deps (-2pts)",
                )
        elif dep_count > 50:
            if not is_heavy:
                total_deduction += 1
                result.suggestions.append(
                    f"'{name}' has {dep_count} direct deps (-1pt)",
                )

    result.score = max(0, MAX_DEPTH - total_deduction)
    return result


def score_coverage(sddm: SDDM) -> DimensionResult:
    """Score SDDM Coverage (0-15).

    Works in both offline and live mode — scores spec documentation
    quality based on version hints, structured locations, and
    consistency.
    """
    result = DimensionResult(
        name="SDDM Coverage",
        score=0,
        max_score=MAX_COVERAGE,
    )

    unique = sddm.unique_packages
    total_packages = len(unique)

    if total_packages == 0:
        result.score = 0
        result.issues.append(
            "No package references found in spec corpus",
        )
        result.suggestions.append(
            "Add package references with version hints in "
            "markdown tables or backtick-quoted text",
        )
        return result

    well_documented = 0

    for name, refs in unique.items():
        has_version = any(r.version_hint for r in refs)
        has_structured = any(r.in_table or r.in_backticks for r in refs)

        # Flag: single-spec mention with no version
        if len(set(r.source_spec for r in refs)) == 1 and not has_version:
            result.issues.append(
                f"'{name}' appears in only 1 spec with no version hint"
                f" ({refs[0].source_spec}:{refs[0].line_number})",
            )

        # Flag: conflicting version hints across specs
        version_hints = {
            r.version_hint for r in refs if r.version_hint
        }
        if len(version_hints) > 1:
            result.issues.append(
                f"'{name}' has conflicting version hints: "
                f"{', '.join(sorted(version_hints))}",
            )

        # A package is well-documented if it has both version + structure
        if has_version and has_structured:
            well_documented += 1
        elif has_version or has_structured:
            # Partial credit: count as half
            well_documented += 0.5

    ratio = well_documented / total_packages

    if ratio >= 1.0:
        result.score = MAX_COVERAGE  # 15
    elif ratio >= 0.9:
        result.score = 12
    elif ratio >= 0.7:
        result.score = 9
    elif ratio >= 0.5:
        result.score = 6
    else:
        result.score = max(0, int(ratio * MAX_COVERAGE))

    if result.score < MAX_COVERAGE:
        undocumented = total_packages - int(well_documented)
        result.suggestions.append(
            f"{undocumented} of {total_packages} packages lack full "
            f"documentation (version hint + structured location)",
        )

    return result


# ── Main scorer ────────────────────────────────────────────────────────


def score_corpus(
    sddm: SDDM,
    *,
    offline: bool = True,
    threshold: int = 60,
    fail_on_zero_dimension: bool = True,
) -> SCRResult:
    """Score a spec corpus against the SCR rubric.

    Returns a full SCRResult with per-dimension scores, status, and
    gate decision.
    """
    vuln = score_vulnerability(sddm, offline=offline)
    vital = score_vitality(sddm, offline=offline)
    dep = score_depth(sddm, offline=offline)
    cov = score_coverage(sddm)

    result = SCRResult(
        vulnerability=vuln,
        vitality=vital,
        depth=dep,
        coverage=cov,
    )

    # Gate logic: zero-veto -> threshold -> status bands
    if fail_on_zero_dimension and any(
        d.score == 0 for d in result.dimensions
    ):
        zero_dims = [
            d.name for d in result.dimensions if d.score == 0
        ]
        result.blocked = True
        result.block_reason = f"Zero score on: {', '.join(zero_dims)}"
        result.status = f"BLOCKED -- {result.block_reason}"
        result.approved = False
    elif result.total < 40:
        result.status = (
            "Not ready for review -- return to author for rework"
        )
        result.approved = False
    elif result.total < threshold:
        result.status = "Under review -- not ready for composition"
        result.approved = False
    elif result.total >= 80:
        result.status = "High-quality supply chain posture"
        result.approved = True
    else:
        result.status = "Approved -- composition may begin"
        result.approved = True

    return result

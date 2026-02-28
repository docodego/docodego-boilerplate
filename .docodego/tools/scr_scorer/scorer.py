"""SCR dimension scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from scoring_common.types import DimensionResult

from .parser import SDDM, scan_unlisted_packages
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
    """Score Known Vulnerability Exposure (0-40)."""
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

    total_deduction = 0
    for name, ref in sddm.unique_packages.items():
        vulns = query_osv(
            name, version=ref.version, ecosystem=ref.ecosystem,
        )
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
    """Score Package Vitality (0-25)."""
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

    now = datetime.now(timezone.utc)
    vital_count = 0.0
    queried = 0

    for name, ref in sddm.unique_packages.items():
        if ref.ecosystem != "npm":
            continue
        npm_data = query_npm(name)
        if npm_data is None:
            continue
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
    """Score Supply Chain Depth (0-20)."""
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

    total_deduction = 0

    for name, ref in sddm.unique_packages.items():
        if ref.ecosystem != "npm":
            continue
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


def score_coverage(
    sddm: SDDM, *, spec_dir: Path | None = None,
) -> DimensionResult:
    """Score Manifest Quality (0-15).

    Scores the completeness of the dependency manifest:
    version specified, ecosystem specified, justification present.
    Also cross-validates that packages in specs are in the manifest.
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
            "No packages found in dependency manifest",
        )
        result.suggestions.append(
            "Create a dependencies.md manifest with Package, "
            "Version, Ecosystem, and Justification columns",
        )
        return result

    # Report parse warnings as issues
    for warning in sddm.warnings:
        result.issues.append(warning)

    complete = 0
    for name, ref in unique.items():
        has_version = bool(ref.version and ref.version != "latest")
        has_ecosystem = bool(ref.ecosystem)
        has_justification = bool(ref.justification)

        if has_version and has_ecosystem and has_justification:
            complete += 1
        elif has_ecosystem and has_justification:
            complete += 0.5
            result.suggestions.append(
                f"'{name}' has no pinned version (using 'latest')",
            )
        else:
            missing = []
            if not has_version:
                missing.append("version")
            if not has_ecosystem:
                missing.append("ecosystem")
            if not has_justification:
                missing.append("justification")
            result.issues.append(
                f"'{name}' missing: {', '.join(missing)}",
            )

    # Cross-validate: packages in specs must be in manifest
    if spec_dir is not None:
        manifest_names = set(unique.keys())
        unlisted = scan_unlisted_packages(spec_dir, manifest_names)
        for pkg, spec_file, line in unlisted:
            result.issues.append(
                f"'{pkg}' in {spec_file}:{line} not in manifest",
            )
            # Penalize: each unlisted package reduces completeness
            complete = max(0, complete - 0.5)

    ratio = complete / total_packages

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

    return result


# ── Main scorer ────────────────────────────────────────────────────────


def score_corpus(
    sddm: SDDM,
    *,
    offline: bool = True,
    threshold: int = 60,
    fail_on_zero_dimension: bool = True,
    spec_dir: Path | None = None,
) -> SCRResult:
    """Score a spec corpus against the SCR rubric."""
    vuln = score_vulnerability(sddm, offline=offline)
    vital = score_vitality(sddm, offline=offline)
    dep = score_depth(sddm, offline=offline)
    cov = score_coverage(sddm, spec_dir=spec_dir)

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

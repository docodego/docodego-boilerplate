"""SHS dimensions: Line Budget and Structural Completeness."""

from __future__ import annotations

import re

from scoring_common.types import DimensionResult

from .anti_gaming import (
    DATE_RE,
    EXPECTED_SECTIONS,
    SECTION_ALIASES,
    SEMVER_RE,
    VALID_STATUSES,
)
from .parser import ParsedHealthSpec


# ── Dimension 3: Line Budget (0-25) ────────────────────────────────────


def score_line_budget(
    specs: list[ParsedHealthSpec],
    line_limit: int = 500,
    data_heavy_limit: int = 650,
) -> DimensionResult:
    """Score specs against line-count limits."""
    result = DimensionResult(name="Line Budget", score=0)

    if not specs:
        result.issues.append("No specs found in directory")
        return result

    compliant = 0
    total = len(specs)

    for spec in specs:
        limit = data_heavy_limit if spec.table_count >= 3 else line_limit
        overshoot = spec.line_count - limit

        if overshoot <= 0:
            compliant += 1
        elif overshoot / limit <= 0.2:
            tag = "data-heavy " if spec.table_count >= 3 else ""
            result.suggestions.append(
                f"{spec.name}: {spec.line_count} lines "
                f"({tag}limit {limit}, {overshoot} over) — "
                f"split into focused sub-specs, never compress content"
            )
        else:
            tag = "data-heavy " if spec.table_count >= 3 else ""
            result.issues.append(
                f"{spec.name}: {spec.line_count} lines "
                f"({tag}limit {limit}, {overshoot} over) — "
                f"split into focused sub-specs by actor or workflow, "
                f"never reduce content to fit"
            )

    for spec in specs:
        if len(spec.related_specs_links) >= 15:
            result.suggestions.append(
                f"{spec.name}: Related Specifications has "
                f"{len(spec.related_specs_links)} entries "
                f"— consider splitting responsibilities"
            )

    ratio = compliant / total if total > 0 else 1.0

    if ratio >= 1.0:
        result.score = 25
    elif ratio >= 0.95:
        result.score = 20
    elif ratio >= 0.85:
        result.score = 15
    elif ratio >= 0.70:
        result.score = 10
    else:
        result.score = max(0, int(ratio * 25))

    return result


# ── Dimension 4: Structural Completeness (0-25) ────────────────────────


def _heading_matches_pattern(
    heading: str, pattern: re.Pattern[str],
) -> bool:
    """Check if a heading matches the pattern or its aliases."""
    if pattern.match(heading):
        return True
    canonical = pattern.pattern.strip("^$").replace("\\s+", " ")
    for alias_key, alias_patterns in SECTION_ALIASES.items():
        if pattern.match(alias_key) or alias_key.lower() == canonical.lower():
            for alias_pat in alias_patterns:
                if alias_pat.match(heading):
                    return True
    return False


def _score_sections(
    specs: list[ParsedHealthSpec],
) -> tuple[float, list[str]]:
    """Score section presence. Returns (ratio, issues)."""
    issues: list[str] = []

    if not specs:
        return 1.0, issues

    total_expected = 0
    total_present = 0

    for spec in specs:
        expected = EXPECTED_SECTIONS.get(
            spec.spec_type, EXPECTED_SECTIONS["unknown"],
        )
        total_expected += len(expected)

        missing: list[str] = []
        for pat in expected:
            found = any(
                _heading_matches_pattern(h, pat)
                for h in spec.section_headings
            )
            if found:
                total_present += 1
            else:
                name = pat.pattern.strip("^$").replace("\\s+", " ")
                missing.append(name)

        if missing:
            issues.append(
                f"{spec.name} ({spec.spec_type}): missing "
                f"{', '.join(missing)}"
            )

    ratio = total_present / total_expected if total_expected > 0 else 1.0
    return ratio, issues


def _score_frontmatter(
    specs: list[ParsedHealthSpec],
) -> tuple[float, list[str]]:
    """Score frontmatter field validity. Returns (ratio, issues)."""
    issues: list[str] = []
    required_fields = ["id", "version", "created", "owner", "status"]

    if not specs:
        return 1.0, issues

    total_checks = len(specs) * len(required_fields)
    valid_count = 0

    for spec in specs:
        fm = spec.frontmatter
        for fld in required_fields:
            val = fm.get(fld, "")
            if not val:
                issues.append(
                    f"{spec.name}: missing '{fld}' in frontmatter",
                )
                continue

            if fld == "version" and not SEMVER_RE.match(val):
                issues.append(
                    f"{spec.name}: version '{val}' is not semver",
                )
                continue
            if fld == "created" and not DATE_RE.match(val):
                issues.append(
                    f"{spec.name}: created '{val}' is not YYYY-MM-DD",
                )
                continue
            if fld == "status" and val.lower() not in VALID_STATUSES:
                issues.append(
                    f"{spec.name}: status '{val}' is not valid",
                )
                continue

            valid_count += 1

    ratio = valid_count / total_checks if total_checks > 0 else 1.0
    return ratio, issues


def _score_link_integrity(
    specs: list[ParsedHealthSpec],
) -> tuple[float, list[str]]:
    """Score link resolution. Returns (ratio, issues)."""
    issues: list[str] = []

    total_links = 0
    resolved_links = 0

    for spec in specs:
        for text, target, line_no in spec.all_md_links:
            if not target.endswith(".md"):
                continue
            if target.startswith(("http://", "https://")):
                continue

            total_links += 1
            resolved = (spec.filepath.parent / target).resolve()
            if resolved.is_file():
                resolved_links += 1
            else:
                issues.append(
                    f"{spec.name}:{line_no}: broken link "
                    f"[{text}]({target})"
                )

    ratio = resolved_links / total_links if total_links > 0 else 1.0
    return ratio, issues


def score_structural_completeness(
    specs: list[ParsedHealthSpec],
) -> DimensionResult:
    """Score structural completeness: sections + frontmatter + links."""
    result = DimensionResult(name="Structural Completeness", score=0)

    sec_ratio, sec_issues = _score_sections(specs)
    fm_ratio, fm_issues = _score_frontmatter(specs)
    link_ratio, link_issues = _score_link_integrity(specs)

    result.issues.extend(sec_issues[:10])
    result.issues.extend(fm_issues[:10])
    result.issues.extend(link_issues[:10])

    if len(sec_issues) > 10:
        result.issues.append(
            f"... and {len(sec_issues) - 10} more section issues"
        )
    if len(fm_issues) > 10:
        result.issues.append(
            f"... and {len(fm_issues) - 10} more frontmatter issues"
        )
    if len(link_issues) > 10:
        result.issues.append(
            f"... and {len(link_issues) - 10} more broken links"
        )

    section_pts = int(round(sec_ratio * 15))
    fm_pts = int(round(fm_ratio * 5))
    link_pts = int(round(link_ratio * 5))
    result.score = min(25, section_pts + fm_pts + link_pts)

    return result

"""ICS dimension scoring engine."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .anti_gaming import (
    check_failure_mode_substance,
    count_boilerplate_criteria,
    is_boilerplate,
)
from .parser import REQUIRED_SECTIONS, ParsedSpec

# ── Vague qualifiers (Unambiguity dimension) ────────────────────────────

VAGUE_QUALIFIERS = [
    re.compile(r"\bfast\b", re.I),
    re.compile(r"\bslow\b", re.I),
    re.compile(r"\bgood\b", re.I),
    re.compile(r"\buser[\-\s]?friendly\b", re.I),
    re.compile(r"\bintuitive\b", re.I),
    re.compile(r"\breasonable\b", re.I),
    re.compile(r"\bappropriate\b", re.I),
    re.compile(r"\bhigh[\-\s]?quality\b", re.I),
    re.compile(r"\brobust\b", re.I),
    re.compile(r"\bscalable\b(?!\s*[\(\:\—\-–]\s*\d)", re.I),  # ok if followed by a number
    re.compile(r"\befficient\b(?!\s*[\(\:\—\-–]\s*\d)", re.I),
    re.compile(r"\bsecure\b(?!\s*[\(\:\—\-–])", re.I),  # ok if qualified
    re.compile(r"\bas\s+needed\b", re.I),
    re.compile(r"\bshould\b", re.I),
    re.compile(r"\bmay\b", re.I),
]

# Measurable language patterns (Testability dimension)
MEASURABLE_PATTERNS = [
    re.compile(r"\d+\s*(%|percent|ms|seconds?|minutes?|hours?|mb|gb|kb)", re.I),
    re.compile(r"(at\s+least|at\s+most|no\s+more\s+than|no\s+fewer\s+than)\s+\d+", re.I),
    re.compile(r"(must|shall)\s+not\s+exceed\s+\d+", re.I),
    re.compile(r"(within|under|over|above|below)\s+\d+", re.I),
    re.compile(r"\b\d+th[\-\s]percentile\b", re.I),
    re.compile(r"(true|false|enabled|disabled|present|absent|empty|non[\-\s]?empty)", re.I),
    re.compile(r"(returns?|responds?\s+with)\s+(2\d{2}|4\d{2}|5\d{2})", re.I),
    re.compile(r"(equals?|=|>=|<=|>|<)\s*\d+", re.I),
]

# Section word count threshold for "non-empty"
MIN_SECTION_WORDS = 50
# Minimum distinct failure modes
MIN_FAILURE_MODES = 3

# ── Failure mode splitting ──────────────────────────────────────────────

# Top-level bullet: no leading whitespace before the marker
_TOP_BULLET = re.compile(r"^(?:[-*•]|\d+[.\)])\s+", re.MULTILINE)


@dataclass
class DimensionResult:
    """Score result for a single ICS dimension."""

    name: str
    score: int  # 0-25
    max_score: int = 25
    issues: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    @property
    def band(self) -> str:
        """Compute band from current score (always up-to-date)."""
        if self.score <= 8:
            return "low"
        if self.score <= 18:
            return "mid"
        return "high"


@dataclass
class ICSResult:
    """Complete ICS scoring result."""

    completeness: DimensionResult
    testability: DimensionResult
    unambiguity: DimensionResult
    threat_coverage: DimensionResult
    total: int = 0
    status: str = ""
    approved: bool = False
    blocked: bool = False
    block_reason: str = ""

    def __post_init__(self):
        self.total = (
            self.completeness.score
            + self.testability.score
            + self.unambiguity.score
            + self.threat_coverage.score
        )

    @property
    def dimensions(self) -> list[DimensionResult]:
        return [self.completeness, self.testability, self.unambiguity, self.threat_coverage]


def _split_failure_modes(content: str) -> list[str]:
    """Split failure mode section into individual entries.

    Groups each top-level bullet with its indented sub-bullets so that
    a structure like:
        - **Title**
            - **What happens:** ...
            - **Recovery:** ...
    is treated as a single failure mode entry.
    """
    starts = [m.start() for m in _TOP_BULLET.finditer(content)]

    if starts:
        entries = []
        for i, start in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else len(content)
            chunk = content[start:end].strip()
            if chunk:
                entries.append(chunk)
        return entries

    # Fallback: split by blank-line-separated paragraphs
    return [p.strip() for p in content.split("\n\n") if p.strip()]


def _extract_criteria_lines(content: str) -> list[str]:
    """Extract individual acceptance criteria from section content."""
    lines = []
    for line in content.split("\n"):
        stripped = line.strip()
        # Match checklist items or bullet points
        if re.match(r"^[-*•]\s*\[.\]\s*", stripped):
            lines.append(re.sub(r"^[-*•]\s*\[.\]\s*", "", stripped))
        elif re.match(r"^[-*•]\s+", stripped):
            lines.append(re.sub(r"^[-*•]\s+", "", stripped))
        elif re.match(r"^\d+[.)]\s+", stripped):
            lines.append(re.sub(r"^\d+[.)]\s+", "", stripped))
    return [l for l in lines if l]


# ── Dimension scorers ───────────────────────────────────────────────────


def score_completeness(spec: ParsedSpec) -> DimensionResult:
    """Score Completeness (0-25): all required sections present and non-empty."""
    result = DimensionResult(name="Completeness", score=0)

    present = spec.present_sections
    missing = spec.missing_sections
    total_required = len(REQUIRED_SECTIONS)

    if missing:
        result.issues.append(f"Missing sections: {', '.join(missing)}")
        for m in missing:
            result.suggestions.append(f"Add a '{m.replace('_', ' ').title()}' section")

    # Base score from section presence
    presence_ratio = len(present) / total_required
    base = int(presence_ratio * 15)  # up to 15 points for presence

    # Depth score from word count
    thin_sections = []
    depth_points = 0
    for name in present:
        sec = spec.sections[name]
        if sec.word_count >= MIN_SECTION_WORDS:
            depth_points += 2.5
        elif sec.word_count > 0:
            depth_points += 1
            thin_sections.append(f"{name} ({sec.word_count} words)")

    if thin_sections:
        result.issues.append(f"Thin sections (< {MIN_SECTION_WORDS} words): {', '.join(thin_sections)}")
        result.suggestions.append(f"Expand thin sections to at least {MIN_SECTION_WORDS} words each")

    # Governance section bonus (not required but recognized)
    if "governance" in spec.sections:
        gov = spec.sections["governance"]
        if gov.word_count >= MIN_SECTION_WORDS:
            depth_points += 1

    result.score = min(25, int(base + depth_points))
    return result


def score_testability(spec: ParsedSpec) -> DimensionResult:
    """Score Testability (0-25): acceptance criteria contain measurable language."""
    result = DimensionResult(name="Testability", score=0)

    ac_section = spec.sections.get("acceptance_criteria")
    if ac_section is None:
        result.issues.append("No Acceptance Criteria section found")
        result.suggestions.append("Add acceptance criteria with specific, measurable pass/fail conditions")
        return result

    criteria = _extract_criteria_lines(ac_section.content)
    if not criteria:
        # Fall back to full content analysis
        criteria = [l.strip() for l in ac_section.content.split("\n") if l.strip()]

    if not criteria:
        result.issues.append("Acceptance Criteria section is empty")
        return result

    total = len(criteria)
    boilerplate_count = count_boilerplate_criteria(criteria)
    if boilerplate_count > 0:
        result.issues.append(f"{boilerplate_count} boilerplate criteria detected (zero credit)")
        result.suggestions.append("Replace generic criteria like 'system must work correctly' with specific thresholds")

    measurable_count = 0
    unmeasurable = []
    for criterion in criteria:
        if is_boilerplate(criterion):
            continue
        if any(pat.search(criterion) for pat in MEASURABLE_PATTERNS):
            measurable_count += 1
        else:
            unmeasurable.append(criterion[:80])

    effective_total = total - boilerplate_count
    if effective_total <= 0:
        result.issues.append("All criteria are boilerplate")
        result.score = 0
        return result

    ratio = measurable_count / effective_total

    if ratio >= 0.9:
        result.score = 25
    elif ratio >= 0.7:
        result.score = 20
    elif ratio >= 0.5:
        result.score = 15
    elif ratio >= 0.3:
        result.score = 10
    else:
        result.score = max(0, int(ratio * 25))

    if unmeasurable:
        preview = unmeasurable[:3]
        result.issues.append(f"{len(unmeasurable)} criteria lack measurable language")
        for u in preview:
            result.suggestions.append(f"Add specific threshold to: \"{u}...\"")

    return result


def score_unambiguity(spec: ParsedSpec) -> DimensionResult:
    """Score Unambiguity (0-25): absence of vague qualifiers."""
    result = DimensionResult(name="Unambiguity", score=25)

    # Scan all sections for vague qualifiers
    all_text = " ".join(
        sec.content for sec in spec.sections.values()
    )

    found_qualifiers: dict[str, int] = {}
    for pat in VAGUE_QUALIFIERS:
        matches = pat.findall(all_text)
        if matches:
            qualifier = matches[0].lower()
            found_qualifiers[qualifier] = found_qualifiers.get(qualifier, 0) + len(matches)

    total_violations = sum(found_qualifiers.values())

    if total_violations == 0:
        result.score = 25
    elif total_violations <= 2:
        result.score = 20
    elif total_violations <= 5:
        result.score = 15
    elif total_violations <= 8:
        result.score = 10
    elif total_violations <= 12:
        result.score = 5
    else:
        result.score = 0

    if found_qualifiers:
        top = sorted(found_qualifiers.items(), key=lambda x: -x[1])[:5]
        for word, count in top:
            result.issues.append(f"Vague qualifier '{word}' appears {count} time(s)")
        result.suggestions.append(
            "Replace vague terms with specific, measurable language "
            "(e.g., 'fast' → 'response time ≤ 200ms')"
        )

    return result


def score_threat_coverage(spec: ParsedSpec) -> DimensionResult:
    """Score Threat Coverage (0-25): ≥3 failure modes with recovery paths."""
    result = DimensionResult(name="Threat Coverage", score=0)

    fm_section = spec.sections.get("failure_modes")
    if fm_section is None:
        result.issues.append("No Failure Modes / Threat Model section found")
        result.suggestions.append(
            "Add a Failure Modes section with at least 3 failure scenarios "
            "and recovery paths"
        )
        return result

    entries = _split_failure_modes(fm_section.content)

    if not entries:
        result.issues.append("Failure Modes section is empty")
        return result

    substantive_count = 0
    total = len(entries)
    for i, entry in enumerate(entries):
        passes, reason = check_failure_mode_substance(entry)
        if passes:
            substantive_count += 1
        else:
            result.issues.append(f"Failure mode #{i + 1}: {reason}")

    # Gate: need at least MIN_FAILURE_MODES substantive entries
    if substantive_count < MIN_FAILURE_MODES:
        if substantive_count == 2:
            result.score = 16
        elif substantive_count == 1:
            result.score = 8
        else:
            result.score = 0
        result.suggestions.append(
            f"Add {MIN_FAILURE_MODES - substantive_count} more failure mode(s) "
            f"with recovery paths (keywords: falls back, retries, alerts, "
            f"degrades, escalates)"
        )
    else:
        # Score by ratio of substantive to total
        ratio = substantive_count / total
        if ratio >= 0.9:
            result.score = 25
        elif ratio >= 0.7:
            result.score = 20
        elif ratio >= 0.5:
            result.score = 15
        elif ratio >= 0.3:
            result.score = 10
        else:
            result.score = max(0, int(ratio * 25))

    return result


# ── Main scorer ─────────────────────────────────────────────────────────


def score_spec(
    spec: ParsedSpec,
    *,
    threshold: int = 60,
    threat_floor: int = 15,
    fail_on_zero_dimension: bool = True,
) -> ICSResult:
    """Score a parsed spec against the ICS rubric.

    Returns a full ICSResult with per-dimension scores, status, and gate decision.
    """
    completeness = score_completeness(spec)
    testability = score_testability(spec)
    unambiguity = score_unambiguity(spec)
    threat_cov = score_threat_coverage(spec)

    result = ICSResult(
        completeness=completeness,
        testability=testability,
        unambiguity=unambiguity,
        threat_coverage=threat_cov,
    )

    # Gate logic
    if threat_cov.score < threat_floor:
        result.blocked = True
        result.block_reason = (
            f"Threat Coverage below floor ({threat_cov.score}/{threat_floor} minimum)"
        )
        result.status = f"BLOCKED — {result.block_reason}"
        result.approved = False
    elif fail_on_zero_dimension and any(d.score == 0 for d in result.dimensions):
        zero_dims = [d.name for d in result.dimensions if d.score == 0]
        result.blocked = True
        result.block_reason = f"Zero score on: {', '.join(zero_dims)}"
        result.status = f"BLOCKED — {result.block_reason}"
        result.approved = False
    elif result.total < 40:
        result.status = "Not ready for review — return to author for rework"
        result.approved = False
    elif result.total < threshold:
        result.status = "Under review — not ready for composition"
        result.approved = False
    elif result.total >= 80:
        result.status = "High-quality specification"
        result.approved = True
    else:
        result.status = "Approved — composition may begin"
        result.approved = True

    return result

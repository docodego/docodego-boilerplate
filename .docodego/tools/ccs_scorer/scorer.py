"""CCS dimension scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from .anti_gaming import (
    L1_PATTERN,
    L2_PATTERN,
    L3_PATTERN,
    TIER_PATTERN,
    count_vague_qualifiers,
    has_if_then_form,
    has_scope_signal,
    has_tool_reference,
    has_violation_signal,
    has_vague_scope,
)
from .parser import REQUIRED_SECTIONS, ParsedConventionSpec, extract_bullets

MIN_RULES_WORDS = 50
MIN_INTENT_WORDS = 30


# ── Result dataclasses ───────────────────────────────────────────────────


@dataclass
class DimensionResult:
    """Score result for a single CCS dimension."""

    name: str
    score: int          # 0-25
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
class CCSResult:
    """Complete CCS scoring result."""

    precision: DimensionResult
    detectability: DimensionResult
    enforcement_coverage: DimensionResult
    scope_clarity: DimensionResult
    total: int = 0
    status: str = ""
    approved: bool = False
    blocked: bool = False
    block_reason: str = ""

    def __post_init__(self) -> None:
        self.total = (
            self.precision.score
            + self.detectability.score
            + self.enforcement_coverage.score
            + self.scope_clarity.score
        )

    @property
    def dimensions(self) -> list[DimensionResult]:
        return [
            self.precision,
            self.detectability,
            self.enforcement_coverage,
            self.scope_clarity,
        ]


# ── Dimension scorers ────────────────────────────────────────────────────


def score_precision(spec: ParsedConventionSpec) -> DimensionResult:
    """Precision (0-25): IF/THEN rules, ≥50 words in Rules, zero vague qualifiers.

    Scoring breakdown:
    - IF/THEN form ratio × 15   (max 15)
    - Rules word count ≥ 50      (5 pts)
    - Vague qualifier penalty    (up to -5, starts at 5)
    """
    result = DimensionResult(name="Precision", score=0)

    rules_sec = spec.sections.get("rules")
    if rules_sec is None:
        result.issues.append("No Rules section found")
        result.suggestions.append(
            "Add a Rules section with IF/THEN rule statements, one rule per bullet"
        )
        return result

    # Word count
    word_pts = 5 if rules_sec.word_count >= MIN_RULES_WORDS else (
        2 if rules_sec.word_count > 0 else 0
    )
    if rules_sec.word_count < MIN_RULES_WORDS:
        result.issues.append(
            f"Rules section too short ({rules_sec.word_count} words, minimum {MIN_RULES_WORDS})"
        )
        result.suggestions.append(
            f"Expand Rules section to at least {MIN_RULES_WORDS} words"
        )

    # IF/THEN form ratio
    bullets = extract_bullets(rules_sec.content)
    if not bullets:
        result.issues.append("Rules section has no bullet-point rules")
        result.suggestions.append(
            "Write each convention rule as a bullet: "
            "IF <condition> THEN <outcome> — count equals N"
        )
        result.score = word_pts
        return result

    if_then_count = sum(1 for b in bullets if has_if_then_form(b))
    if_then_ratio = if_then_count / len(bullets)
    if_then_pts = int(if_then_ratio * 15)

    if if_then_ratio < 1.0:
        missing = len(bullets) - if_then_count
        result.issues.append(
            f"{missing} rule(s) not in IF/THEN form "
            f"({if_then_count}/{len(bullets)} compliant)"
        )
        result.suggestions.append(
            "Rewrite non-compliant rules as: "
            "IF <condition> THEN <outcome> — the count of <X> equals N"
        )

    # Vague qualifier check across all sections
    all_text = " ".join(sec.content for sec in spec.sections.values())
    qualifiers = count_vague_qualifiers(all_text)
    total_violations = sum(qualifiers.values())

    vague_pts = max(0, 5 - min(5, total_violations))

    if qualifiers:
        top = sorted(qualifiers.items(), key=lambda x: -x[1])[:5]
        for word, count in top:
            result.issues.append(f"Vague qualifier '{word}' appears {count} time(s)")
        result.suggestions.append(
            "Replace vague terms with specific, measurable language "
            "(e.g., 'fast' → 'within 200ms', 'should' → concrete IF/THEN rule)"
        )

    result.score = min(25, word_pts + if_then_pts + vague_pts)
    return result


def score_detectability(spec: ParsedConventionSpec) -> DimensionResult:
    """Detectability (0-25): ≥90% of rules name a specific violation signal.

    Compares rule bullet count against signal entries in Violation Signal section.
    """
    result = DimensionResult(name="Detectability", score=0)

    rules_sec = spec.sections.get("rules")
    signal_sec = spec.sections.get("violation_signal")

    if rules_sec is None:
        result.issues.append("No Rules section — cannot assess detectability")
        return result

    if signal_sec is None:
        result.issues.append("No Violation Signal section found")
        result.suggestions.append(
            "Add a Violation Signal section naming the grep pattern, Biome rule ID, "
            "Knip flag, or CI script that detects each rule violation"
        )
        return result

    rule_bullets = extract_bullets(rules_sec.content)
    signal_bullets = extract_bullets(signal_sec.content)
    n_rules = max(len(rule_bullets), 1)

    if not signal_bullets:
        result.issues.append("Violation Signal section has no detection entries")
        result.suggestions.append(
            "Add one detection entry per rule: "
            "grep pattern, Biome rule name, Knip flag, or CI script path"
        )
        return result

    substantive = [b for b in signal_bullets if has_violation_signal(b)]
    n_substantive = len(substantive)
    ratio = min(1.0, n_substantive / n_rules)

    if ratio >= 0.9:
        result.score = 25
    elif ratio >= 0.7:
        result.score = 18
    elif ratio >= 0.5:
        result.score = 12
    elif ratio >= 0.3:
        result.score = 6
    else:
        result.score = max(0, int(ratio * 20))

    weak = [b for b in signal_bullets if not has_violation_signal(b)]
    if weak:
        result.issues.append(
            f"{len(weak)} signal entry/entries lack a specific tool, rule ID, or pattern"
        )
        result.suggestions.append(
            "Name the exact Biome rule, Knip flag, grep regex, or CI script for each violation "
            "(e.g., `noRestrictedImports`, `pnpm knip --include='...'`, `grep -r 'import.*apps/api'`)"
        )

    coverage_gap = n_rules - n_substantive
    if coverage_gap > 0:
        result.issues.append(
            f"{coverage_gap} rule(s) have no corresponding detection signal"
        )

    return result


def score_enforcement_coverage(spec: ParsedConventionSpec) -> DimensionResult:
    """Enforcement Coverage (0-25): tiers present, tools named for L1/L2, remediation for L2/L3.

    Scoring breakdown:
    - Tier coverage (rules vs tier labels): up to 10 pts
    - L1/L2 rules name an exact tool/command:  8 pts
    - Remediation present for L2/L3:           7 pts
    """
    result = DimensionResult(name="Enforcement Coverage", score=0)

    enforcement_sec = spec.sections.get("enforcement")
    remediation_sec = spec.sections.get("remediation")
    rules_sec = spec.sections.get("rules")

    if enforcement_sec is None:
        result.issues.append("No Enforcement section found")
        result.suggestions.append(
            "Add an Enforcement section assigning L1/L2/L3 tiers to each rule: "
            "L1 = auto-enforced by tool, L2 = CI script, L3 = code review only"
        )
        return result

    enforcement_text = enforcement_sec.content
    n_rules = len(extract_bullets(rules_sec.content)) if rules_sec else 1
    tier_matches = TIER_PATTERN.findall(enforcement_text)
    n_tiers = len(tier_matches)

    if n_tiers == 0:
        result.issues.append("No L1/L2/L3 tier labels found in Enforcement section")
        result.suggestions.append(
            "Label each rule with a tier: L1 (biome/tsc auto-enforces), "
            "L2 (CI check), L3 (review gate)"
        )

    # Tier coverage: how many tiers vs how many rules
    tier_ratio = min(1.0, n_tiers / max(n_rules, 1))
    tier_pts = int(tier_ratio * 10)

    # L1/L2 tool check
    has_l1 = bool(L1_PATTERN.search(enforcement_text))
    has_l2 = bool(L2_PATTERN.search(enforcement_text))
    has_automated = has_l1 or has_l2
    names_tool = has_tool_reference(enforcement_text)

    if has_automated and not names_tool:
        result.issues.append(
            "L1/L2 rule(s) present but no specific tool or command named"
        )
        result.suggestions.append(
            "Name the exact tool for L1/L2 rules "
            "(e.g., `biome lint`, `pnpm knip`, `tsc --noEmit`)"
        )
    tool_pts = 8 if (not has_automated or names_tool) else 3

    # Remediation check for L2/L3
    has_l3 = bool(L3_PATTERN.search(enforcement_text))
    needs_remediation = has_l2 or has_l3
    remediation_ok = remediation_sec is not None and remediation_sec.word_count >= 20

    if needs_remediation and not remediation_ok:
        result.issues.append(
            "L2/L3 rules present but Remediation section is missing or too short"
        )
        result.suggestions.append(
            "Add a Remediation section with ordered steps to resolve each L2/L3 violation"
        )
    remediation_pts = 7 if (not needs_remediation or remediation_ok) else 2

    result.score = min(25, tier_pts + tool_pts + remediation_pts)
    return result


def score_scope_clarity(spec: ParsedConventionSpec) -> DimensionResult:
    """Scope Clarity (0-25): ≥80% of rules bounded by glob, folder, or workspace name.

    Checks each rule bullet for a specific scope signal and penalises vague scope terms.
    """
    result = DimensionResult(name="Scope Clarity", score=0)

    rules_sec = spec.sections.get("rules")
    if rules_sec is None:
        result.issues.append("No Rules section — cannot assess scope clarity")
        return result

    bullets = extract_bullets(rules_sec.content)
    if not bullets:
        result.issues.append("Rules section has no bullet-point rules to check for scope")
        return result

    scoped = [b for b in bullets if has_scope_signal(b)]
    vague_only = [b for b in bullets if has_vague_scope(b) and not has_scope_signal(b)]
    ratio = len(scoped) / len(bullets)

    if ratio >= 0.8:
        result.score = 25
    elif ratio >= 0.6:
        result.score = 18
    elif ratio >= 0.4:
        result.score = 12
    elif ratio >= 0.2:
        result.score = 6
    else:
        result.score = max(0, int(ratio * 25))

    unscoped = len(bullets) - len(scoped)
    if unscoped > 0:
        result.issues.append(
            f"{unscoped} rule(s) lack a specific scope "
            "(glob pattern, folder path, or workspace name)"
        )
        result.suggestions.append(
            "Bound each rule to a specific scope: "
            "e.g., 'all files under `apps/web/`', 'files matching `**/*.tsx`', "
            "'workspace `packages/library`'"
        )

    if vague_only:
        result.issues.append(
            f"{len(vague_only)} rule(s) use vague scope terms "
            "('everywhere', 'all components', 'entire codebase') without a path qualifier"
        )
        result.suggestions.append(
            "Replace vague scope with a specific glob or folder path"
        )

    return result


# ── Main scorer ──────────────────────────────────────────────────────────


def score_spec(
    spec: ParsedConventionSpec,
    *,
    threshold: int = 60,
    fail_on_zero_dimension: bool = True,
) -> CCSResult:
    """Score a parsed convention spec against the CCS rubric.

    Returns a full CCSResult with per-dimension scores, status, and gate decision.
    """
    precision = score_precision(spec)
    detectability = score_detectability(spec)
    enforcement = score_enforcement_coverage(spec)
    scope = score_scope_clarity(spec)

    result = CCSResult(
        precision=precision,
        detectability=detectability,
        enforcement_coverage=enforcement,
        scope_clarity=scope,
    )

    if fail_on_zero_dimension and any(d.score == 0 for d in result.dimensions):
        zero_dims = [d.name for d in result.dimensions if d.score == 0]
        result.blocked = True
        result.block_reason = f"Zero score on: {', '.join(zero_dims)}"
        result.status = f"BLOCKED — {result.block_reason}"
        result.approved = False
    elif result.total < 40:
        result.status = "Not ready for review — return to author for rework"
        result.approved = False
    elif result.total < threshold:
        result.status = "Under review — address gaps before construction"
        result.approved = False
    elif result.total >= 80:
        result.status = "High-quality convention specification"
        result.approved = True
    else:
        result.status = "Approved — construction may proceed"
        result.approved = True

    return result

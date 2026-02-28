"""SDS dimensions 3-4: Input Surface Coverage and Defense Depth Signals."""

from __future__ import annotations

from scoring_common.types import DimensionResult

from .anti_gaming import (
    AUDIT_LOGGING_PATTERNS,
    AUDIT_TRIGGERS,
    CROSS_REF_PATTERNS,
    CSRF_PATTERNS,
    CSRF_TRIGGERS,
    ERROR_SANITIZATION_PATTERNS,
    ERROR_TRIGGERS,
    INPUT_VERBS,
    RATE_LIMIT_PATTERNS,
    RATE_LIMIT_TRIGGERS,
    REJECTION_PATTERNS,
    TOKEN_HARDENING_PATTERNS,
    TOKEN_TRIGGERS,
    VALIDATION_PATTERNS,
    has_any_match,
)
from .parser import ParsedSpec


# ── Helpers ─────────────────────────────────────────────────────────────


def _detect_inputs_in_flow(flow_content: str) -> list[str]:
    """Detect user input actions from behavioral flow text."""
    inputs = []
    for line in flow_content.split("\n"):
        for verb_pat in INPUT_VERBS:
            if verb_pat.search(line):
                inputs.append(line.strip())
                break
    return inputs


def _score_signal(
    raw_text: str,
    signal_patterns: list,
    triggers: list,
    max_pts: int,
    name: str,
    result: DimensionResult,
) -> int:
    """Score a single defense depth signal. Returns points earned."""
    applicable = has_any_match(raw_text, triggers)
    if not applicable:
        return max_pts  # non-applicable -> full points

    has_signal = has_any_match(raw_text, signal_patterns)
    has_cross_ref = has_any_match(raw_text, CROSS_REF_PATTERNS)

    if has_signal:
        return max_pts
    if has_cross_ref:
        return max(1, max_pts - 1)

    result.issues.append(f"No {name} signal found (applicable context detected)")
    result.suggestions.append(f"Add {name} measures or cross-reference a spec")
    return 0


# ── Dimension 3: Input Surface Coverage ─────────────────────────────────


def score_input_surface(spec: ParsedSpec) -> DimensionResult:
    """Score Input Surface Coverage (0-25)."""
    result = DimensionResult(name="Input Surface", score=0)

    flow_sec = spec.sections.get("behavioral_flow")
    if flow_sec is None:
        result.score = 25
        result.suggestions.append(
            "No Behavioral Flow section — system-triggered spec, auto 25"
        )
        return result

    inputs = _detect_inputs_in_flow(flow_sec.content)
    if not inputs:
        result.score = 25
        result.suggestions.append(
            "No user input verbs detected in Behavioral Flow — auto 25"
        )
        return result

    validation_text = ""
    for key in ("business_rules", "constraints", "acceptance_criteria"):
        sec = spec.sections.get(key)
        if sec:
            validation_text += " " + sec.content

    n_inputs = len(inputs)
    validated = 0
    half_credit = 0

    for inp in inputs:
        has_validation = has_any_match(validation_text, VALIDATION_PATTERNS)
        has_rejection = has_any_match(validation_text, REJECTION_PATTERNS)

        if has_validation and has_rejection:
            validated += 1
        elif has_validation:
            half_credit += 1

    effective = validated + (half_credit * 0.5)
    ratio = effective / n_inputs if n_inputs > 0 else 1.0

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

    if validated < n_inputs:
        unvalidated = n_inputs - validated - half_credit
        if unvalidated > 0:
            result.issues.append(
                f"{unvalidated} input(s) detected without validation rules"
            )
        if half_credit > 0:
            result.issues.append(
                f"{half_credit} input(s) have validation but no rejection behavior"
            )
        result.suggestions.append(
            "Add validation rules with rejection behavior (HTTP status, "
            "error message) for each user input"
        )

    return result


# ── Dimension 4: Defense Depth Signals ──────────────────────────────────


def score_defense_depth(spec: ParsedSpec) -> DimensionResult:
    """Score Defense Depth Signals (0-25)."""
    result = DimensionResult(name="Defense Depth", score=0)

    raw = spec.raw_text
    points = 0

    points += _score_signal(
        raw, RATE_LIMIT_PATTERNS, RATE_LIMIT_TRIGGERS, 6,
        "rate limiting", result,
    )
    points += _score_signal(
        raw, CSRF_PATTERNS, CSRF_TRIGGERS, 5,
        "CSRF protection", result,
    )
    points += _score_signal(
        raw, TOKEN_HARDENING_PATTERNS, TOKEN_TRIGGERS, 5,
        "token hardening", result,
    )
    points += _score_signal(
        raw, ERROR_SANITIZATION_PATTERNS, ERROR_TRIGGERS, 5,
        "error sanitization", result,
    )
    points += _score_signal(
        raw, AUDIT_LOGGING_PATTERNS, AUDIT_TRIGGERS, 4,
        "audit logging", result,
    )

    result.score = min(25, points)
    return result

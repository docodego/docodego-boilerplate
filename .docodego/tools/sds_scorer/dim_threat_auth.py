"""SDS dimensions 1-2: Threat Taxonomy Coverage and Auth Boundary Rigor."""

from __future__ import annotations

import re

from scoring_common.types import DimensionResult

from .anti_gaming import (
    APPLICABILITY_TRIGGERS,
    CROSS_REF_PATTERNS,
    STRIDE_PATTERNS,
    count_named_attack_vectors,
    has_any_match,
)
from .parser import ParsedSpec

# Permission table row patterns
_TABLE_ROW = re.compile(r"^\|(.+)\|$", re.MULTILINE)
_UNAUTH_KEYWORDS = re.compile(
    r"\b(unauth\w*|visitor|anonymous|no\s+session|public|guest)\b", re.I,
)
_SINGLE_ROLE = re.compile(
    r"\bsingle\s+role\b|\bno\s+permission\s+model\b|\bno\s+role\s+differenti",
    re.I,
)
_NO_ENDPOINT = re.compile(
    r"\b(infrastructure|config(uration)?|internal|build|ci[\-/]cd|tooling)\b",
    re.I,
)
_401_RE = re.compile(r"\b401\b")
_403_RE = re.compile(r"\b403\b")


# ── Helpers ─────────────────────────────────────────────────────────────


def _applicable_categories(raw_text: str) -> set[str]:
    """Determine which STRIDE categories are applicable to this spec."""
    applicable = set()
    for cat, triggers in APPLICABILITY_TRIGGERS.items():
        if has_any_match(raw_text, triggers):
            applicable.add(cat)
    return applicable


def _extract_table_rows(content: str) -> list[list[str]]:
    """Extract table rows as lists of cell values."""
    rows = []
    for m in _TABLE_ROW.finditer(content):
        cells = [c.strip() for c in m.group(1).split("|")]
        rows.append(cells)
    return rows


# ── Dimension 1: Threat Taxonomy Coverage ───────────────────────────────


def score_threat_taxonomy(spec: ParsedSpec) -> DimensionResult:
    """Score Threat Taxonomy Coverage (0-25)."""
    result = DimensionResult(name="Threat Taxonomy", score=0)

    all_text = spec.raw_text
    applicable = _applicable_categories(all_text)
    if not applicable:
        result.score = 25
        result.suggestions.append(
            "No STRIDE categories applicable — full score by default"
        )
        return result

    scan_text = ""
    for key in ("failure_modes", "constraints", "business_rules"):
        sec = spec.sections.get(key)
        if sec:
            scan_text += " " + sec.content

    if not scan_text.strip():
        result.issues.append(
            "No Failure Modes, Constraints, or Business Rules content to scan"
        )
        return result

    covered = set()
    for cat in applicable:
        patterns = STRIDE_PATTERNS.get(cat, [])
        if has_any_match(scan_text, patterns):
            covered.add(cat)

    n_covered = len(covered)
    uncovered = applicable - covered

    if uncovered:
        result.issues.append(
            f"Uncovered STRIDE categories: {', '.join(sorted(uncovered))}"
        )
        result.suggestions.append(
            "Add failure modes or constraints addressing: "
            + ", ".join(sorted(uncovered))
        )

    bonus = min(3, count_named_attack_vectors(scan_text))

    if n_covered >= 4:
        result.score = 25
    elif n_covered == 3:
        result.score = min(25, 20 + bonus)
    elif n_covered == 2:
        result.score = min(25, 15 + bonus)
    elif n_covered == 1:
        result.score = min(25, 8 + bonus)
    else:
        result.score = min(25, bonus)

    if bonus > 0:
        result.suggestions.append(
            f"Named attack vector bonus: +{bonus} (specific threats referenced)"
        )

    return result


# ── Dimension 2: Auth Boundary Rigor ────────────────────────────────────


def score_auth_boundary(spec: ParsedSpec) -> DimensionResult:
    """Score Auth Boundary Rigor (0-25)."""
    result = DimensionResult(name="Auth Boundary", score=0)

    pm_section = spec.sections.get("permission_model")
    all_text = spec.raw_text

    # Single-role exemption
    if pm_section and _SINGLE_ROLE.search(pm_section.content):
        result.score = 20
        result.suggestions.append("Single-role spec — auto-scored 20/25")
        return result

    # No-endpoint exemption
    intent_sec = spec.sections.get("intent")
    intent_text = intent_sec.content if intent_sec else ""
    context = intent_text + " " + spec.title
    if _NO_ENDPOINT.search(context) and pm_section is None:
        result.score = 22
        result.suggestions.append(
            "Infrastructure/config spec without endpoints — auto-scored 22/25"
        )
        return result

    if pm_section is None:
        result.issues.append("No Permission Model section found")
        result.suggestions.append(
            "Add a Permission Model table with roles and access boundaries"
        )
        return result

    pm_content = pm_section.content
    points = 0

    # Unauthenticated row (8 pts)
    if _UNAUTH_KEYWORDS.search(pm_content):
        points += 8
    else:
        result.issues.append(
            "Permission Model missing unauthenticated/visitor/public row"
        )
        result.suggestions.append(
            "Add a row for unauthenticated users (visitor/anonymous/public)"
        )

    # 401 in unauthenticated context (5 pts)
    if _401_RE.search(all_text):
        points += 5
    else:
        result.issues.append("No HTTP 401 status code found in spec")
        result.suggestions.append(
            "Add 401 response for unauthenticated access attempts"
        )

    # 403 in unauthorized context (5 pts)
    if _403_RE.search(all_text):
        points += 5
    else:
        result.issues.append("No HTTP 403 status code found in spec")
        result.suggestions.append(
            "Add 403 response for unauthorized access attempts"
        )

    # All relevant roles enumerated (7 pts)
    rows = _extract_table_rows(pm_content)
    data_rows = [
        r for r in rows
        if len(r) >= 2 and not all(c.startswith("-") for c in r)
        and not any("---" in c for c in r)
    ]
    if len(data_rows) >= 2:
        points += 7
    elif len(data_rows) == 1:
        points += 4
        result.issues.append("Permission Model has only 1 role row")
        result.suggestions.append("Enumerate all relevant roles in the table")
    else:
        result.issues.append("No structured role rows in Permission Model")
        result.suggestions.append(
            "Use a markdown table with columns: Role, Actions Permitted, etc."
        )

    result.score = min(25, points)
    return result

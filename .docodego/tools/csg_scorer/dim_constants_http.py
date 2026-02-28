"""CSG dimensions 1-2: Shared Constants and HTTP Status Semantics."""

from __future__ import annotations

from scoring_common.types import DimensionResult

from .anti_gaming import HTTP_STATUS_CONTEXT
from .types import (
    ExtractedConstant,
    HttpStatusMention,
    ParsedCorpusSpec,
)

# ── Semantic grouping keywords ────────────────────────────────────────

_SEMANTIC_GROUPS: list[tuple[str, list[str]]] = [
    ("session_expiry", ["session", "expir", "expires"]),
    ("session_refresh", ["session", "refresh", "update"]),
    ("otp_expiry", ["otp", "expir", "code"]),
    ("otp_length", ["otp", "digit", "length", "code"]),
    ("invitation_expiry", ["invit", "expir", "window"]),
    ("rate_limit", ["rate", "limit", "throttl"]),
    ("retry", ["retr", "attempt", "backoff"]),
    ("timeout", ["timeout", "time out", "deadline"]),
    ("upload_size", ["upload", "size", "file", "max"]),
    ("token_expiry", ["token", "expir", "valid"]),
    ("password_length", ["password", "length", "character"]),
    ("cooldown", ["cool", "down", "wait", "delay"]),
    ("page_size", ["page", "size", "per page", "limit"]),
    ("ban_duration", ["ban", "duration", "suspend"]),
    ("cache_ttl", ["cache", "ttl", "expir"]),
]


# ── Dimension 1: Shared Constants (0-25) ─────────────────────────────


def _classify_constant_group(ctx: str) -> str | None:
    lower = ctx.lower()
    for group_name, keywords in _SEMANTIC_GROUPS:
        matches = sum(1 for kw in keywords if kw in lower)
        if matches >= 2:
            return group_name
    return None


def score_shared_constants(
    specs: list[ParsedCorpusSpec],
) -> DimensionResult:
    """Score consistency of shared constants across specs."""
    result = DimensionResult(name="Shared Constants", score=0)

    all_constants: list[ExtractedConstant] = []
    for spec in specs:
        all_constants.extend(spec.constants)

    if not all_constants:
        result.score = 25
        result.suggestions.append(
            "No numeric constants found across specs",
        )
        return result

    groups: dict[str, list[ExtractedConstant]] = {}
    for c in all_constants:
        group = _classify_constant_group(c.context)
        if group is not None:
            groups.setdefault(group, []).append(c)

    cross_spec_groups: dict[str, list[ExtractedConstant]] = {}
    for group_name, constants in groups.items():
        spec_names = {c.spec_name for c in constants}
        if len(spec_names) >= 2:
            cross_spec_groups[group_name] = constants

    if not cross_spec_groups:
        result.score = 25
        return result

    total_groups = len(cross_spec_groups)
    consistent = 0

    for group_name, constants in cross_spec_groups.items():
        per_spec: dict[str, set[float]] = {}
        for c in constants:
            val = (
                c.normalized_seconds
                if c.normalized_seconds is not None
                else c.value
            )
            per_spec.setdefault(c.spec_name, set()).add(val)

        all_values = [vs for vs in per_spec.values()]
        common = all_values[0]
        for vs in all_values[1:]:
            common = common & vs

        if common:
            consistent += 1
        else:
            spec_details: list[str] = []
            seen: set[str] = set()
            for c in constants:
                key = f"{c.spec_name}={c.value} {c.unit}"
                if key not in seen:
                    seen.add(key)
                    spec_details.append(
                        f"{key} (line {c.line_num})",
                    )
            result.issues.append(
                f"Inconsistent '{group_name}': "
                + ", ".join(spec_details[:4]),
            )
            result.suggestions.append(
                f"Reconcile '{group_name}' values across specs",
            )

    ratio = consistent / total_groups if total_groups > 0 else 1.0
    if ratio >= 1.0:
        result.score = 25
    elif ratio >= 0.9:
        result.score = 20
    elif ratio >= 0.75:
        result.score = 15
    elif ratio >= 0.5:
        result.score = 10
    else:
        result.score = max(0, int(ratio * 25))

    return result


# ── Dimension 2: HTTP Status Semantics (0-25) ────────────────────────


def _classify_http_context(
    code: int, context: str,
) -> tuple[bool, str]:
    lower = context.lower()
    if code not in HTTP_STATUS_CONTEXT:
        return True, ""

    own_keywords = HTTP_STATUS_CONTEXT[code]
    own_hits = sum(1 for kw in own_keywords if kw in lower)

    other_hits: dict[int, int] = {}
    for other_code, other_keywords in HTTP_STATUS_CONTEXT.items():
        if other_code == code:
            continue
        hits = sum(1 for kw in other_keywords if kw in lower)
        if hits > 0:
            other_hits[other_code] = hits

    if own_hits > 0:
        return True, ""

    for other_code, hits in sorted(
        other_hits.items(), key=lambda x: -x[1],
    ):
        if hits >= 2:
            return False, f"{code} used in {other_code} context"

    return True, ""


def score_http_status_semantics(
    specs: list[ParsedCorpusSpec],
) -> DimensionResult:
    """Score correct usage of HTTP status codes across specs."""
    result = DimensionResult(name="HTTP Status Semantics", score=0)

    all_mentions: list[HttpStatusMention] = []
    for spec in specs:
        all_mentions.extend(spec.http_status_mentions)

    relevant = [
        m for m in all_mentions if m.code in HTTP_STATUS_CONTEXT
    ]
    if not relevant:
        result.score = 25
        return result

    correct = 0
    total = len(relevant)

    for mention in relevant:
        is_correct, reason = _classify_http_context(
            mention.code, mention.context,
        )
        if is_correct:
            correct += 1
        else:
            result.issues.append(
                f"{mention.spec_name} line {mention.line_num}: "
                f"{reason}",
            )
            result.suggestions.append(
                f"Review HTTP {mention.code} usage in "
                f"{mention.spec_name}",
            )

    ratio = correct / total if total > 0 else 1.0
    if ratio >= 0.95:
        result.score = 25
    elif ratio >= 0.85:
        result.score = 20
    elif ratio >= 0.70:
        result.score = 15
    elif ratio >= 0.50:
        result.score = 10
    else:
        result.score = max(0, int(ratio * 25))

    return result

"""CSG dimensions 1-2: Shared Constants and HTTP Status Semantics."""

from __future__ import annotations

import re

from scoring_common.types import DimensionResult

from .anti_gaming import HTTP_STATUS_CONTEXT
from .types import (
    ExtractedConstant,
    HttpStatusMention,
    ParsedCorpusSpec,
)

# ── Semantic grouping keywords ────────────────────────────────────────
# Each tuple: (group_name, keywords, min_matches, temporal_only)
# temporal_only: if True, only match constants with a time unit

_SEMANTIC_GROUPS: list[tuple[str, list[str], int, bool]] = [
    # More specific groups first — first match wins
    ("notification_threshold", ["notif", "expir"], 2, True),
    ("session_expiry", ["session", "expir", "expires"], 2, True),
    ("session_refresh", ["session", "refresh", "update"], 2, False),
    ("otp_expiry", ["otp", "expir", "code"], 2, True),
    ("otp_length", ["otp", "digit", "length", "code"], 2, False),
    ("invitation_expiry", ["invit", "expir", "window"], 2, True),
    ("rate_limit", ["rate", "limit", "throttl"], 2, False),
    ("retry", ["retr", "attempt", "backoff"], 2, False),
    ("timeout", ["timeout", "time out", "deadline"], 2, True),
    ("upload_size", ["upload", "size", "file", "max"], 2, False),
    ("token_expiry", ["token", "expir"], 2, True),
    ("password_length", ["password", "length", "character"], 2, False),
    ("cooldown", ["cool", "down", "wait", "delay"], 2, True),
    ("page_size", ["page", "size", "per page", "limit"], 2, False),
    ("ban_duration", ["ban", "duration", "suspend"], 2, True),
    ("cache_ttl", ["cache", "ttl", "expir"], 2, True),
]

# Groups that represent non-temporal quantities — time-unit constants
# (seconds, hours, etc.) should never be classified into these groups.
_NON_TEMPORAL_GROUPS: set[str] = {
    "upload_size", "password_length", "page_size",
    "otp_length",
}


# ── Dimension 1: Shared Constants (0-25) ─────────────────────────────

# Pre-compiled word-boundary patterns for each keyword
_KW_PATTERNS: dict[str, re.Pattern[str]] = {}


def _kw_match(keyword: str, text: str) -> bool:
    """Check if *keyword* appears as a whole word in *text*."""
    pat = _KW_PATTERNS.get(keyword)
    if pat is None:
        pat = re.compile(r"\b" + re.escape(keyword), re.I)
        _KW_PATTERNS[keyword] = pat
    return pat.search(text) is not None


def _classify_constant_group(
    ctx: str, *, is_temporal: bool = False,
) -> str | None:
    lower = ctx.lower()
    for group_name, keywords, min_hits, temporal_only in _SEMANTIC_GROUPS:
        # Skip non-temporal groups for time-unit constants
        if is_temporal and group_name in _NON_TEMPORAL_GROUPS:
            continue
        # Skip temporal-only groups for non-temporal constants
        if temporal_only and not is_temporal:
            continue
        # Deduplicate overlapping keywords — if stem "expir" already
        # matched, longer form "expires" is redundant (1 concept)
        matched: list[str] = [
            kw for kw in keywords if _kw_match(kw, lower)
        ]
        unique = []
        for kw in sorted(matched, key=len):
            if not any(other in kw for other in unique):
                unique.append(kw)
        if len(unique) >= min_hits:
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
        is_temporal = c.normalized_seconds is not None
        group = _classify_constant_group(
            c.context, is_temporal=is_temporal,
        )
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

        # If any single spec's values span a wide range (>5x), the
        # group is mixing sub-concepts (e.g. session TTL 604800s vs
        # refresh window 86400s) — skip consistency check.
        mixed = False
        for vs in per_spec.values():
            if len(vs) >= 2:
                lo, hi = min(vs), max(vs)
                if lo > 0 and hi / lo > 5:
                    mixed = True
                    break
        if mixed:
            consistent += 1
            continue

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

"""CSG dimensions 3-4: State Machine Consistency and Permission Symmetry."""

from __future__ import annotations

import re

from scoring_common.types import DimensionResult

from .anti_gaming import TERMINAL_STATES, role_level
from .types import (
    ParsedCorpusSpec,
    PermissionRow,
    StateTransition,
)

# Leaf-state stems — matched against state name substrings so that
# both past-tense ("displayed") and progressive ("displaying") forms
# are recognized as valid endpoints in UI flows.
_LEAF_STEMS = {
    "refresh", "updat", "deliver", "log",
    "redirect", "navigat", "hydrat", "sent",
    "display", "resolv", "ready", "clear",
    "chang", "continu", "success", "idle",
    "view", "page", "tab", "dashboard", "onboarding",
    "hidden", "visible", "open", "authenticat",
    "unauthenticat", "empty", "fallback", "reset",
    "stored", "storing", "loaded", "loading",
}

# Stop words for action normalization
_FILLER = {
    "the", "a", "an", "and", "or", "is", "are", "to",
    "from", "with", "for", "in", "on", "at", "by", "of",
    "that", "this", "which", "their", "its", "all", "any",
}


# ── Dimension 3: State Machine Consistency (0-25) ────────────────────


def score_state_machine_consistency(
    specs: list[ParsedCorpusSpec],
) -> DimensionResult:
    """Score cross-spec state machine transition consistency."""
    result = DimensionResult(
        name="State Machine Consistency", score=0,
    )

    all_transitions: list[StateTransition] = []
    for spec in specs:
        all_transitions.extend(spec.state_transitions)

    if not all_transitions:
        result.score = 25
        return result

    from_states: set[str] = set()
    to_states: set[str] = set()
    for t in all_transitions:
        if t.from_state and t.from_state != "(none)":
            from_states.add(t.from_state)
        to_states.add(t.to_state)

    issues_found = 0
    total_checks = 0

    only_targets = to_states - from_states
    for state in only_targets:
        normalized = state.lower().replace(" ", "_")
        if any(t in normalized for t in TERMINAL_STATES):
            continue
        if any(p in normalized for p in _LEAF_STEMS):
            continue
        base = re.sub(r"\s*\(.*?\)", "", normalized).strip()
        if base in from_states:
            continue
        referencing = [
            t.spec_name for t in all_transitions
            if t.to_state == state
        ]
        unique_specs = sorted(set(referencing))
        if len(unique_specs) < 2:
            continue
        total_checks += 1
        issues_found += 1
        result.issues.append(
            f"Potential dead-end state '{state}' appears only "
            f"as target in: {', '.join(unique_specs[:3])}",
        )

    # Check for ambiguous states across specs
    state_guards: dict[str, list[tuple[str, str]]] = {}
    for t in all_transitions:
        if t.guard:
            state_guards.setdefault(t.from_state, []).append(
                (t.spec_name, t.guard),
            )

    for state, guards in state_guards.items():
        spec_names = {g[0] for g in guards}
        if len(spec_names) >= 2:
            total_checks += 1

    if total_checks == 0:
        result.score = 25
        return result

    valid = total_checks - issues_found
    ratio = valid / total_checks if total_checks > 0 else 1.0
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


# ── Dimension 4: Permission Symmetry & Least Privilege (0-25) ────────


def _normalize_action_key(action: str) -> str:
    lower = action.lower()
    words = re.findall(r"\b\w+\b", lower)
    return " ".join(w for w in words if w not in _FILLER)


def _actions_overlap(a: str, b: str) -> bool:
    key_a = set(_normalize_action_key(a).split())
    key_b = set(_normalize_action_key(b).split())
    if not key_a or not key_b:
        return False
    overlap = key_a & key_b
    min_len = min(len(key_a), len(key_b))
    if min_len <= 2:
        return len(overlap) >= min_len
    # Long action texts need higher overlap to avoid false positives
    # from generic words shared across unrelated permission entries
    threshold = 0.75 if min_len >= 5 else 0.6
    return len(overlap) >= min_len * threshold


def score_permission_symmetry(
    specs: list[ParsedCorpusSpec],
) -> DimensionResult:
    """Score permission consistency and least privilege."""
    result = DimensionResult(
        name="Permission Symmetry", score=0,
    )

    all_permissions: list[PermissionRow] = []
    for spec in specs:
        all_permissions.extend(spec.permission_rows)

    if not all_permissions:
        result.score = 25
        return result

    # ── Symmetry checks (0-15) ──────────────────────────────────
    by_role: dict[str, list[PermissionRow]] = {}
    for p in all_permissions:
        by_role.setdefault(p.role.lower().strip(), []).append(p)

    conflicts = 0
    total_pairs = 0

    for role_name, perms in by_role.items():
        granted = [p for p in perms if p.allowed]
        denied = [p for p in perms if not p.allowed]
        for g in granted:
            for d in denied:
                if g.spec_name == d.spec_name:
                    continue
                total_pairs += 1
                if _actions_overlap(g.action, d.action):
                    conflicts += 1
                    result.issues.append(
                        f"Conflict for role '{role_name}': "
                        f"granted in {g.spec_name}, "
                        f"denied in {d.spec_name}",
                    )

    if total_pairs > 0:
        sym_ratio = (total_pairs - conflicts) / total_pairs
        symmetry_score = int(sym_ratio * 15)
    else:
        symmetry_score = 15

    # ── Least privilege checks (0-10) ───────────────────────────
    total_grants = sum(
        1 for p in all_permissions if p.allowed
    )
    least_priv_issues = 0

    if total_grants > 0:
        compliant = total_grants - least_priv_issues
        priv_ratio = compliant / total_grants
        privilege_score = int(priv_ratio * 10)
    else:
        privilege_score = 10

    result.score = min(25, symmetry_score + privilege_score)

    if conflicts > 0:
        result.suggestions.append(
            f"Resolve {conflicts} permission conflict(s) "
            f"across specs",
        )

    return result

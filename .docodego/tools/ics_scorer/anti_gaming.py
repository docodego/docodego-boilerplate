"""Anti-gaming checks for ICS scoring."""

from __future__ import annotations

import re

# Generic boilerplate phrases that indicate zero-effort acceptance criteria.
BOILERPLATE_PHRASES = [
    re.compile(r"system\s+must\s+work\s+correctly", re.I),
    re.compile(r"no\s+errors?\s+should\s+occur", re.I),
    re.compile(r"system\s+should\s+function\s+(as\s+expected|properly|correctly)", re.I),
    re.compile(r"all\s+features?\s+(must|should)\s+work", re.I),
    re.compile(r"system\s+(must|should)\s+be\s+(reliable|stable|robust)$", re.I),
    re.compile(r"everything\s+(must|should)\s+work", re.I),
    re.compile(r"(must|should)\s+meet\s+all\s+requirements", re.I),
    re.compile(r"system\s+(must|should)\s+be\s+secure$", re.I),
    re.compile(r"system\s+(must|should)\s+perform\s+well$", re.I),
]

# Recovery path signal keywords (at least one must appear in a failure mode entry).
RECOVERY_KEYWORDS = [
    "falls back",
    "fallback",
    "retries",
    "retry",
    "alerts",
    "degrades",
    "graceful",
    "escalates",
    "escalation",
    "manual intervention",
    "circuit breaker",
    "timeout",
    "rolls back",
    "rollback",
    "switches to",
    "failover",
    "queues",
    "rejects",
    "returns error",
    "logs",
    "notifies",
]

MIN_FAILURE_MODE_WORDS = 15


def is_boilerplate(text: str) -> bool:
    """Return True if the text matches a known boilerplate pattern."""
    stripped = text.strip().rstrip(".")
    return any(pat.search(stripped) for pat in BOILERPLATE_PHRASES)


def has_recovery_signal(text: str) -> bool:
    """Return True if the text contains at least one recovery path keyword."""
    lower = text.lower()
    return any(kw in lower for kw in RECOVERY_KEYWORDS)


def check_failure_mode_substance(text: str) -> tuple[bool, str]:
    """Check if a failure mode entry has enough substance.

    Returns (passes, reason).
    """
    words = text.split()
    if len(words) < MIN_FAILURE_MODE_WORDS:
        return False, f"Too short ({len(words)} words, minimum {MIN_FAILURE_MODE_WORDS})"
    if not has_recovery_signal(text):
        return False, "No recovery path signal found"
    return True, ""


def count_boilerplate_criteria(criteria_lines: list[str]) -> int:
    """Count how many acceptance criteria lines are boilerplate."""
    return sum(1 for line in criteria_lines if is_boilerplate(line))

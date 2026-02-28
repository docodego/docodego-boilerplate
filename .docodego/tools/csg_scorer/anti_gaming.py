"""Anti-gaming constants and normalization helpers for CSG scoring."""

from __future__ import annotations

# ── Time unit normalization ────────────────────────────────────────────

TIME_UNITS: dict[str, int] = {
    "second": 1,
    "seconds": 1,
    "sec": 1,
    "secs": 1,
    "s": 1,
    "minute": 60,
    "minutes": 60,
    "min": 60,
    "mins": 60,
    "m": 60,
    "hour": 3600,
    "hours": 3600,
    "hr": 3600,
    "hrs": 3600,
    "h": 3600,
    "day": 86400,
    "days": 86400,
    "d": 86400,
    "week": 604800,
    "weeks": 604800,
}

# ── HTTP status context keywords ──────────────────────────────────────
# Each status code maps to keywords that indicate correct usage.

HTTP_STATUS_CONTEXT: dict[int, list[str]] = {
    401: [
        "unauthenticated",
        "not authenticated",
        "no session",
        "missing token",
        "not logged in",
        "invalid session",
        "expired session",
        "session expired",
        "no valid session",
        "authentication required",
        "auth required",
        "sign in",
        "log in",
        "login required",
        "requires authentication",
        "without a valid session",
        "session cookie",
        "invalid token",
        "tampered",
        "token signature",
    ],
    403: [
        "unauthorized",
        "wrong role",
        "permission denied",
        "forbidden",
        "insufficient privileges",
        "not authorized",
        "role check",
        "access denied",
        "not permitted",
        "no permission",
        "lacks permission",
        "admin only",
        "owner only",
        "role validation",
        "insufficient role",
        "role gate",
        "unauthorized attempt",
    ],
    409: [
        "conflict",
        "duplicate",
        "already exists",
        "concurrent modification",
        "unique constraint",
        "collision",
        "already taken",
        "name taken",
        "slug taken",
        "already active",
        "already pending",
        "race condition",
    ],
}

# ── Terminal state names ──────────────────────────────────────────────

TERMINAL_STATES: set[str] = {
    "deleted",
    "completed",
    "error",
    "expired",
    "cancelled",
    "canceled",
    "archived",
    "revoked",
    "banned",
    "failed",
    "terminated",
    "closed",
    "done",
    "removed",
    "destroyed",
}

# ── Role hierarchy patterns ──────────────────────────────────────────
# Lower index = lower privilege.  Used for least-privilege checks.

ROLE_HIERARCHY: list[str] = [
    "visitor",
    "guest",
    "anonymous",
    "unauthenticated",
    "member",
    "user",
    "authenticated",
    "admin",
    "administrator",
    "owner",
    "super admin",
    "superadmin",
    "app admin",
]


def role_level(role: str) -> int:
    """Return privilege level (0 = lowest) for a role name.

    Unknown roles are placed in the middle of the hierarchy.
    """
    lower = role.lower().strip()
    for i, name in enumerate(ROLE_HIERARCHY):
        if lower == name or lower.startswith(name):
            return i
    return len(ROLE_HIERARCHY) // 2

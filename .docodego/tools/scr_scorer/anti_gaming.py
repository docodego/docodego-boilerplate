"""Anti-gaming patterns for SCR scoring — package detection heuristics."""

from __future__ import annotations

import re

# ── npm package name patterns ──────────────────────────────────────────

# Scoped packages: @scope/name (e.g., @repo/ui, @tanstack/react-query)
# Must end with an alphanumeric character (no trailing dots/hyphens).
SCOPED_PKG_RE = re.compile(
    r"@[a-z][a-z0-9._-]*/[a-z][a-z0-9._-]*[a-z0-9]",
)

# Unscoped packages: lowercase-with-hyphens only (npm convention).
# Underscores are excluded — they indicate code identifiers, not packages.
# Must start with a letter and contain at least one hyphen.
UNSCOPED_PKG_RE = re.compile(
    r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+)+\b",
)

# ── Version hint patterns ──────────────────────────────────────────────

# Matches: v4, v2.1, ^2.0, >=1.5, ~3.1, 4.x, 4.0.0
VERSION_HINT_RE = re.compile(
    r"(?:v\d+(?:\.\d+)*"
    r"|[\^~>=<]{1,2}\s*\d+(?:\.\d+)*"
    r"|\d+\.\d+(?:\.\d+)*"
    r"|\d+\.x(?:\.x)?)",
)

# ── Known heavy frameworks (exempt from depth penalties) ───────────────

KNOWN_HEAVY_FRAMEWORKS: set[str] = {
    "next",
    "nuxt",
    "angular",
    "expo",
    "react-native",
    "electron",
    "tauri",
    "astro",
    "remix",
    "gatsby",
    "svelte",
    "sveltekit",
    "webpack",
    "vite",
    "esbuild",
    "turbopack",
    "storybook",
    "playwright",
    "jest",
    "vitest",
}

# ── Known package names that commonly appear in specs ──────────────────

KNOWN_PACKAGES: set[str] = {
    "better-auth",
    "hono",
    "drizzle-orm",
    "drizzle-kit",
    "tailwindcss",
    "react-native",
    "react-dom",
    "react-router",
    "i18next",
    "react-i18next",
    "lucide-react",
    "zod",
    "typescript",
    "biome",
    "lefthook",
    "turborepo",
    "wrangler",
    "miniflare",
    "scalar",
    "orpc",
    "pnpm",
    "knip",
    "shadcn",
    "uniwind",
    "lefthook",
}

# ── False positive word list ───────────────────────────────────────────
# Common English words or spec terms that look like package names
# but are not actual npm packages.

FALSE_POSITIVES: set[str] = {
    "e.g",
    "i.e",
    "sign-off",
    "sign-in",
    "sign-up",
    "sign-out",
    "log-in",
    "log-out",
    "opt-in",
    "opt-out",
    "pre-code",
    "pre-built",
    "re-export",
    "re-exports",
    "re-render",
    "re-renders",
    "re-run",
    "co-located",
    "co-author",
    "real-time",
    "non-empty",
    "non-null",
    "non-zero",
    "non-goals",
    "read-only",
    "read-write",
    "write-only",
    "auto-fix",
    "auto-generated",
    "auto-save",
    "end-to-end",
    "out-of-scope",
    "up-to-date",
    "built-in",
    "third-party",
    "open-source",
    "type-safe",
    "type-check",
    "type-level",
    "first-party",
    "second-party",
    "dead-code",
    "hot-reload",
    "hot-module",
    "server-side",
    "client-side",
    "left-to-right",
    "right-to-left",
    "back-end",
    "front-end",
    "full-stack",
    "on-demand",
    "per-route",
    "per-page",
    "per-request",
    "per-user",
    "per-org",
    "field-level",
    "route-level",
    "page-level",
    "time-based",
    "role-based",
    "token-based",
    "file-based",
    "event-driven",
    "user-facing",
    "spec-derived",
    "cross-cutting",
    "kebab-case",
    "snake-case",
    "camel-case",
    "pascal-case",
}

# Short words that can never be packages (< 3 chars after stripping)
MIN_PACKAGE_NAME_LENGTH = 3

# Prefixes that indicate compound English words, not packages
_FALSE_PREFIXES = (
    "self-", "non-", "pre-", "post-", "re-", "co-", "un-",
    "anti-", "multi-", "cross-", "sub-", "over-", "under-",
    "semi-", "inter-", "intra-", "mid-", "well-", "ill-",
    "half-", "all-", "ever-", "single-", "double-", "triple-",
    "zero-", "one-", "two-", "three-", "four-", "five-",
    "six-", "seven-", "eight-", "nine-", "ten-",
    "first-", "second-", "third-", "last-",
    "high-", "low-", "long-", "short-", "near-",
    "full-", "hard-", "soft-", "new-", "old-",
)

# Suffixes that indicate compound English words, not packages
_FALSE_SUFFIXES = (
    "-only", "-free", "-like", "-wide", "-safe", "-based",
    "-aware", "-driven", "-level", "-facing", "-ready",
    "-specific", "-sensitive", "-friendly", "-proof",
    "-party", "-source", "-stack", "-end", "-time",
    "-case", "-side", "-off", "-in", "-out", "-up",
    "-text", "-modal", "-form", "-page", "-view",
    "-error", "-success", "-failure", "-check", "-style",
    "-bound", "-linked", "-related", "-oriented",
    "-restricted", "-enabled", "-disabled",
)


def is_false_positive(name: str) -> bool:
    """Return True if a candidate package name is a false positive."""
    lower = name.lower()
    if lower in FALSE_POSITIVES:
        return True
    if len(lower) < MIN_PACKAGE_NAME_LENGTH:
        return True
    # Pure numbers or version-like strings
    if re.match(r"^\d+(\.\d+)*$", lower):
        return True
    # Compound English words with common prefixes
    if any(lower.startswith(p) for p in _FALSE_PREFIXES):
        # But allow known packages that start with these
        if lower not in KNOWN_PACKAGES:
            return True
    # Compound English words with common suffixes
    if any(lower.endswith(s) for s in _FALSE_SUFFIXES):
        if lower not in KNOWN_PACKAGES:
            return True
    return False

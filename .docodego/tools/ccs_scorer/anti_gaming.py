"""Anti-gaming checks and shared detection patterns for CCS scoring."""

from __future__ import annotations

import re

# ── Vague qualifiers (shared with ICS) ──────────────────────────────────

VAGUE_QUALIFIERS: list[re.Pattern[str]] = [
    re.compile(r"\bfast\b", re.I),
    re.compile(r"\bslow\b", re.I),
    re.compile(r"\bgood\b", re.I),
    re.compile(r"\buser[\-\s]?friendly\b", re.I),
    re.compile(r"\bintuitive\b", re.I),
    re.compile(r"\breasonable\b", re.I),
    re.compile(r"\bappropriate\b", re.I),
    re.compile(r"\bhigh[\-\s]?quality\b", re.I),
    re.compile(r"\brobust\b", re.I),
    re.compile(r"\bscalable\b(?!\s*[\(\:\—\-–]\s*\d)", re.I),
    re.compile(r"\befficient\b(?!\s*[\(\:\—\-–]\s*\d)", re.I),
    re.compile(r"\bsecure\b(?!\s*[\(\:\—\-–])", re.I),
    re.compile(r"\bas\s+needed\b", re.I),
    re.compile(r"\bshould\b", re.I),
    re.compile(r"\bmay\b", re.I),
]

# ── Vague scope terms (unbounded rule scope) ─────────────────────────────

VAGUE_SCOPE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\beverywhere\b", re.I),
    re.compile(r"\ball\s+components?\b", re.I),
    re.compile(r"\bentire\s+codebase\b", re.I),
    re.compile(r"\bthe\s+whole\s+project\b", re.I),
    re.compile(r"\banywhere\s+in\s+the\s+(codebase|repo|project)\b", re.I),
    # "all files" only vague when not followed by a scoping phrase
    re.compile(r"\ball\s+files\b(?!\s+(under|in|within|matching)\s+)", re.I),
]

# ── Scope specificity indicators ─────────────────────────────────────────

SCOPE_SIGNAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"`[^`]*[\*/][^`]*`"),                          # glob in backticks
    re.compile(r"`[^`]*/[^`]+`"),                              # path in backticks
    re.compile(r"\bapps/\w"),                                  # app workspace path
    re.compile(r"\bpackages/\w"),                              # package workspace path
    re.compile(r"\bsrc/\w"),                                   # src path
    re.compile(r"\be2e/"),                                     # e2e path
    re.compile(r"\*\*/"),                                      # ** glob
    re.compile(r"\*\.[a-z]{2,4}\b"),                           # *.ts style
    re.compile(r"\.docodego/"),                                # tool paths
    re.compile(r"\b(apps|packages|e2e)/"),                     # workspace roots
    re.compile(                                                # workspace names
        r"\b(web|api|mobile|desktop|browser-extension|library|contracts|ui|i18n)\b",
        re.I,
    ),
]

# ── Violation detection signal indicators ────────────────────────────────

VIOLATION_SIGNAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bbiome\b", re.I),
    re.compile(r"\bknip\b", re.I),
    re.compile(r"\btsc\b", re.I),
    re.compile(r"\bvitest\b", re.I),
    re.compile(r"\bplaywright\b", re.I),
    re.compile(r"\blefthook\b", re.I),
    re.compile(r"\bturbo\b", re.I),
    re.compile(r"\bpnpm\b", re.I),
    re.compile(r"\bgrep\b", re.I),
    re.compile(r"\bnpm\b", re.I),
    re.compile(r"`[a-z][a-zA-Z]{3,}`"),       # camelCase identifier in backticks
    re.compile(r"`[a-z][a-z0-9-]{3,}`"),       # kebab-case rule id in backticks
    re.compile(r"rule\s+(?:id|ID|name)"),       # "rule ID: ..."
    re.compile(r"--[a-z][a-zA-Z-]{2,}"),        # CLI flags (--no-verify etc.)
    re.compile(r"noRestricted\w+"),             # Biome rule names
    re.compile(r"organizeImports"),
    re.compile(r"useImport\w+"),
    re.compile(r"\.json\b"),                    # config file references
    re.compile(r"\.toml\b"),
    re.compile(r"CI\s+(script|check|step)", re.I),
]

# ── Enforcement tier patterns ─────────────────────────────────────────────

TIER_PATTERN: re.Pattern[str] = re.compile(r"\bL[123]\b")
L1_PATTERN: re.Pattern[str] = re.compile(r"\bL1\b")
L2_PATTERN: re.Pattern[str] = re.compile(r"\bL2\b")
L3_PATTERN: re.Pattern[str] = re.compile(r"\bL3\b")

# ── Tool/command reference patterns ──────────────────────────────────────

TOOL_REF_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bbiome\b", re.I),
    re.compile(r"\bknip\b", re.I),
    re.compile(r"\btsc\b", re.I),
    re.compile(r"\bpnpm\b", re.I),
    re.compile(r"\bgithub\s+actions?\b", re.I),
    re.compile(r"\bworkflow\b", re.I),
    re.compile(r"`[^`]+`"),                     # any backtick-quoted command/tool
]


# ── Helper functions ──────────────────────────────────────────────────────


def has_scope_signal(text: str) -> bool:
    """Return True if text contains a specific scope indicator."""
    return any(pat.search(text) for pat in SCOPE_SIGNAL_PATTERNS)


def has_vague_scope(text: str) -> bool:
    """Return True if text uses unbounded vague scope language."""
    return any(pat.search(text) for pat in VAGUE_SCOPE_PATTERNS)


def has_violation_signal(text: str) -> bool:
    """Return True if text names a specific detection tool, rule, or pattern."""
    return any(pat.search(text) for pat in VIOLATION_SIGNAL_PATTERNS)


def has_tool_reference(text: str) -> bool:
    """Return True if text names a specific tool or command."""
    return any(pat.search(text) for pat in TOOL_REF_PATTERNS)


def has_if_then_form(text: str) -> bool:
    """Return True if a rule bullet contains IF ... THEN structure."""
    lower = text.lower()
    if_pos = lower.find("if ")
    if if_pos == -1:
        if_pos = lower.find("if\n")
    then_pos = lower.rfind("then ")
    if then_pos == -1:
        then_pos = lower.rfind("then\n")
    if then_pos == -1:
        then_pos = lower.rfind("then:")
    return if_pos != -1 and then_pos != -1 and then_pos > if_pos


def count_vague_qualifiers(text: str) -> dict[str, int]:
    """Return a dict of vague qualifier → occurrence count found in text."""
    found: dict[str, int] = {}
    for pat in VAGUE_QUALIFIERS:
        matches = pat.findall(text)
        if matches:
            qualifier = matches[0].lower()
            found[qualifier] = found.get(qualifier, 0) + len(matches)
    return found

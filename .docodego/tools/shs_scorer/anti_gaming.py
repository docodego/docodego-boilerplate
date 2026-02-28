"""Anti-gaming constants for SHS scoring."""

from __future__ import annotations

import re

# ── Expected sections per spec type ────────────────────────────────────

# Heading patterns matched case-insensitively against ## headings.
BEHAVIORAL_SECTIONS: list[re.Pattern[str]] = [
    re.compile(r"^intent$", re.I),
    re.compile(r"^acceptance\s+criteria$", re.I),
    re.compile(r"^behavioral\s+flow$", re.I),
    re.compile(r"^failure\s+modes?$", re.I),
    re.compile(r"^constraints?$", re.I),
]

FOUNDATION_SECTIONS: list[re.Pattern[str]] = [
    re.compile(r"^intent$", re.I),
    re.compile(r"^acceptance\s+criteria$", re.I),
    re.compile(r"^constraints?$", re.I),
    re.compile(r"^integration\s+map$", re.I),
]

CONVENTION_SECTIONS: list[re.Pattern[str]] = [
    re.compile(r"^intent$", re.I),
    re.compile(r"^rules?$", re.I),
    re.compile(r"^enforcement$", re.I),
    re.compile(r"^violation\s+signals?$", re.I),
    re.compile(r"^remediation$", re.I),
]

MINIMAL_SECTIONS: list[re.Pattern[str]] = [
    re.compile(r"^intent$", re.I),
    re.compile(r"^acceptance\s+criteria$", re.I),
    re.compile(r"^constraints?$", re.I),
]

EXPECTED_SECTIONS: dict[str, list[re.Pattern[str]]] = {
    "behavioral": BEHAVIORAL_SECTIONS,
    "foundation": FOUNDATION_SECTIONS,
    "convention": CONVENTION_SECTIONS,
    "unknown": MINIMAL_SECTIONS,
}

# ── Section heading aliases ────────────────────────────────────────────

# Maps alternative headings to their canonical form for matching.
SECTION_ALIASES: dict[str, list[re.Pattern[str]]] = {
    "intent": [
        re.compile(r"^purpose$", re.I),
        re.compile(r"^objective$", re.I),
        re.compile(r"^what\s+and\s+why$", re.I),
    ],
    "acceptance criteria": [
        re.compile(r"^success\s+criteria$", re.I),
        re.compile(r"^done\s+when$", re.I),
        re.compile(r"^definition\s+of\s+done$", re.I),
    ],
    "constraints": [
        re.compile(r"^boundaries$", re.I),
        re.compile(r"^out\s+of\s+scope$", re.I),
        re.compile(r"^non[\-\s]?goals$", re.I),
    ],
    "failure modes": [
        re.compile(r"^failure\s+scenarios$", re.I),
        re.compile(r"^risks$", re.I),
        re.compile(r"^edge\s+cases$", re.I),
        re.compile(r"^threat\s+model$", re.I),
    ],
    "behavioral flow": [
        re.compile(r"^flow$", re.I),
        re.compile(r"^process\s+flow$", re.I),
    ],
    "integration map": [
        re.compile(r"^integrations?$", re.I),
        re.compile(r"^dependencies$", re.I),
    ],
    "rules": [
        re.compile(r"^rule\s+set$", re.I),
    ],
    "enforcement": [
        re.compile(r"^tooling$", re.I),
    ],
    "violation signal": [
        re.compile(r"^violation\s+signals?$", re.I),
    ],
    "remediation": [
        re.compile(r"^fix(es)?$", re.I),
    ],
}

# ── Frontmatter validators ─────────────────────────────────────────────

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VALID_STATUSES = {"draft", "approved", "deprecated"}

# ── Infrastructure files excluded from orphan checks ───────────────────

INFRASTRUCTURE_STEMS = {
    "product-context",
    "review",
    "roadmap",
    "readme",
}

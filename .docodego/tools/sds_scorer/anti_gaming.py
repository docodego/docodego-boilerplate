"""Anti-gaming pattern libraries for SDS scoring."""

from __future__ import annotations

import re

# ── STRIDE keyword patterns ─────────────────────────────────────────────
# Each STRIDE category maps to keywords that indicate the spec addresses
# that threat category.

STRIDE_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "spoofing": [
        re.compile(r"\bsession\s+hijack", re.I),
        re.compile(r"\bimpersonat", re.I),
        re.compile(r"\b(token|OTP|code)\s+replay", re.I),
        re.compile(r"\breplay\s+attack", re.I),
        re.compile(r"\bidentity\b", re.I),
        re.compile(r"\bphishing\b", re.I),
        re.compile(r"\bcredential\s+stuffing\b", re.I),
        re.compile(r"\bspoof", re.I),
        re.compile(r"\bforged?\s+(token|session|cookie)", re.I),
        re.compile(r"\bauthenticat\w*\s+(fail|bypass|attack)", re.I),
        re.compile(r"\bman[\-\s]?in[\-\s]?the[\-\s]?middle\b", re.I),
        re.compile(r"\bunauthorized\s+(email\s+)?access\b", re.I),
    ],
    "tampering": [
        re.compile(r"\binjection\b", re.I),
        re.compile(r"\bXSS\b"),
        re.compile(r"\bcross[\-\s]?site\s+script", re.I),
        re.compile(r"\bCSRF\b"),
        re.compile(r"\bparameter\s+tamper", re.I),
        re.compile(r"\bdata\s+modification\b", re.I),
        re.compile(r"\bSQL\s+injection\b", re.I),
        re.compile(r"\btamper", re.I),
        re.compile(r"\bmanipulat\w+\s+(input|data|param)", re.I),
        re.compile(r"\bintercept", re.I),
        re.compile(r"\bnetwork\s+sniff", re.I),
        re.compile(r"\bmalformed\b", re.I),
        re.compile(r"\binvalidat\w+\s+(the\s+)?(OTP|token|code|session)", re.I),
    ],
    "repudiation": [
        re.compile(r"\baudit\s+log", re.I),
        re.compile(r"\blogging\b", re.I),
        re.compile(r"\bnon[\-\s]?repudiation\b", re.I),
        re.compile(r"\baccountability\b", re.I),
        re.compile(r"\b(audit|activity)\s+trail\b", re.I),
        re.compile(r"\blog\w*\s+the\s+(action|attempt|event|failure|error)", re.I),
        re.compile(r"\blog\w*\s+(delivery|request|access)\s+failure", re.I),
        re.compile(r"\brepudiat", re.I),
    ],
    "info_disclosure": [
        re.compile(r"\bdata\s+leak", re.I),
        re.compile(r"\b(data|info(rmation)?)\s+exposure\b", re.I),
        re.compile(r"\bsensitive\s+data\b", re.I),
        re.compile(r"\bPII\b"),
        re.compile(r"\bstack\s+trace\b", re.I),
        re.compile(r"\berror\s+message\s+leak", re.I),
        re.compile(r"\binformation\s+disclosure\b", re.I),
        re.compile(r"\bredact", re.I),
        re.compile(r"\bexpos(e|ing|ure)\s+(internal|secret|key|token)", re.I),
        re.compile(r"\benumeration\s+protect", re.I),
    ],
    "dos": [
        re.compile(r"\brate\s+limit", re.I),
        re.compile(r"\bthrottle\b", re.I),
        re.compile(r"\bDDoS\b", re.I),
        re.compile(r"\bresource\s+exhaust", re.I),
        re.compile(r"\bflood\b", re.I),
        re.compile(r"\bbrute\s+force\b", re.I),
        re.compile(r"\bdenial\s+of\s+service\b", re.I),
        re.compile(r"\b429\b"),
        re.compile(r"\bcooldown\b", re.I),
        re.compile(r"\bretry\s+(cap|limit)\b", re.I),
    ],
    "eop": [
        re.compile(r"\bprivilege\s+escalat", re.I),
        re.compile(r"\brole\s+bypass\b", re.I),
        re.compile(r"\badmin\s+access\b", re.I),
        re.compile(r"\bunauthorized\s+elevat", re.I),
        re.compile(r"\belevation\s+of\s+privilege\b", re.I),
        re.compile(r"\brole\s+check\b", re.I),
        re.compile(r"\bpermission\s+(check|guard|gate)\b", re.I),
        re.compile(r"\baccess\s+control\b", re.I),
        re.compile(r"\bActions?\s+Denied\b", re.I),
        re.compile(r"\bActions?\s+Permitted\b", re.I),
        re.compile(r"\bcannot\s+see\b", re.I),
    ],
}

# ── Applicability triggers ──────────────────────────────────────────────
# Keywords that indicate a STRIDE category is relevant to the spec.

APPLICABILITY_TRIGGERS: dict[str, list[re.Pattern[str]]] = {
    "spoofing": [
        re.compile(r"\bsession\b", re.I),
        re.compile(r"\bauth(enticat|oriz)", re.I),
        re.compile(r"\blogin\b", re.I),
        re.compile(r"\bsign[\-\s]?in\b", re.I),
        re.compile(r"\btoken\b", re.I),
        re.compile(r"\bcookie\b", re.I),
        re.compile(r"\bcredential\b", re.I),
    ],
    "tampering": [
        re.compile(r"\buser\s+input\b", re.I),
        re.compile(r"\bform\b", re.I),
        re.compile(r"\bsubmit\b", re.I),
        re.compile(r"\benter\b", re.I),
        re.compile(r"\btype\b", re.I),
        re.compile(r"\bupload\b", re.I),
        re.compile(r"\brequest\s+body\b", re.I),
        re.compile(r"\bpayload\b", re.I),
    ],
    "repudiation": [
        re.compile(r"\bsensitive\b", re.I),
        re.compile(r"\bdelete\b", re.I),
        re.compile(r"\bremove\b", re.I),
        re.compile(r"\bmodif(y|ies|ication)\b", re.I),
        re.compile(r"\btransfer\b", re.I),
        re.compile(r"\bpayment\b", re.I),
        re.compile(r"\binvit", re.I),
    ],
    "info_disclosure": [
        re.compile(r"\berror\b", re.I),
        re.compile(r"\b(4|5)\d{2}\b"),
        re.compile(r"\bstack\b", re.I),
        re.compile(r"\bresponse\b", re.I),
        re.compile(r"\bAPI\b"),
        re.compile(r"\bpersonal\b", re.I),
        re.compile(r"\bemail\b", re.I),
    ],
    "dos": [
        re.compile(r"\bpublic\b", re.I),
        re.compile(r"\bendpoint\b", re.I),
        re.compile(r"\buser\s+input\b", re.I),
        re.compile(r"\bsubmit\b", re.I),
        re.compile(r"\brequest\b", re.I),
        re.compile(r"\bAPI\b"),
    ],
    "eop": [
        re.compile(r"\brole\b", re.I),
        re.compile(r"\badmin\b", re.I),
        re.compile(r"\bowner\b", re.I),
        re.compile(r"\bmember\b", re.I),
        re.compile(r"\bpermission\b", re.I),
        re.compile(r"\bauthoriz", re.I),
    ],
}

# ── Named attack vector bonus patterns ──────────────────────────────────

NAMED_ATTACK_VECTORS: list[re.Pattern[str]] = [
    re.compile(r"\bCSRF\b"),
    re.compile(r"\btiming\s+attack\b", re.I),
    re.compile(r"\btoken\s+replay\b", re.I),
    re.compile(r"\bSQL\s+injection\b", re.I),
    re.compile(r"\bXSS\b"),
    re.compile(r"\bclickjacking\b", re.I),
    re.compile(r"\bpath\s+traversal\b", re.I),
    re.compile(r"\bSSRF\b"),
    re.compile(r"\bopen\s+redirect\b", re.I),
    re.compile(r"\bbrute[\-\s]?force\b", re.I),
    re.compile(r"\bcredential\s+stuffing\b", re.I),
    re.compile(r"\bsession\s+fixation\b", re.I),
    re.compile(r"\breplay\s+attack\b", re.I),
    re.compile(r"\bman[\-\s]?in[\-\s]?the[\-\s]?middle\b", re.I),
    re.compile(r"\benumeration\s+attack\b", re.I),
]

# ── Input verb patterns (Behavioral Flow scanning) ──────────────────────

INPUT_VERBS: list[re.Pattern[str]] = [
    re.compile(r"\benters?\b", re.I),
    re.compile(r"\btypes?\b(?!\s+(of|system|script|check))", re.I),
    re.compile(r"\bselects?\b", re.I),
    re.compile(r"\buploads?\b", re.I),
    re.compile(r"\bsubmits?\b", re.I),
    re.compile(r"\bpastes?\b", re.I),
    re.compile(r"\bfills?\b", re.I),
    re.compile(r"\bprovides?\b", re.I),
    re.compile(r"\bsets?\b(?!\s+(the|a|an|up|cookie|header))", re.I),
    re.compile(r"\bchooses?\b", re.I),
]

# ── Defense depth signal patterns ───────────────────────────────────────

RATE_LIMIT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\brate\s+limit", re.I),
    re.compile(r"\bthrottle\b", re.I),
    re.compile(r"\b429\b"),
    re.compile(r"\bcooldown\b", re.I),
]

CSRF_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bCSRF\b"),
    re.compile(r"\bSameSite\b", re.I),
    re.compile(r"\banti[\-\s]?forgery\b", re.I),
    re.compile(r"\borigin\s+validation\b", re.I),
]

TOKEN_HARDENING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bhttpOnly\b", re.I),
    re.compile(r"\bsecure\s+flag\b", re.I),
    re.compile(r"\btoken\s+rotation\b", re.I),
    re.compile(r"\bsigned\s+cookie\b", re.I),
    re.compile(r"\bHttpOnly\b"),
]

ERROR_SANITIZATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bgeneric\s+error\b", re.I),
    re.compile(r"\bno\s+stack\s+trace\b", re.I),
    re.compile(r"\bsanitize\b", re.I),
    re.compile(r"\bredact", re.I),
    re.compile(r"\bstack\s+trace\s+.{0,20}absent\b", re.I),
    re.compile(r"\berror[\s\-]?handl\w+\s+spec\b", re.I),
]

AUDIT_LOGGING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\baudit\b", re.I),
    re.compile(r"\blog\s+the\s+(action|attempt|event)\b", re.I),
    re.compile(r"\blog\w*\s+(the\s+)?delivery\s+failure\b", re.I),
    re.compile(r"\bmonitor\b", re.I),
]

# ── Applicability triggers for defense depth signals ────────────────────

RATE_LIMIT_TRIGGERS: list[re.Pattern[str]] = [
    re.compile(r"\bpublic\b", re.I),
    re.compile(r"\bendpoint\b", re.I),
    re.compile(r"\buser\s+input\b", re.I),
    re.compile(r"\bsubmit\b", re.I),
    re.compile(r"\blogin\b", re.I),
    re.compile(r"\bsign[\-\s]?in\b", re.I),
]

CSRF_TRIGGERS: list[re.Pattern[str]] = [
    re.compile(r"\bstate[\-\s]?chang", re.I),
    re.compile(r"\bPOST\b"),
    re.compile(r"\bPUT\b"),
    re.compile(r"\bDELETE\b"),
    re.compile(r"\bsubmit\b", re.I),
    re.compile(r"\bcreate\b", re.I),
    re.compile(r"\bupdate\b", re.I),
    re.compile(r"\bmodif", re.I),
]

TOKEN_TRIGGERS: list[re.Pattern[str]] = [
    re.compile(r"\bsession\b", re.I),
    re.compile(r"\btoken\b", re.I),
    re.compile(r"\bcookie\b", re.I),
    re.compile(r"\bauth(enticat)", re.I),
]

ERROR_TRIGGERS: list[re.Pattern[str]] = [
    re.compile(r"\berror\b", re.I),
    re.compile(r"\b500\b"),
    re.compile(r"\bfailure\b", re.I),
    re.compile(r"\bexception\b", re.I),
]

AUDIT_TRIGGERS: list[re.Pattern[str]] = [
    re.compile(r"\bsensitive\b", re.I),
    re.compile(r"\bdelete\b", re.I),
    re.compile(r"\bpermission\b", re.I),
    re.compile(r"\badmin\b", re.I),
    re.compile(r"\bpayment\b", re.I),
    re.compile(r"\btransfer\b", re.I),
]

# ── Validation rule patterns ────────────────────────────────────────────

VALIDATION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bvalidat", re.I),
    re.compile(r"\breject", re.I),
    re.compile(r"\bformat\s+(check|validation)\b", re.I),
    re.compile(r"\bmax\s+(length|size|chars?)\b", re.I),
    re.compile(r"\bmin\s+(length|size|chars?)\b", re.I),
    re.compile(r"\bregex\b", re.I),
    re.compile(r"\bpattern\b", re.I),
    re.compile(r"\b(must|shall)\s+(be|match|contain)\b", re.I),
    re.compile(r"\bZod\b"),
    re.compile(r"\bschema\b", re.I),
    re.compile(r"\bsanitiz", re.I),
    re.compile(r"\btrim\b", re.I),
    re.compile(r"\bstrip\b", re.I),
]

REJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b4\d{2}\b"),
    re.compile(r"\berror\s+message\b", re.I),
    re.compile(r"\breject", re.I),
    re.compile(r"\bfail\b", re.I),
    re.compile(r"\binvalid\b", re.I),
    re.compile(r"\bdisplay\w*\s+(a\s+)?error\b", re.I),
    re.compile(r"\breturn\w*\s+(HTTP\s+)?4\d{2}\b", re.I),
]

# ── Cross-reference credit patterns ─────────────────────────────────────

CROSS_REF_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"defined\s+in\s+`[^`]+`", re.I),
    re.compile(r"(covered|handled)\s+(in|by)\s+`[^`]+`", re.I),
    re.compile(r"(see|refer\s+to)\s+`[^`]+\.md`", re.I),
    re.compile(r"spec(ification)?\s*$", re.I),
    re.compile(r"\berror[\s\-]?handling\s+spec\b", re.I),
]


# ── Helper functions ────────────────────────────────────────────────────


def has_any_match(text: str, patterns: list[re.Pattern[str]]) -> bool:
    """Return True if text matches any pattern in the list."""
    return any(pat.search(text) for pat in patterns)


def count_named_attack_vectors(text: str) -> int:
    """Count distinct named attack vectors found in text."""
    return sum(1 for pat in NAMED_ATTACK_VECTORS if pat.search(text))

"""Markdown convention spec parser — extracts sections by heading patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Section name → list of case-insensitive heading patterns that match it.
SECTION_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "intent": [
        re.compile(r"^intent$", re.I),
        re.compile(r"^purpose$", re.I),
        re.compile(r"^objective$", re.I),
        re.compile(r"^why\s+this\s+convention$", re.I),
    ],
    "rules": [
        re.compile(r"^rules?$", re.I),
        re.compile(r"^convention\s+rules?$", re.I),
        re.compile(r"^rule\s+set$", re.I),
        re.compile(r"^coding\s+rules?$", re.I),
        re.compile(r"^the\s+rules?$", re.I),
    ],
    "enforcement": [
        re.compile(r"^enforcement$", re.I),
        re.compile(r"^enforcement\s+tiers?$", re.I),
        re.compile(r"^enforcement\s+&\s+tiers?$", re.I),
        re.compile(r"^tiers?$", re.I),
        re.compile(r"^enforcement\s+levels?$", re.I),
    ],
    "violation_signal": [
        re.compile(r"^violation\s+signal$", re.I),
        re.compile(r"^violation\s+detection$", re.I),
        re.compile(r"^detection$", re.I),
        re.compile(r"^signals?$", re.I),
        re.compile(r"^how\s+to\s+detect$", re.I),
        re.compile(r"^detecting\s+violations?$", re.I),
    ],
    "correct_forbidden": [
        re.compile(r"^correct\s+vs\.?\s+forbidden$", re.I),
        re.compile(r"^examples?$", re.I),
        re.compile(r"^correct\s+and\s+incorrect$", re.I),
        re.compile(r"^right\s+vs\.?\s+wrong$", re.I),
        re.compile(r"^do\s+vs\.?\s+don.?t$", re.I),
        re.compile(r"^correct\s+vs\.\s+forbidden$", re.I),
    ],
    "remediation": [
        re.compile(r"^remediation$", re.I),
        re.compile(r"^fix(es)?$", re.I),
        re.compile(r"^resolution$", re.I),
        re.compile(r"^how\s+to\s+(fix|resolve)$", re.I),
        re.compile(r"^remediation\s+steps?$", re.I),
        re.compile(r"^fixing\s+violations?$", re.I),
    ],
}

REQUIRED_SECTIONS = ["intent", "rules", "enforcement", "violation_signal", "remediation"]

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_BULLET_RE = re.compile(r"^(?:[-*•]|\d+[.)]\s)\s*(.+)$")


@dataclass
class Section:
    """A parsed section from a convention spec file."""

    name: str       # canonical section key
    heading: str    # original heading text
    level: int      # heading depth (1-6)
    content: str = ""
    word_count: int = 0


@dataclass
class ParsedConventionSpec:
    """Result of parsing a markdown convention spec file."""

    sections: dict[str, Section] = field(default_factory=dict)
    raw_text: str = ""
    title: str = ""

    @property
    def missing_sections(self) -> list[str]:
        return [s for s in REQUIRED_SECTIONS if s not in self.sections]

    @property
    def present_sections(self) -> list[str]:
        return [s for s in REQUIRED_SECTIONS if s in self.sections]


def _classify_heading(text: str) -> str | None:
    """Return canonical section name if heading matches a known pattern, else None."""
    stripped = text.strip()
    for section_name, patterns in SECTION_PATTERNS.items():
        for pat in patterns:
            if pat.match(stripped):
                return section_name
    return None


def extract_bullets(content: str) -> list[str]:
    """Extract top-level bullet text from section content."""
    bullets = []
    for line in content.split("\n"):
        m = _BULLET_RE.match(line.strip())
        if m:
            bullets.append(m.group(1).strip())
    return [b for b in bullets if b]


def parse_spec(markdown: str) -> ParsedConventionSpec:
    """Parse a markdown convention spec file into structured sections."""
    result = ParsedConventionSpec(raw_text=markdown)
    lines = markdown.split("\n")

    current_section: str | None = None
    current_heading: str = ""
    current_level: int = 0
    content_lines: list[str] = []
    title_found = False
    in_frontmatter = False
    frontmatter_done = False

    def _flush() -> None:
        nonlocal current_section, content_lines
        if current_section is not None:
            body = "\n".join(content_lines).strip()
            words = len(body.split()) if body else 0
            result.sections[current_section] = Section(
                name=current_section,
                heading=current_heading,
                level=current_level,
                content=body,
                word_count=words,
            )
        content_lines = []

    for line in lines:
        # Handle YAML frontmatter
        if line.strip() == "---" and not frontmatter_done:
            if not in_frontmatter:
                in_frontmatter = True
                continue
            else:
                in_frontmatter = False
                frontmatter_done = True
                continue
        if in_frontmatter:
            continue

        heading_match = _HEADING_RE.match(line.strip())
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            if level == 1 and not title_found:
                result.title = heading_text
                title_found = True

            section_name = _classify_heading(heading_text)
            if section_name is not None:
                _flush()
                current_section = section_name
                current_heading = heading_text
                current_level = level
                continue

        if current_section is not None:
            content_lines.append(line)

    _flush()
    return result

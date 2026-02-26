"""Markdown spec parser — extracts sections by heading patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Section name → list of case-insensitive heading patterns that match it.
# Patterns are matched against the heading text after stripping '#' and whitespace.
SECTION_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "intent": [
        re.compile(r"^intent$", re.I),
        re.compile(r"^purpose$", re.I),
        re.compile(r"^objective$", re.I),
        re.compile(r"^what and why$", re.I),
    ],
    "acceptance_criteria": [
        re.compile(r"^acceptance\s+criteria$", re.I),
        re.compile(r"^success\s+criteria$", re.I),
        re.compile(r"^done\s+when$", re.I),
        re.compile(r"^definition\s+of\s+done$", re.I),
    ],
    "constraints": [
        re.compile(r"^constraints$", re.I),
        re.compile(r"^boundaries$", re.I),
        re.compile(r"^out\s+of\s+scope$", re.I),
        re.compile(r"^non[\-\s]?goals$", re.I),
    ],
    "failure_modes": [
        re.compile(r"^failure\s+modes$", re.I),
        re.compile(r"^failure\s+scenarios$", re.I),
        re.compile(r"^risks$", re.I),
        re.compile(r"^edge\s+cases$", re.I),
        re.compile(r"^threat\s+model$", re.I),
    ],
    "governance": [
        re.compile(r"^governance(\s+checkpoint)?$", re.I),
        re.compile(r"^governor\s+sign[\-\s]?off$", re.I),
        re.compile(r"^human\s+review$", re.I),
        re.compile(r"^kill\s+switch$", re.I),
    ],
}

REQUIRED_SECTIONS = ["intent", "acceptance_criteria", "constraints", "failure_modes"]

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


@dataclass
class Section:
    """A parsed section from a spec file."""

    name: str  # canonical section key
    heading: str  # original heading text
    level: int  # heading depth (1-6)
    content: str = ""  # body text under the heading
    word_count: int = 0


@dataclass
class ParsedSpec:
    """Result of parsing a markdown spec file."""

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


def parse_spec(markdown: str) -> ParsedSpec:
    """Parse a markdown spec file into structured sections."""
    result = ParsedSpec(raw_text=markdown)
    lines = markdown.split("\n")

    current_section: str | None = None
    current_heading: str = ""
    current_level: int = 0
    content_lines: list[str] = []
    title_found = False

    def _flush():
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
        heading_match = _HEADING_RE.match(line.strip())
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            # Capture title from first h1
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

        # Skip frontmatter
        if line.strip() == "---" and not content_lines and current_section is None:
            continue

        if current_section is not None:
            content_lines.append(line)

    _flush()
    return result

"""Markdown spec parser for SDS — extracts sections by heading patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Section name -> list of case-insensitive heading patterns that match it.
SECTION_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "failure_modes": [
        re.compile(r"^failure\s+modes?$", re.I),
        re.compile(r"^failure\s+scenarios?$", re.I),
        re.compile(r"^risks?$", re.I),
        re.compile(r"^edge\s+cases?$", re.I),
        re.compile(r"^threat\s+model$", re.I),
    ],
    "permission_model": [
        re.compile(r"^permission\s+model$", re.I),
        re.compile(r"^permissions?$", re.I),
        re.compile(r"^access\s+control$", re.I),
        re.compile(r"^authorization$", re.I),
        re.compile(r"^roles?\s+and\s+permissions?$", re.I),
    ],
    "behavioral_flow": [
        re.compile(r"^behavioral\s+flow$", re.I),
        re.compile(r"^user\s+flow$", re.I),
        re.compile(r"^flow$", re.I),
        re.compile(r"^workflow$", re.I),
        re.compile(r"^user\s+journey$", re.I),
    ],
    "business_rules": [
        re.compile(r"^business\s+rules?$", re.I),
        re.compile(r"^rules?$", re.I),
        re.compile(r"^business\s+logic$", re.I),
    ],
    "constraints": [
        re.compile(r"^constraints?$", re.I),
        re.compile(r"^boundaries$", re.I),
        re.compile(r"^out\s+of\s+scope$", re.I),
        re.compile(r"^non[\-\s]?goals$", re.I),
    ],
    "intent": [
        re.compile(r"^intent$", re.I),
        re.compile(r"^purpose$", re.I),
        re.compile(r"^objective$", re.I),
    ],
    "acceptance_criteria": [
        re.compile(r"^acceptance\s+criteria$", re.I),
        re.compile(r"^success\s+criteria$", re.I),
    ],
    "declared_omissions": [
        re.compile(r"^declared\s+omissions?$", re.I),
        re.compile(r"^omissions?$", re.I),
    ],
    "integration_map": [
        re.compile(r"^integration\s+map$", re.I),
    ],
}

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")


@dataclass
class Section:
    """A parsed section from a spec file."""

    name: str       # canonical section key
    heading: str    # original heading text
    level: int      # heading depth (1-6)
    content: str = ""
    word_count: int = 0


@dataclass
class ParsedSpec:
    """Result of parsing a markdown spec file for SDS scoring."""

    sections: dict[str, Section] = field(default_factory=dict)
    raw_text: str = ""
    title: str = ""


def _classify_heading(text: str) -> str | None:
    """Return canonical section name if heading matches a known pattern."""
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
            elif current_section is not None and level <= current_level:
                _flush()
                current_section = None
                continue

        if current_section is not None:
            content_lines.append(line)

    _flush()
    return result

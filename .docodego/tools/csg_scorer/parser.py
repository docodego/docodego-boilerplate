"""Markdown spec parser for CSG — extracts cross-spec analysis data."""

from __future__ import annotations

import re
from pathlib import Path

from .extractors import (
    extract_constants_from_text,
    extract_http_statuses,
    parse_permission_table,
    parse_state_machine_table,
)
from .types import (
    ExtractedConstant,
    HttpStatusMention,
    ParsedCorpusSpec,
    PermissionRow,
    StateTransition,
)

# Re-export types for downstream imports
__all__ = [
    "ExtractedConstant",
    "HttpStatusMention",
    "ParsedCorpusSpec",
    "PermissionRow",
    "StateTransition",
    "parse_spec",
]

# ── Heading detection ──────────────────────────────────────────────────

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")

_SECTION_NAMES: dict[str, list[re.Pattern[str]]] = {
    "business_rules": [
        re.compile(r"^business\s+rules$", re.I),
    ],
    "constraints": [
        re.compile(r"^constraints$", re.I),
        re.compile(r"^boundaries$", re.I),
    ],
    "acceptance_criteria": [
        re.compile(r"^acceptance\s+criteria$", re.I),
        re.compile(r"^success\s+criteria$", re.I),
    ],
    "permission_model": [
        re.compile(r"^permission\s+model$", re.I),
        re.compile(r"^permissions$", re.I),
    ],
    "state_machine": [
        re.compile(r"^state\s+machine$", re.I),
        re.compile(r"^state\s+diagram$", re.I),
        re.compile(r"^state\s+transitions?$", re.I),
    ],
}


# ── Section extraction ────────────────────────────────────────────────


def _classify_heading(text: str) -> str | None:
    """Return canonical section name if heading matches, else None."""
    stripped = text.strip()
    for section_name, patterns in _SECTION_NAMES.items():
        for pat in patterns:
            if pat.match(stripped):
                return section_name
    return None


def _extract_sections(
    lines: list[str],
) -> dict[str, tuple[int, list[str]]]:
    """Extract named sections as {name: (start_line, content_lines)}."""
    sections: dict[str, tuple[int, list[str]]] = {}
    current: str | None = None
    current_level = 0
    start_line = 0
    content: list[str] = []

    def _flush() -> None:
        nonlocal current, content
        if current is not None:
            sections[current] = (start_line, content)
        content = []

    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line.strip())
        if m:
            level = len(m.group(1))
            heading_text = m.group(2).strip()
            section_name = _classify_heading(heading_text)
            if section_name is not None:
                _flush()
                current = section_name
                current_level = level
                start_line = i + 1
                continue
            elif current is not None and level <= current_level:
                _flush()
                current = None
                continue
        if current is not None:
            content.append(line)

    _flush()
    return sections


# ── Main parse function ───────────────────────────────────────────────


def parse_spec(filepath: Path) -> ParsedCorpusSpec:
    """Parse a single spec file for cross-spec analysis data."""
    markdown = filepath.read_text(encoding="utf-8")
    lines = markdown.split("\n")
    spec_name = filepath.stem

    result = ParsedCorpusSpec(
        filepath=filepath,
        name=spec_name,
    )

    sections = _extract_sections(lines)

    # Store raw section content
    if "business_rules" in sections:
        start, content = sections["business_rules"]
        result.business_rules = "\n".join(content)
    if "constraints" in sections:
        start, content = sections["constraints"]
        result.constraints = "\n".join(content)
    if "acceptance_criteria" in sections:
        start, content = sections["acceptance_criteria"]
        result.acceptance_criteria = "\n".join(content)

    # Parse Permission Model table
    if "permission_model" in sections:
        _, content = sections["permission_model"]
        result.permission_rows = parse_permission_table(
            content, spec_name,
        )

    # Parse State Machine table
    if "state_machine" in sections:
        _, content = sections["state_machine"]
        result.state_transitions = parse_state_machine_table(
            content, spec_name,
        )

    # Extract HTTP status mentions from entire file
    result.http_status_mentions = extract_http_statuses(
        lines, spec_name,
    )

    # Extract constants from business rules, constraints, and AC
    for section_key in (
        "business_rules", "constraints", "acceptance_criteria",
    ):
        if section_key in sections:
            start, content = sections[section_key]
            text = "\n".join(content)
            result.constants.extend(
                extract_constants_from_text(
                    text, start, spec_name, lines,
                ),
            )

    return result

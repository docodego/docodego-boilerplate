"""Markdown spec parser for SHS — extracts per-file metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_TABLE_ROW_RE = re.compile(r"^\|.+\|.+\|")
_FRONTMATTER_KV = re.compile(r"^(\w[\w-]*)\s*:\s*(.+)$")


@dataclass
class ParsedHealthSpec:
    """Metadata extracted from a single spec file."""

    filepath: Path
    name: str  # stem
    subdirectory: str  # parent dir name
    line_count: int = 0
    table_count: int = 0
    frontmatter: dict[str, str] = field(default_factory=dict)
    section_headings: list[str] = field(default_factory=list)
    related_specs_links: list[str] = field(default_factory=list)
    all_md_links: list[tuple[str, str, int]] = field(default_factory=list)
    spec_type: str = "unknown"


def _parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], int]:
    """Extract YAML frontmatter between --- delimiters.

    Returns the key-value dict and the line index after the closing ---.
    """
    fm: dict[str, str] = {}
    if not lines or lines[0].strip() != "---":
        return fm, 0

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return fm, i + 1
        m = _FRONTMATTER_KV.match(line.strip())
        if m:
            key = m.group(1).lower()
            val = m.group(2).strip().strip('"').strip("'")
            # Strip list brackets for roles etc.
            if val.startswith("[") and val.endswith("]"):
                val = val[1:-1].strip()
            fm[key] = val
    return fm, 0


def _count_tables(lines: list[str]) -> int:
    """Count distinct markdown tables (groups of consecutive table rows)."""
    count = 0
    in_table = False
    for line in lines:
        is_row = bool(_TABLE_ROW_RE.match(line.strip()))
        if is_row and not in_table:
            count += 1
            in_table = True
        elif not is_row:
            in_table = False
    return count


def _detect_spec_type(fm: dict[str, str], subdir: str) -> str:
    """Detect spec type from frontmatter id prefix or subdirectory."""
    spec_id = fm.get("id", "")
    if spec_id.startswith("SPEC-"):
        return "behavioral"
    if spec_id.startswith("FOUND-"):
        return "foundation"
    if spec_id.startswith("CONV-"):
        return "convention"
    # Fallback to subdirectory name
    subdir_lower = subdir.lower()
    if "behavioral" in subdir_lower:
        return "behavioral"
    if "foundation" in subdir_lower:
        return "foundation"
    if "convention" in subdir_lower:
        return "convention"
    return "unknown"


def _extract_related_links(
    lines: list[str], start_idx: int,
) -> list[str]:
    """Extract markdown link targets from the Related Specifications section."""
    links: list[str] = []
    for line in lines[start_idx:]:
        stripped = line.strip()
        # Stop at next ## heading
        if _HEADING_RE.match(stripped) and stripped.startswith("## "):
            break
        for _text, target in _MD_LINK_RE.findall(line):
            if target.endswith(".md"):
                links.append(target)
    return links


def parse_spec(filepath: Path) -> ParsedHealthSpec:
    """Parse a single spec file and extract health metadata."""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    subdir = filepath.parent.name

    fm, body_start = _parse_frontmatter(lines)
    spec_type = _detect_spec_type(fm, subdir)

    # Extract headings and locate Related Specifications
    headings: list[str] = []
    related_start: int | None = None
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line.strip())
        if m:
            level = len(m.group(1))
            heading_text = m.group(2).strip()
            if level == 2:
                headings.append(heading_text)
                if re.match(
                    r"^related\s+spec", heading_text, re.I,
                ):
                    related_start = i + 1

    # Related specs links
    related_links: list[str] = []
    if related_start is not None:
        related_links = _extract_related_links(lines, related_start)

    # All markdown links with line numbers
    all_links: list[tuple[str, str, int]] = []
    for i, line in enumerate(lines, start=1):
        for text, target in _MD_LINK_RE.findall(line):
            all_links.append((text, target, i))

    return ParsedHealthSpec(
        filepath=filepath,
        name=filepath.stem,
        subdirectory=subdir,
        line_count=len(lines),
        table_count=_count_tables(lines),
        frontmatter=fm,
        section_headings=headings,
        related_specs_links=related_links,
        all_md_links=all_links,
        spec_type=spec_type,
    )


def collect_specs(directory: Path) -> list[ParsedHealthSpec]:
    """Walk a directory and parse all spec .md files.

    Excludes README.md, REVIEW.md, and ROADMAP.md.
    """
    excluded = {
        "readme.md", "review.md", "roadmap.md", "product-context.md",
    }
    specs: list[ParsedHealthSpec] = []

    for md_file in sorted(directory.rglob("*.md")):
        if md_file.name.lower() in excluded:
            continue
        specs.append(parse_spec(md_file))

    return specs

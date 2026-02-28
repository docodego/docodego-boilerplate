"""SDDM parser — extracts package references from a spec corpus."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .anti_gaming import (
    KNOWN_PACKAGES,
    SCOPED_PKG_RE,
    UNSCOPED_PKG_RE,
    VERSION_HINT_RE,
    is_false_positive,
)

# ── Data structures ────────────────────────────────────────────────────


@dataclass
class PackageRef:
    """A single reference to a package found in a spec file."""

    name: str  # e.g., "better-auth", "@repo/ui", "hono"
    version_hint: str  # e.g., "v4", "^2.0", ">=1.5", "" if none
    source_spec: str  # filename where found
    in_table: bool  # found in a markdown table cell?
    in_backticks: bool  # found in backtick quotes?
    line_number: int


@dataclass
class SDDM:
    """Spec-Derived Dependency Manifest."""

    packages: list[PackageRef] = field(default_factory=list)
    unique_packages: dict[str, list[PackageRef]] = field(
        default_factory=dict,
    )

    def add(self, ref: PackageRef) -> None:
        """Add a package reference and update the unique index."""
        self.packages.append(ref)
        self.unique_packages.setdefault(ref.name, []).append(ref)


# ── Negation context ──────────────────────────────────────────────────
# Lines that mention a package as NOT being used (e.g., "count of X
# equals 0", "imports from X instead of Y").  These are architectural
# decisions, not actual dependencies.

_NEGATION_RE = re.compile(
    r"\bequals\s+0\b|\binstead\s+of\b",
    re.IGNORECASE,
)

# ── Table detection ────────────────────────────────────────────────────

_TABLE_ROW_RE = re.compile(r"^\|.+\|$")
_SEPARATOR_ROW_RE = re.compile(r"^\|[\s:|-]+\|$")

# ── Backtick extraction ───────────────────────────────────────────────

_BACKTICK_RE = re.compile(r"`([^`]+)`")

# Patterns that indicate backtick content is code, not a package name
_CODE_IDENTIFIER_RE = re.compile(
    r"_"  # underscores = code identifier
    r"|/"  # slashes = file path (but allow @scope/name)
    r"|\.(?:ts|js|tsx|jsx|json|yaml|yml|toml|css|html|md|py)$"
    r"|\(\)"  # function call
    r"|="  # assignment
    r"|^\d"  # starts with digit
    r"|[A-Z]",  # camelCase or PascalCase = code identifier
)

# ── Frontmatter detection ─────────────────────────────────────────────

_FRONTMATTER_FENCE = "---"


def _is_table_row(line: str) -> bool:
    """Return True if line is a markdown table row (not separator)."""
    stripped = line.strip()
    return bool(
        _TABLE_ROW_RE.match(stripped)
        and not _SEPARATOR_ROW_RE.match(stripped)
    )


def _find_version_near(text: str, pkg_end: int) -> str:
    """Look for a version hint near the package name position."""
    # Search in a window after the package name
    window = text[pkg_end : pkg_end + 30]
    match = VERSION_HINT_RE.search(window)
    if match:
        return match.group(0)
    return ""


def _extract_packages_from_text(
    text: str,
    *,
    source_spec: str,
    line_number: int,
    in_table: bool,
    in_backticks: bool,
) -> list[PackageRef]:
    """Extract package references from a text fragment."""
    refs: list[PackageRef] = []
    seen_in_line: set[str] = set()

    # Scoped packages (@scope/name)
    for match in SCOPED_PKG_RE.finditer(text):
        name = match.group(0)
        if name in seen_in_line:
            continue
        # Skip internal workspace packages (@repo/*)
        if name.startswith("@repo/"):
            continue
        seen_in_line.add(name)
        version = _find_version_near(text, match.end())
        refs.append(PackageRef(
            name=name,
            version_hint=version,
            source_spec=source_spec,
            in_table=in_table,
            in_backticks=in_backticks,
            line_number=line_number,
        ))

    # Unscoped packages: only accept known package names.
    # Hyphenated words are too common in English prose to accept
    # based solely on backtick/table context.
    for match in UNSCOPED_PKG_RE.finditer(text):
        name = match.group(0)
        if name in seen_in_line:
            continue
        if name not in KNOWN_PACKAGES:
            continue
        seen_in_line.add(name)
        version = _find_version_near(text, match.end())
        refs.append(PackageRef(
            name=name,
            version_hint=version,
            source_spec=source_spec,
            in_table=in_table,
            in_backticks=in_backticks,
            line_number=line_number,
        ))

    return refs


def _parse_file(path: Path) -> list[PackageRef]:
    """Parse a single spec file and extract all package references."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    filename = path.name
    refs: list[PackageRef] = []

    in_frontmatter = False
    frontmatter_count = 0
    in_failure_modes = False

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Skip frontmatter
        if stripped == _FRONTMATTER_FENCE:
            frontmatter_count += 1
            in_frontmatter = frontmatter_count == 1
            if frontmatter_count == 2:
                in_frontmatter = False
            continue
        if in_frontmatter:
            continue

        # Track sections — skip Failure Modes (describes error
        # scenarios, not actual dependencies)
        if stripped.startswith("## "):
            in_failure_modes = stripped == "## Failure Modes"
        if in_failure_modes:
            continue

        # Skip blank lines and heading markers
        if not stripped or stripped.startswith("#"):
            # Still check headings for backtick content
            pass

        is_table = _is_table_row(stripped)

        # Skip lines in negation context:
        # - "equals 0" on current or next line (multi-line
        #   "count of X equals 0" patterns)
        # - "instead of" on current line only, and only outside
        #   tables (inside tables it describes fallback behavior)
        idx = line_num - 1  # 0-based index into lines
        fwd = lines[idx : idx + 2]
        if any(re.search(r"\bequals\s+0\b", w, re.I) for w in fwd):
            continue
        if not is_table and re.search(
            r"\binstead\s+of\b", stripped, re.I,
        ):
            continue

        # Extract from backtick-quoted text
        for bt_match in _BACKTICK_RE.finditer(stripped):
            bt_content = bt_match.group(1)
            # Skip backtick content that looks like code identifiers
            # (but allow scoped packages like @repo/ui)
            if (
                _CODE_IDENTIFIER_RE.search(bt_content)
                and not bt_content.startswith("@")
            ):
                continue
            refs.extend(_extract_packages_from_text(
                bt_content,
                source_spec=filename,
                line_number=line_num,
                in_table=is_table,
                in_backticks=True,
            ))

        # Extract from the full line (non-backtick context)
        # Remove backtick content first to avoid double-counting
        plain_text = _BACKTICK_RE.sub("", stripped)
        if plain_text.strip():
            refs.extend(_extract_packages_from_text(
                plain_text,
                source_spec=filename,
                line_number=line_num,
                in_table=is_table,
                in_backticks=False,
            ))

    return refs


def parse_directory(directory: Path) -> SDDM:
    """Scan all .md files in a directory tree and build the SDDM."""
    sddm = SDDM()
    md_files = sorted(directory.rglob("*.md"))

    for md_file in md_files:
        # Skip non-spec files (READMEs, ROADMAPs, REVIEWs)
        stem_upper = md_file.stem.upper()
        if stem_upper in ("README", "ROADMAP", "REVIEW", "CHANGELOG"):
            continue

        for ref in _parse_file(md_file):
            sddm.add(ref)

    return sddm

"""Manifest parser — reads dependencies.md into the SDDM."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PackageRef:
    """A single package entry from the dependency manifest."""

    name: str
    version: str
    ecosystem: str
    justification: str


@dataclass
class SDDM:
    """Spec-Derived Dependency Manifest."""

    unique_packages: dict[str, PackageRef] = field(
        default_factory=dict,
    )
    warnings: list[str] = field(default_factory=list)

    def add(self, ref: PackageRef) -> None:
        """Add a package reference. Warns on duplicates."""
        if ref.name in self.unique_packages:
            self.warnings.append(
                f"Duplicate package '{ref.name}' in manifest"
            )
            return
        self.unique_packages[ref.name] = ref


# ── Table parsing ────────────────────────────────────────────────────

_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|$")


def _parse_table_row(line: str) -> list[str] | None:
    """Parse a markdown table row into cell values.

    Returns None if the line is not a table row or is a separator.
    """
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return None
    if _SEPARATOR_RE.match(stripped):
        return None
    cells = [c.strip() for c in stripped.split("|")]
    # split("|") produces empty strings at start/end
    return cells[1:-1]


def parse_manifest(path: Path) -> SDDM:
    """Parse a dependencies.md manifest file into an SDDM."""
    sddm = SDDM()

    if not path.exists():
        sddm.warnings.append(
            f"Manifest not found: {path.as_posix()}"
        )
        return sddm

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    header_found = False
    col_map: dict[str, int] = {}

    for line_num, line in enumerate(lines, start=1):
        cells = _parse_table_row(line)
        if cells is None:
            continue

        # First table row = header
        if not header_found:
            header_found = True
            for i, cell in enumerate(cells):
                col_map[cell.lower()] = i
            # Validate required columns
            required = {"package", "version", "ecosystem"}
            missing = required - set(col_map)
            if missing:
                sddm.warnings.append(
                    f"Missing columns: {', '.join(sorted(missing))}"
                )
                return sddm
            continue

        # Data row
        pkg_idx = col_map.get("package", 0)
        ver_idx = col_map.get("version", 1)
        eco_idx = col_map.get("ecosystem", 2)
        jst_idx = col_map.get("justification", -1)

        if len(cells) <= max(pkg_idx, ver_idx, eco_idx):
            sddm.warnings.append(
                f"Line {line_num}: too few columns"
            )
            continue

        name = cells[pkg_idx].strip("`")
        version = cells[ver_idx]
        ecosystem = cells[eco_idx]
        justification = (
            cells[jst_idx] if jst_idx >= 0 and jst_idx < len(cells)
            else ""
        )

        if not name:
            sddm.warnings.append(
                f"Line {line_num}: empty package name"
            )
            continue

        ref = PackageRef(
            name=name,
            version=version,
            ecosystem=ecosystem,
            justification=justification,
        )
        sddm.add(ref)

    if not header_found:
        sddm.warnings.append("No table found in manifest")

    # Print warnings to stderr
    for warning in sddm.warnings:
        print(f"  warning: {warning}", file=sys.stderr)

    return sddm


# ── Spec cross-validation ────────────────────────────────────────────

# Scoped packages are unambiguous: @scope/name
_SCOPED_RE = re.compile(r"@[a-z][a-z0-9._-]*/[a-z][a-z0-9._-]*[a-z0-9]")

_FRONTMATTER_FENCE = "---"


def _is_negation_line(line: str) -> bool:
    """Return True if a line mentions a package in negation context."""
    lower = line.lower()
    return (
        "equals 0" in lower
        or "pnpm dlx" in lower
        or "npx " in lower
        or "instead of" in lower
    )


def scan_unlisted_packages(
    spec_dir: Path, manifest_names: set[str],
) -> list[tuple[str, str, int]]:
    """Scan specs for package references not in the manifest.

    Returns list of (package_name, spec_filename, line_number)
    for packages found in spec prose that are absent from the
    manifest. Only detects scoped packages (@scope/name). Skips
    negation contexts and Failure Modes sections.
    """
    unlisted: list[tuple[str, str, int]] = []

    md_files = sorted(spec_dir.rglob("*.md"))
    for md_file in md_files:
        stem_upper = md_file.stem.upper()
        if stem_upper in (
            "README", "ROADMAP", "REVIEW", "CHANGELOG",
            "DEPENDENCIES",
        ):
            continue

        text = md_file.read_text(encoding="utf-8")
        lines = text.split("\n")
        seen_in_file: set[str] = set()

        in_frontmatter = False
        fm_count = 0
        in_failure_modes = False

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # Skip frontmatter
            if stripped == _FRONTMATTER_FENCE:
                fm_count += 1
                in_frontmatter = fm_count == 1
                if fm_count == 2:
                    in_frontmatter = False
                continue
            if in_frontmatter:
                continue

            # Track sections — skip Failure Modes
            if stripped.startswith("## "):
                in_failure_modes = stripped == "## Failure Modes"
            if in_failure_modes:
                continue

            # Skip negation context (current + next line)
            idx = line_num - 1
            fwd = lines[idx : idx + 2]
            if any(_is_negation_line(w) for w in fwd):
                continue

            # Scoped packages
            for m in _SCOPED_RE.finditer(stripped):
                name = m.group(0)
                if name.startswith("@repo/"):
                    continue
                if name in seen_in_file:
                    continue
                seen_in_file.add(name)
                if name not in manifest_names:
                    unlisted.append(
                        (name, md_file.name, line_num),
                    )

    return unlisted

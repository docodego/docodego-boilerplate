"""Extraction helpers — constants, HTTP statuses, tables."""

from __future__ import annotations

import re

from .anti_gaming import TIME_UNITS
from .types import (
    ExtractedConstant,
    HttpStatusMention,
    PermissionRow,
    StateTransition,
)

# ── Constant extraction patterns ──────────────────────────────────────

# Time pattern: "N seconds/minutes/hours/days"
_TIME_RE = re.compile(
    r"(\d[\d,]*(?:\.\d+)?)\s*[-\s]?"
    r"(seconds?|secs?|minutes?|mins?|hours?|hrs?|days?|weeks?)\b",
    re.I,
)

# Count pattern: "N retries/attempts/digits/characters"
_COUNT_RE = re.compile(
    r"(\d[\d,]*)\s*[-\s]?"
    r"(retries|retry|attempts?|digits?|characters?|chars?|items?|"
    r"options?|entries|members?|sessions?|records?|rows?|"
    r"bytes?|kb|mb|gb|pixels?|px)\b",
    re.I,
)

# Named constant: "exactly/maximum/minimum/at most/up to N"
_NAMED_RE = re.compile(
    r"(exactly|maximum|minimum|at\s+most|at\s+least|up\s+to|"
    r"no\s+more\s+than|no\s+fewer\s+than)\s+(\d[\d,]*(?:\.\d+)?)",
    re.I,
)

# HTTP status code pattern with context
_HTTP_STATUS_RE = re.compile(
    r"\b(HTTP\s+)?([1-5]\d{2})\b",
)

# ── Table parsing ─────────────────────────────────────────────────────

_TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
_TABLE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|$")


# ── Table parsing helpers ─────────────────────────────────────────────


def parse_table_rows(
    content_lines: list[str],
) -> list[list[str]]:
    """Parse markdown table rows into lists of cell values.

    Skips the header separator row. Returns all data rows.
    """
    rows: list[list[str]] = []
    header_found = False
    separator_found = False

    for line in content_lines:
        stripped = line.strip()
        if not _TABLE_ROW_RE.match(stripped):
            if header_found and separator_found and rows:
                break
            continue

        if _TABLE_SEP_RE.match(stripped):
            separator_found = True
            continue

        if not header_found:
            header_found = True
            cells = [
                c.strip() for c in stripped.strip("|").split("|")
            ]
            rows.append(cells)
            continue

        if separator_found:
            cells = [
                c.strip() for c in stripped.strip("|").split("|")
            ]
            rows.append(cells)

    return rows


def parse_permission_table(
    content_lines: list[str], spec_name: str,
) -> list[PermissionRow]:
    """Parse Permission Model table into PermissionRow objects."""
    rows = parse_table_rows(content_lines)
    if len(rows) < 2:
        return []

    result: list[PermissionRow] = []
    for row in rows[1:]:  # skip header
        if len(row) < 3:
            continue
        role = row[0].strip()
        permitted = row[1].strip()
        denied = row[2].strip()

        if permitted and permitted.lower() != "none":
            result.append(PermissionRow(
                role=role,
                action=permitted,
                allowed=True,
                spec_name=spec_name,
            ))
        if denied and denied.lower() != "none":
            result.append(PermissionRow(
                role=role,
                action=denied,
                allowed=False,
                spec_name=spec_name,
            ))

    return result


def parse_state_machine_table(
    content_lines: list[str], spec_name: str,
) -> list[StateTransition]:
    """Parse State Machine table into StateTransition objects."""
    rows = parse_table_rows(content_lines)
    if len(rows) < 2:
        return []

    result: list[StateTransition] = []
    for row in rows[1:]:  # skip header
        if len(row) < 3:
            continue
        from_state = row[0].strip().lower().replace(" ", "_")
        to_state = row[1].strip().lower().replace(" ", "_")
        trigger = row[2].strip() if len(row) > 2 else ""
        guard = row[3].strip() if len(row) > 3 else ""

        if from_state and to_state:
            result.append(StateTransition(
                from_state=from_state,
                to_state=to_state,
                trigger=trigger,
                guard=guard,
                spec_name=spec_name,
            ))

    return result


# ── Constant extraction ───────────────────────────────────────────────


def _get_context_window(
    lines: list[str], line_idx: int, window: int = 25,
) -> str:
    """Get a word-based context window around a given line.

    Uses ±1 line to keep context tight and avoid bleeding keywords
    from unrelated paragraphs into the classification window.
    """
    start = max(0, line_idx - 1)
    end = min(len(lines), line_idx + 2)
    text = " ".join(lines[start:end])
    words = text.split()
    if len(words) <= window:
        return " ".join(words)
    mid = len(words) // 2
    half = window // 2
    s = max(0, mid - half)
    e = min(len(words), s + window)
    return " ".join(words[s:e])


def _normalize_number(raw: str) -> float:
    """Parse a number string, stripping commas."""
    return float(raw.replace(",", ""))


def extract_constants_from_text(
    text: str,
    base_line: int,
    spec_name: str,
    lines_for_context: list[str],
) -> list[ExtractedConstant]:
    """Extract numeric constants from a section's text."""
    results: list[ExtractedConstant] = []
    text_lines = text.split("\n")

    for local_idx, line in enumerate(text_lines):
        abs_line = base_line + local_idx

        for m in _TIME_RE.finditer(line):
            value = _normalize_number(m.group(1))
            unit = m.group(2).lower()
            multiplier = TIME_UNITS.get(unit, 1)
            ctx = _get_context_window(
                lines_for_context, abs_line,
            )
            results.append(ExtractedConstant(
                value=value,
                unit=unit,
                normalized_seconds=value * multiplier,
                context=ctx,
                line_num=abs_line + 1,
                spec_name=spec_name,
            ))

        for m in _COUNT_RE.finditer(line):
            value = _normalize_number(m.group(1))
            unit = m.group(2).lower()
            ctx = _get_context_window(
                lines_for_context, abs_line,
            )
            results.append(ExtractedConstant(
                value=value,
                unit=unit,
                normalized_seconds=None,
                context=ctx,
                line_num=abs_line + 1,
                spec_name=spec_name,
            ))

        for m in _NAMED_RE.finditer(line):
            value = _normalize_number(m.group(2))
            qualifier = m.group(1).lower().strip()
            ctx = _get_context_window(
                lines_for_context, abs_line,
            )
            results.append(ExtractedConstant(
                value=value,
                unit=qualifier,
                normalized_seconds=None,
                context=ctx,
                line_num=abs_line + 1,
                spec_name=spec_name,
            ))

    return results


# ── HTTP status extraction ────────────────────────────────────────────


def extract_http_statuses(
    lines: list[str], spec_name: str,
) -> list[HttpStatusMention]:
    """Find all HTTP status code mentions with 30-word context."""
    results: list[HttpStatusMention] = []
    for i, line in enumerate(lines):
        for m in _HTTP_STATUS_RE.finditer(line):
            code = int(m.group(2))
            if code < 100 or code > 599:
                continue
            # 30-word context window
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            text = " ".join(lines[start:end])
            words = text.split()
            if len(words) > 30:
                mid = len(words) // 2
                s = max(0, mid - 15)
                words = words[s:s + 30]
            context = " ".join(words)
            results.append(HttpStatusMention(
                code=code,
                context=context,
                spec_name=spec_name,
                line_num=i + 1,
            ))

    return results

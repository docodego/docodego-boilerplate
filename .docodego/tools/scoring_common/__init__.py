"""Shared infrastructure for all DoCoDeGo scoring tools."""

from __future__ import annotations

import os
from pathlib import Path

from scoring_common.audit import write_audit
from scoring_common.cli import add_common_args
from scoring_common.reporter import (
    bar,
    dim_to_dict,
    format_json,
    format_text,
    result_to_dict,
)
from scoring_common.types import DimensionResult

__all__ = [
    "DimensionResult",
    "add_common_args",
    "bar",
    "dim_to_dict",
    "fix_encoding",
    "format_json",
    "format_text",
    "load_dotenv",
    "result_to_dict",
    "write_audit",
]

# tools.env lives at the tools/ root (parent of scoring_common/)
_DOTENV_PATH = Path(__file__).resolve().parent.parent / "tools.env"


def load_dotenv() -> None:
    """Load .env from the tools directory. Existing env vars take priority."""
    if not _DOTENV_PATH.exists():
        return
    for line in _DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


def fix_encoding() -> None:
    """Fix Windows cp1252 encoding crash when printing Unicode."""
    import io
    import sys

    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer, encoding="utf-8", errors="replace",
        )
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer, encoding="utf-8", errors="replace",
        )

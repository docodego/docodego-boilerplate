"""Shared CLI argument definitions for all scoring tools."""

from __future__ import annotations

import argparse


def add_common_args(parser: argparse.ArgumentParser) -> None:
    """Add --threshold, --format, --no-zero-veto, --audits to *parser*."""
    parser.add_argument(
        "--threshold",
        type=int,
        default=60,
        help="Minimum score to pass (default: 60)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-zero-veto",
        action="store_true",
        help="Disable zero-dimension veto",
    )
    parser.add_argument(
        "--audits",
        type=str,
        default=None,
        help="Write audit JSON to this directory (or set DOCODEGO_CYCLE)",
    )

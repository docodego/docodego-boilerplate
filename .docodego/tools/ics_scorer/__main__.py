"""CLI entry point for ICS Scorer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .parser import parse_spec
from .reporter import format_json, format_text
from .scorer import score_spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ics-scorer",
        description="DoCoDeGo ICS Scorer — score specification quality against the Intent Clarity Score rubric.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Markdown spec file(s) to score",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=60,
        help="Minimum ICS score to pass (default: 60)",
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
        help="Disable zero-dimension veto (allow passing with a zero score on one dimension)",
    )
    parser.add_argument(
        "--threat-floor",
        type=int,
        default=15,
        help="Minimum Threat Coverage score (default: 15)",
    )

    args = parser.parse_args(argv)

    any_failed = False

    for filepath in args.files:
        path = Path(filepath)
        if not path.exists():
            print(f"Error: file not found: {filepath}", file=sys.stderr)
            any_failed = True
            continue

        markdown = path.read_text(encoding="utf-8")
        spec = parse_spec(markdown)
        result = score_spec(
            spec,
            threshold=args.threshold,
            threat_floor=args.threat_floor,
            fail_on_zero_dimension=not args.no_zero_veto,
        )

        if args.format == "json":
            print(format_json(result, filename=str(path), threshold=args.threshold))
        else:
            print(format_text(result, filename=str(path), threshold=args.threshold))

        if not result.approved:
            any_failed = True

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())

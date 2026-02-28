"""CLI entry point for ICS Scorer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scoring_common import add_common_args, fix_encoding, load_dotenv

fix_encoding()
load_dotenv()

from scoring_common.audit import resolve_audit_dir, write_audit

from .parser import parse_spec
from .reporter import TOOL_KEY, _result_to_dict, format_json, format_text
from .scorer import score_spec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ics-scorer",
        description=(
            "DoCoDeGo ICS Scorer — score specification quality "
            "against the Intent Clarity Score rubric."
        ),
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Markdown spec file(s) to score",
    )
    add_common_args(parser)
    parser.add_argument(
        "--threat-floor",
        type=int,
        default=15,
        help="Minimum Threat Coverage score (default: 15)",
    )

    args = parser.parse_args(argv)
    audit_dir = resolve_audit_dir(args.audits)
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

        display_path = path.as_posix()

        if audit_dir:
            tool_dict = _result_to_dict(result, threshold=args.threshold)
            audit_file = write_audit(
                audit_dir, path, TOOL_KEY, tool_dict, display_path,
            )
            print(f"  {TOOL_KEY}: {result.total}/100  {audit_file.as_posix()}")
        elif args.format == "json":
            print(format_json(result, filename=display_path, threshold=args.threshold))
        else:
            print(format_text(result, filename=display_path, threshold=args.threshold))

        if not result.approved:
            any_failed = True

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())

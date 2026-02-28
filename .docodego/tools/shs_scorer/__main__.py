"""CLI entry point for SHS Scorer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scoring_common import add_common_args, fix_encoding, load_dotenv

fix_encoding()
load_dotenv()

from scoring_common.audit import resolve_audit_dir, write_audit

from .parser import collect_specs
from .reporter import TOOL_KEY, _result_to_dict, format_json, format_text
from .scorer import score_corpus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="shs-scorer",
        description=(
            "DoCoDeGo SHS Scorer — score spec corpus health "
            "against the Spec Health Score rubric."
        ),
    )
    parser.add_argument(
        "directory",
        help="Directory containing spec files to check",
    )
    parser.add_argument(
        "--flows",
        default=None,
        help="Optional flows directory for coverage check",
    )
    parser.add_argument(
        "--line-limit",
        type=int,
        default=500,
        help="Maximum lines per spec (default: 500)",
    )
    parser.add_argument(
        "--data-heavy-limit",
        type=int,
        default=650,
        help="Maximum lines for specs with 3+ tables (default: 650)",
    )
    add_common_args(parser)

    args = parser.parse_args(argv)
    spec_dir = Path(args.directory)

    if not spec_dir.is_dir():
        print(
            f"Error: directory not found: {args.directory}",
            file=sys.stderr,
        )
        return 1

    flows_dir = Path(args.flows) if args.flows else None
    if flows_dir and not flows_dir.is_dir():
        print(
            f"Warning: flows directory not found: {args.flows}, "
            f"skipping flow coverage check",
            file=sys.stderr,
        )
        flows_dir = None

    specs = collect_specs(spec_dir)
    if not specs:
        print(
            f"Error: no spec files found in {args.directory}",
            file=sys.stderr,
        )
        return 1

    result = score_corpus(
        specs,
        threshold=args.threshold,
        line_limit=args.line_limit,
        data_heavy_limit=args.data_heavy_limit,
        flows_dir=flows_dir,
        fail_on_zero_dimension=not args.no_zero_veto,
    )

    display_path = spec_dir.as_posix()
    audit_dir = resolve_audit_dir(args.audits)

    if audit_dir:
        tool_dict = _result_to_dict(result, threshold=args.threshold)
        # Use a synthetic path for the corpus audit
        corpus_path = spec_dir / "_corpus"
        audit_file = write_audit(
            audit_dir, corpus_path, TOOL_KEY, tool_dict, display_path,
        )
        print(
            f"  {TOOL_KEY}: {result.total}/100  "
            f"{audit_file.as_posix()}"
        )
    elif args.format == "json":
        print(
            format_json(
                result, filename=display_path, threshold=args.threshold,
            )
        )
    else:
        print(
            format_text(
                result, filename=display_path, threshold=args.threshold,
            )
        )

    return 1 if not result.approved else 0


if __name__ == "__main__":
    sys.exit(main())

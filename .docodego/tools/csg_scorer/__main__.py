"""CLI entry point for CSG Scorer — directory-based corpus analysis."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scoring_common import fix_encoding, load_dotenv

fix_encoding()
load_dotenv()

from scoring_common.audit import resolve_audit_dir, write_audit

from .parser import parse_spec
from .reporter import TOOL_KEY, _result_to_dict, format_json, format_text
from .scorer import score_corpus


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="csg-scorer",
        description=(
            "DoCoDeGo CSG Scorer — Constraint Symmetry Guard. "
            "Detects contradictions between specs that share "
            "business rules, constants, or permissions."
        ),
    )
    parser.add_argument(
        "directory",
        help="Directory containing spec files to check",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=60,
        help="Minimum CSG score to pass (default: 60)",
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
        help=(
            "Write audit JSON to this directory "
            "(or set DOCODEGO_AUDITS)"
        ),
    )

    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(
            f"Error: directory not found: {args.directory}",
            file=sys.stderr,
        )
        return 1

    # Walk directory for .md files
    md_files = sorted(directory.glob("**/*.md"))
    if not md_files:
        print(
            f"Error: no .md files found in {args.directory}",
            file=sys.stderr,
        )
        return 1

    # Parse all specs
    specs = []
    for filepath in md_files:
        spec = parse_spec(filepath)
        specs.append(spec)

    # Score the corpus
    result = score_corpus(
        specs,
        threshold=args.threshold,
        fail_on_zero_dimension=not args.no_zero_veto,
    )

    display_path = directory.as_posix()

    # Audit output
    audit_dir = resolve_audit_dir(args.audits)
    if audit_dir:
        tool_dict = _result_to_dict(result, threshold=args.threshold)
        # Use _corpus as the "spec" identifier for audit
        corpus_path = directory / "_corpus"
        audit_file = write_audit(
            audit_dir,
            corpus_path,
            TOOL_KEY,
            tool_dict,
            display_path,
        )
        print(
            f"  {TOOL_KEY}: {result.total}/100  "
            f"{audit_file.as_posix()}",
        )
    elif args.format == "json":
        print(format_json(
            result,
            filename=display_path,
            threshold=args.threshold,
        ))
    else:
        print(format_text(
            result,
            filename=display_path,
            threshold=args.threshold,
        ))

    return 1 if not result.approved else 0


if __name__ == "__main__":
    sys.exit(main())

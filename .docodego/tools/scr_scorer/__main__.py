"""CLI entry point for SCR Scorer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scoring_common import add_common_args, fix_encoding, load_dotenv

fix_encoding()
load_dotenv()

from scoring_common.audit import resolve_audit_dir, write_audit

from .parser import parse_manifest
from .reporter import TOOL_KEY, _result_to_dict, format_json, format_text
from .scorer import score_corpus


def _resolve_manifest(
    directory: Path, explicit: str | None,
) -> Path | None:
    """Resolve the dependency manifest path.

    Priority:
    1. Explicit --manifest flag
    2. Parent directory (for group dirs like behavioral/)
    3. Same directory (if invoked on specs root)
    """
    if explicit:
        p = Path(explicit)
        if p.exists():
            return p
        return None

    # Parent: <directory>/../dependencies.md
    parent = directory.parent / "dependencies.md"
    if parent.exists():
        return parent

    # Same dir: <directory>/dependencies.md
    same = directory / "dependencies.md"
    if same.exists():
        return same

    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scr-scorer",
        description=(
            "DoCoDeGo SCR Scorer -- score supply chain risk "
            "from a dependency manifest."
        ),
    )
    parser.add_argument(
        "directory",
        help="Spec group directory (used for audit path)",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help=(
            "Path to dependencies.md manifest "
            "(auto-resolved from directory if omitted)"
        ),
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        default=False,
        help="Skip network queries (live is default)",
    )
    add_common_args(parser)

    args = parser.parse_args(argv)

    directory = Path(args.directory)
    if not directory.is_dir():
        print(
            f"Error: directory not found: {args.directory}",
            file=sys.stderr,
        )
        return 1

    # Resolve manifest
    manifest_path = _resolve_manifest(directory, args.manifest)
    if manifest_path is None:
        print(
            "Error: dependencies.md manifest not found. "
            "Use --manifest to specify the path.",
            file=sys.stderr,
        )
        return 1

    # Parse manifest into SDDM
    sddm = parse_manifest(manifest_path)

    # Score the corpus
    result = score_corpus(
        sddm,
        offline=args.offline,
        threshold=args.threshold,
        fail_on_zero_dimension=not args.no_zero_veto,
        spec_dir=directory,
    )

    display_path = directory.as_posix()

    audit_dir = resolve_audit_dir(args.audits)
    if audit_dir:
        tool_dict = _result_to_dict(result, threshold=args.threshold)
        # Use a synthetic _corpus path for the audit file
        corpus_path = directory / "_corpus.md"
        audit_file = write_audit(
            audit_dir, corpus_path, TOOL_KEY, tool_dict, display_path,
        )
        print(
            f"  {TOOL_KEY}: {result.total}/100  "
            f"{audit_file.as_posix()}",
        )
    elif args.format == "json":
        print(format_json(
            result, filename=display_path, threshold=args.threshold,
        ))
    else:
        print(format_text(
            result, filename=display_path, threshold=args.threshold,
        ))

    return 1 if not result.approved else 0


if __name__ == "__main__":
    sys.exit(main())

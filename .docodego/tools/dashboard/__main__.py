"""CLI entry point: load audit JSONs, inject into HTML template."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from scoring_common import fix_encoding

from dashboard.loader import (
    TOOL_INFO,
    TOOL_ORDER,
    compute_stats,
    load_audits,
)

TEMPLATE = Path(__file__).parent / "template.html"
DATA_MARKER = "/*__DATA__*/null"


def main() -> None:
    """Generate HTML dashboard from audit JSON files."""
    if len(sys.argv) < 2:
        print(
            "Usage: .docodego/tools/run dashboard <audits-dir> [out.html]",
            file=sys.stderr,
        )
        sys.exit(1)

    audit_dir = Path(sys.argv[1])
    if not audit_dir.is_dir():
        print(f"Not a directory: {audit_dir}", file=sys.stderr)
        sys.exit(1)

    output = Path(sys.argv[2]) if len(sys.argv) > 2 else (
        audit_dir / "dashboard.html"
    )

    per_spec, corpus = load_audits(audit_dir)
    if not per_spec and not corpus:
        print("No audit files found.", file=sys.stderr)
        sys.exit(1)

    stats = compute_stats(per_spec, corpus)
    timestamps = [
        s.get("timestamp", "")
        for s in per_spec + corpus
        if s.get("timestamp")
    ]

    data = {
        "specs": per_spec,
        "corpus": corpus,
        "stats": stats,
        "meta": {
            "timestamp": max(timestamps) if timestamps else "unknown",
            "tools": TOOL_INFO,
            "toolOrder": TOOL_ORDER,
        },
    }

    template = TEMPLATE.read_text(encoding="utf-8")
    html = template.replace(DATA_MARKER, json.dumps(data))
    output.write_text(html, encoding="utf-8")

    print(f"Dashboard written to {output}")
    n = sum(len(s) for s in stats["toolScores"].values())
    print(f"  {stats['totalSpecs']} specs, "
          f"{stats['totalCorpus']} corpus, {n} tool runs")


if __name__ == "__main__":
    fix_encoding()
    main()

"""Single-process audit runner with threaded parallelism."""

from __future__ import annotations

import glob
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scoring_common import fix_encoding, load_dotenv

fix_encoding()
load_dotenv()

# ── Scoring rules per spec group ─────────────────────────────────────
# Maps directory name → which per-file and corpus scorers to run.
# Per-file: ics, ccs, sds.  Corpus: csg, shs, scr.

GROUP_RULES: dict[str, dict[str, list[str]]] = {
    "behavioral": {
        "per_file": ["ics", "sds"],
        "corpus": ["csg", "shs", "scr"],
    },
    "foundation": {
        "per_file": ["ics", "sds"],
        "corpus": ["shs", "scr"],
    },
    "conventions": {
        "per_file": ["ccs"],
        "corpus": [],
    },
}


def _md_files(directory: str) -> list[str]:
    return sorted(glob.glob(f"{directory}/*.md"))


def _resolve_paths() -> tuple[Path, Path]:
    """Derive specs and audits dirs from DOCODEGO_CYCLE."""
    cycle_env = os.environ.get("DOCODEGO_CYCLE", "")

    if not cycle_env:
        print(
            "Error: set DOCODEGO_CYCLE (or configure tools.env)",
            file=sys.stderr,
        )
        sys.exit(1)

    cycle = Path(cycle_env)
    specs = cycle / "output" / "specs"
    audits = cycle / "audits"

    if not specs.is_dir():
        print(f"Error: specs dir not found: {specs}", file=sys.stderr)
        sys.exit(1)

    return specs, audits


def main() -> None:
    start = time.perf_counter()
    specs_dir, audits_dir = _resolve_paths()

    # Lazy imports — all scorers loaded once
    from ics_scorer.__main__ import main as ics_main
    from ccs_scorer.__main__ import main as ccs_main
    from sds_scorer.__main__ import main as sds_main
    from csg_scorer.__main__ import main as csg_main
    from shs_scorer.__main__ import main as shs_main
    from scr_scorer.__main__ import main as scr_main
    from dashboard.__main__ import main as dash_main

    scorers = {
        "ics": ics_main, "ccs": ccs_main, "sds": sds_main,
        "csg": csg_main, "shs": shs_main, "scr": scr_main,
    }

    # Discover spec groups present on disk
    groups = {
        d.name: d for d in sorted(specs_dir.iterdir())
        if d.is_dir() and d.name in GROUP_RULES
    }

    # Phase 1: per-file scorers in parallel
    per_file_tasks: list[tuple[str, list[str]]] = []
    for gname, gdir in groups.items():
        files = _md_files(str(gdir))
        if not files:
            continue
        for tool in GROUP_RULES[gname]["per_file"]:
            per_file_tasks.append((tool, files))

    if per_file_tasks:
        print("=== Per-file scorers ===")
        with ThreadPoolExecutor(max_workers=len(per_file_tasks)) as pool:
            for tool, files in per_file_tasks:
                pool.submit(scorers[tool], files)

    # Phase 2: corpus scorers in parallel
    corpus_tasks: list[tuple[str, str]] = []
    for gname, gdir in groups.items():
        for tool in GROUP_RULES[gname]["corpus"]:
            corpus_tasks.append((tool, str(gdir)))

    if corpus_tasks:
        print("\n=== Corpus scorers ===")
        with ThreadPoolExecutor(max_workers=len(corpus_tasks)) as pool:
            for tool, directory in corpus_tasks:
                pool.submit(scorers[tool], [directory])

    # Phase 3: dashboard
    print("\n=== Dashboard ===")
    saved_argv = sys.argv
    sys.argv = ["dashboard", str(audits_dir)]
    dash_main()
    sys.argv = saved_argv

    elapsed = time.perf_counter() - start
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()

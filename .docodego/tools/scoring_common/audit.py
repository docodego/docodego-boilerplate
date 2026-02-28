"""Audit file I/O — merge tool results into .audit.json files."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Environment variable for the default audits directory.
# CLI --audits flag overrides this.
AUDITS_ENV_VAR = "DOCODEGO_AUDITS"


def resolve_audit_dir(cli_value: str | None) -> Path | None:
    """Return the audit directory from CLI flag or env var.

    Priority: --audits flag > DOCODEGO_AUDITS env var > None.
    """
    if cli_value:
        return Path(cli_value)
    env = os.environ.get(AUDITS_ENV_VAR)
    if env:
        return Path(env)
    return None


def write_audit(
    audit_dir: Path,
    spec_path: Path,
    tool_key: str,
    tool_dict: dict[str, Any],
    display_path: str,
) -> Path:
    """Merge tool result into the audit file, preserving other tools' data.

    Writes to: <audit_dir>/<parent_dir>/<stem>.audit.json
    Example:   audits/foundation/api-framework.audit.json
    """
    audit_file = (
        audit_dir / spec_path.parent.name / f"{spec_path.stem}.audit.json"
    )
    audit_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing audit data if present (preserves other tools' results)
    if audit_file.exists():
        existing: dict[str, Any] = json.loads(
            audit_file.read_text(encoding="utf-8"),
        )
    else:
        existing = {"spec": display_path, "tools": {}}

    existing["timestamp"] = datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ",
    )
    existing["tools"][tool_key] = tool_dict
    audit_file.write_text(
        json.dumps(existing, indent=2) + "\n", encoding="utf-8",
    )
    return audit_file

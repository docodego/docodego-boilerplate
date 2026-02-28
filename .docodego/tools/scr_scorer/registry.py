"""HTTP clients for OSV and npm registry APIs with disk cache."""

from __future__ import annotations

import hashlib
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────

TIMEOUT = 5  # seconds per request
OSV_URL = "https://api.osv.dev/v1/query"
NPM_URL = "https://registry.npmjs.org"

# Disk cache: .docodego/tools/.cache/<source>/<key>.json
# TTL: npm 24h, osv 6h (vulnerabilities change more often)
_CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"
NPM_TTL_HOURS = 24
OSV_TTL_HOURS = 6

# In-memory cache for npm responses (shared across dimensions)
_npm_cache: dict[str, dict | None] = {}


# ── Disk cache ────────────────────────────────────────────────────────


def _cache_key(source: str, name: str) -> Path:
    """Return the cache file path for a given source + package name."""
    safe = hashlib.sha256(name.encode()).hexdigest()[:16]
    return _CACHE_DIR / source / f"{safe}.json"


def _read_cache(path: Path, ttl_hours: int) -> dict | None:
    """Read a cached JSON file if it exists and is fresh."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        ts = data.get("_cached_at", "")
        if not ts:
            return None
        cached_at = datetime.fromisoformat(ts)
        age_hours = (
            datetime.now(timezone.utc) - cached_at
        ).total_seconds() / 3600
        if age_hours > ttl_hours:
            return None
        return data.get("payload")
    except (json.JSONDecodeError, ValueError, OSError):
        return None


def _write_cache(path: Path, payload: object) -> None:
    """Write a JSON payload to the cache."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "_cached_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        path.write_text(
            json.dumps(data, separators=(",", ":")),
            encoding="utf-8",
        )
    except OSError:
        pass  # cache write failure is non-fatal


# ── Low-level fetch ───────────────────────────────────────────────────


def _fetch_json(
    url: str,
    *,
    body: dict | None = None,
    timeout: int = TIMEOUT,
) -> dict | None:
    """Fetch JSON from a URL. Returns None on any error."""
    try:
        if body is not None:
            data = json.dumps(body).encode()
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
            )
        else:
            req = urllib.request.Request(url)

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
    ):
        return None


# ── OSV API ───────────────────────────────────────────────────────────


def query_osv(name: str) -> list[dict]:
    """Query OSV for vulnerabilities affecting a package.

    Returns a list of vulnerability objects, each with at least
    a 'severity' field. Returns [] on network error.
    Uses disk cache with 6h TTL.
    """
    cache_path = _cache_key("osv", name)
    cached = _read_cache(cache_path, OSV_TTL_HOURS)
    if cached is not None:
        return cached

    payload: dict = {
        "package": {"name": name, "ecosystem": "npm"},
    }
    result = _fetch_json(OSV_URL, body=payload)
    if result is None:
        return []
    vulns = result.get("vulns", [])
    _write_cache(cache_path, vulns)
    return vulns


def classify_severity(vuln: dict) -> str:
    """Extract the highest severity level from a vulnerability.

    Returns one of: CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN.
    """
    for sev in vuln.get("severity", []):
        score_str = sev.get("score", "")
        try:
            score = float(score_str)
        except (ValueError, TypeError):
            continue
        if score >= 9.0:
            return "CRITICAL"
        if score >= 7.0:
            return "HIGH"
        if score >= 4.0:
            return "MEDIUM"
        return "LOW"

    # Fallback: check database_specific or ecosystem severity
    db = vuln.get("database_specific", {})
    raw = db.get("severity", "").upper()
    if raw in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        return raw

    return "UNKNOWN"


# ── npm Registry ──────────────────────────────────────────────────────


def query_npm(name: str) -> dict | None:
    """Query npm registry for package metadata.

    Returns the registry response or None on error.
    Uses in-memory cache (per-run) + disk cache (24h TTL).
    """
    if name in _npm_cache:
        return _npm_cache[name]

    cache_path = _cache_key("npm", name)
    cached = _read_cache(cache_path, NPM_TTL_HOURS)
    if cached is not None:
        _npm_cache[name] = cached
        return cached

    # Scoped packages need URL encoding: @scope/name → @scope%2fname
    encoded = name.replace("/", "%2f")
    url = f"{NPM_URL}/{encoded}"
    result = _fetch_json(url)
    _npm_cache[name] = result
    if result is not None:
        _write_cache(cache_path, result)
    return result


def get_last_modified(npm_data: dict) -> datetime | None:
    """Extract last-modified timestamp from npm registry data."""
    time_map = npm_data.get("time", {})
    modified = time_map.get("modified")
    if not modified:
        return None
    try:
        return datetime.fromisoformat(
            modified.replace("Z", "+00:00"),
        )
    except (ValueError, TypeError):
        return None


def is_deprecated(npm_data: dict) -> bool:
    """Check if the latest version is deprecated."""
    dist_tags = npm_data.get("dist-tags", {})
    latest = dist_tags.get("latest", "")
    if not latest:
        return False
    versions = npm_data.get("versions", {})
    latest_meta = versions.get(latest, {})
    return bool(latest_meta.get("deprecated"))


def get_dep_count(npm_data: dict) -> int:
    """Count direct dependencies of the latest version."""
    dist_tags = npm_data.get("dist-tags", {})
    latest = dist_tags.get("latest", "")
    if not latest:
        return 0
    versions = npm_data.get("versions", {})
    latest_meta = versions.get(latest, {})
    deps = latest_meta.get("dependencies", {})
    return len(deps)

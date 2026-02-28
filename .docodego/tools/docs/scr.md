# SCR — Supply Chain Radar

> [All Tools](../README.md) · Status: **Implemented** (`scr_scorer/`)

## Purpose

Pre-code supply chain risk assessment. Extracts every package
and framework mentioned in specs, then evaluates maintenance
health, known vulnerabilities, and dependency depth — all before
a single package is installed.

Works on any markdown spec corpus. Extracts package names from
markdown tables and backtick-quoted references. Queries public
registries (npm, OSV) for live data — no hardcoded package
lists.

## Target Specs

Any spec corpus, scored as a directory. Live mode requires
network access.

## CLI

```bash
# Live mode — default (queries npm + OSV APIs)
.docodego/tools/run scr_scorer <directory>

# Offline mode (skips network, scores only spec content)
.docodego/tools/run scr_scorer --offline <directory>

# JSON output
.docodego/tools/run scr_scorer --format json <directory>

# Custom threshold (default is 60)
.docodego/tools/run scr_scorer --threshold 80 <directory>
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `directory` | *(required)* | Directory containing spec files to scan for package references |
| `--format` | `text` | Output format: `text` (human-readable) or `json` (structured) |
| `--threshold` | `60` | Minimum total score (out of 100) required to pass |
| `--offline` | off | Skip network queries; score only from spec content (live is default) |
| `--no-zero-veto` | off | Allow passing even if one dimension scores 0 |
| `--audits` | *(none)* | Write audit JSON to this directory (or set `DOCODEGO_AUDITS`) |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Corpus meets the threshold |
| `1` | Below threshold, zero-veto triggered, or directory not found |

## Input: SDDM

The Spec-Derived Dependency Manifest is auto-extracted by
scanning all specs for package references:

- Markdown table cells containing package names (detected by
  npm-like patterns: `@scope/name`, lowercase-with-hyphens)
- Backtick-quoted package names in prose
- Version hints where present (`v4`, `^2.0`, `>=1.5`)

Extracts: package name, version hint (if present), source spec.

## Dimensions (weighted, total = 100)

### 1. Known Vulnerability Exposure (0–40)

Do referenced packages have known CVEs? Weighted highest because
a single critical CVE can compromise the entire application.

- Queries OSV API (`api.osv.dev`) per package + version range
- Version-window analysis: checks advisories for the specific
  major version mentioned in specs, not just latest
- **Severity-weighted deduction:** critical −10, high −5,
  medium −2, low −1 from a starting 40
- A single critical CVE drops the score by 25% — this is
  intentional
- **Offline mode:** awards full score (40/40) since no
  vulnerabilities can be confirmed without network
- **Scoring:** `40 − deductions`, clamped to 0–40

### 2. Package Vitality (0–25)

Are the referenced packages actively maintained?

- Queries npm registry for each SDDM entry's `time.modified`
  field
- < 6 months since last publish → full marks
- 6–12 months → partial
- > 12 months or `deprecated` field present → 0 for that package
- `^0.x` version hints flagged as pre-stable
- **Offline mode:** awards neutral score (12/25) since vitality
  cannot be determined without network
- **Scoring:** 100% vital → 25, 90%+ → 20, 70%+ → 15, 50%+ → 10,
  else linear

### 3. Supply Chain Depth (0–20)

How deep are the transitive dependency trees?

- Queries npm registry for each package's `dependencies` field,
  recursively counts transitive deps (depth limit 5)
- **Blast radius ranking:** `transitive_count × (1 + critical_CVEs)`
  — top entry = biggest future exposure
- Packages with > 100 transitive deps get flagged; > 200 gets
  a suggestion to evaluate alternatives
- Known-heavy frameworks (detected by high dep count) are
  annotated rather than penalized
- **Offline mode:** awards neutral score (10/20)
- **Scoring:** starts at 20, −2 per package > 100 deps
  (known-heavy exempt), −1 per package > 50 deps, floor 0

### 4. SDDM Coverage (0–15)

Are package references well-documented in specs?

- Checks that every package in the SDDM appears with a version
  hint (not just a bare name)
- Checks that packages are referenced in a structured location
  (table cell, Integration Map) rather than only in prose
- Flags packages mentioned in only one spec with no version —
  potentially accidental or undecided dependencies
- Flags duplicate package names with conflicting version hints
  across specs
- **Scoring:** 100% well-documented → 15, 90%+ → 12, 70%+ → 9,
  50%+ → 6, else linear

## Gate Logic

Standard: zero-veto → threshold (default 60) → status bands.

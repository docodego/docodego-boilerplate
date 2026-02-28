# SCR — Supply Chain Radar

> [All Tools](../README.md) · Status: **Implemented** (`scr_scorer/`)

## Purpose

Pre-code supply chain risk assessment. Reads a `dependencies.md`
manifest listing every third-party package, then evaluates
maintenance health, known vulnerabilities, and dependency depth —
all before a single package is installed.

Works on any spec corpus that includes a `dependencies.md` manifest
in markdown table format.

## Target Specs

Any spec corpus, scored as a directory. The manifest is resolved
automatically from the group directory's parent. Live mode requires
network access.

## CLI

```bash
# Live mode — default (queries npm + OSV APIs)
.docodego/tools/run scr_scorer <directory>

# Offline mode (skips network, scores only manifest content)
.docodego/tools/run scr_scorer --offline <directory>

# Explicit manifest path
.docodego/tools/run scr_scorer --manifest path/to/dependencies.md <directory>

# JSON output
.docodego/tools/run scr_scorer --format json <directory>

# Custom threshold (default is 60)
.docodego/tools/run scr_scorer --threshold 80 <directory>
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `directory` | *(required)* | Spec group directory (used for audit path and manifest resolution) |
| `--manifest` | *(auto)* | Path to `dependencies.md` manifest (auto-resolved from parent dir if omitted) |
| `--format` | `text` | Output format: `text` (human-readable) or `json` (structured) |
| `--threshold` | `60` | Minimum total score (out of 100) required to pass |
| `--offline` | off | Skip network queries; score only from manifest content (live is default) |
| `--no-zero-veto` | off | Allow passing even if one dimension scores 0 |
| `--audits` | *(none)* | Write audit JSON to this directory (or set `DOCODEGO_CYCLE`) |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Corpus meets the threshold |
| `1` | Below threshold, zero-veto triggered, or manifest not found |

## Input: Dependency Manifest

The manifest is a `dependencies.md` file with a markdown table:

```markdown
| Package | Version | Ecosystem | Justification |
|---------|---------|-----------|---------------|
| hono | ^4 | npm | API framework on Cloudflare Workers |
| zod | ^4 | npm | Schema validation for API contracts |
```

**Required columns:** Package, Version, Ecosystem.
**Optional column:** Justification (improves coverage score).

Manifest resolution order:
1. Explicit `--manifest` path
2. `<directory>/../dependencies.md` (parent of group dir)
3. `<directory>/dependencies.md` (specs root)

## Dimensions (weighted, total = 100)

### 1. Known Vulnerability Exposure (0–40)

Do referenced packages have known CVEs? Weighted highest because
a single critical CVE can compromise the entire application.

- Queries OSV API (`api.osv.dev`) per package + version + ecosystem
- Version-aware: passes the manifest version to OSV for precise
  matching instead of querying all-time vulnerabilities
- **Severity-weighted deduction:** critical −10, high −5,
  medium −2, low −1 from a starting 40
- A single critical CVE drops the score by 25% — this is
  intentional
- **Offline mode:** awards full score (40/40) since no
  vulnerabilities can be confirmed without network
- **Scoring:** `40 − deductions`, clamped to 0–40

### 2. Package Vitality (0–25)

Are the referenced packages actively maintained?

- Queries npm registry for each package's `time.modified` field
- Skips non-npm ecosystem packages
- < 6 months since last publish → full marks
- 6–12 months → partial
- > 12 months or `deprecated` field present → 0 for that package
- **Offline mode:** awards neutral score (12/25) since vitality
  cannot be determined without network
- **Scoring:** 100% vital → 25, 90%+ → 20, 70%+ → 15, 50%+ → 10,
  else linear

### 3. Supply Chain Depth (0–20)

How deep are the transitive dependency trees?

- Queries npm registry for each package's `dependencies` count
- Skips non-npm ecosystem packages
- Packages with > 100 deps get flagged; known-heavy frameworks
  (expo, storybook, turbo) are exempt
- **Offline mode:** awards neutral score (10/20)
- **Scoring:** starts at 20, −2 per package > 100 deps
  (known-heavy exempt), −1 per package > 50 deps, floor 0

### 4. SDDM Coverage (0–15)

Is the dependency manifest complete and well-structured?

- Checks each entry for: pinned version (not "latest"),
  ecosystem specified, justification present
- Full entry (version + ecosystem + justification) → 1 point
- Partial entry (ecosystem + justification, no version) → 0.5
- Missing fields are flagged as issues
- Parse warnings (duplicates, malformed rows) count as issues
- **Cross-validation:** scoped packages (`@scope/name`) found
  in spec prose but absent from the manifest are flagged —
  negation contexts and Failure Modes sections are excluded
- **Scoring:** 100% complete → 15, 90%+ → 12, 70%+ → 9,
  50%+ → 6, else linear

## Gate Logic

Standard: zero-veto → threshold (default 60) → status bands.

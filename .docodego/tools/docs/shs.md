# SHS — Spec Health Score

> [All Tools](../README.md) · Status: **Implemented** (`shs_scorer/`)

## Purpose

Structural health across an entire spec corpus. Catches specs
that fell out of sync with the group, broken cross-references,
orphan specs, oversized files, and missing sections or
frontmatter fields.

Works on any directory of markdown specs. Auto-detects spec
types from frontmatter or directory structure. No project-specific
knowledge required.

## Target Specs

Any spec corpus, scored as a directory.

## CLI

```bash
# Score a spec directory (text output)
.docodego/tools/run shs_scorer <directory>

# With optional flows directory for coverage check
.docodego/tools/run shs_scorer <directory> --flows <flows-dir>

# JSON output
.docodego/tools/run shs_scorer --format json <directory>

# Custom line limits
.docodego/tools/run shs_scorer --line-limit 400 --data-heavy-limit 550 <directory>

# Disable zero-dimension veto
.docodego/tools/run shs_scorer --no-zero-veto <directory>
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `directory` | *(required)* | Directory containing spec files to check |
| `--format` | `text` | Output format: `text` (human-readable) or `json` (structured) |
| `--threshold` | `60` | Minimum total score (out of 100) required to pass |
| `--flows` | *(none)* | Optional flows directory for coverage check |
| `--line-limit` | `500` | Maximum lines per spec |
| `--data-heavy-limit` | `650` | Maximum lines for specs with 3+ tables |
| `--no-zero-veto` | off | Allow passing even if one dimension scores 0 |
| `--audits` | *(none)* | Write audit JSON to this directory (or set `DOCODEGO_CYCLE`) |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Corpus meets the threshold |
| `1` | Below threshold, zero-veto triggered, or directory not found |

## Dimensions (4 x 25 = 100)

### 1. Status Consistency (0–25)

Do all specs in the same group share the same lifecycle status?

- Groups specs by subdirectory (e.g., `behavioral/`, `foundation/`,
  `conventions/`)
- Uses majority vote within each group to find anomalies
- Valid statuses: `draft`, `approved`, `deprecated` — anything
  else (typos, legacy values) is flagged as invalid
- Invalid statuses always deduct 5 points
- **Scoring:** all groups uniform → 25, 90%+ → 20, 70%+ → 15,
  50%+ → 10, else linear

### 2. Reference Coverage (0–25)

Are specs connected to each other and bidirectionally?

- **Orphan detection:** counts inbound references per spec (from
  Related Specifications links). Specs with zero inbound
  references are orphans — nothing connects to them
- **Bidirectional references (informational):** for each edge
  A → B, checks whether B → A exists. Reported as a suggestion
  but not scored — reference graphs are naturally directional
- **Flow mapping (optional):** if `--flows` directory is provided,
  matches flow files to spec files by filename. Unmatched flows =
  planned but unwritten specs; unmatched specs = ad-hoc specs
  without a flow. If no flows directory provided, this sub-check
  is skipped and full points awarded
- **Scoring:** composite of orphan ratio and flow match ratio,
  weighted equally. 100% on both → 25, proportional otherwise

### 3. Line Budget (0–25)

Are specs within reasonable size limits?

- Default limit: 500 lines (specs are prose, not source code)
- Data-heavy tolerance: specs with 3+ markdown tables get a
  higher limit (650 lines)
- Severity grading: within limit → no flag, 1–20% over →
  suggestion, 20%+ over → issue
- Secondary check: Related Specifications section with 15+
  entries flags "doing too much"
- Line limits configurable via `--line-limit` and
  `--data-heavy-limit` flags
- **Scoring:** 100% compliant → 25, 95%+ → 20, 85%+ → 15,
  70%+ → 10, else linear

### 4. Structural Completeness (0–25)

Are required sections and frontmatter fields present?

**Section presence (0–15):**

- Auto-detects spec type from frontmatter `id` prefix or
  subdirectory name, then checks for expected sections
- Sections are detected by `## Heading` text, matched
  case-insensitively against known heading patterns
- Missing required sections are flagged as issues
- Specs with no detectable type are checked against a minimal
  set: Intent, Acceptance Criteria, Constraints

**Frontmatter validity (0–5):**

- Checks for standard frontmatter fields: `id`, `version`,
  `created`, `owner`, `status`
- Validates formats: `version` matches semver, `created` matches
  date pattern, `status` is a recognized value

**Link integrity (0–5):**

- Every `[text](path.md)` resolves to an existing file (relative
  to source file's directory)
- Broken links emit source file, line number, and unresolved
  target

**Scoring:** `(present sections / expected) × 15` +
`(valid frontmatter / expected) × 5` +
`(resolved links / total links) × 5`

## Gate Logic

Standard: zero-veto → threshold (default 60) → status bands.

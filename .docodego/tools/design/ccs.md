# CCS — Convention Clarity Score

> [All Tools](../README.md) · Status: **Implemented** (`ccs_scorer/`)

## Purpose

Scores individual convention specs for enforcement readiness — is
the convention precise enough to be automated, detectable, and
scoped to specific code?

## Target Specs

Any convention spec, scored one at a time.

## CLI

```bash
# Score a single spec (text output)
PYTHONPATH=.docodego/tools python -m ccs_scorer <file>

# Score multiple specs with JSON output
PYTHONPATH=.docodego/tools python -m ccs_scorer --format json <files...>

# Custom threshold (default is 60)
PYTHONPATH=.docodego/tools python -m ccs_scorer --threshold 80 <file>

# Disable zero-dimension veto
PYTHONPATH=.docodego/tools python -m ccs_scorer --no-zero-veto <file>
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `files` | *(required)* | One or more markdown convention spec files to score |
| `--format` | `text` | Output format: `text` (human-readable) or `json` (structured) |
| `--threshold` | `60` | Minimum total score (out of 100) required to pass |
| `--no-zero-veto` | off | Allow passing even if one dimension scores 0 |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All scored files meet the threshold |
| `1` | At least one file failed (below threshold, zero-veto, or not found) |

## Dimensions (4 x 25 = 100)

### 1. Precision (0–25)

Are rules written in unambiguous IF/THEN form?

- **IF/THEN ratio:** what fraction of rule bullets follow
  `IF <condition> THEN <outcome>` structure
- **Rules word count:** penalizes empty or stub Rules sections
- **Vague qualifier penalty:** same 15-pattern list as ICS,
  deducts from a starting 5 points
- **What it catches:** vague rules like "code should be clean"
  that can't be linted

### 2. Detectability (0–25)

Does each rule have a matching violation signal?

- **Substantive signal:** names a tool, rule ID, grep pattern,
  CI script, or backtick-quoted identifier
- **Scoring:** 90%+ coverage → 25, 70%+ → 18, 50%+ → 12,
  30%+ → 6, else linear
- **What it catches:** rules with no automated detection mechanism

### 3. Enforcement Coverage (0–25)

Are rules tiered (L1/L2/L3) and backed by tooling?

- **L1** = auto-enforced by a tool (zero human effort)
- **L2** = CI script or custom check (runs unattended)
- **L3** = code review only (requires human judgement)
- **Scoring:** tier label coverage (0–10), L1/L2 tool naming
  (0–8), remediation section depth (0–7)
- **What it catches:** rules with no enforcement plan, L1/L2
  rules that don't name the enforcing tool

### 4. Scope Clarity (0–25)

Are rules scoped to specific code locations?

- **Scope signals:** glob patterns, paths with `/`, directory
  prefixes (`apps/`, `packages/`, `src/`, `e2e/`), file
  extension patterns (`*.ext`), named workspaces
- **Vague scope flags:** "everywhere", "all components", "entire
  codebase", "the whole project"
- **Scoring:** 80%+ scoped → 25, 60%+ → 18, 40%+ → 12,
  20%+ → 6, else linear
- **What it catches:** rules that apply "everywhere" with no
  target path

## Gate Logic

Same as ICS: zero-veto → threshold (default 60) → status bands.
No threat floor (conventions don't have failure modes).

## Expected Spec Structure

The parser recognises these sections by heading text
(case-insensitive, multiple aliases accepted):

| Section Key | Required | Accepted Headings |
|-------------|----------|-------------------|
| `intent` | Yes | Intent, Purpose, Objective, Why This Convention |
| `rules` | Yes | Rules, Rule, Convention Rules, Rule Set, Coding Rules, The Rules |
| `enforcement` | Yes | Enforcement, Enforcement Tiers, Tiers, Enforcement Levels |
| `violation_signal` | Yes | Violation Signal, Violation Detection, Detection, Signals, How to Detect |
| `remediation` | Yes | Remediation, Fix, Fixes, Resolution, How to Fix, Remediation Steps |
| `correct_forbidden` | No | Correct vs. Forbidden, Examples, Do vs. Don't |

YAML frontmatter (between `---` fences) is skipped automatically.

## Module Architecture

```
ccs_scorer/
├── __init__.py        Package metadata (version)
├── __main__.py        CLI entry point, argument parsing, file I/O
├── parser.py          Markdown parser — heading classification,
│                      section extraction, bullet extraction
├── scorer.py          Four dimension scorers + gate logic
├── anti_gaming.py     Regex pattern libraries for vague qualifiers,
│                      scope signals, violation signals, tier labels,
│                      tool references, IF/THEN detection
└── reporter.py        Text and JSON output formatters
```

### Data Flow

```
.md file → parser.parse_spec() → ParsedConventionSpec
         → scorer.score_spec()  → CCSResult
         → reporter.format_*()  → text or JSON output
```

## JSON Output Schema

```json
{
    "file": "path/to/spec.md",
    "overall_score": 100,
    "threshold": 60,
    "threshold_met": true,
    "blocked": false,
    "block_reason": "",
    "status": "High-quality convention specification",
    "dimensions": {
        "precision": {
            "score": 25, "max_score": 25, "band": "high",
            "issues": [], "suggestions": []
        },
        "detectability": {
            "score": 25, "max_score": 25, "band": "high",
            "issues": [], "suggestions": []
        },
        "enforcement_coverage": {
            "score": 25, "max_score": 25, "band": "high",
            "issues": [], "suggestions": []
        },
        "scope_clarity": {
            "score": 25, "max_score": 25, "band": "high",
            "issues": [], "suggestions": []
        }
    }
}
```

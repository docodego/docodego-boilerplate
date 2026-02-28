# ICS — Intent Clarity Score

> [All Tools](../README.md) · Status: **Implemented** (`ics_scorer/`)

## Purpose

Scores individual behavioral and foundation specs for intent
clarity — does the spec communicate what to build, how to verify
it, and what can go wrong?

## Target Specs

Any behavioral or foundation spec, scored one at a time.

## CLI

```bash
# Score a single spec (text output)
PYTHONPATH=.docodego/tools python -m ics_scorer <file>

# Score multiple specs with JSON output
PYTHONPATH=.docodego/tools python -m ics_scorer --format json <files...>

# Custom threshold (default is 60)
PYTHONPATH=.docodego/tools python -m ics_scorer --threshold 80 <file>

# Custom threat floor (default is 15)
PYTHONPATH=.docodego/tools python -m ics_scorer --threat-floor 20 <file>

# Disable zero-dimension veto
PYTHONPATH=.docodego/tools python -m ics_scorer --no-zero-veto <file>
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `files` | *(required)* | One or more markdown spec files to score |
| `--format` | `text` | Output format: `text` (human-readable) or `json` (structured) |
| `--threshold` | `60` | Minimum total score (out of 100) required to pass |
| `--threat-floor` | `15` | Minimum Threat Coverage score — blocks approval if not met |
| `--no-zero-veto` | off | Allow passing even if one dimension scores 0 |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All scored files meet the threshold |
| `1` | At least one file failed (below threshold, zero-veto, threat floor, or not found) |

## Dimensions (4 x 25 = 100)

### 1. Completeness (0–25)

Are the four required sections present and substantive?

- **Required sections:** Intent, Acceptance Criteria, Constraints,
  Failure Modes
- **Scoring:** 0–15 for presence ratio, 0–10 for depth (50+ words
  per section earns full credit), +1 bonus for optional Governance
  section
- **What it catches:** stub sections, missing sections, specs that
  have headings but no real content

### 2. Testability (0–25)

Do acceptance criteria contain measurable, machine-verifiable
language?

- **Measurable patterns:** numeric thresholds (`200 ms`), bound
  expressions (`at least 3`), binary states (`present`, `absent`),
  HTTP codes (`returns 401`), equality operators (`equals 1`)
- **Boilerplate filter:** generic criteria like "system must work
  correctly" earn zero credit and are excluded from the ratio
- **Scoring:** 90%+ measurable → 25, 70%+ → 20, 50%+ → 15,
  30%+ → 10, else linear
- **What it catches:** vague acceptance criteria that can't be
  automated into tests

### 3. Unambiguity (0–25)

Is the spec free of vague qualifiers?

- **Vague qualifiers (15 patterns):** fast, slow, good, intuitive,
  appropriate, robust, scalable, efficient, secure, as needed,
  should, may, etc.
- **Smart exceptions:** `scalable` and `efficient` allowed when
  followed by a number; `secure` allowed when followed by a
  qualifying clause
- **Scoring:** 0 violations → 25, 1–2 → 20, 3–5 → 15, 6–8 → 10,
  9–12 → 5, 13+ → 0
- **What it catches:** weasel words that leave implementation open
  to interpretation

### 4. Threat Coverage (0–25)

Does the spec define enough failure modes with recovery paths?

- **Substantive failure mode** = 15+ words AND contains a recovery
  keyword (falls back, retries, alerts, degrades, rejects, returns
  error, logs, notifies, etc.)
- **Scoring:** 3+ substantive → 25, 2 → 16, 1 → 8, 0 → 0
- **Threat floor gate:** Threat Coverage must score ≥ 15 or the
  entire spec is BLOCKED regardless of total score
- **What it catches:** specs with no error handling plan, failure
  modes that list problems without solutions

## Gate Logic

1. Threat floor check (default 15) → BLOCKED if not met
2. Zero-veto → BLOCKED if any dimension = 0
3. Total threshold (default 60) → pass/fail
4. Status bands: 0–39 not ready, 40–59 under review, 60–79
   approved, 80–100 high-quality

## Expected Spec Structure

The parser recognises these sections by heading text
(case-insensitive, multiple aliases accepted):

| Section Key | Required | Accepted Headings |
|-------------|----------|-------------------|
| `intent` | Yes | Intent, Purpose, Objective, What and Why |
| `acceptance_criteria` | Yes | Acceptance Criteria, Success Criteria, Done When, Definition of Done |
| `constraints` | Yes | Constraints, Boundaries, Out of Scope, Non-Goals |
| `failure_modes` | Yes | Failure Modes, Failure Scenarios, Risks, Edge Cases, Threat Model |
| `governance` | No | Governance, Governance Checkpoint, Governor Sign-Off, Human Review, Kill Switch |

YAML frontmatter (between `---` fences) is skipped automatically.

## Module Architecture

```
ics_scorer/
├── __init__.py        Package metadata (version)
├── __main__.py        CLI entry point, argument parsing, file I/O
├── parser.py          Markdown parser — heading classification,
│                      section extraction, word counting
├── scorer.py          Four dimension scorers + gate logic
├── anti_gaming.py     Boilerplate detection, recovery keyword
│                      matching, failure mode substance checks
└── reporter.py        Text and JSON output formatters
```

### Data Flow

```
.md file → parser.parse_spec() → ParsedSpec
         → scorer.score_spec()  → ICSResult
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
    "status": "High-quality specification",
    "dimensions": {
        "completeness": {
            "score": 25, "max_score": 25, "band": "high",
            "issues": [], "suggestions": []
        },
        "testability": {
            "score": 25, "max_score": 25, "band": "high",
            "issues": [], "suggestions": []
        },
        "unambiguity": {
            "score": 25, "max_score": 25, "band": "high",
            "issues": [], "suggestions": []
        },
        "threat_coverage": {
            "score": 25, "max_score": 25, "band": "high",
            "issues": [], "suggestions": []
        }
    }
}
```

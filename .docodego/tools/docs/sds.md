# SDS — Security Design Score

> [All Tools](../README.md) · Status: **Implemented** (`sds_scorer/`)

## Purpose

Enforces security-by-design at the spec level — does the spec
address threats systematically (STRIDE), define auth boundaries,
cover input validation, and signal defense-in-depth measures?

Goes deeper than ICS Threat Coverage, which only checks that
failure modes exist. SDS checks what categories of threats are
covered, whether the permission model is rigorous, and whether
inputs are validated with rejection behavior.

Works on any markdown spec that uses standard sections (Failure
Modes, Permission Model, Behavioral Flow, Business Rules,
Constraints). No project-specific knowledge required.

## Target Specs

Any behavioral or foundation spec, scored one at a time.

## CLI

```bash
# Score a single spec (text output)
.docodego/tools/run sds_scorer <file>

# Score multiple specs with JSON output
.docodego/tools/run sds_scorer --format json <files...>

# Custom threshold (default is 60)
.docodego/tools/run sds_scorer --threshold 80 <file>

# Disable zero-dimension veto
.docodego/tools/run sds_scorer --no-zero-veto <file>
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `files` | *(required)* | One or more markdown spec files to score |
| `--format` | `text` | Output format: `text` (human-readable) or `json` (structured) |
| `--threshold` | `60` | Minimum total score (out of 100) required to pass |
| `--no-zero-veto` | off | Allow passing even if one dimension scores 0 |
| `--audits` | *(none)* | Write audit JSON to this directory (or set `DOCODEGO_CYCLE`) |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All scored files meet the threshold |
| `1` | At least one file failed (below threshold, zero-veto, or not found) |

## Dimensions (4 x 25 = 100)

### 1. Threat Taxonomy Coverage (0–25)

Do failure modes cover applicable STRIDE categories?

- **STRIDE categories:** Spoofing, Tampering, Repudiation,
  Information Disclosure, Denial of Service, Elevation of Privilege
- Classifies each failure mode entry against STRIDE using keyword
  patterns (e.g., "session hijacking" → Spoofing, "injection" →
  Tampering)
- **Applicability filter:** only categories relevant to the spec
  count — specs mentioning sessions trigger Spoofing, specs with
  user input trigger Tampering, etc.
- Named attack vectors (CSRF, timing attack, token replay) earn
  bonus credit over generic "malicious user" language
- Specs with zero applicable categories → 25 by default
- **Scoring:** 4+ categories covered → 25, 3 → 20, 2 → 15,
  1 → 8, 0 → 0

### 2. Auth Boundary Rigor (0–25)

Is the permission model well-defined with clear auth boundaries?

- Checks Permission Model table for an unauthenticated row
  (visitor / anonymous / no session / public)
- Verifies 401 appears in unauthenticated contexts, 403 in
  unauthorized contexts (not swapped)
- Checks all relevant roles are enumerated
- **Single-role exemption:** specs stating a single role or no
  permission model → 20/25 automatically
- **No-endpoint exemption:** specs without user-facing endpoints
  (infrastructure, config) → 22/25 automatically
- **Scoring:** unauthenticated row (8) + correct 401 (5) + correct
  403 (5) + all roles (7)

### 3. Input Surface Coverage (0–25)

Are user inputs identified and matched to validation rules?

- Scans Behavioral Flow for input verbs: enters, types, selects,
  uploads, submits, pastes, fills, provides, sets, chooses
- Cross-references each detected input against Business Rules and
  Constraints for validation rules
- Checks that validation rules specify rejection behavior (HTTP
  status, error message shape, partial write prevention)
- Rules that say "validate" without failure outcome → half credit
- No inputs detected (system-triggered spec) → 25 by default
- **Scoring:** 90%+ validated → 25, 70%+ → 20, 50%+ → 15,
  30%+ → 10, else linear

### 4. Defense Depth Signals (0–25)

Does the spec mention defense-in-depth measures where applicable?

- **Rate limiting (0–6):** triggers on public endpoints / user
  input — `rate limit`, `throttle`, `429`, `cooldown`
- **CSRF protection (0–5):** triggers on state-changing operations
  — `CSRF`, `SameSite`, `anti-forgery`, `origin validation`
- **Token hardening (0–5):** triggers on session/token creation —
  `httpOnly`, `secure flag`, `token rotation`, `signed cookie`
- **Error sanitization (0–5):** triggers on error responses —
  `generic error`, `no stack trace`, `sanitize`, or cross-ref to
  a dedicated error handling spec
- **Audit logging (0–4):** triggers on sensitive operations —
  `audit`, `log the action`, `log the attempt`, `monitor`
- Non-applicable signals award full points automatically
- Cross-reference credit for delegating to dedicated specs

## Gate Logic

Standard: zero-veto → threshold (default 60) → status bands.

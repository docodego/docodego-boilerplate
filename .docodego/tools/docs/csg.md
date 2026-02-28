# CSG — Constraint Symmetry Guard

> [All Tools](../README.md) · Status: **Implemented** (`csg_scorer/`)

## Purpose

Detects contradictions between specs that share business rules.
When two specs both define the same constant (session expiry,
OTP length, invitation window), they must agree. When two specs
both assign permissions to the same role, they must not conflict.

Works on any corpus of markdown specs that use standard sections
(Business Rules, Constraints, Acceptance Criteria, Permission
Model, State Machine). No canonical glossary or external schema
required — the tool compares specs against each other.

## Target Specs

Any set of behavioral specs, scored as a corpus. Takes a
directory.

## CLI

```bash
# Score a spec directory (text output)
.docodego/tools/run csg_scorer <directory>

# JSON output
.docodego/tools/run csg_scorer --format json <directory>

# Custom threshold (default is 60)
.docodego/tools/run csg_scorer --threshold 80 <directory>

# Disable zero-dimension veto
.docodego/tools/run csg_scorer --no-zero-veto <directory>
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `directory` | *(required)* | Directory containing behavioral spec files to check |
| `--format` | `text` | Output format: `text` (human-readable) or `json` (structured) |
| `--threshold` | `60` | Minimum total score (out of 100) required to pass |
| `--no-zero-veto` | off | Allow passing even if one dimension scores 0 |
| `--audits` | *(none)* | Write audit JSON to this directory (or set `DOCODEGO_AUDITS`) |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Corpus meets the threshold |
| `1` | Below threshold, zero-veto triggered, or directory not found |

## Dimensions (4 x 25 = 100)

### 1. Shared Constants (0–25)

Do numeric constants agree across specs?

- Extracts constants from Business Rules, Constraints, and
  Acceptance Criteria:
  - Time: `N seconds/minutes/hours/days` → normalized to seconds
  - Count: `N retries/attempts/digits/characters`
  - Named: `exactly/maximum/minimum/at most/up to N`
- Groups by semantic meaning using keyword context (50-word
  window) — e.g., two specs both mentioning "session" + "expir"
  near a time value are grouped together
- Unit normalization: "7 days" and "604800 seconds" recognized
  as equivalent
- Reports inconsistent groups with spec name, value, and line
- **Scoring:** 100% consistent → 25, 90%+ → 20, 75%+ → 15,
  50%+ → 10, else linear

### 2. HTTP Status Semantics (0–25)

Are 401/403/409 used with correct semantics everywhere?

- Finds every HTTP status code mention with 30 words of context
- Classifies context against canonical meanings:
  - 401: unauthenticated, no session, missing token
  - 403: unauthorized, wrong role, permission denied
  - 409: conflict, duplicate, already exists
- **Swap detector:** 401 in a 403 context or vice versa is a
  high-severity issue
- **Scoring:** 95%+ correct → 25, 85%+ → 20, 70%+ → 15,
  50%+ → 10, else linear

### 3. State Machine Consistency (0–25)

Do state transitions connect correctly across specs?

- Parses State Machine tables for (from_state, to_state, trigger,
  guard) tuples
- Validates that terminal states in one spec appear as initial
  states in connected specs
- Flags unreachable states: appear only as `to_state` but never
  as `from_state` (excluding recognized terminal states like
  `deleted`, `completed`, `error`)
- Flags ambiguous states: same name, different semantics across
  specs (detected via conflicting guard conditions)
- If no cross-spec transitions exist → 25
- **Scoring:** 100% valid → 25, 90%+ → 20, 75%+ → 15, 50%+ → 10,
  else linear

### 4. Permission Symmetry & Least Privilege (0–25)

Does no spec grant what another spec denies for the same role,
and are permissions scoped to the minimum necessary?

**Symmetry checks (0–15):**

- Parses Permission Model tables into (role, action, allowed/denied)
  triples
- Cross-checks: if spec A grants a role action X and spec B
  denies the same role action X → conflict
- Uses keyword matching for action descriptions across specs
- Validates role capability consistency: permissions should not
  silently expand across specs

**Least privilege checks (0–10):**

- **Over-broad grants:** flags actions assigned to lower roles
  that other specs restrict to higher roles
- **Ownership scoping:** flags actions that say "can manage
  resources" without qualifying "own" vs "all"
- **Role ceiling:** for each action across the corpus, identifies
  the highest role that performs it. If a lower role is also
  granted the same action without scope qualification, flags as
  potential privilege escalation

**Scoring:** `(non_conflicting / total_pairs) × 15` +
`(least_privilege_compliant / total_grants) × 10`

## Gate Logic

Standard: zero-veto → threshold (default 60) → status bands.

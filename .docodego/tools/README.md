# Scoring Tools

Master index of all scoring tools. Each tool is generic — it
works on any markdown spec corpus without project-specific
knowledge. Each has a dedicated design document describing its
purpose, dimensions, scoring logic, and gate behavior.

## Quick Start

```bash
# Run any tool via the runner script (sources .env automatically)
.docodego/tools/run ics_scorer <spec-file>
.docodego/tools/run ccs_scorer --format json <spec-files...>

# Or set env vars manually
PYTHONPATH=.docodego/tools python -m ics_scorer <spec-file>
```

Configuration lives in `.docodego/tools/tools.env`:

```
PYTHONPATH=.docodego/tools
DOCODEGO_AUDITS=.docodego/cycle-01/audits
```

The runner script sources this file. Tools also auto-load
`DOCODEGO_AUDITS` via a built-in dotenv loader at startup.

## What Each Tool Answers

| Tool | Question |
|------|----------|
| **ICS** | Can a developer/AI build this feature from the spec alone, without guessing? |
| **CCS** | Can an AI/developer enforce this convention, or is it too vague to automate? |
| **SDS** | Has the spec author thought through security — threats, auth, inputs, defenses? |
| **CSG** | Do specs that share business rules, constants, and permissions actually agree? |
| **SHS** | Is the spec corpus structurally sound — linked, complete, and within limits? |
| **SCR** | Are the dependencies referenced in specs healthy, safe, and well-documented? |

## Tool Matrix

| # | Tool | Acronym | Status | Scope | Dimensions | Target Specs |
|---|------|---------|--------|-------|------------|--------------|
| 1 | [Intent Clarity Score](design/ics.md) | ICS | Implemented | Single file | 4 x 25 | Behavioral + Foundation |
| 2 | [Convention Clarity Score](design/ccs.md) | CCS | Implemented | Single file | 4 x 25 | Convention |
| 3 | [Security Design Score](design/sds.md) | SDS | Implemented | Single file | 4 x 25 | Behavioral + Foundation |
| 4 | [Constraint Symmetry Guard](design/csg.md) | CSG | Implemented | Directory | 4 x 25 | Behavioral |
| 5 | [Spec Health Score](design/shs.md) | SHS | Implemented | Directory | 4 x 25 | All |
| 6 | [Supply Chain Radar](design/scr.md) | SCR | Implemented | Directory | 40 + 25 + 20 + 15 | All |

## Shared Conventions

All tools share these properties:

- **Pure Python 3.10+ stdlib** — no pip dependencies
- **Gate logic:** zero-veto → threshold (default 60) → status bands
  (0–39 not ready, 40–59 under review, 60–79 approved, 80–100
  high-quality)
- **Band thresholds:** low 0–8, mid 9–18, high 19–25
- **Output formats:** `--format text` (ASCII progress bars) or
  `--format json` (structured, CI-friendly)
- **Audit output:** set `DOCODEGO_AUDITS=<dir>` (or pass
  `--audits <dir>`) to write `.audit.json` files mirroring the
  spec folder structure — multiple tools merge into one file
  per spec
- **Shared code:** `scoring_common/` package provides
  `DimensionResult`, audit I/O, and reporter helpers — each
  tool's reporter is a thin wrapper
- **Module layout:** `__init__.py`, `__main__.py`, `parser.py`,
  `scorer.py`, `anti_gaming.py`, `reporter.py`

## Two Scoring Modes

| Mode | Tools | Input | What it scores |
|------|-------|-------|---------------|
| Single-file | ICS, CCS, SDS | One or more `.md` files | Quality of individual specs |
| Directory | CSG, SHS, SCR | Spec directory | Consistency across the corpus |

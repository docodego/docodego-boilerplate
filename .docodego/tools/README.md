# ICS Scorer

**Automated Intent Clarity Score for DoCoDeGo specifications.**

The ICS Scorer parses markdown spec files against the DoCoDeGo rubric and returns a 0-100 quality score across four dimensions: Completeness, Testability, Unambiguity, and Threat Coverage.

## Quick Start

### CLI

```bash
# Score a spec file
python -m ics_scorer example_spec.md

# JSON output for CI pipelines
python -m ics_scorer example_spec.md --format json

# Custom threshold
python -m ics_scorer example_spec.md --threshold 70

# Score multiple files
python -m ics_scorer specs/*.md
```

DO NOT Explore the source files. You only need to know the cli commands
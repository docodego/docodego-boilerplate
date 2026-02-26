# Foundation Summary

DoCoDeGo (**DO**cumentation, **CO**nstruction, **DE**livery, **GO**vernance) is a post-Agile framework for teams using AI to build systems. It centers human judgment on intent, direction, and accountability while delegating implementation to AI. The name is an anagram of **Good Code** -- the framework name is the outcome.

**Core Axiom:**
> Intent is the primary artifact. Implementation is a compiled derivative. Governance is earned through the loop.

When AI generates implementation, the specification becomes what code used to be -- the thing you write first, get right, version-control, and treat as authoritative.


## The Twelve Statutes

| # | Statute | Pillar | Principle | Becomes Critical At |
|---|---------|--------|-----------|-------------------|
| 1 | Intent Is Absolute | DO | When AI builds wrong, refine the intent -- never patch the code. Emergency patches require mandatory spec update within one cycle. | Stage 1 |
| 2 | Code Is Regenerable | CO | Preserve logic, not syntax. System invariants (business rules, data/API contracts) are NOT regenerable and require human review. | Stage 2 |
| 3 | The Spec Is the Contract | DO | Construction does not begin without an approved spec. Verbal agreements, Slack messages, meeting notes are not specs. | Stage 1 |
| 4 | Zero-Latency Evolution | DE | Changes deliver as fast as validation permits. Every delay beyond validation is waste. | Stage 2 |
| 5 | The Human as Governor | GO | Human's primary contribution: judgment, clarity, accountability. Coding is not the primary measure of value. | Stage 1 |
| 6 | Transparent Reasoning | GO | Every agent produces auditable reasoning traces. Agents without traces should not get autonomous tasks. | Stage 3 |
| 7 | Quality Through Context | DO | AI output quality = context quality. Ambiguity in spec = defects in output. When AI generates wrong output, ask "what was ambiguous?" not "what's wrong with the AI?" | Stage 1 |
| 8 | Resilience Over Robustness | CO | Design for reconstruction, not for never-failing. Clear specs + simple systems > complex defensive systems with poor specs. | Stage 2 |
| 9 | Security by Design | GO | Every spec includes a threat model. No exceptions. | Stage 1 |
| 10 | Alignment Before Delivery | GO | Delivery does not proceed without governance validation at the current stage's required depth. | Stage 2 |
| 11 | Feedback Closes the Loop | DE | Deployment telemetry must return to DO. Feedback not fed back is waste. | Stage 2 |
| 12 | Simplicity of Spec | DO | Complexity signals unclear intent. Complex acceptance criteria often = multiple requirements that need separating. | Stage 1 |

**By pillar:** DO (1, 3, 7, 12), CO (2, 8), DE (4, 11), GO (5, 6, 9, 10)

---

## The Specification Template

### Two Modes

| Mode | When | Sections |
|------|------|----------|
| **Simple Spec** | Single action, no branching, single role, no external integrations | Required sections + Edge Cases + declared omissions |
| **Full Spec** | Multiple steps, branching, stateful entities, multiple roles, external integrations | All sections whose triggers are met + declared omissions for the rest |


**Trigger:** If a feature needs a Behavioral Flow, it is a Full Spec.

### Required Sections

1. **Intent** -- One paragraph: what, why, for whom. No implementation details.
2. **Constraints** -- Bullet list, each independently testable (binary pass/fail).
3. **Acceptance Criteria** -- Binary pass/fail checklist. If you can't test it, it doesn't belong.
4. **Threat Model** -- Minimum 3 failure modes with: what happens, source, consequence, recovery.
5. **Out of Scope** -- Explicit list of what this spec does NOT cover.

### Optional Sections (include when triggered)

| Section | Trigger |
|---------|---------|
| **Integration Map** | Feature calls external system |
| **Behavioral Flow** | Multiple steps or branching |
| **State Machine** | Entities with a lifecycle |
| **Business Rules** | Behavior differs by conditions |
| **Permission Model** | Different user capabilities |
| **Edge Cases** | Recommended for all features |
| **Related Specifications** | Dependencies on other specs |

### The Declared Omission Rule

Silence is not omission. When an optional section is not needed, state why: "No external integrations." / "Single-action feature; no flow needed." / "No stateful entities."

### Spec Hierarchy (large projects)

| Level | Purpose | ICS Scored? |
|-------|---------|-------------|
| **Product Context** (1 per product) | Shared constraints, roles, glossary | No |
| **Domain Spec** (1 per capability) | Layer-agnostic behavioral definition | Yes (gates decomposition) |
| **Component Spec** (1 per layer per domain) | Layer-specific implementation requirements | Yes (gates construction) |

### Spec Lifecycle

```
draft --> review --> approved --> deprecated
                       |
                  (construction begins)
```

Versioning: Patch (clarification only) / Minor (new criteria, triggers re-validation) / Major (intent change, may need full regeneration).

---

## Intent Clarity Score (ICS)

**Formula:** ICS = Completeness (0-25) + Testability (0-25) + Unambiguity (0-25) + Threat Coverage (0-25)

| ICS | Meaning | Action |
|-----|---------|--------|
| < 40 | Not ready for review | Return for rework |
| 40-59 | Under review | Address gaps |
| >= 60 | Approved for construction | Proceed to CO |
| >= 80 | High-quality | No action needed |

**Threat Coverage floor:** Score below 15/25 fails the gate regardless of composite score.

**Inter-rater consistency:** Score with 2+ reviewers. Disagreement > 10 points/dimension means the spec is genuinely ambiguous. Single reviewer: score conservatively.

**Ambiguous qualifiers to avoid:** fast, slow, good, user-friendly, intuitive, reasonable, appropriate, high-quality, robust, scalable (without target), secure (without specific requirements), efficient (without measurement).


## The Six Metrics

| Metric | Pillar | Owner | What It Measures | Threshold |
|--------|--------|-------|-----------------|-----------|
| **ICS** (Intent Clarity Score) | DO | Intent Architect | Spec quality before construction | >= 60 to begin CO |
| **SDL** (Spec-to-Delivery Latency) | DE | Flow Steward | Time: spec approval --> first deployment | Trending down |
| **AAR** (Agent Alignment Rate) | GO | Governor | % outputs passing acceptance on first attempt | >= 70% |
| **GTR** (Governance Trigger Rate) | GO | Governor | % cycles requiring governance escalation | < 10% |
| **RC** (Regeneration Confidence) | CO | Construction Lead | Behavioral equivalence after regeneration | All checks pass before production |
| **DDL** (Drift Detection Latency) | GO | Governor | Time: drift occurs --> detected | Trending down |

### Key Warning Signals

- **AAR declining 3 consecutive cycles** = governance trigger regardless of threshold
- **GTR at 0% for extended period at Stage 3+** = governance may not be looking
- **AAR >= 95%** = verify specs aren't too simple or acceptance criteria too loose

### Anti-Gaming Measures

- **ICS:** Spec author cannot be sole scorer; >= 80 warrants external validation
- **AAR:** Acceptance criteria must be written/reviewed by someone other than the constructor
- **GTR:** Non-escalation must be documented with rationale; undocumented non-escalation is governance failure
- **Metric ownership rotation:** Rotate AAR and GTR ownership at stage advancement or annually


## Anti-Patterns

| # | Anti-Pattern | What Happens | Correction |
|---|-------------|-------------|-----------|
| 1 | **Retrospective Documentation** | Build first, write spec after to match. Destroys DO pillar value. Detect: specs written after construction in git history. | Rewrite spec from intent, not current behavior |
| 2 | **Governance as Audit** | GO added post-delivery. Issues found require rollback. Findings filed, not acted on. | Governance belongs in the loop; Governor needs actual halt authority |
| 3 | **Worked Example as Template** | Copy ticket routing example structure everywhere. ICS is high (format correct) but content hollow. | ICS review challenges content, not just format |
| 4 | **Velocity Addiction** | DoCoDeGo vocabulary with Agile metrics. Story points relabeled; sprints remain two-week. | Replace metrics operationally: ICS, AAR, SDL, GTR |
| 5 | **Invisible Governance** | Autonomous agents, minimal oversight. No confidence thresholds, no trace review, no kill-switch. | Match governance maturity to AI autonomy level |
| 6 | **Spec Sprawl** | Specs grow but never pruned. Requirements from 3 iterations ago remain. AI builds to the entire spec. | Regular spec health reviews; ask "does this still describe what we want?" |
| 7 | **Governor Capture** | Governor loses independence (engineering capture: rubber stamp) or (business capture: defers to delivery pressure). | Separate Governor from engineering; document non-escalation decisions; peer review of governance decisions |
| 8 | **Ceremony Creep** | Stage 1 team running Stage 3 governance. Each addition individually defensible; accumulation destroys adoptability. | Audit ceremony against stage requirements; remove what stage doesn't require |
| **Meta** | **DoCoDeGo as Process** | Framework vocabulary + ceremonies, no actual alignment improvement. Metrics tracked but not acted on. | Test: "does what they build match what they intended?" Everything else is means. |

---

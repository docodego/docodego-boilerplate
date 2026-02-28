---
id: [unique identifier, e.g. SPEC-2026-042]
version: 1.0.0
created: [YYYY-MM-DD]
owner: [Intent Architect name]
status: draft
roles: [list defined roles, if applicable]
---

# [System or Feature Name]

## Intent

[One paragraph. What is this for? What problem does it solve for the people who depend on it?
Write for a competent colleague who has never seen this system. No implementation details.
No technical jargon unless the domain requires it.]

## Integration Map

**Triggering condition:** Required when the feature calls an external system, consumes an event, or writes to a system outside its own domain.

[Table of external dependencies:]

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| [system name] | [read/write/event] | [trigger condition] | [failure behavior] |

**Declaring inapplicable:** If this feature has no external integrations, state: "No external integrations."

## Behavioral Flow

**Triggering condition:** Required when the feature involves multiple steps, user decisions, or branching paths.

[The sequence of steps and branching paths. Can be narrative, bulleted, or diagrammatic.
Each step should name its actor explicitly: `[Actor] → action → outcome`]

**Multi-actor scenarios:** Where actor handoffs occur (e.g., User submits → System validates → Admin is notified), mark the handoff point explicitly as a step.

**Declaring inapplicable:** If this feature is a single action with no branching, state: "Single-action feature; no flow needed."

## State Machine

**Triggering condition:** Required when the feature involves entities that have a lifecycle — orders, tasks, approvals, subscriptions, user accounts, tickets, bookings, content items.

[Table or enumeration of states and transitions:]

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| [state] | [state] | [event] | [condition, if any] |

**Declaring inapplicable:** If this feature has no stateful entities, state: "No stateful entities."

## Business Rules

**Triggering condition:** Required when behavior differs based on combinations of conditions — pricing, eligibility, permissions, routing, classification, approval workflows.

[Conditional logic that governs behavior:]

- **Rule [name]:** IF [condition 1] AND [condition 2] AND [condition n] THEN [outcome]
- **Rule [name]:** IF [condition] THEN [outcome]

**Declaring inapplicable:** If behavior is unconditional, state: "No conditional business rules."

## Permission Model

**Triggering condition:** Required when the feature has multiple user types, or some users can do things others cannot.

[Table of roles and permissions:]

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| [role] | [actions] | [actions] | [what they can/cannot see] |

**Declaring inapplicable:** If all users have the same capabilities, state: "Single role; no permission model needed."

## Constraints

[Bullet list. Each item must be independently testable — binary pass or fail.
Constraints define what must be true and what must not happen.]

- The system must [specific, measurable requirement]
- The system must not [specific prohibition]
- Response time must not exceed [specific threshold] under [specific load condition]
- [Continue as needed — no minimum, no maximum]

**Constraint vs. CO decision:**
- A **constraint** is non-negotiable — the AI cannot change it. Include technology choices and API paths that are pre-agreed or existing contracts.
- A **CO decision** is an implementation choice — the AI should determine it from context. Do not include open technology decisions or new endpoint design.
- **Default rule:** If changing it requires a stakeholder decision (not just a technical decision), it is a constraint.

## Acceptance Criteria

[Binary pass/fail checklist. Every criterion must be automatable or manually verifiable.
If you cannot write a test for it, it does not belong here.]

- [ ] [Criterion 1: specific, measurable, unambiguous]
- [ ] [Criterion 2]
- [ ] [Criterion 3 — include at least one negative criterion: "does not X when Y"]

**Traceability:** Acceptance criteria should map to flow steps and business rule conditions. A criterion that cannot be traced to a flow step may be testing the wrong thing.

## Edge Cases

**Triggering condition:** Recommended for all features. Every feature has edge cases.

[Non-adversarial failure scenarios — operational situations that require defined behavior:]

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| [what happens] | [what system must do] | [how this is verified] |

**Examples:** empty states, boundary conditions, concurrent access, partial failures, invalid inputs, integration timeouts, duplicate submissions.

## Threat Model

For each failure mode, name: what goes wrong, who or what causes it, what the consequence is, and how the system or team recovers. Minimum three failure modes. A threat model that cannot name three failure modes is a sign the spec is not yet understood well enough to build.

**Focus:** This section covers security and adversarial failures. Operational edge cases belong in Edge Cases above.

**Categories to consider:** incorrect or malicious inputs, system or dependency failures, adversarial use, data integrity issues, performance boundary violations, unauthorized access.

### Failure Mode 1: [Name]
**What happens:** [Description of the failure and its trigger]
**Source:** [Incorrect input / system failure / adversarial action / data issue / other]
**Consequence:** [Impact on users, data, or system]
**Recovery:** [How the system responds automatically, and what human action is required]

### Failure Mode 2: [Name]
**What happens:**
**Consequence:**
**Recovery:**

### Failure Mode 3: [Name]
**What happens:**
**Consequence:**
**Recovery:**

## Declared Omissions

[Explicit list of what this specification does NOT cover.
This is as important as what it does cover. Forces clarity about boundaries.]

- This specification does not address [specific capability or scenario]
- [Continue as needed]

## Related Specifications

[Links to specifications this one depends on or affects.]

- [SPEC-ID: Name](link) — [brief description of relationship]
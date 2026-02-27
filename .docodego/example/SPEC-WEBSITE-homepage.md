---
id: SPEC-WEBSITE-HOME
version: 1.1.0
created: 2026-02-26
owner: User (Intent Architect)
status: draft
roles: [Visitor, Framework Adopter]
parent: SPEC-WEBSITE-CTX
---

# DoCoDeGo Website — Homepage

## Intent

The homepage is the first impression of the DoCoDeGo framework. It must communicate what DoCoDeGo is, why it exists, and how to get started — within a single scroll narrative. A first-time visitor with no prior knowledge must be able to understand the framework's core value proposition within 60 seconds and know exactly where to go next based on their role.

The homepage does not try to replace the documentation. It creates curiosity and provides clear navigation to deeper content.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Starlight docs | link navigation | User clicks docs links | Static links; always available in build |
| ICS Scorer | embed (React island) | Section 7 renders | Show static mockup screenshot instead |

## Behavioral Flow

1. [Visitor] → lands on homepage → sees Hero section with DOCODEGO → GOOD CODE anagram
2. [Visitor] → scrolls → encounters The Problem (without/with contrast)
3. [Visitor] → scrolls → sees The Loop (DO→CO→DE→GO cycle diagram)
4. [Visitor] → scrolls → reads The Four Values (manifesto)
5. [Visitor] → scrolls → sees Four Pillars Detail (role + metric per pillar)
6. [Visitor] → scrolls → sees Six Metrics (framework measurement system)
7. [Visitor] → scrolls → interacts with Tools Preview (ICS Scorer)
8. [Visitor] → scrolls → reaches Audience Paths ("Where do you start?")
9. [Visitor] → scrolls → reads Social Proof (case studies/testimonials)
10. [Visitor] → scrolls → reaches Final CTA ("Good Code. Governed.")
11. [Visitor] → clicks a CTA → navigates to docs, tools, or audience-specific page

**Key decision point:** Section 8 (Audience Paths) is the primary routing mechanism. Five paths map to five user types defined in Product Context.

## State Machine

No stateful entities. Single-action feature; static page with optional interactive embed.

## Business Rules

No conditional business rules. Content is identical for all visitors.

## Permission Model

Single role (anonymous visitor); no permission model needed.

## Constraints

### Layout & Structure
- C01: The homepage must contain exactly 10 sections, each fitting within one viewport height (100vh max) on a 1440px wide display
- C02: A sticky header must remain visible during scroll, containing: site logo, navigation links (Framework | Docs | Blog | Tools | For Leaders | Enterprise), and a theme toggle
- C03: The header must use a backdrop blur effect for readability over scrolling content
- C04: Each section must communicate exactly one key message

### Visual Identity
- C05: The base palette must use zinc neutrals from Tailwind (zinc-50 through zinc-950)
- C06: Pillar accent colors (Blue #3B82F6, Cyan #06B6D4, Amber #F59E0B, Red #EF4444) must be used only for tags, accent borders, icon tints, and hover states — never as large background fills
- C07: Typography must use Inter for all text and JetBrains Mono for code
- C08: Component styling must follow shadcn/ui defaults (border-radius, shadows, spacing)
- C09: The site must render correctly in both light and dark themes, defaulting to system preference

### Content
- C10: The Hero section must feature the DOCODEGO → GOOD CODE anagram as the dominant visual element
- C11: Section 5 (Four Pillars) must include all four pillar names, their associated role titles, and their primary metrics
- C12: Section 6 (Six Metrics) must include all six metrics: ICS, SDL, AAR, GTR, RC, DDL
- C13: Section 8 (Audience Paths) must provide exactly five paths matching the five user types in Product Context
- C14: All framework terminology must match definitions in `open/05-ref-03-glossary.md`

### Performance
- C15: Total JavaScript payload must not exceed 100KB (gzipped)
- C16: Largest Contentful Paint (LCP) must be under 1 second
- C17: Cumulative Layout Shift (CLS) must be under 0.1

### Implementation
- C18: Interactive components (ICS Scorer) must use React via Astro islands (`client:visible` or `client:load`)
- C19: No single source file (`.astro`, `.tsx`, `.ts`, `.css`) must exceed 200 lines

### Accessibility
- C20: All content must meet WCAG 2.1 AA contrast ratios
- C21: All interactive elements must be keyboard-navigable
- C22: The page must be navigable by screen reader with semantic heading hierarchy (h1 → h2 → h3)

### Responsive Design
- CH15: All grid sections (Pillars, Metrics, Audience, Social Proof) must use responsive grid classes — single column on mobile, 2 columns on sm, full columns on lg+
- CH16: The hero heading must scale from text-5xl on mobile to text-[80px] on desktop
- CH17: The Loop diagram must stack vertically on mobile (< 640px) with rotated arrows

## Acceptance Criteria

- [ ] AC01: The Hero section (S1) contains the anagram, tagline, and at least 1 CTA — all 3 elements are present and visible above the fold on a 1440x900 viewport without scrolling
- [ ] AC02: The anagram text in S1 has a font size >= 64px, making it the largest text element in the Hero section — verified by computed style inspection
- [ ] AC03: Each of the 10 sections has a computed height <= 900px when rendered at 1440px width — verified by measuring all 10 section bounding boxes
- [ ] AC04: The sticky header element has `position: sticky` or equivalent and remains visible at 100% scroll depth — verified by automated scroll test confirming the header is present at 0%, 50%, and 100% scroll positions
- [ ] AC05: axe-core audit returns 0 contrast violations in both light and dark themes — verified by running axe-core with `color-contrast` rule enabled in both modes
- [ ] AC06: CSS audit returns 0 violations — pillar color hex values (#3B82F6, #06B6D4, #F59E0B, #EF4444) must not exceed 5% of visual surface area and appear only within designated sections (S3, S4, S5, S6) as tags, borders, or accents
- [ ] AC07: The ICS Scorer in S7 accepts text input of >= 50 characters and returns a numeric score between 0 and 100 within 2 seconds — if JavaScript is disabled, a static fallback image is present instead
- [ ] AC08: Automated link checker confirms all 5 audience path links in S8 respond with 200 status codes — link check must return 0 failures
- [ ] AC09: Lighthouse Performance score >= 95 on both mobile and desktop profiles — verified by Lighthouse CI audit
- [ ] AC10: Tab-through test confirms that at least 100% of interactive elements (links, buttons, inputs) are reachable via keyboard — focus order follows DOM order with no trapped or skipped elements
- [ ] AC11: Total page load time is under 2000ms on a simulated 4G connection (1.6 Mbps downlink, 150ms RTT) — verified by Lighthouse throttled audit
- [ ] AC12: Section 4 renders exactly 4 framework values and each equals the canonical wording in `open/01-core-02-manifesto.md` — Intent over Implementation, Direction over Production, Flow over Releases, Governance over Process — string comparison must return true for all 4
- [ ] AC13: Section 6 displays all 6 metrics (ICS, SDL, AAR, GTR, RC, DDL) — glossary validator confirms each abbreviation and description equals the canonical text in `open/05-ref-03-glossary.md`, returning true for all 6 comparisons
- [ ] AC15: At viewport width 375px, no content overflows horizontally and all cards stack in a single column
- [ ] AC16: At viewport width 1280px, Pillars renders 4 columns, Metrics 3 columns, Audience 5 columns

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| JavaScript disabled | ICS Scorer shows static mockup; all other sections render as static HTML | Section 7 displays fallback image |
| Narrow viewport (<375px) | Sections stack vertically; no horizontal overflow; header collapses to hamburger menu | No horizontal scrollbar on 320px viewport |
| System theme changes while page is open | Theme updates without page reload | Toggle OS theme; page responds immediately |
| Visitor lands on anchor link (e.g., #tools) | Page scrolls to correct section; sticky header visible | Direct URL navigation to section |
| Very slow connection (2G) | Hero section renders first (above fold priority); images lazy-load | LCP under 3s on 2G throttle |

## Threat Model

### Failure Mode 1: Misrepresentation of Framework
**What happens:** Homepage content diverges from canonical framework documents (e.g., wrong metric names, incorrect role titles, missing values)
**Source:** Content drift during implementation or updates
**Consequence:** Visitors learn incorrect framework information; credibility damage
**Recovery:** CI/CD build step logs all framework terminology mismatches and rejects deployment when glossary validation fails. The system falls back to the last verified content snapshot. Manual intervention by the Intent Architect is required to approve content changes that touch framework terminology. AC12 and AC13 enforce traceability to canonical docs.

### Failure Mode 2: Accessibility Failure
**What happens:** Pillar accent colors fail contrast ratios on light or dark backgrounds, or interactive elements are not keyboard-accessible
**Source:** Design decisions that prioritize aesthetics over accessibility
**Consequence:** WCAG 2.1 AA non-compliance; exclusion of users with visual or motor impairments
**Recovery:** axe-core audit runs in CI pipeline and rejects deployment when any contrast violation is detected. The system alerts the Composition Lead via build notification and logs all failing elements with their computed contrast ratios. Constraints C20-C22 are non-negotiable gates — the build degrades to a blocked state until violations are resolved.

### Failure Mode 3: Performance Degradation
**What happens:** ICS Scorer React island or animation JavaScript pushes payload over 100KB; LCP exceeds 1s
**Source:** Feature creep in interactive sections; unoptimized dependencies
**Consequence:** Lighthouse score drops below 95; degraded mobile experience
**Recovery:** Bundle size check in CI rejects builds exceeding 100KB gzipped JavaScript. If the ICS Scorer island exceeds its budget, the build falls back to a static screenshot fallback and notifies the Flow Steward. Lighthouse audit logs all performance regressions with before/after metrics. Animations use CSS-only with graceful degradation when prefers-reduced-motion is active.

### Failure Mode 4: Content-Design Misalignment
**What happens:** Pencil design and code implementation diverge — design shows one thing, code delivers another
**Source:** Composition without traceability to spec constraints
**Consequence:** Rework required; delivered site does not match approved design
**Recovery:** Every Pencil section maps to a constraint (C01-C20) and every code component maps to a Pencil section. Visual regression tests log pixel-level differences and reject deployment when drift exceeds the threshold. The system alerts the Composition Lead and escalates to the Governor when structural misalignment is detected. Manual intervention resolves whether the design or code is authoritative.

## Out of Scope

- This specification does not address blog content, documentation layout, or marketing pages (separate domain specs)
- This specification does not address SEO meta tags or structured data (covered in polish phase)
- This specification does not address animations beyond "subtle, optional" (CO decision)
- This specification does not address the specific copy for testimonials in Section 9 (content sourced from case studies during implementation)
- This specification does not address cookie consent, analytics, or tracking (separate concern)

## Related Specifications

- [SPEC-WEBSITE-CTX](./SPEC-WEBSITE-context.md) — Parent product context
- SPEC-WEBSITE-DOCS — Starlight docs integration (to be written)
- SPEC-WEBSITE-BLOG — Blog collection (to be written)
- SPEC-WEBSITE-MARKETING — Marketing pages (to be written)

---

## Traceability Matrix

### Constraints → Sections

| Section | Constraints | Acceptance Criteria |
|---------|-------------|-------------------|
| Header (sticky) | C02, C03 | AC04 |
| S1: Hero | C04, C10 | AC01, AC02 |
| S2: Problem | C04 | AC03 |
| S3: Loop | C04, C06 | AC03, AC06 |
| S4: Values | C04, C14 | AC03, AC12 |
| S5: Pillars | C04, C06, C11 | AC03, AC06 |
| S6: Metrics | C04, C12 | AC03, AC13 |
| S7: Tools | C04 | AC03, AC07 |
| S8: Audience | C04, C13 | AC03, AC08 |
| S9: Social Proof | C04 | AC03 |
| S10: CTA | C04 | AC03 |
| All sections | C01, C05, C07, C08, C09 | AC05, AC09, AC10, AC11 |
| All sections | C15, C16, C17, C18, C19 | AC09 |
| All sections | C20, C21, C22 | AC05, AC10 |

### DO → CO Handoff

When this spec reaches ICS >= 60 and status = approved:
1. **CO Phase 1**: Design in Pencil — each section maps to a named frame, each constraint verified visually
2. **CO Phase 2**: Implement in Astro — each Pencil frame maps to a `.astro` component, each constraint verified in code

### CO → DE Handoff

When composition is complete:
1. **DE Validation**: Run acceptance criteria checklist (AC01-AC13)
2. **DE Automated**: Lighthouse audit, axe-core audit, link checker, glossary validator
3. **DE Deploy**: Deploy when all gates pass

### DE → GO Feedback

After deployment:
1. **GO Monitor**: Track visitor behavior — do they reach Section 8? Do they click audience paths?
2. **GO Measure**: AAR (did the page match intent on first composition?), DDL (how quickly do we detect content drift?)
3. **GO Findings**: Feed back into spec revision (version bump) for next iteration

---

**docodego.com** · *DOcument · COmpose · DEmonstrate · GOvern*

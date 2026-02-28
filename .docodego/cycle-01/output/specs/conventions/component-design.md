---
id: CONV-2026-004
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Component Design

## Intent

Enforces consistent React component authoring in `apps/web` and `apps/browser-extension`. Single-responsibility components, explicit props interfaces, extracted literals, controlled nesting depth, and co-located tests reduce re-renders and keep the component tree navigable.

## Rules

- IF a React component in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` renders more than one distinct UI concern (data fetching, layout, and form handling combined) THEN split it into focused child components so each addresses exactly one concern
- IF a component in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` accepts props THEN define and export a `XxxProps` interface named after the component with a `Props` suffix in the same file
- IF a JSX element in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` passes an inline object literal `{{}}` or array literal `{[]}` directly as a prop THEN extract it to a named constant defined outside the JSX return block
- IF a component render return in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` nests JSX more than 3 levels deep THEN extract the nested section into a named sub-component
- IF a component file exists at `apps/web/src/**/*.tsx` THEN a co-located test file with the same base name and `.test.tsx` extension MUST exist in the same directory

## Enforcement

- L2 — CI `grep -rn 'useQuery\|fetch(' apps/web/src apps/browser-extension/src` cross-referenced with layout JSX in the same file
- L2 — CI `grep -rLE 'interface \w+Props'` on `apps/web/src/**/*.tsx` and `apps/browser-extension/src/**/*.tsx`
- L2 — CI `grep -rnE '=\{\{[^}]'` on `apps/web/src/**/*.tsx` and `apps/browser-extension/src/**/*.tsx`
- L2 — CI JSX nesting depth check on `apps/web/src/**/*.tsx` and `apps/browser-extension/src/**/*.tsx`
- L2 — CI `grep -rL '.test.tsx'` on component files under `apps/web/src/`

## Violation Signal

- `grep -rn 'useQuery\|fetch('` in `apps/web/src/**/*.tsx` returns matches in files also containing form or layout JSX
- `grep -rLE 'interface \w+Props'` in `apps/web/src/**/*.tsx` lists files missing a `XxxProps` interface
- `grep -rnE '=\{\{[^}]'` in `apps/web/src/**/*.tsx` returns lines with inline object literals as JSX props
- `grep -c "^\s\{16,\}"` on `apps/web/src/**/*.tsx` returns lines indented 16+ spaces, indicating JSX nesting beyond 3 levels
- `grep -rL '.test.tsx'` against `apps/web/src/**/*.tsx` returns components without a co-located test file

## Correct vs. Forbidden

```tsx
// Correct — apps/web/src/components/card.tsx
export interface CardProps { title: string; children: React.ReactNode; }
export function Card({ title, children }: CardProps) {
    return <div>{title}{children}</div>;
}

// Forbidden — inline type, inline style object
export function Card({ title, children }: { title: string; children: React.ReactNode }) {
    return <div style={{ padding: "1rem" }}>{title}{children}</div>;
}
```

## Remediation

- **Single responsibility** — extract data-fetching into a custom hook and layout into a separate wrapper component
- **Props interface** — add an exported `XxxProps` interface at the top of the file matching the component name
- **Inline literals** — extract to a `const` before the return statement or at module scope if static
- **Nesting depth** — extract the deeply nested subtree into a named sub-component in the same or sibling file
- **Co-located test** — create a `.test.tsx` file in the same directory with at least one `vitest` render test

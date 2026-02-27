---
id: CONV-2026-011
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# UI Styling Conventions

## Intent

Enforces consistent Tailwind CSS usage across `apps/web`, `apps/browser-extension`, and `packages/ui` workspaces. Canonical classes, logical properties, RTL overrides, and the correct component primitive library prevent styling drift and layout bugs in bidirectional locales.

## Rules

- IF a JSX file in `apps/web/**/*.tsx` or `packages/ui/**/*.tsx` uses an arbitrary Tailwind value such as `w-[320px]` or `text-[#ff0000]` when a canonical utility class exists THEN `grep -rE '\[' --include='*.tsx'` detects the violation and the author runs `pnpm dlx @tailwindcss/upgrade` to replace it
- IF a JSX file in `apps/web/**/*.tsx` or `packages/ui/**/*.tsx` uses a physical directional class (`pl-`, `pr-`, `ml-`, `mr-`, `text-left`, `text-right`, `rounded-l-`, `rounded-r-`, `left-`, `right-`, `inset-l-`, `inset-r-`) THEN code review rejects it because logical equivalents (`ps-`/`pe-`, `ms-`/`me-`, `text-start`/`text-end`, `rounded-s-`/`rounded-e-`, `inset-s-`/`inset-e-`) exist
- IF a JSX file in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` uses `translate-x-*` without a paired `rtl:-translate-x-*` variant THEN `grep -rn 'translate-x-' --include='*.tsx'` detects the missing RTL counterpart because `translate-x` has no logical equivalent in Tailwind
- IF a component file in `packages/ui/**/*.tsx` or `apps/web/**/*.tsx` imports from `@radix-ui/*` THEN `knip` flags the forbidden dependency because the Shadcn `base-vega` style uses `@base-ui/react` exclusively
- IF a `biome-ignore` comment suppresses an a11y lint rule in `packages/ui/**/*.tsx` or `apps/web/**/*.tsx` on an element that is not a `<label>` THEN code review rejects the suppression and the a11y issue is fixed in the component source

## Enforcement

- L2 — `grep -rE '\[' --include='*.tsx'` on `apps/web/` and `packages/ui/` for arbitrary values
- L2 — `grep -rE '(pl-|pr-|ml-|mr-|text-left|text-right|rounded-l-|rounded-r-)' --include='*.tsx'` on `apps/web/` and `packages/ui/`
- L2 — `grep -rn 'translate-x-' --include='*.tsx'` on `apps/web/` and `apps/browser-extension/`
- L1 — `knip` detects `@radix-ui/*` imports in `packages/ui/` and `apps/web/`
- L3 — code review verifies `biome-ignore` a11y suppression targets only `<label>` in `packages/ui/` and `apps/web/`

## Violation Signal

- `grep -rE '\[' --include='*.tsx'` in `apps/web/` or `packages/ui/` returns lines containing arbitrary Tailwind bracket syntax
- `grep -rE '(pl-|pr-|text-left|rounded-l-)' --include='*.tsx'` in `apps/web/` or `packages/ui/` returns physical directional classes
- `grep -rn 'translate-x-' --include='*.tsx'` in `apps/web/` or `apps/browser-extension/` returns files lacking a corresponding `rtl:` override
- `knip` reports `@radix-ui/*` as an unlisted or unused dependency in `packages/ui/` or `apps/web/`
- `grep -rn 'biome-ignore.*a11y' --include='*.tsx'` in `packages/ui/` or `apps/web/` returns lines where the suppressed element is not a `<label>`

## Correct vs. Forbidden

```tsx
// Correct — apps/web/src/components/sidebar.tsx
<div className="ps-4 pe-2 text-start rounded-s-lg">
    <span className="translate-x-2 rtl:-translate-x-2" />
</div>

// Forbidden — physical classes, missing RTL override
<div className="pl-4 pr-2 text-left rounded-l-lg">
    <span className="translate-x-2" />
</div>
```

## Remediation

- **Arbitrary values** — run `pnpm dlx @tailwindcss/upgrade` after every `shadcn add` to replace bracket syntax with canonical Tailwind utilities across `apps/web/` and `packages/ui/`
- **Physical classes** — replace `pl-`/`pr-` with `ps-`/`pe-`, `ml-`/`mr-` with `ms-`/`me-`, `text-left`/`text-right` with `text-start`/`text-end`, and `rounded-l-`/`rounded-r-` with `rounded-s-`/`rounded-e-` in all `apps/web/` and `packages/ui/` files
- **RTL translate** — add `rtl:-translate-x-*` alongside every `translate-x-*` usage in `apps/web/` and `apps/browser-extension/` because no logical Tailwind equivalent exists
- **Radix imports** — replace `@radix-ui/*` imports with `@base-ui/react` equivalents in `packages/ui/` and `apps/web/` to match the Shadcn `base-vega` style
- **biome-ignore a11y** — remove the suppression comment and fix the underlying accessibility violation in the component source rather than silencing the lint rule

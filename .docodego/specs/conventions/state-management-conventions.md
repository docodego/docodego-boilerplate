---
id: CONV-2026-006
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# State Management Conventions

## Intent

Standardizes how `apps/web` and `apps/browser-extension` handle server data, shared client state, and ephemeral form state. Server data flows through TanStack Query, shared UI state lives in Zustand, and form-local state stays in React hooks.

## Rules

- IF a component in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` fetches data from a `@repo/contracts` oRPC endpoint THEN it MUST use `useQuery` or `useMutation` from `@tanstack/react-query` — not raw `fetch()` or `useEffect`-based fetching
- IF state in `apps/web/` needs to be shared across 2 or more unrelated component trees THEN it MUST live in a Zustand store under `apps/web/src/stores/` instead of being prop-drilled
- IF a form in `apps/web/**/*.tsx` manages its own field values THEN it MUST use React `useState` or `react-hook-form` — ephemeral form values MUST NOT be stored in a Zustand store or TanStack Query cache
- IF a `useQuery` call in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` defines a query key THEN the key MUST be an array starting with a domain string literal followed by identifiers — e.g. `["org", orgId, "members"]`
- IF a Zustand store in `apps/web/src/stores/` exports more than 5 top-level state fields THEN split it into focused slice files

## Enforcement

- L2 — CI `grep -rn "useEffect" apps/web/src apps/browser-extension/src` cross-referenced with `fetch(` to flag bypassed TanStack Query
- L2 — CI `grep -rn "create(" apps/web/src --exclude-dir=stores` to find Zustand stores outside `apps/web/src/stores/`
- L3 — code review on `apps/web/**/*.tsx` form components for Zustand/TanStack Query misuse
- L2 — CI `grep -rn "queryKey.*['\"]" apps/web/src apps/browser-extension/src` to detect flat string keys
- L2 — CI `grep -c "^\s*[a-zA-Z].*:" apps/web/src/stores/*.ts` returning count >5

## Violation Signal

- `grep -rn "useEffect" apps/web/src` combined with `grep -rn "fetch("` returns components fetching without `@tanstack/react-query`
- `grep -rn "create(" apps/web/src --exclude-dir=stores` returns Zustand `create()` calls outside `apps/web/src/stores/`
- `grep -rn "useStore\|setQueryData" apps/web/src/**/*.tsx` flags form components writing ephemeral field values into Zustand or TanStack Query cache
- `grep -rn "queryKey.*['\"]" apps/web/src apps/browser-extension/src` returns flat string query keys not using an array with domain prefix
- `grep -c "^\s*[a-zA-Z].*:" apps/web/src/stores/*.ts` returns count >5 for an oversized Zustand store

## Correct vs. Forbidden

```tsx
// Correct — apps/web/src/features/org/members-list.tsx
const { data } = useQuery({
    queryKey: ["org", orgId, "members"],
    queryFn: () => client.org.members({ orgId }),
});

// Forbidden — raw fetch in useEffect
useEffect(() => {
    fetch(`/api/org/${orgId}/members`).then(r => r.json()).then(setData);
}, [orgId]);
```

```ts
// Correct store location: apps/web/src/stores/sidebar-store.ts
// Forbidden store location: apps/web/src/components/sidebar/use-sidebar-state.ts (contains create())
```

## Remediation

- **useEffect+fetch** — replace with a `useQuery` wrapping the `@repo/contracts` oRPC client method and a structured array query key
- **Zustand outside stores/** — move the store to `apps/web/src/stores/` with a kebab-case filename and update import paths
- **Form state in Zustand** — refactor to `useState` or `react-hook-form` for all ephemeral input state
- **Flat query key** — rewrite as a typed array: `[domain, ...identifiers]`
- **Oversized store** — split into focused slice files, each handling one domain concern with ≤5 state fields

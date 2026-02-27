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

Standardizes how `apps/web` and `apps/browser-extension` handle server data, shared client state, and ephemeral form state. Server data flows through TanStack Query via oRPC utilities, shared UI state lives in Zustand, and form-local state stays in React hooks.

## Rules

- IF a component in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` fetches data from an oRPC procedure THEN it MUST use `orpc.<procedure>.queryOptions()` from `@orpc/tanstack-query` passed into `useQuery` — not a raw `queryFn` or `useEffect`-based fetching
- IF a component in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` calls a mutating oRPC procedure THEN it MUST use `orpc.<procedure>.mutationOptions()` from `@orpc/tanstack-query` passed into `useMutation`
- IF state in `apps/web/` needs to be shared across 2 or more unrelated component trees THEN it MUST live in a Zustand store under `apps/web/src/stores/` instead of being prop-drilled
- IF a form in `apps/web/**/*.tsx` manages its own field values THEN it MUST use React `useState` or `react-hook-form` — ephemeral form values MUST NOT be stored in a Zustand store or TanStack Query cache
- IF a Zustand store in `apps/web/src/stores/` exports more than 5 top-level state fields THEN split it into focused slice files

## Enforcement

- L2 — CI `grep -rn "useQuery\|useMutation" apps/web/src apps/browser-extension/src` to detect calls not using `@orpc/tanstack-query` utilities
- L2 — CI `grep -rn "useMutation" apps/web/src apps/browser-extension/src` cross-referenced against `mutationOptions` usage
- L2 — CI `grep -rn "create(" apps/web/src --exclude-dir=stores` to find Zustand stores outside `apps/web/src/stores/`
- L3 — code review on `apps/web/**/*.tsx` form components for Zustand/TanStack Query misuse
- L2 — CI `grep -c "^\s*[a-zA-Z].*:" apps/web/src/stores/*.ts` returning count >5

## Violation Signal

- `grep -rn "queryFn:" apps/web/src apps/browser-extension/src` returns manual `queryFn` definitions that bypass `@orpc/tanstack-query` utilities
- `grep -rn "useMutation" apps/web/src apps/browser-extension/src --include="*.tsx"` returns calls not passing `mutationOptions()` output
- `grep -rn "create(" apps/web/src --exclude-dir=stores` returns Zustand `create()` calls outside `apps/web/src/stores/`
- `grep -rn "useStore\|setQueryData" apps/web/src/**/*.tsx` flags form components writing ephemeral field values into Zustand or TanStack Query cache
- `grep -c "^\s*[a-zA-Z].*:" apps/web/src/stores/*.ts` returns count >5 for an oversized Zustand store

## Correct vs. Forbidden

```tsx
// Correct — apps/web/src/features/org/members-list.tsx
import { useQuery } from "@tanstack/react-query";
import { orpc } from "@repo/contracts";

function MembersList({ orgId }: { orgId: string }) {
    const { data } = useQuery(orpc.org.members.queryOptions({ input: { orgId } }));
    return <ul>{data?.map((m) => <li key={m.id}>{m.name}</li>)}</ul>;
}

// Forbidden — manual queryKey/queryFn bypasses oRPC type safety
const { data } = useQuery({
    queryKey: ["org", orgId, "members"],
    queryFn: () => fetch(`/api/org/${orgId}/members`).then(r => r.json()),
});
```

```ts
// Correct store location: apps/web/src/stores/sidebar-store.ts
// Forbidden: apps/web/src/components/sidebar/use-sidebar-state.ts containing Zustand create()
```

## Remediation

- **Manual queryFn** — replace with `useQuery(orpc.<procedure>.queryOptions({ input: ... }))` using the `@orpc/tanstack-query` utility
- **Manual mutationFn** — replace with `useMutation(orpc.<procedure>.mutationOptions())`
- **Zustand outside stores/** — move to `apps/web/src/stores/` with a kebab-case filename and update imports
- **Form state in Zustand** — refactor to `useState` or `react-hook-form` for all ephemeral input state
- **Oversized store** — split into focused slice files, each handling one domain concern with ≤5 state fields

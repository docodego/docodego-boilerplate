---
id: CONV-2026-005
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Hooks Conventions

## Intent

Enforces consistent React hook authoring across `apps/web`, `apps/mobile`, and `apps/browser-extension`. Mandates the `use` prefix, restricts side effects to `useEffect`, prohibits redundant effect-based state sync, requires explicit dependency arrays, and limits `useState` proliferation.

## Rules

- IF a function in `apps/web/**`, `apps/mobile/**`, or `apps/browser-extension/**` calls any React hook internally THEN the function name MUST start with `use` so the rules-of-hooks linter can track call order
- IF a custom hook in `apps/web/**/*.ts` or `apps/browser-extension/**/*.ts` executes a side effect (fetch, DOM mutation, subscription) THEN that side effect MUST be inside a `useEffect` call and never at the hook body top level
- IF a `useEffect` in `apps/web/**/*.tsx` writes to a `useState` setter where the value derives entirely from existing state or props THEN replace it with `useMemo` or inline derivation
- IF a `useEffect`, `useCallback`, or `useMemo` call in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx` omits the dependency array THEN `biome` rule `useExhaustiveDependencies` blocks the build
- IF a component in `apps/web/**/*.tsx` contains 3 or more `useState` calls managing related state THEN extract them into a named custom hook in the same directory

## Enforcement

- L1 — `biome` rule `useHookAtTopLevel` on `apps/web/**`, `apps/mobile/**`, `apps/browser-extension/**`
- L2 — CI `grep -rn "fetch\|addEventListener" apps/web/src/**/use*.ts apps/browser-extension/src/**/use*.ts` outside `useEffect`
- L2 — CI `grep -Pn "useEffect.*set[A-Z]" apps/web/src/**/*.tsx`
- L1 — `biome` rule `useExhaustiveDependencies` on `apps/web/**/*.tsx` and `apps/browser-extension/**/*.tsx`
- L3 — code review on `apps/web/**/*.tsx` components with 3+ related `useState` calls

## Violation Signal

- `biome` rule `useHookAtTopLevel` fires on hook calls in non-`use`-prefixed functions in `apps/web/**`, `apps/mobile/**`, `apps/browser-extension/**`
- `grep -rn "fetch\|addEventListener" apps/web/src/**/use*.ts` returns side effects outside `useEffect`
- `grep -Pn "useEffect.*set[A-Z]" apps/web/src/**/*.tsx` returns effects writing derived state to `useState` setters
- `biome` rule `useExhaustiveDependencies` fires on missing dependency arrays in `apps/web/**/*.tsx` or `apps/browser-extension/**/*.tsx`
- `grep -c "useState" apps/web/src/**/*.tsx` returns count ≥3 per component file

## Correct vs. Forbidden

```ts
// Correct — apps/web/src/hooks/use-auth.ts
function useAuth() {
    const [user, setUser] = useState<User | null>(null);
    useEffect(() => { fetchCurrentUser().then(setUser); }, []);
    return { user };
}

// Forbidden — non-use prefix, top-level side effect
function getAuth() {
    const sub = subscribe("user", () => {}); // top-level side effect
    return sub;
}
```

```tsx
// Correct — apps/web/src/components/product-list.tsx
const total = useMemo(() => items.reduce((s, i) => s + i.price, 0), [items]);

// Forbidden — useEffect writing derived state
useEffect(() => { setTotal(items.reduce((s, i) => s + i.price, 0)); }, [items]);
```

## Remediation

- **`use` prefix** — rename the function to start with `use` and update all call sites
- **Top-level side effect** — move the side-effecting code into a `useEffect` with the correct dependency array
- **Effect-based state sync** — replace the effect+state pair with `useMemo` or inline derivation
- **Missing deps array** — add the dependency array with all referenced closure variables
- **`useState` proliferation** — create a `use-<feature>.ts` file in the same directory and move related state into it

---
id: CONV-2026-002
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# TypeScript Discipline

## Intent

This convention enforces strict TypeScript practices across all workspaces
in `apps/` and `packages/`. It eliminates unsafe type escape hatches,
mandates discriminated unions over boolean flag clusters, requires
`import type` for type-only imports, bans file extensions in import
paths, and ensures every tsconfig enables `verbatimModuleSyntax`.
These rules prevent runtime type errors, reduce bundle size by
tree-shaking type-only imports, and keep module resolution consistent
across web, api, mobile, desktop, browser-extension, library, contracts,
ui, and i18n workspaces.

## Rules

- IF a TypeScript file in `apps/**/*.ts` or `apps/**/*.tsx` uses `any` without an accompanying `// @ts-expect-error` comment on the same line or preceding line THEN `biome` lint blocks the commit and reports a `noExplicitAny` violation — one violation per occurrence in apps/ workspaces
- IF a TypeScript file in `packages/**/*.ts` or `packages/**/*.tsx` uses `any` without an accompanying `// @ts-expect-error` comment on the same line or preceding line THEN `biome` lint blocks the commit and reports a `noExplicitAny` violation — one violation per occurrence in packages/ workspaces
- IF a module in `apps/**/*.ts` or `packages/**/*.ts` models a state with multiple boolean flags like `isLoading` and `isError` instead of a discriminated union with a `status` field THEN the code review rejects the pull request — applies to all workspaces under apps/ and packages/
- IF a TypeScript file in `apps/**/*.ts` or `packages/**/*.ts` imports a type without the `import type` keyword THEN `biome` lint reports a `useImportType` violation and `tsc` emits an error because `verbatimModuleSyntax` is enabled — applies to web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n workspaces
- IF an import statement in `apps/**/*.ts` or `packages/**/*.ts` includes a file extension like `.ts`, `.tsx`, or `.js` THEN `biome` lint flags the import and the code review rejects it — `moduleResolution: "bundler"` handles resolution in all apps/ and packages/ workspaces
- IF a tsconfig at `apps/*/tsconfig.json` or `packages/*/tsconfig.json` does not set `verbatimModuleSyntax` to `true` THEN the CI check `grep -r "verbatimModuleSyntax" apps/*/tsconfig.json packages/*/tsconfig.json` detects the missing flag and blocks the merge — enforced across all workspace tsconfig files

## Enforcement

- **L1** — `noExplicitAny`: `biome lint` auto-detects `any` usage in `apps/**/*.ts` and `packages/**/*.ts` files and blocks the commit
- **L1** — `useImportType`: `biome lint` auto-detects missing `import type` in `apps/**/*.ts` and `packages/**/*.ts` files and blocks the commit
- **L1** — `verbatimModuleSyntax` compile check: `tsc --noEmit` emits error TS1484 when a type-only import lacks `import type` in `apps/` and `packages/` workspaces with `verbatimModuleSyntax` enabled
- **L2** — `verbatimModuleSyntax` config: CI script runs `grep -r "verbatimModuleSyntax" apps/*/tsconfig.json packages/*/tsconfig.json` and blocks the merge when any tsconfig omits the flag
- **L3** — discriminated unions: code review verifies that state objects in `apps/` and `packages/` use `status` discriminated unions instead of boolean flag clusters
- **L1** — no file extensions in imports: `biome lint` auto-detects file extensions in import paths across `apps/**/*.ts` and `packages/**/*.ts` files; code review additionally verifies compliance

## Violation Signal

- `biome` rule `noExplicitAny` reports each `any` usage without `// @ts-expect-error` in `apps/**/*.ts` and `packages/**/*.ts` files
- `biome` rule `useImportType` reports each type-only import missing the `type` keyword in `apps/**/*.ts` and `packages/**/*.ts` files
- `tsc --noEmit` emits error TS1484 when a type-only import lacks `import type` and `verbatimModuleSyntax` is `true` in `apps/*/tsconfig.json` and `packages/*/tsconfig.json`
- `grep -rn "isLoading.*boolean" apps/ packages/` detects boolean flag clusters that indicate missing discriminated unions in apps/ and packages/ workspaces
- `biome` lint detects file extensions in import paths across `apps/**/*.ts` and `packages/**/*.ts` — the rule flags `.ts`, `.tsx`, and `.js` suffixes
- `grep -rn "verbatimModuleSyntax" apps/*/tsconfig.json packages/*/tsconfig.json` verifies every workspace tsconfig includes the required flag

## Correct vs. Forbidden

**`any` usage (applies to `apps/**/*.ts` and `packages/**/*.ts`)**

```ts
// Forbidden
const data: any = fetchData();

// Correct — explicit type
const data: UserProfile = fetchData();

// Correct — explained escape hatch
// @ts-expect-error legacy API returns untyped blob
const data: unknown = legacyFetch();
```

**Discriminated union (applies to `apps/**/*.ts` and `packages/**/*.ts`)**

```ts
// Forbidden — boolean flag cluster
interface State {
    isLoading: boolean;
    isError: boolean;
    data: User | null;
}

// Correct — discriminated union
type State =
    | { status: "loading" }
    | { status: "error"; error: Error }
    | { status: "success"; data: User };
```

**Import type (applies to `apps/**/*.ts` and `packages/**/*.ts`)**

```ts
// Forbidden — value import for type-only usage
import { UserProfile } from "@repo/contracts";

// Correct — type keyword present
import type { UserProfile } from "@repo/contracts";
```

**File extension in imports (applies to `apps/**/*.ts` and `packages/**/*.ts`)**

```ts
// Forbidden — file extension present
import { validate } from "./validate.ts";

// Correct — no extension
import { validate } from "./validate";
```

## Remediation

When `biome` reports a `noExplicitAny` violation in `apps/**/*.ts` or `packages/**/*.ts`, replace `any` with the correct concrete type or use `unknown` with a `// @ts-expect-error` comment explaining the reason. When `biome` reports a `useImportType` violation, add the `type` keyword to the import statement. When a boolean flag cluster is found during review in apps/ or packages/ code, refactor the interface into a discriminated union with a `status` literal type field. When `grep` detects a missing `verbatimModuleSyntax` in `apps/*/tsconfig.json` or `packages/*/tsconfig.json`, add `"verbatimModuleSyntax": true` to the `compilerOptions` block of the offending tsconfig. When an import includes a file extension, remove the `.ts`, `.tsx`, or `.js` suffix from the import path.

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

Enforces strict TypeScript practices across all `apps/` and `packages/` workspaces. Eliminates unsafe type escape hatches, mandates discriminated unions, requires `import type` for type-only imports, and keeps module resolution consistent via `moduleResolution: "bundler"`.

## Rules

- IF a file in `apps/**/*.ts` or `packages/**/*.ts` uses `any` without a `// @ts-expect-error` comment THEN `biome` rule `noExplicitAny` blocks the build
- IF a module in `apps/**/*.ts` or `packages/**/*.ts` models state with multiple boolean flags (`isLoading`, `isError`) instead of a discriminated union THEN code review rejects the pull request
- IF a file in `apps/**/*.ts` or `packages/**/*.ts` imports a type without the `import type` keyword THEN `biome` rule `useImportType` and `tsc` with `verbatimModuleSyntax` block the build
- IF an import in `apps/**/*.ts` or `packages/**/*.ts` includes a file extension (`.ts`, `.tsx`, `.js`) THEN `biome` lint flags the import — `moduleResolution: "bundler"` handles resolution
- IF a tsconfig at `apps/*/tsconfig.json` or `packages/*/tsconfig.json` omits `verbatimModuleSyntax: true` THEN a CI `grep` check blocks the merge

## Enforcement

- L1 — `biome` rule `noExplicitAny` on `apps/**/*.ts` and `packages/**/*.ts`
- L3 — code review rejects boolean flag clusters in `apps/` and `packages/`
- L1 — `biome` rule `useImportType` + `tsc --noEmit` on `apps/` and `packages/`
- L1 — `biome` lint on import extensions in `apps/**/*.ts` and `packages/**/*.ts`
- L2 — CI `grep -r "verbatimModuleSyntax" apps/*/tsconfig.json packages/*/tsconfig.json`

## Violation Signal

- `biome` rule `noExplicitAny` fires per `any` without `// @ts-expect-error` in `apps/` or `packages/`
- `grep -rn "isLoading.*boolean" apps/ packages/` detects boolean flag clusters
- `biome` rule `useImportType` fires per missing `type` keyword in `apps/` or `packages/`; `tsc` emits TS1484
- `biome` lint flags `.ts`/`.tsx`/`.js` suffixes in import paths in `apps/` or `packages/`
- `grep -rn "verbatimModuleSyntax" apps/*/tsconfig.json packages/*/tsconfig.json` returns no match for missing flag

## Correct vs. Forbidden

```ts
// Correct — apps/web/src/data/user.ts
import type { UserProfile } from "@repo/contracts";
type State = { status: "loading" } | { status: "error"; error: Error } | { status: "success"; data: UserProfile };

// Forbidden — value import, boolean flags
import { UserProfile } from "@repo/contracts";
interface State { isLoading: boolean; isError: boolean; data: UserProfile | null; }
```

```ts
// Correct — no extension
import { validate } from "./validate";
// Forbidden — extension present
import { validate } from "./validate.ts";
```

## Remediation

- **`any`** — replace with a concrete type or use `unknown` with a `// @ts-expect-error` comment explaining the reason
- **Boolean flags** — refactor to a discriminated union with a `status` literal field
- **`import type`** — add the `type` keyword to all type-only import statements
- **File extension** — remove the `.ts`/`.tsx`/`.js` suffix from the import path
- **`verbatimModuleSyntax`** — add `"verbatimModuleSyntax": true` to `compilerOptions` in the offending tsconfig

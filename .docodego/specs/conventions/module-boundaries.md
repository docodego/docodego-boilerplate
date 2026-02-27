---
id: CONV-2026-003
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Module Boundaries

## Intent

This convention enforces strict import boundaries between workspaces in the docodego monorepo. Every workspace communicates through published `@repo/*` package exports rather than reaching into another workspace's internal source tree. Shared API types flow exclusively through `@repo/contracts`, and the `@repo/i18n` core export remains free of React dependencies. These boundaries prevent tight coupling, keep builds deterministic, and ensure that each workspace can be type-checked and tested in isolation.

## Rules

- IF a file in `apps/web/**`, `apps/mobile/**`, `apps/desktop/**`, or `apps/browser-extension/**` imports from `apps/api/src/` THEN `biome` `noRestrictedImports` blocks the build with a lint error — one violation per import statement in the web, mobile, desktop, or browser-extension workspace
- IF a TypeScript file in `apps/**` or `packages/**` references another workspace using a bare relative path (e.g., `../../packages/ui/src/button`) instead of the `@repo/<name>` scope THEN `tsc` fails to resolve the import because `paths` only maps `@repo/*` — applies to all workspaces under `apps/` and `packages/`
- IF any file in `packages/i18n/src/index.ts` or any re-export from the `@repo/i18n` core entry point imports from `react` or `react-dom` THEN `knip` reports an unlisted dependency and `tsc` emits a type error in non-React consumers — the i18n core export in `packages/i18n` remains React-free
- IF a frontend file in `apps/web/**`, `apps/mobile/**`, `apps/desktop/**`, or `apps/browser-extension/**` calls `fetch()` directly against an internal api route instead of using the `@repo/contracts` oRPC client THEN `grep` detects the raw fetch pattern and the CI check fails — all cross-workspace api calls in web, mobile, desktop, and browser-extension use `@repo/contracts`

## Enforcement

- **L1** — `biome` `noRestrictedImports` rule auto-blocks direct `apps/api/src/` imports from `apps/web`, `apps/mobile`, `apps/desktop`, and `apps/browser-extension` at lint time
- **L1** — `tsc` path resolution rejects bare relative cross-workspace imports; only `@repo/*` aliases resolve across `apps/` and `packages/` boundaries
- **L2** — `knip` detects undeclared React dependencies in `packages/i18n/src/index.ts` via `pnpm knip --include dependencies` during CI
- **L2** — CI script runs `grep -rn "fetch(" apps/web/src apps/mobile/src apps/desktop/src apps/browser-extension/src` and flags raw fetch calls that bypass `@repo/contracts` oRPC client wrappers

## Violation Signal

- `biome` rule `noRestrictedImports` fires when any file in `apps/web/**`, `apps/mobile/**`, `apps/desktop/**`, or `apps/browser-extension/**` contains an import path starting with `apps/api/src/` or a relative path resolving into the api workspace
- `tsc` emits error TS2307 (cannot find module) when a file in `apps/**` or `packages/**` uses a bare relative import like `../../packages/library/src/utils` instead of `@repo/library`
- `knip` reports unlisted dependency `react` in `packages/i18n` when `packages/i18n/src/index.ts` contains `import ... from "react"` — run `pnpm knip --include dependencies`
- `grep -rn "fetch(" apps/web/src apps/mobile/src apps/desktop/src apps/browser-extension/src` returns matches for raw `fetch()` calls that bypass the `@repo/contracts` oRPC client in frontend workspaces

## Correct vs. Forbidden

**Rule 1 — API type imports**

```ts
// Correct: import shared types via @repo/contracts in apps/web
import type { UserResponse } from "@repo/contracts";

// Forbidden: reach into api internals from apps/web
import type { UserResponse } from "../../apps/api/src/routes/user";
```

**Rule 2 — Cross-workspace imports**

```ts
// Correct: use @repo scope from apps/mobile
import { validators } from "@repo/library";

// Forbidden: bare relative path from apps/mobile into packages/library
import { validators } from "../../packages/library/src/validators";
```

**Rule 3 — i18n React isolation**

```ts
// Correct: packages/i18n/src/index.ts exports only pure i18n utilities
export { t, changeLanguage, supportedLocales } from "./core";

// Forbidden: packages/i18n/src/index.ts re-exports React bindings
export { useTranslation } from "./react"; // pulls in react dependency
```

```ts
// Correct: React consumers import from the subpath
import { useTranslation } from "@repo/i18n/react";
```

**Rule 4 — API calls via contracts**

```ts
// Correct: use oRPC client from @repo/contracts in apps/web
import { client } from "@repo/contracts";
const users = await client.user.list();

// Forbidden: raw fetch in apps/web bypassing @repo/contracts
const users = await fetch("/api/users").then((r) => r.json());
```

## Remediation

When a violation is detected, follow these steps to restore compliance with the workspace boundary rules across `apps/` and `packages/`:

1. **Direct api import violation** — Replace the relative import path targeting `apps/api/src/` with a type-only import from `@repo/contracts`. If the needed type does not exist in contracts, add a new oRPC contract definition in `packages/contracts/src/` and export it from the package entry point before updating the consuming file in web, mobile, desktop, or browser-extension.

2. **Bare relative cross-workspace import** — Replace the relative path with the corresponding `@repo/<name>` scoped import. Verify that the target package exports the needed symbol from its entry point in `packages/<name>/src/index.ts`. If the export is missing, add it to the package public api and re-run `tsc` across all workspaces with `pnpm typecheck`.

3. **React in i18n core violation** — Move the React-dependent code from `packages/i18n/src/index.ts` into `packages/i18n/src/react.ts` (the `@repo/i18n/react` subpath). Update all consumers that imported React bindings from `@repo/i18n` to import from `@repo/i18n/react` instead. Run `pnpm knip --include dependencies` to confirm that `react` no longer appears as a dependency of the i18n core.

4. **Raw fetch bypassing contracts** — Replace the `fetch()` call with the corresponding oRPC client method from `@repo/contracts`. If the endpoint lacks a contract definition, create one in `packages/contracts/src/` that matches the api route handler signature. Run `grep -rn "fetch(" apps/web/src apps/mobile/src` to confirm no raw fetch calls remain in frontend workspaces.

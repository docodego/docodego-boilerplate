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

Enforces strict import boundaries between workspaces. Every workspace communicates through `@repo/*` package exports; shared API types flow through `@repo/contracts`; the `@repo/i18n` core stays React-free. These boundaries keep builds deterministic and allow each workspace to be type-checked in isolation.

## Rules

- IF a file in `apps/web/**`, `apps/mobile/**`, `apps/desktop/**`, or `apps/browser-extension/**` imports from `apps/api/src/` THEN `biome` rule `noRestrictedImports` blocks the build
- IF a file in `apps/**` or `packages/**` references another workspace via a bare relative path instead of `@repo/<name>` THEN `tsc` fails to resolve the import — only `@repo/*` paths are mapped
- IF `packages/i18n/src/index.ts` or any `@repo/i18n` re-export imports from `react` or `react-dom` THEN `knip` reports an unlisted dependency and `tsc` emits a type error in non-React consumers
- IF a file in `apps/web/**`, `apps/mobile/**`, `apps/desktop/**`, or `apps/browser-extension/**` calls `fetch()` directly against an internal API route THEN a CI `grep` check flags the raw fetch pattern

## Enforcement

- L1 — `biome` rule `noRestrictedImports` on `apps/web`, `apps/mobile`, `apps/desktop`, `apps/browser-extension`
- L1 — `tsc` path resolution rejects bare relative cross-workspace imports in `apps/` and `packages/`
- L2 — `pnpm knip --include dependencies` on `packages/i18n`
- L2 — CI `grep -rn "fetch(" apps/web/src apps/mobile/src apps/desktop/src apps/browser-extension/src`

## Violation Signal

- `biome` rule `noRestrictedImports` fires on `apps/api/src/` imports from frontend workspaces
- `tsc` emits TS2307 on bare relative paths like `../../packages/library/src/utils` in `apps/` or `packages/`
- `knip` reports unlisted dependency `react` in `packages/i18n` — run `pnpm knip --include dependencies`
- `grep -rn "fetch(" apps/web/src apps/mobile/src apps/desktop/src apps/browser-extension/src` returns raw fetch calls

## Correct vs. Forbidden

```ts
// Correct — apps/web uses @repo/contracts for API types
import type { UserResponse } from "@repo/contracts";

// Forbidden — direct import from apps/api internals
import type { UserResponse } from "../../apps/api/src/routes/user";
```

```ts
// Correct — @repo/i18n/react subpath for React bindings
import { useTranslation } from "@repo/i18n/react";

// Forbidden — React binding in packages/i18n core entry
export { useTranslation } from "./react"; // in packages/i18n/src/index.ts
```

## Remediation

- **Direct API import** — replace with a type import from `@repo/contracts`; add the type to `packages/contracts/src/` if missing
- **Bare relative path** — replace with `@repo/<name>` scoped import; verify the symbol is exported from the package entry point
- **React in i18n core** — move React-dependent code to `packages/i18n/src/react.ts` and update consumers to import from `@repo/i18n/react`
- **Raw fetch** — replace with the corresponding `@repo/contracts` oRPC client method

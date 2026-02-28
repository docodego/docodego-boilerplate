---
id: CONV-2026-008
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Error Handling Conventions

## Intent

Standardizes error propagation, classification, and user-facing messaging across the api and web workspaces. Prevents silent error swallowing, enforces a typed error hierarchy, and requires i18n keys for every user-visible message.

## Rules

- IF code in `apps/api/src/**/*.ts` throws an error THEN it MUST throw an instance of `AppError` or a subclass defined in `packages/library/src/errors.ts` with a typed `code` string and numeric `statusCode` — never throw plain `new Error()`
- IF a service function in `apps/api/src/services/**/*.ts` catches an error it cannot handle THEN it MUST rethrow the original error; only Hono route handlers in `apps/api/src/routes/**/*.ts` convert errors to HTTP responses
- IF a user-facing error message is returned from `apps/api/src/**/*.ts` or rendered in `apps/web/src/**/*.tsx` THEN the message string MUST reference an `@repo/i18n` translation key — never a hardcoded English literal
- IF a `catch` block in `apps/api/src/**/*.ts` or `apps/web/src/**/*.ts` calls `console.error` without rethrowing or returning an error response THEN `biome` lint rule `noConsole` flags the silent swallow

## Enforcement

- L1 — `tsc` type-checks `AppError` usage in `apps/api/src/**`
- L2 — CI `grep -rn "throw new Error("` in `apps/api/src/**` detects plain Error throws
- L2 — CI `grep -rn "catch" apps/api/src/services/**` detects service-layer swallows without rethrow
- L1 — `biome` rule `noConsole` on `apps/api/src/**` and `apps/web/src/**`

## Violation Signal

- `tsc --noEmit` reports type errors when `apps/api/src/**` code throws non-`AppError` instances
- `grep -rn "throw new Error(" apps/api/src/` returns lines throwing plain `Error` instead of `AppError`
- `grep -rn "catch" apps/api/src/services/` returns catch blocks that do not rethrow in service files
- `biome lint` rule `noConsole` fires on `console.error` calls in `apps/api/src/**` or `apps/web/src/**` catch blocks

## Correct vs. Forbidden

```ts
// Correct — apps/api/src/routes/auth.ts
import { AppError } from "@repo/library/errors";
throw new AppError("AUTH_EXPIRED", 401);

// Forbidden — plain Error in apps/api/src/routes/auth.ts
throw new Error("token expired");
```

```ts
// Correct — apps/web/src/components/login-form.tsx
const msg = t("errors.auth_expired");

// Forbidden — hardcoded string in apps/web/src/components/login-form.tsx
const msg = "Your session has expired";
```

## Remediation

- **Plain Error** — replace `throw new Error(...)` with `throw new AppError(code, statusCode)` using a typed code from `packages/library/src/errors.ts`
- **Service swallow** — remove the `catch` block or add `throw error` at the end of the catch body in `apps/api/src/services/**`
- **Hardcoded message** — add a translation key to the `@repo/i18n` namespace and replace the literal string with `t("errors.<key>")`
- **Silent console.error** — either rethrow the error after logging or return an error response to the caller

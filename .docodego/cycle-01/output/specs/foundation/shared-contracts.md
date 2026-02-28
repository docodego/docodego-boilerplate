---
id: SPEC-2026-008
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: approved
roles: [Framework Adopter]
---

[← Back to Roadmap](../ROADMAP.md)

# Shared Contracts

## Intent

This spec defines the `@repo/contracts` package that serves as the
single source of truth for all API type definitions shared between
the backend (`apps/api`) and frontend consumers (`apps/web`,
`apps/browser-extension`). The package uses oRPC contract definitions
with Zod v4 schemas to declare every RPC endpoint's input and output
types. By defining contracts in a shared package rather than inline
in route handlers, the monorepo enforces compile-time type safety
across the API boundary — any schema change in contracts immediately
surfaces type errors in both the server implementation and client
consumption code. This spec ensures that the contracts package is
structured correctly, exports typed definitions, and integrates
with oRPC's OpenAPI generation.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `@orpc/contract` | read | Build time and runtime when defining contract routes with `oc.input()` and `oc.output()` | Build fails at compile time because oRPC contract builder functions are unresolved and CI alerts to block deployment |
| `zod` (v4) | read | Build time and runtime when declaring input/output validation schemas for every endpoint | Build fails at compile time because Zod schema types are unresolved and CI alerts to block deployment |
| `apps/api` (oRPC router) | read | App startup when the oRPC router imports contract definitions to register typed route handlers | API server cannot start because route handler types are unresolved, returning 500 on all oRPC endpoints until contracts are restored |
| `apps/web` (oRPC client) | read | Build time and runtime when the frontend generates typed oRPC client calls from contract schemas | Frontend build fails because the oRPC client cannot resolve endpoint types and CI alerts to block deployment |
| `apps/browser-extension` | read | Build time and runtime when the extension generates typed oRPC client calls from contract schemas | Extension build fails because the oRPC client cannot resolve endpoint types and CI alerts to block deployment |

## Behavioral Flow

1. **[Developer]** → creates or modifies a Zod schema inside
    `packages/contracts/src/` using `oc.input()` and `oc.output()`
    to define the endpoint's request and response shapes
2. **[TypeScript compiler]** → validates the schema definitions
    at build time and surfaces type errors if the Zod v4 syntax
    is incorrect or if types are inconsistent across the contract
3. **[oRPC router in apps/api]** → imports contract definitions
    from `@repo/contracts` and registers route handlers whose
    input/output types are constrained by the contract schemas
4. **[oRPC client in apps/web]** → imports contract definitions
    from `@repo/contracts` and generates typed client functions
    that enforce the same input/output shapes at the call site
5. **[oRPC OpenAPI generator]** → reads the Zod schemas from
    the imported contracts at runtime and produces an OpenAPI
    specification containing endpoint definitions and schemas
6. **[CI pipeline]** → runs `pnpm typecheck` across all
    workspaces, and any mismatch between a contract schema and
    its consumers produces at least 1 type error that blocks
    deployment

## State Machine

No stateful entities. The contracts package is a compile-time type
definition layer with no runtime lifecycle — contracts are static
schema declarations that do not transition between states.

## Business Rules

No conditional business rules. Contract schemas define structural
validation (field presence, types, constraints) unconditionally —
there is no branching logic based on runtime conditions within the
contracts package itself.

## Permission Model

Single role; no permission model is needed. The contracts package
is a shared type definition layer consumed identically by all
workspaces — there are no user roles or access controls within
the package itself because all consumers have equal read access
to every exported contract definition.

## Acceptance Criteria

- [ ] The `packages/contracts` directory is present and contains a `package.json` with `"name"` equal to `"@repo/contracts"` — the name field value equals `"@repo/contracts"` exactly
- [ ] The `package.json` sets `"type"` to `"module"` (present) and `"private"` to true — both fields are present with those exact values
- [ ] The package depends on `@orpc/contract` and `zod` via catalog references — both dependencies are present in `package.json` and each version string equals `"catalog:"`
- [ ] At least 1 contract file is present in `packages/contracts/src/` that exports typed oRPC contract definitions — the export count is >= 1
- [ ] Every contract definition uses `oc.input()` and `oc.output()` with Zod schemas — the count of contract endpoints without Zod validation equals 0
- [ ] The `zod` dependency resolves to Zod v4 — the version in the pnpm catalog equals `^4.0.0` or above and is present in the lockfile
- [ ] The `"exports"` field in `package.json` is present and non-empty — at least 1 subpath export entry is present mapping to a valid module path
- [ ] The `apps/api` workspace imports contracts from `@repo/contracts` — at least 1 import statement referencing `@repo/contracts` is present in the API source
- [ ] The `apps/web` workspace imports contracts from `@repo/contracts` — at least 1 import statement referencing `@repo/contracts` is present in the web source
- [ ] Running `pnpm typecheck` after adding a required field to a contract schema produces at least 1 type error in consuming workspaces — the error count is >= 1
- [ ] The oRPC server router derives its OpenAPI spec from contract Zod schemas — the generated spec is present and contains at least 1 endpoint definition
- [ ] The `package.json` contains both a `"typecheck"` script and a `"test"` script — both are present and non-empty string values
- [ ] Running `pnpm --filter contracts typecheck` exits with code = 0 and produces 0 type errors — the exit code equals 0

## Constraints

- All request and response schemas are defined in
    `@repo/contracts`, never inline in route handlers or client
    code. The count of Zod schema definitions for API
    input/output in `apps/api/src/` route files equals 0 —
    handlers reference contracts exclusively. This separation
    ensures that schema changes are caught at compile time on
    both sides of the API boundary.
- The contracts package has exactly 2 runtime dependencies:
    `@orpc/contract` and `zod`. The count of additional runtime
    dependencies in `package.json` equals 0. Development
    dependencies for TypeScript tooling are permitted but the
    package does not pull in React, Hono, or any
    platform-specific library.
- The package never imports from `apps/*` workspaces —
    dependency flow is unidirectional from `packages/contracts`
    to `apps/*`. The count of import statements referencing
    `apps/` in the contracts source files equals 0.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A developer adds a required field to a contract input schema but does not update the frontend consumer that calls that endpoint | The TypeScript compiler surfaces at least 1 type error in the consuming workspace during `pnpm typecheck` because the oRPC client type no longer matches the updated contract | `pnpm typecheck` exits with a non-zero code and the error output references the consuming file and the missing field name |
| A developer removes an existing contract export that is still imported by `apps/api` or `apps/web` | The TypeScript compiler surfaces an unresolved import error in every consuming workspace that references the deleted export | `pnpm typecheck` exits with a non-zero code and the error output references the deleted export name and the consuming file path |
| A developer defines a Zod schema inline in an API route handler instead of importing it from `@repo/contracts` | The oRPC router type binding rejects the inline schema because the route handler type is constrained by the contract definition, producing a type error at compile time | `pnpm typecheck` exits with a non-zero code and the error output references a type mismatch between the inline schema and the contract type |
| The contracts package `package.json` is missing the `"exports"` field or has an empty exports map | Consuming workspaces cannot resolve `@repo/contracts` subpath imports, causing build failures in `apps/api` and `apps/web` | `pnpm typecheck` exits with a non-zero code and the error output references an unresolved module specifier for `@repo/contracts` |
| A developer upgrades `zod` to a version that is incompatible with `@orpc/contract` type inference | The TypeScript compiler surfaces type errors in the contract files where `oc.input()` and `oc.output()` receive schemas whose inferred types do not match the expected oRPC contract builder signatures | `pnpm typecheck` exits with a non-zero code and the error output references a type mismatch in the contract definition files |

## Failure Modes

- **Schema drift between server and client**
    - **What happens:** A developer modifies a Zod schema in the API route handler instead of in `@repo/contracts`, causing the server to accept different input than the client sends based on stale contract types.
    - **Source:** Incorrect developer workflow that bypasses the shared contracts package by defining schemas inline in route handler files.
    - **Consequence:** The server validates against a different schema than the client expects, leading to runtime 400 errors on requests that the frontend considers valid.
    - **Recovery:** The CI typecheck step alerts on the type mismatch because the route handler's inline schema does not match the contract type, and deployment is blocked until the developer moves the schema change back to `@repo/contracts`.
- **Breaking contract change without consumer update**
    - **What happens:** A developer adds a new required field to a contract input schema but does not update the frontend form that calls that endpoint, causing runtime 400 validation errors for end users.
    - **Source:** Incomplete change propagation where the contract schema is updated but consuming workspaces are not updated to supply the new required field.
    - **Consequence:** The oRPC client sends requests missing the new required field, and the server rejects them with 400 status codes, breaking the affected user workflow entirely.
    - **Recovery:** The CI typecheck step alerts with a type mismatch diagnostic listing the missing field and the consuming file path, and deployment is blocked until all consuming workspaces are updated to match the new contract schema.
- **Circular dependency between contracts and apps**
    - **What happens:** A developer imports an app-specific utility from `apps/api` or `apps/web` into `@repo/contracts`, creating a circular dependency that breaks the unidirectional dependency flow required by the monorepo architecture.
    - **Source:** Incorrect import added to the contracts package that references an `apps/*` workspace, violating the package boundary constraint.
    - **Consequence:** Turborepo's topological build fails with a cycle detection error, preventing all workspaces from building and blocking the entire CI pipeline.
    - **Recovery:** The build step alerts with a cycle detection diagnostic identifying the import chain, and the developer removes the app import and moves the shared utility to `@repo/library` instead, restoring the unidirectional dependency flow.
- **Missing or invalid package exports configuration**
    - **What happens:** The `"exports"` field in the contracts `package.json` is deleted, misconfigured, or points to a non-existent file path, preventing consuming workspaces from resolving `@repo/contracts` subpath imports.
    - **Source:** Incorrect manual edit to the contracts `package.json` that removes or corrupts the exports map entries for the package subpaths.
    - **Consequence:** All workspaces that import from `@repo/contracts` fail to resolve the module specifier, causing build failures across `apps/api`, `apps/web`, and `apps/browser-extension` simultaneously.
    - **Recovery:** The CI typecheck step alerts with unresolved module errors referencing the `@repo/contracts` import paths, and deployment degrades to a full block until the developer restores the correct `"exports"` field mapping in the contracts `package.json`.

## Declared Omissions

- The oRPC server router implementation, middleware stack,
    and error handling configuration are not covered here and
    are defined in `api-framework.md` instead of this spec
- The oRPC client configuration, TanStack Query integration,
    and frontend retry logic are not covered here and are
    defined in behavioral specs instead of this spec
- Zod schema design patterns, custom validation rules, and
    field-level error message formatting are implementation
    details left to the developer and are not constrained by
    this spec
- Runtime validation error formatting, HTTP status code
    mapping, and error response structure are not covered here
    and are defined in `api-framework.md` error handler section

## Related Specifications

- [api-framework](api-framework.md) — Defines the Hono app,
    oRPC router integration, and error handling that consumes
    the contracts defined in this package at runtime
- [database-schema](database-schema.md) — Defines the Drizzle
    ORM table schemas whose column types inform the Zod schemas
    used in contract input and output definitions
- [shared-i18n](shared-i18n.md) — Defines the i18n
    infrastructure whose translation keys are referenced in
    contract error messages returned by the API framework
- [ci-cd-pipelines](ci-cd-pipelines.md) — Defines the CI
    pipeline that runs `pnpm typecheck` across all workspaces to
    enforce contract type safety at the deployment gate

[← Back to Roadmap](../ROADMAP.md)

# Shared Contracts

## Intent

This spec defines the `@repo/contracts` package that serves as the single source of truth for all API type definitions shared between the backend (`apps/api`) and frontend consumers (`apps/web`, `apps/browser-extension`). The package uses oRPC contract definitions with Zod v4 schemas to declare every RPC endpoint's input and output types. By defining contracts in a shared package rather than inline in route handlers, the monorepo enforces compile-time type safety across the API boundary — any schema change in contracts immediately surfaces type errors in both the server implementation and client consumption code. This spec ensures that the contracts package is structured correctly, exports typed definitions, and integrates with oRPC's OpenAPI generation.

## Acceptance Criteria

- [ ] The `packages/contracts` directory is present and contains a `package.json` with `"name"` set to `"@repo/contracts"`
- [ ] The `package.json` sets `"type"` to `"module"` and `"private"` to true
- [ ] The package depends on `@orpc/contract` and `zod` via catalog references — both dependencies are present and use `"catalog:"` versions
- [ ] At least 1 contract file is present in `packages/contracts/src/` that exports typed oRPC contract definitions
- [ ] Every contract definition uses `oc.input()` and `oc.output()` with Zod schemas — the count of contract endpoints without Zod validation equals 0
- [ ] All Zod schemas use Zod v4 syntax — the `zod` import resolves to version `^4.0.0` as defined in the catalog
- [ ] The package exports its contracts via the `"exports"` field in `package.json` — at least 1 subpath export is present and non-empty
- [ ] The `apps/api` workspace imports contracts from `@repo/contracts` — at least 1 import statement referencing `@repo/contracts` is present in the API source files
- [ ] The `apps/web` workspace imports contracts from `@repo/contracts` — at least 1 import statement referencing `@repo/contracts` is present in the web source files
- [ ] Running `pnpm typecheck` with a modified contract schema (e.g., adding a required field) produces at least 1 type error in consuming workspaces that have not been updated — the error count is >= 1
- [ ] The oRPC server router in `apps/api` derives its OpenAPI spec from the contract Zod schemas — the generated spec is present and contains at least 1 endpoint definition
- [ ] The package contains a `"typecheck"` script and a `"test"` script in `package.json` — both are present and non-empty
- [ ] Running `pnpm --filter contracts typecheck` exits with code = 0 and produces 0 errors

## Constraints

- All request and response schemas are defined in `@repo/contracts`, never inline in route handlers or client code. The count of Zod schema definitions for API input/output in `apps/api/src/` route files equals 0 — handlers reference contracts exclusively. This separation ensures that schema changes are caught at compile time on both sides of the API boundary.
- The contracts package has exactly 2 runtime dependencies: `@orpc/contract` and `zod`. The count of additional runtime dependencies in `package.json` equals 0. Development dependencies for TypeScript tooling are permitted but the package must not pull in React, Hono, or any platform-specific library.
- The package never imports from `apps/*` workspaces — dependency flow is unidirectional from `packages/contracts` to `apps/*`. The count of import statements referencing `apps/` in the contracts source files equals 0.

## Failure Modes

- **Schema drift between server and client**: A developer modifies a Zod schema in the API route handler instead of in `@repo/contracts`, causing the server to accept different input than the client sends. The CI typecheck step returns error because the route handler's inline schema does not match the contract type, and the developer is directed to update the contract in `@repo/contracts` instead of defining schemas inline.
- **Breaking contract change without consumer update**: A developer adds a new required field to a contract input schema but does not update the frontend form that calls that endpoint, causing runtime 400 errors. The CI typecheck step catches this because the oRPC client in `apps/web` expects the old type signature, and returns error with a type mismatch diagnostic listing the missing field and the consuming file.
- **Circular dependency between contracts and apps**: A developer imports an app-specific utility into `@repo/contracts`, creating a circular dependency that causes Turborepo's topological build to fail. The build step returns error with a cycle detection diagnostic identifying the import chain, and the developer removes the app import and moves the shared utility to `@repo/library` instead.

## Declared Omissions

- oRPC server router implementation and middleware (covered by `api-framework.md`)
- oRPC client configuration and TanStack Query integration (covered by behavioral specs)
- Zod schema design patterns and validation rules (implementation detail, not spec-level concern)
- Runtime validation error formatting (covered by `api-framework.md` error handler)

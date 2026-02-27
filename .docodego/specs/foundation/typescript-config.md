---
id: SPEC-2026-003
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: draft
roles: [Framework Adopter]
---

[← Back to Roadmap](../ROADMAP.md)

# TypeScript Config

## Intent

This spec defines the TypeScript compiler configuration hierarchy
for the DoCodeGo boilerplate monorepo. Every workspace compiles
under strict mode with a shared base configuration, and each
workspace extends this base with platform-specific overrides. The
configuration enforces `moduleResolution: "bundler"` for
extensionless imports, `verbatimModuleSyntax: true` for explicit
type-only import syntax, and ES2024 as the compilation target.
This spec ensures type safety is consistent across all 5
application targets and 4 shared packages, that path aliases
resolve correctly, and that the TypeScript compiler catches errors
uniformly regardless of which workspace a developer is editing.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `pnpm-workspace.yaml` catalog | read | Build or typecheck resolves the TypeScript version | Build fails at dependency resolution because the TypeScript version is absent from the catalog and pnpm alerts with an unresolved dependency error |
| Turborepo `typecheck` pipeline | read | `pnpm typecheck` invokes `tsc` per workspace in dependency order | Turbo falls back to sequential execution and the developer sees a missing task warning but each workspace `tsc` still runs independently |
| Biome (formatter/linter) | read | `pnpm lint` reads source files that TypeScript also compiles | Biome operates independently of `tsc` — if TypeScript is misconfigured, Biome still runs but type errors remain unreported until `pnpm typecheck` executes |
| Bundlers (Vite, esbuild, Metro, WXT) | read | Each bundler reads the workspace `tsconfig.json` for path aliases and JSX settings | The bundler falls back to its own default resolution, causing import failures that surface as build-time errors with module-not-found diagnostics |
| `@cloudflare/workers-types` | read | `tsc` resolves Cloudflare Worker global types for the API workspace | The API workspace typecheck fails with missing type errors for `D1Database`, `R2Bucket`, and other Cloudflare binding types, and CI alerts on the failure |

## Behavioral Flow

1. **[Developer]** runs `pnpm typecheck` at the
    monorepo root directory
2. **[Turborepo]** reads the pipeline definition and invokes
    `tsc --noEmit` in each workspace in topological dependency
    order, starting with leaf packages first
3. **[tsc per workspace]** loads the workspace `tsconfig.json`,
    follows the `extends` chain to `tsconfig.base.json` at the
    monorepo root, merges compiler options, and resolves path
    aliases
4. **[tsc per workspace]** type-checks all included source files
    and reports diagnostics (errors and warnings) to stdout
5. **[Turborepo]** collects exit codes from all workspace
    typecheck runs — if any workspace returns a non-zero exit
    code, the overall `pnpm typecheck` command exits with code 1
6. **[CI pipeline]** treats a non-zero exit code from
    `pnpm typecheck` as a failed quality gate and blocks the
    deployment pipeline from proceeding

## State Machine

No stateful entities. TypeScript configuration is a static
hierarchy of JSON files — no entities have a lifecycle or state
transitions within this spec's scope.

## Business Rules

- **Rule base-inheritance:** IF a workspace `tsconfig.json`
    declares an `extends` field THEN the value references the
    root `tsconfig.base.json` via a relative path (not a
    `@repo/` package reference), ensuring all workspaces inherit
    the same strict-mode and module-resolution settings
- **Rule mobile-extends:** IF the workspace is `apps/mobile`
    THEN its `tsconfig.json` extends `expo/tsconfig.base` as the
    primary base, because Expo requires its own base config for
    Metro bundler compatibility with React Native
- **Rule path-alias-restriction:** IF a workspace defines a
    `paths` entry in its `tsconfig.json` THEN the workspace is
    either `apps/web` or `apps/browser-extension`, and the only
    alias defined is `@/*` mapping to `./src/*` for Shadcn
    component imports

## Permission Model

Single role; no permission model is needed because TypeScript
configuration files are edited by any developer with repository
write access and there are no role-based restrictions on config
changes.

## Acceptance Criteria

- [ ] A root `tsconfig.base.json` is present and sets `strict` to true, `target` to `"ES2024"`, `module` to `"ESNext"`, `moduleResolution` to `"bundler"`, and `verbatimModuleSyntax` to true — all 5 values are present in the file
- [ ] The root `tsconfig.base.json` sets `skipLibCheck` to true to avoid type-checking third-party declaration files — this value is present and equals true
- [ ] At least 8 workspace `tsconfig.json` files are present, and each one contains an `"extends"` field that references the root base via a relative path (not a package reference) — 0 `extends` values contain `@repo/`
- [ ] The `apps/web` workspace `tsconfig.json` sets `"jsx"` to `"react-jsx"` and defines a `@/*` path alias that is present and maps to `"./src/*"` — both values are present in the config
- [ ] The `apps/api` workspace `tsconfig.json` includes `"@cloudflare/workers-types"` in its `types` array — this value is present in the config file
- [ ] The `apps/mobile` workspace `tsconfig.json` extends `expo/tsconfig.base` — this value is present in the `extends` field
- [ ] The `apps/desktop` workspace contains 0 TypeScript source files — only Rust code and configuration files are present in the workspace directory
- [ ] Running `pnpm typecheck` exits with code = 0 and produces 0 errors and 0 warnings on a clean checkout
- [ ] All imports between workspace packages use extensionless paths — 0 imports contain `.js`, `.ts`, or `.mjs` file extensions
- [ ] The `verbatimModuleSyntax` value equals true in the base config, and at least 90% of type-only imports across the codebase use the `import type` syntax
- [ ] Each shared package workspace (`packages/*`) sets `"declaration"` to true and `"declarationMap"` to true in its tsconfig — both values are present
- [ ] The `packages/contracts` workspace tsconfig sets `"noUncheckedIndexedAccess"` to true — this value is present and equals true
- [ ] Running `pnpm typecheck` completes in under 120 seconds on CI with warm Turborepo cache

## Constraints

- No workspace sets `moduleResolution` to `"node"` or `"node16"`
    — all workspace tsconfig files that declare
    `moduleResolution` set it to `"bundler"` exclusively, since
    every target goes through a bundler (Vite, esbuild, Metro,
    or WXT). The total count of non-bundler `moduleResolution`
    values across all tsconfig files equals 0.
- TypeScript version is pinned to `^5.9.3` via the pnpm catalog
    — running `pnpm ls typescript` across all workspaces returns
    the same major.minor version, and the catalog entry is
    present in `pnpm-workspace.yaml`.
- tsconfig `extends` chains use only relative paths (e.g.,
    `../../tsconfig.base.json`), never `@repo/` package
    references — the count of `@repo/` strings in tsconfig
    `extends` fields equals 0 across all workspaces.
- No workspace sets `strict` to false or disables any
    strict-mode sub-flag (`noImplicitAny`, `strictNullChecks`,
    `strictFunctionTypes`) — every workspace inherits
    `strict: true` from the base config and the count of `false`
    overrides for these flags equals 0.
- Path aliases are limited to `@/*` for Shadcn imports in
    `apps/web` and `apps/browser-extension` only — no other
    custom path aliases are defined, and the total count of
    `paths` entries across all other workspace tsconfigs
    equals 0.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A developer adds a new workspace without creating a `tsconfig.json` file or without an `extends` field pointing to the root base | Turborepo silently skips the typecheck for that workspace because no `typecheck` script is defined in the workspace `package.json`, and the missing config is not caught until a downstream consumer fails | CI alerts on the downstream failure and the developer adds the missing tsconfig with the correct `extends` chain |
| A workspace `tsconfig.json` sets `jsx` to `"react-jsx"` but the workspace does not have React as a dependency in its `package.json` | The `tsc` compiler emits an error because the JSX runtime module `react/jsx-runtime` cannot be resolved, and the typecheck exits with code 1 | `pnpm typecheck` output contains a diagnostic referencing the missing `react/jsx-runtime` module |
| A developer adds `.js` extensions to imports in a workspace that uses `moduleResolution: "bundler"` and extensionless imports everywhere else | The imports resolve correctly in that workspace but consumers importing from that package fail with module-not-found errors because the bundler does not strip extensions | `pnpm typecheck` on the consuming workspace exits with code 1 and the diagnostic names the unresolved `.js` import path |
| The `pnpm-workspace.yaml` catalog entry for TypeScript is removed or the version is changed to a different major version | All workspaces that reference `catalog:` for TypeScript fail at install time with an unresolved catalog reference error | `pnpm install` exits with a non-zero code and the error message names the missing catalog entry for `typescript` |
| Two workspaces define conflicting `paths` aliases — one maps `@/*` to `./src/*` and another maps `@/*` to `./lib/*` | Each workspace resolves its own `paths` alias independently because `tsc` scopes path resolution to the workspace `tsconfig.json`, so there is no cross-workspace collision | Both workspaces pass `pnpm typecheck` independently and the bundler resolves each alias within its own workspace context |

## Failure Modes

- **Strict mode regression**
    - **What happens:** A developer sets `strict` to false or
        `noImplicitAny` to false in a workspace tsconfig to
        suppress type errors, weakening type safety for that
        entire workspace.
    - **Source:** Manual override of inherited strict-mode flags
        in a workspace-level tsconfig file during development.
    - **Consequence:** The workspace compiles with implicit
        `any` types and null-safety gaps, allowing runtime type
        errors that the compiler would otherwise catch.
    - **Recovery:** The CI typecheck step alerts on the override
        because a config validation script returns error listing
        the workspace and the overridden flag that violated the
        strict-mode constraint, and deployment is blocked until
        the flag is restored.
- **Module resolution mismatch**
    - **What happens:** A workspace switches to
        `moduleResolution: "node16"` and adds `.js` extensions
        to imports, causing other workspaces that consume its
        exports to fail with resolution errors.
    - **Source:** Developer changes the module resolution
        strategy in a workspace tsconfig without updating
        downstream consumers.
    - **Consequence:** All workspaces importing from the changed
        package fail typecheck with "module not found"
        diagnostics, blocking the entire CI pipeline.
    - **Recovery:** The CI typecheck step alerts on the consuming
        workspace with "module not found" diagnostics, and the
        developer falls back to `"bundler"` resolution which is
        mandated by the base tsconfig for all workspaces.
- **Missing type declarations in shared packages**
    - **What happens:** A shared package builds without
        `declaration` set to true, causing downstream workspaces
        to lose type information and fall back to implicit `any`
        types for all exports from that package.
    - **Source:** Developer removes or omits the `declaration`
        and `declarationMap` flags from a shared package
        tsconfig.
    - **Consequence:** Downstream consumers compile with
        implicit `any` types for all imports from the affected
        package, defeating strict mode and hiding type errors.
    - **Recovery:** The CI typecheck step alerts on implicit
        `any` types in consuming workspaces because `strict: true`
        with `noImplicitAny` treats these as errors that block
        the build, and the developer adds the missing
        `declaration: true` flag.
- **Path alias collision with workspace protocol**
    - **What happens:** A developer adds a custom path alias in
        a workspace that conflicts with the `@repo/` workspace
        protocol scope, causing TypeScript to resolve the wrong
        module at compile time while the bundler resolves the
        correct one at build time.
    - **Source:** Unrestricted path alias definition in a
        workspace tsconfig that overlaps with the monorepo
        workspace protocol namespace.
    - **Consequence:** Type-checking passes with incorrect type
        information while the runtime uses different module
        resolutions, producing silent type mismatches that
        surface only at runtime.
    - **Recovery:** The CI build step alerts when the bundled
        output produces runtime type mismatches caught by Zod
        validation in the contracts package, and the developer
        falls back to using the `@repo/` workspace protocol
        instead of a custom path alias for cross-workspace
        imports.

## Declared Omissions

- Biome lint and format configuration is not covered in this
    spec — linting rules, formatting settings, and import
    sorting are defined in `code-quality.md` instead
- Per-workspace build tool configuration (Vite, Metro,
    Wrangler, WXT) is not covered here — bundler-specific
    settings are defined in the platform-specific specs for each
    application workspace
- Runtime type validation with Zod schemas is not covered in
    this spec — Zod schema definitions and oRPC contract types
    are defined in `shared-contracts.md` instead
- Type generation from Wrangler bindings or TanStack Router
    route trees is not covered here — generated type workflows
    are defined in the platform-specific specs for each
    application workspace
- CI pipeline configuration for running `pnpm typecheck` in
    GitHub Actions is not covered here — pipeline definitions
    and caching strategy are defined in `ci-cd-pipelines.md`

## Related Specifications

- [code-quality](code-quality.md) — Biome lint and format
    configuration that complements TypeScript type-checking with
    style enforcement and import sorting rules
- [shared-contracts](shared-contracts.md) — oRPC contract
    definitions and Zod schemas that depend on strict TypeScript
    compilation for type-safe API endpoint generation
- [ci-cd-pipelines](ci-cd-pipelines.md) — CI/CD pipeline
    configuration that runs `pnpm typecheck` as a quality gate
    before deployment to Cloudflare Workers
- [api-framework](api-framework.md) — Hono API framework
    configuration that depends on `@cloudflare/workers-types`
    being present in the API workspace tsconfig types array
- [monorepo-structure](monorepo-structure.md) — pnpm workspace and
    Turborepo configuration that defines the catalog entry for
    TypeScript version pinning and the typecheck pipeline task

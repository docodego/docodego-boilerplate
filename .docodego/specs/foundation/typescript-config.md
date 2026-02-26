[← Back to Roadmap](../ROADMAP.md)

# TypeScript Config

## Intent

This spec defines the TypeScript compiler configuration hierarchy for the DoCodeGo boilerplate monorepo. Every workspace compiles under strict mode with a shared base configuration, and each workspace extends this base with platform-specific overrides. The configuration enforces `moduleResolution: "bundler"` for extensionless imports, `verbatimModuleSyntax: true` for explicit type-only import syntax, and ES2024 as the compilation target. This spec ensures type safety is consistent across all 5 application targets and 4 shared packages, that path aliases resolve correctly, and that the TypeScript compiler catches errors uniformly regardless of which workspace a developer is editing.

## Acceptance Criteria

- A root `tsconfig.base.json` is present and sets `strict` to true, `target` to `"ES2024"`, `module` to `"ESNext"`, `moduleResolution` to `"bundler"`, and `verbatimModuleSyntax` to true
- The root `tsconfig.base.json` sets `skipLibCheck` to true to avoid type-checking third-party declaration files
- At least 8 workspace `tsconfig.json` files are present, and each one contains an `"extends"` field that references the root base via a relative path (not a package reference)
- The `apps/web` workspace `tsconfig.json` sets `"jsx"` to `"react-jsx"` and defines a `@/*` path alias that is present and maps to `"./src/*"`
- The `apps/api` workspace `tsconfig.json` includes `"@cloudflare/workers-types"` in its `types` array — this value is present in the config
- The `apps/mobile` workspace `tsconfig.json` extends `expo/tsconfig.base` — this value is present in the `extends` field
- The `apps/desktop` workspace contains 0 TypeScript source files — only Rust code and configuration files are present
- Running `pnpm typecheck` exits with code = 0 and produces 0 errors and 0 warnings on a clean checkout
- All imports between workspace packages use extensionless paths — 0 imports contain `.js`, `.ts`, or `.mjs` file extensions
- The `verbatimModuleSyntax` value equals true in the base config, and at least 90% of type-only imports across the codebase use the `import type` syntax
- Each shared package workspace (`packages/*`) sets `"declaration"` to true and `"declarationMap"` to true in its tsconfig
- The `packages/contracts` workspace tsconfig sets `"noUncheckedIndexedAccess"` to true
- Running `pnpm typecheck` completes in under 120 seconds on CI with warm Turborepo cache

## Constraints

- No workspace sets `moduleResolution` to `"node"` or `"node16"` — all workspace tsconfig files that declare `moduleResolution` set it to `"bundler"` exclusively, since every target goes through a bundler (Vite, esbuild, Metro, or WXT). The total count of non-bundler `moduleResolution` values across all tsconfig files equals 0.
- TypeScript version is pinned to `^5.9.3` via the pnpm catalog — running `pnpm ls typescript` across all workspaces returns the same major.minor version, and the catalog entry is present in `pnpm-workspace.yaml`.
- tsconfig `extends` chains use only relative paths (e.g., `../../tsconfig.base.json`), never `@repo/` package references — the count of `@repo/` strings in tsconfig `extends` fields equals 0 across all workspaces.
- No workspace sets `strict` to false or disables any strict-mode sub-flag (`noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`) — every workspace inherits `strict: true` from the base config and the count of `false` overrides for these flags equals 0.
- Path aliases are limited to `@/*` for Shadcn imports in `apps/web` and `apps/browser-extension` only — no other custom path aliases are defined, and the total count of `paths` entries across all other workspace tsconfigs equals 0.

## Failure Modes

- **Strict mode regression**: A developer sets `strict` to false or `noImplicitAny` to false in a workspace tsconfig to suppress type errors, weakening type safety for that workspace. The CI typecheck step catches this because the root base config enforces `strict: true`, and a config validation script returns error listing the workspace and the overridden flag that violated the strict-mode constraint.
- **Module resolution mismatch**: A workspace switches to `moduleResolution: "node16"` and adds `.js` extensions to imports, causing other workspaces that consume its exports to fail with resolution errors. The CI typecheck step returns error on the consuming workspace with "module not found" diagnostics, and the developer is directed to the base tsconfig which mandates `"bundler"` resolution for all workspaces.
- **Missing type declarations**: A shared package builds without `declaration` set to true, causing downstream workspaces to lose type information and fall back to `any` types. The CI typecheck step logs errors about implicit `any` types in the consuming workspace, and the build pipeline rejects the output because `strict: true` with `noImplicitAny` treats these as errors that block the build.
- **Path alias collision**: A developer adds a custom path alias in a workspace that conflicts with the `@repo/` workspace protocol scope, causing TypeScript to resolve the wrong module at compile time while the bundler resolves the correct one at build time. The CI build step returns error when the bundled output produces runtime type mismatches caught by Zod validation in the contracts package, and the developer is notified with a clear diagnostic showing both the tsconfig alias and the workspace protocol resolution for the conflicting path.

## Declared Omissions

- Biome lint and format configuration (covered by `code-quality.md`)
- Per-workspace build tool configuration such as Vite, Metro, or Wrangler (covered by platform-specific specs)
- Runtime type validation with Zod (covered by `shared-contracts.md`)
- Type generation from Wrangler or TanStack Router (covered by platform-specific specs)

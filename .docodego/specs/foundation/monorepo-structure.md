[← Back to Roadmap](../ROADMAP.md)

# Monorepo Structure

## Intent

This spec defines the workspace layout, package management, and build orchestration for the DoCodeGo boilerplate monorepo. The monorepo hosts 5 application targets (web, API, mobile, desktop, browser extension) and 4 shared packages under a single repository managed by pnpm workspaces and orchestrated by Turborepo. The goal is to enable cross-platform code sharing with strict dependency isolation, centralized version management via the pnpm catalog, and deterministic topological builds. This spec exists to ensure every workspace follows the same structural conventions and that the build pipeline produces correct, cache-friendly outputs for all targets.

## Acceptance Criteria

- The root `pnpm-workspace.yaml` declares exactly 3 workspace globs (`apps/*`, `packages/*`, `e2e`), and each glob is present in the file
- The root `package.json` sets `"type": "module"` — the value equals `"module"` and is not absent
- The monorepo contains at least 5 application workspaces: `apps/web`, `apps/api`, `apps/mobile`, `apps/desktop`, and `apps/browser-extension` are all present on disk
- The monorepo contains at least 4 shared package workspaces: `packages/library`, `packages/contracts`, `packages/ui`, and `packages/i18n` are all present on disk
- The monorepo contains at least 1 test workspace: the `e2e` directory is present on disk
- All shared packages use the `@repo/<name>` scope — `@repo/library`, `@repo/contracts`, `@repo/ui`, and `@repo/i18n` are present in their respective `package.json` name fields
- Every workspace `package.json` references shared dependencies via `"catalog:"` — at least 90% of shared dependencies use the catalog reference instead of hardcoded version ranges
- The `pnpm-workspace.yaml` catalog section lists at least 25 shared dependencies with pinned version ranges
- The root `turbo.json` defines at least 6 pipeline tasks: `build`, `dev`, `typecheck`, `test`, `typegen`, and `storybook` are all present
- The `build` task in `turbo.json` sets `dependsOn` to include `"^build"` — this value is present and enabled
- The `dev` task in `turbo.json` sets `persistent` to true and `cache` to false
- The `typecheck` task in `turbo.json` sets `dependsOn` to include `"^build"` — this value is present and enabled
- Running `pnpm install` at the root with warm cache completes in under 60 seconds and exits with code = 0
- Running `pnpm build` produces outputs for all workspaces and exits with code = 0 with 0 errors
- Every workspace `package.json` contains a `"typecheck"` script that is present and non-empty, and a `"test"` script that is present and non-empty
- The `turbo.json` sets `"ui"` to `"tui"` — this value equals `"tui"` and is not absent

## Constraints

- pnpm is the sole package manager — `npx`, `bunx`, and `yarn` are never used anywhere in the repository, including scripts, CI workflows, and documentation examples. Running a global search for these tool names across all files returns 0 matches outside of documentation that explicitly warns against their use.
- All file and folder names within the monorepo follow kebab-case naming — no file or folder contains uppercase letters or underscores in its name, except for generated files and third-party configuration files that mandate specific casing.
- The `packages/i18n` core export must never import React — the string `"react"` is absent from the core subpath's dependency list, and React bindings are isolated to the `@repo/i18n/react` subpath export only.
- Workspace cross-references use the `workspace:*` protocol in `package.json` dependencies, not relative file paths or version ranges — every internal dependency value equals `"workspace:*"`.
- The pnpm lockfile `pnpm-lock.yaml` is committed to the repository and is present in version control — it is not listed in `.gitignore`.
- No workspace publishes to npm — the `"private"` field is true in every workspace `package.json`, and no `"publishConfig"` field is present.

## Failure Modes

- **Catalog version drift**: A developer adds a dependency with a hardcoded version instead of `"catalog:"`, causing version mismatch across workspaces. The CI lint step rejects the pull request by running a check that scans all workspace `package.json` files for shared dependencies not using the catalog reference, and the developer returns error with a clear message identifying which dependency and workspace violated the catalog rule.
- **Topological build order violation**: A workspace imports a generated type from another workspace before that workspace has built, causing TypeScript compilation to fail with missing module errors. Turborepo's `dependsOn: ["^build"]` configuration prevents this by enforcing that all upstream dependencies build first, and if a developer removes this dependency declaration, the CI build step returns error immediately with unresolved import diagnostics.
- **Silent task skipping**: A new workspace is added without `"typecheck"` or `"test"` scripts in its `package.json`, causing Turborepo to silently skip quality checks for that workspace. The CI pipeline runs a pre-check that verifies every workspace listed in `pnpm-workspace.yaml` contains both scripts, and returns error with a list of workspaces missing required scripts before any build or test task executes.
- **Phantom dependency access**: A workspace imports a package that is not declared in its own `package.json` but is hoisted from another workspace's dependencies, working locally but failing in CI or production. pnpm's strict dependency isolation (non-flat `node_modules/.pnpm` structure) rejects the import at runtime, and the developer receives a clear "module not found" error that logs the missing dependency name and the workspace that attempted the import.

## Declared Omissions

- Individual workspace build configurations (covered by per-app specs like `tauri-build.md`, `expo-build.md`)
- CI/CD pipeline definitions (covered by `ci-cd-pipelines.md`)
- TypeScript compiler configuration details (covered by `typescript-config.md`)
- Code quality tooling configuration (covered by `code-quality.md`)

---
id: SPEC-2026-002
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: draft
roles: [Framework Adopter]
---

[← Back to Roadmap](../ROADMAP.md)

# Monorepo Structure

## Intent

This spec defines the workspace layout, package management, and build orchestration for the DoCodeGo boilerplate monorepo. The monorepo hosts 5 application targets (web, API, mobile, desktop, browser extension) and 4 shared packages under a single repository managed by pnpm workspaces and orchestrated by Turborepo. The goal is to enable cross-platform code sharing with strict dependency isolation, centralized version management via the pnpm catalog, and deterministic topological builds. This spec exists to ensure every workspace follows the same structural conventions and that the build pipeline produces correct, cache-friendly outputs for all targets.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| pnpm (package manager) | read/write | Every install, script execution, and dependency resolution across all workspaces | Build and install commands fail with a non-zero exit code and the developer receives a clear error that pnpm is not installed or not in the system PATH |
| Turborepo | read | Every orchestrated task such as `build`, `typecheck`, `test`, `dev`, `typegen`, and `storybook` | Task orchestration falls back to serial pnpm script execution, losing parallelism and caching, and the developer receives a missing binary error |
| pnpm catalog (`pnpm-workspace.yaml`) | read | Every `pnpm install` when resolving `"catalog:"` version references in workspace `package.json` files | Install fails with an unresolved catalog reference error and exits with a non-zero code, blocking all downstream tasks |
| `@repo/*` shared packages | read | Build time and runtime when apps import from `@repo/library`, `@repo/contracts`, `@repo/ui`, or `@repo/i18n` | TypeScript compilation fails with unresolved module errors and the build exits with a non-zero code |

## Behavioral Flow

1. **[Developer]** → clones the repository and runs `pnpm install` at the root directory
2. **[pnpm]** → reads `pnpm-workspace.yaml` to discover workspace globs (`apps/*`, `packages/*`, `e2e`) → resolves `"catalog:"` references from the catalog section → links internal `workspace:*` dependencies → writes `pnpm-lock.yaml` → exits with code 0 on success
3. **[Developer]** → runs `pnpm build` (or `pnpm typecheck`, `pnpm test`, `pnpm dev`)
4. **[Turborepo]** → reads `turbo.json` pipeline definition → computes topological dependency graph from `dependsOn` declarations → checks local and remote cache for previously completed task outputs
5. **[Turborepo]** → executes tasks in parallel respecting `dependsOn: ["^build"]` ordering — upstream packages build before downstream apps that depend on them
6. **[Turborepo]** → collects task exit codes → reports success (all exit code 0) or failure (at least 1 non-zero exit code) → caches successful outputs for subsequent runs

## State Machine

No stateful entities. The monorepo structure is a static workspace layout with no entities that have a lifecycle or state transitions within this spec's scope.

## Business Rules

No conditional business rules. Workspace discovery, dependency resolution, and build orchestration execute unconditionally based on the declared configuration in `pnpm-workspace.yaml` and `turbo.json`.

## Permission Model

Single role; no permission model is needed. All developers have identical read/write access to every workspace, and there are no role-based restrictions on which workspaces a developer can modify or build.

## Acceptance Criteria

- [ ] The root `pnpm-workspace.yaml` declares exactly 3 workspace globs (`apps/*`, `packages/*`, `e2e`), and each glob is present in the file
- [ ] The root `package.json` sets `"type": "module"` — the value equals `"module"` and is not absent
- [ ] The monorepo contains at least 5 application workspaces: `apps/web`, `apps/api`, `apps/mobile`, `apps/desktop`, and `apps/browser-extension` are all present on disk
- [ ] The monorepo contains at least 4 shared package workspaces: `packages/library`, `packages/contracts`, `packages/ui`, and `packages/i18n` are all present on disk
- [ ] The monorepo contains at least 1 test workspace: the `e2e` directory is present on disk
- [ ] All shared packages use the `@repo/<name>` scope — `@repo/library`, `@repo/contracts`, `@repo/ui`, and `@repo/i18n` are present in their respective `package.json` name fields
- [ ] Every workspace `package.json` references shared dependencies via `"catalog:"` — at least 90% of shared dependencies use the catalog reference instead of hardcoded version ranges
- [ ] The `pnpm-workspace.yaml` catalog section lists at least 25 shared dependencies with pinned version ranges
- [ ] The root `turbo.json` defines at least 6 pipeline tasks: `build`, `dev`, `typecheck`, `test`, `typegen`, and `storybook` are all present
- [ ] The `build` task in `turbo.json` sets `dependsOn` to include `"^build"` — this value is present and enabled
- [ ] The `dev` task in `turbo.json` sets `persistent` to true and `cache` to false
- [ ] The `typecheck` task in `turbo.json` sets `dependsOn` to include `"^build"` — this value is present and enabled
- [ ] Running `pnpm install` at the root with warm cache completes in under 60 seconds and exits with code = 0
- [ ] Running `pnpm build` produces outputs for all workspaces and exits with code = 0 with 0 errors
- [ ] Every workspace `package.json` contains a `"typecheck"` script that is present and non-empty, and a `"test"` script that is present and non-empty
- [ ] The `turbo.json` sets `"ui"` to `"tui"` — this value equals `"tui"` and is not absent

## Constraints

- pnpm is the sole package manager — `npx`, `bunx`, and `yarn` are never used anywhere in the repository, including scripts, CI workflows, and documentation examples. Running a global search for these tool names across all files returns 0 matches outside of documentation that explicitly warns against their use.
- All file and folder names within the monorepo follow kebab-case naming — no file or folder contains uppercase letters or underscores in its name, except for generated files and third-party configuration files that mandate specific casing.
- The `packages/i18n` core export must never import React — the string `"react"` is absent from the core subpath's dependency list, and React bindings are isolated to the `@repo/i18n/react` subpath export only.
- Workspace cross-references use the `workspace:*` protocol in `package.json` dependencies, not relative file paths or version ranges — every internal dependency value equals `"workspace:*"`.
- The pnpm lockfile `pnpm-lock.yaml` is committed to the repository and is present in version control — it is not listed in `.gitignore`.
- No workspace publishes to npm — the `"private"` field is true in every workspace `package.json`, and no `"publishConfig"` field is present.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A developer adds a new workspace directory under `apps/` without adding the required `"typecheck"` and `"test"` scripts to its `package.json` | The CI pre-check script detects the missing scripts and exits with a non-zero code before any Turborepo tasks execute, listing the workspace that lacks the required scripts | CI output contains the workspace name and the names of the missing scripts, and the pipeline exits with code 1 |
| A developer runs `pnpm install` for the first time on a fresh clone without any existing `node_modules` directories present | pnpm reads the committed `pnpm-lock.yaml`, resolves all `"catalog:"` references, installs all dependencies, and links all `workspace:*` references — the install exits with code 0 in under 60 seconds on a standard CI runner | The `node_modules` directory is present in the root and all workspace directories, and `pnpm build` succeeds immediately after |
| A developer adds a dependency with a hardcoded version string such as `"^5.0.0"` instead of using the `"catalog:"` reference for a shared dependency | The CI catalog lint step scans all workspace `package.json` files and rejects the pull request, identifying which dependency and workspace violated the catalog rule | CI output lists the exact dependency name, the hardcoded version, and the workspace path, and the pipeline exits with code 1 |
| Two developers modify different workspaces in parallel and both regenerate `pnpm-lock.yaml` with conflicting changes | Git merge conflict occurs on `pnpm-lock.yaml`, and the developer resolves the conflict by running `pnpm install` which regenerates a consistent lockfile from the merged `package.json` files | After conflict resolution and `pnpm install`, the lockfile is valid and `pnpm build` exits with code 0 |

## Failure Modes

- **Catalog version drift**
    - **What happens:** A developer adds a dependency with a hardcoded version string instead of `"catalog:"`, causing version mismatch across multiple workspaces that consume the same dependency.
    - **Source:** Manual editing of a workspace `package.json` without following the catalog convention.
    - **Consequence:** Different workspaces resolve different versions of the same dependency, leading to runtime type mismatches or duplicated bundles that increase output size.
    - **Recovery:** The CI lint step rejects the pull request by scanning all workspace `package.json` files for shared dependencies not using the catalog reference, and the developer returns error with a message identifying the dependency and workspace — the system alerts before merge.
- **Topological build order violation**
    - **What happens:** A workspace imports a generated type from another workspace before that workspace has built, causing TypeScript compilation to fail with missing module errors.
    - **Source:** A developer removes or modifies the `dependsOn: ["^build"]` declaration in `turbo.json` for a build task.
    - **Consequence:** TypeScript compilation fails with unresolved import errors for the downstream workspace, and the build exits with a non-zero code.
    - **Recovery:** Turborepo's `dependsOn: ["^build"]` configuration prevents this by enforcing upstream builds first — if a developer removes this declaration, the CI build step returns error immediately with unresolved import diagnostics and alerts the team via the failed pipeline status.
- **Silent task skipping**
    - **What happens:** A new workspace is added without `"typecheck"` or `"test"` scripts in its `package.json`, causing Turborepo to silently skip quality checks for that workspace.
    - **Source:** Developer creates a new workspace directory and `package.json` without including the required script entries.
    - **Consequence:** The new workspace has 0 type safety validation and 0 test coverage, and defects in that workspace are not caught until downstream consumers fail.
    - **Recovery:** The CI pipeline runs a pre-check that verifies every workspace listed in `pnpm-workspace.yaml` contains both scripts — the check returns error with a list of workspaces missing required scripts and alerts by blocking the pipeline before any build or test task executes.
- **Phantom dependency access**
    - **What happens:** A workspace imports a package that is not declared in its own `package.json` but is hoisted from another workspace's dependencies, working locally but failing in CI or production.
    - **Source:** Implicit dependency resolution caused by the developer forgetting to add the dependency to the consuming workspace's `package.json`.
    - **Consequence:** The import works on the developer's machine but fails with a "module not found" error in CI or production where hoisting does not occur.
    - **Recovery:** pnpm's strict dependency isolation with the non-flat `node_modules/.pnpm` structure rejects the import at runtime — the developer receives a "module not found" error that logs the missing dependency name, and CI alerts by failing the build before deployment.

## Declared Omissions

- Individual workspace build configurations (Astro, Expo, Tauri, WXT) are not covered here and are defined in per-app specs such as `tauri-build.md` and `expo-build.md`
- CI/CD pipeline definitions, GitHub Actions workflows, and deployment automation are not covered here and are defined in `ci-cd-pipelines.md`
- TypeScript compiler configuration details, `tsconfig.json` structure, and path alias setup are not covered here and are defined in `typescript-config.md`
- Code quality tooling configuration including Biome, Knip, and Lefthook setup is not covered here and is defined in `code-quality.md`
- Runtime environment variables, secret management, and per-workspace `.env` file conventions are not covered here and are deferred to deployment and configuration specs

## Related Specifications

- [typescript-config](typescript-config.md) — TypeScript compiler configuration, `tsconfig.json` inheritance structure, and path alias setup used by all workspaces
- [code-quality](code-quality.md) — Biome linting and formatting, Knip dead code detection, and Lefthook git hooks that run across all workspaces
- [ci-cd-pipelines](ci-cd-pipelines.md) — CI/CD pipeline definitions, GitHub Actions workflows, and deployment automation that orchestrate monorepo builds
- [shared-contracts](shared-contracts.md) — oRPC contract definitions in `@repo/contracts` consumed by both the API workspace and frontend workspaces
- [shared-i18n](shared-i18n.md) — Internationalization infrastructure in `@repo/i18n` providing translation functions to all platform targets

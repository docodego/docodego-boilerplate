---
id: SPEC-2026-011
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: approved
roles: [Framework Adopter]
---

[← Back to Roadmap](../ROADMAP.md)

# CI/CD Pipelines

## Intent

This spec defines the GitHub Actions workflows, deployment strategy,
and quality gate automation for the DoCodeGo boilerplate. The CI/CD
system enforces the same quality checks that run locally via Lefthook
hooks, deploys each platform target to its respective hosting
environment, and produces desktop builds across a matrix of operating
systems. Each platform has a distinct deployment target: web to
Cloudflare Pages, API to Cloudflare Workers, mobile to Expo EAS
Build, desktop to Tauri platform-specific binaries, and browser
extension to store-ready archives. This spec ensures that no code
reaches production without passing the full quality gate and that
deployments are automated, reproducible, and auditable through
GitHub Actions run history.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| GitHub Actions | orchestration | Every push, pull request, tag, or manual dispatch event triggers one or more workflows | Workflows do not execute and deployments are blocked until the GitHub Actions service recovers |
| Cloudflare Pages | write | Deployment workflow pushes static web build output after a successful merge to `main` | Web deployment step fails and the workflow alerts with a non-zero exit code while the previous production deployment remains live |
| Cloudflare Workers | write | Deployment workflow runs `wrangler deploy` after a successful merge to `main` | API deployment step fails and the workflow alerts with a non-zero exit code while the previous production worker version remains live |
| Expo EAS Build | write | Mobile build workflow submits a build request to Expo's cloud build service on tagged releases | Mobile build step fails and the workflow alerts with the EAS error diagnostic while other deployment targets remain unaffected |
| pnpm store cache | read/write | Every workflow run restores and saves the pnpm dependency cache keyed by `pnpm-lock.yaml` hash | Cache miss triggers a full `pnpm install` from the registry, increasing CI run time but not blocking the workflow |
| Tauri build toolchain | read | Desktop build workflow invokes Rust compiler and platform-specific system libraries on each OS runner | Desktop build step fails on the affected OS and the workflow alerts with the compilation error while other OS builds continue |

## Behavioral Flow

1. **[Developer]** → opens a pull request targeting `main` or
    pushes commits to an existing pull request branch
2. **[GitHub Actions]** → triggers the quality gate workflow on
    `ubuntu-latest` → runs `pnpm install --frozen-lockfile` →
    restores pnpm cache from the `pnpm-lock.yaml` hash key
3. **[Quality gate workflow]** → executes `pnpm quality` which
    runs lint, typecheck, test, and knip in sequence → exits
    with code 0 on success or non-zero on any failure
4. **[GitHub branch protection]** → blocks merge if the quality
    gate status check reports a failure → developer must fix and
    push again before the pull request can merge
5. **[Developer]** → merges pull request to `main` after the
    quality gate passes all checks
6. **[GitHub Actions]** → triggers the deployment workflow on
    push to `main` → builds and deploys web to Cloudflare Pages
    and API to Cloudflare Workers in parallel jobs
7. **[Developer]** → creates a version tag or triggers manual
    dispatch for a desktop release
8. **[GitHub Actions]** → triggers the desktop build workflow →
    runs Tauri builds across a 3-OS matrix (Ubuntu, macOS,
    Windows) → uploads 6 platform-specific artifacts

## State Machine

No stateful entities. CI/CD pipelines are stateless
event-driven workflows — each run is an independent execution
with no lifecycle transitions tracked within this spec's scope.

## Business Rules

- **Rule quality-gate-required:** IF a pull request targets
    `main` AND the quality gate workflow has not passed THEN
    GitHub branch protection blocks the merge until the check
    reports success, ensuring no unvalidated code enters the
    main branch.
- **Rule desktop-trigger-restriction:** IF the event is a push
    to `main` without a version tag AND no manual dispatch was
    triggered THEN the desktop build workflow does not execute,
    reserving expensive cross-platform builds for intentional
    release events only.
- **Rule frozen-lockfile-enforcement:** IF `pnpm-lock.yaml` is
    out of sync with `package.json` dependency declarations THEN
    `pnpm install --frozen-lockfile` fails with a non-zero exit
    code and the workflow halts before reaching the quality gate
    command.

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Contributor | Open pull requests, trigger quality gate via PR events, view workflow run logs and artifacts | Push directly to `main`, merge without passing quality gate, trigger deployment workflow manually | Can see workflow logs for their own PRs but cannot access repository secrets or deployment credentials |
| Maintainer | Merge pull requests after quality gate passes, trigger manual dispatch for desktop builds, access deployment logs | Push directly to `main` if branch protection is enforced, bypass required status checks without admin override | Can see all workflow logs, deployment status, and artifact downloads but secrets are masked in logs |
| GitHub Actions bot | Execute workflow steps, read repository code, write deployment artifacts, access secrets via `${{ secrets.* }}` | Modify branch protection rules, approve pull requests, change repository settings | Has access to secrets only within workflow execution context and cannot expose them in log output |

## Acceptance Criteria

- [ ] A `.github/workflows/` directory is present and contains at least 2 workflow files for quality gate and deployment
- [ ] A quality gate workflow is present that runs on every pull request targeting `main` and executes `pnpm quality` (lint, typecheck, test, knip) — the workflow exits with code 0 on a clean codebase
- [ ] The `--frozen-lockfile` flag is present in the quality gate install step — `pnpm install --frozen-lockfile` prevents lockfile modifications in CI
- [ ] The pnpm cache step is present in the quality gate workflow — the cache key includes the `pnpm-lock.yaml` hash and the `restore-keys` field is present
- [ ] The `ubuntu-latest` runner label is present in the quality gate workflow file — this is the only runner used for the quality gate job
- [ ] A deployment workflow is present that triggers on push to `main` and deploys at least 2 targets: `apps/web` to Cloudflare Pages and `apps/api` to Cloudflare Workers
- [ ] The web build exits with code 0 after running `pnpm --filter web build` and the static output directory is present for deployment to Cloudflare Pages
- [ ] The `wrangler deploy` command is present in the API deployment step and runs from the `apps/api` directory to deploy the worker
- [ ] A desktop build workflow is present that builds Tauri binaries across at least 3 OS targets: `ubuntu-latest`, `macos-latest`, and `windows-latest` — all 3 runner labels are present in the matrix
- [ ] The Rust setup step is present in the desktop build workflow and installs Rust and system dependencies before running `tauri build`
- [ ] The desktop build workflow produces at least 6 artifacts: `.msi` + `.exe` (Windows), `.dmg` + `.app` (macOS), `.AppImage` + `.deb` (Linux) — all formats are present in the upload-artifact step patterns
- [ ] The count of `@main` or `@master` branch references in action versions equals 0 — all workflows pin their GitHub Actions versions using SHA hashes or exact version tags
- [ ] The pnpm version value is present in all workflows and equals the version in the project root `packageManager` field in `package.json`
- [ ] The quality gate is enabled as a required status check in branch protection — pull requests cannot merge to `main` without this check passing

## Constraints

- All CI commands use `pnpm` exclusively — the count of `npm`,
    `npx`, `yarn`, or `bunx` commands across all workflow files
    equals 0. This matches the monorepo's package manager
    constraint defined in the product context.
- Workflow secrets (Cloudflare API tokens, EAS tokens) are
    referenced via `${{ secrets.* }}` and are never hardcoded —
    the count of plaintext API keys or tokens in workflow files
    equals 0. Secret names are documented in the workflow file
    comments but their values are absent from the repository.
- The quality gate runs the identical `pnpm quality` command
    that developers run locally via the `pre-push` Lefthook
    hook — the CI and local quality checks are the same command,
    ensuring 0 drift between local and CI validation.
- Desktop builds run only on tagged releases or manual dispatch,
    not on every push to `main` — the desktop workflow trigger
    includes `workflow_dispatch` and optionally `push.tags` but
    does not trigger on `push.branches` for `main`.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A pull request contains only documentation changes in `.md` files with no source code modifications affecting the quality gate | The quality gate workflow still runs because it triggers on all pull requests to `main` regardless of changed file types, ensuring doc-only PRs pass lint checks | Workflow run completes with exit code 0 and the quality gate status check reports success on the pull request |
| Two deployment workflows trigger simultaneously because two pull requests merge to `main` within seconds of each other | Each workflow run executes independently with its own checkout of the `main` branch at the respective commit SHA, and Cloudflare handles atomic deployments so the last deployment wins | Both workflow runs complete and the final production state matches the latest commit on `main` |
| The pnpm cache action fails to restore due to a GitHub Actions cache service outage affecting cache read operations | The workflow falls back to a full `pnpm install` from the npm registry without the cache, increasing run time by 30-60 seconds but not failing the workflow | Workflow logs show a cache miss message and the install step still completes with exit code 0 |
| A developer force-pushes to a pull request branch while the quality gate workflow is already running on the previous commit | GitHub Actions cancels the in-progress workflow run for the previous commit and starts a new run for the force-pushed commit, preventing stale results | The previous run shows as cancelled and the new run executes on the updated commit SHA |
| The Cloudflare API token secret is missing or expired when the deployment workflow attempts to deploy the API worker | The `wrangler deploy` step fails with an authentication error and the workflow exits with a non-zero code while the previous production deployment remains live | Workflow logs show an authentication failure message and the deployment step is marked as failed |

## Failure Modes

- **Quality gate bypass via direct push to the main branch**
    - **What happens:** A developer pushes directly to `main`
        bypassing the pull request flow, which skips the
        required quality gate status check entirely.
    - **Source:** Developer misconfiguration or intentional
        bypass of the branch protection rules that enforce
        the pull request requirement on the main branch.
    - **Consequence:** Unvalidated code reaches the main branch
        and triggers the deployment workflow, potentially
        deploying broken or failing code to production.
    - **Recovery:** Branch protection rules are configured to
        require the quality gate workflow, so GitHub alerts
        the developer by rejecting the direct push with a
        "required status check" error and forces them to
        open a pull request instead.
- **Frozen lockfile violation during CI dependency installation**
    - **What happens:** A developer commits code that requires a
        new dependency but forgets to update `pnpm-lock.yaml`,
        causing `pnpm install --frozen-lockfile` to fail in CI.
    - **Source:** Developer omission where `pnpm install` was
        not run locally after adding a new dependency to a
        workspace `package.json` file.
    - **Consequence:** The quality gate workflow fails at the
        install step before reaching lint, typecheck, test,
        or knip checks, blocking the pull request from merging.
    - **Recovery:** The workflow alerts the developer with a
        diagnostic message explaining that the lockfile is out
        of date, and the developer retries after running
        `pnpm install` locally to regenerate the lockfile.
- **Stale pnpm cache causing phantom module resolution errors**
    - **What happens:** The CI cache restores an outdated
        `node_modules/.pnpm` store that conflicts with updated
        dependencies in the lockfile, causing module resolution
        errors during build or test steps.
    - **Source:** Cache corruption or partial cache restore from
        a previous workflow run that used a different lockfile
        version with incompatible dependency versions.
    - **Consequence:** The quality gate or deployment workflow
        fails with confusing module-not-found errors that do
        not reproduce locally on the developer's machine.
    - **Recovery:** The cache key includes the `pnpm-lock.yaml`
        hash so any lockfile change invalidates the stale cache
        automatically, and the workflow falls back to a clean
        install because the `restore-keys` field allows partial
        matches that trigger a fresh dependency resolution.
- **Desktop build failure on a single OS in the build matrix**
    - **What happens:** The Tauri build succeeds on macOS and
        Linux but fails on Windows due to a missing system
        dependency or platform-specific compilation error,
        producing an incomplete release with only 4 of 6
        expected artifacts.
    - **Source:** Platform-specific dependency mismatch where a
        system library required by Tauri is not installed on the
        Windows runner image or has an incompatible version.
    - **Consequence:** The release is incomplete with missing
        Windows binaries, and users on Windows cannot download
        the desktop application from this release.
    - **Recovery:** The matrix strategy allows all 3 OS builds
        to complete independently so the workflow degrades
        gracefully by uploading successful macOS and Linux
        artifacts while alerting on the Windows job failure
        with the specific compilation diagnostic for debugging.
- **Cloudflare deployment authentication failure during deploy**
    - **What happens:** The `wrangler deploy` command fails
        because the Cloudflare API token stored in GitHub
        secrets has expired or been revoked, preventing the
        API or web deployment from completing.
    - **Source:** Expired or rotated Cloudflare API token that
        was not updated in the GitHub repository secrets
        settings by the repository maintainer.
    - **Consequence:** The deployment workflow fails and no new
        code reaches production, while the previous deployment
        remains live and unaffected by the failed run.
    - **Recovery:** The workflow alerts the maintainer with the
        authentication error from wrangler, and the maintainer
        retries the deployment after rotating the Cloudflare
        API token and updating the GitHub secret value.

## Declared Omissions

- Cloudflare Pages and Workers runtime configuration details
    including `wrangler.toml` settings are not covered here and
    are defined in `api-framework.md` and platform deployment
    documentation instead.
- Expo EAS Build profiles, mobile signing credentials, and the
    mobile release submission process are not covered here and
    are defined in the mobile platform specification instead.
- Browser extension store submission process is not covered here
    because it is a manual process that is not automated through
    CI/CD pipelines in this boilerplate.
- GitHub Actions runner self-hosting, cost optimization, and
    billing configuration are not covered here because they are
    infrastructure-level concerns outside this spec's scope.
- Preview environment deployment for pull request branches is
    not covered here and will be addressed in a future iteration
    of the CI/CD pipeline specification if needed.

## Related Specifications

- [api-framework](api-framework.md) — Defines the Hono app
    configuration and Cloudflare Workers runtime settings that
    the deployment workflow targets with `wrangler deploy`
- [shared-contracts](shared-contracts.md) — Defines the oRPC
    contracts and Zod schemas that the quality gate validates
    through typecheck during `pnpm quality` execution in CI
- [database-schema](database-schema.md) — Defines the Drizzle
    ORM schema and D1 migration strategy that CI must not break
    when running the quality gate checks on pull requests
- [auth-server-config](auth-server-config.md) — Defines the
    Better Auth configuration that depends on correct deployment
    of environment secrets through the CI/CD pipeline
- [expo-build](expo-build.md) — Defines the Expo 54 mobile
    application build configuration including EAS Build profiles
    that the CI/CD deployment workflow invokes to produce mobile
    binaries for iOS and Android release submissions
- [tauri-build](tauri-build.md) — Defines the Tauri 2 desktop
    application build configuration including Rust backend setup
    and platform-specific targets that the CI/CD desktop build
    workflow compiles across the 3-OS matrix

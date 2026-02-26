[← Back to Roadmap](../ROADMAP.md)

# CI/CD Pipelines

## Intent

This spec defines the GitHub Actions workflows, deployment strategy, and quality gate automation for the DoCodeGo boilerplate. The CI/CD system enforces the same quality checks that run locally via Lefthook hooks, deploys each platform target to its respective hosting environment, and produces desktop builds across a matrix of operating systems. Each platform has a distinct deployment target: web to Cloudflare Pages, API to Cloudflare Workers, mobile to Expo EAS Build, desktop to Tauri platform-specific binaries, and browser extension to store-ready archives. This spec ensures that no code reaches production without passing the full quality gate and that deployments are automated, reproducible, and auditable through GitHub Actions run history.

## Acceptance Criteria

- [ ] A `.github/workflows/` directory is present and contains at least 2 workflow files
- [ ] A quality gate workflow is present that runs on every pull request targeting the `main` branch and executes `pnpm quality` (lint, typecheck, test, knip) — the workflow exits with code = 0 on a clean codebase
- [ ] The quality gate workflow installs dependencies using `pnpm install --frozen-lockfile` — the `--frozen-lockfile` flag is present to prevent lockfile modifications in CI
- [ ] The quality gate workflow uses a pnpm cache step — the cache key includes the `pnpm-lock.yaml` hash and the `restore-keys` field is present
- [ ] The quality gate workflow runs on `ubuntu-latest` — this runner label is present in the workflow file
- [ ] A deployment workflow is present that triggers on push to `main` and deploys at least 2 targets: `apps/web` to Cloudflare Pages and `apps/api` to Cloudflare Workers
- [ ] The web deployment step runs `pnpm --filter web build` and deploys the static output directory — the build command exits with code = 0 and the output directory is present
- [ ] The API deployment step runs `wrangler deploy` from the `apps/api` directory — the wrangler command is present in the workflow step
- [ ] A desktop build workflow is present that builds Tauri binaries across at least 3 OS targets: `ubuntu-latest`, `macos-latest`, and `windows-latest` — all 3 runner labels are present in the matrix
- [ ] The desktop build workflow installs Rust and system dependencies before running `tauri build` — the Rust setup step is present in the workflow
- [ ] The desktop build workflow produces at least 6 artifacts: `.msi` + `.exe` (Windows), `.dmg` + `.app` (macOS), `.AppImage` + `.deb` (Linux) — all formats are present in the upload-artifact step patterns
- [ ] All workflows pin their GitHub Actions versions using SHA hashes or exact version tags — the count of `@main` or `@master` branch references in action versions equals 0
- [ ] All workflows set `pnpm` version to match the project root `packageManager` field — the version value is present and equals the version in `package.json`
- [ ] The quality gate workflow is a required status check — pull requests cannot merge to `main` without this check passing (enabled = true in branch protection)

## Constraints

- All CI commands use `pnpm` exclusively — the count of `npm`, `npx`, `yarn`, or `bunx` commands across all workflow files equals 0. This matches the monorepo's package manager constraint defined in the product context.
- Workflow secrets (Cloudflare API tokens, EAS tokens) are referenced via `${{ secrets.* }}` and are never hardcoded — the count of plaintext API keys or tokens in workflow files equals 0. Secret names are documented in the workflow file comments but their values are absent from the repository.
- The quality gate runs the identical `pnpm quality` command that developers run locally via the `pre-push` Lefthook hook — the CI and local quality checks are the same command, ensuring 0 drift between local and CI validation.
- Desktop builds run only on tagged releases or manual dispatch, not on every push to `main` — the desktop workflow trigger includes `workflow_dispatch` and optionally `push.tags` but does not trigger on `push.branches` for `main`.

## Failure Modes

- **Quality gate bypass via direct push**: A developer pushes directly to `main` bypassing the pull request flow, skipping the required quality gate status check. Branch protection rules are configured to require the quality gate workflow as a required status check, and GitHub rejects the direct push with a "required status check" error, forcing the developer to open a pull request instead.
- **Frozen lockfile violation in CI**: A developer commits code that requires a new dependency but forgets to update `pnpm-lock.yaml`, causing `pnpm install --frozen-lockfile` to fail in CI. The workflow returns error with a diagnostic message explaining that the lockfile is out of date, and the developer runs `pnpm install` locally to regenerate the lockfile before pushing again.
- **Stale pnpm cache causing install failures**: The CI cache restores an outdated `node_modules/.pnpm` store that conflicts with updated dependencies in the lockfile, causing phantom module resolution errors. The cache key includes the `pnpm-lock.yaml` hash, so any lockfile change invalidates the cache automatically. If the cache is corrupted, the workflow falls back to a clean install because the `restore-keys` field allows partial matches that trigger a fresh resolution.
- **Desktop build failure on one OS**: The Tauri build succeeds on macOS and Linux but fails on Windows due to a missing system dependency, producing an incomplete release with only 4 of 6 artifacts. The matrix strategy allows all 3 OS builds to complete independently (early termination is disabled), and the workflow returns error on the Windows job with the specific compilation diagnostic while still uploading the successful macOS and Linux artifacts for debugging.

## Declared Omissions

- Cloudflare Pages and Workers configuration details (covered by `api-framework.md` and platform deployment docs)
- Expo EAS Build profiles and mobile release process (covered by `expo-build.md`)
- Browser extension store submission process (manual, not automated in CI)
- GitHub Actions runner self-hosting or cost optimization (infrastructure concern)

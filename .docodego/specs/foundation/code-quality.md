[← Back to Roadmap](../ROADMAP.md)

# Code Quality

## Intent

This spec defines the code quality tooling stack for the DoCodeGo boilerplate monorepo, covering linting, formatting, dead code detection, commit message validation, and git hook automation. The tooling stack consists of Biome for linting and formatting, Knip for dead code and unused dependency detection, Commitlint for conventional commit enforcement, and Lefthook for git hook management. This spec ensures that every code change passing through the repository meets consistent formatting standards, contains no unused exports or dependencies, follows the conventional commit format, and triggers quality checks at the correct git lifecycle points without manual intervention.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Biome | read | Every `pnpm lint` or `pnpm lint:fix` invocation and during the pre-push git hook | The lint command returns a non-zero exit code and the pre-push hook blocks the push until Biome is reinstalled via `pnpm install` |
| Knip | read | Every `pnpm knip` invocation and during the `pnpm quality` gate | The quality gate returns a non-zero exit code and the pre-push hook blocks the push until Knip is reinstalled via `pnpm install` |
| Commitlint | read | Every `git commit` via the commit-msg Lefthook hook | The commit-msg hook fails with a non-zero exit code and the commit is rejected until Commitlint is reinstalled via `pnpm install` |
| Lefthook | read | Every `git commit`, `git push`, and `git merge` lifecycle event | Git hooks do not execute and quality checks are skipped entirely until Lefthook is reinstalled via `pnpm hooks:install` |
| Turborepo | read | Every `pnpm typecheck` and `pnpm test` invocation within the quality gate | The typecheck or test step returns a non-zero exit code and the quality gate halts at the failing step |
| `@repo/ui` (label component) | read | When Biome scans the UI package for `biome-ignore` suppression comments | The single permitted `biome-ignore` comment on the `label` component is the only allowed accessibility suppression in the entire codebase |

## Behavioral Flow

1. **[Developer]** writes code changes and stages files for commit in the local working directory
2. **[Developer]** runs `git commit` with a conventional commit message following the `type(scope): message` format
3. **[Lefthook commit-msg hook]** intercepts the commit and passes the commit message to Commitlint for validation against the allowed types and scopes list
4. **[Commitlint]** validates the message format and returns exit code 0 if the format matches or exit code 1 with diagnostic output if the format is invalid, blocking the commit
5. **[Developer]** runs `git push` to send committed changes to the remote repository
6. **[Lefthook pre-push hook]** intercepts the push and runs `pnpm quality` which executes 4 sequential steps: lint, typecheck, test, and knip
7. **[Biome]** checks all files for formatting violations and lint errors, returning exit code 0 with 0 violations or exit code 1 with a list of violations that block the push
8. **[TypeScript compiler]** runs typecheck across all workspaces via Turborepo, returning exit code 0 or exit code 1 with type errors that block the push
9. **[Test runner]** runs all workspace test suites via Turborepo, returning exit code 0 or exit code 1 with test failures that block the push
10. **[Knip]** scans all workspaces for unused exports, files, and dependencies, returning exit code 0 with 0 findings or exit code 1 with a report of unused items that block the push
11. **[Lefthook post-merge hook]** runs `pnpm install` after a successful merge to ensure dependencies are synchronized with the merged `pnpm-lock.yaml` file

## State Machine

No stateful entities. The code quality tooling stack is a stateless pipeline of checks — no entities have a lifecycle within this spec's scope.

## Business Rules

No conditional business rules. Each tool in the quality gate executes unconditionally on every relevant git lifecycle event in a fixed sequential order.

## Permission Model

Single role; no permission model is needed. All developers in the repository have identical access to every quality tool, and no tool restricts execution based on user identity or role.

## Acceptance Criteria

- [ ] Running `pnpm lint` exits with code = 0 on a clean checkout, producing 0 lint errors and 0 format violations
- [ ] Running `pnpm lint:fix` exits with code = 0 and auto-fixes all formatting violations in-place
- [ ] The Biome config sets indent width to 4, line width to 90, quote style to `"double"` — each value is present and enabled in the configuration file
- [ ] Biome trailing commas are enabled (set to `"all"`) and semicolons are enabled (set to `"always"`) — both values are present in the config
- [ ] Biome import sorting is enabled — the `organizeImports` setting is present and set to true in the config
- [ ] The root `package.json` contains a `"lint"` script and a `"lint:fix"` script — both are present and non-empty, and neither invokes Turborepo
- [ ] Running `pnpm knip` exits with code = 0 on a clean checkout, detecting 0 unused exports, 0 unused files, and 0 unused dependencies
- [ ] The `knip.json` configuration is present at the root and declares at least 10 workspace entries matching the workspaces in `pnpm-workspace.yaml`
- [ ] Knip runs with the `--cache` flag — the `"knip"` script in root `package.json` contains the literal string `--cache` in its value
- [ ] Running `pnpm lint:commit` exits with code = 0 for a commit message matching the format `type(scope): message`
- [ ] Running `pnpm lint:commit` exits with code = 1 for a commit message that does not match the conventional commit format
- [ ] Commitlint accepts at least 11 commit types (feat, fix, docs, refactor, test, chore, ci, dx, perf, build, revert) — each type is present in the config
- [ ] Commitlint accepts at least 11 commit scopes (web, api, mobile, desktop, extension, contracts, ui, library, i18n, deps, repo) — each scope is present in the config
- [ ] A `lefthook.yml` file is present at the root and defines at least 3 git hooks
- [ ] The `commit-msg` hook entry is present in `lefthook.yml` and runs Commitlint
- [ ] The `pre-push` hook entry is present in `lefthook.yml` and runs the full quality gate (`pnpm quality`)
- [ ] The `post-merge` hook entry is present in `lefthook.yml` and runs `pnpm install`
- [ ] Running `pnpm quality` executes 4 steps (lint, typecheck, test, knip) in sequence and exits with code = 0 on a clean checkout
- [ ] The count of `biome-ignore` comments across the entire codebase equals 1 — only the `label` component in `packages/ui` has this suppression

## Constraints

- Biome is the sole linter and formatter — ESLint, Prettier, and dprint are not installed anywhere in the repository. Running `pnpm ls eslint prettier dprint` returns 0 matches across all workspaces, and no configuration files for these tools (`.eslintrc`, `.prettierrc`, `dprint.json`) are present on disk.
- Biome is not run through Turborepo because its execution time is under 2 seconds, making Turborepo's caching overhead non-beneficial. The `turbo.json` file contains 0 task entries for `lint` or `lint:fix`.
- Lefthook is the sole git hook manager — Husky, simple-git-hooks, and lint-staged are not installed. Running `pnpm ls husky simple-git-hooks lint-staged` returns 0 matches, and no `.husky` directory is present on disk.
- The `--no-verify` flag is absent from all CI scripts and documentation — the count of `--no-verify` occurrences across all workflow files and markdown docs equals 0.
- No `biome-ignore` suppression comments are permitted except for the single `label` accessibility exception — the total count across the codebase equals 1.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A developer runs `pnpm lint` on a codebase with 0 source files changed since the last commit | Biome exits with code 0 and produces no output because there are no violations to report in the unchanged files | Exit code equals 0 and stdout contains no violation entries |
| A developer commits with an empty commit message that contains 0 characters | The Commitlint validation in the commit-msg hook rejects the commit with exit code 1 and logs the expected format pattern | The commit is not created and the git log does not contain the empty-message entry |
| A developer runs `pnpm quality` when 1 workspace has a failing test but all other checks pass | The quality gate halts at the test step with exit code 1 and does not proceed to the knip step because the sequence is fail-fast | Exit code equals 1 and the knip step output is absent from the terminal |
| The `lefthook.yml` file is deleted or missing from the repository root directory | Git hooks do not execute and quality checks are skipped on commit and push until `pnpm hooks:install` restores the hooks | Running `git push --dry-run` completes without triggering the pre-push quality gate |
| A developer adds a new workspace to `pnpm-workspace.yaml` but does not add a matching entry to `knip.json` | Knip does not scan the new workspace and unused exports in that workspace are not detected until the entry is added | Running `pnpm knip` exits with code 0 but the new workspace files are absent from the scan output |
| A developer runs `pnpm lint:fix` on a file that contains both formatting violations and lint errors that cannot be auto-fixed | Biome auto-fixes all formatting violations in-place but reports the unfixable lint errors with exit code 1 and diagnostic output | The formatting violations are corrected in the file but the lint error count in stdout is greater than 0 |

## Failure Modes

- **Formatting drift between developers causes inconsistent code style across the repository**
    - **What happens:** A developer's editor does not have Biome configured as the default formatter, causing inconsistent formatting that passes locally in the editor but fails when checked by the CI pipeline or pre-push hook.
    - **Source:** Misconfigured local editor settings or missing Biome editor extension on the developer's machine.
    - **Consequence:** Pull request diffs contain formatting noise mixed with logic changes, making code review harder and increasing merge conflict frequency.
    - **Recovery:** The pre-push hook falls back to running `pnpm lint` which returns a non-zero exit code with a list of files that do not match the configured formatting rules, and the developer runs `pnpm lint:fix` to auto-correct all formatting violations before re-pushing.
- **Unused dependency accumulation increases install time and bundle size over multiple releases**
    - **What happens:** A developer removes usage of a dependency from source code but forgets to remove it from `package.json`, causing the dependency to remain installed and increasing install time and bundle size with each forgotten removal.
    - **Source:** Incomplete refactoring where source code references are deleted but the corresponding `package.json` entry is not cleaned up.
    - **Consequence:** The `node_modules` directory grows with unused packages, install time increases, and the dependency tree contains entries that provide no runtime or build-time value.
    - **Recovery:** Knip detects the unused dependency during `pnpm quality` and returns a non-zero exit code with the workspace name, dependency name, and the `package.json` path where it remains declared — the pre-push hook alerts the developer and blocks the push until the unused entry is removed.
- **Invalid commit message format breaks changelog generation and semantic versioning automation**
    - **What happens:** A developer writes a commit message like "fixed the bug" without the conventional commit format `type(scope): message`, which breaks automated changelog generation and semantic version bumping.
    - **Source:** Developer oversight or unfamiliarity with the conventional commit format required by the repository.
    - **Consequence:** Commits with non-standard messages enter the repository history, breaking changelog tooling that parses commit types and scopes for release notes.
    - **Recovery:** The commit-msg Lefthook hook runs Commitlint which rejects the commit with exit code 1 and logs the expected format along with the list of valid types and scopes — the developer retries the commit with a corrected message before the invalid entry can reach the repository history.
- **Quality gate bypass via hook skip allows unvalidated code to reach the main branch**
    - **What happens:** A developer uses `git push --no-verify` to bypass the pre-push quality gate, pushing code that fails lint, typecheck, or test checks directly to the remote repository without local validation.
    - **Source:** Deliberate use of the `--no-verify` flag to skip Lefthook hooks during a push operation.
    - **Consequence:** Code that fails lint, typecheck, or test checks enters the remote repository and can block other developers or break the main branch CI pipeline.
    - **Recovery:** The CI pipeline runs the identical `pnpm quality` command as a required status check and returns a non-zero exit code that blocks the pull request merge — CI alerts the developer with the same diagnostic output they would have seen locally, and the unvalidated code degrades to a blocked PR state until all checks pass.

## Declared Omissions

- TypeScript compiler configuration, strict mode settings, and `tsconfig.json` inheritance hierarchy are not covered here and are defined in `typescript-config.md`
- CI/CD pipeline job definitions, GitHub Actions workflow files, and deployment automation are not covered here and are defined in `ci-cd-pipelines.md`
- Tailwind CSS class conventions, logical property rules, and component styling patterns are not covered here and are defined in `shared-ui.md`
- Test framework configuration, test file naming conventions, and per-workspace test runner setup are not covered here and are defined in per-workspace specs

## Related Specifications

- [typescript-config](typescript-config.md) — TypeScript compiler settings and `tsconfig.json` structure that the typecheck step in the quality gate validates against
- [ci-cd-pipelines](ci-cd-pipelines.md) — CI/CD pipeline definitions that run the same `pnpm quality` gate as a required status check on pull requests
- [shared-ui](shared-ui.md) — Shared UI component library containing the single `label` component with the only permitted `biome-ignore` suppression comment
- [api-framework](api-framework.md) — API framework spec whose Hono middleware and oRPC router code is subject to the Biome linting and formatting rules defined here

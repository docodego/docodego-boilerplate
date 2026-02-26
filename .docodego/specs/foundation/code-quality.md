[← Back to Roadmap](../ROADMAP.md)

# Code Quality

## Intent

This spec defines the code quality tooling stack for the DoCodeGo boilerplate monorepo, covering linting, formatting, dead code detection, commit message validation, and git hook automation. The tooling stack consists of Biome for linting and formatting, Knip for dead code and unused dependency detection, Commitlint for conventional commit enforcement, and Lefthook for git hook management. This spec ensures that every code change passing through the repository meets consistent formatting standards, contains no unused exports or dependencies, follows the conventional commit format, and triggers quality checks at the correct git lifecycle points without manual intervention.

## Acceptance Criteria

- [ ] Running `pnpm lint` exits with code = 0 on a clean checkout, producing 0 lint errors and 0 format violations
- [ ] Running `pnpm lint:fix` exits with code = 0 and auto-fixes all formatting violations in-place
- [ ] The Biome config sets indent width to 4, line width to 90, quote style to `"double"` — each value is present and enabled in the configuration file
- [ ] Biome trailing commas are enabled (set to `"all"`) and semicolons are enabled (set to `"always"`) — both values are present in the config
- [ ] Biome import sorting is enabled — the `organizeImports` setting is present and set to true in the config
- [ ] The root `package.json` contains a `"lint"` script and a `"lint:fix"` script — both are present and non-empty, and neither invokes Turborepo
- [ ] Running `pnpm knip` exits with code = 0 on a clean checkout, detecting 0 unused exports, 0 unused files, and 0 unused dependencies
- [ ] The `knip.json` configuration is present at the root and declares at least 10 workspace entries matching the workspaces in `pnpm-workspace.yaml`
- [ ] Knip runs with the `--cache` flag — the `"knip"` script in `package.json` contains the `--cache` argument
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

## Failure Modes

- **Formatting drift between developers**: A developer's editor does not have Biome configured as the default formatter, causing inconsistent formatting that passes locally but fails in CI. The `pre-push` hook catches the drift by running `pnpm lint` which returns error with a list of files that do not match the configured formatting rules, and the developer runs `pnpm lint:fix` to auto-correct all formatting violations before re-pushing.
- **Unused dependency accumulation**: A developer removes usage of a dependency from source code but forgets to remove it from `package.json`, increasing install time and bundle size over time. Knip detects the unused dependency during `pnpm quality` and returns error with the workspace name, dependency name, and the `package.json` path where it remains declared, prompting the developer to remove it before the push is accepted.
- **Invalid commit message format**: A developer writes a commit message like "fixed the bug" without the conventional commit format, breaking changelog generation and semantic versioning. The `commit-msg` Lefthook hook runs Commitlint which rejects the commit with exit code 1 and logs the expected format (`type(scope): message`) along with the list of valid types and scopes, preventing the invalid message from entering the repository history.
- **Quality gate bypass via hook skip**: A developer uses `git push --no-verify` to bypass the pre-push quality gate, pushing code that fails lint, typecheck, or test checks. The CI pipeline runs the identical `pnpm quality` command as a required status check, and returns error blocking the pull request merge with the same diagnostic output the developer would have seen locally, ensuring no unvalidated code reaches the main branch.

## Declared Omissions

- TypeScript compiler configuration and strict mode settings (covered by `typescript-config.md`)
- CI/CD pipeline job definitions and GitHub Actions workflows (covered by `ci-cd-pipelines.md`)
- Tailwind CSS class conventions and logical property rules (covered by `shared-ui.md`)
- Test framework configuration and test file conventions (covered by per-workspace specs)

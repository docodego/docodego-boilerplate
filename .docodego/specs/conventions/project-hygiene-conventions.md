---
id: CONV-2026-012
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Project Hygiene Conventions

## Intent

Defines dependency management, commit discipline, and package-manager exclusivity rules that keep the monorepo consistent across all `apps/` and `packages/` workspaces. Violations are caught by `grep`, `knip`, `commitlint`, and `biome` before code reaches the main branch.

## Rules

- IF a script in `apps/*/package.json`, `packages/*/package.json`, or any `.github/workflows/*.yml` file invokes `npx`, `bunx`, or `yarn` THEN `grep -rn "npx\|bunx\|yarn"` detects the violation — use `pnpm` or `pnpm dlx` exclusively
- IF a dependency appears in two or more workspace `package.json` files under `apps/` or `packages/` with a pinned version instead of `catalog:` THEN `grep -rn` across `apps/*/package.json` and `packages/*/package.json` detects the duplicate — define the version in `pnpm-workspace.yaml` under `catalog:` and reference it as `catalog:` in each workspace
- IF a new dependency is added to any workspace under `apps/` or `packages/` THEN it must meet: bundle size at most 5 KB (above 10 KB requires written justification in the pull request), weekly npm downloads above 1000, and last publish within 12 months — `knip` detects unused additions after the fact
- IF a file in `apps/**/*.ts` or `packages/**/*.ts` imports from `date-fns` THEN `biome` rule `noRestrictedImports` blocks the lint check — use native `Intl.DateTimeFormat` and `Intl.RelativeTimeFormat` APIs instead
- IF a commit message in the repository does not match `type(scope): message` with allowed types (`feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `dx`, `perf`, `build`, `revert`) and allowed scopes (`web`, `api`, `mobile`, `desktop`, `extension`, `contracts`, `ui`, `library`, `i18n`, `deps`, `repo`) THEN `commitlint` run by `lefthook` blocks the commit

## Enforcement

- L1 — `grep -rn "npx\|bunx\|yarn"` on `apps/` and `packages/`
- L2 — `grep -rn` across `apps/*/package.json` and `packages/*/package.json` for duplicate pinned versions
- L2 — `knip` detects unused dependencies in `apps/` and `packages/`
- L1 — `biome` rule `noRestrictedImports` blocks `date-fns` imports in `apps/` and `packages/`
- L1 — `commitlint` via `lefthook` validates commit message format

## Violation Signal

- `grep -rn "npx\|bunx\|yarn" apps/ packages/` returns matches in scripts or CI workflow files
- `grep -rn` across `apps/*/package.json` and `packages/*/package.json` finds duplicate pinned versions not using `catalog:`
- `knip --include=dependencies` reports unused or unvetted packages in `apps/` or `packages/`
- `biome lint` exits non-zero when `noRestrictedImports` catches a `date-fns` import in `apps/` or `packages/`
- `commitlint --from HEAD~1` exits non-zero for commits not matching `type(scope): message` format

## Correct vs. Forbidden

```jsonc
// Correct — packages/ui/package.json uses catalog:
{
    "dependencies": {
        "react": "catalog:"
    }
}

// Forbidden — packages/ui/package.json pins version directly
{
    "dependencies": {
        "react": "^19.0.0"
    }
}
```

## Remediation

- **pnpm exclusivity** — replace every `npx`, `bunx`, or `yarn` call with `pnpm` or `pnpm dlx` in `apps/*/package.json`, `packages/*/package.json`, and `.github/workflows/*.yml`
- **catalog duplication** — move the shared version into `pnpm-workspace.yaml` under `catalog:` and replace the pinned version with `catalog:` in each workspace `package.json`
- **dependency vetting** — remove the unvetted dependency with `pnpm remove` in the target workspace under `apps/` or `packages/`, or add written justification if bundle size exceeds 10 KB
- **date-fns removal** — replace `date-fns` calls with `Intl.DateTimeFormat` or `Intl.RelativeTimeFormat` and run `pnpm remove date-fns` in the affected workspace
- **commit format** — amend the commit message to `type(scope): message` using `git commit --amend` with an allowed type and scope from the convention list

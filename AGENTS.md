# AGENTS.md

Instructions for Agentic Coders when working on this codebase.

## Project

docodego-boilerplate — TypeScript monorepo template with 5 platform
targets (web, api, mobile, desktop, browser extension). Built with
pnpm workspaces and Turborepo.

## Commands

```
pnpm dev            Start all dev servers
pnpm build          Build all workspaces
pnpm typecheck      TypeScript check all workspaces
pnpm test           Run all tests
pnpm lint           Biome format + lint check (read-only)
pnpm lint:fix       Biome with auto-fix
pnpm lint:commit    Validate last commit message
pnpm knip           Dead code / unused dependency detection
pnpm quality        Full quality gate (lint → typecheck → test → knip)
pnpm typegen        Generate types (wrangler, router)
pnpm storybook      Start Storybook
pnpm hooks:install  Install git hooks via lefthook
```

## Formatting

- 4-space indent, CRLF line endings, 90-char line width
- 300-line max per file — split into modules if exceeded
- Double quotes, trailing commas, semicolons
- Kebab-case for all file and folder names
- TypeScript everywhere. JS only for configs that require it

## Workspace structure

```
apps/web              Astro 5 + React 19 (SSG landing + SPA dashboard)
apps/api              Hono 4 on Cloudflare Workers
apps/mobile           Expo 54 + React Native
apps/desktop          Tauri 2 (wraps web)
apps/browser-extension  WXT + React 19
packages/library      Shared validators, constants, utils
packages/contracts    oRPC contracts (shared API types)
packages/ui           Shadcn components
packages/i18n         i18n infrastructure (i18next)
e2e/                  Playwright E2E tests
```

## Conventions

- `@repo/<name>` scope for all workspace packages
- **pnpm only** — always use `pnpm` or `pnpm dlx`. Never use `npx`,
  `bunx`, or `yarn`. This applies to scripts, CI, and all commands
- Conventional commits: `type(scope): message`
  - Types: feat, fix, docs, refactor, test, chore, ci, dx, perf,
    build, revert
  - Scopes: web, api, mobile, desktop, extension, contracts, ui,
    library, i18n, deps, repo
- Use `catalog:` in workspace package.json for shared dependency
  versions (defined in pnpm-workspace.yaml)
- `packages/i18n` core export must never import React — use the
  `@repo/i18n/react` subpath for React bindings
- No date-fns — use native `Intl` APIs for date/number formatting

## Git

- Never commit or push without explicit user approval — show the diff and ask first
- NEVER include Claude co-author in commits/PRs
- Use `pwsh -Command` if bash command fails
- Quality gate is cumulative — later milestones must not break checks that previously passed

## TypeScript

- No file extensions in imports — `moduleResolution: "bundler"`
  handles resolution. `verbatimModuleSyntax: true` enforces
  `import type` for type-only imports
- tsconfig extends use relative paths (`../library/tsconfig.node.json`),
  never package references (`@repo/library/tsconfig.node.json`)
- Every workspace needs explicit `typecheck` and `test` scripts in
  package.json — turbo silently skips workspaces without them

## Tooling

- Biome runs at root (`pnpm lint`), not through turbo — too fast
  for turbo caching to help
- knip runs with `--cache` for faster consecutive runs
- **Scoring tools**: Run via `.docodego/tools/run <tool> <spec-file>` (auto-sources `.env`). See `.docodego/tools/README.md` for more info.

## Tailwind CSS

- Canonical classes only — no arbitrary values when a utility class
  exists. Run `pnpm dlx @tailwindcss/upgrade` after every `shadcn add`
- Logical properties only — `ps-`/`pe-` not `pl-`/`pr-`,
  `inset-s-`/`inset-e-` not `left-`/`right-`,
  `text-start`/`text-end` not `text-left`/`text-right`,
  `rounded-s-`/`rounded-e-` not `rounded-l-`/`rounded-r-`
- `translate-x` has no logical equivalent — use `rtl:` override

## UI Composition

- Shadcn `base-vega` style uses `@base-ui/react`, not Radix —
  don't assume Radix primitives
- tsconfig needs `@/*` path alias for Shadcn-generated imports
  (`@/lib/utils`, `@/components/ui/button`)
- After `shadcn add`, always:
  1. Run `pnpm dlx @tailwindcss/upgrade` for canonical classes
  2. Audit sub-components for missing RTL variants (e.g.
     `data-[side=inline-start/end]`) that parents have
  3. Run `pnpm lint:fix` to format and sort imports
- Only `label` gets `biome-ignore` for a11y — no other suppressions. You must edit component to fix a11y issues.

## Dependencies

- Prefer zero-dependency TypeScript. Libraries <5KB OK, >10KB needs justification.
- Before adding any dependency: check weekly downloads >1000, last publish <12 months, bundle size impact, no heavy transitive deps.

## File Limits

- **Source modules** — max ~300 lines (mapping/data-heavy: ~400)
- **Test files** — max ~400 lines, split by feature beyond that
- **Type definitions** — max ~250 lines
- When a file exceeds these limits, refactor before adding more code.

### Complexity over line count

- A short file with deep nesting is worse than a long flat file. Prefer flat, declarative code.
- **Exports** — if a file exports >5 distinct functions/classes, split into a folder-based structure (e.g., `utils/string.ts`, `utils/date.ts`) instead of one `utils.ts`.
- **Imports** — if the import block exceeds ~50 lines, the file is doing too much regardless of total line count. Split responsibilities into separate modules or extract a facade that re-exports from smaller files.

## Compact Instructions

When compacting, focus on: code changes made, test results, errors encountered, and current task state. Drop verbose tool output, file listings, and exploration logs.

## LLMS txt

Better Auth : Fetch(https://www.better-auth.com/llms.txt)
Base UI: Fetch(https://base-ui.com/llms.txt)
ShadCn : https://ui.shadcn.com/llms.txt
Orpc : https://orpc.dev/llms.txt

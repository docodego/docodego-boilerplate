---
id: CONV-2026-001
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Code Style Convention

## Intent

This convention enforces uniform formatting and file-naming rules across every workspace in the docodego-boilerplate monorepo. Consistent indentation, line endings, quote style, naming patterns, file-size limits, and language constraints reduce friction during code review, prevent merge-conflict noise, and allow automated tooling to catch violations before they reach the main branch.

## Rules

- IF a source file in `apps/**/*.ts` or `apps/**/*.tsx` or `packages/**/*.ts` or `packages/**/*.tsx` uses an indent width other than 4 spaces THEN `biome format` reports a formatting error for that file — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n
- IF a source file in `apps/**/*.ts` or `packages/**/*.ts` contains LF-only line endings instead of CRLF THEN `biome format` reports a line-ending mismatch for that file — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n
- IF a line in a source file under `apps/` or `packages/` exceeds 90 characters THEN `biome format` reports a line-width violation for that line — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n
- IF a string literal in a source file under `apps/` or `packages/` uses single quotes instead of double quotes THEN `biome format` rewrites that literal to use double quotes — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n
- IF a source file or folder under `apps/` or `packages/` uses camelCase, PascalCase, or snake_case in its name instead of kebab-case THEN `grep -rE` against the file tree detects the naming violation — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n
- IF a source module under `apps/**/*.ts` or `packages/**/*.ts` exceeds 300 lines THEN a `grep -c` line-count check flags that file for splitting into focused modules — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n
- IF a test file under `apps/**/*.test.ts` or `packages/**/*.test.ts` exceeds 400 lines THEN a `grep -c` line-count check flags that test file for splitting by feature — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n
- IF a type definition file under `apps/**/*.d.ts` or `packages/**/*.d.ts` exceeds 250 lines THEN a `grep -c` line-count check flags that type file for splitting into smaller declaration modules — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n
- IF a non-config source file under `apps/` or `packages/` uses the `.js` or `.jsx` extension instead of `.ts` or `.tsx` THEN `grep` against the file tree detects the language violation and flags it for conversion to TypeScript — web, api, mobile, desktop, browser-extension, library, contracts, ui, i18n

## Enforcement

- **L1** (indent width): `biome format --check` auto-detects indent violations in `apps/` and `packages/` workspaces
- **L1** (line endings): `biome format --check` auto-detects CRLF violations in `apps/` and `packages/` workspaces
- **L1** (line width): `biome format --check` auto-detects lines exceeding 90 characters in `apps/` and `packages/` workspaces
- **L1** (quote style): `biome format --check` auto-detects single-quote usage in `apps/` and `packages/` workspaces
- **L2** (kebab-case naming): CI script runs `grep -rE '[A-Z_]' --include='*.ts'` on file names under `apps/` and `packages/` to detect non-kebab-case violations
- **L2** (source module line limit): CI script runs `grep -c '' <file>` for each `*.ts` file under `apps/` and `packages/` and flags files exceeding 300 lines
- **L2** (test file line limit): CI script runs `grep -c '' <file>` for each `*.test.ts` file under `apps/` and `packages/` and flags files exceeding 400 lines
- **L2** (type definition line limit): CI script runs `grep -c '' <file>` for each `*.d.ts` file under `apps/` and `packages/` and flags files exceeding 250 lines
- **L3** (TypeScript-only rule): code review verifies that no new `.js` or `.jsx` files appear under `apps/` or `packages/` unless the file is a config that explicitly requires a `.js` extension

## Violation Signal

- Indent width: `biome format --check` exits non-zero when files under `apps/` or `packages/` use tabs or non-4-space indentation
- Line endings: `biome format --check` exits non-zero when files under `apps/` or `packages/` contain LF-only line endings
- Line width: `biome format --check` exits non-zero when lines in files under `apps/` or `packages/` exceed 90 characters
- Quote style: `biome format --check` exits non-zero when string literals under `apps/` or `packages/` use single quotes
- Kebab-case naming: `grep -rE '[A-Z]' --include='*.ts'` against file paths under `apps/` and `packages/` returns matches for non-kebab-case file or folder names
- Source module line limit: `grep -c '' <file>` for `*.ts` files under `apps/` and `packages/` returns a count exceeding 300
- Test file line limit: `grep -c '' <file>` for `*.test.ts` files under `apps/` and `packages/` returns a count exceeding 400
- Type definition line limit: `grep -c '' <file>` for `*.d.ts` files under `apps/` and `packages/` returns a count exceeding 250
- TypeScript-only rule: `grep -rE '\.jsx?$' --include='*.js' --include='*.jsx'` under `apps/` and `packages/` returns matches for non-config JavaScript files

## Correct vs. Forbidden

**Indent width (4 spaces)**

Correct:
```ts
// apps/web/src/utils/format.ts
function formatDate(date: Date): string {
    return new Intl.DateTimeFormat("en-US").format(date);
}
```

Forbidden:
```ts
// apps/web/src/utils/format.ts
function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US").format(date); // 2-space indent
}
```

**Kebab-case naming**

Correct: `apps/web/src/components/date-picker.tsx`

Forbidden: `apps/web/src/components/DatePicker.tsx`

**File extension**

Correct: `packages/library/src/validators.ts`

Forbidden: `packages/library/src/validators.js`

## Remediation

When `biome format --check` reports formatting violations (indent, line endings, line width, or quote style), run `pnpm lint:fix` from the repository root to auto-fix all L1 violations across `apps/` and `packages/` workspaces. When a CI script flags a kebab-case naming violation, rename the offending file or folder to use lowercase-kebab-case and update all import paths referencing the old name. When a line-count check flags a source module exceeding 300 lines, split the file into focused modules with single responsibilities under the same directory and re-export from an index file. When a test file exceeds 400 lines, split it by feature into separate test files. When a type definition exceeds 250 lines, break it into smaller declaration files grouped by domain. When code review identifies a new `.js` or `.jsx` file that is not a required config, rename it to `.ts` or `.tsx` and add proper type annotations.

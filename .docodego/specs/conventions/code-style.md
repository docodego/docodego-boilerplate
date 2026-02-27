---
id: CONV-2026-001
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Code Style

## Intent

Enforces uniform formatting, naming, and file-size rules across all `apps/` and `packages/` workspaces. Formatting violations are caught by `biome`; naming and size violations are caught by CI scripts before merge.

## Rules

- IF a file in `apps/**/*.ts` or `packages/**/*.ts` uses indent width other than 4 spaces THEN `biome format --check` reports a formatting error
- IF a file in `apps/**/*.ts` or `packages/**/*.ts` uses LF-only line endings instead of CRLF THEN `biome format --check` reports a line-ending mismatch
- IF a line in `apps/` or `packages/` exceeds 90 characters THEN `biome format --check` reports a line-width violation
- IF a string literal in `apps/` or `packages/` uses single quotes THEN `biome format --check` rewrites it to double quotes
- IF a file or folder name under `apps/` or `packages/` is not kebab-case THEN a CI `grep -rE` script flags the naming violation
- IF a source module in `apps/**/*.ts` or `packages/**/*.ts` exceeds 300 lines THEN a CI line-count check flags it for splitting
- IF a test file in `apps/**/*.test.ts` or `packages/**/*.test.ts` exceeds 400 lines THEN a CI line-count check flags it for splitting
- IF a type definition in `apps/**/*.d.ts` or `packages/**/*.d.ts` exceeds 250 lines THEN a CI line-count check flags it for splitting
- IF a non-config source file in `apps/` or `packages/` uses `.js` or `.jsx` extension THEN code review flags it for conversion to TypeScript

## Enforcement

- L1 — `biome format --check` on indent width in `apps/` and `packages/`
- L1 — `biome format --check` on line endings in `apps/` and `packages/`
- L1 — `biome format --check` on line width in `apps/` and `packages/`
- L1 — `biome format --check` on quote style in `apps/` and `packages/`
- L2 — CI `grep -rE '[A-Z_]'` on file names under `apps/` and `packages/`
- L2 — CI `grep -c` on `*.ts` source files in `apps/` and `packages/`
- L2 — CI `grep -c` on `*.test.ts` files in `apps/` and `packages/`
- L2 — CI `grep -c` on `*.d.ts` files in `apps/` and `packages/`
- L3 — code review blocks new `.js`/`.jsx` in `apps/` and `packages/`

## Violation Signal

- `biome format --check` exits non-zero for indent violations in `apps/` or `packages/`
- `biome format --check` exits non-zero for CRLF violations in `apps/` or `packages/`
- `biome format --check` exits non-zero for lines over 90 chars in `apps/` or `packages/`
- `biome format --check` exits non-zero for single-quote strings in `apps/` or `packages/`
- `grep -rE '[A-Z]' --include='*.ts'` on paths under `apps/` and `packages/` returns non-kebab names
- `grep -c ''` on `*.ts` files in `apps/` or `packages/` returns count >300
- `grep -c ''` on `*.test.ts` files in `apps/` or `packages/` returns count >400
- `grep -c ''` on `*.d.ts` files in `apps/` or `packages/` returns count >250
- `grep -rE '\.jsx?$'` under `apps/` or `packages/` returns non-config JS files

## Correct vs. Forbidden

```ts
// Correct — apps/web/src/utils/format.ts
function formatDate(date: Date): string {
    return new Intl.DateTimeFormat("en-US").format(date);
}

// Forbidden — 2-space indent, single quotes
function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US').format(date);
}
```

Correct filename: `apps/web/src/components/date-picker.tsx`
Forbidden filename: `apps/web/src/components/DatePicker.tsx`

## Remediation

- **Formatting** — run `pnpm lint:fix` to auto-fix indent, line endings, width, and quotes across `apps/` and `packages/`
- **Kebab-case** — rename file/folder to lowercase-kebab-case and update all import paths referencing it
- **Line-count** — split into focused modules in the same directory and re-export from an index file
- **JS extension** — rename to `.ts`/`.tsx` and add type annotations

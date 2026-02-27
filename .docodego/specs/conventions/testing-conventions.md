---
id: CONV-2026-010
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Testing Conventions

## Intent

Standardizes test tooling, file placement, and naming across all `apps/` and `packages/` workspaces. Each platform target uses exactly one test runner and one E2E framework, eliminating runner drift and ensuring `pnpm test` executes every suite without configuration guesswork.

## Rules

- IF a unit or integration test file exists under `apps/**/*.test.ts` or `packages/**/*.test.ts` THEN it MUST use `vitest` as the test runner — not Jest, Mocha, or any other runner
- IF an E2E test targets the web app THEN it MUST live under `e2e/` and use `playwright` — not Cypress, Selenium, or any other E2E framework
- IF an E2E test targets `apps/mobile` THEN it MUST use Maestro flow files stored under `apps/mobile/e2e/` — not Detox or Appium
- IF a source file exists at `apps/**/*.ts` or `packages/**/*.ts` THEN its unit test MUST be co-located in the same directory with a `.test.ts` or `.test.tsx` suffix — not placed in a separate `__tests__/` folder
- IF a `describe` block exists in `apps/**/*.test.ts` or `packages/**/*.test.ts` THEN the description string THAT follows MUST name the unit under test; IF an `it` block exists THEN its description MUST complete the sentence "it verbs an outcome"
- IF a `test.skip`, `it.skip`, `describe.skip`, `test.only`, `it.only`, or `describe.only` call exists in `apps/**/*.test.ts` or `packages/**/*.test.ts` THEN a `// TODO: <ticket-id>` comment MUST appear on the preceding line

## Enforcement

- L1 — `vitest` config in `apps/` and `packages/` rejects non-vitest imports
- L1 — `playwright` config enforces `e2e/` as the sole web E2E test directory
- L2 — CI `grep -rn 'from .jest'` detects Jest imports in `apps/` and `packages/`
- L2 — CI `grep -rn '__tests__/'` detects forbidden test folder patterns in `apps/` and `packages/`
- L2 — CI `grep -rn 'describe\|it\|test' --include='*.test.ts'` validates naming in `apps/` and `packages/`
- L2 — CI `grep -Bn1 '\.skip\|\.only'` detects missing ticket comments in `apps/` and `packages/`

## Violation Signal

- `grep -rn "from 'jest'" --include='*.test.ts'` under `apps/` or `packages/` returns non-vitest imports
- `grep -rn '__tests__/' --include='*.ts'` under `apps/` or `packages/` detects non-co-located test paths
- `grep -rn 'cypress\|selenium' --include='*.ts'` under `e2e/` detects forbidden E2E frameworks
- `grep -rn 'detox\|appium' --include='*.ts'` under `apps/mobile/` detects forbidden mobile E2E tools
- `grep -Pn 'describe\(' --include='*.test.ts'` under `apps/` or `packages/` paired with lint validates naming
- `grep -Bn1 '\.skip\|\.only' --include='*.test.ts'` under `apps/` or `packages/` finds missing TODO ticket lines

## Correct vs. Forbidden

```ts
// Correct — apps/web/src/utils/format.test.ts (co-located, vitest)
import { describe, it, expect } from "vitest";
import { formatDate } from "./format";

describe("formatDate", () => {
    it("returns ISO string for valid input", () => {
        expect(formatDate(new Date("2026-01-01"))).toBe("1/1/2026");
    });
});

// Forbidden — apps/web/src/__tests__/format.test.ts (separate folder, jest)
import { formatDate } from "../format";

test("formatDate works", () => {
    expect(formatDate(new Date("2026-01-01"))).toBe("1/1/2026");
});
```

## Remediation

- Replace Jest/Mocha imports with `vitest` equivalents and update `apps/` or `packages/` workspace config to reference the vitest config
- Move files from `__tests__/` to sit beside their source file in `apps/` or `packages/` and rename with `.test.ts` suffix
- Replace Cypress or Selenium test files under `e2e/` with Playwright equivalents and remove the old framework dependency
- Add a `// TODO: TICKET-NNN` comment on the line before every `.skip` or `.only` call in `apps/` or `packages/` test files
- Rewrite vague `describe`/`it` descriptions in `apps/` or `packages/` to name the unit and verb the outcome explicitly

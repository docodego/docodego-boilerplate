---
id: CONV-2026-009
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Data Access Conventions

## Intent

Standardizes how `apps/api` interacts with the database layer in `apps/api/src/db/`. All queries use Drizzle ORM with explicit column selects, multi-table writes wrap in transactions, loop-based queries are replaced with batched alternatives, and query helpers stay co-located with their Drizzle schema files.

## Rules

- IF a function in `apps/api/**` executes a database query THEN it MUST use the Drizzle ORM query builder — no raw SQL strings via `db.run()` or template literals
- IF a Drizzle query in `apps/api/src/db/**` uses `.select()` THEN it MUST list explicit columns — no bare `.select()` which returns all columns including sensitive fields
- IF a service function in `apps/api/src/services/**` writes to 2 or more database tables THEN it MUST wrap all writes in a single `db.transaction()` call
- IF a function in `apps/api/**` calls a database query inside a loop iterating over a result set THEN extract it to a single batched query with `.where(inArray(...))` — count equals 1 violation per loop-query pair
- IF a query helper function exists in `apps/api/src/db/**` THEN it MUST be defined in the same file as the Drizzle schema it queries — no query functions scattered across service files

## Enforcement

- L1 — `biome` lint rule flags `db.run()` or tagged template SQL in `apps/api/**`
- L2 — CI `grep -rn "\.select()" apps/api/src/db/` detects bare `.select()` without column arguments
- L2 — CI `grep -rn "db\.\(insert\|update\|delete\)" apps/api/src/services/` cross-referenced against `db.transaction` usage
- L2 — CI `grep -Pn "for\s*\(.*\)\s*\{[^}]*db\." apps/api/src/` detects queries inside loops
- L3 — code review on `apps/api/src/db/**` verifies query helpers are co-located with their schema definitions

## Violation Signal

- `grep -rn "db.run\|sql\`" apps/api/src/` returns raw SQL usage bypassing the Drizzle query builder
- `grep -rn "\.select()" apps/api/src/db/` returns bare `.select()` calls without explicit column lists
- `grep -rn "db\.\(insert\|update\|delete\)" apps/api/src/services/` returns multi-table writes outside a `db.transaction` block
- `grep -Pn "for\b.*db\." apps/api/src/` returns database queries executed inside loop bodies
- `grep -rn "from.*schema" apps/api/src/services/` returns query helpers imported from service files instead of `apps/api/src/db/`

## Correct vs. Forbidden

```ts
// Correct — apps/api/src/db/users.ts — explicit columns
const result = await db
    .select({ id: users.id, name: users.name })
    .from(users)
    .where(eq(users.orgId, orgId));

// Forbidden — bare .select() returns all columns
const result = await db.select().from(users);
```

```ts
// Correct — apps/api/src/services/billing.ts — transaction
await db.transaction(async (tx) => {
    await tx.insert(invoices).values(invoice);
    await tx.update(subscriptions).set({ status: "active" });
});

// Forbidden — two writes without transaction wrapper
await db.insert(invoices).values(invoice);
await db.update(subscriptions).set({ status: "active" });
```

## Remediation

- **Raw SQL** — replace `db.run()` or template-literal SQL with the equivalent Drizzle query builder chain in `apps/api/src/db/`
- **Bare `.select()`** — add an explicit column object listing only the fields the caller needs, omitting sensitive columns like `passwordHash`
- **Missing transaction** — wrap the multi-table write block in `db.transaction(async (tx) => { ... })` and switch all inner calls to use `tx`
- **N+1 loop query** — collect the IDs from the outer result set and replace the inner loop query with a single `.where(inArray(table.id, ids))` call
- **Scattered query helper** — move the function into the schema file under `apps/api/src/db/` and update all import paths

---
id: CONV-2026-007
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# API Layer Conventions

## Intent

Enforces consistent API patterns across `apps/api` and `packages/contracts`. All oRPC procedures use verb-noun naming with Zod-validated inputs and outputs, Hono handlers stay thin by delegating logic to service functions, and middleware contains only cross-cutting concerns.

## Rules

- IF an oRPC procedure in `packages/contracts/**` is named without a verb-noun pattern (e.g. `user` instead of `getUser`) THEN `grep -rE` detects the non-conforming export name in `packages/contracts/src/`
- IF an oRPC procedure in `packages/contracts/**` defines an input or output without a Zod schema THEN `tsc` emits a type error because the oRPC contract type requires `z.ZodType` for input and output
- IF a Hono handler in `apps/api/**` returns HTTP 401 THEN the request lacks valid authentication credentials; IF it returns 403 THEN the user is authenticated but lacks permission; IF it returns 404 THEN the resource does not exist — code review catches status code misuse
- IF a Hono route handler in `apps/api/src/routes/**` contains more than one await chain or conditional branch THEN extract the logic into a service function in `apps/api/src/services/`
- IF a Hono middleware in `apps/api/src/middleware/**` contains domain logic beyond auth or session checks THEN code review rejects it — middleware in `apps/api/` handles only cross-cutting concerns

## Enforcement

- L2 — `grep -rE` on `packages/contracts/src/` for exports not matching camelCase verb-noun
- L1 — `tsc --noEmit` on `packages/contracts` for missing Zod schema types
- L3 — code review on `apps/api/src/routes/` for HTTP status code correctness
- L3 — code review on `apps/api/src/routes/` for handler complexity and service extraction
- L3 — code review on `apps/api/src/middleware/` for domain logic leaking into middleware

## Violation Signal

- `grep -rE "export (const|function) [a-z]+[A-Z]" packages/contracts/src/` returns procedure names not starting with `get`, `list`, `create`, `update`, or `delete`
- `tsc --noEmit` on `packages/contracts` exits non-zero when a procedure input or output omits a `z.ZodType` definition
- `grep -rn "c\.json(.*40[13])" apps/api/src/routes/` returns handlers where 401 or 403 status codes pair with incorrect authorization or authentication context
- `grep -c "await"` on handler files in `apps/api/src/routes/` returns count greater than 1 per handler function
- `grep -rn "transform\|validate\|calculate"` in `apps/api/src/middleware/` returns domain logic in middleware files

## Correct vs. Forbidden

```ts
// Correct — packages/contracts/src/user.ts (verb-noun naming with Zod)
export const getUser = contract.input(z.object({ id: z.string() }));
export const listUsers = contract.input(z.object({ page: z.number() }));

// Forbidden — noun-only name, no Zod schema
export const user = contract.input({ id: "string" });
```

```ts
// Correct — apps/api/src/routes/user.ts (thin handler)
app.get("/users/:id", async (c) => {
    const result = await userService.getById(c.req.param("id"));
    return c.json(result);
});

// Forbidden — business logic directly in handler
app.get("/users/:id", async (c) => {
    const raw = await db.query("SELECT * FROM users WHERE id = ?");
    const transformed = raw.map((r) => ({ ...r, name: r.first }));
    return c.json(transformed);
});
```

## Remediation

- **Procedure naming** — rename the export in `packages/contracts/src/` to a camelCase verb-noun pattern like `getUser`, `listUsers`, `createOrder`, or `deleteItem`
- **Missing Zod schema** — wrap the input and output definitions with `z.object(...)` in `packages/contracts/` so `tsc` resolves the expected `z.ZodType` constraint
- **Status code misuse** — review the HTTP semantics: 401 for missing or invalid credentials in `apps/api/`, 403 for insufficient permissions, 404 for absent resources
- **Handler complexity** — extract the multi-step logic from the route handler in `apps/api/src/routes/` into a function in `apps/api/src/services/` and call it from the handler
- **Middleware domain logic** — move data transformation, validation, or business rules out of `apps/api/src/middleware/` into `apps/api/src/services/` or route-level utilities

[← Back to Roadmap](../ROADMAP.md)

# API Framework

## Intent

This spec defines the Hono web framework configuration, middleware stack, error handling, oRPC router integration, and API documentation setup for the DoCodeGo boilerplate API running on Cloudflare Workers. The API serves as the single backend for all 5 platform targets (web, mobile, desktop, browser extension, and developer API consumers). The Hono app is configured with a specific middleware execution order, a structured error handler, CORS policy, locale detection, and an oRPC router that exposes type-safe RPC endpoints. Scalar provides auto-generated interactive API documentation from the OpenAPI spec produced by oRPC. This spec ensures that every incoming request passes through the correct middleware chain and that all API responses follow a consistent format.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| D1 (Cloudflare SQL) | read/write | Every database query via Drizzle ORM | Route handlers return 500 and the global error handler falls back to a generic JSON error message for the client |
| R2 (Cloudflare Storage) | read/write | File upload/download operations | Affected file routes return 500 and the error handler degrades gracefully while non-storage routes remain fully operational |
| `@repo/contracts` | read | App startup (schema registration) | Build fails at compile time because the oRPC router cannot resolve contract types and CI alerts to block deployment |
| `@repo/i18n` | read | Each request (locale middleware) | Translation function falls back to the default English locale strings so responses remain readable but untranslated for non-English users |
| Better Auth | read/write | Requests to `/api/auth/**` | Auth endpoints return 500 and the error handler degrades to a generic authentication error while non-auth routes remain unaffected |

## Behavioral Flow

1. **[Client]** → sends HTTP request to Cloudflare Worker
2. **[CORS middleware]** → validates origin against allowed web app URL → rejects with 403 if origin is not permitted
3. **[Logger middleware]** → logs request method, path, and timing
4. **[Locale middleware]** → parses `Accept-Language` header → resolves to `"en"` or `"ar"` → attaches `t()` function to Hono context → sets `Content-Language` response header
5. **[Hono router]** → matches request path:
   - `/api/auth/**` → **[Better Auth handler]** → processes auth request → returns response
   - `/api/reference` → **[Scalar middleware]** → returns HTML documentation page
   - All other API routes → **[oRPC router]** → validates input against Zod schemas → executes handler → returns JSON response
6. **[Error handler]** → catches any unhandled error from steps 2–5 → returns JSON `{ code, message }` with the mapped HTTP status code (400, 401, 403, 404, or 500) → redacts stack trace in production

## State Machine

No stateful entities. The API framework is a stateless request-response pipeline — no entities have a lifecycle within this spec's scope.

## Business Rules

No conditional business rules. Middleware executes unconditionally on every request in fixed order.

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Unauthenticated | Access `/api/reference`, send requests to `/api/auth/**` | Access any oRPC route requiring a session | Cannot see protected resource data |
| Authenticated | Access all oRPC routes, access `/api/reference` | N/A (route-level auth covered by route-specific specs) | Per-route visibility defined in route-specific specs |

## Acceptance Criteria

- [ ] A Hono app instance is present at `apps/api/src/index.ts` and is exported as the default Cloudflare Worker handler
- [ ] The Hono app type-binds its `Env` to include at least 2 Cloudflare bindings: `DB` (D1) and `STORAGE` (R2) — both are present in the type definition
- [ ] The middleware stack executes in the following order, and each middleware is present in the app configuration: CORS, request logger, locale detection, Better Auth handler, oRPC router
- [ ] The CORS middleware sets `origin` to the web app URL, `credentials` to true, and `allowHeaders` to include `"Content-Type"` — all 3 values are present
- [ ] The locale detection middleware parses the `Accept-Language` header, resolves it to a supported locale (`"en"` or `"ar"`), and attaches a `t()` translation function to the Hono context — the function is present and callable by downstream handlers
- [ ] The response from every route includes a `Content-Language` header — this header is present in all API responses with a value of `"en"` or `"ar"`
- [ ] The Better Auth handler is mounted at `/api/auth/**` and processes all auth-related requests — this route pattern is present in the app configuration
- [ ] The oRPC router is mounted and serves all RPC endpoints — the router is present and connected to the contracts defined in `@repo/contracts`
- [ ] The oRPC router generates an OpenAPI specification at runtime from Zod schemas — the spec is present and accessible at a dedicated endpoint
- [ ] The Scalar API reference middleware serves interactive documentation at `/api/reference` — this route returns 200 and renders the documentation page
- [ ] The `/api/reference` endpoint returns 200 without a session cookie or token — it is publicly accessible with no authentication required
- [ ] The global error handler catches all unhandled errors and returns a JSON response with the structure `{ code: string, message: string }` — both fields are present in every error response
- [ ] Authentication failures return 401, authorization failures return 403, validation errors return 400, missing resources return 404, and unexpected errors return 500 — each status code is present in the error handler mapping
- [ ] Validation errors (Zod schema rejections) return 400 with field-level detail — the response body includes at least 1 field name and its validation error message
- [ ] In production, the error handler redacts internal details from 500 responses — the `message` field contains a generic string and the stack trace is absent
- [ ] In development, the error handler includes the full stack trace in 500 responses — the stack trace is present in the response body
- [ ] The `wrangler.toml` sets `compatibility_date` to `"2025-01-01"` and enables the `nodejs_compat` flag — both values are present

## Constraints

- All API responses use JSON format — the count of HTML responses from API routes (excluding the Scalar documentation page) equals 0. The Scalar page at `/api/reference` is the only route that returns HTML content.
- The Hono app runs exclusively on Cloudflare Workers — no Express, Fastify, or other Node.js server frameworks are installed. The count of `express`, `fastify`, or `koa` imports in the API workspace equals 0.
- The oRPC router consumes contracts from `@repo/contracts` — all route input and output schemas are defined in the contracts package, not inline in route handlers. The count of inline Zod schema definitions in route handler files equals 0 for request/response validation.
- The API does not serve static files — static assets are served by Cloudflare Pages (web) or bundled into platform-specific apps. The count of static file serving middleware in the Hono app equals 0.
- TanStack Query on the client is configured with `retry` set to 1 — a failed request retries exactly 1 time before being treated as a failure. This value is present in the query client configuration.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The client sends a request without an `Accept-Language` header present in the request | Locale middleware falls back to the default locale `"en"` and attaches the English translation `t()` function to the Hono context | Response includes `Content-Language: en` header and the body contains English-language strings |
| The `Accept-Language` header contains an unsupported locale such as `fr` that is not in the supported set | Locale middleware falls back to `"en"` because the requested locale is not in the supported locale list of `en` and `ar` | Response includes `Content-Language: en` header regardless of the unsupported locale value sent |
| The `Accept-Language` header is malformed with invalid syntax such as `;;;` that cannot be parsed | Locale middleware degrades gracefully and falls back to `"en"` without throwing an unhandled exception or crashing the worker | Response includes `Content-Language: en` and the HTTP status code is not 500 |
| The client sends a request body that contains invalid JSON syntax that cannot be parsed by the runtime | The oRPC router rejects the request with HTTP 400 before the request reaches the route handler logic | Response body contains a `code` field indicating a JSON parse error and the HTTP status is 400 |
| The client sends a request to a URL path that does not match any registered route in the Hono router | Hono returns HTTP 404 with the standard error JSON structure `{ code, message }` and does not fall through silently | Response status is 404 and the response body is valid JSON containing both `code` and `message` fields |
| A CORS preflight OPTIONS request arrives from an origin that is not in the allowed origin list | The CORS middleware rejects the preflight request and does not forward it to any downstream route handler | Response omits the `Access-Control-Allow-Origin` header, signaling the browser to block the cross-origin request |

## Failure Modes

- **Middleware ordering error**
    - **What happens:** Locale detection middleware is placed after the oRPC router, causing route handlers to access an undefined `t()` function.
    - **Source:** Incorrect middleware registration order during development.
    - **Consequence:** Every localized response returns 500 and users see generic error messages instead of translated content.
    - **Recovery:** The error handler falls back to a generic English message for the 500 response, and the integration test verifies that a request with `Accept-Language: ar` returns `Content-Language: ar` with a localized message — CI alerts and blocks deployment if the test fails.
- **CORS rejection on cross-origin requests**
    - **What happens:** The CORS `origin` value does not match the web app's deployment URL, causing browsers to block all API requests from the frontend with a CORS preflight failure.
    - **Source:** Misconfigured environment variable or hardcoded origin value after a domain change.
    - **Consequence:** The frontend cannot communicate with the API and all cross-origin calls fail silently in the browser.
    - **Recovery:** The system degrades to blocking all cross-origin requests until the origin is corrected, and the integration test sends a preflight OPTIONS request verifying `Access-Control-Allow-Origin` and `Access-Control-Allow-Credentials` headers — CI alerts and blocks deployment if either header is missing.
- **OpenAPI spec desync**
    - **What happens:** A developer modifies a Zod schema in `@repo/contracts` but the API documentation shows stale endpoint definitions.
    - **Source:** Attempted bypass of the contracts package by defining inline schemas in route handlers.
    - **Consequence:** API consumers rely on incorrect documentation, leading to integration failures.
    - **Recovery:** oRPC generates the OpenAPI spec at runtime from Zod schemas, so desync cannot occur for contract-based routes — CI typecheck alerts on inline schema definitions because route handler types will not match contract types, and deployment is blocked.
- **Error handler leaking stack traces in production**
    - **What happens:** The global error handler fails to check the environment flag and includes full stack traces in 500 responses served to end users.
    - **Source:** Missing or incorrect environment check in error handler logic.
    - **Consequence:** End users see internal file paths, dependency versions, and code structure, aiding potential attackers.
    - **Recovery:** The error handler falls back to a generic message string for all 500 responses in production mode, never exposing internals — the integration test triggers a 500 error in production mode and verifies the response body contains zero stack trace lines, and CI alerts and blocks deployment if any internal detail is present.
- **D1 database connection failure**
    - **What happens:** The D1 binding is unavailable or returns connection errors during a request that requires database access via Drizzle ORM.
    - **Source:** Cloudflare D1 service degradation, misconfigured binding name in `wrangler.toml`, or exceeded D1 rate limits.
    - **Consequence:** All routes that query the database return 500 errors and auth flows that check session state also fail, effectively locking users out.
    - **Recovery:** The global error handler falls back to a generic JSON error response with a 500 status code and a user-safe message, and the system degrades gracefully because non-database routes such as `/api/reference` and the OpenAPI spec endpoint continue serving normally.
- **Malicious or oversized request payload**
    - **What happens:** An attacker sends an extremely large JSON body or deeply nested payload to an oRPC endpoint, attempting to exhaust worker memory or CPU time.
    - **Source:** Adversarial input from an unauthenticated or authenticated client sending a crafted request body.
    - **Consequence:** The Cloudflare Worker exceeds its CPU time limit or memory allocation and the request is terminated by the runtime, returning a platform-level error.
    - **Recovery:** Cloudflare Workers enforce a 128 MB memory limit and a CPU time ceiling per request, so the platform degrades the individual request without affecting other concurrent requests — Zod schema validation in the oRPC router rejects non-conforming payloads before handler logic executes, providing an early exit for malformed input.

## Declared Omissions

- Better Auth plugin configuration, session strategy, and OAuth provider setup are not covered here and are defined in `auth-server-config.md`
- Database schema definitions, migration strategy, and Drizzle ORM table configuration are not covered here and are defined in `database-schema.md`
- oRPC contract definitions, shared Zod schemas, and API type exports are not covered here and are defined in `shared-contracts.md`
- Frontend TanStack Query configuration, error display components, and client-side retry logic are not covered here and are defined in behavioral specs
- CI/CD deployment workflow for Cloudflare Workers, GitHub Actions pipelines, and preview environments are not covered here and are defined in `ci-cd-pipelines.md`

## Related Specifications

- [auth-server-config](auth-server-config.md) — Better Auth plugin configuration, session strategy, and OAuth provider setup for the authentication system
- [database-schema](database-schema.md) — Database schema definitions, migration strategy, and Drizzle ORM table configuration for Cloudflare D1
- [shared-contracts](shared-contracts.md) — oRPC contract definitions and Zod schemas consumed by the router for type-safe API endpoints
- [shared-i18n](shared-i18n.md) — Internationalization infrastructure providing the `t()` translation function used by the locale middleware
- [ci-cd-pipelines](ci-cd-pipelines.md) — CI/CD deployment workflow, GitHub Actions pipelines, and preview environment configuration for Cloudflare Workers

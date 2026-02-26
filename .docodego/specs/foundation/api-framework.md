[← Back to Roadmap](../ROADMAP.md)

# API Framework

## Intent

This spec defines the Hono web framework configuration, middleware stack, error handling, oRPC router integration, and API documentation setup for the DoCodeGo boilerplate API running on Cloudflare Workers. The API serves as the single backend for all 5 platform targets (web, mobile, desktop, browser extension, and developer API consumers). The Hono app is configured with a specific middleware execution order, a structured error handler, CORS policy, locale detection, and an oRPC router that exposes type-safe RPC endpoints. Scalar provides auto-generated interactive API documentation from the OpenAPI spec produced by oRPC. This spec ensures that every incoming request passes through the correct middleware chain and that all API responses follow a consistent format.

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

## Failure Modes

- **Middleware ordering error**: The locale detection middleware is placed after the oRPC router, causing route handlers to access an undefined `t()` function and returning error 500 on every localized response. The integration test for locale detection verifies that a request with `Accept-Language: ar` returns a response with `Content-Language: ar` and a localized error message, and returns error if the header is absent or the translation function is not attached to the context.
- **CORS rejection on cross-origin requests**: The CORS `origin` value does not match the web app's deployment URL, causing the browser to block all API requests from the frontend with a CORS preflight failure. The integration test sends a preflight OPTIONS request with the web app origin and verifies the response includes `Access-Control-Allow-Origin` matching that origin and `Access-Control-Allow-Credentials` set to true, and returns error if either header is absent or incorrect.
- **OpenAPI spec desync**: A developer modifies a Zod schema in `@repo/contracts` but the oRPC router does not regenerate the OpenAPI spec, causing the Scalar documentation to display stale endpoint definitions. Since oRPC generates the spec at runtime from the Zod schemas, this desync cannot occur — the spec is always derived from the current contract definitions. If a developer bypasses contracts and defines inline schemas, the CI typecheck returns error because the route handler types do not match the contract types.
- **Error handler leaking stack traces in production**: The global error handler fails to check the environment and includes full stack traces in 500 responses served to end users, exposing internal file paths and dependency versions. The integration test for error handling sends a request that triggers a 500 error in production mode and verifies that the response body contains 0 stack trace lines and the `message` field equals the generic error string, returning error if any internal detail is present.

## Declared Omissions

- Better Auth plugin configuration and session strategy (covered by `auth-server-config.md`)
- Database schema and migration strategy (covered by `database-schema.md`)
- oRPC contract definitions and Zod schemas (covered by `shared-contracts.md`)
- Frontend TanStack Query configuration and error display (covered by behavioral specs)
- CI/CD deployment workflow for Cloudflare Workers (covered by `ci-cd-pipelines.md`)

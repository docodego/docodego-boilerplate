[← Back to Roadmap](../ROADMAP.md)

# Auth Server Config

## Intent

This spec defines the server-side authentication configuration for the DoCodeGo boilerplate, covering Better Auth initialization, plugin wiring, cookie strategy, session management, and client-side auth helper setup. Better Auth is initialized as a Hono middleware with 7 plugins: Email OTP, Passkey, Anonymous, SSO, Organization (with teams), Admin, and DodoPayments. This spec ensures that the auth server is configured with the correct database adapter, cookie settings, session parameters, and plugin options so that all authentication flows described in the behavioral specs function correctly across web, mobile, desktop, and browser extension platforms.

## Acceptance Criteria

- [ ] A Better Auth server instance is present at `apps/api/src/auth.ts` (or equivalent path) and exports the configured auth handler
- [ ] The auth server uses the Drizzle adapter with the D1 database binding — the `database` option references the Drizzle instance connected to the `DB` binding
- [ ] Exactly 7 plugins are enabled on the server: `emailOTP`, `passkey`, `anonymous`, `sso`, `organization`, `admin`, and `dodoPayments` — each plugin is present in the `plugins` array
- [ ] The `emailOTP` plugin sets OTP length to 6 digits and OTP expiry to 300 seconds (5 minutes)
- [ ] The `emailOTP` plugin sets `disableSignUp` to false, allowing OTP sign-in to create new accounts automatically
- [ ] The `emailOTP` plugin provides a `sendVerificationOTP` callback that is present and dispatches the OTP code via the email service
- [ ] The `organization` plugin enables teams — the `teams` option is present and set to true
- [ ] The `anonymous` plugin is enabled with 0 additional configuration required beyond its presence in the plugins array
- [ ] The session configuration sets `expiresIn` to 604800 seconds (7 days) and `updateAge` to 86400 seconds (24 hours)
- [ ] The session cookie sets httpOnly: true, secure: true in production, sameSite: `"lax"`, and path: `"/"` — all 4 values are present
- [ ] A hint cookie named `docodego_authed` is set alongside the session cookie — it is non-httpOnly (readable by JavaScript), carries no sensitive data, and its value equals true when a session is active
- [ ] The `user` schema is extended with a `preferredLocale` field that is present and nullable — it accepts `"en"` or `"ar"` or null
- [ ] The `session` schema is extended with an `activeTeamId` field that is present and nullable
- [ ] A Better Auth client instance is present at `apps/web/src/lib/auth-client.ts` and exports at least 5 plugin clients: `emailOTPClient`, `passkeyClient`, `anonymousClient`, `organizationClient`, and `ssoClient`
- [ ] The auth client sets `baseURL` to the API server URL — this value is present and non-empty
- [ ] Running the auth handler against a test request with a valid session cookie returns 200 and the session object contains `userId`, `expiresAt`, and `activeOrganizationId` fields that are all present

## Constraints

- The auth system is entirely passwordless — no password plugin is installed, no password fields exist in the user or account tables, and the count of password-related imports or configurations in the auth setup equals 0. The only sign-in methods are Email OTP, Passkey, Anonymous, and SSO.
- The `dodoPayments` plugin configuration is commented out in the initial boilerplate, awaiting payment credentials. The plugin import is present but its configuration block is wrapped in a comment with a `Status: Planned` annotation. The count of active (uncommented) DodoPayments configuration lines equals 0 until credentials are provided.
- The auth server runs on Cloudflare Workers — all auth logic executes in the edge runtime with no Node.js-specific APIs. The count of `node:` protocol imports in auth-related files equals 0.
- Better Auth's built-in `generate` CLI is not used for schema generation — all auth tables are defined manually in Drizzle schema files (as specified in `database-schema.md`). The count of `npx @better-auth/cli generate` references in scripts equals 0.

## Failure Modes

- **Plugin initialization failure**: A Better Auth plugin is misconfigured (wrong option type, missing required callback), causing the auth server to throw during initialization. The Hono app catches the startup error and returns error 500 on all auth routes with a diagnostic message that logs the plugin name and the specific configuration error to the Worker logs, allowing the developer to identify and fix the misconfigured plugin.
- **Cookie domain mismatch**: The session cookie is set with a domain that does not match the API server's actual domain, causing the browser to silently reject the cookie and preventing session persistence. The auth middleware detects that no session cookie is present on subsequent requests from authenticated users and logs a warning that includes the cookie domain and the request origin, prompting the developer to align the cookie domain configuration with the deployment URL.
- **Session expiry miscalculation**: The `expiresIn` or `updateAge` values are set incorrectly (e.g., in milliseconds instead of seconds), causing sessions to expire within minutes instead of 7 days. The auth middleware logs session creation events with the computed `expiresAt` timestamp, and integration tests verify that a session created at time T has an `expiresAt` value equal to T plus 604800 seconds, catching the miscalculation before deployment.
- **Missing hint cookie**: The `docodego_authed` hint cookie is not set during session creation, causing Astro pages to render the unauthenticated layout on every page load before the full session validation completes. The integration test for the sign-in flow verifies that the response contains both the session cookie and the hint cookie, and returns error if the hint cookie is absent from the `Set-Cookie` headers.

## Declared Omissions

- Individual sign-in flow behavior and UI interactions (covered by behavioral specs per auth method)
- Database table definitions and migration strategy (covered by `database-schema.md`)
- Hono middleware stack ordering and error handler (covered by `api-framework.md`)
- Mobile auth client configuration with expo-secure-store (covered by mobile behavioral specs)
- Browser extension token relay pattern (covered by `extension-authenticates-via-token-relay.md`)

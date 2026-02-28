---
id: SPEC-2026-006
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: approved
roles: [Framework Adopter]
---

[← Back to Roadmap](../ROADMAP.md)

# Auth Server Config

## Intent

This spec defines the server-side authentication configuration
for the DoCodeGo boilerplate, covering Better Auth
initialization, plugin wiring, cookie strategy, session
management, and client-side auth helper setup. Better Auth is
initialized as a Hono middleware with 7 plugins: Email OTP,
Passkey, Anonymous, SSO, Organization (with teams), Admin, and
DodoPayments. This spec ensures that the auth server is
configured with the correct database adapter, cookie settings,
session parameters, and plugin options so that all
authentication flows described in the behavioral specs function
correctly across web, mobile, desktop, and browser extension
platforms.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| D1 (Cloudflare SQL) via Drizzle ORM | read/write | Every auth operation that reads or writes user, session, account, or organization data | Auth endpoints return 500 and the error handler falls back to a generic JSON error message for the client |
| `@repo/contracts` | read | App startup when Better Auth resolves shared Zod types for input validation | Build fails at compile time because auth-related contract types cannot resolve, and CI alerts to block deployment |
| Email Service | write | OTP dispatch during email-based sign-in and verification flows | The `sendVerificationOTP` callback fails and the OTP sign-in flow returns 500, logging the delivery failure to Worker logs |
| Hono Framework (`api-framework.md`) | mount | App startup when the auth handler is mounted at `/api/auth/**` on the Hono router | The Hono app cannot route auth requests and all `/api/auth/**` paths return 404 until the handler is re-registered |
| DodoPayments API | read/write | Payment-related auth events such as subscription status checks (planned, currently commented out) | No impact on current functionality because the plugin configuration is commented out and inactive until credentials are provided |

## Behavioral Flow

1. **[Client]** sends an auth request to `/api/auth/**`
    on the Hono server
2. **[Hono router]** matches the `/api/auth/**` path and
    forwards the request to the Better Auth handler
3. **[Better Auth handler]** identifies the auth method
    from the request path and payload (OTP, Passkey,
    Anonymous, SSO, or Admin action)
4. **[Better Auth handler]** validates the request input
    against plugin-specific rules (OTP length equals 6,
    passkey challenge format is valid, SSO provider is
    registered)
5. **[Better Auth handler]** queries the D1 database via
    Drizzle ORM to verify or create user and account
    records
6. **[Better Auth handler]** creates a session record in
    the database with `expiresIn` set to 604800 seconds
    and `updateAge` set to 86400 seconds
7. **[Better Auth handler]** sets the session cookie
    (httpOnly: true, sameSite: lax, path: /) and the
    `docodego_authed` hint cookie (httpOnly: false,
    value: "true") on the response
8. **[Better Auth handler]** returns the session object
    containing `userId`, `expiresAt`, and
    `activeOrganizationId` fields to the client

## State Machine

No stateful entities. Session lifecycle (creation,
refresh, expiry, revocation) is managed entirely by
Better Auth's internal state machine. This spec
configures the parameters (expiry duration, refresh
interval, cookie attributes) but does not define new
state transitions.

## Business Rules

- **Rule passwordless-only:** IF a sign-in request
    arrives THEN the auth server processes it through
    one of the 4 enabled methods (Email OTP, Passkey,
    Anonymous, SSO) AND the count of password-based
    auth plugins equals 0
- **Rule otp-length:** IF the emailOTP plugin generates
    a one-time password THEN the OTP length equals
    exactly 6 digits AND the OTP expires after exactly
    300 seconds (5 minutes)
- **Rule otp-auto-signup:** IF a user submits a valid
    OTP for an email address that has no existing
    account THEN Better Auth creates a new user account
    automatically because `disableSignUp` is set to
    false
- **Rule session-refresh:** IF an authenticated request
    arrives AND the session age exceeds 86400 seconds
    (24 hours) since last refresh THEN Better Auth
    updates the session `expiresAt` to the current time
    plus 604800 seconds (7 days)
- **Rule hint-cookie-sync:** IF a session cookie is set
    on the response THEN the `docodego_authed` hint
    cookie with value "true" is also set, AND if the
    session cookie is removed THEN the hint cookie is
    also removed

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Unauthenticated | Send OTP request, initiate passkey registration or assertion, start anonymous session, begin SSO flow | Access admin endpoints, manage organizations or teams, view session details | Cannot see any protected user or organization data |
| Authenticated | Access session data, join organizations, switch active team, manage own account | Access admin-only endpoints such as user listing or role management | Can see own user record and organizations they belong to |
| Admin | List all users, ban or unban accounts, impersonate users, manage roles | N/A (full access within admin plugin scope) | Can see all user records and all organization memberships |

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
- [ ] The session cookie sets httpOnly: true, sameSite: `"lax"`, and path: `"/"` — all 3 values are present in every environment
- [ ] In production the session cookie enables HTTPS-only transport by setting the TLS-required cookie attribute to true — this attribute is present in the cookie configuration when the environment is production
- [ ] A hint cookie named `docodego_authed` is set alongside the session cookie — it is non-httpOnly (readable by JavaScript), carries no sensitive data, and its value equals "true" when a session is active
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
- The session cookie name is controlled by Better Auth's default naming convention — the boilerplate does not override the cookie name. The hint cookie name is exactly `docodego_authed` and the count of alternative hint cookie names equals 0.
- The `preferredLocale` field on the user schema accepts only `"en"`, `"ar"`, or null — the count of other locale values permitted equals 0.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The client sends an OTP verification request with an expired OTP code that exceeded the 300-second TTL | Better Auth rejects the OTP and returns 401 with a message indicating the code has expired, without creating a session | Response status is 401 and the response body contains an expiration-related error code |
| The client sends a passkey assertion for a credential ID that does not exist in the database | Better Auth returns 401 because no matching credential record is found in the accounts table | Response status is 401 and no new session record is created in the database |
| The client sends a sign-in request with an email address containing mixed casing such as `User@Example.COM` | Better Auth normalizes the email to lowercase before lookup to prevent duplicate accounts for the same address | The database query uses the lowercased form and returns the existing user record regardless of input casing |
| Two concurrent OTP verification requests arrive for the same user within the same 300-second OTP window | Only the first request creates a session and the second request returns 401 because the OTP is consumed on first use | The second response status is 401 and the database contains exactly 1 new session record |
| The `sendVerificationOTP` callback throws an error during OTP dispatch because the email service is unreachable | Better Auth catches the callback error and returns 500 to the client, logging the failure to Worker logs without exposing internal details | Response status is 500 and Worker logs contain the email service error message |
| The client sends a session cookie that references a session ID which has been deleted from the database | Better Auth treats the request as unauthenticated because the session lookup returns no matching record | The auth middleware does not attach a session to the request context and downstream handlers see no active session |

## Failure Modes

- **Plugin initialization failure at server startup**
    - **What happens:** A Better Auth plugin is misconfigured with an incorrect option type or a missing required callback, causing the auth server to throw during initialization and preventing all auth routes from responding.
    - **Source:** Incorrect plugin configuration during development or after a Better Auth version upgrade that changes the plugin API.
    - **Consequence:** All `/api/auth/**` routes return 500 and no user can sign in, sign up, or manage their session until the plugin configuration is corrected.
    - **Recovery:** The Hono error handler falls back to a generic JSON error response with a 500 status code, and Worker logs contain the plugin name and the specific configuration error — the developer alerts on the log output and corrects the misconfigured plugin before redeploying.
- **Cookie domain mismatch between API and client origins**
    - **What happens:** The session cookie is set with a domain attribute that does not match the API server's actual deployment domain, causing the browser to silently reject the cookie on every auth response and preventing session persistence.
    - **Source:** Misconfigured environment variable or hardcoded domain value after a deployment URL change.
    - **Consequence:** Users complete the sign-in flow and receive a 200 response, but the browser discards the session cookie and all subsequent requests arrive without authentication, creating an infinite sign-in loop.
    - **Recovery:** The auth middleware logs a warning that includes the cookie domain and the request origin when it detects that no session cookie is present on a request from a recently-authenticated user — the developer alerts on the log output and corrects the domain configuration to match the deployment URL.
- **Session expiry miscalculation using milliseconds instead of seconds**
    - **What happens:** The `expiresIn` or `updateAge` values are set in milliseconds instead of seconds, causing sessions to expire in approximately 7 milliseconds instead of 7 days and forcing users to re-authenticate on every request.
    - **Source:** Developer confusion between the millisecond convention used by some libraries and the seconds convention used by Better Auth's session configuration.
    - **Consequence:** Every authenticated user loses their session within milliseconds, rendering the application unusable for any action that requires authentication.
    - **Recovery:** The integration test verifies that a session created at time T has an `expiresAt` value equal to T plus 604800 seconds — CI alerts and blocks deployment if the computed expiry falls outside the expected 7-day window.
- **Missing hint cookie on session creation response**
    - **What happens:** The `docodego_authed` hint cookie is not set during session creation, causing Astro pages to render the unauthenticated layout on every initial page load before the full session validation completes via the API.
    - **Source:** The hint cookie logic is omitted from the session creation hook or the cookie name is misspelled in the configuration.
    - **Consequence:** Authenticated users see a flash of unauthenticated content on every page navigation, degrading the perceived performance and user experience.
    - **Recovery:** The integration test for the sign-in flow verifies that the response `Set-Cookie` headers contain both the session cookie and the `docodego_authed` hint cookie — CI alerts and blocks deployment if the hint cookie is absent from the response headers.
- **Email service unavailable during OTP dispatch**
    - **What happens:** The `sendVerificationOTP` callback fails because the configured email service is unreachable or returns an error, preventing the OTP code from being delivered to the user's inbox.
    - **Source:** Email service outage, misconfigured API credentials, or network connectivity failure between the Cloudflare Worker and the email provider.
    - **Consequence:** Users who attempt OTP-based sign-in never receive the verification code and cannot complete authentication through the email OTP method.
    - **Recovery:** The callback logs the delivery failure to Worker logs and the auth handler returns 500 to the client with a generic error message — the system degrades to offering alternative sign-in methods (Passkey, SSO, Anonymous) while the email service issue is resolved.

## Declared Omissions

- Individual sign-in flow behavior, UI interactions, and step-by-step user journeys are not covered here and are defined in behavioral specs per auth method
- Database table definitions, column types, migration strategy, and Drizzle ORM schema configuration are not covered here and are defined in `database-schema.md`
- Hono middleware stack ordering, CORS policy, error handler logic, and request pipeline configuration are not covered here and are defined in `api-framework.md`
- Mobile auth client configuration with Expo encrypted storage for token persistence on native platforms is not covered here and is defined in mobile behavioral specs
- Browser extension token relay pattern for cross-context authentication between popup and content scripts is not covered here and is defined in `extension-authenticates-via-token-relay.md`
- OAuth provider registration, SSO callback URL configuration, and identity provider metadata setup are not covered here and are defined in SSO-specific behavioral specs
- Rate limiting and brute-force protection for OTP verification attempts are not covered here and are defined in the security hardening specification

## Related Specifications

- [api-framework](api-framework.md) — Hono middleware stack, error handler, and CORS configuration that mounts and routes the Better Auth handler
- [database-schema](database-schema.md) — Drizzle ORM table definitions for user, session, account, organization, and team tables consumed by Better Auth
- [shared-contracts](shared-contracts.md) — oRPC contract definitions and Zod schemas that provide shared type-safe validation for auth-related API inputs
- [shared-i18n](shared-i18n.md) — Internationalization infrastructure providing locale resolution used by the `preferredLocale` user field
- [ci-cd-pipelines](ci-cd-pipelines.md) — CI/CD deployment workflow and GitHub Actions pipelines that run integration tests validating auth configuration before deployment

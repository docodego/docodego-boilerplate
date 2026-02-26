---
id: SPEC-2026-017
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Signs In with SSO

## Intent

This spec defines the single sign-on (SSO) authentication flow for the DoCodeGo boilerplate, supporting both OIDC and SAML protocols. An enterprise user navigates to `/signin`, enters their work email or selects their identity provider, and is redirected to the external IdP for authentication. After successful authentication at the IdP, the callback returns to DoCodeGo where the server validates the response, resolves or creates the user account, provisions organization membership if the SSO provider is linked to an organization, creates a session, and redirects to `/app`. On the desktop app (Tauri), the IdP page opens in the system browser via `tauri-plugin-opener` and the callback returns through the `docodego://` deep link scheme. This spec ensures the SSO flow works across both OIDC and SAML protocols, handles user provisioning and org membership correctly, and supports the desktop two-app handoff pattern.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| External IdP (OIDC) | read | SSO initiation and callback for OIDC providers | Server returns HTTP 502 to the client and logs the connection error with the IdP URL and failure reason for the administrator to investigate |
| External IdP (SAML) | read | SSO initiation and callback for SAML providers | Server returns HTTP 502 to the client and logs the SAML endpoint failure with provider ID and timestamp for administrator investigation |
| D1 (Cloudflare SQL) | read/write | User lookup, user creation, membership provisioning, session creation | Route handler returns HTTP 500 and the global error handler falls back to a generic JSON error message for the client |
| Better Auth | read/write | Session creation and cookie management after successful IdP callback | Auth session creation returns HTTP 500 and the error handler degrades to a generic authentication error message |
| `@repo/contracts` | read | App startup (schema registration for SSO endpoints) | Build fails at compile time because the oRPC router cannot resolve contract types and CI alerts to block deployment |
| `@repo/i18n` | read | Each request (locale middleware for SSO UI strings) | Translation function falls back to the default English locale strings so SSO-related messages remain readable but untranslated |

## Behavioral Flow

1. **[User]** → navigates to `/signin` and enters work email or selects an identity provider from the configured SSO provider list
2. **[Client]** → calls `authClient.signIn.sso()` with the provider information (email domain or provider ID) to initiate the SSO flow
3. **[Server]** → queries the `ssoProvider` table to find a matching provider by email domain or provider ID — if no match is found, returns HTTP 404 with a localized error message
4. **[Server]** → determines the protocol type from the matched provider record:
   - **OIDC path:** fetches the `.well-known/openid-configuration` discovery endpoint from the IdP with a 10-second timeout, constructs the authorization URL with redirect URI `/api/auth/sso/callback/{providerId}`
   - **SAML path:** constructs a SAML authentication request and generates the redirect URL to the IdP's single sign-on endpoint with callback at `/api/auth/saml2/callback/{providerId}`
5. **[Server]** → redirects the user's browser to the external IdP URL via HTTP redirect with a `Location` header containing the constructed URL
6. **[User]** → authenticates at the external IdP (credentials, MFA, and other prompts are controlled entirely by the IdP)
7. **[IdP]** → redirects back to the DoCodeGo callback URL with the authentication response:
   - **OIDC callback:** the IdP redirects to `/api/auth/sso/callback/{providerId}` with an authorization code parameter that the server will exchange for tokens
   - **SAML callback:** the IdP posts a SAML response containing signed assertions to `/api/auth/saml2/callback/{providerId}` for server-side validation
8. **[Server]** → validates the IdP response:
   - **OIDC:** exchanges authorization code for tokens, validates ID token signature, and extracts user claims (email, name)
   - **SAML:** validates the XML signature on the response, checks assertion timestamps against `NotOnOrAfter` to prevent replay, and extracts user identity attributes
9. **[Server]** → extracts the user's email from the IdP response and queries the `user` table:
   - If a user with the extracted email exists, the server uses that existing user record
   - If no user exists, the server creates a new `user` record with the extracted email and profile data
10. **[Server]** → checks the `organizationId` field on the matched `ssoProvider` record:
    - If `organizationId` is non-null, the server checks for existing membership and creates a `member` record linking the user to that organization if one does not already exist
11. **[Server]** → creates a session record in the `session` table with `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days from the current timestamp
12. **[Server]** → sets the session cookie and the `docodego_authed` hint cookie in the response headers
13. **[Client]** → receives the response and redirects to `/app` to complete the sign-in flow

**Desktop handoff (Tauri):**

14. **[Desktop App]** → opens the IdP sign-in page in the system browser via `tauri-plugin-opener` instead of loading it inside the Tauri webview
15. **[System Browser]** → user authenticates at the IdP, and the IdP redirects to `docodego://auth/callback` instead of an HTTP callback URL
16. **[Desktop App]** → receives the deep link callback and completes authentication using the callback parameters — if the deep link fails to route, the system browser displays the callback URL and the desktop app presents a manual input dialog for the user to paste the URL

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | provider_lookup | User submits email or selects IdP on the `/signin` page | Email or provider ID is non-empty |
| provider_lookup | idp_redirect | Server finds matching SSO provider in `ssoProvider` table | Provider record exists with valid `oidcConfig` or `samlConfig` |
| provider_lookup | error | Server finds no matching provider for the given email domain | No provider record matches the email domain or provider ID |
| idp_redirect | awaiting_callback | Browser is redirected to external IdP URL for authentication | IdP URL is constructed and redirect response is sent |
| awaiting_callback | validating_response | IdP redirects back to DoCodeGo callback URL with auth response | Callback URL receives authorization code (OIDC) or assertion (SAML) |
| validating_response | user_resolution | Server validates IdP response (token signature or XML signature) | Validation passes with no signature or timestamp errors |
| validating_response | error | Server detects invalid signature, expired assertion, or malformed response | Validation fails due to cryptographic or temporal check |
| user_resolution | session_created | Server resolves or creates user, provisions org membership, creates session | User record and session record are both persisted to D1 |
| session_created | authenticated | Server sets session cookie and hint cookie, client redirects to `/app` | Both cookies are present in response headers |
| error | idle | User is shown error message and can retry the SSO sign-in flow | Error response is delivered to the client |

## Business Rules

- **Rule SSO-protocol-routing:** IF the matched `ssoProvider` record contains a non-null `oidcConfig` THEN the server initiates the OIDC flow with discovery endpoint fetch and authorization URL construction; IF the record contains a non-null `samlConfig` instead THEN the server initiates the SAML flow with authentication request construction
- **Rule user-dedup:** IF a user with the extracted email already exists in the `user` table THEN the server uses the existing record and does not create a duplicate; IF no user exists THEN the server creates a new `user` record
- **Rule org-membership-provision:** IF the matched `ssoProvider` record has a non-null `organizationId` AND the user is not already a member of that organization THEN the server creates a new `member` record linking the user to the organization; IF the user is already a member THEN no duplicate record is created
- **Rule desktop-browser-handoff:** IF the client platform is the Tauri desktop app THEN the IdP page opens in the system browser via `tauri-plugin-opener` and the callback uses the `docodego://auth/callback` deep link scheme instead of an HTTP URL
- **Rule session-expiry:** IF authentication succeeds THEN the server creates a session with `expiresAt` set to exactly 7 days (168 hours) from the current timestamp

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Unauthenticated | Initiate SSO sign-in from `/signin`, submit email for provider lookup, authenticate at external IdP | Access any authenticated route or view `/app` dashboard content | Cannot see organization data or member lists until authenticated |
| Authenticated (post-SSO) | Access `/app` and all authenticated routes, view org dashboard if membership was provisioned | Re-initiate SSO while an active session exists (redirected to `/app` instead) | Sees only organizations and resources associated with their `member` records |

## Constraints

- The SSO flow supports exactly 2 protocols: OIDC and SAML — the `ssoProvider` table stores either an `oidcConfig` or a `samlConfig` for each provider, and the server routes the flow based on which config is present. The count of supported SSO protocol types equals 2.
- The SSO callback URL is protocol-specific and deterministic — OIDC callbacks arrive at `/api/auth/sso/callback/{providerId}` and SAML callbacks arrive at `/api/auth/saml2/callback/{providerId}`. The `{providerId}` segment matches the provider's ID in the `ssoProvider` table, and the count of wildcard or catch-all callback routes equals 0.
- On the desktop app, the IdP page opens in the system browser, not in the Tauri webview — the webview has no address bar or navigation controls, making it unsuitable for external IdP pages. The count of in-webview IdP page loads in the desktop SSO flow equals 0.
- Organization auto-provisioning via SSO is non-destructive — if the user is already a member of the organization linked to the SSO provider, no duplicate `member` record is created. The server checks for existing membership before inserting, and the count of duplicate member records for the same user-org pair equals 0.

## Acceptance Criteria

- [ ] The `/signin` page displays an SSO option that accepts the user's work email or presents a list of configured identity providers — at least 1 SSO-related input or selection element is present
- [ ] The client calls `authClient.signIn.sso()` with the provider information when the user initiates SSO — the method invocation is present in the sign-in handler
- [ ] The server looks up the matching provider in the `ssoProvider` table using the provided email domain or provider ID — the database query is present and filters by the provider identifier
- [ ] For OIDC providers, the server fetches the `.well-known/openid-configuration` endpoint from the IdP and constructs the authorization URL — the discovery fetch and URL construction are both present
- [ ] For SAML providers, the server constructs a SAML authentication request and generates the redirect URL to the IdP's single sign-on endpoint — the SAML request construction is present in the handler
- [ ] The server redirects the user's browser to the external IdP URL — the HTTP redirect response is present with a `Location` header containing a non-empty URL
- [ ] For OIDC callbacks at `/api/auth/sso/callback/{providerId}`, the server exchanges the authorization code for tokens, validates the ID token signature, and extracts claims — all 3 steps are present
- [ ] For SAML callbacks at `/api/auth/saml2/callback/{providerId}`, the server validates the XML signature and checks assertion timestamps — both validation steps are present
- [ ] The server extracts the user's email from the IdP response — the email field is present, non-empty, and stored as a string
- [ ] If a user with the extracted email already exists in the `user` table, the server uses that existing record — the count of duplicate user records for the same email equals 0
- [ ] If no user with the extracted email exists, the server creates a new `user` record — the new row is present in the `user` table after the call completes
- [ ] If the SSO provider has a non-null `organizationId` in the `ssoProvider` table, the user is automatically added as a member of that organization — the `member` record is present with the correct `organizationId` and `userId`
- [ ] On successful authentication, the server creates a session record in the `session` table with `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days — all 4 fields are present and non-empty
- [ ] On successful authentication, the server sets the session cookie and the `docodego_authed` hint cookie — both cookies are present in the response headers
- [ ] After successful sign-in, the client redirects to `/app` — the window location pathname equals the string `/app` after navigation completes
- [ ] On the desktop app (Tauri), the IdP sign-in page opens in the system browser via `tauri-plugin-opener` instead of inside the webview — the opener plugin invocation is present in the desktop SSO handler
- [ ] On the desktop app, the IdP callback redirects to `docodego://auth/callback` instead of an HTTP URL — the deep link scheme is present in the callback configuration for desktop targets
- [ ] All UI text related to the SSO flow is rendered via i18n translation keys — the count of hardcoded English strings in the SSO UI components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user enters an email domain that matches multiple SSO providers configured in the `ssoProvider` table | The server selects the first matching provider by insertion order and proceeds with that single provider, returning no ambiguity error | Response contains a redirect to a single IdP URL and the HTTP status is 302 |
| The IdP returns a valid OIDC token with an email that differs from the email the user originally entered on the `/signin` page | The server uses the email from the IdP token as the authoritative email for user resolution, ignoring the originally entered email | The `user` record email matches the IdP-provided email, not the originally entered email |
| The OIDC discovery endpoint returns a valid JSON response but is missing the `authorization_endpoint` field required for URL construction | The server rejects the discovery response and returns HTTP 502 with a diagnostic error code indicating the IdP configuration is incomplete | Response status is 502 and the response body contains a `code` field indicating a discovery configuration error |
| The user authenticates at the IdP and the callback arrives, but the `ssoProvider` record was deleted between redirect and callback arrival | The server returns HTTP 404 because the provider lookup by `providerId` finds no matching record in the `ssoProvider` table | Response status is 404 and the response body contains both `code` and `message` fields |
| The SSO provider has a non-null `organizationId` but the referenced organization record does not exist in the `organization` table | The server logs a warning about the orphaned `organizationId` reference and completes authentication without creating a membership record, ensuring the user is not blocked | The user receives a valid session and is redirected to `/app` despite the missing organization |
| The IdP SAML response contains an assertion with `NotOnOrAfter` set to exactly the current server timestamp (boundary condition) | The server treats the exact-match timestamp as expired and rejects the assertion, returning HTTP 400 with a diagnostic code | Response status is 400 and the response body contains a code indicating an expired assertion |

## Failure Modes

- **IdP discovery endpoint unreachable**
    - **What happens:** The server cannot fetch the OIDC `.well-known/openid-configuration` endpoint from the IdP due to a network timeout or DNS failure, blocking the authorization URL construction entirely.
    - **Source:** Network connectivity failure or DNS resolution error between the Cloudflare Worker and the external identity provider discovery endpoint.
    - **Consequence:** The user cannot initiate the OIDC SSO flow and is blocked from signing in via their configured identity provider.
    - **Recovery:** The server applies a timeout of 10 seconds on the discovery fetch, returns HTTP 502 to the client, and logs the connection error with the IdP URL and failure reason — the client falls back to displaying a localized error message suggesting the user retry or contact their administrator.

- **SAML assertion timestamp expired**
    - **What happens:** The SAML response contains an assertion whose `NotOnOrAfter` timestamp is in the past, indicating a stale or replayed response that cannot be trusted for authentication.
    - **Source:** Clock skew between the IdP and the DoCodeGo server, or a replayed SAML response from a previous authentication attempt.
    - **Consequence:** The user cannot complete SAML-based SSO sign-in because the server correctly rejects the untrusted assertion.
    - **Recovery:** The server rejects the assertion and returns HTTP 400 with a diagnostic code, logs a warning with the assertion ID and the expired timestamp value — the client falls back to displaying a localized error message prompting the user to retry the SSO sign-in from the beginning.

- **SSO provider not found for email domain**
    - **What happens:** The user enters an email address whose domain does not match any configured SSO provider in the `ssoProvider` table, and the server cannot route the SSO flow to an identity provider.
    - **Source:** Unconfigured email domain because the organization administrator has not yet set up SSO for that domain in the system.
    - **Consequence:** The user cannot sign in via SSO and is blocked from accessing their organization's workspace through this authentication method.
    - **Recovery:** The server returns HTTP 404, and the client degrades gracefully by displaying a localized message notifying the user to try email OTP sign-in or contact their organization administrator to configure SSO for their domain.

- **Desktop deep link callback not received**
    - **What happens:** After authenticating at the IdP in the system browser, the `docodego://auth/callback` deep link fails to route back to the Tauri app because the custom URL scheme is not registered or another application intercepts the link.
    - **Source:** Missing or overridden custom URL scheme registration on the user's operating system, or a conflicting application handling the `docodego://` protocol.
    - **Consequence:** The desktop app never receives the authentication callback and the user remains in an unauthenticated state with the system browser showing the deep link URL.
    - **Recovery:** The system browser displays the deep link URL as a fallback, and the desktop app degrades to showing a localized manual input dialog where the user can paste the callback URL to complete authentication — the dialog logs the paste attempt for diagnostics.

- **D1 database failure during user provisioning**
    - **What happens:** The D1 database returns a connection error or timeout during user lookup, user creation, or organization membership provisioning after the IdP callback has been validated.
    - **Source:** Cloudflare D1 service degradation, exceeded rate limits, or transient infrastructure failure in the database binding.
    - **Consequence:** The user successfully authenticated at the IdP but the server cannot persist the user record or session, resulting in a failed sign-in despite valid IdP credentials.
    - **Recovery:** The global error handler falls back to returning HTTP 500 with a generic JSON error message, and the client displays a localized retry message — the user can retry the SSO flow because the IdP session remains valid and the callback will re-trigger user provisioning on the next attempt.

## Declared Omissions

- SSO provider configuration and management by organization administrators is not covered here and is defined in the `org-admin-configures-sso-provider.md` specification
- Deep link handling, URL scheme registration, and platform-specific routing logic is not covered here and is defined in `user-opens-a-deep-link.md` and `mobile-handles-deep-link.md`
- Multi-factor authentication prompts during IdP authentication are controlled entirely by the external identity provider and are not managed by the DoCodeGo application
- Mobile-specific SSO sign-in behavior using in-app browser or platform authentication APIs is not covered here and is defined in `user-signs-in-on-mobile.md`
- SSO provider certificate rotation, SAML metadata refresh, and OIDC key rotation are operational concerns not covered by this authentication flow specification

## Related Specifications

- [org-admin-configures-sso-provider](org-admin-configures-sso-provider.md) — Defines how organization administrators create, update, and delete SSO provider configurations in the `ssoProvider` table
- [user-opens-a-deep-link](user-opens-a-deep-link.md) — Defines the deep link routing and URL scheme handling that the desktop SSO callback depends on for the Tauri handoff
- [user-signs-in-on-mobile](user-signs-in-on-mobile.md) — Defines mobile-specific SSO behavior using platform authentication APIs, complementing the web and desktop flows in this spec
- [auth-server-config](../foundation/auth-server-config.md) — Defines Better Auth plugin configuration, session strategy, and provider setup that the SSO flow relies on for session creation
- [database-schema](../foundation/database-schema.md) — Defines the `user`, `session`, `ssoProvider`, `member`, and `organization` table schemas used throughout this SSO flow

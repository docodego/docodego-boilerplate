[← Back to Roadmap](../ROADMAP.md)

# User Signs In with SSO

## Intent

This spec defines the single sign-on (SSO) authentication flow for the DoCodeGo boilerplate, supporting both OIDC and SAML protocols. An enterprise user navigates to `/signin`, enters their work email or selects their identity provider, and is redirected to the external IdP for authentication. After successful authentication at the IdP, the callback returns to DoCodeGo where the server validates the response, resolves or creates the user account, provisions organization membership if the SSO provider is linked to an organization, creates a session, and redirects to `/app`. On the desktop app (Tauri), the IdP page opens in the system browser via `tauri-plugin-opener` and the callback returns through the `docodego://` deep link scheme. This spec ensures the SSO flow works across both OIDC and SAML protocols, handles user provisioning and org membership correctly, and supports the desktop two-app handoff pattern.

## Acceptance Criteria

- [ ] The `/signin` page displays an SSO option that accepts the user's work email or shows a list of configured identity providers — at least 1 SSO-related input or selection element is present
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

## Constraints

- The SSO flow supports exactly 2 protocols: OIDC and SAML — the `ssoProvider` table stores either an `oidcConfig` or a `samlConfig` for each provider, and the server routes the flow based on which config is present. The count of supported SSO protocol types equals 2.
- The SSO callback URL is protocol-specific and deterministic — OIDC callbacks arrive at `/api/auth/sso/callback/{providerId}` and SAML callbacks arrive at `/api/auth/saml2/callback/{providerId}`. The `{providerId}` segment matches the provider's ID in the `ssoProvider` table, and the count of wildcard or catch-all callback routes equals 0.
- On the desktop app, the IdP page must open in the system browser, not in the Tauri webview — the webview has no address bar or navigation controls, making it inappropriate for external IdP pages. The count of in-webview IdP page loads in the desktop SSO flow equals 0.
- Organization auto-provisioning via SSO is non-destructive — if the user is already a member of the organization linked to the SSO provider, no duplicate `member` record is created. The server checks for existing membership before inserting, and the count of duplicate member records for the same user-org pair equals 0.

## Failure Modes

- **IdP discovery endpoint unreachable**: The server cannot fetch the OIDC `.well-known/openid-configuration` endpoint from the IdP due to a network timeout or DNS failure, blocking the authorization URL construction. The server applies a timeout of 10 seconds on the discovery fetch, and if it fails, returns error HTTP 502 to the client and logs the connection error with the IdP URL and failure reason for the administrator to investigate.
- **SAML assertion timestamp expired**: The SAML response contains an assertion whose `NotOnOrAfter` timestamp is in the past, indicating a stale or replayed response that cannot be trusted. The server rejects the assertion and returns error HTTP 400 with a diagnostic code, and logs a warning with the assertion ID and the expired timestamp value, preventing authentication with outdated SAML responses.
- **SSO provider not found for email domain**: The user enters an email address whose domain does not match any configured SSO provider in the `ssoProvider` table, and the server cannot route the SSO flow to an identity provider. The server returns error HTTP 404, and the client displays a localized message notifying the user to try email OTP sign-in or contact their organization administrator to configure SSO for their domain.
- **Desktop deep link callback not received**: After authenticating at the IdP in the system browser, the `docodego://auth/callback` deep link fails to route back to the Tauri app because the scheme is not registered or another application intercepts the link. The system browser displays the deep link URL as a fallback, and the desktop app shows a localized manual input dialog where the user can paste the callback URL to complete authentication, with the dialog logging the paste attempt for diagnostics.

## Declared Omissions

- SSO provider configuration by org admins (covered by `org-admin-configures-sso-provider.md`)
- Deep link handling and routing (covered by `user-opens-a-deep-link.md` and `mobile-handles-deep-link.md`)
- IdP multi-factor authentication prompts (controlled by the external IdP, not by DoCodeGo)
- Mobile SSO sign-in behavior (covered by `user-signs-in-on-mobile.md`)

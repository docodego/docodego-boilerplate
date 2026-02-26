# Authentication Flows

---

## Email OTP Sign-In

The user navigates to `/signin`. The page renders a clean form with a single email input field and a "Send code" button. There are also secondary options visible: a "Sign in with passkey" button, an SSO link for enterprise users, and a "Continue as guest" option at the bottom.

The user types their email address and clicks "Send code." The client calls `authClient.emailOtp.sendVerificationOtp({ email, type: "sign-in" })`. The button transitions to a loading state while the request is in flight. On the server side, Better Auth generates a 6-digit OTP, stores it in the `verification` table, and fires the `sendVerificationOTP` callback. In development, the OTP is logged to the console. In production, the system sends it via the configured email service. The server does not reveal whether the email address belongs to an existing account — it always responds with success to prevent enumeration.

Once the server responds, the UI transitions from the email input step to the OTP entry step. The email address is displayed at the top so the user knows where the code was sent, along with a "change email" link that takes them back to the first step. Six individual digit inputs appear, auto-focusing the first one. As the user types each digit, focus advances to the next input automatically.

After the user enters all six digits, the client calls `authClient.signIn.emailOtp({ email, otp })`. If the OTP is correct and not expired (5-minute window), the server creates a session. The session record includes the user's `ipAddress` and `userAgent`. The server also sets the `docodego_authed` hint cookie — a simple flag that Astro SSG pages read to know the user is authenticated, preventing a flash of unauthenticated content on static pages. The client then redirects to `/app`.

If the user does not exist yet, Better Auth auto-creates a new user account during the sign-in call (since `disableSignUp` is false). The new user record gets the email, `emailVerified` set to true, and a generated name. The system then proceeds with session creation and redirect exactly the same as for an existing user.

If the OTP is wrong, the server returns an error. The UI displays an inline error message below the OTP inputs. The user can clear the inputs and try again. After 3 failed attempts, the OTP is invalidated — the user needs to go back to the email step and request a fresh code. If the OTP has expired (more than 5 minutes old), the error message tells the user the code has expired and prompts them to request a new one.

---

## Passkey / WebAuthn Sign-In

From the `/signin` page, the user clicks "Sign in with passkey." The client calls `authClient.signIn.passkey()`, which kicks off the WebAuthn authentication ceremony. The browser shows its native biometric or PIN prompt — Touch ID on Mac, Windows Hello on Windows, fingerprint or face recognition on mobile. The user completes the biometric verification.

Behind the scenes, the browser sends the signed challenge back to the server. The server looks up the credential in the `passkey` table by `credentialID`, verifies the signature against the stored `publicKey`, checks and increments the `counter` to prevent replay attacks, and validates the `deviceType`. If everything checks out, the server creates a session with `ipAddress` and `userAgent`, sets the `docodego_authed` hint cookie, and responds with success. The client redirects to `/app`.

If the user cancels the browser's biometric prompt, the WebAuthn ceremony aborts and the client stays on the sign-in page with no error — the user simply didn't complete the action. If the credential is not recognized (e.g., the user is on a new device without synced passkeys), the browser prompt fails to find matching credentials and the ceremony errors out. The UI shows a message suggesting the user try a different sign-in method.

Passkey registration happens separately, from within the app after the user is already authenticated. In the security settings page, the user clicks "Add passkey." The client calls `authClient.passkey.addPasskey()`, which triggers the browser's WebAuthn registration ceremony. The user completes the biometric prompt, and the browser generates a new credential pair. The server stores the public key, credential ID, counter, device type, backup status, and transports in the `passkey` table. The user can optionally name the passkey (e.g., "MacBook Pro Touch ID") for easy identification later.

The security settings page also lists all registered passkeys via `authClient.passkey.listUserPasskeys()`, showing each passkey's name, device type, and creation date. Users can rename passkeys with `authClient.passkey.updatePasskey()` or delete them with `authClient.passkey.deletePasskey()`.

---

## Anonymous Guest Session

When a visitor wants to explore the app without creating an account, they click "Continue as guest" on the sign-in page. The client calls `authClient.signIn.anonymous()`.

The server creates a new user record with `isAnonymous` set to `true`. The email is auto-generated in the format `anon-{uuid}@anon.docodego.com` (configured via the `emailDomainName` option). A display name is generated as well. A full session is created with `ipAddress` and `userAgent`, and the `docodego_authed` hint cookie is set. The client redirects to `/app`.

The anonymous user can browse the app and interact with features as a guest. They see a persistent banner or prompt encouraging them to create a full account to save their work.

When the guest decides to upgrade, they initiate the account-linking flow. They enter their real email address and go through the standard email OTP verification. The client calls the sign-in flow with the real email. Better Auth's `onLinkAccount` callback fires with `{ anonymousUser, newUser }` — this is where the system migrates any data the guest created (preferences, drafts, etc.) from the anonymous user record to the new account. The anonymous user record is then deleted automatically. The user continues with a full account, all their guest activity preserved.

---

## SSO (SAML / OIDC) Sign-In

Enterprise users see an SSO option on the `/signin` page. They click it and are prompted to enter their work email address or select their organization's identity provider from a list.

The client calls `authClient.signIn.sso()` with the appropriate provider information. The server looks up the SSO provider configuration in the `ssoProvider` table, which stores the `issuer`, `domain`, and either `oidcConfig` or `samlConfig` depending on the provider type. The `organizationId` field links the provider to a specific organization.

For OIDC providers, the server constructs the authorization URL using the provider's configuration (discovered automatically from the issuer's `.well-known/openid-configuration` endpoint). The client redirects the user's browser to the external identity provider — Okta, Azure AD, Google Workspace, or whatever the org has configured. The user authenticates there using their corporate credentials (potentially including their own MFA).

After successful authentication at the IdP, the browser redirects back to the app's callback URL. For OIDC, this hits the `/api/auth/sso/callback/{providerId}` endpoint. The server exchanges the authorization code for tokens, validates the ID token, and extracts user information based on the field mapping configured in `oidcConfig.mapping`.

For SAML providers, the flow is similar but uses SAML assertions instead of OAuth tokens. The IdP posts a SAML response to `/api/auth/sso/saml2/callback/{providerId}`. The server validates the XML signature against the stored certificate, checks timestamps and audience restrictions, and extracts user attributes from the assertion.

In both cases, the server then either finds an existing user by email or creates a new one. If the SSO provider is linked to an organization (via `organizationId`), the user is automatically provisioned as a member of that organization with the default role. A session is created with `ipAddress` and `userAgent`, the `docodego_authed` cookie is set, and the user arrives back in the app authenticated. The client redirects to `/app`.

SSO provider configuration is managed by organization admins through the organization settings. An admin registers a new provider by supplying the issuer URL (for OIDC) or the IdP metadata (for SAML), along with the required credentials and certificates. The provider is stored in the `ssoProvider` table tied to the organization.

---

## Session Behavior

All authentication methods create sessions the same way. Each session record in the database includes:

- A unique session `token` that is set as a signed cookie on the client
- The `userId` linking back to the authenticated user
- `ipAddress` and `userAgent` captured from the request for security auditing
- `expiresAt` set to 7 days from creation by default
- `activeOrganizationId` tracking which organization the user is currently working in
- `activeTeamId` tracking which team context is active within that organization

Sessions refresh automatically. When a session is accessed and it is older than 24 hours (the `updateAge`), the server extends its expiration by another 7 days. This means active users never get logged out unexpectedly, while abandoned sessions expire naturally.

The `docodego_authed` cookie is a lightweight hint cookie separate from the actual session token. It does not contain any sensitive data — it simply tells Astro's statically-generated pages that the user has an active session. This prevents the flash of unauthenticated content (FOUC) that would otherwise happen when a static page loads before the client-side auth check completes. The actual session validation always happens server-side when the SPA portion loads.

Users can view and manage their active sessions from the security settings page. `authClient.listSessions()` shows all active sessions across devices, displaying the IP address, user agent (parsed into browser and OS), and creation time. Users can revoke individual sessions with `authClient.revokeSession(token)` or terminate all other sessions with `authClient.revokeOtherSessions()`.

---

## i18n and RTL Considerations

The entire sign-in flow supports internationalization. All UI text — labels, button text, error messages, placeholders — is translated through i18next using the `auth` namespace. The app ships with English (en) and Arabic (ar) translations.

When the app loads, the locale is detected from the `Accept-Language` header on the server side and from browser preferences on the client side. If the detected locale is Arabic (or any RTL language like Hebrew, Farsi, or Urdu), the layout flips to right-to-left. The email input, OTP fields, buttons, and error messages all respect logical properties (start/end instead of left/right) via Tailwind's logical property utilities, so the layout adapts naturally without any special RTL-specific code.

The OTP email sent to the user is also localized — the subject line and body text use the detected locale from the request's `Accept-Language` header, pulling translations from the `email` i18n namespace.

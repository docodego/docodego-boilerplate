---
id: SPEC-2026-015
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Signs In with Passkey

## Intent

This spec defines the passkey (WebAuthn) sign-in flow for the DoCodeGo boilerplate. The user clicks a "Sign in with passkey" button on the `/signin` page, which triggers the browser's native WebAuthn authentication ceremony. The browser presents a biometric or PIN prompt (Touch ID on macOS, Windows Hello on Windows, or the platform equivalent), and upon successful authentication, the signed credential response is sent to the server. The server verifies the credential against the stored public key in the `passkey` table, checks the counter value to prevent replay attacks, creates a session, and redirects the user to `/app`. On Linux (WebKitGTK) where WebAuthn is not available, the passkey button is hidden and the user relies on alternative sign-in methods. This spec ensures the passkey flow is functional on supported platforms, gracefully degraded on unsupported platforms, and resistant to credential replay attacks.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth (server) | read/write | Every passkey sign-in attempt via `authClient.signIn.passkey()` | The server returns HTTP 500 and the client displays a localized error message prompting the user to retry or use email OTP sign-in instead |
| `passkey` table (D1) | read/write | Credential lookup and counter update during server-side verification | The database query fails and the server returns HTTP 500 with a generic error while non-passkey sign-in routes remain unaffected |
| `session` table (D1) | write | Session creation after successful passkey verification completes | Session creation fails and the server returns HTTP 500 despite valid credentials, requiring the user to retry the sign-in attempt |
| WebAuthn API (`navigator.credentials`) | read | Client-side call to `navigator.credentials.get()` during the authentication ceremony | The passkey button is not rendered on the page and the user falls back to email OTP or SSO sign-in methods with 0 broken UI elements |
| `@repo/i18n` | read | Rendering all UI text, error messages, and button labels in the passkey flow | Translation function falls back to the default English locale strings so the passkey UI remains functional but untranslated for non-English users |

## Behavioral Flow

1. **[User]** → arrives at the `/signin` page and sees a translated "Sign in with passkey" button alongside other authentication options such as email OTP and SSO
2. **[Client]** → checks whether the `navigator.credentials` API is present and available at runtime before rendering the passkey button on the page
3. **[Client]** → if the API is present, renders the "Sign in with passkey" button as visible and enabled; if the API is absent (such as on Linux WebKitGTK in Tauri), hides the button entirely and the user must use email OTP or SSO instead
4. **[User]** → clicks the "Sign in with passkey" button, and the client calls `authClient.signIn.passkey()` which initiates the WebAuthn authentication ceremony
5. **[Browser]** → immediately presents its native biometric or PIN prompt — Touch ID on macOS, Windows Hello on Windows, or the platform-specific equivalent on other systems
6. **[User]** → authenticates using their biometric (fingerprint, face) or device PIN to complete the ceremony, or dismisses the prompt by clicking Cancel or pressing Escape
7. **[Client]** → if the user dismisses the browser biometric prompt, no request is sent to the server and the user remains on `/signin` with no error shown, free to retry or choose a different sign-in method
8. **[Browser → Server]** → if the user completes authentication, the browser sends the signed authentication response containing the credential assertion to the server for verification
9. **[Server]** → looks up the credential by `credentialID` in the `passkey` table and retrieves the stored `publicKey` associated with that credential entry
10. **[Server]** → verifies the signature on the authenticator response using the stored public key, confirming the user possesses the private key associated with the registered passkey
11. **[Server]** → checks and increments the `counter` value to prevent replay attacks — if the counter in the response is not strictly greater than the stored counter, the authentication is rejected
12. **[Server]** → creates a session in the `session` table with the standard fields: signed token cookie, `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days out
13. **[Server]** → sets the `docodego_authed` hint cookie alongside the session cookie so that Astro pages can detect authenticated state client-side without a server round-trip
14. **[Client]** → receives the successful response and redirects the user to `/app` by updating the window location to the application dashboard route
15. **[Server]** → if the browser sends a credential that the server cannot match to any entry in the `passkey` table, the server returns an error and the UI displays a localized message suggesting the user try another sign-in method such as email OTP
16. **[Client — Desktop]** → on the desktop app (Tauri), macOS WKWebView and Windows WebView2 support WebAuthn so the biometric or PIN prompt appears as expected, but on Linux WebKitGTK WebAuthn support is limited and is not reliably available

## State Machine

No stateful entities within this spec's scope. The passkey sign-in is a stateless request-response authentication ceremony where the credential counter is an anti-replay mechanism, not a lifecycle state tracked by the application.

## Business Rules

- **Rule counter-check:** IF the `counter` value in the authentication response is less than or equal to the stored `counter` in the `passkey` table THEN the server rejects the authentication attempt and returns HTTP 400 with a diagnostic error code indicating a potential replay attack
- **Rule credential-match:** IF the `credentialID` from the authentication response does not match any entry in the `passkey` table THEN the server rejects the request and returns HTTP 400 with a localized error message suggesting the user try email OTP or SSO sign-in instead
- **Rule no-account-creation:** IF the passkey sign-in handler receives a valid credential that matches a stored entry THEN the handler creates a session but never creates a new user account, because passkey sign-in requires a pre-registered credential in the `passkey` table

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Unauthenticated visitor | Click "Sign in with passkey" button, complete the WebAuthn ceremony, and receive a new session upon successful verification | Access `/app` routes or any authenticated API endpoints before completing sign-in | Sees the `/signin` page with the passkey button visible only when `navigator.credentials` API is present |
| Authenticated user | Access `/app` routes and all session-protected endpoints after successful passkey sign-in completes | N/A (route-level restrictions covered by route-specific specs) | Full access to dashboard and authenticated features after redirect to `/app` |

## Acceptance Criteria

- [ ] The `/signin` page displays a "Sign in with passkey" button — the button element is present and visible when `navigator.credentials` API is available
- [ ] The passkey button is hidden when the `navigator.credentials` API is absent — the button element is not rendered, and the count of visible passkey sign-in elements equals 0 on unsupported browsers
- [ ] Clicking the passkey button calls `authClient.signIn.passkey()` — the client method invocation is present in the click handler
- [ ] The browser displays its native biometric or PIN prompt after the call — the WebAuthn ceremony is initiated and the `navigator.credentials.get()` call is present in the execution flow
- [ ] The server looks up the credential by `credentialID` in the `passkey` table — the database query is present and filters by the credential ID extracted from the authentication response
- [ ] The server verifies the authenticator signature using the stored `publicKey` from the `passkey` table — the signature verification call is present and returns true for valid credentials
- [ ] The server checks that the `counter` value in the authentication response is strictly greater than the stored `counter` in the `passkey` table — the comparison is present and uses the `>` operator
- [ ] After successful counter validation, the server updates the stored `counter` in the `passkey` table to the new value from the response — the update query is present and the stored counter equals the new value
- [ ] On successful verification, the server creates a session record in the `session` table with `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days from the current time — all 4 fields are present and non-empty
- [ ] On successful verification, the server sets the session token as a signed, httpOnly cookie — the `Set-Cookie` header is present in the response with `HttpOnly` = true
- [ ] On successful verification, the server sets the `docodego_authed` hint cookie with `httpOnly` = false — the cookie is present and readable via `document.cookie`
- [ ] After successful sign-in, the client redirects to `/app` — the redirect is present and the window location pathname changes to `/app` after navigation completes
- [ ] If the user cancels the browser biometric prompt (clicks "Cancel" or presses Escape), no request is sent to the server — the client remains on `/signin` and the count of error messages displayed equals 0
- [ ] If the server cannot match the credential ID to any entry in the `passkey` table, it returns HTTP 400 and the UI displays a localized error message suggesting alternative sign-in methods — the error message element is present
- [ ] All UI text related to the passkey flow is rendered via i18n translation keys — the count of hardcoded English strings in the passkey UI components equals 0

## Constraints

- The passkey sign-in flow is available only on platforms that support the WebAuthn `navigator.credentials` API — the button visibility is determined by a runtime feature check, not by user-agent string parsing. The count of user-agent-based passkey detection logic in the codebase equals 0. On platforms where the API is absent (Linux WebKitGTK in Tauri), the button is not rendered.
- The counter check is mandatory and non-bypassable — the server rejects any authentication response where the counter value is less than or equal to the stored counter. This prevents replay attacks where an attacker captures and resends a previous authentication response. The comparison uses strict greater-than (`>`) and the count of `>=` comparisons for counter validation equals 0.
- The passkey flow does not create new user accounts — unlike the email OTP flow, a passkey sign-in requires a pre-registered credential in the `passkey` table. If no matching credential exists, the server returns error. The count of user creation operations in the passkey sign-in handler equals 0.
- The `docodego_authed` hint cookie is set identically to all other sign-in methods — it is non-httpOnly, contains no session token, and is used only for FOUC prevention on Astro SSG pages.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user's browser supports `navigator.credentials` but no passkeys are registered for this device, resulting in an empty authenticator list | The browser's native prompt displays a "no passkeys available" message and the client catches the resulting error, then displays a localized message suggesting email OTP or SSO sign-in | The client remains on `/signin` and the error message element is present with a non-empty localized string |
| The user completes biometric authentication but the network connection drops before the credential response reaches the server | The client receives a network error from the HTTP call, displays a localized "connection lost" error message, and the user retries the sign-in by clicking the passkey button again | The client remains on `/signin` and no session cookie is set because the server never received the request |
| Two concurrent sign-in attempts from the same passkey on different browser tabs send credential responses with the same counter value | The first request to reach the server succeeds and updates the counter, and the second request is rejected with HTTP 400 because its counter value equals the newly stored counter | The second response returns HTTP 400 and the rejected tab displays a localized error message |
| The passkey button is clicked rapidly multiple times before the first WebAuthn ceremony completes in the browser | The browser handles concurrent `navigator.credentials.get()` calls by showing only 1 biometric prompt at a time, and the client disables the button after the first click to prevent duplicate invocations | The count of simultaneous pending credential requests equals 1 |

## Failure Modes

- **Counter replay attack detected**
    - **What happens:** An attacker intercepts a valid WebAuthn authentication response and replays it to the server at a later time, sending the same counter value that was already consumed by the original request.
    - **Source:** Adversarial action capturing and resending a previous authentication response over the network.
    - **Consequence:** If the counter check were absent, the attacker would gain unauthorized session access using a stale credential response.
    - **Recovery:** The server rejects the authentication attempt and returns error HTTP 400 because the counter value is less than or equal to the stored counter, and the server logs a warning with the credential ID and mismatched counter values for auditing purposes.
- **Credential not found in database**
    - **What happens:** The browser sends a valid WebAuthn response, but the `credentialID` does not match any entry in the `passkey` table because the user deleted their passkey or is using the wrong account credentials.
    - **Source:** User error or account misconfiguration where the passkey was removed from the server but remains on the device authenticator.
    - **Consequence:** The user cannot sign in via passkey and receives an error instead of being silently rejected with no feedback.
    - **Recovery:** The server rejects the request and returns error HTTP 400 with a diagnostic code, and the client displays a localized message notifying the user to falls back to email OTP or SSO sign-in instead.
- **WebAuthn API unavailable at runtime**
    - **What happens:** The user's browser or webview does not support the `navigator.credentials` API, such as an older browser version or Linux WebKitGTK in Tauri where WebAuthn is not implemented.
    - **Source:** Platform limitation where the runtime environment lacks WebAuthn support in its browser engine or webview implementation.
    - **Consequence:** The passkey sign-in method is entirely inaccessible to the user on that platform, requiring alternative authentication methods.
    - **Recovery:** The client checks for API availability before rendering and falls back to hiding the passkey button entirely, and the user degrades to email OTP or SSO sign-in methods with the page rendering 0 broken UI elements.
- **Biometric hardware failure during ceremony**
    - **What happens:** The device's biometric sensor (fingerprint reader, face camera) is unavailable or malfunctions during the WebAuthn ceremony, causing the browser to display an error in the native prompt dialog.
    - **Source:** Hardware malfunction or driver failure on the user's device preventing the biometric sensor from completing the authentication scan.
    - **Consequence:** The user cannot complete the biometric step and the WebAuthn ceremony fails, leaving the user without a session token on the sign-in page.
    - **Recovery:** The browser handles the failure internally and returns error to the client, which catches the exception and logs the failure reason, then falls back to displaying a localized message notifying the user to retry or use an alternative sign-in method.

## Declared Omissions

- Passkey registration flow is not covered by this spec and is defined separately in `user-registers-a-passkey.md` which handles the credential creation ceremony
- Passkey management operations (rename and remove) are not covered here and are defined in `user-renames-a-passkey.md` and `user-removes-a-passkey.md` respectively
- Mobile passkey behavior on React Native is not covered because passkeys are not supported in the Expo environment as documented in `expo-build.md` constraints
- Browser extension passkey behavior is not covered by this spec and is handled by extension-specific behavioral specs that address the WXT webview context

## Related Specifications

- [user-registers-a-passkey](user-registers-a-passkey.md) — defines the passkey registration ceremony where the user creates and stores a new WebAuthn credential
- [user-renames-a-passkey](user-renames-a-passkey.md) — defines the flow for renaming an existing passkey entry in the user's credential management interface
- [user-removes-a-passkey](user-removes-a-passkey.md) — defines the flow for deleting a passkey from the `passkey` table and the user's device authenticator
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — defines the email OTP sign-in flow that serves as the primary fallback when passkey is unavailable
- [auth-server-config](../foundation/auth-server-config.md) — defines Better Auth plugin configuration, session strategy, and the passkey plugin server-side setup
- [database-schema](../foundation/database-schema.md) — defines the `passkey` and `session` table schemas used by the credential lookup and session creation queries

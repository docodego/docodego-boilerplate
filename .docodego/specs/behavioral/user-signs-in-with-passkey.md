[← Back to Roadmap](../ROADMAP.md)

# User Signs In with Passkey

## Intent

This spec defines the passkey (WebAuthn) sign-in flow for the DoCodeGo boilerplate. The user clicks a "Sign in with passkey" button on the `/signin` page, which triggers the browser's native WebAuthn authentication ceremony. The browser presents a biometric or PIN prompt (Touch ID on macOS, Windows Hello on Windows, or the platform equivalent), and upon successful authentication, the signed credential response is sent to the server. The server verifies the credential against the stored public key in the `passkey` table, checks the counter value to prevent replay attacks, creates a session, and redirects the user to `/app`. On Linux (WebKitGTK) where WebAuthn is not available, the passkey button is hidden and the user must use alternative sign-in methods. This spec ensures the passkey flow is functional on supported platforms, gracefully degraded on unsupported platforms, and resistant to credential replay attacks.

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

## Failure Modes

- **Counter replay attack detected**: An attacker intercepts a valid WebAuthn authentication response and replays it to the server at a later time. The server detects that the `counter` value in the replayed response is less than or equal to the stored counter, rejects the authentication attempt, and returns error HTTP 400. The server logs a warning with the credential ID and the mismatched counter values for auditing purposes.
- **Credential not found in database**: The browser sends a valid WebAuthn response, but the `credentialID` does not match any entry in the `passkey` table because the user deleted their passkey or is using the wrong account. The server rejects the request and returns error HTTP 400 with a diagnostic code, and the client displays a localized message notifying the user to try email OTP or SSO sign-in instead.
- **WebAuthn API unavailable at runtime**: The user's browser or webview does not support the `navigator.credentials` API, such as an older browser version or Linux WebKitGTK in Tauri where WebAuthn is not implemented. The client checks for API availability before rendering the passkey button, and if the check returns false, the button is hidden. The user falls back to email OTP or SSO sign-in methods, and the page renders with 0 broken or non-functional passkey UI elements.
- **Biometric hardware failure during ceremony**: The device's biometric sensor (fingerprint reader, face camera) is unavailable or malfunctions during the WebAuthn ceremony, causing the browser to display an error in the native prompt. The browser handles this internally and returns an error to the client, which catches the exception and logs the failure reason, then displays a localized message notifying the user to retry or use an alternative sign-in method.

## Declared Omissions

- Passkey registration flow (covered by `user-registers-a-passkey.md`)
- Passkey management (rename, remove) (covered by `user-renames-a-passkey.md` and `user-removes-a-passkey.md`)
- Mobile passkey behavior — passkeys are not supported on React Native (covered by `expo-build.md` constraint)
- Browser extension passkey behavior (covered by extension behavioral specs)

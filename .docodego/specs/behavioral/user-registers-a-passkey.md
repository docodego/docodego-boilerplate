---
id: SPEC-2026-051
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Registers a Passkey

## Intent

This spec defines the passkey registration flow for the DoCodeGo boilerplate. An authenticated user navigates to `/app/settings/security`, views their registered passkeys, and clicks "Register passkey" to initiate the WebAuthn registration ceremony via `authClient.passkey.addPasskey()`. The browser presents a platform authenticator prompt (fingerprint reader, facial recognition, or device PIN), and upon completion the server stores the new credential in the `passkey` table with the public key, credential ID, counter, device type, backup eligibility, and supported transports. The user can assign a friendly name to the passkey. The passkey list refreshes to display the new entry with its name, device type, and creation date. Each entry includes a Delete button that triggers a confirmation dialog and calls `authClient.passkey.deletePasskey({ id })` upon confirmation. On platforms where the WebAuthn `navigator.credentials` API is absent (Linux WebKitGTK in Tauri), the "Register passkey" button is hidden and a localized message explains the limitation. This spec ensures registration works on supported platforms and degrades gracefully on unsupported ones.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.passkey.addPasskey()` (Better Auth client) | write | When the user clicks the "Register passkey" button to initiate the WebAuthn registration ceremony | The client receives an error response and displays a localized error toast notifying the user that passkey registration failed, with no credential stored |
| WebAuthn API (`navigator.credentials`) | read/write | Client-side call to `navigator.credentials.create()` during the registration ceremony after the user clicks the register button | The "Register passkey" button is hidden entirely and the client displays a localized message explaining that passkey registration is not supported on this platform |
| `passkey` table (D1) | write | Server stores the new passkey credential data after the WebAuthn registration ceremony completes successfully on the client side | The database write fails and the server returns HTTP 500 with a generic error while the client displays a localized error toast and no passkey entry appears |
| `authClient.passkey.deletePasskey({ id })` (Better Auth client) | delete | When the user confirms deletion of an existing passkey entry by clicking "Delete" and confirming the dialog prompt | The client receives an error response and displays a localized error toast notifying the user that passkey deletion failed, with the passkey entry remaining in the list |
| `@repo/i18n` | read | Rendering all UI text including button labels, empty-state messages, error toasts, confirmation dialogs, and platform-unsupported notices | Translation function falls back to the default English locale strings so the security settings page remains functional but displays untranslated English text for non-English users |

## Behavioral Flow

1. **[User]** → navigates to `/app/settings/security` and views the passkeys section, which displays a list of registered passkeys or a localized "No passkeys registered yet" message if the list is empty
2. **[Client]** → checks whether the `navigator.credentials` API is present and available at runtime before rendering the "Register passkey" button on the security settings page
3. **[Client]** → if the API is absent (such as on Linux WebKitGTK in Tauri), hides the "Register passkey" button entirely and displays a localized message explaining that passkey registration is not supported on this platform
4. **[User]** → clicks the "Register passkey" button, and the client calls `authClient.passkey.addPasskey()` which initiates the WebAuthn registration ceremony in the browser
5. **[Browser]** → presents its native platform authenticator prompt — fingerprint reader on macOS (Touch ID), facial recognition or PIN on Windows (Windows Hello), or the platform-specific equivalent
6. **[User]** → completes the biometric or PIN prompt to confirm their identity, or cancels the browser prompt by clicking Cancel or pressing Escape to abort the ceremony
7. **[Client]** → if the user cancels or dismisses the browser prompt, catches the resulting error, displays a localized error toast indicating the registration was cancelled, and no credential is stored on the server
8. **[Browser → Server]** → if the user completes the authenticator prompt, the browser sends the signed registration response containing the new credential public key and attestation data to the server
9. **[Server]** → stores the new passkey in the `passkey` table with fields: `publicKey`, `credentialID`, `counter` (initial value 0), `deviceType`, `backedUp` (boolean), and `transports` (array of supported transport types)
10. **[Client]** → after the server confirms storage, optionally prompts the user to assign a friendly name (such as "MacBook Pro Touch ID") to the newly registered passkey for identification purposes
11. **[Client]** → refreshes the passkey list to display the new entry with its friendly name (or a default label), the device type, and the creation date formatted via `Intl.DateTimeFormat`
12. **[User]** → views the updated passkey list where each entry displays a Delete button alongside the passkey name, device type, and creation date information
13. **[User]** → clicks the Delete button on a passkey entry, and the client displays a confirmation dialog asking the user to confirm the deletion before proceeding
14. **[User]** → confirms the deletion in the dialog, and the client calls `authClient.passkey.deletePasskey({ id })` to remove the passkey from the server-side `passkey` table
15. **[Server]** → deletes the passkey record from the `passkey` table and returns a success response to the client confirming the removal operation completed
16. **[Client]** → refreshes the passkey list to reflect the deletion, removing the entry from the displayed list and showing the empty-state message if no passkeys remain

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| Idle (security settings page loaded) | Ceremony In Progress | User clicks "Register passkey" button | The `navigator.credentials` API is present and the button is visible and enabled on the page |
| Ceremony In Progress | Storing Credential | Browser authenticator prompt completed successfully by the user | The browser returns a valid signed registration response with credential public key and attestation data |
| Ceremony In Progress | Idle | User cancels or dismisses the browser authenticator prompt | The browser returns an error or abort signal indicating the ceremony was not completed by the user |
| Storing Credential | Registration Complete | Server stores the passkey in the `passkey` table and returns HTTP 200 success | The database write succeeds and the server returns a valid passkey record with the credential ID and metadata |
| Storing Credential | Idle (with error toast) | Server returns an error during the passkey storage operation | The database write fails or the server returns HTTP 500 and the client displays a localized error toast message |
| Registration Complete | Idle | Passkey list refreshes and the user views the updated list with the new entry displayed | The client receives the updated passkey list from the server and re-renders the passkeys section with the new entry |

## Business Rules

- **Rule webauthn-api-check:** IF the `navigator.credentials` API is absent at runtime (detected via feature check, not user-agent parsing) THEN the "Register passkey" button is hidden and a localized message is displayed explaining that passkey registration is not supported on this platform
- **Rule ceremony-cancel-no-store:** IF the user cancels the browser authenticator prompt or the WebAuthn ceremony fails for any reason THEN no credential is stored on the server, the client displays a localized error toast, and the user remains on the security settings page free to retry
- **Rule optional-friendly-name:** IF the registration ceremony completes and the server stores the passkey THEN the user is offered the option to assign a friendly name to the passkey, with a default label used if the user declines to enter a custom name
- **Rule delete-requires-confirmation:** IF the user clicks the Delete button on a passkey entry THEN a confirmation dialog is displayed and the `authClient.passkey.deletePasskey({ id })` call is made only after the user explicitly confirms the deletion action

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | Register new passkeys, assign friendly names, delete any passkey on their own account, and view the full passkey list | Registering passkeys for other users' accounts or accessing other users' security settings pages | Full visibility of the passkeys section including the register button (when API is present) and all passkey entries |
| Admin | Register new passkeys on their own account, assign friendly names, delete their own passkeys, and view their own passkey list | Registering or deleting passkeys on behalf of other users or accessing other users' passkey management interface | Same visibility as Owner but limited to their own account security settings page only |
| Member | Register new passkeys on their own account, assign friendly names, delete their own passkeys, and view their own passkey list | Registering or deleting passkeys on behalf of other users or accessing other users' passkey management interface | Same visibility as Owner but limited to their own account security settings page only |
| Unauthenticated | None — unauthenticated visitors cannot access the security settings page at `/app/settings/security` | All actions including viewing the passkey list, registering passkeys, and deleting passkeys are denied entirely | The `/app/settings/security` route redirects unauthenticated visitors to `/signin` with 0 passkey UI elements visible |

## Constraints

- The passkey registration button visibility is determined by a runtime feature check for the `navigator.credentials` API — the count of user-agent-string-based passkey detection logic in the codebase equals 0, and the check uses `typeof navigator.credentials !== "undefined"` or equivalent API presence detection
- The server stores exactly 6 fields per passkey record: `publicKey`, `credentialID`, `counter`, `deviceType`, `backedUp`, and `transports` — the count of passkey records missing any of these 6 fields equals 0 in the database
- The passkey list displays creation dates formatted via native `Intl.DateTimeFormat` and not via date-fns — the count of date-fns imports in the passkey security settings component equals 0
- The confirmation dialog for passkey deletion is mandatory and non-bypassable — the count of `authClient.passkey.deletePasskey()` calls that execute without a preceding user confirmation equals 0
- All UI text in the passkeys section is rendered via `@repo/i18n` translation keys — the count of hardcoded English strings in the passkey management components equals 0
- The WebAuthn registration ceremony timeout is limited to 120 seconds (120000 ms) — if the user does not complete the authenticator prompt within 120 seconds, the ceremony aborts and the client displays a localized timeout error toast

## Acceptance Criteria

- [ ] The `/app/settings/security` page displays a passkeys section with a "Register passkey" button — the button element is present and visible when `navigator.credentials` API is available
- [ ] The passkeys section displays a localized "No passkeys registered yet" empty-state message when the user has 0 registered passkeys in the `passkey` table
- [ ] The "Register passkey" button is hidden when the `navigator.credentials` API is absent — the button element is not rendered and the count of visible register-passkey elements equals 0
- [ ] A localized platform-unsupported message is displayed when the `navigator.credentials` API is absent — the message element is present with non-empty translated text
- [ ] Clicking the "Register passkey" button calls `authClient.passkey.addPasskey()` — the client method invocation is present in the click handler code
- [ ] The browser displays its native authenticator prompt after the `addPasskey()` call — the WebAuthn ceremony is initiated and the count of `navigator.credentials.create()` invocations equals 1
- [ ] After successful registration, the server stores a passkey record with all 6 required fields (`publicKey`, `credentialID`, `counter`, `deviceType`, `backedUp`, `transports`) — each field is present and non-empty
- [ ] The passkey list refreshes after registration and the count of displayed passkey entries equals the count of records in the `passkey` table for that user — each entry displays a non-empty name, device type, and creation date
- [ ] The user can assign a friendly name to the newly registered passkey — the name input field is present and the stored passkey record reflects the user-provided name value
- [ ] Each passkey entry in the list displays exactly 1 Delete button — the count of Delete button elements equals the count of displayed passkey entries and is greater than 0
- [ ] Clicking the Delete button displays a confirmation dialog before executing the deletion — the dialog element is present and visible with confirm and cancel actions
- [ ] Confirming deletion calls `authClient.passkey.deletePasskey({ id })` and removes the passkey — the passkey record is absent from the `passkey` table after the call returns HTTP 200
- [ ] If the user cancels the browser authenticator prompt, no passkey is stored on the server — the count of new `passkey` table records equals 0 and a localized error toast is displayed
- [ ] On the desktop app (Tauri), macOS WKWebView and Windows WebView2 display the authenticator prompt — the WebAuthn ceremony is initiated and the native biometric or PIN prompt is present
- [ ] All UI text in the passkeys section is rendered via i18n translation keys — the count of hardcoded English strings in the passkey components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user registers a passkey and then immediately clicks "Register passkey" again before the list finishes refreshing | The client disables the "Register passkey" button during the active ceremony and re-enables it only after the list refresh completes, preventing duplicate concurrent ceremonies | The count of simultaneous pending `navigator.credentials.create()` calls equals 1 and the button has `disabled` attribute set to true |
| The user registers multiple passkeys on the same device in a single session, each with a different friendly name assigned | Each passkey is stored as a separate record in the `passkey` table with a unique `credentialID`, and the list displays all entries with their distinct friendly names and creation timestamps | The count of passkey records for the user equals the number of registration ceremonies completed, and each `credentialID` value is unique |
| The user attempts to register a passkey on Linux WebKitGTK in Tauri where the `navigator.credentials` API is not available | The "Register passkey" button is not rendered and a localized message explains that passkey registration is not supported on this platform, with 0 JavaScript errors thrown | The count of visible "Register passkey" button elements equals 0 and the platform-unsupported message element is present |
| The user deletes all registered passkeys and the passkey list becomes empty after the last deletion completes | The passkey list displays the localized "No passkeys registered yet" empty-state message and the "Register passkey" button remains visible and enabled for new registrations | The count of passkey entries in the list equals 0 and the empty-state message element is present with non-empty text content |
| The WebAuthn registration ceremony succeeds on the client but the server returns HTTP 500 when storing the passkey record | The client displays a localized error toast indicating the registration failed, no new passkey entry appears in the list, and the user can retry by clicking "Register passkey" again | The count of new passkey entries in the displayed list equals 0 and the error toast element is present and visible |

## Failure Modes

- **WebAuthn ceremony cancelled or aborted by user**
    - **What happens:** The user clicks Cancel or presses Escape on the browser's native authenticator prompt, or the biometric sensor times out after 120 seconds without receiving input from the user.
    - **Source:** User action (deliberate cancellation) or inactivity timeout during the platform authenticator prompt displayed by the browser's WebAuthn implementation.
    - **Consequence:** No credential is created on the server, no passkey record is written to the `passkey` table, and the user remains on the security settings page with the passkey list unchanged.
    - **Recovery:** The client catches the abort error and displays a localized error toast notifying the user, then falls back to the idle state where the "Register passkey" button is re-enabled for retry.

- **Server storage failure during passkey credential write**
    - **What happens:** The WebAuthn ceremony completes on the client but the server fails to write the passkey record to the `passkey` table due to a database connection error or D1 write failure.
    - **Source:** Infrastructure failure in the Cloudflare D1 database layer or a transient network error between the server handler and the database during the write operation.
    - **Consequence:** The credential is generated on the client device but not persisted on the server, resulting in a phantom credential that exists on the device authenticator but cannot be used for sign-in.
    - **Recovery:** The server returns error HTTP 500 and the client displays a localized error toast notifying the user that registration failed, then logs the error with the credential ID for debugging purposes.

- **Platform authenticator hardware failure during registration ceremony**
    - **What happens:** The device's biometric sensor (fingerprint reader, face camera) malfunctions or the hardware driver crashes during the WebAuthn registration ceremony, causing the browser to report an error.
    - **Source:** Hardware malfunction or driver failure on the user's device preventing the biometric sensor from completing the identity verification scan during registration.
    - **Consequence:** The user cannot complete the registration ceremony and no passkey credential is created, leaving the user unable to register a passkey until the hardware issue is resolved.
    - **Recovery:** The browser returns error to the client, which catches the exception and falls back to displaying a localized error toast notifying the user to retry or check their device biometric settings.

- **Passkey deletion fails due to server error**
    - **What happens:** The user confirms passkey deletion in the dialog but the `authClient.passkey.deletePasskey({ id })` call fails because the server returns HTTP 500 due to a database error or network timeout.
    - **Source:** Infrastructure failure in the Cloudflare D1 database layer or a transient network error during the delete operation targeting the `passkey` table record.
    - **Consequence:** The passkey record remains in the `passkey` table and continues to appear in the user's passkey list, with the user unable to remove it until the server error is resolved.
    - **Recovery:** The client catches the error response and displays a localized error toast notifying the user that deletion failed, then logs the error with the passkey ID for debugging and keeps the entry visible in the list.

## Declared Omissions

- Passkey sign-in flow is not covered by this spec and is defined separately in `user-signs-in-with-passkey.md` which handles the authentication ceremony
- Passkey rename operations beyond the initial friendly name assignment are not covered here and are defined in `user-renames-a-passkey.md`
- Mobile passkey behavior on React Native (Expo) is not covered because passkeys are not supported in the Expo environment as documented in platform constraints
- Browser extension passkey behavior is not covered by this spec and is handled by extension-specific behavioral specs that address the WXT webview context
- Rate limiting for passkey registration attempts is not defined in this spec and is handled by the server-side rate limiting infrastructure spec

## Related Specifications

- [user-signs-in-with-passkey](user-signs-in-with-passkey.md) — defines the passkey sign-in ceremony where the user authenticates with an existing WebAuthn credential
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — defines the email OTP sign-in flow that serves as the primary fallback when passkey is unavailable on the platform
- [user-updates-profile](user-updates-profile.md) — defines the user profile update flow that shares the same settings page layout as the security settings section
- [session-lifecycle](session-lifecycle.md) — defines the session management lifecycle that governs the authenticated state required to access the security settings page
- [auth-server-config](../foundation/auth-server-config.md) — defines Better Auth plugin configuration including the passkey plugin server-side setup and `passkey` table schema

---
id: SPEC-2026-074
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Signs In on Mobile

## Intent

This spec defines the mobile sign-in flow for the DoCodeGo
boilerplate running on Expo 54 with React Native. The mobile app
presents a sign-in screen with three authentication methods: email
OTP, SSO, and anonymous guest access. Passkey (WebAuthn) is
intentionally excluded because React Native does not reliably
support WebAuthn across devices and OS versions. For email OTP,
the user enters their email, taps "Send code," receives a 6-digit
one-time passcode, and enters it via six individual digit inputs
with auto-advance focus and paste support. For SSO, the app opens
the system browser to the identity provider's sign-in page, and
after authentication the provider redirects back to the app via a
deep link that Expo Router intercepts. On successful authentication
through any method, the session token is persisted via
`expo-secure-store` in the device's encrypted keychain, surviving
app restarts without requiring re-authentication. The
`react-native-keyboard-controller` manages keyboard appearance so
that input fields shift upward when the keyboard opens, preventing
content from being obscured. Post-authentication navigation routes
the user to the active organization's dashboard if the user belongs
to at least one organization, to the onboarding flow if the user
has zero organizations, or follows the same logic for anonymous
guests with an option to upgrade later.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.emailOtp.sendVerificationOtp()` | write | User taps "Send code" after entering their email address on the sign-in screen | The client receives an error response and displays a localized error message prompting the user to retry the request |
| `authClient.signIn.emailOtp()` | write | All 6 digit inputs are filled after the user types or pastes the one-time passcode | The client receives an error response and displays a localized inline error beneath the code inputs for the user |
| `expo-secure-store` (keychain) | write/read | After successful authentication to persist the session token, and on app launch to restore the session | The token cannot be stored or retrieved and the app falls back to requiring the user to sign in again on next launch |
| Expo Router (deep link SSO callback) | read | Identity provider redirects back to the app after SSO authentication completes in the system browser | The deep link fails to route and the app displays a localized error message prompting the user to retry the SSO flow |
| `react-native-keyboard-controller` | read | Keyboard opens while the user is interacting with the email input or the 6-digit code inputs on the sign-in screen | Input fields are obscured by the keyboard and the user cannot see what they are typing until the keyboard is dismissed manually |
| `@repo/i18n` | read | Rendering all sign-in screen labels, button text, error messages, and placeholder text in the user's locale | Translation function falls back to the default English locale strings so the sign-in screen remains usable but displays untranslated English text |

## Behavioral Flow

1. **[User]** opens the mobile app and sees the sign-in screen
    with localized form labels, an email input field with a "Send
    code" button, an SSO option below it, and an anonymous guest
    access option — there is no passkey option because WebAuthn is
    not reliably supported on React Native
2. **[Client]** initializes `react-native-keyboard-controller` so
    that the email input and code inputs shift upward when the
    on-screen keyboard opens, preventing the keyboard from
    obscuring any input fields on the sign-in screen
3. **[User]** types their email address into the input field and
    taps the "Send code" button to request a one-time passcode
    for email OTP authentication
4. **[Client]** disables the "Send code" button, displays a
    loading indicator, and calls
    `authClient.emailOtp.sendVerificationOtp({ email, type:
    "sign-in" })` to request an OTP from the server
5. **[Server]** generates a 6-digit numeric code and sends it to
    the provided email address, then responds with a generic
    success message regardless of whether the email exists to
    maintain enumeration protection
6. **[Client]** transitions to the code entry step, displaying
    six individual digit inputs where focus automatically advances
    to the next input as the user types each digit
7. **[User]** types digits one at a time with auto-advance moving
    focus forward, or pastes a full 6-digit code which fills all
    six inputs at once via the paste handler
8. **[Client]** detects all six digits are present and calls
    `authClient.signIn.emailOtp({ email, otp })` to verify the
    code against the server
9. **[Branch -- SSO flow]** If the user taps the SSO option, the
    app opens the system browser to the identity provider's
    sign-in page for the configured provider
10. **[User]** completes authentication at the identity provider
    in the system browser, and the provider redirects back to the
    app via a deep link that Expo Router intercepts and processes
11. **[Branch -- anonymous guest]** If the user taps the anonymous
    guest option, the client calls `authClient.signIn.anonymous()`
    with zero additional parameters and the server creates an
    anonymous user account with the same session handling as full
    accounts
12. **[Client]** on successful authentication through any method,
    persists the session token via `expo-secure-store` which
    stores it in the device's encrypted keychain so the token
    survives app restarts without requiring re-authentication
13. **[Client]** checks the user's organization membership count:
    if the user belongs to at least 1 organization, the app
    navigates to the active organization's dashboard screen
14. **[Client]** if the user has 0 organizations, the app
    navigates to the onboarding flow to create their first
    organization
15. **[Client]** if the user authenticated as an anonymous guest,
    the same navigation logic applies with an additional option
    to upgrade to a full account displayed as a persistent banner

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| sign_in_screen | loading_otp | User taps "Send code" button on the sign-in screen | Email field is non-empty and passes format validation |
| loading_otp | code_entry | Server returns 200 from the send-OTP endpoint | HTTP response status equals 200 |
| loading_otp | sign_in_error | Server returns non-200 or network request times out | HTTP response status does not equal 200 or request exceeds timeout |
| code_entry | verifying_otp | All 6 digit inputs are filled by typing or pasting | Count of filled digit inputs equals 6 |
| verifying_otp | authenticated | Server returns 200 from the verify-OTP endpoint | OTP matches stored value, is not expired, and retry count is under 3 |
| verifying_otp | code_entry_error | Server returns 400 from the verify-OTP endpoint | OTP is incorrect, expired, or retry limit of 3 has been reached |
| code_entry_error | verifying_otp | User re-enters 6 digits after correcting the code | Retry count is under 3 and OTP record is not yet invalidated |
| sign_in_screen | sso_browser | User taps the SSO option on the sign-in screen | At least 1 SSO provider is configured for the user's context |
| sso_browser | authenticated | Expo Router intercepts the deep link callback from the identity provider | Deep link contains a valid session token parameter |
| sso_browser | sign_in_error | Deep link callback fails or the user cancels in the system browser | No valid callback is received within the timeout period of 120 seconds |
| sign_in_screen | authenticated | User taps anonymous guest option and server returns 200 | Server creates anonymous user record and session successfully |
| authenticated | dashboard | Client checks organization membership and count is at least 1 | User belongs to at least 1 organization |
| authenticated | onboarding | Client checks organization membership and count equals 0 | User belongs to 0 organizations |

## Business Rules

- **Rule no-passkey-on-mobile:** IF the client platform is the
    Expo React Native mobile app THEN the sign-in screen renders 0
    passkey-related buttons or options because WebAuthn is not
    reliably supported on React Native across devices and OS versions
- **Rule keyboard-controller-keeps-inputs-visible:** IF the
    on-screen keyboard opens while the user interacts with the email
    input or the 6-digit code inputs THEN
    `react-native-keyboard-controller` shifts the input fields
    upward so that 0 input fields are obscured by the keyboard
- **Rule 6-digit-code-auto-advances-focus:** IF the user types a
    single digit into one of the six code inputs THEN focus
    automatically advances to the next input in sequence so the
    user does not need to manually tap the next field
- **Rule paste-fills-all-inputs:** IF the user pastes a 6-digit
    string into any of the code inputs THEN the paste handler
    distributes the digits across all 6 inputs at once and the
    count of filled inputs equals 6 after the paste event
- **Rule token-persisted-in-keychain:** IF authentication succeeds
    through any method (email OTP, SSO, or anonymous) THEN the
    session token is stored via `expo-secure-store` in the device's
    encrypted keychain and persists across app restarts until the
    session expires or is revoked
- **Rule has-org-goes-to-dashboard:** IF the authenticated user
    belongs to at least 1 organization THEN the app navigates to
    the active organization's dashboard screen after sign-in
- **Rule no-org-goes-to-onboarding:** IF the authenticated user
    belongs to 0 organizations THEN the app navigates to the
    onboarding flow to create their first organization after sign-in

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Unauthenticated mobile user | View the sign-in screen, enter email for OTP, tap SSO option, tap anonymous guest option | Access any authenticated screen or view dashboard content before completing authentication | Cannot see organization data, member lists, or any application content behind the sign-in gate |
| Authenticated mobile user (post sign-in) | Access all authenticated screens, view organization dashboard, navigate the application, sign out | Re-initiate sign-in while an active session token exists in `expo-secure-store` (redirected to dashboard instead) | Sees only organizations and resources associated with their membership records in the current session |

## Constraints

- The mobile sign-in screen presents exactly 3 authentication methods: email OTP, SSO, and anonymous guest access — the count of passkey or WebAuthn options on the mobile sign-in screen equals 0 because React Native does not reliably support WebAuthn across devices and OS versions.
- The session token is stored exclusively via `expo-secure-store` in the device's encrypted keychain — the count of session tokens stored in `AsyncStorage`, plain-text files, or unencrypted storage locations equals 0.
- The `react-native-keyboard-controller` keeps all input fields visible when the keyboard is open — the count of input fields obscured by the on-screen keyboard during email entry or code entry equals 0.
- The 6-digit code entry inputs auto-advance focus after each digit keystroke — the delay between a digit keystroke and focus advancing to the next input is under 50 milliseconds.
- The SSO deep link callback from the identity provider is handled by Expo Router — the count of SSO callbacks handled outside of Expo Router's deep link listener equals 0.
- The post-authentication navigation decision is based on the user's organization membership count — users with at least 1 organization land on the dashboard, and users with 0 organizations land on the onboarding flow, with 0 exceptions to this routing rule.

## Acceptance Criteria

- [ ] The mobile sign-in screen displays an email input field, a "Send code" button, an SSO option, and an anonymous guest option — all 4 elements are present and visible when the screen loads
- [ ] The mobile sign-in screen displays 0 passkey or WebAuthn options — the count of passkey-related buttons or links on the screen equals 0
- [ ] Tapping "Send code" calls `authClient.emailOtp.sendVerificationOtp({ email, type: "sign-in" })` — the client method invocation is present in the tap handler
- [ ] After the OTP is sent, the UI transitions to a code entry step showing exactly 6 individual digit inputs — all 6 inputs are present and visible on the screen
- [ ] Typing a digit in one code input advances focus to the next input within 50 milliseconds — the auto-advance behavior is present and the active element changes after each keystroke
- [ ] Pasting a full 6-digit code fills all 6 inputs at once — the paste handler distributes digits across all fields and the count of filled inputs equals 6
- [ ] Once all 6 digits are present, the client calls `authClient.signIn.emailOtp({ email, otp })` — the verification request is sent automatically when the last digit is entered or pasted
- [ ] Tapping the SSO option opens the system browser to the identity provider's sign-in page — the system browser launch is present and the in-app webview is not used
- [ ] After SSO authentication, the identity provider's redirect is intercepted by Expo Router via a deep link — the deep link listener is registered and the count of SSO callbacks processed outside Expo Router equals 0
- [ ] On successful authentication through any method, the session token is stored via `expo-secure-store` — the token is present in the device's encrypted keychain after authentication completes
- [ ] After authentication, if the user belongs to at least 1 organization, the app navigates to the active organization's dashboard — the navigation target is the dashboard screen
- [ ] After authentication, if the user belongs to 0 organizations, the app navigates to the onboarding flow — the navigation target equals the onboarding screen and the count of dashboard screens shown equals 0
- [ ] The `react-native-keyboard-controller` prevents the keyboard from obscuring input fields — the count of obscured inputs when the keyboard is open equals 0
- [ ] All UI text on the sign-in screen is rendered via `@repo/i18n` translation keys — the count of hardcoded English strings in the sign-in screen components equals 0
- [ ] The session token persisted in `expo-secure-store` survives app restarts — after killing and relaunching the app, the stored token is present and non-empty in the keychain and the count of sign-in prompts shown equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user pastes a value containing non-numeric characters such as `12AB56` into the code inputs on the mobile sign-in screen | The paste handler strips non-digit characters and fills only valid digits into the inputs, leaving remaining fields empty | Input fields contain only the digits `1`, `2`, `5`, `6` and the remaining 2 fields are empty |
| The user taps "Send code" and then immediately rotates the device from portrait to landscape orientation while the OTP request is in flight | The loading state is preserved across the orientation change and the response is handled when it arrives without duplicate requests | The network log shows exactly 1 OTP request and the UI displays the code entry step after the response arrives |
| The user taps the SSO option and authenticates at the identity provider, but the deep link callback fails because Expo Router does not have the scheme registered | The app does not receive the callback and the system browser displays the redirect URL — the user sees a localized error after the 120-second timeout | The app displays a localized error message after 120 seconds and the user can retry the SSO flow from the sign-in screen |
| The `expo-secure-store` keychain write fails because the device's hardware enclave storage is full or the keychain access is denied by the OS | The app catches the storage error, does not navigate to the dashboard, and displays a localized error message on the sign-in screen | The error message element is present on the sign-in screen and the navigation to dashboard does not occur |
| The user has 0 network connectivity when they tap "Send code" on the mobile sign-in screen | The client receives a network error, re-enables the "Send code" button, and displays a localized error message indicating no network connection | The "Send code" button is enabled and the error message element is visible on the sign-in screen |
| The user backgrounds the app during the SSO flow in the system browser and returns after 10 minutes to complete authentication at the identity provider | The deep link callback is processed when the app returns to the foreground and the session token is stored in the keychain | The session token is present in `expo-secure-store` and the app navigates to the dashboard or onboarding screen |

## Failure Modes

- **Email OTP delivery failure prevents the mobile user from receiving the 6-digit code needed to complete authentication**
    - **What happens:** The email provider fails to deliver the OTP email due to a transient SMTP or API error, and the mobile user never receives the 6-digit code in their inbox or email app.
    - **Source:** External email service degradation, network timeout between the server and the email provider, or misconfigured email credentials in the server environment.
    - **Consequence:** The user cannot complete email OTP authentication on the mobile app because they have no code to enter, and they remain on the code entry screen without feedback about the delivery issue.
    - **Recovery:** The server logs the delivery failure with error details and returns HTTP 200 to maintain enumeration protection — the user retries by tapping "Send code" again, which generates a fresh OTP and retries the email delivery through the provider.

- **Expo-secure-store keychain write failure prevents the session token from being persisted after successful authentication on the mobile device**
    - **What happens:** The `expo-secure-store` API call to write the session token to the device keychain fails because the hardware enclave storage is full, access is denied by the OS, or the keychain service is temporarily unavailable.
    - **Source:** Device-level storage constraints, OS-level keychain access restrictions, or a corrupted keychain state on the user's mobile device.
    - **Consequence:** The session token is not persisted, and the user will be required to sign in again on the next app launch because the token cannot be retrieved from the keychain.
    - **Recovery:** The app catches the keychain write error, logs the failure with the error code and device info, and falls back to completing the current session in memory only — the user can continue using the app for the current session but will need to re-authenticate on the next app restart.

- **SSO deep link callback not received by Expo Router after the user completes authentication at the identity provider in the system browser**
    - **What happens:** After the user authenticates at the identity provider in the system browser, the deep link redirect fails to route back to the Expo app because the URL scheme is not registered, another app intercepts the link, or the OS blocks the redirect.
    - **Source:** Missing or overridden custom URL scheme registration in the Expo app configuration, a conflicting application handling the same URL scheme, or an OS-level restriction on deep link routing.
    - **Consequence:** The mobile app never receives the authentication callback and the user remains unauthenticated with the system browser showing the redirect URL that cannot be processed.
    - **Recovery:** The app degrades to displaying a localized error message after the 120-second timeout period, prompting the user to retry the SSO flow from the sign-in screen — the error message logs the timeout event for diagnostics and notifies the user to contact support if the issue persists.

- **Network connectivity loss during OTP verification causes the verification request to fail after the user has entered all 6 digits on the mobile device**
    - **What happens:** The user enters all 6 digits of the OTP code, the client attempts to call `authClient.signIn.emailOtp({ email, otp })`, but the network request fails because the device lost connectivity between the code entry and the verification attempt.
    - **Source:** Mobile network instability such as switching between Wi-Fi and cellular, entering an area with no signal coverage, or airplane mode being enabled during the verification request.
    - **Consequence:** The verification request does not reach the server, the user receives no authentication response, and the OTP remains valid on the server but the client cannot complete the flow until connectivity is restored.
    - **Recovery:** The client detects the network error, displays a localized error message indicating connectivity loss, and falls back to allowing the user to retry the verification by tapping a "Retry" button that re-sends the same OTP code once network connectivity is restored.

## Declared Omissions

- This specification does not address OTP email template content, styling, or rendering logic — that behavior is defined in `system-sends-otp-email.md` as a separate concern
- This specification does not address post-sign-in organization resolution, team assignment, or workspace routing beyond the initial dashboard-or-onboarding decision defined here
- This specification does not address rate limiting on OTP generation or anonymous sign-in endpoints — that behavior is enforced by the global rate limiter defined in `api-framework.md`
- This specification does not address the guest-to-full-account upgrade flow on mobile — that behavior is defined in `guest-upgrades-to-full-account.md` as a separate specification
- This specification does not address SSO provider configuration and management by organization administrators — that behavior is defined in `org-admin-configures-sso-provider.md`

## Related Specifications

- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — Defines the web-platform email OTP flow that this mobile spec adapts for React Native with native keyboard handling and keychain storage
- [user-signs-in-with-sso](user-signs-in-with-sso.md) — Defines the web and desktop SSO flow that this mobile spec adapts for Expo Router deep link callbacks in the mobile context
- [user-signs-in-as-guest](user-signs-in-as-guest.md) — Defines the anonymous guest sign-in flow that this mobile spec includes as one of the three available authentication methods
- [auth-server-config](../foundation/auth-server-config.md) — Defines Better Auth server configuration including the emailOtp, anonymous, and SSO plugins that power mobile sign-in endpoints
- [database-schema](../foundation/database-schema.md) — Defines the schema for the `user`, `session`, and `verification` tables used by the mobile sign-in flow on the server side

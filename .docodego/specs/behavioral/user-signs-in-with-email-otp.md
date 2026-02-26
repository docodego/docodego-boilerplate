---
id: SPEC-2026-014
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Signs In with Email OTP

## Intent

This spec defines the end-to-end email OTP sign-in flow for the
DoCodeGo boilerplate. The user enters their email address on the
`/signin` page, receives a 6-digit numeric one-time passcode via
email, and enters the code to authenticate. The flow doubles as
sign-up — if the email does not belong to an existing user, a new
user record is created automatically. The server generates the OTP,
stores it in the `verification` table with a 5-minute expiry, and
dispatches it via email (or logs it to the console in development).
The client presents a 6-digit code entry UI with auto-advance focus
and paste support. After verification, the server creates a session,
sets the session cookie and the `docodego_authed` hint cookie, and
redirects the user to `/app`. Failed attempts are capped at 3 retries
before the OTP is invalidated.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth (`emailOtp` plugin) | read/write | OTP generation and verification requests | Server returns 500 and the global error handler falls back to a generic JSON error message for the client |
| `verification` table (D1) | read/write | Store and validate OTP records | Route handlers return 500 and the error handler degrades gracefully while non-database routes remain operational |
| `user` table (D1) | read/write | Look up or create user on verification | Route handlers return 500 and the error handler falls back to a generic JSON error response |
| `session` table (D1) | write | Create session record after OTP verification | Session creation fails with 500 and the user is not authenticated until the database recovers |
| Email service (console in dev) | write | Dispatch OTP email after generation | Server logs the delivery failure and returns HTTP 200 to maintain enumeration protection — user retries by clicking "Send code" again |
| `@repo/i18n` | read | Render all UI text on `/signin` and code entry | Translation function falls back to the default English locale strings so the page remains usable |

## Behavioral Flow

1. **[User]** navigates to `/signin` and sees the authentication
    page with all UI text localized, including an email input
    field with a "Send code" button among the available options
2. **[User]** types their email address into the input field and
    clicks the "Send code" button to request a one-time passcode
3. **[Client]** disables the "Send code" button, displays a
    loading indicator, and calls
    `authClient.emailOtp.sendVerificationOtp({ email, type:
    "sign-in" })` to request a one-time passcode from the server
4. **[Server]** generates a 6-digit numeric OTP and stores it in
    the `verification` table with a 5-minute expiry timestamp,
    then dispatches the code via email — in development the code
    is logged to the console instead of being sent
5. **[Server]** responds with a generic success message regardless
    of whether the email is associated with an existing account,
    ensuring enumeration protection so an attacker cannot probe
    the system to discover which emails are registered
6. **[Client]** transitions to the code entry step, showing six
    individual digit inputs where focus automatically advances to
    the next input as the user types each digit
7. **[User]** types digits one at a time with auto-advance moving
    focus to the next input, or pastes a full 6-digit code which
    fills all inputs at once via the paste handler
8. **[Client]** detects all six digits are present and
    automatically calls
    `authClient.signIn.emailOtp({ email, otp })` to verify the
    code against the server
9. **[Branch — code is correct]** Server creates a new session in
    the `session` table recording the session token as a signed
    cookie along with the user's `ipAddress`, `userAgent`, and an
    `expiresAt` timestamp set to 7 days from now
10. **[Server]** sets the `docodego_authed` hint cookie — a
    JS-readable non-httpOnly cookie that Astro pages use to
    prevent a flash of unauthenticated content (FOUC) on the
    client side
11. **[Client]** receives the session cookies and redirects the
    user to `/app` to begin the authenticated application
    experience
12. **[Branch — email not in `user` table]** If the email does
    not belong to an existing user, the server automatically
    creates a new user record since `disableSignUp` is set to
    `false` — the OTP sign-in flow doubles as a sign-up flow
    for new users
13. **[Branch — wrong code]** If the user enters an incorrect
    code, the UI displays a localized inline error message
    beneath the code inputs and the user can retry up to 3
    times before the OTP is invalidated
14. **[Branch — expired code]** If more than 5 minutes have
    elapsed since the OTP was generated, the UI displays a
    localized message explaining the code has expired and
    prompts the user to request a fresh one by clicking "Send
    code" again

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| email_entry | loading | User clicks "Send code" | Email field is non-empty and passes format validation |
| loading | code_entry | Server returns 200 from send-OTP endpoint | HTTP response status equals 200 |
| loading | email_entry_error | Server returns non-200 or network error | HTTP response status does not equal 200 or request times out |
| code_entry | verifying | All 6 digit inputs are filled | Count of filled digit inputs equals 6 |
| verifying | authenticated | Server returns 200 from verify endpoint | OTP matches, not expired, retry count under 3 |
| verifying | code_entry_error | Server returns 400 from verify endpoint | OTP incorrect, expired, or retry limit reached |
| code_entry_error | verifying | User re-enters 6 digits and submits | Retry count under 3 and OTP not yet invalidated |
| code_entry_error | email_entry | Retry limit of 3 reached and user clicks "Resend" | OTP has been invalidated after 3 failed attempts |
| authenticated | redirected | Client processes session cookies | Session cookie and hint cookie are both present |

## Business Rules

- **Rule OTP-uniqueness:** IF a new OTP is requested for an
    email AND an active OTP already exists for that email THEN
    the server invalidates the existing OTP before storing the
    new one, ensuring at most 1 active OTP per email at any time
- **Rule OTP-expiry:** IF the current time exceeds the
    `expiresAt` timestamp on the OTP record THEN the server
    rejects the verification attempt with HTTP 400 and the
    client displays a localized expiry message
- **Rule retry-cap:** IF the user has submitted 3 incorrect
    codes for the same OTP THEN the server invalidates the OTP
    record and all subsequent verification attempts return HTTP
    400 regardless of the code entered
- **Rule auto-signup:** IF the OTP verification succeeds AND
    the email does not match any existing `user` record THEN
    the server creates a new `user` record with the provided
    email before creating the session
- **Rule enumeration-protection:** IF the "Send code" request
    is received THEN the server returns HTTP 200 with an
    identical response structure regardless of whether the
    email exists in the `user` table, producing 0 difference
    in status code or body fields between existing and
    non-existing emails

## Permission Model

Single role; no permission model needed. The email OTP
sign-in flow is accessible to all unauthenticated visitors
and does not differentiate between user roles — every
visitor who reaches `/signin` has identical capabilities.

## Acceptance Criteria

- [ ] The `/signin` page displays an email input field and a "Send code" button — both elements are present and visible when the page loads
- [ ] Clicking "Send code" calls `authClient.emailOtp.sendVerificationOtp({ email, type: "sign-in" })` — the client method invocation is present in the click handler
- [ ] The server generates a 6-digit numeric OTP and stores it in the `verification` table with an `expiresAt` value = current time + 300 seconds (5 minutes) — the row is present after the call
- [ ] The server returns HTTP 200 regardless of whether the email exists in the `user` table — the response status code equals 200 for both existing and non-existing emails, producing 0 difference in response structure
- [ ] The "Send code" button is disabled and displays a loading indicator while the OTP request is in flight — the disabled attribute is present during the API call
- [ ] After the OTP is sent, the UI transitions to a code entry step showing exactly 6 individual digit input fields — all 6 inputs are present and visible
- [ ] Typing a digit in one input advances focus to the next input — the auto-advance behavior is present and after each keystroke the active element changes to the next input field in sequence
- [ ] Pasting a full 6-digit code fills all 6 inputs at once — the paste handler distributes digits across all fields and the count of filled inputs equals 6
- [ ] Once all 6 digits are present, the client calls `authClient.signIn.emailOtp({ email, otp })` — the verification request is present and sent automatically when the last digit is entered
- [ ] On verification, the server creates a session record in the `session` table with `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days from the current time — all 4 fields are present and non-empty
- [ ] On verification, the server sets the session token as a signed httpOnly cookie — the `Set-Cookie` header is present in the response with `HttpOnly` = true
- [ ] On verification, the server sets the `docodego_authed` hint cookie with `httpOnly` = false so that client-side JavaScript can read it — the cookie is present and readable via `document.cookie`
- [ ] After sign-in, the client redirects to `/app` — the redirect is present and the window location pathname changes to `/app` after navigation completes
- [ ] If the email does not belong to an existing user, the server creates a new `user` record with the provided email before creating the session — the new user row is present in the `user` table after the call
- [ ] If the OTP is incorrect, the server returns HTTP 400 and the UI displays a localized inline error message beneath the code inputs — the error element is present and visible
- [ ] The user can retry up to 3 times with an incorrect code — after exactly 3 failed attempts the OTP is invalidated and the server returns 400 on any subsequent attempt with the same code
- [ ] If the OTP has expired (more than 300 seconds since generation), the server returns HTTP 400 and the UI displays a localized expiry message prompting the user to request a new code — the expiry message element is present
- [ ] All UI text on the `/signin` page and code entry step is rendered via i18n translation keys — the count of hardcoded English strings in the sign-in UI components equals 0

## Constraints

- The server response to the "Send code" request does not reveal whether the email is registered — this is an enumeration protection measure. The HTTP status code equals 200 for both existing and non-existing emails. The response body contains 0 fields that differ between the two cases. This prevents attackers from probing the system to discover which emails are registered.
- The OTP is exactly 6 numeric digits — the generated value matches the pattern `^\d{6}$` and contains 0 alphabetic or special characters. The `verification` table stores the OTP alongside the email and expiry timestamp, and each email has at most 1 active OTP at any time (sending a new code invalidates the previous one).
- The `docodego_authed` hint cookie is non-httpOnly and non-sensitive — it contains no session token or user data, only a boolean indicator that an authenticated session exists. Astro SSG pages read this cookie client-side to prevent a flash of unauthenticated content (FOUC) without requiring a server round-trip.
- The retry limit of 3 is enforced server-side — the client does not track retry count locally. After 3 failed verification attempts, the server deletes or invalidates the OTP record in the `verification` table, and subsequent verification calls return HTTP 400 regardless of the code entered.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User clicks "Send code" multiple times within 2 seconds before the first request completes | The client disables the button on the first click and ignores subsequent clicks — the server receives at most 1 OTP generation request per user action | The disabled attribute is present on the button within 100ms of the first click and the network log shows exactly 1 request |
| User pastes a value containing non-numeric characters such as `12AB56` into the code inputs | The paste handler strips non-digit characters and fills only valid digits — the count of non-numeric characters in the input fields equals 0 after the paste event | Input fields contain only the digits `1`, `2`, `5`, `6` and the remaining fields are empty |
| User navigates away from the code entry step and returns after 5 minutes have elapsed | The OTP has expired on the server and the next verification attempt returns HTTP 400 with a localized expiry message prompting the user to request a new code | The error message element is present and the HTTP response status equals 400 |
| User submits 3 incorrect codes and then enters the correct code on a 4th attempt | The OTP was invalidated after the 3rd failure — the server returns HTTP 400 on the 4th attempt regardless of code correctness | The HTTP response status equals 400 and the response body contains an error code indicating the OTP is invalidated |
| User opens `/signin` in 2 browser tabs and requests OTP from both tabs for the same email | The second request invalidates the first OTP — only the code from the second request is valid for verification | Submitting the first OTP returns HTTP 400 and submitting the second OTP returns HTTP 200 |
| The email input contains leading or trailing whitespace such as `" user@example.com "` | The client trims whitespace before sending the request — the email value in the API request body contains 0 leading or trailing space characters | The request payload email field equals `"user@example.com"` with no surrounding whitespace |

## Failure Modes

- **Email delivery failure prevents user from receiving the OTP code**
    - **What happens:** The email provider fails to deliver the OTP email due to a transient SMTP or API error, and the user never receives the 6-digit code in their inbox.
    - **Source:** External email service degradation, network timeout between server and email provider, or misconfigured email credentials in the environment.
    - **Consequence:** The user cannot complete authentication because they have no code to enter, and they remain stuck on the code entry screen without feedback about the delivery failure.
    - **Recovery:** The server logs the delivery failure with error details and returns HTTP 200 to maintain enumeration protection — the user retries by clicking "Send code" again, which generates a fresh OTP and retries the email delivery through the provider.
- **OTP replay attack after the 5-minute expiry window has elapsed**
    - **What happens:** An attacker intercepts a valid OTP via email compromise or network sniffing and attempts to use it after the 300-second expiry window has elapsed.
    - **Source:** Adversarial action where a third party obtains the OTP value through unauthorized email access, man-in-the-middle attack, or shoulder surfing.
    - **Consequence:** If the server did not enforce expiry, the attacker would gain unauthorized access to the victim's account using a stale code that the legitimate user has already abandoned.
    - **Recovery:** The server rejects the expired code and returns HTTP 400 — the `expiresAt` check falls back to blocking all verification attempts for codes older than 300 seconds, and the attacker receives an error response with no session created.
- **Brute-force attempt exhausts the 3-retry limit on a valid OTP**
    - **What happens:** An attacker or automated script submits random 6-digit codes against the verification endpoint, attempting to guess the OTP by cycling through numeric combinations.
    - **Source:** Adversarial action targeting the verification endpoint with automated requests to guess the 6-digit code by brute force.
    - **Consequence:** After 3 incorrect submissions the OTP is invalidated, and if the legitimate user has not yet entered their code, they lose access to the current OTP and need to request a new one.
    - **Recovery:** The server invalidates the OTP after 3 failed attempts and rejects all subsequent verification calls — the user falls back to requesting a new OTP by clicking "Send code" again, which generates a fresh code and restarts the flow.
- **Browser autofill interference fills OTP inputs with saved password credentials**
    - **What happens:** The browser's password manager or autofill feature detects the 6 input fields and attempts to fill them with saved credentials, displaying incorrect data in the code fields.
    - **Source:** Browser heuristic that misidentifies OTP digit inputs as a password or username field and populates them with stored credential data.
    - **Consequence:** The user sees non-numeric saved credential data in the OTP fields, causing confusion and a failed verification attempt if they submit without correcting the values.
    - **Recovery:** The input fields set `autocomplete="one-time-code"` to hint the browser to use OTP autofill instead of password autofill, and the fields fall back to `type="text"` with `inputMode="numeric"` to prevent password manager popup interference on the code entry screen.

## Declared Omissions

- This specification does not address OTP email template content, styling, or rendering logic — that behavior is defined in `system-sends-otp-email.md` as a separate concern
- This specification does not address post-sign-in organization resolution, team assignment, or workspace routing — that behavior is defined in `session-lifecycle.md`
- This specification does not address rate limiting on OTP generation requests — that behavior is enforced by the global rate limiter defined in `api-framework.md`
- This specification does not address mobile-specific sign-in UI layout, deep linking, or native OTP autofill — that behavior is defined in `user-signs-in-on-mobile.md`
- This specification does not address the SSO or passkey sign-in flows — those are defined in `user-signs-in-with-sso.md` and `user-signs-in-with-passkey.md` respectively

## Related Specifications

- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the `emailOtp` plugin that powers OTP generation and verification
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `user`, `session`, and `verification` tables used by this sign-in flow
- [session-lifecycle](session-lifecycle.md) — Post-authentication session management, cookie refresh strategy, and session expiry handling
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure providing translation keys for all sign-in UI text
- [api-framework](../foundation/api-framework.md) — Hono middleware stack, CORS configuration, and global error handler that wraps all API responses

[← Back to Roadmap](../ROADMAP.md)

# User Signs In with Email OTP

## Intent

This spec defines the end-to-end email OTP sign-in flow for the DoCodeGo boilerplate. The user enters their email address on the `/signin` page, receives a 6-digit numeric one-time passcode via email, and enters the code to authenticate. The flow doubles as sign-up — if the email does not belong to an existing user, a new user record is created automatically. The server generates the OTP, stores it in the `verification` table with a 5-minute expiry, and dispatches it via email (or logs it to the console in development). The client presents a 6-digit code entry UI with auto-advance focus and paste support. After successful verification, the server creates a session, sets the session cookie and the `docodego_authed` hint cookie, and redirects the user to `/app`. Failed attempts are capped at 3 retries before the OTP is invalidated.

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
- [ ] On successful verification, the server creates a session record in the `session` table with `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days from the current time — all 4 fields are present and non-empty
- [ ] On successful verification, the server sets the session token as a signed, httpOnly cookie — the `Set-Cookie` header is present in the response with `HttpOnly` = true
- [ ] On successful verification, the server sets the `docodego_authed` hint cookie with `httpOnly` = false so that client-side JavaScript can read it — the cookie is present and readable via `document.cookie`
- [ ] After successful sign-in, the client redirects to `/app` — the redirect is present and the window location pathname changes to `/app` after navigation completes
- [ ] If the email does not belong to an existing user, the server creates a new `user` record with the provided email before creating the session — the new user row is present in the `user` table after the call
- [ ] If the OTP is incorrect, the server returns HTTP 400 and the UI displays a localized inline error message beneath the code inputs — the error element is present and visible
- [ ] The user can retry up to 3 times with an incorrect code — after exactly 3 failed attempts the OTP is invalidated and the server returns 400 on any subsequent attempt with the same code
- [ ] If the OTP has expired (more than 300 seconds since generation), the server returns HTTP 400 and the UI displays a localized expiry message prompting the user to request a new code — the expiry message element is present
- [ ] All UI text on the `/signin` page and code entry step is rendered via i18n translation keys — the count of hardcoded English strings in the sign-in UI components equals 0

## Constraints

- The server response to the "Send code" request must not reveal whether the email is registered — this is an enumeration protection measure. The HTTP status code equals 200 for both existing and non-existing emails. The response body contains 0 fields that differ between the two cases. This prevents attackers from probing the system to discover which emails are registered.
- The OTP is exactly 6 numeric digits — the generated value matches the pattern `^\d{6}$` and contains 0 alphabetic or special characters. The `verification` table stores the OTP alongside the email and expiry timestamp, and each email has at most 1 active OTP at any time (sending a new code invalidates the previous one).
- The `docodego_authed` hint cookie is non-httpOnly and non-sensitive — it contains no session token or user data, only a boolean indicator that an authenticated session exists. Astro SSG pages read this cookie client-side to prevent a flash of unauthenticated content (FOUC) without requiring a server round-trip.
- The retry limit of 3 is enforced server-side — the client does not track retry count locally. After 3 failed verification attempts, the server deletes or invalidates the OTP record in the `verification` table, and subsequent verification calls return HTTP 400 regardless of the code entered.

## Failure Modes

- **Email delivery failure**: The email provider fails to deliver the OTP email due to a transient SMTP or API error, and the user never receives the code. The server logs the delivery failure with the error details to the server-side log and returns HTTP 200 to the client regardless to maintain enumeration protection. The user can click "Send code" again to request a new OTP, which generates a fresh code and retries the email delivery through the provider.
- **OTP replay after expiry**: An attacker intercepts a valid OTP and attempts to use it after the 5-minute window has elapsed, sending the stale code to the verification endpoint. The server checks the `expiresAt` timestamp before accepting the code, and if the current time exceeds `expiresAt`, the server rejects the code and returns error HTTP 400, preventing authentication with expired credentials.
- **Concurrent OTP requests for same email**: A user clicks "Send code" multiple times in quick succession, generating multiple OTP records for the same email address in the verification table. The server invalidates any existing OTP for the email before generating a new one, ensuring that at most 1 active OTP exists per email at any time. Older codes are rejected and the server returns error if the user submits a previously invalidated code.
- **Browser autofill interference with code inputs**: The browser's password manager or autofill feature attempts to fill the 6-digit OTP inputs with saved credentials, displaying incorrect data in the code fields and confusing the user. The input fields set `autocomplete="one-time-code"` to hint the browser to use SMS or email OTP autofill instead of password autofill, and fall back to `type="text"` with `inputMode="numeric"` to prevent password manager popup interference on the code entry screen.

## Declared Omissions

- OTP email template content and rendering (covered by `system-sends-otp-email.md`)
- Post-sign-in organization and team resolution (covered by `session-lifecycle.md`)
- Rate limiting on OTP requests (covered by `api-framework.md` global rate limiter)
- Mobile-specific sign-in behavior (covered by `user-signs-in-on-mobile.md`)

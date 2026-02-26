[← Back to Roadmap](../ROADMAP.md)

# Guest Upgrades to Full Account

## Intent

This spec defines the flow for upgrading an anonymous guest account to a full account in the DoCodeGo boilerplate. A guest user who signed in anonymously clicks the persistent upgrade banner or navigates to account settings, enters a real email address, and completes OTP verification. Upon successful verification, Better Auth's `onLinkAccount` callback fires, the system migrates all guest data to the new full account, clears the `isAnonymous` flag, deletes the original anonymous user record, and the user continues their session seamlessly without re-authentication. The upgrade banner disappears after the conversion is complete. This spec ensures that the upgrade path is discoverable, that data migration is complete, and that the user's session remains valid throughout the process.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth (anonymous plugin) | read/write | OTP verification and `onLinkAccount` callback during upgrade | The upgrade request returns HTTP 500 and the error handler falls back to a generic JSON error message while the guest session remains intact and unchanged |
| D1 (Cloudflare SQL) | read/write | Email uniqueness check, data migration transaction, anonymous record deletion | The upgrade transaction rolls back and the system degrades gracefully — the user remains anonymous and retries the upgrade later |
| `@repo/contracts` | read | App startup (schema registration for upgrade endpoint types) | Build fails at compile time because the oRPC router cannot resolve contract types and CI alerts to block deployment |
| `@repo/i18n` | read | Each upgrade UI step (banner, email input, OTP entry, success/error messages) | Translation function falls back to the default English locale strings so upgrade UI remains readable but untranslated for non-English users |
| OTP email service | write | After email submission to send the 6-digit verification code | The OTP send call returns an error and the client displays a localized message asking the user to retry — the upgrade flow degrades to the email entry step |

## Behavioral Flow

1. **[Guest user]** → an anonymous user who has been browsing the application as a guest decides to link a real email address by clicking the persistent localized upgrade banner or navigating to their account settings where they find an option to convert their guest account into a full account
2. **[Client]** → renders the email input form where the guest enters their real email address to begin the upgrade process
3. **[Client]** → submits the email to the upgrade endpoint on the API server for validation and OTP initiation
4. **[Server]** → checks the `user` table for email uniqueness — if the email already belongs to another account, returns HTTP 409 with a localized error message and the flow stops
5. **[Server]** → initiates the standard OTP verification flow by generating a 6-digit code, storing it in the `verification` table with a 5-minute expiry (`expiresAt` = current time + 300 seconds), and sending it to the provided email address (logged to console in development)
6. **[Client]** → transitions to the same six-digit code entry UI used during normal sign-in, displaying exactly 6 individual digit inputs for the user to enter the OTP
7. **[Guest user]** → receives the OTP and enters the 6-digit code through the six-digit code entry UI into the verification inputs
8. **[Server]** → validates the OTP code against the `verification` table — if incorrect and attempts < 3, returns HTTP 400 with remaining attempts count; if attempts = 3, invalidates the OTP and returns HTTP 400 prompting a restart
9. **[Server]** → once the code is verified, Better Auth's `onLinkAccount` callback fires with `{ anonymousUser, newUser }`, signaling that a guest identity is being merged into a full account
10. **[Server]** → executes an atomic database transaction to migrate all guest data — preferences, drafts, and any other activity accumulated during the anonymous session — from the anonymous user ID to the upgraded account ID, sets `isAnonymous` to false, updates the email field to the verified address, updates the session's `userId` in-place, and deletes the original anonymous user record
11. **[Client]** → receives the success response, the upgrade banner disappears since the user now has a verified email, and the user continues their session seamlessly with the existing session token unchanged — no re-authentication is required
12. **[Server]** → all activity from the guest period is preserved and attributed to the new full account, and from this point forward the user signs in with their real email via OTP, passkey, or any other method they configure

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| anonymous | email_entry | Guest clicks upgrade banner or account settings upgrade option | `user.isAnonymous` equals true |
| email_entry | otp_pending | Guest submits a valid email address that passes uniqueness check | Email is not already registered to another user in the `user` table |
| email_entry | email_entry (error) | Guest submits an email that belongs to another account | Server returns HTTP 409 indicating the email is already in use |
| otp_pending | upgraded | Guest enters the correct 6-digit OTP code within 3 attempts | OTP matches the stored code and `expiresAt` has not passed |
| otp_pending | otp_pending (retry) | Guest enters an incorrect OTP code with remaining attempts > 0 | Attempt count is less than 3 and OTP has not expired |
| otp_pending | email_entry (reset) | Guest exhausts all 3 OTP attempts or the OTP expires after 300 seconds | Attempt count equals 3 or current time exceeds `expiresAt` |
| upgraded | session_continues | Server completes atomic data migration and session update transaction | All data records reference the new user ID and `isAnonymous` equals false |

## Business Rules

- **Rule email-uniqueness:** IF the submitted email address already exists in the `user` table belonging to a different account THEN the server rejects the upgrade with HTTP 409 and the client displays a localized error prompting the user to provide a different email address
- **Rule otp-retry-limit:** IF the guest enters an incorrect OTP code AND the cumulative attempt count equals 3 THEN the server invalidates the OTP record and the client prompts the user to restart the upgrade flow from the email entry step
- **Rule otp-expiry:** IF the OTP verification request arrives after `expiresAt` (current time + 300 seconds from generation) THEN the server rejects the code with HTTP 400 and the client prompts the user to request a new code
- **Rule atomic-migration:** IF any step in the data migration transaction fails (migrating records, clearing `isAnonymous`, updating email, updating session, deleting anonymous record) THEN the entire transaction rolls back and the user remains anonymous with no partial state changes
- **Rule session-preservation:** IF the upgrade completes successfully THEN the server updates the session's `userId` to the upgraded account in-place and the session token cookie remains unchanged — no re-authentication is required

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Anonymous guest (`isAnonymous` = true) | Initiate the upgrade flow, submit email for verification, enter OTP code, complete the upgrade | Access full-account-only features before completing the upgrade (defined in route-specific specs) | Sees the persistent upgrade banner and the account settings upgrade option |
| Authenticated user (`isAnonymous` = false) | Access all full-account features as defined in route-specific specs | Initiate the upgrade flow (the upgrade option and banner are hidden when `isAnonymous` equals false) | Does not see the upgrade banner or account settings upgrade option |

## Acceptance Criteria

- [ ] The persistent upgrade banner displayed to anonymous users contains a button or link to initiate the upgrade flow — the interactive element is present and visible when `user.isAnonymous` equals true
- [ ] The account settings page contains an upgrade option for anonymous users — the option element is present when `user.isAnonymous` equals true and absent when `user.isAnonymous` equals false
- [ ] Clicking the upgrade trigger displays an email input field where the user enters their real email address — the input element is present and accepts text input
- [ ] After the user submits their email, the system calls the OTP send endpoint and generates a 6-digit code stored in the `verification` table with `expiresAt` = current time + 300 seconds — the verification row is present after the call
- [ ] The UI transitions to the 6-digit code entry step with exactly 6 individual digit inputs — all 6 input fields are present and visible
- [ ] After successful OTP verification, Better Auth's `onLinkAccount` callback fires with the anonymous user and new user references — the callback invocation is present in the auth configuration
- [ ] The system migrates all guest data (preferences, drafts, activity) from the anonymous user to the upgraded account — the count of data records still referencing the old anonymous user ID equals 0 after migration
- [ ] The `isAnonymous` flag on the user record is set to false after the upgrade completes — the field value is present and equals false
- [ ] The user's email field is updated to the real email address provided during upgrade — the email value is present, non-empty, and no longer matches the `anon-{uuid}@anon.docodego.com` pattern
- [ ] The original anonymous user record is deleted from the `user` table after data migration — the old record is absent from the table
- [ ] The user's existing session remains valid after the upgrade — no re-authentication is required and the session record is present in the `session` table with the same token
- [ ] The upgrade banner disappears after the conversion completes — the banner element is absent from the rendered DOM when `user.isAnonymous` equals false
- [ ] All UI text in the upgrade flow is rendered via i18n translation keys — the count of hardcoded English strings in the upgrade components equals 0

## Constraints

- The upgrade flow reuses the same OTP verification UI and server logic as the standard email OTP sign-in — no separate OTP implementation exists for the upgrade path. The count of duplicate OTP generation or verification functions in the codebase equals 0. The same `verification` table, 6-digit format, 5-minute expiry, and 3-retry limit apply.
- The upgrade is atomic — either all data is migrated and the anonymous record is deleted, or none of it happens. If the migration fails partway through, the transaction rolls back and the user remains anonymous. The count of partially migrated states where `isAnonymous` = false but data still references the old user ID equals 0.
- The session is preserved across the upgrade without re-authentication — the server updates the session's `userId` to point to the upgraded account in-place. The session token cookie remains unchanged and the `docodego_authed` hint cookie stays set throughout the process.
- The real email address provided during upgrade must not already belong to another user — the server checks for email uniqueness before proceeding. If the email is already registered, the upgrade is rejected and the user must provide a different email.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The guest submits an email address that is already registered to an existing full account in the `user` table | The server rejects the upgrade with HTTP 409 and the client displays a localized error message prompting the user to provide a different email address | Response status is 409 and the response body contains a localized error message with the email conflict code |
| The guest enters 3 incorrect OTP codes in succession, exhausting the retry limit for that verification record | The server invalidates the OTP record and returns HTTP 400 on the third attempt, and the client prompts the user to restart the upgrade flow from the email entry step | Response status is 400 after the third attempt and the `verification` record is marked as expired or deleted |
| The guest starts the upgrade flow but the OTP expires after 300 seconds before they enter the code into the verification inputs | The server rejects the expired OTP with HTTP 400 and the client displays a localized message asking the user to request a new verification code | Response status is 400 and the error code indicates OTP expiration rather than incorrect code |
| The guest's session expires (7-day timeout) while they are in the middle of the OTP verification step of the upgrade flow | The server returns HTTP 401 because no valid session context exists, and the client falls back to redirecting the user to `/signin` | Response status is 401 and the client navigates to the sign-in page |
| The guest enters a valid email and correct OTP but the database transaction fails during data migration due to a D1 error | The server rolls back the entire transaction, the user remains anonymous with `isAnonymous` still true, and the server returns HTTP 500 with a localized retry message | Response status is 500 and the `isAnonymous` flag remains true on the user record |
| The guest closes the browser tab after submitting their email but before entering the OTP code, then returns later | The OTP remains valid in the `verification` table until `expiresAt` passes (300 seconds from generation), so the user can resume by navigating back and entering the code | The `verification` row is present and `expiresAt` has not passed if within the 5-minute window |

## Failure Modes

- **Email already registered to another user**
    - **What happens:** The guest enters an email address that already exists in the `user` table belonging to a different account, causing a uniqueness conflict during the upgrade process.
    - **Source:** User input conflict — the guest provides an email that is already associated with an existing full account in the system.
    - **Consequence:** The upgrade cannot proceed because linking the email to the anonymous account would create a duplicate, violating the email uniqueness constraint.
    - **Recovery:** The server rejects the upgrade request and returns error HTTP 409, and the client displays a localized message notifying the user that the email is already in use — the guest retries by providing a different email address to complete the upgrade.

- **OTP verification fails after 3 attempts**
    - **What happens:** The guest enters incorrect codes 3 times during the upgrade OTP step, exhausting the retry limit and invalidating the OTP verification record in the database.
    - **Source:** User input error — the guest misreads or mistypes the 6-digit code received via email, or the code was delivered to the wrong inbox.
    - **Consequence:** The current OTP is permanently invalidated and cannot be retried, blocking the upgrade flow until a new code is generated.
    - **Recovery:** The server rejects subsequent verification attempts and returns error HTTP 400, and the client displays a localized message prompting the user to request a new code — the system falls back to the email entry step where the guest restarts the flow.

- **Data migration fails mid-transaction**
    - **What happens:** The server encounters a database error while migrating guest data records from the anonymous user to the upgraded account, leaving the migration incomplete within the transaction scope.
    - **Source:** Database failure — D1 connection error, exceeded write limits, or constraint violation during the multi-table data migration transaction.
    - **Consequence:** Without rollback protection, the system could end up in a partially migrated state where some records reference the old user ID and others reference the new one.
    - **Recovery:** The server rolls back the entire transaction so no partial state exists, logs the database error with the affected table and row details, and returns error HTTP 500 to the client with a localized message — the user remains anonymous and retries the upgrade later.

- **Session invalidation during upgrade**
    - **What happens:** The user's session expires naturally (7-day timeout) while they are in the middle of the OTP verification step, causing the upgrade request to fail with no valid session context available.
    - **Source:** Session lifecycle expiration — the guest took too long between starting the upgrade flow and completing OTP verification, exceeding the session TTL.
    - **Consequence:** The server cannot identify the anonymous user to upgrade because the session token is no longer valid, and the upgrade request is rejected entirely.
    - **Recovery:** The server returns error HTTP 401, and the client falls back to redirecting the user to `/signin` where they can sign in as a guest again and retry the upgrade from the beginning of the flow.

## Declared Omissions

- OTP email template design, delivery mechanism, and retry logic for failed email sends are not covered here and are defined in `system-sends-otp-email.md`
- Guest sign-in flow that creates the initial anonymous account and session is not covered here and is defined in `user-signs-in-as-guest.md`
- Upgrade banner UI component rendering, animation, positioning, and visibility toggle logic are not covered here and are defined in `user-signs-in-as-guest.md` acceptance criteria
- Full account deletion flow for users who previously upgraded from guest accounts is not covered here and are defined in `user-deletes-their-account.md`
- Rate limiting on the OTP send endpoint and brute-force protection for the verification endpoint are not covered here and are defined in the API framework and auth server configuration specs

## Related Specifications

- [user-signs-in-as-guest](user-signs-in-as-guest.md) — Defines the guest sign-in flow that creates the anonymous account and session which this upgrade flow converts to a full account
- [system-sends-otp-email](system-sends-otp-email.md) — Defines the OTP email generation, template rendering, and delivery mechanism used during the upgrade verification step
- [user-deletes-their-account](user-deletes-their-account.md) — Defines the account deletion flow that applies to upgraded accounts after they have been converted from guest to full status
- [auth-server-config](../foundation/auth-server-config.md) — Defines Better Auth plugin configuration including the anonymous plugin and `onLinkAccount` callback used during the upgrade process
- [database-schema](../foundation/database-schema.md) — Defines the `user`, `session`, and `verification` table schemas referenced by the upgrade data migration transaction

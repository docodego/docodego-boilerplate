[← Back to Roadmap](../ROADMAP.md)

# Guest Upgrades to Full Account

## Intent

This spec defines the flow for upgrading an anonymous guest account to a full account in the DoCodeGo boilerplate. A guest user who signed in anonymously clicks the persistent upgrade banner or navigates to account settings, enters a real email address, and completes OTP verification. Upon successful verification, Better Auth's `onLinkAccount` callback fires, the system migrates all guest data to the new full account, clears the `isAnonymous` flag, deletes the original anonymous user record, and the user continues their session seamlessly without re-authentication. The upgrade banner disappears after the conversion is complete. This spec ensures that the upgrade path is discoverable, that data migration is complete, and that the user's session remains valid throughout the process.

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

## Failure Modes

- **Email already registered to another user**: The guest enters an email address that already exists in the `user` table belonging to a different account, causing a uniqueness conflict. The server rejects the upgrade request and returns error HTTP 409, and the client displays a localized message notifying the user that the email is already in use and they must provide a different email address to complete the upgrade.
- **OTP verification fails after 3 attempts**: The guest enters incorrect codes 3 times during the upgrade OTP step, exhausting the retry limit and invalidating the OTP. The server rejects subsequent verification attempts and returns error HTTP 400, and the client displays a localized message prompting the user to request a new code by restarting the upgrade flow from the email entry step.
- **Data migration fails mid-transaction**: The server encounters a database error while migrating guest data records from the anonymous user to the upgraded account, leaving the migration incomplete. The server rolls back the entire transaction, logs the database error with the affected table and row details, and returns error HTTP 500 to the client with a localized message asking the user to retry the upgrade.
- **Session invalidation during upgrade**: The user's session expires naturally (7-day timeout) while they are in the middle of the OTP verification step, causing the upgrade request to fail with no valid session context. The server returns error HTTP 401, and the client falls back to redirecting the user to `/signin` where they can sign in as a guest again and retry the upgrade from the beginning.

## Declared Omissions

- OTP email template and delivery (covered by `system-sends-otp-email.md`)
- Guest sign-in flow that creates the anonymous account (covered by `user-signs-in-as-guest.md`)
- Upgrade banner UI rendering and visibility logic (covered by `user-signs-in-as-guest.md` acceptance criteria)
- Full account deletion flow for upgraded users (covered by `user-deletes-their-account.md`)

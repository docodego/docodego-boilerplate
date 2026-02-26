[← Back to Roadmap](../ROADMAP.md)

# User Signs In as Guest

## Intent

This spec defines the anonymous guest sign-in flow for the DoCodeGo boilerplate. The user clicks a "Continue as guest" button on the `/signin` page, and the server creates an anonymous user account with no email, credentials, or verification step required. The server assigns an auto-generated email in the format `anon-{uuid}@anon.docodego.com` to satisfy the email uniqueness constraint, sets `isAnonymous` to `true` on the user record, creates a full session, and redirects the user to `/app`. A persistent upgrade banner is displayed throughout the guest session encouraging the user to link a real email address. This spec ensures that guest sign-in is instant, that anonymous accounts are distinguishable from full accounts, and that the upgrade path is always visible.

## Acceptance Criteria

- [ ] The `/signin` page displays a "Continue as guest" button — the button element is present and visible when the page loads
- [ ] Clicking the "Continue as guest" button calls `authClient.signIn.anonymous()` with 0 additional parameters — the client method invocation is present in the click handler
- [ ] The server creates a new `user` record with `isAnonymous` = true — the field value is present and equals true in the created row
- [ ] The server assigns an auto-generated email in the format `anon-{uuid}@anon.docodego.com` to the user record — the email matches the pattern `^anon-[a-f0-9-]+@anon\.docodego\.com$` and is present in the `email` column
- [ ] The auto-generated email satisfies the unique constraint on the `user.email` column — inserting 2 guest users produces 2 distinct email values and the count of constraint violations equals 0
- [ ] The server creates a session record in the `session` table with `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days from the current time — all 4 fields are present and non-empty
- [ ] The server sets the session token as a signed, httpOnly cookie — the `Set-Cookie` header is present in the response with `HttpOnly` = true
- [ ] The server sets the `docodego_authed` hint cookie with `httpOnly` = false — the cookie is present and readable via `document.cookie`
- [ ] After successful guest sign-in, the client redirects to `/app` — the redirect is present and the window location pathname changes to `/app` after navigation completes
- [ ] A persistent upgrade banner is displayed in the application UI for anonymous users — the banner element is present and visible when `user.isAnonymous` equals true
- [ ] The upgrade banner contains a localized message and a link or button to initiate account upgrade — both the text element and the interactive element are present in the banner
- [ ] The upgrade banner is absent for non-anonymous users — when `user.isAnonymous` equals false, the banner element is absent from the rendered DOM
- [ ] The guest sign-in flow completes with 0 intermediate steps — no email entry, no OTP, and no verification is required, and the total API call count equals 1
- [ ] All UI text related to guest sign-in and the upgrade banner is rendered via i18n translation keys — the count of hardcoded English strings in these components equals 0

## Constraints

- Guest accounts are flagged with `isAnonymous` = true at the database level — this flag is the only distinguishing attribute between anonymous and full accounts. The guest has a valid session, can access all authenticated routes, and interacts with the application identically to a full user except for the visible upgrade banner.
- The auto-generated email format `anon-{uuid}@anon.docodego.com` is an implementation detail that never appears in the UI — the count of UI elements displaying the anonymous email to the user equals 0. The email exists solely to satisfy the database uniqueness constraint on the `user.email` column.
- The upgrade banner is persistent and cannot be dismissed by the guest — it remains visible on every page under `/app/*` until the user upgrades to a full account by linking a real email address. The count of close or dismiss buttons on the upgrade banner equals 0.
- Anonymous accounts have the same session expiry (7 days) as full accounts — there is no shortened session duration for guests. The `expiresAt` value in the `session` table uses the identical 7-day offset regardless of the `isAnonymous` flag.

## Failure Modes

- **UUID collision on auto-generated email**: The server generates an anonymous email that collides with an existing user email in the `user` table, causing a unique constraint violation on insert. The server catches the constraint error and retries the insert with a newly generated UUID up to 3 times, logging each collision attempt. If all 3 retries fail, the server returns error HTTP 500 with a diagnostic message for investigation.
- **Anonymous user accesses restricted org feature**: A guest attempts to perform an organization action (creating an org or inviting a member) that requires a verified email address, but the guest has only an auto-generated anonymous email. The server checks `user.isAnonymous` before processing the request, and if the value equals true, the server rejects the request and returns error HTTP 403 with a localized message notifying the user to upgrade to a full account first.
- **Session cookie not set due to network interruption**: The server creates the anonymous user record and session successfully, but the response fails to deliver the `Set-Cookie` header to the client due to a connection drop mid-response. The client detects the absent `docodego_authed` hint cookie and falls back to remaining on the `/signin` page without redirecting. The orphaned server-side session record expires naturally after the 7-day timeout period.
- **Upgrade banner not rendering for anonymous user**: A code change inadvertently removes the upgrade banner component or breaks the `isAnonymous` check, causing anonymous users to browse without seeing the upgrade prompt. The CI test suite includes a test that renders the application shell with `user.isAnonymous` = true and asserts the upgrade banner element is present in the DOM, and returns error if the assertion fails, blocking the build.

## Declared Omissions

- Guest-to-full-account upgrade flow (covered by `guest-upgrades-to-full-account.md`)
- Guest account deletion (covered by `guest-deletes-anonymous-account.md`)
- Organization and team restrictions for anonymous users (covered by org behavioral specs)
- Mobile guest sign-in behavior (covered by `user-signs-in-on-mobile.md`)

---
id: SPEC-2026-016
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Signs In as Guest

## Intent

This spec defines the anonymous guest sign-in flow for the DoCodeGo boilerplate. The user clicks a "Continue as guest" button on the `/signin` page, and the server creates an anonymous user account with no email, credentials, or verification step required. The server assigns an auto-generated email in the format `anon-{uuid}@anon.docodego.com` to satisfy the email uniqueness constraint, sets `isAnonymous` to `true` on the user record, creates a full session, and redirects the user to `/app`. A persistent upgrade banner is displayed throughout the guest session encouraging the user to link a real email address. This spec ensures that guest sign-in is instant, that anonymous accounts are distinguishable from full accounts, and that the upgrade path is always visible.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth (`signIn.anonymous`) | write | Client clicks "Continue as guest" button on `/signin` | The client receives an error response and remains on the `/signin` page without creating any user record or session |
| D1 database (user + session tables) | write | Server creates the anonymous `user` record and associated `session` record | The server returns HTTP 500 and the global error handler falls back to a generic JSON error message for the client |
| `@repo/i18n` | read | Rendering the upgrade banner text and sign-in button label | The UI falls back to the default English locale strings so the banner and button remain readable but untranslated for non-English users |

## Behavioral Flow

1. **[User]** → arrives at `/signin` and sees a localized "Continue as guest" option displayed alongside the standard email and passkey sign-in methods
2. **[User]** → clicks the "Continue as guest" button, and the client calls `authClient.signIn.anonymous()` with no additional input — no email, no credentials, no verification step required
3. **[Better Auth server handler]** → creates a new `user` record with `isAnonymous` set to `true` and assigns an auto-generated email in the format `anon-{uuid}@anon.docodego.com` to satisfy the email uniqueness constraint without requiring real contact information
4. **[Better Auth server handler]** → creates a full `session` record in the `session` table with all standard fields including signed token cookie, `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days from the current timestamp
5. **[Better Auth server handler]** → sets the `docodego_authed` hint cookie on the response so that Astro pages recognize the user as authenticated, then returns HTTP 200
6. **[Client]** → receives the 200 response, detects the `docodego_authed` hint cookie is present, and redirects the guest to `/app`
7. **[Client]** → the guest can browse and interact with the application as a logged-in user, with a persistent localized banner displayed encouraging the guest to create a full account by linking a real email address
8. **[Client]** → the upgrade banner remains visible throughout the guest's session on every page under `/app/*` to remind them that their activity can be preserved by upgrading — until they upgrade, the guest account functions like any other account but is flagged as anonymous in the system

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| Unauthenticated visitor on `/signin` | Authenticated anonymous user on `/app` | User clicks "Continue as guest" and the server returns HTTP 200 with session cookies | The server successfully creates both the `user` and `session` records in D1 |
| Authenticated anonymous user | Authenticated full user (banner removed) | User completes the account upgrade flow defined in `guest-upgrades-to-full-account.md` | The `isAnonymous` flag is set to false and a verified email is linked to the account |

## Business Rules

- **Rule anonymous-email-format:** IF the user initiates guest sign-in THEN the server generates an email matching `anon-{uuid}@anon.docodego.com` where the UUID is a freshly generated v4 UUID that satisfies the unique constraint on `user.email`
- **Rule session-parity:** IF the user is anonymous (`isAnonymous` = true) THEN the session `expiresAt` value uses the identical 7-day offset as full accounts, with 0 difference in session duration
- **Rule upgrade-banner-visibility:** IF `user.isAnonymous` equals true THEN the upgrade banner is rendered and visible on every page under `/app/*`, and IF `user.isAnonymous` equals false THEN the banner element is absent from the DOM
- **Rule banner-persistence:** IF the user is anonymous THEN the upgrade banner has 0 close or dismiss buttons and remains visible until the user upgrades to a full account

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Anonymous guest (`isAnonymous` = true) | Access all authenticated routes under `/app/*`, create and read own resources, use the full application UI | Create organizations, invite members, or perform actions requiring a verified email address — server returns HTTP 403 | The upgrade banner is visible on every page; the auto-generated `anon-{uuid}` email is never displayed in the UI |
| Authenticated full user (`isAnonymous` = false) | Access all authenticated routes, create organizations, invite members, perform all actions | N/A (route-level restrictions defined in route-specific specs) | The upgrade banner is absent from the DOM; full account email is displayed in profile settings |

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

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user clicks "Continue as guest" while already authenticated with an existing non-anonymous session cookie present in the browser | The client detects the existing session and redirects to `/app` without creating a duplicate anonymous account, preserving the current session | The user table contains 0 new anonymous records and the session cookie remains unchanged after the click |
| The user opens 2 browser tabs on `/signin` and clicks "Continue as guest" in both tabs within 1 second of each other | Each tab creates a separate anonymous user record with a distinct UUID-based email, and each tab receives its own session cookie with no conflict | The user table contains 2 distinct anonymous records and both tabs redirect to `/app` independently |
| The user has JavaScript disabled in the browser when the `/signin` page loads and the "Continue as guest" button is rendered | The button is non-functional because `authClient.signIn.anonymous()` requires JavaScript to execute the API call | The page displays the button but clicking it produces no navigation and the user remains on `/signin` |
| The server generates a UUID that matches an existing anonymous email in the `user` table, triggering a unique constraint violation on insert | The server catches the constraint error and retries the insert with a newly generated UUID, up to 3 times, logging each collision attempt before returning HTTP 500 if all retries fail | The server logs contain the collision retry entries and the final response is either HTTP 200 with a new UUID or HTTP 500 after 3 failures |

## Failure Modes

- **UUID collision on auto-generated email causes a unique constraint violation that prevents the anonymous user record from being inserted into the database**
    - **What happens:** The server generates an anonymous email `anon-{uuid}@anon.docodego.com` that collides with an existing user email in the `user` table, causing a unique constraint violation on the database insert operation.
    - **Source:** Statistically improbable UUID collision or a bug in the UUID generation logic that produces duplicate values across separate sign-in requests.
    - **Consequence:** The anonymous user record fails to insert into the database, and the guest sign-in flow cannot complete, leaving the user stuck on the `/signin` page.
    - **Recovery:** The server catches the constraint error and retries the insert with a newly generated UUID up to 3 times, logging each collision attempt for diagnostics. If all 3 retries fail, the server returns error HTTP 500 with a diagnostic message and the user can retry the sign-in manually.
- **Anonymous guest user attempts to access a restricted organization feature that requires a verified email address to proceed**
    - **What happens:** A guest attempts to perform an organization action such as creating an org or inviting a member that requires a verified email address, but the guest has only an auto-generated anonymous email.
    - **Source:** The guest navigates to an organization management page and submits a form that triggers a server-side permission check against the `isAnonymous` flag.
    - **Consequence:** The organization action cannot proceed because the server rejects requests from anonymous users for operations requiring verified email addresses, blocking the guest from completing the action.
    - **Recovery:** The server checks `user.isAnonymous` before processing the request, and if the value equals true, the server rejects the request and returns error HTTP 403 with a localized message notifying the user to upgrade to a full account first.
- **Session cookie not set due to a network interruption that drops the HTTP response before headers are fully transmitted to the client**
    - **What happens:** The server creates the anonymous user record and session successfully, but the HTTP response fails to deliver the `Set-Cookie` header to the client because the connection drops mid-response before headers are fully transmitted.
    - **Source:** Network instability between the Cloudflare Worker edge and the client device, such as a mobile user losing connectivity during the response transfer.
    - **Consequence:** The client never receives the session cookies, so it cannot authenticate subsequent requests and the user remains stuck on the `/signin` page without access to `/app`.
    - **Recovery:** The client detects the absent `docodego_authed` hint cookie and falls back to remaining on the `/signin` page without redirecting, allowing the user to retry the guest sign-in. The orphaned server-side session record expires naturally after the 7-day timeout period.
- **Upgrade banner not rendering for anonymous user because a code change removes the component or breaks the isAnonymous conditional check**
    - **What happens:** A code change inadvertently removes the upgrade banner component or breaks the `isAnonymous` conditional check, causing anonymous users to browse the application without seeing the upgrade prompt on any page.
    - **Source:** A developer modifies the application shell layout or the user context provider and removes or breaks the banner rendering logic during a refactor.
    - **Consequence:** Anonymous users have no visible indication that their account is temporary, reducing the likelihood of voluntary account upgrades and increasing orphaned anonymous records.
    - **Recovery:** The CI test suite includes a test that renders the application shell with `user.isAnonymous` = true and asserts the upgrade banner element is present in the DOM — CI alerts and blocks deployment if the assertion fails, preventing the regression from reaching production.

## Declared Omissions

- This specification does not address the guest-to-full-account upgrade flow, which is covered separately in `guest-upgrades-to-full-account.md`
- This specification does not address guest account deletion or cleanup of orphaned anonymous records, which is covered in `guest-deletes-anonymous-account.md`
- This specification does not address organization and team restrictions for anonymous users beyond the HTTP 403 rejection, which is covered in org behavioral specs
- This specification does not address mobile-specific guest sign-in behavior or native app session handling, which is covered in `user-signs-in-on-mobile.md`
- This specification does not address rate limiting on the anonymous sign-in endpoint to prevent automated account creation abuse

## Related Specifications

- [guest-upgrades-to-full-account](guest-upgrades-to-full-account.md) — defines the flow for converting an anonymous guest account to a full account by linking a verified email address
- [guest-deletes-anonymous-account](guest-deletes-anonymous-account.md) — defines the deletion and cleanup process for anonymous user records and their associated session data
- [auth-server-config](../foundation/auth-server-config.md) — defines the Better Auth server configuration including the anonymous plugin that powers the guest sign-in endpoint
- [database-schema](../foundation/database-schema.md) — defines the `user` and `session` table schemas including the `isAnonymous` column and email uniqueness constraint
- [shared-i18n](../foundation/shared-i18n.md) — defines the i18n infrastructure providing translation keys used by the upgrade banner and sign-in button labels

---
id: SPEC-2026-065
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Revokes User Sessions

## Intent

This spec defines the flow by which an app admin navigates to the user
management section of the admin dashboard, locates a target user, opens
their profile detail view, and clicks the "Sessions" tab to review that
user's active sessions. The sessions section loads by calling
`authClient.admin.listUserSessions({ userId })` and displays a table
showing each session's IP address, user agent (browser and operating
system), and the date and time the session was last active. The admin
can revoke an individual session by clicking the "Revoke" button on a
specific row, which calls
`authClient.admin.revokeUserSession({ sessionToken })` to invalidate
that single session, or can revoke all sessions at once by clicking
"Revoke all sessions", which calls
`authClient.admin.revokeUserSessions({ userId })` to invalidate every
active session belonging to that user. Unlike banning, revoking
sessions does not prevent the user from signing back in — it forces
re-authentication, which is the correct response when credentials are
potentially compromised but the user themselves is not at fault. Each
revocation action — whether individual or bulk — is recorded in the
audit log with the admin's identity, the affected user's identity,
whether it was a single or bulk revocation, and the UTC timestamp.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.listUserSessions()` endpoint | read | The app admin opens the "Sessions" tab on a user's profile detail view, triggering a query to fetch all active sessions belonging to that user from the server | The client receives an error response and displays a localized error message via Sonner — the sessions table remains empty and the admin retries after the endpoint recovers |
| `authClient.admin.revokeUserSession()` endpoint | write | The app admin clicks the "Revoke" button on a specific session row to invalidate that single session, sending the session token to the server for deletion | The client receives an error response and displays a localized error toast via Sonner — the targeted session remains active and the admin retries after the endpoint recovers |
| `authClient.admin.revokeUserSessions()` endpoint | write | The app admin clicks the "Revoke all sessions" button to invalidate every active session belonging to the target user at once, sending the user ID to the server | The client receives an error response and displays a localized error toast via Sonner — all sessions remain active and the admin retries after the endpoint recovers |
| `session` table (D1) | read/delete | The list endpoint reads active session rows for the target user, and the revoke endpoints delete one or all session rows belonging to that user from the database | The session list fails to load and returns HTTP 500 for reads, or the revoke mutation rejects with HTTP 500 for deletes — existing sessions remain unchanged until D1 recovers |
| Audit log | write | After each revocation succeeds — whether individual or bulk — the server writes an audit entry capturing the admin's user ID, the affected user's ID, the revocation type (single or bulk), and the UTC timestamp | Audit log write fails and the server logs the failure — the revocation itself is already committed and the session is invalidated, so enforcement continues even without the audit entry |
| `@repo/i18n` | read | All column headers, button labels, empty state text, confirmation dialog text, toast messages, and error messages in the sessions view are rendered via translation keys at component mount time | Translation function falls back to the default English locale strings so the sessions view and all feedback messages remain fully usable and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[App Admin]** navigates to the user management section of the
    admin dashboard, which displays a paginated list of all registered
    users with their current status, role, and account details

2. **[App Admin]** searches for or scrolls to the specific user whose
    sessions they need to review, using the search field to filter by
    name or email, then selects that user to open their profile detail
    view

3. **[App Admin]** clicks on the "Sessions" tab within the target
    user's profile detail view to view the user's active sessions,
    triggering the client to fetch session data from the server

4. **[Client]** calls `authClient.admin.listUserSessions({ userId })`
    with the target user's ID to retrieve all active sessions belonging
    to that user from the server's session store

5. **[Server]** verifies that the calling user's `user.role` field
    equals `"admin"` — if the caller does not hold the app admin role,
    the server rejects the request with HTTP 403 and returns no session
    data to the client

6. **[Server]** queries the `session` table for all active session
    rows belonging to the target user and returns the result set
    containing each session's token, IP address, user agent string, and
    last active timestamp

7. **[Client]** renders the sessions data as a table with localized
    column headers — each row displays the session's IP address, the
    user agent (browser and operating system), the last active date and
    time, and a "Revoke" action button

8. **[Client]** renders a "Revoke all sessions" button above or below
    the sessions table, visible only when the table contains at least
    one active session row, enabling bulk revocation of every session
    at once

9. **[Branch — individual revoke]** **[App Admin]** clicks the
    "Revoke" button on a specific session row to terminate that single
    session, triggering a localized confirmation dialog that states the
    selected session will be invalidated immediately

10. **[App Admin]** confirms the individual revoke action in the
    confirmation dialog, and the client transitions the "Revoke" button
    to a loading state to prevent duplicate submissions while the
    request is in flight

11. **[Client]** calls
    `authClient.admin.revokeUserSession({ sessionToken })` with the
    session's token to invalidate that specific session on the server

12. **[Server]** verifies the caller holds the app admin role, then
    deletes the session row matching the provided token from the
    `session` table, immediately invalidating that session so the user
    is signed out on their next request from that device

13. **[Server]** writes an audit log entry capturing the admin's user
    ID, the affected user's user ID, the revocation type as "single",
    the revoked session's token identifier, and the UTC timestamp of
    the revocation action

14. **[Server]** returns HTTP 200 confirming that the individual
    session was revoked and the audit entry was recorded, and the
    client refreshes the sessions table to remove the revoked row

15. **[Client]** receives the success response, displays a localized
    confirmation toast via Sonner stating that the session has been
    revoked, and invalidates the TanStack Query cache for the session
    list to trigger a re-fetch

16. **[Branch — bulk revoke]** **[App Admin]** clicks the "Revoke all
    sessions" button to terminate every active session belonging to the
    target user, triggering a localized confirmation dialog that states
    all sessions will be invalidated immediately

17. **[App Admin]** confirms the bulk revoke action in the confirmation
    dialog, and the client transitions the "Revoke all sessions" button
    to a loading state to prevent duplicate submissions while the
    request is in flight

18. **[Client]** calls
    `authClient.admin.revokeUserSessions({ userId })` with the target
    user's ID to invalidate all active sessions belonging to that user

19. **[Server]** verifies the caller holds the app admin role, then
    deletes all session rows belonging to the target user from the
    `session` table, immediately invalidating every active session so
    the user is signed out on their next request from any device

20. **[Server]** writes an audit log entry capturing the admin's user
    ID, the affected user's user ID, the revocation type as "bulk",
    the count of sessions revoked, and the UTC timestamp of the bulk
    revocation action

21. **[Server]** returns HTTP 200 confirming that all sessions were
    revoked and the audit entry was recorded, and the client refreshes
    the sessions table to show an empty state

22. **[Client]** receives the success response, displays a localized
    confirmation toast via Sonner stating that all sessions have been
    revoked, and invalidates the TanStack Query cache for the session
    list to trigger a re-fetch showing the empty state

23. **[Branch — user impact]** The affected user's current browsing
    sessions fail on their very next API request because the sessions
    have been deleted — the client receives an authentication error
    and the user is redirected to the sign-in page, but the user is
    not banned and can sign in again immediately with valid credentials

24. **[Branch — network error]** If the revocation request fails due
    to a network error or timeout, the client displays a localized
    error toast via Sonner and re-enables the action button so the
    admin can retry the submission without refreshing the page

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| user_detail_idle | sessions_loading | App admin clicks the "Sessions" tab on the target user's profile detail view to load the user's active sessions | Calling user's `user.role` equals `"admin"` and the target user's profile detail view is open and visible |
| sessions_loading | sessions_loaded | Server returns the session list with HTTP 200 containing zero or more active session records for the target user | The `authClient.admin.listUserSessions()` call completes with a valid response containing the session array |
| sessions_loading | sessions_error | Server returns a non-200 error code or the request times out before the session list response is received from the server | Database query fails, authorization check fails, or a network error occurs during the list request |
| sessions_error | sessions_loading | App admin clicks a "Retry" button or re-opens the "Sessions" tab to attempt fetching the session list from the server again | The previous error has been displayed to the admin and the admin initiates a new fetch attempt |
| sessions_loaded | confirming_single_revoke | App admin clicks the "Revoke" button on a specific session row and the confirmation dialog appears for the individual revocation | At least one session row is present in the table and the admin clicked the "Revoke" button on a specific row |
| sessions_loaded | confirming_bulk_revoke | App admin clicks the "Revoke all sessions" button and the confirmation dialog appears for the bulk revocation action | At least one session row is present in the table and the admin clicked the "Revoke all sessions" button |
| confirming_single_revoke | submitting_single_revoke | App admin confirms the individual revocation in the confirmation dialog, triggering the revoke mutation request to the server | The admin clicked the confirm action in the dialog rather than cancelling or dismissing the dialog |
| confirming_single_revoke | sessions_loaded | App admin cancels or dismisses the individual revocation confirmation dialog without confirming the action | The admin clicked cancel or closed the dialog, returning to the sessions table with all rows intact |
| confirming_bulk_revoke | submitting_bulk_revoke | App admin confirms the bulk revocation in the confirmation dialog, triggering the revoke-all mutation request to the server | The admin clicked the confirm action in the dialog rather than cancelling or dismissing the dialog |
| confirming_bulk_revoke | sessions_loaded | App admin cancels or dismisses the bulk revocation confirmation dialog without confirming the action | The admin clicked cancel or closed the dialog, returning to the sessions table with all rows intact |
| submitting_single_revoke | revoke_success | Server returns HTTP 200 confirming the individual session was revoked and the audit log entry was written to the database | Server-side role check passes, the session row is deleted, and the audit log write completes |
| submitting_single_revoke | revoke_error | Server returns a non-200 error code or the request times out before a response is received from the server | Database delete fails, authorization check fails, or a network error occurs during the mutation request |
| submitting_bulk_revoke | revoke_success | Server returns HTTP 200 confirming all sessions were revoked and the audit log entry was written to the database | Server-side role check passes, all session rows are deleted, and the audit log write completes |
| submitting_bulk_revoke | revoke_error | Server returns a non-200 error code or the request times out before a response is received from the server | Database delete fails, authorization check fails, or a network error occurs during the mutation request |
| revoke_success | sessions_loaded | Client displays the success toast and the sessions table refreshes to reflect the updated session list from the re-fetched data | TanStack Query cache invalidation completes and the sessions table re-renders with the updated session list |
| revoke_error | sessions_loaded | Client displays the error toast and re-enables the action button so the admin can retry the revocation submission | Error message is visible via Sonner toast and the previously clicked action button is re-enabled for retry |

## Business Rules

- **Rule app-admin-role-required:** IF the authenticated user's
    `user.role` field does not equal `"admin"` THEN the
    `authClient.admin.listUserSessions()`,
    `authClient.admin.revokeUserSession()`, and
    `authClient.admin.revokeUserSessions()` endpoints reject the
    request with HTTP 403 AND the server logs the unauthorized attempt
    with the caller's user ID and timestamp before returning the error
- **Rule individual-vs-bulk-revocation:** IF the app admin clicks the
    "Revoke" button on a specific session row THEN only that single
    session is invalidated via
    `authClient.admin.revokeUserSession({ sessionToken })` and the
    remaining sessions stay active; IF the app admin clicks "Revoke all
    sessions" THEN every active session belonging to the target user is
    invalidated via
    `authClient.admin.revokeUserSessions({ userId })` in a single
    server-side operation
- **Rule revocation-does-not-block-sign-in:** IF the admin revokes one
    or all of a user's sessions THEN the user is signed out on their
    next API request for each invalidated session, but the user is not
    banned and can sign in again immediately with valid credentials —
    unlike the ban flow, session revocation does not set `user.banned`
    to `true` and does not prevent future authentication
- **Rule sign-out-on-next-request:** IF a session token has been
    deleted from the `session` table via either the individual or bulk
    revocation endpoint THEN the user's next API request using that
    session token fails authentication and the client receives an
    unauthorized error, redirecting the user to the sign-in page
- **Rule audit-distinguishes-single-vs-bulk:** IF the admin revokes a
    single session THEN the audit log entry records the revocation type
    as "single" with the specific session token identifier; IF the
    admin revokes all sessions THEN the audit log entry records the
    revocation type as "bulk" with the count of sessions that were
    invalidated in the operation

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin (managing another user's sessions) | View the user management list, search for users, open a user's profile detail view, click the "Sessions" tab, view the sessions table with IP address and user agent and last active timestamp, click "Revoke" on individual sessions, click "Revoke all sessions", and see success or error toasts | None — the app admin has full access to list and revoke any user's sessions through the admin dashboard, with all actions enforced by server-side role verification | The "Sessions" tab, sessions table, individual "Revoke" buttons, and "Revoke all sessions" button are all visible and interactive when the admin opens any user's profile detail view |
| Non-admin authenticated user | None — the admin user management page is not accessible to non-admin users and the route guard redirects or returns HTTP 403 before the page renders any content | Viewing the user management section, accessing any user's admin detail page, viewing the sessions tab, or calling any of the admin session endpoints, which reject with HTTP 403 | The admin user management page is not rendered; the user is redirected or shown a 403 error before any admin controls are mounted or visible |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the admin user management page component renders any content or loads any session data | Accessing the admin user management page, viewing session data, or calling any admin session endpoint without a valid authenticated session token | The admin page is not rendered; the redirect to `/signin` occurs before any page elements are mounted or any session data is fetched from the server |

## Constraints

- The `authClient.admin.listUserSessions()` endpoint enforces the app
    admin role server-side by reading the calling user's `user.role`
    field — the count of session listings returned to non-admin users
    equals 0
- The `authClient.admin.revokeUserSession()` endpoint enforces the app
    admin role server-side — the count of individual session revocations
    initiated by non-admin users equals 0
- The `authClient.admin.revokeUserSessions()` endpoint enforces the
    app admin role server-side — the count of bulk session revocations
    initiated by non-admin users equals 0
- All column headers, button labels, empty state text, confirmation
    dialog text, toast messages, and error messages in the sessions view
    are rendered via i18n translation keys — the count of hardcoded
    English string literals in the sessions view component equals 0
- The audit log entry is written after every revocation action and
    captures the admin's user ID, the affected user's user ID, the
    revocation type (single or bulk), and the UTC timestamp — the count
    of revocation operations that complete without a corresponding audit
    log write attempt equals 0
- The "Revoke all sessions" button is hidden or disabled when the
    sessions table contains zero active sessions — the count of bulk
    revocation requests dispatched when no sessions exist equals 0

## Acceptance Criteria

- [ ] Clicking the "Sessions" tab on a user's profile detail view calls `authClient.admin.listUserSessions({ userId })` — the API invocation count equals 1 and the sessions table renders with localized column headers for IP address, user agent, and last active timestamp
- [ ] Each session row displays the session's IP address, user agent string (browser and operating system), and the last active date and time — all three data fields are present and visible in every row
- [ ] Each session row contains a "Revoke" action button — the total count of visible "Revoke" buttons equals the number of active sessions returned by the list endpoint and each button is enabled
- [ ] Clicking "Revoke" on a specific session row triggers a localized confirmation dialog — the dialog element is present and visible before the revocation mutation is dispatched to the server
- [ ] After confirming the individual revoke, the client calls `authClient.admin.revokeUserSession({ sessionToken })` — the mutation invocation count equals 1 and the payload contains the correct session token
- [ ] On individual revocation success the server deletes the targeted session row from the `session` table — the count of session records matching that token equals 0 after the mutation
- [ ] On individual revocation success a localized confirmation toast appears via Sonner — the toast element is present and visible within 500ms of the API returning HTTP 200
- [ ] The "Revoke all sessions" button is visible only when the sessions table contains at least one active session — the button is absent or disabled when the session count equals 0
- [ ] Clicking "Revoke all sessions" triggers a localized confirmation dialog — the dialog element is present and visible before the bulk revocation mutation is dispatched to the server
- [ ] After confirming the bulk revoke, the client calls `authClient.admin.revokeUserSessions({ userId })` — the mutation invocation count equals 1 and the payload contains the correct user ID
- [ ] On bulk revocation success the server deletes all session rows belonging to the target user — the count of session records for that user ID in the `session` table equals 0 after the mutation
- [ ] On bulk revocation success the sessions table refreshes to show an empty state with a localized message indicating no active sessions exist for the target user
- [ ] A non-admin authenticated user calling any of the admin session endpoints directly receives HTTP 403 — the response status equals 403 and no session data is returned or modified
- [ ] The audit log contains an entry for each revocation action with the admin's user ID, the affected user's user ID, the revocation type (single or bulk), and the UTC timestamp — all four fields are present and non-null
- [ ] After session revocation the affected user can sign in again with valid credentials — the sign-in endpoint returns HTTP 200, a new session row is present in the `session` table, and `user.banned` equals `false`

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| App admin opens the "Sessions" tab for a user who has zero active sessions in the database | The sessions table renders an empty state with a localized message indicating no active sessions exist — the "Revoke all sessions" button is hidden or disabled because there are no sessions to revoke | The sessions table row count equals 0 and the "Revoke all sessions" button is absent or has the disabled attribute present |
| App admin revokes the last remaining active session for a user using the individual "Revoke" button on that single row | The session is deleted and the sessions table transitions to the empty state — the "Revoke all sessions" button becomes hidden or disabled because no sessions remain after the revocation | The session row count equals 0 after the mutation and the empty state message is visible in the sessions table |
| App admin opens the sessions tab and then the user creates a new session by signing in on another device before the admin clicks revoke | The sessions table shows stale data until the admin refreshes — clicking "Revoke all sessions" revokes the sessions known at the time of the last fetch, and the new session persists until the admin re-fetches the list | The bulk revocation deletes the session rows returned by the most recent list call and the new session remains active in the database |
| Two app admins attempt to revoke the same individual session simultaneously from different browser sessions | The first revocation succeeds and the second receives an error or a no-op response because the session row has already been deleted from the database by the first request | One request returns HTTP 200 and the other returns an error or HTTP 200 with zero rows affected, and the session table contains zero rows for that token |
| App admin clicks "Revoke all sessions" for a user who has 100 or more active sessions in the session table simultaneously | The server processes the bulk deletion in a single database operation rather than iterating row-by-row — all 100 sessions are deleted and the audit log records the bulk revocation with the total count of sessions invalidated | All session rows for the target user are deleted from the `session` table and the audit log entry's session count field equals the number that was present before the operation |
| The server successfully deletes session rows but the audit log write fails due to a transient D1 error after the revocation completes | The revocation is enforced and the sessions are invalidated, but no audit trail exists for this specific revocation action — the server logs the audit write failure for administrative review | The target session rows are absent from the `session` table and a warning log entry is present for the failed audit log write operation |

## Failure Modes

- **Database query fails when listing the target user's active sessions from the session table**
    - **What happens:** The app admin clicks the "Sessions" tab and the
        client sends the `authClient.admin.listUserSessions()` request,
        but the D1 database query fails due to a transient storage error
        before the session rows are read, leaving the sessions table
        empty with no data to display.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        read query that fetches active session rows for the target user.
    - **Consequence:** The app admin cannot see the user's active
        sessions and cannot make informed decisions about which sessions
        to revoke, blocking the entire revocation workflow until the
        database recovers.
    - **Recovery:** The server returns HTTP 500 and the client displays
        a localized error message via Sonner — the admin retries by
        re-opening the "Sessions" tab once D1 recovers, and the empty
        sessions table shows a retry action.
- **Session deletion fails when revoking an individual session from the session table**
    - **What happens:** The app admin confirms the individual revocation
        and the client sends the
        `authClient.admin.revokeUserSession({ sessionToken })` request,
        but the D1 database delete fails due to a transient storage
        error before the session row is removed, leaving that session
        active and the user still signed in on that device.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        single-row delete that removes the targeted session from the
        `session` table.
    - **Consequence:** The targeted session remains active and the user
        continues to be signed in on that device, and no audit log entry
        is created because the entire operation failed before any state
        change was committed to the database.
    - **Recovery:** The server returns HTTP 500 and the client displays
        a localized error toast via Sonner — the admin retries the
        individual revocation once D1 recovers and the "Revoke" button
        is re-enabled for another submission attempt.
- **Bulk session deletion fails when revoking all sessions for the target user**
    - **What happens:** The app admin confirms the bulk revocation and
        the client sends the
        `authClient.admin.revokeUserSessions({ userId })` request, but
        the D1 database delete fails due to a transient storage error
        before any session rows are removed, leaving all sessions active
        and the user still signed in on every device.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        bulk delete operation that removes all session rows belonging to
        the target user from the `session` table.
    - **Consequence:** All sessions remain active and the user continues
        to be signed in on every device, and no audit log entry is
        created because the entire operation failed before any state
        change was committed to the database.
    - **Recovery:** The server returns HTTP 500 and the client displays
        a localized error toast via Sonner — the admin retries the bulk
        revocation once D1 recovers and the "Revoke all sessions" button
        is re-enabled for another submission attempt.
- **Non-admin user bypasses the client guard and calls the admin session endpoints directly**
    - **What happens:** A user without the app admin role crafts a
        direct HTTP request to the
        `authClient.admin.revokeUserSession()` or
        `authClient.admin.revokeUserSessions()` endpoint using a valid
        session cookie, bypassing the client-side UI that hides admin
        controls from non-admin users.
    - **Source:** Adversarial action where a non-admin user sends a
        hand-crafted HTTP request to the admin session revocation
        endpoint with a valid session token, circumventing the
        client-side visibility guard that conditionally renders admin
        controls only for users with `user.role` equal to `"admin"`.
    - **Consequence:** Without server-side enforcement any authenticated
        user could revoke another user's sessions, disrupting their
        access across devices and creating false administrative records
        in the audit log, undermining the security trust boundary.
    - **Recovery:** The mutation handler rejects the request with
        HTTP 403 after verifying the calling user's `user.role` field
        in the `user` table — the server logs the unauthorized attempt
        with the caller's user ID and timestamp, and no session rows
        are deleted from the database.

## Declared Omissions

- This specification does not address the user's own self-service
    session management workflow — that behavior is fully defined in
    the separate `user-manages-sessions.md` specification covering the
    user's personal session list and revocation controls
- This specification does not address the banning workflow that also
    invalidates sessions as a side effect — that behavior is fully
    defined in the separate `app-admin-bans-a-user.md` specification
    covering ban form configuration and session invalidation on ban
- This specification does not address rate limiting on the admin
    session revocation endpoints — that behavior is enforced by the
    global rate limiter defined in `api-framework.md` covering all
    mutation endpoints uniformly across the API layer
- This specification does not address session creation or renewal
    lifecycle — that behavior is fully defined in the separate
    `session-lifecycle.md` specification covering how sessions are
    created, refreshed, and expire in the `session` table
- This specification does not address the content or format of the
    audit log storage schema — audit log structure and retention
    policies are defined separately from this admin action flow and
    apply uniformly to all administrative operations

## Related Specifications

- [user-manages-sessions](user-manages-sessions.md) — Defines the
    user's own self-service session management workflow where users can
    view and revoke their own sessions, in contrast to this admin-level
    session revocation flow that operates on any user's sessions
- [app-admin-bans-a-user](app-admin-bans-a-user.md) — Defines the
    ban workflow that also invalidates all sessions as a side effect of
    banning, but additionally prevents future sign-in by setting
    `user.banned` to `true`, unlike this revocation-only flow
- [app-admin-lists-and-searches-users](app-admin-lists-and-searches-users.md)
    — Admin user management list and search flow that provides the entry
    point for locating and selecting the target user before navigating
    to their sessions tab in the profile detail view
- [session-lifecycle](session-lifecycle.md) — Session creation and
    expiration lifecycle that governs the session rows read and deleted
    during this flow's list and revocation operations, defining how
    sessions are stored and managed in the `session` table
- [auth-server-config](../foundation/auth-server-config.md) — Better
    Auth server configuration including the admin plugin that validates
    the `user.role` field and exposes the admin session management
    endpoints used by this specification's list and revocation flows

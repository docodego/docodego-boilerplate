---
id: SPEC-2026-059
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Bans a User

## Intent

This spec defines the flow by which an app admin navigates to the user
management section of the admin dashboard, locates a target user, opens
their profile detail view, and initiates a ban action by clicking the
"Ban" button. The admin fills out a ban configuration form that includes
an optional free-text reason field and an optional expiration date picker
— leaving the expiration date empty creates a permanent ban, while
setting a date creates a temporary ban that lifts automatically when
that date arrives. On confirmation, the client calls
`authClient.admin.banUser({ userId, banReason, banExpires })` and the
server verifies the caller holds the app admin role (`user.role =
"admin"`) before updating the target user's record: `user.banned` is
set to `true`, `user.banReason` stores the admin-provided text, and
`user.banExpires` is set to the chosen date or `null` for a permanent
ban. The server then invalidates all active sessions belonging to the
banned user, forcing immediate sign-out on the user's next API request.
The entire action is recorded in the audit log with the admin's identity,
the banned user's identity, the reason, the expiration setting, and the
timestamp, creating a clear accountability trail for moderation actions.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.banUser()` endpoint | write | App admin clicks the Confirm button on the ban configuration form after filling in the optional reason and expiration fields, sending the ban mutation to the server | The client receives an error response and displays a localized error toast via Sonner — the target user's record remains unchanged and the admin retries after the endpoint recovers |
| `user` table (D1) | read/write | The user management page loads user records for listing and search, and the ban mutation writes `user.banned`, `user.banReason`, and `user.banExpires` to the target user's row | The user list fails to load and returns HTTP 500, and the ban mutation rejects with HTTP 500 so the target user's record remains unchanged in the database until D1 recovers |
| `session` table (D1) | delete | After the ban mutation updates the user record, the server deletes all active session rows belonging to the banned user to force immediate sign-out | Session deletion fails and the server logs the failure — the ban is still recorded on the user record but the banned user's existing sessions remain active until they expire naturally or are cleaned up |
| Audit log | write | After the ban mutation succeeds, the server writes an audit entry capturing the admin's user ID, the banned user's ID, the ban reason, the expiration setting, and the UTC timestamp | Audit log write fails and the server logs the failure — the ban itself is already committed to the user record and session invalidation has already completed, so the ban is enforced even without the audit entry |
| `@repo/i18n` | read | All form labels, button text, placeholder text, date picker labels, confirmation dialog text, toast messages, and error messages on the ban form are rendered via translation keys at component mount time | Translation function falls back to the default English locale strings so the ban form and all feedback messages remain fully usable and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[App Admin]** navigates to the user management section of the
    admin dashboard, which displays a paginated list of all registered
    users with their current status, role, and account details

2. **[App Admin]** searches for or scrolls to the specific user they
    intend to ban, using the search field to filter by name or email,
    then selects that user to open their profile detail view

3. **[App Admin]** clicks the "Ban" action button on the target user's
    profile detail view, which opens a ban configuration form as a
    modal or inline panel with localized field labels

4. **[Client]** renders the ban configuration form with two optional
    fields: a free-text reason field where the admin describes why the
    user is being banned, and a date picker for setting an expiration
    date on the ban

5. **[App Admin]** optionally enters a ban reason in the free-text
    field describing the justification for the ban action, such as
    "Repeated violation of community guidelines" or a similar
    explanation for the moderation decision

6. **[App Admin]** optionally selects an expiration date using the
    date picker — setting a date creates a temporary ban that lifts
    automatically when that date arrives, and leaving the date picker
    empty creates a permanent ban that remains until manually removed

7. **[Client]** validates the expiration date if one is provided —
    the date is rejected if it is in the past, and a localized
    validation error message is displayed inline next to the date
    picker field until the admin selects a future date

8. **[App Admin]** clicks the Confirm button to submit the ban,
    triggering a localized confirmation dialog that states the target
    user will be banned and all their active sessions will be
    terminated immediately upon confirmation

9. **[App Admin]** confirms the action in the confirmation dialog,
    and the client transitions the Confirm button to a loading state
    while the request is in flight, preventing duplicate submissions

10. **[Client]** calls `authClient.admin.banUser({ userId, banReason,
    banExpires })` with the target user's ID, the optional reason
    text (or `null` if left empty), and the optional expiration date
    (or `null` if left empty for a permanent ban)

11. **[Server]** verifies that the calling user's `user.role` field
    equals `"admin"` — if the caller does not hold the app admin role,
    the server rejects the request with HTTP 403 and no changes are
    written to the target user's record in the database

12. **[Server]** updates the target user's record in the `user` table:
    `user.banned` is set to `true`, `user.banReason` is set to the
    admin-provided text or `null`, and `user.banExpires` is set to
    the chosen expiration date or `null` for a permanent ban

13. **[Server]** deletes all active session rows in the `session`
    table that belong to the banned user, invalidating every active
    session so the user is effectively signed out on their very next
    API request across all devices and browsers

14. **[Server]** writes an audit log entry capturing the app admin's
    user ID, the banned user's user ID, the ban reason, the
    expiration setting (date or permanent), and the UTC timestamp of
    the ban action for accountability and moderation review

15. **[Server]** returns HTTP 200 confirming that the ban was applied,
    the sessions were invalidated, and the audit entry was recorded
    successfully

16. **[Client]** receives the success response, displays a localized
    confirmation toast via Sonner stating that the user has been
    banned, and invalidates the TanStack Query cache for the target
    user's data to trigger a re-fetch of the updated profile

17. **[Client]** refreshes the target user's detail view to reflect
    the new banned status — the user's status indicator changes to
    "banned" and the "Ban" button is replaced with an "Unban" button

18. **[Branch — banned user's next request]** The banned user's
    current browsing session fails on their very next API request
    because all sessions have been deleted — the client receives an
    authentication error and the user is effectively signed out and
    redirected to the landing page

19. **[Branch — banned user tries to sign in]** If the banned user
    attempts to sign in again, the sign-in flow checks `user.banned`
    and rejects the attempt, displaying a localized ban error message
    that includes the ban reason if one was provided by the admin

20. **[Branch — network error]** If the ban mutation request fails
    due to a network error or timeout, the client displays a generic
    localized error toast via Sonner and re-enables the Confirm
    button so the admin can retry the submission

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| user_detail_idle | ban_form_open | App admin clicks the "Ban" action button on the target user's profile detail view to initiate the ban workflow | Calling user's `user.role` equals `"admin"` and the target user is not already banned (`user.banned` equals `false`) |
| ban_form_open | ban_form_filled | App admin enters a reason, selects an expiration date, or modifies any field in the ban configuration form | At least one interaction with the ban form has occurred, even if both optional fields remain empty |
| ban_form_filled | confirming | App admin clicks the Confirm button and the confirmation dialog appears asking the admin to verify the ban action | Client-side validation passes — if an expiration date is provided, it is a valid future date |
| confirming | submitting | App admin confirms the action in the confirmation dialog, triggering the mutation request to the server | The admin clicked the confirm action in the dialog rather than cancelling or dismissing the dialog |
| confirming | ban_form_filled | App admin cancels or dismisses the confirmation dialog without confirming the ban action | The admin clicked cancel or closed the dialog, returning to the form with all field values intact |
| submitting | ban_success | Server returns HTTP 200 confirming the ban was applied, sessions were invalidated, and the audit log entry was written | Server-side role check passes and the database writes for ban fields, session deletion, and audit log all complete |
| submitting | ban_error | Server returns a non-200 error code or the request times out before a response is received from the server | Database write fails, authorization check fails, or a network error occurs during the mutation request |
| ban_success | user_detail_idle | Client displays the success toast and the target user's detail view refreshes to show the banned status and the "Unban" button | TanStack Query cache invalidation completes and the detail view re-renders with the updated ban status from the re-fetched data |
| ban_error | ban_form_filled | Client displays the error toast and the ban form retains the admin's entries for correction and retry of the ban submission | Error message is visible via Sonner toast and the Confirm button is re-enabled with the previously entered reason and expiration values intact |

## Business Rules

- **Rule app-admin-role-required:** IF the authenticated user's
    `user.role` field does not equal `"admin"` THEN the
    `authClient.admin.banUser()` endpoint rejects the request with
    HTTP 403 AND the server logs the unauthorized attempt with the
    caller's user ID and timestamp before returning the error response
- **Rule temporary-vs-permanent-ban:** IF the app admin provides an
    expiration date in the `banExpires` field THEN the ban is temporary
    and lifts automatically when the current UTC time exceeds the
    expiration date; IF the admin leaves `banExpires` as `null` THEN
    the ban is permanent and remains in effect until an app admin
    manually unbans the user through the unban flow
- **Rule session-invalidation-on-ban:** IF the server successfully
    sets `user.banned` to `true` on the target user's record THEN the
    server deletes all active session rows belonging to that user from
    the `session` table so the banned user is signed out on their very
    next API request across all devices and browsers
- **Rule sign-in-rejection-while-banned:** IF a user with
    `user.banned` equal to `true` attempts to sign in AND the ban has
    not expired (either `banExpires` is `null` or the current UTC time
    is less than or equal to `banExpires`) THEN the sign-in flow
    rejects the attempt without creating a session and displays a
    localized ban error screen
- **Rule ban-reason-included-in-error:** IF the server's ban
    rejection response includes a non-null `banReason` field THEN the
    ban error screen displays the admin-provided reason text to the
    banned user; IF `banReason` is `null` THEN the ban error screen
    displays a generic default ban message without a specific reason

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin (banning another user) | View the user management list, search for users, open a user's profile detail view, click the "Ban" button, fill out the ban form with optional reason and expiration, confirm the ban action, and see the success or error toast | Banning their own admin account — the "Ban" button is hidden or disabled with a localized tooltip when the target user ID equals the admin's own user ID to prevent self-banning | The "Ban" button, ban form, confirmation dialog, and toast messages are all visible and interactive when the target user is not the admin themselves and is not already banned |
| Non-admin authenticated user | None — the admin user management page is not accessible to non-admin users and the route guard redirects or returns HTTP 403 before the page renders any content | Viewing the user management section, accessing any user's admin detail page, or calling the `authClient.admin.banUser()` endpoint, which rejects with HTTP 403 | The admin user management page is not rendered; the user is redirected or shown a 403 error before any admin controls are mounted or visible |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the admin user management page component renders any content or loads any user data | Accessing the admin user management page or calling the `authClient.admin.banUser()` endpoint without a valid authenticated session token | The admin page is not rendered; the redirect to `/signin` occurs before any page elements are mounted or any user data is fetched from the server |

## Constraints

- The `authClient.admin.banUser()` mutation endpoint enforces the
    app admin role server-side by reading the calling user's `user.role`
    field — the count of successful ban operations initiated by
    non-admin users equals 0
- The ban expiration date, when provided, is validated to be a future
    UTC timestamp — the client rejects past dates with a localized
    validation error and the count of ban mutations submitted with a
    past expiration date equals 0
- Session invalidation occurs within the same server-side transaction
    or sequence as the ban record update — the count of active session
    rows belonging to the banned user after the ban mutation completes
    equals 0 when the session deletion succeeds
- All form labels, button text, confirmation dialog text, date picker
    labels, placeholder text, toast messages, and error messages on the
    ban form are rendered via i18n translation keys — the count of
    hardcoded English string literals in the ban form component equals 0
- The audit log entry is written after every ban action and captures
    the admin's user ID, the banned user's user ID, the ban reason, the
    expiration setting, and the UTC timestamp — the count of ban
    mutations that complete without a corresponding audit log write
    attempt equals 0
- The "Ban" button is hidden or disabled when the target user is
    already banned (`user.banned` equals `true`) — the count of
    duplicate ban mutations dispatched for an already-banned user from
    the UI equals 0

## Acceptance Criteria

- [ ] Clicking "Ban" on a non-banned user's detail page opens a ban configuration form with a free-text reason field and a date picker — both fields are present and rendered with localized labels
- [ ] The ban reason field accepts free-text input and is optional — the form can be submitted with the reason field empty and the `banReason` parameter is sent as `null`
- [ ] The expiration date picker is optional — the form can be submitted with no expiration date selected and the `banExpires` parameter equals `null` in the mutation payload for a permanent ban
- [ ] Selecting a past date in the expiration date picker displays a localized validation error inline — the Confirm button remains disabled and the count of mutation requests dispatched equals 0
- [ ] Clicking Confirm triggers a localized confirmation dialog that explicitly states the user will be banned and all active sessions will be terminated — the dialog is present and visible before the mutation is dispatched
- [ ] After confirming, the client calls `authClient.admin.banUser({ userId, banReason, banExpires })` — the mutation invocation count equals 1 and the payload contains the correct user ID, reason, and expiration values
- [ ] The Confirm button transitions to a loading state while the mutation is in flight — the button shows a loading indicator and the count of additional mutation requests dispatched during this state equals 0
- [ ] On mutation success the server sets `user.banned` to `true`, `user.banReason` to the provided text or `null`, and `user.banExpires` to the provided date or `null` — all three fields are present on the target user's record after the mutation
- [ ] On mutation success the server deletes all active session rows belonging to the banned user — the count of session records for the banned user's ID in the `session` table equals 0 after the mutation
- [ ] On mutation success a localized confirmation toast appears via Sonner — the toast element is present and visible within 500ms of the API returning HTTP 200
- [ ] On mutation success the target user's detail view refreshes to show the banned status — the status indicator text equals "banned" and the count of visible "Ban" button elements equals 0 while the "Unban" button is present
- [ ] On mutation failure due to a network error the client displays a localized error toast — the toast element is present and the Confirm button returns to its interactive state for retry
- [ ] A non-admin authenticated user calling `authClient.admin.banUser()` directly receives HTTP 403 — the response status equals 403 and the target user's `user.banned` field remains `false`
- [ ] The audit log contains an entry for the ban action with the admin's user ID, the banned user's user ID, the ban reason, the expiration setting, and the UTC timestamp — all five fields are present and non-null (except banReason and banExpires which are nullable)
- [ ] All text on the ban form, confirmation dialog, and toast messages is rendered via i18n translation keys — the count of hardcoded English strings in the ban form component equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| App admin attempts to ban a user who is already banned with `user.banned` equal to `true` in the database | The "Ban" button is hidden or disabled on the target user's detail page because the user is already banned — the admin sees the "Unban" button instead and no duplicate ban mutation is dispatched | The "Ban" button disabled attribute is present or the element is absent, and the network request count to the `authClient.admin.banUser()` endpoint equals 0 |
| App admin sets an expiration date that is exactly one minute in the future and submits the ban form immediately | The ban is accepted because the expiration date is in the future at the time of submission — the ban remains active for approximately one minute and then expires automatically when the server evaluates the ban check | The mutation returns HTTP 200 and the `user.banExpires` field is set to the near-future timestamp, and the ban check fails to reject sign-in after the expiration time passes |
| App admin opens the ban form but navigates away from the detail page before clicking Confirm to submit the ban | No mutation request is sent because the admin did not confirm the ban — the target user's record in the `user` table remains unchanged and no sessions are invalidated | The network request count to the `authClient.admin.banUser()` endpoint equals 0 and the target user's `user.banned` field remains at its original value |
| Two app admins attempt to ban the same user simultaneously from different browser sessions at the same moment | The last mutation to complete wins at the database level — both mutations set `user.banned` to `true` with potentially different reasons or expiration dates, and the final values reflect whichever write was persisted last | Both mutations return HTTP 200 and the target user's ban fields in the `user` table equal the values from the last successfully processed request |
| App admin attempts to ban their own admin account by manipulating the client or sending a direct API request with their own user ID | The server rejects the self-ban attempt because an admin cannot ban themselves — the endpoint returns HTTP 400 and the target user's record remains unchanged in the database | The response status equals 400 and the admin's `user.banned` field remains `false` with no sessions invalidated |
| The server successfully updates `user.banned` to `true` but the session deletion query fails due to a transient D1 error before any session rows are removed | The ban is recorded on the user record but the existing sessions remain active until they expire naturally or are cleaned up — the server logs the session deletion failure for admin review | The target user's `user.banned` equals `true` in the database and a warning log entry is present for the failed session deletion operation |

## Failure Modes

- **Database write fails when updating the target user's ban fields in the user table**
    - **What happens:** The app admin confirms the ban and the client
        sends the `authClient.admin.banUser()` request, but the D1
        database write fails due to a transient storage error before the
        ban fields are committed to the `user` table, leaving the target
        user's record unchanged with `user.banned` still equal to `false`.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        single-row update that writes `user.banned`, `user.banReason`,
        and `user.banExpires` to the target user's record.
    - **Consequence:** The ban does not take effect, the user's sessions
        remain active, and no audit log entry is created because the
        entire operation failed before any state change was committed to
        the database.
    - **Recovery:** The server returns HTTP 500 and the client displays
        a localized error toast via Sonner — the admin retries the ban
        once the D1 database recovers and the Confirm button is
        re-enabled for another submission attempt.
- **Session invalidation fails after the ban record is successfully written to the user table**
    - **What happens:** The server successfully updates `user.banned` to
        `true` on the target user's record, but the subsequent query to
        delete all active session rows from the `session` table fails due
        to a transient D1 error, leaving the banned user's sessions
        active across their devices.
    - **Source:** Transient database failure during the session deletion
        query that runs after the ban fields have already been committed
        to the target user's record in the `user` table.
    - **Consequence:** The banned user's existing sessions remain valid
        and functional until they expire naturally, meaning the user can
        continue making authenticated API requests despite being banned
        until the sign-in rejection catches them on their next sign-in
        attempt.
    - **Recovery:** The server logs the session deletion failure and
        alerts the admin via the audit log that session invalidation did
        not complete — the admin falls back to manually revoking the
        banned user's sessions through the session management interface,
        and the ban itself is still enforced at sign-in time regardless.
- **Non-admin user bypasses the client guard and calls the admin banUser endpoint directly**
    - **What happens:** A user without the app admin role crafts a
        direct HTTP request to the `authClient.admin.banUser()` mutation
        endpoint using a valid session cookie, bypassing the client-side
        UI that hides admin controls from non-admin users, and attempts
        to ban another user without authorization.
    - **Source:** Adversarial action where a non-admin user sends a
        hand-crafted HTTP request to the admin ban mutation endpoint with
        a valid session token, circumventing the client-side visibility
        guard that conditionally renders admin controls only for users
        with `user.role` equal to `"admin"`.
    - **Consequence:** Without server-side enforcement any authenticated
        user could ban another user, disrupt their access, and create
        false moderation records in the audit log, undermining the
        administrative trust boundary.
    - **Recovery:** The mutation handler rejects the request with
        HTTP 403 after verifying the calling user's `user.role` field
        in the `user` table — the server logs the unauthorized attempt
        with the caller's user ID and timestamp, and no changes are
        written to the target user's database record.
- **Audit log write fails after the ban and session invalidation both succeed**
    - **What happens:** The server successfully bans the user and
        invalidates all their sessions, but the audit log write fails
        due to a transient storage error, leaving no accountability
        record for the ban action in the audit system.
    - **Source:** Transient database or logging service failure during
        the audit log insert that runs after the ban fields and session
        deletion have already been committed to the database.
    - **Consequence:** The ban is fully enforced and the user is signed
        out, but no audit trail exists for this ban action, which
        degrades the accountability and traceability of administrative
        moderation decisions.
    - **Recovery:** The server logs the audit write failure to the
        application error log and notifies the admin that the audit
        entry was not recorded — the ban remains in effect and the admin
        can manually document the action or the system retries the
        audit write on the next scheduled reconciliation pass.

## Declared Omissions

- This specification does not address the admin workflow for unbanning
    a user — that behavior is fully defined in the separate
    `app-admin-unbans-a-user.md` specification covering the unban
    confirmation flow and field reset logic
- This specification does not address the banned user's sign-in
    rejection experience in detail — that behavior is fully defined in
    the separate `banned-user-attempts-sign-in.md` specification
    covering ban screen rendering and error display
- This specification does not address ban enforcement on API requests
    made with existing sessions between the ban timestamp and session
    expiration — middleware-level ban checks on every request are
    defined separately from this admin action flow
- This specification does not address rate limiting on the
    `authClient.admin.banUser()` endpoint — that behavior is enforced
    by the global rate limiter defined in `api-framework.md` covering
    all mutation endpoints uniformly across the API layer
- This specification does not address a ban appeal or dispute process
    because no appeal mechanism exists in the current boilerplate scope
    and moderation decisions are final until an admin unbans the user

## Related Specifications

- [banned-user-attempts-sign-in](banned-user-attempts-sign-in.md) —
    Defines the sign-in rejection experience for banned users, including
    the ban screen rendering with reason and expiration display, which
    is the direct downstream consequence of the ban action defined here
- [app-admin-updates-user-details](app-admin-updates-user-details.md)
    — Admin user detail editing flow that operates on the same `user`
    table records and shares the same admin dashboard navigation pattern
    used by this ban action flow
- [app-admin-lists-and-searches-users](app-admin-lists-and-searches-users.md)
    — Admin user management list and search flow that provides the entry
    point for locating and selecting the target user before initiating
    the ban action from their profile detail view
- [auth-server-config](../foundation/auth-server-config.md) — Better
    Auth server configuration including the admin plugin that validates
    the `user.role` field and exposes the `authClient.admin.banUser()`
    endpoint used by this specification's ban confirmation flow
- [session-lifecycle](session-lifecycle.md) — Session creation and
    expiration lifecycle that governs the session rows deleted during
    the ban action's session invalidation step, defining how sessions
    are stored and managed in the `session` table

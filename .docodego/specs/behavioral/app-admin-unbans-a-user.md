---
id: SPEC-2026-060
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Unbans a User

## Intent

This spec defines the flow by which an app admin navigates to the user
management section of the admin dashboard, locates a banned user by
searching, filtering by banned status, or scrolling through the list,
opens the banned user's profile detail view, and clicks the "Unban"
action button to reinstate the user's access. A localized confirmation
prompt prevents accidental unbans. Upon confirmation, the client calls
`authClient.admin.unbanUser({ userId })` and the server verifies that
the caller holds the app-level admin role (`user.role = "admin"`)
before clearing all ban-related fields on the target user's record:
`user.banned` is set to `false`, `user.banReason` is set to `null`,
and `user.banExpires` is set to `null`. After the unban completes, the
user can sign in normally through any authentication method without a
forced password reset or special re-entry flow. The unban action is
recorded in the audit log with the admin's identity, the target user's
identity, and a UTC timestamp to maintain a complete moderation history.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.unbanUser()` endpoint | write | App admin confirms the unban action on the banned user's profile detail page, sending the target user's ID to the server for ban field clearing | The client receives an error response and displays a localized error toast via Sonner — the target user's ban fields remain unchanged in the database until the endpoint recovers and the admin retries the unban action |
| `user` table (D1) | read/write | The user list page loads banned users with their status indicators for filtering and display, and the unban mutation clears `user.banned`, `user.banReason`, and `user.banExpires` on the target user's record | The user list fails to load with HTTP 500 and the unban mutation rejects with HTTP 500 — no partial update is written to the target user's record and all ban fields remain at their previous values in the database |
| Audit log | write | After the server clears the ban fields on the target user's record, it writes an audit log entry recording which app admin performed the unban, which user was unbanned, and the UTC timestamp of the action | Audit log write fails but the unban itself succeeds — the server logs the audit write failure for operational diagnostics and the admin receives a success response because the primary unban operation completed |
| `@repo/i18n` | read | All UI text on the user list, profile detail page, unban button label, confirmation prompt message, success toast, and error toast are rendered via translation keys at component mount and interaction time | Translation function falls back to the default English locale strings so the unban flow remains fully usable and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[App Admin]** navigates to the user management section of the
    app admin dashboard, where banned users are visually
    distinguishable in the user list with a banned status indicator
    badge displayed next to their name and profile information

2. **[App Admin]** locates the specific banned user they want to
    reinstate by searching by name or email, filtering the user list
    by banned status to narrow the results, or scrolling through the
    full user list to find the target user entry

3. **[App Admin]** selects the banned user from the list to open
    their profile detail view, which displays the user's current
    information alongside the active ban status, ban reason (if one
    was provided when the ban was issued), and ban expiration date
    (if the ban is temporary rather than permanent)

4. **[App Admin]** clicks the "Unban" action button on the banned
    user's profile detail page to initiate the process of lifting the
    ban and restoring the user's access to the application

5. **[Client]** displays a localized confirmation prompt asking the
    app admin to confirm the unban action — the prompt clearly states
    the target user's display name and the irreversibility of
    clearing the ban record fields from the user's account

6. **[App Admin]** confirms the unban action in the confirmation
    prompt by clicking the confirm button, signaling the client to
    proceed with the unban API call to the server

7. **[Client]** transitions the "Unban" button to a loading state
    while the request is in flight, preventing duplicate submissions
    until the server responds with a success or failure result

8. **[Client]** calls `authClient.admin.unbanUser({ userId })` with
    the target user's ID, sending the unban mutation request to the
    server for processing and persistence

9. **[Server]** verifies that the calling user's `user.role` field
    equals `"admin"` — if the caller does not hold the app admin
    role, the server rejects the request with HTTP 403 and no changes
    are written to the target user's ban fields in the database

10. **[Server]** clears all ban-related fields on the target user's
    record in the `user` table: `user.banned` is set to `false`,
    `user.banReason` is set to `null`, and `user.banExpires` is set
    to `null` — all three fields are cleared in a single atomic
    database write operation

11. **[Server]** writes an audit log entry recording the app admin's
    user ID, the target user's ID, and the UTC timestamp of the
    unban action to maintain a complete moderation history alongside
    the original ban record

12. **[Server]** returns HTTP 200 confirming that the ban fields were
    cleared and the audit log entry was written, completing the
    server-side unban operation

13. **[Client]** receives the success response, displays a localized
    toast notification via Sonner confirming that the user has been
    unbanned, and invalidates the TanStack Query cache for the target
    user's data to trigger a re-fetch of the updated profile

14. **[Client]** refreshes the target user's profile detail page to
    reflect the updated status — the banned status indicator is
    removed, the ban reason and ban expiration fields are no longer
    displayed, and the "Unban" button is replaced or hidden because
    the user is no longer banned

15. **[Branch — admin cancels confirmation]** If the app admin
    clicks the cancel button in the confirmation prompt instead of
    confirming, the prompt closes and no API call is made — the
    target user's ban fields remain unchanged and the "Unban" button
    returns to its default interactive state

16. **[Branch — network error]** If the unban mutation request fails
    due to a network error or timeout, the client displays a generic
    localized error toast via Sonner and re-enables the "Unban"
    button so the admin can retry the action without re-navigating

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| detail_page_idle | confirmation_prompt_open | App admin clicks the "Unban" action button on the banned user's profile detail page | Target user's `user.banned` field equals `true` and the calling user's `user.role` equals `"admin"` |
| confirmation_prompt_open | detail_page_idle | App admin clicks the cancel button in the confirmation prompt to abort the unban action | The cancel button is clicked before the confirm button and no API request has been dispatched |
| confirmation_prompt_open | submitting | App admin clicks the confirm button in the confirmation prompt to proceed with the unban | The confirm button is clicked and the client begins the API request to the server |
| submitting | unban_success | Server returns HTTP 200 confirming that the target user's ban fields were cleared and the audit log was written | Server-side authorization passes and the database write completes for all three ban fields |
| submitting | unban_error | Server returns a non-200 error code or the request times out before a response is received | Database write fails, authorization check fails, or a network error interrupts the request |
| unban_success | detail_page_idle | Client displays the success toast and the detail page refreshes to show the unbanned status with the ban indicator removed | TanStack Query cache invalidation completes and the profile detail page re-renders with updated data |
| unban_error | detail_page_idle | Client displays the error toast and the "Unban" button returns to its default interactive state for retry | Error message is visible and the "Unban" button is re-enabled with no changes to the target user's ban fields |

## Business Rules

- **Rule app-admin-role-required:** IF the authenticated user's
    `user.role` field does not equal `"admin"` THEN the
    `authClient.admin.unbanUser()` endpoint rejects the request with
    HTTP 403 AND the server does not modify any ban fields on the
    target user's record in the database
- **Rule all-ban-fields-cleared-on-unban:** IF the unban mutation
    succeeds THEN the server sets `user.banned` to `false`,
    `user.banReason` to `null`, and `user.banExpires` to `null` in
    a single atomic database write — the count of partially cleared
    ban records (where one field is cleared but another is not)
    equals 0 after the operation completes
- **Rule early-unban-clears-expiry-regardless:** IF the target user
    has a temporary ban with a future `user.banExpires` date that has
    not yet passed THEN the unban operation clears all three ban
    fields identically to a permanent ban unban — the `banExpires`
    field is set to `null` regardless of whether the original
    expiration date had been reached
- **Rule no-forced-reset-after-unban:** IF a user's ban has been
    lifted by an admin THEN the user signs in through any available
    authentication method (email OTP, passkey, or SSO) without a
    forced password reset, special re-entry flow, or "welcome back"
    prompt — the sign-in experience is identical to a user who was
    never banned
- **Rule confirmation-required:** IF the app admin clicks the
    "Unban" button THEN a localized confirmation prompt is displayed
    before any API call is made — the count of unban mutation
    requests dispatched without a preceding confirmation equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin | View the user management list with banned status indicators, filter and search for banned users, open a banned user's profile detail page, click the "Unban" button, confirm the unban action, and see the success or error toast after the operation completes | N/A — the app admin has full access to the unban flow for all banned users in the system | The "Unban" button is visible and interactive on the profile detail page of any user whose `user.banned` field equals `true`; the button is hidden or absent when the user is not banned |
| Non-admin authenticated user | None — the admin user management page is not accessible to non-admin users and the route guard redirects or returns HTTP 403 before the page renders any content or user data | Viewing the user management list, accessing any user's profile detail page through the admin interface, or calling the `authClient.admin.unbanUser()` endpoint, which rejects with HTTP 403 | The admin user management page is not rendered; the user is redirected or shown a 403 error before any admin controls or user data are mounted or visible |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the user management page component renders any content or loads any user data from the server | Accessing the user management page or calling the `authClient.admin.unbanUser()` endpoint without a valid authenticated session token | The user management page is not rendered; the redirect to `/signin` occurs before any page elements are mounted or visible |

## Constraints

- The `authClient.admin.unbanUser()` mutation endpoint enforces the
    app admin role server-side by reading the calling user's
    `user.role` field — the count of unban operations initiated by
    non-admin users that succeed equals 0
- All three ban fields (`user.banned`, `user.banReason`,
    `user.banExpires`) are cleared in a single atomic database write
    operation — the count of partially cleared ban records where one
    field is updated but another is not equals 0 after the operation
- The confirmation prompt is displayed before any unban API call is
    dispatched — the count of `authClient.admin.unbanUser()` mutation
    requests sent without a preceding user confirmation equals 0
- The unban flow does not trigger a forced password reset, special
    re-entry flow, or "welcome back" prompt for the unbanned user —
    the count of additional authentication steps required beyond the
    standard sign-in flow after an unban equals 0
- All UI text including the unban button label, confirmation prompt
    message, success toast, error toast, and banned status indicator
    labels are rendered via i18n translation keys — the count of
    hardcoded English string literals in the unban flow components
    equals 0
- The audit log entry for the unban action records the admin's user
    ID, the target user's ID, and a UTC timestamp — the count of
    unban operations that complete without a corresponding audit log
    write attempt equals 0

## Acceptance Criteria

- [ ] Banned users in the user management list display a visible banned status indicator badge — the indicator element is present and visible for every user record where `user.banned` equals `true`
- [ ] The app admin can filter the user list by banned status to show only banned users — the filtered list contains exclusively users where `user.banned` equals `true` and the count of non-banned users in the filtered results equals 0
- [ ] Clicking a banned user in the list opens their profile detail view showing the ban status, ban reason (if present), and ban expiration (if present) — all three fields are visible and non-empty when values exist in the database record
- [ ] Clicking the "Unban" button on a banned user's profile displays a localized confirmation prompt — the prompt element is present and visible within 200ms of the button click and contains the target user's display name
- [ ] Canceling the confirmation prompt closes it without sending an API request — the prompt element is absent from the DOM after cancel and the network request count to `authClient.admin.unbanUser()` equals 0
- [ ] Confirming the unban action calls `authClient.admin.unbanUser({ userId })` with the correct target user ID — the mutation invocation count equals 1 and the payload `userId` matches the target user's ID
- [ ] On mutation success the server sets `user.banned` to `false`, `user.banReason` to `null`, and `user.banExpires` to `null` — all three fields in the `user` table equal their cleared values after the operation
- [ ] On mutation success a localized confirmation toast appears via Sonner — the toast element is present and visible within 500ms of the API returning HTTP 200
- [ ] On mutation success the profile detail page refreshes to show the unbanned status — the banned status indicator is absent, the ban reason field is not displayed, and the "Unban" button is hidden or absent
- [ ] On mutation failure due to a network error the client displays a localized error toast — the toast element is present and the "Unban" button returns to its interactive state with the disabled attribute absent
- [ ] A non-admin authenticated user calling `authClient.admin.unbanUser()` directly receives HTTP 403 — the response status equals 403 and the target user's ban fields in the `user` table remain unchanged
- [ ] An unban on a temporarily banned user with a future `banExpires` date clears all three ban fields — `user.banned` equals `false`, `user.banReason` equals `null`, and `user.banExpires` equals `null` after the operation regardless of the original expiry date
- [ ] After being unbanned the user can sign in via email OTP, passkey, or SSO without a forced password reset — the sign-in flow creates a session and the count of additional authentication prompts beyond the standard flow equals 0
- [ ] The audit log contains an entry for the unban action with the admin's user ID, the target user's ID, and a UTC timestamp — the count of audit log entries matching the unban event equals 1 after the operation

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| App admin attempts to unban a user whose `user.banned` field is already `false` because the user was previously unbanned or was never banned | The server returns HTTP 400 indicating the target user is not currently banned because the `user.banned` field equals `false` — no database write occurs and no audit log entry is created for this no-op request | HTTP response status equals 400 and the target user's record in the `user` table remains unchanged with `user.banned` equal to `false` |
| App admin unbans a temporarily banned user whose `banExpires` date has already passed, meaning the ban would have expired automatically without admin intervention | The server clears all three ban fields identically to an active ban unban — `user.banned` is set to `false`, `user.banReason` to `null`, and `user.banExpires` to `null` — and writes the audit log entry to record that an admin explicitly lifted the expired ban | All three ban fields equal their cleared values in the `user` table and the audit log contains the unban entry with the admin's ID and timestamp |
| Two app admins attempt to unban the same banned user simultaneously from different browser sessions, sending concurrent `authClient.admin.unbanUser()` requests | Both requests reach the server and the first to execute clears all three ban fields — the second request either succeeds idempotently (clearing already-cleared fields) or returns HTTP 400 if the server validates that the user is already unbanned before writing | The target user's ban fields are cleared after both requests complete and at least 1 audit log entry exists for the unban action with the correct admin ID |
| App admin clicks the "Unban" button and confirms, but the network connection drops before the server response reaches the client, leaving the request status unknown | The client times out waiting for a response and displays a localized error toast indicating a network failure — the admin can retry the unban action, and if the server had already processed the first request, the retry either succeeds idempotently or returns HTTP 400 for an already-unbanned user | The error toast element is present and the "Unban" button is re-enabled for retry after the timeout period elapses |
| App admin unbans a user who had an active session before the ban was issued and whose session was revoked as part of the ban enforcement process | The unban clears the ban fields but does not restore previously revoked sessions — the user creates a new session by signing in normally after the unban, and the revoked session remains invalid in the session store | The user's ban fields are cleared, the previously revoked session record remains inactive, and a new session is created upon the next successful sign-in |
| App admin opens the confirmation prompt for unbanning a user, then leaves the browser tab idle for an extended period before clicking confirm, causing the session token to expire | The client sends the unban request with an expired session token and the server rejects it with HTTP 401 — the client redirects the admin to the sign-in page to re-authenticate before retrying the unban action | HTTP response status equals 401 and the target user's ban fields remain unchanged until the admin re-authenticates and retries |

## Failure Modes

- **Database write fails when clearing the ban fields on the target user's record**
    - **What happens:** The app admin confirms the unban and the
        client sends the `authClient.admin.unbanUser()` request, but
        the D1 database write fails due to a transient storage error
        before the ban fields are updated, leaving `user.banned`,
        `user.banReason`, and `user.banExpires` at their original
        banned-state values in the database.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        single-row update operation targeting the three ban fields on
        the target user's record.
    - **Consequence:** The unban does not take effect and the target
        user remains banned with their original ban reason and
        expiration date intact — the user cannot sign in until the
        admin successfully retries the unban operation.
    - **Recovery:** The server returns HTTP 500 and the client
        displays a localized error toast via Sonner — the admin
        retries the unban action once the D1 database recovers
        and the "Unban" button is re-enabled for another attempt.

- **Non-admin user bypasses the client guard and calls the admin unbanUser endpoint directly**
    - **What happens:** A user without the app admin role crafts a
        direct HTTP request to the `authClient.admin.unbanUser()`
        mutation endpoint using a valid session cookie, bypassing the
        client-side UI that hides admin controls from non-admin
        users, and attempts to unban a user without authorization.
    - **Source:** Adversarial or accidental action where a non-admin
        user sends a hand-crafted HTTP request to the admin mutation
        endpoint with a valid session token, circumventing the
        client-side visibility guard that conditionally renders admin
        controls only for users with the admin role.
    - **Consequence:** Without server-side enforcement any
        authenticated user could lift bans on other users, undermining
        the moderation system and potentially allowing abusive users
        to regain access to the platform without admin approval.
    - **Recovery:** The mutation handler rejects the request with
        HTTP 403 after verifying the calling user's `user.role` field
        in the `user` table — the server logs the unauthorized
        attempt with the caller's user ID and timestamp, and no ban
        fields are modified on the target user's database record.

- **Audit log write fails after the ban fields are cleared on the target user's record**
    - **What happens:** The server clears all three ban fields on the
        target user's record, but the subsequent audit log write fails
        due to a transient error, resulting in a completed unban
        action with no corresponding audit trail entry for the
        moderation history.
    - **Source:** Transient failure in the audit log storage system
        or a write timeout that occurs after the primary ban field
        update has already been committed to the `user` table in the
        D1 database.
    - **Consequence:** The unban takes effect and the user can sign
        in normally, but the moderation history is incomplete because
        the audit log entry for this unban action is missing — admins
        reviewing the moderation log will not see this specific unban
        event.
    - **Recovery:** The server logs the audit write failure to the
        application error log for operational diagnostics and
        notifies the monitoring system — the primary unban operation
        is not rolled back because the audit log is a secondary
        concern, and a background reconciliation process can detect
        and backfill missing audit entries by comparing user ban
        state transitions against the audit log timeline.

- **Confirmation prompt fails to render due to a client-side component error**
    - **What happens:** The app admin clicks the "Unban" button but
        the confirmation prompt component fails to render due to a
        JavaScript runtime error or a missing i18n translation key,
        leaving the admin unable to confirm or cancel the action
        through the expected prompt interface.
    - **Source:** Client-side rendering error in the confirmation
        dialog component caused by a missing dependency, a null
        reference in the component state, or an unresolved i18n key
        that prevents the prompt text from being generated.
    - **Consequence:** The admin cannot proceed with the unban
        action through the normal confirmation flow, and no API call
        is dispatched because the confirmation step acts as a gate
        that prevents direct mutation calls without explicit user
        confirmation.
    - **Recovery:** The client catches the rendering error in an
        error boundary, logs the component failure for diagnostics,
        and degrades gracefully by displaying a localized fallback
        error message that instructs the admin to reload the page and
        retry the unban action from the profile detail view.

## Declared Omissions

- This specification does not address the admin workflow for banning
    a user — that behavior is fully defined in the separate
    `app-admin-bans-a-user.md` specification covering ban reason,
    expiration, and field setting
- This specification does not address ban enforcement at sign-in time
    when a banned user attempts to authenticate — that behavior is
    fully defined in the separate `banned-user-attempts-sign-in.md`
    specification
- This specification does not address revocation of active sessions
    belonging to the banned user — session revocation during ban
    enforcement is covered in the separate
    `app-admin-revokes-user-sessions.md` specification
- This specification does not address rate limiting on the
    `authClient.admin.unbanUser()` endpoint — that behavior is
    enforced by the global rate limiter defined in
    `api-framework.md` covering all mutation endpoints uniformly
- This specification does not address bulk unban operations for
    multiple users at once — the current flow handles single-user
    unbans only, and batch moderation actions are outside the current
    boilerplate scope

## Related Specifications

- [app-admin-bans-a-user](app-admin-bans-a-user.md) — Defines the
    admin workflow for banning a user, including setting the `banned`,
    `banReason`, and `banExpires` fields that this unban flow clears
- [banned-user-attempts-sign-in](banned-user-attempts-sign-in.md) —
    Defines the ban enforcement behavior at sign-in time, checking
    the `user.banned` field that this unban flow sets to `false` to
    restore access
- [app-admin-views-user-details](app-admin-views-user-details.md) —
    Defines the admin user detail page that serves as the entry point
    for the unban action, displaying the banned user's profile and
    ban metadata
- [auth-server-config](../foundation/auth-server-config.md) — Better
    Auth server configuration including the admin plugin that validates
    the `user.role` field and exposes the
    `authClient.admin.unbanUser()` endpoint used by this flow
- [database-schema](../foundation/database-schema.md) — Schema
    definition for the `user` table that stores the `banned`,
    `banReason`, and `banExpires` fields read and written by the
    unban mutation handler

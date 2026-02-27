---
id: SPEC-2026-064
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Removes a User

## Intent

This spec defines the flow by which an app admin navigates to the user
management section of the admin dashboard, locates a target user,
opens their profile detail view, and initiates a permanent removal
action by clicking the "Remove" button. Because removing a user is
irreversible and fundamentally different from banning (which can be
undone), the system presents a destructive action confirmation dialog
that makes the consequences explicit. The dialog states that this
action will permanently delete the user's account, revoke all active
sessions, remove the user from every organization they belong to, and
erase their account record entirely. The app admin must type the
user's email address into a confirmation field to prevent accidental
deletions — only after the confirmation input matches does the
"Remove permanently" button become active. On confirmation, the client
calls `authClient.admin.removeUser({ userId })` and the server
verifies the caller holds the app admin role (`user.role = "admin"`)
before executing the atomic removal sequence: first all active
sessions belonging to the user are revoked, then all organization
memberships are deleted, and finally the user's account record itself
is permanently deleted from the database. Either all steps complete or
none of them take effect. The removed user's active browsing sessions
fail on the next API request, and any subsequent sign-in attempt finds
no matching account — unlike a banned user who sees a ban message, a
removed user cannot authenticate because the account no longer exists.
The removal action is recorded in the audit log with the admin's
identity, the removed user's identifier and email, and the timestamp,
preserving traceability even after the user record is deleted.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.removeUser()` endpoint | write | App admin clicks the "Remove permanently" button in the destructive action confirmation dialog after typing the user's email address into the confirmation field, sending the removal mutation to the server | The client receives an error response and displays a localized error toast via Sonner — the target user's record remains unchanged in the database and the admin retries once the endpoint recovers |
| `user` table (D1) | read/write | The user management page loads user records for listing and search display, and the removal mutation permanently deletes the target user's row from the `user` table as the final step of the atomic removal sequence | The user list fails to load and returns HTTP 500, and the removal mutation rejects with HTTP 500 so the target user's account record remains unchanged in the database until D1 recovers from the transient failure |
| `session` table (D1) | delete | After the server verifies the admin role, the removal sequence deletes all active session rows belonging to the target user as the first step before removing memberships and the account record | Session deletion fails and the entire atomic transaction rolls back — no changes are committed to the session, member, or user tables, and the server returns HTTP 500 so the admin retries after D1 recovers |
| `member` table (D1) | delete | After sessions are revoked, the removal sequence deletes all `member` rows linking the target user to organizations, removing them from every org roster and team they belonged to | Membership deletion fails and the entire atomic transaction rolls back — sessions that were deleted within the transaction are restored, and the server returns HTTP 500 so the admin retries after D1 recovers |
| Audit log | write | After the removal transaction commits, the server writes an audit entry capturing the admin's user ID, the removed user's former ID and email address, and the UTC timestamp of the removal action | Audit log write fails and the server logs the failure — the removal itself is already committed because the audit write occurs after the atomic transaction, so the account is deleted but the audit entry is missing until manual reconciliation |
| `@repo/i18n` | read | All confirmation dialog text, warning messages, email confirmation field labels, button labels, toast messages, and error messages in the removal flow are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the confirmation dialog and all feedback messages remain fully usable and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[App Admin]** navigates to the user management section of the
    admin dashboard, which displays a paginated list of all registered
    users with their current status, role, and account details

2. **[App Admin]** searches for or scrolls to the specific user they
    intend to permanently remove, using the search field to filter by
    name or email, then selects that user to open their profile detail
    view

3. **[App Admin]** clicks the "Remove" action button on the target
    user's profile detail view, which opens a destructive action
    confirmation dialog with localized warning text

4. **[Client]** renders the destructive action confirmation dialog
    stating that this action will permanently delete the user's
    account, revoke all active sessions, remove the user from every
    organization, and erase the account record entirely

5. **[Client]** renders an email confirmation input field within the
    dialog requiring the admin to type the target user's email address
    exactly — the "Remove permanently" button remains disabled until
    the typed value matches the target user's email

6. **[App Admin]** types the target user's email address into the
    confirmation input field, and the "Remove permanently" button
    transitions from disabled to enabled only when the typed value
    exactly matches the target user's email address

7. **[App Admin]** clicks the enabled "Remove permanently" button to
    submit the removal, and the client transitions the button to a
    loading state while the request is in flight, preventing duplicate
    submissions

8. **[Client]** calls `authClient.admin.removeUser({ userId })` with
    the target user's ID, sending the removal mutation request to the
    server for processing

9. **[Server]** verifies that the calling user's `user.role` field
    equals `"admin"` — if the caller does not hold the app admin role,
    the server rejects the request with HTTP 403 and no changes are
    written to any database table

10. **[Server]** begins the atomic removal transaction and first
    deletes all active session rows in the `session` table that belong
    to the target user, revoking every active session so the user is
    signed out on their next API request across all devices

11. **[Server]** deletes all `member` rows in the `member` table that
    link the target user to organizations, removing the user from
    every organization roster and every team they belonged to

12. **[Server]** permanently deletes the target user's row from the
    `user` table as the final step of the atomic transaction — either
    all three deletion steps (sessions, memberships, account) commit
    together or none of them take effect

13. **[Server]** writes an audit log entry capturing the app admin's
    user ID, the removed user's former user ID and email address, and
    the UTC timestamp of the removal action for compliance and
    accountability traceability

14. **[Server]** returns HTTP 200 confirming that the removal was
    completed, all sessions were invalidated, all memberships were
    deleted, and the audit entry was recorded

15. **[Client]** receives the success response, displays a localized
    confirmation toast via Sonner stating that the user has been
    permanently removed, and invalidates the TanStack Query cache for
    the user list to trigger a re-fetch of the updated data

16. **[Client]** navigates back to the user management list or
    refreshes the current view — the removed user no longer appears
    in the user list because their record has been deleted from the
    database

17. **[Branch -- removed user's next request]** The removed user's
    current browsing session fails on their very next API request
    because all sessions have been deleted — the client receives an
    authentication error and the user is signed out and redirected to
    the landing page

18. **[Branch -- removed user tries to sign in]** If the removed user
    attempts to sign in again, the system finds no matching account
    and treats them as an unrecognized user — unlike a banned user who
    sees a ban message, a removed user cannot authenticate because the
    account no longer exists in the database

19. **[Branch -- network error]** If the removal mutation request
    fails due to a network error or timeout, the client displays a
    generic localized error toast via Sonner and re-enables the
    "Remove permanently" button so the admin can retry the submission

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| user_detail_idle | remove_dialog_open | App admin clicks the "Remove" action button on the target user's profile detail view to initiate the removal workflow | Calling user's `user.role` equals `"admin"` and the target user's account record exists in the `user` table |
| remove_dialog_open | email_confirmed | App admin types a value into the email confirmation field that exactly matches the target user's email address | Input field value is an exact case-sensitive match with the target user's email address stored in the `user` table |
| email_confirmed | remove_dialog_open | App admin clears or modifies the email confirmation input so it no longer matches the target user's email address | Input field value does not exactly match the target user's email address after the edit |
| remove_dialog_open | user_detail_idle | App admin cancels or dismisses the confirmation dialog without confirming the removal action | The admin clicked cancel or closed the dialog, and no mutation request was dispatched to the server |
| email_confirmed | user_detail_idle | App admin cancels or dismisses the confirmation dialog after entering the email but before clicking the remove button | The admin clicked cancel or closed the dialog, and no mutation request was dispatched to the server |
| email_confirmed | submitting | App admin clicks the enabled "Remove permanently" button after the email confirmation input matches the target user's email | The "Remove permanently" button is not already in a loading or disabled state and the email input matches |
| submitting | remove_success | Server returns HTTP 200 confirming the atomic removal of sessions, memberships, and the user record, plus the audit log write | Server-side role check passes and the atomic transaction deleting sessions, memberships, and the user row commits |
| submitting | remove_error | Server returns a non-200 error code or the request times out before a response is received from the server | Database transaction fails, authorization check fails, or a network error occurs during the mutation request |
| remove_success | user_list_view | Client displays the success toast and navigates back to the user management list or refreshes the current view | TanStack Query cache invalidation completes and the user list re-renders without the removed user's entry |
| remove_error | email_confirmed | Client displays the error toast and the confirmation dialog retains the admin's email input for retry of the removal | Error message is visible via Sonner toast and the "Remove permanently" button is re-enabled with the email input intact |

## Business Rules

- **Rule app-admin-role-required:** IF the authenticated user's
    `user.role` field does not equal `"admin"` THEN the
    `authClient.admin.removeUser()` endpoint rejects the request with
    HTTP 403 AND the server logs the unauthorized attempt with the
    caller's user ID and timestamp before returning the error response
- **Rule email-confirmation-required:** IF the confirmation dialog is
    open THEN the "Remove permanently" button remains disabled until
    the admin types a value into the email confirmation field that
    exactly matches the target user's email address — the count of
    removal requests submitted without a matching email confirmation
    equals 0
- **Rule atomic-removal:** IF the admin confirms the removal and the
    server processes the request THEN all active sessions, all
    organization memberships, and the user record are deleted within a
    single atomic database transaction so the count of partially
    removed accounts where sessions or memberships exist without a
    corresponding user row equals 0
- **Rule session-revocation-before-record-deletion:** IF the atomic
    removal transaction executes THEN session rows are deleted before
    organization memberships and the user record — the session table
    deletion is the first operation in the transaction sequence to
    prevent the removed user from making authenticated API requests
    during the membership and account cleanup steps
- **Rule membership-cleanup-before-account-deletion:** IF the atomic
    removal transaction executes THEN all `member` rows linking the
    user to organizations are deleted before the `user` row itself —
    this ordering prevents foreign key violations and orphaned
    membership records that reference a non-existent user ID
- **Rule audit-entry-preserves-deleted-user-reference:** IF the
    removal transaction commits THEN the audit log entry preserves the
    removed user's former user ID and email address even though the
    `user` row no longer exists in the database — the count of removal
    audit entries without a preserved user identifier and email equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin (removing another user) | View the user management list, search for users, open a user's profile detail view, click the "Remove" button, type the email confirmation, click "Remove permanently", and see the success or error toast after the mutation completes | Removing their own admin account — the "Remove" button is hidden or disabled with a localized tooltip when the target user ID equals the admin's own user ID to prevent self-removal | The "Remove" button, confirmation dialog with email input, "Remove permanently" button, and toast messages are all visible and interactive when the target user is not the admin themselves |
| Non-admin authenticated user | None — the admin user management page is not accessible to non-admin users and the route guard redirects or returns HTTP 403 before the page renders any content or loads any user data | Viewing the user management section, accessing any user's admin detail page, or calling the `authClient.admin.removeUser()` endpoint, which rejects with HTTP 403 on the server | The admin user management page is not rendered; the user is redirected or shown a 403 error before any admin controls are mounted or visible in the browser |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the admin user management page component renders any content or loads any user data | Accessing the admin user management page or calling the `authClient.admin.removeUser()` endpoint without a valid authenticated session token in the request | The admin page is not rendered; the redirect to `/signin` occurs before any page elements are mounted or any user data is fetched from the server |

## Constraints

- The `authClient.admin.removeUser()` mutation endpoint enforces the
    app admin role server-side by reading the calling user's `user.role`
    field — the count of removal operations initiated by non-admin
    users that result in a deleted user record equals 0
- The email confirmation input field requires an exact match with the
    target user's email address — the count of enabled "Remove
    permanently" button states where the input does not match the
    target user's email equals 0
- The removal transaction is atomic — the count of committed
    transactions that delete the `user` row without also deleting all
    associated `session` and `member` rows equals 0, ensuring no
    orphaned session or membership records remain after removal
- All confirmation dialog text, warning messages, email confirmation
    field labels, button labels, toast messages, and error messages in
    the removal flow are rendered via i18n translation keys — the count
    of hardcoded English string literals in the removal flow components
    equals 0
- The audit log entry written after removal preserves the removed
    user's former user ID and email address — the count of removal
    audit entries that lack either the former user ID or the former
    email address equals 0
- After the removal transaction commits, any request bearing the
    former user's session token returns HTTP 401 — the count of
    authenticated requests using a removed user's session token that
    return a non-401 status code equals 0

## Acceptance Criteria

- [ ] Clicking "Remove" on a user's detail page opens a destructive action confirmation dialog with a localized warning explaining that removal is permanent and irreversible — the dialog element is present and visible in the DOM within 300ms of the button click
- [ ] The confirmation dialog contains an email confirmation input field and the "Remove permanently" button is disabled when the input is empty — the disabled attribute is present on the button and the input element is rendered with a localized placeholder
- [ ] The "Remove permanently" button transitions from disabled to enabled when the typed email exactly matches the target user's email address — the disabled attribute is absent from the button within 100ms of the input matching
- [ ] The "Remove permanently" button transitions back to disabled when the admin modifies the email input so it no longer matches — the disabled attribute is present on the button within 100ms of the mismatch
- [ ] Clicking the enabled "Remove permanently" button calls `authClient.admin.removeUser({ userId })` — the mutation invocation count equals 1 and the payload contains the correct target user ID
- [ ] The "Remove permanently" button transitions to a loading state while the mutation is in flight — the button shows a loading indicator and the count of additional mutation requests dispatched during this state equals 0
- [ ] On mutation success the server deletes all active session rows belonging to the target user — the count of session records for the removed user's ID in the `session` table equals 0 after the mutation completes
- [ ] On mutation success the server deletes all `member` rows linking the target user to organizations — the count of member records for the removed user's ID in the `member` table equals 0 after the mutation completes
- [ ] On mutation success the server permanently deletes the target user's row from the `user` table — the count of user records with the removed user's ID in the `user` table equals 0 after the mutation completes
- [ ] On mutation success a localized confirmation toast appears via Sonner — the toast element is present and visible within 500ms of the API returning HTTP 200
- [ ] On mutation success the removed user no longer appears in the user management list after cache invalidation — the count of list entries matching the removed user's ID equals 0 after the TanStack Query re-fetch
- [ ] On mutation failure due to a network error the client displays a localized error toast — the toast element is present and the "Remove permanently" button returns to its interactive enabled state for retry
- [ ] A non-admin authenticated user calling `authClient.admin.removeUser()` directly receives HTTP 403 — the response status equals 403 and the target user's record remains present in the `user` table
- [ ] The audit log contains an entry for the removal action with the admin's user ID, the removed user's former user ID, the removed user's former email address, and the UTC timestamp — all 4 fields are present and non-null in the audit entry
- [ ] A subsequent sign-in attempt by the removed user returns a credentials-not-found error because the account no longer exists — the HTTP response status equals 401 or 404 and no ban message is displayed
- [ ] All text in the confirmation dialog, email input placeholder, button labels, and toast messages is rendered via i18n translation keys — the count of hardcoded English strings in the removal flow components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| App admin attempts to remove a user whose account was already deleted by another admin moments earlier | The server returns HTTP 404 because the target user's row no longer exists in the `user` table — the client displays a localized error toast indicating the user was not found and no mutation side effects occur | The HTTP response status equals 404 and the audit log contains no new removal entry for the already-deleted user ID |
| App admin types the target user's email with different casing (uppercase versus lowercase) into the confirmation field | The email confirmation matching is exact and case-sensitive — the "Remove permanently" button remains disabled until the typed value matches the stored email address exactly including casing | The disabled attribute remains present on the "Remove permanently" button when the casing does not match the target user's email |
| App admin opens the removal dialog but navigates away from the detail page before clicking "Remove permanently" | No mutation request is sent because the admin did not click the "Remove permanently" button — the target user's record in the `user` table remains unchanged and no sessions or memberships are affected | The network request count to the `authClient.admin.removeUser()` endpoint equals 0 and the target user's row still exists in the database |
| Two app admins attempt to remove the same user simultaneously from different browser sessions at the same moment | The first transaction to acquire the database lock commits and deletes the user — the second transaction finds no matching user row and the server returns HTTP 404 for the second request | One response status equals 200 and the other equals 404, and the `user` table contains 0 rows for the target user ID |
| App admin attempts to remove their own admin account by manipulating the client or sending a direct API request with their own user ID | The server rejects the self-removal attempt because an admin cannot remove themselves — the endpoint returns HTTP 400 and the admin's account record remains unchanged in the database | The response status equals 400 and the admin's `user` row still exists with all sessions and memberships intact |
| The removed user had active sessions on 5 different devices and was a member of 12 organizations at the time of removal | The atomic transaction deletes all 5 session rows and all 12 member rows before deleting the user row — the count of session rows, member rows, and user rows for the target ID all equal 0 after the transaction commits | The `session` table count for the user ID equals 0, the `member` table count equals 0, and the `user` table count equals 0 |

## Failure Modes

- **Database transaction fails when executing the atomic removal sequence that deletes sessions, memberships, and the user record**
    - **What happens:** The app admin confirms the removal and the
        client sends the `authClient.admin.removeUser()` request, but
        the D1 database returns an error during the atomic transaction,
        causing the entire operation to roll back with no partial
        changes committed to any of the three tables involved.
    - **Source:** Transient Cloudflare D1 database failure, Worker
        resource exhaustion, or a network interruption between the
        Worker and the D1 binding during the multi-table deletion
        transaction that spans the session, member, and user tables.
    - **Consequence:** The user sees an error toast and the target
        user's account remains fully intact — all sessions remain
        valid, all organization memberships are unchanged, and the
        target user can continue using the application normally because
        the transaction rolled back completely with no partial state.
    - **Recovery:** The server returns HTTP 500 and logs the
        transaction error with the target user ID and timestamp — the
        client falls back to displaying a localized error toast via
        Sonner and re-enables the "Remove permanently" button so the
        admin retries the removal once the D1 service recovers.
- **Non-admin user bypasses the client guard and calls the admin removeUser endpoint directly with a valid session token**
    - **What happens:** A user without the app admin role crafts a
        direct HTTP request to the `authClient.admin.removeUser()`
        mutation endpoint using a valid session cookie, bypassing the
        client-side UI that hides admin controls from non-admin users,
        and attempts to remove another user without authorization.
    - **Source:** Adversarial action where a non-admin user sends a
        hand-crafted HTTP request to the admin removal mutation endpoint
        with a valid session token, circumventing the client-side
        visibility guard that conditionally renders admin controls only
        for users with `user.role` equal to `"admin"`.
    - **Consequence:** Without server-side enforcement any authenticated
        user could permanently delete another user's account, destroy
        their sessions, remove their organization memberships, and
        create false administrative records in the audit log.
    - **Recovery:** The mutation handler rejects the request with
        HTTP 403 after verifying the calling user's `user.role` field
        in the `user` table — the server logs the unauthorized attempt
        with the caller's user ID and timestamp, and no changes are
        written to the target user's database record.
- **Audit log write fails after the removal transaction commits, leaving no accountability record for the permanent deletion**
    - **What happens:** The server commits the atomic removal
        transaction that deletes all sessions, memberships, and the
        user record, but the subsequent audit log write fails due to a
        transient storage error, leaving no accountability record for
        the removal action in the audit system.
    - **Source:** Transient database or logging service failure during
        the audit log insert that runs after the removal transaction
        has already committed to the database, because the audit write
        is performed outside the atomic transaction boundary.
    - **Consequence:** The removal is fully enforced and the user's
        account, sessions, and memberships are permanently deleted, but
        no audit trail exists for this removal action, which degrades
        the compliance traceability of administrative actions.
    - **Recovery:** The server logs the audit write failure to the
        application error log and notifies the admin that the audit
        entry was not recorded — the removal remains in effect and the
        admin falls back to manually documenting the action until the
        system retries the audit write on the next reconciliation pass.
- **Network timeout occurs between the client and the server after the admin clicks "Remove permanently" but before a response is received**
    - **What happens:** The client sends the removal mutation request
        but the network connection drops or times out before the server
        response reaches the client, leaving the admin uncertain about
        whether the removal was processed on the server side.
    - **Source:** Network interruption, proxy timeout, or CDN edge
        failure between the client browser and the Cloudflare Worker
        handling the `authClient.admin.removeUser()` mutation endpoint
        during the in-flight request window.
    - **Consequence:** The server either completed the removal
        transaction or rolled it back, but the client cannot determine
        which outcome occurred — the admin sees a timeout error and
        does not know if the user was removed or if the request failed
        before processing began on the server.
    - **Recovery:** The client displays a localized error toast via
        Sonner and re-enables the "Remove permanently" button — the
        admin retries the removal, and the server either processes the
        new request normally or returns HTTP 404 if the user was
        already deleted by the timed-out request.

## Declared Omissions

- This specification does not address soft-deleting or archiving the
    removed user's account with the ability to restore it within a
    grace period — the removal covered by this spec is permanent and
    irreversible with no recovery mechanism after the transaction
    commits to the database
- This specification does not address deleting user-generated content
    within organizations the removed user belonged to — content
    attribution and retention policies for departed or deleted users
    are covered by the data-governance spec as a separate concern from
    account removal
- This specification does not address notifying organization members
    or admins when a user is removed and disappears from their
    organization rosters — notification behavior for member departure
    events is defined in the organization notification spec
- This specification does not address rate limiting on the
    `authClient.admin.removeUser()` endpoint — that behavior is
    enforced by the global rate limiter defined in `api-framework.md`
    covering all mutation endpoints uniformly across the API layer
- This specification does not address the difference between
    admin-initiated removal and user-initiated self-deletion — the
    self-deletion flow is defined in `user-deletes-their-account.md`
    with a different confirmation mechanism and ownership checks

## Related Specifications

- [app-admin-bans-a-user](app-admin-bans-a-user.md) — Admin ban
    flow that operates on the same `user` table records and shares the
    same admin dashboard navigation pattern, but banning is reversible
    while removal is permanent and irreversible
- [app-admin-lists-and-searches-users](app-admin-lists-and-searches-users.md)
    — Admin user management list and search flow that provides the
    entry point for locating and selecting the target user before
    initiating the removal action from their profile detail view
- [app-admin-views-user-details](app-admin-views-user-details.md)
    — Admin user detail view spec defining the profile detail page
    where the "Remove" button is located and where the removal
    confirmation dialog is triggered by the admin
- [user-deletes-their-account](user-deletes-their-account.md) —
    Self-service account deletion flow that covers user-initiated
    permanent deletion with ownership checks, which differs from the
    admin-initiated removal defined in this specification
- [session-lifecycle](session-lifecycle.md) — Session creation and
    expiration lifecycle that governs the session rows deleted during
    the removal action's session invalidation step within the atomic
    transaction
- [auth-server-config](../foundation/auth-server-config.md) — Better
    Auth server configuration including the admin plugin that validates
    the `user.role` field and exposes the
    `authClient.admin.removeUser()` endpoint used by this removal flow

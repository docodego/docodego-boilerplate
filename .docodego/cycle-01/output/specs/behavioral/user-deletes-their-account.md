---
id: SPEC-2026-055
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Deletes Their Account

## Intent

This spec defines the self-service account deletion flow by which an
authenticated user permanently removes their own account from the DoCodeGo
platform. The user initiates the action from the danger zone section at the
bottom of the account settings page at `/app/settings/account`. Before
deletion can proceed, the system checks whether the user is the owner of
any organization — if ownership exists, the deletion is blocked until the
user transfers ownership or deletes those organizations. When the ownership
check passes, a confirmation dialog requires the user to type a specific
confirmation phrase to prevent accidental deletion. After confirmation, the
client calls the account deletion endpoint. The server revokes all active
sessions, removes the user from every organization membership, and
permanently deletes the user record from the database. The user is then
redirected to the landing page or sign-in page. The deletion is final with
no recovery mechanism — any subsequent sign-in attempt with the former
email fails as if the account never existed.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth server SDK (`deleteUser` endpoint) | write | Client calls the account deletion endpoint after the user types the confirmation phrase and clicks the final confirm button in the deletion dialog | The server returns HTTP 500 and the client falls back to displaying a localized error message in the confirmation dialog, leaving the user account fully intact with all sessions and memberships unchanged until the service recovers |
| `user` table (D1) | write | Server permanently deletes the `user` row after revoking all sessions and removing all organization memberships in the same atomic transaction | The database write fails, the transaction rolls back, the server returns HTTP 500, and the client falls back to showing a localized error message — the user account remains fully intact because no partial deletion is committed |
| `session` table (D1) | write | Server revokes all active session rows linked to the user ID as part of the atomic deletion transaction before removing the user record itself | The session revocation fails, the transaction rolls back, the server returns HTTP 500, and the user account remains intact with all sessions still valid until the database recovers and the user retries |
| `member` table (D1) | write | Server removes all `member` rows linking the user to organizations as part of the atomic deletion transaction, effectively removing the user from every organization they belong to | The member row deletion fails, the transaction rolls back, the server returns HTTP 500, and the user account remains intact with all organization memberships unchanged until the service recovers |
| `@repo/i18n` | read | All confirmation dialog text, warning messages, confirmation phrase instructions, button labels, and error messages displayed during the deletion flow are rendered via i18n translation keys | Translation function falls back to the default English locale strings so the confirmation dialog remains functional and the user can still complete or cancel the deletion with English text |

## Behavioral Flow

1. **[User]** navigates to `/app/settings/account` where a danger zone
    section appears at the bottom of the page, always visible to the
    authenticated user — account deletion is a self-service action
    available to every authenticated user regardless of role
2. **[User]** clicks the delete account button in the danger zone section
    to initiate the account deletion process for their own account
3. **[Client]** sends a preflight request to the server to check whether
    the user is the owner of any organization before opening the
    confirmation dialog
4. **[Server]** queries the `member` table for all rows where the user ID
    matches and the role equals `owner`, returning the list of owned
    organizations to the client
5. **[Branch — user owns organizations]** The client displays a blocking
    message explaining that the user must first transfer ownership of each
    listed organization to another member or delete those organizations
    before account deletion can proceed — the confirmation dialog is not
    opened and the delete action is blocked until ownership is resolved
6. **[Branch — ownership check passes]** The client opens a confirmation
    dialog displaying a localized permanent warning that deleting the
    account cannot be undone, that all personal data, profile information,
    and organization memberships will be permanently removed
7. **[Client]** renders an input field within the confirmation dialog
    requiring the user to type a specific confirmation phrase — such as
    the word "delete" or their email address — before the final confirm
    button becomes enabled
8. **[User]** types the required confirmation phrase into the input field,
    and the confirm button transitions from disabled to enabled only when
    the typed value exactly matches the expected confirmation phrase
9. **[User]** clicks the enabled confirm button to proceed with permanent
    account deletion, or clicks cancel to dismiss the dialog without
    taking any action
10. **[Branch — user cancels]** The confirmation dialog closes and the
    user's account remains fully intact with no changes made to the user
    record, sessions, or memberships
11. **[Client]** disables the confirm button, displays a loading indicator,
    and calls the account deletion endpoint to request permanent removal
    of the user's account
12. **[Server]** receives the deletion request, validates the authenticated
    session, re-checks that the user does not own any organizations, and
    begins the atomic deletion transaction
13. **[Server]** revokes all active sessions belonging to the user by
    deleting all `session` rows linked to the user ID within the atomic
    transaction
14. **[Server]** removes the user from every organization by deleting all
    `member` rows linked to the user ID within the same atomic transaction
15. **[Server]** permanently deletes the `user` row from the database as
    the final step of the atomic transaction, then clears any session
    cookies from the response and returns HTTP 200
16. **[Client]** receives the success response, clears all local session
    state, and redirects the user to the landing page or the sign-in page
    at `/signin`
17. **[Post-deletion]** The user's credentials no longer exist in the
    system — any subsequent attempt to sign in with the former email
    address returns a credentials-not-found error as if the account never
    existed, and the user must register a new account to use the
    application again

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| settings_page | ownership_check | User clicks the delete account button in the danger zone | Authenticated user is viewing `/app/settings/account` |
| ownership_check | ownership_blocked | Server returns a non-empty list of owned organizations | Count of organizations where user role equals `owner` is greater than 0 |
| ownership_check | dialog_open | Server returns an empty list of owned organizations | Count of organizations where user role equals `owner` equals 0 |
| ownership_blocked | settings_page | User dismisses the ownership blocking message | None — dismiss is always available |
| dialog_open | phrase_entered | User types the correct confirmation phrase in the input field | Input field value exactly matches the expected confirmation phrase |
| phrase_entered | dialog_open | User clears or modifies the input so it no longer matches the expected phrase | Input field value does not match the expected confirmation phrase |
| dialog_open | settings_page | User clicks cancel or dismisses the dialog | None — cancel is always available |
| phrase_entered | settings_page | User clicks cancel or dismisses the dialog after entering the phrase | None — cancel is always available |
| phrase_entered | deleting | User clicks the enabled confirm button | Confirm button is not already in a loading or disabled state |
| deleting | deletion_complete | Server returns HTTP 200 from the account deletion endpoint | All sessions revoked, all memberships removed, user row deleted within atomic transaction |
| deleting | dialog_error | Server returns non-200 or network error | HTTP response status does not equal 200 or the request times out |
| dialog_error | phrase_entered | Client re-enables the confirm button for retry | User record still exists in the database and the retry request can proceed |
| deletion_complete | redirected | Client navigates to the landing page or `/signin` | Success response received and local session state cleared |

## Business Rules

- **Rule org-owner-deletion-blocked:** IF the authenticated user is the
    owner of 1 or more organizations THEN the account deletion is blocked
    AND the client displays a message listing the owned organizations with
    instructions to transfer ownership or delete those organizations before
    the confirmation dialog can be opened — the count of account deletions
    processed while the user holds organization ownership equals 0
- **Rule confirmation-phrase-required:** IF the ownership check passes and
    the confirmation dialog is open THEN the confirm button remains disabled
    until the user types a value that exactly matches the expected
    confirmation phrase — the count of deletion requests submitted without
    a matching confirmation phrase equals 0
- **Rule atomic-cleanup:** IF the user confirms deletion and the server
    processes the request THEN all active sessions, all organization
    memberships, and the user record itself are removed within a single
    atomic database transaction so the count of partially deleted accounts
    where sessions or memberships exist without a corresponding user row
    equals 0
- **Rule no-recovery-after-deletion:** IF the account deletion transaction
    commits successfully THEN there is no mechanism to recover, restore, or
    undo the deletion — the count of recovery endpoints or undo actions
    available for deleted accounts equals 0 and subsequent sign-in attempts
    with the former email return a credentials-not-found error

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (not an org owner) | View the danger zone section on the account settings page, click the delete account button, pass the ownership check, type the confirmation phrase, confirm deletion, and be redirected after the account is permanently removed | None — a non-owner user has full authority to delete their own account through this self-service flow | Danger zone section is present and visible at the bottom of `/app/settings/account` with the delete account button and all warning text fully rendered |
| User (org owner) | View the danger zone section on the account settings page and click the delete account button to initiate the ownership check | Proceeding past the ownership check — the confirmation dialog is not opened and the deletion is blocked until the user transfers ownership of all owned organizations or deletes them | Danger zone section is visible but clicking delete triggers the ownership blocking message instead of the confirmation dialog, and the confirm button is never rendered |
| Admin (organization role) | View the danger zone section and delete their own account if they do not own any organizations — the admin organization role does not affect account-level deletion eligibility | Deleting their account while they also hold `owner` role in any organization — the ownership check blocks at the organization level regardless of admin status | Same as User (not an org owner) if they pass the ownership check, same as User (org owner) if they own any organizations |
| Unauthenticated visitor | None — the route guard redirects to `/signin` before the account settings page loads | Access any part of `/app/settings/account` or call the account deletion endpoint | Account settings page is not rendered — redirect to `/signin` occurs before any component mounts |

## Constraints

- The confirm button in the deletion dialog is disabled until the typed
    input exactly matches the expected confirmation phrase — the count of
    enabled confirm button states where the input does not match the phrase
    equals 0
- The server re-validates the ownership check within the deletion request
    handler — the count of successful account deletions where the user owns
    at least 1 organization at the time of the server-side check equals 0
- The deletion transaction is atomic — the count of committed transactions
    that delete the `user` row without also deleting all associated `session`
    and `member` rows equals 0, ensuring no orphaned session or membership
    records remain after deletion
- All UI text in the danger zone section, ownership blocking message, and
    confirmation dialog is rendered via i18n translation keys — the count of
    hardcoded English strings in the deletion flow components equals 0
- After the deletion transaction commits, any request bearing the former
    user's session token returns HTTP 401 — the count of successful
    authenticated requests using a deleted user's session token equals 0
- The confirmation phrase input field does not accept empty strings as a
    valid match — the count of deletion requests triggered with an empty
    confirmation phrase input equals 0

## Acceptance Criteria

- [ ] The danger zone section with the delete account button is present and visible at the bottom of `/app/settings/account` when the user is authenticated — the delete button element is present in the DOM after the page loads
- [ ] Clicking the delete account button triggers an ownership check that queries the server for organizations where the user role equals `owner` — the ownership check request is present in the network activity log within 500ms of the button click
- [ ] When the user owns 1 or more organizations, a blocking message is displayed listing the owned organizations — the blocking message element is present and visible in the DOM and the confirmation dialog element count equals 0
- [ ] When the user owns 0 organizations, the confirmation dialog opens with a localized permanent warning — the dialog element is present and visible within 300ms of the ownership check response
- [ ] The confirmation dialog contains an input field requiring the user to type a specific confirmation phrase before the confirm button becomes enabled — the confirm button disabled attribute is present when the input value does not match the expected phrase
- [ ] The confirm button transitions from disabled to enabled when the typed input exactly matches the expected confirmation phrase — the disabled attribute is absent from the confirm button within 100ms of the input matching
- [ ] Clicking cancel closes the dialog without deleting the account — the dialog element is absent from the DOM after cancel and the `user` row still exists in the database
- [ ] Clicking the enabled confirm button calls the account deletion endpoint — the deletion API request is present in the network activity log with the correct user context
- [ ] The confirm button is disabled and a loading indicator is present while the deletion request is in flight — the disabled attribute is present on the confirm button and the loading element is visible during the API call
- [ ] On HTTP 200, all `session` rows linked to the user ID are deleted — the count of session rows with the deleted user's ID in the database equals 0 after the response
- [ ] On HTTP 200, all `member` rows linked to the user ID are deleted — the count of member rows with the deleted user's ID in the database equals 0 after the response
- [ ] On HTTP 200, the `user` row is permanently deleted — the count of user rows with the deleted user's ID in the database equals 0 after the response
- [ ] After successful deletion, the client redirects to the landing page or `/signin` — the window location pathname equals `/` or `/signin` within 1000ms of the success response
- [ ] A subsequent sign-in attempt with the former email address returns a credentials-not-found error — the HTTP response status equals 401 or 404 and the error message indicates the account does not exist
- [ ] A request bearing the former user's session token after deletion returns HTTP 401 — the response status equals 401 for any authenticated endpoint called with the deleted session token
- [ ] The ownership blocking message includes the names of all owned organizations — the count of owned organization names displayed in the blocking message equals the count of organizations where the user's role is `owner`
- [ ] All dialog text, button labels, input placeholders, and error messages are rendered via i18n translation keys — the count of hardcoded English string literals in the deletion flow components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User double-clicks the confirm button before the first deletion request completes | The client disables the confirm button immediately on the first click, preventing a second request — the server receives exactly 1 deletion request and the count of deletion API calls equals 1 | The disabled attribute is present on the confirm button within 100ms of the first click and the network log shows exactly 1 deletion request |
| User's session expires after typing the confirmation phrase but before clicking confirm | Clicking the confirm button triggers the deletion request which returns HTTP 401 from the server — the client redirects the user to `/signin` and the account is not deleted | HTTP response status equals 401 and the `user` row still exists in the database after the failed request |
| User transfers ownership of their last organization while the deletion dialog is already open | The deletion request proceeds because the server re-validates ownership at request time — if the transfer committed before the deletion request arrives the server-side ownership check passes and the deletion completes | The ownership re-check query returns 0 owned organizations and the deletion transaction commits, resulting in the `user` row count equaling 0 |
| User is the owner of multiple organizations and transfers ownership of only 1 before retrying | The ownership check still returns at least 1 remaining owned organization — the blocking message updates to reflect the reduced list and the confirmation dialog remains unavailable | The blocking message element lists only the remaining owned organizations and the confirmation dialog element count in the DOM equals 0 |
| User navigates away from the settings page while the deletion request is in flight | The deletion request continues processing on the server regardless of client-side navigation — the transaction either commits or rolls back based on server-side execution, not client state | The server processes the request to completion and the `user` row count equals 0 if the transaction committed, or equals 1 if it rolled back |
| Two browser tabs are open on the account settings page and the user confirms deletion in the first tab | The second tab's next data fetch or navigation returns HTTP 401 because all sessions are revoked — the route guard redirects the second tab to `/signin` | HTTP response status in the second tab equals 401 and the window location pathname changes to `/signin` after the next interaction |
| User types the confirmation phrase with trailing whitespace or different casing | The confirmation phrase matching is exact — trailing spaces or incorrect casing do not match and the confirm button remains disabled until the input exactly matches the expected value | The disabled attribute remains present on the confirm button when the input contains trailing whitespace or mismatched casing |

## Failure Modes

- **Account deletion request fails due to a transient D1 database error causing the atomic transaction to roll back completely**
    - **What happens:** The client calls the account deletion endpoint after the user confirms, but the D1 database returns an error during the atomic transaction that revokes sessions, removes memberships, and deletes the user row, causing the entire operation to roll back with no partial changes committed to any table.
    - **Source:** Transient Cloudflare D1 database failure, Worker resource exhaustion, or a network interruption between the Worker and the D1 service during the multi-table deletion transaction.
    - **Consequence:** The user sees an error state in the confirmation dialog and the account remains fully intact — all sessions remain valid, all organization memberships are unchanged, and the user can continue using the application normally because the transaction rolled back completely.
    - **Recovery:** The server returns HTTP 500 and logs the transaction error with the user ID and timestamp — the client falls back to displaying a localized error message within the dialog and re-enables the confirm button so the user can retry the deletion once the D1 service recovers from the transient failure.
- **Ownership check returns stale data because the member table read is eventually consistent with a recent ownership transfer**
    - **What happens:** The user recently transferred ownership of an organization to another member, but the ownership check query reads a stale replica of the `member` table that still shows the user as the owner, causing the client to display the ownership blocking message even though the transfer has already committed on the primary database.
    - **Source:** Eventual consistency lag in the D1 database read replica used by the ownership check query, where the ownership transfer transaction committed on the primary but has not propagated to the replica within the read window.
    - **Consequence:** The user is temporarily unable to proceed with account deletion despite having legitimately transferred all organization ownership — the blocking message lists organizations the user no longer owns, creating confusion and requiring the user to wait and retry.
    - **Recovery:** The user retries the ownership check after a brief interval, at which point the replica catches up to the primary — the server re-queries the `member` table and returns an empty list of owned organizations, allowing the confirmation dialog to open and the deletion to proceed normally.
- **Server-side ownership re-validation fails after the client-side check passed, blocking the deletion at the endpoint level**
    - **What happens:** The client-side ownership check returns 0 owned organizations and the confirmation dialog opens, but between the check and the user clicking confirm, another process assigns the user as owner of an organization — the server-side re-validation within the deletion endpoint detects the new ownership and rejects the request with HTTP 409.
    - **Source:** A race condition where an organization ownership transfer or creation event occurs between the client-side preflight ownership check and the server-side re-validation embedded in the deletion transaction.
    - **Consequence:** The user sees an error in the confirmation dialog after typing the phrase and clicking confirm — the account is not deleted and the user must resolve the new ownership before retrying, which is the correct behavior because the server-side check prevents deleting an account that now owns an organization.
    - **Recovery:** The server rejects the deletion with HTTP 409 and returns the list of newly owned organizations — the client falls back to closing the confirmation dialog and displaying the ownership blocking message with the updated list so the user can transfer or delete the newly owned organizations before retrying.
- **Session cookie clearance fails on the client after a successful server-side deletion, leaving a stale cookie in the browser**
    - **What happens:** The server successfully commits the deletion transaction and returns HTTP 200 with a `Set-Cookie` header clearing the session cookie, but the browser fails to process the cookie clearance header due to a client-side cookie policy or extension interference, leaving a stale session cookie that the browser continues to send with subsequent requests.
    - **Source:** Browser cookie policy restrictions, a third-party browser extension that intercepts or blocks `Set-Cookie` headers, or a client-side storage API failure that prevents the session cookie from being removed from the cookie jar.
    - **Consequence:** The browser sends the stale session token with subsequent requests, but the server has already deleted all session rows — every request returns HTTP 401 because the session token resolves to no valid session, effectively locking the user out of any authenticated action.
    - **Recovery:** The server returns HTTP 401 for every request bearing the stale token, and the client-side route guard falls back to redirecting the user to `/signin` — the redirect clears local state and the stale cookie expires based on its configured max-age, after which the browser stops sending it with requests.

## Declared Omissions

- This specification does not address soft-deleting or archiving the user account with the ability to restore it within a grace period — the deletion covered by this spec is permanent and irreversible with no recovery mechanism after the transaction commits
- This specification does not address deleting user-generated content within organizations the user belonged to — content attribution and retention policies for departed or deleted users are covered by the data-governance spec as a separate concern
- This specification does not address notifying organization members or admins when a user deletes their account and is removed from their organizations — notification behavior for member departure events is defined in the organization notification spec
- This specification does not address rate limiting on the account deletion endpoint — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly across the platform
- This specification does not address how the danger zone section and deletion dialog render on mobile viewport sizes or within the Tauri desktop wrapper — those platform-specific layout contexts are covered by their respective platform specs in later roadmap phases
- This specification does not address the account deletion flow for guest or anonymous accounts — that behavior is defined in `guest-deletes-anonymous-account.md` as a distinct flow with different cleanup requirements and no ownership check

## Related Specifications

- [user-updates-profile](user-updates-profile.md) — Account settings page spec that defines the settings UI at `/app/settings/account` where the danger zone section containing the delete button is located
- [user-transfers-organization-ownership](user-transfers-organization-ownership.md) — Ownership transfer spec that the user must complete for each owned organization before account deletion can proceed past the ownership check
- [user-deletes-an-organization](user-deletes-an-organization.md) — Organization deletion spec covering the alternative path where the user deletes owned organizations instead of transferring ownership before deleting their account
- [session-lifecycle](session-lifecycle.md) — Session management spec covering session revocation behavior that is triggered as part of the atomic account deletion transaction to invalidate all active sessions
- [guest-deletes-anonymous-account](guest-deletes-anonymous-account.md) — Guest account deletion spec that covers the distinct cleanup flow for anonymous guest accounts, which differs from the full account deletion covered by this spec
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the `deleteUser` endpoint and session revocation mechanisms used in the account deletion transaction
- [database-schema](../foundation/database-schema.md) — Drizzle ORM table definitions for the `user`, `session`, and `member` tables permanently removed or modified during the atomic deletion transaction

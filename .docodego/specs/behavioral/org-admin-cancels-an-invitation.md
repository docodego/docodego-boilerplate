---
id: SPEC-2026-035
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Org Admin, Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# Org Admin Cancels an Invitation

## Intent

This spec defines the flow by which an org admin or org owner cancels an outstanding
invitation from the organization members page at `/app/$orgSlug/members`. The admin
navigates to the Pending tab, which lists all invitations that have not yet been accepted,
declined, or expired. Each row shows the invitee's email, the assigned role, the expiration
date, and a "Cancel" action button. The admin clicks "Cancel" on the target invitation, a
localized confirmation dialog appears, and on confirmation the client calls
`authClient.organization.cancelInvitation()` with the invitation identifier. The server
invalidates the invitation token and sets the status to "canceled." The Pending tab
refreshes automatically so the canceled invitation no longer appears there. The invitation
moves to the History tab with a "canceled" badge in a neutral accent color, alongside the
invitee's email and the cancellation date. If the invitee clicks the invalidated link, the
application detects the token is no longer valid and renders a localized message with no
action buttons other than a link to the home or sign-in screen. Cancellation does not block
re-inviting the same email address; the duplicate-check no longer applies once the original
invitation is canceled.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| oRPC mutation endpoint (`cancelInvitation`) | write | Admin confirms the cancellation dialog — client calls the endpoint with the invitation ID to set invitation status to "canceled" on the server | The server returns HTTP 500 and the client displays a localized error message inside the confirmation dialog, leaving the invitation status unchanged in the "pending" state until the request succeeds |
| `invitation` table (D1) | read/write | Server reads the invitation record to validate status equals "pending" before writing the "canceled" status and invalidating the token | The database read fails with HTTP 500 and the server rejects the mutation — the client falls back to displaying a localized error, leaving the invitation unchanged in the Pending tab |
| Better Auth organization plugin | read/write | Validates the calling user holds the `admin` or `owner` role before processing the cancellation, then writes the updated invitation status to the database | The server rejects the request with HTTP 403 and logs the unauthorized attempt — no status changes are applied and the client alerts the user that the action failed due to insufficient permissions |
| `@repo/i18n` | read | All dialog text, button labels, confirmation messages, and error strings in the cancellation flow are rendered via i18n translation keys | Translation function falls back to the default English locale strings so the confirmation dialog remains functional and all text remains visible without localized translations |

## Behavioral Flow

1. **[User]** (org admin or org owner) navigates to `/app/$orgSlug/members` and opens
    the Pending tab, which lists all outstanding invitations that have not yet been accepted,
    declined, or expired, with each row showing the invitee's email, the assigned role, the
    expiration date, and a "Cancel" action button
2. **[User]** clicks the "Cancel" button on the specific invitation row they wish to revoke,
    which opens a localized confirmation dialog explaining that the invitee will no longer be
    able to use the invitation link to join the organization
3. **[Branch — admin dismisses the dialog]** If the admin clicks the localized "Cancel"
    button inside the confirmation dialog (not the row-level "Cancel" button), the dialog
    closes without taking any action and the invitation remains in the Pending tab with its
    original status, expiration date, and role assignment intact
4. **[User]** clicks the localized "Confirm" button inside the confirmation dialog to
    proceed with the cancellation, which disables the Confirm button and displays a loading
    indicator while the request is in flight
5. **[Client]** calls `authClient.organization.cancelInvitation()` with the invitation
    identifier extracted from the row that was targeted for cancellation
6. **[Server]** validates that the calling user holds the `admin` or `owner` role in the
    organization, then reads the invitation record to confirm its current status equals
    "pending" before proceeding with the update
7. **[Branch — invitation already canceled or expired]** If the invitation status is not
    "pending" at the time the server processes the request, the server returns HTTP 409 and
    the client closes the dialog, removes the stale row from the Pending tab, and displays
    a localized message indicating the invitation was already resolved
8. **[Server]** sets the invitation status to "canceled" and invalidates the invitation
    token so that any subsequent use of the invitation link returns an invalid-invitation
    response, then returns HTTP 200 confirming the update
9. **[Client]** receives the successful response, closes the confirmation dialog, and
    refreshes the Pending tab so the canceled invitation no longer appears in the list —
    the count of pending invitation rows in the tab decreases by exactly 1
10. **[Client]** moves the canceled invitation to the History tab where it appears with a
    "canceled" badge displayed in a neutral accent color, alongside the invitee's email
    address and the date of cancellation
11. **[Branch — invitee clicks the invalidated link]** If the invitee later clicks the
    original invitation URL, the application resolves the token, detects the invitation
    status is "canceled," and renders a localized message explaining the invitation is
    no longer valid — no acceptance or decline buttons are presented and the invitee
    receives only a link to return to the home page or sign-in screen
12. **[Branch — admin re-invites the same email]** After cancellation the admin can
    return to the Pending tab, click "Invite member," enter the same email address, and
    issue a fresh invitation because the duplicate-check no longer blocks re-inviting an
    email whose only existing invitation has status "canceled" — the canceled record
    remains in the History tab for reference alongside the new pending invitation

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| pending_tab_idle | dialog_open | Admin clicks the "Cancel" button on a pending invitation row | Calling user's role in the `member` table equals `admin` or `owner` |
| dialog_open | pending_tab_idle | Admin clicks the "Cancel" button inside the confirmation dialog | Dialog dismiss action received without submitting confirmation |
| dialog_open | submitting | Admin clicks the "Confirm" button inside the confirmation dialog | Confirm button is enabled and invitation ID is non-empty |
| submitting | cancellation_success | Server returns HTTP 200 with invitation status updated to "canceled" | Invitation token invalidated and status written to database |
| submitting | cancellation_error | Server returns non-200 or network error during the mutation call | Database write failed or role validation rejected the request |
| submitting | already_resolved | Server returns HTTP 409 because invitation status is not "pending" | Invitation was already canceled or expired before the server processed the request |
| cancellation_error | dialog_open | Client re-enables Confirm button and displays error inside the dialog | Error message is visible and the dialog remains open for retry |
| cancellation_success | pending_tab_refreshed | Client closes the dialog and removes the canceled row from the Pending tab | Pending tab row count decreases by exactly 1 after the refresh |
| pending_tab_refreshed | history_tab_updated | Client adds the canceled invitation to the History tab with the "canceled" badge | History tab entry is present with invitee email and cancellation date |

## Business Rules

- **Rule admin-or-owner-only:** IF the calling user's role in the organization is not
    `admin` or `owner` THEN the server rejects the `cancelInvitation` call with HTTP 403
    and no invitation status is changed regardless of the client-side button visibility guard
- **Rule pending-status-required:** IF the invitation's current status is not "pending"
    at the time the server processes the cancellation THEN the server returns HTTP 409 and
    no write is performed — the client removes the stale row from the Pending tab and
    displays a localized already-resolved message to the admin
- **Rule token-invalidation:** IF the cancellation completes successfully THEN the
    invitation token is invalidated so that any request to the invitation URL returns an
    invalid-invitation response and the count of successful acceptances using the canceled
    token equals 0
- **Rule pending-tab-removal:** IF the server returns HTTP 200 for the cancellation THEN
    the client removes the invitation row from the Pending tab and the count of Pending tab
    rows decreases by exactly 1 — the invitation is no longer listed under pending entries
- **Rule history-tab-entry:** IF the cancellation succeeds THEN the canceled invitation
    appears in the History tab with a "canceled" badge and a neutral accent color alongside
    the invitee's email and the ISO-formatted cancellation date
- **Rule duplicate-check-lifted:** IF an invitation's status is "canceled" THEN the
    duplicate-check no longer blocks the admin from issuing a new invitation to the same
    email address — the count of duplicate-check rejections for a canceled email equals 0
- **Rule no-action-buttons-for-invitee:** IF the invitee clicks an invalidated invitation
    URL THEN the application renders a localized invalid-invitation message with 0 action
    buttons and provides only a link to the home page or sign-in screen

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Org Owner | View the Pending tab, click "Cancel" on any pending invitation row, confirm the cancellation dialog, trigger `cancelInvitation` on the server with full authorization, and re-invite the same email after cancellation | Cancel an invitation that is not in "pending" status — server returns HTTP 409 for non-pending invitations regardless of the owner's role | Sees all pending invitation rows in the Pending tab and the "Cancel" button is rendered and clickable on each row |
| Org Admin | View the Pending tab, click "Cancel" on any pending invitation row, confirm the cancellation dialog, and trigger `cancelInvitation` on the server with full authorization identical to the owner role for this specific action | Cancel an invitation that is not in "pending" status — server returns HTTP 409, and cancel invitations belonging to organizations where the user holds only the `member` role | Sees all pending invitation rows in the Pending tab and the "Cancel" button is rendered and clickable on each row |
| Org Member | None — regular members cannot view the Pending tab or access any invitation management actions including cancellation | Click "Cancel" on any invitation row, open the cancellation confirmation dialog, or call `cancelInvitation` — server returns HTTP 403 for any attempt | The Pending tab and invitation management controls are not rendered for members — the count of Cancel buttons visible to a member equals 0 |
| Unauthenticated visitor | None — the route guard redirects unauthenticated visitors to `/signin` before the members page renders | Access the members page, the Pending tab, or any invitation management feature | The members page is not rendered — the redirect to `/signin` occurs before any members component is mounted |

## Constraints

- The `cancelInvitation` endpoint enforces the `admin` or `owner` role server-side by
    reading the calling user's role from the `member` table before processing — the count
    of successful cancellations initiated by `member`-role users equals 0
- The server validates the invitation status equals "pending" before writing the
    "canceled" status — the count of write operations on non-pending invitations equals 0
- The invitation token is invalidated atomically with the status update — the count of
    successful invitation acceptances using a token whose status is "canceled" equals 0
- The Pending tab row count decreases by exactly 1 after a successful cancellation —
    the count of canceled invitations still visible in the Pending tab equals 0 after
    the client refresh
- The History tab entry for a canceled invitation contains the invitee's email address,
    the "canceled" badge, and the cancellation date — the count of History tab entries
    for this cancellation event equals 1 after the Pending tab refresh
- All text in the cancellation confirmation dialog is rendered via i18n translation
    keys — the count of hardcoded English strings in the dialog component equals 0
- The count of action buttons presented to the invitee on the invalidated invitation
    URL page equals 0 — only a localized message and a home or sign-in link are rendered

## Acceptance Criteria

- [ ] The Pending tab is present on the members page and contains one row per outstanding invitation — the row count equals the count of invitations with status "pending" for the organization
- [ ] Each pending invitation row contains a "Cancel" button — the count of Cancel button elements in the Pending tab equals 1 per row and the total Cancel button count matches the pending invitation row count
- [ ] Clicking "Cancel" on a row opens the confirmation dialog — the dialog element is present and visible after the click, and the dialog element count equals 1
- [ ] The confirmation dialog contains a "Confirm" button and a dismiss "Cancel" button — the count of each button element inside the dialog equals 1
- [ ] Clicking the dismiss "Cancel" button inside the dialog closes the dialog without sending a request — the dialog element is absent from the DOM and the count of network requests to `cancelInvitation` equals 0
- [ ] Clicking "Confirm" calls `cancelInvitation` with the correct invitation ID — the mutation invocation count equals 1 and the payload contains the targeted invitation's ID as a non-empty string
- [ ] The Confirm button is disabled during the in-flight request — the Confirm button `disabled` attribute is present within 100ms of clicking Confirm and the loading indicator element is present
- [ ] The server returns HTTP 200 on a valid cancellation — the HTTP response status equals 200 and the invitation record's status field equals "canceled" in the database
- [ ] After a successful cancellation the Pending tab no longer contains the canceled row — the count of Pending tab rows equals the pre-cancellation count minus 1 after the client refresh
- [ ] After a successful cancellation the History tab contains a new entry with the "canceled" badge — the History tab entry count increases by exactly 1 and the badge element with text "canceled" is present
- [ ] A `cancelInvitation` call from a `member`-role user returns HTTP 403 — the HTTP response status equals 403 and the invitation status in the database remains "pending"
- [ ] A `cancelInvitation` call on an already-canceled invitation returns HTTP 409 — the HTTP response status equals 409 and the count of database write operations equals 0
- [ ] The invitee receives a localized invalid-invitation message when clicking the invalidated URL — the invalid-invitation message element is present and the count of action buttons on the page equals 0
- [ ] After cancellation the admin can issue a new invitation to the same email address — the `inviteMember` call with the previously invited email returns 200 and a new pending invitation row is present in the Pending tab
- [ ] All text in the confirmation dialog is rendered via i18n translation keys — the count of hardcoded English strings in the dialog component equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The admin opens the confirmation dialog but the invitation expires before they click Confirm | The server returns HTTP 409 because the invitation status is no longer "pending" — the client closes the dialog, removes the stale row from the Pending tab, and displays a localized already-resolved message | HTTP response status equals 409 and the count of pending invitation rows in the Pending tab decreases by exactly 1 without a successful cancellation write |
| Two admins simultaneously click Cancel on the same pending invitation in different browser sessions | The first request succeeds and sets the status to "canceled" — the second request arrives at the server and receives HTTP 409 because the invitation status is no longer "pending" | First response status equals 200 and the database invitation status equals "canceled"; second response status equals 409 and the count of database write operations for the second request equals 0 |
| The admin clicks Confirm twice rapidly before the first request completes due to a double-click event | The client disables the Confirm button on the first click so subsequent clicks produce no additional network requests — the server receives at most 1 mutation request per confirmation action | Confirm button disabled attribute is present within 100ms of the first click and the count of `cancelInvitation` network requests equals 1 |
| The cancellation mutation request fails with a network error before receiving a response from the server | The client treats the failure as an error, re-enables the Confirm button, and displays a localized error message inside the confirmation dialog so the admin can retry | The Confirm button is re-enabled within 100ms of the error event, the error message element is present inside the dialog, and the invitation status in the database remains "pending" |
| The admin cancels an invitation and immediately attempts to re-invite the same email address in the same session | The duplicate-check passes because the original invitation status is "canceled" — the `inviteMember` call returns HTTP 200 and a new pending invitation row appears in the Pending tab | The `inviteMember` HTTP response status equals 200, the new pending row is present in the Pending tab, and the History tab shows both the canceled and the new invitation entries |

## Failure Modes

- **The `cancelInvitation` mutation fails due to a transient D1 database write error**
    - **What happens:** The client calls `authClient.organization.cancelInvitation()` but the D1 database returns an error during the status update write, leaving the invitation in the "pending" state with its original token still valid because no partial update was committed to the database.
    - **Source:** Transient Cloudflare D1 database failure or network interruption between the Cloudflare Worker and the D1 binding during the invitation status update write operation.
    - **Consequence:** The invitation remains in the Pending tab and the invitee can still use the original invitation link to accept or decline because the token has not been invalidated and the status is still "pending."
    - **Recovery:** The server returns HTTP 500 and the client falls back to displaying a localized error message inside the confirmation dialog while re-enabling the Confirm button so the admin retries the cancellation after the transient D1 failure resolves.
- **A non-admin user bypasses the client guard and calls `cancelInvitation` directly**
    - **What happens:** A `member`-role user crafts a direct HTTP request to the `cancelInvitation` mutation endpoint using a valid session cookie, bypassing the client-side guard that hides the Cancel button from members, attempting to revoke an invitation without holding the required role.
    - **Source:** Adversarial action where a `member`-role user sends a hand-crafted HTTP request to the mutation endpoint with a valid session token, circumventing the client-side conditional rendering that withholds Cancel controls from non-admin users.
    - **Consequence:** Without server-side role enforcement any member could revoke outstanding invitations unilaterally, disrupting the onboarding of invited colleagues and bypassing the admin-or-owner access control the feature depends on.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after verifying the calling user's role in the `member` table is `admin` or `owner` — the server logs the unauthorized attempt with the user ID and invitation ID for audit and no invitation status changes are applied.
- **The invitee clicks the invitation link after cancellation but before the token invalidation is fully propagated**
    - **What happens:** A brief propagation window exists between the server writing "canceled" to the invitation status and the token invalidation taking effect at the edge — if the invitee resolves the token during this window, the application detects the canceled status during server-side validation and blocks acceptance regardless of token validity.
    - **Source:** Eventual-consistency propagation delay in Cloudflare's edge infrastructure between the D1 write for the status update and the edge cache invalidation for the invitation token lookup during the cancellation operation.
    - **Consequence:** If the acceptance request reaches the server before the status propagates, the server checks the invitation status field directly in D1 and finds "canceled," preventing the acceptance from proceeding even if the token appears structurally valid.
    - **Recovery:** The server always validates invitation status from the D1 source of truth before processing an acceptance — the server rejects the acceptance with an invalid-invitation response and the client notifies the invitee with a localized message explaining the invitation is no longer valid.
- **The History tab fails to display the canceled invitation entry after a successful cancellation**
    - **What happens:** The server returns HTTP 200 confirming the cancellation, the Pending tab removes the row, but the History tab does not refresh or append the canceled invitation entry because the client state update for the History list fails to trigger after the mutation response is processed.
    - **Source:** A missing cache invalidation or state update step in the cancellation success handler that updates the Pending tab list but omits refreshing the History tab list, leaving the History tab stale until the user navigates away and returns to the page.
    - **Consequence:** The admin sees the invitation removed from the Pending tab but cannot verify the cancellation in the History tab during the same session, reducing auditability and potentially causing the admin to re-cancel the same invitation unnecessarily.
    - **Recovery:** The cancellation success handler invalidates both the Pending tab list and the History tab list in the same cache invalidation step — if the History refetch fails the client falls back to a full page reload of the members page, which triggers a fresh query for both tabs on mount and alerts the admin if the reload itself fails.

## Declared Omissions

- This specification does not address inviting a new member to the organization — that behavior is defined in `org-admin-invites-a-member.md` covering the invitation creation form and duplicate-check logic before any invitation exists
- This specification does not address the flow where the invitee accepts an outstanding invitation before the admin clicks Cancel — that behavior is defined in `user-accepts-an-invitation.md` covering the acceptance screen and role assignment steps
- This specification does not address the flow where the invitee declines an outstanding invitation — that behavior is defined in `user-declines-an-invitation.md` covering the decline confirmation and History tab entry for declined invitations
- This specification does not address the system sending the original invitation email to the invitee — that behavior is defined in `system-sends-invitation-email.md` covering the email template and delivery confirmation steps
- This specification does not address invitation expiration — the automatic transition from "pending" to "expired" status based on the expiration date is an infrastructure concern defined in the scheduled-jobs or background-tasks specification
- This specification does not address rate limiting on the `cancelInvitation` endpoint — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly

## Related Specifications

- [org-admin-invites-a-member](org-admin-invites-a-member.md) — Invitation creation flow that produces the pending invitation records this spec cancels, including the duplicate-check that is lifted after a cancellation
- [user-accepts-an-invitation](user-accepts-an-invitation.md) — Invitee-side acceptance flow that is blocked by a canceled invitation status, showing the invalid-invitation screen this spec defines for the invalidated token path
- [user-declines-an-invitation](user-declines-an-invitation.md) — Invitee-side decline flow that shares the History tab display pattern with the canceled badge entry this spec writes on successful cancellation
- [system-sends-invitation-email](system-sends-invitation-email.md) — Email delivery flow for the original invitation that contains the token this spec invalidates when the admin confirms the cancellation
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that validates member roles and executes the invitation status update for the cancellation mutation
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `invitation` table including the `status` and `token` fields read and written during the cancellation operation

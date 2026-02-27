---
id: SPEC-2026-032
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [Org Admin, Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# Org Admin Invites a Member

## Intent

This spec defines the flow by which an organization admin or owner invites a
new member to join their organization from the members page at
`/app/$orgSlug/members`. The page displays all current members in an Active
tab, pending invitations in a Pending tab, and past invitations in a History
tab. The initiating admin or owner clicks the "Invite member" button, completes
a dialog with the invitee's email address and a role assignment of either
Member or Admin, then submits the form. The client calls
`authClient.organization.inviteMember({ email, inviteRole, organizationId })`
to create an invitation record with a 7-day expiry window. An invitation email
is dispatched to the invitee; in development mode this email is logged to the
console rather than dispatched through a mail provider, while in production
the email is delivered via the configured email service. The Pending tab
refreshes automatically to show the new entry. Duplicate invitations for the
same email address within the same organization are rejected with an error
that requires the admin to cancel the existing invitation, wait for expiry, or
use a different address.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| oRPC mutation endpoint (`inviteMember`) | write | Admin submits the invite dialog with a valid email and role — the client calls the endpoint with `{ email, inviteRole, organizationId }` to create the invitation record on the server | The server returns HTTP 500 and the client displays a localized error message inside the invite dialog, leaving no invitation record created and allowing the admin to retry the submission once the endpoint recovers |
| `invitation` table (D1) | read/write | Server reads the invitation table to check for a duplicate pending invitation before writing the new record with the email, role, organizationId, and a 7-day expiry timestamp | The database read fails with HTTP 500 and the server returns error to the client without writing any record — the client alerts the admin with a localized error so the invitation is not partially committed to the database |
| Email delivery service | write | Server dispatches an invitation email to the invitee's address containing the invitation link after writing the invitation record to the `invitation` table successfully | In development mode the email is logged to the console rather than sent — in production the server logs the delivery failure and returns HTTP 500 so the admin retries after the email provider recovers |
| Better Auth organization plugin | read/write | Validates that the calling user holds the `admin` or `owner` role before creating the invitation record, and writes the invitation entry with the role assignment and expiry window | The server rejects the request with HTTP 403 if the role check fails, logs the unauthorized attempt with the user ID and timestamp, and returns error to the client without writing any invitation record |
| `@repo/i18n` | read | All dialog labels, field placeholders, role option text, button labels, and error messages in the invite dialog are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the invite dialog remains fully functional even when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[User]** (organization admin or owner) navigates to
    `/app/$orgSlug/members` and sees the members page with three tabs: Active
    showing all current members, Pending showing outstanding invitations, and
    History showing past invitations; an "Invite member" button is present in
    the top-right area of the page

2. **[User]** clicks the "Invite member" button to begin the invitation flow,
    which causes the invite dialog to open in the foreground

3. **[Client]** renders the invite dialog containing localized labels and two
    input controls: an email address field for the invitee's address and a role
    dropdown with two options — Member and Admin

4. **[User]** enters the invitee's email address into the email field and
    selects the intended role from the dropdown (Member or Admin), then clicks
    the submit button to send the invitation

5. **[Client]** validates that the email field contains a non-empty, valid
    email address format and that a role is selected before allowing submission
    — the submit button is disabled while the fields are empty or invalid

6. **[Client]** calls
    `authClient.organization.inviteMember({ email, inviteRole, organizationId })`
    with the entered values, disabling the submit button and displaying a
    loading indicator while the request is in flight

7. **[Server]** verifies the calling user holds the `admin` or `owner` role in
    the target organization, then queries the `invitation` table to check
    whether a pending invitation for the same email address already exists for
    this organization

8. **[Branch — duplicate invitation exists]** If a pending invitation for the
    same email is found in the `invitation` table, the server returns an error
    indicating a duplicate invitation exists — the dialog displays a localized
    error message and the admin must either wait for the existing invitation to
    expire, cancel it from the Pending tab, or use a different email address

9. **[Server]** creates a new invitation record in the `invitation` table tied
    to the organization with the assigned role and a 7-day expiry window
    calculated from the current timestamp, then dispatches an invitation email
    to the invitee's address containing the invitation link

10. **[Branch — development mode]** In development mode the invitation email is
    logged to the console instead of being dispatched through a real mail
    provider, so the invitation link is accessible for local testing without
    requiring a configured email service

11. **[Server]** returns HTTP 200 confirming the invitation record was created
    and the email was dispatched (or logged in development mode)

12. **[Client]** closes the invite dialog and the Pending tab refreshes
    automatically to show the new invitation entry displaying the invitee's
    email address, the assigned role, and the expiration date computed from the
    7-day window

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| members_page_idle | dialog_open | Admin clicks the "Invite member" button | Calling user's role in the `member` table equals `admin` or `owner` |
| dialog_open | dialog_filled | Admin enters a valid email and selects a role | Email field value is a non-empty valid email format and role dropdown selection is non-empty |
| dialog_filled | dialog_open | Admin clears the email field or deselects the role | Email field value is empty or role dropdown value is empty |
| dialog_filled | submitting | Admin clicks the submit button | Email field value is a valid email format and role dropdown value is non-empty |
| submitting | invite_success | Server returns HTTP 200 with the invitation record created | Invitation record is written to the `invitation` table and email is dispatched |
| submitting | invite_error_duplicate | Server returns an error indicating a duplicate pending invitation | A pending invitation for the same email and organizationId already exists in the `invitation` table |
| submitting | invite_error_server | Server returns HTTP 500 or a non-200 error code | Database write or email dispatch fails during invitation record creation |
| invite_error_duplicate | dialog_filled | Admin dismisses the error and modifies the email field or navigates to cancel the existing invite | Error message is visible and the email field is re-enabled for editing |
| invite_error_server | dialog_filled | Admin dismisses the error and the dialog returns to the filled state | Error message is visible and the submit button is re-enabled for retry |
| invite_success | members_page_idle | Client closes the dialog and the Pending tab refreshes | Dialog element count in the DOM equals 0 and the Pending tab lists the new invitation |

## Business Rules

- **Rule role-gate:** IF the authenticated user's role in the organization is
    not `admin` or `owner` THEN the `inviteMember` endpoint rejects the request
    with HTTP 403 AND the server logs the unauthorized attempt with the user ID
    and timestamp before returning the error response
- **Rule duplicate-prevention:** IF a pending invitation record with the same
    `email` and `organizationId` already exists in the `invitation` table THEN
    the server returns an error to the client AND no new invitation record is
    written — the admin must cancel the existing invitation, wait for the 7-day
    expiry to elapse, or use a different email address
- **Rule seven-day-expiry:** IF a new invitation record is created THEN the
    `expiresAt` field is set to the current timestamp plus exactly 7 days AND
    the invitation link in the email encodes this expiry so the invitee cannot
    accept the invitation after the window has elapsed
- **Rule role-assignment:** IF the admin submits the invite dialog THEN the
    `inviteRole` field in the request payload equals either `member` or `admin`
    AND the server rejects any other role value with HTTP 400 to enforce the
    two-option constraint defined in the dialog dropdown
- **Rule pending-tab-refresh:** IF the server returns HTTP 200 for the invite
    mutation THEN the client closes the invite dialog AND automatically
    refreshes the Pending tab so the new invitation is immediately visible to
    the admin without requiring a manual page reload
- **Rule dev-mode-logging:** IF the server environment is development mode THEN
    the invitation email is logged to the console instead of dispatched through
    the configured email provider AND the invitation record is still written to
    the `invitation` table with the same 7-day expiry as production invitations

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View the members page with Active, Pending, and History tabs, click the "Invite member" button, complete the invite dialog, submit the invitation with Member or Admin role, and see the new entry in the Pending tab after success | Inviting with a role other than Member or Admin — other role values are rejected with HTTP 400 by the server's role validation check | The "Invite member" button is visible and enabled; all three tabs (Active, Pending, History) are visible and accessible |
| Admin | View the members page with Active, Pending, and History tabs, click the "Invite member" button, complete the invite dialog, submit the invitation with Member or Admin role, and see the new entry in the Pending tab after success | Inviting with a role other than Member or Admin — the dropdown contains exactly two options and the server rejects values outside the allowed set with HTTP 400 | The "Invite member" button is visible and enabled; all three tabs (Active, Pending, History) are visible and accessible |
| Member | View the members page showing existing members in the Active tab without access to invitation management controls | Clicking the "Invite member" button — the button is absent from the DOM for non-admin members and any direct API call to `inviteMember` returns HTTP 403 | The "Invite member" button is absent from the DOM; the count of "Invite member" button elements equals 0 for users with the `member` role |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the members page component renders | Accessing `/app/$orgSlug/members` or calling the `inviteMember` endpoint without a valid session | The members page is not rendered; the redirect to `/signin` occurs before any members page UI is mounted or visible |

## Constraints

- The `inviteRole` field in the request payload must equal exactly `member` or
    `admin` — the count of invitation records created with any other role value
    equals 0 because the server returns HTTP 400 for out-of-range role values
- The invitation record `expiresAt` timestamp must equal the creation timestamp
    plus exactly 7 days (604800 seconds) — the count of invitation records with
    an expiry window outside this value equals 0
- The count of pending invitation records for the same `email` and
    `organizationId` combination at any point in time must not exceed 1 — the
    server enforces this by checking for existing pending records before writing
    a new one and returning an error when a duplicate is detected
- The `inviteMember` endpoint enforces the `admin` or `owner` role server-side
    by reading the calling user's role from the `member` table — the count of
    invitation records created by users with a `member` role equals 0
- All dialog text, labels, placeholders, role option labels, and error messages
    are rendered via i18n translation keys — the count of hardcoded English
    string literals in the invite dialog component equals 0
- The submit button is disabled while the email field is empty or contains an
    invalid format — the count of network requests to `inviteMember` with an
    empty or malformed email value equals 0 from the client

## Acceptance Criteria

- [ ] The "Invite member" button is present in the DOM on the members page for an `admin`-role user — the button element count equals 1
- [ ] The "Invite member" button is present in the DOM on the members page for an `owner`-role user — the button element count equals 1
- [ ] The "Invite member" button is absent from the DOM for a `member`-role user — the button element count equals 0
- [ ] Clicking the "Invite member" button opens the invite dialog — the dialog element is present and visible within 200ms of the click event
- [ ] The invite dialog contains an email input field and a role dropdown with exactly 2 options — the option count in the role dropdown equals 2
- [ ] The submit button is disabled when the email field is empty — the disabled attribute is present on the submit button when the email value length equals 0
- [ ] The submit button is enabled after the admin enters a valid email and selects a role — the disabled attribute is absent when both fields contain non-empty valid values
- [ ] Submitting the dialog calls `authClient.organization.inviteMember` with the entered email, selected role, and organization ID — the method invocation count equals 1 and the payload email field is non-empty
- [ ] A successful invitation returns HTTP 200 and a new invitation record exists in the `invitation` table — the response status equals 200 and the invitation row count for the email and organizationId equals 1
- [ ] The invitation record `expiresAt` value equals the creation timestamp plus 604800 seconds — the difference between `expiresAt` and `createdAt` in seconds equals 604800
- [ ] After a successful invitation the dialog closes — the dialog element count in the DOM equals 0 within 500ms of receiving HTTP 200
- [ ] After a successful invitation the Pending tab shows the new entry with the invitee's email, assigned role, and expiration date — the pending invitation row element for the invited email is present and non-empty
- [ ] Submitting an invite for an email that already has a pending invitation returns an error — the error element is present in the dialog and the invitation record count for the email and organizationId remains 1
- [ ] A direct `inviteMember` call from a `member`-role user returns HTTP 403 — the response status equals 403 and the invitation record count in the database equals 0
- [ ] All dialog text and labels are rendered via i18n keys — the count of hardcoded English string literals in the invite dialog component equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Admin submits the invite dialog but the invitee's email address is already an active member of the organization | The server detects that the email belongs to an existing member record and returns an error to the client — the dialog displays a localized error message and no new invitation record is created for an already-active member | The error element is present in the dialog and the invitation record count for the email and organizationId equals 0 after the submission |
| Admin clicks the submit button twice in rapid succession before the first request completes | The client disables the submit button on the first click, preventing duplicate invitation requests — the server receives at most 1 `inviteMember` call per dialog submission and exactly 1 invitation record is written | The disabled attribute is present on the submit button within 100ms of the first click and the invitation record count for the email equals 1 |
| Admin opens the invite dialog but loses network connectivity before submitting | The dialog remains open with the form values intact — if the admin submits while offline the request times out and the dialog displays a localized network error message, allowing the admin to retry once connectivity is restored | The error element is present in the dialog after the timeout event and the invitation record count for the email equals 0 in the database |
| The 7-day expiry window elapses before the invitee accepts the invitation | The invitation record in the `invitation` table is treated as expired — the invitee's link returns an error when they attempt to accept and the admin sees the invitation in the History tab rather than the Pending tab | The invitation acceptance endpoint returns an error for the expired token and the invitation row appears in the History tab with an expired status indicator |
| Admin invites a previously rejected or expired invitee whose email appears in the History tab | A new pending invitation record is created for the email because no current pending invitation exists — the Pending tab shows the new entry and the History tab retains the old record independently | The invitation record count in the Pending tab for the email equals 1 and the History tab record count for the same email equals 1 after the new invite is created |
| Admin cancels the invite dialog after entering an email and selecting a role but without submitting | The dialog closes with no network request sent — the invitation record count for the entered email and organizationId remains unchanged and the Pending tab does not gain a new row | The network request count to `inviteMember` equals 0 after the cancel action and the Pending tab row count remains the same as before the dialog was opened |

## Failure Modes

- **Email delivery service is unavailable when the invitation record is created**
    - **What happens:** The server writes the invitation record to the `invitation` table
        successfully but the subsequent call to the email delivery provider fails due to
        a provider outage or network timeout, so the invitee never receives the invitation
        link in their inbox despite the record existing in the database.
    - **Source:** Transient failure of the configured email delivery service or a network
        interruption between the Cloudflare Worker and the external email provider during
        the dispatch step that follows the successful database write.
    - **Consequence:** The invitation record exists in the `invitation` table with a valid
        7-day expiry but the invitee has no way to discover or act on it because the
        email containing the invitation link was never delivered to their inbox.
    - **Recovery:** The server logs the email delivery failure with the invitation ID and
        invitee address, then returns HTTP 500 — the client alerts the admin with a
        localized error explaining the email was not sent so they can retry or share the
        invitation link through an alternative channel once the email provider recovers.
- **Non-admin user bypasses the client guard and calls the inviteMember endpoint directly**
    - **What happens:** A user with the `member` role crafts a direct HTTP request to the
        `inviteMember` mutation endpoint using a valid session cookie, circumventing the
        client-side UI that hides the "Invite member" button from non-admin members, and
        attempts to create an invitation record without the required role authorization.
    - **Source:** Adversarial or accidental action where a member sends a hand-crafted
        HTTP request to the mutation endpoint with a valid session token, bypassing the
        client-side visibility guard that conditionally renders the invite button only for
        admin and owner role members.
    - **Consequence:** Without server-side enforcement any member could invite external
        parties into the organization without admin or owner approval, bypassing the access
        control model and potentially granting unauthorized access to organization resources.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after verifying
        the calling user's role in the `member` table — the server logs the unauthorized
        attempt with the user ID, organization ID, and timestamp, and no invitation record
        is written to the `invitation` table.
- **Duplicate invitation check fails due to a race condition allowing two concurrent invite submissions**
    - **What happens:** Two admin sessions submit separate invitation requests for the same
        email address within the same organization at nearly the same time — both requests
        pass the duplicate check independently before either write completes, resulting in
        two pending invitation records for the same invitee in the `invitation` table.
    - **Source:** A time-of-check to time-of-use race condition where both Workers read the
        `invitation` table before either has written its new record, causing both duplicate
        checks to pass and both writes to succeed without detecting the conflict during the
        concurrent execution window.
    - **Consequence:** The invitee receives two invitation emails with two distinct links —
        accepting either one succeeds but the second unused invitation record remains in the
        Pending tab until it expires, creating confusion for admins reviewing the invitation
        list and potentially allowing the invitee to rejoin after being removed.
    - **Recovery:** The database schema enforces a unique constraint on the combination of
        `email` and `organizationId` for pending invitation records — if the concurrent
        write violates this constraint the second write returns an error and the server
        retries with a duplicate error response to the client, notifying the admin that
        the invitation already exists.
- **inviteMember mutation request times out before the server responds**
    - **What happens:** The admin clicks submit and the `inviteMember` request is dispatched
        but the Cloudflare Worker takes longer than the client timeout threshold to respond,
        causing the client to receive a timeout error before knowing whether the invitation
        record was created or the email was dispatched.
    - **Source:** Cloudflare Worker cold start latency combined with a D1 write exceeding
        200ms or email provider latency that pushes the total server processing time beyond
        the client-configured request timeout window, leaving the outcome of the invitation
        creation unknown to the client.
    - **Consequence:** The admin sees a timeout error in the invite dialog without knowing
        whether the invitation was created — retrying risks creating a duplicate pending
        invitation, and not retrying leaves the invitee without the email if the server
        request failed before completing the write operation to the database.
    - **Recovery:** The client falls back to re-enabling the submit button and displaying
        a localized timeout error inside the dialog — the admin navigates to the Pending
        tab to check whether the invitation record appears before retrying, and the server
        logs the request ID with its completion status so the admin can verify the outcome
        without guessing.

## Declared Omissions

- This specification does not address the flow by which an invitee accepts or declines
    the invitation email link — that behavior is defined in `user-accepts-an-invitation.md`
    as a separate concern covering invitation token validation, role assignment on accept,
    and the redirect destination after the invitee joins the organization
- This specification does not address cancelling a pending invitation from the Pending
    tab — that behavior is defined in `org-admin-manages-pending-invitations.md` as a
    separate concern covering the cancel action, confirmation dialog, and record deletion
    from the `invitation` table without affecting existing member records
- This specification does not address removing an existing active member from the
    organization — that behavior is defined in `org-admin-removes-a-member.md` covering
    the admin-initiated removal flow that deletes the `member` row and revokes access
- This specification does not address promoting or demoting an existing member's role
    within the organization — that behavior is defined in `org-admin-manages-member-roles.md`
    covering the role assignment controls on the Active members tab
- This specification does not address rate limiting on the `inviteMember` mutation
    endpoint — that behavior is enforced by the global rate limiter defined in
    `api-framework.md` covering all mutation endpoints uniformly across the API layer

## Related Specifications

- [user-accepts-an-invitation](user-accepts-an-invitation.md) — The counterpart flow defining how the invitee receives and accepts the invitation link, validates the token expiry, and joins the organization with the assigned role
- [org-admin-removes-a-member](org-admin-removes-a-member.md) — Admin-initiated removal flow for existing active members, covering the confirmation dialog and `removeMember` endpoint used for involuntary departures from the organization
- [user-leaves-an-organization](user-leaves-an-organization.md) — Voluntary departure flow for members who remove themselves using the same `removeMember` endpoint called with the user's own identity
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that validates member roles, creates invitation records, and manages the `inviteMember` endpoint behavior
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `invitation` and `member` tables read and written during the invitation creation, duplicate check, and expiry enforcement steps
- [shared-contracts](../foundation/shared-contracts.md) — oRPC contract definitions for the `inviteMember` mutation including the Zod schema that validates `email`, `inviteRole`, and `organizationId` before the mutation reaches the database layer

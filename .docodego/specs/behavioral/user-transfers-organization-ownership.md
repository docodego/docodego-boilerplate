---
id: SPEC-2026-029
version: 1.0.0
created: 2026-02-27
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Transfers Organization Ownership

## Intent

This spec defines the flow by which the current owner of an organization
transfers ownership to an existing admin member from within the organization
settings page at `/app/$orgSlug/settings`. The transfer is an irreversible
atomic handoff: the previous owner's role changes to admin and the selected
admin's role changes to owner in a single server-side operation. Only the
current owner can initiate the transfer. Only admin-role members appear as
eligible recipients. The danger zone section containing the transfer control
is hidden from all non-owner members so admins and regular members never see
or interact with it. After transfer, the previous owner's UI refreshes to
reflect their downgraded role and the new owner gains all owner-level
privileges — including billing access, organization deletion, and future
ownership transfers — on their next page load or data fetch.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| oRPC mutation endpoint (`transferOwnership`) | write | Owner confirms the transfer after selecting an admin from the dialog list — the client calls the endpoint with the selected member's ID to execute the atomic role swap on the server | The server returns HTTP 500 and the client displays a localized error message inside the confirmation dialog, leaving both roles unchanged so neither party loses or gains permissions until the request succeeds |
| `member` table (D1) | read/write | Server reads the current member list to populate the eligible admin list in the dialog, and writes both role changes atomically when the owner confirms the transfer | The read fails with a 500 error and the dialog renders an error state instead of the admin list — the write failure rolls back both role changes so no partial ownership state is committed to the database |
| Better Auth organization plugin | read/write | Validates the calling user has the `owner` role before processing the transfer, and updates the `member` rows for both the previous and new owner atomically within the same transaction | The server rejects the transfer with a 500 error and logs the failure — no role changes are applied and the client retries by re-opening the confirmation dialog after the auth system recovers |
| `@repo/i18n` | read | All dialog text, warning messages, button labels, and role-change explanations in the transfer dialog are rendered via i18n translation keys | Translation function falls back to the default English locale strings so the transfer dialog remains functional and the warning text remains visible without localized text |

## Behavioral Flow

1. **[User]** (organization owner) navigates to `/app/$orgSlug/settings` and
    sees the danger zone section at the bottom of the page, which is visible
    exclusively to the current owner and contains destructive actions including
    the "Transfer ownership" button
2. **[User]** clicks the "Transfer ownership" button to initiate the ownership
    handoff flow, which opens a dialog listing all current members who hold
    the admin role within the organization
3. **[Branch — no admin members exist]** If the organization has no members
    with the admin role, the dialog displays an empty state indicating no
    eligible recipients are available and the transfer cannot proceed —
    the owner must promote at least one member to admin before the transfer
    is possible
4. **[User]** reviews the list of eligible admin members and selects one
    admin as the intended new owner of the organization
5. **[Client]** updates the dialog to show a confirmation step with a clear,
    localized warning explaining that the current owner will lose owner-level
    privileges and be downgraded to admin, and the selected admin will gain
    full ownership including billing access, organization deletion rights,
    and the ability to perform future ownership transfers
6. **[User]** explicitly confirms the transfer by clicking the confirm button
    in the confirmation dialog — there is no way to trigger the transfer
    accidentally, as the confirmation step requires a deliberate separate action
7. **[Client]** calls the ownership transfer mutation endpoint with the
    selected admin member's ID, disabling the confirm button and showing
    a loading indicator while the request is in flight
8. **[Server]** verifies the calling user holds the `owner` role, then
    atomically updates both `member` rows in a single database transaction:
    the previous owner's role changes from `owner` to `admin`, and the
    selected admin's role changes from `admin` to `owner`
9. **[Server]** returns HTTP 200 confirming both role changes took effect
    simultaneously — the organization always has exactly one member with the
    `owner` role at every point in time, with zero gap and zero shared
    ownership state between the old and new values
10. **[Client]** closes the transfer dialog and refreshes the settings page
    to reflect the previous owner's new admin role — the danger zone section
    disappears from the settings view because the calling user no longer holds
    the owner role, and all owner-only controls are no longer rendered for them
11. **[New owner]** gains access to all owner-level actions including the
    danger zone section, billing management, organization deletion, and
    future ownership transfers on their next page load or data fetch after
    the transfer completes

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| settings_idle | dialog_open | Owner clicks "Transfer ownership" button | Calling user's role in the `member` table equals `owner` |
| dialog_open | dialog_empty | Dialog renders with 0 admin members in the eligible list | Count of members with `admin` role in the organization equals 0 |
| dialog_open | admin_selected | Owner clicks on one admin member in the eligible list | At least 1 admin member is present in the list and the user clicks a valid list item |
| admin_selected | confirming | Client shows the confirmation step with the localized ownership-change warning | Selected admin member ID is non-empty and the warning text is rendered |
| confirming | transferring | Owner clicks the confirm button in the confirmation dialog | Confirm button is enabled and the selected member ID is non-empty |
| transferring | transfer_success | Server returns HTTP 200 with both role changes applied | Both `member` rows updated atomically in the same transaction |
| transferring | transfer_error | Server returns non-200 or network error | Database transaction rolled back and both roles unchanged |
| transfer_error | confirming | User dismisses the error and the dialog returns to the confirmation step | Error message is visible and the confirm button is re-enabled for retry |
| transfer_success | settings_refreshed | Client closes dialog and reloads settings page with admin role | Danger zone section is absent from the refreshed view because the calling user is now an admin |

## Business Rules

- **Rule owner-only-initiation:** IF the authenticated user's role in the
    organization is not `owner` THEN the danger zone section is not rendered
    on the settings page AND the `transferOwnership` endpoint rejects the
    call with HTTP 403 regardless of the client-side visibility guard
- **Rule admin-only-eligibility:** IF the transfer dialog opens THEN only
    members whose current role equals `admin` appear in the eligible recipient
    list AND members with the `member` role are excluded from the list entirely
    so they cannot be selected as transfer targets
- **Rule atomic-handoff:** IF the owner confirms the transfer THEN the server
    executes both role updates in a single database transaction AND if either
    write fails both changes are rolled back, ensuring the organization never
    has zero owners or two owners at any point during the operation
- **Rule single-owner-invariant:** IF the transfer completes successfully THEN
    the count of `member` rows with `role = owner` for the organization equals
    exactly 1, with the new owner holding the role and the previous owner
    holding the `admin` role
- **Rule no-self-transfer:** IF the selected recipient ID equals the calling
    user's ID THEN the server rejects the transfer with HTTP 400 because
    an owner cannot transfer ownership to themselves
- **Rule danger-zone-visibility:** IF the authenticated user's role is not
    `owner` THEN the danger zone section containing the "Transfer ownership"
    button is not rendered in the settings page DOM and its count in the
    document equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View the danger zone section on the settings page, click "Transfer ownership," select an eligible admin from the dialog list, confirm the transfer, and be downgraded to admin after the handoff completes | Transfer ownership to a member with a non-admin role, transfer ownership to themselves, or trigger the transfer without the explicit confirmation step | Danger zone section is visible and interactive; the "Transfer ownership" button is rendered and clickable |
| Admin | None — admins cannot initiate or request an ownership transfer; they can only receive ownership if the current owner selects and confirms them as the new owner | Open the transfer dialog, click the "Transfer ownership" button, or access any part of the danger zone section (the section is not rendered for admins) | Danger zone section is absent from the settings page DOM; the count of danger zone elements visible to an admin equals 0 |
| Member | None — regular members have no access to the danger zone section and cannot participate in the ownership transfer flow in any capacity | View the danger zone section, open the transfer dialog, or be selected as a transfer recipient (members do not appear in the eligible admin list) | Danger zone section is absent from the settings page DOM; the count of danger zone elements visible to a member equals 0 |
| Unauthenticated visitor | None — the route guard redirects unauthenticated visitors to `/signin` before the settings page renders | Access any part of the settings page including the transfer flow | The settings page is not rendered; the redirect to `/signin` occurs before any settings component is mounted |

## Constraints

- The `transferOwnership` mutation endpoint enforces the `owner` role
    server-side by reading the calling user's role from the `member` table
    before processing the request — the count of successful transfers
    initiated by non-owner users equals 0
- Both role updates are executed in a single atomic database transaction —
    the count of states where the organization has 0 owners or 2 owners
    in the `member` table equals 0 at every observable point during the transfer
- Only members with the `admin` role appear in the eligible recipient list
    in the transfer dialog — the count of non-admin members rendered in the
    list equals 0
- The confirmation dialog requires an explicit confirm action from the owner
    before the mutation is called — the count of transfers triggered without
    the confirmation step equals 0
- The server rejects self-transfer attempts where the recipient ID equals the
    calling user's ID with HTTP 400 — the count of successful self-transfers
    equals 0
- After a successful transfer the previous owner's settings view no longer
    renders the danger zone section — the count of danger zone DOM elements
    visible to the downgraded user equals 0 after the page refreshes
- All text in the transfer dialog including the warning message, button
    labels, and role descriptions is rendered via i18n translation keys —
    the count of hardcoded English strings in the dialog component equals 0

## Acceptance Criteria

- [ ] The danger zone section containing the "Transfer ownership" button is present in the DOM when the owner views the settings page — the danger zone element count equals 1 for an owner-role user
- [ ] The danger zone section is absent from the DOM when an admin views the settings page — the count of danger zone elements in the DOM equals 0 for an admin-role user
- [ ] The danger zone section is absent from the DOM when a member views the settings page — the count of danger zone elements in the DOM equals 0 for a member-role user
- [ ] Clicking "Transfer ownership" opens the transfer dialog and the dialog element is present and visible — the dialog count in the DOM equals 1 after the button click
- [ ] The transfer dialog lists only members with the `admin` role — the count of list items in the dialog equals the count of admin-role members and the count of member-role items in the list equals 0
- [ ] When no admin members exist the dialog shows an empty state and the confirm button is absent — the list item count equals 0 and the confirm button element is absent from the dialog
- [ ] Selecting an admin from the list advances the dialog to the confirmation step with the localized warning text present — the confirmation step element is visible and the warning text element is present in the DOM
- [ ] The confirmation step displays a warning that the current owner will be downgraded to admin and the selected admin will gain full ownership — both role-change descriptions are present as non-empty text elements in the dialog
- [ ] Clicking confirm calls the `transferOwnership` mutation with the selected member's ID — the mutation invocation count equals 1 and the payload contains the selected member's ID as a non-empty string
- [ ] The server executes both role changes atomically — after a successful transfer the previous owner's `member` row role equals `admin` and the new owner's `member` row role equals `owner`, with count of owner rows equaling 1
- [ ] After a successful transfer the client refreshes the settings page and the danger zone section is absent from the DOM — the danger zone element count equals 0 after the refresh for the previous owner
- [ ] A `transferOwnership` call from an admin-role user returns HTTP 403 and both member roles remain unchanged — the response status equals 403 and the count of role changes in the database equals 0
- [ ] A `transferOwnership` call where the recipient ID equals the calling user's ID returns HTTP 400 — the response status equals 400 and the count of role changes in the database equals 0
- [ ] The count of hardcoded English strings in the transfer dialog component equals 0 — all text is rendered via i18n translation keys

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The owner opens the transfer dialog and the only admin is removed from the organization by another session before the owner confirms | The eligible admin list becomes stale and the server rejects the transfer with HTTP 400 because the selected member no longer holds the admin role — the client displays a localized error and re-fetches the admin list so the owner sees the current state | HTTP response status equals 400 and the dialog re-renders with an updated admin list that excludes the removed member |
| The owner selects an admin and confirms, but the mutation request is submitted twice due to a double-click on the confirm button | The client disables the confirm button on the first click and ignores subsequent clicks — the server receives at most 1 mutation request per confirmation action and the transfer executes exactly once | Confirm button disabled attribute is present within 100ms of the first click and the network log shows exactly 1 mutation request |
| The owner initiates a transfer while the organization has exactly 1 admin who is also the only other member | The dialog shows 1 eligible recipient and the transfer proceeds normally — the previous owner becomes an admin alongside the new owner, resulting in an organization with 1 owner and 1 admin | After the transfer the `member` table contains exactly 1 row with `role = owner` and 1 row with `role = admin`, and the count of member rows equals 2 |
| The transfer mutation request times out before receiving a response due to a network interruption | The client treats the timeout as a failure and re-enables the confirm button, displaying a localized timeout error inside the dialog — the owner retries by clicking confirm again after the network recovers | The confirm button is re-enabled within 100ms of the timeout event, the error element is present in the dialog, and the mutation count in the activity log equals 1 for the failed attempt |
| A new owner who received ownership tries to transfer ownership again on the same page load without navigating away | The new owner's session does not yet reflect the ownership change on the current page — they must reload the page before the danger zone section appears in their settings view, and the transfer button becomes available after the page fetches their updated role | Before reload the new owner's danger zone element count equals 0; after reload the danger zone element count equals 1 and the "Transfer ownership" button is present |
| The owner dismisses the confirmation dialog without clicking confirm and then reopens it | No mutation is called during the dismissal — the dialog returns to the admin selection step on reopening with no admin pre-selected, requiring the owner to restart the selection process | The mutation invocation count equals 0 after the dismissal and the dialog renders in the initial admin list state on the second open |

## Failure Modes

- **Database transaction fails mid-execution leaving ownership in an inconsistent state**
    - **What happens:** The server begins the atomic role-swap transaction but the D1
        write fails after updating one of the two `member` rows, causing the transaction
        to roll back and leaving both roles at their original values before the transfer
        attempt.
    - **Source:** Transient Cloudflare D1 database failure or network interruption
        between the Worker and the D1 binding during the multi-row update transaction
        execution.
    - **Consequence:** The ownership transfer does not complete, both the previous
        owner and the selected admin retain their original roles, and the organization
        continues operating normally with the same ownership structure as before.
    - **Recovery:** The server rolls back the transaction and returns HTTP 500 — the
        client displays a localized error inside the confirmation dialog and re-enables
        the confirm button so the owner retries the transfer after the transient D1
        failure resolves.
- **Non-owner user bypasses the client guard and calls the transfer endpoint directly**
    - **What happens:** An admin or member crafts a direct HTTP request to the
        `transferOwnership` mutation endpoint using a valid session cookie, bypassing
        the client-side danger zone visibility guard that hides the button from
        non-owner users, attempting to seize ownership without authorization.
    - **Source:** Adversarial action where a member or admin sends a hand-crafted
        HTTP request to the mutation endpoint with a valid session token, circumventing
        the client-side route guard that conditionally renders the danger zone section.
    - **Consequence:** Without server-side enforcement any admin could grant themselves
        owner privileges unilaterally, bypassing the intended one-owner-at-a-time
        constraint and breaking billing, deletion, and governance controls for the org.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after
        verifying the calling user's role in the `member` table equals `owner` — the
        server logs the unauthorized attempt with the user ID and timestamp for audit
        purposes and no role changes are applied to any member row.
- **Selected admin is removed from the organization between dialog open and confirm**
    - **What happens:** The owner opens the transfer dialog and selects an admin, but
        before confirming, a concurrent admin action removes that member from the
        organization so the selected member ID no longer exists in the `member` table
        when the transfer mutation reaches the server.
    - **Source:** Concurrent membership management operation where a second admin
        removes or demotes the selected member in a different browser session during
        the time window between the owner selecting the admin and clicking confirm.
    - **Consequence:** The transfer executes against a stale member ID — without
        server-side validation the selected member's role would not be found, leaving
        the previous owner as the only owner and the intended recipient never receiving
        ownership.
    - **Recovery:** The server validates the recipient member ID exists and holds the
        `admin` role before executing the transaction — if the member is not found or
        their role is not `admin`, the server returns HTTP 400 and the client alerts
        the owner that the selected recipient is no longer eligible, prompting them to
        reopen the dialog and select a current admin from the refreshed list.
- **New owner does not see owner controls because their session reflects the old role**
    - **What happens:** The transfer completes on the server but the new owner has the
        settings page open in their browser and their local session still shows the
        `admin` role, so the danger zone section and owner-only controls do not appear
        until they reload the page or trigger a data refetch.
    - **Source:** Stale client-side session cache where the role update is persisted
        server-side but the new owner's frontend has not fetched the updated membership
        record since the transfer was executed by the previous owner.
    - **Consequence:** The new owner cannot access billing, organization deletion, or
        the transfer button until they reload — this creates a temporary gap where
        owner actions are unavailable despite the server having granted the role.
    - **Recovery:** The spec declares that new owner controls become available on the
        next page load or data fetch — the new owner notifies their browser to reload
        the settings page, and the client falls back to displaying the correct danger
        zone section after fetching the updated `member` row from the server.

## Declared Omissions

- This specification does not address deleting the organization from the danger zone —
    that behavior is defined in `user-deletes-an-organization.md` as a separate
    concern covering the deletion confirmation dialog and cascading member removal
- This specification does not address promoting a regular member to admin so they
    become eligible for ownership transfer — that behavior is defined in
    `org-admin-manages-member-roles.md` covering role assignment and demotion flows
- This specification does not address editing organization name or slug from the
    settings page — that behavior is defined in `user-updates-organization-settings.md`
    as a separate concern for the non-destructive settings form
- This specification does not address rate limiting on the `transferOwnership`
    mutation endpoint — that behavior is enforced by the global rate limiter defined
    in `api-framework.md` covering all mutation endpoints uniformly
- This specification does not address notifying the new owner or previous owner via
    email when ownership changes — email notification behavior is defined in the
    notifications infrastructure spec covering organization event emails

## Related Specifications

- [user-updates-organization-settings](user-updates-organization-settings.md) — Organization settings page that hosts the danger zone section containing the "Transfer ownership" button this spec activates
- [user-deletes-an-organization](user-deletes-an-organization.md) — Danger zone sibling action for permanently deleting the organization, also restricted to the owner role and requiring explicit confirmation
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that validates member roles and executes the atomic role-swap transaction for the transfer
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `member` table that stores the `role` field read and written during the ownership transfer operation
- [shared-contracts](../foundation/shared-contracts.md) — oRPC contract definitions for the `transferOwnership` mutation including the Zod schema that validates the recipient member ID before the mutation reaches the database layer
- [api-framework](../foundation/api-framework.md) — Hono middleware stack and global error handler that wraps the transfer endpoint and returns consistent JSON error shapes for 400, 403, and 500 responses consumed by the transfer dialog

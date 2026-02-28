---
id: SPEC-2026-037
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Org Admin, Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# Org Admin Removes a Member

## Intent

This spec defines the involuntary removal flow by which an organization admin
or owner removes another member from their organization. The admin navigates to
the members page at `/app/$orgSlug/members`, locates the target member in the
Active tab, and clicks the delete button on that member's row. The owner's row
does not display a delete button because the owner cannot be removed from their
own organization. A localized confirmation dialog appears to prevent accidental
removals. After the admin confirms, the client calls
`authClient.organization.removeMember({ memberIdOrEmail, organizationId })` to
execute the removal. The server validates that the calling user holds the
`admin` or `owner` role, confirms that the target member is not the
organization owner, deletes the membership record, and revokes all access
immediately. The members list refreshes to reflect the removal. If the removed
member is currently viewing the organization, their next server request fails
the membership check and the application redirects them away from the
organization context. The removed user's account is not deleted; they simply
lose all association with this organization and must receive a new invitation
to rejoin.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth organization plugin (`removeMember`) | write | Admin confirms the removal dialog and the client calls `authClient.organization.removeMember({ memberIdOrEmail, organizationId })` to delete the target member's record | The server returns HTTP 500 and the client falls back to displaying a localized error message inside the confirmation dialog while keeping the membership record intact until the admin retries |
| `member` table (D1) | read/write | Server reads the target member's record to confirm their role is not `owner`, then deletes the record upon a validated admin removal request | The database read or delete operation fails and the server returns HTTP 500 — the client notifies the admin with a localized error message so the membership record is not left in a partial state |
| `session` table (D1) | read | Server reads the active session to resolve the calling user's identity and verify their `admin` or `owner` role in the target organization before processing the removal | The session lookup fails and the server returns HTTP 401 — the client redirects the admin to `/signin` so they can re-authenticate before retrying the removal request |
| Astro client-side router | write | After a successful removal the client refreshes the members list in the Active tab to reflect the departed member's absence from the organization | Navigation falls back to a full page reload via `window.location.assign` if the client router is unavailable, producing the same refreshed members list without a client-side transition |
| `@repo/i18n` | read | All dialog text, confirmation button labels, warning messages, and error strings in the removal flow are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the confirmation dialog remains fully functional but displays untranslated text for non-English locale users |

## Behavioral Flow

1. **[User]** (organization admin or owner) navigates to
    `/app/$orgSlug/members` and views the Active tab, which lists all current
    members of the organization with each row displaying the member's name,
    email, role, and a delete button — except for the owner's row, which does
    not display a delete button because the owner cannot be removed

2. **[User]** clicks the delete button on the target member's row to initiate
    the removal flow, which triggers a localized confirmation dialog to appear
    in the foreground of the page

3. **[Client]** renders a confirmation dialog with localized translated text
    warning the admin that the target member will lose all access to the
    organization's resources immediately upon confirmation, and that the action
    cannot be undone without issuing a new invitation

4. **[User]** reads the warning text and explicitly clicks the confirm button
    to proceed with removing the member, or clicks the cancel button to dismiss
    the dialog without taking any action on the membership record

5. **[Branch -- admin cancels]** The confirmation dialog closes and the target
    member remains in the organization with no changes made to the membership
    record, the session state, or the members list display

6. **[Client]** disables the confirm button, displays a loading indicator, and
    calls `authClient.organization.removeMember({ memberIdOrEmail,
    organizationId })` using the target member's identity to request their
    removal from the organization

7. **[Server]** receives the removal request, reads the calling user's session
    to resolve their identity, and queries the `member` table to confirm that
    the caller holds the `admin` or `owner` role in the target organization

8. **[Branch -- caller lacks admin or owner role]** The server rejects the
    request with HTTP 403 because the calling user does not have the required
    role to remove members from the organization — the client displays a
    localized error message explaining insufficient permissions

9. **[Server]** queries the `member` table for the target member to confirm
    their role is not `owner`, then deletes the `member` row linking the target
    user to the organization, revoking all their access immediately within the
    same database transaction

10. **[Branch -- target is the organization owner]** The server rejects the
    request with HTTP 403 because the organization owner cannot be removed by
    any other member — the client displays a localized error message explaining
    that the owner cannot be removed from the organization

11. **[Server]** returns HTTP 200 confirming the successful removal and the
    client processes the response to refresh the members list display

12. **[Client]** closes the confirmation dialog and refreshes the Active tab
    in the members list so the removed member's row is no longer visible — the
    count of member rows in the Active tab decreases by exactly 1

13. **[Post-removal]** If the removed member is currently viewing the
    organization — browsing its pages or working within its context — their
    next request to the server fails the membership check and the application
    redirects them away from the organization, typically to an organization
    selector or the default landing page

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| members_list_idle | dialog_open | Admin clicks the delete button on a member row | Calling user's role equals `admin` or `owner` and the target member's role does not equal `owner` |
| dialog_open | members_list_idle | Admin clicks the cancel button in the confirmation dialog | None |
| dialog_open | removal_pending | Admin clicks the confirm button in the confirmation dialog | Confirm button is not already in a loading or disabled state |
| removal_pending | removed | Server returns HTTP 200 confirming the membership record deletion | Membership record deletion completes and the `member` row is absent from the database |
| removal_pending | removal_error | Server returns non-200 or the request times out before a response | HTTP response status does not equal 200 or the network request exceeds the timeout threshold |
| removal_error | dialog_open | Client re-enables the confirm button and displays a localized error | Server error was transient and the membership record is still present in the database |
| removed | members_list_refreshed | Client refreshes the Active tab to remove the departed member's row | Active tab row count decreases by exactly 1 after the client-side refresh completes |

## Business Rules

- **Rule admin-or-owner-only:** IF the calling user's role in the organization
    is not `admin` or `owner` THEN the server rejects the `removeMember`
    request with HTTP 403 AND the delete button is absent from the DOM for
    non-admin members, preventing the non-admin from initiating the flow at
    all — the server enforces this independently of the client-side guard
- **Rule owner-cannot-be-removed:** IF the target member's role in the
    organization equals `owner` THEN the server rejects the removal request
    with HTTP 403 AND the delete button is absent from the owner's row in the
    members list — the owner cannot be removed by any member including another
    admin or even the owner themselves through this endpoint
- **Rule no-self-removal-via-admin-flow:** IF the calling user's
    `memberIdOrEmail` equals the target `memberIdOrEmail` in the request THEN
    the server processes the request through the same validation pipeline —
    the admin-initiated removal endpoint does not distinguish between removing
    oneself and removing another member, but the voluntary self-departure
    flow in `user-leaves-an-organization.md` covers the self-removal use case
- **Rule immediate-access-revocation:** IF the `member` row is deleted THEN
    all resource access tied to that membership is revoked within the same
    database transaction, and the count of accessible organization resources
    for the removed user equals 0 from the moment the deletion commits
- **Rule members-list-refresh:** IF the server returns HTTP 200 for the
    removal THEN the client closes the confirmation dialog AND automatically
    refreshes the Active tab so the removed member's row is no longer visible
    to the admin without requiring a manual page reload

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View all member rows in the Active tab, click the delete button on any non-owner member row, confirm the removal dialog, and trigger `removeMember` on the server with full authorization to remove admins and members alike | Removing themselves — the owner's row does not display a delete button and the server rejects any direct API call targeting the owner's membership record with HTTP 403 | The delete button is visible on all non-owner member rows in the Active tab; the owner's own row does not display a delete button |
| Admin | View all member rows in the Active tab, click the delete button on any non-owner and non-self member row, confirm the removal dialog, and trigger `removeMember` on the server to remove regular members from the organization | Removing the organization owner — the owner's row does not display a delete button and the server rejects the request with HTTP 403 if the target is the owner | The delete button is visible on all non-owner member rows in the Active tab; the owner's row does not display a delete button |
| Member | View the members list in the Active tab without access to any removal controls or the ability to remove other members from the organization | Clicking a delete button on any member row — the delete button is absent from the DOM for `member`-role users and any direct API call to `removeMember` returns HTTP 403 | The delete button is absent from all member rows; the count of delete button elements visible to a regular member equals 0 in the Active tab |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the members page component renders any content | Accessing `/app/$orgSlug/members` or calling the `removeMember` endpoint without a valid authenticated session | The members page is not rendered; the redirect to `/signin` occurs before any members UI or removal controls are mounted or visible |

## Constraints

- The `removeMember` endpoint enforces the `admin` or `owner` role server-side
    by reading the calling user's role from the `member` table — the count of
    successful removal operations initiated by `member`-role users equals 0
    because the server validates the caller's role before any deletion occurs
- The delete button is absent from the organization owner's row in the members
    list — the count of delete button elements rendered on the owner's row equals
    0 in the Active tab, and the server independently rejects any removal request
    targeting the owner with HTTP 403
- The server enforces owner protection independently of the client — the count
    of successful removal operations where the target member's role equals `owner`
    equals 0, regardless of the client-side UI state or direct API requests
- After a successful removal the `member` row count for the removed user in the
    target organization equals 0, and all subsequent requests to organization-scoped
    endpoints return HTTP 403 for the removed user's session
- The confirmation dialog contains localized text rendered via i18n translation
    keys — the count of hardcoded English string literals in the removal dialog
    component equals 0

## Acceptance Criteria

- [ ] The delete button is present on each non-owner member row in the Active tab for an `admin`-role user — the delete button element count per non-owner row equals 1
- [ ] The delete button is present on each non-owner member row in the Active tab for an `owner`-role user — the delete button element count per non-owner row equals 1
- [ ] The delete button is absent from the organization owner's row in the Active tab — the delete button element count on the owner's row equals 0
- [ ] The delete button is absent from all member rows for a `member`-role user — the total delete button element count in the Active tab equals 0
- [ ] Clicking the delete button opens a confirmation dialog — the dialog element is present and visible within 200ms of the click event
- [ ] The confirmation dialog contains a warning that the target member will lose all access — the warning text element is present and non-empty within the dialog
- [ ] Cancelling the dialog leaves the membership intact — the `member` row count for the target user in the organization equals 1 after the cancel button is clicked
- [ ] Confirming the removal calls `authClient.organization.removeMember` with the target member's `memberIdOrEmail` and the correct `organizationId` — the method invocation count equals 1 after the confirm click
- [ ] The confirm button displays a loading indicator and its `disabled` attribute is present while the removal request is in flight — the disabled attribute is present within 100ms of the confirm click
- [ ] A successful removal returns HTTP 200 and the `member` row count for the target user in the organization equals 0 — the response status equals 200 and the database row is absent after the call
- [ ] After a successful removal the Active tab no longer contains the removed member's row — the member row count in the Active tab equals the pre-removal count minus 1 after the client refresh
- [ ] A removal attempt targeting the organization owner returns HTTP 403 — the response status equals 403 and the `member` row count for the owner remains 1 after the request
- [ ] A direct `removeMember` call from a `member`-role user returns HTTP 403 — the response status equals 403 and the target member's `member` row count in the organization remains 1
- [ ] The removed member's next request to an organization-scoped endpoint returns HTTP 403 — the response status equals 403 for any request to `/app/{orgSlug}/` using the removed user's session
- [ ] All dialog text, button labels, and error messages are rendered via i18n translation keys — the count of hardcoded English string literals in the removal dialog component equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Admin clicks the confirm button twice in rapid succession before the first request completes | The confirm button is disabled on the first click, preventing duplicate removal requests — the server receives exactly 1 `removeMember` call and no duplicate deletion occurs | The disabled attribute is present on the confirm button within 100ms of the first click and the count of outbound `removeMember` requests equals 1 |
| Two admins simultaneously attempt to remove the same member from different browser sessions | The first request succeeds and deletes the `member` row — the second request arrives at the server and returns HTTP 404 or HTTP 403 because the membership no longer exists | The first response status equals 200 and the `member` row is absent; the second response status equals 404 or 403 and the database state remains unchanged |
| Admin loses network connectivity after clicking confirm but before the server responds with a result | The removal request times out on the client — the dialog remains open with the loading indicator and an error message appears so the admin retries once connectivity returns | The error element is present in the dialog after the request timeout and the `member` row count for the target user remains 1 in the database |
| Admin attempts to remove a member who has already left the organization voluntarily via the leave flow | The server returns HTTP 404 or HTTP 403 because the target member's `member` row no longer exists in the database — the client displays a localized error and refreshes the members list | The response status equals 404 or 403 and the Active tab refreshes to reflect the member's absence with the row count updated accordingly |
| Removed member is currently viewing the organization dashboard when the removal completes on the server | The removed member's next request to the server fails the membership check — the route middleware rejects the request with HTTP 403 and redirects the user away from the organization context | The HTTP response status for the removed member's next request equals 403 and the window location changes away from the former organization's routes |
| Organization has exactly 2 members (the owner and one other) and the owner removes the other member | The removal succeeds and the organization now has exactly 1 remaining member (the owner) — the Active tab shows only the owner's row and no delete buttons are visible | The `member` row count for the organization equals 1 after the removal and the Active tab delete button count equals 0 since only the owner remains |

## Failure Modes

- **Removal request fails due to a transient D1 database error during the member row deletion operation**
    - **What happens:** The client calls `authClient.organization.removeMember` and the server's DELETE query against the `member` table fails due to a transient Cloudflare D1 error or Worker timeout, leaving the membership record intact and the target user still a member of the organization with full access.
    - **Source:** Transient Cloudflare D1 database failure or network interruption between the Worker process and the D1 binding during the DELETE operation execution on the `member` table.
    - **Consequence:** The admin receives an error response after confirming removal — the target member remains in the organization with full access, and the confirmation dialog remains visible until the admin dismisses or retries the operation.
    - **Recovery:** The server returns HTTP 500 and logs the D1 error with the query context and the target member ID — the client falls back to re-enabling the confirm button and displaying a localized error message so the admin retries the removal once the D1 service recovers.

- **Non-admin user bypasses the client guard and calls the removeMember endpoint directly via a crafted HTTP request**
    - **What happens:** A user with the `member` role crafts a direct HTTP request to the `removeMember` endpoint using a valid session cookie, circumventing the client-side guard that hides the delete button from non-admin members, and attempts to remove another member from the organization without authorization.
    - **Source:** Adversarial or accidental action where a `member`-role user sends a hand-crafted API request directly to the removal endpoint, bypassing the client-side conditional rendering that withholds the delete button from users without the `admin` or `owner` role.
    - **Consequence:** Without server-side enforcement any member could remove other members from the organization without admin authorization, disrupting team composition and bypassing the access control model entirely.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after verifying the calling user's role in the `member` table — the server logs the unauthorized attempt with the user ID, target member ID, and timestamp for audit purposes, and no membership record deletion occurs.

- **Membership check after removal does not block the removed user's access to former organization routes**
    - **What happens:** After a successful removal, the removed user's browser still holds a cached session referencing the former organization as `activeOrganizationId` — the user makes a request to an organization-scoped endpoint and the server reads the stale session value instead of checking the live `member` table.
    - **Source:** A stale session cache where the server reads `activeOrganizationId` from the session without verifying it against the current `member` table, allowing the removed user to access data from an organization they no longer belong to during the cache window.
    - **Consequence:** The removed user can view or interact with organization resources they no longer have authorization to access, creating a data exposure window between the removal and the next session refresh or validation cycle on the server.
    - **Recovery:** The route middleware validates each request against the live `member` table rather than the cached session value — if the membership row is absent the server rejects the request with HTTP 403 and notifies the client to clear the stale organization reference from the local state store.

- **Admin attempts to remove the organization owner via a direct API call bypassing the client-side owner protection**
    - **What happens:** An admin crafts a direct HTTP request to the `removeMember` endpoint targeting the organization owner's `memberIdOrEmail`, circumventing the client-side guard that hides the delete button from the owner's row, and attempts to delete the owner's membership record.
    - **Source:** Adversarial action where an admin user sends a hand-crafted API request to the removal endpoint with the owner's identity as the target, bypassing the UI constraint that prevents the delete button from rendering on the owner's row.
    - **Consequence:** Without server-side enforcement the owner would be deleted from the `member` table, leaving the organization with no owner and preventing any future ownership operations or administrative changes.
    - **Recovery:** The server rejects the request with HTTP 403 after reading the target member's role from the `member` table and confirming it equals `owner` — the server logs the unauthorized attempt with the caller's user ID and the target owner ID for audit, and the owner's membership record remains intact.

## Declared Omissions

- This specification does not address voluntary self-departure by a member — that behavior is defined in `user-leaves-an-organization.md` covering the user-initiated leave flow using the same `removeMember` endpoint with the user's own identity
- This specification does not address transferring organization ownership — that behavior is defined in `user-transfers-organization-ownership.md` covering the ownership transfer dialog and the role reassignment steps
- This specification does not address deleting an organization entirely — that behavior is defined in `user-deletes-an-organization.md` covering the confirmation dialog and cascading deletion of all member and resource records
- This specification does not address inviting a member back after removal — the removed user must receive a new invitation processed through the flow defined in `user-accepts-an-invitation.md` to regain membership
- This specification does not address rate limiting on the `removeMember` endpoint — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly
- This specification does not address what happens to content or data created by the removed member within the organization — retention and attribution policies for user-generated content are covered by the data-governance spec

## Related Specifications

- [user-leaves-an-organization](user-leaves-an-organization.md) — Voluntary counterpart to this spec covering user-initiated departure from an organization, sharing the same underlying `removeMember` endpoint called with the user's own identity
- [org-admin-invites-a-member](org-admin-invites-a-member.md) — Invitation creation flow that the admin uses to re-invite a removed member, producing a new pending invitation record in the `invitation` table
- [user-accepts-an-invitation](user-accepts-an-invitation.md) — Invitation acceptance flow that allows a removed user to rejoin the organization after receiving a new invitation from an admin or owner
- [user-transfers-organization-ownership](user-transfers-organization-ownership.md) — Ownership transfer flow that the owner must complete before the owner role can be changed, related to the owner-cannot-be-removed guard in this spec
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that provides the `removeMember` endpoint and enforces the role-based and owner-protection guards
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `member` and `organization` tables read and written during the removal operation and the post-removal membership validation steps

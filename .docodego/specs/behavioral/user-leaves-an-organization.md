---
id: SPEC-2026-030
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [Org Admin, Org Member]
---

[← Back to Roadmap](../ROADMAP.md)

# User Leaves an Organization

## Intent

This spec defines the voluntary departure flow for an authenticated user who
wishes to remove themselves from an organization they belong to. The user
initiates the action from the organization settings page at
`/app/$orgSlug/settings` or from the members list at `/app/$orgSlug/members`.
A confirmation dialog is presented to warn that all access to the
organization's resources will be revoked immediately. After confirmation, the
client calls `authClient.organization.removeMember({ memberIdOrEmail,
organizationId })` with the user's own member identity. The server validates
that the requesting user is not the organization owner, removes the membership
record, and revokes all access. The user is then redirected to another
organization they belong to, or to `/app/onboarding` if this was their only
organization. This flow is voluntary and distinct from involuntary removal by
an administrator.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth organization plugin (`removeMember`) | write | Client calls `authClient.organization.removeMember({ memberIdOrEmail, organizationId })` after the user confirms the departure dialog | The server returns HTTP 500 and the client falls back to displaying a localized error message in the dialog while keeping the user's membership intact until the request succeeds |
| `member` table (D1) | read/write | Server reads the membership record to confirm the user is not the owner, then deletes the record upon a validated departure request | The database read or delete fails, the server returns HTTP 500, and the client notifies the user with a localized error so the membership is not left in a partial state |
| `session` table (D1) | read | Server reads the active session to resolve the calling user's identity and their role within the target organization before processing the removal | The session lookup fails, the server returns HTTP 401, and the client redirects the user to `/signin` so they can re-authenticate before retrying |
| Astro client-side router | write | After a successful departure the client navigates the user away from the former organization's routes to the next available organization or to `/app/onboarding` | Navigation falls back to a full page reload via `window.location.assign` if the client router is unavailable, producing the same destination URL without a client-side transition |
| `@repo/i18n` | read | All dialog text, confirmation button labels, and error messages in the leave-organization UI are rendered via i18n translation keys | Translation function falls back to the default English locale strings so the dialog remains functional but untranslated for non-English users |

## Behavioral Flow

1. **[User]** navigates to `/app/$orgSlug/settings` or `/app/$orgSlug/members`
    and sees a "Leave organization" option visible in the UI — this option is
    present for any authenticated member who does not hold the owner role in
    the current organization

2. **[User]** clicks the "Leave organization" option to initiate the departure
    flow, which triggers the confirmation dialog to appear in the foreground

3. **[Client]** renders a confirmation dialog with localized translated text
    warning the user that they will lose access to all resources within the
    organization immediately upon confirmation, and that rejoining will require
    a new invitation from an organization admin

4. **[User]** reads the warning text and explicitly clicks the confirm button
    to proceed with leaving the organization, or clicks the cancel button to
    dismiss the dialog without taking any action

5. **[Branch — user cancels]** The confirmation dialog closes and the user
    remains a member of the organization with no changes made to the membership
    record or session state

6. **[Client]** disables the confirm button, displays a loading indicator, and
    calls `authClient.organization.removeMember({ memberIdOrEmail,
    organizationId })` using the user's own member identity to request removal

7. **[Server]** receives the removal request, reads the calling user's session
    to resolve their identity, and queries the `member` table to confirm that
    the user holds a non-owner role in the target organization before proceeding

8. **[Branch — user is the organization owner]** The server rejects the request
    with HTTP 403 because the owner cannot leave their own organization — the
    client displays a localized error message explaining that ownership must be
    transferred or the organization deleted before the owner can depart

9. **[Server]** validates that the requesting user is removing their own
    membership record and not another member's record, then deletes the `member`
    row linking the user to the organization, revoking all access immediately

10. **[Server]** returns HTTP 200 confirming the successful departure and the
    client processes the response to determine the redirect destination

11. **[Branch — user belongs to other organizations]** The client redirects the
    user to the next available organization's dashboard at
    `/app/{nextOrgSlug}/` so the user lands on an active workspace without
    interruption

12. **[Branch — this was the user's only organization]** The client redirects
    the user to `/app/onboarding` so they can create a new organization and
    establish a new workspace context

13. **[Post-departure]** Any subsequent navigation attempt to
    `/app/{formerOrgSlug}/...` fails the membership check on the server and the
    route guard redirects the user to an organization selector or their default
    organization, ensuring the former org's routes are inaccessible

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| viewing_org | dialog_open | User clicks "Leave organization" | User is authenticated and their role in the org does not equal `owner` |
| dialog_open | viewing_org | User clicks the cancel button | None |
| dialog_open | departure_pending | User clicks the confirm button | Confirm button is not already in a loading state |
| departure_pending | departed | Server returns HTTP 200 | Membership record deletion completes successfully |
| departure_pending | departure_error | Server returns non-200 | HTTP response status does not equal 200 or request times out |
| departure_error | dialog_open | Client re-enables the confirm button for retry | Server error was transient and the membership record is still present |
| departed | next_org_dashboard | Client navigates to next available org | User has at least 1 remaining organization membership |
| departed | onboarding | Client navigates to `/app/onboarding` | User has 0 remaining organization memberships |

## Business Rules

- **Rule owner-cannot-leave:** IF the authenticated user's role in the
    organization equals `owner` THEN the server rejects the removal request
    with HTTP 403 AND the "Leave organization" option is hidden from the
    owner's view in the UI, preventing the owner from initiating the flow at
    all — the owner must transfer ownership or delete the organization first
- **Rule self-only-removal:** IF the removal request is processed THEN the
    server confirms that the `memberIdOrEmail` in the request payload resolves
    to the same identity as the authenticated session user — the endpoint
    rejects any attempt to remove a different member's record with HTTP 403
    because cross-member removal is the admin's responsibility
- **Rule immediate-access-revocation:** IF the `member` row is deleted THEN
    all resource access tied to that membership is revoked within the same
    database transaction, and the count of accessible organization resources
    for the departed user equals 0 from the moment the deletion commits
- **Rule redirect-to-next-org:** IF the departure succeeds AND the user's
    session contains at least 1 remaining organization membership THEN the
    client navigates to the dashboard of the next available organization so
    the count of seconds the user spends on a blank or broken route equals 0
- **Rule redirect-to-onboarding:** IF the departure succeeds AND the user's
    session contains 0 remaining organization memberships THEN the client
    navigates to `/app/onboarding` and the count of organization memberships
    the user holds equals 0 at the time of navigation

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Member | View the "Leave organization" option on the settings and members pages, open the confirmation dialog, confirm departure, and be redirected after a successful departure | Removing another member's record — that action requires admin or owner role and is covered by `org-admin-removes-a-member.md` | Sees the "Leave organization" option on both the settings page and the members list page |
| Admin | View the "Leave organization" option on the settings and members pages, open the confirmation dialog, confirm departure, and be redirected after a successful departure | Removing themselves if they are also the owner — the owner role check takes precedence over the admin role | Sees the "Leave organization" option alongside other admin-level actions on the settings and members pages |
| Owner | No leave action available — the owner cannot leave their own organization through this flow and must transfer ownership or delete the organization via the separate flows | Initiating the leave flow — the "Leave organization" option is absent from the owner's view and the server rejects any direct API call with HTTP 403 | The "Leave organization" option is absent from the UI so the owner sees 0 instances of the leave trigger on both the settings and members pages |
| Unauthenticated visitor | None — the route guard redirects to `/signin` before any organization page renders | Access to `/app/$orgSlug/settings` or `/app/$orgSlug/members` routes | Organization pages are not rendered; redirect to `/signin` occurs before any UI is visible |

## Constraints

- The `removeMember` call uses the authenticated user's own `memberIdOrEmail`
    — the count of requests that successfully remove a different member's record
    via this endpoint equals 0 because the server validates identity before deletion
- The "Leave organization" UI option is hidden from users whose role in the
    organization equals `owner` — the count of leave triggers visible to the
    owner in the settings page and members list equals 0
- The server enforces the owner-cannot-leave rule independently of the client
    — the HTTP 403 response is returned even if the client somehow renders the
    option for an owner, ensuring 0 unauthorized owner departures reach the database
- After a successful departure the `member` row count for the departed user in
    the target organization equals 0, and all subsequent requests to
    organization-scoped endpoints return HTTP 403 for the departed user
- The redirect destination is determined from the session's remaining
    memberships at the time the HTTP 200 response is received — the count of
    seconds the client spends on a broken route after departure equals 0

## Acceptance Criteria

- [ ] The "Leave organization" option is present and visible on the `/app/$orgSlug/settings` page for a `member`-role user — the option element is present in the DOM and its count equals 1
- [ ] The "Leave organization" option is present and visible on the `/app/$orgSlug/members` page for a `member`-role user — the option element is present in the DOM and its count equals 1
- [ ] The "Leave organization" option is absent from the UI for the organization owner — the option element count in the DOM equals 0 when the authenticated user's role equals `owner`
- [ ] Clicking "Leave organization" opens a confirmation dialog — the dialog element is present and visible within 200ms of the click event
- [ ] The confirmation dialog contains a warning that access to all organization resources will be revoked — the warning text element is present and non-empty within the dialog
- [ ] Cancelling the dialog leaves the membership intact — the `member` row count for the user in the organization equals 1 after the cancel button is clicked
- [ ] Confirming departure calls `authClient.organization.removeMember` with the user's own `memberIdOrEmail` and the correct `organizationId` — the method invocation is present and the count of calls equals 1 after the confirm button is clicked
- [ ] The confirm button displays a loading indicator and its `disabled` attribute is present while the removal request is in flight — the disabled attribute is present within 100ms of the confirm click
- [ ] A successful departure returns HTTP 200 and the `member` row count for the user in the organization equals 0 — the response status equals 200 and the database row is absent after the call
- [ ] After departure when other organizations exist, the window location pathname changes to `/app/{nextOrgSlug}/` — the pathname equals a valid org slug path and the former org slug is absent from the pathname
- [ ] After departure when the departed org was the user's only org, the window location pathname equals `/app/onboarding` — the pathname equals `/app/onboarding` within 1000ms of receiving the HTTP 200 response
- [ ] Navigating to the former organization's routes after departure returns HTTP 403 — the response status equals 403 for any request to `/app/{formerOrgSlug}/` endpoints using the departed user's session
- [ ] A departure attempt by the organization owner returns HTTP 403 — the response status equals 403 and the `member` row count for the owner in the organization remains 1 after the request
- [ ] All dialog text, button labels, and error messages are rendered via i18n translation keys — the count of hardcoded English string literals in the leave-organization UI components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User clicks the confirm button twice in rapid succession before the first request completes | The confirm button is disabled on the first click, preventing duplicate removal requests — the server receives exactly 1 `removeMember` call and the network log count equals 1 | The disabled attribute is present on the confirm button within 100ms of the first click and the count of outbound requests to `removeMember` equals 1 |
| User is removed by an admin at the same moment they submit their own leave confirmation | The server processes whichever request arrives first — the `member` row is deleted by the first successful operation and the second request returns HTTP 404 or HTTP 403 because the membership no longer exists | The HTTP response status for the second concurrent request is either 404 or 403 and the count of `member` rows for the user in the organization equals 0 after both requests complete |
| User loses network connectivity after clicking confirm but before the server responds | The departure request times out on the client — the dialog remains open with the loading state and an error message appears so the user can retry once connectivity is restored | The error element is present in the dialog after the request timeout and the `member` row count for the user remains 1 in the database |
| User's last organization membership is the one they are attempting to leave | The departure succeeds and the client redirects to `/app/onboarding` — the user can create or join a new organization from the onboarding page | The window location pathname equals `/app/onboarding` and the total count of the user's organization memberships in the database equals 0 after the departure |
| User navigates directly to `/app/{formerOrgSlug}/settings` after leaving, using the browser back button | The route guard detects the missing membership and redirects the user away from the former organization's route before any settings UI renders | The window location pathname does not remain on the former org settings route and the settings form element count in the DOM equals 0 |
| Organization has exactly 1 member (the user themselves) and that user leaves | The departure succeeds, the `member` row is deleted, and the organization record remains in the database — orphaned organizations without members are not automatically deleted | The HTTP response status equals 200, the `member` row count equals 0 for the organization, and the `organization` row remains present in the database |

## Failure Modes

- **Removal request fails due to a transient D1 database error during the member row deletion**
    - **What happens:** The client calls `authClient.organization.removeMember` and the server's DELETE query against the `member` table fails due to a transient Cloudflare D1 error or Worker timeout, leaving the membership record intact and the user still a member of the organization.
    - **Source:** Transient Cloudflare D1 database failure or network interruption between the Worker process and the D1 binding during the DELETE operation execution.
    - **Consequence:** The user sees an error response after confirming departure — they remain a member of the organization with full access, and the confirmation dialog remains visible until the user dismisses or retries.
    - **Recovery:** The server returns HTTP 500 and logs the D1 error with the query context — the client falls back to re-enabling the confirm button and displaying a localized error message so the user can retry the departure once the D1 service recovers from the transient failure.
- **Owner attempts to leave the organization via a direct API call bypassing the UI**
    - **What happens:** The organization owner crafts a direct HTTP request to the `removeMember` endpoint with a valid session cookie and their own `memberIdOrEmail`, circumventing the client-side UI that hides the "Leave organization" option for owners, and attempts to remove themselves from the organization.
    - **Source:** Adversarial or accidental action where the owner sends a hand-crafted API request directly to the removal endpoint, bypassing the client-side guard that prevents the owner from initiating the leave flow through the standard UI.
    - **Consequence:** Without server-side enforcement the owner would be deleted from the `member` table, leaving the organization with no owner — this would prevent any future ownership operations and leave the organization in an unmanaged state.
    - **Recovery:** The server rejects the request with HTTP 403 after reading the calling user's role from the `member` table — the `member` row is not deleted and the server logs the unauthorized attempt with the user ID and timestamp for audit purposes.
- **Client navigates to a broken route after departure because the next-org redirect fails**
    - **What happens:** After the server returns HTTP 200 for the departure, the client-side logic that resolves the redirect destination fails to read the remaining organization memberships from the session, causing the navigation to target a stale or undefined route instead of the next valid org dashboard or `/app/onboarding`.
    - **Source:** A client-side state management gap where the session membership list is not refreshed before the redirect logic runs, or a race condition where the session update from the server has not propagated to the client state store at the time of navigation.
    - **Consequence:** The user sees a 404 or a blank dashboard after departure, unable to access any workspace without manually navigating to `/app/onboarding` or refreshing the page to reload the updated session state.
    - **Recovery:** The departure success handler refetches the session membership list before computing the redirect target — if the refetch fails the client falls back to navigating to `/app/onboarding` unconditionally, which always resolves to a valid route regardless of remaining membership count.
- **Membership check after departure does not block access to former organization routes**
    - **What happens:** After a successful departure, the departed user makes a request to an organization-scoped API endpoint such as `/app/{formerOrgSlug}/members` and the server fails to enforce the membership check, returning data instead of HTTP 403 because the session still carries a cached reference to the former organization.
    - **Source:** A stale session cache where the server reads `activeOrganizationId` from the session without verifying it against the current `member` table, allowing the departed user to access data from an organization they no longer belong to.
    - **Consequence:** The departed user can view or interact with organization resources they no longer have authorization to access, creating a data exposure window between the departure and the next session refresh cycle.
    - **Recovery:** The route middleware validates each request against the live `member` table rather than the cached session value — if the membership row is absent the server rejects the request with HTTP 403 and notifies the client to clear the stale organization reference from local state.

## Declared Omissions

- This specification does not address involuntary removal of a member by an organization admin or owner — that behavior is defined in `org-admin-removes-a-member.md` as a separate concern covering the admin-initiated removal flow
- This specification does not address transferring organization ownership before leaving — the owner must complete the transfer via the flow defined in `user-transfers-organization-ownership.md` before this leave flow becomes available to them
- This specification does not address deleting an organization — that behavior is defined in `user-deletes-an-organization.md` covering the confirmation dialog and cascading deletion of all member and resource records
- This specification does not address re-joining an organization after departure — the user must receive a new invitation processed through the flow defined in `user-accepts-an-invitation.md` to regain membership
- This specification does not address rate limiting on the `removeMember` endpoint — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly
- This specification does not address what happens to content or data created by the departed user within the organization — retention and attribution policies for user-generated content are covered by the data-governance spec

## Related Specifications

- [org-admin-removes-a-member](org-admin-removes-a-member.md) — Involuntary counterpart to this spec covering admin-initiated removal of a member from an organization, sharing the same underlying `removeMember` endpoint
- [user-accepts-an-invitation](user-accepts-an-invitation.md) — The invitation acceptance flow that allows a departed user to rejoin an organization after receiving a new invitation from an admin
- [user-creates-first-organization](user-creates-first-organization.md) — Onboarding creation flow that the client redirects to when a user departs their only organization and has zero remaining memberships
- [user-deletes-an-organization](user-deletes-an-organization.md) — Alternative to departure for the organization owner who cannot use this leave flow and must delete the organization or transfer ownership first
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that provides the `removeMember` endpoint and enforces the owner-cannot-leave rule
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `member` and `organization` tables read and written during the departure and redirect-destination resolution steps

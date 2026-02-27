---
id: SPEC-2026-031
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# User Deletes an Organization

## Intent

This spec defines the flow by which an authenticated organization owner
permanently deletes an organization from within the DoCodeGo dashboard.
The deletion entry point is the danger zone section at the bottom of the
organization settings page at `/app/$orgSlug/settings`, which is visible
only to the owner. The owner must confirm the action through an explicit
confirmation dialog that warns of permanent, irreversible data loss before
the client calls `authClient.organization.delete({ organizationId })`. On
success, all member associations, team structures, and organization data
are permanently removed. The owner is redirected to `/app` where standard
entry logic routes them to their next active organization or to
`/app/onboarding` if the deleted org was their only one. All other members
of the deleted organization lose access immediately.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth server SDK (`organization` plugin) | write | Client calls `authClient.organization.delete({ organizationId })` after the owner confirms the deletion dialog to permanently remove the organization and all associated records | The server returns HTTP 500 and the client falls back to displaying a localized error message in the dialog, leaving the organization intact and allowing the owner to close the dialog and retry when the service recovers |
| `organization` table (D1) | write | Server deletes the `organization` row and cascades deletion to all associated `member`, `team`, and `invitation` rows in the same transaction | The database write fails, the transaction rolls back, the server returns HTTP 500, and the client falls back to showing a generic error message — the organization remains fully intact because no partial deletion is committed |
| `member` table (D1) | write | Server removes all `member` rows linked to the deleted organization as part of the cascading delete transaction on confirmation | The cascading delete fails, the transaction rolls back, the server returns HTTP 500, and the organization record is not modified — all existing member associations remain active until the server recovers |
| `@repo/i18n` | read | All confirmation dialog text, warning messages, button labels, and error messages displayed during the deletion flow are rendered via i18n translation keys | Translation function falls back to the default English locale strings so the confirmation dialog remains functional and the owner can still complete or cancel the deletion |
| Astro client-side router | write | After successful deletion the client navigates to `/app` so the standard entry logic can route the owner to their next active organization or to onboarding | Navigation falls back to a full page reload via `window.location.assign("/app")` if the client router is unavailable, producing the same end destination through the standard entry logic |

## Behavioral Flow

1. **[User]** navigates to `/app/$orgSlug/settings` where a danger zone
    section appears at the bottom of the page, visible exclusively to the
    organization owner — admins and regular members do not see this section
2. **[User]** clicks the delete button in the danger zone section to
    initiate the deletion process for the current organization
3. **[Client]** opens a confirmation dialog displaying a clear, localized
    warning that explains deleting the organization cannot be undone and
    that all organization data, member associations, and team structures
    will be permanently removed — the dialog requires an explicit
    confirmation action to proceed
4. **[User]** confirms the deletion by clicking the confirm button inside
    the dialog, which is the only way to proceed — there is no way to
    accidentally trigger deletion with a single click
5. **[Client]** calls `authClient.organization.delete({ organizationId })`
    with the current organization's ID, disabling the confirm button and
    displaying a loading indicator while the request is in flight
6. **[Server]** permanently deletes the organization row and cascades
    removal to all associated member associations, team structures, and
    any pending invitations, then returns HTTP 200 on success
7. **[Client]** receives the success response and navigates to `/app`
    where the standard entry logic takes over for the owner
8. **[Branch — owner has other organizations]** If the owner still belongs
    to other organizations after deletion, the standard entry logic at
    `/app` redirects the owner to their next active organization's dashboard
9. **[Branch — deleted org was the owner's only organization]** If the
    deleted organization was the owner's only organization, the standard
    entry logic redirects the owner to `/app/onboarding` to create a new
    organization
10. **[Branch — other members are actively viewing the org]** All members
    of the deleted organization lose access immediately — any member who
    was viewing the org's dashboard at the time of deletion encounters the
    org context becoming invalid on their next navigation or data fetch,
    and the route guard routes them away from the now-invalid org path
11. **[Branch — owner cancels the dialog]** If the owner clicks cancel or
    closes the confirmation dialog without confirming, the deletion is
    aborted, the dialog closes, and the settings page remains unchanged
    with the organization intact

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| settings_page | dialog_open | Owner clicks the delete button in the danger zone | Authenticated user's role in the organization equals `owner` |
| dialog_open | deleting | Owner clicks the confirm button inside the dialog | Confirmation action is present within the dialog — not a single click from the settings page |
| dialog_open | settings_page | Owner clicks cancel or dismisses the dialog | None — cancel is always available |
| deleting | deletion_complete | Server returns HTTP 200 from the delete endpoint | All organization rows and cascading records are removed from the database |
| deleting | dialog_error | Server returns non-200 or network error | HTTP response status does not equal 200 or the request times out |
| dialog_error | deleting | Owner clicks retry inside the error state of the dialog | Organization record still exists in the database and the retry request can proceed |
| deletion_complete | redirected_to_app | Client navigates to `/app` | Success response received from the delete endpoint |
| redirected_to_app | org_dashboard | Standard entry logic detects the owner belongs to at least 1 remaining org | Count of remaining organization memberships for the owner is greater than 0 |
| redirected_to_app | onboarding | Standard entry logic detects the owner has no remaining organizations | Count of remaining organization memberships for the owner equals 0 |

## Business Rules

- **Rule owner-only-deletion:** IF the authenticated user's role in the
    organization is not `owner` THEN the danger zone section is not
    rendered on the settings page AND the delete endpoint returns HTTP 403
    if called directly — admins and members cannot initiate or complete
    deletion regardless of client-side state
- **Rule explicit-confirmation-required:** IF the owner clicks the delete
    button THEN a confirmation dialog must be presented AND the
    organization is not deleted unless the owner explicitly clicks the
    confirm button within the dialog — a single click on the delete button
    alone does not trigger deletion
- **Rule cascading-deletion:** IF the organization deletion is confirmed
    AND the server commits the transaction THEN all `member` rows, `team`
    rows, and `invitation` rows linked to the deleted organization ID are
    removed in the same atomic transaction so that count of orphaned
    member records referencing a deleted organization equals 0
- **Rule immediate-access-revocation:** IF the organization is deleted
    THEN all active sessions scoped to that organization lose access
    immediately — any subsequent authenticated request by a former member
    referencing the deleted organization's ID returns HTTP 404 or is
    redirected by the route guard
- **Rule post-deletion-routing:** IF the deletion succeeds THEN the client
    navigates to `/app` AND the standard entry logic checks whether the
    owner has remaining organization memberships to determine routing to
    an existing org dashboard or to `/app/onboarding`

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View the danger zone section on the settings page, click the delete button to open the confirmation dialog, confirm deletion to permanently remove the organization and all its records | None — the owner has exclusive authority to delete the organization they own | Danger zone section is present and fully visible including the delete button and all warning text |
| Admin | View organization settings, update name and slug, invite members | Initiate or confirm organization deletion — the danger zone section is not rendered for admins and the delete endpoint returns HTTP 403 for admin-role callers | Danger zone section is absent from the settings page DOM — the delete button is not rendered for admin-role users |
| Member | View organization settings in read-only mode based on the settings spec | Initiate or confirm organization deletion — the danger zone section is not rendered for members and the delete endpoint returns HTTP 403 for member-role callers | Danger zone section is absent from the settings page DOM — the delete button is not rendered for member-role users |
| Unauthenticated visitor | None — route guard redirects to `/signin` before the settings page loads | Access any part of `/app/$orgSlug/settings` or call the delete endpoint | Settings page and danger zone are not rendered — redirect to `/signin` occurs before any component mounts |

## Constraints

- The danger zone section and delete button must not be rendered in the
    DOM for users with roles other than `owner` — the count of delete
    button elements present in the settings page DOM for admin-role and
    member-role users equals 0
- The delete endpoint must return HTTP 403 for any caller whose membership
    role is not `owner` — role is read from the `member` table server-side
    and the count of successful deletions triggered by non-owner callers
    equals 0
- The deletion is atomic — the count of committed transactions that delete
    the `organization` row without also deleting all associated `member`
    rows equals 0, ensuring no orphaned member records remain after deletion
- The confirmation dialog must be present before any deletion request is
    sent to the server — the count of `organization.delete` API calls
    triggered without a prior confirmation dialog interaction equals 0
- All UI text in the danger zone section and confirmation dialog is rendered
    via i18n translation keys — the count of hardcoded English strings in
    the danger zone and dialog components equals 0

## Acceptance Criteria

- [ ] The danger zone section with the delete button is present and visible on the settings page when the authenticated user's role equals `owner` — the delete button element is present in the DOM after the page loads
- [ ] The danger zone section delete button is absent from the settings page DOM when the authenticated user's role equals `admin` or `member` — the delete button element count in the DOM equals 0 for non-owner roles
- [ ] Clicking the delete button opens a confirmation dialog — the dialog element is present and visible within 300ms of the button click and the organization is not deleted at this point
- [ ] The confirmation dialog contains a localized warning message explaining deletion is permanent and irreversible — the warning text element is present and non-empty within the dialog
- [ ] The confirmation dialog contains a confirm button and a cancel button — both button elements are present within the dialog and their count equals 2
- [ ] Clicking cancel closes the dialog without deleting the organization — the dialog element is absent from the DOM after cancel and the organization row still exists in the database
- [ ] Clicking confirm in the dialog calls `authClient.organization.delete({ organizationId })` — the delete API request is present in the network activity log with the correct `organizationId` value
- [ ] The confirm button is disabled and a loading indicator is present while the delete request is in flight — the disabled attribute is present on the confirm button and the loading element is present during the API call
- [ ] On HTTP 200, the server removes the `organization` row — the count of organization rows with the deleted organization's ID in the database equals 0 after the response
- [ ] On HTTP 200, all `member` rows referencing the deleted organization ID are removed — the count of member rows with the deleted organization's ID equals 0 after the response
- [ ] On HTTP 200, the client navigates to `/app` — the window location pathname equals `/app` within 1000ms of the success response
- [ ] If the owner has remaining organizations after deletion, the route at `/app` redirects to an active org dashboard — the window location pathname changes from `/app` to `/app/{nextOrgSlug}/` within 1 navigation cycle
- [ ] If the deleted org was the owner's only organization, the route at `/app` redirects to `/app/onboarding` — the window location pathname equals `/app/onboarding` after the entry logic runs
- [ ] A direct call to the delete endpoint from an `admin`-role user returns HTTP 403 and the organization record is not modified — the response status equals 403 and the count of deleted organization rows equals 0
- [ ] A direct call to the delete endpoint from a `member`-role user returns HTTP 403 and the organization record is not modified — the response status equals 403 and the count of deleted organization rows equals 0
- [ ] A former member navigating to the deleted org's dashboard path is routed away — the window location pathname does not remain on `/app/{deletedOrgSlug}/` and the route guard redirects the user within 1 navigation cycle
- [ ] The count of hardcoded English strings in the danger zone and confirmation dialog components equals 0 — all visible text is rendered via i18n translation keys

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Owner double-clicks the confirm button before the first delete request completes | The client disables the confirm button immediately on the first click, preventing a second request — the server receives exactly 1 delete request and the count of deletion API calls equals 1 | The disabled attribute is present on the confirm button within 100ms of the first click and the network log shows exactly 1 delete request |
| Another member is actively viewing the org dashboard at the exact moment the owner confirms deletion | The member's next navigation or data fetch returns a context-invalid response — the route guard detects the unresolvable org and routes the member away from the stale `/app/{orgSlug}/` path within 1 navigation cycle | The window location pathname for the affected member does not remain on the deleted org path after the next navigation event |
| The delete request fails with HTTP 500 due to a transient D1 error | The dialog displays a localized error state and the organization record remains fully intact — the owner can close the dialog and retry the deletion | The dialog error element is present, the dialog remains open, and the count of deleted organization rows in the database equals 0 |
| Owner initiates deletion but their session expires before they click confirm in the dialog | The client shows the dialog but clicking confirm triggers a 401 response from the server — the client redirects the owner to `/signin` and the organization is not deleted | HTTP response status equals 401 and the organization row still exists in the database |
| Owner opens the deletion dialog and then navigates away by clicking a sidebar link before confirming | The dialog closes and the deletion is aborted — 0 delete requests are sent to the server and the organization remains intact | The dialog element is absent from the DOM after navigation and the organization row count in the database is unchanged |
| Two browser tabs are open on the settings page and the owner confirms deletion in the first tab | The second tab's next data fetch or navigation encounters the invalid org context — the route guard detects the stale org and redirects that tab away | Window location pathname in the second tab changes away from the deleted org path within 1 navigation cycle of the next user interaction |

## Failure Modes

- **Delete API call fails due to a transient D1 database error causing the deletion transaction to roll back**
    - **What happens:** The client calls `authClient.organization.delete({ organizationId })` after the owner confirms, but the D1 database returns an error during the transaction that removes the `organization` row and cascades to `member` and `team` rows, causing the entire operation to roll back with no partial deletions committed.
    - **Source:** Transient Cloudflare D1 database failure, Worker resource exhaustion, or a network interruption between the Worker and the D1 service during the delete transaction.
    - **Consequence:** The owner sees an error state in the confirmation dialog and the organization remains fully intact — all members retain their access and the org dashboard continues to function normally because the transaction rolled back completely.
    - **Recovery:** The server returns HTTP 500 and logs the transaction error with the organization ID and timestamp — the client falls back to displaying a localized error message within the dialog and re-enables the confirm button so the owner can retry the deletion once the D1 service recovers.
- **Non-owner user bypasses the client-side guard and calls the delete endpoint directly with a valid session cookie**
    - **What happens:** A user with `admin` or `member` role in the organization crafts a direct HTTP request to the `organization.delete` endpoint using their valid session token, circumventing the client-side danger zone visibility guard that hides the delete button from non-owner users.
    - **Source:** Adversarial action where a non-owner member inspects the API surface and sends a hand-crafted delete request with a valid session, exploiting the absence of server-side role enforcement if it were missing.
    - **Consequence:** Without server-side enforcement any authenticated member could permanently delete an organization and all its data, destroying the accounts and workspaces of all other members without their knowledge or the owner's consent.
    - **Recovery:** The delete endpoint rejects the request with HTTP 403 after reading the caller's role from the `member` table and confirming it is not `owner` — the organization record is not modified and the server logs the unauthorized attempt with the user ID, organization ID, and timestamp for audit review.
- **Former member accesses a stale cached route after another user deletes the organization**
    - **What happens:** A member is actively viewing the org's dashboard when the owner deletes the organization from another session — the member's browser still holds a valid session and a cached route pointing to `/app/{orgSlug}/`, and subsequent navigation attempts reference an organization ID that no longer exists in the database.
    - **Source:** Asynchronous deletion event where the organization is removed without proactively invalidating the sessions or cached state of other currently-active members viewing the org's pages.
    - **Consequence:** The member encounters route errors, empty API responses, or 404 returns on data fetches referencing the deleted organization ID — the dashboard displays broken or empty state until the member is redirected away.
    - **Recovery:** The route guard detects that the org slug from the URL does not resolve to a valid organization in the member's updated membership list and falls back to redirecting the member to `/app`, where the standard entry logic routes them to a remaining org or to `/app/onboarding` if they have no other organizations — the session remains valid throughout.
- **Post-deletion redirect routes the owner to an incorrect destination because the entry logic reads stale session data**
    - **What happens:** After the deletion succeeds and the client navigates to `/app`, the standard entry logic reads the `activeOrganizationId` from the session which still references the now-deleted organization, causing the entry logic to attempt routing to the deleted org's dashboard instead of to a remaining org or to onboarding.
    - **Source:** A missing session invalidation step in the deletion success handler that leaves the stale `activeOrganizationId` on the session object, causing the entry redirect logic to dereference a deleted organization ID.
    - **Consequence:** The owner is redirected to `/app/{deletedOrgSlug}/` which no longer exists, resulting in a 404 or route error rather than a smooth transition to a remaining organization or to onboarding as the spec requires.
    - **Recovery:** The deletion success handler clears `activeOrganizationId` from the session before navigating to `/app` — if the session update fails the entry logic at `/app` falls back to fetching a fresh membership list from the server, and if the owner has 0 remaining memberships it notifies by redirecting to `/app/onboarding` while if memberships remain it redirects to the first available org dashboard.

## Declared Omissions

- This specification does not address deleting individual members from an organization without deleting the entire organization — that behavior is defined in `org-admin-removes-a-member.md` as a distinct moderation action covering the member removal flow
- This specification does not address transferring organization ownership to another member before deletion — that behavior is defined in `user-transfers-organization-ownership.md` as a prerequisite flow the owner would complete before initiating deletion
- This specification does not address archiving or soft-deleting an organization with the ability to restore it later — the deletion covered by this spec is permanent and irreversible with no recovery path after the transaction commits
- This specification does not address notifying former members via email or in-app notification when their organization is deleted — any notification behavior for deletion events is defined in the organization notification spec as a separate concern
- This specification does not address rate limiting on the `organization.delete` endpoint — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly
- This specification does not address how the deletion danger zone renders on mobile viewport sizes or within the Tauri desktop wrapper — those platform-specific contexts are covered by their respective platform specs in later roadmap phases

## Related Specifications

- [user-updates-organization-settings](user-updates-organization-settings.md) — Organization settings page spec that defines the settings page at `/app/$orgSlug/settings` where the danger zone section containing the delete button is located
- [user-creates-an-organization](user-creates-an-organization.md) — Organization creation spec covering the flow triggered when the deleted org was the owner's only organization and they are redirected to `/app/onboarding` after deletion
- [user-creates-first-organization](user-creates-first-organization.md) — Onboarding organization creation spec covering the `/app/onboarding` destination reached after deletion when the owner has no remaining organizations
- [session-lifecycle](session-lifecycle.md) — Session management spec covering `activeOrganizationId` updates and session invalidation that are relevant to the post-deletion redirect routing behavior
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the `organization` plugin that provides the `delete` endpoint and enforces ownership role checks used in this spec
- [database-schema](../foundation/database-schema.md) — Drizzle ORM table definitions for the `organization`, `member`, and `team` tables permanently removed during the cascading delete transaction
- [api-framework](../foundation/api-framework.md) — Hono middleware stack and global error handler that wraps the delete endpoint and returns consistent HTTP 403, 404, and 500 responses consumed by the confirmation dialog error state

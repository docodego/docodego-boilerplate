---
id: SPEC-2026-045
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User, Org Admin, Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# User Deletes a Team

## Intent

This spec defines the flow by which an organization admin or owner
permanently deletes a team from within their organization on the
DoCodeGo platform. The deletion entry point is the teams page at
`/app/$orgSlug/teams`, where each team row displays a trash icon
that opens a confirmation dialog. The confirmation dialog renders
translated text via `@repo/i18n` asking: "Are you sure you want to
delete '{name}'?" This two-step confirmation prevents accidental
team deletions. The system enforces a safety guard that disables
the trash icon when only one team remains in the organization,
because every organization must have at least one team at all times.
When the user confirms deletion, the client calls
`authClient.organization.removeTeam({ teamId, organizationId })`
and the server deletes the team record along with all team-member
associations tied to it. Organization members who belonged to the
deleted team remain in the organization with their org-level
membership and permissions fully intact — only their association
with that specific team is removed. After successful deletion the
team list refreshes to reflect the removal. Regular members without
the `admin` or `owner` role do not see the trash icon and cannot
initiate this flow.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth server SDK (`organization` plugin, `removeTeam` endpoint) | write | Client calls `authClient.organization.removeTeam({ teamId, organizationId })` after the user confirms the deletion dialog to permanently remove the team and all associated team-member records from the database | The server returns HTTP 500 and the client falls back to displaying a localized error message inside the confirmation dialog while keeping the dialog open so the user can retry the deletion once the service recovers |
| `team` table (D1) via Drizzle ORM | write | Server deletes the `team` row identified by the `teamId` provided in the `removeTeam` request payload after confirming the team exists and belongs to the specified organization | The database delete operation fails, the transaction rolls back, the server returns HTTP 500, and the client falls back to displaying a localized error message — the team record and all associated team-member records remain intact because no partial deletion is committed |
| `teamMember` table (D1) via Drizzle ORM | write | Server deletes all `teamMember` rows linked to the deleted team as part of the cascading delete operation that removes both the team and its membership associations in a single transaction | The cascading delete fails, the transaction rolls back, the server returns HTTP 500, and the team record is not modified — all existing team-member associations remain active until the database service recovers |
| `@repo/i18n` localization layer | read | All confirmation dialog text including the "Are you sure you want to delete '{name}'?" prompt, button labels, and error messages are rendered via i18n translation keys throughout the delete-team confirmation dialog | The translation function falls back to the default English locale strings so the confirmation dialog remains functional but displays untranslated English text for non-English locale users |

## Behavioral Flow

### Initiating Deletion

1. **[User]** (organization admin or owner) navigates to the teams
    page at `/app/$orgSlug/teams`, which lists all existing teams in
    the organization with each row displaying the team name, member
    count, and a trash icon for deletion — the trash icon is only
    visible to users whose role equals `admin` or `owner` in the
    organization

2. **[Client]** renders each team row with a trash icon that is
    enabled when the organization contains more than one team, and
    disabled when only one team remains in the organization because
    the organization must always have at least one team

3. **[User]** clicks the trash icon on a team row to initiate the
    deletion flow, which triggers the client to open a confirmation
    dialog overlay on top of the current page

4. **[Client]** renders a confirmation dialog with localized text
    that asks: "Are you sure you want to delete '{name}'?" where
    `{name}` is the target team's display name interpolated into
    the translated string, plus a confirm button and a cancel button

### Safety Guard

5. **[Branch — last remaining team]** If the organization has
    exactly one team remaining, the trash icon on that team's row is
    disabled and non-clickable, preventing the user from opening the
    confirmation dialog — the organization must always have at least
    one team, so the system prevents deletion of the final team
    entirely by disabling the interaction at the UI level

### Confirming Deletion

6. **[User]** confirms the deletion by clicking the confirm button
    inside the dialog, which is the only way to proceed — there is
    no way to accidentally trigger deletion with a single click on
    the trash icon alone

7. **[Client]** calls
    `authClient.organization.removeTeam({ teamId, organizationId })`
    with the target team's ID and the current organization's ID,
    disabling the confirm button and displaying a loading indicator
    while the request is in flight

8. **[Server]** receives the removal request, verifies that the
    calling user holds the `admin` or `owner` role in the specified
    organization by querying the `member` table, and confirms the
    target team exists and belongs to that organization

9. **[Branch — caller lacks admin or owner role]** The server
    rejects the request with HTTP 403 because the calling user does
    not have the required role to delete teams in the organization —
    the client displays a localized error message explaining
    insufficient permissions inside the confirmation dialog

10. **[Branch — last team server-side guard]** The server checks the
    total team count for the organization and if the target team is
    the only remaining team, the server rejects the request with
    HTTP 403 to enforce the minimum-one-team-per-organization
    business rule independently of the client-side disabled state

11. **[Server]** deletes the `team` row and all associated
    `teamMember` rows linked to the deleted team in a single atomic
    transaction, then returns HTTP 200 confirming the deletion
    completed — organization members who were part of the deleted
    team remain in the organization with their org-level membership
    and permissions fully intact because only the team-specific
    association records are removed

12. **[Client]** receives the successful response, closes the
    confirmation dialog, and refreshes the team list on the teams
    page to reflect the deletion — the deleted team's row is absent
    from the list and the team count decreases by exactly one

13. **[Branch — user cancels the dialog]** If the user clicks the
    cancel button or clicks outside the confirmation dialog without
    confirming, the dialog closes and the teams page remains
    unchanged with the team intact and no deletion request sent to
    the server

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| teams_page | dialog_open | User clicks the trash icon on a team row to open the confirmation dialog | User's role equals `admin` or `owner` and the organization contains more than 1 team so the trash icon is enabled |
| dialog_open | deleting | User clicks the confirm button inside the confirmation dialog to proceed with team deletion | Confirmation action is present within the dialog and the confirm button is not already disabled by a pending request |
| dialog_open | teams_page | User clicks the cancel button or clicks outside the dialog to dismiss it without confirming deletion | None — cancel is always available regardless of dialog state or loading status |
| deleting | deletion_complete | Server returns HTTP 200 from the `removeTeam` endpoint confirming the team and all team-member records are deleted | Database transaction commits and both the `team` row and all associated `teamMember` rows are removed from the database |
| deleting | dialog_error | Server returns non-200 or the network request times out before a response arrives from the server | HTTP response status does not equal 200 or the request exceeds the configured timeout threshold |
| dialog_error | deleting | User clicks the confirm button again to retry the deletion after a transient error is displayed | Team record still exists in the database and the error was a transient server or network failure |
| dialog_error | teams_page | User clicks the cancel button to dismiss the dialog after seeing the error without retrying the deletion | None — cancel is always available from the error state |
| deletion_complete | teams_page (refreshed) | Client closes the dialog and refreshes the team list to remove the deleted team's row from the display | The deleted team's row is absent from the refreshed team list and the team count has decreased by 1 |

## Business Rules

- **Rule last-team-protection:** IF the organization has exactly 1
    team remaining THEN the trash icon on that team's row is disabled
    at the client level AND the server independently rejects any
    `removeTeam` request that would result in 0 teams for the
    organization by returning HTTP 403 — the count of teams in any
    organization after a successful deletion is always greater than
    or equal to 1
- **Rule confirmation-required:** IF the user clicks the trash icon
    on a team row THEN a confirmation dialog must be presented AND
    the team is not deleted unless the user explicitly clicks the
    confirm button within the dialog — a single click on the trash
    icon alone triggers 0 deletion requests to the server
- **Rule member-org-membership-preserved:** IF a team is deleted
    THEN all organization members who were part of the deleted team
    retain their organization-level membership and permissions fully
    intact — the count of `member` table records modified or deleted
    as a result of a `removeTeam` operation equals 0 because only
    `teamMember` association records are removed
- **Rule admin-or-owner-only:** IF the calling user's role in the
    organization is not `admin` and not `owner` THEN the trash icon
    is absent from the DOM for `member`-role users AND the server
    rejects any `removeTeam` request from a `member`-role user with
    HTTP 403 — the server enforces this independently of the
    client-side guard to prevent unauthorized team deletions via
    direct API calls

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View the trash icon on all team rows, click the trash icon to open the confirmation dialog, confirm deletion to permanently remove the team and all its team-member associations from the organization | Delete the last remaining team in the organization — the trash icon is disabled when only 1 team remains and the server returns HTTP 403 for any `removeTeam` request targeting the sole remaining team | The trash icon is visible on every team row in the teams list and the confirmation dialog is accessible for all teams except the last remaining team where the trash icon is disabled |
| Admin | View the trash icon on all team rows, click the trash icon to open the confirmation dialog, confirm deletion to permanently remove the team and all its team-member associations from the organization | Delete the last remaining team in the organization — the trash icon is disabled when only 1 team remains and the server returns HTTP 403 for any `removeTeam` request targeting the sole remaining team | The trash icon is visible on every team row in the teams list and the confirmation dialog is accessible for all teams except the last remaining team where the trash icon is disabled |
| Member | View all team rows on the teams page including team names and member counts but without any access to deletion controls or the ability to remove teams from the organization | Clicking a trash icon on any team row — the trash icon is absent from the DOM for `member`-role users and any direct API call to `removeTeam` returns HTTP 403 from the server | The trash icon is absent from all team rows; the count of trash icon elements visible to a regular member equals 0 on the teams page |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the teams page component renders any content or team data | Accessing `/app/$orgSlug/teams` or calling the `removeTeam` endpoint without a valid authenticated session — the server returns HTTP 401 for direct API calls | The teams page is not rendered; the redirect to `/signin` occurs before any teams UI or deletion controls are mounted or visible |

## Constraints

- The trash icon is disabled on the last remaining team row when
    the organization contains exactly 1 team — the count of enabled
    trash icon elements when the team list contains exactly 1 team
    equals 0, preventing the user from opening the confirmation
    dialog for the sole remaining team
- The `removeTeam` endpoint enforces the `admin` or `owner` role
    server-side by reading the calling user's role from the `member`
    table — the count of successful team deletions initiated by
    `member`-role users equals 0 because the server validates the
    caller's role before any delete operation occurs
- The `removeTeam` endpoint enforces the minimum-one-team rule
    server-side by counting remaining teams before committing the
    delete — the count of organizations with 0 teams after a
    `removeTeam` call equals 0 at all times in the database
- The deletion is atomic — the count of committed transactions that
    delete the `team` row without also deleting all associated
    `teamMember` rows equals 0, ensuring no orphaned team-member
    records remain referencing a deleted team after the transaction
    commits
- All UI text in the confirmation dialog is rendered via i18n
    translation keys — the count of hardcoded English strings in the
    delete-team confirmation dialog component equals 0
- The team list on the teams page reflects the deletion within
    1000ms of receiving a successful HTTP 200 response from the
    server — the deleted team's row element is absent from the list
    after the client-side refresh completes

## Acceptance Criteria

- [ ] The trash icon is present on each team row for an `admin`-role user when the organization contains more than 1 team — the trash icon element count per team row equals 1
- [ ] The trash icon is present on each team row for an `owner`-role user when the organization contains more than 1 team — the trash icon element count per team row equals 1
- [ ] The trash icon is absent from all team rows for a `member`-role user — the total trash icon element count in the teams list equals 0
- [ ] The trash icon is disabled on the sole remaining team row when the organization contains exactly 1 team — the disabled attribute is present on the trash icon element
- [ ] Clicking the trash icon opens a confirmation dialog with the translated text "Are you sure you want to delete '{name}'?" — the dialog element count in the DOM equals 1 and the dialog heading text character count is greater than 0
- [ ] Clicking the cancel button closes the dialog without sending a deletion request — the dialog element is absent from the DOM and the count of `removeTeam` requests sent equals 0
- [ ] Clicking the confirm button calls `authClient.organization.removeTeam({ teamId, organizationId })` — the method invocation count equals 1 after the confirm click
- [ ] The confirm button's `disabled` attribute is present and a loading indicator is visible while the deletion request is in flight — the disabled attribute is present within 100ms of the confirm click
- [ ] A successful deletion returns HTTP 200 and the `team` table row is absent from the database — the response status equals 200 and the team record count for that team ID equals 0
- [ ] All `teamMember` rows referencing the deleted team ID are absent from the database after successful deletion — the `teamMember` record count for the deleted team ID equals 0
- [ ] Organization members who were part of the deleted team retain their `member` table records — the difference between the `member` record count before and after the `removeTeam` call equals 0 for those users
- [ ] The team list row count decreases by exactly 1 after successful deletion — the difference between the pre-deletion teams page row count and the post-deletion row count equals 1
- [ ] A direct `removeTeam` call from a `member`-role user returns HTTP 403 — the response status equals 403 and the team record count for that team ID in the database equals 1
- [ ] A `removeTeam` call targeting the last remaining team in the organization returns HTTP 403 — the response status equals 403 and the team record remains in the database with the organization team count equaling 1
- [ ] The count of hardcoded English strings in the delete-team confirmation dialog component equals 0 — all labels, prompt text, button text, and error messages are rendered via i18n translation keys

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Two admins simultaneously submit `removeTeam` requests for different teams in an organization that has exactly 2 teams, which would bring the count to 0 | The server's team count check inside a transaction ensures only 1 deletion succeeds; the second request receives HTTP 403 with a last-team-protection error code and the database contains exactly 1 team for the organization | The first response status equals 200, the second response status equals 403, and the team count for the organization in the database equals 1 |
| User clicks the confirm button twice in rapid succession before the first `removeTeam` request completes and the server responds | The confirm button is disabled immediately on the first click, preventing a second request — the server receives exactly 1 `removeTeam` call and no duplicate deletion occurs in the database | The disabled attribute is present on the confirm button within 100ms of the first click and the count of outbound `removeTeam` requests equals 1 |
| User's session expires after opening the confirmation dialog but before clicking the confirm button to submit the deletion request | The `removeTeam` request reaches the server with an expired session token — the server returns HTTP 401 and the client redirects the user to `/signin` to re-authenticate before retrying | The server response status equals 401 and the client navigates to `/signin` within 2000ms of receiving the response |
| An admin deletes a team while another member of that team is actively viewing the teams page in a different browser session | The other member's next data fetch or page navigation reflects the updated team list without the deleted team — the deleted team's row is absent from the teams list on the next refresh triggered by navigation or polling | The deleted team's row element is absent from the teams list DOM in the other member's browser after the next data fetch completes |
| User opens the confirmation dialog for a team and then navigates away by clicking a sidebar link before clicking confirm | The dialog closes and the deletion is aborted — 0 `removeTeam` requests are sent to the server and the team remains intact in the database with all team-member associations preserved | The dialog element is absent from the DOM after navigation and the team record count in the database is unchanged |
| The organization transitions from 3 teams to 2 teams after a deletion, and the admin then opens the trash icon on one of the 2 remaining teams | The trash icon is enabled because the organization still has more than 1 team — the confirmation dialog opens and the admin can proceed with the deletion, leaving exactly 1 team remaining | The trash icon element does not have the disabled attribute and the dialog element is present after the click |

## Failure Modes

- **removeTeam request fails due to a transient D1 database error during the server-side transaction for team and team-member record deletion**
    - **What happens:** The client calls `authClient.organization.removeTeam({ teamId, organizationId })` but the D1 database returns an error during the DELETE operations against the `team` and `teamMember` tables, causing the transaction to roll back and leaving all records intact in the database.
    - **Source:** Transient Cloudflare D1 database failure, Worker resource exhaustion, or a network interruption between the Worker process and the D1 database service during the cascading delete transaction execution.
    - **Consequence:** The user sees an error message inside the confirmation dialog and the team remains fully intact in the teams list — no partial deletion is committed because the transaction rolled back, and all team-member associations remain active.
    - **Recovery:** The server returns HTTP 500 and logs the D1 error with the team ID, organization ID, and error context — the client falls back to displaying a localized error message inside the dialog while re-enabling the confirm button so the user can retry the deletion once the D1 service recovers.
- **Non-admin user bypasses the client-side guard and calls the removeTeam endpoint directly via a crafted HTTP request with a valid session cookie**
    - **What happens:** A user with the `member` role crafts a direct HTTP request to the `removeTeam` endpoint using their valid session cookie, circumventing the client-side guard that hides the trash icon from non-admin members, and attempts to delete a team without authorization.
    - **Source:** Adversarial or accidental action where a `member`-role user sends a hand-crafted API request directly to the `removeTeam` endpoint, bypassing the client-side conditional rendering that withholds the trash icon from users without the `admin` or `owner` role.
    - **Consequence:** Without server-side enforcement any member could delete teams in the organization without admin authorization, destroying team structures and removing team-member associations for all affected users without their knowledge or consent.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after verifying the calling user's role in the `member` table — the server logs the unauthorized attempt with the user ID, target team ID, organization ID, and timestamp for audit purposes, and no team or team-member records are deleted.
- **Client-side team count check returns a stale value allowing the user to open the confirmation dialog for the last remaining team in the organization**
    - **What happens:** The client renders the teams page with a cached team count of 2, but another admin has already deleted one team from a different session, leaving only 1 team — the current user sees an enabled trash icon and opens the confirmation dialog for what is now the sole remaining team.
    - **Source:** A stale client-side team list cache or a race condition between two admin sessions where the first admin deletes a team and the second admin's browser has not yet refreshed the team count data from the server.
    - **Consequence:** The user opens the confirmation dialog and clicks confirm for the last remaining team — if the server did not enforce the last-team-protection rule independently, the organization would end up with 0 teams, violating the minimum-one-team business rule.
    - **Recovery:** The server enforces the minimum-one-team rule by counting teams within the delete transaction before committing — the server rejects the request with HTTP 403 and returns error indicating the team cannot be deleted because it is the last remaining team, and the client falls back to displaying the error inside the dialog and refreshing the team list to reflect the current state.

## Declared Omissions

- This specification does not address creating a new team in the organization — that behavior is covered by `user-creates-a-team.md` which defines the creation dialog, validation rules, and the `createTeam` endpoint flow
- This specification does not address renaming an existing team — that behavior is covered by `user-renames-a-team.md` which defines the rename dialog, pre-filled input, and the `updateTeam` endpoint flow
- This specification does not address managing team membership including adding or removing individual members from a team — those operations are defined in `org-admin-manages-team-members.md` covering the TeamMembersDialog
- This specification does not address what happens to team-scoped resources or assignments when a team is deleted — retention and reassignment policies for team-level artifacts are covered by separate data governance specifications
- This specification does not address rate limiting on the `removeTeam` endpoint — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly across the API layer
- This specification does not address how the team deletion controls render on mobile viewport sizes or within the Tauri desktop wrapper — those platform-specific layout contexts are covered by their respective platform specifications in later roadmap phases

## Related Specifications

- [user-creates-a-team](user-creates-a-team.md) — Team creation flow that defines how new teams are added to the organization, which is the inverse operation of the deletion flow defined in this spec
- [user-renames-a-team](user-renames-a-team.md) — Team rename flow that shares the same teams page entry point and permission model requiring `admin` or `owner` role to access team mutation controls
- [org-admin-manages-team-members](org-admin-manages-team-members.md) — Team membership management flow that defines adding and removing members from teams, which intersects with deletion because all team-member associations are cascaded when a team is deleted
- [user-deletes-an-organization](user-deletes-an-organization.md) — Organization deletion flow that cascades to all teams and members within the organization, a higher-level destructive operation that also removes all teams in the process
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that provides the `removeTeam` endpoint and enforces role-based permission guards used in this spec
- [database-schema](../foundation/database-schema.md) — Drizzle ORM table definitions for the `team` and `teamMember` tables permanently removed during the cascading delete transaction in this spec

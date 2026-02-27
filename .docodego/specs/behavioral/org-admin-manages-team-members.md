---
id: SPEC-2026-042
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Org Admin, Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# Org Admin Manages Team Members

## Intent

This spec defines the flow by which an organization admin or owner manages the
membership of a specific team within the organization. The admin navigates to
the teams page at `/app/$orgSlug/teams`, clicks the users icon on a team row
to open the TeamMembersDialog, and then adds or removes members from that team.
Adding a member selects from organization members who are not yet part of the
team and calls `authClient.organization.addTeamMember()` to associate that
person with the team. Removing a member calls
`authClient.organization.removeTeamMember()` to disassociate that person from
the team without affecting their organization-level membership or permissions.
Team membership is entirely independent of organization membership: removing
someone from a team does not revoke their access to the organization or any
other team they belong to. The dialog updates after each add or remove
operation to reflect the current state of the team.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth organization plugin `addTeamMember()` method | write | Admin selects an organization member from the available members list and confirms adding them to the team inside the TeamMembersDialog | The server returns HTTP 500 and the client displays a localized error message inside the TeamMembersDialog while the team membership record remains unchanged until the admin retries the add operation |
| Better Auth organization plugin `removeTeamMember()` method | write | Admin clicks the remove action on a team member row inside the TeamMembersDialog to disassociate that person from the team | The server returns HTTP 500 and the client displays a localized error message inside the TeamMembersDialog while the team membership record remains intact until the admin retries the remove operation |
| `teamMember` table (D1) | read/write | Server reads existing team member records to populate the dialog list, writes a new record when adding a member, and deletes the record when removing a member from the team | The database read or write operation fails and the server returns HTTP 500 — the client alerts the admin with a localized error message so no partial team membership data is committed to the database |
| `member` table (D1) | read | Server reads the `member` table to resolve the list of organization members eligible for team addition by filtering out users who already belong to the target team | The database read operation fails and the server returns HTTP 500 — the client displays a localized error message in the TeamMembersDialog and the admin retries by reopening the dialog once the database recovers |
| `@repo/i18n` | read | All dialog headings, member list labels, add and remove button text, confirmation messages, and error strings in the TeamMembersDialog are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the TeamMembersDialog remains fully functional but displays untranslated text for non-English locale users |

## Behavioral Flow

1. **[Org Admin]** navigates to the teams page at `/app/$orgSlug/teams` and
    views the list of teams for the organization, where each team row displays
    a users icon that opens the team members management dialog

2. **[Org Admin]** clicks the users icon on a specific team row to open the
    TeamMembersDialog, which displays localized labels and all current members
    of that specific team in a scrollable list

3. **[Client]** renders the TeamMembersDialog containing the team name as the
    dialog heading, a list of all current team members with each row showing
    the member's name, email, and a remove action, and a member selection
    control for adding new members to the team

4. **[Org Admin]** selects a member to add from a list of organization members
    who are not yet part of this team — the selection control displays only
    those organization members whose IDs are absent from the current team
    member list, ensuring no duplicate additions

5. **[Client]** calls `authClient.organization.addTeamMember()` with the
    selected member's identity and the target team ID to associate that person
    with the team, disabling the selection control and displaying a loading
    indicator while the request is in flight

6. **[Server]** receives the add request, validates that the calling user holds
    the `admin` or `owner` role in the organization, confirms the target user
    is an existing organization member by querying the `member` table, and
    verifies the target user is not already a member of the team by querying
    the `teamMember` table

7. **[Branch -- target is already a team member]** The server rejects the
    request with an error because the target user already belongs to the team
    — the client displays a localized duplicate membership error message
    inside the TeamMembersDialog and re-enables the selection control

8. **[Branch -- target is not an organization member]** The server rejects the
    request with HTTP 403 because only existing organization members can be
    added to teams — the client displays a localized error explaining that the
    target user is not a member of the organization

9. **[Server]** inserts a new record into the `teamMember` table linking the
    selected organization member to the target team and returns HTTP 200
    confirming the addition was successful

10. **[Client]** updates the TeamMembersDialog immediately to show the newly
    added member in the team members list, removes that person from the
    available members selection control, and re-enables the selection control
    for further additions

11. **[Org Admin]** clicks the remove action on a team member row inside the
    TeamMembersDialog to initiate the removal of that person from the team

12. **[Client]** calls `authClient.organization.removeTeamMember()` with the
    target member's identity and the team ID to disassociate that person from
    the team, disabling the remove action and displaying a loading indicator
    while the request is in flight

13. **[Server]** receives the remove request, validates that the calling user
    holds the `admin` or `owner` role in the organization, and deletes the
    `teamMember` record linking the target user to the team

14. **[Server]** returns HTTP 200 confirming the removal — this removes the
    person from the team only and they remain a full member of the organization
    with all their org-level permissions intact because team membership is
    entirely independent of organization membership

15. **[Client]** updates the TeamMembersDialog to remove the departed member's
    row from the team members list and adds that person back to the available
    members selection control so they can be re-added in the future if needed

16. **[Post-operation]** The dialog updates after each add or remove operation
    to reflect the current state of the team — the team member count displayed
    in the dialog equals the number of `teamMember` records for that team in
    the database at all times

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| teams_list_idle | dialog_open | Admin clicks the users icon on a team row on the teams page | Calling user's role in the `member` table equals `admin` or `owner` for the organization |
| dialog_open | add_member_pending | Admin selects an organization member from the available members list and confirms the addition | Selected member's ID is present in the `member` table and absent from the `teamMember` table for the target team |
| add_member_pending | dialog_open | Server returns HTTP 200 and the client updates the team members list with the newly added member | New `teamMember` record exists in the database linking the added member to the target team |
| add_member_pending | add_member_error | Server returns a non-200 status code or the request times out before a response is received | HTTP response status does not equal 200 or the network request exceeds the timeout threshold |
| add_member_error | dialog_open | Client displays a localized error message and re-enables the member selection control for retry | Error message element is present in the dialog and the selection control is re-enabled for interaction |
| dialog_open | remove_member_pending | Admin clicks the remove action on a team member row inside the TeamMembersDialog | Target member's `teamMember` record exists in the database for the target team |
| remove_member_pending | dialog_open | Server returns HTTP 200 and the client removes the departed member's row from the team members list | The `teamMember` record for the removed member is absent from the database for the target team |
| remove_member_pending | remove_member_error | Server returns a non-200 status code or the request times out before a response is received | HTTP response status does not equal 200 or the network request exceeds the timeout threshold |
| remove_member_error | dialog_open | Client displays a localized error message and re-enables the remove action for retry | Error message element is present in the dialog and the remove action is re-enabled for interaction |
| dialog_open | teams_list_idle | Admin closes the TeamMembersDialog by clicking the close button or clicking outside the dialog | Dialog element is removed from the DOM and the teams list page is visible behind the closed dialog |

## Business Rules

- **Rule org-membership-required-before-team-add:** IF the admin attempts to
    add a user to a team AND that user's record is absent from the `member`
    table for the organization THEN the server rejects the `addTeamMember()`
    request with HTTP 403 because only existing organization members can be
    added to teams — the client displays a localized error explaining that
    the target user must be an organization member before being added to any
    team within that organization
- **Rule team-membership-independent-of-org-membership:** IF a member is
    removed from a team via `removeTeamMember()` THEN that person remains a
    full member of the organization with all their org-level permissions intact
    — the `member` table record for that user is not deleted or modified and
    their access to the organization and all other teams they belong to is
    completely unaffected by the team removal operation
- **Rule admin-or-owner-only:** IF the calling user's role in the organization
    is not `admin` and not `owner` THEN the server rejects both
    `addTeamMember()` and `removeTeamMember()` requests with HTTP 403 AND
    the users icon on team rows is either absent or non-functional for
    `member`-role users — the server enforces this independently of the
    client-side guard to prevent unauthorized team membership modifications
- **Rule duplicate-add-prevention:** IF the admin attempts to add a member who
    already belongs to the target team AND that member's `teamMember` record
    already exists in the database for the target team THEN the server rejects
    the `addTeamMember()` request with an error indicating duplicate membership
    — the count of `teamMember` records for any given member-team pair equals
    exactly 1 at all times, enforced by the server's uniqueness validation

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View the TeamMembersDialog with all current team members listed, add any organization member to the team via `addTeamMember()`, and remove any team member via `removeTeamMember()` | Adding a non-organization-member to a team — the server rejects the request with HTTP 403 because team membership requires prior organization membership | The users icon is visible on all team rows, the member selection control displays all eligible organization members, and the remove action is visible on every team member row |
| Admin | View the TeamMembersDialog with all current team members listed, add any organization member to the team via `addTeamMember()`, and remove any team member via `removeTeamMember()` | Adding a non-organization-member to a team — the server rejects the request with HTTP 403 because team membership requires prior organization membership | The users icon is visible on all team rows, the member selection control displays all eligible organization members, and the remove action is visible on every team member row |
| Member | None — the `member`-role user cannot open the TeamMembersDialog or modify team membership because the users icon interaction is gated behind the admin or owner role check | Opening the TeamMembersDialog, calling `addTeamMember()`, and calling `removeTeamMember()` — any direct API call returns HTTP 403 from the server | The users icon on team rows is either absent from the DOM or visually disabled for `member`-role users, preventing them from initiating any team membership management action |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the teams page component renders any team management content or dialog controls | Accessing `/app/$orgSlug/teams` or calling any team membership endpoint without a valid authenticated session — all requests are redirected or rejected | The teams page is not rendered; the redirect to `/signin` occurs before any teams list, users icons, or TeamMembersDialog controls are mounted or visible |

## Constraints

- The `addTeamMember()` endpoint enforces that the target user is an existing
    organization member by querying the `member` table — the count of successful
    team additions for non-organization-members equals 0 because the server
    validates organization membership before writing to the `teamMember` table
- The `teamMember` table enforces uniqueness on the member-team pair — the
    count of duplicate `teamMember` records for any given member ID and team ID
    combination equals 0 at all times, enforced by the server's validation
    before the INSERT operation completes
- Removing a member from a team via `removeTeamMember()` does not delete or
    modify the member's record in the `member` table — the count of `member`
    table modifications triggered by a `removeTeamMember()` call equals 0
    because team membership is entirely independent of organization membership
- The `addTeamMember()` and `removeTeamMember()` endpoints enforce the `admin`
    or `owner` role server-side by reading the calling user's role from the
    `member` table — the count of successful team membership mutations initiated
    by `member`-role users equals 0 because the server validates the caller's
    role before any write operation occurs
- All dialog headings, member list labels, button text, error messages, and
    confirmation strings in the TeamMembersDialog are rendered via i18n
    translation keys — the count of hardcoded English string literals in the
    TeamMembersDialog component equals 0
- The TeamMembersDialog displays the current team member count after each add
    or remove operation — the displayed count equals the number of `teamMember`
    records for that team in the database within 200ms of each operation
    completing on the server

## Acceptance Criteria

- [ ] Clicking the users icon on a team row at `/app/$orgSlug/teams` opens the TeamMembersDialog — the dialog element is present and visible within 200ms of the click event
- [ ] The TeamMembersDialog displays all current members of the selected team — the difference between the dialog row count and the `teamMember` record count for that team equals 0
- [ ] The TeamMembersDialog displays localized labels for all headings, buttons, and member list items — the count of hardcoded English string literals in the dialog component equals 0
- [ ] The member selection control displays only organization members not yet part of the team — the difference between the option count and the expected eligible member count equals 0
- [ ] Selecting a member and confirming the addition calls `authClient.organization.addTeamMember()` — the method invocation count equals 1 after the selection and confirmation
- [ ] A successful `addTeamMember()` call returns HTTP 200 and the new `teamMember` record exists in the database — the response status equals 200 and the record count for that member-team pair equals 1
- [ ] After a successful addition the dialog updates immediately to show the newly added member — the team member row count in the dialog increases by 1 within 200ms of the server response
- [ ] Attempting to add a member who already belongs to the team returns an error — the error element is present in the dialog and the `teamMember` record count for that member-team pair remains 1
- [ ] Attempting to add a non-organization-member to the team returns HTTP 403 — the response status equals 403 and no `teamMember` record is created in the database
- [ ] Clicking the remove action on a team member row calls `authClient.organization.removeTeamMember()` — the method invocation count equals 1 after the remove click
- [ ] A successful `removeTeamMember()` call returns HTTP 200 and the `teamMember` record is deleted — the response status equals 200 and the record count for that member-team pair equals 0
- [ ] After a successful removal the dialog updates to remove the departed member's row — the team member row count in the dialog decreases by 1 within 200ms of the server response
- [ ] Removing a member from the team does not affect their organization membership — the `member` table record count for the removed user equals 1 after the `removeTeamMember()` call completes
- [ ] The removed team member is still present in all other teams they belong to — the `teamMember` record count for the removed user in other teams equals the pre-removal count, which is greater than or equal to 0
- [ ] A direct `addTeamMember()` call from a `member`-role user returns HTTP 403 — the response status equals 403 and no `teamMember` record is created in the database
- [ ] A direct `removeTeamMember()` call from a `member`-role user returns HTTP 403 — the response status equals 403 and the target `teamMember` record remains intact in the database
- [ ] The users icon on team rows is absent or non-functional for `member`-role users — the interactive users icon element count for `member`-role users equals 0 on the teams page

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Admin attempts to add the last remaining non-team organization member to the team leaving zero eligible members | The addition succeeds with HTTP 200 and the member selection control becomes empty with zero options available since all organization members now belong to the team | The response status equals 200 and the member selection control option count equals 0 after the addition completes |
| Admin removes the only member from a team leaving the team with zero members | The removal succeeds with HTTP 200 and the TeamMembersDialog displays an empty team members list with a localized empty state message indicating no members belong to the team | The response status equals 200 and the team member row count in the dialog equals 0 after the removal completes |
| Two admins simultaneously attempt to add the same organization member to the same team from different browser sessions | The first request succeeds and creates the `teamMember` record — the second request returns a duplicate membership error because the record already exists in the database for that member-team pair | The first response status equals 200 and the second response returns an error with the `teamMember` record count for that member-team pair equaling exactly 1 |
| Admin opens the TeamMembersDialog for a team and another admin removes an organization member from the organization while the dialog is still open | The team member who was removed from the organization is no longer a valid team member — the server cascade-deletes or invalidates the `teamMember` record and the dialog reflects the change on the next refresh | The `teamMember` record for the removed organization member is absent from the database and the dialog member count decreases accordingly on next data fetch |
| Admin clicks the remove action twice in rapid succession on the same team member row before the first request completes | The remove action is disabled on the first click preventing duplicate removal requests — the server receives exactly 1 `removeTeamMember()` call and no duplicate deletion error occurs | The disabled attribute is present on the remove action within 100ms of the first click and the `removeTeamMember()` invocation count equals 1 |
| Admin opens the TeamMembersDialog for a team that has no members and no eligible organization members to add | The dialog renders with an empty team members list and an empty member selection control — both display localized empty state messages indicating no members and no eligible members | The team member row count equals 0 and the member selection option count equals 0 in the dialog upon opening |

## Failure Modes

- **addTeamMember() fails due to a transient D1 write error during team member record insertion**
    - **What happens:** The server validates the caller's role and confirms the target is an organization member but the subsequent INSERT operation to the `teamMember` table fails due to a transient D1 database error or network timeout, so the team membership is not persisted despite passing all validation checks on the server side.
    - **Source:** Cloudflare D1 transient write failure or network interruption between the Worker and the D1 binding during the INSERT query execution step that follows the successful validation of the caller's role and the target member's organization membership.
    - **Consequence:** The admin sees an error in the TeamMembersDialog and the selected member does not appear in the team members list — no partial team membership data is committed to the database because the write operation failed before completion.
    - **Recovery:** The server logs the D1 write error with the team ID, target member ID, and error context, then returns HTTP 500 — the client alerts the admin with a localized error message in the TeamMembersDialog and the admin retries the addition by selecting the same member again once the D1 service recovers.

- **removeTeamMember() fails due to a transient D1 delete error during team member record removal**
    - **What happens:** The server validates the caller's role and locates the target `teamMember` record but the DELETE operation against the `teamMember` table fails due to a transient D1 database error, leaving the team membership record intact and the target user still associated with the team.
    - **Source:** Transient Cloudflare D1 database failure or network interruption between the Worker process and the D1 binding during the DELETE operation execution on the `teamMember` table for the target member-team pair.
    - **Consequence:** The admin receives an error response after clicking the remove action — the target member remains in the team with their membership intact, and the TeamMembersDialog continues to display the member in the team members list until the admin retries the operation.
    - **Recovery:** The server returns HTTP 500 and logs the D1 error with the query context and the target member ID — the client falls back to re-enabling the remove action and displaying a localized error message so the admin retries the removal once the D1 service recovers from the transient failure.

- **Non-admin user bypasses the client guard and calls addTeamMember() or removeTeamMember() directly via a crafted HTTP request**
    - **What happens:** A user with the `member` role crafts a direct HTTP request to the `addTeamMember()` or `removeTeamMember()` endpoint using a valid session cookie, circumventing the client-side guard that hides or disables team membership controls from non-admin members, and attempts to modify team membership without authorization.
    - **Source:** Adversarial or accidental action where a `member`-role user sends a hand-crafted API request directly to the team membership mutation endpoint, bypassing the client-side conditional rendering that withholds the users icon interaction from users without the `admin` or `owner` role.
    - **Consequence:** Without server-side enforcement any member could add arbitrary users to teams or remove existing team members without admin authorization, disrupting team composition and bypassing the access control model for team management entirely.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after verifying the calling user's role in the `member` table — the server logs the unauthorized attempt with the user ID, target member ID, team ID, and timestamp for audit purposes, and no `teamMember` record is created or deleted.

- **addTeamMember() is called for a user whose organization membership was revoked between the dialog opening and the add confirmation**
    - **What happens:** The admin opens the TeamMembersDialog which populates the available members list, but before the admin selects and confirms the addition, another admin removes the target user from the organization via `removeMember()`, so the `addTeamMember()` call references a user who is no longer an organization member.
    - **Source:** A race condition where the organization membership of the target user is revoked between the time the TeamMembersDialog populates its available members list and the time the admin confirms the addition, creating a stale reference to a former organization member.
    - **Consequence:** The server receives an `addTeamMember()` call for a user whose `member` record no longer exists in the organization — without validation the server would create an orphaned `teamMember` record pointing to a non-existent organization membership, creating data inconsistency.
    - **Recovery:** The server validates that the target user's `member` record exists in the organization before writing to the `teamMember` table — if the record is absent the server rejects the request with HTTP 403 and the client notifies the admin with a localized error explaining that the target user is no longer an organization member.

## Declared Omissions

- This specification does not address the creation or deletion of teams themselves — team lifecycle management including creating, renaming, and deleting teams is defined in a separate specification covering the teams page at `/app/$orgSlug/teams`
- This specification does not address team-level permissions or role assignments within a team — team members inherit their organization-level role and this spec only covers the association and disassociation of members with teams
- This specification does not address rate limiting on the `addTeamMember()` or `removeTeamMember()` endpoints — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly
- This specification does not address bulk adding or removing of multiple team members in a single operation — each add and remove is processed individually through the TeamMembersDialog with one API call per member action
- This specification does not address what happens to team-scoped resources or assignments when a member is removed from a team — retention and reassignment policies for team-level artifacts are covered by the data-governance spec

## Related Specifications

- [org-admin-removes-a-member](org-admin-removes-a-member.md) — Organization-level member removal flow that cascades to team membership, related to the race condition where a team add targets a recently removed organization member
- [org-admin-invites-a-member](org-admin-invites-a-member.md) — Invitation flow that creates new organization members who then become eligible for team addition through the TeamMembersDialog member selection control
- [org-admin-changes-member-role](org-admin-changes-member-role.md) — Role change flow that determines whether a member has admin or owner permissions required to access the team membership management controls
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that provides the `addTeamMember()` and `removeTeamMember()` endpoints and enforces role-based guards
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `teamMember`, `member`, and `team` tables that store team membership records read and written during the add and remove operations
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure providing translation keys for all TeamMembersDialog labels, buttons, empty state messages, and error messages rendered in the dialog

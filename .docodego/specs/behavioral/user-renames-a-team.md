---
id: SPEC-2026-041
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User, Org Admin, Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# User Renames a Team

## Intent

This spec defines the flow by which an organization admin or owner renames
an existing team within their organization. The user navigates to the teams
page at `/app/$orgSlug/teams`, locates the target team in the list, and
clicks the pencil icon on that team's row to open a rename dialog. The
dialog renders with translated labels via `@repo/i18n` and pre-fills the
input field with the team's current name so the user can see exactly what
they are changing from. The user edits the name to their desired value and
clicks save. The client calls
`authClient.organization.updateTeam({ teamId, data: { name } })` to
persist the change. The server validates that the calling user holds the
`admin` or `owner` role in the organization, confirms the new name is
non-empty, updates the `team` table row in D1, and returns the updated
record. Once the server confirms the update, the dialog closes and the
team list refreshes to display the updated team name in the row that was
edited. Regular members without the `admin` or `owner` role do not see
the pencil icon and cannot initiate this flow. The rename operation does
not affect team membership, permissions, or any resources associated with
the team beyond the display name.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth organization plugin (`updateTeam`) | write | User clicks save in the rename dialog and the client calls `authClient.organization.updateTeam({ teamId, data: { name } })` to persist the new team name to the database | The server returns HTTP 500 and the client falls back to displaying a localized error message inside the rename dialog while keeping the original team name intact until the user retries |
| `team` table (D1) | read/write | Server reads the existing team row to confirm it exists, then updates the `name` column with the new value provided in the `updateTeam` request payload | The database read or update operation fails and the server returns HTTP 500 — the client notifies the user with a localized error message so the team name is not left in a partial state |
| `member` table (D1) | read | Server reads the calling user's membership record to verify their `admin` or `owner` role in the organization before processing the rename request | The membership lookup fails and the server returns HTTP 500 — the client displays a localized error message inside the rename dialog so the user retries once the database recovers |
| `session` table (D1) | read | Server reads the active session to resolve the calling user's identity and verify their authenticated status before processing the rename request | The session lookup fails and the server returns HTTP 401 — the client redirects the user to `/signin` so they can re-authenticate before retrying the rename |
| `@repo/i18n` | read | All dialog labels, input placeholders, button text, validation messages, and error strings in the rename flow are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the rename dialog remains fully functional but displays untranslated text for non-English locale users |

## Behavioral Flow

1. **[User]** (organization admin or owner) navigates to
    `/app/$orgSlug/teams` and views the teams page, which lists all teams
    in the organization with each row displaying the team name, member
    count, and a pencil icon — the pencil icon is only visible to users
    whose role equals `admin` or `owner` in the organization

2. **[User]** clicks the pencil icon on the target team's row to initiate
    the rename flow, which triggers a localized rename dialog to appear in
    the foreground of the page

3. **[Client]** renders a rename dialog with translated labels and the
    team's current name pre-filled in the input field so the user can see
    exactly what they are changing from — the save button is enabled only
    when the input value differs from the current name and is non-empty

4. **[User]** edits the name in the input field to their desired value and
    clicks the save button to submit the rename, or clicks the cancel
    button to dismiss the dialog without making any changes to the team
    record

5. **[Branch -- user cancels]** The rename dialog closes and the team
    retains its original name with no changes made to the `team` table
    row, the team list display, or any associated team membership records

6. **[Client]** disables the save button, displays a loading indicator,
    and calls `authClient.organization.updateTeam({ teamId, data:
    { name } })` using the new name value from the input field to request
    the rename on the server

7. **[Server]** receives the update request, reads the calling user's
    session to resolve their identity, and queries the `member` table to
    confirm that the caller holds the `admin` or `owner` role in the
    target organization

8. **[Branch -- caller lacks admin or owner role]** The server rejects
    the request with HTTP 403 because the calling user does not have the
    required role to rename teams in the organization — the client
    displays a localized error message explaining insufficient permissions

9. **[Branch -- new name is empty or blank]** The server rejects the
    request with HTTP 400 because the team name field is required and
    cannot be an empty string or whitespace-only value — the client
    displays a localized validation error message in the rename dialog

10. **[Server]** updates the `name` column in the `team` table row for
    the target team with the new value and returns HTTP 200 with the
    updated team record confirming the rename completed in the database

11. **[Client]** closes the rename dialog and refreshes the team list so
    the updated team name is visible in the row that was edited — the
    displayed name in that row matches the new value submitted by the user

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| teams_list_idle | dialog_open | User clicks the pencil icon on a team row to open the rename dialog | Calling user's role equals `admin` or `owner` in the organization and the pencil icon element is present on the row |
| dialog_open | teams_list_idle | User clicks the cancel button or presses Escape to dismiss the rename dialog | None — cancel is always available regardless of input state or loading status |
| dialog_open | rename_pending | User clicks the save button in the rename dialog to submit the new team name | Input value is non-empty and differs from the current team name and the save button is not already disabled |
| rename_pending | renamed | Server returns HTTP 200 confirming the team name update in the database | Team table row `name` column value equals the new name submitted in the request payload |
| rename_pending | rename_error | Server returns non-200 or the request times out before a response arrives from the server | HTTP response status does not equal 200 or the network request exceeds the configured timeout threshold |
| rename_error | dialog_open | Client re-enables the save button and displays a localized error message inside the dialog | Server error was transient and the team record is still present with its previous name in the database |
| renamed | teams_list_refreshed | Client refreshes the teams list to display the updated team name in the edited row | The team row name text content equals the new name after the client-side refresh completes successfully |

## Business Rules

- **Rule name-required:** IF the new team name submitted in the rename
    request is an empty string or contains only whitespace characters THEN
    the server rejects the `updateTeam` request with HTTP 400 AND the
    client prevents submission by disabling the save button when the input
    value is empty — the server enforces this independently of the
    client-side guard to prevent blank team names via direct API calls
- **Rule org-membership-required:** IF the calling user does not have an
    active membership record in the organization that owns the target team
    THEN the server rejects the `updateTeam` request with HTTP 403 AND
    the calling user cannot access the `/app/$orgSlug/teams` route because
    the route middleware validates organization membership before rendering
    the page — the server enforces this at the endpoint level independently
    of the client-side route guard
- **Rule permission-gate:** IF the calling user's role in the organization
    is not `admin` or `owner` THEN the server rejects the `updateTeam`
    request with HTTP 403 AND the pencil icon is absent from the DOM for
    non-admin members, preventing the member from initiating the rename
    flow at all — the server enforces this independently of the
    client-side guard so direct API calls from `member`-role users are
    rejected with the same HTTP 403 response

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View all team rows on the teams page, click the pencil icon on any team row, edit the team name in the rename dialog, and submit the `updateTeam` request with full authorization to rename any team in the organization | None — the owner has unrestricted access to all team rename operations within their organization and the server grants full authorization for every valid `updateTeam` request | The pencil icon is visible on every team row in the teams list and the rename dialog is accessible for all teams in the organization |
| Admin | View all team rows on the teams page, click the pencil icon on any team row, edit the team name in the rename dialog, and submit the `updateTeam` request to rename any team in the organization | None — the admin has full access to team rename operations within the organization, identical to the owner for this specific flow | The pencil icon is visible on every team row in the teams list and the rename dialog is accessible for all teams in the organization |
| Member | View all team rows on the teams page including team names and member counts but without any access to rename controls or the ability to modify team names | Clicking a pencil icon on any team row — the pencil icon is absent from the DOM for `member`-role users and any direct API call to `updateTeam` returns HTTP 403 | The pencil icon is absent from all team rows; the count of pencil icon elements visible to a regular member equals 0 on the teams page |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the teams page component renders any content or team data | Accessing `/app/$orgSlug/teams` or calling the `updateTeam` endpoint without a valid authenticated session — the server returns HTTP 401 for direct API calls | The teams page is not rendered; the redirect to `/signin` occurs before any teams UI or rename controls are mounted or visible |

## Constraints

- The `updateTeam` endpoint enforces the `admin` or `owner` role
    server-side by reading the calling user's role from the `member`
    table — the count of successful rename operations initiated by
    `member`-role users equals 0 because the server validates the
    caller's role before any update occurs
- The pencil icon is absent from team rows for users whose role equals
    `member` — the count of pencil icon elements rendered in the teams
    list for a `member`-role user equals 0, and the server independently
    rejects any `updateTeam` request from a `member`-role user with
    HTTP 403
- The rename dialog pre-fills the input field with the current team name
    so the user can see the existing value — the input element's initial
    value equals the team's current `name` column value from the `team`
    table at the time the dialog opens
- After a successful rename the `team` table row's `name` column value
    equals the new name submitted in the request, and the teams list
    displays the updated name in the row that was edited without
    requiring a full page reload
- The rename dialog contains localized text rendered via i18n translation
    keys — the count of hardcoded English string literals in the rename
    dialog component equals 0, and all labels, placeholders, buttons, and
    error messages use translation keys from `@repo/i18n`
- The save button is disabled when the input value equals the current
    team name or is empty — the count of `updateTeam` requests sent with
    an unchanged or empty name value from the dialog equals 0 under
    normal client-side operation

## Acceptance Criteria

- [ ] The pencil icon is present on each team row for an `admin`-role user — the pencil icon element count per team row equals 1
- [ ] The pencil icon is present on each team row for an `owner`-role user — the pencil icon element count per team row equals 1
- [ ] The pencil icon is absent from all team rows for a `member`-role user — the total pencil icon element count in the teams list equals 0
- [ ] Clicking the pencil icon opens a rename dialog with the current team name pre-filled — the input element value equals the current team name within 200ms of the click event
- [ ] The save button is disabled when the input value equals the current team name — the disabled attribute is present on the save button when the input value has not changed
- [ ] The save button is disabled when the input value is empty — the disabled attribute is present on the save button when the input field contains an empty string
- [ ] Cancelling the dialog leaves the team name unchanged — the `team` table row `name` column value equals the original name and the count of `updateTeam` requests sent equals 0 after the cancel button is clicked
- [ ] Confirming the rename calls `authClient.organization.updateTeam` with the correct `teamId` and new name — the method invocation count equals 1 after the save click
- [ ] The save button displays a loading indicator and its `disabled` attribute is present while the rename request is in flight — the disabled attribute is present within 100ms of the save click
- [ ] A successful rename returns HTTP 200 and the `team` table row `name` column equals the new value — the response status equals 200 and the database column matches the submitted name
- [ ] After a successful rename the teams list displays the updated name in the edited row — the row text content equals the new team name within 500ms after the client refresh completes
- [ ] A rename attempt from a `member`-role user via direct API call returns HTTP 403 — the response status equals 403 and the `team` table row `name` column remains unchanged
- [ ] A rename attempt with an empty name returns HTTP 400 — the response status equals 400 and the `team` table row `name` column retains the previous value
- [ ] All dialog labels, input placeholders, button text, and error messages are rendered via i18n translation keys — the count of hardcoded English string literals in the rename dialog component equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User clicks the save button twice in rapid succession before the first rename request completes | The save button is disabled on the first click, preventing duplicate rename requests — the server receives exactly 1 `updateTeam` call and no duplicate update occurs | The disabled attribute is present on the save button within 100ms of the first click and the count of outbound `updateTeam` requests equals 1 |
| Two admins simultaneously rename the same team from different browser sessions with different names | The first request succeeds and updates the `team` row — the second request also succeeds and overwrites the first rename with its own value, producing the last-write-wins result | The final `team` table row `name` column value equals the name submitted in the second request, and both responses return HTTP 200 |
| User loses network connectivity after clicking save but before the server responds with a result | The rename request times out on the client — the dialog remains open with a loading indicator and a localized error message appears so the user retries once connectivity returns | The error element is present in the dialog after the request timeout and the `team` table row `name` column retains its previous value in the database |
| User submits a name that is identical to the current team name by modifying and then reverting the input | The client-side guard prevents submission because the save button is disabled when the input value equals the current name — no `updateTeam` request is sent to the server | The disabled attribute is present on the save button and the count of outbound `updateTeam` requests equals 0 after the user reverts the input |
| User submits a name containing only whitespace characters such as spaces or tabs in the input field | The client-side guard prevents submission because the save button is disabled for empty or whitespace-only input — additionally the server rejects the request with HTTP 400 if the guard is bypassed | The disabled attribute is present on the save button for whitespace-only input and a direct API call with whitespace-only name returns HTTP 400 |
| User submits a very long team name that exceeds the maximum allowed length for the name column | The server rejects the request with HTTP 400 because the name exceeds the column length constraint — the client displays a localized validation error in the rename dialog | The response status equals 400 for names exceeding the column limit and the `team` table row `name` column retains its previous value |

## Failure Modes

- **Rename request fails due to a transient D1 database error during the team row update operation**
    - **What happens:** The client calls `authClient.organization.updateTeam` and the server's UPDATE query against the `team` table fails due to a transient Cloudflare D1 error or Worker timeout, leaving the team name unchanged and the original name still displayed in the teams list.
    - **Source:** Transient Cloudflare D1 database failure or network interruption between the Worker process and the D1 binding during the UPDATE operation execution on the `team` table row.
    - **Consequence:** The user receives an error response after clicking save — the team retains its original name in the database and the rename dialog remains visible until the user dismisses it or retries the operation.
    - **Recovery:** The server returns HTTP 500 and logs the D1 error with the query context and the target team ID — the client falls back to re-enabling the save button and displaying a localized error message so the user retries the rename once the D1 service recovers.

- **Non-admin user bypasses the client guard and calls the updateTeam endpoint directly via a crafted HTTP request**
    - **What happens:** A user with the `member` role crafts a direct HTTP request to the `updateTeam` endpoint using a valid session cookie, circumventing the client-side guard that hides the pencil icon from non-admin members, and attempts to rename a team without authorization.
    - **Source:** Adversarial or accidental action where a `member`-role user sends a hand-crafted API request directly to the rename endpoint, bypassing the client-side conditional rendering that withholds the pencil icon from users without the `admin` or `owner` role.
    - **Consequence:** Without server-side enforcement any member could rename teams in the organization without admin authorization, causing confusion about team identity and disrupting organizational naming conventions.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after verifying the calling user's role in the `member` table — the server logs the unauthorized attempt with the user ID, target team ID, and timestamp for audit purposes, and no team name update occurs.

- **Session expires between opening the rename dialog and clicking the save button to submit the new name**
    - **What happens:** The user opens the rename dialog, edits the team name, but their session expires before they click save — the `updateTeam` request reaches the server with an invalid or expired session token and the server cannot resolve the calling user's identity.
    - **Source:** Session expiration due to the configured session TTL elapsing while the user has the rename dialog open and is composing the new team name, producing a stale session cookie in the subsequent API request.
    - **Consequence:** The rename request fails because the server cannot authenticate the caller — the user loses the name they typed in the dialog input field and must re-authenticate before they can attempt the rename operation again.
    - **Recovery:** The server returns HTTP 401 for the expired session and the client notifies the user by redirecting to `/signin` — after re-authentication the user navigates back to the teams page and retries the rename with the desired name value.

## Declared Omissions

- This specification does not address creating a new team — that behavior is covered by a separate spec defining the team creation dialog, validation rules, and the `createTeam` endpoint flow
- This specification does not address deleting a team from the organization — that behavior is covered by a separate spec defining the deletion confirmation dialog and cascading removal of team membership records
- This specification does not address changing team membership or adding and removing members from a team — those operations use separate endpoints and are defined in their own behavioral specifications
- This specification does not address renaming the organization itself — that behavior is defined in `user-updates-organization-settings.md` covering the organization name and slug update flow
- This specification does not address rate limiting on the `updateTeam` endpoint — that behavior is enforced by the global rate limiter covering all mutation endpoints uniformly across the API layer

## Related Specifications

- [user-updates-organization-settings](user-updates-organization-settings.md) — Organization settings update flow that covers renaming the organization itself, which is a parallel pattern to this team rename flow but targets the organization record instead of a team record
- [org-admin-changes-member-role](org-admin-changes-member-role.md) — Role change flow that determines which users have the `admin` or `owner` role required to access the rename controls and submit `updateTeam` requests in this spec
- [org-admin-removes-a-member](org-admin-removes-a-member.md) — Member removal flow that shares the same permission model pattern where `admin` and `owner` roles gate access to mutation operations on organization resources
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the organization plugin that provides the `updateTeam` endpoint and enforces the role-based permission guards used in this spec
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `team`, `member`, and `organization` tables read and written during the rename operation and the permission validation steps

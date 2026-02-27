---
id: SPEC-2026-040
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User, Org Admin, Org Owner]
---

[← Back to Roadmap](../ROADMAP.md)

# User Creates a Team

## Intent

This spec defines the flow for creating a new team within an existing
organization in the DoCodeGo platform. A user who is a member of an
organization navigates to the teams page at `/app/$orgSlug/teams`,
which lists all existing teams in that organization. The user clicks a
"Create team" button, fills in a team name in a dialog with localized
labels, and submits the form. The client calls
`authClient.organization.createTeam({ name, organizationId })` to
create the team on the server. The system enforces a hard cap of 25
teams per organization, defined by `LIMITS.MAX_TEAMS_PER_ORG`. If the
organization already has 25 teams, the creation request fails and the
user sees a localized error message indicating the limit has been
reached. On success, the dialog closes and the team list refreshes to
display the newly created team. This spec ensures that team creation
is gated by organizational membership, that the per-organization team
limit is enforced server-side, and that the user receives clear
feedback for both success and failure outcomes.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth server SDK (`organization` plugin, `createTeam` endpoint) | write | Client calls `authClient.organization.createTeam({ name, organizationId })` when the user submits the create-team dialog form with a valid team name | The server returns HTTP 500 and the client falls back to displaying a localized error message inside the dialog while keeping the dialog open so the user can retry |
| D1 (Cloudflare SQL) via Drizzle ORM (`team` table) | read/write | Server reads the current team count for the organization to enforce the 25-team limit and writes the new `team` row during creation | The database query or write fails, the transaction rolls back, the server returns HTTP 500, and the client falls back to displaying a localized error message with a retry option |
| `LIMITS.MAX_TEAMS_PER_ORG` configuration constant (value: 25) | read | Server reads this constant before inserting a new team row to determine whether the organization has reached its maximum allowed team count | The constant is a compile-time value embedded in the server bundle, so unavailability is not possible at runtime — if the build omits it, the server falls back to rejecting all creation requests until redeployed with the constant present |
| `@repo/i18n` localization layer | read | All dialog labels, input placeholders, button text, validation messages, and error strings are rendered via i18n translation keys throughout the create-team dialog | The translation function falls back to the default English locale strings so the dialog remains functional but displays untranslated English text for non-English users |

## Behavioral Flow

1. **[User]** navigates to the teams page at `/app/$orgSlug/teams`,
    which lists all existing teams in the organization, displaying each
    team's name and metadata in a scrollable list
2. **[Client]** renders the teams page with a "Create team" button
    visible to users who are members of the current organization, using
    localized labels from the i18n translation layer
3. **[User]** clicks the "Create team" button on the teams page, which
    triggers the client to open a dialog overlay on top of the current
    page
4. **[Client]** renders the create-team dialog with localized labels
    and a single input field for the team name, plus a submit button
    and a cancel button to dismiss the dialog without creating a team
5. **[User]** enters the desired team name into the input field and
    clicks the submit button to create the team
6. **[Client]** validates that the team name input is non-empty before
    sending the request — if the input is empty, the client displays a
    localized validation error beneath the input field and does not
    send any request to the server
7. **[Client]** calls
    `authClient.organization.createTeam({ name, organizationId })` with
    the entered name and the current organization's ID, disabling the
    submit button and displaying a loading indicator while the request
    is in flight
8. **[Server]** receives the creation request, verifies that the
    calling user is a member of the specified organization, counts the
    existing teams for that organization, and compares the count against
    `LIMITS.MAX_TEAMS_PER_ORG` (25)
9. **[Branch — team limit reached]** If the organization already has
    25 teams, the server returns HTTP 403 with an error code indicating
    the team limit has been reached, and the client displays a localized
    error message inside the dialog informing the user that no more
    teams can be created in this organization
10. **[Server]** creates the new `team` row in the database with the
    provided name and the organization's ID, then returns HTTP 200 with
    the new team object
11. **[Client]** receives the successful response, closes the
    create-team dialog, and refreshes the team list on the teams page
    to display the newly created team alongside all previously existing
    teams

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| teams_page | dialog_open | User clicks the "Create team" button on the teams page | User is a member of the current organization |
| dialog_open | dialog_open (validation_error) | User clicks submit with an empty team name input field | Team name input value is an empty string or contains only whitespace characters |
| dialog_open | submitting | User clicks submit with a non-empty team name in the input field | Team name input value is a non-empty string after trimming whitespace |
| submitting | team_created | Server returns HTTP 200 with the new team object in the response body | Database write commits and team count was below 25 before insertion |
| submitting | dialog_open (limit_error) | Server returns HTTP 403 indicating the organization has reached the maximum team count of 25 | Existing team count for the organization equals 25 at the time of the server check |
| submitting | dialog_open (server_error) | Server returns HTTP 500 due to a database failure or other internal server error | Database write fails or an unexpected server-side exception occurs during team creation |
| team_created | teams_page (refreshed) | Client closes the dialog and refreshes the team list to include the new team | Response body contains the new team object with a valid ID and name |
| dialog_open | teams_page | User clicks the cancel button or clicks outside the dialog to dismiss it | None — cancellation is always allowed regardless of form state |

## Business Rules

- **Rule team-limit-enforcement:** IF a user submits a create-team
    request for an organization THEN the server counts the existing
    teams for that organization AND if the count equals or exceeds
    `LIMITS.MAX_TEAMS_PER_ORG` (25) THEN the server returns HTTP 403
    with a team-limit-reached error code AND the count of teams in
    that organization after the request equals the count before the
    request
- **Rule team-name-required:** IF the user submits the create-team
    dialog THEN the team name input must contain at least 1 non-
    whitespace character AND if the trimmed input is empty the client
    displays a localized validation error and sends 0 requests to the
    server
- **Rule org-membership-required:** IF a user attempts to create a
    team in an organization THEN the server verifies that the calling
    user has an active membership in that organization AND if the user
    is not a member the server returns HTTP 403 with an unauthorized
    error code AND creates 0 new team rows in the database

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | Open the create-team dialog, enter a team name, submit the form, and create a new team in the organization up to the 25-team limit | Create a team when the organization has already reached the 25-team limit (server returns HTTP 403 rejection) | Sees all existing teams on the teams page and sees the "Create team" button in the teams page header |
| Admin | Open the create-team dialog, enter a team name, submit the form, and create a new team in the organization up to the 25-team limit | Create a team when the organization has already reached the 25-team limit (server returns HTTP 403 rejection) | Sees all existing teams on the teams page and sees the "Create team" button in the teams page header |
| Member | Open the create-team dialog, enter a team name, submit the form, and create a new team in the organization up to the 25-team limit | Create a team when the organization has already reached the 25-team limit (server returns HTTP 403 rejection) | Sees all existing teams on the teams page and sees the "Create team" button in the teams page header |
| Unauthenticated | None — all dashboard pages require an active session and the auth guard redirects to `/signin` before any dashboard component renders | Access the teams page or create-team dialog (auth guard blocks access before rendering the dashboard layout) | Cannot see the teams page or create-team dialog because the auth guard redirects to `/signin` before the dashboard renders |

## Constraints

- The maximum number of teams per organization equals 25 as defined by
    `LIMITS.MAX_TEAMS_PER_ORG` — the count of teams in any single
    organization must never exceed 25 at any point in time
- The team name must contain at least 1 non-whitespace character — the
    count of create-team requests sent to the server with an empty or
    whitespace-only name from the client equals 0
- The server enforces organizational membership before creating a team
    — the count of team rows created for organizations where the calling
    user has no active membership equals 0
- The create-team dialog renders all text via i18n translation keys —
    the count of hardcoded English strings in the dialog component
    equals 0
- The team list on the teams page reflects the newly created team
    within 1000ms of receiving a successful HTTP 200 response from the
    server — the new team element is present in the list after refresh
- The create-team dialog disables the submit button during request
    flight — the count of duplicate creation requests sent while a
    previous request is in flight equals 0

## Acceptance Criteria

- [ ] The "Create team" button is present on the teams page at `/app/$orgSlug/teams` — the button element is present and visible when a user who is a member of the organization loads the page
- [ ] Clicking "Create team" opens the create-team dialog — the dialog element is present and visible after the click, and the dialog contains exactly 1 text input field for the team name
- [ ] Submitting with an empty team name sends 0 requests to the server — the validation error element is present beneath the input field and the count of POST requests to `createTeam` equals 0
- [ ] Submitting with a valid team name sends exactly 1 request to `authClient.organization.createTeam` — the network request is present with the team name and organizationId in the payload
- [ ] The submit button's `disabled` attribute is present while the creation request is in flight — the loading indicator element is present and the count of additional submit clicks that trigger new requests equals 0
- [ ] The server returns HTTP 200 and the dialog closes within 1000ms of receiving the response — the dialog element is absent from the DOM after the successful response
- [ ] The team list count equals the previous count plus 1 after successful creation — the count of team items on the teams page after creation equals the count before creation plus 1
- [ ] Creating team number 26 returns HTTP 403 — when the organization has exactly 25 existing teams, the server response status equals 403 and the error message references the team limit
- [ ] The error message for the 25-team limit is displayed inside the dialog — the error element is present and visible within the dialog and the dialog remains open with the previously entered team name intact
- [ ] A non-member user attempting to create a team receives HTTP 403 — the server response status equals 403 and the count of new team rows created in the database equals 0
- [ ] The count of hardcoded English strings in the create-team dialog component equals 0 — all labels, placeholders, button text, and error messages are rendered via i18n translation keys
- [ ] Clicking the cancel button or clicking outside the dialog closes the dialog without creating a team — the dialog element is absent from the DOM and the count of createTeam requests sent equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Two users submit createTeam requests simultaneously that would bring the team count from 24 to 26, exceeding the 25-team limit | The server's count check inside a transaction ensures only 1 creation succeeds; the second request receives HTTP 403 with a team-limit-reached error code and the database contains exactly 25 teams | The first response status equals 200, the second response status equals 403, and the team count for the organization in the database equals 25 |
| The user submits a team name consisting entirely of whitespace characters such as spaces and tabs with no visible text content | The client trims the input and detects an empty value, displays a localized validation error beneath the input field, and sends 0 requests to the server | The validation error element is present beneath the input field and the count of POST requests to createTeam equals 0 |
| The user submits a team name that is extremely long, exceeding 256 characters in total length including spaces and special characters | The server validates the team name length and returns HTTP 400 with a validation error if the name exceeds the maximum allowed length, keeping the dialog open | The server response status equals 400 and the error element is present inside the dialog with a length-related validation message |
| The user's session expires after opening the create-team dialog but before submitting the form, resulting in an unauthenticated request | The server returns HTTP 401 for the unauthenticated request and the client redirects the user to the `/signin` page to re-authenticate before retrying | The server response status equals 401 and the client navigates to `/signin` within 2000ms of receiving the response |
| The user opens the create-team dialog on a slow network connection and the server takes more than 10 seconds to respond to the request | The client continues to display the loading indicator and keeps the submit button disabled until the response arrives or the request times out | The loading indicator element is present and the submit button's disabled attribute is present throughout the wait period |
| The organization has exactly 25 teams and an admin deletes 1 team, then the user immediately submits a create-team request for a new team | The server counts 24 existing teams at the time of the create request, which is below the 25-team limit, and creates the new team returning HTTP 200 | The server response status equals 200 and the team count for the organization after the operation equals 25 |

## Failure Modes

- **Team creation fails due to a database write error during the server-side transaction for the new team row insertion**
    - **What happens:** The client calls `authClient.organization.createTeam({ name, organizationId })` but the D1 database returns an error during the write of the `team` row, causing the transaction to roll back and leaving no partial records in the database.
    - **Source:** Transient D1 database failure, Cloudflare Workers resource exhaustion, or a network interruption between the Worker and the D1 database service during the write operation.
    - **Consequence:** The user sees no new team in the team list, the dialog remains open with the previously entered team name intact, and the organization's team count in the database is unchanged from before the request.
    - **Recovery:** The server returns HTTP 500 and the client falls back to displaying a localized error message inside the dialog while re-enabling the submit button so the user can retry the creation after the transient database issue resolves.
- **Team limit check returns an incorrect count due to a race condition between two concurrent creation requests for the same organization**
    - **What happens:** Two users submit createTeam requests at the same instant for an organization with 24 teams, and both count queries return 24 before either insert commits, allowing both inserts to proceed and resulting in 26 teams which exceeds the 25-team limit.
    - **Source:** Missing database-level serialization or transaction isolation that allows concurrent reads of the team count before either concurrent write has committed the new team row to the database.
    - **Consequence:** The organization ends up with 26 teams in the database, violating the `LIMITS.MAX_TEAMS_PER_ORG` constraint of 25 and potentially causing unexpected behavior in other features that rely on the team limit.
    - **Recovery:** The server enforces the team limit using a database-level unique constraint or serializable transaction isolation so the second concurrent insert rejects with an error, and the client falls back to displaying a localized error message prompting the user to retry.
- **Dialog fails to close after a successful team creation because the client-side success handler encounters a JavaScript runtime error**
    - **What happens:** The server returns HTTP 200 with the new team object but the client's success callback throws an unhandled exception before closing the dialog, leaving the dialog visually open even though the team was created in the database.
    - **Source:** A bug in the dialog close logic, a state management error in the React component that prevents the dialog's open state from transitioning to false, or a missing null check on the response data.
    - **Consequence:** The user sees the dialog still open and assumes the creation failed, potentially clicking submit again and triggering a duplicate team creation request that the server processes as a new valid team.
    - **Recovery:** The client wraps the success handler in a try-catch block that logs the error to the console and falls back to forcing the dialog closed and triggering a full team list refetch from the server to ensure the UI reflects the current database state.
- **The i18n translation layer fails to load the translation bundle for the user's selected locale when opening the create-team dialog**
    - **What happens:** The user opens the create-team dialog but the i18n translation bundle for their selected locale fails to load from the server or is missing the required translation keys for the dialog's labels and messages.
    - **Source:** A missing translation file for the user's locale, a network error during translation bundle fetch, or an incomplete translation key set in the locale file that omits the create-team dialog keys.
    - **Consequence:** The dialog renders with missing or broken text labels, making it difficult for the user to understand the form fields and action buttons, potentially leading to confusion or form abandonment.
    - **Recovery:** The i18n translation function falls back to the default English locale strings for any missing keys so the dialog remains fully functional with English text, and the client logs a warning indicating which translation keys were missing for the requested locale.

## Declared Omissions

- This specification does not address team membership management, including adding or removing users from a created team, which is covered by separate team-membership specifications
- This specification does not address editing or renaming an existing team after creation, which is a distinct flow with its own validation and permission requirements
- This specification does not address deleting a team from an organization, which involves different confirmation steps and cascading data cleanup operations
- This specification does not address team-level permissions or role assignments within a team, which are governed by the team-role management specifications
- This specification does not address the visual design or layout of the teams page beyond the presence of the "Create team" button and the create-team dialog structure
- This specification does not address server-side rate limiting or throttling of the createTeam endpoint, which is an infrastructure concern defined in the API framework specifications

## Related Specifications

- [user-creates-an-organization](user-creates-an-organization.md) — Organization creation flow that establishes the parent entity within which teams are created, sharing similar dialog-based creation patterns
- [user-creates-first-organization](user-creates-first-organization.md) — First-time organization creation during onboarding, establishing the organizational context required before any teams can exist
- [org-admin-manages-custom-roles](org-admin-manages-custom-roles.md) — Custom role management within organizations that defines the permission model governing who can perform team-related actions
- [org-admin-removes-a-member](org-admin-removes-a-member.md) — Member removal flow that intersects with team membership when a removed organization member also belongs to teams in that organization
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the `organization` plugin that provides the `createTeam` endpoint used in this specification
- [database-schema](../foundation/database-schema.md) — Drizzle ORM table definitions for the `team` table and related organization tables written to during the team creation flow

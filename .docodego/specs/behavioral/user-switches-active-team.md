---
id: SPEC-2026-043
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Switches Active Team

## Intent

This spec defines how an authenticated user switches the active team
within an organization from the dashboard. Within an organization, a
user belongs to one or more teams. The dashboard sidebar or a dedicated
team switcher component displays the localized name of the user's
currently active team. Clicking this component opens a dropdown listing
all teams the user is a member of within the current organization, with
the active team visually marked. Selecting a different team calls
`authClient.organization.setActiveTeam({ teamId })` to update the
session's `activeTeamId` on the server. Unlike organization switching,
which is driven by a URL change, team switching is a session-level
operation — the URL does not change, but the session now carries the
new team context. All API responses and permission checks then scope
to the new team, and the dashboard re-renders with team-scoped data
refetched via TanStack Query caches keyed by team ID.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.organization.setActiveTeam({ teamId })` endpoint | write | When the user selects a different team from the team switcher dropdown and the client submits the team ID to the server | The client displays a localized error toast notifying the user that the team switch failed, and the session retains the previous `activeTeamId` so no stale context is applied |
| Session table (D1 / session store) | write | When the server receives the `setActiveTeam` call and updates the `activeTeamId` field in the user's active session record | The server returns error HTTP 500 and the client falls back to retaining the previous `activeTeamId` in the session — the user is notified via a localized error toast that the team switch did not persist |
| TanStack Query cache (team-keyed) | read | When the session update completes and dashboard components refetch data scoped to the newly active team using cache keys that include the team identifier | The UI degrades to a loading skeleton for team-scoped components and retries the fetch — stale cached data from a prior visit to the same team is displayed instantly while the background refetch completes |
| @repo/i18n (localization) | read | When the team switcher renders team names, dropdown labels, error toasts, and loading states using localized translation keys from the i18n namespace | The component falls back to rendering the raw translation key string instead of localized text, and logs the missing key to the console so developers can identify untranslated strings during development |

## Behavioral Flow

1. **[User]** is authenticated and viewing the dashboard within an
    organization — the sidebar or a dedicated team switcher component
    displays the localized name of the user's currently active team
2. **[User]** clicks the team switcher component to open a dropdown
    listing all teams the user is a member of within the current
    organization
3. **[Client]** opens the team switcher dropdown and visually marks the
    currently active team — highlighted or checked — so the user can see
    which team context they are working in at a glance, then renders the
    full list of the user's teams within the current organization
4. **[User]** clicks on a different team in the dropdown list to
    initiate a team context switch to the selected team
5. **[Client]** calls `authClient.organization.setActiveTeam({ teamId })`
    with the ID of the selected team to request the server to update the
    session's active team context
6. **[Server]** receives the `setActiveTeam` call, verifies the user is
    a member of the specified team within the current organization, and
    updates the session's `activeTeamId` to reflect the newly selected
    team — unlike organization switching, which is driven by a URL
    change, team switching is a session-level operation and the URL does
    not change
7. **[Client]** once the session update completes, API responses and
    permission checks scope to the new team context — any team-specific
    data such as team members, team settings, or team-scoped resources
    reflects the newly selected team
8. **[Client]** the user's effective permissions change depending on
    their role within the selected team — for example, a user who is an
    admin of one team but a regular member of another will see different
    options and capabilities after switching
9. **[Client]** the dashboard re-renders to reflect the new team
    context — components that display team-scoped data refetch their
    content based on the updated `activeTeamId` in the session, using
    TanStack Query caches keyed by team ID so that previously visited
    teams load instantly from cache while background refetches run
10. **[Client]** the sidebar, header, and content area all update to
    match the selected team — the team switcher now displays the name
    of the newly active team as the current selection

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| viewing_team | dropdown_open | User clicks the team switcher component in the sidebar or header | User is authenticated and has at least 1 team membership in the current organization |
| dropdown_open | viewing_team | User clicks outside the dropdown or presses Escape to dismiss without selecting | No team was selected before dismissal and the active team remains unchanged |
| dropdown_open | switching_team | User clicks a different team in the dropdown list | Selected team ID differs from the current `activeTeamId` in the session |
| switching_team | viewing_team | Server confirms `setActiveTeam` call and session `activeTeamId` is updated to the new team | The server returned a success response and the session record reflects the new team ID |
| switching_team | switch_failed | Server rejects the `setActiveTeam` call due to network error or membership validation failure | The server returned an error response or the request timed out before completion |
| switch_failed | viewing_team | Client displays an error toast and reverts to the previous active team context | The previous `activeTeamId` is restored in the UI and the session record is unchanged |

## Business Rules

- **Rule team-membership-required:** IF the user calls
    `setActiveTeam({ teamId })` with a team ID AND the user does not
    have an active membership record for that team within the current
    organization THEN the server returns error and the session
    `activeTeamId` remains unchanged — the count of successful team
    switches to teams the user is not a member of equals 0
- **Rule session-scoped-switch:** IF the user switches the active team
    THEN the URL does not change because team switching is a
    session-level operation — the count of URL pathname changes during
    a team switch event equals 0, and the session `activeTeamId` field
    is the exclusive source of truth for team context
- **Rule scoped-data-on-switch:** IF the session `activeTeamId`
    updates to a new team THEN all subsequent API responses and
    dashboard queries scope to the new team context — the count of API
    responses returning data from the previous team after the switch
    completes equals 0
- **Rule permission-scope-per-team:** IF the user has different roles
    across teams (for example admin in team A and member in team B) THEN
    the effective permissions rendered in the dashboard reflect the
    user's role in the currently active team — the count of permission
    checks referencing a non-active team's role equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | Opens team switcher, views all teams within the organization, switches to any team they are a member of, and retains owner-level permissions across all owned teams | Cannot switch to a team they are not a member of within the current organization | Team switcher dropdown lists only teams the user has an active membership record for within the current organization |
| Admin | Opens team switcher, views all teams they belong to within the organization, switches active team, and retains admin-level permissions for teams where they hold admin role | Cannot switch to a team they are not a member of, and cannot access admin capabilities for teams where they hold a non-admin role | Team switcher dropdown lists only teams the user has an active membership record for — admin-specific UI elements render only for teams with admin role |
| Member | Opens team switcher, views all teams they belong to within the organization, and switches active team to any team they are a member of | Cannot switch to a team they are not a member of, and cannot access admin or owner capabilities in any team context | Team switcher dropdown lists only teams the user has an active membership record for — restricted UI elements are hidden for member-role teams |
| Unauthenticated | No actions permitted — dashboard routes redirect to the sign-in page before the team switcher component is rendered | Cannot access team switcher, dropdown, or any team-scoped dashboard data at any point | No team data or switcher UI is visible to unauthenticated visitors at any point in the interaction |

## Constraints

- The session `activeTeamId` is the single source of truth for team
    context — the dashboard does not maintain a separate client-side
    team-context store that can diverge from the session value, and
    any divergence between the client state and the session
    `activeTeamId` is treated as an error condition that triggers a
    session re-fetch.
- The team switcher dropdown must list only teams for which the user
    has an active membership record within the current organization —
    the count of teams in the dropdown must equal the count of rows in
    the team membership table for that user with an active status in the
    current org, and it must not include teams the user does not belong
    to.
- Switching the active team must not alter the browser URL pathname —
    the count of URL pathname changes during a team switch event equals
    0, distinguishing team switching from organization switching which
    is URL-driven.
- The `setActiveTeam` call must complete and update the session within
    2000 ms under normal network conditions — if the call exceeds 2000
    ms the client displays a timeout error toast and retains the
    previous `activeTeamId`.
- All team-scoped data displayed after a switch must correspond to the
    newly active team — the count of rendered UI elements displaying
    data from the previous team after the switch completes and the
    dashboard re-renders equals 0.
- The team switcher component must display localized team names using
    @repo/i18n translation keys — the count of unlocalized raw strings
    rendered in the team switcher equals 0 when a translation key exists
    for the team name label.

## Acceptance Criteria

- [ ] The team switcher component is present in the dashboard sidebar or header and its text content equals the localized name of the user's currently active team — the component element is present in the DOM and its inner text is non-empty
- [ ] Clicking the team switcher opens a dropdown — the count of dropdown items is non-empty and equals the count of active team membership rows for that user in the current organization
- [ ] The currently active team is visually marked in the dropdown — the count of items with a checked or highlighted active class equals 1
- [ ] Clicking a different team in the dropdown calls `setActiveTeam({ teamId })` — the count of requests to the setActiveTeam endpoint equals 1 after the click event, and the request payload's teamId is non-empty and equals the selected team's identifier
- [ ] The server updates the session `activeTeamId` to the newly selected team — the session record's `activeTeamId` is non-empty and equals the new team's identifier after the setActiveTeam call completes
- [ ] The URL pathname does not change during a team switch — the count of URL pathname changes during the switch event equals 0, and the window location pathname before and after the switch are equal
- [ ] After the session update, TanStack Query issues new requests keyed by the new team's identifier — the count of pending queries for the old team key equals 0 after the switch settles
- [ ] The sidebar, header, and content area reflect the new team after re-fetch — the team switcher text equals the new team's localized name, and the count of UI elements displaying the previous team's name equals 0
- [ ] Switching to a team the user is not a member of returns an error and the session `activeTeamId` remains unchanged — the count of successful setActiveTeam responses for non-member teams equals 0
- [ ] The user's effective permissions update to match their role in the newly active team — admin-specific UI elements are present when the user holds admin role and absent when the user holds member role in the selected team
- [ ] Cached data for a previously visited team renders on initial switch without a loading skeleton — the count of visible loading skeleton frames on the initial render equals 0 when TanStack Query holds cached data for that team
- [ ] The team switcher dropdown closes after a selection event triggers the setActiveTeam call — the count of rendered dropdown elements after selection equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User belongs to only 1 team within the current organization and opens the team switcher dropdown | The dropdown opens and shows 1 item representing the current team, which is marked as active — there are no other selectable items, and the user cannot switch because no other teams are available | The count of dropdown items equals 1 and the count of non-active selectable items equals 0 |
| User switches team while a background data fetch is still in flight for the current team | TanStack Query cancels or ignores the in-flight query for the old team key and immediately issues new queries keyed by the new team — no stale data from the old team appears in the dashboard after the switch settles | The network log shows the old team query was cancelled or its response was discarded, and the rendered data matches only the new team's identifier |
| Admin removes the user from a team during the user's active session, and the user then attempts to switch to that team | The server rejects the `setActiveTeam` call because the user no longer has an active membership record for that team, and the client displays a localized error toast while retaining the previous `activeTeamId` | The setActiveTeam response status is non-2xx and the session `activeTeamId` equals the previous team's identifier after the failed switch attempt |
| User switches organization (URL change) while a team switch is in progress for the previous organization | The pending `setActiveTeam` call for the previous org is cancelled or its response is discarded — the new org's default team context is applied and the stale team switch does not overwrite the new org's session state | The session `activeTeamId` reflects the default team for the new org, and no response from the cancelled setActiveTeam call is applied |
| User opens the team switcher while the current team's data is still loading after a prior switch | The dropdown opens and lists all teams as normal — the partial loading state of the current team's data does not block the switcher from being interactive and usable | The dropdown is visible and interactive within 300 ms of the click, regardless of whether the current team's data fetch has completed |
| Network disconnection occurs immediately after the user clicks a team in the dropdown | The `setActiveTeam` call fails with a network error and the client displays a localized error toast — the session `activeTeamId` is unchanged and the previous team context is preserved in the UI | The setActiveTeam request fails with a network error and the team switcher text still equals the previous active team's localized name |

## Failure Modes

- **setActiveTeam API call fails due to network error or server unavailability during the team switch request**

    **What happens:** The user selects a different team from the dropdown, the client calls `setActiveTeam({ teamId })`, but the request fails due to a transient network interruption, DNS resolution failure, or the API server being temporarily unavailable — the session `activeTeamId` on the server was never updated.

    **Source:** Transient network connectivity loss between the client and the API server, or temporary server-side unavailability caused by deployment rollouts, infrastructure issues, or resource exhaustion on the Cloudflare Workers runtime.

    **Consequence:** Without error handling the client would assume the team switch succeeded and render dashboard data scoped to the new team while the session still references the old team — API responses would return data for the previous team, creating a mismatch between what the user expects and what is displayed.

    **Recovery:** The client catches the failed request and falls back to retaining the previous `activeTeamId` in the UI state — a localized error toast notifies the user that the team switch did not complete, and the dashboard retries the data fetch for the original team to restore consistent state.

- **Session write conflict: concurrent setActiveTeam calls from multiple browser tabs produce inconsistent session state**

    **What happens:** The user has two browser tabs open within the same organization and switches to team A in one tab while switching to team B in the other tab within a narrow time window — both `setActiveTeam` calls reach the server and the session `activeTeamId` is updated twice in rapid succession, leaving one tab's local state diverged from the final session value.

    **Source:** Concurrent session writes from multiple tabs sharing the same session cookie, where the last-write-wins semantics of the session store cause one tab's expected `activeTeamId` to be overwritten by the other tab's request without notification.

    **Consequence:** One browser tab displays dashboard data scoped to team A while the session actually references team B — subsequent API calls from the diverged tab return team B data, creating confusion as the user sees mismatched team context between the UI label and the actual data rendered.

    **Recovery:** Each tab's dashboard components detect the divergence when API responses reference a different team than the locally cached `activeTeamId` — the client alerts the user with a localized notification that the team context changed externally and retries the session fetch to synchronize the local state with the server-side `activeTeamId`.

- **Stale team membership: user attempts to switch to a team from which they were removed mid-session**

    **What happens:** The user's team membership list was fetched at session start and cached client-side, but an admin removes them from one of those teams during the active session — the team switcher dropdown still shows the removed team because the client-side list has not been refreshed, and the user clicks it to initiate a switch.

    **Source:** Stale client-side team membership cache from an earlier fetch, combined with a server-side membership change that occurred after the cache was populated during the current authenticated session.

    **Consequence:** The user clicks the stale team entry and triggers a `setActiveTeam` call for a team they no longer belong to — without a server-side membership guard, the unauthorized team context would be applied to the session and team-scoped data would be returned to the removed user.

    **Recovery:** The server-side `setActiveTeam` handler performs a live membership check before updating the session — it rejects the call for the removed team, logs the unauthorized access attempt, and returns error to the client. The client falls back to retaining the previous `activeTeamId` and displays a localized error toast informing the user that they are no longer a member of that team.

- **Dashboard re-render race: TanStack Query background refetch for the previous team resolves after the team switch completes**

    **What happens:** The user switches from team A to team B, but a pending background refetch keyed to team A resolves after the switch completes and attempts to write team A's data into the active view, potentially overwriting team B's data that the user expects to see after the switch.

    **Source:** Race condition between a background refetch keyed to the prior team identifier and the TanStack Query cache write that occurs after the `setActiveTeam` call updates the active team context in the dashboard components.

    **Consequence:** The user momentarily sees team members, team settings, and team-scoped resources from team A displayed in the team B dashboard context — data from a team the user intended to leave is briefly visible, causing confusion about which team context is active.

    **Recovery:** TanStack Query caches are keyed by team identifier — the query client rejects or discards responses whose cache key does not match the current `activeTeamId`, and the dashboard falls back to displaying only data from cache keys matching the currently active team. The count of cross-team data writes to the active view after the switch settles equals 0.

## Declared Omissions

- This specification does not address how teams are created, renamed, or deleted within an organization — those operations are defined in separate team management specs as distinct administrative flows
- This specification does not address the initial team assignment when a user first joins an organization — that behavior is governed by the invitation acceptance and session lifecycle specs as a separate concern
- This specification does not address organization switching, which is URL-driven and follows a different interaction pattern — that behavior is defined in the user-switches-organization spec
- This specification does not address team member invitation, removal, or role assignment flows — those operations are defined in separate team member management specs and are outside the scope of the team switching interaction
- This specification does not address mobile-specific team switcher UI layout or native interaction patterns — that behavior is defined in the mobile platform specs for the Expo application

## Related Specifications

- [user-switches-organization](user-switches-organization.md) — Organization switching flow that uses URL-driven context changes, which this team switching flow complements with session-level team context updates within an organization
- [session-lifecycle](session-lifecycle.md) — Post-authentication session management including initial `activeTeamId` assignment and session persistence that this team switching flow depends on for storing the active team
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration and organization plugin wiring that manages `setActiveTeam` endpoint logic and session `activeTeamId` updates
- [database-schema](../foundation/database-schema.md) — Schema definitions for the team and team membership tables that the `setActiveTeam` handler queries to verify membership before updating the session
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure providing the translation keys for team switcher labels, dropdown items, error toasts, and loading states

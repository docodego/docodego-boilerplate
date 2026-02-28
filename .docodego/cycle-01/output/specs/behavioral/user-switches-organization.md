---
id: SPEC-2026-026
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Org Owner, Org Admin, Member]
---

[← Back to Roadmap](../ROADMAP.md)

# User Switches Organization

## Intent

This spec defines how an authenticated user switches between organizations
they belong to from within the dashboard. The OrgSwitcher component in the
dashboard header displays the user's current organization and exposes a
dropdown listing all organizations the user is a member of. Selecting a
different organization navigates the browser to `/app/{newSlug}/`, where the
URL slug is the sole source of org context — it is bookmarkable and shareable.
The `$orgSlug` layout route's `beforeLoad` hook reads the new slug and loads
the corresponding org data, updating the session's `activeOrganizationId`
without a dedicated context-switch API call. All dashboard data re-fetches
for the new org once the route settles, with TanStack Query serving cached
data instantly for recently visited orgs while background refetches run.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| TanStack Router (`$orgSlug` layout route) | read | When the user selects a different organization and the browser navigates to `/app/{newSlug}/` | Navigation falls back to a router error boundary, which renders a localized error page and prevents the dashboard from loading with stale org context |
| TanStack Query (org-keyed cache) | read | When the new route settles and dashboard data re-fetches for the selected organization | The UI degrades to a loading skeleton and retries the fetch — stale cached data from a prior visit is displayed instantly while the background refetch completes |
| Better Auth session (`activeOrganizationId`) | write | When the `$orgSlug` `beforeLoad` hook resolves the new slug and updates the active organization in the session | The `beforeLoad` hook returns an error and the router redirects the user back to the previous valid org route so no stale context is applied |
| `organization` table (D1) | read | When `beforeLoad` loads org data for the newly selected slug to verify the user is a member | The route handler returns HTTP 403 and the router redirects the user to their default org route — the unauthorized org context is never applied to the session |

## Behavioral Flow

1. **[User]** is authenticated and viewing the dashboard for their current
    organization — the OrgSwitcher component is visible in the header and
    displays the localized name of the current organization
2. **[User]** clicks the OrgSwitcher component in the dashboard header to
    open the organization dropdown listing all organizations the user belongs to
3. **[Client]** opens the OrgSwitcher dropdown and visually marks the current
    organization — highlighted or checked — so the user can immediately see
    which org they are working in, then renders the full list of the user's orgs
4. **[User]** clicks on a different organization in the dropdown list to
    initiate a context switch to the selected organization
5. **[Client]** navigates the browser to `/app/{newSlug}/` where `newSlug` is
    the slug of the selected organization — the URL becomes the single source
    of truth for org context and is bookmarkable and shareable with any user
    who has access to that org
6. **[Router]** the `$orgSlug` layout route's `beforeLoad` hook picks up the
    new slug from the URL, verifies the user is a member of the org, and loads
    the corresponding org data for the new context
7. **[Server]** updates the session's `activeOrganizationId` to reflect the
    newly selected organization — there is no separate API call to switch
    context because the route change itself drives the context change
8. **[Client]** once the route change completes, all dashboard data
    re-fetches for the new org context using TanStack Query caches keyed
    by org — if the user has visited this org recently, cached data appears
    instantly while background refetches run in parallel
9. **[Client]** the sidebar, header, and content area all reflect the new
    organization — page titles, member lists, settings, and any
    org-specific data update to match the selected org

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| viewing_org | dropdown_open | User clicks OrgSwitcher component in header | User is authenticated and has at least 1 organization membership |
| dropdown_open | viewing_org | User clicks outside the dropdown or presses Escape | No org was selected before dismissal |
| dropdown_open | navigating | User clicks a different org in the dropdown list | Selected org slug differs from the current route slug |
| navigating | loading_org_data | Router `beforeLoad` hook resolves new slug and user membership is confirmed | User is a member of the selected organization |
| navigating | access_denied | Router `beforeLoad` hook finds user is not a member of the selected org | User does not have a membership record for that org |
| loading_org_data | viewing_org | TanStack Query settles for the new org context and all dashboard data is ready | Route change completed and `activeOrganizationId` updated in session |
| access_denied | viewing_org | Router redirects user to their default org route | Redirect preserves the previous valid org context |

## Business Rules

- **Rule slug-as-context:** IF the user navigates to `/app/{newSlug}/` THEN
    the `$orgSlug` layout route's `beforeLoad` hook uses `newSlug` as the
    exclusive source of org context — no separate API call is issued to switch
    context; the URL change is the context change, and the count of
    standalone context-switch API calls per navigation event equals 0
- **Rule membership-guard:** IF the `beforeLoad` hook resolves the slug AND
    the user does not have a membership record for that org THEN the server
    returns HTTP 403 and the router redirects the user to their default org
    route, leaving the session `activeOrganizationId` unchanged
- **Rule cache-keying:** IF the user has previously visited a given org AND
    TanStack Query holds a cached response for that org's data THEN the cached
    data is displayed on navigation while background refetches run, producing
    0 visible loading skeleton frames for recently visited orgs on first render
- **Rule active-org-update:** IF `beforeLoad` succeeds and the route
    completes THEN the session's `activeOrganizationId` is updated to the
    new org's identifier before any dashboard data is rendered for that route

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated member | Opens OrgSwitcher, views all orgs they belong to in the dropdown, navigates to any org they are a member of | Cannot navigate to or load dashboard data for an org they are not a member of | OrgSwitcher dropdown lists only orgs the user has an active membership record for — orgs they are not a member of are not shown |
| Unauthenticated visitor | No actions permitted — dashboard routes redirect to the sign-in page before the OrgSwitcher is rendered | Cannot access OrgSwitcher, dropdown, or any org dashboard route | No org data or switcher UI is visible to unauthenticated visitors at any point |

## Constraints

- The URL slug `/app/{newSlug}/` is the single source of truth for org
    context — the dashboard does not maintain a separate client-side
    org-context store that can diverge from the URL. The route slug and
    the session `activeOrganizationId` must be in sync at all times; any
    divergence is treated as an error condition.
- The OrgSwitcher dropdown must list only organizations for which the user
    has an active membership record — the count of orgs in the dropdown must
    equal the count of rows in the `member` table for that user with an active
    status, and it must not include orgs the user does not belong to.
- Navigating to an org the user is not a member of must produce HTTP 403 and
    a router redirect to the user's default org — the session
    `activeOrganizationId` must not be updated on a 403 response, and the
    redirect must restore the previous valid org context within 1 navigation
    cycle.
- The context switch does not issue a standalone API call to update
    `activeOrganizationId` — it is driven exclusively by the route change and
    the `$orgSlug` `beforeLoad` hook. The count of standalone context-switch
    API calls per org navigation event must equal 0.

## Acceptance Criteria

- [ ] The OrgSwitcher component is present in the dashboard header and its text content equals the localized name of the user's current organization — the component element is present in the DOM and its inner text is non-empty
- [ ] Clicking the OrgSwitcher opens a dropdown — the count of dropdown items is non-empty and equals the count of active membership rows for that user in the `member` table where status equals active
- [ ] The current organization is visually marked as active in the dropdown — the count of items with a checked or highlighted active class equals 1
- [ ] Clicking a different org in the dropdown navigates the browser to `/app/{newSlug}/` — the window location pathname is non-empty and equals `/app/{newSlug}/` after the click event, and the count of navigation errors equals 0
- [ ] The `$orgSlug` `beforeLoad` hook updates the session `activeOrganizationId` — the session record's `activeOrganizationId` is non-empty and equals the new org's identifier after navigation completes
- [ ] No standalone context-switch API call is issued when switching orgs — the count of requests to a dedicated context-switch endpoint during the navigation event equals 0
- [ ] After route change, TanStack Query issues new requests keyed by the new org's identifier — the count of pending queries for the old org key equals 0 after navigation settles
- [ ] The sidebar, header, and content area reflect the new organization after re-fetch — the page title is non-empty and its text content equals the new org's name, and the count of UI elements displaying the previous org's name equals 0
- [ ] Navigating to an org the user is not a member of returns 403 and redirects to the user's default org route — the session `activeOrganizationId` is unchanged and the URL equals the previous valid org route after redirect
- [ ] The URL `/app/{orgSlug}/` is bookmarkable — pasting it into a browser while authenticated as a member of that org loads the org dashboard directly, and the count of intermediate redirects to a context-switch endpoint equals 0
- [ ] Cached data for a recently visited org renders on initial navigation without a loading skeleton — the count of visible loading skeleton frames on the initial render equals 0 before the background refetch completes
- [ ] The OrgSwitcher dropdown is not present in the DOM after a selection event triggers navigation — the count of rendered dropdown elements after selection equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User opens a bookmarked URL `/app/{orgSlug}/` for an org they were removed from since creating the bookmark | The `beforeLoad` hook finds no active membership record, returns HTTP 403, and the router redirects the user to their default org route — the unauthorized org's dashboard data is never loaded | HTTP response status equals 403 and the final window location pathname equals the default org route, not the bookmarked path |
| User switches org while a background data fetch is still in flight for the current org | TanStack Query cancels or ignores the in-flight query for the old org key and immediately issues new queries keyed by the new org — no stale data from the old org appears in the dashboard after navigation settles | The network log shows the old org query was cancelled or its response was discarded, and the rendered data matches only the new org's identifier |
| User belongs to only 1 organization and opens the OrgSwitcher dropdown | The dropdown opens and shows 1 item representing the current org, which is marked as active — there are no other selectable items, and the user cannot switch because no other orgs are available | The count of dropdown items equals 1 and the count of non-active selectable items equals 0 |
| Two browser tabs are open to different orgs belonging to the same user | Each tab maintains its own URL-derived org context independently — switching org in one tab does not alter the other tab's URL or session context until a full page refresh occurs in the other tab | After switching org in tab A, tab B's window location pathname remains unchanged and its dashboard still shows the previous org's data |
| User clicks the OrgSwitcher while the current org's data is still loading | The dropdown opens and lists all orgs as normal — the partial loading state of the current org does not block the switcher from being usable | The dropdown is visible and interactive within 300 ms of the click, regardless of whether the current org's data fetch has completed |
| User pastes a URL for a valid org they belong to into the browser address bar | The router resolves the slug, `beforeLoad` confirms membership, and the dashboard loads for that org — `activeOrganizationId` is set to the pasted org's identifier | The session `activeOrganizationId` equals the org from the pasted URL and the dashboard reflects that org's data |

## Failure Modes

- **Revoked membership: user navigates to an org they no longer belong to**

    **What happens:** The user clicks a bookmarked URL or follows a shared link to an org dashboard from which their membership was revoked after the link was created, and `beforeLoad` finds no active membership record for that org. This occurs when an admin removes the user from an organization during or after a prior authenticated session.

    **Source:** Stale URL retained by the user after an admin removed them from the organization, or a shared link distributed to the user before their membership was revoked.

    **Consequence:** Without the membership guard the user would load another organization's dashboard data — page titles, member lists, settings, and confidential org-specific content would be exposed to an unauthorized user who has been removed from that org.

    **Recovery:** The `beforeLoad` hook rejects the route and returns HTTP 403 — the router falls back to redirecting the user to their default org route, and the unauthorized org's data is never fetched or rendered. The count of authorized-data responses for a revoked-membership navigation equals 0.

- **Context divergence: URL slug and session `activeOrganizationId` disagree after partial navigation failure**

    **What happens:** A transient network interruption or an unhandled router exception causes the browser history to push the new org slug while the `beforeLoad` hook's session-update write did not complete, leaving the URL reflecting one org and `activeOrganizationId` still pointing to the previous org.

    **Source:** Unhandled exception or network timeout in the `beforeLoad` hook that allows the history push to occur but prevents the server-side session write from completing successfully.

    **Consequence:** Dashboard queries keyed by the URL slug conflict with the stale `activeOrganizationId`, producing responses that mix data from 2 different orgs — member counts, settings panels, and page titles reflect the wrong organization's data until consistency is restored.

    **Recovery:** The router error boundary catches the incomplete navigation and alerts the user with a localized error message — the session `activeOrganizationId` retries the update on the next `beforeLoad` invocation, and a full page reload restores consistency between the URL slug and the session value. The count of diverged states that persist across a full page reload equals 0.

- **Stale cache cross-contamination: background refetch resolves for previous org after navigation**

    **What happens:** The user navigates from org A to org B, but a pending background refetch keyed to org A resolves after the navigation completes and writes org A's data into the active view, overwriting org B's data that the user expects to see.

    **Source:** Race condition between a background refetch keyed to the prior org identifier and the TanStack Query cache write that occurs after the navigation event updates the active org context in the dashboard.

    **Consequence:** The user sees member counts, settings panels, and page titles from org A displayed in the org B dashboard — confidential data from an organization the user intended to leave is momentarily visible, causing confusion and potential data exposure.

    **Recovery:** TanStack Query caches are keyed by org identifier — the query client rejects or discards responses whose cache key does not match the current active route slug, and the dashboard falls back to displaying only data from cache keys matching the current org. The count of cross-org data writes to the active view after navigation settles equals 0.

- **Stale dropdown: org entry remains visible after membership is revoked mid-session**

    **What happens:** The user's org membership list was fetched at session start and cached client-side, but an admin removes them from one of those orgs during the active session. The OrgSwitcher dropdown still shows the removed org because the client-side list has not been refreshed, and the user clicks it to initiate a navigation.

    **Source:** Stale client-side membership cache from an earlier fetch, combined with a server-side membership change that occurred after the cache was populated during the current authenticated session.

    **Consequence:** The user clicks the stale org entry and triggers a navigation to `/app/{removedOrgSlug}/` — without a server-side guard at the route level, the unauthorized org context would be applied to the session and org data would be returned.

    **Recovery:** The `beforeLoad` hook performs a live server-side membership check on every navigation event — it rejects the route and returns HTTP 403 for the removed org, logs the unauthorized access attempt, and redirects the user to their default org route. The stale dropdown entry produces 0 successful authorized-data responses after membership revocation.

## Declared Omissions

- This specification does not address how the initial organization is selected when a user first signs in after account creation — that behavior is defined in the session-lifecycle spec as a separate concern covering post-authentication org resolution
- This specification does not address creating, renaming, or deleting organizations — those operations are defined in the user-creates-an-organization and user-updates-organization-settings specs as distinct flows
- This specification does not address organization member invitation or removal flows — those operations are defined in separate member-management specs and are outside the scope of the org-switching interaction
- This specification does not address deep-link routing within an org such as navigating directly to a specific settings page or member detail view via a shared URL — that behavior is governed by the route hierarchy defined in the web app routing spec
- This specification does not address mobile-specific OrgSwitcher UI layout or native navigation transitions — that behavior is defined in the mobile platform specs for the Expo app

## Related Specifications

- [session-lifecycle](session-lifecycle.md) — Post-authentication session management including initial org resolution and `activeOrganizationId` assignment that this switching flow depends on
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration and organization plugin wiring that manages `activeOrganizationId` updates in the session during org switching
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `organization` and `member` tables that `beforeLoad` queries to verify membership and load org data
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure providing the translation keys for OrgSwitcher labels, dropdown items, and error messages
- [api-framework](../foundation/api-framework.md) — Hono middleware stack and global error handler that returns HTTP 403 responses when the membership guard in `beforeLoad` rejects an unauthorized org navigation

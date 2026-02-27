---
id: SPEC-2026-044
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Navigates the Dashboard

## Intent

This spec defines how an authenticated user interacts with the
dashboard shell after landing on `/app/{orgSlug}/`. The dashboard
renders three persistent regions — a sidebar, a header bar, and a
main content area powered by a TanStack Router Outlet. The sidebar
provides organization-level and user-level navigation links with
localized labels, and it adapts between a persistent panel on
desktop and a drawer overlay on mobile viewports. The header bar
contains controls for collapsing the sidebar, switching
organizations, toggling the theme, and accessing account actions.
All pages under the `$orgSlug/` route share organization context
loaded by the `$orgSlug` layout route's `beforeLoad` hook, which
reads the URL slug and provides org data to every child route
without re-fetching the org identity on each navigation.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| TanStack Router Outlet (content area) | read | When the user clicks a sidebar nav item and the router resolves the corresponding child route to render in the content area | The router error boundary catches the failed route resolution and renders a localized error page in the content area, preventing the user from seeing a blank or broken layout |
| Zustand sidebar-store with localStorage persistence | read/write | When the user clicks the collapse toggle to expand or collapse the sidebar, and on page load to restore the persisted sidebar state | The sidebar falls back to its default expanded state on desktop and closed state on mobile, and the user's previous collapse preference is lost until localStorage becomes available again |
| `$orgSlug` beforeLoad hook (layout route) | read | When the dashboard route mounts or the user navigates to a new `$orgSlug` path, the hook loads the active organization data from the URL slug | The beforeLoad hook returns an error and the router redirects the user to the sign-in page or a fallback route, preventing the dashboard from rendering with missing org context data |
| @repo/i18n (localization infrastructure) | read | When the sidebar renders nav item labels, the header renders control labels, and error messages are displayed to the user in the dashboard shell | The UI degrades to displaying raw translation keys instead of localized strings, and the user sees untranslated identifiers for all sidebar labels and header controls until translations load |

## Behavioral Flow

1. **[User]** is authenticated and lands on `/app/{orgSlug}/` — the
    dashboard shell renders with three regions: a sidebar on the left,
    a header bar across the top, and the main content area in the
    center that acts as a TanStack Router Outlet for the active child
    route

2. **[Client]** renders the sidebar divided into two groups — the
    first group contains organization-level pages with localized
    labels: Overview, Members, Teams, and Org Settings; the second
    group is a user-level section containing a link to personal
    Settings

3. **[User]** clicks any nav item in the sidebar to load the
    corresponding child route into the content area — the sidebar
    itself does not re-render or reset when the content area swaps
    to the new route

4. **[Client]** on desktop viewports, the sidebar is persistent and
    visible by default — a collapse toggle in the header shrinks it
    to a narrow icon rail, showing only icons without labels

5. **[Client]** reads the Zustand sidebar-store to determine
    whether the sidebar is expanded or collapsed — the store persists
    the expanded or collapsed state to localStorage so the sidebar
    remembers its position across page reloads and sessions

6. **[Client]** on mobile viewports, the sidebar transforms into a
    drawer overlay that slides in from the side — a hamburger button
    in the header opens it, and tapping outside the drawer or
    selecting a nav item closes it automatically

7. **[Client]** renders the header bar across the top of the
    dashboard containing several controls: a collapse toggle on the
    left that controls the sidebar's expanded or collapsed state, an
    org switcher that displays the current organization's name and
    provides access to switch between organizations, a theme toggle
    that lets the user flip between light, dark, and system themes,
    and an avatar dropdown in the far right that provides access to
    account-related actions

8. **[Client]** the `$orgSlug` layout route's `beforeLoad` hook loads
    the active organization's data based on the slug from the URL —
    all pages under the `$orgSlug/` route share the same organization
    context, and every child route inherits this context automatically

9. **[User]** navigates between Overview, Members, Teams, and Org
    Settings — all pages operate within the same org context without
    re-fetching the org identity because the `beforeLoad` hook has
    already loaded and provided the org data to the route tree

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| unauthenticated | dashboard_loading | User navigates to `/app/{orgSlug}/` with a valid session | User has a valid authentication session and is a member of the org identified by the URL slug |
| dashboard_loading | dashboard_ready | `$orgSlug` beforeLoad hook resolves org data and the shell layout renders with sidebar, header, and content area | Org data loaded and TanStack Router Outlet rendered the default child route for the org |
| dashboard_ready | navigating_child | User clicks a sidebar nav item to load a different child route into the content area | The target route is a valid child route of the `$orgSlug` layout and the user has permission to view it |
| navigating_child | dashboard_ready | TanStack Router resolves the new child route and renders it in the content area while sidebar and header remain stable | The child route component mounted and rendered without errors in the Router Outlet |
| sidebar_expanded | sidebar_collapsed | User clicks the collapse toggle in the header on a desktop viewport to shrink the sidebar to an icon rail | The viewport width is at or above the desktop breakpoint and the sidebar is currently in expanded state |
| sidebar_collapsed | sidebar_expanded | User clicks the collapse toggle in the header on a desktop viewport to restore the sidebar to full width with labels | The viewport width is at or above the desktop breakpoint and the sidebar is currently in collapsed state |
| mobile_drawer_closed | mobile_drawer_open | User taps the hamburger button in the header on a mobile viewport to open the sidebar drawer overlay | The viewport width is below the desktop breakpoint and the drawer is currently closed |
| mobile_drawer_open | mobile_drawer_closed | User taps outside the drawer overlay or selects a nav item in the drawer to close it | The drawer is currently open and the user interacted outside the drawer area or selected a navigation item |
| dashboard_ready | theme_changed | User clicks the theme toggle in the header to cycle between light, dark, and system themes | The theme toggle is rendered in the header and the user clicked it to change the active theme |
| dashboard_loading | auth_redirect | `$orgSlug` beforeLoad hook fails because the session is invalid or the user is not a member of the org | The authentication check or membership verification in the beforeLoad hook returned a failure response |

## Business Rules

- **Rule sidebar-state-persistence:** IF the user clicks the
    collapse toggle to expand or collapse the sidebar THEN the
    Zustand sidebar-store writes the new state to localStorage and
    on subsequent page reloads the store reads localStorage to
    restore the sidebar to its persisted state — the count of
    localStorage writes per toggle click equals 1
- **Rule org-context-from-slug:** IF the user navigates to
    `/app/{orgSlug}/` THEN the `$orgSlug` layout route's
    `beforeLoad` hook reads the slug from the URL and loads the
    organization data for that slug — no separate API call is issued
    to set org context because the URL slug is the sole source of
    truth for the active organization
- **Rule mobile-drawer-behavior:** IF the viewport width is below
    the desktop breakpoint THEN the sidebar renders as a drawer
    overlay instead of a persistent panel, and tapping outside the
    drawer or selecting a nav item closes the drawer — the count of
    open drawer instances after a nav item selection equals 0
- **Rule auth-required:** IF the user is not authenticated THEN the
    dashboard route redirects the user to the sign-in page before
    rendering the shell layout — the count of dashboard shell renders
    for unauthenticated users equals 0
- **Rule child-route-stability:** IF the user clicks a sidebar nav
    item THEN only the TanStack Router Outlet content area re-renders
    with the new child route — the sidebar and header remain mounted
    and stable, and the count of sidebar re-renders per child route
    navigation equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | Clicks all sidebar nav items including Overview, Members, Teams, Org Settings, and personal Settings; uses collapse toggle, org switcher, theme toggle, and avatar dropdown | No actions are denied to the owner within the dashboard shell navigation — all sidebar items and header controls are accessible | All sidebar nav items and header controls are visible and interactive for the owner role without restriction |
| Admin | Clicks all sidebar nav items including Overview, Members, Teams, Org Settings, and personal Settings; uses collapse toggle, org switcher, theme toggle, and avatar dropdown | No navigation actions are denied to admins within the dashboard shell — admins can access all sidebar items and header controls | All sidebar nav items and header controls are visible and interactive for the admin role without restriction |
| Member | Clicks sidebar nav items including Overview, Members, Teams, and personal Settings; uses collapse toggle, org switcher, theme toggle, and avatar dropdown | Cannot access Org Settings page — clicking Org Settings either hides the link or the route guard redirects the member away from the settings page | The Org Settings sidebar link is either hidden from the member's sidebar or visually disabled to indicate the member cannot access that page |
| Unauthenticated | No actions are permitted — the dashboard route's auth guard redirects the user to the sign-in page before the shell layout renders | Cannot view or interact with any part of the dashboard shell including sidebar, header, content area, or any navigation controls | No dashboard UI is visible — the redirect to sign-in occurs before any dashboard components mount in the DOM |

## Constraints

- The sidebar collapse state persists to localStorage via the Zustand
    sidebar-store — the stored value must survive browser restarts
    and the sidebar must restore to its persisted state within 1
    render cycle after the dashboard shell mounts, with 0 visible
    flicker between default and persisted states.
- The TanStack Router Outlet in the content area must render the
    active child route within 300 ms of a sidebar nav item click on
    a warm cache — the sidebar and header must remain mounted and
    must not unmount or re-render during the child route transition.
- The `$orgSlug` beforeLoad hook must load organization data before
    any child route renders — the count of child route renders that
    occur before the org data is available equals 0, ensuring all
    child routes have access to org context on their initial render.
- The mobile drawer overlay must close within 200 ms of a nav item
    selection or an outside tap — the count of open drawer instances
    after the close animation completes equals 0.
- All sidebar nav item labels and header control labels must display
    localized strings from @repo/i18n — the count of raw translation
    keys visible in the rendered DOM equals 0 when the i18n namespace
    has loaded.
- The dashboard shell layout must render identically in LTR and RTL
    locales using logical CSS properties — the sidebar uses
    `inset-inline-start` and the header controls use logical padding
    via `padding-inline-start` and `padding-inline-end`.

## Acceptance Criteria

- [ ] The dashboard shell renders three distinct regions — sidebar, header, and content area — when the user lands on `/app/{orgSlug}/`, and the count of rendered shell regions equals 3
- [ ] The sidebar contains exactly 5 nav items with localized labels: Overview, Members, Teams, Org Settings, and personal Settings — the count of sidebar nav items equals 5 for an owner or admin
- [ ] Clicking a sidebar nav item loads the corresponding child route into the TanStack Router Outlet without unmounting the sidebar or header — the count of sidebar unmount events equals 0 and the sidebar DOM element remains present in the DOM after navigation
- [ ] The collapse toggle in the header shrinks the sidebar to an icon rail on desktop viewports — the sidebar width decreases to the icon-rail width and the count of visible text labels in the collapsed sidebar equals 0
- [ ] The Zustand sidebar-store persists the collapse state to localStorage — after toggling the sidebar and reloading the page, the localStorage value equals the last toggle state and the sidebar renders in its persisted state within 1 render cycle
- [ ] On mobile viewports, the sidebar renders as a drawer overlay opened by the hamburger button — the drawer is not present in the visible DOM until the hamburger button is clicked
- [ ] Tapping outside the mobile drawer overlay or selecting a nav item closes the drawer — the count of open drawer instances after the close event equals 0
- [ ] The header bar contains a collapse toggle, an org switcher displaying the current org name, a theme toggle, and an avatar dropdown — the count of header controls equals 4
- [ ] The theme toggle cycles between light, dark, and system themes — after clicking the toggle, the document root element's theme attribute value is non-empty and equals the selected theme string
- [ ] The `$orgSlug` beforeLoad hook loads org data from the URL slug before any child route renders — the org context object is non-empty and its slug property equals the URL path segment
- [ ] Navigating between Overview, Members, Teams, and Org Settings does not re-fetch the org identity — the count of org-identity API requests after the initial beforeLoad resolution equals 0 during intra-org navigation
- [ ] An unauthenticated user navigating to `/app/{orgSlug}/` is redirected to the sign-in page — the final window location pathname equals the sign-in route and the count of rendered dashboard shell components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User reloads the page while the sidebar is in collapsed state | The Zustand sidebar-store reads the persisted collapsed state from localStorage and the sidebar renders in collapsed icon-rail mode without first rendering expanded and then collapsing | The sidebar width on initial render equals the icon-rail width, and the count of layout shift events during mount equals 0 |
| User resizes the browser window from desktop to mobile viewport width while the sidebar is expanded | The sidebar transitions from a persistent expanded panel to a closed mobile drawer overlay — the persistent sidebar is removed from the layout and the drawer is closed by default | The sidebar persistent panel is not present in the visible DOM at mobile viewport width, and the drawer overlay count equals 0 until the hamburger button is tapped |
| User navigates to `/app/{orgSlug}/` with a slug that does not match any organization in the database | The `$orgSlug` beforeLoad hook fails to find org data for the slug and returns an error — the router renders a localized 404-style error page in the content area instead of the dashboard | The error boundary renders an error component with a non-empty localized message, and the count of rendered child route components equals 0 |
| User clicks a sidebar nav item while the previous child route is still loading in the content area | The TanStack Router cancels or supersedes the pending navigation and resolves the latest clicked route — the content area renders only the most recently selected child route | The content area displays the component for the last-clicked nav item, and the count of rendered child route components equals 1 |
| User opens the dashboard in a browser with localStorage disabled or unavailable | The Zustand sidebar-store cannot read or write the persisted collapse state and the sidebar renders in its default expanded state on desktop and closed drawer state on mobile | The sidebar renders in expanded state on desktop, and the count of console errors from the sidebar-store equals 0 because the store handles the missing localStorage gracefully |
| User clicks the collapse toggle rapidly multiple times within 500 ms | The sidebar-store processes each toggle sequentially and the final state reflects the last toggle — the sidebar does not get stuck in an intermediate or inconsistent animation state | The sidebar's final collapsed or expanded state matches the expected result of an odd or even number of toggles, and the localStorage value matches the rendered state |

## Failure Modes

- **beforeLoad hook failure: org data fails to load from the URL slug**

    **What happens:** The `$orgSlug` layout route's `beforeLoad` hook encounters a network error or server error when attempting to load the organization data for the slug in the URL, leaving the dashboard without org context data for any child route to consume.

    **Source:** A transient network interruption, a server-side error in the org data endpoint, or a malformed slug in the URL that the server cannot resolve to a valid organization record in the database.

    **Consequence:** Without org context data, all child routes under the `$orgSlug/` layout would render with missing organization information — page titles, member lists, settings panels, and org-specific data would be absent or display undefined values throughout the dashboard.

    **Recovery:** The beforeLoad hook returns an error to the router, which falls back to rendering a localized error boundary page in the content area and logs the failed org data request — the user can retry by refreshing the page or navigating to a different org route.

- **localStorage unavailable: sidebar-store cannot persist collapse state**

    **What happens:** The Zustand sidebar-store attempts to read the persisted sidebar collapse state from localStorage on page load, but localStorage is unavailable because the browser has disabled it, storage quota is exceeded, or the user is in a restricted browsing mode that blocks storage access.

    **Source:** Browser privacy settings that disable localStorage, storage quota exceeded from other application data, or a restricted browsing mode such as certain incognito configurations that block persistent storage writes and reads.

    **Consequence:** The sidebar-store cannot restore the user's preferred collapse state on page load and cannot persist new toggle actions — the user loses their sidebar preference on every page reload and the sidebar resets to its default expanded state each time the dashboard mounts.

    **Recovery:** The Zustand sidebar-store falls back to using the default expanded state on desktop and closed drawer state on mobile when localStorage is unavailable — the store catches the storage access error and logs a warning, allowing the dashboard to render without crashing.

- **i18n namespace fails to load: sidebar and header labels display raw translation keys**

    **What happens:** The @repo/i18n infrastructure fails to load the dashboard namespace containing translation strings for sidebar nav item labels and header control labels, causing the i18n lookup to return raw translation keys instead of localized human-readable strings.

    **Source:** A network request failure when fetching the translation JSON file for the user's locale, a misconfigured namespace path in the i18n initialization, or a missing translation file for a newly added locale that has not been populated with dashboard strings.

    **Consequence:** The user sees raw keys like `dashboard.sidebar.overview` and `dashboard.header.theme_toggle` instead of localized labels in the sidebar and header — the dashboard is functionally usable but the navigation labels are unintelligible to users who do not recognize the translation key naming convention.

    **Recovery:** The i18n infrastructure degrades to displaying the raw translation keys as fallback text and logs the namespace loading failure — the dashboard retries loading the namespace on the next navigation event, and the user can trigger a retry by refreshing the page to re-request the missing translation file.

- **TanStack Router Outlet fails to render the child route component**

    **What happens:** The TanStack Router Outlet encounters an error when attempting to render the child route component after the user clicks a sidebar nav item — the component import fails due to a code-splitting chunk load error or the component throws during its initial render lifecycle.

    **Source:** A code-splitting chunk fails to load over the network because of a transient connection issue or a deployment that invalidated the chunk hash, or the child route component throws an unhandled exception during rendering from unexpected data shapes.

    **Consequence:** The content area displays a blank or broken view while the sidebar and header remain functional — the user cannot access the page they navigated to and sees either a white screen or an uncaught error in the content region of the dashboard layout.

    **Recovery:** The router error boundary catches the failed route render and falls back to displaying a localized error message in the content area with a retry action — the user can click retry to re-attempt loading the chunk, and the sidebar remains interactive so the user can navigate to a different page.

## Declared Omissions

- This specification does not define the content, layout, or data-fetching logic of individual child route pages such as the Overview dashboard, Members list, Teams view, or Org Settings form — those are defined in their own dedicated behavioral specs.
- This specification does not cover the org switcher's internal dropdown behavior, organization creation, or the full org-switching flow — that behavior is defined in the user-switches-organization spec as a separate interaction.
- This specification does not address authentication flows, session validation, or sign-in page behavior — the auth guard redirect is referenced but the sign-in flow itself is covered by the session-lifecycle and sign-in specs.
- This specification does not define the avatar dropdown's internal menu items or account management actions — those are governed by separate user-settings and account-management behavioral specs.
- This specification does not cover the theme toggle's persistence mechanism or the full theming infrastructure — the toggle interaction is referenced but the theme storage and CSS variable system are defined in the foundation theming spec.

## Related Specifications

- [session-lifecycle](session-lifecycle.md) — Defines post-authentication session management and initial org resolution that determines which org the user lands on before the dashboard shell renders
- [user-switches-organization](user-switches-organization.md) — Covers the org switcher dropdown interaction and the full org context switch flow that the dashboard header's org switcher component triggers
- [shared-i18n](../foundation/shared-i18n.md) — Provides the internationalization infrastructure and translation loading mechanism that supplies localized labels for all sidebar nav items and header controls
- [database-schema](../foundation/database-schema.md) — Defines the organization table schema that the `$orgSlug` beforeLoad hook queries to load org data from the URL slug for the dashboard context
- [auth-server-config](../foundation/auth-server-config.md) — Configures the Better Auth server and session management that the dashboard route's auth guard relies on to redirect unauthenticated users to sign-in

---
id: SPEC-2026-075
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Navigates Mobile App

## Intent

This spec defines how a user navigates the mobile application built
with Expo 54 and React Native. Expo Router v6 provides file-based
routing that organizes screens as files within the app directory and
generates typed routes automatically. The primary navigation structure
uses tab navigation for top-level sections — dashboard, members,
teams, settings — and stack navigation for drill-down flows within
each section. Navigating between tabs preserves the state of each
section so the user can switch away and return without losing their
place. `react-native-gesture-handler` enables native gesture
recognition including swipe-from-left-edge to go back in a stack,
long-press for contextual actions, and pull-to-refresh on list
screens. `react-native-reanimated` drives screen transition animations
on the UI thread for 60fps fluidity. `react-native-safe-area-context`
ensures content respects device-specific insets for notches, status
bars, dynamic islands, and home indicators. Deep links using the
`docodego://` scheme open directly to the corresponding screen, with
an unauthenticated redirect to sign-in that returns to the deep link
target after authentication. The app consumes `@repo/contracts` for
typed oRPC API calls, `@repo/i18n` for localized strings with RTL
support via `expo-localization`, and `@repo/library` for shared
validators, constants, and formatters.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Expo Router v6 (file-based routing engine that generates typed routes from the app directory structure and manages tab and stack navigation) | read/write | When the app launches and Expo Router resolves the initial route from the file system, and when the user taps a tab or drills into a stack screen triggering a route transition | The router fails to resolve the requested route and falls back to rendering a localized error screen in the current navigation context, preventing the user from reaching the target screen |
| `react-native-gesture-handler` (native gesture recognition library that intercepts touch events for swipe-back, long-press, and pull-to-refresh interactions) | read | When the user performs a touch gesture on a screen — swiping from the left edge to go back, long-pressing an item for contextual actions, or pulling down on a list to refresh data | Gesture recognition is unavailable and the user falls back to tapping the back button in the header for stack navigation and tapping explicit refresh buttons instead of pull-to-refresh gestures |
| `react-native-reanimated` (animation library that runs transition animations on the UI thread for 60fps push and pop screen transitions) | read | When Expo Router performs a screen transition — pushing a new screen onto a stack or popping back to the previous screen — and reanimated drives the shared-element or slide animation | Screen transitions render without animation and the new screen appears instantly with no visual transition, degrading the navigation experience but preserving functional correctness of the route change |
| `react-native-safe-area-context` (inset provider that supplies device-specific measurements for notches, status bars, dynamic islands, and home indicators) | read | When each screen renders its layout and queries the safe area insets to position content away from system UI elements that would otherwise clip or obscure the screen content | Content renders without inset awareness and the user sees text, buttons, or interactive elements hidden behind the device notch, status bar, dynamic island, or home indicator bar at the bottom |
| `@repo/contracts` (typed oRPC contract definitions shared between mobile client and API that enforce compile-time type alignment for all API requests and responses) | read | When a screen fetches data from the API using an oRPC client call — loading dashboard data, member lists, team details, or settings values from the Cloudflare Workers API endpoint | The oRPC client call fails and the screen falls back to displaying a localized error message with a retry action, and previously cached data is displayed if available in the local query cache |
| `@repo/i18n` with `expo-localization` (internationalization infrastructure that loads locale-specific translations and activates RTL layout based on the detected device locale) | read | When the app initializes and `expo-localization` detects the device locale to load the matching translation namespace, and when each screen renders localized labels, messages, and formatters | The i18n infrastructure falls back to displaying raw translation keys instead of localized strings, and RTL layout activation fails so Arabic and Hebrew locales render in LTR direction until translations load |

## Behavioral Flow

1. **[App]** launches and Expo Router v6 initializes file-based
    routing by scanning the app directory structure to generate typed
    routes — the router builds the navigation tree with tab navigation
    at the root level and stack navigators nested within each tab
    section for drill-down flows

2. **[App]** renders the bottom tab bar with exactly 4 tabs —
    dashboard, members, teams, and settings — each tab maps to a
    top-level route file in the app directory and displays a localized
    label from `@repo/i18n` alongside an icon identifying the section

3. **[App]** initializes `react-native-safe-area-context` to query
    device-specific insets for the notch, status bar, dynamic island,
    and home indicator — every screen wraps its content within the safe
    area boundaries so that no interactive element or text is clipped
    or hidden behind system UI elements

4. **[App]** detects the device locale via `expo-localization` and
    loads the matching translation namespace from `@repo/i18n` — if
    the detected locale is Arabic or Hebrew, React Native activates
    RTL layout direction so the tab bar, navigation headers, and all
    screen content mirror to right-to-left reading order

5. **[User]** taps a tab in the bottom tab bar to switch between
    dashboard, members, teams, and settings sections — Expo Router
    navigates to the corresponding top-level route and the tab bar
    highlights the active tab with a visual indicator

6. **[App]** preserves the navigation state of each tab section when
    the user switches between tabs — if the user drilled three screens
    deep in the members tab, switched to settings, and returned to
    members, the members tab restores to the third screen without
    resetting the stack to the root

7. **[User]** taps an item within a tab section to drill into a
    detail screen — Expo Router pushes a new screen onto the stack
    navigator for that tab and `react-native-reanimated` drives a
    slide-from-right push animation on the UI thread at 60 frames per
    second or higher

8. **[User]** swipes from the left edge of the screen to go back in
    a stack — `react-native-gesture-handler` recognizes the
    horizontal pan gesture starting within 20 pixels of the left edge
    and `react-native-reanimated` drives the interactive pop animation
    that follows the user's finger position at 60 frames per second or
    higher

9. **[User]** long-presses an item on a list screen to trigger
    contextual actions — `react-native-gesture-handler` recognizes the
    long-press gesture after a 500 ms hold duration and the app
    displays a contextual action menu with options relevant to the
    pressed item

10. **[User]** pulls down on a list screen to refresh the data —
    `react-native-gesture-handler` recognizes the pull-to-refresh
    gesture and the app re-fetches the list data from the API via
    `@repo/contracts` oRPC calls, replacing the stale list content
    with the fresh response within 3000 ms on a standard connection

11. **[App]** implements infinite scroll on paginated list screens —
    when the user scrolls within 200 pixels of the list bottom, the
    app fetches the next page of data via `@repo/contracts` oRPC calls
    and appends the new items to the existing list without replacing
    the currently visible content

12. **[User]** taps a `docodego://` deep link from a notification,
    email, or chat message on their device — Expo Router resolves the
    path from the deep link URL and navigates to the matching screen
    inside the app

13. **[App]** checks the authentication state when a deep link
    arrives — if the user is not authenticated, the app redirects to
    the sign-in screen and stores the deep link target path; after the
    user completes sign-in, the app navigates to the stored target
    path so the user reaches the intended screen

14. **[User]** switches the active organization from within the
    navigation structure — the app updates the organization context
    and reloads the data for the current tab section to reflect the
    newly selected organization without forcing the user to leave the
    app or restart the navigation flow

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| app_launching | tabs_ready | Expo Router v6 finishes initializing the file-based routing tree, safe area insets are loaded, and the bottom tab bar renders with 4 tabs visible | The user has a valid authentication session and at least one organization membership to display content for |
| app_launching | sign_in_required | Expo Router initializes but the authentication check determines no valid session exists for the current user | The session token is absent, expired, or invalid and the auth guard intercepts the navigation before the tab bar renders |
| tabs_ready | tab_switching | The user taps a different tab in the bottom tab bar to navigate from the current section to another top-level section | The target tab is not the currently active tab and the tab bar is visible and interactive at the bottom of the screen |
| tab_switching | tabs_ready | Expo Router completes the tab transition and renders the target tab section, restoring any previously preserved stack navigation state within that tab | The target tab route resolved and the screen component mounted with its preserved navigation state intact |
| tabs_ready | stack_pushing | The user taps an item within the current tab section to drill into a detail screen, triggering a stack push navigation event | The current tab section has a stack navigator and the tapped item maps to a valid child route within that stack |
| stack_pushing | stack_active | Expo Router pushes the new screen onto the stack and `react-native-reanimated` completes the slide-from-right push animation at 60fps on the UI thread | The new screen component mounted and the push animation completed without dropping below 60 frames per second |
| stack_active | stack_popping | The user swipes from the left edge to go back or taps the header back button, triggering a stack pop navigation event handled by `react-native-gesture-handler` | The current stack has at least 2 screens and the swipe gesture started within 20 pixels of the left screen edge |
| stack_popping | tabs_ready | Expo Router pops the top screen from the stack and the pop animation completes, returning to the previous screen or the tab root if only one screen remained | The pop animation completed and the previous screen in the stack rendered with its preserved state |
| stack_popping | stack_active | Expo Router pops the top screen from the stack but more than one screen remains in the stack after the pop, keeping the user in a drilled-down state | The stack contains 2 or more screens after the pop operation completes and the previous screen renders |
| tabs_ready | deep_link_resolving | The user taps a `docodego://` deep link from a notification, email, or chat message and Expo Router receives the path for resolution | The deep link URL uses the `docodego://` scheme and the path portion is a non-empty string |
| deep_link_resolving | tabs_ready | Expo Router resolves the deep link path to a matching screen and navigates to it within the correct tab and stack context determined by the route file location | The user has a valid session and the deep link path matches a defined route in the Expo Router file structure |
| deep_link_resolving | sign_in_required | The deep link arrives but the user has no valid authentication session, so the app redirects to sign-in and stores the target path | The session check returns invalid and the deep link target path is stored for post-authentication redirect |
| sign_in_required | deep_link_resolving | The user completes sign-in and the app retrieves the stored deep link target path to resume navigation to the intended screen | A valid session is established and the stored deep link target path is a non-empty string in memory |
| sign_in_required | tabs_ready | The user completes sign-in without a stored deep link target and the app navigates to the default dashboard tab | A valid session is established and no stored deep link target path exists in memory |
| tabs_ready | org_switching | The user selects a different organization from the organization switcher within the navigation structure to change the active org context | The user is a member of the selected organization and the selected org differs from the currently active org |
| org_switching | tabs_ready | The app updates the organization context, reloads the data for the current tab section to reflect the new org, and the tab bar remains visible | The org context update completes and the current tab section re-renders with data for the newly selected organization |

## Business Rules

- **Rule tab-state-preserved-on-switch:** IF the user drills into a
    stack within any tab section and then switches to a different tab
    THEN the previous tab's stack navigation state is preserved in
    memory — when the user returns to the previous tab, the count of
    stack screens equals the same depth as when the user left and the
    screen content matches the last viewed state
- **Rule swipe-back-navigates-stack:** IF the user swipes from the
    left edge of the screen starting within 20 pixels of the edge THEN
    `react-native-gesture-handler` triggers a stack pop navigation and
    `react-native-reanimated` drives the interactive pop animation —
    the stack depth decreases by exactly 1 after the gesture completes
- **Rule pull-to-refresh-reloads-data:** IF the user performs a
    pull-to-refresh gesture on a list screen THEN the app re-fetches
    the list data from the API via `@repo/contracts` oRPC calls and
    replaces the displayed list content with the fresh response — the
    count of stale items visible after the refresh completes equals 0
- **Rule content-never-behind-system-ui:** IF the screen renders on
    a device with a notch, status bar, dynamic island, or home
    indicator THEN `react-native-safe-area-context` provides inset
    values and the screen positions all interactive elements and text
    outside the inset boundaries — the count of pixels of interactive
    content overlapping system UI elements equals 0
- **Rule deep-link-redirects-unauthenticated-to-sign-in:** IF a
    `docodego://` deep link arrives and the user does not have a valid
    authentication session THEN the app redirects to the sign-in
    screen and stores the deep link target path in memory — after
    sign-in completes, the app navigates to the stored path and the
    final screen matches the deep link target route
- **Rule org-switch-without-leaving-app:** IF the user selects a
    different organization from the organization switcher THEN the app
    updates the org context and reloads the current tab section data
    without restarting the navigation flow — the count of app restarts
    triggered by an org switch equals 0 and the tab bar remains
    visible throughout the transition

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner (authenticated user with owner role in the active organization who has full access to all navigation sections and screens) | Taps all 4 tabs — dashboard, members, teams, settings — drills into any stack screen, uses swipe-back gesture, long-press contextual actions, pull-to-refresh, deep link navigation, and org switching | No navigation actions are denied to the owner — all tabs, stack screens, contextual actions, and organization switching controls are accessible without restriction | All 4 tab icons and labels are visible in the bottom tab bar, all list items display contextual action options on long-press, and the org switcher displays all organizations the owner belongs to |
| Admin (authenticated user with admin role in the active organization who has access to all sections except owner-exclusive management screens) | Taps all 4 tabs — dashboard, members, teams, settings — drills into stack screens, uses gestures, pull-to-refresh, deep link navigation, and org switching with the same navigation capabilities as the owner role | Cannot access owner-exclusive management screens within the settings stack — the route guard redirects the admin away from those screens and renders an unauthorized message | All 4 tab icons and labels are visible in the bottom tab bar, but owner-exclusive settings screens are hidden from the settings stack navigation list |
| Member (authenticated user with member role in the active organization who has access to dashboard, members, teams, and personal settings) | Taps dashboard, members, and teams tabs, accesses personal settings within the settings tab, uses gestures, pull-to-refresh, deep link navigation to permitted screens, and org switching | Cannot access organization-level settings screens — the route guard blocks navigation to org settings and the app renders an unauthorized message if the user attempts direct access via deep link | All 4 tab icons are visible but the org settings section within the settings tab is hidden from the member's view, showing only personal settings options |
| Unauthenticated (user with no valid session who is redirected to the sign-in screen before any tab navigation renders) | No tab navigation actions are permitted — the auth guard redirects to the sign-in screen before the tab bar mounts and the user can only interact with the sign-in and authentication screens | Cannot view or interact with any tab, stack screen, list, or navigation control — the entire tab-based navigation structure is inaccessible until the user completes authentication | No tab bar is visible, no navigation screens render, and the user sees only the sign-in screen until a valid session is established through the authentication flow |

## Constraints

- Screen transition animations driven by `react-native-reanimated`
    run on the UI thread and maintain 60 frames per second or higher
    during push and pop transitions — the count of frames dropped
    below the 60fps threshold during a screen transition equals 0
    under normal operating conditions.
- The swipe-back gesture recognized by `react-native-gesture-handler`
    activates when the touch starts within 20 pixels of the left
    screen edge — touches starting beyond 20 pixels from the edge do
    not trigger the back navigation gesture, and the gesture
    recognition latency from touch start to animation start is 100 ms
    or fewer.
- `react-native-safe-area-context` inset values are applied to every
    screen layout so that the count of interactive elements or text
    characters obscured by the device notch, status bar, dynamic
    island, or home indicator equals 0 across all supported device
    models.
- Pull-to-refresh data re-fetch via `@repo/contracts` oRPC calls
    completes within 3000 ms on a standard mobile network connection
    — the loading indicator remains visible for the duration of the
    fetch and disappears within 100 ms of the response arriving.
- Deep link resolution from URL receipt to the target screen render
    completes within 500 ms when the user has a valid session — the
    elapsed time from the deep link tap to the target screen becoming
    interactive is 500 ms or fewer.
- Tab switching preserves the full stack navigation state for each
    section — the count of stack screens lost when the user switches
    away from a tab and returns equals 0, and the restored screen
    renders with the identical scroll position and form state that was
    present when the user left.
- The bottom tab bar renders exactly 4 tabs with localized labels
    from `@repo/i18n` — the count of visible tabs equals 4 for
    authenticated users and the count of raw translation keys
    displayed instead of localized labels equals 0 when the i18n
    namespace has loaded.

## Acceptance Criteria

- [ ] The bottom tab bar renders exactly 4 tabs — dashboard, members, teams, settings — and the count of visible tab icons equals 4 for authenticated users
- [ ] Tapping a tab navigates to the corresponding top-level route and the active tab indicator highlights the selected tab — the count of highlighted tabs equals 1 at any given time
- [ ] Tab switching preserves stack navigation state — after drilling 3 screens deep in one tab, switching to another tab, and returning, the stack depth equals 3 and the screen content matches the last viewed state
- [ ] Drilling into a detail screen triggers a slide-from-right push animation driven by `react-native-reanimated` on the UI thread — the animation frame rate is 60fps or higher and the count of dropped frames equals 0
- [ ] Swiping from the left edge within 20 pixels triggers an interactive pop animation — the stack depth decreases by exactly 1 after the gesture completes and the animation runs at 60fps or higher
- [ ] Long-pressing an item on a list screen for 500 ms displays a contextual action menu — the count of contextual menu items displayed is 1 or more and the menu appears within 100 ms of the 500 ms hold threshold
- [ ] Pull-to-refresh on a list screen re-fetches data via `@repo/contracts` oRPC calls and the fresh data replaces stale content within 3000 ms — the count of stale items after refresh completes equals 0
- [ ] Safe area insets from `react-native-safe-area-context` prevent content from being obscured — the count of interactive elements overlapping the device notch, status bar, dynamic island, or home indicator equals 0
- [ ] Deep link navigation via `docodego://` resolves to the correct screen within 500 ms when the user has a valid session — the rendered screen path matches the deep link target path
- [ ] An unauthenticated deep link redirects to sign-in, stores the target path, and navigates to the stored path after authentication — the final screen path equals the original deep link target path
- [ ] Organization switching updates the active org context and reloads the current tab data without restarting the navigation flow — the count of app restarts triggered by org switch equals 0
- [ ] RTL layout activates when `expo-localization` detects an Arabic or Hebrew device locale — the tab bar order, navigation headers, and screen content mirror to right-to-left direction and the count of LTR-rendered elements in an RTL locale equals 0
- [ ] Infinite scroll on paginated list screens fetches the next page when the user scrolls within 200 pixels of the list bottom — the new items append to the existing list and the count of list resets during pagination equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user taps the currently active tab while drilled 3 screens deep in that tab's stack navigator | The stack pops to the root screen of the active tab, resetting the stack depth to 1, and the root screen re-renders with its default state while the tab bar remains highlighted on the same tab | The stack depth equals 1 after the tap, the root screen of the tab is visible, and the count of tab switches triggered equals 0 |
| The user performs a swipe-back gesture on the root screen of a tab where no previous screen exists in the stack | The gesture is ignored because the stack contains only 1 screen and there is no screen to pop back to — the root screen remains visible and no navigation transition occurs | The stack depth remains 1, the root screen stays visible, and the count of navigation pop events triggered equals 0 |
| The user receives a deep link for a screen that requires a higher permission level than their current role provides | Expo Router navigates to the screen route but the route guard intercepts and renders a localized unauthorized message instead of the screen content — the user remains in the app without crashing | The unauthorized message screen renders with a non-empty localized string and the count of app crashes equals 0 |
| The user switches organizations while a pull-to-refresh API call is still in-flight for the previous organization context | The in-flight API request is cancelled or its response is discarded when the org context changes — the app re-fetches data for the new organization and the count of data items displayed from the previous org equals 0 | The displayed list contains only items belonging to the newly selected organization and the count of items from the previous org equals 0 |
| The device rotates from portrait to landscape while a screen transition animation is in progress between two stack screens | The animation completes without interruption and the destination screen re-renders with the landscape layout dimensions — `react-native-safe-area-context` provides updated inset values for the new orientation | The destination screen renders with landscape-correct dimensions and the count of animation interruptions during the rotation equals 0 |
| The app launches for the first time with no cached navigation state and the user has memberships in 3 organizations | The app loads the default organization (first in the membership list), renders the dashboard tab as the initial active tab, and the org switcher displays all 3 organizations as available options | The active tab is dashboard, the count of available organizations in the org switcher equals 3, and the displayed data belongs to the default organization |

## Failure Modes

- **Expo Router fails to resolve a route from the file-based
    directory structure during app initialization or navigation**

    **What happens:** Expo Router encounters a missing or malformed
    route file in the app directory and cannot generate the typed route
    for a screen that the user attempts to navigate to via tab tap,
    stack push, or deep link resolution.

    **Source:** A route file was deleted, renamed, or contains a syntax
    error that prevents Expo Router from parsing the file into a valid
    route definition during the build step or at runtime.

    **Consequence:** The user taps a tab or drills into a screen and
    sees an error boundary instead of the expected content — the
    navigation flow is interrupted and the user cannot reach the
    target screen through the normal tab or stack navigation path.

    **Recovery:** Expo Router falls back to rendering a localized error
    boundary screen within the affected navigation context and logs
    the route resolution failure — the user navigates to a different
    tab or taps the back button to return to a working screen.

- **`react-native-safe-area-context` fails to provide inset values
    on a device with non-standard system UI geometry**

    **What happens:** The safe area context provider returns zero
    values for all insets on a device that has a notch, dynamic island,
    or non-standard status bar height, causing the screen layout to
    position content behind system UI elements.

    **Source:** The device runs a custom Android ROM or a device model
    not in the safe area library's known device list, resulting in the
    inset query returning default zero values instead of the actual
    system UI measurements.

    **Consequence:** Text, buttons, and interactive elements render
    behind the device notch or status bar, making portions of the
    screen content unreadable or untappable until the user scrolls the
    content into a visible area of the screen.

    **Recovery:** The app falls back to applying a minimum top padding
    of 44 pixels and a minimum bottom padding of 34 pixels as
    hardcoded safe defaults when the safe area insets return 0 on a
    device that reports a notch or cutout — the logs record the
    device model and OS version for the zero-inset condition.

- **Deep link resolution fails because the stored target path is
    lost during the sign-in redirect flow**

    **What happens:** The user taps a `docodego://` deep link without
    an active session, the app stores the target path and redirects to
    sign-in, but the stored path is cleared from memory during the
    sign-in process due to a state reset or app background eviction.

    **Source:** The mobile operating system evicts the app from memory
    while the user is completing sign-in in an external browser or
    webview, or the sign-in flow triggers a full app state reset that
    clears the in-memory stored deep link target path.

    **Consequence:** The user completes sign-in but the app navigates
    to the default dashboard tab instead of the intended deep link
    target screen — the user must manually navigate to the screen they
    originally intended to reach via the deep link.

    **Recovery:** The app falls back to navigating to the default
    dashboard tab after sign-in when no stored deep link path exists
    and logs the missing target path condition — the user retries the
    deep link by tapping the original link source again now that the
    session is active.

- **`@repo/i18n` translation namespace fails to load and screen
    labels display raw translation keys**

    **What happens:** The i18n infrastructure fails to load the mobile
    app translation namespace during initialization, causing all tab
    labels, screen headers, and button text to display raw translation
    keys like `mobile.tabs.dashboard` instead of localized strings.

    **Source:** A network request to fetch the translation JSON file
    for the detected device locale timed out, or the translation file
    for a newly added locale was not included in the app bundle and
    cannot be loaded from the remote translation endpoint.

    **Consequence:** The user sees untranslated key identifiers
    throughout the app navigation — tab labels, screen titles,
    contextual action menu items, and error messages are displayed as
    dot-separated key strings that are unintelligible to the user.

    **Recovery:** The i18n infrastructure degrades to displaying raw
    translation keys as fallback text and logs the namespace loading
    failure with the locale identifier — the app retries loading the
    namespace on the next screen navigation event and the user can
    force a retry by closing and reopening the app.

## Declared Omissions

- This specification does not define the content, data-fetching
    logic, or layout of individual screens such as the dashboard
    overview, member list, team detail, or settings forms — those
    are defined in their own dedicated behavioral specifications.
- This specification does not cover the sign-in flow, session token
    management, or authentication provider configuration — the auth
    redirect on deep link is referenced but the full authentication
    behavior is defined in the sign-in and session-lifecycle
    specifications.
- This specification does not address push notification delivery,
    payload handling, or notification permission prompts — the deep
    link from a notification is referenced but the notification
    infrastructure is defined in a separate notification specification.
- This specification does not define the organization switcher's
    internal dropdown design, org creation, or the full org-switching
    data flow — the navigation-level org switch is referenced but
    the detailed switching behavior is in the user-switches-organization
    specification.
- This specification does not cover offline data caching, background
    sync, or network connectivity monitoring — the pull-to-refresh and
    infinite scroll behaviors assume an active network connection and
    offline resilience is defined in a separate data synchronization
    specification.

## Related Specifications

- [session-lifecycle](session-lifecycle.md) — defines the session management and authentication state that determines whether the mobile app renders the tab navigation or redirects the user to the sign-in screen on launch and deep link arrival
- [user-switches-organization](user-switches-organization.md) — defines the full organization switching flow including data reloading and context updates that the mobile app's org switcher navigation control triggers
- [user-navigates-the-dashboard](user-navigates-the-dashboard.md) — defines the web dashboard navigation structure that the mobile app mirrors with tab and stack navigation using the same route hierarchy and org context model
- [user-opens-a-deep-link](user-opens-a-deep-link.md) — defines the desktop deep link handling via the Tauri Deep-Link plugin that complements the mobile deep link handling via Expo Router covered in this specification
- [user-changes-language](user-changes-language.md) — defines the language change flow and locale detection that determines which `@repo/i18n` translation namespace is loaded and whether RTL layout is activated in the mobile app

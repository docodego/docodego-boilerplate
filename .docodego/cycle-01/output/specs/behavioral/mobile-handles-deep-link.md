---
id: SPEC-2026-076
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# Mobile Handles Deep Link

## Intent

This spec defines how the Expo 54 mobile application handles deep
links using the custom `docodego://` URL scheme registered with the
operating system. When the user taps a `docodego://` link anywhere on
their device — in a push notification, an email, a chat message, or
another app — the operating system recognizes the custom URL scheme
and hands the URL to the DoCodeGo mobile application. If the app is
not already running, the OS launches it with the deep link URL as the
initial route. Expo Router v6 intercepts the incoming URL, extracts
the path portion, and matches it against the file-based route
definitions. When the user is authenticated with a valid session token
stored in `expo-secure-store`, the app navigates directly to the
target screen. When the user is not authenticated or the session token
has expired, the app preserves the deep link target path in memory,
redirects to the localized sign-in screen, and after the user
completes authentication the app retrieves the preserved path and
navigates there automatically. If the deep link points to a resource
within a different organization than the user's current active org,
the app switches the active organization context before rendering the
target screen. The behavior is identical from the user's perspective
regardless of whether the app was already running (warm start) or
launched from a terminated state (cold start).

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `docodego://` URL scheme OS registration (operating system association between the custom protocol and the Expo application binary registered during app install) | read | When the user taps a `docodego://` link anywhere on the device and the OS resolves the scheme to the DoCodeGo mobile application | The operating system does not associate the `docodego://` scheme with any application and tapping the link opens a browser or displays an OS-level "no handler" error — the user falls back to opening the app manually and navigating to the target screen |
| Expo Router v6 (file-based router that extracts the path from the incoming URL and matches it against typed route definitions) | read/write | When the OS hands the deep link URL to the app and the router extracts the path portion to resolve it against file-based route definitions | The router cannot parse the incoming URL or has no matching route definition for the extracted path and falls back to rendering the default screen instead of showing an error page to the user |
| `expo-secure-store` (encrypted key-value store that persists the session token on the device for authentication state checks) | read | When the app receives a deep link URL and checks whether a valid session token exists before deciding to navigate directly or redirect to sign-in | The `expo-secure-store` module is inaccessible due to a device-level keychain lockout or data corruption and the app treats the user as unauthenticated — the app falls back to redirecting the user to the sign-in screen with the deep link target preserved in memory |
| Organization context switcher (module that changes the active organization when the deep link targets a resource in a different org than the currently selected one) | read/write | When the authenticated user navigates via deep link to a resource belonging to an organization different from the currently active organization context | The org context switch fails because the user is not a member of the target organization and the app returns error code 403 — the user sees a "not a member" message and falls back to viewing the currently active organization |
| Sign-in screen with preserved target path (localized authentication screen that stores the deep link target in memory before the user authenticates via email OTP or SSO) | read/write | When the app detects the user is unauthenticated or the session token has expired and redirects to sign-in while preserving the original deep link target path | The sign-in screen fails to preserve the deep link target path due to a memory allocation error and the path is lost — after authentication the user falls back to landing on the default home screen instead of the intended deep link destination |

## Behavioral Flow

1. **[User]** taps a `docodego://` link on their device — in a push
    notification, an email, a chat message, or another app — to open
    a specific screen within the DoCodeGo mobile application

2. **[OS]** recognizes the `docodego://` custom URL scheme registered
    by the Expo app during installation, resolves the handler, and
    hands the full URL to the DoCodeGo mobile application process —
    if the app is not already running, the OS launches it with the
    deep link URL as the initial route argument

3. **[App]** receives the deep link URL from the operating system
    and Expo Router v6 intercepts the incoming URL to extract the
    path portion — for example, `docodego://app/acme-corp/members`
    resolves to the `/app/acme-corp/members` route path

4. **[App]** matches the extracted path against its file-based typed
    route definitions — if the path matches a valid route, navigation
    proceeds to step 5; if the path does not match any known route,
    the app falls back to rendering the default screen and the flow
    ends without showing an error page to the user

5. **[App]** reads the session token from `expo-secure-store` to
    determine the user's authentication state — if a valid
    non-expired session token exists, the user is authenticated and
    the flow continues to step 6; if no token exists or the token
    has expired, the flow jumps to step 8

6. **[App]** checks whether the deep link target resource belongs to
    a different organization than the user's currently active org —
    if the target org differs, the app switches the active
    organization context to the target org before rendering; if the
    target org is the same as the active org, no context switch
    occurs

7. **[User]** sees the target screen rendered with all expected data
    loaded for the correct organization context — the deep link
    navigation is complete and the user interacts with the screen
    normally without needing any additional navigation steps

8. **[App]** detects the user is unauthenticated or the session
    token has expired and preserves the deep link target path in
    memory so it is not lost during the authentication flow — the
    app then redirects the user to the localized sign-in screen

9. **[User]** signs in through one of the available mobile
    authentication methods — email OTP or SSO — completing the
    authentication flow and establishing a new session token stored
    in `expo-secure-store`

10. **[App]** retrieves the preserved deep link target path from
    memory after the user completes authentication and navigates
    automatically to the originally intended screen — the user
    arrives at the deep link destination without needing to tap the
    link again or perform any manual navigation

11. **[App]** during a cold start (app launched from terminated
    state), receives the deep link URL as the initial URL passed
    during app initialization — Expo Router reads this URL during
    startup and uses it as the initial route, so the user lands on
    the target screen after the app finishes loading (provided the
    authentication check in step 5 passes)

12. **[App]** during a warm start (app already running in foreground
    or background), receives the deep link URL from the OS and the
    existing Expo Router instance handles navigation immediately
    within the current navigation stack — the user sees the target
    screen load without any app restart or re-initialization delay

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | url_received | The user taps a `docodego://` link on their device and the OS delivers the URL to the DoCodeGo mobile application process | The incoming URL uses the `docodego://` custom scheme and the OS has a registered handler for the scheme |
| url_received | path_extracting | Expo Router v6 intercepts the incoming deep link URL and begins extracting the path portion from the full URL string | The URL is well-formed and contains a non-empty path after the `docodego://` scheme prefix |
| path_extracting | route_matching | Expo Router extracts the path (for example `/app/acme-corp/members`) and attempts to match it against the file-based typed route definitions | The extracted path is a non-empty string that can be compared against the route definition table |
| route_matching | auth_checking | Expo Router finds a matching route definition for the extracted path and proceeds to verify the user's authentication state | The path matches exactly one route definition in the file-based routing table |
| route_matching | fallback_screen | Expo Router cannot find any matching route definition for the extracted path from the deep link URL | No route definition in the routing table matches the extracted path |
| fallback_screen | idle | The app renders the default screen because the deep link path had no matching route and returns to waiting for the next event | The default screen component rendered and the app is ready to accept new deep link URLs |
| auth_checking | org_checking | The app reads the session token from `expo-secure-store` and confirms it is valid and not expired, establishing the user as authenticated | The session token exists in `expo-secure-store` and the token expiration timestamp is in the future |
| auth_checking | path_preserving | The app reads `expo-secure-store` and finds no session token or the token has expired past its validity window | No session token exists in `expo-secure-store` or the token expiration timestamp is in the past |
| org_checking | navigating | The app checks the target org against the active org and either switches context or confirms they match, then proceeds to navigation | The user is a member of the target organization or the target org matches the currently active org |
| org_checking | org_denied | The app attempts to switch to the target organization but the user is not a member of that organization | The user's membership list does not include the target organization identifier |
| org_denied | idle | The app displays a "not a member" error message and returns to the idle state without navigating to the target screen | The error message rendered and the user remains on their current screen |
| navigating | idle | Expo Router navigates to the target screen, the screen renders with all expected data, and the app returns to waiting for the next event | The target screen component rendered and all required data loaded |
| path_preserving | signing_in | The app preserves the deep link target path in memory and redirects the user to the localized sign-in screen for authentication | The deep link path is stored in memory and the sign-in screen is ready to render |
| signing_in | post_auth_navigating | The user completes authentication via email OTP or SSO and the app establishes a new session token in `expo-secure-store` | The authentication flow completed and a valid session token is now stored in `expo-secure-store` |
| post_auth_navigating | idle | The app retrieves the preserved deep link path from memory and navigates to the target screen after successful authentication | The preserved path exists in memory and the target screen rendered with the authenticated user's data |

## Business Rules

- **Rule valid-path-navigates:** IF Expo Router v6 extracts a path
    from the deep link URL and the path matches a route definition in
    the file-based routing table THEN the app proceeds with navigation
    to the matched route — the count of matched routes for the
    extracted path equals exactly 1
- **Rule invalid-path-falls-back:** IF Expo Router v6 extracts a
    path from the deep link URL and no route definition matches the
    extracted path THEN the app renders the default screen instead of
    displaying an error page — the count of error pages shown to the
    user equals 0
- **Rule authenticated-navigates-directly:** IF the app reads the
    session token from `expo-secure-store` and the token is valid and
    not expired THEN the app navigates directly to the target screen
    without showing the sign-in screen — the count of sign-in screen
    renders equals 0
- **Rule unauthenticated-preserves-path-redirects-to-sign-in:** IF
    the app reads `expo-secure-store` and finds no session token or
    the token has expired THEN the app preserves the deep link target
    path in memory and redirects to the localized sign-in screen —
    the count of preserved paths in memory equals 1
- **Rule post-auth-resumes-deep-link:** IF the user completes
    authentication and a preserved deep link target path exists in
    memory THEN the app retrieves the path and navigates to the
    target screen automatically — the count of manual navigation
    steps required from the user after sign-in equals 0
- **Rule org-context-switched-if-needed:** IF the deep link target
    resource belongs to an organization different from the user's
    currently active org and the user is a member of the target org
    THEN the app switches the active organization context before
    rendering the target screen — the active org identifier after
    navigation matches the target org identifier from the deep link
- **Rule cold-start-uses-url-as-initial-route:** IF the app is
    launched from a terminated state with a deep link URL as the
    startup argument THEN Expo Router reads the URL during
    initialization and uses it as the initial route — the initial
    route path equals the extracted path from the deep link URL

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated User (has a valid non-expired session token in `expo-secure-store` when the deep link arrives) | Tap deep links to navigate directly to target screens, trigger org context switch when deep link targets a different organization, navigate to any screen the user has role-based access to via the deep link path | Cannot access screens that require a higher permission level than the user's current role — such as admin-only screens that return a 403 forbidden response from the route guard | The user sees the target screen content rendered with data scoped to the active organization context, subject to the same role-based visibility constraints as manual in-app navigation |
| Unauthenticated User (no valid session token exists in `expo-secure-store` when the deep link arrives or the token has expired) | Tap deep links to trigger the app, have the deep link target path preserved in memory during sign-in redirect, complete authentication via email OTP or SSO to navigate to the preserved target after sign-in | Cannot view or interact with any authenticated screen content via deep link — the app redirects to the sign-in screen before any target screen data loads or renders | The user sees only the localized sign-in screen when tapping a deep link to an authenticated route, and after authentication sees the target screen with data for their authenticated identity |

## Constraints

- The path extraction from a deep link URL and route matching by
    Expo Router v6 completes within 300 ms of the app receiving the
    URL from the operating system — the elapsed time from URL receipt
    to route match result is 300 ms or fewer.
- The session token read from `expo-secure-store` completes within
    100 ms of the app requesting the token for authentication state
    verification — the elapsed time from read request to token
    availability is 100 ms or fewer.
- The organization context switch when a deep link targets a
    different org completes within 500 ms of the switch being
    triggered — the elapsed time from switch initiation to active
    org update is 500 ms or fewer.
- The preserved deep link target path remains in memory for the
    entire duration of the authentication flow, up to a maximum of
    600 seconds — if authentication is not completed within 600
    seconds the preserved path is discarded.
- The app handles cold start deep links during initialization with
    a total startup-to-target-screen time of 3000 ms or fewer — the
    elapsed time from app launch to target screen render equals
    3000 ms or fewer.
- All deep link URLs use the `docodego://` scheme exclusively — the
    count of alternative custom URL schemes registered by the
    application equals 0 and no other scheme is accepted.

## Acceptance Criteria

- [ ] Tapping `docodego://app/acme-corp/members` in an external app navigates the mobile app to the members screen — the Expo Router current path equals `/app/acme-corp/members` and the count of error screens shown equals 0
- [ ] The path extraction and route matching completes within 300 ms of the app receiving the deep link URL — the elapsed time from URL receipt to route match result is 300 ms or fewer
- [ ] When the deep link path does not match any route definition, the app renders the default screen — the count of default screen renders equals 1 and the count of error page renders equals 0
- [ ] When a valid session token exists in `expo-secure-store`, the app navigates directly to the target screen — the count of sign-in screen renders equals 0 and the target screen data loads within 2000 ms
- [ ] When no session token exists or the token has expired, the app preserves the deep link path and redirects to sign-in — the count of preserved paths in memory equals 1 and the sign-in screen renders within 500 ms
- [ ] After the user completes authentication, the app navigates to the preserved deep link target — the count of manual navigation steps required from the user equals 0 and the target screen renders within 2000 ms of auth completion
- [ ] When the deep link targets a resource in a different org than the active org, the app switches org context — the active org identifier after navigation equals the target org extracted from the deep link URL path and the count of org switch failures equals 0
- [ ] The org context switch completes within 500 ms of being triggered — the elapsed time from switch initiation to active org update is 500 ms or fewer
- [ ] During cold start with a deep link URL, Expo Router uses the URL as the initial route — the initial route path equals the extracted deep link path and total startup-to-screen time is 3000 ms or fewer
- [ ] During warm start, the existing Expo Router instance handles the deep link navigation within the current stack — the count of app re-initializations equals 0 and the target screen renders within 1000 ms
- [ ] The session token read from `expo-secure-store` completes within 100 ms — the elapsed time from read request to token availability is 100 ms or fewer
- [ ] The preserved deep link path is discarded after 600 seconds if authentication is not completed — the count of stale preserved paths in memory after 600 seconds equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user taps a deep link while the app is completely terminated and the OS launches the app with the URL as a cold start argument | The app initializes, Expo Router reads the deep link URL as the initial URL, checks authentication via `expo-secure-store`, and navigates to the target screen or redirects to sign-in with the path preserved in memory | The target screen renders after initialization with the correct route path, or the sign-in screen renders with the preserved path count equal to 1 |
| The user taps two deep links in rapid succession within 500 ms before the first navigation completes inside the app | The second deep link URL overwrites the first navigation and Expo Router navigates to the path from the second URL — the first navigation is abandoned and only the second route renders on screen | The Expo Router current path matches the second deep link path and the first target screen component did not fully render |
| The deep link URL contains query parameters like `docodego://app/search?q=test&page=2` that need to be preserved during navigation | The app extracts the full path and query string from the URL and forwards both to Expo Router — the router receives the query parameters and the target screen renders with the expected search state | The Expo Router search params include `q=test` and `page=2` after deep link navigation and the search results screen displays results for "test" |
| The deep link targets an org where the user is not a member, triggering an access denial during org context switch | The app attempts to switch the active org but the membership check fails and the app displays a "not a member" error message — the user remains on the current screen with the previous active org unchanged | The active org identifier remains unchanged and the count of "not a member" error messages displayed equals 1 |
| The user taps a deep link, gets redirected to sign-in, but waits longer than 600 seconds before completing authentication | The preserved deep link path is discarded after 600 seconds and after the user signs in the app navigates to the default home screen instead of the expired deep link target | The count of preserved paths in memory equals 0 after 600 seconds and the post-auth landing screen is the default home screen |
| The deep link URL contains URL-encoded characters like `docodego://app/teams/my%20team` that require decoding during path extraction | Expo Router preserves the URL-encoded path and handles decoding — the target screen renders with the decoded team name "my team" displayed correctly in the user interface | The route matches with the decoded path segment and the team screen renders with the team name "my team" visible |

## Failure Modes

- **Expo Router v6 fails to match the deep link path against any
    route definition in the file-based routing table**
    - **What happens:** The app receives a deep link URL and Expo
        Router extracts the path portion, but the routing table has
        no matching route because the link was generated by an older
        app version or contains a typo in the path segment.
    - **Source:** The deep link was shared from a different app
        version that included routes not present in the current
        build, or the link was manually constructed with an incorrect
        path that does not correspond to any file-based route.
    - **Consequence:** The user does not see the intended content
        and instead sees the default screen, which does not indicate
        what specific screen they were trying to reach via the deep
        link URL.
    - **Recovery:** The app logs the unmatched path for diagnostics
        and falls back to rendering the default screen — the user
        navigates manually through the app navigation to find the
        content they intended to access via the deep link.

- **The session token read from `expo-secure-store` fails due to
    device-level encryption or storage unavailability on the device**
    - **What happens:** The app attempts to read the session token
        from `expo-secure-store` to verify authentication state, but
        `expo-secure-store` returns an error because the device
        keychain is locked or the storage was cleared by the OS.
    - **Source:** The device-level encrypted storage became
        unavailable because the user changed their device passcode
        or the OS cleared the keychain during a system update or
        storage reclamation event on the device.
    - **Consequence:** The app cannot determine whether the user is
        authenticated and treats the user as unauthenticated, which
        redirects to the sign-in screen even if the user was
        previously signed in and had a valid session.
    - **Recovery:** The app logs the `expo-secure-store` read
        failure with the error code, preserves the deep link path in
        memory, and falls back to redirecting the user to the
        sign-in screen where they can re-authenticate and proceed to
        the target.

- **Organization context switch fails because the user is not a
    member of the target organization referenced in the deep link**
    - **What happens:** The app receives a deep link pointing to a
        resource in a specific organization and attempts to switch
        the active org context, but the membership check returns
        that the user does not belong to the target organization.
    - **Source:** The deep link was shared by a member of a
        different organization and the tapping user was never invited
        to or removed from that organization, making the resource
        inaccessible to them under the current membership rules.
    - **Consequence:** The org context switch is denied and the user
        cannot view the linked content because the target
        organization's data is not accessible without membership —
        the user remains on their current active org screen.
    - **Recovery:** The app returns error code 403 with a localized
        "not a member" message and logs the denied org switch with
        the target org identifier — the user falls back to viewing
        their currently active organization content.

- **Preserved deep link path is lost during the authentication
    redirect because of an unexpected app crash or memory pressure**
    - **What happens:** The app preserves the deep link target path
        in memory before redirecting to the sign-in screen, but an
        unexpected app crash or OS memory pressure event clears the
        in-memory state before the user completes authentication.
    - **Source:** The operating system terminates the app process due
        to low-memory conditions while the user is on the sign-in
        screen, or an unhandled exception in the authentication flow
        causes a crash that resets the in-memory preserved path.
    - **Consequence:** After the user completes authentication, the
        preserved deep link path no longer exists in memory and the
        app cannot navigate to the originally intended screen — the
        user lands on the default home screen instead.
    - **Recovery:** The app logs the missing preserved path after
        authentication completion and falls back to navigating the
        user to the default home screen — the user retries by
        tapping the original deep link again from the notification
        or message where they found it.

## Declared Omissions

- This specification does not define the visual appearance or layout
    of the default fallback screen rendered when a deep link path
    has no matching route — that screen design is covered by the
    mobile app shell and navigation specification.
- This specification does not cover Android App Links or iOS
    Universal Links using HTTPS domain-based deep linking — only the
    custom `docodego://` URL scheme is addressed in this behavioral
    flow definition.
- This specification does not define the email OTP or SSO
    authentication flow details including token exchange, session
    creation, and identity provider configuration — those behaviors
    are defined in the user-signs-in-with-email-otp and
    user-signs-in-with-sso specifications respectively.
- This specification does not address analytics or telemetry
    collection for deep link usage metrics such as tap-through rates
    or most visited deep link targets — usage tracking is defined in
    a separate observability specification outside this scope.
- This specification does not cover push notification delivery
    mechanisms or how `docodego://` links are embedded within push
    notification payloads — notification composition is handled by
    the notification infrastructure specification.

## Related Specifications

- [user-opens-a-deep-link](user-opens-a-deep-link.md) — defines the
    Tauri desktop application deep link handling via the same
    `docodego://` URL scheme, covering the desktop-specific path
    forwarding to TanStack Router and `show_window()` IPC behavior
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) —
    defines the email OTP authentication flow that the mobile app
    uses as one of the sign-in methods during the unauthenticated
    deep link detour to establish a session token
- [user-signs-in-with-sso](user-signs-in-with-sso.md) — defines the
    SSO authentication flow that the mobile app uses as an
    alternative sign-in method during the unauthenticated deep link
    redirect to the localized sign-in screen
- [session-lifecycle](session-lifecycle.md) — defines the session
    token lifecycle including creation, storage in `expo-secure-store`,
    expiration checks, and refresh behavior that determines whether a
    deep link navigates directly or redirects to sign-in
- [user-switches-organization](user-switches-organization.md) —
    defines the organization context switching behavior that the deep
    link handler invokes when the target resource belongs to a
    different organization than the user's currently active org

---
id: SPEC-2026-068
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Opens a Deep Link

## Intent

This spec defines how the Tauri 2 desktop application handles deep
links via the custom `docodego://` URL scheme registered with the
operating system through the Tauri Deep-Link plugin. When the user
clicks a `docodego://` link anywhere in the OS — in an email client,
a chat application, a web browser, or any other program — the
operating system recognizes the custom scheme and hands the URL to the
Tauri application. The application extracts the path portion from the
URL and forwards it to TanStack Router inside the webview, which
navigates to the matching route as if the user had clicked a link
within the application itself. If the application window is minimized
or hidden when the deep link is activated, the `show_window()` IPC
command is called to bring the window to the foreground so the user
sees the result immediately. Deep links also serve a critical role in
the OAuth sign-in flow: when the user signs in via SSO, the external
identity provider redirects back to `docodego://auth/callback?...`
with the authentication tokens, and the Tauri application hands this
to the auth handler to complete the session without manual token
copying. Deep link handling only applies when the application runs
inside Tauri — the web application detects this by checking for the
presence of `window.__TAURI__`, and when this global is absent (in a
regular browser), deep link registration is skipped entirely.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Tauri Deep-Link plugin (registers the `docodego://` custom URL scheme with the operating system during application startup) | read/write | When the Tauri application initializes during startup and registers the `docodego://` scheme with the OS, and when an incoming deep link URL is received and forwarded to the webview | The custom URL scheme is not registered with the OS and clicking `docodego://` links anywhere in the operating system has no effect — the OS displays a "no application associated" error and the user falls back to manually navigating within the application |
| `docodego://` URL scheme OS registration (operating system association between the custom protocol and the Tauri application binary) | write | When the Tauri Deep-Link plugin calls the OS-specific API to register the `docodego://` protocol handler during application startup or at install time | The operating system does not associate the `docodego://` scheme with any application and all deep links using this scheme fail to resolve — the user falls back to opening the desktop application manually and navigating to the target route |
| TanStack Router (client-side router inside the webview that resolves URL paths to application routes and renders the corresponding page) | write | When the Tauri application extracts the path portion from the deep link URL and forwards it to TanStack Router for client-side navigation within the webview | The router rejects the path because no matching route definition exists and falls back to rendering the 404 not-found page — the user sees the not-found page and must navigate manually to the intended destination |
| `show_window()` IPC command (Tauri IPC call that brings the native window to the foreground and gives it operating system focus) | write | When a deep link is received while the application window is minimized or hidden, the `show_window()` IPC command is called to bring the window to the foreground before navigation | The IPC call fails and the window remains minimized or hidden — the navigation occurs in the background but the user does not see it until they manually restore the window from the taskbar or system tray |
| `window.__TAURI__` detection (global JavaScript object injected by Tauri into the webview context that indicates the application is running inside the Tauri desktop runtime) | read | When the web application initializes and checks for the presence of `window.__TAURI__` to determine whether to register deep link listeners and enable Tauri-specific IPC commands | The detection check returns `undefined` because the application is running in a regular browser, and all deep link registration and Tauri IPC listener setup is skipped entirely — the application operates as a standard web application without deep link capabilities |
| OAuth callback handler (authentication handler that processes the `docodego://auth/callback` deep link with tokens and parameters to complete the SSO sign-in flow) | read/write | When the Tauri application receives a deep link with the path `/auth/callback` containing OAuth tokens and parameters from the external identity provider redirect | The callback handler fails to process the tokens and the user remains unauthenticated — the application logs the callback processing error and falls back to displaying the sign-in page where the user can retry the SSO authentication flow |

## Behavioral Flow

1. **[Tauri]** registers the `docodego://` custom URL scheme with the
    operating system via the Tauri Deep-Link plugin during application
    startup — the OS associates the `docodego://` protocol with the
    Tauri application binary so that all URLs using this scheme are
    routed to the application

2. **[Webview]** checks for the presence of `window.__TAURI__` during
    web application initialization — if the global object exists, the
    application registers deep link event listeners to receive incoming
    URLs from the Tauri runtime; if the global object is absent, all
    deep link registration is skipped because the application is
    running in a regular browser

3. **[User]** clicks a deep link such as
    `docodego://app/docodego/members` anywhere in the operating system
    — in an email client, a chat application, a web browser, or any
    other program that renders clickable URLs

4. **[OS]** recognizes the `docodego://` scheme, resolves the
    registered application binary, and hands the full URL to the Tauri
    application process — if the application is already running, the
    URL is delivered to the existing process; if the application is not
    running, the OS launches it with the URL as a startup argument

5. **[Tauri]** receives the deep link URL from the operating system
    via the Deep-Link plugin, parses the URL to extract the path
    portion (for example `/app/docodego/members` from the full URL
    `docodego://app/docodego/members`), and forwards the extracted
    path to the webview

6. **[Tauri]** checks whether the application window is currently
    visible — if the window is minimized or hidden, calls the
    `show_window()` IPC command to bring the native window to the
    foreground and give it operating system focus so the user can see
    the navigation result immediately

7. **[Webview]** receives the extracted path from the Tauri runtime
    and passes it to TanStack Router, which performs client-side
    navigation to the matching route — the target page loads with all
    expected data and UI state as if the user had clicked an internal
    navigation link

8. **[User]** sees the target page rendered inside the application
    window, which is now in the foreground — the deep link navigation
    is complete and the user interacts with the page normally

9. **[User]** clicks an OAuth callback deep link
    `docodego://auth/callback?...` after completing SSO authentication
    at an external identity provider in the system browser — the
    browser redirects to this URL after the provider confirms the
    user's identity

10. **[OS]** recognizes the `docodego://` scheme and routes the
    callback URL to the Tauri application process, delivering the full
    URL including the query parameters containing authentication tokens
    and session data

11. **[Tauri]** receives the OAuth callback deep link, identifies the
    `/auth/callback` path, and hands the full URL with all query
    parameters to the OAuth callback handler instead of forwarding to
    TanStack Router for regular page navigation

12. **[Webview]** the OAuth callback handler processes the callback
    URL, extracts the authentication tokens and parameters, establishes
    the user session, and navigates to the authenticated landing page
    — the user is signed in without needing to manually copy tokens or
    switch between browser and desktop application windows

13. **[Webview]** when running in a regular browser where
    `window.__TAURI__` is absent, no deep link listeners are
    registered and no `docodego://` scheme handling occurs — the web
    application operates as a standard browser-based application
    without any deep link capabilities

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| app_not_running | scheme_registered | The Tauri application launches and the Deep-Link plugin registers the `docodego://` custom URL scheme with the operating system | The Tauri Deep-Link plugin is configured in the application and the OS accepts the scheme registration request |
| scheme_registered | awaiting_deep_link | The web application initializes inside the webview, detects `window.__TAURI__` is present, and registers deep link event listeners | The `window.__TAURI__` global object exists and the deep link event listener registration completes |
| awaiting_deep_link | path_extracting | The OS delivers a `docodego://` URL to the Tauri application process because the user clicked a deep link anywhere in the operating system | The incoming URL uses the `docodego://` scheme and the Tauri Deep-Link plugin receives the URL event |
| path_extracting | window_showing | The Tauri runtime extracts the path portion from the deep link URL and determines the application window is minimized or hidden | The extracted path is a non-empty string and the window `is_visible` property returns false |
| path_extracting | router_navigating | The Tauri runtime extracts the path from the deep link URL and determines the application window is already visible in the foreground | The extracted path is a non-empty string, the path does not match `/auth/callback`, and the window `is_visible` property returns true |
| window_showing | router_navigating | The `show_window()` IPC command completes and the native window is now visible in the foreground with operating system focus | The window `is_visible` property returns true after the IPC call completes and the path does not start with `/auth/callback` |
| router_navigating | awaiting_deep_link | TanStack Router resolves the extracted path to a matching route definition and renders the target page inside the webview | The router found a matching route and the page component rendered without a navigation error |
| router_navigating | route_not_found | TanStack Router cannot find a matching route definition for the extracted path from the deep link URL | The router has no route definition matching the extracted path and renders the 404 not-found page |
| route_not_found | awaiting_deep_link | The 404 not-found page is rendered and the application returns to waiting for the next deep link event | The not-found page component rendered and the user can continue navigating or wait for another deep link |
| path_extracting | oauth_processing | The Tauri runtime extracts the path from the deep link URL and identifies it as `/auth/callback` containing OAuth tokens | The extracted path starts with `/auth/callback` and the URL contains query parameters with authentication tokens |
| window_showing | oauth_processing | The `show_window()` IPC command completes and the extracted path starts with `/auth/callback` containing OAuth tokens | The window is now visible and the extracted path starts with `/auth/callback` |
| oauth_processing | awaiting_deep_link | The OAuth callback handler processes the authentication tokens, establishes the session, and navigates to the authenticated landing page | The session is created and the navigation to the authenticated page completes |
| oauth_processing | oauth_error | The OAuth callback handler fails to process the tokens because they are invalid, expired, or the callback URL is malformed | The token validation fails or the callback URL is missing required parameters |
| oauth_error | awaiting_deep_link | The application displays the sign-in page after the OAuth callback failure and returns to waiting for the next deep link | The sign-in page rendered and the error was logged for diagnostics |

## Business Rules

- **Rule custom-scheme-registered-on-launch:** IF the Tauri desktop
    application starts and the Deep-Link plugin is configured THEN the
    `docodego://` custom URL scheme is registered with the operating
    system before the web application finishes initializing inside the
    webview — the count of registered URL scheme handlers for
    `docodego://` equals 1 after startup completes
- **Rule path-forwarded-to-router:** IF the Tauri application receives
    a deep link URL with a path that does not start with
    `/auth/callback` THEN the path portion is extracted and forwarded
    to TanStack Router for client-side navigation — the navigated
    route path inside the webview matches the extracted path from the
    deep link URL
- **Rule window-shown-if-hidden:** IF a deep link is received while
    the application window is minimized or hidden THEN the
    `show_window()` IPC command is called to bring the window to the
    foreground before navigation occurs — the window `is_visible`
    property returns true after the IPC call and before the route
    renders
- **Rule oauth-callback-handled-as-deep-link:** IF the Tauri
    application receives a deep link URL with the path
    `/auth/callback` and query parameters containing OAuth tokens THEN
    the URL is handed to the OAuth callback handler instead of
    TanStack Router — the callback handler processes the tokens,
    establishes the session, and the count of manual token copy
    operations required from the user equals 0
- **Rule deep-link-skipped-in-browser:** IF the web application
    detects that `window.__TAURI__` is absent (indicating a regular
    browser environment) THEN no deep link event listeners are
    registered and no `docodego://` scheme handling code executes —
    the count of deep link event listeners registered in a browser
    context equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated User (has a valid session when the deep link arrives and TanStack Router navigates to the target route) | Click deep links anywhere in the OS to navigate inside the application, trigger `show_window()` to bring the window to the foreground, navigate to any authenticated route via deep link path forwarding to TanStack Router | Cannot access deep link routes that require a higher permission level than the user's current role, such as admin-only routes that return a 403 forbidden response from the route guard | The user sees the target page content rendered inside the webview after deep link navigation, subject to the same visibility constraints as if the user had navigated manually through the application UI |
| Unauthenticated User (no valid session exists when the deep link arrives and the route guard intercepts the navigation) | Click deep links anywhere in the OS to trigger the Tauri application, receive OAuth callback deep links at `docodego://auth/callback` to complete SSO sign-in, view the sign-in page after a route guard redirect | Cannot access authenticated routes via deep link — the TanStack Router route guard intercepts the navigation and redirects to the sign-in page before the target content renders | The user sees only the sign-in page when a deep link targets an authenticated route, and sees the OAuth callback processing result when the deep link is an authentication callback |
| OS (operating system that resolves the `docodego://` scheme to the registered Tauri application and delivers the URL) | Resolve the `docodego://` custom URL scheme to the registered application binary, deliver the full deep link URL to the Tauri process, launch the application if it is not already running when a deep link is clicked | Cannot modify the deep link URL content or query parameters during delivery, cannot intercept or filter the URL before handing it to the Tauri application process | The OS has no visibility into the deep link navigation result inside the webview or the OAuth callback processing — it only resolves the scheme and delivers the URL to the application |

## Constraints

- The Tauri Deep-Link plugin registers the `docodego://` custom URL
    scheme with the operating system during application startup — the
    count of registered scheme handlers for `docodego://` equals
    exactly 1 after the application finishes initialization.
- The path extraction from a deep link URL and forwarding to TanStack
    Router completes within 200 ms of the Tauri application receiving
    the URL from the operating system — the elapsed time from URL
    receipt to router navigation start is 200 ms or fewer.
- The `show_window()` IPC command brings the application window to the
    foreground within 100 ms of being called when the window is
    minimized or hidden — the elapsed time from IPC call to window
    visible equals 100 ms or fewer.
- The OAuth callback handler at `docodego://auth/callback` processes
    the authentication tokens and establishes the user session within
    3000 ms of receiving the callback deep link — the elapsed time
    from callback receipt to session creation equals 3000 ms or fewer.
- The `window.__TAURI__` detection check executes during web
    application initialization and the result determines whether deep
    link listeners are registered — the count of deep link event
    listeners registered when `window.__TAURI__` is absent equals 0.
- All deep link URLs use the `docodego://` scheme exclusively — the
    count of alternative custom URL schemes registered by the
    application equals 0 and no other scheme is accepted by the
    Deep-Link plugin.

## Acceptance Criteria

- [ ] The Tauri Deep-Link plugin registers the `docodego://` custom URL scheme with the operating system during application startup — the count of registered scheme handlers equals 1
- [ ] Clicking `docodego://app/docodego/members` in an external application navigates the webview — the TanStack Router current path equals `/app/docodego/members` and the count of 404 page renders equals 0
- [ ] The extracted path from the deep link URL is forwarded to TanStack Router within 200 ms of URL receipt — the elapsed time from receipt to navigation start is 200 ms or fewer
- [ ] When the application window is minimized and a deep link is clicked, `show_window()` brings the window to the foreground — the window `is_visible` property returns true after the IPC call
- [ ] The `show_window()` IPC command completes within 100 ms of being called — the elapsed time from IPC call to window visible is 100 ms or fewer
- [ ] Clicking `docodego://auth/callback?token=xyz` routes to the OAuth callback handler — the count of TanStack Router navigation events triggered equals 0 and the callback handler invocation count equals 1
- [ ] The OAuth callback handler processes tokens and establishes a session within 3000 ms — the elapsed time from callback receipt to session creation is 3000 ms or fewer
- [ ] After successful OAuth callback processing, the user is redirected away from the callback route — the TanStack Router current path starts with `/app` and the count of sign-in page renders equals 0
- [ ] When `window.__TAURI__` is absent in a regular browser, no deep link event listeners are registered — the count of registered deep link listeners equals 0
- [ ] When `window.__TAURI__` is present in the Tauri desktop app, deep link event listeners are registered — the count of registered deep link listeners equals 1 or more
- [ ] A deep link with an unrecognized path that matches no route definition renders the 404 not-found page — the count of not-found page renders equals 1 and the count of target page renders equals 0
- [ ] The application handles a deep link received while the app is already running by delivering the URL to the existing process — the count of new application instances spawned equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user clicks a deep link while the Tauri application is not running and the OS launches the application with the URL as a startup argument | The Tauri application starts, registers the `docodego://` scheme, processes the startup URL argument, extracts the path, and navigates to the target route after initialization completes | The TanStack Router current path matches the extracted path from the startup deep link URL after initialization |
| The user clicks two deep links in rapid succession within 500 ms before the first navigation completes inside the webview | The second deep link URL overwrites the first navigation and TanStack Router navigates to the path from the second URL — the first navigation is abandoned and only the second route renders | The TanStack Router current path matches the second deep link path and the first target page component did not fully render |
| The deep link URL contains query parameters like `docodego://app/search?q=test&page=2` that need to be preserved during navigation | The Tauri application extracts the full path and query string from the URL and forwards both to TanStack Router — the router receives the query parameters and the target page renders with the expected search state | The TanStack Router search params include `q=test` and `page=2` after deep link navigation |
| The deep link URL contains an encoded path with special characters like `docodego://app/teams/my%20team` that require URL decoding | The Tauri application preserves the URL-encoded path and forwards it to TanStack Router which handles the decoding — the target page renders with the decoded team name "my team" | The TanStack Router matches the route with the decoded path segment and renders the correct team page |
| Another application on the system has registered the same `docodego://` scheme, creating a conflict with the Tauri application registration | The OS resolves the conflict using platform-specific rules (last registered wins on Windows, first registered wins on macOS) and only one application receives the deep link — the losing application never receives the URL | The deep link is delivered to exactly one application and the count of applications receiving the URL equals 1 |
| The OAuth callback deep link arrives but the external identity provider included an error parameter like `docodego://auth/callback?error=access_denied` | The OAuth callback handler detects the error parameter, does not attempt to extract authentication tokens, and redirects the user to the sign-in page with a localized error message | The user sees the sign-in page with an error message and the count of session creation attempts equals 0 |

## Failure Modes

- **Deep-Link plugin fails to register the custom URL scheme with
    the operating system during application startup**
    - **What happens:** The Tauri Deep-Link plugin calls the
        OS-specific API to register the `docodego://` scheme but the
        registration call returns an error because the OS denies the
        registration or the scheme is already claimed by another
        application on the system.
    - **Source:** The operating system blocks the scheme registration
        because another application already registered the same
        `docodego://` protocol, or the application lacks the required
        OS permissions to register a custom URL scheme handler on the
        current user account.
    - **Consequence:** No deep links using the `docodego://` scheme
        are routed to the application and clicking deep links anywhere
        in the OS either opens the wrong application or displays an
        OS-level error indicating no handler is registered for the
        protocol.
    - **Recovery:** The Tauri application logs the scheme registration
        failure with the OS error code and the conflicting application
        identifier if available — the application continues running
        with all other functionality intact and the user falls back to
        navigating manually within the application instead of using
        deep links.

- **`show_window()` IPC command fails when the deep link arrives
    while the application window is minimized or hidden**
    - **What happens:** The Tauri runtime receives a deep link URL
        and calls `show_window()` to bring the window to the
        foreground, but the IPC command fails because the window handle
        is invalid or the OS window manager denies the focus request
        due to platform-specific focus stealing prevention policies.
    - **Source:** The native window handle became invalid due to an
        internal state inconsistency after the window was minimized for
        an extended period, or the OS focus stealing prevention policy
        blocks the application from bringing its window to the
        foreground without user interaction.
    - **Consequence:** The deep link navigation occurs inside the
        webview but the user does not see it because the window remains
        minimized or hidden — the navigation result is invisible until
        the user manually restores the window from the taskbar or
        system tray.
    - **Recovery:** The Tauri runtime logs the IPC failure with the
        window handle identifier and the OS error details — the
        navigation to the target route proceeds regardless and the user
        falls back to manually restoring the window from the taskbar
        or clicking the system tray icon to see the navigation result.

- **TanStack Router fails to match the extracted path from the deep
    link URL to any defined route**
    - **What happens:** The Tauri application extracts the path from
        the deep link URL and forwards it to TanStack Router, but the
        router has no route definition matching the extracted path
        because the link contains an outdated or invalid route that
        was removed in a newer application version.
    - **Source:** The deep link was generated by an older version of
        the application or shared by a user running a different
        version, and the target route no longer exists in the current
        application build deployed in the webview.
    - **Consequence:** The user sees the 404 not-found page instead
        of the expected content, and the deep link navigation does not
        achieve its intended purpose of taking the user directly to a
        specific page within the application.
    - **Recovery:** TanStack Router renders the 404 not-found page
        and logs the unmatched path for diagnostics — the user falls
        back to navigating manually through the application sidebar
        or navigation menu to find the content they intended to access
        via the deep link.

- **OAuth callback deep link contains invalid or expired tokens that
    the callback handler cannot process into a valid session**
    - **What happens:** The Tauri application receives a deep link at
        `docodego://auth/callback` with query parameters, but the
        OAuth tokens are expired, malformed, or were already consumed
        by a previous callback attempt, and the callback handler
        cannot establish a valid session.
    - **Source:** The external identity provider issued tokens with a
        short validity window that expired before the deep link
        reached the Tauri application, or a network interruption
        caused a delay that pushed the callback past the token
        expiration timestamp.
    - **Consequence:** The user is not signed in despite having
        completed the identity provider authentication, and the
        desktop application remains in an unauthenticated state with
        the sign-in page displayed inside the webview.
    - **Recovery:** The OAuth callback handler logs the token
        validation failure with the error details and token expiration
        timestamp — the application redirects the user to the sign-in
        page and the user retries the SSO authentication flow which
        generates fresh tokens from the identity provider.

## Declared Omissions

- This specification does not define the visual appearance or layout
    of the 404 not-found page rendered when a deep link path has no
    matching route — that page design is covered by the application
    shell and navigation specification.
- This specification does not cover mobile deep link handling via
    Android App Links or iOS Universal Links — mobile deep linking
    uses platform-specific mechanisms defined in a separate
    mobile-handles-deep-link specification.
- This specification does not define the SSO authentication flow
    details including token exchange, session cookie creation, and
    identity provider configuration — those behaviors are defined in
    the user-signs-in-with-sso specification.
- This specification does not address the auto-update mechanism that
    ensures deep link routes remain valid across application versions
    — version-specific route compatibility is an operational concern
    outside the scope of this deep link handling specification.
- This specification does not cover analytics or telemetry collection
    for deep link usage metrics such as click-through rates or most
    visited deep link targets — usage tracking is defined in a
    separate observability specification.

## Related Specifications

- [user-launches-desktop-app](user-launches-desktop-app.md) — defines
    the Tauri desktop application startup sequence during which the
    Deep-Link plugin registers the `docodego://` custom URL scheme
    with the operating system and the webview initializes
- [user-uses-system-tray](user-uses-system-tray.md) — defines the
    system tray icon behavior including the `show_window()` visibility
    toggle that the deep link handler also uses to bring the window to
    the foreground when a link arrives while the window is hidden
- [user-signs-in-with-sso](user-signs-in-with-sso.md) — defines the
    full SSO authentication flow including the desktop handoff pattern
    where the identity provider redirects back to
    `docodego://auth/callback` which this specification handles as a
    deep link
- [user-navigates-the-dashboard](user-navigates-the-dashboard.md) —
    defines the dashboard navigation structure and route definitions
    that TanStack Router resolves when a deep link path is forwarded
    for client-side navigation inside the webview
- [session-lifecycle](session-lifecycle.md) — defines the session
    management lifecycle that determines whether a deep link navigation
    succeeds with authenticated content or redirects to the sign-in
    page via the route guard

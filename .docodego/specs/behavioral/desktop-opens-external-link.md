---
id: SPEC-2026-069
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# Desktop Opens External Link

## Intent

This spec defines how the Tauri 2 desktop application handles clicks
on external links — URLs that point outside the application to domains
such as GitHub repositories, documentation sites, or changelog pages.
Because the desktop application runs inside a Tauri webview with no
browser chrome (no address bar, no tabs, no back button), allowing
the webview to navigate to an external URL would strand the user on
an external page with no way to return to the application. The
`tauri-plugin-opener` intercepts outbound navigation requests that
target external domains and opens those URLs in the user's default
system browser (Chrome, Firefox, Safari, or whichever browser the OS
has configured as the default). The webview remains on the page the
user was viewing, undisturbed, with no navigation and no state loss.
This same mechanism handles OAuth redirects during SSO sign-in: the
opener plugin launches the identity provider's sign-in page in the
system browser, and after authentication completes the provider
redirects back to the desktop application via the
`docodego://auth/callback` deep link, returning the user to the app
with their session established. All external link elements rendered
in the webview use `target="_blank"` or equivalent attributes so the
opener plugin can identify and intercept them before the webview
processes the navigation.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `tauri-plugin-opener` (Tauri plugin that intercepts outbound navigation and delegates URL opening to the OS default browser) | intercept/write | When the user clicks any link in the webview that targets an external domain outside the application's own origin, or when the OAuth flow initiates a redirect to an identity provider URL | The plugin fails to intercept the navigation and the webview navigates directly to the external URL, stranding the user outside the application — the application logs the interception failure and the user falls back to manually copying the URL and pasting it into a browser |
| OS default browser (Chrome, Firefox, Safari, or the browser configured as the system default for handling HTTP and HTTPS URLs) | write | When `tauri-plugin-opener` calls the OS shell API to open the intercepted external URL in the default browser application | The OS reports no default browser configured or the default browser binary is missing, and the opener plugin returns an error — the application logs the browser launch failure and notifies the user via a toast that the link could not be opened in the system browser |
| Webview navigation interception (prevents the webview from navigating away from the application origin to external domains) | block | When the webview receives a navigation event targeting a URL outside the application's bundled origin, the opener plugin blocks the webview navigation before the page unloads | The navigation interception fails and the webview leaves the application origin, rendering the external page inside the native window — the user loses access to the application UI and falls back to restarting the desktop application to restore the webview to the application |
| `docodego://auth/callback` deep link (custom URL scheme registered with the OS that routes OAuth callback redirects back to the desktop application) | read | When the identity provider completes OAuth authentication and redirects the browser to the `docodego://auth/callback` URL with the authorization code, the OS routes the deep link to the running Tauri application | The deep link registration is missing or another application has claimed the `docodego://` scheme, and the callback redirect fails to reach the desktop application — the user falls back to copying the authorization code manually or restarting the SSO flow from the desktop application |

## Behavioral Flow

1. **[User]** clicks an external link in the desktop application
    webview — for example a GitHub repository link, a documentation
    URL, or a changelog link rendered in the footer of the landing
    page inside the Tauri native window

2. **[Tauri]** `tauri-plugin-opener` intercepts the outbound
    navigation request before the webview processes it, inspects the
    target URL, and determines that the domain is external to the
    application's own bundled origin

3. **[Tauri]** the opener plugin calls the OS shell API to open the
    external URL in the user's default system browser — passing the
    full URL string to the platform-specific open command (ShellExecute
    on Windows, `open` on macOS, `xdg-open` on Linux)

4. **[OS]** the default system browser launches or activates an
    existing browser window and navigates to the external URL in a new
    tab — the external page loads independently of the desktop
    application process

5. **[Tauri]** the webview remains on the page the user was viewing
    before clicking the link — no navigation occurred in the webview,
    no page state was lost, and the DOM remains fully interactive with
    all form inputs, scroll positions, and component state preserved

6. **[User]** reads the external content in the system browser and
    switches back to the desktop application window at any time to
    continue working — the application is exactly where the user left
    it with no re-rendering or re-authentication required

7. **[User]** initiates an SSO sign-in from the desktop application,
    triggering an OAuth flow that requires redirecting to an external
    identity provider URL for authentication

8. **[Tauri]** `tauri-plugin-opener` intercepts the OAuth redirect
    URL targeting the identity provider domain and opens the identity
    provider sign-in page in the user's default system browser using
    the same OS shell API mechanism as regular external links

9. **[User]** completes authentication on the identity provider
    sign-in page in the system browser by entering credentials and
    approving the authorization request

10. **[OS]** the identity provider redirects the browser to the
    `docodego://auth/callback` deep link URL containing the
    authorization code — the OS recognizes the custom `docodego://`
    URL scheme and routes the deep link to the running Tauri
    desktop application

11. **[Tauri]** receives the `docodego://auth/callback` deep link
    with the authorization code, exchanges the code for session
    tokens via the API, and establishes the authenticated session
    in the webview — the user is now signed in without having
    navigated the webview away from the application

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| webview_idle | external_link_intercepted | The user clicks a link in the webview that targets a URL outside the application's bundled origin domain | The target URL domain does not match the application origin and `tauri-plugin-opener` is registered and active |
| external_link_intercepted | system_browser_opening | The opener plugin calls the OS shell API to open the external URL in the default system browser | The OS shell API call returns a non-error result indicating the browser launch was initiated |
| system_browser_opening | webview_idle | The OS confirms the default browser received the URL and the webview remains on the current application page with no navigation | The webview `location.href` still matches the application origin and the DOM state is unchanged |
| webview_idle | oauth_redirect_intercepted | The user initiates an SSO sign-in flow and the OAuth redirect targets the identity provider URL which is outside the application origin | The OAuth redirect URL domain does not match the application origin and the opener plugin is active |
| oauth_redirect_intercepted | idp_page_in_browser | The opener plugin opens the identity provider sign-in page in the default system browser via the OS shell API | The OS shell API call returns a non-error result and the identity provider page loads in the browser |
| idp_page_in_browser | callback_received | The identity provider completes authentication and redirects the browser to the `docodego://auth/callback` deep link which the OS routes to the Tauri application | The `docodego://` URL scheme is registered with the OS and the running Tauri application receives the deep link event |
| callback_received | webview_idle | The Tauri application extracts the authorization code from the callback URL, exchanges it for session tokens, and the webview reflects the authenticated state | The authorization code exchange returns valid session tokens and the session is stored in the webview cookie store |

## Business Rules

- **Rule external-link-opens-in-system-browser:** IF the user clicks
    a link in the webview that targets a URL with a domain different
    from the application's own bundled origin THEN `tauri-plugin-opener`
    opens that URL in the OS default system browser — the count of
    external URLs opened inside the webview equals 0
- **Rule webview-navigation-blocked-for-external-urls:** IF a
    navigation event targets a domain outside the application origin
    THEN the webview navigation is blocked before the page unloads and
    the webview `location.href` continues to match the application
    origin — the count of webview navigations to external domains
    equals 0
- **Rule webview-state-preserved:** IF the opener plugin intercepts
    an external link click and opens the URL in the system browser THEN
    the webview DOM state is fully preserved — scroll position, form
    inputs, and component state remain identical to their values before
    the click with 0 properties reset
- **Rule oauth-redirect-uses-opener:** IF the OAuth SSO flow requires
    redirecting to an external identity provider URL THEN the opener
    plugin opens the identity provider page in the system browser using
    the same interception mechanism as regular external links — the
    count of identity provider pages rendered inside the webview
    equals 0
- **Rule deep-link-returns-session-after-oauth:** IF the identity
    provider completes authentication and redirects to the
    `docodego://auth/callback` deep link THEN the OS routes the
    callback to the running Tauri application and the application
    exchanges the authorization code for session tokens — the count of
    successful deep link callbacks that result in an authenticated
    session equals 1 per SSO sign-in attempt

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (interacts with external links inside the Tauri webview and initiates OAuth SSO flows from the desktop application) | Click external links in the webview which triggers the opener plugin to open URLs in the system browser, initiate SSO sign-in which triggers the OAuth redirect to the identity provider in the system browser, switch between the system browser and the desktop application window | Cannot navigate the webview to an external domain because the opener plugin intercepts and blocks all outbound navigation before the webview processes it | External links are rendered as clickable elements in the webview UI but clicking them opens the system browser instead of navigating the webview — the user sees no URL bar or navigation controls inside the webview |
| Tauri (runtime that hosts the webview and manages the opener plugin, deep link handler, and OS shell API interactions) | Register the `tauri-plugin-opener` to intercept outbound navigation events, call the OS shell API to open URLs in the default browser, register the `docodego://` custom URL scheme with the OS, receive deep link callbacks and extract authorization codes | Cannot control which system browser the OS launches because the browser selection is determined by the OS default browser configuration, cannot modify the identity provider sign-in page rendered in the system browser | The Tauri runtime has visibility into all navigation events occurring in the webview and all deep link events routed to the application by the OS |
| OS (operating system that launches the default browser, manages the custom URL scheme registry, and routes deep link callbacks) | Launch the default system browser when the opener plugin requests a URL to be opened, route `docodego://auth/callback` deep link events from the browser to the registered Tauri application, manage the default browser configuration | Cannot intercept or modify the content of the external URL being opened, cannot block the deep link callback from reaching the Tauri application once the URL scheme is registered | The OS handles the URL scheme routing and browser launching transparently without visibility into the webview content or the OAuth token exchange |

## Constraints

- The `tauri-plugin-opener` intercepts and redirects external link
    clicks to the system browser within 200 ms of the click event —
    the count of milliseconds from click event to OS shell API call
    equals 200 or fewer.
- The webview `location.href` remains unchanged after an external
    link click — the count of webview navigations to non-application
    domains per external link click equals 0.
- The `docodego://auth/callback` deep link is registered with the OS
    during application installation and is active for the entire
    application lifetime — the count of unregistered deep link scheme
    events during the application lifecycle equals 0.
- The OAuth deep link callback delivers the authorization code to the
    Tauri application within 5000 ms of the identity provider issuing
    the redirect — the count of milliseconds from redirect issuance to
    application receipt equals 5000 or fewer.
- All external link elements in the webview use `target="_blank"` or
    equivalent opener-compatible attributes — the count of external
    links missing the `target="_blank"` attribute in the rendered DOM
    equals 0.
- The opener plugin handles concurrent external link clicks by
    processing each click independently without blocking the webview
    event loop — the count of dropped link-open requests due to
    concurrency equals 0.

## Acceptance Criteria

- [ ] Clicking a GitHub repository link in the webview opens the URL in the OS default browser — the count of browser tabs opened with the target URL equals 1
- [ ] After clicking an external link the webview remains on the application page — the webview `location.href` matches the application origin and the count of external-domain navigations equals 0
- [ ] The webview DOM state is preserved after an external link click — the count of scroll position changes equals 0, the count of form input values cleared equals 0, and the count of component state resets equals 0
- [ ] Clicking a documentation link from the landing page footer opens the URL in the system browser within 200 ms of the click event — the elapsed time from click to browser launch equals 200 ms or fewer
- [ ] The `tauri-plugin-opener` blocks the webview from navigating to any external domain — the count of successful webview navigations to non-application domains equals 0 across 10 consecutive external link clicks
- [ ] Initiating SSO sign-in opens the identity provider page in the system browser — the count of identity provider pages rendered inside the webview equals 0
- [ ] After completing OAuth authentication the `docodego://auth/callback` deep link routes back to the desktop application — the count of deep link events received by the Tauri application per SSO flow equals 1
- [ ] The authorization code from the deep link callback is exchanged for session tokens — the count of authenticated sessions established after a successful OAuth callback equals 1
- [ ] The webview reflects the authenticated state after the OAuth callback without requiring a page reload — the count of page reloads triggered by the callback equals 0 and the dashboard route renders within 2000 ms of the callback
- [ ] Multiple external links clicked in rapid succession each open in the system browser independently — the count of browser tabs opened equals the count of links clicked when 5 links are clicked within 2000 ms
- [ ] The `docodego://` custom URL scheme is registered with the OS and active while the application is running — the count of unhandled `docodego://` scheme events during the application lifetime equals 0
- [ ] Internal application links (same-origin navigation) are not intercepted by the opener plugin — the count of same-origin links incorrectly opened in the system browser equals 0 across 10 internal navigation events

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user clicks an external link but no default browser is configured on the operating system | The opener plugin catches the OS shell API error indicating no default browser is available, logs the error details, and displays a toast notification in the webview informing the user that the link could not be opened | The toast notification is visible in the webview, the webview remains on the application page, and the error log entry contains the target URL and the OS error code |
| The user clicks an external link while the system browser is already open with multiple tabs consuming high memory | The OS shell API opens the URL in a new tab in the existing browser instance regardless of the browser's memory usage — the opener plugin does not check or limit browser resource consumption | A new browser tab opens with the external URL and the webview remains on the application page with the count of webview navigations equals 0 |
| The user clicks the same external link multiple times rapidly within 500 ms | Each click is processed independently by the opener plugin and the OS opens the URL in a new browser tab for each click — the count of browser tabs opened equals the number of clicks | The number of browser tabs opened with the target URL matches the click count and the webview state is preserved after all clicks |
| The identity provider takes longer than 60 seconds to complete the OAuth flow and the user has not interacted with the desktop application during that time | The desktop application waits for the deep link callback with no timeout on the application side — the Tauri deep link handler remains active for the entire application lifetime and processes the callback whenever it arrives | The deep link callback is received and processed after the delayed authentication and the session is established with 0 errors |
| Another application has registered the `docodego://` URL scheme and intercepts the OAuth callback before the Tauri application receives it | The Tauri application does not receive the deep link callback and the OAuth flow does not complete — the user remains unauthenticated and the application displays the sign-in page with no session established | The count of authenticated sessions after the OAuth redirect equals 0 and the sign-in page is displayed with a prompt to retry the SSO flow |
| The user clicks an internal application link (same-origin) that the opener plugin incorrectly identifies as external | The opener plugin correctly distinguishes internal links by comparing the URL domain against the application origin and does not intercept same-origin navigation — the webview navigates normally | The webview `location.href` changes to the new internal route and the count of system browser launches for internal links equals 0 |

## Failure Modes

- **The opener plugin fails to intercept an external link click and the webview navigates away from the application**
    - **What happens:** The `tauri-plugin-opener` does not intercept
        the outbound navigation event and the webview navigates to the
        external URL, replacing the application UI with the external
        page content inside the native window.
    - **Source:** The opener plugin is not registered in the Tauri
        plugin configuration, or the plugin failed to initialize during
        application startup due to a missing dependency or configuration
        error in the `tauri.conf.json` file.
    - **Consequence:** The user is stranded on an external page inside
        the native window with no address bar, no back button, and no
        navigation controls to return to the application — the user
        loses access to the entire application UI.
    - **Recovery:** The application detects the webview navigation away
        from the application origin and logs the navigation event with
        the target URL — the user falls back to closing and restarting
        the desktop application to restore the webview to the
        application origin.

- **The OS shell API fails to launch the default system browser when the opener plugin requests a URL to be opened**
    - **What happens:** The opener plugin calls the OS shell API to
        open an external URL in the default browser but the API call
        returns an error because no default browser is configured, the
        browser binary is missing, or the OS security policy blocks
        the shell open command.
    - **Source:** The user has uninstalled their default browser, the
        OS default browser registry entry is corrupted, or a security
        policy on the device restricts application-initiated browser
        launches via the shell API.
    - **Consequence:** The external link does not open anywhere and the
        user receives no visual feedback about the failure unless the
        application explicitly handles the error — the user cannot
        access the external resource from the link click.
    - **Recovery:** The opener plugin catches the OS shell API error
        and notifies the user via a toast notification in the webview
        that the link could not be opened — the application logs the
        error with the target URL and the OS error code, and the user
        falls back to manually copying the URL from the toast message
        and pasting it into a browser.

- **The deep link callback from the OAuth flow does not reach the Tauri application because the URL scheme registration is missing or hijacked**
    - **What happens:** The identity provider completes authentication
        and redirects the browser to `docodego://auth/callback` but the
        OS does not route the deep link to the Tauri application
        because the custom URL scheme is not registered or another
        application has claimed the `docodego://` scheme.
    - **Source:** The `docodego://` URL scheme was not registered
        during application installation due to an installer error, or
        another application on the device registered the same custom
        URL scheme after the desktop application was installed.
    - **Consequence:** The OAuth flow does not complete and the user
        remains unauthenticated — the desktop application continues
        displaying the sign-in page and the authorization code from the
        identity provider is lost because no application processes the
        callback redirect.
    - **Recovery:** The desktop application detects that the OAuth
        callback was not received within 120 seconds of initiating the
        SSO flow and logs a timeout warning — the sign-in page notifies
        the user that the SSO flow did not complete and prompts the
        user to retry the SSO sign-in or falls back to an alternative
        sign-in method such as email OTP.

- **The webview loses state after an external link click due to an unexpected page reload triggered by the navigation interception**
    - **What happens:** The opener plugin intercepts the external link
        click and blocks the webview navigation, but the interception
        mechanism triggers an unintended page reload in the webview
        that clears form inputs, resets scroll position, and destroys
        in-memory component state.
    - **Source:** The navigation interception handler calls
        `event.preventDefault()` on the navigation event but a side
        effect in the webview engine causes the current page to reload
        instead of remaining static, triggered by a browser engine bug
        or an incompatible Tauri plugin version.
    - **Consequence:** The user loses all unsaved form data and the
        webview returns to the initial page state, requiring the user
        to re-enter form inputs and re-navigate to their previous
        position within the application.
    - **Recovery:** The application detects the unexpected page reload
        via a page lifecycle event listener and logs a warning with the
        URL that triggered the reload — the application retries loading
        the current route and restores any state persisted in
        localStorage or session cookies to minimize data loss for the
        user.

## Declared Omissions

- This specification does not define the visual styling or placement
    of external link indicators (such as an external-link icon next to
    URLs) in the webview — the UI treatment of external links is
    covered by the component design system in @repo/ui.
- This specification does not cover the behavior of `mailto:`, `tel:`,
    or other non-HTTP URL schemes clicked in the webview — handling of
    non-HTTP schemes requires a separate specification addressing the
    opener plugin configuration for each scheme type.
- This specification does not address the OAuth token refresh flow
    that occurs after the initial session is established via the deep
    link callback — token refresh and session extension are covered by
    the session-lifecycle behavioral specification.
- This specification does not define the list of allowed external
    domains or any domain allowlist/blocklist filtering — all external
    domains are treated identically by the opener plugin with no
    domain-level restrictions applied.
- This specification does not cover the behavior when the desktop
    application is not running and the user clicks a `docodego://`
    deep link — cold-start deep link handling requires a separate
    specification addressing application launch from a URL scheme
    invocation.

## Related Specifications

- [user-launches-desktop-app](user-launches-desktop-app.md) — defines
    the Tauri desktop application startup sequence including webview
    initialization and plugin registration that enables the opener
    plugin to intercept external link clicks after the application is
    fully running
- [user-uses-system-tray](user-uses-system-tray.md) — defines the
    system tray icon behavior for the desktop application including
    window visibility management that the user relies on when switching
    between the desktop application and the system browser after
    clicking an external link
- [user-signs-in-with-sso](user-signs-in-with-sso.md) — defines the
    SSO sign-in flow that triggers the OAuth redirect handled by the
    opener plugin to open the identity provider page in the system
    browser and return via the `docodego://auth/callback` deep link
- [session-lifecycle](session-lifecycle.md) — defines the session
    management lifecycle including token exchange and session cookie
    storage that completes the OAuth flow after the deep link callback
    delivers the authorization code to the Tauri application

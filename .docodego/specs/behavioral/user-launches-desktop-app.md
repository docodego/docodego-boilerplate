---
id: SPEC-2026-066
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Launches Desktop App

## Intent

This spec defines how a user launches the Tauri 2 desktop application
on Windows, macOS, or Linux and reaches a fully interactive state with
the web application rendered inside a native window. On Windows the
user double-clicks the `.exe` file or selects the app from the Start
menu. On macOS the user opens the `.app` bundle from the Applications
folder after installing from the `.dmg` image. On Linux the user runs
the `.AppImage` directly or launches from the application menu when
installed via the `.deb` package. Regardless of platform, the Tauri
runtime starts a native window containing a webview that loads the
full web application. The Window-State plugin restores the window to
its last-used size and position on subsequent launches, and uses a
centered default size on first launch. No browser chrome is visible
inside the window — no address bar, tabs, or navigation buttons. The
window has an OS-native title bar with minimize, maximize, and close
buttons. A tray icon registers in the system notification area on
Windows or the menu bar area on macOS, providing quick access to show,
hide, or quit the application. Authentication works via cookies stored
natively in the Tauri webview, so existing sessions persist across
application restarts without requiring the user to sign in again. All
UI text within the webview is localized through the @repo/i18n
infrastructure.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Tauri 2 runtime (native application host that spawns the window and manages the process lifecycle) | process start | When the user launches the executable on Windows via `.exe`, on macOS via `.app` bundle, or on Linux via `.AppImage` or `.deb`-installed desktop entry — the runtime initializes the native window and webview | The application process fails to start and the operating system displays a platform-specific error dialog — the user falls back to opening the web application directly in a browser at the hosted URL |
| Webview engine (WKWebView on macOS, WebView2 on Windows, WebKitGTK on Linux — renders the web application) | render | When the Tauri runtime creates the native window and the webview component initializes to load the bundled web application assets from the local filesystem | The native window opens but displays a blank or error page because the webview engine is missing or incompatible — the application logs the webview initialization failure and the user falls back to the browser-hosted version of the web application |
| Window-State plugin (Tauri plugin that persists and restores window position and dimensions across sessions) | read/write | On launch the plugin reads the last-saved window geometry from persistent storage and applies it to the native window, and on window move or resize events the plugin writes the updated geometry | The plugin fails to read saved state and the window falls back to the default centered position at 1280 by 720 pixels — subsequent geometry changes are not persisted until the plugin storage becomes available again |
| Tray icon registration (system notification area on Windows, menu bar area on macOS — provides show, hide, and quit actions) | write | During application startup after the native window is created, the Tauri runtime registers a tray icon with a context menu containing Show, Hide, and Quit actions | The tray icon does not appear in the system notification area and the user falls back to interacting with the application exclusively through the native window title bar controls — no functionality is lost because all actions remain available through the window itself |
| Cookie-based auth session (Tauri webview cookie storage that persists authentication tokens across restarts) | read | When the webview loads the web application, the auth client reads existing session cookies from the webview cookie store to determine whether the user has an active authenticated session | The webview cookie store returns no session cookies and the web application redirects the user to the sign-in page — the user re-authenticates and a new session cookie is written for future restarts |
| @repo/i18n (localization infrastructure that provides translated strings for all UI text rendered in the webview) | read | When the web application initializes inside the webview and renders all UI components including navigation labels, button text, and status messages in the user's configured locale | The i18n namespace fails to load and the UI degrades to displaying raw translation keys instead of localized strings — the application logs the missing namespace and retries loading the translations on the next navigation event |

## Behavioral Flow

1. **[User]** launches the desktop application — on Windows by
    double-clicking the `.exe` file or selecting the app from the
    Start menu, on macOS by opening the `.app` bundle from the
    Applications folder, on Linux by running the `.AppImage` or
    selecting the app from the application menu after `.deb`
    installation

2. **[Tauri]** runtime initializes the native process, allocates
    memory for the application context, and begins creating the
    native window with an embedded webview component specific to the
    operating system — WKWebView on macOS, WebView2 on Windows, or
    WebKitGTK on Linux

3. **[Tauri]** Window-State plugin reads the last-saved window
    geometry (position and dimensions) from persistent storage — if
    saved state exists the window opens at the restored position and
    size, matching exactly where the user left it in the previous
    session

4. **[Tauri]** if no saved window state exists because this is the
    first launch, the Window-State plugin falls back to the default
    configuration — the window opens centered on the primary display
    at 1280 by 720 pixels

5. **[Webview]** loads the full web application from the bundled
    local assets — the webview renders the application UI inside the
    native window without any browser chrome, meaning no address bar,
    no tab strip, and no forward or back navigation buttons are
    visible to the user

6. **[Webview]** the native window displays an OS-rendered title bar
    with standard minimize, maximize, and close buttons — the title
    bar appearance follows the operating system theme and makes the
    application indistinguishable from other native desktop programs

7. **[Tauri]** registers a tray icon in the system notification area
    on Windows or the menu bar area on macOS — the tray icon context
    menu provides three actions: Show (brings the window to the
    foreground), Hide (minimizes to tray), and Quit (terminates the
    application process)

8. **[Webview]** the auth client reads existing session cookies from
    the webview cookie store to determine the authentication state —
    if a valid session cookie exists the user proceeds directly to the
    dashboard without re-authenticating

9. **[Webview]** if no valid session cookie exists in the webview
    cookie store, the web application redirects the user to the
    sign-in page where they authenticate using any configured method
    (email OTP, passkey, or SSO)

10. **[Webview]** all UI text rendered in the webview is localized
    through the @repo/i18n infrastructure — labels, button text,
    navigation items, and status messages display in the user's
    configured locale language

11. **[User]** the application is fully running and interactive — the
    user can interact with the web application inside the native
    window, use the tray icon to show or hide the window, and their
    session persists across application restarts via cookies stored
    in the webview

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| not_running | runtime_initializing | User launches the executable on Windows, macOS, or Linux through the platform-specific method (double-click, Start menu, Applications folder, AppImage, or application menu) | The executable file exists on disk and the operating system grants permission to start the process |
| runtime_initializing | window_creating | Tauri runtime completes process initialization and begins creating the native window with the platform-specific webview component | The webview engine (WKWebView, WebView2, or WebKitGTK) is installed and available on the operating system |
| window_creating | window_state_restoring | Native window is created and the Window-State plugin attempts to read saved geometry from persistent storage | The window handle is valid and the Window-State plugin is registered in the Tauri configuration |
| window_state_restoring | webview_loading | Window-State plugin applies the restored geometry (or the 1280 by 720 default if no saved state exists) and the window is positioned on screen | The restored geometry places the window within the bounds of at least one connected display |
| webview_loading | session_checking | Webview finishes loading the bundled web application assets and the auth client initializes to read session cookies | The webview rendered the application entry point without a loading error and the DOM is interactive |
| session_checking | app_ready_authenticated | Auth client reads a valid session cookie from the webview cookie store and confirms the session has not expired | The session cookie exists, has not expired, and the auth server validates the session token |
| session_checking | app_ready_unauthenticated | Auth client finds no session cookie or the existing session cookie has expired or is invalid | The webview cookie store returned no valid session cookie or the auth server rejected the token |
| app_ready_authenticated | not_running | User selects Quit from the tray icon context menu or clicks the close button on the native window title bar | The application has no unsaved state that requires a confirmation dialog before closing |
| app_ready_unauthenticated | not_running | User selects Quit from the tray icon context menu or clicks the close button on the native window title bar | The application has no unsaved state that requires a confirmation dialog before closing |

## Business Rules

- **Rule window-state-restored-on-relaunch:** IF the user has
    previously launched and repositioned the desktop application THEN
    the Window-State plugin restores the window to the exact saved
    position and dimensions on the next launch — the count of pixels
    difference between the saved geometry and the restored geometry
    equals 0
- **Rule first-launch-default-size:** IF the user launches the
    desktop application for the first time and no saved window state
    exists in persistent storage THEN the window opens centered on the
    primary display at exactly 1280 by 720 pixels — the window width
    equals 1280 and the window height equals 720
- **Rule no-browser-chrome:** IF the Tauri webview renders the web
    application inside the native window THEN no browser UI elements
    are visible to the user — the count of visible address bars equals
    0, the count of visible tab strips equals 0, and the count of
    visible navigation buttons equals 0
- **Rule tray-icon-registered-on-launch:** IF the Tauri runtime
    completes the application startup sequence THEN a tray icon is
    registered in the system notification area with a context menu
    containing exactly 3 actions: Show, Hide, and Quit — the count of
    tray icon context menu items equals 3
- **Rule cookie-session-persists-across-restarts:** IF the user has
    an authenticated session and quits the desktop application THEN on
    the next launch the webview cookie store contains the session
    cookie and the user is not required to re-authenticate — the count
    of sign-in prompts displayed to a previously authenticated user on
    relaunch equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated User (session restored from cookie stored in the Tauri webview cookie store) | Launch the desktop application, interact with the full web application inside the webview, use all tray icon actions (Show, Hide, Quit), resize and reposition the native window with geometry persisted by the Window-State plugin | No actions are denied to an authenticated user within the desktop application — all web application features available in the browser are identically available in the Tauri webview | The full web application UI is visible inside the native window including the dashboard, settings pages, and all navigation elements rendered in the user's configured locale |
| Unauthenticated User (no valid session cookie found in the Tauri webview cookie store on launch) | Launch the desktop application, view the sign-in page rendered in the webview, authenticate using email OTP or passkey or SSO, use tray icon actions (Show, Hide, Quit), resize and reposition the native window | Cannot access the dashboard or any authenticated routes — the web application route guard redirects all navigation attempts to the sign-in page until authentication completes | Only the sign-in page is visible inside the native window — authenticated routes and dashboard content are not rendered until the user completes the sign-in flow and a valid session cookie is written |
| OS (operating system that launches the Tauri process and manages the native window lifecycle) | Start the application process when the user requests a launch, provide the webview engine (WKWebView, WebView2, or WebKitGTK), manage the native title bar rendering, host the tray icon in the system notification area | Cannot modify the web application content rendered inside the webview, cannot read or write session cookies stored in the webview cookie store, cannot alter the Window-State plugin saved geometry | The OS renders the native title bar and tray icon but has no visibility into the web application state, authentication status, or user data displayed within the webview content area |

## Constraints

- The Tauri runtime completes process initialization and displays the
    native window within 3000 ms of the user launching the executable
    — the count of milliseconds from process start to window visible
    equals 3000 or fewer.
- The webview loads and renders the web application entry point
    within 2000 ms of the native window appearing on screen — the
    count of milliseconds from window visible to interactive DOM
    equals 2000 or fewer.
- The Window-State plugin persists window geometry changes within
    500 ms of the user finishing a move or resize operation — the
    count of geometry changes lost due to delayed persistence equals 0
    when the user waits at least 500 ms before quitting.
- All UI text rendered inside the webview uses @repo/i18n translation
    keys with zero hardcoded English strings — the count of hardcoded
    user-facing strings in the desktop application webview equals 0.
- The tray icon context menu renders in the OS locale language using
    native system APIs — the count of tray menu items not matching the
    OS locale equals 0.
- The webview cookie store retains session cookies across application
    restarts with no explicit cookie-export mechanism — the count of
    session cookies lost between a quit and relaunch cycle equals 0
    when the application exits cleanly.

## Acceptance Criteria

- [ ] Launching the `.exe` on Windows starts the Tauri runtime and displays a native window — the count of native windows visible after launch equals 1
- [ ] Launching the `.app` bundle on macOS starts the Tauri runtime and displays a native window — the count of native windows visible after launch equals 1
- [ ] Running the `.AppImage` on Linux starts the Tauri runtime and displays a native window — the count of native windows visible after launch equals 1
- [ ] The Window-State plugin restores the window to the previously saved position on relaunch — the pixel difference between the saved and restored x-coordinate equals 0 and the y-coordinate difference equals 0
- [ ] On first launch with no saved state the window opens centered at 1280 by 720 pixels — the window width equals 1280 and the window height equals 720
- [ ] The webview renders the web application with no browser chrome visible — the count of visible address bars equals 0 and the count of visible tab strips equals 0
- [ ] The native window title bar displays OS-rendered minimize, maximize, and close buttons — the count of title bar control buttons equals 3
- [ ] A tray icon appears in the system notification area with a context menu — the count of tray icon context menu items equals 3 (Show, Hide, Quit)
- [ ] Clicking Show in the tray context menu brings the window to the foreground — the window `is_visible` property returns true after clicking Show
- [ ] Clicking Hide in the tray context menu hides the window from the taskbar — the window `is_visible` property returns false after clicking Hide
- [ ] A previously authenticated user relaunching the app is not prompted to sign in — the count of sign-in page renders for a user with a valid session cookie equals 0
- [ ] An unauthenticated user launching the app sees the sign-in page — the rendered route path equals the sign-in page path
- [ ] All UI text inside the webview is localized via @repo/i18n — the count of hardcoded English strings in rendered DOM text content equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User launches the app but the webview engine (WebView2 on Windows) is not installed on the system | The Tauri runtime detects the missing webview engine and displays a native error dialog instructing the user to install the required webview component from the platform vendor | The native error dialog is displayed with a message containing the webview engine name and the count of webview render attempts equals 0 |
| Window-State plugin has saved geometry that places the window entirely off-screen because the user disconnected an external monitor | The Window-State plugin detects that the restored position is outside the bounds of all connected displays and falls back to centering the window on the primary display at 1280 by 720 pixels | The window is visible on the primary display and the restored position differs from the saved position because the off-screen geometry was rejected |
| User launches the application while another instance is already running on the same machine | The Tauri runtime detects the existing instance via a single-instance lock, brings the existing window to the foreground, and the new process exits immediately without creating a second window | The count of native windows equals 1 after the second launch attempt and the existing window `is_focused` property returns true |
| Session cookie exists in the webview cookie store but has expired since the last application run | The auth client reads the expired cookie, the auth server rejects the session token, and the web application redirects the user to the sign-in page to re-authenticate | The rendered route path equals the sign-in page path and the count of dashboard renders before re-authentication equals 0 |
| The user quits the application by force-killing the process instead of using the close button or Quit from the tray menu | The Window-State plugin does not get a chance to persist the latest geometry and the next launch restores the last successfully saved position and size from before the force-kill event | The restored window geometry matches the last persisted state before the force-kill and the count of geometry corruption errors equals 0 |
| The tray icon registration fails because the system notification area is full or the OS denies tray access (Linux with no system tray) | The application continues running with the native window fully functional and logs a warning about the tray icon registration failure — all window management is done through the title bar controls | The native window is visible and interactive, the count of tray icons equals 0, and the count of logged tray registration warnings equals 1 |

## Failure Modes

- **Webview engine missing or incompatible on the target platform**
    - **What happens:** The Tauri runtime attempts to initialize the
        platform-specific webview engine (WebView2 on Windows,
        WKWebView on macOS, or WebKitGTK on Linux) but the engine is
        not installed, is an incompatible version, or fails to load
        the required system library.
    - **Source:** The user is running a fresh Windows installation
        without the WebView2 runtime, or a Linux distribution that
        does not include the WebKitGTK package, or a macOS version
        older than the minimum supported release for WKWebView.
    - **Consequence:** The native window cannot render any web content
        and the application is unusable because the webview is the
        sole rendering surface for the entire user interface — no
        fallback native UI exists within the desktop application.
    - **Recovery:** The Tauri runtime logs the webview initialization
        error with the engine name and version details, then displays
        a native OS dialog that notifies the user to install the
        required webview engine and provides the download URL for the
        platform vendor's installer page.

- **Window-State plugin fails to read or write persisted geometry**
    - **What happens:** The Window-State plugin attempts to read the
        saved window position and dimensions from the persistent
        storage file but the file is corrupted, the filesystem denies
        read access, or the storage directory was deleted between
        application sessions.
    - **Source:** The persistent storage file was corrupted by a
        previous force-kill that interrupted a write operation, or the
        user manually deleted the application data directory, or a
        filesystem permission change revoked read access to the Tauri
        configuration directory.
    - **Consequence:** The window cannot restore its previous position
        and dimensions, so the user's custom window placement from the
        previous session is lost and the window opens at the default
        position instead of where the user left it.
    - **Recovery:** The Window-State plugin catches the read error and
        falls back to the default centered position at 1280 by 720
        pixels — it logs a warning with the storage path and error
        details, and on the next window move or resize event it
        retries writing the geometry to re-create the storage file.

- **Tray icon registration fails on the target operating system**
    - **What happens:** The Tauri runtime attempts to register a tray
        icon in the system notification area but the registration call
        returns an error because the OS denies tray access, the system
        tray service is not running, or the notification area has
        reached its maximum capacity.
    - **Source:** A Linux desktop environment that does not include a
        system tray (such as certain Wayland-only configurations
        without a status notifier service), or a Windows group policy
        that restricts applications from adding tray icons, or a macOS
        sandbox restriction that blocks menu bar item registration.
    - **Consequence:** The user cannot access the Show, Hide, and Quit
        shortcuts from the tray icon context menu, reducing the
        convenience of managing the application window without finding
        it in the taskbar or dock.
    - **Recovery:** The Tauri runtime catches the tray registration
        error and logs a warning with the platform name and error code
        — the application continues running with full functionality
        through the native window title bar, and the user falls back
        to using the minimize, maximize, and close buttons for all
        window management operations.

- **Session cookie is missing or rejected on application relaunch**
    - **What happens:** The user relaunches the desktop application
        expecting to resume their authenticated session, but the
        webview cookie store returns no session cookie or returns a
        cookie that the auth server rejects because it has expired or
        been revoked on the server side.
    - **Source:** The session expired due to the server-configured
        maximum session duration, the admin revoked the user's session
        while the application was closed, or the webview cookie store
        was cleared by the operating system's storage management
        process or a manual cache deletion by the user.
    - **Consequence:** The user is not automatically signed in and the
        web application redirects to the sign-in page, requiring the
        user to re-authenticate before accessing the dashboard or any
        protected routes within the desktop application.
    - **Recovery:** The web application redirects the user to the
        sign-in page and logs the session validation failure reason
        — the user re-authenticates using email OTP, passkey, or SSO,
        and a new session cookie is written to the webview cookie
        store that persists for future application restarts.

## Declared Omissions

- This specification does not define the auto-update mechanism that
    checks for new application versions and downloads patches — that
    behavior is covered by a separate spec addressing the Tauri updater
    plugin configuration and update notification workflow.
- This specification does not cover the deep-linking behavior where
    clicking a custom protocol URL in the browser opens the desktop
    application — custom URL scheme registration and intent handling
    are defined in a separate deep-linking specification.
- This specification does not address the crash reporting or telemetry
    collection that occurs when the Tauri runtime or webview encounters
    an unrecoverable error — crash reporting integration and data
    collection consent are covered by a separate observability spec.
- This specification does not define the specific sign-in flows (email
    OTP, passkey, or SSO) available on the sign-in page — those
    authentication methods are documented in their respective behavioral
    specifications (user-signs-in-with-email-otp, user-signs-in-with-passkey,
    user-signs-in-with-sso).
- This specification does not cover the visual theme applied to the
    webview content (light mode, dark mode, or system preference) — the
    theme selection and application mechanism are defined in the
    user-changes-theme behavioral specification.

## Related Specifications

- [user-changes-theme](user-changes-theme.md) — Defines the theme
    switching mechanism that operates inside the Tauri webview including
    the localStorage-based persistence and the OS title bar visual
    mismatch behavior documented for the desktop application context
- [session-lifecycle](session-lifecycle.md) — Defines the full
    authentication session lifecycle including cookie creation,
    validation, expiration, and revocation that determines whether the
    desktop application user is authenticated on launch or redirected
    to sign-in
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) —
    Defines the email OTP sign-in flow that unauthenticated desktop
    application users follow when no valid session cookie exists in the
    Tauri webview cookie store and the sign-in page is rendered
- [user-navigates-the-dashboard](user-navigates-the-dashboard.md) —
    Defines the dashboard shell and navigation structure that the
    authenticated desktop application user sees after the session
    cookie is validated and the web application loads inside the Tauri
    webview

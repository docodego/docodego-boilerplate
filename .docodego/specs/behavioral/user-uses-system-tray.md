---
id: SPEC-2026-067
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Uses System Tray

## Intent

This spec defines how the Tauri desktop application creates and
manages a system tray icon that provides persistent access to window
visibility controls and application lifecycle actions. When the
desktop application launches, a tray icon appears in the operating
system notification area — the taskbar notification area (system tray)
in the bottom-right corner on Windows, or the menu bar at the top of
the screen on macOS. The tray icon remains present for the entire
lifetime of the application process, giving the user a persistent
access point for toggling window visibility and quitting the
application. Left-clicking the tray icon toggles the main window: if
the window is visible it hides, and if the window is hidden it shows
and receives focus. Right-clicking the tray icon opens a context menu
with two localized options rendered via @repo/i18n translation keys:
"Show" which brings the window to the foreground and focuses it, and
"Quit" which closes the application entirely by removing the tray icon
and terminating the process. When the user clicks the close button (X)
on the application window, the application quits entirely — there is
no minimize-to-tray behavior on close. The window closes, the tray
icon is removed, and the application process terminates. This keeps
the close behavior simple and predictable: closing the window means
closing the application.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Tauri tray icon API (`tray::TrayIconBuilder`) for creating and managing the system tray icon | read/write | When the desktop application launches and the Rust backend initializes the tray icon in the OS notification area, and when the tray icon is removed during application termination | The application launches without a tray icon and the user loses the ability to toggle window visibility or access the context menu from the notification area, falling back to standard window controls only |
| OS notification area on Windows (taskbar system tray) or menu bar on macOS for hosting the tray icon | read | When the Tauri tray icon API registers the icon with the operating system during application startup and when the icon is removed during shutdown | The tray icon registration fails and the icon does not appear in the notification area, and the application logs a warning at startup indicating the tray icon could not be registered with the OS |
| Tauri context menu API for building the right-click menu with localized "Show" and "Quit" options | read/write | When the user right-clicks the tray icon and the Rust backend constructs and displays the context menu with translated labels | The context menu fails to render and the user cannot access the "Show" or "Quit" options, falling back to left-click toggle for window visibility and the window close button (X) for quitting |
| Tauri window visibility IPC (`appWindow.show()`, `appWindow.hide()`, `appWindow.setFocus()`) for controlling main window state | write | When the user left-clicks the tray icon to toggle visibility, or selects "Show" from the context menu to bring the window to the foreground and focus it | The window visibility toggle fails and the window remains in its current state (visible or hidden), and the application logs the IPC failure for diagnostics |
| @repo/i18n localization infrastructure for providing translated labels for the context menu "Show" and "Quit" options | read | When the Rust backend constructs the context menu and retrieves the localized strings for the two menu items based on the current application locale | The context menu falls back to displaying the default English labels "Show" and "Quit" as hardcoded fallback values when the i18n namespace fails to load or returns empty translations |

## Behavioral Flow

1. **[Tauri]** initializes the system tray icon during application
    startup by calling the tray icon builder API, registering the icon
    with the operating system notification area — the taskbar system
    tray on Windows or the menu bar on macOS

2. **[OS]** displays the tray icon in the notification area where it
    remains visible for the entire lifetime of the application process
    until the application terminates and removes the icon

3. **[User]** left-clicks the tray icon while the main application
    window is currently visible on screen

4. **[Tauri]** receives the left-click event on the tray icon, checks
    the current visibility state of the main window, determines that
    the window is visible, and calls `appWindow.hide()` to hide the
    main window from the screen

5. **[User]** left-clicks the tray icon while the main application
    window is currently hidden

6. **[Tauri]** receives the left-click event on the tray icon, checks
    the current visibility state of the main window, determines that
    the window is hidden, calls `appWindow.show()` to make the window
    visible, and then calls `appWindow.setFocus()` to bring the window
    to the foreground and give it keyboard focus

7. **[User]** right-clicks the tray icon to open the context menu

8. **[Tauri]** constructs a context menu with exactly 2 items: a
    "Show" option with a localized label retrieved from @repo/i18n,
    and a "Quit" option with a localized label retrieved from
    @repo/i18n, then displays the context menu at the tray icon
    position

9. **[User]** selects the "Show" option from the context menu

10. **[Tauri]** receives the "Show" menu item click event, calls
    `appWindow.show()` to make the window visible if it is hidden,
    and calls `appWindow.setFocus()` to bring the window to the
    foreground and give it keyboard focus regardless of its previous
    visibility state

11. **[User]** selects the "Quit" option from the context menu

12. **[Tauri]** receives the "Quit" menu item click event, removes
    the tray icon from the OS notification area, closes the main
    application window, and terminates the application process
    entirely

13. **[User]** clicks the close button (X) on the main application
    window title bar

14. **[Tauri]** receives the window close event, removes the tray
    icon from the OS notification area, closes the window, and
    terminates the application process — there is no minimize-to-tray
    behavior, the close button always results in full application
    termination

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| (none) | app_running_window_visible | The desktop application launches and the Tauri backend initializes the tray icon and displays the main window | The tray icon registration with the OS notification area completed and the main window rendered |
| app_running_window_visible | app_running_window_hidden | The user left-clicks the tray icon while the main window is visible on screen | The main window's `isVisible()` returns true and the left-click event was received on the tray icon |
| app_running_window_hidden | app_running_window_visible | The user left-clicks the tray icon while the main window is hidden, or selects the "Show" option from the right-click context menu | The main window's `isVisible()` returns false and the left-click or "Show" menu click event was received |
| app_running_window_visible | app_running_window_visible | The user selects the "Show" option from the context menu while the window is already visible and focused | The main window's `isVisible()` returns true and the "Show" click calls `setFocus()` without changing visibility |
| app_running_window_visible | app_terminated | The user selects "Quit" from the context menu or clicks the close button (X) on the window title bar | The "Quit" menu click or window close event was received and the tray icon removal and process termination proceed |
| app_running_window_hidden | app_terminated | The user selects "Quit" from the right-click context menu while the main window is hidden | The "Quit" menu click event was received and the tray icon removal and process termination proceed |

## Business Rules

- **Rule left-click-toggles-visibility:** IF the user left-clicks the
    tray icon AND the main window is currently visible THEN the window
    hides, and IF the main window is currently hidden THEN the window
    shows and receives keyboard focus via `setFocus()`
- **Rule right-click-opens-context-menu:** IF the user right-clicks
    the tray icon THEN a context menu with exactly 2 localized items
    ("Show" and "Quit") appears at the tray icon position — the count
    of menu items equals 2
- **Rule quit-terminates-process-and-removes-tray:** IF the user
    selects "Quit" from the context menu THEN the tray icon is removed
    from the OS notification area AND the main window closes AND the
    application process terminates — the count of remaining tray icons
    after quit equals 0
- **Rule close-button-quits-not-minimizes:** IF the user clicks the
    close button (X) on the application window THEN the application
    quits entirely — the tray icon is removed, the window closes, and
    the process terminates with no minimize-to-tray behavior
- **Rule tray-icon-lifetime-equals-app-lifetime:** IF the application
    process is running THEN the tray icon is visible in the OS
    notification area, and IF the application process terminates THEN
    the tray icon is absent from the notification area — the tray icon
    exists for exactly the duration of the process lifetime

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User | Left-click the tray icon to toggle window visibility, right-click the tray icon to open the context menu, select "Show" to bring the window to the foreground, select "Quit" to terminate the application, and click the close button (X) to quit | No actions are denied to the user — all tray icon interactions and window close actions are unrestricted because the desktop application runs under the user's OS session | The tray icon is visible in the OS notification area for the entire application lifetime, the context menu appears on right-click, and the main window visibility toggles on left-click |
| OS | Provides the notification area (Windows taskbar system tray or macOS menu bar) for hosting the tray icon, dispatches click events to the Tauri backend, and renders the context menu at the tray icon position | The OS does not initiate tray icon actions or modify the application window state without a user-initiated event — all state changes originate from user clicks on the tray icon or window controls | The OS renders the tray icon and context menu according to platform conventions and visual styling (icon size, menu appearance, notification area placement) |

## Constraints

- The tray icon is registered with the OS notification area during
    application startup and remains visible until the application
    process terminates — the count of tray icons present while the
    application is running equals exactly 1.
- The context menu contains exactly 2 items: "Show" and "Quit" — the
    count of context menu items equals 2 and no additional items are
    present in the menu.
- The context menu labels "Show" and "Quit" are rendered via @repo/i18n
    translation keys — the count of hardcoded English strings in the
    tray context menu equals 0 when translations are loaded.
- The close button (X) on the application window terminates the
    process entirely — the count of minimize-to-tray behaviors on
    window close equals 0.
- Left-click toggle latency from click to window visibility change is
    under 100 ms — the window hides or shows within 100 ms of the
    tray icon left-click event being received by the Tauri backend.
- The tray icon is removed from the OS notification area before
    process exit — the count of orphaned tray icons remaining after
    the application process terminates equals 0.

## Acceptance Criteria

- [ ] When the desktop application launches, a tray icon appears in the OS notification area — the count of tray icons registered by the application equals 1
- [ ] The tray icon remains visible in the notification area for the entire application lifetime — the icon is present from startup until process termination
- [ ] Left-clicking the tray icon while the window is visible hides the window — `appWindow.isVisible()` returns false after the left-click event
- [ ] Left-clicking the tray icon while the window is hidden shows the window and gives it focus — `appWindow.isVisible()` returns true and the window has keyboard focus
- [ ] Right-clicking the tray icon opens a context menu with exactly 2 items — the menu item count equals 2 and the items are labeled "Show" and "Quit"
- [ ] The context menu labels "Show" and "Quit" are localized via @repo/i18n translation keys — the count of hardcoded English strings in the menu equals 0
- [ ] Selecting "Show" from the context menu brings the window to the foreground — `appWindow.isVisible()` returns true and `appWindow.isFocused()` returns true after selecting "Show"
- [ ] Selecting "Quit" from the context menu removes the tray icon and terminates the process — the tray icon is absent from the notification area and the process exit code equals 0
- [ ] Clicking the close button (X) on the window quits the application entirely — the tray icon is removed, the window closes, and the process terminates with exit code 0
- [ ] There is no minimize-to-tray behavior when the close button (X) is clicked — the count of minimize-to-tray actions triggered by the close button equals 0
- [ ] The tray icon is cleaned up on process exit — the count of orphaned tray icons remaining in the notification area after termination equals 0
- [ ] Left-click window toggle completes within 100 ms of the tray icon click event — the elapsed time from click event to visibility state change is under 100 ms

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user left-clicks the tray icon rapidly multiple times within 200 ms, sending consecutive toggle events | Each click event is processed sequentially and the final window visibility state matches the expected toggle result for the total number of clicks — an even count leaves the window in its original state, an odd count toggles it | The window visibility state after rapid clicks matches the parity of the click count and no intermediate state corruption occurs |
| The user right-clicks the tray icon while the context menu is already open from a previous right-click | The existing context menu closes and a new context menu opens at the current tray icon position — the count of simultaneously visible context menus equals 1 | Exactly 1 context menu is visible after the second right-click and the menu items are correct |
| The user selects "Show" from the context menu while the window is already visible and in the foreground | The window remains visible and receives focus via `setFocus()` without any flickering or hide-then-show sequence — the visibility state does not change | `appWindow.isVisible()` returns true before and after the "Show" selection and no visibility state transition occurs |
| The OS notification area is full or the tray icon registration fails during application startup | The application launches without a tray icon and the user controls the window exclusively through the title bar close button (X) and OS taskbar — the application logs a warning indicating tray icon registration failed | The application process is running, the main window is visible, and a warning log entry is present indicating tray registration failure |
| The application process crashes or is forcefully killed by the OS task manager | The OS reclaims the notification area slot and removes the tray icon automatically as part of process cleanup — no orphaned icon remains | The tray icon is absent from the notification area after the process is no longer running |
| The user unplugs an external monitor where the application window was displayed while the tray icon is in the primary monitor notification area | The window repositions to the primary display bounds on the next show action triggered by left-click or "Show" menu selection — the tray icon remains in the primary notification area unaffected | The window is visible on the primary display after the show action and the tray icon remains present |

## Failure Modes

- **Tray icon registration fails during application startup because the OS notification area is unavailable**
    - **What happens:** The Tauri tray icon builder API attempts to
        register the icon with the OS notification area during startup
        but the registration call returns an error because the
        notification area service is unavailable or the icon resource
        cannot be loaded from the application bundle.
    - **Source:** OS notification area service is not running, the
        icon asset file is missing from the Tauri application bundle,
        or the platform does not support system tray icons in the
        current desktop environment configuration.
    - **Consequence:** The application launches without a tray icon
        and the user cannot toggle window visibility via left-click or
        access the context menu via right-click, losing the persistent
        access point for window control and application termination
        from the notification area.
    - **Recovery:** The application logs a warning with the
        registration error details and falls back to operating without
        a tray icon — the user controls the application through the
        standard window title bar close button (X) and OS taskbar
        interactions for the remainder of the session.

- **Window visibility IPC call fails when the user left-clicks the tray icon to toggle the window state**
    - **What happens:** The Tauri backend receives the left-click
        event on the tray icon and calls `appWindow.show()` or
        `appWindow.hide()` via IPC, but the IPC call returns an error
        and the window remains in its previous visibility state
        instead of toggling as expected by the user.
    - **Source:** The IPC channel between the Tauri Rust backend and
        the webview frontend is interrupted, or the window handle has
        become invalid due to an internal state inconsistency in the
        Tauri window manager after a display configuration change.
    - **Consequence:** The window does not toggle visibility and the
        user sees no response to their tray icon click, creating a
        perception that the application is frozen or unresponsive to
        tray interactions.
    - **Recovery:** The Tauri backend logs the IPC error with the
        attempted operation (show or hide) and the window handle
        identifier — the user retries the left-click action which
        triggers a fresh IPC call, and if the failure persists the
        user falls back to using the OS taskbar to access the window.

- **Context menu construction fails and the right-click menu does not appear when the user right-clicks the tray icon**
    - **What happens:** The Tauri backend receives the right-click
        event and attempts to build the context menu with localized
        labels from @repo/i18n, but the menu construction or display
        call fails and no context menu appears for the user.
    - **Source:** The @repo/i18n translation namespace fails to load
        the localized labels for "Show" and "Quit", or the Tauri
        context menu API encounters a platform-specific error when
        attempting to display the native menu at the tray icon
        position on the current OS.
    - **Consequence:** The user cannot access the "Show" or "Quit"
        options from the tray icon right-click menu, losing the
        ability to explicitly show the window or quit the application
        from the tray context menu.
    - **Recovery:** The Tauri backend catches the menu construction
        error and logs a warning with the failure details — the user
        falls back to left-clicking the tray icon for window
        visibility toggle and clicking the close button (X) on the
        window title bar to quit the application entirely.

## Declared Omissions

- This specification does not define the visual design, dimensions,
    or asset format of the tray icon image — those details are covered
    by the Tauri application bundle configuration and platform-specific
    icon guidelines for Windows and macOS notification areas.
- This specification does not cover tray icon tooltip text or balloon
    notification behavior — the tray icon displays no tooltip on hover
    and no balloon notifications are sent from the tray icon in this
    implementation.
- This specification does not address minimize-to-tray on window close
    because the design decision is to quit entirely on close — a future
    spec would be required to add minimize-to-tray behavior if the
    product requirements change to support background operation.
- This specification does not cover Linux desktop environments because
    the current desktop target supports only Windows and macOS — Linux
    tray icon support varies by desktop environment and would require
    a dedicated spec addressing freedesktop.org system tray protocols.
- This specification does not define keyboard shortcuts or hotkeys for
    showing or hiding the application window — global hotkey support
    for window toggle is a separate feature that would require its own
    spec covering OS-level keyboard shortcut registration and conflict
    handling.

## Related Specifications

- [user-changes-theme](user-changes-theme.md) — defines the theme
    switching mechanism for the desktop application webview content,
    including the OS-rendered title bar visual mismatch behavior that
    applies when the tray icon is managing window visibility
- [user-navigates-the-dashboard](user-navigates-the-dashboard.md) —
    defines the dashboard shell and navigation structure that the user
    interacts with when the tray icon "Show" action brings the main
    window to the foreground and focuses it
- [session-lifecycle](session-lifecycle.md) — defines the
    authentication session management that governs whether the user
    has an active session when the application is running and the tray
    icon is present in the notification area
- [user-changes-language](user-changes-language.md) — defines the
    language switching mechanism that determines the locale used by
    @repo/i18n when rendering the localized "Show" and "Quit" labels
    in the tray icon context menu

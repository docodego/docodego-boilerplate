# Desktop App (Tauri)

## Core Principle

The desktop app is not a second frontend. It is a thin Tauri 2 shell that wraps the same web app running in `apps/web`. All UI, routing, state management, and business logic come from the web codebase. The Tauri layer provides native OS integration -- window management, system tray, deep links, auto-updates, and shell access -- but renders no UI of its own.

---

## App Launch

The user double-clicks the `.exe` on Windows or opens the `.app` from the `.dmg` on macOS. The Tauri runtime starts and opens a native window. Inside that window, it loads the web app.

The window opens at the size and position the user last used. The Window-State plugin remembers these values between sessions, so if the user moved the window to their second monitor and made it half-screen last time, it comes back exactly like that.

There is no browser chrome. No address bar, no tabs, no navigation buttons. The app looks and feels like a native desktop application. The title bar is the OS-native title bar with minimize, maximize, and close buttons.

---

## System Tray

When the app launches, a tray icon appears in the OS system tray (the notification area on Windows, the menu bar on macOS).

Clicking the tray icon toggles the main window's visibility. If the window is hidden or minimized, clicking the tray icon brings it to the front. If the window is already visible and focused, clicking the tray icon hides it.

Right-clicking the tray icon opens a context menu with basic options like "Show" and "Quit." Selecting "Quit" closes the application entirely and removes the tray icon.

---

## Deep Linking

The desktop app registers a custom URL scheme: `docodego://`. Any link in the OS that starts with this scheme is intercepted by the Tauri app.

For example, the user receives a link like `docodego://app/docodego/members` in an email or chat message. They click it. The OS recognizes the `docodego://` scheme and hands the URL to the Tauri app. Tauri receives the deep link, extracts the path (`/app/docodego/members`), and forwards it to TanStack Router inside the web app. The app navigates to that route as if the user had clicked a link within the app itself.

This also works for OAuth callbacks. When the user signs in with an external provider (SSO), the browser opens to complete the OAuth flow. Once authentication succeeds, the provider redirects to `docodego://auth/callback?...`. The OS routes this back to the Tauri app, which passes the callback URL to the auth handler. The user ends up signed in inside the desktop app without having to copy-paste tokens or switch windows manually.

---

## Desktop-Specific UI Indicators

The web app detects whether it is running inside Tauri by checking for the `window.__TAURI__` global. This object exists when the app is loaded in a Tauri webview and is absent in a normal browser.

When running inside Tauri:

- The settings page shows an **"App Version"** line. The web app calls the `get_app_version()` IPC command to query the Tauri backend for the version string (e.g., "1.2.0") and displays it.
- A tray status indicator may appear in the UI to confirm the system tray is active.

When running in a normal browser, these desktop-specific elements are hidden entirely. The user never sees references to features that do not apply to their environment.

---

## External Links

When the user clicks a link that points to an external URL (outside the app), the link opens in the user's default OS browser, not inside the Tauri window. The Shell plugin handles this. Internally, the web app calls the shell plugin's open function, which delegates to the OS to launch the URL in whatever browser the user has set as default.

This keeps the Tauri window focused on the app. The user is not navigated away from their workflow.

For OAuth sign-in flows, the same mechanism applies: the browser opens to the identity provider's login page. After the user authenticates, the callback deep link (`docodego://...`) brings them back to the desktop app.

---

## IPC Commands

The web app can call a small set of Tauri backend commands from JavaScript:

- **`show_window()`** -- brings the Tauri window to the front and gives it focus. Useful if the app needs to surface itself after a background event (like receiving a deep link while minimized).
- **`quit_app()`** -- closes the application. The tray icon is removed and the process exits.
- **`get_app_version()`** -- returns the app's version string as defined in the Tauri configuration. The web app uses this to display version info in the settings page.

These commands are only available when `window.__TAURI__` exists. The web app should guard all IPC calls behind that check so they are never invoked in a browser context.

---

## Auto-Updates

The Tauri Updater plugin checks a configured release server for new versions. The developer sets the update URL in the Tauri configuration, pointing to wherever release manifests are hosted.

When the app launches (or at a configured interval), the updater checks for a newer version. If one is found, the user sees a prompt -- either a system-native dialog or an in-app notification -- telling them an update is available. The user can accept or dismiss.

If the user accepts, the update is downloaded and applied. Depending on platform and configuration, the app may restart automatically or prompt the user to restart. After restart, the user is running the new version.

If the user dismisses the update prompt, the app continues running the current version. The updater will check again on the next launch or interval.

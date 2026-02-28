[← Back to Index](README.md)

# User Opens a Deep Link

## The user clicks a deep link

The application registers the custom URL scheme `docodego://` with the operating system via the Tauri Deep-Link plugin. When the user clicks a link like `docodego://app/docodego/members` anywhere in the OS, whether in an email, a chat message, a browser, or another application, the OS recognizes the `docodego://` scheme and hands the URL to the Tauri application.

## The app navigates to the linked route

Tauri receives the URL and extracts the path portion, in this example `/app/docodego/members`. It forwards this path to TanStack Router inside the webview, which navigates to that route as if the user had clicked a link within the application itself. The user sees the target page load with all the expected data and UI state. If the app was minimized or hidden when the deep link was clicked, the `show_window()` IPC command is called to bring the window to the foreground so the user can see the result immediately.

## Deep links handle OAuth callbacks

Deep links also serve a critical role in the OAuth sign-in flow. When the user [signs in via SSO](user-signs-in-with-sso.md), the browser opens to complete the authentication with the external provider. Once the provider confirms the user's identity, the browser redirects to `docodego://auth/callback?...` with the necessary tokens and parameters. The OS routes this back to the Tauri app, which hands it to the auth handler. The auth handler processes the callback, establishes the session, and the user is signed in without needing to manually copy tokens or switch between windows.

## Desktop-only detection

Deep link handling only applies when the application is running as a Tauri desktop app. The web application detects the desktop environment by checking for the presence of `window.__TAURI__`. When this global is present, the app knows it is running inside Tauri and can register deep link listeners and invoke IPC commands. In a regular browser, `window.__TAURI__` does not exist, and deep link registration is skipped entirely.

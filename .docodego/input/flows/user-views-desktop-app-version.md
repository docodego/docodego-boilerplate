[← Back to Index](README.md)

# User Views Desktop App Version

## Navigating to the About Section

The user opens the settings area within the desktop app. At the bottom of the settings page, a localized "About" section displays application information. This section is only visible when the app detects it is running inside Tauri by checking for the presence of `window.__TAURI__` — it does not appear in the regular web application.

## Displaying the Version

On render, the about section calls the `get_app_version` IPC command, which returns the current application version string from the Tauri binary's `tauri.conf.json`. The version is displayed alongside the application name — for example, "DoCodeGo Desktop v1.2.0." The version shown here matches the version of the installed binary, not the web application bundle, so the user can confirm whether their [auto-update](desktop-auto-updates.md) applied successfully.

## Checking for Updates

Next to the version display, a localized "Check for updates" link allows the user to manually trigger the [auto-update](desktop-auto-updates.md) check. If an update is available, the update prompt appears as described in the auto-update flow. If the app is already on the latest version, a brief localized message confirms that no update is available.

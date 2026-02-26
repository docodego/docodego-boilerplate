[← Back to Index](README.md)

# Desktop Auto-Updates

## The app checks for updates

The Tauri Updater plugin is configured with a release server URL specified in the Tauri configuration. When the user launches the desktop application, the updater plugin automatically checks this server for a newer version. The check compares the currently installed version against the latest version available on the server. This check can also be configured to run at a regular interval while the app is running, not just at launch.

## A new version is available

If the server reports a newer version, the user is presented with an update prompt. This can take the form of a system dialog or an in-app notification, depending on how the developer has configured the update flow. The localized prompt informs the user that a new version is available and asks whether they want to update now.

## The user accepts or dismisses the update

If the user accepts the update, the application downloads the new version from the release server and applies it. Once the download and installation are complete, the app may restart automatically to load the new version. The user is now running the latest release.

If the user dismisses the prompt, nothing happens. They continue using their current version without interruption. The updater will check again the next time the app is launched, or at the next configured check interval, giving the user another opportunity to update.

[← Back to Index](README.md)

# Desktop Sends a Notification

## Permission Request

The first time the Tauri desktop application needs to send an OS-native notification, it requests notification permission from the operating system via `tauri-plugin-notification`. The OS presents its standard permission prompt asking the user whether to allow notifications from the application. If the user grants permission, notifications are enabled for the current and all future sessions. If the user denies permission, the application silently skips sending notifications and does not prompt again — the user would need to re-enable notifications through their OS settings.

## When Notifications Are Sent

The desktop application sends notifications in response to specific events that the user should know about even when the app is not in the foreground. These events include: an [invitation](user-accepts-an-invitation.md) has been received for the user to join an organization, the user's current session is about to expire and they should re-authenticate soon, and a new [application update](desktop-auto-updates.md) is available for download. Each notification includes a title and a brief body message describing the event.

## Notification Appearance

Notifications are rendered by the operating system's native notification system, not by the application itself. On macOS they appear in Notification Center, on Windows they appear in the Action Center, and on Linux they appear through the desktop environment's notification daemon. The notification displays the application icon, a title summarizing the event, and a short body with relevant details such as the organization name for an invitation or the version number for an update.

## User Clicks the Notification

When the user clicks on a notification, the Tauri application is brought to the foreground. The application then navigates the user to the page relevant to the notification's event. For an invitation notification, the user is taken to the invitation acceptance page. For a session expiry warning, the user is taken to the sign-in page. For an update notification, the user is shown the update prompt. If the application was closed when the notification was clicked, it launches and navigates to the relevant page after startup completes.

## Notifications While the App Is in Focus

When the application is already in the foreground and focused, OS-native notifications are suppressed. Instead, the relevant event is communicated through the application's in-app notification system, such as a toast or banner within the UI. This avoids redundant alerts when the user is already looking at the application.

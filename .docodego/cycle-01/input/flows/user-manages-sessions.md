[← Back to Index](README.md)

# User Manages Sessions

## Viewing Active Sessions

The user navigates to the security settings page at `/app/settings/security`. The active sessions section loads the user's sessions by calling `authClient.listSessions()`. The result is displayed as a table with localized column headers where each row shows the session's user agent (browser and operating system), the date the session was created, and an actions column.

## Identifying the Current Session

The session the user is currently using is marked with a "Current" badge. This session does not have a revoke button — the user cannot terminate the session they are actively using from this interface. All other sessions display a "Revoke" button in the actions column.

## Revoking Individual Sessions

To terminate a specific session, the user clicks the "Revoke" button on that row. The client calls `authClient.revokeSession({ token })` with the session's token. The server invalidates the session immediately and the sessions list refreshes to remove the revoked entry. If another device or browser was using that session, the user on that device will be signed out on their next request to the server.

## Revoking All Other Sessions

When the user has more than one session active, a "Revoke all other sessions" button appears. Clicking it calls `authClient.revokeOtherSessions()`, which terminates every session except the current one. All other devices and browsers where the user was signed in will be signed out on their next server request. The sessions list refreshes to show only the current session remaining.

## Desktop Behavior

On the desktop app, the session recorded in the `session` table carries the Tauri webview's user agent string rather than a standard browser user agent. Desktop sessions may appear with a less familiar user agent compared to recognizable names like "Chrome" or "Firefox." The sessions list UI should parse the user agent and display a friendly label like "DoCodeGo Desktop" for Tauri sessions rather than the raw user agent string, so the user can easily identify which session belongs to their desktop app.

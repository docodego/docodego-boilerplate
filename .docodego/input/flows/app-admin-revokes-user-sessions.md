[← Back to Index](README.md)

# App Admin Revokes User Sessions

## The app admin locates the user

The app admin navigates to the user management section of the app admin dashboard. This view [lists all registered users](app-admin-lists-and-searches-users.md) with their current status, role, and account details. The app admin searches for or scrolls to the user whose sessions they need to review, then selects that user to open their profile detail view. Within the profile detail view, the app admin clicks on a "Sessions" tab or section to view the user's active sessions.

## The app admin reviews the user's active sessions

The sessions section loads by calling `authClient.admin.listUserSessions({ userId })`. The result is displayed as a table where each row represents one active session. Each row shows the session's IP address, user agent (browser and operating system), and the date and time the session was last active. This gives the app admin visibility into where and how the user is currently signed in — useful for identifying suspicious activity such as sessions from unexpected locations or unfamiliar devices.

## The app admin revokes an individual session

To terminate a specific session, the app admin clicks the "Revoke" button on that row. The client calls `authClient.admin.revokeUserSession({ sessionToken })` with the session's token. The server invalidates that session immediately, and the sessions list refreshes to remove the revoked entry. If the user was actively browsing on the device associated with that session, they will be signed out on their next request to the server. This is useful when the app admin can identify a single compromised session without needing to disrupt the user's other devices.

## The app admin revokes all sessions

When the situation calls for a broader response — for example, a potentially compromised account — the app admin can click the "Revoke all sessions" button instead of terminating sessions one by one. This calls `authClient.admin.revokeUserSessions({ userId })`, which invalidates every active session belonging to that user at once. The sessions list refreshes to show an empty state. The user is signed out everywhere and must sign in again on any device they want to use. Unlike [banning a user](app-admin-bans-a-user.md), revoking all sessions does not prevent the user from signing back in — it simply forces re-authentication, which is the appropriate response when credentials may be compromised but the user themselves is not at fault.

## The action is audit logged

Each session revocation — whether individual or bulk — is recorded in the audit log. The log entry captures which app admin performed the action, which user's sessions were affected, whether it was a single revocation or a bulk revocation, and the timestamp. This creates a clear record of administrative security interventions for compliance and review.

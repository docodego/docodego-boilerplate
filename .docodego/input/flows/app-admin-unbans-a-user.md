[← Back to Index](README.md)

# App Admin Unbans a User

## The app admin locates the banned user

The app admin navigates to the user management section of the app admin dashboard. Banned users are visually distinguishable in the user list, marked with a banned status indicator. The app admin finds the specific banned user they want to reinstate, either by searching, filtering by banned status, or scrolling through the list, and selects them to open their profile detail view.

## The app admin unbans the user

From the banned user's profile, the app admin clicks the "Unban" action button. A confirmation prompt appears to prevent accidental unbans. The app admin confirms the action, and the client calls `authClient.admin.unbanUser({ userId })`. The server receives this request, verifies the caller has the app admin role (`user.role = "admin"`), and then clears the ban-related fields on the user's record: `user.banned` is set to `false`, and both `user.banReason` and `user.banExpires` are cleared.

## The user can sign in again

With the ban lifted, the user can now sign in normally through any of the available authentication methods. There is no special "welcome back" flow or forced password reset. The user simply signs in as they would under normal circumstances, and the application behaves as if the ban never existed. If the user had a temporary ban that was manually lifted early, the same outcome applies: all ban fields are cleared regardless of whether the original expiration date had been reached.

## The action is audit logged

The unban action is recorded in the audit log, capturing which app admin performed the unban, which user was unbanned, and the timestamp. This maintains a complete moderation history alongside the original ban record.

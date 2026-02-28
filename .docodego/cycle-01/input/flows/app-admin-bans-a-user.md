[← Back to Index](README.md)

# App Admin Bans a User

## The app admin locates the user to ban

The app admin navigates to the user management section of the app admin dashboard. This view lists all registered users with their current status, role, and account details. The app admin searches for or scrolls to the specific user they need to ban, then selects that user to open their profile detail view. From here, the app admin clicks the "Ban" action button, which opens a ban configuration form.

## The app admin configures the ban

The ban form presents two optional fields with localized labels: a free-text reason field where the app admin can describe why the user is being banned, and an expiration date picker. If the app admin sets an expiration date, the ban is temporary and will automatically lift when that date arrives. If the app admin leaves the expiration date empty, the ban is permanent and will remain in effect until manually removed by an app admin. The app admin fills in the details and confirms the action.

## The system processes the ban

When the app admin confirms, the client calls `authClient.admin.banUser({ userId, banReason, banExpires })`. The server receives this request, verifies the caller has the app admin role (`user.role = "admin"`), and then updates the target user's record: `user.banned` is set to `true`, `user.banReason` is stored with whatever text the admin provided, and `user.banExpires` is set to either the chosen date or `null` for a permanent ban. The server then immediately invalidates all active sessions belonging to the banned user.

## The banned user experiences the ban

Because all sessions are invalidated, the banned user's current browsing session fails on their very next API request. The client receives an authentication error, and the user is effectively signed out. If the banned user tries to sign in again, the sign-in flow checks the `user.banned` field and rejects the attempt, displaying a ban error message that includes the ban reason if one was provided. The user cannot access any authenticated part of the application until the ban is lifted, either by expiration or by an app admin manually [unbanning them](app-admin-unbans-a-user.md).

## The action is audit logged

The entire ban action is recorded in the audit log, capturing which app admin performed the ban, which user was banned, the reason provided, the expiration setting, and the timestamp. This creates a clear accountability trail for all administrative moderation actions.

[← Back to Index](README.md)

# App Admin Impersonates a User

## The app admin initiates impersonation

The app admin is handling a support request or debugging an issue that requires seeing the application exactly as a specific user sees it. The app admin navigates to user management, selects the target user, and clicks the "Impersonate" action. The client calls `authClient.admin.impersonateUser({ userId })`. By default, app admins cannot impersonate other app admin-role users. This is controlled by the `allowImpersonatingAdmins: false` configuration, so if the target user has an admin role, the server rejects the request.

## The server creates an impersonation session

The server verifies the caller has the app admin role (`user.role = "admin"`) and that the target user is eligible for impersonation. It then creates a new session tied to the target user, but with the `session.impersonatedBy` field set to the app admin's own userId. This field is what distinguishes an impersonation session from a real one. The app admin's own original session is preserved so they can return to it later. The impersonation session has a default time limit of one hour, after which it automatically expires.

## The app admin sees the app as the target user

Once the impersonation session is active, the app admin's browser now operates under the target user's identity. The app admin sees the target user's dashboard, their organizations, their data, and their permissions. Everything the application renders is exactly what the target user would see. However, the UI displays a clear impersonation indicator: a persistent banner or floating badge with localized text that reads "Impersonating [user's name]" along with a stop button. This indicator is always visible so the app admin never loses awareness that they are operating under another user's identity.

## The app admin stops impersonation

When the app admin is done, they click the stop button on the impersonation indicator. The client calls `authClient.admin.stopImpersonating()`, which revokes the impersonation session and restores the app admin's original session. The app admin is returned to their own view of the application with their own identity, dashboard, and data. If the app admin does not explicitly stop, the impersonation session automatically expires after the one-hour time limit, at which point the app admin is returned to their own session.

## The action is audit logged

Both the start and end of impersonation are recorded in the audit log. The log captures which app admin impersonated which user, when the impersonation began, and when it ended, whether by manual stop or automatic expiration. This creates a complete accountability record for every impersonation event.

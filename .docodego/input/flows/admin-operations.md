# Admin Operations

## Admin Role Context

Admin users are identified by `user.role = "admin"` in the database. The Better Auth admin plugin provides elevated API endpoints that only users with the admin role can call. If a non-admin user attempts to call any admin endpoint, the request is rejected with an authorization error.

Admin actions are audit-logged. When an admin bans a user, impersonates a user, or changes a role, the system records who did what and when.

---

## Banning a User

An admin navigates to a user management view and decides to ban a specific user. The admin interface provides a ban action with optional fields for a reason and expiration date.

When the admin submits the ban, the app calls `authClient.admin.banUser({ userId, banReason, banExpires })`. The `banReason` is a free-text string explaining why the user is being banned. The `banExpires` is an optional date -- if provided, the ban is temporary and lifts automatically after that date. If omitted, the ban is permanent.

On the server, the user's `banned` field is set to `true`. If provided, `banReason` and `banExpires` are stored on the user record. All of that user's active sessions are immediately invalidated. This means if the banned user is currently browsing the app, their very next request fails authentication, and they are effectively signed out.

When the banned user tries to sign in again (or makes any authenticated request), they see an error message indicating they have been banned. The system does not reveal the specific reason to the banned user unless the app is configured to show it.

To reverse a ban, the admin calls `authClient.admin.unbanUser({ userId })`. This clears the `banned` flag, `banReason`, and `banExpires` fields on the user record. The user can now sign in again normally.

---

## Impersonating a User

Sometimes an admin needs to see the app exactly as a specific user sees it -- to debug an issue, verify permissions, or investigate a support ticket.

The admin calls `authClient.admin.impersonateUser({ userId })`. The server creates a new session tied to the target user, but with the `impersonatedBy` field set to the admin's user ID. The admin's browser now operates under this impersonation session. From this point on, the admin sees everything the target user would see -- their dashboard, their organizations, their data.

The UI should display a clear visual indicator that the admin is in impersonation mode. This could be a banner at the top of the page or a floating badge showing "Impersonating [user name]" with a button to stop. This prevents the admin from accidentally taking actions they think are their own.

The impersonation session has a configurable time limit (default: 1 hour). After that, the session expires automatically and the admin is returned to their own context.

To end impersonation early, the admin clicks the stop-impersonation button, which calls `authClient.admin.stopImpersonating()`. The impersonation session is revoked and the admin is returned to their own session. They see the app as themselves again.

The admin cannot impersonate other admins by default. This is a safety guard configured on the server (`allowImpersonatingAdmins: false`).

---

## User Management

### Listing Users

The admin navigates to a user management page. The app calls `authClient.admin.listUsers()` to fetch a paginated list of all users. The response includes user records along with pagination metadata (total count, limit, offset).

The admin can search for users by name or email. Search supports operators like "contains," "starts with," and "ends with." The admin can also filter users by fields such as role or ban status, and sort results by creation date, name, or email.

The list displays each user's name, email, role, ban status, and creation date. Clicking on a user navigates to their detail view.

### Viewing User Details

The admin clicks on a specific user. The app calls `authClient.admin.getUserDetails()` with the user's ID. The detail view shows the full user record: name, email, role, ban status (with reason and expiry if banned), email verification status, creation date, and last updated date.

From this view, the admin can take actions on the user -- ban, unban, impersonate, change role, or remove.

### Creating a User

The admin clicks a "Create user" action. A form appears with fields for name, email, password, and role. The admin fills in the details and submits. The app calls `authClient.admin.createUser()` with the provided data. The new user is created in the database and appears in the user list. This is useful for provisioning accounts without the user going through the normal signup flow.

### Setting a User's Role

The admin selects a user and changes their role. The app calls `authClient.admin.setRole({ userId, role })` with the new role value (e.g., "admin" or "user"). The user's role is updated in the database. If the user is currently signed in, their session reflects the new role on the next request.

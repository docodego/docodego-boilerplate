[← Back to Index](README.md)

# App Admin Views User Details

## Navigating to the User Detail Page

The app admin opens the [user management list](app-admin-lists-and-searches-users.md) and clicks on a user row. The client navigates to a dedicated user detail page, passing the selected user's ID. The page calls `authClient.admin.listUsers()` (filtered to the specific user) to fetch the full user record from the server and displays a loading state until the data arrives.

## User Information Display

The detail page presents all stored fields for the selected user with localized labels. The display name, email address, and email verification status are shown at the top. Below that, the user's role is displayed as either "user" or "admin," and the `isAnonymous` flag is indicated if the account was created through anonymous authentication. The account creation date (`createdAt`) is formatted according to the app's locale settings.

## Ban Status

If the user is currently banned, a prominent localized banner is displayed showing the ban status, the reason provided by the app admin who issued the ban, and the expiration date if the ban is temporary. If the ban is permanent, the banner states that no expiry has been set. If the user is not banned, this section is either hidden or shows an "Active" status indicator.

## Active Sessions and Organization Memberships

The detail page includes a list of the user's active sessions, showing device or client information and when each session was created. Below the sessions list, the page displays every organization the user belongs to, along with the user's role within each organization. These lists give the app admin a complete picture of the user's current activity and affiliations before taking any administrative action.

## Available Actions

Action buttons are rendered based on the user's current state. If the user is not banned, a "Ban" button links to the [ban flow](app-admin-bans-a-user.md). If the user is currently banned, an "Unban" button links to the [unban flow](app-admin-unbans-a-user.md). An "Impersonate" button launches the [impersonate flow](app-admin-impersonates-a-user.md). A "Change Role" button opens the [role change flow](app-admin-changes-user-role.md). A "Revoke Sessions" button triggers the [session revocation flow](app-admin-revokes-user-sessions.md). A "Remove" button initiates the [user removal flow](app-admin-removes-a-user.md). An "Edit" button opens the [edit user details flow](app-admin-updates-user-details.md). Each button is only shown when the action is applicable to the user's current state, preventing impossible operations from being attempted.

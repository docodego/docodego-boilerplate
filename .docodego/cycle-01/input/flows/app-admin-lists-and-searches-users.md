[← Back to Index](README.md)

# App Admin Lists and Searches Users

## Accessing the User Management View

The app admin navigates to the user management section of the app admin dashboard. This page is only accessible to users with the app admin role (`user.role = "admin"`). The page loads by calling `authClient.admin.listUsers()` and presents a paginated table of all registered users in the system.

## The User Table

Each row in the table displays key information about a user with localized column headers: their name, email address, account status (active or banned), role (user or admin), and the date their account was created. If a user is currently banned, their row is visually distinguished — for example, with a badge or muted styling — so that banned accounts are immediately recognizable at a glance.

## Searching and Filtering

Above the table, a search input allows the app admin to filter users by name or email address. As the app admin types, the table updates to show only matching results. The search queries the server with the filter parameters, calling `authClient.admin.listUsers({ searchField, searchValue })` to retrieve the filtered set. The app admin can also filter by specific criteria such as role or ban status to narrow down the list further.

## Pagination

The user list is paginated to handle large numbers of registered users efficiently. Navigation controls at the bottom of the table allow the app admin to move between pages. The server returns users in batches using cursor-based or offset-based pagination, and the client fetches subsequent pages on demand. The current page position and total user count are displayed so the app admin knows where they are in the full list.

## Accessing User Actions

Each row in the table serves as an entry point to individual user management actions. The app admin can click on a user row or use action buttons within the row to perform operations such as [banning a user](app-admin-bans-a-user.md), [unbanning a user](app-admin-unbans-a-user.md), [impersonating a user](app-admin-impersonates-a-user.md), or [changing a user's role](app-admin-changes-user-role.md). These actions are covered in their own dedicated flows — the user list serves as the central hub from which all user-level administrative actions originate.

---
id: SPEC-2026-056
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Lists and Searches Users

## Intent

This spec defines the behavior when an app admin navigates to the user management section of the admin dashboard to view, search, and filter the full list of registered users. The app admin opens the user management page, which is restricted to users with `user.role = "admin"` — non-admin users and unauthenticated visitors are redirected away. On load, the client calls `authClient.admin.listUsers()` to fetch the first page of users from the server. The server returns a paginated batch of user records from the D1 database, and the client renders a table displaying each user's name, email, account status (active or banned), role (user or admin), and account creation date. All column headers and status labels are localized via `@repo/i18n`. A search input above the table allows the admin to filter users by name or email by calling `authClient.admin.listUsers({ searchField, searchValue })` with the filter parameters. Additional filters for role and ban status narrow the result set further. Pagination controls at the bottom of the table allow navigation between pages, with the current page position and total user count displayed. Each row serves as an entry point to individual user actions (ban, unban, impersonate, change role) covered in dedicated specifications.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth (`authClient.admin.listUsers()`) | read | On page load to fetch the initial paginated user list and on each search or filter change to fetch matching results | The client receives an HTTP 500 error response and falls back to displaying an empty table with a localized error message prompting the admin to retry the request |
| D1 (Cloudflare SQL) | read | Every `listUsers` call queries the user table with optional search filters, role filters, ban status filters, and pagination parameters | The server returns an HTTP 500 error because the database query fails, and the client falls back to displaying an empty table state with the error message |
| `@repo/i18n` | read | Rendering all column headers, status badges, filter labels, pagination controls, and error messages on the user management page | The client falls back to the default English locale strings so the page remains functional but untranslated for non-English users |
| `@repo/contracts` | read | Compile time — the `listUsers` request parameters and response shape are defined in the shared contracts package for type-safe API communication | The build fails at compile time because the request and response types cannot be resolved, and CI alerts to block deployment |

## Behavioral Flow

1. **[App Admin]** → the app admin navigates to the user management section of the admin dashboard by selecting the user management link from the admin navigation menu
2. **[Client — Route Guard]** → the client-side route guard checks that the current user has `user.role = "admin"` before rendering the page — if the user does not have the admin role, the client redirects them to the main dashboard and does not render the user management page
3. **[Client — Initial Load]** → the client calls `authClient.admin.listUsers()` with no filter parameters and the default pagination offset of 0 to fetch the first page of registered users from the server
4. **[Server — Query Execution]** → the server receives the `listUsers` request, validates that the requesting user has the admin role, queries the D1 user table with the default sort order (creation date descending), and returns the first batch of user records along with the total user count and pagination cursor
5. **[Client — Table Render]** → the client renders the user table with localized column headers (name, email, status, role, created date) — each row displays the user's data, and rows for banned users are visually distinguished with a colored badge or muted row styling so that banned accounts are immediately recognizable
6. **[Client — Pagination Display]** → the client renders pagination controls below the table showing the current page position, total user count, and navigation buttons for moving between pages — the admin can see where they are in the full list
7. **[App Admin — Search]** → the app admin types into the search input above the table to filter users by name or email address — as the admin types, the client debounces the input and calls `authClient.admin.listUsers({ searchField, searchValue })` with the entered filter parameters
8. **[Server — Filtered Query]** → the server receives the filtered `listUsers` request, applies the search field and search value as a case-insensitive partial match against the user table, resets pagination to the first page, and returns the matching user records with an updated total count
9. **[Client — Filtered Results]** → the client replaces the table contents with the filtered result set and updates the pagination controls to reflect the new total count and page position
10. **[App Admin — Additional Filters]** → the app admin selects additional filter criteria such as role (user or admin) or ban status (active or banned) from filter controls above the table — the client combines these with any active search query and calls `authClient.admin.listUsers()` with all active filter parameters
11. **[Server — Combined Filter Query]** → the server applies all filter parameters (search text, role filter, ban status filter) together in a single query against the D1 user table and returns the matching paginated results
12. **[Client — Updated Results]** → the client updates the table and pagination controls to reflect the combined filter results, maintaining all active filters visually indicated in the filter controls
13. **[App Admin — Page Navigation]** → the app admin clicks a pagination control to navigate to the next or previous page — the client calls `authClient.admin.listUsers()` with the current filter parameters and the new pagination offset to fetch the requested page
14. **[App Admin — Row Action Entry]** → the app admin clicks on a user row or an action button within the row to initiate a user-level administrative action such as banning, unbanning, impersonating, or changing the user's role — these actions are handled by their dedicated specification flows

## State Machine

No stateful entities are introduced by this flow. The user management page is a read-only listing view — it queries the user table but does not modify any user records. Filter and pagination state is transient client-side state that resets on page navigation and does not persist to the server or database.

## Business Rules

- **Rule app-admin-role-required:** IF the current user has `user.role = "admin"` THEN the client renders the user management page and the server processes `listUsers` requests; IF the current user does not have `user.role = "admin"` THEN the client redirects to the main dashboard and the server returns HTTP 403 for `listUsers` requests
- **Rule banned-visual-distinction:** IF a user record in the table has `user.banned` equals true THEN the client renders that row with a visually distinct banned indicator (colored status badge and muted row styling) so banned accounts are immediately recognizable at a glance
- **Rule search-server-side:** IF the app admin enters text in the search input THEN the client sends the search parameters to the server via `authClient.admin.listUsers({ searchField, searchValue })` and the server performs the filtering in the D1 query — the client does not perform client-side filtering of previously fetched results
- **Rule paginated-results:** IF the total number of user records exceeds the page size THEN the server returns results in paginated batches and includes the total count and pagination cursor in the response so the client can render navigation controls and fetch subsequent pages on demand

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin (`user.role = "admin"`) | View the user management page, list all registered users, search users by name or email, filter by role or ban status, navigate between pages, click into individual user actions | Modify user records directly from the list view — all modifications are handled by dedicated action flows | Full visibility of all user records including name, email, role, ban status, and creation date for every registered user in the system |
| User (`user.role = "user"`) | None — the route guard redirects to the main dashboard before the page renders, and the server rejects `listUsers` requests with HTTP 403 | View the user management page, list users, search users, filter users, access any admin-only endpoint | No visibility of the user management page or any user listing data because the redirect occurs before any data is fetched |
| Unauthenticated | None — the authentication guard redirects to the sign-in page before the route guard is evaluated | All actions on the user management page are denied because the visitor is redirected to sign-in before reaching the admin route guard | No visibility of any authenticated content because the redirect to sign-in occurs before any page content is rendered |

## Constraints

- The user management page is server-filtered and server-paginated — the client never holds the full user list in memory. All search, filter, and pagination operations produce a new server request to `authClient.admin.listUsers()` with the relevant parameters, and the client renders only the current page of results.
- The search input is debounced on the client before sending the request to the server — the debounce interval prevents excessive API calls while the admin is still typing. The client does not send a request for every keystroke.
- The route guard check for `user.role = "admin"` is enforced on both client and server — the client-side route guard prevents rendering the page for non-admin users, and the server-side middleware independently validates the admin role on every `listUsers` request, returning HTTP 403 if the role check fails.
- Column headers, status labels, filter labels, and pagination text are rendered via `@repo/i18n` translation keys — the count of hardcoded English strings in the user management page component equals 0.
- The user table displays a maximum of one page of results at a time — the page size is a fixed constant defined in the server configuration, not a user-adjustable parameter.

## Acceptance Criteria

- [ ] The user management page renders only when the current user has `user.role = "admin"` — non-admin users are redirected to the main dashboard and the page component is absent from the DOM
- [ ] On page load, the client calls `authClient.admin.listUsers()` and the table displays the first page of user records with columns for name, email, status, role, and created date — the count of visible columns equals 5
- [ ] Each row for a user with `user.banned` equals true displays a visually distinct banned indicator (status badge) that is absent from rows where `user.banned` equals false
- [ ] The search input filters users by name or email by calling `authClient.admin.listUsers({ searchField, searchValue })` — the count of non-matching records in the server response equals 0
- [ ] The role filter narrows results to users with the selected role — when filtering by "admin", the count of non-admin users in the response equals 0
- [ ] The ban status filter narrows results to users with the selected status — when filtering by "banned", every record in the response has `user.banned` equals true
- [ ] Pagination controls display the current page position and total user count — navigating to page 2 calls `authClient.admin.listUsers()` with a non-empty offset or cursor parameter present in the request
- [ ] The server rejects `listUsers` requests from non-admin users with HTTP 403 — the response status code equals 403 and the response body contains no user records
- [ ] All column headers, status labels, filter labels, and pagination text are rendered via i18n translation keys — the count of hardcoded English strings in the user management page component equals 0
- [ ] The search input is debounced — typing 5 characters in rapid succession produces no more than 2 server requests for the search endpoint
- [ ] Clicking a user row or action button navigates to the relevant user action flow — the navigation target URL contains the selected user's identifier and is non-empty
- [ ] The table displays an empty state message when no users match the active search and filter criteria — the empty state element is present and the table body contains 0 data rows
- [ ] Unauthenticated visitors are redirected to the sign-in page before any user data is fetched — the count of `listUsers` API calls made by unauthenticated visitors equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The app admin searches for a string that matches zero users in the database because no registered user has that name or email address | The client displays a localized empty state message in the table body indicating no matching users were found, and the pagination controls show a total count of 0 | The empty state element is present in the DOM, the table body contains 0 data rows, and the total count display shows 0 |
| The app admin applies a role filter for "admin" combined with a search query, and the intersection of both filters returns an empty result set because no admin user matches the search text | The client displays the empty state message with both the role filter and search query visually indicated as active, and clearing either filter restores the previously filtered results | The empty state element is present, both filter indicators are visible, and removing one filter triggers a new `listUsers` request that returns non-empty results |
| The system has exactly one registered user (the current app admin viewing the page), and the admin searches for a different name that does not match their own record | The table shows the empty state with 0 results for the search query, and clearing the search restores the single-row table showing only the current admin's own user record | The total count equals 0 during the search and equals 1 after clearing the search, with the single row displaying the current admin's own data |
| The app admin navigates to the last page of a paginated user list, and another admin deletes or bans users on the previous page, causing the last page to become empty after a refresh | The client detects that the current page offset exceeds the new total count and falls back to displaying the last valid page of results rather than showing an empty page with a stale offset | The client issues a corrected `listUsers` request with an adjusted offset, and the table displays the actual last page of results with valid data rows |
| The server returns an HTTP 500 error when the app admin attempts to load the user list because the D1 database is temporarily unreachable | The client displays a localized error message in place of the table data and provides a retry button that re-calls `authClient.admin.listUsers()` when clicked by the admin | The error message element is present, the table body contains 0 data rows, and clicking the retry button triggers a new `listUsers` request |
| The app admin has an active search query and navigates to page 2, then clears the search input while on page 2 of the filtered results | The client resets pagination to page 1 and calls `authClient.admin.listUsers()` with no search parameters and an offset of 0, displaying the first page of the unfiltered user list | The pagination offset in the API request equals 0 and the search parameters are absent from the request after clearing the search input |

## Failure Modes

- **Server returns HTTP 500 when fetching user list due to D1 database connection failure**
    - **What happens:** The app admin loads the user management page or performs a search, but the server cannot connect to the D1 database to execute the user query.
    - **Source:** D1 database is temporarily unreachable due to Cloudflare infrastructure issues or a misconfigured database binding in the worker configuration.
    - **Consequence:** The user table cannot be populated, and the admin sees no user data on the page, blocking all listing, searching, and filtering operations.
    - **Recovery:** The client falls back to displaying a localized error message with a retry button, and the admin clicks retry to re-issue the `listUsers` request — the server logs the database connection error for infrastructure diagnostics.

- **Route guard bypass allows non-admin user to reach the user management page due to client-side role check desynchronization**
    - **What happens:** A non-admin user reaches the user management page because the client-side route guard reads a stale or incorrect role value from the local session cache, bypassing the intended admin-only restriction.
    - **Source:** The client session cache contains an outdated `user.role` value that has not been refreshed after a server-side role change by another admin.
    - **Consequence:** The non-admin user sees the user management page layout, but the server rejects the `listUsers` API request with HTTP 403 because the server-side middleware independently validates the admin role.
    - **Recovery:** The server rejects the request and returns error HTTP 403 with no user data, and the client receives the 403 response and redirects the user to the main dashboard — the server logs the unauthorized access attempt for admin review.

- **Search query returns stale results due to server-side caching of user list query responses**
    - **What happens:** The app admin searches for a user who was recently registered or whose data was recently updated, but the server returns cached results from a previous query that do not include the new or updated user record.
    - **Source:** An intermediate caching layer on the server or CDN caches the `listUsers` response and serves stale data for subsequent requests with the same query parameters.
    - **Consequence:** The admin cannot find the user they are looking for, leading to confusion and potentially incorrect administrative decisions based on outdated information.
    - **Recovery:** The `listUsers` endpoint returns error-free responses with a `Cache-Control: no-store` header to prevent intermediate caching, and the client degrades gracefully by allowing the admin to trigger a manual refresh that bypasses any client-side cache with a cache-busting query parameter.

- **Pagination offset exceeds total user count after concurrent user deletion by another admin**
    - **What happens:** The app admin is viewing the last page of the user list, and another admin deletes users from the system concurrently, reducing the total count so that the current page offset points beyond the end of the result set.
    - **Source:** Concurrent admin operations modify the user table between pagination requests, creating an inconsistency between the client's stored page offset and the server's current total count.
    - **Consequence:** The server returns an empty result set for the requested offset, and the admin sees an empty table page despite users still existing in the system.
    - **Recovery:** The server falls back to returning the last valid page of results when the requested offset exceeds the total count, and the client updates the pagination controls to reflect the corrected page position and new total count.

## Declared Omissions

- This specification does not define the behavior for banning a user from the list view — that action flow is fully specified in `app-admin-bans-a-user.md` and is accessed via the row action entry point
- This specification does not define the behavior for unbanning a user from the list view — that action flow is fully specified in `app-admin-unbans-a-user.md` and is accessed via the row action entry point
- This specification does not define the behavior for impersonating a user from the list view — that action flow is fully specified in `app-admin-impersonates-a-user.md` and is accessed via the row action entry point
- This specification does not define the behavior for changing a user's role from the list view — that action flow is covered in `app-admin-changes-user-role.md` and is accessed via the row action entry point
- This specification does not define the server-side sorting algorithm for the user table — sort order is creation date descending by default and does not require admin configuration in this specification

## Related Specifications

- [app-admin-bans-a-user](app-admin-bans-a-user.md) — Defines the admin workflow for banning a user, which is one of the row-level actions accessible from the user list table
- [app-admin-unbans-a-user](app-admin-unbans-a-user.md) — Defines the admin workflow for unbanning a previously banned user, which is one of the row-level actions accessible from the user list table
- [app-admin-impersonates-a-user](app-admin-impersonates-a-user.md) — Defines the admin workflow for impersonating a user to view the application from their perspective, accessed from the user list table
- [app-admin-changes-user-role](app-admin-changes-user-role.md) — Defines the admin workflow for changing a user's role between user and admin, accessed from the user list table row actions
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth plugin configuration and admin middleware that the `listUsers` endpoint integrates with for role-based access control
- [app-admin-creates-a-user](app-admin-creates-a-user.md) — Defines the admin workflow for creating a new user account via the admin dashboard, which adds a new entry to the user list displayed on the user management page

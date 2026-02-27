---
id: SPEC-2026-057
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Views User Details

## Intent

This spec defines the behavior when an app admin navigates to the user detail page to view comprehensive information about a specific user account. The app admin opens the user management list and clicks on a user row, causing the client to navigate to a dedicated detail page that calls `authClient.admin.listUsers()` filtered by the selected user's ID. The detail page displays the user's display name, email address, email verification status, role (user or admin), anonymous account indicator, account creation date formatted by locale, ban status with reason and expiration, active sessions with device information, and organization memberships with roles. Action buttons are rendered conditionally based on the user's current state: Ban or Unban (mutually exclusive based on ban status), Impersonate, Change Role, Revoke Sessions, Remove, and Edit. This spec ensures the admin has a complete picture of a user's account state, activity, and affiliations before taking any administrative action, and that impossible operations are prevented by conditionally hiding inapplicable action buttons.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.listUsers()` | read | The client calls this method filtered by user ID when the detail page mounts to fetch the full user record from the server | The detail page displays a localized error message and a retry button instead of user data, and logs the fetch failure to the client console for diagnostics |
| User table (D1 Cloudflare SQL) | read | The server queries the user table to retrieve all stored fields including display name, email, role, banned status, banReason, banExpires, isAnonymous, and createdAt | The server returns an HTTP 500 error response because the user record cannot be retrieved, and the client falls back to displaying the error state with a retry option |
| Session table (D1 Cloudflare SQL) | read | The server queries the session table to retrieve all active sessions for the selected user, including device or client information and session creation timestamps | The server returns the user record without session data, and the client falls back to displaying an empty sessions list with a localized message indicating sessions are temporarily unavailable |
| Member table (D1 Cloudflare SQL) | read | The server queries the member table to retrieve all organization memberships for the selected user, including the organization name and the user's role within each organization | The server returns the user record without membership data, and the client falls back to displaying an empty memberships list with a localized message indicating memberships are temporarily unavailable |
| `@repo/i18n` | read | The client uses i18n translation keys to render all labels, status indicators, ban banner text, date formats, and action button labels on the detail page | The client falls back to the default English locale strings so all labels and messages remain readable but untranslated for non-English users |

## Behavioral Flow

1. **[App Admin]** opens the user management list page and identifies the target user row within the displayed list of user accounts in the admin dashboard
2. **[App Admin]** clicks on the target user row, which triggers the client to capture the selected user's ID and initiate navigation to the dedicated user detail page
3. **[Client]** navigates to the user detail page route, passing the selected user's ID as a route parameter, and immediately renders a loading skeleton state while the data fetch is in progress
4. **[Client]** calls `authClient.admin.listUsers()` with a filter for the specific user ID to request the full user record, active sessions, and organization memberships from the server
5. **[Server]** receives the filtered `listUsers` request, verifies that the requesting user holds the app admin role, and queries the user table in D1 to retrieve all stored fields for the specified user ID
6. **[Server]** queries the session table in D1 to retrieve all active sessions for the specified user ID, including device or client information and the creation timestamp for each session record
7. **[Server]** queries the member table in D1 to retrieve all organization memberships for the specified user ID, including the organization name and the user's role within each organization
8. **[Server]** assembles the complete user detail response containing the user record fields, the list of active sessions, and the list of organization memberships, then returns it to the client as a JSON response
9. **[Client]** receives the user detail response and replaces the loading skeleton with the fully rendered detail page, displaying the user's display name, email address, and email verification status at the top of the page
10. **[Client]** renders the user's role as either "user" or "admin" using a localized label, and if the `isAnonymous` field equals true, displays a localized indicator showing that the account was created through anonymous authentication
11. **[Client]** formats the `createdAt` timestamp according to the app's locale settings using the native `Intl.DateTimeFormat` API and displays the formatted account creation date on the detail page
12. **[Client]** evaluates the `banned` field on the user record — if `banned` equals true, the client renders a prominent localized ban banner at the top of the detail page showing the ban status
13. **[Client]** within the ban banner, displays the `banReason` text if the field is non-null, and formats the `banExpires` timestamp using `Intl.DateTimeFormat` if the ban is temporary — if `banExpires` is null, the banner states that the ban is permanent with no expiry set
14. **[Client]** if the `banned` field equals false, the client either hides the ban section entirely or renders a localized "Active" status indicator to confirm the user is not currently banned
15. **[Client]** renders the list of active sessions in a dedicated section, displaying the device or client information string and the formatted session creation timestamp for each session entry
16. **[Client]** renders the list of organization memberships in a dedicated section below the sessions list, displaying the organization name and the user's role within each organization for every membership entry
17. **[Client]** renders action buttons conditionally based on the user's current state: if `banned` equals false, a "Ban" button is displayed; if `banned` equals true, an "Unban" button is displayed — these two buttons are mutually exclusive
18. **[Client]** renders the "Impersonate" button, the "Change Role" button, the "Revoke Sessions" button, the "Remove" button, and the "Edit" button — each button is only rendered when the action is applicable to the user's current state, preventing impossible operations from being attempted

## State Machine

| State | Entry Condition | Exit Condition | Visible Elements |
|-------|----------------|----------------|------------------|
| Loading | The client navigates to the user detail page and the data fetch request is in progress | The server response arrives and the client processes the user detail data successfully or an error is received | A loading skeleton placeholder is displayed in place of all user detail sections on the page |
| Loaded | The server response arrives with a valid user detail payload and the client finishes rendering all sections of the detail page | The app admin navigates away from the detail page or initiates a data refresh by triggering a page reload action | All user information sections, ban status, sessions list, memberships list, and conditional action buttons are displayed on the page |
| Error | The server returns an error response (HTTP 500 or network failure) during the data fetch or the response cannot be parsed by the client | The app admin clicks the retry button to re-initiate the data fetch request or navigates away from the detail page entirely | A localized error message is displayed with a retry button, and no user detail sections or action buttons are rendered on the page |

## Business Rules

- **Rule app-admin-role-required:** IF the requesting user does not hold the app admin role THEN the server rejects the `listUsers` request with an HTTP 403 response and the client redirects to the dashboard with a localized "access denied" notification
- **Rule ban-banner-conditional:** IF the `banned` field on the user record equals true THEN the client renders the ban banner with the ban reason (when `banReason` is non-null) and formatted expiration date (when `banExpires` is non-null), otherwise the client displays a permanent ban notice; IF `banned` equals false THEN the ban banner is hidden or replaced with an "Active" status indicator
- **Rule action-buttons-state-conditional:** IF the `banned` field equals false THEN the "Ban" button is rendered and the "Unban" button is hidden; IF the `banned` field equals true THEN the "Unban" button is rendered and the "Ban" button is hidden — Impersonate, Change Role, Revoke Sessions, Remove, and Edit buttons are rendered when their respective actions are applicable to the current user state
- **Rule isAnonymous-indicator:** IF the `isAnonymous` field on the user record equals true THEN the client renders a localized indicator adjacent to the user's identity section stating that the account was created through anonymous authentication; IF `isAnonymous` equals false THEN no anonymous indicator is rendered on the detail page

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin | View the full user detail page including all stored fields, active sessions, organization memberships, ban status with reason and expiry, and all applicable action buttons for the selected user | N/A — the app admin has full read access to the user detail page and all conditional action buttons are rendered based on user state | The app admin can see all user fields, all sessions, all memberships, and all action buttons applicable to the user's current state |
| User (non-admin) | N/A — no actions are permitted on the admin user detail page for non-admin users | View the admin user detail page, access the admin user management routes, call `authClient.admin.listUsers()`, and interact with any admin action buttons | The server returns HTTP 403 for the `listUsers` request and the client redirects away from the admin route to the user's own dashboard |
| Unauthenticated | N/A — no actions are permitted because the visitor has no authenticated session | Access any admin route, view any user detail page, call any admin API endpoint, and interact with any admin UI element | The client redirects the unauthenticated visitor to the sign-in page before any admin route is rendered or any admin API request is sent |

## Constraints

- The detail page calls `authClient.admin.listUsers()` filtered to a single user ID — the response contains exactly 1 user record, and the client does not display or process data for any other user in the system.
- All date and time values on the detail page are formatted using the native `Intl.DateTimeFormat` API according to the user's locale preference — the detail page does not use date-fns or any third-party date formatting library.
- The ban banner, action button labels, session labels, membership labels, and all static text on the detail page are rendered through `@repo/i18n` translation keys — the count of hardcoded English strings on the detail page equals 0.
- The "Ban" and "Unban" buttons are mutually exclusive on the detail page — the count of pages where both buttons are simultaneously visible equals 0 because the `banned` field is a boolean with exactly two possible states.
- The detail page renders action buttons only for operations applicable to the user's current state — no button triggers an API call that the server would reject based on the user's current state (for example, unbanning a user who is not banned).
- The admin role check is enforced server-side on the `listUsers` endpoint — the client-side route guard is a convenience redirect, not a security boundary, and the server independently verifies the admin role on every request.

## Acceptance Criteria

- [ ] When the app admin clicks a user row in the management list, the client navigates to the detail page with the selected user's ID present as a route parameter
- [ ] The detail page calls `authClient.admin.listUsers()` filtered by user ID and displays a loading skeleton until the response arrives — the loading state element is present and visible before data is received
- [ ] The detail page displays the user's display name, email address, and email verification status (true or false) at the top of the page — all 3 fields are present and non-empty in the rendered output
- [ ] The user's role is displayed as either "user" or "admin" using a localized label — the role element is present and contains exactly one of the 2 expected localized role values
- [ ] If `isAnonymous` equals true, a localized anonymous account indicator is rendered — the indicator element is present when true and absent when false
- [ ] The `createdAt` timestamp is formatted using `Intl.DateTimeFormat` according to the app's locale — the formatted date element is present and the output matches the locale-specific format
- [ ] If `banned` equals true, a prominent ban banner is rendered showing the ban status — the banner element is present and visible on the page
- [ ] If `banReason` is non-null, the ban banner displays the reason text — the reason element is present and its text content equals the `banReason` value from the server response
- [ ] If `banExpires` is non-null, the ban banner displays the formatted expiration date — the expiry element is present; if `banExpires` is null, the banner displays a "permanent ban" notice and the expiry element is absent
- [ ] If `banned` equals false, the ban banner is hidden or replaced with an "Active" status indicator — the ban banner element is absent and the active indicator is present
- [ ] The active sessions section renders each session's device information and creation timestamp — the count of rendered session entry elements equals the count of session records returned by the server response, and each entry contains non-empty device text
- [ ] The organization memberships section renders each membership's organization name and user role — the count of rendered membership entry elements equals the count of membership records returned by the server response, and each entry contains non-empty role text
- [ ] If `banned` equals false, the "Ban" button is visible and the "Unban" button is absent; if `banned` equals true, the "Unban" button is visible and the "Ban" button is absent
- [ ] The "Impersonate," "Change Role," "Revoke Sessions," "Remove," and "Edit" buttons are each present on the detail page when the action is applicable to the user's current state
- [ ] All text on the detail page is rendered through i18n translation keys — the count of hardcoded English strings equals 0
- [ ] If the server returns an HTTP 500 error, the detail page displays a localized error message with a retry button — the error element is present and the retry button is functional
- [ ] If the requesting user does not hold the app admin role, the server returns HTTP 403 and the response body contains 0 user detail fields — the client redirects to the dashboard and no user data is present in the response

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The selected user has 0 active sessions and 0 organization memberships, resulting in empty lists for both sections on the detail page | The client renders both sections with localized empty state messages (for example, "No active sessions" and "No organization memberships") instead of hiding the sections entirely | Both section containers are present in the DOM, each containing a localized empty state message element, and the count of session entries and membership entries both equal 0 |
| The selected user has a `banReason` set to an empty string rather than null, indicating the admin cleared the reason after initially setting one during the ban action | The client treats an empty string as equivalent to null for display purposes and falls back to a generic localized ban message instead of displaying an empty reason field | The ban banner displays the generic default ban message, and the reason-specific element is absent from the rendered output |
| The selected user has `banned` set to true and `banExpires` set to a timestamp that has already passed, meaning the ban has expired but the `banned` field was not reset by an admin | The detail page displays the ban banner with the expired expiration date formatted normally, because the detail page is a read-only view and does not evaluate ban expiry logic — ban enforcement is a server-side concern during sign-in | The ban banner is displayed with the formatted past expiration date, and the "Unban" button is rendered because `banned` equals true regardless of expiry |
| The app admin navigates directly to the user detail page URL with a user ID that does not exist in the database, bypassing the management list entirely | The server returns an empty result from `listUsers` filtered by the non-existent ID, and the client displays a localized "User not found" error message with a link back to the management list | The error state is displayed with the "User not found" message element present, and no user detail sections or action buttons are rendered |
| The selected user has an extremely long display name (over 200 characters) or ban reason text that exceeds the expected display width on the detail page | The client truncates the overflowing text with a CSS text-overflow ellipsis or wraps it within the container boundaries — the layout does not break or overflow outside the detail page bounds | The display name and ban reason elements are rendered within their container bounds, and no horizontal scrollbar appears on the detail page |
| The network connection drops after the detail page starts loading but before the server response arrives, causing the fetch request to time out | The client displays a localized network error message with a retry button after the fetch timeout elapses, allowing the admin to attempt the data fetch again when connectivity is restored | The error state element is displayed with the retry button present and functional, and no partial user data is rendered on the page |

## Failure Modes

- **Server returns HTTP 500 when querying the user table due to D1 database connection failure**
    - **What happens:** The `listUsers` endpoint fails to query the user table because the D1 database connection is unavailable or times out during the request execution.
    - **Source:** D1 Cloudflare SQL infrastructure outage or transient connection failure between the Worker and the D1 database instance.
    - **Consequence:** The detail page cannot display any user information, sessions, or memberships because the entire response depends on the user table query succeeding first.
    - **Recovery:** The client falls back to displaying a localized error message with a retry button, and logs the HTTP 500 status to the client console for diagnostics — the admin can click retry to re-initiate the fetch after the transient failure resolves.

- **Admin role check bypassed due to missing middleware on the listUsers endpoint after API route refactoring**
    - **What happens:** A refactoring of the API routes inadvertently removes or bypasses the admin role verification middleware on the `listUsers` endpoint, allowing non-admin users to fetch user detail data.
    - **Source:** Incorrect code change during development that removes the admin guard from the route handler or middleware chain for the `listUsers` endpoint.
    - **Consequence:** Non-admin users gain read access to other users' personal information, sessions, and organization memberships, creating a data exposure vulnerability.
    - **Recovery:** The CI test suite includes a test that calls `listUsers` with a non-admin user token and asserts that the response status equals 403 — CI alerts and blocks deployment if the admin guard is missing from the endpoint.

- **Session or membership data missing from the server response due to partial query failure in the database layer**
    - **What happens:** The user record query succeeds but the session table or member table query fails due to a transient D1 error, resulting in a response that contains user fields but lacks session or membership data.
    - **Source:** Transient D1 database error affecting one of the secondary queries (session or member table) while the primary user query completes normally.
    - **Consequence:** The detail page renders user information correctly but displays empty or missing sessions and memberships sections, giving the admin an incomplete picture of the user's activity.
    - **Recovery:** The client degrades gracefully by rendering the available user data and displaying localized "temporarily unavailable" messages in the sessions and memberships sections — the admin can reload the page to retry the failed queries.

- **Ban banner displays incorrect expiration date due to timezone mismatch in client-side date formatting logic**
    - **What happens:** The client formats the `banExpires` timestamp using a timezone offset that does not match the stored UTC value, causing the displayed expiration date to be shifted by several hours from the actual expiry time.
    - **Source:** Incorrect timezone handling in the `Intl.DateTimeFormat` configuration that fails to normalize the UTC timestamp before formatting it for display.
    - **Consequence:** The admin sees a ban expiration date that is hours ahead of or behind the actual expiry, leading to confusion about when the ban will be lifted for the affected user.
    - **Recovery:** The client falls back to formatting all ban expiry timestamps with an explicit UTC timezone specifier in the `Intl.DateTimeFormat` options, and the CI test suite includes a test that asserts the formatted output matches the expected UTC date string.

## Declared Omissions

- This specification does not define the behavior of individual admin action buttons (Ban, Unban, Impersonate, Change Role, Revoke Sessions, Remove, Edit) — each action is fully defined in its own dedicated behavioral specification
- This specification does not define the user management list page layout, filtering, sorting, or pagination behavior — the list page is a separate concern covered in its own specification
- This specification does not define real-time updates or WebSocket subscriptions for live changes to user data — the detail page displays a static snapshot that requires a manual page reload to refresh
- This specification does not define audit logging of admin views — tracking which admins viewed which user records is outside the current boilerplate scope and would be defined separately if required
- This specification does not define the behavior when the app admin views their own user detail record — self-view behavior follows the same rendering logic with no special handling or restrictions

## Related Specifications

- [app-admin-bans-a-user](app-admin-bans-a-user.md) — Defines the admin workflow for banning a user, which is triggered by the "Ban" action button rendered on the user detail page when the user is not currently banned
- [app-admin-unbans-a-user](app-admin-unbans-a-user.md) — Defines the admin workflow for unbanning a user, which is triggered by the "Unban" action button rendered on the user detail page when the user is currently banned
- [app-admin-revokes-user-sessions](app-admin-revokes-user-sessions.md) — Defines the admin workflow for revoking active sessions, which is triggered by the "Revoke Sessions" action button on the user detail page
- [app-admin-impersonates-a-user](app-admin-impersonates-a-user.md) — Defines the admin workflow for impersonating a user, triggered by the "Impersonate" action button on the user detail page
- [app-admin-changes-user-role](app-admin-changes-user-role.md) — Defines the admin workflow for changing a user's app-level role, triggered by the "Change Role" action button on the user detail page
- [app-admin-removes-a-user](app-admin-removes-a-user.md) — Defines the admin workflow for permanently removing a user, triggered by the "Remove" action button on the user detail page
- [app-admin-updates-user-details](app-admin-updates-user-details.md) — Defines the admin workflow for editing user profile fields, triggered by the "Edit" action button on the user detail page
- [banned-user-attempts-sign-in](banned-user-attempts-sign-in.md) — Defines the sign-in rejection behavior for banned users, which is related to the ban status information displayed on the user detail page
- [user-manages-sessions](user-manages-sessions.md) — Defines the user-facing session management behavior, complementing the admin view of active sessions displayed on the user detail page

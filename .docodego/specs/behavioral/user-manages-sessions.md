---
id: SPEC-2026-054
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Manages Sessions

## Intent

This spec defines how an authenticated user views, identifies, and revokes active sessions from the security settings page at `/app/settings/security`. The user opens the active sessions section, which loads all current sessions by calling `authClient.listSessions()` and renders them in a table with localized column headers showing the user agent (browser and operating system), the creation date, and an actions column. The current session is marked with a "Current" badge and does not display a revoke button, preventing the user from terminating the session they are actively using. Other sessions display a "Revoke" button that calls `authClient.revokeSession({ token })` to invalidate the targeted session immediately. When more than 1 session is active, a "Revoke all other sessions" button appears and calls `authClient.revokeOtherSessions()` to terminate every session except the current one. On the desktop app (Tauri), the session record carries the Tauri webview user agent string, and the UI parses this to display a friendly label such as "DoCodeGo Desktop" instead of the raw user agent. This spec ensures that users have full visibility into their active sessions and can revoke any non-current session individually or in bulk.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.listSessions()` via Better Auth client SDK | read | When the user navigates to `/app/settings/security` and the active sessions section mounts | The sessions table displays an error state with a translated message and a retry button, and logs the failure reason for diagnostics |
| `authClient.revokeSession({ token })` via Better Auth client SDK | write | When the user clicks the "Revoke" button on a specific non-current session row | The revoke button displays a translated error toast notification and the session remains active until the user retries the operation |
| `authClient.revokeOtherSessions()` via Better Auth client SDK | write | When the user clicks the "Revoke all other sessions" button to terminate every session except the current one | The bulk revoke button displays a translated error toast notification and all other sessions remain active until the user retries |
| D1 `session` table via Drizzle ORM | read/write | On every list, individual revoke, and bulk revoke operation against the session records stored in Cloudflare D1 | The API endpoint returns HTTP 500 and the client falls back to displaying a translated error message with a retry option |
| `@repo/i18n` translation keys | read | When rendering column headers, badges, button labels, error messages, and the Tauri-friendly user agent label in the sessions table | The UI falls back to the default English translation strings embedded in the component source code as literal fallback values |

## Behavioral Flow

1. **[User]** navigates to `/app/settings/security` and scrolls to the active sessions section of the page
2. **[Client]** calls `authClient.listSessions()` to retrieve the list of all active sessions for the authenticated user from the server
3. **[Server]** queries the `session` table in D1 for all records matching the current user's `userId` and returns the list of sessions to the client
4. **[Client]** renders the sessions as a table with 3 localized column headers: user agent (browser and operating system), creation date, and actions
5. **[Client]** identifies the current session by matching its token against the active session token stored in the authentication context
6. **[Client]** marks the current session row with a translated "Current" badge in the actions column and does not render a revoke button for this row
7. **[Client]** renders a "Revoke" button in the actions column for every session row that is not the current session
8. **[User]** clicks the "Revoke" button on a specific non-current session row to terminate that session
9. **[Client]** calls `authClient.revokeSession({ token })` with the targeted session's token to invalidate it on the server
10. **[Server]** deletes the targeted session record from the `session` table in D1 and returns a success response to the client
11. **[Client]** refreshes the sessions list by calling `authClient.listSessions()` again and re-renders the table without the revoked session entry
12. **[Client]** checks whether more than 1 session is present in the list and conditionally renders the "Revoke all other sessions" button
13. **[User]** clicks the "Revoke all other sessions" button to terminate every session except the current one
14. **[Client]** calls `authClient.revokeOtherSessions()` to delete all session records except the current session from the server
15. **[Server]** deletes all session records for the user from the `session` table except the record matching the current session token and returns a success response
16. **[Client]** refreshes the sessions list and re-renders the table showing only the current session with its "Current" badge
17. **[Client]** hides the "Revoke all other sessions" button because exactly 1 session remains in the list
18. **[Client]** parses each session's user agent string and displays a friendly label — for Tauri webview user agents, the label reads "DoCodeGo Desktop" instead of the raw user agent string, and for standard browser user agents, the label shows the browser name and operating system

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| (none) | Sessions loaded | User navigates to `/app/settings/security` and `authClient.listSessions()` returns HTTP 200 with at least 1 session | The user is authenticated and holds a valid session token in the authentication context |
| Sessions loaded | Session revoked | User clicks "Revoke" on a non-current session and `authClient.revokeSession({ token })` returns HTTP 200 | The targeted session token is not equal to the current session token and the record exists in the `session` table |
| Sessions loaded | All others revoked | User clicks "Revoke all other sessions" and `authClient.revokeOtherSessions()` returns HTTP 200 | More than 1 session is present in the list and the current session token is excluded from deletion |
| Sessions loaded | Load error | `authClient.listSessions()` returns a non-200 response or the network request fails entirely | The server is unreachable or the session token is invalid causing the API to reject the request |
| Session revoked | Sessions loaded | Client calls `authClient.listSessions()` to refresh the table after the individual revocation completes | The refresh call returns HTTP 200 with the updated list of remaining active sessions |
| All others revoked | Sessions loaded | Client calls `authClient.listSessions()` to refresh the table after the bulk revocation completes | The refresh call returns HTTP 200 with exactly 1 session (the current session) remaining |

## Business Rules

- **Rule current-session-no-revoke:** IF the session row matches the current session token THEN the actions column displays a translated "Current" badge instead of a "Revoke" button AND the count of revoke buttons rendered for the current session equals 0
- **Rule revoke-all-others-button-visibility:** IF the total number of active sessions in the list is greater than 1 THEN the "Revoke all other sessions" button is visible AND if exactly 1 session remains THEN the button is hidden from the UI
- **Rule immediate-invalidation-on-revoke:** IF the user clicks "Revoke" on a session row THEN the server deletes the session record from the `session` table immediately AND any device using that revoked token receives HTTP 401 on its next request
- **Rule desktop-tauri-ua-friendly-label:** IF the session's user agent string contains the Tauri webview identifier THEN the UI displays "DoCodeGo Desktop" as the friendly label instead of the raw user agent string

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | List all own sessions, revoke any individual non-current session, revoke all other sessions via the bulk action button | Revoke the current session from this interface, view or revoke sessions belonging to other users | Can only see sessions associated with their own `userId` in the `session` table |
| Admin | List all own sessions, revoke any individual non-current session, revoke all other sessions via the bulk action button | Revoke the current session from this interface, view or revoke sessions belonging to other users from this page | Can only see sessions associated with their own `userId`; admin session management for other users is a separate spec |
| Member | List all own sessions, revoke any individual non-current session, revoke all other sessions via the bulk action button | Revoke the current session from this interface, view or revoke sessions belonging to other users | Can only see sessions associated with their own `userId` in the `session` table |
| Unauthenticated | None — the security settings page at `/app/settings/security` requires authentication and redirects to `/signin` | All actions on this page including listing, revoking individual sessions, and bulk revoking sessions | Cannot see any session data because the auth guard redirects to `/signin` before the page content is rendered |

## Constraints

- The sessions table column headers, button labels, badge text, and error messages are rendered via `@repo/i18n` translation keys — the count of hardcoded English strings in the sessions management UI component equals 0.
- The "Revoke all other sessions" button is only visible when the active session count is greater than 1 — when exactly 1 session (the current session) remains, the button is absent from the DOM.
- The current session row does not render a "Revoke" button under any circumstances — the actions column for the current session contains only the translated "Current" badge, and the count of revoke buttons for the current session equals 0.
- User agent parsing for the Tauri webview identifier is handled client-side — the server returns the raw user agent string and the client maps known patterns to friendly labels ("DoCodeGo Desktop" for Tauri, browser name and OS for standard agents).
- The sessions list refreshes after every revocation operation (individual or bulk) — the client calls `authClient.listSessions()` after each successful revoke to ensure the displayed data is consistent with the server state.
- Session revocation is immediate and non-reversible — once the server deletes the session record from the `session` table, any device using that token receives HTTP 401 on its next authenticated request and there is no undo mechanism.

## Acceptance Criteria

- [ ] Navigating to `/app/settings/security` displays an active sessions section with a table containing 3 columns — the column count equals 3 (user agent, created date, actions)
- [ ] The sessions table loads data by calling `authClient.listSessions()` on component mount — the API call is present in the component lifecycle and returns HTTP 200
- [ ] Each session row displays a parsed user agent label showing the browser name and operating system — the label text is non-empty and present in every row
- [ ] The current session row displays a translated "Current" badge in the actions column — the badge element is present and visible for exactly 1 row
- [ ] The current session row does not display a "Revoke" button — the count of revoke buttons rendered in the current session row equals 0
- [ ] Non-current session rows display a "Revoke" button in the actions column — the button element is present and visible for each non-current session row
- [ ] Clicking "Revoke" on a non-current session calls `authClient.revokeSession({ token })` — the API call is present with the correct token parameter and returns HTTP 200
- [ ] After a successful individual revoke, the sessions list refreshes and the revoked session is absent from the table — the row count decreases by 1
- [ ] When more than 1 session is active, the "Revoke all other sessions" button is visible — the button element is present in the DOM when session count is greater than 1
- [ ] Clicking "Revoke all other sessions" calls `authClient.revokeOtherSessions()` — the API call is present and returns HTTP 200
- [ ] After a successful bulk revoke, the sessions list shows exactly 1 remaining session (the current session) — the table row count equals 1
- [ ] After bulk revoke, the "Revoke all other sessions" button is hidden — the button element is absent from the DOM when session count equals 1
- [ ] Tauri webview user agent strings are displayed as "DoCodeGo Desktop" — the friendly label is present instead of the raw user agent string for Tauri sessions
- [ ] All column headers, button labels, badge text, and error messages use `@repo/i18n` translation keys — the count of hardcoded English strings equals 0
- [ ] When `authClient.listSessions()` fails, the table displays an error state with a retry button — the error message is present and the retry button is visible

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user has exactly 1 active session (the current session) and no other sessions exist in the `session` table | The sessions table displays 1 row with the "Current" badge, no "Revoke" buttons are rendered, and the "Revoke all other sessions" button is absent from the DOM | The table row count equals 1, the revoke button count equals 0, and the bulk revoke button is absent |
| The user clicks "Revoke" on a session that was already revoked from another device between the list load and the button click | The server returns a success response (idempotent operation) because the desired state (session absent) is already achieved, and the client refreshes the list to reflect the current state | The API returns HTTP 200 and the sessions list refreshes without displaying an error to the user |
| The user clicks "Revoke all other sessions" while another device simultaneously revokes one of the sessions targeted by the bulk operation | The server processes the bulk deletion and the concurrent individual deletion completes independently without conflict, and the client refreshes to show only the current session | The API returns HTTP 200 and the refreshed list shows exactly 1 session remaining |
| The session's user agent string is empty or null because the client did not send a `User-Agent` header during authentication | The UI displays a translated "Unknown device" fallback label instead of an empty cell or a rendering error in the user agent column | The fallback label text is present in the row and the cell is non-empty |
| The user navigates away from the security settings page while a revocation request is still in-flight and has not yet completed | The revocation completes on the server regardless of the client navigation, and on returning to the page the sessions list reflects the updated state | The session record is absent from the `session` table after the in-flight request completes |
| The user has 50 active sessions across many devices and browsers, creating a long sessions table | The sessions table renders all 50 rows without pagination because the session count is bounded by practical device usage limits, and the "Revoke all other sessions" button is visible | The table row count equals 50 and all rows are present in the DOM |

## Failure Modes

- **listSessions API call fails due to network error or server unavailability when loading the security settings page**
    - **What happens:** The client calls `authClient.listSessions()` but the request fails due to a network interruption or server error, leaving the sessions table empty with no data to display.
    - **Source:** Network interruption, DNS resolution failure, or server-side error (HTTP 500) during the sessions list retrieval from the D1 database.
    - **Consequence:** The user cannot view their active sessions and cannot revoke any sessions, losing visibility into their account's security state.
    - **Recovery:** The client falls back to displaying a translated error message in the sessions table area with a retry button that calls `authClient.listSessions()` again, and logs the failure reason for diagnostics.

- **revokeSession API call fails after the user clicks the Revoke button on a specific session row**
    - **What happens:** The client calls `authClient.revokeSession({ token })` but the server returns an error, leaving the targeted session active and the user unable to terminate it from this attempt.
    - **Source:** Network timeout, server-side error (HTTP 500), or database write failure when attempting to delete the session record from the D1 `session` table.
    - **Consequence:** The targeted session remains valid and the device using that session retains access to the user's account until the session expires naturally at its `expiresAt` timeout.
    - **Recovery:** The client displays a translated error toast notification and the "Revoke" button returns to its enabled state so the user can retry the operation, and logs the failure reason for diagnostics.

- **revokeOtherSessions API call fails during bulk revocation leaving all other sessions active**
    - **What happens:** The client calls `authClient.revokeOtherSessions()` but the server returns an error or the request times out, leaving all non-current sessions active despite the user's intent to revoke them.
    - **Source:** Network timeout, server-side error (HTTP 500), or database transaction failure when attempting to delete multiple session records from the D1 `session` table.
    - **Consequence:** All other devices and browsers retain access to the user's account because the sessions were not deleted from the database.
    - **Recovery:** The client displays a translated error toast notification and the "Revoke all other sessions" button returns to its enabled state so the user can retry, and the client logs the failure reason for diagnostics.

- **User agent parsing fails to identify the Tauri webview string and displays the raw user agent instead of the friendly label**
    - **What happens:** A Tauri version update changes the webview user agent format, and the client-side parsing logic does not recognize the new pattern, causing the raw user agent string to be displayed instead of "DoCodeGo Desktop."
    - **Source:** Tauri framework update that modifies the webview user agent string format beyond what the client parser regex handles.
    - **Consequence:** The user sees an unfamiliar raw user agent string for their desktop session, making it harder to identify which session belongs to the desktop app.
    - **Recovery:** The parser degrades gracefully by displaying the raw user agent string as-is instead of crashing, and the development team updates the parser regex to match the new Tauri user agent format in a subsequent release, and logs a warning when an unrecognized user agent pattern is encountered.

## Declared Omissions

- Admin-initiated session revocation for other users from an administrative dashboard is not covered here and is defined in `app-admin-revokes-user-sessions.md`
- Session creation, refresh, context switching, and the underlying session lifecycle are not covered here and are defined in `session-lifecycle.md` as a separate spec
- Session expiry detection during active use and the associated user experience flow are not covered here and are defined in `session-expires-mid-use.md`
- The sign-out flow that invalidates the current session is not covered here and is defined in `user-signs-out.md` as a separate spec
- Rate limiting on session revocation API calls to prevent abuse is not covered here and is handled by the API-level rate limiting configuration

## Related Specifications

- [session-lifecycle](session-lifecycle.md) — defines session creation, refresh, context switching, and revocation behavior that this spec's UI triggers through the Better Auth client SDK
- [session-expires-mid-use](session-expires-mid-use.md) — covers the client-side detection and user experience handling when a session expires during active use of the application
- [user-signs-out](user-signs-out.md) — covers the sign-out flow for the current session, which is distinct from the session revocation of other sessions defined in this spec
- [auth-server-config](../foundation/auth-server-config.md) — defines Better Auth plugin configuration and session strategy that governs the session table schema and API endpoints used by this spec
- [database-schema](../foundation/database-schema.md) — defines the `session` table schema including columns like `token`, `userId`, `userAgent`, and `expiresAt` that this spec reads and displays

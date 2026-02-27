---
id: SPEC-2026-019
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: draft
roles: [Authenticated User]
---

[← Back to Roadmap](../ROADMAP.md)

# Session Lifecycle

## Intent

This spec defines the session creation, refresh, context switching, and revocation behavior for the DoCodeGo boilerplate. A session is created whenever a user authenticates through any supported method (email OTP, passkey, anonymous, SSO) and is stored in the `session` table with a token, user association, device metadata, a 7-day expiry, and active organization/team context. Sessions refresh automatically when accessed after a 24-hour `updateAge` threshold, extending the expiry by another 7 days. The session tracks mutable organizational context through `activeOrganizationId` and `activeTeamId` fields. Users can revoke individual sessions or bulk-revoke all other sessions from security settings. This spec ensures sessions are created consistently across all auth methods, refreshed transparently, and revocable by the user.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| D1 (Cloudflare SQL) via Drizzle ORM | read/write | Every session create, refresh, context switch, and revoke operation | Route handlers return 500 and the global error handler falls back to a generic JSON error response for the client |
| Better Auth session API | read/write | Every authentication event triggers session creation and every authenticated request triggers session lookup | Auth endpoints return 500 and the error handler degrades to a generic authentication error while non-auth routes remain unaffected |
| `@repo/contracts` | read | App startup when session-related oRPC contracts are registered | Build fails at compile time because the oRPC router cannot resolve contract types and CI alerts to block deployment |

## Behavioral Flow

1. **[Client]** sends authentication request via one of the 4 supported methods (email OTP, passkey, anonymous, or SSO)
2. **[Better Auth]** validates the authentication credentials and returns a success result to the session handler
3. **[Session handler]** creates a new row in the `session` table with `token`, `userId`, `ipAddress`, `userAgent`, `expiresAt` (current time + 604800 seconds), `activeOrganizationId`, and `activeTeamId`
4. **[Session handler]** sets two cookies on the response: a signed `httpOnly` session cookie containing the token and a non-`httpOnly` `docodego_authed` hint cookie — a JS-readable cookie that tells Astro pages the user is logged in
5. **[Astro]** uses the `docodego_authed` hint cookie to prevent a flash of unauthenticated content (FOUC) during page loads by conditionally rendering the authenticated or unauthenticated layout before the full session is validated server-side
6. **[Client]** sends a subsequent authenticated request with the session cookie attached automatically by the browser
7. **[Better Auth middleware]** looks up the session record by token and checks whether `expiresAt` is in the future:
   - If expired (no request within the 604800-second window) → the session is no longer valid, returns HTTP 401, and the client falls back to redirecting the user to `/signin`
   - If valid and last refresh was more than 86400 seconds ago (the `updateAge` threshold) → extends `expiresAt` by another 604800 seconds and continues to the route handler, ensuring active users are never unexpectedly logged out
   - If valid and last refresh was less than 86400 seconds ago → continues to the route handler without updating `expiresAt`
8. **[Client]** sends an organization or team switch request to change the current session's organizational context
9. **[Session handler]** updates `activeOrganizationId` or `activeTeamId` on the session record so the server can scope API responses and permissions to the correct organizational context without requiring the client to pass identifiers on every request
10. **[Admin user]** impersonates another user, and the session handler sets the `impersonatedBy` field on the session to the admin's user ID, creating an audit trail and allowing the system to display an impersonation indicator in the UI
11. **[Client]** sends a revoke request targeting either a single session token (for example, an unrecognized device) or all other sessions via bulk revocation
12. **[Session handler]** deletes the targeted session row(s) from the `session` table, explicitly excluding the current session token when bulk revoking via a `WHERE token != ?` clause, and any subsequent request using a revoked token is rejected forcing re-authentication

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| (none) | active | User completes authentication via any of the 4 supported methods | Authentication result is valid and a user record exists in the database |
| active | active (refreshed) | Authenticated request arrives with a valid session token | Last refresh occurred more than 86400 seconds ago, so `expiresAt` is extended by 604800 seconds |
| active | active (context switched) | User sends an organization or team switch request | The target organization or team ID belongs to the user's membership set |
| active | expired | No authenticated request arrives within the 604800-second expiry window | Current time exceeds the session's `expiresAt` timestamp value |
| active | revoked | User explicitly revokes the session from security settings | The session token matches the targeted token in the revocation request |
| active | revoked (bulk) | User bulk-revokes all other sessions from security settings | All session tokens except the current one are deleted from the `session` table |

## Business Rules

- **Rule session-creation:** IF authentication succeeds via any of the 4 supported methods (email OTP, passkey, anonymous, SSO) THEN a new session record is created with `expiresAt` set to current time + 604800 seconds
- **Rule passive-refresh:** IF an authenticated request arrives AND the session was last refreshed more than 86400 seconds ago THEN the server extends `expiresAt` by 604800 seconds without any client-side action or notification
- **Rule no-unnecessary-refresh:** IF an authenticated request arrives AND the session was last refreshed less than 86400 seconds ago THEN the server does not update `expiresAt` to prevent excessive database writes
- **Rule context-isolation:** IF a user switches organization or team on one session THEN only that session's `activeOrganizationId` or `activeTeamId` is updated, and other sessions for the same user on different devices remain unchanged
- **Rule bulk-revoke-exclusion:** IF a user bulk-revokes all other sessions THEN the current session token is explicitly excluded from the deletion query via `WHERE token != ?` clause

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated user (session owner) | Create sessions via authentication, refresh own sessions passively, switch organization/team context on own sessions, revoke own individual sessions, bulk-revoke all other own sessions | Revoke sessions belonging to other users, view session records of other users | Can only see and manage sessions associated with their own `userId` in the `session` table |
| Unauthenticated user | Initiate authentication to create a new session | Access any session management endpoint, revoke sessions, switch context | Cannot see any session data because all session endpoints require a valid session cookie |
| Admin (impersonating) | Access the target user's session as if authenticated, with `impersonatedBy` field set to the admin's user ID | Covered by `app-admin-impersonates-a-user.md` and not detailed in this spec | Covered by `app-admin-impersonates-a-user.md` and not detailed in this spec |

## Constraints

- Session refresh is passive and transparent to the user — the server extends `expiresAt` automatically during normal request processing without any client-side action or notification. The `updateAge` threshold of 86400 seconds (24 hours) prevents excessive database writes on every request while ensuring active sessions remain valid indefinitely.
- The `activeOrganizationId` and `activeTeamId` fields are mutable and scoped to the session — switching organization or team context does not affect other sessions for the same user on different devices. Each session independently tracks its own organizational context.
- The `docodego_authed` hint cookie is set identically across all auth methods — it contains no session token or user data, only a boolean indicator for client-side FOUC prevention. The hint cookie has no explicit expiry and is cleared only during sign-out or session revocation.
- Session tokens are signed server-side — the client cannot forge or modify a session token. The server validates the token signature on every request before looking up the session record.

## Acceptance Criteria

- [ ] A session record is created in the `session` table on every successful authentication — the record is present after email OTP, passkey, anonymous, and SSO sign-in, covering all 4 auth methods
- [ ] The session record contains `token`, `userId`, `ipAddress`, `userAgent`, `expiresAt`, `activeOrganizationId`, and `activeTeamId` — all 7 fields are present in the created row
- [ ] The `expiresAt` field is set to the current time + 604800 seconds (7 days) at creation — the value is present and within 1 second of the expected timestamp
- [ ] The session token is delivered as a signed, httpOnly cookie — the `Set-Cookie` header is present with `HttpOnly` = true and the TLS-only cookie attribute is present in production
- [ ] The `docodego_authed` hint cookie is set alongside the session cookie with `httpOnly` = false — the cookie is present and readable via `document.cookie`
- [ ] When a request uses a session last refreshed more than 86400 seconds (24 hours) ago, the server extends `expiresAt` by another 604800 seconds — the updated `expiresAt` value is present and later than the previous value
- [ ] When a request uses a session refreshed less than 86400 seconds ago, the server does not update `expiresAt` — the `expiresAt` value remains unchanged after the request
- [ ] The `activeOrganizationId` field updates when the user switches organizations — the field value is present and equals the newly selected organization's ID after the switch
- [ ] The `activeTeamId` field updates when the user switches teams — the field value is present and equals the newly selected team's ID after the switch
- [ ] The `impersonatedBy` field is present on the session record and is null for non-impersonated sessions — the field exists and its default value equals null
- [ ] Revoking an individual session removes the record from the `session` table — the row is absent after the revocation call and subsequent requests with that token return 401
- [ ] Bulk revoking all other sessions removes all session records except the current one — the count of remaining sessions for the user equals 1 (the current session only)
- [ ] Sessions that are not accessed for more than 604800 seconds (7 days) are no longer valid — requests with an expired session token return 401
- [ ] All session operations (create, refresh, revoke) are performed via Better Auth's session API — the count of custom session management implementations equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A request arrives with a valid-looking session cookie but the corresponding record is absent from the `session` table due to admin revocation or database cleanup | The server rejects the request with HTTP 401 and the client falls back to redirecting the user to `/signin` to re-authenticate | Response status is 401 and the response body contains a `code` field indicating an invalid session |
| Two browser tabs send simultaneous organization-switch requests for the same session, causing a race condition on the `activeOrganizationId` field | The server applies last-write-wins strategy and the client refreshes the organization context on page focus to ensure the UI reflects the current `activeOrganizationId` value | After both requests complete, the `activeOrganizationId` equals the value from the last-processed request |
| A user attempts to revoke a session token that does not exist in the `session` table because it was already revoked or expired | The server returns a success response (idempotent operation) without throwing an error because the desired state (session absent) is already achieved | Response status is 200 and no error is present in the response body |
| A user has exactly 1 active session and triggers bulk revocation of all other sessions | The server finds 0 other sessions to delete and returns success with the current session unchanged — the count of remaining sessions equals 1 | Response status is 200 and the current session record remains present in the `session` table |
| The server's system clock drifts more than 60 seconds ahead of the database server time, causing sessions to appear expired prematurely | The session refresh logic uses database-generated timestamps instead of application server timestamps, and the server logs a warning when clock drift exceeds 60 seconds | Session remains valid despite clock skew and a warning log entry is present |
| A request arrives with a session cookie that has been tampered with by modifying the token signature | The server rejects the token because signature validation fails before any database lookup occurs, returning HTTP 401 | Response status is 401 and no database query is executed for the tampered token |

## Failure Modes

- **Session record missing from database after external deletion**
    - **What happens:** A request arrives with a valid-looking session cookie, but the corresponding record is absent from the `session` table because it was deleted by admin revocation, database cleanup, or a bulk revocation from another device.
    - **Source:** External database modification or concurrent session management operation that removes the record.
    - **Consequence:** The user's request fails with no session context, and any in-progress work that depends on authentication is interrupted.
    - **Recovery:** The server rejects the request and returns error HTTP 401, and the client falls back to redirecting the user to `/signin` to re-authenticate and create a new session.
- **Clock skew causes premature session expiry across server instances**
    - **What happens:** The server's system clock is ahead of the actual time by more than 60 seconds, causing sessions to appear expired before their intended 7-day window because the comparison uses a future timestamp.
    - **Source:** System clock misconfiguration, NTP synchronization failure, or VM clock drift on the Cloudflare Workers runtime.
    - **Consequence:** Users are unexpectedly logged out and forced to re-authenticate even though their sessions have not reached the 604800-second expiry window.
    - **Recovery:** The session refresh logic falls back to database-generated timestamps instead of application server timestamps to mitigate clock skew, and the server logs a warning when clock drift exceeds 60 seconds so operators can investigate and correct the time synchronization.
- **Concurrent context switch race condition on the same session**
    - **What happens:** Two browser tabs send simultaneous organization-switch requests for the same session, causing a race condition where both writes target the `activeOrganizationId` field and the final value depends on execution order.
    - **Source:** User action in multiple browser tabs pointing to the same application with the same session cookie.
    - **Consequence:** One tab displays a stale organization context that does not match the value stored in the database, leading to user confusion about which organization is active.
    - **Recovery:** The server applies last-write-wins strategy and the client degrades gracefully by refreshing the organization context on page focus to ensure the UI reflects the current `activeOrganizationId` value, logging the context correction for diagnostics.
- **Bulk revocation accidentally deletes the current session**
    - **What happens:** A bug in the bulk revocation query deletes all sessions including the current one because the exclusion clause is missing or malformed, forcing the user to re-authenticate immediately after revoking other sessions.
    - **Source:** Incorrect SQL query construction in the bulk revocation handler that omits the `WHERE token != ?` exclusion clause.
    - **Consequence:** The user loses their active session and is immediately logged out, defeating the purpose of the bulk-revoke-all-others operation.
    - **Recovery:** The server explicitly excludes the current session token from the deletion query, and if the current session is absent from the table after the operation, the server returns error HTTP 500 and rolls back the transaction to restore all deleted sessions.

## Declared Omissions

- Session expiry detection during active use and the associated user experience flow are not covered here and are defined in `session-expires-mid-use.md`
- The session management user interface in security settings including listing, viewing, and revoking sessions from a dashboard is not covered here and is defined in `user-manages-sessions.md`
- Admin impersonation session behavior including how the `impersonatedBy` field is populated and how impersonation sessions differ from normal sessions is not covered here and is defined in `app-admin-impersonates-a-user.md`
- Admin-initiated session revocation for other users from an administrative dashboard is not covered here and is defined in `app-admin-revokes-user-sessions.md`
- Rate limiting on session creation to prevent brute-force authentication attacks is not covered here and is handled by the authentication specs for each individual sign-in method

## Related Specifications

- [auth-server-config](../foundation/auth-server-config.md) — Defines Better Auth plugin configuration and session strategy that governs token signing and cookie settings used by this spec
- [database-schema](../foundation/database-schema.md) — Defines the `session` table schema including all columns referenced by this spec such as `token`, `userId`, `expiresAt`, and context fields
- [session-expires-mid-use](session-expires-mid-use.md) — Covers the client-side detection and UX handling when a session expires during active use of the application
- [user-manages-sessions](user-manages-sessions.md) — Covers the security settings UI where users view active sessions and trigger individual or bulk revocation
- [app-admin-impersonates-a-user](app-admin-impersonates-a-user.md) — Covers admin impersonation sessions and how the `impersonatedBy` field is set and used during impersonation

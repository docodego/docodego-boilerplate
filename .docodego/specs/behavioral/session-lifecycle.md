[← Back to Roadmap](../ROADMAP.md)

# Session Lifecycle

## Intent

This spec defines the session creation, refresh, context switching, and revocation behavior for the DoCodeGo boilerplate. A session is created whenever a user authenticates through any supported method (email OTP, passkey, anonymous, SSO) and is stored in the `session` table with a token, user association, device metadata, a 7-day expiry, and active organization/team context. Sessions refresh automatically when accessed after a 24-hour `updateAge` threshold, extending the expiry by another 7 days. The session tracks mutable organizational context through `activeOrganizationId` and `activeTeamId` fields. Users can revoke individual sessions or bulk-revoke all other sessions from security settings. This spec ensures sessions are created consistently across all auth methods, refreshed transparently, and revocable by the user.

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

## Constraints

- Session refresh is passive and transparent to the user — the server extends `expiresAt` automatically during normal request processing without any client-side action or notification. The `updateAge` threshold of 86400 seconds (24 hours) prevents excessive database writes on every request while ensuring active sessions remain valid indefinitely.
- The `activeOrganizationId` and `activeTeamId` fields are mutable and scoped to the session — switching organization or team context does not affect other sessions for the same user on different devices. Each session independently tracks its own organizational context.
- The `docodego_authed` hint cookie is set identically across all auth methods — it contains no session token or user data, only a boolean indicator for client-side FOUC prevention. The hint cookie has no explicit expiry and is cleared only during sign-out or session revocation.
- Session tokens are signed server-side — the client cannot forge or modify a session token. The server validates the token signature on every request before looking up the session record.

## Failure Modes

- **Session record missing from database**: A request arrives with a valid-looking session cookie, but the corresponding record is absent from the `session` table (deleted by admin revocation or database cleanup). The server rejects the request and returns error HTTP 401, and the client falls back to redirecting the user to `/signin` to re-authenticate.
- **Clock skew causes premature expiry**: The server's system clock is ahead of the actual time, causing sessions to appear expired before their intended 7-day window. The server logs a warning when the clock drift exceeds 60 seconds compared to the database server time, and the session refresh logic uses database-generated timestamps instead of application server timestamps to mitigate clock skew.
- **Concurrent context switch on same session**: Two browser tabs send simultaneous organization-switch requests for the same session, causing a race condition on the `activeOrganizationId` field. The server applies the last-write-wins strategy, and the client refreshes the organization context on page focus to ensure the UI reflects the current `activeOrganizationId` value, logging the context correction for diagnostics.
- **Bulk revocation fails to exclude current session**: A bug in the bulk revocation query deletes all sessions including the current one, forcing the user to re-authenticate immediately after revoking other sessions. The server explicitly excludes the current session token from the deletion query using a `WHERE token != ?` clause, and returns error HTTP 500 if the current session is absent from the table after the operation, rolling back the transaction.

## Declared Omissions

- Session expiry mid-use detection and UX (covered by `session-expires-mid-use.md`)
- Session management UI in security settings (covered by `user-manages-sessions.md`)
- Admin impersonation session behavior (covered by `app-admin-impersonates-a-user.md`)
- Admin session revocation (covered by `app-admin-revokes-user-sessions.md`)

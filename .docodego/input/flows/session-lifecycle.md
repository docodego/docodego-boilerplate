# Session Lifecycle

## Session Creation

A session is created whenever a user successfully authenticates through any supported method — email OTP, passkey, anonymous sign-in, or SSO. The server writes a new record to the `session` table containing: a `token` (delivered as a signed cookie), `userId`, `ipAddress`, `userAgent`, `expiresAt` (set to 7 days from creation), `activeOrganizationId`, and `activeTeamId`. Alongside the session cookie, the server sets the `docodego_authed` hint cookie — a JS-readable, non-httpOnly cookie that tells Astro pages the user is logged in. Astro uses this hint to prevent a flash of unauthenticated content (FOUC) during page loads by conditionally rendering the appropriate layout before the full session is validated server-side.

## Session Refresh

Sessions refresh automatically based on access age. When a request is made using a session that was last refreshed more than 24 hours ago (the `updateAge` threshold), the server extends the `expiresAt` timestamp by another 7 days. This means active users are never unexpectedly logged out — as long as they use the application at least once within a 7-day window, their session remains valid indefinitely. Sessions that are not accessed for 7 days expire naturally and are no longer valid.

## Context Switching

The session tracks the user's current organizational context through two mutable fields. The `activeOrganizationId` field updates whenever the user switches to a different organization within the application. The `activeTeamId` field updates when the user changes their active team context within an organization. These fields allow the server to scope API responses and permissions to the correct organizational context without requiring the client to pass organization or team identifiers on every request.

## Admin Impersonation

The `impersonatedBy` field on the session is set when an admin user impersonates another user. This field records the admin's user ID, creating an audit trail and allowing the system to display an impersonation indicator in the UI. The impersonation mechanism and its controls are covered in detail in the admin flows.

## Session Revocation

Users can revoke sessions from their security settings. Individual sessions can be terminated — for example, revoking a session from an unrecognized device. Bulk revocation allows a user to sign out of all other sessions at once, keeping only the current session active. When a session is revoked, the corresponding record is removed from the `session` table and any subsequent request using that token is rejected, forcing the user on that device to re-authenticate.

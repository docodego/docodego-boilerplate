---
id: SPEC-2026-061
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Impersonates a User

## Intent

This spec defines the flow by which an app admin selects a target user
from the user management interface and activates an impersonation
session via `authClient.admin.impersonateUser({ userId })` to view
the application exactly as that user sees it. The server verifies the
caller holds the app admin role (`user.role = "admin"`), confirms the
target user is not an admin (controlled by
`allowImpersonatingAdmins: false`), and creates a new session tied to
the target user with the `session.impersonatedBy` field set to the app
admin's own userId. The app admin's original session is preserved so
they can return to it later. During impersonation, the UI displays a
persistent localized banner showing "Impersonating [user's name]" with
a stop button so the admin never loses awareness of their impersonated
state. The admin ends impersonation by clicking stop, which calls
`authClient.admin.stopImpersonating()` to revoke the impersonation
session and restore the original admin session. If the admin does not
explicitly stop, the impersonation session automatically expires after
1 hour and the admin is returned to their own session. Both the start
and end of every impersonation event are recorded in the audit log with
the admin's userId, the target user's userId, and timestamps.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.impersonateUser()` endpoint | write | App admin clicks the "Impersonate" action button on the target user's detail page in the user management interface, sending the target userId to the server to create an impersonation session | The client receives an error response and displays a localized error toast via Sonner — no impersonation session is created and the admin remains on their own session until the endpoint recovers and the admin retries |
| `authClient.admin.stopImpersonating()` endpoint | write | App admin clicks the stop button on the impersonation indicator banner to end the impersonation session and restore the admin's original session identity and dashboard view | The client receives an error response and displays a localized error toast — the impersonation session remains active until the admin retries the stop action or the 1-hour automatic expiry triggers session restoration |
| `session` table (D1, `impersonatedBy` field) | read/write | On impersonation start the server creates a new session row with `impersonatedBy` set to the admin's userId, and on stop or expiry the server deletes the impersonation session row and reactivates the admin's original session | The session creation fails and returns HTTP 500 so no impersonation session is written — the admin remains on their original session and the target user's view is not activated until the database recovers |
| Audit log | write | On impersonation start the server writes an audit entry recording the admin userId, target userId, and start timestamp, and on stop or expiry the server writes a second audit entry recording the end timestamp and termination reason | Audit log write degrades silently — the impersonation session proceeds or terminates as normal but the accountability record is incomplete until the audit log storage recovers and the missing entries are backfilled |
| `@repo/i18n` | read | The impersonation indicator banner text, stop button label, confirmation dialog text, error toast messages, and all localized strings in the impersonation flow are rendered via translation keys at component mount time | Translation function falls back to the default English locale strings so the impersonation indicator banner, stop button, and all feedback messages remain fully usable and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[App Admin]** navigates to the user management interface and
    selects a target user whose account they need to view for a
    support request or debugging investigation

2. **[App Admin]** clicks the "Impersonate" action button on the
    target user's detail page to initiate an impersonation session
    that will switch the admin's browser to the target user's identity

3. **[Client]** calls
    `authClient.admin.impersonateUser({ userId })` with the target
    user's ID, sending the impersonation request to the server for
    authorization and session creation

4. **[Server]** verifies that the calling user's `user.role` field
    equals `"admin"` — if the caller does not hold the app admin role,
    the server rejects the request with HTTP 403 and no impersonation
    session is created

5. **[Branch — target is admin]** If the target user's `user.role`
    field equals `"admin"` and `allowImpersonatingAdmins` is set to
    `false`, the server rejects the request with HTTP 403 and returns
    a localized error message indicating that admin users cannot be
    impersonated under the current configuration

6. **[Server]** creates a new session row in the `session` table
    tied to the target user's identity, with the
    `session.impersonatedBy` field set to the app admin's own userId
    and a 1-hour expiration timestamp calculated from the current time

7. **[Server]** preserves the app admin's original session by
    keeping it active in the `session` table so the admin can return
    to it when impersonation ends via stop or automatic expiry

8. **[Server]** writes an audit log entry recording the admin's
    userId, the target user's userId, and the impersonation start
    timestamp to create an accountability record for this event

9. **[Client]** receives the impersonation session from the server
    and transitions the browser to operate under the target user's
    identity, loading the target user's dashboard, organizations,
    data, and permissions

10. **[Client]** renders a persistent localized impersonation
    indicator — a floating banner or badge displaying
    "Impersonating [user's name]" text and a stop button — that
    remains visible on every page throughout the impersonation session

11. **[App Admin]** browses the application as the target user,
    seeing the exact same dashboard, organizations, data, and
    permission boundaries that the target user would see in their
    own authenticated session

12. **[App Admin]** clicks the stop button on the impersonation
    indicator banner to end the impersonation session and return to
    their own admin identity and dashboard view

13. **[Client]** calls `authClient.admin.stopImpersonating()` to
    send the stop request to the server for session revocation and
    admin session restoration

14. **[Server]** revokes the impersonation session by deleting the
    session row with the `impersonatedBy` field and reactivates the
    app admin's original session as the active session for the
    browser

15. **[Server]** writes an audit log entry recording the admin's
    userId, the target user's userId, the impersonation end
    timestamp, and the termination reason as "manual stop" to
    complete the accountability record

16. **[Client]** restores the app admin's own view of the
    application with their own identity, dashboard, organizations,
    and data, confirming that impersonation has ended via a localized
    toast notification

17. **[Branch — auto-expiry]** If the app admin does not explicitly
    stop impersonation within 1 hour, the server automatically
    expires the impersonation session by deleting the session row,
    reactivates the admin's original session, and writes an audit
    log entry with the termination reason as "auto-expiry" — the
    client detects the session change and returns the admin to their
    own dashboard view

18. **[Branch — network error on start]** If the
    `authClient.admin.impersonateUser()` request fails due to a
    network error or timeout, the client displays a localized error
    toast via Sonner and the admin remains on their own session with
    no impersonation session created

19. **[Branch — network error on stop]** If the
    `authClient.admin.stopImpersonating()` request fails due to a
    network error or timeout, the client displays a localized error
    toast via Sonner and the impersonation session remains active
    until the admin retries or the 1-hour auto-expiry triggers

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| admin_session_idle | impersonation_requesting | App admin clicks the "Impersonate" button on the target user's detail page in the user management interface | Calling user's `user.role` equals `"admin"` and the target user's detail page is loaded with a valid target userId |
| impersonation_requesting | impersonation_active | Server returns HTTP 200 confirming the impersonation session was created with the `impersonatedBy` field set to the admin's userId | Server validates admin role, confirms target is not an admin user, and creates the session row in the `session` table |
| impersonation_requesting | impersonation_error | Server returns HTTP 403 because the target user is an admin or the caller lacks the admin role, or the request fails due to a network error | Target user's `user.role` equals `"admin"` with `allowImpersonatingAdmins` set to `false`, or the caller's role is not `"admin"`, or a network error occurs |
| impersonation_error | admin_session_idle | Client displays the error toast and the admin acknowledges the error by dismissing it or navigating away from the target user's detail page | Error toast is visible and the admin's original session remains active with no impersonation session created |
| impersonation_active | stop_requesting | App admin clicks the stop button on the persistent impersonation indicator banner to end the impersonation session | The impersonation indicator banner is visible and the stop button is interactive and not in a loading state |
| impersonation_active | session_expired | The 1-hour impersonation session duration elapses without the admin clicking the stop button to end the session manually | Current timestamp exceeds the impersonation session's expiration timestamp set at creation time plus 1 hour |
| stop_requesting | admin_session_restored | Server returns HTTP 200 confirming the impersonation session was revoked and the admin's original session was reactivated | Server deletes the impersonation session row and the admin's original session is valid and present in the `session` table |
| stop_requesting | impersonation_active | The stop request fails due to a network error or server error and the impersonation session remains active until the admin retries | Network error or HTTP 500 response prevents the stop operation from completing on the server side |
| session_expired | admin_session_restored | Server automatically expires the impersonation session and reactivates the admin's original session after the 1-hour time limit passes | The admin's original session is valid and present in the `session` table when the automatic expiry triggers |
| admin_session_restored | admin_session_idle | Client restores the admin's own dashboard view and displays a localized toast confirming impersonation has ended | The admin's original session is active and the client has loaded the admin's own identity, dashboard, and data |

## Business Rules

- **Rule app-admin-role-required:** IF the authenticated user's
    `user.role` field does not equal `"admin"` THEN the
    `authClient.admin.impersonateUser()` endpoint rejects the request
    with HTTP 403 AND no impersonation session is created in the
    `session` table for the target user
- **Rule cannot-impersonate-admin:** IF the target user's `user.role`
    field equals `"admin"` AND the `allowImpersonatingAdmins`
    configuration is set to `false` THEN the server rejects the
    impersonation request with HTTP 403 AND returns a localized error
    message indicating that admin users cannot be impersonated
- **Rule impersonatedBy-field-set:** IF an impersonation session is
    created THEN the `session.impersonatedBy` field is set to the app
    admin's own userId AND the session is tied to the target user's
    identity for all permission and data access checks during the
    impersonation period
- **Rule original-session-preserved:** IF an impersonation session is
    active THEN the app admin's original session remains in the
    `session` table with its existing expiration and metadata AND the
    count of deleted original admin sessions during impersonation
    equals 0
- **Rule 1-hour-time-limit:** IF an impersonation session has been
    active for 1 hour (3600 seconds) without the admin clicking stop
    THEN the server automatically expires the impersonation session by
    deleting the session row AND reactivates the admin's original
    session as the active session
- **Rule impersonation-indicator-always-visible:** IF an impersonation
    session is active THEN the client renders a persistent localized
    banner displaying "Impersonating [user's name]" text and a stop
    button AND the count of pages rendered without the impersonation
    indicator during an active impersonation session equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin (impersonating non-admin user) | Click "Impersonate" on a non-admin target user's detail page, view the application as the target user with all of the target user's data and permissions, click stop to end impersonation and restore their own admin session | Impersonating a target user whose `user.role` equals `"admin"` — the server rejects the request with HTTP 403 when `allowImpersonatingAdmins` is set to `false` | The "Impersonate" button is visible on non-admin user detail pages; during impersonation the persistent indicator banner with stop button is always visible on every page |
| Non-admin authenticated user | None — the admin impersonation endpoints are not accessible to non-admin users and the server rejects all calls with HTTP 403 before any session manipulation occurs | Calling `authClient.admin.impersonateUser()` or `authClient.admin.stopImpersonating()` — both endpoints reject with HTTP 403 when the caller's `user.role` does not equal `"admin"` | The "Impersonate" button is not rendered on user detail pages for non-admin users; the admin user management interface is not accessible |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the user management page component renders any content or data | Accessing the user management page or calling the admin impersonation endpoints without a valid authenticated session token | The user management page is not rendered; the redirect to `/signin` occurs before any page elements are mounted or visible |

## Constraints

- The `authClient.admin.impersonateUser()` endpoint enforces the app
    admin role server-side by reading the calling user's `user.role`
    field — the count of impersonation sessions created by non-admin
    users equals 0
- The `allowImpersonatingAdmins` configuration defaults to `false`
    and the server enforces this check before creating an impersonation
    session — the count of impersonation sessions targeting admin-role
    users equals 0 when the configuration is `false`
- Every impersonation session has the `session.impersonatedBy` field
    set to the app admin's userId — the count of impersonation session
    rows in the `session` table where `impersonatedBy` is null equals 0
- The impersonation session expires automatically after 1 hour (3600
    seconds) from creation — the count of impersonation sessions that
    remain active beyond the 3600-second expiration window equals 0
- The app admin's original session is preserved in the `session` table
    during impersonation — the count of original admin sessions deleted
    during an active impersonation period equals 0
- Both the start and end of every impersonation event are recorded in
    the audit log — the count of impersonation events without a
    corresponding start and end audit log entry pair equals 0
- All impersonation indicator text, stop button labels, toast messages,
    and error messages are rendered via i18n translation keys — the
    count of hardcoded English string literals in the impersonation UI
    components equals 0

## Acceptance Criteria

- [ ] Clicking "Impersonate" on a non-admin target user's detail page calls `authClient.admin.impersonateUser({ userId })` — the mutation invocation count equals 1 and the payload contains the target user's userId
- [ ] After impersonation starts the browser operates under the target user's identity — the count of active sessions where userId equals the target user's ID and `impersonatedBy` is non-empty equals 1
- [ ] The impersonation session row in the `session` table has the `impersonatedBy` field present and non-empty — a query filtering by the impersonation session ID returns 1 row where the `impersonatedBy` column value is non-empty
- [ ] The admin's original session remains present in the `session` table during impersonation — the count of original admin session rows equals 1 and the expiration timestamp is unchanged from the pre-impersonation value
- [ ] A persistent impersonation indicator banner is visible on every page during impersonation — the banner element is present in the DOM and displays the target user's name with a stop button visible at all times
- [ ] Clicking the stop button calls `authClient.admin.stopImpersonating()` — the mutation invocation count equals 1 and the admin's view returns to their own dashboard within 2 seconds of the server response
- [ ] After stopping impersonation the admin's active session userId equals their own userId — the impersonation session row is absent from the `session` table and the admin's original session is active
- [ ] The impersonation session auto-expires after 3600 seconds — a session created with a 1-hour TTL is absent from the `session` table after 3600 seconds elapse and the admin's original session is reactivated
- [ ] An admin attempting to impersonate another admin-role user receives HTTP 403 — the response status equals 403 and no impersonation session row is created in the `session` table for the target admin user
- [ ] A non-admin user calling `authClient.admin.impersonateUser()` directly receives HTTP 403 — the response status equals 403 and no impersonation session is created in the `session` table
- [ ] An audit log entry is written when impersonation starts — the count of audit log rows with action type "impersonation_start" for the admin-target pair equals 1 within 500ms of the session creation
- [ ] An audit log entry is written when impersonation ends — the count of audit log rows with action type "impersonation_end" for the admin-target pair equals 1 within 500ms of the session termination
- [ ] On network error during impersonation start the client displays a localized error toast — the toast element is present within 500ms and no impersonation session is created on the server
- [ ] On network error during impersonation stop the client displays a localized error toast — the toast element is present within 500ms and the impersonation session remains active until retry or auto-expiry

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| App admin attempts to impersonate a target user who also holds the admin role with `allowImpersonatingAdmins` set to `false` | The server detects the target user's `user.role` equals `"admin"` and rejects the request with HTTP 403 — no impersonation session is created and the admin sees a localized error toast explaining that admin users cannot be impersonated | HTTP response status equals 403 and the count of impersonation session rows for the target admin user equals 0 |
| App admin's impersonation session reaches the 1-hour auto-expiry while the admin is actively browsing the target user's data | The server deletes the expired impersonation session row and reactivates the admin's original session — the client detects the session change on the next API call and redirects the admin to their own dashboard with a localized notification | The impersonation session row is absent from the `session` table after 3600 seconds and the admin's active session userId equals their own userId |
| App admin closes the browser tab during an active impersonation session without clicking the stop button first | The impersonation session remains active in the `session` table until the 1-hour auto-expiry triggers — the audit log records the end with termination reason "auto_expiry" when the session expires | The impersonation session row persists until 3600 seconds elapse and the audit log end entry has termination reason equal to "auto_expiry" |
| App admin attempts to start a second impersonation session while one is already active for a different target user | The server either rejects the second request with HTTP 400 indicating an impersonation session is already active, or terminates the first impersonation session before creating the second one based on server configuration | The count of concurrent impersonation sessions for a single admin equals at most 1 at any point in time |
| The target user's account is banned or deleted while the app admin is actively impersonating that user's session | The impersonation session becomes invalid on the next API call because the target user's account is no longer active — the server returns an error and the client falls back to restoring the admin's original session with a localized notification | The impersonation session is terminated and the admin's active session userId equals their own userId after the fallback |
| App admin clicks the stop button but the network request fails due to a timeout before the server processes the revocation | The client displays a localized error toast and the impersonation session remains active — the stop button returns to its interactive state so the admin retries the stop action or waits for the 1-hour auto-expiry | The error toast is visible and the impersonation session row remains in the `session` table until the admin retries or expiry triggers |

## Failure Modes

- **Server fails to create the impersonation session due to a D1 database write error**
    - **What happens:** The app admin clicks "Impersonate" and the
        client sends the `authClient.admin.impersonateUser()` request,
        but the D1 database write fails due to a transient storage
        error before the impersonation session row is committed to the
        `session` table with the `impersonatedBy` field.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        insert operation that writes the new impersonation session row
        to the `session` table.
    - **Consequence:** No impersonation session is created and the
        admin remains on their own original session with their own
        dashboard and identity — the target user's view is never
        activated and the admin sees an error toast on the user detail
        page.
    - **Recovery:** The server returns HTTP 500 and the client
        displays a localized error toast via Sonner — the admin
        retries the impersonation request once the D1 database
        recovers and the "Impersonate" button is re-enabled for
        another attempt.
- **Non-admin user bypasses the client guard and calls the admin impersonateUser endpoint directly**
    - **What happens:** A user without the app admin role crafts a
        direct HTTP request to the
        `authClient.admin.impersonateUser()` endpoint using a valid
        session cookie, bypassing the client-side UI that hides the
        "Impersonate" button from non-admin users, and attempts to
        create an impersonation session for another user without
        authorization.
    - **Source:** Adversarial or accidental action where a non-admin
        user sends a hand-crafted HTTP request to the admin
        impersonation endpoint with a valid session token,
        circumventing the client-side visibility guard that
        conditionally renders the "Impersonate" button only for users
        with `user.role` equal to `"admin"`.
    - **Consequence:** Without server-side enforcement any
        authenticated user could create an impersonation session and
        view another user's data, dashboard, organizations, and
        permissions, breaking the administrative boundary and enabling
        unauthorized access to private user information.
    - **Recovery:** The endpoint handler rejects the request with
        HTTP 403 after verifying the calling user's `user.role` field
        in the `user` table — the server logs the unauthorized attempt
        with the caller's user ID and timestamp, and no impersonation
        session is written to the `session` table.
- **Audit log write fails when recording the impersonation start or end event**
    - **What happens:** The impersonation session is created or
        terminated on the server, but the subsequent audit log write
        fails due to a storage error, leaving an incomplete
        accountability record for the impersonation event that does
        not include the start or end entry.
    - **Source:** Transient storage failure or write timeout on the
        audit log table during the insert operation that records the
        admin userId, target userId, timestamp, and termination reason
        for the impersonation event.
    - **Consequence:** The impersonation session proceeds or
        terminates as normal from a functional perspective, but the
        audit trail is incomplete — compliance reviews cannot verify
        when the impersonation started or ended for the affected event
        until the missing entry is recovered.
    - **Recovery:** The server logs the audit write failure to the
        application error log and notifies the operations team — the
        impersonation session is not blocked by the audit failure, and
        the missing audit entries are backfilled from the error log
        once the audit log storage recovers.
- **Admin's original session expires while an impersonation session is still active**
    - **What happens:** The app admin's original session reaches its
        own expiration time while the impersonation session is still
        active, meaning the admin has no valid session to return to
        when impersonation ends via stop or auto-expiry.
    - **Source:** The original admin session has a shorter TTL than
        the 1-hour impersonation window, or the admin started
        impersonation near the end of their original session's
        lifetime without the session being refreshed.
    - **Consequence:** When impersonation ends the server attempts to
        reactivate the admin's original session but finds it expired
        or absent — the admin cannot be returned to their own
        dashboard and is left in an unauthenticated state requiring a
        fresh sign-in.
    - **Recovery:** The server detects the expired original session
        during the stop or auto-expiry flow and returns an error
        indicating the admin's session is no longer valid — the client
        falls back to redirecting the admin to the `/signin` page with
        a localized message explaining that their session expired and
        they need to sign in again.

## Declared Omissions

- This specification does not address impersonation of admin-role
    users when `allowImpersonatingAdmins` is set to `true` — that
    configuration variant and its additional authorization checks are
    outside the scope of this default-configuration flow
- This specification does not address granular permission restrictions
    during impersonation, such as preventing the admin from performing
    write operations while viewing as the target user — all actions
    are permitted under the target user's full identity and permissions
- This specification does not address rate limiting on the
    `authClient.admin.impersonateUser()` endpoint — that behavior is
    enforced by the global rate limiter defined in `api-framework.md`
    covering all mutation endpoints uniformly across the API layer
- This specification does not address how the impersonation indicator
    banner renders on mobile viewport sizes within Expo or within the
    Tauri desktop wrapper — those platform-specific layout details are
    covered by their respective platform specs
- This specification does not address impersonation audit log
    retention policies or archival schedules — those operational
    concerns are defined in the platform administration and compliance
    specifications covering audit data lifecycle management

## Related Specifications

- [app-admin-views-user-details](app-admin-views-user-details.md) —
    User detail page where the app admin selects the target user and
    clicks the "Impersonate" button to initiate the impersonation flow
    defined in this specification
- [app-admin-lists-and-searches-users](app-admin-lists-and-searches-users.md) —
    User management listing page where the app admin navigates to find
    and select the target user before opening their detail page to
    access the impersonation action
- [session-lifecycle](session-lifecycle.md) — Session creation,
    refresh, and expiration mechanics that govern both the admin's
    original session preservation and the impersonation session's
    1-hour TTL enforcement in the `session` table
- [banned-user-attempts-sign-in](banned-user-attempts-sign-in.md) —
    Ban enforcement flow that checks the `user.banned` field, which is
    relevant when the target user's account is banned during an active
    impersonation session and the session becomes invalid
- [auth-server-config](../foundation/auth-server-config.md) — Better
    Auth server configuration including the admin plugin that validates
    the `user.role` field, exposes the impersonation endpoints, and
    controls the `allowImpersonatingAdmins` configuration flag
- [database-schema](../foundation/database-schema.md) — Schema
    definition for the `session` table that stores the
    `impersonatedBy` field distinguishing impersonation sessions from
    regular sessions in the D1 database
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization
    infrastructure providing translation keys for the impersonation
    indicator banner text, stop button label, toast messages, and all
    localized strings in the impersonation flow

---
id: SPEC-2026-063
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Changes a User's Role

## Intent

This spec defines the flow by which an app admin navigates to the user
management section of the admin dashboard, locates a target user, opens
their profile detail view, and changes the user's role using the role
dropdown. The dropdown displays the user's current role with localized
labels and allows the admin to select a new role, such as changing from
"user" to "admin" or from "admin" to "user". On confirmation, the
client calls `authClient.admin.setRole({ userId, role })` with the
target user's ID and the newly selected role. The server verifies the
caller holds the app admin role (`user.role = "admin"`) before updating
the target user's `role` field in the `user` table to the new value.
The change takes effect immediately at the data level — the server
reads the user's role from the database on each API request, so no
session invalidation or re-authentication is required. If the target
user is currently signed in, their next API request reflects the
updated role: promotion to admin grants access to admin-only dashboard
sections on the next navigation, and demotion from admin revokes access
to those sections immediately on the next navigation.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.setRole()` endpoint | write | App admin selects a new role from the dropdown and confirms the role change, sending the mutation with the target user's ID and the selected role to the server | The client receives an error response and displays a localized error toast via Sonner — the target user's `role` field remains unchanged in the database and the admin retries after the endpoint recovers |
| `user` table (D1 `role` field) | read/write | The user management page loads user records for listing and search, and the role change mutation writes the new value to the target user's `role` field in the `user` table row | The user list fails to load and returns HTTP 500, and the role change mutation rejects with HTTP 500 so the target user's `role` field remains at its previous value in the database until D1 recovers |
| `@repo/i18n` | read | All role dropdown labels, button text, confirmation dialog text, toast messages, and error messages on the role change form are rendered via translation keys at component mount time and when the dropdown options are populated | Translation function falls back to the default English locale strings so the role dropdown labels, confirmation dialog, and all feedback messages remain fully usable and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[App Admin]** navigates to the user management section of the
    admin dashboard, which displays a paginated list of all registered
    users with their current status, role, and account details

2. **[App Admin]** searches for or scrolls to the specific user whose
    role needs to change, using the search field to filter by name or
    email, then selects that user to open their profile detail view

3. **[App Admin]** locates the role dropdown on the target user's
    profile detail view, which displays the user's current role with
    a localized label (e.g., "User" or "Admin" translated via i18n)

4. **[App Admin]** clicks the role dropdown and selects the new role
    from the available options — for example, changing from "user" to
    "admin" or from "admin" to "user" — and the dropdown updates to
    show the newly selected value

5. **[Client]** detects the role selection change and displays a
    localized confirmation dialog asking the app admin to verify the
    role change, stating the target user's name and the new role that
    will be assigned upon confirmation

6. **[App Admin]** confirms the role change in the confirmation dialog,
    and the client transitions the confirm button to a loading state
    while the request is in flight, preventing duplicate submissions

7. **[Client]** calls `authClient.admin.setRole({ userId, role })`
    with the target user's ID and the newly selected role string,
    sending the role change mutation to the server for processing

8. **[Server]** verifies that the calling user's `user.role` field
    equals `"admin"` — if the caller does not hold the app admin role,
    the server rejects the request with HTTP 403 and no changes are
    written to the target user's record in the database

9. **[Server]** validates that the provided role value is one of the
    allowed roles ("user" or "admin") — if the role value is invalid,
    the server rejects the request with HTTP 400 and no changes are
    written to the target user's record in the database

10. **[Server]** updates the target user's `role` field in the `user`
    table to the new value — the `role` column value in the database
    equals the submitted role string and the count of rows where the
    old role value persists after the write equals 0

11. **[Server]** returns HTTP 200 confirming that the role change was
    applied to the target user's record in the database, including
    the updated role value in the response body

12. **[Client]** receives the success response, displays a localized
    confirmation toast via Sonner stating that the user's role has
    been updated, and invalidates the TanStack Query cache for the
    target user's data to trigger a re-fetch of the updated profile

13. **[Client]** refreshes the target user's detail view to reflect
    the new role — the role dropdown displays the newly assigned role
    as the current value with the correct localized label

14. **[Branch — target user's next request]** If the target user is
    currently signed in, their next API request reflects the updated
    role — the role value returned in the response equals the new role
    string and the count of re-authentication prompts triggered equals
    0 because the server reads `role` from the database on each request

15. **[Branch — promoted user navigates]** If the target user was
    promoted to admin, admin-only sections of the dashboard become
    accessible on their next navigation because the server returns
    the updated role in the session data for that request

16. **[Branch — demoted user navigates]** If the target user was
    demoted from admin, admin-only sections of the dashboard become
    inaccessible on their next navigation and the client redirects
    the user away from admin routes when the role check fails

17. **[Branch — network error]** If the role change mutation request
    fails due to a network error or timeout, the client displays a
    generic localized error toast via Sonner and re-enables the
    confirm button so the admin can retry the submission

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| user_detail_idle | role_selecting | App admin clicks the role dropdown on the target user's profile detail view to begin the role change workflow | Calling user's `user.role` equals `"admin"` and the target user's detail view is fully loaded with the current role displayed |
| role_selecting | confirming | App admin selects a different role from the dropdown, triggering the localized confirmation dialog to appear | The selected role differs from the target user's current `role` value in the database |
| role_selecting | user_detail_idle | App admin closes the dropdown without selecting a different role, returning to the idle detail view state | The admin clicked away or pressed Escape without selecting a new role value from the dropdown |
| confirming | submitting | App admin confirms the role change in the confirmation dialog, triggering the mutation request to the server | The admin clicked the confirm action in the dialog rather than cancelling or dismissing the dialog |
| confirming | user_detail_idle | App admin cancels or dismisses the confirmation dialog without confirming the role change | The admin clicked cancel or closed the dialog, and the role dropdown reverts to the original current role value |
| submitting | role_change_success | Server returns HTTP 200 confirming the role change was applied and the target user's `role` field was updated in the database | Server-side role check passes, the role value is valid, and the database write for the `role` field completes |
| submitting | role_change_error | Server returns a non-200 error code or the request times out before a response is received from the server | Database write fails, authorization check fails, validation fails, or a network error occurs during the mutation request |
| role_change_success | user_detail_idle | Client displays the success toast and the target user's detail view refreshes to show the updated role — the role dropdown selected value equals the new role string and the count of stale role labels visible equals 0 | TanStack Query cache invalidation completes and the detail view re-renders with the updated role from the re-fetched data |
| role_change_error | user_detail_idle | Client displays the error toast and the role dropdown reverts to the original role value for the admin to retry | Error message is visible via Sonner toast and the role dropdown displays the unchanged current role from the database |

## Business Rules

- **Rule app-admin-role-required:** IF the authenticated user's
    `user.role` field does not equal `"admin"` THEN the
    `authClient.admin.setRole()` endpoint rejects the request with
    HTTP 403 AND the server logs the unauthorized attempt with the
    caller's user ID and timestamp before returning the error response
- **Rule role-read-per-request:** IF the target user's `role` field
    is updated in the `user` table THEN the change takes effect on the
    target user's very next API request because the server reads the
    role from the database on each request — no session invalidation
    or re-authentication is required for the updated role to be enforced
- **Rule valid-roles-are-user-and-admin:** IF the `role` parameter in
    the `authClient.admin.setRole()` request is not one of the allowed
    values ("user" or "admin") THEN the server rejects the request with
    HTTP 400 AND no changes are written to the target user's record in
    the database
- **Rule promotion-grants-admin-access-immediately:** IF the target
    user's `role` field is changed from "user" to "admin" in the `user`
    table THEN admin-only dashboard sections become accessible to that
    user on their next navigation or API request without requiring
    sign-out or session refresh
- **Rule demotion-revokes-admin-access-immediately:** IF the target
    user's `role` field is changed from "admin" to "user" in the `user`
    table THEN admin-only dashboard sections become inaccessible to
    that user on their next navigation or API request and the client
    redirects the user away from admin routes

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin (changing another user's role) | View the user management list, search for users, open a user's profile detail view, click the role dropdown, select a new role, confirm the role change, and see the success or error toast | Changing their own role — the role dropdown is disabled with a localized tooltip when the target user ID equals the admin's own user ID to prevent self-demotion or self-modification | The role dropdown, confirmation dialog, and toast messages are all visible and interactive when the target user is not the admin themselves |
| Non-admin authenticated user | None — the admin user management page is not accessible to non-admin users and the route guard redirects or returns HTTP 403 before the page renders any content | Viewing the user management section, accessing any user's admin detail page, or calling the `authClient.admin.setRole()` endpoint, which rejects with HTTP 403 | The admin user management page is not rendered; the user is redirected or shown a 403 error before any admin controls are mounted or visible |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the admin user management page component renders any content or loads any user data | Accessing the admin user management page or calling the `authClient.admin.setRole()` endpoint without a valid authenticated session token | The admin page is not rendered; the redirect to `/signin` occurs before any page elements are mounted or any user data is fetched from the server |

## Constraints

- The `authClient.admin.setRole()` mutation endpoint enforces the
    app admin role server-side by reading the calling user's `user.role`
    field — the count of role change operations initiated by non-admin
    users that succeed equals 0
- The role value is validated server-side to be one of the allowed
    values ("user" or "admin") — the count of role change mutations
    committed with an invalid role value equals 0
- All role dropdown labels, button text, confirmation dialog text,
    toast messages, and error messages are rendered via i18n translation
    keys — the count of hardcoded English string literals in the role
    change component equals 0
- The role dropdown is disabled when the target user ID equals the
    admin's own user ID — the count of self-role-change mutations
    dispatched from the UI equals 0
- The confirmation dialog is displayed before the role change mutation
    is dispatched — the count of role change mutations sent without the
    admin first seeing and confirming the confirmation dialog equals 0

## Acceptance Criteria

- [ ] Clicking the role dropdown on a user's detail page displays the available roles ("user" and "admin") with localized labels — both options are present and rendered via i18n translation keys
- [ ] Selecting a different role from the dropdown triggers a localized confirmation dialog that states the target user's name and the new role — the dialog is present and visible before the mutation is dispatched
- [ ] After confirming, the client calls `authClient.admin.setRole({ userId, role })` — the mutation invocation count equals 1 and the payload contains the correct user ID and role value
- [ ] The confirm button transitions to a loading state while the mutation is in flight — the button displays a loading indicator and the count of additional mutation requests dispatched during this state equals 0
- [ ] On mutation success the server returns HTTP 200 and the target user's `role` field in the `user` table equals the selected role value — the count of rows where `role` differs from the submitted value after the mutation equals 0
- [ ] On mutation success a localized confirmation toast appears via Sonner — the toast element is present and visible within 500ms of the API returning HTTP 200
- [ ] On mutation success the target user's detail view refreshes within 500ms to show the updated role — the role dropdown selected value equals the new role string and the count of stale role labels visible equals 0
- [ ] On mutation failure due to a network error the client displays a localized error toast — the toast element is present and the role dropdown reverts to the original role value
- [ ] A non-admin authenticated user calling `authClient.admin.setRole()` directly receives HTTP 403 — the response status equals 403 and the target user's `role` field remains unchanged
- [ ] Submitting an invalid role value (not "user" or "admin") via direct API call returns HTTP 400 — the response status equals 400 and the target user's `role` field remains unchanged in the database
- [ ] The role dropdown is disabled when the target user ID equals the admin's own user ID — the disabled attribute is present and the count of self-role-change mutation requests equals 0
- [ ] The target user's next API request after a role change returns the updated role value in the response — the role field in the response equals the new value and the count of re-authentication prompts triggered equals 0
- [ ] All text on the role dropdown, confirmation dialog, and toast messages is rendered via i18n translation keys — the count of hardcoded English strings in the role change component equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| App admin selects the same role that the user currently has from the role dropdown without choosing a different value | The confirmation dialog does not appear because the selected role equals the current role — no mutation request is dispatched and the dropdown remains in its current state | The network request count to the `authClient.admin.setRole()` endpoint equals 0 and no confirmation dialog element is rendered |
| App admin attempts to change their own role by navigating to their own user detail page in the admin dashboard | The role dropdown is disabled with a localized tooltip explaining that admins cannot change their own role — no mutation request is dispatched when the admin interacts with the disabled dropdown | The role dropdown disabled attribute is present and the network request count to `authClient.admin.setRole()` equals 0 |
| Two app admins attempt to change the same user's role simultaneously from different browser sessions at the same moment | The last mutation to complete wins at the database level — both mutations write to the `role` field and the final value reflects whichever write was persisted last by the database | Both mutations return HTTP 200 and the target user's `role` field in the `user` table equals the value from the last successfully processed request |
| App admin changes a user's role from "user" to "admin" while the target user is actively browsing admin-restricted routes | The target user gains access to admin-only sections on their next navigation because the server reads the updated `role` field from the database on each request — no sign-out is required | The target user's next API request returns the updated role and admin-restricted endpoints return HTTP 200 instead of HTTP 403 |
| App admin demotes another admin to "user" while the target admin is viewing the admin dashboard | The demoted user loses access to admin-only sections on their next navigation — the client redirects the user away from admin routes when the role check returns "user" instead of "admin" | The demoted user's next API request to an admin endpoint returns HTTP 403 and the client redirects to a non-admin route |
| Network connection drops after the admin confirms the role change but before the server receives the mutation request | The client displays a localized network error toast via Sonner after the request times out, the role dropdown reverts to the original value, and the confirm button is re-enabled for retry | The target user's `role` field in the `user` table remains unchanged and the error toast element is present and visible |

## Failure Modes

- **Database write fails when updating the target user's role field in the user table**
    - **What happens:** The app admin confirms the role change and the
        client sends the `authClient.admin.setRole()` request, but the
        D1 database write fails due to a transient storage error before
        the `role` field is committed to the `user` table, leaving the
        target user's role unchanged at its previous value.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        single-row update that writes the new `role` value to the
        target user's record.
    - **Consequence:** The role change does not take effect, the target
        user retains their previous role for all subsequent API requests,
        and the admin sees an error state in the UI indicating the
        operation did not complete.
    - **Recovery:** The server returns HTTP 500 and the client displays
        a localized error toast via Sonner — the admin retries the role
        change once the D1 database recovers and the confirm button is
        re-enabled for another submission attempt.
- **Non-admin user bypasses the client guard and calls the admin setRole endpoint directly**
    - **What happens:** A user without the app admin role crafts a
        direct HTTP request to the `authClient.admin.setRole()` mutation
        endpoint using a valid session cookie, bypassing the client-side
        UI that hides admin controls from non-admin users, and attempts
        to change another user's role without authorization.
    - **Source:** Adversarial action where a non-admin user sends a
        hand-crafted HTTP request to the admin setRole mutation endpoint
        with a valid session token, circumventing the client-side
        visibility guard that conditionally renders admin controls only
        for users with `user.role` equal to `"admin"`.
    - **Consequence:** Without server-side enforcement any authenticated
        user could elevate another user's privileges or demote admins,
        undermining the entire role-based access control boundary and
        compromising administrative trust.
    - **Recovery:** The mutation handler rejects the request with
        HTTP 403 after verifying the calling user's `user.role` field
        in the `user` table — the server logs the unauthorized attempt
        with the caller's user ID and timestamp, and no changes are
        written to the target user's database record.
- **Admin submits an invalid role value via a manipulated client request to the setRole endpoint**
    - **What happens:** An app admin or adversarial user sends a
        request to `authClient.admin.setRole()` with a `role` parameter
        that is not one of the allowed values ("user" or "admin"), such
        as "superadmin" or an empty string, attempting to set an
        unrecognized role on the target user's record.
    - **Source:** Manipulated HTTP request payload where the `role`
        field contains a value outside the allowed enumeration, either
        through browser developer tools, a proxy, or a hand-crafted API
        call that bypasses client-side dropdown validation.
    - **Consequence:** Without server-side validation the target user's
        `role` field could be set to an unrecognized value, causing
        unpredictable access control behavior across all role-gated
        endpoints and dashboard sections.
    - **Recovery:** The server validates the `role` parameter against
        the allowed values and rejects the request with HTTP 400,
        returning a localized error message — no changes are written to
        the target user's database record and the server logs the
        invalid role submission attempt.

## Declared Omissions

- This specification does not address the admin workflow for banning
    or unbanning a user — those behaviors are fully defined in the
    separate `app-admin-bans-a-user.md` and `app-admin-unbans-a-user.md`
    specifications covering ban lifecycle flows
- This specification does not address role-based access control
    enforcement on individual API endpoints — middleware-level role
    checks on every request are defined separately from this admin
    action flow in the API framework specification
- This specification does not address rate limiting on the
    `authClient.admin.setRole()` endpoint — that behavior is enforced
    by the global rate limiter defined in `api-framework.md` covering
    all mutation endpoints uniformly across the API layer
- This specification does not address custom role definitions beyond
    "user" and "admin" because the current boilerplate scope only
    supports these two roles and custom role management is handled by
    the organization-level role system defined in `org-admin-manages-custom-roles.md`
- This specification does not address audit logging of role changes
    because the audit logging infrastructure is defined as a cross-
    cutting concern in the API framework and is not specific to this
    individual admin action flow

## Related Specifications

- [app-admin-views-user-details](app-admin-views-user-details.md) —
    Defines the admin user detail view that provides the profile page
    where the role dropdown is located and the admin initiates the role
    change action described in this specification
- [app-admin-lists-and-searches-users](app-admin-lists-and-searches-users.md)
    — Admin user management list and search flow that provides the entry
    point for locating and selecting the target user before navigating
    to their detail view to change their role
- [app-admin-updates-user-details](app-admin-updates-user-details.md)
    — Admin user detail editing flow that operates on the same `user`
    table records and shares the same admin dashboard navigation pattern
    used by this role change flow
- [auth-server-config](../foundation/auth-server-config.md) — Better
    Auth server configuration including the admin plugin that validates
    the `user.role` field and exposes the `authClient.admin.setRole()`
    endpoint used by this specification's role change confirmation flow
- [session-lifecycle](session-lifecycle.md) — Session creation and
    expiration lifecycle that governs how the server reads the user's
    role from the database on each request, enabling immediate role
    enforcement without session invalidation after a role change

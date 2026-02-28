---
id: SPEC-2026-058
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Updates User Details

## Intent

This spec defines the flow by which an app admin navigates to a target
user's detail page, opens an edit form pre-filled with the user's current
display name, email address, and profile image, modifies one or more of
those fields, and saves the changes via
`authClient.admin.updateUser({ userId, name, email, image })`. The server
verifies that the caller holds the app-level admin role (`user.role =
"admin"`) before applying the update to the target user's record in the
`user` table. Only changed fields are sent in the mutation payload. On
success, a localized toast notification confirms the update and the detail
page refreshes to display the new values immediately. If the target user
is the admin's own account, the edit button is hidden or disabled because
personal account changes are handled through the standard profile settings
page, maintaining a clear audit boundary between self-service and
administrative operations. This flow covers basic user information editing
only; changing a user's role is handled in a separate flow.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.updateUser()` endpoint | write | App admin clicks the Save button after editing one or more fields in the user detail edit form, sending only the changed fields to the server for persistence in the target user's record | The client receives an error response and displays a localized error toast via Sonner — the target user's existing data remains unchanged in the database until the endpoint recovers and the admin retries |
| `user` table (D1) | read/write | The user detail page loads to pre-fill the edit form with the target user's current display name, email, and profile image, and the mutation writes the updated fields upon save | The detail page fails to load the target user's current values and returns HTTP 500, and the mutation rejects with HTTP 500 so no partial update is written to the user record in the database |
| TanStack Query cache | read/write | On page load the cache serves the target user's data for form pre-fill, and on successful mutation the cache is invalidated to trigger a re-fetch so the detail page displays updated values immediately | Cache invalidation falls back to a stale read — the detail page retains the old user data until the next manual page reload or navigation event that triggers a fresh query for the target user's record |
| Sonner toast | write | On save success a localized confirmation toast is displayed, and on save failure a localized error toast is displayed describing the rejection reason returned by the server | Toast notification degrades silently — the form state itself reflects the outcome through the detail page refresh on success or the retained edits on failure, even without a visible toast notification |
| `@repo/i18n` | read | All form labels, button text, placeholder text, validation messages, error messages, tooltip text, and toast messages on the user detail edit form are rendered via translation keys at component mount time | Translation function falls back to the default English locale strings so the edit form and all feedback messages remain fully usable and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[App Admin]** opens the user detail page for the target user and
    clicks the "Edit" action button to begin modifying the user's basic
    information from the administrative interface

2. **[Client]** renders a localized edit form — either inline on the
    detail page or as a modal — pre-filled with the target user's current
    display name, email address, and profile image retrieved from the
    TanStack Query cache or a fresh API fetch

3. **[Client]** renders the Save button in a disabled state because no
    fields have been modified yet — the button remains disabled until at
    least one field value differs from the original pre-filled value

4. **[App Admin]** modifies one or more fields in the edit form, such as
    correcting a misspelled display name, changing an email address, or
    updating the profile image URL

5. **[Client]** runs client-side validation on each modified field — the
    email field is validated for correct email format and the display name
    field is validated to be non-empty before the form can be submitted

6. **[Client]** enables the Save button because at least one field value
    now differs from its original pre-filled value, indicating that the
    admin has made a meaningful change to the target user's information

7. **[App Admin]** clicks the Save button to submit the modified fields
    to the server for persistence in the target user's record

8. **[Client]** transitions the Save button to a loading state while the
    request is in flight, preventing duplicate submissions until the
    server responds with a success or failure result

9. **[Client]** calls `authClient.admin.updateUser({ userId, name,
    email, image })` with only the fields that differ from the original
    pre-filled values, sending the mutation request to the server

10. **[Server]** verifies that the calling user's `user.role` field
    equals `"admin"` — if the caller does not hold the app admin role,
    the server rejects the request with HTTP 403 and no update is written
    to the target user's record in the database

11. **[Server]** validates the incoming field values — the email address
    is checked for uniqueness against existing records in the `user` table
    and the display name is confirmed to be non-empty after trimming
    whitespace

12. **[Branch — email already in use]** If the submitted email address
    already belongs to another user account in the `user` table, the
    server rejects the request with HTTP 400 and a localized error
    message indicating that the email is already in use — the form
    retains the admin's edits so they can correct the email and retry

13. **[Server]** applies the validated updates to the target user's
    record in the `user` table and returns HTTP 200 confirming that the
    changes were persisted successfully

14. **[Client]** receives the success response, displays a localized
    toast notification via Sonner confirming that the user's details
    were updated, and invalidates the TanStack Query cache for the
    target user's data to trigger a re-fetch

15. **[Client]** refreshes the detail page to display the new values
    immediately — the updated display name, email, and profile image
    are visible without requiring a manual page reload

16. **[Branch — network error]** If the mutation request fails due to a
    network error or timeout, the client displays a generic localized
    error toast via Sonner and re-enables the Save button so the admin
    can retry the submission without re-entering their changes

17. **[Branch — self-edit attempt]** If the app admin opens the user
    detail page for their own account, the "Edit" button is hidden or
    disabled with a localized tooltip explaining that personal account
    changes are made through the standard profile settings page,
    preventing any self-edit attempt from this administrative flow

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| detail_page_idle | edit_form_open | App admin clicks the "Edit" action button on the target user's detail page | Calling user's `user.role` equals `"admin"` and the target user's ID does not equal the calling user's ID |
| edit_form_open | edit_form_dirty | App admin modifies at least one field value so it differs from the original pre-filled value | At least one field value is non-equal to the original value loaded from the target user's record |
| edit_form_dirty | edit_form_open | App admin reverts all modified fields back to their original pre-filled values | All field values equal their original pre-filled values from the target user's record |
| edit_form_dirty | submitting | App admin clicks the Save button after client-side validation passes for all modified fields | Email field contains a valid email format and display name field is non-empty after trimming whitespace |
| submitting | update_success | Server returns HTTP 200 confirming the target user's record was updated with the new field values | Server-side validation passes and the updated fields are written to the `user` table |
| submitting | update_error | Server returns a non-200 error code or the request times out before a response is received | Database write fails, email uniqueness check fails, authorization check fails, or network error occurs |
| update_success | detail_page_idle | Client displays the success toast and the detail page refreshes to show the updated values from the re-fetched data | TanStack Query cache invalidation completes and the detail page re-renders with the new user data |
| update_error | edit_form_dirty | Client displays the error toast and the form retains the admin's edits for correction and retry | Error message is visible and the Save button is re-enabled with the previously entered field values intact |

## Business Rules

- **Rule app-admin-role-required:** IF the authenticated user's
    `user.role` field does not equal `"admin"` THEN the
    `authClient.admin.updateUser()` endpoint rejects the request with
    HTTP 403 AND the server logs the unauthorized attempt with the
    caller's user ID and timestamp before returning the error response
- **Rule self-edit-restricted:** IF the target user's ID equals the
    calling app admin's own user ID THEN the "Edit" button on the detail
    page is hidden or disabled with a localized tooltip AND the client
    does not render the edit form because personal account changes are
    handled through the standard profile settings page
- **Rule save-disabled-until-changed:** IF no field value in the edit
    form differs from its original pre-filled value THEN the Save button
    remains disabled AND the count of mutation requests dispatched while
    no fields have changed equals 0
- **Rule email-uniqueness-enforced:** IF the submitted email address
    already belongs to another user account in the `user` table THEN the
    server rejects the update with HTTP 400 AND returns a localized error
    message indicating the email is already in use by another account
- **Rule edit-retention-on-error:** IF the
    `authClient.admin.updateUser()` mutation fails for any reason THEN
    the edit form retains all of the admin's modified field values so the
    admin can correct the issue and retry without re-entering all fields
    from scratch

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin (editing another user) | View the target user's detail page, open the edit form pre-filled with current values, modify display name, email, and profile image fields, click Save to submit the mutation, and see the success or error toast | Editing their own account through this flow — the "Edit" button is hidden or disabled with a localized tooltip when the target user ID equals the admin's own user ID | The "Edit" button, edit form, and Save button are all visible and interactive when viewing another user's detail page |
| App Admin (viewing own account) | View their own user detail page with all current information displayed as read-only content without any edit controls visible | Opening the edit form for their own account — the "Edit" button is hidden or disabled and the admin is directed to the profile settings page for self-service changes | The "Edit" button is absent or disabled with a tooltip; the edit form is not rendered and the Save button is not present in the DOM |
| Non-admin authenticated user | None — the user detail admin page is not accessible to non-admin users and the route guard redirects or returns HTTP 403 before the page renders | Viewing any user's detail page through the admin interface or calling the `authClient.admin.updateUser()` endpoint, which rejects with HTTP 403 | The admin user detail page is not rendered; the user is redirected or shown a 403 error before any edit controls are mounted |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the user detail page component renders any content or data | Accessing the user detail page or calling the `authClient.admin.updateUser()` endpoint without a valid authenticated session token | The user detail page is not rendered; the redirect to `/signin` occurs before any page elements are mounted or visible |

## Constraints

- The `authClient.admin.updateUser()` mutation endpoint enforces the
    app admin role server-side by reading the calling user's `user.role`
    field — the count of successful user updates initiated by non-admin
    users equals 0
- The edit form sends only fields that differ from the original
    pre-filled values — the count of unchanged fields included in the
    mutation payload equals 0 for every submission
- The Save button is disabled until at least one field value differs
    from its original — the count of mutation requests dispatched while
    all field values equal their pre-filled originals equals 0
- The email uniqueness check runs server-side before the update is
    written — the count of user records in the `user` table sharing
    the same email address equals 1 at all times after the mutation
    completes
- The "Edit" button is hidden or disabled when the target user ID
    equals the calling admin's own user ID — the count of self-edit
    form renders in this administrative flow equals 0
- All form labels, button text, validation messages, tooltip text,
    error messages, and toast messages on the edit form are rendered
    via i18n translation keys — the count of hardcoded English string
    literals in the user detail edit form component equals 0

## Acceptance Criteria

- [ ] Clicking "Edit" on a target user's detail page renders an edit form pre-filled with the user's current display name, email, and profile image — the input values are non-empty and equal the stored values after the form loads
- [ ] The Save button is disabled when no field value differs from its original pre-filled value — the disabled attribute is present on the Save button and the count of dispatched mutation requests equals 0
- [ ] The Save button becomes enabled when at least one field value differs from its original — the disabled attribute is absent and the button is interactive after the admin modifies a field
- [ ] Clicking Save after editing calls `authClient.admin.updateUser({ userId, name, email, image })` with only the changed fields — the mutation invocation count equals 1 and the payload contains only fields that differ from the original values
- [ ] The Save button transitions to a loading state while the mutation is in flight — the button shows a loading indicator and the count of additional mutation requests that can be triggered during this state equals 0
- [ ] On mutation success a localized confirmation toast appears via Sonner — the toast element is present and visible within 500ms of the API returning HTTP 200
- [ ] On mutation success the TanStack Query cache for the target user's data is invalidated — the detail page displays the updated values and the count of stale fields visible after re-fetch equals 0
- [ ] On mutation failure due to a duplicate email the client displays a localized error message indicating the email is already in use — the error element is present and the form retains the admin's edits with all field values intact
- [ ] On mutation failure due to a network error the client displays a generic localized error toast — the toast element is present and the Save button returns to its interactive state with the disabled attribute absent
- [ ] A non-admin authenticated user calling `authClient.admin.updateUser()` directly receives HTTP 403 — the response status equals 403 and the target user's record in the `user` table remains unchanged
- [ ] When the target user ID equals the calling admin's own user ID the "Edit" button is hidden or disabled — the count of visible and enabled "Edit" button elements on the admin's own detail page equals 0
- [ ] The disabled "Edit" button on the admin's own detail page shows a localized tooltip explaining that personal changes are made through profile settings — the tooltip element is present and its text content is non-empty
- [ ] Client-side validation rejects an empty display name — the validation error element is present and the Save button remains disabled when the display name field is empty after trimming
- [ ] Client-side validation rejects an invalid email format — the validation error element is present and the Save button remains disabled when the email field does not match a valid email pattern

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| App admin submits an email address that is already associated with another user account in the `user` table | The server detects the duplicate email during the uniqueness check and returns HTTP 400 with a localized error message — the form retains the admin's edits and the target user's record remains unchanged until the admin corrects the email | HTTP response status equals 400 and the target user's email in the `user` table remains at the original value before the attempted update |
| App admin opens the edit form but navigates away from the detail page before clicking Save to submit changes | No mutation request is sent because the admin did not click Save — the target user's record in the `user` table remains at its current values and the navigation proceeds without triggering any write operation | The network request count to the `authClient.admin.updateUser()` endpoint equals 0 and the target user's record is unchanged after navigation |
| App admin edits a user whose record is simultaneously updated by another admin from a different browser session | The last mutation to complete wins at the database level — the target user's record stores whichever update was persisted last, and each admin's detail page reflects the final values after the next data fetch completes | Both mutations return HTTP 200 and the target user's fields in the `user` table equal the values from the last successfully processed request |
| App admin clears the display name field entirely and attempts to submit the form with an empty name value | Client-side validation prevents submission because the display name is empty after trimming — the validation error is displayed inline and the Save button remains disabled until the admin enters a non-empty name | The validation error element is present, the Save button disabled attribute equals true, and the mutation request count equals 0 |
| App admin edits only the profile image field without changing the display name or email address fields | The mutation payload contains only the `image` field and the `userId` because name and email were not modified — the server updates only the profile image in the target user's record and leaves the other fields unchanged | The mutation payload includes `image` and `userId` with name and email absent, and HTTP response status equals 200 |
| The target user's session is active while the app admin updates their display name and email address fields | The target user's active session continues with the old cached data until their next data fetch or page navigation triggers a re-fetch — the server-side record reflects the new values immediately after the admin's mutation succeeds | The target user's record in the `user` table equals the updated values and the target user's client displays the new values after the next cache invalidation or page refresh |

## Failure Modes

- **Database write fails when updating the target user's record in the user table**
    - **What happens:** The app admin clicks Save and the client sends
        the `authClient.admin.updateUser()` request, but the D1 database
        write fails due to a transient storage error before the updated
        fields are committed to the `user` table, leaving the target
        user's record at its original values.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        single-row update operation that writes the changed fields to
        the target user's record.
    - **Consequence:** The update does not take effect and the target
        user's display name, email, and profile image remain at their
        previous values, while the admin sees an error toast on the
        edit form and the database row remains unmodified.
    - **Recovery:** The server returns HTTP 500 and the client displays
        a localized error toast via Sonner — the admin retries the
        update once the D1 database recovers and the Save button is
        re-enabled for another submission attempt.
- **Non-admin user bypasses the client guard and calls the admin updateUser endpoint directly**
    - **What happens:** A user without the app admin role crafts a
        direct HTTP request to the `authClient.admin.updateUser()`
        mutation endpoint using a valid session cookie, bypassing the
        client-side UI that hides admin controls from non-admin users,
        and attempts to modify another user's details without
        authorization.
    - **Source:** Adversarial or accidental action where a non-admin
        user sends a hand-crafted HTTP request to the admin mutation
        endpoint with a valid session token, circumventing the
        client-side visibility guard that conditionally renders admin
        controls only for users with `user.role` equal to `"admin"`.
    - **Consequence:** Without server-side enforcement any authenticated
        user could modify another user's display name, email, or profile
        image, breaking the administrative boundary and potentially
        enabling account takeover through unauthorized email changes.
    - **Recovery:** The mutation handler rejects the request with
        HTTP 403 after verifying the calling user's `user.role` field
        in the `user` table — the server logs the unauthorized attempt
        with the caller's user ID and timestamp, and no update is
        written to the target user's database record.
- **TanStack Query cache invalidation fails after a successful admin update mutation**
    - **What happens:** The mutation succeeds and the server persists
        the updated fields to the target user's record in D1, but the
        client-side TanStack Query cache invalidation does not trigger,
        leaving stale user data on the detail page despite the
        successful server-side update.
    - **Source:** A cache invalidation gap where the mutation success
        handler fails to call the invalidation function due to a runtime
        error, an unhandled promise rejection, or a query key mismatch
        between the mutation and the target user's data query.
    - **Consequence:** The admin sees the success toast but the detail
        page continues to display the old display name, email, or
        profile image, creating a confusing inconsistency that persists
        until a manual page reload triggers a fresh query.
    - **Recovery:** The mutation success handler notifies the target
        user's data query cache to invalidate and refetch — if
        invalidation fails the admin falls back to a manual page reload
        that triggers a fresh query and resolves the stale data across
        all displayed fields on the detail page.
- **App admin submits an email address that is already in use by another account in the user table**
    - **What happens:** The admin changes the target user's email to
        an address that already belongs to another user account — the
        server detects the duplicate during the uniqueness constraint
        check against the `user` table and rejects the update before
        writing any changes to the target user's record.
    - **Source:** The admin entered an email address that is already
        associated with a different user record in the `user` table,
        violating the unique constraint on the email column that
        prevents two accounts from sharing the same email address.
    - **Consequence:** The target user's email address remains at its
        previous value and no fields are updated on the target user's
        record — the admin sees an error message on the form and the
        database row is unmodified by the rejected mutation attempt.
    - **Recovery:** The server returns HTTP 400 with a localized error
        message indicating the email is already in use — the admin
        corrects the email field to a unique address and retries the
        submission with the form retaining all other edited field values.

## Declared Omissions

- This specification does not address changing a user's app-level role
    (such as promoting a user to admin or demoting an admin to a regular
    user) — that behavior is defined in a separate spec covering the
    admin role assignment flow with its own authorization and audit rules
- This specification does not address banning or unbanning a user account
    from the admin interface — that behavior is defined in a separate
    spec covering the ban lifecycle including ban reason, expiration, and
    enforcement at sign-in time
- This specification does not address deleting a user account from the
    admin interface — that behavior is defined in a separate spec covering
    cascading cleanup of user data, sessions, and organization memberships
- This specification does not address rate limiting on the
    `authClient.admin.updateUser()` endpoint — that behavior is enforced
    by the global rate limiter defined in `api-framework.md` covering all
    mutation endpoints uniformly across the API layer
- This specification does not address how the user detail edit form
    renders on mobile viewport sizes within Expo or within the Tauri
    desktop wrapper — those platform-specific layout details are covered
    by their respective platform specs

## Related Specifications

- [user-updates-profile](user-updates-profile.md) — Self-service profile
    update flow where users edit their own display name through the profile
    settings page, which is the designated alternative when an admin
    attempts to edit their own account through this administrative flow
- [banned-user-attempts-sign-in](banned-user-attempts-sign-in.md) — Ban
    enforcement flow that checks the `user.banned` field at sign-in time,
    which operates on the same `user` table records that this admin edit
    flow modifies for display name, email, and profile image fields
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth
    server configuration including the admin plugin that validates the
    `user.role` field and exposes the `authClient.admin.updateUser()`
    endpoint used by this specification's edit-and-save flow
- [database-schema](../foundation/database-schema.md) — Schema definition
    for the `user` table that stores the display name, email, and image
    fields read and written by the edit form and the admin update mutation
    handler
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization
    infrastructure providing translation keys for all edit form labels,
    button text, validation messages, tooltip text, toast messages, and
    error descriptions rendered on the user detail edit form

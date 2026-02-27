---
id: SPEC-2026-062
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [App Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# App Admin Creates a User

## Intent

This spec defines the flow by which an app admin navigates to the user
management section of the app admin dashboard, opens a user creation
form, fills in the new user's name, email address, password, and role,
and submits the form to create a new user account via
`authClient.admin.createUser()`. The server verifies that the caller
holds the app-level admin role (`user.role = "admin"`) before creating
the new user record in the `user` table (D1) with the provided details.
The password is hashed before storage using the same process as the
normal signup flow. This flow exists for situations where the normal
self-service signup process is not suitable, such as provisioning
accounts for team members, creating test accounts, or onboarding users
who need to be set up by an app admin. No welcome email or email
verification step is triggered by this admin-created flow. The created
user can immediately sign in with the email and password the app admin
provided. On success, the new user immediately appears in the user
management list and a localized toast notification confirms the creation.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.admin.createUser()` endpoint | write | App admin clicks the Submit button after filling in all required fields in the user creation form, sending the name, email, password, and role to the server for user record creation | The client receives an error response and displays a localized error toast via Sonner — no user record is created in the database and the form retains the admin's input until the endpoint recovers and the admin retries |
| `user` table (D1) | write | The server inserts a new row into the `user` table with the provided name, email, hashed password, and role after verifying the caller's admin role and validating all field values | The insert operation fails and the server returns HTTP 500 — no partial user record is written to the database and the client displays a localized error toast informing the admin that user creation failed |
| Password hashing (Better Auth internal) | transform | The server hashes the plain-text password provided by the app admin before writing the new user record to the `user` table, using the same hashing algorithm as the normal signup flow | Password hashing failure prevents the user record from being created — the server returns HTTP 500 and the client displays a localized error toast, ensuring no plain-text password is ever stored in the database |
| TanStack Query cache | read/write | On successful user creation the cache for the user management list is invalidated to trigger a re-fetch so the new user appears in the list immediately without requiring a manual page reload | Cache invalidation falls back to a stale read — the user management list retains the previous data until the next manual page reload or navigation event that triggers a fresh query for the user list |
| Sonner toast | write | On creation success a localized confirmation toast is displayed, and on creation failure a localized error toast is displayed describing the rejection reason returned by the server | Toast notification degrades silently — the form state itself reflects the outcome through the list refresh on success or the retained form inputs on failure, even without a visible toast notification |
| `@repo/i18n` | read | All form labels, field placeholders, button text, validation messages, error messages, and toast messages on the user creation form are rendered via translation keys at component mount time | Translation function falls back to the default English locale strings so the creation form and all feedback messages remain fully usable and readable when the i18n resource bundle is unavailable for non-English locales |

## Behavioral Flow

1. **[App Admin]** navigates to the user management section of the app
    admin dashboard and clicks the "Create user" button to begin the
    process of adding a new user account to the application

2. **[Client]** renders a localized user creation form with input
    fields for the new user's name, email address, password, and a
    role dropdown — all fields are initially empty and the Submit
    button is disabled until all required fields are filled

3. **[App Admin]** enters the new user's display name into the name
    field, which accepts standard text input and is validated to be
    non-empty after trimming whitespace before the form can be
    submitted to the server

4. **[App Admin]** enters the new user's email address into the email
    field, which is validated for correct email format on the client
    side before the form can be submitted to the server

5. **[App Admin]** enters a password into the password field, which is
    validated to meet the application's password requirements (minimum
    length and complexity) before the form can be submitted

6. **[App Admin]** selects a role from the role dropdown, which
    contains exactly two options: "user" and "admin" — the dropdown
    defaults to "user" and the admin explicitly selects the desired
    role for the new account

7. **[Client]** enables the Submit button because all required fields
    (name, email, password, and role) are filled and pass client-side
    validation, indicating the form is ready for submission

8. **[App Admin]** clicks the Submit button to send the completed
    form data to the server for user account creation

9. **[Client]** transitions the Submit button to a loading state while
    the request is in flight, preventing duplicate submissions until
    the server responds with a success or failure result

10. **[Client]** calls `authClient.admin.createUser({ name, email,
    password, role })` with the form data, sending the creation
    request to the server

11. **[Server]** verifies that the calling user's `user.role` field
    equals `"admin"` — if the caller does not hold the app admin role,
    the server rejects the request with HTTP 403 and no user record is
    created in the database

12. **[Server]** validates the incoming field values — the email
    address is checked for uniqueness against existing records in the
    `user` table, the name is confirmed to be non-empty, and the
    password is confirmed to meet the application's requirements

13. **[Branch — email already in use]** If the submitted email address
    already belongs to another user account in the `user` table, the
    server rejects the request with HTTP 400 and a localized error
    message indicating that the email is already in use — the form
    retains the admin's input so they can correct the email and retry

14. **[Server]** hashes the plain-text password using the same
    algorithm as the normal signup flow before writing the new user
    record, ensuring no plain-text password is stored in the database

15. **[Server]** inserts the new user record into the `user` table
    with the provided name, email, hashed password, and role, and
    returns HTTP 200 confirming that the account was created

16. **[Client]** receives the success response, displays a localized
    toast notification via Sonner confirming that the user account was
    created, and invalidates the TanStack Query cache for the user
    management list to trigger a re-fetch

17. **[Client]** resets the creation form to its initial empty state
    and the new user immediately appears in the user management list
    without requiring a manual page reload

18. **[Branch — no welcome email]** The server does not send a welcome
    email or trigger an email verification step for admin-created
    accounts — the created user can sign in immediately with the
    email and password the app admin provided without verifying their
    email address

19. **[Branch — network error]** If the creation request fails due to
    a network error or timeout, the client displays a generic
    localized error toast via Sonner and re-enables the Submit button
    so the admin can retry the submission without re-entering their
    input

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| user_list_idle | creation_form_open | App admin clicks the "Create user" button on the user management page to open the creation form | Calling user's `user.role` equals `"admin"` and the user management page has fully loaded with the current user list |
| creation_form_open | creation_form_valid | App admin fills in all required fields (name, email, password, role) and all fields pass client-side validation | Name is non-empty after trimming, email matches a valid email format, password meets the application's requirements, and role is selected |
| creation_form_valid | creation_form_open | App admin clears or invalidates one or more required fields so that client-side validation no longer passes for all fields | At least one field fails client-side validation — name is empty, email format is invalid, or password does not meet requirements |
| creation_form_valid | submitting | App admin clicks the Submit button after all fields pass client-side validation and the form is ready for server submission | All required fields are non-empty and pass client-side validation, and the Submit button is in its enabled interactive state |
| submitting | creation_success | Server returns HTTP 200 confirming the new user record was inserted into the `user` table with the provided details | Server-side validation passes, email uniqueness check passes, password hashing completes, and the insert is written to the database |
| submitting | creation_error | Server returns a non-200 error code or the request times out before a response is received | Database insert fails, email uniqueness check fails, authorization check fails, password hashing fails, or network error occurs |
| creation_success | user_list_idle | Client displays the success toast, resets the form to its initial empty state, and the user management list refreshes to show the new user | TanStack Query cache invalidation completes and the user management list re-renders with the newly created user record visible |
| creation_error | creation_form_valid | Client displays the error toast and the form retains the admin's input for correction and retry with the Submit button re-enabled | Error message is visible and the Submit button is re-enabled with the previously entered field values intact for the admin to correct |

## Business Rules

- **Rule app-admin-role-required:** IF the authenticated user's
    `user.role` field does not equal `"admin"` THEN the
    `authClient.admin.createUser()` endpoint rejects the request with
    HTTP 403 AND the server logs the unauthorized attempt with the
    caller's user ID and timestamp before returning the error response
- **Rule password-hashed-before-storage:** IF the server accepts the
    creation request THEN the plain-text password provided by the app
    admin is hashed using the same algorithm as the normal signup flow
    before the new user record is written to the `user` table AND the
    count of plain-text passwords stored in the database equals 0
- **Rule no-welcome-email-triggered:** IF a user account is created
    through the `authClient.admin.createUser()` endpoint THEN no
    welcome email, verification email, or any other automated email
    notification is sent to the new user's email address AND the count
    of emails dispatched during this flow equals 0
- **Rule no-email-verification-required:** IF a user account is
    created through the admin creation flow THEN the new user's email
    address is treated as verified by default AND the user can sign in
    immediately with the provided email and password without completing
    an email verification step
- **Rule role-must-be-user-or-admin:** IF the app admin selects a role
    for the new user account THEN the role value is restricted to
    exactly `"user"` or `"admin"` AND the server rejects any creation
    request with a role value outside of this set with HTTP 400

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| App Admin | Navigate to the user management section, click the "Create user" button, fill in all form fields (name, email, password, role), submit the form to create the new user account, and see the success or error toast | None — the app admin has full access to the user creation flow and all form fields are visible and interactive on the user management page | The "Create user" button, creation form, all input fields, role dropdown, and Submit button are all visible and interactive for users with `user.role` equal to `"admin"` |
| Non-admin authenticated user | None — the user management admin page is not accessible to non-admin users and the route guard redirects or returns HTTP 403 before the page renders | Accessing the user management page, viewing the "Create user" button, opening the creation form, or calling the `authClient.admin.createUser()` endpoint, which rejects with HTTP 403 | The admin user management page is not rendered; the user is redirected or shown a 403 error before any creation controls are mounted |
| Unauthenticated visitor | None — the route guard redirects unauthenticated requests to `/signin` before the user management page component renders any content or data | Accessing the user management page or calling the `authClient.admin.createUser()` endpoint without a valid authenticated session token | The user management page is not rendered; the redirect to `/signin` occurs before any page elements are mounted or visible |

## Constraints

- The `authClient.admin.createUser()` endpoint enforces the app admin
    role server-side by reading the calling user's `user.role` field —
    the count of successful user creations initiated by non-admin
    users equals 0
- The role dropdown on the creation form contains exactly two options:
    `"user"` and `"admin"` — the count of role values outside this set
    that are accepted by the server equals 0
- The password is hashed before storage using the same algorithm as
    the normal signup flow — the count of plain-text passwords stored
    in the `user` table equals 0 at all times after the creation
    completes
- The email uniqueness check runs server-side before the insert is
    written — the count of user records in the `user` table sharing
    the same email address equals 1 at all times after the creation
    completes
- No welcome email or email verification step is triggered by the
    admin creation flow — the count of automated emails dispatched
    during this flow equals 0 for every successful creation
- All form labels, field placeholders, button text, validation
    messages, error messages, and toast messages on the creation form
    are rendered via i18n translation keys — the count of hardcoded
    English string literals in the user creation form component
    equals 0

## Acceptance Criteria

- [ ] Clicking "Create user" on the user management page renders a creation form with empty fields for name, email, password, and a role dropdown — the input values are empty and the Submit button disabled attribute is present
- [ ] The Submit button is disabled when any required field is empty or fails client-side validation — the disabled attribute is present on the Submit button and the count of dispatched creation requests equals 0
- [ ] The Submit button becomes enabled when all required fields are filled and pass client-side validation — the disabled attribute is absent and the button is interactive after all fields are valid
- [ ] Clicking Submit after filling all fields calls `authClient.admin.createUser({ name, email, password, role })` — the mutation invocation count equals 1 and the payload contains all four fields
- [ ] The Submit button transitions to a loading state while the mutation is in flight — the button shows a loading indicator and the count of additional creation requests that can be triggered during this state equals 0
- [ ] On mutation success a localized confirmation toast appears via Sonner — the toast element is present and visible within 500ms of the API returning HTTP 200
- [ ] On mutation success the TanStack Query cache for the user management list is invalidated — the list displays the newly created user and the count of missing new user entries after re-fetch equals 0
- [ ] On mutation success the creation form resets to its initial empty state — all input field values are empty and the Submit button disabled attribute is present after the reset completes
- [ ] On mutation failure due to a duplicate email the client displays a localized error message indicating the email is already in use — the error element is present and the form retains the admin's input with all field values intact
- [ ] On mutation failure due to a network error the client displays a generic localized error toast — the toast element is present and the Submit button returns to its interactive state with the disabled attribute absent
- [ ] A non-admin authenticated user calling `authClient.admin.createUser()` directly receives HTTP 403 — the response status equals 403 and no new user record is inserted into the `user` table
- [ ] The password is hashed before storage — the password column value in the newly created `user` table record is non-empty and does not equal the plain-text value submitted by the app admin
- [ ] No welcome email or verification email is sent after admin-created user account creation — the count of email dispatch calls during the creation flow equals 0
- [ ] The role dropdown contains exactly two options: "user" and "admin" — the option count equals 2 and the default selected value equals "user"
- [ ] Client-side validation rejects an empty name field — the validation error element is present and the Submit button remains disabled when the name field is empty after trimming

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| App admin submits an email address that is already associated with another user account in the `user` table | The server detects the duplicate email during the uniqueness check and returns HTTP 400 with a localized error message — the form retains the admin's input and no new user record is created in the database | HTTP response status equals 400 and the user record count for that email address in the `user` table remains at 1 |
| App admin submits a password that does not meet the application's minimum length or complexity requirements | Client-side validation prevents submission because the password does not meet requirements — the validation error is displayed inline and the Submit button remains disabled until the admin enters a compliant password | The validation error element is present, the Submit button disabled attribute equals true, and the creation request count equals 0 |
| App admin fills in all fields but navigates away from the page before clicking Submit to create the user | No creation request is sent because the admin did not click Submit — no new user record is inserted into the `user` table and the navigation proceeds without triggering any write operation | The network request count to the `authClient.admin.createUser()` endpoint equals 0 and the user record count is unchanged after navigation |
| App admin creates a user with the "admin" role, granting the new user administrative privileges immediately upon creation | The server inserts the new user record with `role = "admin"` — the new user can access admin-only endpoints and pages immediately after signing in with the provided email and password | The new user's `role` field in the `user` table equals `"admin"` and the user can call admin endpoints after authentication |
| Two app admins simultaneously submit creation forms with the same email address from different browser sessions | The first creation request that reaches the database insert succeeds, and the second request fails the email uniqueness check — the server returns HTTP 400 for the second request and only one user record exists for that email | The user record count for the submitted email in the `user` table equals 1 after both requests complete |
| App admin clears the name field entirely and attempts to submit the form with an empty name value after trimming whitespace | Client-side validation prevents submission because the name is empty after trimming — the validation error is displayed inline and the Submit button remains disabled until the admin enters a non-empty name | The validation error element is present, the Submit button disabled attribute equals true, and the creation request count equals 0 |

## Failure Modes

- **Database insert fails when writing the new user record to the user table**
    - **What happens:** The app admin clicks Submit and the client
        sends the `authClient.admin.createUser()` request, but the D1
        database insert fails due to a transient storage error before
        the new user record is committed to the `user` table, leaving
        no new user record in the database.
    - **Source:** Transient Cloudflare D1 database failure or network
        interruption between the Worker and the D1 binding during the
        single-row insert operation that writes the new user record
        with the hashed password and assigned role.
    - **Consequence:** The user account is not created and no record
        exists in the `user` table for the submitted email address,
        while the admin sees an error toast on the creation form and
        the user management list remains unchanged.
    - **Recovery:** The server returns HTTP 500 and the client displays
        a localized error toast via Sonner — the admin retries the
        creation once the D1 database recovers and the Submit button is
        re-enabled for another submission attempt.
- **Non-admin user bypasses the client guard and calls the admin createUser endpoint directly**
    - **What happens:** A user without the app admin role crafts a
        direct HTTP request to the `authClient.admin.createUser()`
        endpoint using a valid session cookie, bypassing the
        client-side UI that hides admin controls from non-admin users,
        and attempts to create a new user account without
        authorization.
    - **Source:** Adversarial or accidental action where a non-admin
        user sends a hand-crafted HTTP request to the admin creation
        endpoint with a valid session token, circumventing the
        client-side visibility guard that conditionally renders admin
        controls only for users with `user.role` equal to `"admin"`.
    - **Consequence:** Without server-side enforcement any
        authenticated user could create new accounts with arbitrary
        roles including admin, breaking the administrative boundary
        and enabling privilege escalation through unauthorized account
        creation.
    - **Recovery:** The creation handler rejects the request with
        HTTP 403 after verifying the calling user's `user.role` field
        in the `user` table — the server logs the unauthorized attempt
        with the caller's user ID and timestamp, and no new user
        record is written to the database.
- **Password hashing fails before the new user record is written to the database**
    - **What happens:** The server receives a valid creation request
        from an authorized app admin, but the password hashing
        operation fails due to an internal error in the hashing
        library or an out-of-memory condition before the hashed value
        can be produced for storage in the `user` table.
    - **Source:** Internal failure in the password hashing algorithm
        execution (such as the bcrypt or scrypt library encountering
        a runtime error) or a resource constraint on the Cloudflare
        Worker that prevents the hashing computation from completing
        within the execution time limit.
    - **Consequence:** The new user record is not created because the
        server cannot produce a hashed password — no plain-text
        password is written to the database and the admin sees an
        error toast indicating that the creation failed without any
        partial record in the `user` table.
    - **Recovery:** The server returns HTTP 500 and the client
        displays a localized error toast via Sonner — the admin
        retries the creation after the transient condition resolves
        and the Submit button is re-enabled for another attempt.
- **TanStack Query cache invalidation fails after a successful admin creation**
    - **What happens:** The creation succeeds and the server inserts
        the new user record into the `user` table in D1, but the
        client-side TanStack Query cache invalidation does not trigger,
        leaving the user management list without the newly created user
        despite the successful server-side insert.
    - **Source:** A cache invalidation gap where the mutation success
        handler fails to call the invalidation function due to a
        runtime error, an unhandled promise rejection, or a query key
        mismatch between the mutation and the user management list
        data query.
    - **Consequence:** The admin sees the success toast but the user
        management list does not display the newly created user,
        creating a confusing inconsistency that persists until a
        manual page reload triggers a fresh query for the user list.
    - **Recovery:** The mutation success handler notifies the user
        management list query cache to invalidate and refetch — if
        invalidation fails the admin falls back to a manual page
        reload that triggers a fresh query and resolves the stale
        list data across the user management page.

## Declared Omissions

- This specification does not address editing or updating a user's
    details after creation — that behavior is defined in
    `app-admin-updates-user-details.md` covering the edit form with
    its own field validation and mutation endpoint
- This specification does not address banning or unbanning a user
    account from the admin interface — that behavior is defined in a
    separate spec covering the ban lifecycle including ban reason,
    expiration date, and enforcement at sign-in time
- This specification does not address deleting a user account from
    the admin interface — that behavior is defined in a separate spec
    covering cascading cleanup of user data, sessions, and
    organization memberships upon account deletion
- This specification does not address rate limiting on the
    `authClient.admin.createUser()` endpoint — that behavior is
    enforced by the global rate limiter defined in `api-framework.md`
    covering all mutation endpoints uniformly across the API layer
- This specification does not address the normal self-service signup
    flow where users create their own accounts — that behavior is
    defined in a separate spec covering public registration with email
    verification and welcome email delivery

## Related Specifications

- [app-admin-updates-user-details](app-admin-updates-user-details.md)
    — Admin user editing flow where an app admin modifies an existing
    user's display name, email, and profile image, which operates on
    the same `user` table records that this creation flow inserts
- [app-admin-lists-and-searches-users](app-admin-lists-and-searches-users.md)
    — Admin user listing flow that displays the user management page
    where the "Create user" button is located, and where the newly
    created user appears after the TanStack Query cache is invalidated
- [banned-user-attempts-sign-in](banned-user-attempts-sign-in.md) —
    Ban enforcement flow that checks the `user.banned` field at sign-in
    time, which operates on the same `user` table records that this
    admin creation flow inserts with a default unbanned status
- [auth-server-config](../foundation/auth-server-config.md) — Better
    Auth server configuration including the admin plugin that validates
    the `user.role` field and exposes the
    `authClient.admin.createUser()` endpoint used by this
    specification's creation flow
- [database-schema](../foundation/database-schema.md) — Schema
    definition for the `user` table that stores the name, email, hashed
    password, and role fields written by the admin creation mutation
    handler in this specification
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization
    infrastructure providing translation keys for all creation form
    labels, field placeholders, button text, validation messages, toast
    messages, and error descriptions rendered on the user creation form

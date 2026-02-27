---
id: SPEC-2026-024
version: 1.0.0
created: 2026-02-27
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Creates First Organization

## Intent

This spec defines the onboarding flow a newly registered user completes
to create their first organization in DoCodeGo. After signing up, a user
who belongs to no organizations is automatically redirected from `/app`
to `/app/onboarding`, where they are presented with a form to name their
organization and claim a unique URL slug. As the user types, the client
auto-generates a slug from the organization name, validates the format
client-side, and debounce-checks slug availability against the server.
When the form is submitted, the server creates the organization, sets the
user as its owner, activates the new organization on the session, and
redirects the user to the organization's dashboard. Users who already
belong to at least one organization, including those who joined via
invitation, never see the onboarding page — they are routed directly to
their active organization's dashboard.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth (`organization` plugin) | read/write | `authClient.organization.checkSlug({ slug })` is called for slug availability and `authClient.organization.create({ name, slug })` is called on form submission | Server returns HTTP 500 and the global error handler falls back to a generic JSON error response — the user cannot complete onboarding until the service recovers |
| `organization` table (D1) | read/write | Slug uniqueness check reads existing slugs and organization creation inserts a new row with `name`, `slug`, `createdAt`, and `createdBy` fields | Route handlers return HTTP 500 and the error handler degrades gracefully while read-only routes remain operational |
| `member` table (D1) | write | Inserting the owner membership record linking the new user to the newly created organization with the `owner` role | Membership creation fails with HTTP 500 and the organization row is rolled back to prevent orphaned records with 0 owner members |
| `session` (Better Auth) | write | `activeOrganizationId` is set on the session to the newly created organization's ID upon successful creation | Session update fails silently and the user is redirected to `/app` where the active organization resolver falls back to selecting the first available organization |
| `@repo/i18n` | read | Rendering all onboarding page labels, slug preview text, validation messages, and button text | Translation function falls back to the default English locale strings so the form remains fully usable with 0 broken UI elements |

## Behavioral Flow

1. **[System]** detects that the authenticated user belongs to 0 organizations
    after sign-in and immediately redirects the user from `/app` to
    `/app/onboarding` before the dashboard renders
2. **[User]** arrives at `/app/onboarding` and sees a clean form with
    two labeled fields — an organization name input and a URL slug input —
    plus a slug preview line showing `docodego.com/app/{slug}/`
3. **[User]** begins typing an organization name into the name field,
    and the client responds by computing a derived slug on every keystroke
4. **[Client]** calls the `toSlug()` function on the current name value,
    converting it to lowercase, replacing spaces with hyphens, and stripping
    all characters that are not lowercase letters, numbers, or hyphens,
    then writes the result into the slug field
5. **[Client]** updates the slug preview below the slug field to reflect
    the derived value in real time, showing the full URL the organization
    will occupy at `docodego.com/app/{slug}/`
6. **[User]** optionally edits the slug field manually; once the user
    modifies the slug directly, the client stops overwriting the slug field
    on subsequent name edits so the custom slug is preserved
7. **[Client]** validates the slug format on every change to the slug field:
    minimum 3 characters, only lowercase letters, numbers, and hyphens
    allowed, and no leading or trailing hyphens — inline validation errors
    are displayed for each violated rule
8. **[Client]** waits for the user to stop typing into the slug field and
    then fires a debounced availability check by calling
    `authClient.organization.checkSlug({ slug })` to ask the server whether
    the slug is already taken
9. **[Server]** queries the `organization` table for an existing row whose
    `slug` column matches the submitted value and responds with an availability
    result indicating taken or available
10. **[Client]** displays a visual indicator next to the slug field showing
    whether the slug is available or taken — a taken slug prevents form
    submission until the user chooses a different value
11. **[User]** fills in both fields to their satisfaction and clicks the
    submit button, which is enabled only when the organization name is
    non-empty, the slug passes format validation, and the availability check
    shows the slug is not taken
12. **[Client]** calls `authClient.organization.create({ name, slug })` with
    the final field values, disabling the submit button and showing a loading
    indicator while the request is in flight
13. **[Server]** inserts a new row into the `organization` table with the
    supplied `name` and `slug` values, then inserts a row into the `member`
    table marking the requesting user as the `owner` of the new organization
14. **[Server]** updates the session's `activeOrganizationId` field to the
    newly created organization's ID so subsequent requests are scoped to
    the new organization
15. **[Server]** returns a success response containing the new organization's
    ID and slug
16. **[Client]** receives the success response and redirects the user to
    `/app/{slug}/`, which is the dashboard for the newly created organization
17. **[Branch — slug already taken at submission time]** If the slug was
    claimed by another user between the last availability check and the
    create call, the server returns HTTP 409 and the client displays a
    localized error message informing the user the slug is no longer available
    and prompting them to choose a different one
18. **[Branch — user already has organization membership]** If a user who
    already belongs to at least one organization navigates directly to
    `/app/onboarding`, the client detects the existing membership and
    redirects them to `/app` without rendering the onboarding form

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| unauthenticated | redirected_to_onboarding | User is authenticated and belongs to 0 organizations | Count of organization memberships for the user equals 0 |
| redirected_to_onboarding | form_idle | Onboarding page finishes rendering | All form fields are empty and the slug preview is blank |
| form_idle | name_entry | User types at least 1 character into the name field | Name field value length is greater than 0 |
| name_entry | slug_derived | Client runs `toSlug()` on the name value | Name field value is non-empty and `toSlug()` returns a non-empty string |
| slug_derived | slug_checking | User stops typing and the debounce timer fires | Slug value passes format validation — at least 3 characters, only valid characters, no leading or trailing hyphens |
| slug_checking | slug_available | Server returns availability = true from checkSlug | HTTP response indicates the slug is not present in the `organization` table |
| slug_checking | slug_taken | Server returns availability = false from checkSlug | HTTP response indicates the slug is already present in the `organization` table |
| slug_taken | slug_checking | User edits the slug field and debounce timer fires | New slug value passes format validation |
| slug_available | submitting | User clicks the submit button | Name is non-empty, slug is valid, slug indicator shows available |
| submitting | success | Server returns HTTP 200 from the create endpoint | Organization and membership rows are present in the database |
| submitting | conflict_error | Server returns HTTP 409 from the create endpoint | Slug was claimed between the availability check and the create call |
| conflict_error | slug_checking | User edits the slug field and debounce timer fires | New slug value passes format validation |
| success | redirected_to_dashboard | Client processes the response and triggers navigation | Response contains a non-empty `slug` field used to build the redirect URL |

## Business Rules

- **Rule first-time-only:** IF an authenticated user navigates to `/app` AND
    the count of organization memberships for that user equals 0 THEN the
    server redirects the user to `/app/onboarding` — users with at least 1
    membership are never redirected to the onboarding page
- **Rule invitation-bypass:** IF a user joined via an organization invitation
    AND the invitation was accepted before the user reached `/app` THEN the
    user already has 1 or more memberships and the onboarding redirect does
    not fire, routing them directly to their active organization's dashboard
- **Rule slug-format:** IF the slug value does not match the pattern
    `^[a-z0-9][a-z0-9-]*[a-z0-9]$` with a minimum length of 3 characters
    THEN the server rejects the create request with HTTP 400 and the client
    displays a localized validation error with the count of violated rules
- **Rule slug-uniqueness:** IF a create request is received AND an existing
    `organization` row has a `slug` column value equal to the submitted slug
    THEN the server returns HTTP 409 and the client prompts the user to choose
    a different slug value
- **Rule owner-assignment:** IF an organization is created successfully THEN
    the server inserts exactly 1 row into the `member` table with the `role`
    field set to `owner` and the `userId` field set to the requesting user's
    ID — the count of owner membership rows for the new organization equals 1
- **Rule auto-slug-stop:** IF the user has manually edited the slug field at
    least 1 time THEN subsequent keystrokes in the name field do not overwrite
    the slug field — the auto-generation ceases permanently for that form session

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated user with 0 organization memberships | View and submit the onboarding form, check slug availability, and create exactly 1 new organization in this flow | Create a second organization via the onboarding form — they are redirected away from `/app/onboarding` once they have 1 membership | Sees only the onboarding form with 0 dashboard chrome elements rendered |
| Authenticated user with 1 or more organization memberships | Navigate directly to `/app/{slug}/` and use all organization features they are authorized for within existing memberships | Access `/app/onboarding` — they are redirected to `/app` with 0 onboarding form elements visible | Sees the standard application dashboard with 0 onboarding-related UI elements |
| Unauthenticated visitor | None — all `/app` routes require authentication | Access `/app/onboarding` — they are redirected to `/signin` with 0 onboarding form elements rendered | Sees the sign-in page with 0 authenticated UI elements |

## Constraints

- The onboarding redirect from `/app` to `/app/onboarding` is evaluated
    server-side on every request to `/app` — the membership count query runs
    on the server and the count of client-side membership checks equals 0 to
    prevent bypass via JavaScript manipulation.
- The slug uniqueness check at form submission is enforced server-side with
    a unique index constraint on the `slug` column of the `organization` table
    — the database returns a constraint violation if 2 rows share the same
    slug, making client-side debounce checks an optimization only, not the
    authoritative uniqueness gate.
- The `toSlug()` transformation is deterministic — identical name inputs
    always produce identical slug outputs. The transformation applies
    lowercase conversion, space-to-hyphen replacement, and non-alphanumeric
    character removal in that fixed order with 0 deviations.
- The slug preview URL displayed below the slug field always reflects the
    current slug field value in real time — the count of milliseconds between
    a slug field change and the preview update equals 0 (synchronous update
    with no debounce on the preview itself, only on the server availability
    check).

## Acceptance Criteria

- [ ] Unauthenticated user navigating to `/app` is redirected to `/signin` — window location pathname equals `/signin` and the onboarding form is absent
- [ ] Authenticated user with 0 org memberships navigating to `/app` is redirected to `/app/onboarding` — onboarding form element count equals 1 and the signin form is absent
- [ ] Authenticated user with 1+ org memberships navigating to `/app/onboarding` is redirected to `/app` — onboarding form element count equals 0
- [ ] Onboarding form renders exactly 2 input fields (name and slug) — visible form input element count equals 2
- [ ] Typing in name field auto-populates slug via `toSlug()` — slug field is non-empty and the slug character count equals the transformed name length after each valid keystroke
- [ ] After manually editing slug field, further name keystrokes do not overwrite it — slug value remains non-empty and unchanged after 3 subsequent name keystrokes
- [ ] Slug preview updates in real time — preview text content equals `docodego.com/app/{slug}/` and stale preview count equals 0
- [ ] Slug shorter than 3 characters triggers validation error — error element is present and slug character count is less than 3
- [ ] Slug containing uppercase letters triggers validation error — error element is present and disabled attribute is present on submit button
- [ ] Slug with leading hyphen triggers validation error — error element is present and disabled attribute is present on submit button
- [ ] Slug with trailing hyphen triggers validation error — error element is present and disabled attribute is present on submit button
- [ ] Debounced availability check fires after user stops typing — network request to `checkSlug` is present within 500ms of last keystroke
- [ ] Available slug shows availability indicator — indicator element is present and submit button disabled attribute is absent
- [ ] Taken slug shows taken indicator and disables submit — taken indicator is present and disabled attribute is present on submit button
- [ ] Successful create inserts exactly 1 row into `organization` table — row count for submitted slug equals 1 and duplicate slug row count equals 0
- [ ] Successful create inserts exactly 1 row into `member` table with `role` = `owner` — member row is present and `userId` field is non-empty
- [ ] Successful create updates session `activeOrganizationId` — session field value is non-empty and equals the new organization ID
- [ ] Successful create redirects to `/app/{slug}/` — navigation event count equals 1 and the onboarding form element count equals 0 after redirect
- [ ] Server returning HTTP 409 on create displays conflict error and re-enables submit — error element is present and disabled attribute is absent from submit button
- [ ] All UI text is rendered via i18n keys — hardcoded English string count in onboarding components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User types a name that produces a slug shorter than 3 characters, such as a single letter like `A` | The `toSlug()` function returns `a` which is 1 character — the client shows a format validation error and the submit button remains disabled because the slug length is less than 3 | The error element is present and the disabled attribute is present on the submit button |
| User types a name with only special characters such as `!!!` which produces an empty slug after `toSlug()` strips them all | The slug field is empty after transformation — the client shows a required field error and the debounced availability check is not fired because the slug is empty | The error element is present and the count of network requests to checkSlug equals 0 |
| User submits the form and the availability check shows available, but another user claims the same slug in the interval between the check and the create request | The server's unique index constraint returns a conflict error and the server responds with HTTP 409 — the client displays a localized conflict message and prompts the user to choose a different slug | The HTTP response status equals 409 and the conflict error element is present |
| User clicks the submit button multiple times within 300 milliseconds before the first create request completes | The client disables the submit button on the first click and ignores subsequent clicks — the server receives exactly 1 create request per form submission | The disabled attribute is present on the submit button within 50 milliseconds of the first click and the network log shows exactly 1 POST request |
| User pastes a mixed-case slug value such as `My-Org-2026` directly into the slug field | The format validation detects uppercase characters and displays a localized error message — the submit button remains disabled because the slug does not match the allowed pattern | The error element is present and the disabled attribute is present on the submit button |
| The debounced availability check network request fails with a 500 error before the user submits | The client treats an errored availability check as inconclusive and keeps the submit button disabled until a successful check confirms availability — the count of submit requests sent during an errored check state equals 0 | The submit button disabled attribute is present and the count of create POST requests equals 0 |

## Failure Modes

- **Organization creation fails due to transient database write error**
    - **What happens:** The `authClient.organization.create({ name, slug })`
        call reaches the server but the D1 database write to the `organization`
        or `member` table fails due to a transient I/O error or connection
        timeout, leaving the user on the onboarding form with no organization
        created.
    - **Source:** External database service degradation or transient network
        error between the Cloudflare Worker and the D1 instance during the
        insert transaction.
    - **Consequence:** The user receives an HTTP 500 error response and remains
        on the onboarding form without an organization — the session's
        `activeOrganizationId` is not updated and the user is not redirected
        to any dashboard.
    - **Recovery:** The server rolls back any partial writes and returns error
        HTTP 500 — the client re-enables the submit button and notifies the user
        with a localized error message prompting them to retry the form submission
        when the service recovers.
- **Slug race condition creates a duplicate between availability check and create**
    - **What happens:** Two users independently check the same slug value,
        both receive an available result, and then both submit creation requests
        simultaneously — the second create request hits the unique index
        constraint after the first succeeds.
    - **Source:** Race condition between concurrent organization creation
        requests arriving at the server within milliseconds of each other for
        the same slug value.
    - **Consequence:** The second user's create call fails with a constraint
        violation despite the client-side availability indicator showing
        available — the second user is unexpectedly blocked from their chosen
        slug.
    - **Recovery:** The server detects the constraint violation and returns
        error HTTP 409 — the client degrades to displaying a localized conflict
        message and re-enables the slug field so the user retries with a
        different value.
- **Slug availability check is unavailable during form interaction**
    - **What happens:** The `authClient.organization.checkSlug({ slug })`
        request fails or times out, leaving the availability indicator in an
        inconclusive state — the user cannot determine whether their chosen
        slug is free to use.
    - **Source:** Transient network error, Cloudflare Worker cold-start delay,
        or D1 read timeout between the client browser and the API endpoint
        during the debounced availability check.
    - **Consequence:** The user cannot advance to form submission because the
        submit button remains disabled until a successful availability check
        confirms the slug — the onboarding flow stalls with the user waiting
        for network recovery.
    - **Recovery:** The client retries the availability check automatically
        after the next slug field change fires the debounce timer — the user
        can edit the slug by 1 character and back to re-trigger the check, and
        the page logs the failed check to the browser console for diagnostics.
- **Session update fails after successful organization creation**
    - **What happens:** The organization and member rows are written
        successfully but the subsequent call to update `activeOrganizationId`
        on the session fails due to a transient error, leaving the session
        pointing to no active organization.
    - **Source:** Transient session store failure occurring between the
        successful D1 write and the session mutation in Better Auth's session
        layer, resulting in an inconsistent state.
    - **Consequence:** The user is redirected to `/app/{slug}/` but the session
        carries no active organization, causing the dashboard to show an empty
        state or redirect back to onboarding for a second time.
    - **Recovery:** The `/app` redirect guard falls back to selecting the
        first organization from the user's membership list if `activeOrganizationId`
        is absent — the user lands on their dashboard with the correct organization
        context restored without requiring another form submission.

## Declared Omissions

- This specification does not address the organization settings page, member
    invitation flow, or any post-creation configuration — those behaviors are
    defined in separate specs covering organization management
- This specification does not address the case where a user is added to an
    organization by an administrator through a back-office tool — that path
    bypasses the onboarding form entirely and is out of scope for this spec
- This specification does not address billing, plan selection, or subscription
    creation during onboarding — those behaviors are defined in payment and
    subscription specs as separate post-creation concerns
- This specification does not address the organization switcher or multi-org
    navigation — those behaviors are defined in the active organization
    management spec which handles users who belong to multiple organizations
- This specification does not address rate limiting on the slug availability
    check endpoint — that behavior is enforced by the global rate limiter
    defined in `api-framework.md`

## Related Specifications

- [auth-server-config](../foundation/auth-server-config.md) — defines the
    Better Auth server configuration including the `organization` plugin that
    powers `checkSlug` and `create` operations used in this flow
- [database-schema](../foundation/database-schema.md) — defines the schema
    for the `organization` and `member` tables written during organization
    creation, including the unique index on the `slug` column
- [session-lifecycle](session-lifecycle.md) — defines post-authentication
    session management including how `activeOrganizationId` is set and read
    across requests after organization creation
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — defines
    the sign-in flow that precedes this onboarding flow for users who have
    just created their account via email OTP
- [api-framework](../foundation/api-framework.md) — defines the Hono
    middleware stack, global error handler, and rate limiting that wrap the
    slug check and organization create API endpoints
- [shared-i18n](../foundation/shared-i18n.md) — defines the i18n
    infrastructure providing translation keys for all onboarding form labels,
    validation messages, and the slug preview URL text

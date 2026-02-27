---
id: SPEC-2026-025
version: 1.0.0
created: 2026-02-27
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Creates an Organization

## Intent

This spec defines the flow for creating an additional organization from within
the DoCodeGo dashboard. A user who already belongs to at least one organization
opens the OrgSwitcher dropdown in the app header, selects the "Create
organization" option, and fills in a name and URL slug on the creation form. The
slug auto-generates from the name via `toSlug()` and is validated for format and
uniqueness with a debounced availability check. On submit, the app calls
`authClient.organization.create({ name, slug })`, the user becomes the owner of
the new organization, the active session switches to the new org, and the client
navigates to `/app/{newSlug}/`. This spec ensures that slug uniqueness is
enforced before submission, that the OrgSwitcher reflects the new org
immediately, and that the user can switch back to any previously existing org at
any time through the same switcher.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth server SDK (`organization` plugin) | write | Client calls `authClient.organization.create({ name, slug })` on form submission to create the new organization and assign ownership to the calling user | The server returns HTTP 500 and the client falls back to displaying a localized error message on the form while keeping the form open so the user can retry the submission |
| Better Auth slug check endpoint (`authClient.organization.checkSlug`) | read | Client calls the endpoint in a debounced handler after each keystroke in the slug field to determine whether the slug is already taken before the user submits | The check request times out and the client degrades to allowing form submission without pre-validation, relying on the server-side uniqueness constraint to reject duplicates at submission time |
| D1 (Cloudflare SQL) via Drizzle ORM | read/write | Server reads existing slugs for uniqueness checks and writes the new `organization` row and `member` row during creation | The database write fails, the transaction rolls back, the server returns HTTP 500, and the client falls back to displaying a localized error message with a retry option |
| `@repo/i18n` | read | All form labels, placeholders, validation messages, and error strings in the creation form are rendered via i18n translation keys | Translation function falls back to the default English locale strings so the form remains functional but untranslated for non-English users |

## Behavioral Flow

1. **[User]** is authenticated and belongs to at least one existing organization,
    opens the app header, and clicks on the OrgSwitcher component which displays
    a dropdown listing all organizations the user is currently a member of,
    sorted alphabetically
2. **[User]** clicks the "Create organization" option at the bottom of the
    OrgSwitcher dropdown, which closes the dropdown and opens the organization
    creation form
3. **[Client]** renders the organization creation form with a localized
    organization name input, a URL slug input, and a slug preview showing the
    resulting URL in the format `docodego.com/app/{slug}/`
4. **[User]** types an organization name into the name input field; as the user
    types, the client automatically generates the slug value by calling
    `toSlug()` on the current name, converting it to lowercase, replacing spaces
    with hyphens, and stripping special characters, then populates the slug field
    with the result
5. **[Client]** fires a debounced availability check by calling
    `authClient.organization.checkSlug({ slug })` after each auto-generated or
    manually entered slug value, then displays the result as an inline indicator
    showing whether the slug is available or already taken
6. **[Branch — user edits the slug manually]** If the user directly edits the
    slug input field, the client disables further auto-generation from the name
    field for the remainder of the session on this form, so that subsequent name
    changes do not overwrite the user's manually chosen slug value
7. **[User]** reviews the slug preview showing the full URL
    `docodego.com/app/{slug}/` and confirms the name and slug are correct, then
    clicks the submit button to create the organization
8. **[Client]** validates the slug format client-side before submission —
    minimum 3 characters, lowercase letters, numbers, and hyphens only, no
    leading or trailing hyphens — and if validation fails the client displays a
    localized inline error message beneath the slug field without sending any
    request to the server
9. **[Client]** calls `authClient.organization.create({ name, slug })` if
    client-side validation passes and the slug availability check returned
    available, disabling the submit button and displaying a loading indicator
    while the request is in flight
10. **[Server]** receives the creation request, validates the slug format and
    uniqueness against the database one final time, creates the `organization`
    row with the provided name and slug, and creates a `member` row linking the
    calling user to the new organization with the `owner` role
11. **[Server]** updates the caller's session by setting `activeOrganizationId`
    to the ID of the newly created organization so that subsequent authenticated
    requests are scoped to the new org, then returns HTTP 200 with the new
    organization object
12. **[Client]** receives the successful response, navigates to
    `/app/{newSlug}/` to land the user on the new organization's dashboard, and
    the OrgSwitcher dropdown now includes the new organization alongside all
    previously existing organizations so the user can switch back at any time
13. **[Branch — slug already taken at submission time]** If the server-side
    uniqueness check fails because another user created an organization with the
    same slug between the availability check and the submission, the server
    returns HTTP 409 and the client displays a localized inline error message
    prompting the user to choose a different slug, keeping the form open with
    all previously entered values intact

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| org_switcher_closed | org_switcher_open | User clicks the OrgSwitcher component in the app header | User has at least 1 existing organization membership |
| org_switcher_open | creation_form | User clicks "Create organization" at the bottom of the switcher dropdown | None |
| creation_form | creation_form (slug_auto_generated) | User types in the name field and the slug field is still in auto-generate mode | `slugManuallyEdited` equals false |
| creation_form | creation_form (slug_manual) | User directly edits the slug input field for the first time | `slugManuallyEdited` transitions from false to true and remains true for the lifetime of this form |
| creation_form | creation_form (slug_checking) | Client fires the debounced slug availability check after a keystroke | Slug value is non-empty |
| creation_form (slug_checking) | creation_form (slug_available) | Server returns available status for the slug | Response indicates slug is not taken |
| creation_form (slug_checking) | creation_form (slug_taken) | Server returns taken status for the slug | Response indicates slug is already in use |
| creation_form | submitting | User clicks the submit button and client-side validation passes | Slug length is at least 3, slug matches `^[a-z0-9][a-z0-9-]*[a-z0-9]$`, slug availability check returned available |
| submitting | org_created | Server returns HTTP 200 with the new organization object | Database write commits successfully |
| submitting | creation_form (server_error) | Server returns HTTP 409 or HTTP 500 | Slug conflict or database failure |
| org_created | dashboard | Client navigates to `/app/{newSlug}/` | `activeOrganizationId` has been set to the new org's ID |

## Business Rules

- **Rule slug-format:** IF the user submits the creation form THEN the slug must
    match the pattern `^[a-z0-9][a-z0-9-]*[a-z0-9]$` AND the slug length must
    be at least 3 characters AND the count of uppercase letters, spaces, and
    special characters other than hyphens in the slug must equal 0
- **Rule slug-uniqueness:** IF the slug passes format validation THEN the server
    queries the `organization` table and the slug must not match any existing row
    AND if a conflict exists the server returns HTTP 409 with a slug-conflict
    error code
- **Rule auto-generate-disable:** IF the user directly edits the slug input
    field THEN the client sets `slugManuallyEdited` to true AND subsequent
    changes to the name field no longer trigger auto-generation, ensuring the
    user's manual slug choice is preserved
- **Rule owner-role:** IF the organization creation request succeeds THEN the
    server creates a `member` row linking the calling user to the new
    organization with the role set to `owner` AND the count of other roles
    assigned to the creator equals 0
- **Rule active-org-switch:** IF the organization is created successfully THEN
    the server sets `activeOrganizationId` on the caller's session to the new
    organization's ID so that the next authenticated request is scoped to the
    new org AND the previous active organization is no longer the active org
    until the user explicitly switches back

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated user (any role in any existing org) | Open the OrgSwitcher dropdown, click "Create organization," fill and submit the creation form, and become owner of the newly created organization | Create an organization with a slug that is already in use by another organization (server returns HTTP 409 rejection) | Sees all organizations they are a member of in the OrgSwitcher dropdown and sees the "Create organization" option at the bottom of the dropdown |
| Unauthenticated visitor | None — all dashboard pages require an active session and the auth guard redirects to `/signin` before any dashboard component renders | Access the OrgSwitcher or organization creation form (auth guard blocks access before rendering) | Cannot see the OrgSwitcher or creation form because the auth guard redirects to `/signin` before the dashboard layout renders |

## Constraints

- The slug must be at least 3 characters long, contain only lowercase letters,
    numbers, and hyphens, and must not start or end with a hyphen — the count
    of slugs that violate this pattern accepted by the server equals 0
- The slug uniqueness check is enforced both client-side (debounced availability
    call) and server-side (uniqueness constraint at submission) — a slug that is
    taken at submission time causes the server to return HTTP 409 regardless of
    whether the client-side check passed
- Auto-generation from the name uses `toSlug()` — the function lowercases the
    input, replaces spaces with hyphens, and strips all special characters that
    are not alphanumeric or hyphens, producing a value that always passes format
    validation
- Manually editing the slug field disables further auto-generation for the
    lifetime of the form instance — the count of auto-generation triggers after
    `slugManuallyEdited` equals true must be 0
- The creating user is assigned the `owner` role in the new organization — the
    count of `member` rows linking the creator to the new org with a role other
    than `owner` equals 0
- The session `activeOrganizationId` is updated to the new org's ID immediately
    on successful creation — all subsequent API calls from the client include
    the new org's ID in the session context before the client navigates to the
    new org's dashboard

## Acceptance Criteria

- [ ] The OrgSwitcher dropdown contains a "Create organization" option — the option element is present in the dropdown when the user opens the OrgSwitcher component in the app header
- [ ] Clicking "Create organization" opens the creation form — the form element is present and visible after the click, and the OrgSwitcher dropdown element is absent from the DOM
- [ ] Typing in the name field auto-generates a slug within 300ms — the slug field value updates within 300ms of each keystroke when `slugManuallyEdited` equals false and the field value is non-empty
- [ ] The auto-generated slug violates format rules 0 times — the count of slugs produced by `toSlug()` that contain uppercase letters, spaces, or characters other than `[a-z0-9-]` equals 0
- [ ] Manually editing the slug disables auto-generation — after the first direct edit the slug field value remains unchanged when the name field changes, and the count of auto-generation triggers equals 0
- [ ] The slug preview text equals `docodego.com/app/{slug}/` — the preview element's text content matches the pattern `docodego.com/app/[a-z0-9-]+/` and updates within 100ms of each slug field change
- [ ] The availability check network request is present within 500ms of the last keystroke — the request to `checkSlug` is present in the activity log and the inline indicator element is present after the response returns
- [ ] Submitting with a slug shorter than 3 characters sends 0 requests to the creation endpoint — the error element is present beneath the slug field and the count of POST requests to `organization.create` equals 0
- [ ] Submitting with a slug containing uppercase letters sends 0 requests — the validation error element is present and the count of POST requests to `organization.create` equals 0 for any slug matching `[A-Z!@#$%^&*]`
- [ ] Clicking submit when validation passes sends 1 request — the `organization.create` network request is present, the submit button `disabled` attribute is present during the request, and the loading indicator element is present
- [ ] The server returns 200 and the client navigates within 1000ms — the HTTP response status equals 200 and the window location pathname changes to `/app/{newSlug}/` within 1000ms of receiving the response
- [ ] The OrgSwitcher list count equals the previous count plus 1 — after creation the count of organization items in the OrgSwitcher dropdown equals the count before creation plus 1
- [ ] The creator's `member` row role equals `owner` — the `role` field on the `member` row linking the creator to the new organization equals `owner` and the count of other role values on that row equals 0
- [ ] The session `activeOrganizationId` equals the new org's ID — the session object returned by the server contains `activeOrganizationId` equal to the ID of the newly created organization and the value is non-empty
- [ ] A slug conflict returns 409 and the form remains present — the HTTP response status equals 409 on a duplicate slug submission and the form element is present with the previously entered name value intact
- [ ] The count of hardcoded English strings in the creation form components equals 0 — all labels, placeholders, error messages, and button text are rendered via i18n translation keys with 0 literal English strings

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| Two users submit the same slug at exactly the same time before either availability check has returned a conflict | The server's uniqueness constraint ensures only 1 creation succeeds; the second request receives HTTP 409 and the client displays a localized slug-conflict error prompting the user to choose a different slug | The first response status equals 200, the second response status equals 409, and the database contains exactly 1 organization row with that slug |
| The user types a name that produces a slug shorter than 3 characters, such as "AB" which generates "ab" | The auto-generated slug fails the minimum-length validation and the client displays a localized error beneath the slug field, disabling the submit button until the slug is at least 3 characters long | The error element is present with a minimum-length message and the submit button's disabled attribute is set |
| The user types a name containing only special characters, such as "!!!," which produces an empty slug after `toSlug()` strips all characters | The slug field is empty and the client shows a localized validation error prompting the user to enter a valid name or manually specify a slug of at least 3 characters | The slug field value is empty or equals an empty string and the error element is present beneath the slug field |
| The availability check request times out because the API is unreachable for more than 5 seconds | The client degrades to allowing form submission without pre-validation and relies on the server-side uniqueness check at submission time to enforce the constraint | The availability indicator shows a neutral or unknown state and the submit button is enabled, allowing the user to proceed |
| The user submits the form while the availability check request is still in flight and has not yet returned a result | The client waits for the availability check to complete before enabling the submit button, or shows a pending state indicator; the server independently validates the slug uniqueness at submission time regardless of client state | The submit button remains disabled or in a loading state until the availability check resolves, and the server's response determines the final outcome |
| The user navigates away from the creation form by clicking another org in the OrgSwitcher before submitting | The form is closed and 0 creation requests are sent to the server, leaving all existing organizations unchanged | The form element is absent from the DOM after navigation and the organization count in the database is unchanged |

## Failure Modes

- **Organization creation fails due to a database write error during the server-side transaction for the new organization row**
    - **What happens:** The client calls `authClient.organization.create({ name, slug })` but the D1 database returns an error during the write of the `organization` or `member` row, causing the transaction to roll back and leaving no partial records in the database.
    - **Source:** Transient D1 database failure, Cloudflare Workers resource exhaustion, or a network interruption between the Worker and the D1 service.
    - **Consequence:** The user sees no new organization in the OrgSwitcher, the session `activeOrganizationId` is unchanged, and the user remains on the creation form without being redirected to the new org's dashboard.
    - **Recovery:** The server returns HTTP 500 and the client falls back to displaying a localized error message on the form while re-enabling the submit button so the user can retry the creation after the transient issue resolves.
- **Slug conflict at submission time after a successful availability check because another user registered the same slug between the check and the submission**
    - **What happens:** The client's debounced availability check returns available for the chosen slug, but between that check and the form submission, a different user creates an organization with the identical slug, making it unavailable by the time the server processes the request.
    - **Source:** Race condition caused by concurrent user activity on the platform where 2 or more users attempt to claim the same slug within the same short time window.
    - **Consequence:** The user receives an unexpected HTTP 409 response after a successful availability check, causing confusion because the slug appeared available moments before submission.
    - **Recovery:** The server returns HTTP 409 with a slug-conflict error code and the client falls back to displaying a localized inline error message beneath the slug field, keeping the form open with the name and slug values intact so the user can choose a different slug and resubmit.
- **OrgSwitcher does not reflect the new organization immediately after creation due to a stale client-side cache**
    - **What happens:** After the server returns HTTP 200 for the creation request, the OrgSwitcher still shows only the previous organizations because the client's organization list cache has not been invalidated or refreshed with the newly created org.
    - **Source:** A missing cache invalidation step in the creation success handler, or a client-side state management bug that does not append the new organization to the cached list after a successful creation response.
    - **Consequence:** The user navigates to the new org's dashboard but cannot switch back to the new org from the OrgSwitcher if they navigate away, because the new org does not appear in the switcher list until a full page reload.
    - **Recovery:** The creation success handler invalidates the organization list cache and refetches the full membership list from the server before navigating — if the refetch fails the client falls back to a full page reload at `/app/{newSlug}/` which triggers a fresh membership query on mount.
- **Session activeOrganizationId not updated after organization creation, leaving the user scoped to the previous org**
    - **What happens:** The organization record is created successfully in the database but the server fails to update `activeOrganizationId` on the caller's session, so all subsequent API calls from the client are still scoped to the previously active organization instead of the new one.
    - **Source:** A missing session update step in the organization creation handler, or a bug in the Better Auth `organization` plugin that skips the session update when creating a new org from a user who already has an active org.
    - **Consequence:** The user is redirected to `/app/{newSlug}/` but all data queries on that page return results scoped to the old org, causing the new org's dashboard to display incorrect or empty data.
    - **Recovery:** The integration test for this flow asserts that the session object returned by the creation endpoint contains `activeOrganizationId` equal to the new org's ID — CI alerts and blocks deployment if the session field does not match, and on failure the client falls back to calling the switch-organization endpoint explicitly before navigating.

## Declared Omissions

- This specification does not address the first-organization creation flow that occurs during onboarding when the user has no existing organizations, which is covered by `user-creates-first-organization.md`
- This specification does not address switching between existing organizations in the OrgSwitcher without creating a new one, which is covered by `user-switches-organization.md`
- This specification does not address updating organization settings such as name, logo, or slug after the organization has been created, which is covered by `user-updates-organization-settings.md`
- This specification does not address logo upload for the new organization during or after creation, which is covered by `user-uploads-organization-logo.md`
- This specification does not address inviting members to the newly created organization, which is covered by `org-admin-invites-a-member.md`
- This specification does not address server-side rate limiting or throttling of the organization creation endpoint, which is an infrastructure concern defined in `api-framework.md`

## Related Specifications

- [user-creates-first-organization](user-creates-first-organization.md) — Onboarding-time organization creation flow for users who have no existing organizations, covering the same form but in the initial setup context
- [user-switches-organization](user-switches-organization.md) — OrgSwitcher flow for switching the active organization to an existing one without creating a new organization
- [user-updates-organization-settings](user-updates-organization-settings.md) — Post-creation organization settings management including name and slug changes that build on the organization record this spec creates
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the `organization` plugin that provides the `create` and `checkSlug` endpoints used in this spec
- [database-schema](../foundation/database-schema.md) — Drizzle ORM table definitions for the `organization` and `member` tables written to during the creation flow
- [session-lifecycle](session-lifecycle.md) — Session management specification covering `activeOrganizationId` updates that are triggered by successful organization creation

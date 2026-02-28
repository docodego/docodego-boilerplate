---
id: SPEC-2026-046
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Updates Profile

## Intent

This spec defines the flow by which an authenticated user navigates to the
profile settings page at `/app/settings/profile`, edits their display name,
and saves the change via `authClient.updateUser()`. The profile page is a
user-level route that lives outside the `$orgSlug/` namespace and is not
scoped to any specific organization. On success the cached user data in
TanStack Query is invalidated so every component that displays the user's
name — the avatar dropdown in the header, for instance — re-fetches and
reflects the updated name immediately across the entire application. The
email field is displayed as read-only because email changes are not handled
through this form, and an avatar section is present as a placeholder for
future avatar upload functionality.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `authClient.updateUser()` endpoint | write | User clicks the save button after editing the display name in the profile form | The client receives an error response and displays a localized error toast via Sonner — the user's existing profile data remains unchanged in the database until the endpoint recovers |
| `user` table (D1) | read/write | Profile page loads to pre-fill the form with the current display name and email, and the mutation writes the updated display name upon save | The profile page fails to load current values and returns a 500 error, and the mutation rejects with a 500 so no partial update is written to the user record |
| TanStack Query cache | write | On successful profile update the user data cache is invalidated to trigger a re-fetch across all components that display the user's name | Cache invalidation falls back to a stale read — components retain the old display name until the next manual page reload or navigation event that triggers a fresh query |
| Sonner toast | write | On save success a localized confirmation toast is displayed, and on save failure a localized error toast is displayed describing the problem | Toast notification degrades silently — the form state itself reflects the outcome (success clears dirty state, failure retains edits) even without a visible toast notification |
| `@repo/i18n` | read | All form labels, button text, placeholder text, error messages, and toast messages on the profile page are rendered via translation keys | Translation function falls back to the default English locale strings so the profile settings page remains fully usable without localized text for the active locale |

## Behavioral Flow

1. **[User]** navigates to `/app/settings/profile` via the Settings link in
    the sidebar's user section — this is a user-level route, not scoped to
    any specific organization, and it lives outside the `$orgSlug/` namespace
2. **[Client]** loads the profile page and renders a form with localized
    labels displaying the user's current information — the display name field
    is editable and the email field is shown but disabled or read-only since
    email changes are not handled through this form
3. **[Client]** renders an avatar section as a placeholder for future avatar
    upload functionality — the section is present but does not support file
    selection or upload in this flow
4. **[User]** edits the display name field and clicks the Save button to
    submit the updated value to the server
5. **[Client]** transitions the Save button to a loading state while the
    request is in flight, preventing duplicate submissions until the server
    responds with a success or failure result
6. **[Client]** calls `authClient.updateUser()` with the updated display
    name, sending the mutation request to the server for persistence in the
    user record
7. **[Branch — mutation succeeds]** A toast confirmation appears via Sonner
    confirming the profile was updated — the cached user data is invalidated
    in TanStack Query, causing any component that displays the user's name
    (the avatar dropdown in the header, for instance) to re-fetch and reflect
    the new name immediately across the entire app
8. **[Branch — mutation fails]** An error toast appears via Sonner describing
    what went wrong — the form retains the user's edits so they can retry
    without re-entering their changes, and the Save button returns to its
    default interactive state

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | loading_form | User navigates to `/app/settings/profile` | User is authenticated and the session token is valid |
| loading_form | form_ready | Profile page loads with current display name and email pre-filled | API returns 200 with user data including name and email fields |
| loading_form | load_error | API returns non-200 or network error during page load | HTTP response status does not equal 200 or the request times out |
| form_ready | submitting | User edits the display name and clicks the Save button | Display name field value differs from the original pre-filled value |
| submitting | success | API returns 200 and the user record is updated with the new display name | Mutation completes and the response confirms the name change was persisted |
| submitting | error | API returns non-200 or network error during mutation | HTTP response status does not equal 200 or the request times out |
| success | form_ready | TanStack Query cache is invalidated and components re-fetch the updated name | Cache invalidation call completes and the form resets dirty state |
| error | submitting | User clicks the Save button again to retry with the retained edits | Display name field still contains the edited value from the failed attempt |

## Business Rules

- **Rule email-read-only:** IF the profile form is rendered THEN the email
    field is displayed as disabled or read-only and cannot be edited through
    this form — email changes require a separate verification flow that is
    not part of this specification
- **Rule cache-invalidation-on-success:** IF the `authClient.updateUser()`
    mutation succeeds THEN the TanStack Query cache entry for user data is
    invalidated immediately, causing every component that reads user data
    to re-fetch and render the updated display name within the same client
    session without requiring a manual page reload
- **Rule edit-retention-on-failure:** IF the `authClient.updateUser()`
    mutation fails THEN the profile form retains the user's edited display
    name value in the input field so the user can click Save again to retry
    without re-entering their changes from scratch
- **Rule auth-required:** IF the user is not authenticated THEN the route
    guard redirects the user to `/signin` before the profile page renders
    — the profile form is never displayed to unauthenticated visitors and
    the `authClient.updateUser()` endpoint rejects unauthenticated requests
    with HTTP 401

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner (of the profile) | View profile form with current display name and email pre-filled, edit the display name field, click Save to submit the mutation, see success or error toast | Edit the email field through this form — email changes are handled via a separate verification flow not covered by this specification | All form fields are visible; the display name input is interactive and the Save button is rendered |
| Admin (any org admin viewing their own profile) | View and edit their own profile form identically to the Owner row — profile settings are user-level and not org-scoped | Edit the email field through this form — the same restriction applies to all authenticated users regardless of org role | All form fields are visible; the display name input is interactive and the Save button is rendered |
| Member (any org member viewing their own profile) | View and edit their own profile form identically to the Owner row — profile settings are user-level and not org-scoped | Edit the email field through this form — the same restriction applies to all authenticated users regardless of org role | All form fields are visible; the display name input is interactive and the Save button is rendered |
| Unauthenticated | None — the route guard redirects to `/signin` before the profile page loads and the mutation endpoint rejects with HTTP 401 | Access to any part of `/app/settings/profile` including viewing the profile form or submitting any mutation | The profile page is not rendered; redirect to `/signin` occurs immediately upon navigation |

## Constraints

- The display name field is pre-filled from the API response on page load —
    the input value equals the current `user.name` and the count of
    pre-filled editable fields on the profile form equals 1
- The email field is rendered as disabled or read-only — the count of
    interactive email input fields on the profile form equals 0 and the
    email value matches the current `user.email` from the API response
- The Save button is disabled or visually inactive while the mutation
    request is in flight — the count of concurrent mutation requests that
    can be triggered by clicking Save equals 1 at any given moment
- The TanStack Query cache invalidation is triggered in the mutation
    success handler — the count of components still rendering the old
    display name after a successful mutation equals 0 within one re-fetch
    cycle of the cache invalidation
- All form labels, button text, toast messages, and error descriptions
    are rendered via i18n translation keys — the count of hardcoded English
    strings in the profile settings page UI components equals 0
- The route guard redirects unauthenticated visitors to `/signin` before
    the profile page renders — the count of profile form elements visible
    to unauthenticated visitors equals 0

## Acceptance Criteria

- [ ] Navigating to `/app/settings/profile` renders the display name input field pre-filled with the current `user.name` — the input value is non-empty and equals the stored display name after the page loads
- [ ] Navigating to `/app/settings/profile` renders the email field as disabled or read-only showing the current `user.email` — the email input has a disabled or readonly attribute and its value equals the stored email address
- [ ] The avatar section is present on the profile page as a visible placeholder element — the avatar area is rendered in the DOM and does not contain an interactive file upload control
- [ ] Clicking Save after editing the display name calls `authClient.updateUser()` with the updated name — the mutation invocation count equals 1 after the Save button is clicked and the request payload contains the edited display name value
- [ ] The Save button transitions to a loading state while the mutation is in flight — the button shows a loading indicator and the count of additional mutation requests that can be triggered by clicking Save during this state equals 0
- [ ] On mutation success a localized confirmation toast appears via Sonner — the toast element is present and visible within 500ms of the API returning a success response
- [ ] On mutation success the TanStack Query cache for user data is invalidated — the count of components still rendering the old display name after the cache invalidation equals 0 within one re-fetch cycle
- [ ] On mutation success the avatar dropdown in the header reflects the updated display name — the name text in the avatar dropdown element equals the new display name and the old name text is absent
- [ ] On mutation failure a localized error toast appears via Sonner describing what went wrong — the error toast element is present and visible after the API returns a non-200 response
- [ ] On mutation failure the form retains the user's edited display name in the input field — the display name input value equals the user's edited text and does not revert to the original pre-filled value
- [ ] On mutation failure the Save button returns to its default interactive state — the button is clickable and the loading indicator is absent so the user can retry the submission
- [ ] An unauthenticated visitor navigating to `/app/settings/profile` is redirected to `/signin` — the window location pathname equals `/signin` and the profile form element is absent from the DOM
- [ ] The count of hardcoded English strings in the profile settings page UI components equals 0 — all visible text is rendered via i18n translation keys and the count of string literals outside translation calls equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User submits the form without changing the display name from its pre-filled value | The client either disables the Save button when the value is unchanged from the original, or the mutation is called and the API treats it as a no-op returning 200 with the existing data — the count of persisted changes equals 0 | Save button disabled attribute is present when the form value matches the original, or HTTP response status equals 200 with unchanged data |
| User clears the display name field entirely and clicks Save leaving an empty string after trimming whitespace | The client or server rejects the empty display name with a validation error — the API returns HTTP 400 or the client prevents submission, and the user record is not updated with a blank name | HTTP response status equals 400 or the Save button is disabled, and the `user.name` field in the database is unchanged |
| User enters a display name that consists only of whitespace characters such as spaces and tabs | The client or server trims the input and rejects it as empty — the validation error is displayed and the user record retains the previous display name without storing whitespace-only values | The validation error element is present and the `user.name` field in the database is unchanged from the previous value |
| User's session expires between loading the profile page and clicking Save | The mutation request returns HTTP 401 because the session token is no longer valid — the client displays an error toast or redirects to `/signin` and the form edits are lost | HTTP response status equals 401 and the window location pathname equals `/signin` or an error toast element is present |
| User opens two browser tabs with the profile page and saves different display names from each tab | The last mutation to complete wins — the user record stores whichever display name was persisted last, and cache invalidation in both tabs eventually reflects the final stored value | The `user.name` field in the database equals the display name from the last successful mutation, and both tabs show the same name after re-fetch |
| Network disconnects after the user clicks Save and the request never reaches the server | The mutation times out and the client displays a network error toast — the form retains the user's edits and the Save button returns to its interactive state for retry when connectivity resumes | The error toast element is present, the display name input still contains the edited value, and the Save button is clickable |

## Failure Modes

- **Profile update mutation fails due to a transient D1 write error**
    - **What happens:** The `authClient.updateUser()` call reaches the
        server but the D1 write operation to update the user record fails
        due to a transient database error, preventing the new display name
        from being persisted even though the request was valid.
    - **Source:** Cloudflare D1 transient write failure or connection
        timeout between the Worker and the D1 binding during the UPDATE
        operation on the user table.
    - **Consequence:** The user receives an error response and sees an
        error toast via Sonner — the display name in the database remains
        unchanged and other components continue to render the old name
        across the application until the user successfully retries.
    - **Recovery:** The server logs the D1 write failure with the user ID
        and mutation context, and the client retries the mutation when
        the user clicks Save again after the transient D1 failure recovers
        and database connectivity is restored.
- **TanStack Query cache invalidation fails after a successful mutation**
    - **What happens:** The mutation succeeds and the server persists the
        updated display name to the user record in D1, but the client-side
        TanStack Query cache invalidation does not trigger, leaving stale
        user data in components that read from the cache.
    - **Source:** A cache invalidation gap where the mutation success
        handler fails to call the invalidation function due to a runtime
        error, an unhandled promise rejection, or a query key mismatch
        between the mutation and the user data query.
    - **Consequence:** The user sees the updated name in the profile form
        input but the avatar dropdown in the header and other components
        continue to display the old name, creating a confusing inconsistency
        that persists until a manual page reload.
    - **Recovery:** The mutation success handler notifies the user data
        query cache to invalidate and refetch — if invalidation fails the
        user falls back to a manual page reload that triggers a fresh query
        and resolves the stale name across all components.
- **Unauthenticated mutation attempt after session expiration mid-form**
    - **What happens:** The user loads the profile page while authenticated,
        edits the display name, but their session expires before they click
        Save — the mutation request is sent with an expired session token
        and the server rejects it because the user is no longer authenticated.
    - **Source:** Session token expiration due to inactivity timeout or
        server-side session invalidation occurring between the initial page
        load and the moment the user submits the profile update form.
    - **Consequence:** The mutation returns HTTP 401 and the user's edits
        are not persisted — the profile page displays an error toast or
        the route guard redirects the user to `/signin`, and any unsaved
        changes in the display name field are lost during the redirect.
    - **Recovery:** The client alerts the user with an error toast or
        redirects to `/signin` where the user re-authenticates — after
        signing in the user navigates back to the profile page and
        re-enters the display name change from the beginning.

## Declared Omissions

- This specification does not address changing the user's email address — email
    changes require a separate verification flow with confirmation links and are
    defined in a distinct spec covering account email update with re-verification
- This specification does not address uploading or updating the user's profile
    avatar image — that behavior is defined in `user-uploads-profile-avatar.md`
    as a separate file-upload flow with its own size, type, and storage constraints
- This specification does not address account deletion or deactivation from the
    profile settings page — that behavior is covered by a separate spec defining
    the confirmation dialog and cascading cleanup of user data across organizations
- This specification does not address rate limiting on the `authClient.updateUser()`
    endpoint — that behavior is enforced by the global rate limiter defined in
    `api-framework.md` covering all mutation endpoints uniformly across the API
- This specification does not address how the profile settings page renders on
    mobile viewport sizes within Expo or within the Tauri desktop wrapper — those
    platform-specific layout details are covered by their respective platform specs

## Related Specifications

- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server
    configuration including the user update endpoint that validates authentication
    and persists the updated display name to the user record in the database
- [database-schema](../foundation/database-schema.md) — Schema definition for
    the `user` table that stores the display name and email fields read and written
    by the profile form and the `authClient.updateUser()` mutation handler
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure
    providing translation keys for all profile page labels, button text, toast
    messages, and error descriptions rendered on the profile settings form
- [api-framework](../foundation/api-framework.md) — Hono middleware stack and
    global error handler that wraps the user update endpoint and returns consistent
    JSON error shapes for 400, 401, and 500 responses consumed by the profile form
- [user-uploads-profile-avatar](user-uploads-profile-avatar.md) — Avatar upload
    flow that handles file selection, validation, R2 storage, and cache invalidation
    for the user profile image referenced as a placeholder section in this spec

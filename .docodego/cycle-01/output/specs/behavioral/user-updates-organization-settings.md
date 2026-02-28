---
id: SPEC-2026-027
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [Org Owner, Org Admin]
---

[← Back to Roadmap](../ROADMAP.md)

# User Updates Organization Settings

## Intent

This spec defines the flow by which an authenticated organization owner or admin
navigates to the organization settings page, edits the organization name or slug,
and saves the changes via an oRPC mutation. The settings page lives at
`/app/$orgSlug/settings` and pre-fills the form with the organization's current
name and slug. When the slug changes the API validates the new value for format
and uniqueness against all existing organizations, and on success the client
navigates to the updated URL path so the address bar stays in sync. When only
the name changes the URL is unchanged and the updated name propagates throughout
the dashboard including the OrgSwitcher header component. Users without owner or
admin roles cannot edit org settings — they see a read-only view or are
redirected by the route guard.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| oRPC mutation endpoint (`updateOrganization`) | write | User clicks the save button after editing the org name or slug in the settings form | The client receives an error response and the form displays a localized error message, leaving the existing organization data unchanged until the API recovers |
| `organization` table (D1) | read/write | Settings page loads to pre-fill form values, and mutation writes the updated name or slug upon save | The settings page fails to load current values, returning a 500 error, and the mutation rejects with a 500 so no partial update is written to the database |
| Better Auth organization plugin | read | Slug uniqueness validation is executed server-side during the mutation to confirm the new slug is not already taken by a different organization | The server rejects the mutation with a 500 error and logs the failure — the client displays a generic error message and the user retries when the auth system recovers |
| `@repo/i18n` | read | All form labels, button text, error messages, and page headings are rendered via translation keys on the settings page | Translation function falls back to the default English locale strings so the settings page remains usable without localized text |
| Astro client-side router | write | After a successful slug-change mutation the client navigates to the new `/app/{newSlug}/settings` URL to keep the address bar in sync | Navigation falls back to a full page reload via `window.location.assign` if the client router is unavailable, producing the same end state |

## Behavioral Flow

1. **[User]** navigates to `/app/$orgSlug/settings` via the sidebar's Org
    Settings link to access the settings page for the active organization
2. **[Client]** loads the settings page and renders a form displaying
    localized labels pre-filled with the organization's current name and
    current slug, so the user can see the existing values before editing
3. **[User]** edits either the organization name, the organization slug,
    or both fields in the settings form, then clicks the save button to
    submit the changes
4. **[Client]** submits an oRPC mutation with the updated name and slug
    values to the API, triggering server-side validation and persistence
5. **[Branch — slug was changed]** The API validates the new slug for
    uniqueness — the same rules apply as during organization creation:
    minimum 3 characters, lowercase letters, numbers, and hyphens only,
    no leading or trailing hyphens, and the slug must not already be taken
    by another organization
6. **[Branch — slug validation fails]** The API returns HTTP 400 and the
    client displays a localized inline error message explaining the
    constraint that was violated, leaving the form editable so the user
    can correct the slug and resubmit
7. **[Branch — mutation succeeds and slug changed]** The client navigates
    to the new URL path at `/app/{newSlug}/settings` so the address bar
    stays in sync with the updated slug — the OrgSwitcher and sidebar
    links update to reflect the new slug value
8. **[Branch — mutation succeeds and only name changed]** The page remains
    at the same URL and the updated organization name is reflected in the
    header's OrgSwitcher component and throughout the dashboard without
    requiring a navigation event
9. **[Branch — user lacks permission]** Other members who navigate to
    `/app/$orgSlug/settings` without owner or admin roles either see a
    read-only view of the settings or are redirected away from the page,
    depending on the route guard implementation — the save button is absent
    from the read-only view so non-admin members cannot submit mutations

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | loading_form | User navigates to `/app/$orgSlug/settings` | User is authenticated and the org slug resolves to a valid organization |
| loading_form | form_ready | Settings page loads with current org name and slug pre-filled | API returns 200 with organization data |
| loading_form | load_error | API returns non-200 or network error during page load | HTTP response status does not equal 200 or request times out |
| form_ready | submitting | User edits fields and clicks save | At least 1 field has changed from its original value |
| submitting | slug_format_error | API returns 400 due to slug format violation | New slug fails format check server-side |
| submitting | slug_conflict_error | API returns 409 due to slug already taken | New slug fails uniqueness check server-side |
| submitting | success_slug_changed | API returns 200 and slug was changed | Mutation completes and new slug differs from previous slug |
| submitting | success_name_only | API returns 200 and only name was changed | Mutation completes and slug is unchanged |
| slug_validation_error | submitting | User corrects the slug and clicks save again | Slug field has been edited after the validation error |
| success_slug_changed | navigated | Client router navigates to `/app/{newSlug}/settings` | New slug URL is valid and client router is available |
| success_name_only | form_ready | Dashboard and OrgSwitcher reflect the updated name | Mutation response confirms name update persisted |

## Business Rules

- **Rule slug-format:** IF the slug field is changed AND the new value does
    not match the pattern `^[a-z0-9][a-z0-9-]{1,}[a-z0-9]$` (minimum 3
    characters, lowercase letters, numbers, and hyphens only, no leading
    or trailing hyphens) THEN the API returns HTTP 400 with a localized
    format error and the slug is not persisted
- **Rule slug-uniqueness:** IF the slug field is changed AND the new slug
    value is already taken by a different organization in the `organization`
    table THEN the API returns HTTP 409 with a localized conflict error
    indicating the slug is unavailable and the mutation does not persist
- **Rule url-sync-on-slug-change:** IF the mutation succeeds AND the slug
    was changed THEN the client navigates to `/app/{newSlug}/settings`
    within the same navigation cycle so the address bar reflects the current
    slug and back-navigation does not break
- **Rule name-only-no-navigation:** IF the mutation succeeds AND the slug
    was not changed THEN the client remains at the same URL and updates
    the OrgSwitcher and dashboard header in place using the response data
- **Rule permission-gate:** IF the authenticated user's role in the
    organization is not `owner` and not `admin` THEN the settings form
    is either rendered as read-only with no save button or the route guard
    redirects the user away from `/app/$orgSlug/settings` before the form
    renders — the mutation endpoint also rejects unauthorized calls with
    HTTP 403 regardless of the client-side guard

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View settings form with current org name and slug pre-filled, edit name and slug, submit mutation, navigate to new URL after slug change | None — owner has full access to all organization settings | All settings form fields and the save button are visible and interactive |
| Admin | View settings form with current org name and slug pre-filled, edit name and slug, submit mutation, navigate to new URL after slug change | Transferring ownership — that action is defined in a separate spec | All settings form fields and the save button are visible and interactive |
| Member | View the settings page in read-only mode showing current org name and slug | Edit any field or submit the mutation — the save button is absent from the read-only view | Form fields are visible but non-interactive; the save button is not rendered |
| Unauthenticated visitor | None — route guard redirects to `/signin` before the page loads | Access to any part of `/app/$orgSlug/settings` | The settings page is not rendered; redirect occurs immediately |

## Constraints

- The slug validation pattern `^[a-z0-9][a-z0-9-]{1,}[a-z0-9]$` is enforced
    server-side in the mutation handler — the client count of characters
    matching the pattern equals the total character count of the new slug,
    and the minimum total length equals 3 characters
- The slug uniqueness check queries the `organization` table and excludes the
    current organization's own slug from the conflict check — updating the
    name without changing the slug must not trigger a false uniqueness conflict
- The settings page form fields pre-fill from the API response on load — the
    name input value equals the current `organization.name` and the slug input
    value equals the current `organization.slug`, with count of pre-filled
    fields equaling 2
- The mutation endpoint returns HTTP 403 if the calling user's membership
    record does not have `owner` or `admin` role — role is read from the
    `member` table and is not inferred from the request payload
- After a successful slug-change mutation the client navigates to the new path
    within the same user interaction — the count of full page reloads triggered
    by a slug change equals 0 when the client router is available
- All form labels, error messages, and button text are rendered via i18n
    translation keys — the count of hardcoded English strings in the settings
    page UI components equals 0

## Acceptance Criteria

- [ ] Navigating to `/app/$orgSlug/settings` renders the name input field pre-filled with the current `organization.name` — the input value is non-empty and equals the stored name after the page loads
- [ ] Navigating to `/app/$orgSlug/settings` renders the slug input field pre-filled with the current `organization.slug` — the input value is non-empty and equals the stored slug after the page loads
- [ ] Clicking save dispatches the oRPC `updateOrganization` mutation with both the name and slug fields present in the payload — the mutation invocation count equals 1 after the save button is clicked
- [ ] Submitting a slug that fails the format check causes the API to return HTTP 400 and the client error element is present and visible — the response status equals 400 and the error element count in the DOM equals 1
- [ ] Submitting a slug already taken by a different organization causes the API to return HTTP 409 and the client conflict error element is present — the response status equals 409 and count of persisted org records with that slug equals 1
- [ ] After a successful mutation where the slug changed, the window location pathname equals `/app/{newSlug}/settings` — the pathname updates within 1 navigation cycle and the old slug path returns a 404 response
- [ ] After a successful mutation where only the name changed, the window location pathname remains unchanged and equals `/app/{originalSlug}/settings` — count of navigation events triggered by the name-only mutation equals 0
- [ ] After a name-only mutation succeeds, the OrgSwitcher element displays the updated name within 500ms — the updated name text is present in the OrgSwitcher DOM element and the old name text is absent
- [ ] A mutation call from a `member`-role user returns HTTP 403 and the organization record is not modified — the response status equals 403 and count of changed fields in the database equals 0
- [ ] A `member`-role user viewing the settings page sees no save button — the save button element is absent from the DOM and the count of interactive input fields equals 0
- [ ] An unauthenticated visitor navigating to `/app/$orgSlug/settings` is redirected to `/signin` — the window location pathname equals `/signin` and the settings form element is absent from the DOM
- [ ] Submitting the current slug as the new slug returns HTTP 200 with no conflict error — the response status equals 200 and the count of conflict error fields in the response body equals 0
- [ ] The count of hardcoded English strings in the settings page UI components equals 0 — all visible text is rendered via i18n translation keys and the count of string literals outside translation calls equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User submits the form with no changes to either name or slug | The client either disables the save button when values are unchanged or the mutation is called and the API treats it as a no-op returning HTTP 200 with the existing data — count of persisted changes equals 0 | Save button disabled attribute is present when form values match original values, or HTTP response status equals 200 with unchanged data |
| User changes the slug to a value that differs only in letter casing from an existing org slug, such as `MyOrg` vs `myorg` | The API treats slugs as case-insensitive during uniqueness validation and returns HTTP 409 because the lowercase-normalized form of the new slug already exists in the organization table | HTTP response status equals 409 and the error element is present |
| User types a valid slug and saves, then immediately navigates back using the browser back button | The browser navigates back to the old `/app/{oldSlug}/settings` URL which no longer resolves to a valid route — the route guard detects the stale slug and redirects the user to the new `/app/{newSlug}/settings` or to the org dashboard | Window location pathname does not remain on the old slug path more than 1 navigation cycle |
| Two admins save conflicting slug changes at the same time from different browser sessions | The second mutation to arrive at the server encounters a uniqueness conflict because the first mutation already persisted the new slug — the second mutation returns HTTP 409 with a conflict error | HTTP response status for the second concurrent request equals 409 and count of persisted slug values in the organization table equals 1 |
| User submits a slug with leading or trailing hyphens such as `-myorg` or `myorg-` | The API rejects the value with HTTP 400 because the slug format rule prohibits leading and trailing hyphens — the error element describes the format constraint | HTTP response status equals 400 and the error element is present and visible |
| User submits a name that is an empty string after trimming whitespace | The API returns HTTP 400 because a blank organization name is not valid — the client displays a localized error and the form field retains focus | HTTP response status equals 400 and the name field is still editable |

## Failure Modes

- **Slug uniqueness check fails due to a transient D1 read error during mutation**
    - **What happens:** The server-side uniqueness query against the `organization`
        table times out or returns a database error during the slug validation step,
        preventing the mutation from completing even when the slug is genuinely
        unique and the format is valid.
    - **Source:** Cloudflare D1 transient read failure or network timeout between the
        Worker and the D1 binding during the slug uniqueness SELECT query execution.
    - **Consequence:** The user receives a generic HTTP 500 error from the API and
        the settings form displays an error state — the organization name and slug
        remain unchanged in the database because the mutation did not commit.
    - **Recovery:** The server logs the D1 error with the query context and returns
        HTTP 500 — the client displays a localized generic error message and the user
        retries by clicking save again once the D1 service recovers from the transient
        failure.
- **Unauthorized mutation attempt by a member-role user bypassing the client guard**
    - **What happens:** A user with a `member` role in the organization crafts a
        direct API request to the `updateOrganization` mutation endpoint, bypassing
        the client-side read-only view and the missing save button, attempting to
        update the organization name or slug without authorization.
    - **Source:** Adversarial action where a member-role user sends a hand-crafted
        HTTP request to the mutation endpoint with a valid session cookie, circumventing
        the client-side route guard that hides the save button from non-admin members.
    - **Consequence:** Without server-side enforcement the member could overwrite the
        organization name or slug — this would affect every other member's dashboard
        and break URL routing for the entire organization if the slug changes.
    - **Recovery:** The mutation handler rejects the request with HTTP 403 after
        verifying the calling user's role in the `member` table — the organization
        record is not mutated and the server logs the unauthorized attempt with the
        user ID and timestamp for audit purposes.
- **Stale URL after slug change causes broken navigation for other open sessions**
    - **What happens:** A user changes the organization slug while other members have
        the dashboard open in separate browser tabs — those tabs still hold links and
        cached routes pointing to the old slug URL, and clicking any sidebar link
        navigates to a path that no longer resolves to a valid organization.
    - **Source:** The slug change is an atomic rename that invalidates all previously
        bookmarked or cached `/app/{oldSlug}/...` routes across all open sessions and
        browser tabs for all members of the organization.
    - **Consequence:** Other members see a 404 or route error page when they click
        navigation links that reference the old slug — they cannot access the dashboard
        until they reload the application and fetch the updated organization data.
    - **Recovery:** The route guard detects an unresolvable org slug on navigation
        and falls back to redirecting the user to the org switcher page where the
        updated slug is listed — the member selects the organization and the client
        stores the new slug for subsequent navigation without losing their session.
- **Name update propagates inconsistently to OrgSwitcher due to stale client cache**
    - **What happens:** The mutation succeeds and the API persists the new organization
        name, but the OrgSwitcher component in the dashboard header still displays the
        old name because the client-side organization data cache has not been
        invalidated after the mutation response is received.
    - **Source:** A cache invalidation gap where the oRPC mutation response updates
        the local form state but does not trigger a refetch or cache update for the
        organization list query that populates the OrgSwitcher dropdown.
    - **Consequence:** The user sees the new name in the settings form input but the
        old name in the OrgSwitcher header, creating a confusing inconsistency that
        persists until the user manually reloads the page or navigates away and back.
    - **Recovery:** The mutation success handler notifies the organization list query
        cache to invalidate and refetch — the OrgSwitcher re-renders within 500ms of
        the mutation response and displays the updated name, eliminating the stale
        state without requiring a manual reload.

## Declared Omissions

- This specification does not address transferring organization ownership to a different
    member — that behavior is defined in `user-transfers-organization-ownership.md` as
    a separate concern covering the ownership handoff flow
- This specification does not address uploading or updating the organization logo or
    avatar image — that behavior is defined in `user-uploads-organization-logo.md` as a
    distinct file-upload flow with its own constraints and edge cases
- This specification does not address deleting an organization from the settings page
    — that behavior is defined in `user-deletes-an-organization.md` covering the
    confirmation dialog and cascading deletion of all member and team records
- This specification does not address rate limiting on the `updateOrganization` mutation
    endpoint — that behavior is enforced by the global rate limiter defined in
    `api-framework.md` covering all mutation endpoints uniformly
- This specification does not address how the organization settings page renders on
    mobile viewport sizes or within the Tauri desktop wrapper — those contexts are
    covered by their respective platform specs in phases 6a through 6c of the roadmap

## Related Specifications

- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server
    configuration including the organization plugin that validates membership roles
    and enforces the owner and admin permission check on the mutation endpoint
- [database-schema](../foundation/database-schema.md) — Schema definitions for the
    `organization` and `member` tables that store the name, slug, and member roles
    read and written by the settings form and the mutation handler
- [shared-contracts](../foundation/shared-contracts.md) — oRPC contract definitions
    for the `updateOrganization` mutation including the Zod schema that enforces the
    slug format rule before the mutation reaches the database layer
- [api-framework](../foundation/api-framework.md) — Hono middleware stack and global
    error handler that wraps the mutation endpoint and returns consistent JSON error
    shapes for 400, 403, and 500 responses consumed by the settings form
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure
    providing translation keys for all settings page labels, error messages, and
    button text rendered on the organization settings form

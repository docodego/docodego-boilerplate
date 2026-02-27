---
id: SPEC-2026-028
version: 1.0.0
created: 2026-02-27
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Uploads Organization Logo

## Intent

This spec defines the end-to-end flow by which an organization owner or admin
uploads a new logo image for their organization from the settings page at
`/app/$orgSlug/settings`. The admin selects an image using the platform's native
file picker — a browser file input on web and desktop, and `expo-image-picker` on
mobile. The client validates the selected file against size and type constraints
before uploading. If validation passes, the file is streamed to Cloudflare R2
object storage via the `STORAGE` binding on the API, the returned URL is written
to the organization record, and every UI component that displays the logo
re-renders immediately via TanStack Query cache invalidation. Users without owner
or admin role cannot access the upload control, and the API enforces this
server-side by rejecting unauthorized requests with HTTP 403.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Organization logo upload endpoint (`apps/api`) | write | Client sends validated image file after user selects a file and client-side validation passes | The API returns a 500 error and the client displays a localized error toast — the previous logo or placeholder remains unchanged and the admin can retry the upload once the API recovers |
| Cloudflare R2 object storage (`STORAGE` binding) | write | API streams the validated image file to R2 after server-side validation and role check pass | The API returns 500 and logs the R2 write failure — no URL is stored in the organization record, the existing logo or placeholder is preserved, and the admin retries when R2 recovers |
| `organization` table (D1) | write | API updates the organization record with the new R2 object URL after the file is stored | The mutation returns 500 and the R2 object is orphaned without a reference in the database — the organization record retains the previous logo URL and the admin retries once D1 recovers |
| `expo-image-picker` | read | User selects an image on the mobile platform (Expo 54) | Image selection falls back to unavailable state — the client displays a localized error toast and the upload flow does not proceed until the picker recovers |
| `@repo/i18n` | read | All toast messages, button labels, and error text on the logo upload UI are rendered via translation keys | Translation function falls back to the default English locale strings so the upload control remains usable without localized text |
| TanStack Query cache | write | On successful logo upload the organization data cache is invalidated to trigger a re-fetch across all components that display the logo | Cache invalidation falls back to a stale read — components retain the old logo URL until the next manual reload or navigation event that triggers a fresh query |
| Sonner toast | write | On upload success or failure a localized toast notification is displayed to the admin | Toast notification degrades silently — the upload result is reflected in the UI state change (new logo appears or placeholder remains) even without a visible toast |

## Behavioral Flow

1. **[User]** navigates to `/app/$orgSlug/settings` via the sidebar's Org Settings
    link to access the settings page for the active organization (see
    User Updates Organization Settings for settings page navigation details)
2. **[Client]** renders the settings page with a logo section — if a logo has
    already been uploaded it is shown as a thumbnail; otherwise a generic
    placeholder icon is displayed alongside a localized "Change logo" button
    or clickable overlay
3. **[User]** clicks the logo placeholder or the "Change logo" button to open
    the platform's native file picker configured to accept image types only
    (JPEG, PNG, WebP, SVG)
4. **[Branch — web or desktop (Tauri webview)]** The standard browser file input
    opens, displaying the operating system file picker with localized text
    provided by the OS — the picker is filtered to image MIME types only
5. **[Branch — mobile (Expo)]** The `expo-image-picker` handles the selection
    presenting the system media library or camera interface to the user
6. **[User]** selects an image file from the file picker or media library and
    confirms the selection to proceed with the upload
7. **[Client]** validates the selected file against size and type constraints
    before sending it to the server — accepted types are JPEG, PNG, WebP, and
    SVG; oversized files exceed the maximum allowed size limit
8. **[Branch — validation fails]** A localized error toast appears via Sonner
    describing the constraint that was violated, the upload is aborted, and
    the previous logo or placeholder remains unchanged so the admin can retry
    with a different file
9. **[Branch — validation passes]** The client sends the image to the
    organization logo upload endpoint in `apps/api`
10. **[Server]** performs server-side validation of file size and type,
    confirms the requesting user holds the owner or admin role for the
    organization, then streams the file to Cloudflare R2 object storage
    via the `STORAGE` binding
11. **[Server]** returns the stored R2 object URL to the client after the
    file upload to R2 completes
12. **[Server]** a second mutation updates the organization record in D1 with
    the new logo URL returned from R2
13. **[Client]** receives the success response, displays a localized toast
    confirmation via Sonner, and invalidates the cached organization data
    in TanStack Query
14. **[Client]** every component that displays the organization logo — the
    org switcher dropdown, the header, and any member-facing views — re-fetches
    the organization data and renders the new logo immediately
15. **[Branch — upload or mutation fails]** An error toast describes the
    problem via Sonner — the previous logo or placeholder remains unchanged
    so the admin can retry the upload
16. **[Branch — unauthorized request]** The API rejects requests from
    non-owner and non-admin members with HTTP 403 regardless of what the
    client sends — the organization record is not modified

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | picker_open | User clicks logo placeholder or "Change logo" button | User holds owner or admin role and the settings page has loaded |
| picker_open | file_selected | User selects an image file and confirms the selection | File picker returns a file object with a non-empty name and size greater than 0 |
| picker_open | idle | User dismisses the file picker without selecting a file | File picker closes with no selection |
| file_selected | validation_error | Client validation fails for the selected file | File type is not JPEG, PNG, WebP, or SVG, or file size exceeds the maximum limit |
| file_selected | uploading | Client validation passes | File type is accepted and file size is within the allowed limit |
| validation_error | picker_open | User clicks logo placeholder or "Change logo" button again to retry | Previous validation error has been acknowledged |
| uploading | success | API returns 200 and organization record is updated with new logo URL | R2 write and D1 mutation both complete with status 200 |
| uploading | upload_error | API returns non-200 or network error during upload | HTTP response status does not equal 200 or the request times out |
| success | idle | TanStack Query cache is invalidated and components re-fetch the updated logo | Cache invalidation call completes and at least 1 re-fetch is triggered |
| upload_error | picker_open | User clicks logo placeholder or "Change logo" button again to retry | Previous upload error has been acknowledged |

## Business Rules

- **Rule file-type:** IF the selected file's MIME type is not one of `image/jpeg`,
    `image/png`, `image/webp`, or `image/svg+xml` THEN the client aborts the upload
    and displays a localized error toast — the count of allowed MIME types equals 4
    and any file outside this set is rejected before any network request is made
- **Rule client-size-validation:** IF the selected file's size exceeds the maximum
    allowed limit THEN the client aborts the upload before sending any request to
    the API and displays a localized error toast describing the size constraint
- **Rule server-side-role-check:** IF the requesting user's membership record in the
    `member` table does not have `owner` or `admin` role for the organization THEN
    the API returns HTTP 403 and the organization logo URL is not modified — role is
    read from the `member` table and is not inferred from the request payload
- **Rule server-side-validation:** IF the API receives a file upload request THEN
    it performs an independent server-side validation of file size and type before
    streaming to R2 — client-side validation alone is not sufficient and both
    validations must pass for the upload to proceed
- **Rule cache-invalidation:** IF the upload mutation succeeds and the organization
    record is updated with a new logo URL THEN the TanStack Query cache entry for
    the organization data is invalidated immediately so all logo-displaying components
    re-fetch and render the new image without requiring a manual page reload

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | View current logo or placeholder, open file picker, select image, upload logo, see success or error toast, view updated logo after upload | None — owner has full access to all logo upload actions | The "Change logo" button and clickable overlay are visible and interactive |
| Admin | View current logo or placeholder, open file picker, select image, upload logo, see success or error toast, view updated logo after upload | Transferring ownership — that action is defined in a separate spec | The "Change logo" button and clickable overlay are visible and interactive |
| Member | View the current organization logo or placeholder throughout the app | Open the file picker, select an image, or submit any upload request — the upload control is not rendered for members | The logo is visible in the org switcher, header, and member-facing views but the upload control is absent |
| Unauthenticated visitor | None — route guard redirects to `/signin` before the settings page loads | Access to any part of `/app/$orgSlug/settings` including the logo section | The settings page is not rendered; redirect occurs immediately |

## Constraints

- The file type validation accepts exactly 4 MIME types: `image/jpeg`, `image/png`,
    `image/webp`, and `image/svg+xml` — the count of accepted MIME types equals 4
    and the server rejects any file whose content-type header does not match one
    of these 4 values
- The API enforces role authorization server-side — the upload endpoint returns
    HTTP 403 when the calling user's role in the `member` table is not `owner` or
    `admin`, and the count of organization records modified by an unauthorized
    request equals 0
- The R2 object URL returned after a successful upload is stored in the
    `organization` table — the count of organization records with the new logo URL
    equals 1 after a successful upload and the previous URL is overwritten
- The TanStack Query cache invalidation is triggered in the mutation success handler
    — the count of stale logo renders after a successful upload equals 0 within
    the same client session before the next navigation event
- All user-facing text including toast messages, button labels, and error
    descriptions is rendered via i18n translation keys — the count of hardcoded
    English strings in the logo upload UI components equals 0
- Server-side validation runs independently of client-side validation — the API
    does not trust the client's pre-validation and performs its own size and type
    checks before writing to R2

## Acceptance Criteria

- [ ] The settings page at `/app/$orgSlug/settings` renders the logo section — the logo thumbnail or placeholder element is present and visible after the page loads
- [ ] The "Change logo" button or clickable overlay is present and interactive for owner-role users — the element is present and has no disabled attribute when the authenticated user holds the owner role
- [ ] The "Change logo" button or clickable overlay is present and interactive for admin-role users — the element is present and has no disabled attribute when the authenticated user holds the admin role
- [ ] The "Change logo" upload control is absent for member-role users — the count of upload control elements in the DOM equals 0 when the authenticated user holds the member role
- [ ] Clicking the "Change logo" button or placeholder opens the file picker filtered to image types only — the file input's accept attribute equals `image/jpeg,image/png,image/webp,image/svg+xml` or equivalent on the web platform
- [ ] Selecting a file with an unsupported MIME type causes the client to display a localized error toast — the toast element is present and the count of API requests made during the rejected upload equals 0
- [ ] Selecting a file that exceeds the maximum allowed size causes the client to display a localized error toast — the toast element is present and the count of API requests made during the rejected upload equals 0
- [ ] A validated file upload sends the image to the organization logo endpoint — the API receives the request and the request payload contains the file with a non-empty content-type matching one of the 4 accepted MIME types
- [ ] The API returns HTTP 403 when the requesting user holds the member role — the response status equals 403 and the count of organization records modified by the request equals 0
- [ ] The API validates file type server-side independently of the client — submitting a file with an invalid MIME type directly to the endpoint returns HTTP 400 even when the client pre-validation step is bypassed, and the count of R2 write operations equals 0
- [ ] After a successful upload the organization record is updated with the new R2 logo URL — the `organization.logoUrl` field value is non-empty and equals the URL returned by R2 after the upload
- [ ] After a successful upload a localized success toast appears via Sonner — the toast element is present and visible within 500ms of the API returning 200
- [ ] After a successful upload the TanStack Query cache for organization data is invalidated — the count of components still rendering the old logo URL equals 0 within 1 re-fetch cycle
- [ ] After a successful upload the org switcher, header, and member-facing views all display the new logo — the count of UI components still showing the old logo or placeholder after re-fetch equals 0
- [ ] On upload failure the previous logo or placeholder remains unchanged — the `organization.logoUrl` field value equals the value before the failed upload attempt, and the count of modified database rows equals 0
- [ ] On upload failure a localized error toast appears describing the problem — the error toast element is present and visible after the API returns a non-200 response
- [ ] All user-facing strings in the logo upload UI are rendered via i18n translation keys — the count of hardcoded English string literals outside translation calls in the logo upload components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User dismisses the file picker without selecting a file | The upload flow does not proceed and the logo section reverts to its previous state showing the existing thumbnail or placeholder — no API request is made | The count of API requests after the picker is dismissed equals 0 and the logo section element is unchanged |
| User selects an image file that passes client-side type and size validation but the R2 write times out | The API returns 500, no URL is stored in the organization record, and the client displays a localized error toast — the previous logo or placeholder is preserved | HTTP response status equals 500, the organization logoUrl field value is unchanged from before the attempt, and the error toast element is present |
| User clicks the "Change logo" button twice in rapid succession before the picker opens | The client opens the file picker on the first click — the second click has no additional effect because the picker is already open | The count of picker instances open simultaneously equals 1 and the count of API requests before a file is selected equals 0 |
| User uploads a new logo while the TanStack Query cache contains stale organization data from a previous session | The mutation success handler invalidates the cache regardless of its age — all components re-fetch the organization data and render the new logo | The count of components still rendering a logo URL older than the successful upload timestamp equals 0 after re-fetch completes |
| User selects an SVG file whose content is a valid SVG document but the file extension is `.txt` | The server performs MIME type sniffing or validates the content-type header — if the content-type does not match `image/svg+xml` the server rejects the upload with HTTP 400 | HTTP response status equals 400 and the count of R2 write operations for the request equals 0 |
| Admin uploads a logo immediately after another admin in the same organization saves a different logo from a separate browser session | The second upload overwrites the first — the organization record stores the URL of whichever upload completed last, and the cache invalidation triggered by each upload ensures all components eventually render the most recent logo | The count of organization logoUrl values in the database equals 1 and its value equals the R2 URL from the last completed upload |

## Failure Modes

- **R2 object storage write fails mid-stream after partial file transfer**
    - **What happens:** The Cloudflare R2 `STORAGE` binding times out or returns an
        error partway through streaming the image bytes, leaving an incomplete or
        absent object in R2 and no valid URL to return to the client.
    - **Source:** Cloudflare R2 service degradation, network interruption between
        the Worker and the R2 binding, or the uploaded file exceeding an internal
        R2 object size limit during the streaming write operation.
    - **Consequence:** The API cannot return a valid logo URL to the client — the
        organization record is not updated, the previous logo or placeholder is
        preserved, and the admin receives no confirmation that the new logo was saved.
    - **Recovery:** The API returns HTTP 500 and logs the R2 write failure with
        the organization ID and file metadata — the client displays a localized
        error toast and the admin retries the upload once R2 recovers from the
        transient failure.
- **Unauthorized upload attempt by a member-role user bypassing the client guard**
    - **What happens:** A user with a `member` role crafts a direct API request to
        the logo upload endpoint, bypassing the client-side absence of the upload
        control, and submits a valid image file with a valid session cookie in an
        attempt to change the organization logo without authorization.
    - **Source:** Adversarial action where a member-role user sends a hand-crafted
        multipart HTTP request to the upload endpoint, circumventing the client-side
        UI that hides the upload control from non-admin members.
    - **Consequence:** Without server-side role enforcement the member could overwrite
        the organization logo for all members — this would affect the org switcher,
        header, and every member-facing view across all active sessions in the
        organization.
    - **Recovery:** The upload handler rejects the request with HTTP 403 after
        verifying the calling user's role in the `member` table — the R2 write is
        never initiated, the organization record is not modified, and the server
        logs the unauthorized attempt with the user ID and timestamp for audit purposes.
- **D1 mutation fails after R2 write succeeds — orphaned object with no record update**
    - **What happens:** The image is successfully written to R2 and a valid object
        URL is returned, but the subsequent D1 mutation that writes the new logo URL
        to the `organization` table fails due to a transient database error, leaving
        an orphaned R2 object that is referenced nowhere in the database.
    - **Source:** Cloudflare D1 transient write failure, connection timeout between
        the Worker and the D1 binding, or a constraint violation in the `organization`
        table during the URL update operation.
    - **Consequence:** The admin receives an HTTP 500 error and sees an error toast —
        the organization record retains the previous logo URL so the UI is consistent,
        but an unreferenced R2 object consumes storage until it is cleaned up by a
        background process.
    - **Recovery:** The API returns HTTP 500 and logs the D1 failure with the orphaned
        R2 object key so a cleanup job can remove it — the client displays a localized
        error toast and the admin retries the upload, which overwrites the orphaned
        object in R2 and completes the D1 mutation on the next attempt.
- **Client-side MIME type validation bypassed via file extension spoofing**
    - **What happens:** A user renames a non-image file such as a PDF or executable
        to have a `.jpg` extension, causing the browser file input to report an
        image MIME type based on the extension while the actual file content is
        not a valid image.
    - **Source:** A user or adversary deliberately renames a file with an image
        extension to circumvent the client-side file type check, which relies on
        the browser-reported MIME type derived from the file extension.
    - **Consequence:** The client-side validation passes and the file is sent to the
        server — if the server does not independently validate the file content, a
        non-image binary could be stored in R2 and its URL written to the organization
        record, causing broken image renders across all logo display locations.
    - **Recovery:** The server rejects the upload with HTTP 400 after performing
        independent content-type validation — the R2 write is never initiated, the
        organization record is not updated, and the client displays a localized error
        toast notifying the admin that the selected file is not a valid image type.

## Declared Omissions

- This specification does not address the organization logo crop or resize UI — any
    image cropping or resizing behavior prior to upload is defined in a separate
    media-processing spec covering client-side image manipulation before network
    transmission
- This specification does not address the maximum file size constraint value in bytes
    — the specific numeric limit is defined in the API framework spec covering upload
    limits and is enforced identically by both the client validation and the server
    validation layer
- This specification does not address deleting an organization logo without replacing
    it — the action of removing a logo and reverting to the placeholder without
    uploading a new image is defined as a separate mutation in the organization
    settings spec
- This specification does not address rate limiting on the logo upload endpoint —
    that behavior is enforced by the global rate limiter defined in `api-framework.md`
    covering all upload endpoints uniformly across the API
- This specification does not address how the logo upload UI renders on mobile
    viewport sizes within Expo or within the Tauri desktop wrapper beyond the
    file picker selection behavior — those platform-specific layout details are
    covered by their respective platform specs in the roadmap

## Related Specifications

- [user-updates-organization-settings](user-updates-organization-settings.md) —
    Organization settings page that hosts the logo upload section, covering navigation
    to `/app/$orgSlug/settings` and the permission model for the settings page
- [database-schema](../foundation/database-schema.md) — Schema definition for the
    `organization` table including the `logoUrl` field written by the upload mutation
    and the `member` table used for role authorization on the upload endpoint
- [shared-contracts](../foundation/shared-contracts.md) — oRPC contract definitions
    for the logo upload mutation including the file type and size validation schema
    enforced before the request reaches the R2 write operation
- [api-framework](../foundation/api-framework.md) — Hono middleware stack, global
    error handler, and upload size limits that wrap the logo upload endpoint and
    return consistent JSON error shapes for 400, 403, and 500 responses
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure
    providing translation keys for all logo upload UI text including toast messages,
    button labels, and validation error descriptions rendered on the settings page

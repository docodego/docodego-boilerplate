---
id: SPEC-2026-047
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Uploads Profile Avatar

## Intent

This spec defines the end-to-end flow by which an authenticated user
uploads a new profile avatar image from the settings page at
`/app/settings/profile`. The user selects an image using the platform's
native file picker — a browser file input on web and desktop (Tauri
webview), and `expo-image-picker` on mobile. The client validates the
selected file against a 2 MB size limit and accepted MIME types (JPEG,
PNG, WebB) before uploading. If validation passes, the file is streamed
to Cloudflare R2 object storage via the `STORAGE` binding on the API,
a second mutation calls `authClient.updateUser()` to persist the new
avatar URL on the user record, and every UI component that displays the
user's avatar re-renders immediately via TanStack Query cache
invalidation. When no avatar URL is set the app renders a colored circle
containing the user's initials derived from their display name as a
consistent fallback across the header dropdown, organization member
lists, and the org switcher.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Avatar upload endpoint (`apps/api`) | write | Client sends the validated image file after the user selects a file and client-side validation passes successfully | The API returns a 500 error and the client displays a localized error toast — the previous avatar or initials fallback remains unchanged and the user retries the upload once the API recovers |
| Cloudflare R2 object storage (`STORAGE` binding) | write | API streams the validated image file to R2 after server-side validation of file size and MIME type passes | The API returns 500 and logs the R2 write failure — no URL is returned to the client, the existing avatar or initials fallback is preserved, and the user retries when R2 recovers |
| `authClient.updateUser()` | write | API calls updateUser with the new R2 object URL after the file is stored in R2 to persist the avatar URL on the user record | The mutation returns 500 and the R2 object is orphaned without a reference on the user record — the user record retains the previous avatar URL and the user retries once the auth service recovers |
| `expo-image-picker` | read | User selects an image on the mobile platform (Expo 54) to provide a file for the avatar upload flow | Image selection falls back to unavailable state — the client displays a localized error toast and the upload flow does not proceed until the picker becomes available again |
| `@repo/i18n` | read | All toast messages, button labels, and error text on the avatar upload UI are rendered via translation keys from the i18n package | Translation function falls back to the default English locale strings so the upload control remains usable without localized text in the active locale |
| TanStack Query cache | write | On successful avatar upload the user data cache is invalidated to trigger a re-fetch across all components that display the user avatar | Cache invalidation falls back to a stale read — components retain the old avatar or initials fallback until the next manual reload or navigation event triggers a fresh query |
| Sonner toast | write | On upload success or failure a localized toast notification is displayed to the user via the Sonner toast library | Toast notification degrades silently — the upload result is reflected in the UI state change (new avatar appears or initials fallback remains) even without a visible toast |

## Behavioral Flow

1. **[User]** navigates to `/app/settings/profile` via the Settings
    link in the sidebar's user section to access the profile settings
    page where the avatar upload control is located
2. **[Client]** renders the profile page with an avatar section — if an
    avatar has already been uploaded it is shown as a thumbnail image;
    otherwise a colored circle containing the user's initials derived
    from their display name is displayed as the fallback
3. **[Client]** renders a localized "Change avatar" button or clickable
    overlay that appears on hover over the avatar section, inviting the
    user to upload a new image via the platform's native file picker
4. **[User]** clicks the avatar placeholder or the "Change avatar"
    button to open the platform's native file picker configured to
    accept image types only (JPEG, PNG, WebP)
5. **[Branch -- web or desktop (Tauri webview)]** The standard browser
    file input opens, displaying the operating system file picker with
    localized text provided by the OS — the picker is filtered to
    image MIME types only
6. **[Branch -- mobile (Expo)]** The `expo-image-picker` handles the
    selection presenting the system media library or camera interface
    to the user for photo selection on Expo 54
7. **[User]** selects an image file from the file picker or media
    library and confirms the selection to proceed with the upload
8. **[Client]** validates the selected file against size and type
    constraints before sending it to the server — accepted types are
    JPEG, PNG, and WebP; the file size limit is 2 MB and any file
    exceeding this limit is rejected before any network request is made
9. **[Branch -- validation fails]** A localized error toast appears via
    Sonner describing the constraint that was violated ("File too large"
    or "Unsupported format"), the upload is aborted, and the previous
    avatar or initials fallback remains unchanged so the user retries
    with a different file
10. **[Branch -- validation passes]** The client sends the image to the
    avatar upload endpoint in `apps/api` for server-side processing
11. **[Server]** performs server-side validation of file size and MIME
    type independently of the client-side validation, then streams the
    file to Cloudflare R2 object storage via the `STORAGE` binding
12. **[Server]** returns the stored R2 object public URL to the client
    after the file upload to R2 completes with status 200
13. **[Server]** a second mutation calls `authClient.updateUser()` to
    update the user record with the new avatar URL returned from R2
14. **[Client]** receives the success response, displays a localized
    toast confirmation via Sonner, and invalidates the cached user data
    in TanStack Query to trigger a re-fetch across all avatar-displaying
    components
15. **[Client]** every component that displays the user's avatar — the
    header dropdown, organization member lists, and the org switcher —
    re-fetches the user data and renders the new avatar image immediately
    replacing the previous avatar or initials fallback
16. **[Branch -- upload or mutation fails]** An error toast describes the
    problem via Sonner — the previous avatar or initials fallback remains
    unchanged so the user retries the upload
17. **[Client]** whenever the user has no avatar URL set — either because
    they never uploaded one or because the image was removed — the app
    renders a colored circle containing the user's initials derived from
    their display name as a consistent fallback across the header, member
    lists, and the org switcher

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | picker_open | User clicks avatar placeholder or "Change avatar" button | The profile settings page has loaded and the avatar section is rendered |
| picker_open | file_selected | User selects an image file and confirms the selection | File picker returns a file object with a non-empty name and size greater than 0 |
| picker_open | idle | User dismisses the file picker without selecting a file | File picker closes with no selection returned to the client |
| file_selected | validation_error | Client validation rejects the selected file | File MIME type is not JPEG, PNG, or WebP, or file size exceeds 2 MB |
| file_selected | uploading | Client validation passes for the selected file | File MIME type is JPEG, PNG, or WebP and file size is at most 2 MB |
| validation_error | picker_open | User clicks avatar placeholder or "Change avatar" button again to retry | Previous validation error toast has been displayed and the user initiates a new selection |
| uploading | success | API returns 200 and user record is updated with the new avatar URL via authClient.updateUser() | R2 write and updateUser mutation both complete with status 200 |
| uploading | upload_error | API returns non-200 or network error during upload | HTTP response status does not equal 200 or the network request times out |
| success | idle | TanStack Query cache is invalidated and components re-fetch the updated avatar | Cache invalidation call completes and at least 1 re-fetch is triggered |
| upload_error | picker_open | User clicks avatar placeholder or "Change avatar" button again to retry | Previous upload error toast has been displayed and the user initiates a new selection |

## Business Rules

- **Rule client-validation-before-upload:** IF the selected file's size
    exceeds 2 MB or its MIME type is not one of `image/jpeg`,
    `image/png`, or `image/webp` THEN the client aborts the upload
    before sending any request to the API and displays a localized
    error toast — the count of accepted MIME types equals 3 and any
    file outside this set or above the size limit is rejected
- **Rule server-side-validation-independent:** IF the API receives a
    file upload request THEN it performs an independent server-side
    validation of file size and MIME type before streaming to R2 —
    client-side validation alone is not sufficient and both validations
    must pass for the upload to proceed to R2
- **Rule two-step-mutation:** IF the R2 upload completes and returns a
    valid object URL THEN the API calls `authClient.updateUser()` to
    persist the avatar URL on the user record — the upload and the
    record update are 2 distinct sequential operations and the record
    is only updated after R2 returns a valid URL
- **Rule initials-fallback-when-no-avatar:** IF the user record has no
    avatar URL set or the avatar URL is empty THEN every component that
    renders avatars displays a colored circle containing the user's
    initials derived from their display name — this fallback applies
    consistently across the header dropdown, member lists, and org
    switcher
- **Rule cache-invalidation-on-success:** IF the upload mutation
    succeeds and the user record is updated with a new avatar URL THEN
    the TanStack Query cache entry for the user data is invalidated
    immediately so all avatar-displaying components re-fetch and render
    the new image without requiring a manual page reload

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner (account owner) | View current avatar or initials fallback, open file picker, select image, upload avatar, see success or error toast, view updated avatar after upload across all components | None — the owner has full access to their own profile avatar upload actions on the profile settings page | The "Change avatar" button and clickable overlay are visible and interactive on the profile settings page |
| Admin | View current avatar or initials fallback, open file picker, select image, upload their own avatar, see success or error toast, view updated avatar | Cannot upload avatars for other users — this is a user-level route and each user manages only their own avatar on the profile page | The "Change avatar" button and clickable overlay are visible and interactive for the authenticated admin's own profile only |
| Member | View current avatar or initials fallback, open file picker, select image, upload their own avatar, see success or error toast, view updated avatar | Cannot upload avatars for other users — this is a user-level route and each user manages only their own avatar on the profile page | The "Change avatar" button and clickable overlay are visible and interactive for the authenticated member's own profile only |
| Unauthenticated visitor | None — route guard redirects to `/signin` before the profile settings page loads at `/app/settings/profile` | Access to any part of `/app/settings/profile` including the avatar upload section is denied by the route guard | The profile settings page is not rendered; redirect to `/signin` occurs immediately before any content loads |

## Constraints

- The file type validation accepts exactly 3 MIME types: `image/jpeg`,
    `image/png`, and `image/webp` — the count of accepted MIME types
    equals 3 and the server rejects any file whose content-type header
    does not match one of these 3 values
- The maximum allowed file size is 2 MB (2,097,152 bytes) — any file
    exceeding this limit is rejected by both the client-side validation
    and the server-side validation, and the count of API requests made
    for an oversized file equals 0 on the client side
- The TanStack Query cache invalidation is triggered in the mutation
    success handler — the count of stale avatar renders after a
    successful upload equals 0 within the same client session before
    the next navigation event
- All user-facing text including toast messages, button labels, and
    error descriptions is rendered via i18n translation keys — the
    count of hardcoded English strings in the avatar upload UI
    components equals 0
- Server-side validation runs independently of client-side validation
    — the API does not trust the client's pre-validation and performs
    its own size and type checks before writing to R2
- The initials fallback circle is rendered in at least 3 locations
    (header dropdown, organization member lists, org switcher) whenever
    the user record has no avatar URL set — the count of locations
    missing the fallback equals 0

## Acceptance Criteria

- [ ] The profile settings page at `/app/settings/profile` renders the avatar section — the avatar thumbnail or initials fallback element is present and visible after the page loads
- [ ] The "Change avatar" button or clickable overlay is present and interactive for authenticated users — the element is present and has no disabled attribute when the user is signed in
- [ ] Clicking the "Change avatar" button or placeholder opens the file picker filtered to image types only — the file input accept attribute equals `image/jpeg,image/png,image/webp` on the web platform
- [ ] Selecting a file with an unsupported MIME type causes the client to display a localized error toast — the toast element is present and the count of API requests made during the rejected upload equals 0
- [ ] Selecting a file that exceeds 2 MB causes the client to display a localized error toast — the toast element is present and the count of API requests made during the rejected upload equals 0
- [ ] A validated file upload sends the image to the avatar upload endpoint — the API receives the request and the request payload contains the file with a non-empty content-type matching one of the 3 accepted MIME types
- [ ] The API validates file type server-side independently of the client — submitting a file with an invalid MIME type directly to the endpoint returns HTTP 400 even when client pre-validation is bypassed, and the count of R2 write operations equals 0
- [ ] The API validates file size server-side independently of the client — submitting a file exceeding 2 MB directly to the endpoint returns HTTP 400 even when client pre-validation is bypassed, and the count of R2 write operations equals 0
- [ ] After a successful R2 upload the API calls `authClient.updateUser()` with the new avatar URL — the user record avatar field value is non-empty and equals the URL returned by R2 after the upload
- [ ] After a successful upload a localized success toast appears via Sonner — the toast element is present and visible within 500ms of the API returning 200
- [ ] After a successful upload the TanStack Query cache for user data is invalidated — the count of components still rendering the old avatar or initials fallback equals 0 within 1 re-fetch cycle
- [ ] After a successful upload the header dropdown, organization member lists, and org switcher all display the new avatar — the count of UI locations still showing the old avatar or initials fallback after re-fetch equals 0
- [ ] On upload failure the previous avatar or initials fallback remains unchanged — the user record avatar field value equals the value before the failed upload attempt, and the count of modified records equals 0
- [ ] On upload failure a localized error toast appears describing the problem — the error toast element is present and visible after the API returns a non-200 response
- [ ] When the user record has no avatar URL set the app renders a colored circle with the user's initials — the initials fallback element is present in the header dropdown, member lists, and org switcher simultaneously
- [ ] All user-facing strings in the avatar upload UI are rendered via i18n translation keys — the count of hardcoded English string literals outside translation calls in the avatar upload components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User dismisses the file picker without selecting a file | The upload flow does not proceed and the avatar section reverts to its previous state showing the existing thumbnail or initials fallback — no API request is made | The count of API requests after the picker is dismissed equals 0 and the avatar section element is unchanged |
| User selects an image that passes client-side validation but the R2 write times out after partial transfer | The API returns 500, no URL is persisted on the user record via authClient.updateUser(), and the client displays a localized error toast — the previous avatar or initials fallback is preserved | HTTP response status equals 500, the user record avatar field value is unchanged from before the attempt, and the error toast element is present |
| User clicks the "Change avatar" button twice in rapid succession before the picker opens | The client opens the file picker on the first click — the second click has no additional effect because the picker is already open on the screen | The count of picker instances open simultaneously equals 1 and the count of API requests before a file is selected equals 0 |
| User uploads a new avatar while the TanStack Query cache contains stale user data from a previous session | The mutation success handler invalidates the cache regardless of its age — all components re-fetch the user data and render the new avatar image | The count of components still rendering an avatar URL older than the successful upload timestamp equals 0 after re-fetch completes |
| User with no display name set triggers the initials fallback rendering | The initials fallback renders a colored circle with a default placeholder character instead of empty initials — the circle is never empty or invisible | The initials fallback element is present, non-empty, and has a visible background color in the header dropdown, member lists, and org switcher |
| User uploads a new avatar immediately after another browser tab uploads a different avatar for the same account | The second upload overwrites the first — the user record stores the URL of whichever upload completed last, and cache invalidation ensures all tabs eventually render the most recent avatar | The user record avatar field value equals the R2 URL from the last completed upload, and both tabs render the same avatar after re-fetch |

## Failure Modes

- **R2 object storage write fails mid-stream after partial file transfer during avatar upload**
    - **What happens:** The Cloudflare R2 `STORAGE` binding times out or
        returns an error partway through streaming the image bytes, leaving
        an incomplete or absent object in R2 and no valid URL to return
        to the client for the avatar update.
    - **Source:** Cloudflare R2 service degradation, network interruption
        between the Worker and the R2 binding, or the uploaded file
        exceeding an internal R2 object size limit during the streaming
        write operation.
    - **Consequence:** The API cannot return a valid avatar URL to the
        client — the user record is not updated via authClient.updateUser(),
        the previous avatar or initials fallback is preserved, and the
        user receives no confirmation that the new avatar was saved.
    - **Recovery:** The API returns HTTP 500 and logs the R2 write
        failure with the user ID and file metadata — the client displays
        a localized error toast and the user retries the upload once
        R2 recovers from the transient failure condition.
- **authClient.updateUser() mutation fails after R2 write succeeds leaving an orphaned R2 object**
    - **What happens:** The image is written to R2 and a valid object
        URL is returned, but the subsequent authClient.updateUser() call
        that persists the new avatar URL on the user record fails due to
        a transient error, leaving an orphaned R2 object referenced
        nowhere in the user record.
    - **Source:** Auth service transient write failure, connection timeout
        between the Worker and the auth backend, or a constraint violation
        during the user record update operation when calling
        authClient.updateUser().
    - **Consequence:** The user receives an HTTP 500 error and sees an
        error toast — the user record retains the previous avatar URL so
        the UI is consistent, but an unreferenced R2 object consumes
        storage until it is cleaned up by a background process.
    - **Recovery:** The API returns HTTP 500 and logs the updateUser
        failure with the orphaned R2 object key so a cleanup job can
        remove it — the client displays a localized error toast and the
        user retries the upload, which overwrites the orphaned object
        in R2 on the next attempt.
- **Client-side validation rejects the selected file before any network request is made**
    - **What happens:** The user selects a file that exceeds the 2 MB
        size limit or has a MIME type outside the accepted set of JPEG,
        PNG, and WebP — the client-side validation catches the violation
        before any network request is initiated and the upload flow is
        halted immediately.
    - **Source:** User selects an oversized image, a GIF, a BMP, or any
        non-accepted file format from the file picker — the browser or
        expo-image-picker returns the file metadata that the client
        validates against the defined constraints.
    - **Consequence:** No API request is made, no R2 storage is consumed,
        and the server is not involved — the user sees a localized error
        toast explaining the constraint ("File too large" or "Unsupported
        format") and the previous avatar or initials fallback is unchanged.
    - **Recovery:** The client displays a localized error toast via
        Sonner and the user retries by selecting a different file that
        meets the 2 MB size limit and is one of the 3 accepted MIME
        types (JPEG, PNG, WebP) from the file picker.
- **Server-side validation rejects the file after client-side validation passed**
    - **What happens:** The client-side validation passes because the
        browser-reported MIME type matches an accepted format, but the
        server-side validation detects that the actual file content does
        not match the declared content-type header or the file exceeds
        server-enforced limits, and the upload is rejected with HTTP 400.
    - **Source:** A user renames a non-image file to have an image
        extension causing the browser to report an image MIME type based
        on the extension, or the file passes the 2 MB client check but
        exceeds a stricter server-side byte limit after encoding overhead.
    - **Consequence:** The server rejects the upload before writing to
        R2 — no storage is consumed, the user record is not modified via
        authClient.updateUser(), and the previous avatar or initials
        fallback remains unchanged across all avatar-displaying components.
    - **Recovery:** The server rejects the upload with HTTP 400 and logs
        the validation failure with the user ID and file metadata — the
        client displays a localized error toast notifying the user that
        the selected file is not a valid image type and the user retries
        with a valid file.

## Declared Omissions

- This specification does not address avatar image cropping or resizing UI — any image manipulation behavior prior to upload is defined in a separate media-processing spec covering client-side image editing before network transmission
- This specification does not address deleting an avatar without replacing it — the action of removing an avatar and reverting to the initials fallback without uploading a new image is defined as a separate mutation in the user settings spec
- This specification does not address rate limiting on the avatar upload endpoint — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all upload endpoints uniformly across the API
- This specification does not address how the avatar upload UI renders on mobile viewport sizes within Expo or within the Tauri desktop wrapper beyond the file picker selection behavior described in the behavioral flow section
- This specification does not address the specific color derivation algorithm for the initials fallback circle — the color generation logic based on the user's display name is defined in a shared UI utility spec

## Related Specifications

- [user-updates-organization-settings](user-updates-organization-settings.md) — Organization settings page that hosts member lists where user avatars are displayed, covering navigation to organization settings and the permission model
- [database-schema](../foundation/database-schema.md) — Schema definition for the user record including the avatar URL field written by the authClient.updateUser() mutation and the display name field used for initials fallback
- [shared-contracts](../foundation/shared-contracts.md) — oRPC contract definitions for the avatar upload mutation including the file type and size validation schema enforced before the request reaches the R2 write operation
- [api-framework](../foundation/api-framework.md) — Hono middleware stack, global error handler, and upload size limits that wrap the avatar upload endpoint and return consistent JSON error shapes for 400 and 500 responses
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization infrastructure providing translation keys for all avatar upload UI text including toast messages, button labels, and validation error descriptions

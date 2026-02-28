---
id: SPEC-2026-090
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Uploads a File

## Intent

This spec defines how a user selects and uploads a file across all DoCodeGo platform targets — web, desktop, mobile — and how the API processes, validates, and stores the file in Cloudflare R2 object storage. The upload flow begins when the user selects a file using the platform's native file picker, the frontend sends the file data to the API upload endpoint, the API validates size limits and content-type restrictions before streaming the data to R2, and the API returns the stored object's URL or key to the client. Cloudflare R2 provides an S3-compatible API with zero egress costs and is configured as the `STORAGE` binding in `wrangler.toml`, available to all route handlers through the Cloudflare Workers environment. For downloads, the API generates presigned URLs for temporary direct access to R2 objects or proxies the file content through the API layer. On web and desktop, the standard HTML file input presents the native file dialog. On mobile, `expo-image-picker` handles photo and camera selection while `expo-document-picker` handles general file selection, both feeding into the same upload API endpoint used by all platforms. The developer defines specific size limits and content-type constraints based on the use case.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Cloudflare R2 object storage (S3-compatible object storage with zero egress costs configured as the `STORAGE` binding in `wrangler.toml`, used to store user-generated content like avatars, organization logos, and document attachments) | read/write | When the API upload endpoint receives a validated file from the frontend, the handler streams the file data to R2 using the `STORAGE` binding and stores it under a generated key, and when a download is requested, the API reads from R2 to generate a presigned URL or proxy the content | The R2 service is unreachable due to a Cloudflare infrastructure outage or the `STORAGE` binding is misconfigured in `wrangler.toml` — the API returns an HTTP 502 error to the client indicating the storage backend is unavailable and logs the R2 connection failure |
| API upload endpoint in `apps/api` (the Hono route handler that receives multipart file data from the frontend, validates size and content-type against configured limits, and streams the validated file to R2 storage) | read/write | When the frontend sends a file upload request via a multipart POST, the endpoint reads the request body, validates the file size against the configured maximum and the content-type against the allowed list, and if validation passes, streams the data to R2 | The API endpoint is unreachable due to a Cloudflare Workers deployment failure or the worker exceeds its CPU time limit during upload processing — the frontend receives a network error or HTTP 502 and displays a localized error toast via Sonner to inform the user |
| HTML file input on web and desktop (the standard browser file input element that triggers the operating system's native file picker dialog, used identically on web in the browser and on desktop inside the Tauri webview) | read | When the user clicks the upload trigger button in the application, the HTML file input opens the native OS file picker dialog, and the user selects a file which the browser reads into a `File` object for submission to the API | The file input element fails to trigger the native file dialog due to a browser security restriction that blocks programmatic file input activation — the user cannot select a file and the application displays a localized message indicating that file selection is not available |
| `expo-image-picker` on mobile (Expo SDK module that provides access to the device photo library and camera for selecting images on iOS and Android, returning the selected image data for upload to the API endpoint) | read | When the mobile user taps the upload trigger for photo or camera content, `expo-image-picker` opens the device's photo library or camera interface, and the user selects or captures an image which is returned as a local file URI for upload | The `expo-image-picker` module fails to open due to missing camera or photo library permissions on the device — the application catches the permission error, displays a localized toast notifying the user to grant the required permission in device settings, and logs the permission denial |
| `expo-document-picker` on mobile (Expo SDK module that provides access to the device file system and cloud storage providers for selecting general documents on iOS and Android, returning the selected file data for upload) | read | When the mobile user taps the upload trigger for general file content, `expo-document-picker` opens the device's document selection interface, and the user selects a file which is returned as a local file URI for upload to the API endpoint | The `expo-document-picker` module fails to open due to a native module linking error or the document picker interface is not available on the device — the application catches the error, displays a localized toast indicating file selection failed, and logs the module error |
| Presigned URL generator (R2 API capability that creates time-limited signed URLs granting temporary direct access to stored objects, used to serve large files directly from R2 without routing content through the API worker) | write | When the frontend requests a download for a stored file, the API generates a presigned URL with a configured expiry duration and returns it to the client, which uses the URL to fetch the file directly from R2 | The presigned URL generation fails due to an R2 API error or the signing credentials are expired — the API falls back to proxying the file content through the worker and returns the file data directly in the response, logging the presign failure |

## Behavioral Flow

1. **[User]** taps or clicks the upload trigger in the application
    interface, which activates the platform-specific file picker — the
    HTML file input on web and desktop, `expo-image-picker` or
    `expo-document-picker` on mobile

2. **[User]** selects a file from the native file picker dialog — on
    web and desktop, the browser reads the selected file into a `File`
    object; on mobile, the picker returns a local file URI pointing to
    the selected content

3. **[User]** confirms the selection and the frontend begins the upload
    process by sending the file data to the API upload endpoint as a
    multipart POST request with the file content and metadata including
    the original filename and content-type

4. **[User]** sees a loading state on the upload button (spinner or
    disabled appearance) indicating the upload is in flight, preventing
    double submission of the same file

5. **[User]** waits while the API upload endpoint receives the
    multipart request body, extracts the file data, and validates the
    file size against the configured maximum limit (for example 2 MB
    for avatars) and the content-type against the allowed list (for
    example image-only types for avatars)

6. **[User]** receives immediate feedback if validation fails — the API
    returns HTTP 400 with a structured JSON error response containing
    field-level detail about which validation rule failed (size exceeded
    or content-type not allowed) and the frontend displays a localized
    error toast via Sonner

7. **[User]** waits while the API streams the validated file data to
    Cloudflare R2 using the `STORAGE` binding configured in
    `wrangler.toml`, storing the file under a generated key in the R2
    bucket

8. **[User]** receives a success response from the API containing the
    stored object's URL or storage key, and the frontend updates the UI
    to display the uploaded file (for example rendering the new avatar
    image or showing the document attachment link)

9. **[User]** requests a download of a previously uploaded file — the
    API generates a presigned URL with a configured time-limited expiry
    granting temporary direct access to the R2 object, or proxies the
    file content through the API worker for smaller files

10. **[User]** receives the file content through the presigned URL
    (direct from R2) or through the API proxy response, and the
    frontend either displays the image inline or triggers a browser
    download for document attachments

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | file_selected | The user taps the upload trigger and selects a file from the platform-native file picker dialog, providing a `File` object on web/desktop or a local file URI on mobile | The file picker returns a valid file reference with a non-empty filename and a readable file handle or URI |
| file_selected | uploading | The frontend constructs a multipart POST request with the selected file data and sends it to the API upload endpoint, transitioning the upload button to its loading state | The file reference is readable and the network connection is available to send the multipart request to the API |
| uploading | validation_failed | The API upload endpoint rejects the file because the file size exceeds the configured maximum limit or the content-type is not in the allowed list for the upload context | The file size is greater than the configured maximum (for example greater than 2 MB for avatars) or the content-type is not in the allowed list |
| uploading | storing | The API upload endpoint validates the file size and content-type and both pass the configured constraints, and the handler begins streaming the validated file data to Cloudflare R2 | The file size is within the configured limit and the content-type matches an allowed type in the upload context configuration |
| validation_failed | idle | The frontend receives the HTTP 400 error response, displays a localized error toast via Sonner describing the validation failure, clears the loading state, and returns the upload button to its clickable state | The error response is received and parsed and the toast notification is displayed to the user |
| storing | upload_complete | The R2 storage operation completes and the API returns a success response containing the stored object's URL or storage key to the frontend | The R2 put operation returns a success status and the stored object key is generated and included in the response |
| storing | storage_failed | The R2 storage operation fails due to an R2 service error, network timeout, or storage quota issue, and the API returns an HTTP 502 error to the frontend | The R2 put operation returns an error status or the request to R2 times out before the object is stored |
| storage_failed | idle | The frontend receives the HTTP 502 error response, displays a localized error toast indicating the storage backend is unavailable, clears the loading state, and returns the upload button to its clickable state | The error response is received and parsed and the toast notification is displayed to the user |
| upload_complete | idle | The frontend updates the UI to display the uploaded file (rendering the new image or showing the attachment link), clears the loading state, and returns the upload trigger to its clickable state for subsequent uploads | The UI update completes and the loading state is cleared |

## Business Rules

- **Rule size-validated-before-storage:** IF a file upload request
    arrives at the API endpoint THEN the handler validates the file
    size against the configured maximum before streaming to R2 — the
    count of files stored in R2 that exceed the configured size limit
    equals 0
- **Rule content-type-validated-before-storage:** IF a file upload
    request arrives at the API endpoint THEN the handler validates the
    content-type against the allowed list before streaming to R2 — the
    count of files stored in R2 with a disallowed content-type equals 0
- **Rule validation-failure-returns-400:** IF the file size exceeds the
    configured maximum or the content-type is not in the allowed list
    THEN the API returns HTTP 400 with a structured JSON error
    including field-level detail — the HTTP status code for validation
    failures equals 400
- **Rule r2-zero-egress-cost:** IF a file is served from R2 through a
    presigned URL THEN no egress cost is incurred because R2 provides
    zero egress pricing — the count of egress charges for R2 presigned
    URL downloads equals 0
- **Rule presigned-url-preferred-for-large-files:** IF the frontend
    requests a download of a stored file and the file size exceeds the
    threshold for direct proxy THEN the API generates a presigned URL
    for direct R2 access — the count of large files proxied through the
    worker instead of served via presigned URL equals 0
- **Rule loading-state-prevents-double-submission:** IF an upload
    request is in flight THEN the upload button displays a loading
    state and is non-clickable — the count of duplicate upload requests
    sent while a previous upload is in flight equals 0
- **Rule same-endpoint-all-platforms:** IF a file is uploaded from web,
    desktop, or mobile THEN all platforms send the file to the same API
    upload endpoint — the count of platform-specific upload endpoints
    equals 1 (the single shared endpoint)
- **Rule storage-binding-from-wrangler:** IF the API handler accesses
    R2 THEN it uses the `STORAGE` binding defined in `wrangler.toml` —
    the count of hardcoded R2 credentials in the API source code
    equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (the authenticated person who selects a file through the platform-native file picker, initiates the upload, monitors the loading state, and views or downloads the stored file after upload completes) | Select a file through the platform-native file picker, submit the file to the API upload endpoint, view the upload loading state and success or error feedback, download previously uploaded files through presigned URLs or API proxy responses, retry a failed upload by selecting and submitting the file again | Cannot bypass file size or content-type validation enforced at the API layer, cannot upload a file without authentication, cannot directly access R2 storage without going through the API endpoint, cannot modify or delete other users' uploaded files through the upload endpoint | The user sees the upload trigger button, the loading state during upload, the success confirmation with the uploaded file preview, the localized error toast on validation or storage failure, and the download link for previously uploaded files — the user does not see the R2 storage key, the presigned URL generation details, or the internal validation configuration |

## Constraints

- The API upload endpoint validates the file size and content-type
    within 50 ms of receiving the complete multipart request body — the
    count of milliseconds from request body received to validation
    result equals 50 or fewer.
- The R2 storage operation for a 2 MB file completes within 2000 ms
    of the validation passing — the count of milliseconds from
    validation pass to R2 storage confirmation equals 2000 or fewer.
- Presigned URLs generated by the API have a maximum expiry duration
    of 3600 seconds (1 hour) — the count of seconds in the presigned
    URL expiry equals 3600 or fewer.
- The upload button transitions to the loading state within 100 ms of
    the user confirming file selection — the count of milliseconds from
    selection confirmation to loading state display equals 100 or fewer.
- The structured JSON error response for validation failures includes
    at least 1 field-level detail entry specifying which validation
    rule was violated — the count of field-level detail entries in a
    validation error response equals 1 or more.
- The upload endpoint accepts files from all 3 platform targets (web,
    desktop, mobile) through a single shared endpoint — the count of
    platform-specific upload endpoints equals 1.

## Acceptance Criteria

- [ ] The user selects a file through the platform-native file picker and the frontend sends it to the API upload endpoint as a multipart POST — the count of upload requests with a content-type other than `multipart/form-data` equals 0
- [ ] The API validates file size before storing in R2 and rejects files exceeding the configured limit — the HTTP status code for oversized files equals 400
- [ ] The API validates content-type before storing in R2 and rejects files with disallowed types — the HTTP status code for disallowed content-types equals 400
- [ ] The validation error response includes a structured JSON body with field-level detail — the `code` field in the error response is non-empty
- [ ] The frontend displays a localized error toast via Sonner when validation fails — the toast element is present within 500 ms of receiving the error response
- [ ] The API streams the validated file to R2 using the `STORAGE` binding and returns the stored object URL or key — the response body contains a non-empty storage key or URL
- [ ] The upload button shows a loading state while the request is in flight preventing double submission — the button disabled attribute is present during upload
- [ ] The frontend updates the UI to display the uploaded file after a successful upload — the uploaded file preview element is present after the success response
- [ ] The API generates a presigned URL with time-limited expiry for file downloads — the presigned URL expiry duration equals 3600 seconds or fewer
- [ ] On web and desktop the standard HTML file input opens the native OS file dialog when the user clicks the upload trigger — the count of file input elements with a type other than `file` equals 0
- [ ] On mobile `expo-image-picker` handles photo and camera selection and returns a local file URI — the returned URI is non-empty
- [ ] On mobile `expo-document-picker` handles general file selection and returns a local file URI — the returned URI is non-empty
- [ ] All platforms send uploads to the same single API endpoint — the count of distinct upload endpoint paths equals 1

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user selects a file that is exactly at the configured size limit (for example exactly 2 MB for an avatar upload) | The API accepts the file because the size is within the limit (less than or equal to the maximum), streams it to R2, and returns a success response with the stored object URL | The HTTP status code equals 200 and the response body contains a non-empty storage key |
| The user selects a file with a valid content-type extension but the actual file content does not match the declared MIME type (for example a renamed text file with a `.jpg` extension) | The API validates based on the declared content-type from the multipart header, accepts the file, and stores it in R2 — content-based MIME detection is not performed at the boilerplate level | The HTTP status code equals 200 because the declared content-type matches the allowed list regardless of the actual file content |
| The user cancels the native file picker dialog without selecting a file on any platform | The frontend detects the cancellation event (empty file input change on web/desktop, cancelled result from expo pickers on mobile), does not send an upload request, and returns to the idle state | The count of upload requests sent to the API equals 0 and the upload button remains in its clickable state |
| The user's network connection drops during the file upload while the multipart request body is being transmitted to the API | The frontend's HTTP client detects the network failure, cancels the in-flight request, displays a localized error toast indicating the upload failed due to a network error, and returns the upload button to its clickable state | The error toast is displayed with a network error message and the upload button returns to the clickable state |
| The R2 storage quota for the bucket is exceeded when the API attempts to store a validated file | The R2 put operation returns a quota exceeded error, the API catches the error and returns HTTP 502 to the client with a storage error code, and the frontend displays a localized error toast | The HTTP status code equals 502 and the error response code indicates a storage backend failure |
| The user attempts to upload a file on mobile but has not granted camera or photo library permissions required by `expo-image-picker` | The `expo-image-picker` returns a permission denied result, the application displays a localized toast instructing the user to grant the permission in device settings, and no upload request is sent | The toast message references the missing permission and the count of upload requests sent equals 0 |

## Failure Modes

- **R2 storage service is unreachable during a file upload causing the storage operation to fail**
    - **What happens:** The API upload endpoint validates the file and attempts to stream it to R2 using the `STORAGE` binding, but the R2 service is unreachable due to a Cloudflare infrastructure outage, network partition, or misconfigured binding in `wrangler.toml`.
    - **Source:** A Cloudflare infrastructure incident affecting R2 availability, a network partition between the Workers runtime and the R2 storage backend, or an incorrect `STORAGE` binding name in the `wrangler.toml` configuration.
    - **Consequence:** The validated file is not stored and the user's upload fails despite the file passing all validation checks, requiring the user to retry the upload after the storage backend recovers.
    - **Recovery:** The API catches the R2 connection error, returns HTTP 502 with a structured error response indicating storage unavailability, logs the R2 failure details including the binding name and error code, and the frontend displays a localized error toast notifying the user to retry the upload later.

- **Presigned URL generation fails when the user requests a download of a stored file**
    - **What happens:** The API attempts to generate a presigned URL for a stored R2 object to allow the frontend to download the file directly, but the presign operation fails due to an R2 API error, expired signing credentials, or an invalid object key.
    - **Source:** The R2 presign API returns an error due to a temporary service issue, the signing credentials configured in the Workers environment have expired and need rotation, or the stored object key references a file that has been deleted from the bucket.
    - **Consequence:** The user cannot download the file through a direct R2 URL, experiencing a delay or error when attempting to access previously uploaded content.
    - **Recovery:** The API catches the presign failure, falls back to proxying the file content directly through the worker by reading the object from R2 and streaming it in the response body, and logs the presign failure with the object key and error details for credential rotation or investigation.

- **Mobile file picker module fails to initialize due to a native linking error**
    - **What happens:** The user taps the upload trigger on mobile and the application attempts to open `expo-image-picker` or `expo-document-picker`, but the native module fails to initialize because the Expo module is not correctly linked in the native build or the required native framework is missing on the device.
    - **Source:** A missing native module link in the Expo build configuration, an incompatible Expo SDK version that dropped support for the picker module API, or a device running an OS version older than the minimum required by the picker module.
    - **Consequence:** The file picker does not open and the user cannot select a file for upload on the mobile platform, blocking the upload flow entirely on that device.
    - **Recovery:** The application catches the native module initialization error, displays a localized toast notifying the user that file selection is currently unavailable on their device, logs the module error with the Expo SDK version and device OS version, and the user falls back to using the web application for file uploads.

- **File upload request times out because the file size is large and the network bandwidth is limited**
    - **What happens:** The user selects a large file within the size limit and the frontend begins transmitting the multipart request to the API, but the upload takes longer than the HTTP client's timeout threshold due to a low-bandwidth network connection, and the request is aborted before completion.
    - **Source:** The user is on a mobile data connection with bandwidth under 1 Mbps, the file is near the maximum allowed size and the upload duration exceeds the configured HTTP client timeout, or network congestion causes packet loss and retransmission delays.
    - **Consequence:** The upload fails after the user has waited for an extended period, and the partially transmitted data is discarded by the API without being stored in R2, requiring the user to retry the upload when network conditions improve.
    - **Recovery:** The frontend's HTTP client detects the timeout, cancels the request, displays a localized error toast indicating the upload timed out and suggesting the user retry on a faster connection, and returns the upload button to its clickable state so the user can attempt the upload again.

## Declared Omissions

- This specification does not define specific file size limits or allowed content-type lists for individual upload use cases — the developer configures these constraints per endpoint based on the application's requirements (for example 2 MB image-only for avatars versus larger limits for documents)
- This specification does not cover the server-side file processing pipeline after storage such as image resizing, thumbnail generation, or virus scanning — those are application-specific post-upload operations beyond the boilerplate scope
- This specification does not define the R2 bucket configuration, lifecycle policies, or storage class settings — those are infrastructure concerns managed through the Cloudflare dashboard or Terraform configuration outside the application code
- This specification does not address Tauri's native file picker API (`tauri-plugin-dialog`) for advanced use cases like directory selection — the boilerplate uses the standard HTML file input inside the Tauri webview which provides identical behavior to the web platform
- This specification does not cover concurrent multi-file uploads or batch upload progress tracking — the defined flow handles single-file uploads and multi-file support requires a separate specification with its own progress and error handling patterns

## Related Specifications

- [system-handles-errors](system-handles-errors.md) — defines the
    global error handler and structured JSON error response format used
    by the upload endpoint when returning validation failures (HTTP 400)
    and storage errors (HTTP 502) to the frontend client
- [session-lifecycle](session-lifecycle.md) — defines the
    authenticated session that provides the user identity context
    required to authorize upload requests and associate stored files
    with the uploading user's account
- [system-detects-locale](system-detects-locale.md) — defines the
    locale detection flow that determines the language used for
    localized error toast messages displayed by the frontend when
    upload validation fails or the storage backend is unavailable
- [user-changes-language](user-changes-language.md) — defines the
    language switching mechanism that determines which locale is active
    for the file picker UI text and error toast messages displayed
    during the upload flow across all platform targets

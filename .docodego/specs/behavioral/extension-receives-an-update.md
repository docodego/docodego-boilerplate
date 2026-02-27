---
id: SPEC-2026-083
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# Extension Receives an Update

## Intent

This spec defines how the DoCodeGo browser extension receives and
applies an update distributed through the Chrome Web Store or Firefox
Add-ons. The browser handles auto-updates in the background according
to its own update schedule, typically checking every few hours without
any action from the user. When a new extension version is published,
the browser downloads the new package and installs it silently. After
installation the browser terminates the existing background service
worker and starts a fresh instance running the new code. This restart
clears all in-memory state the old service worker held, including
active timers and cached data. Data persisted in
`chrome.storage.local` survives the restart intact, most importantly
the stored authentication token from the token relay flow. When the
new service worker initializes it reads the stored auth token from
`chrome.storage.local`. If the token is still valid the service worker
resumes normal operation by re-establishing the session refresh timer
and handling API requests as before. In rare cases a new extension
version introduces a breaking change to the token storage format or
authentication contract that makes previously stored tokens
incompatible. When the new service worker detects that the stored
token cannot be used it clears the invalid token from
`chrome.storage.local` and the popup reverts to the unauthenticated
sign-in prompt. After an update the extension can optionally display
a badge indicator on the popup icon and a localized "What's new"
section in the popup summarizing user-facing changes. Once the user
views the notice the badge is dismissed and the popup returns to its
normal layout.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Chrome Web Store and Firefox Add-ons (store platforms that host published extension versions and serve update packages to browsers when a new version is available for the DoCodeGo extension) | read | When the browser's update scheduler polls the store at its configured interval (every few hours) to compare the installed extension version against the latest published version | The store is unreachable due to network failure or server downtime and the browser retries the update check at its next scheduled interval — the user continues running the current extension version without interruption until the store becomes accessible again |
| Browser update scheduler (built-in browser mechanism that periodically checks for new versions of installed extensions, downloads update packages, and installs them silently in the background without user interaction) | read/write | Every few hours the scheduler compares the installed extension version against the latest version on the store, downloads the new package if a newer version exists, and triggers the silent installation process | The scheduler fails to run because the browser is closed or the update service is disabled in browser settings — the extension continues running the current version and the update check resumes when the browser restarts or the update service is re-enabled |
| Background service worker (extension-scoped process that is terminated when an update is applied and restarted with the new code, clearing all in-memory state including active timers and cached data while preserving data in `chrome.storage.local`) | read/write | Immediately after the browser applies the extension update the old service worker is terminated and a new service worker instance starts running the updated code, reading the stored auth token from `chrome.storage.local` to determine whether to resume authenticated operation | The new service worker fails to start due to a syntax error or missing module in the updated code — the extension icon remains in the toolbar but popup interactions that depend on the service worker return errors and the user falls back to using the web application directly until a corrected extension update is published |
| `chrome.storage.local` (browser extension storage API that persists key-value data across service worker restarts and extension updates, used to store the authentication token that survives the update process intact) | read/write | When the new service worker initializes after an update it reads the stored auth token from `chrome.storage.local` to determine whether to resume authenticated operation or prompt for re-authentication due to token incompatibility | The storage API call fails due to a browser storage corruption or quota exceeded error — the service worker logs the storage failure and the popup falls back to displaying the sign-in prompt because no valid token can be read from storage |
| Session refresh timer (interval-based timer that the new service worker re-establishes after reading a valid token from `chrome.storage.local` to keep the session alive by sending refresh requests to the DoCodeGo API before token expiry) | write | After the new service worker reads a valid token from `chrome.storage.local` and confirms the token is usable, the worker starts the refresh timer at the same interval used before the update to maintain session continuity | The timer fails to start because the service worker is immediately terminated by the browser after initialization — the token remains in `chrome.storage.local` and the timer is re-established on the next service worker restart triggered by a user interaction or browser event |
| Badge indicator and "What's new" notification (optional popup UI element that displays a badge on the extension icon and renders a localized summary of user-facing changes in the latest version when the release includes noteworthy updates) | write | After an update is applied the extension checks whether the new version includes a "What's new" payload, and if present sets a badge on the extension icon and prepares the notification content for display when the user opens the popup | The badge API call fails due to a browser limitation or the "What's new" payload is missing from the release — the extension continues operating without a badge and the popup renders its normal layout without the notification section |

## Behavioral Flow

1. **[Browser]** the update scheduler polls the Chrome Web Store or
    Firefox Add-ons at its configured interval (every few hours) to
    compare the installed DoCodeGo extension version against the latest
    published version on the store

2. **[Browser]** the store responds with version metadata indicating a
    newer version is available — the browser downloads the new extension
    package in the background without displaying any notification or
    prompt to the user

3. **[Browser]** the browser verifies the downloaded package signature
    against the store's signing certificate and silently installs the
    new extension version, replacing the previous version's code and
    assets on disk

4. **[Browser]** the browser terminates the existing background service
    worker that was running the old extension code — all in-memory state
    held by the old service worker is cleared, including active refresh
    timers, cached API responses, and any temporary variables

5. **[Browser]** the browser starts a new background service worker
    instance loaded with the updated extension code — the new service
    worker begins its initialization sequence and registers event
    listeners for message passing and API routing

6. **[ServiceWorker]** the new service worker reads the stored auth
    token from `chrome.storage.local` using the dedicated storage key
    to determine whether the user was authenticated before the update
    was applied

7. **[ServiceWorker]** the new service worker validates the stored
    token by checking that the token format matches the expected schema
    for the current extension version and optionally verifying the
    token against the DoCodeGo API with a lightweight validation
    request

8. **[ServiceWorker]** if the token is valid and compatible with the
    new version, the service worker re-establishes the session refresh
    timer at the configured interval to keep the session alive by
    sending refresh requests to the DoCodeGo API before token expiry

9. **[User]** opens the extension popup and sees their authenticated
    state exactly as they left it before the update — the popup reads
    the valid token from `chrome.storage.local` and renders the
    authenticated view with the user's context information

10. **[ServiceWorker]** if the stored token fails validation because
    the new version introduced a breaking change to the token storage
    format or because the first API call returns an authentication
    error, the service worker clears the invalid token from
    `chrome.storage.local`

11. **[User]** opens the extension popup after a breaking token
    migration and sees the unauthenticated sign-in prompt because the
    token was cleared from `chrome.storage.local` — the user
    re-authenticates through the token relay flow to continue using the
    extension

12. **[ServiceWorker]** after the update is applied the service worker
    checks whether the new version includes a "What's new" payload
    containing a localized summary of user-facing changes — if the
    payload is present the service worker sets a badge indicator on the
    extension icon using the `chrome.action.setBadgeText()` API

13. **[User]** opens the extension popup and sees the localized
    "What's new" section at the top of the popup summarizing the
    changes in the latest version — all text is rendered via @repo/i18n
    translation keys

14. **[User]** views the "What's new" notice and the service worker
    marks the notice as dismissed in `chrome.storage.local` — the badge
    indicator is removed from the extension icon and the popup returns
    to its normal layout on subsequent opens

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| running_current_version | update_installing | The browser's update scheduler detects a newer extension version on the Chrome Web Store or Firefox Add-ons and begins downloading the update package in the background | The store responds with a version string that is strictly newer than the installed version and the download completes with a valid package signature |
| update_installing | old_worker_terminated | The browser completes the silent installation of the new extension package and terminates the existing background service worker that was running the old code | The installation process writes the new code and assets to disk and the browser's service worker lifecycle manager sends the termination signal to the old worker |
| old_worker_terminated | new_worker_initializing | The browser starts a new background service worker instance loaded with the updated extension code and the new worker begins its initialization sequence | The new service worker script loads without syntax errors and the browser's service worker startup completes within the activation timeout |
| new_worker_initializing | authenticated_resumed | The new service worker reads the stored auth token from `chrome.storage.local`, validates the token format and API compatibility, and re-establishes the session refresh timer | The stored token is present, matches the expected schema for the new version, and the validation check confirms the token is usable |
| new_worker_initializing | token_cleared_unauthenticated | The new service worker reads the stored auth token from `chrome.storage.local` and determines the token is incompatible with the new version due to a format change or API authentication error | The token validation fails because the format does not match the new schema or the first API call returns HTTP 401 indicating the token is invalid for the updated contract |
| authenticated_resumed | badge_displayed | The service worker detects that the new version includes a "What's new" payload with user-facing changes and sets a badge indicator on the extension icon | The "What's new" payload is present in the updated extension bundle and has not been previously dismissed by the user |
| badge_displayed | authenticated_resumed | The user opens the popup, views the "What's new" notice, and the service worker marks the notice as dismissed in `chrome.storage.local` and removes the badge indicator | The user opens the popup while the badge is displayed and the dismiss action writes the seen flag to `chrome.storage.local` |

## Business Rules

- **Rule browser-handles-auto-update-silently:** IF a new extension
    version is published to the Chrome Web Store or Firefox Add-ons
    THEN the browser downloads and installs the update in the
    background without displaying a prompt or notification to the
    user — the count of user-visible update prompts during extension
    auto-update equals 0
- **Rule old-service-worker-terminated-on-update:** IF the browser
    completes the installation of a new extension version THEN the
    browser terminates the existing background service worker that was
    running the old code before starting the new worker — the count of
    simultaneously running service workers for the same extension after
    an update equals 0 because the old worker is terminated first
- **Rule in-memory-state-cleared-on-restart:** IF the browser
    terminates the old background service worker during an update THEN
    all in-memory state is cleared including active refresh timers,
    cached API responses, and temporary variables — the count of
    in-memory timers surviving a service worker termination equals 0
- **Rule chrome-storage-survives-restart:** IF the browser terminates
    and restarts the background service worker during an extension
    update THEN all data stored in `chrome.storage.local` persists
    intact across the restart — the auth token value in storage after
    the restart equals the auth token value stored before the restart
- **Rule valid-token-resumes-operation:** IF the new service worker
    reads a valid and compatible auth token from `chrome.storage.local`
    after an update THEN the service worker resumes authenticated
    operation without requiring user re-authentication — the count of
    sign-in prompts displayed to the user after a non-breaking update
    equals 0
- **Rule invalid-token-cleared-and-sign-in-shown:** IF the new
    service worker detects that the stored auth token is incompatible
    with the updated token schema or the first API call returns HTTP
    401 THEN the service worker clears the invalid token from
    `chrome.storage.local` and the popup displays the sign-in prompt
    — the count of invalid tokens remaining in storage after detection
    equals 0
- **Rule refresh-timer-re-established-after-restart:** IF the new
    service worker reads a valid token from `chrome.storage.local`
    after an update THEN the service worker starts the session refresh
    timer at the configured interval to keep the session alive — the
    count of active refresh timers after a successful token validation
    equals 1
- **Rule whats-new-badge-optional:** IF the new extension version
    includes a "What's new" payload with user-facing changes THEN the
    service worker sets a badge indicator on the extension icon and the
    popup renders a localized "What's new" section — the count of
    badge indicators displayed without a "What's new" payload equals 0
    and the badge is dismissed after the user views the notice

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (receives the extension update silently through the browser's auto-update mechanism and interacts with the popup to view authenticated state or the sign-in prompt after the update is applied) | Open the extension popup after an update to view authenticated state or the sign-in prompt, view the "What's new" notification and dismiss the badge indicator, re-authenticate through the token relay flow if the update introduced a breaking token migration | Cannot control when the browser checks for or applies extension updates, cannot prevent the termination of the old background service worker during the update process, cannot directly modify the token stored in `chrome.storage.local` or bypass the token validation logic in the new service worker | The user sees the authenticated popup view if the token remains valid after the update, sees the sign-in prompt if the token was cleared due to incompatibility, and sees the "What's new" badge and notification only when the release includes a "What's new" payload |
| Background service worker (new instance started by the browser after the update is applied, responsible for reading the stored token, validating compatibility, re-establishing the refresh timer, and managing the "What's new" badge lifecycle) | Read the stored auth token from `chrome.storage.local`, validate the token against the new version's expected schema, re-establish the session refresh timer for valid tokens, clear invalid tokens from storage, set and remove the badge indicator via `chrome.action.setBadgeText()`, write the "What's new" dismissed flag to `chrome.storage.local` | Cannot prevent the browser from terminating the old service worker instance, cannot retain in-memory state from the previous service worker instance across the update restart, cannot force the user to re-authenticate when the token is still valid | The service worker has visibility into the stored token value, the token validation result, the refresh timer state, and the "What's new" payload presence but has no visibility into the browser's update scheduler timing or the old service worker's final state before termination |
| Browser update scheduler (built-in browser mechanism that checks for new extension versions, downloads packages, and triggers the silent installation and service worker restart cycle) | Poll the Chrome Web Store or Firefox Add-ons for version updates, download new extension packages, verify package signatures, terminate the old service worker, install the new version on disk, start the new service worker instance | Cannot modify the contents of `chrome.storage.local`, cannot determine whether the stored auth token is compatible with the new extension version, cannot display update notifications or prompts to the user during the auto-update process | The update scheduler has visibility into the installed extension version and the latest store version but has no visibility into the extension's authentication state or the contents of `chrome.storage.local` |

## Constraints

- The new background service worker completes initialization and
    registers all event listeners within 1000 ms of the browser
    starting the worker after the update — the count of milliseconds
    from worker start to ready state equals 1000 or fewer.
- The `chrome.storage.local` read operation to retrieve the stored
    auth token completes within 100 ms of the new service worker
    reaching the ready state — the count of milliseconds from ready
    state to token read result equals 100 or fewer.
- The session refresh timer is re-established within 500 ms of the
    new service worker confirming a valid token — the count of
    milliseconds from token validation to refresh timer start equals
    500 or fewer.
- The token validation check against the expected schema completes
    within 200 ms of reading the token from `chrome.storage.local` —
    the count of milliseconds from token read to validation result
    equals 200 or fewer.
- The "What's new" badge indicator is set on the extension icon
    within 1000 ms of the new service worker detecting a "What's new"
    payload in the updated bundle — the count of milliseconds from
    payload detection to badge display equals 1000 or fewer.
- All user-facing text in the "What's new" notification section uses
    @repo/i18n translation keys with zero hardcoded English strings —
    the count of hardcoded user-facing strings in the "What's new"
    popup section equals 0.

## Acceptance Criteria

- [ ] The browser downloads and installs the extension update silently without displaying a prompt to the user — the count of user-visible update prompts during auto-update equals 0
- [ ] The browser terminates the old background service worker before starting the new worker after an update — the count of simultaneously running service workers for the extension equals 0 after termination
- [ ] All in-memory state in the old service worker is cleared on termination including active timers — the count of in-memory refresh timers surviving the service worker restart equals 0
- [ ] The auth token stored in `chrome.storage.local` persists intact across the service worker restart during an update — the token value after restart equals the token value before restart
- [ ] The new service worker reads the stored token and re-establishes the refresh timer within 500 ms of confirming a valid token — the count of active refresh timers after validation equals 1
- [ ] The popup displays the authenticated state when the user opens it after a non-breaking update with a valid stored token — the count of sign-in prompts displayed equals 0
- [ ] When the stored token is incompatible with the new version the service worker clears it from `chrome.storage.local` — the count of tokens in storage after clearing an invalid token equals 0
- [ ] The popup displays the sign-in prompt after a breaking token migration clears the stored token — the sign-in button is present within 1000 ms of popup open
- [ ] The user re-authenticates through the token relay flow after a breaking migration and the new token is stored — the stored token value after re-authentication is non-empty
- [ ] The "What's new" badge indicator is set on the extension icon when the release includes a "What's new" payload — the count of badge indicators displayed equals 1
- [ ] The "What's new" notification section renders localized text via @repo/i18n translation keys — the count of hardcoded English strings in the notification section equals 0
- [ ] The badge indicator is removed and the popup returns to normal layout after the user views the "What's new" notice — the count of badge indicators remaining after dismissal equals 0
- [ ] The new service worker completes initialization within 1000 ms of the browser starting the updated worker — the count of milliseconds from worker start to ready state equals 1000 or fewer

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The browser applies an update while the user has the extension popup open and is viewing authenticated content in the current version | The browser terminates the old service worker and the popup detects the disconnection, then the new service worker starts and the popup re-reads `chrome.storage.local` to restore the authenticated state without requiring the user to close and reopen the popup | The popup re-renders the authenticated view within 2000 ms of the update being applied and the count of sign-in prompts displayed equals 0 |
| The browser applies two consecutive updates in rapid succession before the user opens the popup between them | The browser processes each update sequentially, terminating and restarting the service worker for each version, and the final service worker instance runs the latest code with the token validation applied against the most recent schema | The count of active service workers after both updates complete equals 1 and the installed version matches the second update's version string |
| The new service worker starts but the `chrome.storage.local` read operation fails due to a transient browser storage error during the post-update initialization | The service worker catches the storage read error, logs the error with the storage operation details, and defaults to the unauthenticated state by not starting the refresh timer — the popup displays the sign-in prompt when opened | The error log contains the storage read failure entry and the popup shows the sign-in button because no valid token was read from storage |
| The stored token passes local schema validation in the new service worker but the first API call returns HTTP 401 because the server-side contract changed alongside the extension update | The service worker detects the HTTP 401 response, clears the now-invalid token from `chrome.storage.local`, cancels the refresh timer, and the popup reverts to the sign-in prompt on the next open | The count of tokens in `chrome.storage.local` after the HTTP 401 detection equals 0 and the popup displays the sign-in button |
| The extension update includes a "What's new" payload but the user never opens the popup to view the notification after the update is applied | The badge indicator remains visible on the extension icon indefinitely until the user opens the popup and views the notice, because the dismiss action requires the user to see the "What's new" section in the popup | The count of badge indicators on the extension icon equals 1 until the user opens the popup and the dismissed flag in `chrome.storage.local` is absent |
| The user is offline when the browser attempts to check for extension updates at the scheduled interval check time | The browser's update scheduler detects the network failure, logs the check failure, and retries at the next scheduled interval without displaying an error to the user — the extension continues running the current version | The count of error dialogs displayed to the user equals 0 and the extension version remains unchanged until the next successful update check |

## Failure Modes

- **New service worker fails to start after the update due to a code error in the updated bundle**
    - **What happens:** The browser terminates the old service worker and attempts to start the new service worker with the updated code, but the new script contains a syntax error, an unresolved module import, or throws an uncaught exception during initialization that prevents the worker from reaching the ready state.
    - **Source:** A build-time error in the WXT compilation pipeline produced a malformed service worker bundle for the new version, or a dependency import references a module that was tree-shaken out of the production build, or the updated code introduces a runtime error on the initialization path.
    - **Consequence:** The extension icon remains in the toolbar but all popup interactions that depend on the service worker for token management and API routing fail with errors — the user cannot access authenticated features or trigger API calls through the extension until a corrected update is published.
    - **Recovery:** The browser logs the service worker activation error in the extensions developer console and retries activation on the next user interaction — the developer alerts the team to fix the build pipeline and publishes a corrected extension update to the store.

- **Stored auth token becomes corrupted in `chrome.storage.local` during the update restart cycle**
    - **What happens:** The browser terminates the old service worker and starts the new one, but the `chrome.storage.local` data containing the auth token is partially corrupted due to a disk write error that occurred during the browser's internal storage synchronization at the moment of the service worker restart.
    - **Source:** A disk I/O error during the browser's internal IndexedDB or LevelDB synchronization that powers `chrome.storage.local`, a sudden power loss during the update process that interrupted a pending storage write, or browser profile corruption affecting the extension's storage partition.
    - **Consequence:** The new service worker reads a corrupted or malformed token from `chrome.storage.local` that fails schema validation, and the user loses their authenticated session despite not having a breaking token migration — the popup displays the sign-in prompt unexpectedly.
    - **Recovery:** The service worker detects the malformed token during validation, clears the corrupted value from `chrome.storage.local`, logs the corruption details including the token length and format mismatch, and the popup falls back to displaying the sign-in prompt so the user re-authenticates through the token relay flow.

- **Breaking token migration clears a valid token that the user relies on for uninterrupted access**
    - **What happens:** A new extension version introduces a change to the token storage format that makes the previously stored token incompatible, and the new service worker clears the token from `chrome.storage.local` during its initialization validation, even though the user's server-side session is still active and valid.
    - **Source:** A deliberate architectural change in the extension's token storage schema introduced in the new version, a change to the API authentication contract that requires a different token format, or a security fix that invalidates all tokens stored under the previous schema.
    - **Consequence:** The user's authenticated session in the extension is terminated and the popup displays the sign-in prompt, requiring the user to re-authenticate through the full token relay flow despite their server-side session remaining valid — the user perceives this as an unexpected sign-out.
    - **Recovery:** The popup degrades to the unauthenticated state and displays the sign-in prompt with a localized message explaining that re-authentication is required after the update — the user re-authenticates through the token relay flow and the new token is stored in the updated format in `chrome.storage.local`.

- **Badge indicator API call fails preventing the "What's new" notification from being displayed**
    - **What happens:** The new service worker detects a "What's new" payload in the updated bundle and calls `chrome.action.setBadgeText()` to set the badge indicator on the extension icon, but the API call fails because the browser restricts badge modifications during the service worker initialization phase or the badge API is temporarily unavailable.
    - **Source:** A browser-level restriction that prevents `chrome.action` API calls during the first few milliseconds of service worker initialization, a browser bug that intermittently rejects badge API calls after an extension update, or a permission issue with the `chrome.action` namespace in the updated manifest.
    - **Consequence:** The "What's new" notification is prepared in the extension's storage but the badge indicator is not visible on the extension icon, so the user has no visual signal that new information is available — the notification content is still accessible when the user opens the popup on their own initiative.
    - **Recovery:** The service worker catches the badge API error, logs the failure with the error code and the attempted badge text value, and retries setting the badge on the next service worker activation event — the "What's new" content remains available in the popup regardless of the badge display state.

## Declared Omissions

- This specification does not define the Chrome Web Store or Firefox Add-ons publishing pipeline, review process, or version numbering strategy used to release new extension versions to the stores
- This specification does not cover the extension's content script behavior or how content scripts are affected by extension updates — content script lifecycle during updates requires a separate specification with its own restart and injection analysis
- This specification does not address rollback behavior when a new extension version causes critical failures — automatic version rollback mechanisms are not supported by browser extension platforms and require publishing a corrected update as the recovery path
- This specification does not define the "What's new" payload authoring format, content guidelines, or the release workflow that determines which versions include user-facing change summaries in the notification
- This specification does not cover the token relay authentication flow that the user follows to re-authenticate after a breaking token migration — that mechanism is defined in the extension-authenticates-via-token-relay specification

## Related Specifications

- [extension-authenticates-via-token-relay](extension-authenticates-via-token-relay.md)
    — defines the token relay authentication flow that the user
    follows to re-authenticate after a breaking token migration
    clears the stored token from `chrome.storage.local` during an
    extension update
- [user-installs-browser-extension](user-installs-browser-extension.md)
    — defines the initial extension installation flow including the
    background service worker startup and permission grants that
    establish the baseline state from which subsequent updates modify
    the running extension code
- [session-lifecycle](session-lifecycle.md) — defines the session
    creation, refresh, and revocation behavior on the server side that
    determines whether the stored token remains valid after the
    extension update restarts the service worker and re-establishes
    the refresh timer
- [user-changes-language](user-changes-language.md) — defines the
    language switching mechanism that determines which @repo/i18n
    locale the "What's new" notification section uses to render the
    localized summary of user-facing changes after an extension update

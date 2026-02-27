---
id: SPEC-2026-070
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# Desktop Auto-Updates

## Intent

This spec defines how the Tauri 2 desktop application checks for new
versions, prompts the user to install an available update, and applies
the update when the user accepts. The Tauri Updater plugin is
configured with a release server URL specified in the
`tauri.conf.json` configuration file. When the user launches the
desktop application, the updater plugin automatically compares the
currently installed version string against the latest version
available on the release server. This version check also runs at a
configurable interval while the application is running, not only at
launch. If the release server reports a newer version, the
application presents a localized in-app update prompt — translated
through the @repo/i18n infrastructure — informing the user that a new
version is available and asking whether to update now or dismiss. When
the user accepts, the application downloads the update payload from
the release server, verifies its integrity, installs the new version,
and restarts the application so the user is running the latest
release. When the user dismisses the prompt, no download or
installation occurs and the user continues using the current version
without interruption until the next scheduled check or the next
application launch triggers a new version comparison.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Tauri Updater plugin (built-in Tauri plugin that polls the release server, compares versions, downloads update payloads, and triggers installation) | read/write | On application launch and at every configured check interval (default 3600 seconds) while the application is running, the plugin sends a request to the release server to compare versions | The plugin fails to initialize due to a missing or invalid configuration entry in `tauri.conf.json` and the application logs the initialization error — the application continues running without update capability and the user falls back to downloading the latest version manually from the project releases page |
| Release server URL in `tauri.conf.json` (remote HTTP endpoint that hosts version metadata and downloadable update payloads for each platform) | read | When the Tauri Updater plugin sends an HTTP GET request to the configured release server URL to retrieve the latest version metadata including the version string, download URL, and signature | The release server is unreachable due to network failure or server downtime and the updater plugin receives a connection timeout or HTTP 5xx error — the plugin logs the connection failure and retries at the next scheduled check interval without displaying an error to the user |
| Version comparison logic (compares the installed application version string against the version string returned by the release server using semantic versioning) | read | When the updater plugin receives the version metadata response from the release server and parses the latest version string to compare against the currently installed version | The version metadata response contains a malformed version string that cannot be parsed and the comparison logic returns an error — the updater plugin logs the parse failure with the raw response content and falls back to treating the check as no-update-available until the next scheduled interval |
| Update prompt UI (in-app notification component rendered in the webview that displays the available version and presents Accept and Dismiss actions to the user) | write | When the version comparison determines that the release server version is newer than the installed version, the updater triggers the in-app prompt to appear in the webview | The prompt component fails to render due to a webview rendering error and the user is not informed about the available update — the application logs the render failure and retries displaying the prompt on the next version check that detects the same newer version |
| Download and install pipeline (downloads the update payload from the release server URL, verifies the payload signature, writes the update to disk, and triggers the installation process) | write | When the user clicks Accept on the update prompt, the updater plugin begins downloading the update payload and then installs it after signature verification completes | The download fails due to a network interruption or the signature verification rejects the payload as tampered — the updater plugin logs the failure reason, notifies the user via a toast that the update could not be applied, and retries the download on the next user-initiated or scheduled check |
| Application restart (terminates the current application process and launches the newly installed version to complete the update cycle) | write | After the update payload is installed on disk, the updater plugin triggers an application restart to load the new version into the running process | The restart fails because the OS denies process termination or the new binary is corrupted — the application logs the restart failure and notifies the user to manually close and reopen the application to complete the update |
| @repo/i18n (localization infrastructure that provides translated strings for the update prompt text, button labels, and status messages displayed in the webview) | read | When the update prompt component renders in the webview, all user-facing text including the version number label, Accept button text, Dismiss button text, and progress messages are resolved from @repo/i18n translation keys | The i18n namespace fails to load and the prompt degrades to displaying raw translation keys instead of localized strings — the application logs the missing namespace and the prompt remains functional with raw keys visible until the translations load on retry |

## Behavioral Flow

1. **[Tauri]** the Tauri Updater plugin initializes during application
    startup and reads the release server URL from the `endpoints`
    field in the `tauri.conf.json` updater configuration section

2. **[Tauri]** the updater plugin sends an HTTP GET request to the
    release server URL to retrieve the latest version metadata
    including the version string, platform-specific download URL, and
    cryptographic signature for payload verification

3. **[Server]** the release server receives the version check request
    and responds with a JSON payload containing the latest version
    string, the download URL for the platform-matched update binary,
    and the Ed25519 signature of the update payload

4. **[Tauri]** the updater plugin parses the server response and
    compares the latest version string against the currently installed
    application version using semantic versioning comparison — if the
    server version is not newer, the check completes silently with no
    user-visible action

5. **[Tauri]** if the server version is newer than the installed
    version, the updater plugin triggers the in-app update prompt
    component to render in the webview, displaying the available
    version number and two action buttons: Accept and Dismiss

6. **[User]** reads the localized update prompt that informs them a
    new version is available and decides whether to accept the update
    now or dismiss the prompt to continue using the current version

7. **[User]** clicks the Dismiss button on the update prompt — the
    prompt closes immediately, no download or installation begins, and
    the user continues using the current application version without
    any interruption or degradation of functionality

8. **[Tauri]** after the user dismisses the prompt, the updater plugin
    schedules the next version check at the configured interval
    (default 3600 seconds) — when that interval elapses or the user
    relaunches the application, the updater repeats the version check
    from step 2

9. **[User]** clicks the Accept button on the update prompt to begin
    the update process — the prompt transitions to a download progress
    state showing the percentage of the update payload downloaded

10. **[Tauri]** the updater plugin downloads the update payload from
    the release server URL and verifies the Ed25519 signature against
    the public key configured in `tauri.conf.json` to confirm the
    payload has not been tampered with

11. **[Tauri]** after successful signature verification, the updater
    plugin writes the update payload to disk and triggers the
    platform-specific installation process to replace the current
    application binary with the new version

12. **[Tauri]** the updater plugin triggers an automatic application
    restart — the current process terminates and the newly installed
    version launches, loading the user into the updated application
    with all session state preserved via cookies in the webview
    cookie store

13. **[User]** the application is now running the latest version — the
    user can verify the version number in the application settings
    page and all functionality from the previous version remains
    available in the updated release

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | checking | The updater plugin initiates a version check on application launch or when the configured check interval (default 3600 seconds) elapses while the application is running | The release server URL is configured in `tauri.conf.json` and the updater plugin is initialized without errors |
| checking | idle | The release server responds with a version string that is equal to or older than the currently installed version, indicating no update is available | The version comparison completes without errors and the installed version is equal to or newer than the server version |
| checking | prompt_displayed | The release server responds with a version string that is newer than the currently installed version, triggering the in-app update prompt to render | The version comparison determines the server version is strictly newer using semantic versioning rules |
| checking | idle | The HTTP request to the release server fails due to a network timeout, DNS resolution failure, or HTTP 5xx server error | The updater plugin catches the request error, logs the failure, and schedules the next check at the configured interval |
| prompt_displayed | downloading | The user clicks the Accept button on the in-app update prompt to begin downloading the new version from the release server | The download URL from the server response is valid and the network connection is available |
| prompt_displayed | idle | The user clicks the Dismiss button on the in-app update prompt, closing the prompt and deferring the update to the next check cycle | The user has not clicked Accept and explicitly selects the Dismiss action |
| downloading | installing | The update payload download completes and the Ed25519 signature verification confirms the payload integrity against the configured public key | The downloaded payload size matches the expected size and the signature verification returns a valid result |
| downloading | prompt_displayed | The download fails due to a network interruption or the signature verification rejects the payload as invalid or tampered | The updater plugin detects the download error or signature mismatch, logs the failure details, and notifies the user via the prompt UI |
| installing | restarting | The platform-specific installation process completes and the new application binary is written to disk replacing the previous version | The installation process exits with a success code and the new binary is present at the expected filesystem path |
| restarting | idle | The application process terminates and the newly installed version launches, returning the updater plugin to the idle state ready for the next check cycle | The new application process starts and the updater plugin initializes with the updated version string |

## Business Rules

- **Rule check-on-launch:** IF the user launches the desktop
    application and the Tauri Updater plugin is configured with a
    release server URL in `tauri.conf.json` THEN the plugin sends an
    HTTP GET request to the release server to compare the installed
    version against the latest available version — the count of
    version check requests sent on each application launch equals 1
- **Rule check-on-interval:** IF the application is running and the
    configured check interval (default 3600 seconds) elapses since
    the last version check THEN the updater plugin sends a new HTTP
    GET request to the release server — the count of seconds between
    consecutive automatic checks equals 3600 or the configured
    interval value
- **Rule prompt-on-new-version:** IF the release server responds with
    a version string that is strictly newer than the installed version
    THEN the updater plugin renders an in-app update prompt in the
    webview displaying the new version number with Accept and Dismiss
    buttons — the count of update prompts displayed per detected new
    version equals 1
- **Rule accept-downloads-and-installs:** IF the user clicks Accept
    on the update prompt THEN the updater plugin downloads the update
    payload, verifies the Ed25519 signature, installs the new binary,
    and restarts the application — the count of update payloads
    applied after a user Accept action equals 1
- **Rule dismiss-defers-to-next-check:** IF the user clicks Dismiss
    on the update prompt THEN no download or installation occurs and
    the updater plugin waits for the next scheduled check interval or
    application relaunch to perform a new version comparison — the
    count of downloads initiated after a Dismiss action equals 0
- **Rule no-forced-update:** IF the release server reports a newer
    version THEN the application never forces the update without user
    consent — the count of updates applied without the user clicking
    Accept equals 0 and the Dismiss option is always available on
    every update prompt

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (interacts with the in-app update prompt rendered in the webview and decides whether to accept or dismiss the available update) | View the update prompt displaying the available version number, click Accept to begin the download and installation process, click Dismiss to defer the update to the next check cycle, verify the installed version number in the application settings page after an update completes | Cannot modify the release server URL or the check interval configured in `tauri.conf.json`, cannot bypass the Ed25519 signature verification on downloaded update payloads, cannot trigger a manual version check outside the configured schedule | The update prompt is visible in the webview when a newer version is detected, the download progress percentage is visible after clicking Accept, and the current version number is visible in the application settings page |
| Tauri Updater plugin (system component that polls the release server, compares versions, downloads payloads, verifies signatures, and triggers installation and restart) | Send HTTP GET requests to the release server URL, download update payloads to disk, verify Ed25519 signatures against the configured public key, trigger the platform-specific installation process, initiate an application restart after installation | Cannot display the update prompt without the webview rendering the prompt component, cannot force the user to accept an update, cannot skip the Ed25519 signature verification step before installation | The plugin has visibility into the release server response including version metadata and download URLs, the signature verification result, and the installation process exit code |
| Release server (remote HTTP endpoint that hosts version metadata and downloadable update payloads for each target platform) | Respond to HTTP GET version check requests with the latest version string and platform-specific download URL, serve the update payload binary and its Ed25519 signature when requested by the updater plugin | Cannot initiate a push notification to the desktop application, cannot force the application to download or install an update, cannot access the user's session cookies or any application data stored in the webview | The release server has visibility into the requesting application's current version (sent as a request parameter) and the platform identifier but has no visibility into user identity or application state |

## Constraints

- The Tauri Updater plugin completes the version check HTTP request
    and comparison within 5000 ms of initiating the check — the count
    of milliseconds from request start to comparison result equals
    5000 or fewer.
- The update payload download begins within 1000 ms of the user
    clicking Accept on the update prompt — the count of milliseconds
    from Accept click to first download byte received equals 1000 or
    fewer.
- The Ed25519 signature verification completes within 2000 ms of the
    download finishing — the count of milliseconds from download
    complete to verification result equals 2000 or fewer.
- All user-facing text in the update prompt uses @repo/i18n
    translation keys with zero hardcoded English strings — the count
    of hardcoded user-facing strings in the update prompt component
    equals 0.
- The update payload download displays a progress indicator showing
    the percentage completed — the count of progress updates rendered
    during a download equals 1 or more per 10 percent of payload
    downloaded.
- The application restart after installation completes within 5000 ms
    of the installation finishing — the count of milliseconds from
    installation complete to new version process start equals 5000 or
    fewer.

## Acceptance Criteria

- [ ] On application launch the Tauri Updater plugin sends exactly 1 HTTP GET request to the release server URL — the count of version check requests per launch equals 1
- [ ] When the release server returns a version newer than the installed version the update prompt renders in the webview — the count of update prompts displayed equals 1
- [ ] When the release server returns the same version as the installed version no prompt is displayed — the count of update prompts displayed equals 0
- [ ] The update prompt displays the available version number in localized text resolved from @repo/i18n translation keys — the count of hardcoded English strings in the prompt equals 0
- [ ] Clicking Accept on the update prompt starts the update payload download — the count of download requests initiated per Accept click equals 1
- [ ] The download progress indicator updates at least once per 10 percent of payload downloaded — the count of progress updates per download equals 10 or more for a full download
- [ ] The Ed25519 signature verification rejects a payload with an invalid signature — the count of installations proceeding after a failed signature check equals 0
- [ ] After successful installation the application restarts and runs the new version — the installed version string after restart equals the version string reported by the release server
- [ ] Clicking Dismiss on the update prompt closes the prompt with no download initiated — the count of download requests after a Dismiss click equals 0
- [ ] After dismissing the prompt the updater re-checks at the configured interval (default 3600 seconds) — the count of seconds between the dismiss action and the next automatic check equals 3600 or the configured value
- [ ] The version check interval timer runs while the application is open and triggers automatic re-checks — the count of automatic version checks per 7200-second window with default interval equals 2
- [ ] No update is ever applied without the user clicking Accept — the count of update installations triggered without a preceding Accept click equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The release server is unreachable because the user has no network connectivity at launch | The updater plugin catches the connection timeout error, logs the failure with the release server URL, and completes the check silently without displaying an error to the user — the next check occurs at the configured interval | The count of error dialogs displayed to the user equals 0 and the logged error entry contains the release server URL and the timeout duration |
| The release server responds with a version string that is older than the currently installed version (user has a pre-release build) | The updater plugin compares versions using semantic versioning and determines the server version is not newer — no update prompt is displayed and the check completes silently | The count of update prompts displayed equals 0 and the version comparison log entry indicates the installed version is newer |
| The user clicks Accept but the network connection drops during the payload download before completion | The updater plugin detects the download interruption, logs the failure with the number of bytes downloaded, and notifies the user via a toast that the download failed — the prompt returns to its initial state allowing the user to retry | The toast notification is visible in the webview, the count of partially downloaded files left on disk equals 0, and the prompt displays the Accept and Dismiss buttons again |
| The downloaded update payload has an invalid Ed25519 signature because the payload was corrupted during transfer | The updater plugin rejects the payload after signature verification fails, logs the signature mismatch details including the expected and received signature hashes, and notifies the user that the update could not be verified | The count of installations proceeding after signature rejection equals 0 and the user notification contains a message about verification failure |
| The user dismisses the update prompt and then closes and relaunches the application before the next scheduled interval check | The updater plugin performs a new version check on the relaunch (per the check-on-launch rule) and detects the same newer version again, displaying the update prompt a second time | The count of version check requests on the relaunch equals 1 and the update prompt is displayed again with the same newer version number |
| Two version checks overlap because the user relaunches the application exactly when a scheduled interval check is due | The updater plugin serializes version checks so only one HTTP request to the release server is in-flight at any time — the second check waits for the first to complete before initiating | The count of concurrent HTTP requests to the release server equals 1 at any point during the overlap scenario |

## Failure Modes

- **Release server unreachable during version check due to network or server failure**
    - **What happens:** The Tauri Updater plugin sends an HTTP GET
        request to the release server URL but receives a connection
        timeout, DNS resolution failure, or HTTP 5xx server error
        response instead of the expected version metadata payload.
    - **Source:** The user's device has no active network connection,
        the release server is experiencing downtime or maintenance, or
        a firewall rule blocks outbound HTTP requests to the release
        server domain from the desktop application process.
    - **Consequence:** The updater plugin cannot determine whether a
        newer version is available and no update prompt is displayed
        to the user — the user continues running the current version
        without awareness of any available update until the next
        successful check.
    - **Recovery:** The updater plugin logs the connection failure
        with the release server URL, HTTP status code (if received),
        and error message, then retries the version check at the next
        configured interval (default 3600 seconds) without displaying
        an error dialog to the user.

- **Update payload download interrupted or corrupted during transfer from the release server**
    - **What happens:** The user clicks Accept and the updater plugin
        begins downloading the update payload, but the download fails
        midway due to a network disconnection, or the completed
        download produces a file that does not match the expected size
        or checksum reported by the release server.
    - **Source:** The user's network connection drops during the
        download, a proxy server terminates the connection due to a
        timeout, or a man-in-the-middle modifies the payload bytes
        during transfer from the release server to the client.
    - **Consequence:** The update payload on disk is incomplete or
        corrupted and cannot be installed — the Ed25519 signature
        verification rejects the payload, preventing the installation
        of a tampered or partial binary that could crash the
        application.
    - **Recovery:** The updater plugin deletes the corrupted partial
        download from disk, logs the failure with the download URL
        and the number of bytes received, and notifies the user via a
        toast message that the download failed — the prompt returns
        to its initial state so the user retries on the next attempt.

- **Application restart fails after the update payload is installed on disk**
    - **What happens:** The updater plugin completes the download,
        verifies the signature, and installs the new binary to disk,
        but the automatic restart fails because the OS denies process
        termination, the new binary has incorrect filesystem
        permissions, or the new binary is corrupted despite passing
        signature verification.
    - **Source:** A system security policy prevents the application
        from terminating its own process, the filesystem write
        operation set incorrect executable permissions on the new
        binary, or a disk write error silently corrupted the binary
        after the signature check completed.
    - **Consequence:** The user remains running the old version
        despite the new version being present on disk — the update is
        installed but not active, and the user does not benefit from
        the new release until the restart completes.
    - **Recovery:** The updater plugin detects the restart failure,
        logs the error with the OS error code and the new binary file
        path, and notifies the user via an in-app message to manually
        close and reopen the application to complete the update
        process.

- **Version metadata response contains a malformed or unparseable version string from the release server**
    - **What happens:** The release server responds to the version
        check request with a JSON payload where the version string
        field is empty, contains non-numeric characters that violate
        semantic versioning format, or is missing entirely from the
        response body.
    - **Source:** A deployment error on the release server published
        incomplete version metadata, the server response was truncated
        by a network proxy, or a configuration change on the server
        introduced an incompatible version string format.
    - **Consequence:** The updater plugin cannot compare the installed
        version against the server version and cannot determine
        whether an update is available — no prompt is displayed and
        the user continues running the current version without
        awareness of any potential update.
    - **Recovery:** The updater plugin catches the version parse
        error, logs the raw server response content and the parse
        failure details, and falls back to treating the check result
        as no-update-available — the plugin retries the version check
        at the next scheduled interval expecting the server to return
        a corrected response.

## Declared Omissions

- This specification does not define the release server infrastructure
    including the server framework, hosting provider, or deployment
    pipeline used to publish version metadata and update payloads — the
    release server configuration is an operational concern outside the
    desktop application codebase.
- This specification does not cover delta or differential updates that
    download only the changed bytes between the installed and latest
    versions — all updates download the complete platform-specific
    binary payload regardless of the size difference between versions.
- This specification does not address rollback behavior when the newly
    installed version crashes on first launch after an update — crash
    recovery and version rollback mechanisms require a separate
    specification with their own failure mode analysis.
- This specification does not define the release signing key management
    workflow including key generation, rotation, or revocation — the
    Ed25519 key pair lifecycle is an operational security concern managed
    outside the application update flow.
- This specification does not cover update behavior when the application
    is running in a sandboxed environment that restricts filesystem write
    access — platform-specific sandboxing constraints for macOS App Store
    or Linux Snap/Flatpak distributions require separate specifications.

## Related Specifications

- [user-launches-desktop-app](user-launches-desktop-app.md) — defines
    the Tauri desktop application startup sequence during which the
    updater plugin initializes and performs the first version check
    against the release server immediately after the webview loads
- [user-uses-system-tray](user-uses-system-tray.md) — defines the
    system tray icon behavior that remains functional during the update
    download and installation process, allowing the user to show or
    hide the application window while an update is in progress
- [desktop-opens-external-link](desktop-opens-external-link.md) —
    defines how the Tauri webview handles external links including any
    links in the update prompt that point to release notes or changelog
    pages hosted outside the application origin
- [session-lifecycle](session-lifecycle.md) — defines the session
    cookie persistence behavior that ensures the user remains
    authenticated after the application restarts following a completed
    update installation

---
id: SPEC-2026-072
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Views Desktop App Version

## Intent

This spec defines how a user views the current desktop application
version and manually checks for updates from within the settings area
of the Tauri 2 desktop application. The user navigates to the settings
page where a localized "About" section appears at the bottom, but only
when the application detects it is running inside Tauri by checking for
the presence of `window.__TAURI__` on the global scope. This section
does not render in the regular web application served through a
browser. On render, the about section invokes the `get_app_version` IPC
command to retrieve the current binary version string from the Tauri
configuration file `tauri.conf.json`. The version displayed reflects
the installed Tauri binary version, not the web application bundle
version, so the user can confirm whether an auto-update applied
correctly. A localized "Check for updates" link next to the version
display allows the user to manually trigger the Tauri Updater plugin
check. If an update is available the update prompt flow activates. If
the application is already on the latest version a localized
confirmation message displays indicating no update is available. All
text in this section is localized through the @repo/i18n
infrastructure.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `get_app_version` IPC command (Tauri command registered in the Rust backend that reads the version string from the compiled binary metadata) | read | When the about section component mounts inside the settings page and calls the Tauri invoke API to retrieve the current application version string | The IPC call returns an error and the about section displays a localized fallback message indicating the version is unavailable — the component logs the IPC failure with the error code and command name |
| `tauri.conf.json` version source (Tauri configuration file that defines the application version string compiled into the binary at build time) | read (at build) | At build time when the Tauri compiler reads the version field from `tauri.conf.json` and embeds it into the binary metadata accessible via the `get_app_version` IPC command | The build process fails if the version field is missing or malformed in `tauri.conf.json` — the developer falls back to fixing the configuration file before the binary can be compiled and distributed |
| `window.__TAURI__` detection (global JavaScript object injected by the Tauri runtime into the webview context to signal that the app is running inside Tauri) | read | When the settings page renders and the about section component checks `typeof window.__TAURI__ !== "undefined"` to determine whether to display the version information section | The `window.__TAURI__` object is absent because the application is running in a standard browser — the about section does not render and the user sees no version information, which is the intended behavior for the web application |
| Tauri Updater plugin manual check (Tauri plugin that queries the configured update endpoint to determine whether a newer application version is available for download) | invoke | When the user clicks the "Check for updates" link and the component calls the Tauri Updater plugin API to query the remote update endpoint for a newer version | The updater plugin returns a network error and the about section displays a localized error message indicating the update check failed — the component logs the network error details and the user retries by clicking the link again |
| @repo/i18n (localization infrastructure that provides translated strings for the about section labels, version display format, and update status messages) | read | When the about section component renders and loads translation keys for the "About" heading, version label, "Check for updates" link text, and status messages in the user's configured locale | The i18n namespace fails to load and the about section degrades to displaying raw translation keys instead of localized strings — the component logs the missing namespace and retries loading translations on the next render cycle |

## Behavioral Flow

1. **[User]** opens the settings area within the desktop application
    by clicking the settings navigation item in the dashboard sidebar
    or accessing the settings route directly through keyboard
    navigation or a deep link

2. **[Webview]** renders the settings page and evaluates
    `typeof window.__TAURI__ !== "undefined"` to determine whether the
    application is running inside the Tauri desktop shell or in a
    standard web browser environment

3. **[Webview]** if `window.__TAURI__` is defined (the application is
    running inside Tauri), the about section component mounts at the
    bottom of the settings page — if `window.__TAURI__` is undefined
    (the application is running in a browser), the about section does
    not render and the flow ends for this feature

4. **[Webview]** on mount, the about section component calls the
    `get_app_version` IPC command via `invoke("get_app_version")` to
    request the current application version string from the Tauri
    backend

5. **[Tauri]** receives the `get_app_version` IPC invocation, reads
    the version string that was compiled into the binary from the
    `tauri.conf.json` version field at build time, and returns it to
    the webview as a string value

6. **[Webview]** receives the version string and renders it alongside
    the application name in a localized format — for example,
    "DoCodeGo Desktop v1.2.0" — where the version reflects the
    installed binary version, not the web application bundle version,
    so the user can verify that a previously triggered auto-update
    applied correctly

7. **[Webview]** renders a localized "Check for updates" link next to
    the version display using a translation key from the @repo/i18n
    infrastructure, providing the user with a manual mechanism to
    trigger an update check without waiting for the automatic schedule

8. **[User]** clicks the "Check for updates" link to manually trigger
    a query to the remote update endpoint through the Tauri Updater
    plugin

9. **[Tauri]** Updater plugin sends a request to the configured update
    endpoint URL and compares the remote version against the currently
    installed binary version to determine whether an update is
    available

10. **[Webview]** if the Updater plugin reports that an update is
    available, the application activates the update prompt flow as
    defined in the auto-update specification — the user sees the
    update dialog with download and install options

11. **[Webview]** if the Updater plugin reports that the application
    is already running the latest version, the about section displays
    a localized confirmation message such as "You are on the latest
    version" that remains visible for at least 5000 milliseconds
    before automatically dismissing

12. **[User]** reads the version information and update status,
    confirming the currently installed binary version and whether any
    update is pending or the application is up to date

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| settings_page_loading | about_section_hidden | Settings page renders and evaluates `window.__TAURI__` detection check on the global scope | The `window.__TAURI__` object is undefined because the application is running in a standard web browser and not inside the Tauri desktop shell |
| settings_page_loading | about_section_mounting | Settings page renders and evaluates `window.__TAURI__` detection check on the global scope | The `window.__TAURI__` object is defined because the application is running inside the Tauri 2 desktop shell with IPC available |
| about_section_mounting | version_loading | About section component mounts and invokes the `get_app_version` IPC command to retrieve the binary version string from the Tauri backend | The Tauri IPC channel is initialized and the `get_app_version` command is registered in the Rust backend command list |
| version_loading | version_displayed | The `get_app_version` IPC command returns a version string and the component renders it alongside the application name in the localized format | The IPC response contains a non-empty string that matches the semantic version format (major.minor.patch) |
| version_loading | version_fetch_failed | The `get_app_version` IPC command returns an error or the invocation times out after the configured IPC timeout threshold | The IPC response is an error object or no response arrives within 5000 milliseconds of the invocation |
| version_displayed | update_checking | User clicks the "Check for updates" link and the component invokes the Tauri Updater plugin to query the remote update endpoint | The Updater plugin is registered and the configured update endpoint URL is reachable over the network |
| update_checking | update_available | Tauri Updater plugin responds that a newer version exists on the remote update endpoint compared to the currently installed binary | The remote version number is strictly greater than the installed binary version number |
| update_checking | already_up_to_date | Tauri Updater plugin responds that no newer version exists on the remote update endpoint compared to the currently installed binary | The remote version number is equal to or less than the installed binary version number |
| update_checking | update_check_failed | Tauri Updater plugin returns a network error or the remote endpoint does not respond within the configured timeout threshold | The network request fails with a connection error, DNS resolution failure, or HTTP status code outside the 200 range |
| already_up_to_date | version_displayed | The localized "up to date" confirmation message automatically dismisses after being visible for at least 5000 milliseconds | The 5000 millisecond display timer for the confirmation message has elapsed completely |
| update_available | version_displayed | User completes or dismisses the update prompt flow and returns to the settings page where the about section re-renders with the current version | The update prompt dialog is closed either by completing the update or by the user dismissing it |

## Business Rules

- **Rule about-section-hidden-in-browser:** IF the `window.__TAURI__`
    object is undefined on the global scope THEN the about section
    component does not render on the settings page — the count of
    about section DOM elements present on the settings page in a
    standard browser equals 0
- **Rule version-from-binary-not-web-bundle:** IF the
    `get_app_version` IPC command returns a version string THEN the
    displayed version reflects the Tauri binary version compiled from
    `tauri.conf.json`, not the web application bundle version — the
    displayed version string equals the value in the binary metadata
- **Rule manual-check-triggers-updater:** IF the user clicks the
    "Check for updates" link THEN the Tauri Updater plugin queries the
    configured remote update endpoint exactly 1 time per click — the
    count of update endpoint requests per click equals 1
- **Rule update-available-shows-prompt:** IF the Tauri Updater plugin
    reports that a newer version is available on the remote endpoint
    THEN the application activates the update prompt dialog as defined
    in the auto-update specification — the count of update prompt
    dialogs displayed equals 1
- **Rule already-up-to-date-shows-message:** IF the Tauri Updater
    plugin reports that no newer version is available THEN the about
    section displays a localized confirmation message for at least
    5000 milliseconds — the confirmation message visible duration
    equals 5000 milliseconds or more

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated User (signed in and viewing the settings page inside the Tauri desktop application with a valid session) | View the about section with version information, click the "Check for updates" link to trigger a manual update check, read the version string and update status messages displayed in the about section | Cannot modify the displayed version string, cannot bypass the Tauri Updater plugin to install arbitrary binaries, cannot force the about section to render when `window.__TAURI__` is undefined | The about section is visible at the bottom of the settings page only when `window.__TAURI__` is defined — the version string, "Check for updates" link, and status messages are all visible within this section |
| Unauthenticated User (not signed in and redirected to the sign-in page by the route guard inside the Tauri desktop application) | Cannot access the settings page because the route guard redirects to the sign-in page before the settings route renders | Cannot view the about section, cannot see the version string, cannot trigger the "Check for updates" link because the settings page is not rendered | No settings page content is visible — the route guard prevents rendering of the settings page and its about section until the user authenticates |
| Browser User (accessing the web application through a standard browser where `window.__TAURI__` is not injected into the global scope) | View all other settings page content that is not gated behind the `window.__TAURI__` detection check | Cannot view the about section because the `window.__TAURI__` check evaluates to false, cannot trigger the `get_app_version` IPC command, cannot use the "Check for updates" link | The about section is completely hidden — the settings page renders without the about section component and no version information or update check functionality is visible |

## Constraints

- The `get_app_version` IPC command returns the version string within
    3000 milliseconds of invocation — the count of milliseconds from
    IPC invoke to version string received equals 3000 or fewer.
- The about section component renders the version string within
    500 milliseconds of receiving the IPC response — the count of
    milliseconds from IPC response to DOM update equals 500 or fewer.
- All user-facing text in the about section uses @repo/i18n
    translation keys with zero hardcoded English strings — the count
    of hardcoded user-facing strings in the about section equals 0.
- The "Check for updates" link triggers exactly 1 update endpoint
    request per user click with no duplicate requests — the count of
    endpoint requests per click event equals 1.
- The up-to-date confirmation message remains visible for at least
    5000 milliseconds before auto-dismissing — the count of
    milliseconds the message is displayed equals 5000 or more.
- The `window.__TAURI__` detection check completes within 10
    milliseconds of the settings page render start — the count of
    milliseconds from render start to detection result equals 10
    or fewer.

## Acceptance Criteria

- [ ] The about section renders on the settings page when `window.__TAURI__` is defined — the count of about section DOM elements equals 1
- [ ] The about section does not render on the settings page when `window.__TAURI__` is undefined — the count of about section DOM elements equals 0
- [ ] The `get_app_version` IPC command returns the binary version string within 3000 milliseconds — the IPC response time equals 3000 ms or fewer
- [ ] The displayed version string matches the version from `tauri.conf.json` compiled into the binary — the character difference between displayed and binary version equals 0
- [ ] The version label renders in the user's configured locale language via @repo/i18n — the count of hardcoded English strings in the about section equals 0
- [ ] Clicking "Check for updates" triggers exactly 1 request to the update endpoint — the count of endpoint requests per click equals 1
- [ ] When an update is available the update prompt dialog displays within 2000 milliseconds of the check completing — the dialog render time equals 2000 ms or fewer
- [ ] When no update is available a localized "up to date" message displays for at least 5000 milliseconds — the message visible duration equals 5000 ms or more
- [ ] When the `get_app_version` IPC call fails the about section displays a localized error fallback — the count of unhandled IPC errors equals 0
- [ ] When the update check network request fails the about section displays a localized error message — the count of unhandled network errors equals 0
- [ ] The "Check for updates" link is disabled during an active update check to prevent duplicate requests — the count of concurrent update requests equals 1
- [ ] The about section heading text matches the @repo/i18n translation key for the user's locale — the count of mismatched locale strings equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User opens settings in a browser where `window.__TAURI__` is undefined but a browser extension injects a `__TAURI__` mock onto the global scope | The about section attempts to render and calls `get_app_version` but the IPC invocation fails because no Tauri backend exists — the component catches the IPC error and displays the localized version-unavailable fallback message | The IPC call returns an error, the fallback message renders, and the count of successful version displays equals 0 |
| The `get_app_version` IPC command returns an empty string because the `tauri.conf.json` version field was left blank during the build | The about section receives an empty version string and displays the application name without a version number alongside a localized "version unknown" indicator | The displayed version area contains the application name and the version portion renders the "version unknown" localized string |
| User clicks "Check for updates" while the device has no network connectivity and the update endpoint is unreachable | The Tauri Updater plugin returns a network error and the about section displays a localized message indicating the update check failed due to a connectivity issue — the component logs the network error details | The error message renders within 5000 milliseconds of the click and the count of unhandled network exceptions equals 0 |
| User rapidly clicks the "Check for updates" link multiple times within 1000 milliseconds before the first check completes | The component disables the link after the first click and ignores subsequent clicks until the current update check completes — only 1 request reaches the update endpoint | The count of update endpoint requests equals 1 regardless of the number of clicks within the 1000 millisecond window |
| The Tauri Updater plugin returns an update-available response but the update prompt flow fails to activate due to a missing dialog component | The about section catches the dialog activation error, displays a localized error message indicating the update prompt could not be shown, and logs the component error with the dialog identifier | The error message renders and the count of logged dialog activation errors equals 1 |
| The user's locale is set to a language for which the @repo/i18n infrastructure has no translation file loaded for the about section namespace | The i18n infrastructure falls back to the default English locale strings for the about section labels, version format, and status messages — the component logs a warning with the missing locale identifier | The about section renders with English fallback strings and the count of raw translation key displays equals 0 |

## Failure Modes

- **IPC command `get_app_version` fails or times out on invocation**
    - **What happens:** The about section component invokes
        `get_app_version` through the Tauri IPC bridge but the command
        returns an error because the Rust backend handler is not
        registered, the IPC channel is not initialized, or the
        response does not arrive within 5000 milliseconds.
    - **Source:** The Tauri plugin configuration is missing the
        `get_app_version` command registration, the Rust backend
        panicked during command execution, or the IPC bridge
        encountered a serialization error when encoding the response.
    - **Consequence:** The about section cannot display the binary
        version string and the user sees no version information, which
        prevents them from confirming whether an auto-update applied
        correctly to the installed binary.
    - **Recovery:** The component catches the IPC error and falls back
        to displaying a localized "version unavailable" message in the
        about section — it logs the IPC error code and command name,
        and the user retries by navigating away from and back to the
        settings page to re-trigger the IPC invocation.

- **Tauri Updater plugin network request fails during manual check**
    - **What happens:** The user clicks "Check for updates" and the
        Tauri Updater plugin attempts to query the remote update
        endpoint, but the HTTP request fails due to DNS resolution
        failure, connection timeout, TLS certificate error, or the
        server returning an HTTP status code outside the 200 range.
    - **Source:** The user's device has no active network connection,
        the update endpoint server is temporarily unavailable due to
        maintenance, the corporate firewall blocks the update endpoint
        domain, or the TLS certificate for the endpoint has expired.
    - **Consequence:** The user cannot determine whether a newer
        version of the desktop application is available and the manual
        update check provides no actionable result, leaving the user
        unable to verify their application is current.
    - **Recovery:** The component catches the updater plugin error and
        displays a localized error message indicating the update check
        failed — it logs the HTTP status code or network error details,
        re-enables the "Check for updates" link, and the user retries
        the check by clicking the link again after network connectivity
        is restored.

- **Translation namespace for the about section fails to load from
    @repo/i18n**
    - **What happens:** The about section component requests the
        translation namespace for its labels, version format string,
        and status messages, but the @repo/i18n infrastructure returns
        an error because the namespace file is missing from the locale
        bundle, the JSON parse fails, or the network fetch for the
        namespace times out.
    - **Source:** The locale bundle was deployed without the about
        section namespace file, the JSON file contains a syntax error
        introduced during a translation update, or the namespace fetch
        request exceeded the configured 3000 millisecond timeout.
    - **Consequence:** The about section displays raw translation keys
        instead of localized strings, making the version information
        and update status messages unreadable to the user because the
        keys are developer-facing identifiers like
        "settings.about.version_label" rather than human-readable text.
    - **Recovery:** The i18n infrastructure falls back to the default
        English locale strings when the requested locale namespace is
        unavailable — it logs a warning with the missing namespace
        identifier and locale code, and retries loading the namespace
        on the next component render cycle triggered by navigation.

- **Update prompt dialog component fails to activate after updater
    reports an available version**
    - **What happens:** The Tauri Updater plugin reports that a newer
        version is available on the remote endpoint, but the webview
        fails to activate the update prompt dialog because the dialog
        component is not registered in the component tree, a React
        rendering error prevents the dialog from mounting, or the
        dialog state management throws an exception.
    - **Source:** A code-splitting chunk containing the update dialog
        component failed to load due to a corrupted bundle asset, the
        dialog component has a runtime dependency that is undefined in
        the current render context, or a state management error
        occurred when transitioning to the update-available state.
    - **Consequence:** The user clicked "Check for updates" and the
        check completed but no update dialog appears, leaving the user
        unaware that an update is available and unable to proceed with
        the download and installation through the normal update flow.
    - **Recovery:** The about section catches the dialog activation
        error and displays a localized fallback message notifying the
        user that an update is available but the prompt could not be
        shown — it logs the component error with the dialog identifier
        and suggests the user restart the application to trigger the
        automatic update check on next launch.

## Declared Omissions

- This specification does not define the auto-update download and
    installation flow that activates when the user confirms the update
    prompt — that behavior is covered by a separate auto-update
    behavioral specification addressing the Tauri Updater plugin
    lifecycle.
- This specification does not cover the build-time process that writes
    the version string into `tauri.conf.json` or the CI pipeline that
    increments the version number — build configuration and versioning
    strategy are defined in the desktop application build specification.
- This specification does not address the update endpoint server
    configuration, version manifest format, or binary artifact hosting
    — server-side update infrastructure is covered by a separate
    deployment specification for the Tauri update distribution system.
- This specification does not define the settings page layout, routing,
    or navigation structure beyond the about section — the full settings
    page composition is defined in the settings page behavioral
    specification covering all settings subsections and their ordering.
- This specification does not cover the visual theme applied to the
    about section (light mode, dark mode, or system preference) — theme
    switching and its effect on settings page components are defined in
    the user-changes-theme behavioral specification.

## Related Specifications

- [user-launches-desktop-app](user-launches-desktop-app.md) — Defines
    the desktop application startup sequence including Tauri runtime
    initialization, webview loading, and `window.__TAURI__` injection
    that this spec relies on for the about section visibility detection
- [user-changes-theme](user-changes-theme.md) — Defines the theme
    switching mechanism that affects the visual appearance of the about
    section and all other settings page components inside the Tauri
    webview
- [user-changes-language](user-changes-language.md) — Defines the
    locale switching flow that determines which @repo/i18n translation
    namespace is loaded for the about section labels, version format,
    and status messages displayed to the user
- [session-lifecycle](session-lifecycle.md) — Defines the
    authentication session lifecycle that determines whether the user
    can access the settings page where the about section with version
    information and update check functionality is rendered
- [user-navigates-the-dashboard](user-navigates-the-dashboard.md) —
    Defines the dashboard shell and navigation structure that the user
    interacts with to reach the settings page containing the about
    section with the desktop application version display

---
id: SPEC-2026-079
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Installs Browser Extension

## Intent

This spec defines how a user installs the DoCodeGo browser extension
from the Chrome Web Store or Firefox Add-ons, observes the extension
icon appear in the browser toolbar, and reaches the first-interaction
state where the popup displays a localized sign-in prompt. The WXT
framework handles Manifest V3 generation automatically so a single
codebase produces a valid extension for both Chrome and Firefox without
browser-specific configuration files or conditional build steps. On
installation the background service worker starts and becomes the
persistent backend responsible for managing authentication tokens,
routing API calls to the DoCodeGo API, and handling communication
between the popup and the web application. The extension requests three
permissions at install time: `storage` for persisting the auth token
in `chrome.storage.local`, `activeTab` for accessing information about
the currently open tab when the user clicks the extension icon, and
`host_permissions` scoped exclusively to the DoCodeGo API URL for
making authenticated requests. When the user clicks the extension icon
for the first time, the popup opens as a React application built with
components from `@repo/ui` and detects that no auth token is stored,
then displays a localized sign-in prompt translated through the
@repo/i18n infrastructure. The user cannot interact with any
authenticated features until they complete the token relay
authentication flow. The popup provides a clear call to action to sign
in and a brief explanation of what the extension does.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| WXT framework (build tool that generates Manifest V3 extension bundles from a single TypeScript codebase for both Chrome and Firefox) | build/generate | During the extension build process the WXT framework reads the project configuration and generates a valid Manifest V3 bundle including the manifest.json, background service worker entry, and popup HTML for the target browser | The build pipeline fails to produce a valid extension bundle and the extension cannot be packaged or submitted to the Chrome Web Store or Firefox Add-ons — the developer falls back to manually authoring the manifest.json and build configuration for each target browser |
| Background service worker (extension-scoped persistent backend that manages authentication tokens, routes API calls, and bridges communication between the popup and the web application) | process start | Immediately after the browser installs the extension and registers the Manifest V3 service worker entry point defined in the WXT-generated manifest.json file | The service worker fails to start due to a syntax error or missing entry point in the generated bundle — the extension icon appears in the toolbar but all popup interactions that depend on the service worker return errors and the user falls back to using the web application directly in a browser tab |
| `chrome.storage.local` (browser-provided key-value storage API used to persist the authentication token across popup opens, browser restarts, and extension updates) | read/write | When the background service worker writes a received auth token after the token relay flow completes, and when the popup reads the stored token on each open to determine the authentication state | The storage API call rejects with a quota or permission error and the auth token cannot be persisted — the extension logs the storage failure and the user falls back to re-authenticating on every popup open because the token is lost when the popup closes |
| `activeTab` permission (browser permission that grants the extension temporary access to the currently focused tab when the user clicks the extension icon) | read | When the user clicks the extension icon in the toolbar and the browser grants the extension access to the URL and title of the currently active tab for contextual features | The browser denies the `activeTab` permission grant because the user revoked it or the browser is in a restricted mode — the extension popup opens but any feature that depends on the current tab URL or title degrades gracefully by displaying a placeholder message instead of tab-specific content |
| `host_permissions` scoped to the DoCodeGo API URL (browser permission that authorizes the extension to make cross-origin HTTP requests to the DoCodeGo API endpoint for authenticated operations) | read/write | When the background service worker sends authenticated HTTP requests to the DoCodeGo API to fetch user data, verify tokens, or perform actions on behalf of the signed-in user | The browser blocks cross-origin requests to the DoCodeGo API because the host permission was not granted or was revoked by the user — the extension logs the permission denial and the popup displays an error state explaining that the extension cannot communicate with the DoCodeGo API |
| `@repo/ui` (shared Shadcn component library providing React UI components used by the popup to render buttons, forms, and layout elements consistent with the web dashboard design) | render | When the popup React application mounts and renders the sign-in prompt, action buttons, and layout components using the shared component library from the monorepo packages directory | The component library fails to load due to a bundle import error and the popup renders a blank or partially styled interface — the extension logs the component loading failure and the user falls back to using the web application directly in a browser tab |
| @repo/i18n (localization infrastructure that provides translated strings for all user-facing text in the popup including the sign-in prompt, button labels, and extension description) | read | When the popup React application initializes and resolves translation keys for all visible UI text including the sign-in call to action, the extension description text, and button labels | The i18n namespace fails to load and the popup degrades to displaying raw translation keys instead of localized strings — the extension logs the missing namespace and the popup remains functional with raw keys visible until the translations load on retry |

## Behavioral Flow

1. **[User]** navigates to the Chrome Web Store listing page for the
    DoCodeGo extension on a Chromium-based browser, or navigates to
    the Firefox Add-ons listing page on Firefox, and clicks the
    install button to begin the installation process

2. **[Browser]** downloads the extension package from the store,
    verifies the package signature against the store's signing
    certificate, and registers the extension in the browser's
    extension registry using the Manifest V3 configuration generated
    by the WXT framework

3. **[Browser]** adds the DoCodeGo extension icon to the browser
    toolbar in the extensions area — on Chrome the icon appears in
    the extensions menu or pinned to the toolbar if the user pins it,
    on Firefox the icon appears directly in the toolbar after
    installation completes

4. **[Extension]** the browser activates the background service worker
    defined in the WXT-generated manifest.json — the service worker
    initializes and registers event listeners for message passing
    between the popup and the background context, and prepares to
    handle authentication token management and API routing

5. **[Extension]** the Manifest V3 configuration declares three
    permissions that the browser grants at install time: `storage`
    for reading and writing the auth token to `chrome.storage.local`,
    `activeTab` for accessing the currently focused tab information
    when the user clicks the icon, and `host_permissions` scoped to
    the DoCodeGo API URL for making authenticated cross-origin
    HTTP requests

6. **[User]** clicks the DoCodeGo extension icon in the browser
    toolbar for the first time after installation — the browser opens
    the popup window which contains the React application built with
    `@repo/ui` components

7. **[Extension]** the popup React application mounts and checks
    `chrome.storage.local` for an existing auth token — on first
    launch no token exists because the user has not completed the
    token relay authentication flow yet

8. **[Extension]** the popup detects the absence of an auth token and
    renders a localized sign-in prompt using @repo/i18n translation
    keys — the prompt displays a clear call to action button to begin
    the sign-in flow and a brief explanation of what the DoCodeGo
    extension provides to the user

9. **[Extension]** all authenticated features in the popup are blocked
    and not rendered — the popup displays only the sign-in prompt and
    the extension description until the user completes the token relay
    authentication flow and a valid auth token is written to
    `chrome.storage.local`

10. **[User]** sees the localized sign-in prompt in the popup and
    understands that they need to complete the authentication flow
    before accessing any extension features — the extension is fully
    installed, the background service worker is running, all three
    permissions are granted, and the popup is waiting for the user to
    initiate the sign-in process

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| not_installed | installing | User clicks the install button on the Chrome Web Store listing page or the Firefox Add-ons listing page for the DoCodeGo extension | The user is signed into the browser store account (Chrome) or the browser allows unsigned extensions (Firefox development mode) or the listing is published and approved |
| installing | installed_inactive | The browser downloads the extension package, verifies the package signature, registers the extension in the internal extension registry, and adds the icon to the toolbar | The extension package signature is valid, the Manifest V3 configuration is well-formed, and the browser grants the declared permissions (storage, activeTab, host_permissions) |
| installed_inactive | service_worker_running | The browser activates the background service worker defined in the WXT-generated manifest.json and the service worker completes its initialization sequence | The service worker script loads without syntax errors and all event listeners register within the browser's service worker startup timeout |
| service_worker_running | popup_open_unauthenticated | The user clicks the extension icon in the toolbar and the popup React application mounts, reads `chrome.storage.local`, and finds no auth token stored | The popup HTML and JavaScript bundle load without errors and the `chrome.storage.local` read operation completes without a permission error |
| popup_open_unauthenticated | service_worker_running | The user closes the popup by clicking outside of it or pressing Escape — the popup unmounts and the background service worker continues running in the background context | The popup close event fires and the React application unmounts cleanly without leaving pending timers or unresolved promises |
| popup_open_unauthenticated | popup_open_authenticated | The user completes the token relay authentication flow and a valid auth token is written to `chrome.storage.local` by the background service worker — the popup re-reads storage and detects the token | The auth token written to storage is a non-empty string and the background service worker confirms the token is valid by verifying it against the DoCodeGo API |

## Business Rules

- **Rule wxt-generates-mv3-for-both-browsers:** IF the extension
    build pipeline runs THEN the WXT framework generates a valid
    Manifest V3 bundle that produces identical extension behavior on
    Chrome and Firefox — the count of browser-specific configuration
    files maintained outside the WXT framework equals 0
- **Rule service-worker-starts-on-install:** IF the browser
    completes the extension installation and registration THEN the
    background service worker starts within 1000 ms and registers all
    event listeners for message passing and token management — the
    count of active service workers after installation equals 1
- **Rule storage-permission-for-token:** IF the extension is
    installed THEN the `storage` permission is granted and the
    background service worker can read and write auth tokens to
    `chrome.storage.local` — the count of storage permission grants
    after installation equals 1
- **Rule activeTab-for-current-tab:** IF the user clicks the
    extension icon in the toolbar THEN the `activeTab` permission
    grants the extension temporary access to the URL and title of the
    currently focused tab — the count of activeTab permission grants
    per icon click equals 1
- **Rule host-permissions-scoped-to-api:** IF the extension is
    installed THEN the `host_permissions` entry in the manifest is
    scoped exclusively to the DoCodeGo API URL with no wildcard
    patterns matching other domains — the count of host permission
    entries in the manifest equals 1
- **Rule no-token-shows-sign-in-prompt:** IF the popup opens and
    `chrome.storage.local` contains no auth token THEN the popup
    renders a localized sign-in prompt with a call to action button
    and an extension description — the count of sign-in prompts
    displayed when no token exists equals 1
- **Rule authenticated-features-blocked-until-token-present:** IF
    the popup opens and no valid auth token is present in
    `chrome.storage.local` THEN all authenticated features are hidden
    and the user cannot access any protected functionality — the count
    of authenticated feature components rendered without a valid token
    equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User with valid auth token stored in `chrome.storage.local` after completing the token relay authentication flow | Open the popup and interact with all authenticated extension features, trigger API calls to the DoCodeGo API through the background service worker, access current tab information via the `activeTab` permission when clicking the extension icon | Cannot modify the extension permissions declared in the manifest, cannot directly write to `chrome.storage.local` without going through the background service worker token management API, cannot change the `host_permissions` scope at runtime | The popup displays the full authenticated interface including all feature panels, action buttons, and user-specific data fetched from the DoCodeGo API through the background service worker |
| User without an auth token in `chrome.storage.local` before completing the token relay authentication flow (first-time or signed-out state) | Open the popup and view the localized sign-in prompt, click the sign-in call to action button to initiate the token relay authentication flow, read the extension description text rendered in the popup | Cannot access any authenticated features in the popup, cannot trigger API calls to the DoCodeGo API that require authentication, cannot view user-specific data or interact with protected functionality | The popup displays only the sign-in prompt, the call to action button, and the extension description text — all authenticated feature panels are hidden and not rendered in the DOM |
| Background service worker (extension-scoped process that manages tokens and routes API calls between the popup and the DoCodeGo API) | Read and write auth tokens to `chrome.storage.local`, send authenticated HTTP requests to the DoCodeGo API using the granted `host_permissions`, receive and respond to messages from the popup via the extension messaging API | Cannot render UI elements in the popup or modify the popup DOM directly, cannot access tab content beyond what `activeTab` grants when the user clicks the icon, cannot escalate permissions beyond those declared in the manifest | The service worker has access to the auth token in storage, the DoCodeGo API responses, and the message payloads exchanged with the popup — it has no direct visibility into the popup rendering state |

## Constraints

- The background service worker completes initialization and
    registers all event listeners within 1000 ms of the browser
    activating the service worker after installation — the count of
    milliseconds from activation to ready state equals 1000 or fewer.
- The popup React application mounts and renders the sign-in prompt
    within 500 ms of the user clicking the extension icon — the count
    of milliseconds from icon click to visible sign-in prompt equals
    500 or fewer.
- The `chrome.storage.local` read operation to check for an existing
    auth token completes within 100 ms of the popup mount — the count
    of milliseconds from popup mount to storage read result equals
    100 or fewer.
- All user-facing text in the popup uses @repo/i18n translation keys
    with zero hardcoded English strings — the count of hardcoded
    user-facing strings in the popup component tree equals 0.
- The `host_permissions` entry in the generated manifest.json is
    scoped to exactly 1 origin matching the DoCodeGo API URL — the
    count of wildcard host permission patterns equals 0.
- The WXT framework generates a single Manifest V3 bundle that runs
    on both Chrome and Firefox without browser-specific overrides —
    the count of browser-specific manifest files maintained in the
    source repository equals 0.

## Acceptance Criteria

- [ ] Installing the extension from the Chrome Web Store adds the extension icon to the toolbar — the count of DoCodeGo extension icons visible in the toolbar after installation equals 1
- [ ] Installing the extension from Firefox Add-ons adds the extension icon to the toolbar — the count of DoCodeGo extension icons visible in the toolbar after installation equals 1
- [ ] The background service worker starts after installation and reaches the ready state — the count of active background service workers for the extension equals 1
- [ ] The manifest.json declares the `storage` permission in the permissions array — the count of `storage` entries in the manifest permissions array equals 1
- [ ] The manifest.json declares the `activeTab` permission in the permissions array — the count of `activeTab` entries in the manifest permissions array equals 1
- [ ] The manifest.json declares exactly 1 host permission entry scoped to the DoCodeGo API URL — the count of entries in the manifest host_permissions array equals 1
- [ ] Clicking the extension icon opens the popup React application — the count of rendered popup root components after icon click equals 1
- [ ] The popup reads `chrome.storage.local` and when no auth token exists displays the sign-in prompt — the count of sign-in prompt components rendered when no token is stored equals 1
- [ ] The sign-in prompt text is localized using @repo/i18n translation keys — the count of hardcoded English strings in the popup DOM equals 0
- [ ] Authenticated feature components are not rendered when no auth token is present in storage — the count of authenticated feature components in the popup DOM when no token exists equals 0
- [ ] The WXT framework generates a valid Manifest V3 bundle from the single codebase — the count of generated manifest.json files with manifest_version equals 3 per build equals 1
- [ ] The popup renders within 500 ms of the user clicking the extension icon — the count of milliseconds from icon click to visible popup content equals 500 or fewer

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User installs the extension on a Chromium-based browser other than Chrome (Edge, Brave, Vivaldi) that supports Manifest V3 extensions from the Chrome Web Store | The extension installs and functions identically to Chrome because the WXT framework generates a standard Manifest V3 bundle that all Chromium-based browsers support — the icon appears in the toolbar and the popup renders the sign-in prompt | The count of extension icons in the toolbar equals 1 and the popup sign-in prompt renders within 500 ms of the icon click |
| User installs the extension but immediately disables it from the browser extensions management page before clicking the icon | The background service worker stops and the extension icon is removed from the toolbar or grayed out — re-enabling the extension restarts the service worker and restores the icon to its active state | The count of active service workers after disabling equals 0 and after re-enabling equals 1, and the toolbar icon reappears in the active state |
| User installs the extension while offline with no network connectivity available for the background service worker to reach the DoCodeGo API | The extension installs from the browser store cache if previously fetched, the service worker starts and registers event listeners, the popup opens and displays the sign-in prompt — API-dependent features are unavailable until network connectivity returns | The sign-in prompt renders in the popup, the count of API call errors logged by the service worker equals 0 because no API calls are attempted until the user initiates sign-in |
| The browser automatically updates the extension to a new version while the user has an existing auth token stored in `chrome.storage.local` | The `chrome.storage.local` data persists across extension updates because the browser preserves extension storage during updates — the new service worker reads the existing token and the user remains authenticated without re-signing in | The count of auth tokens in `chrome.storage.local` after the update equals 1 and the popup displays the authenticated interface instead of the sign-in prompt |
| User revokes the `host_permissions` grant from the browser's extension permissions settings after installing the extension | The background service worker cannot make authenticated HTTP requests to the DoCodeGo API and all API calls fail with a permission error — the popup detects the failure and displays an error message instructing the user to re-grant the permission | The count of successful API responses equals 0 after permission revocation and the popup displays a permission error message component |
| The `chrome.storage.local` quota is exhausted by other extensions and the auth token write operation fails after the token relay flow | The background service worker catches the storage quota error and logs the failure with the current storage usage — the popup displays an error state indicating that the auth token could not be saved and the user falls back to retrying after clearing storage from other extensions | The count of auth tokens successfully written equals 0 and the logged error contains the storage quota limit and current usage values |

## Failure Modes

- **Background service worker fails to start after extension installation due to a script error**
    - **What happens:** The browser attempts to activate the
        background service worker defined in the WXT-generated
        manifest.json but the script contains a syntax error, an
        unresolved module import, or throws an uncaught exception
        during initialization that prevents the worker from reaching
        the ready state.
    - **Source:** A build-time error in the WXT compilation pipeline
        produced a malformed service worker bundle, or a dependency
        import references a module that was tree-shaken out of the
        production build, or the service worker script exceeds the
        browser's maximum service worker script size limit.
    - **Consequence:** The extension icon appears in the toolbar but
        all popup interactions that depend on the service worker for
        token management and API routing fail silently or display
        error states — the user cannot complete the sign-in flow or
        access any extension functionality.
    - **Recovery:** The browser logs the service worker activation
        error in the extensions developer console and the extension
        retries activation on the next user interaction — the
        developer alerts the team to fix the build pipeline and
        publishes a corrected extension update to the store.

- **`chrome.storage.local` read fails when the popup checks for an existing auth token on open**
    - **What happens:** The popup React application mounts and calls
        `chrome.storage.local.get` to read the auth token but the
        storage API returns an error because the storage is corrupted,
        the browser's internal database is locked by another process,
        or the extension's storage quota has been exceeded by
        previously stored data.
    - **Source:** The browser's internal IndexedDB or LevelDB storage
        backend that powers `chrome.storage.local` encountered a
        corruption event during a previous unexpected browser crash,
        or another extension sharing the storage backend holds a lock
        that blocks read access within the timeout period.
    - **Consequence:** The popup cannot determine whether an auth
        token exists and defaults to rendering the sign-in prompt even
        if the user previously authenticated — the user perceives this
        as being signed out despite having a valid token stored in
        the inaccessible storage.
    - **Recovery:** The popup catches the storage read error and
        falls back to rendering the sign-in prompt as the default
        unauthenticated state, then logs the storage error details
        including the error code and message — the user re-signs in
        and the new token write operation succeeds if the storage
        issue was transient.

- **Browser denies or revokes the `host_permissions` grant preventing API communication with the DoCodeGo server**
    - **What happens:** The background service worker attempts to
        send an authenticated HTTP request to the DoCodeGo API URL
        but the browser blocks the request because the user revoked
        the host permission from the extension settings page, or the
        browser updated its permission enforcement policy and now
        requires explicit user re-approval for the host grant.
    - **Source:** The user navigated to the browser's extension
        permissions management page and toggled off the site access
        permission for the DoCodeGo API domain, or a browser update
        changed the host permission model from install-time grant to
        runtime approval requiring the user to re-authorize the
        domain.
    - **Consequence:** All API calls from the extension to the
        DoCodeGo server fail with a permission denied error and the
        popup cannot fetch user data or perform any authenticated
        actions — the extension is effectively non-functional for
        any feature that requires API communication.
    - **Recovery:** The popup detects the API permission failure and
        displays a localized error message instructing the user to
        re-grant the host permission from the browser's extension
        settings page — the extension logs the permission denial
        event and retries the API call after the user navigates back
        to the popup.

## Declared Omissions

- This specification does not define the token relay authentication
    flow that exchanges credentials between the web application and the
    extension — that mechanism is covered by a separate spec addressing
    the browser-to-extension token relay protocol and popup-to-web
    communication channel.
- This specification does not cover the content script injection
    behavior that modifies web page content when the user visits specific
    domains — content scripts and their injection rules require a
    separate specification with their own permission model and lifecycle
    definition.
- This specification does not address the extension update mechanism
    that delivers new versions through the Chrome Web Store or Firefox
    Add-ons automatic update pipeline — the update behavior and data
    migration between extension versions require a separate specification.
- This specification does not define the specific authenticated features
    available in the popup after the user completes the sign-in flow —
    the authenticated popup interface and its feature set are documented
    in a separate behavioral specification covering extension usage after
    authentication.
- This specification does not cover the browser store listing content
    including the extension description, screenshots, privacy policy, or
    store review process — listing metadata and store compliance are
    operational concerns outside the application codebase behavioral
    specification scope.

## Related Specifications

- [session-lifecycle](session-lifecycle.md) — defines the full
    authentication session lifecycle including token creation, validation,
    expiration, and revocation that determines whether the extension popup
    displays the authenticated interface or the sign-in prompt on each
    open
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) —
    defines the email OTP sign-in flow that extension users follow when
    they click the sign-in call to action in the popup and are redirected
    to the web application to complete authentication via email OTP
- [user-changes-language](user-changes-language.md) — defines the
    language switching mechanism that determines which @repo/i18n locale
    the extension popup uses to render all user-facing text including the
    sign-in prompt and extension description
- [user-changes-theme](user-changes-theme.md) — defines the theme
    switching mechanism that determines whether the extension popup
    renders in light mode, dark mode, or follows the operating system
    preference for the visual appearance of all UI components
- [user-interacts-with-extension-popup](user-interacts-with-extension-popup.md) — defines the authenticated extension popup interface and feature set that the user accesses after completing the sign-in flow initiated from the sign-in prompt rendered during installation

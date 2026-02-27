---
id: SPEC-2026-082
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Interacts with Extension Popup

## Intent

This spec defines how a user interacts with the DoCodeGo browser
extension popup after clicking the extension icon in the browser
toolbar. The popup is a React application rendered from
`src/entrypoints/popup/` that uses `@repo/ui` Shadcn components and
Tailwind CSS for styling consistent with the web dashboard. When the
user clicks the toolbar icon, the popup opens and reads
`chrome.storage.local` to determine the authentication state. If no
valid auth token exists, the popup displays only a localized sign-in
prompt. If a valid token exists, the popup renders the full
authenticated interface with relevant data and action controls. All
API calls from the popup route through the background service worker
using the oRPC client with typed contracts from `@repo/contracts` —
the service worker attaches the stored auth token and forwards the
request to the DoCodeGo API. When the extension needs to interact
with the current browser tab, the popup communicates through the
content script injected into the page, scoped by the `activeTab`
permission so only the explicitly clicked tab is accessible. Dark
mode follows the browser or system preference, or the stored theme
setting, applied via the `dark` class on the popup root element. The
popup uses translations from `@repo/i18n` supporting all web app
locales including Arabic with RTL layout determined by the `dir`
attribute. The popup closes when the user clicks outside it or
presses Escape, discarding all in-progress state — persistent state
like auth tokens and preferences lives in `chrome.storage.local` via
the background service worker and survives open/close cycles.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Extension popup React application (renders from `src/entrypoints/popup/` using `@repo/ui` Shadcn components and Tailwind CSS styling identical to the web dashboard design system) | render/read | When the user clicks the extension toolbar icon the popup mounts, reads auth state from `chrome.storage.local`, and renders the sign-in prompt or authenticated interface based on token presence | The popup fails to mount due to a JavaScript bundle error in the React application entry point — the extension icon click opens a blank popup panel and the user falls back to closing and reopening the popup to trigger a fresh render attempt |
| `@repo/contracts` oRPC typed contracts (shared API type definitions that define request and response shapes for all DoCodeGo API endpoints used by the popup through the service worker proxy) | read/write | When the popup initiates a data fetch or action that requires an API call, the oRPC client constructs the request using typed contracts and sends it to the background service worker for forwarding | The contracts package fails to resolve at build time due to a workspace dependency mismatch — the build fails with a TypeScript compilation error and the CI pipeline alerts the development team to fix the broken dependency |
| Background service worker (extension-scoped persistent backend that proxies all API requests from the popup, attaches the stored auth token as an Authorization header, and forwards requests to the DoCodeGo API) | read/write | On every API request initiated by the popup, the popup sends a message to the service worker which attaches the Authorization header with the stored token and forwards the request to the API endpoint | The service worker is terminated by the browser due to inactivity or memory pressure and restarts on the next message from the popup — the restarted worker reads the token from `chrome.storage.local` and processes the request without requiring user re-authentication |
| Content script (injected into the active browser tab to provide page interaction capabilities, scoped by the `activeTab` permission to the tab the user explicitly clicked the extension icon on) | read/write | When the popup requests information about the current tab or triggers an action on the active page, it sends a message to the content script via `chrome.tabs.sendMessage()` targeting the active tab ID | The content script is not injected because the active tab URL is a restricted page (chrome:// or about:// URLs) — the popup catches the messaging error and displays a placeholder message indicating that page interaction is not available on this tab |
| `@repo/i18n` localization infrastructure (provides translated strings for all user-facing text in the popup, supporting the same locales as the web application including Arabic with right-to-left layout direction) | read | When the popup React application initializes it detects the browser language setting and loads the matching locale namespace from `@repo/i18n` to render all visible text in the detected language | The i18n namespace fails to load due to a missing translation file or network error during lazy loading — the popup degrades to displaying raw translation keys instead of localized strings and logs the missing namespace for debugging |
| `chrome.storage.local` (browser-provided key-value storage API used to persist auth tokens, theme preference, and locale setting across popup open/close cycles, browser restarts, and extension updates) | read/write | When the popup opens it reads the auth token, theme preference, and locale setting from storage — when the user changes preferences the popup writes the updated values through the background service worker | The storage API call rejects with a quota or permission error and the preference values cannot be read or written — the popup falls back to using browser defaults for theme and locale and displays the sign-in prompt because no token is found |

## Behavioral Flow

1. **[User]** clicks the DoCodeGo extension icon in the browser
    toolbar to open the extension popup — the browser creates the
    popup window and begins loading the React application from the
    `src/entrypoints/popup/` entry point

2. **[Popup]** the React application mounts and reads
    `chrome.storage.local` for the auth token, theme preference,
    and locale setting — the storage read completes within 100 ms
    of the popup mount event

3. **[Popup]** applies the theme by checking the stored preference
    in `chrome.storage.local` first, then falling back to the
    browser or system `prefers-color-scheme` media query — the
    `dark` class is added to or removed from the popup root element
    based on the resolved theme value

4. **[Popup]** initializes `@repo/i18n` with the stored locale
    from `chrome.storage.local` or detects the browser language
    setting via `navigator.language` — for Arabic (ar) the popup
    sets `dir="rtl"` on the root element and loads the RTL
    stylesheet variant

5. **[Popup]** evaluates the auth token read from storage — if the
    token is absent or empty the popup transitions to the
    unauthenticated state and renders only the localized sign-in
    prompt with no access to authenticated features

6. **[Popup]** if a valid auth token exists in storage the popup
    transitions to the authenticated state and renders the main
    interface with data panels, action controls, and user context
    information fetched from the DoCodeGo API

7. **[Popup]** sends an API request by constructing the call using
    the oRPC client with typed contracts from `@repo/contracts` and
    forwarding the request as a message to the background service
    worker via `chrome.runtime.sendMessage()`

8. **[ServiceWorker]** receives the API request message from the
    popup, retrieves the stored auth token from
    `chrome.storage.local`, attaches it as an `Authorization`
    header on the outgoing HTTP request, and sends the request to
    the DoCodeGo API endpoint

9. **[ServiceWorker]** receives the API response and forwards the
    response payload back to the popup via the message response
    callback — the popup renders the received data in the
    authenticated interface components

10. **[User]** triggers an action that requires interaction with
    the current browser tab — the popup sends a message to the
    content script via `chrome.tabs.sendMessage()` targeting the
    active tab ID

11. **[ContentScript]** receives the message from the popup,
    executes the requested action on the active page (reading page
    information or triggering a DOM interaction), and returns the
    result to the popup via the message response callback

12. **[Popup]** the `activeTab` permission restricts content script
    interaction to only the tab the user explicitly clicked the
    extension icon on — the popup cannot access any other open tabs
    or inject scripts into background pages

13. **[User]** clicks outside the popup window or presses the
    Escape key — the browser closes the popup and the React
    application unmounts, discarding all in-progress component
    state including form inputs, scroll position, and pending
    requests

14. **[Popup]** on close all transient state is lost because the
    popup reinitializes from scratch on every open — persistent
    data including the auth token, theme preference, and locale
    setting remains in `chrome.storage.local` managed by the
    background service worker and survives across open/close cycles

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| closed | loading | The user clicks the DoCodeGo extension icon in the browser toolbar and the browser begins rendering the popup React application from the entry point | The extension is installed and enabled in the browser, the popup HTML and JavaScript bundle are present in the extension package, and no other popup instance is open |
| loading | unauthenticated | The popup reads `chrome.storage.local` and finds no valid auth token stored, or the storage read returns an empty value for the token key | The storage read operation completes without a permission error and the returned token value is absent, empty, or null |
| loading | authenticated | The popup reads `chrome.storage.local` and finds a valid non-empty auth token stored by the background service worker during a previous token relay flow | The storage read operation completes without a permission error and the returned token value is a non-empty string |
| authenticated | fetching_data | The popup initiates an API request through the oRPC client and sends the request message to the background service worker for forwarding to the DoCodeGo API | The service worker is running and responsive to messages, and the auth token is present in `chrome.storage.local` for the Authorization header attachment |
| fetching_data | authenticated | The background service worker returns the API response payload to the popup via the message response callback and the popup renders the received data in the interface | The API response status code is HTTP 200 and the response payload conforms to the `@repo/contracts` typed response schema |
| fetching_data | unauthenticated | The API request returns HTTP 401 indicating the auth token is expired or revoked, and the popup clears the local auth state and transitions to the sign-in prompt | The API response status code is HTTP 401 and the service worker clears the invalid token from `chrome.storage.local` |
| authenticated | tab_interaction | The user triggers an action that requires content script communication and the popup sends a message to the content script via `chrome.tabs.sendMessage()` on the active tab | The `activeTab` permission is granted for the current tab and the content script is injected into the active page |
| tab_interaction | authenticated | The content script returns the result of the page interaction to the popup via the message response callback and the popup updates the interface with the received data | The content script responds within 5000 ms and the response payload contains the requested page information or action confirmation |
| authenticated | closed | The user clicks outside the popup or presses Escape, and the browser closes the popup window causing the React application to unmount and discard transient state | The popup close event fires and the React unmount lifecycle completes without errors |
| unauthenticated | closed | The user clicks outside the popup or presses Escape while viewing the sign-in prompt, and the browser closes the popup window and unmounts the React application | The popup close event fires and the React unmount lifecycle completes without errors |

## Business Rules

- **Rule unauthenticated-shows-sign-in-only:** IF the popup opens
    and `chrome.storage.local` contains no valid auth token THEN the
    popup renders only the localized sign-in prompt and hides all
    authenticated feature components — the count of authenticated
    feature components rendered without a valid token equals 0
- **Rule authenticated-shows-main-ui:** IF the popup opens and
    `chrome.storage.local` contains a valid non-empty auth token
    THEN the popup renders the full authenticated interface with
    data panels and action controls — the count of visible
    authenticated feature panels equals 1 or more
- **Rule api-calls-route-through-service-worker:** IF the popup
    initiates an API request using the oRPC client THEN the request
    message is sent to the background service worker via
    `chrome.runtime.sendMessage()` and not directly to the API —
    the count of direct HTTP requests from the popup to the DoCodeGo
    API equals 0
- **Rule service-worker-attaches-token:** IF the background service
    worker receives an API request message from the popup THEN it
    reads the auth token from `chrome.storage.local` and attaches it
    as an `Authorization` header on the outgoing request — the count
    of API requests forwarded without the `Authorization` header
    equals 0
- **Rule active-tab-only-access:** IF the popup sends a message to
    the content script for page interaction THEN the message targets
    only the tab the user explicitly clicked the extension icon on
    via the `activeTab` permission — the count of tabs accessible
    beyond the active tab equals 0
- **Rule theme-follows-browser-preference:** IF no theme preference
    is stored in `chrome.storage.local` THEN the popup applies the
    theme from the browser or system `prefers-color-scheme` media
    query — the `dark` class on the popup root element matches the
    system dark mode state when no stored preference exists
- **Rule locale-from-browser-language:** IF no locale preference is
    stored in `chrome.storage.local` THEN the popup detects the
    browser language via `navigator.language` and loads the matching
    @repo/i18n namespace — the rendered text language matches the
    browser language setting when no stored locale exists
- **Rule arabic-uses-rtl-layout:** IF the resolved locale is Arabic
    (ar) THEN the popup sets `dir="rtl"` on the root element and
    loads the RTL stylesheet variant — the `dir` attribute value on
    the popup root element equals `rtl` when the locale is Arabic
- **Rule popup-reinitializes-on-close:** IF the popup closes via
    click-outside or Escape press THEN all transient component state
    is discarded and the next open starts a fresh React mount — the
    count of preserved transient state values between consecutive
    popup opens equals 0
- **Rule persistent-state-survives-close:** IF the popup closes
    THEN the auth token, theme preference, and locale setting stored
    in `chrome.storage.local` remain intact and are available on the
    next popup open — the count of persistent storage keys lost on
    popup close equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User with valid auth token stored in `chrome.storage.local` who opens the popup by clicking the extension icon in the browser toolbar | Open the popup and view the authenticated interface with data panels, trigger API calls to the DoCodeGo API through the background service worker proxy, interact with the content script on the active tab via `activeTab` permission, change theme and locale preferences stored in `chrome.storage.local` | Cannot make direct HTTP requests from the popup to the DoCodeGo API bypassing the service worker, cannot access tabs other than the active tab clicked on, cannot modify the extension manifest permissions at runtime, cannot prevent popup reinitialization on close | The popup displays the full authenticated interface with user-specific data fetched from the API, the current tab information via the content script, and the applied theme and locale preferences |
| User without a valid auth token in `chrome.storage.local` who opens the popup by clicking the extension icon in the browser toolbar | Open the popup and view the localized sign-in prompt, click the sign-in call to action to initiate the token relay authentication flow, view the extension description text rendered in the popup | Cannot access any authenticated features, cannot trigger API calls that require authentication, cannot interact with the content script for page-specific actions, cannot view user-specific data or feature panels | The popup displays only the sign-in prompt, the call to action button, and the extension description text — all authenticated feature panels and data displays are hidden from the DOM |
| Background service worker (proxies API requests from the popup, attaches stored auth tokens, and manages persistent state in `chrome.storage.local` on behalf of the popup) | Receive API request messages from the popup and forward them with the Authorization header to the DoCodeGo API, read and write auth tokens and preference values in `chrome.storage.local`, respond to popup messages with API response payloads | Cannot render UI elements in the popup or modify the popup DOM directly, cannot initiate tab interactions without a message from the popup, cannot escalate permissions beyond those declared in the extension manifest | The service worker has access to the auth token, API response data, and preference values in storage but has no direct visibility into the popup rendering state or component lifecycle |

## Constraints

- The popup React application mounts and renders the initial view
    (sign-in prompt or authenticated interface) within 500 ms of the
    user clicking the extension icon — the count of milliseconds
    from icon click to visible content equals 500 or fewer.
- The `chrome.storage.local` read operation for auth token, theme,
    and locale completes within 100 ms of the popup mount — the
    count of milliseconds from mount to storage read completion
    equals 100 or fewer.
- All user-facing text in the popup uses `@repo/i18n` translation
    keys with zero hardcoded English strings — the count of
    hardcoded user-facing strings in the popup component tree
    equals 0.
- The popup sends API requests exclusively through the background
    service worker message channel and never makes direct HTTP
    requests to the DoCodeGo API — the count of direct fetch calls
    from the popup to the API origin equals 0.
- Content script interaction via `chrome.tabs.sendMessage()` targets
    only the active tab granted by the `activeTab` permission — the
    count of tabs messaged beyond the active tab per popup session
    equals 0.
- The content script responds to popup messages within 5000 ms or
    the popup treats the interaction as timed out — the count of
    milliseconds from message send to response timeout equals
    5000 or fewer.

## Acceptance Criteria

- [ ] Clicking the extension icon opens the popup and renders visible content within 500 ms — the count of milliseconds from icon click to first visible content equals 500 or fewer
- [ ] When no auth token exists in `chrome.storage.local` the popup displays only the sign-in prompt — the count of authenticated feature components rendered equals 0
- [ ] When a valid auth token exists in `chrome.storage.local` the popup displays the authenticated interface — the count of visible authenticated feature panels equals 1 or more
- [ ] API calls from the popup route through the background service worker and not directly to the API — the count of direct HTTP requests from the popup to the DoCodeGo API equals 0
- [ ] The background service worker attaches the stored auth token as an Authorization header on forwarded API requests — the count of forwarded requests missing the Authorization header equals 0
- [ ] Content script interaction is scoped to the active tab via the `activeTab` permission — the count of tabs accessed beyond the active tab equals 0
- [ ] When no stored theme preference exists the popup applies the browser or system `prefers-color-scheme` value — the `dark` class presence on the root element matches the system dark mode state returning true or false
- [ ] When the stored theme preference is dark the popup adds the `dark` class to the root element — the `dark` class is present on the popup root element
- [ ] The popup detects the browser language via `navigator.language` and loads the matching `@repo/i18n` locale within 200 ms of mount — the count of locale mismatches between rendered text and browser language equals 0
- [ ] When the locale is Arabic the popup sets `dir="rtl"` on the root element — the count of root elements with `dir` attribute value not equal to `rtl` when locale is Arabic equals 0
- [ ] All user-facing text uses `@repo/i18n` translation keys with zero hardcoded English strings — the count of hardcoded user-facing strings in the popup DOM equals 0
- [ ] Closing the popup via click-outside or Escape discards transient state — the count of preserved transient state values between consecutive opens equals 0
- [ ] Persistent state in `chrome.storage.local` including auth token and preferences survives popup close — the count of storage keys lost after popup close equals 0
- [ ] The content script responds to popup messages within 5000 ms or the popup displays a timeout indicator — the count of milliseconds from message send to timeout equals 5000 or fewer

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user opens the popup on a restricted browser page (chrome://, about://, or browser settings page) where content scripts cannot be injected | The popup opens and displays the authenticated interface or sign-in prompt normally, but any feature requiring content script interaction displays a placeholder message explaining that page interaction is unavailable on restricted pages | The popup renders within 500 ms, the content script messaging call returns an error, and the placeholder message component is present in the DOM |
| The user opens the popup while the browser is offline with no network connectivity available for API requests | The popup opens, reads the auth token from `chrome.storage.local`, and attempts API calls through the service worker which fail with network errors — the popup displays cached data if available or an offline indicator with a retry button | The popup mounts within 500 ms, the API request fails with a network error, and the offline indicator component is present in the DOM |
| The user rapidly opens and closes the popup 5 times within 3 seconds to test reinitialization behavior | Each open triggers a fresh React mount that reads storage and renders the correct state, and each close discards transient state completely — no memory leaks or stale event listeners accumulate across cycles | The count of mounted popup instances at any point equals 1, and the memory footprint after 5 cycles does not exceed 2 times the single-open baseline |
| The browser terminates the background service worker between popup opens due to inactivity timeout | The popup opens and sends an API request message that triggers the service worker to restart, the restarted worker reads the token from `chrome.storage.local` and processes the request — the user experiences a slight delay but no authentication loss | The API response arrives within 3000 ms accounting for service worker restart time, and the auth token remains valid in storage |
| The user changes the system theme from light to dark while the popup is open and no stored preference exists | The popup detects the `prefers-color-scheme` change via a media query listener and toggles the `dark` class on the root element in real time without requiring a popup close and reopen | The `dark` class is added to the root element within 200 ms of the system theme change event |
| The `chrome.storage.local` read returns an empty object because extension storage was cleared externally by a browser cleanup tool or storage quota exceeded | The popup treats the empty storage as unauthenticated state and renders the sign-in prompt with default theme (system preference) and default locale (browser language) — no JavaScript errors thrown during the storage read | The popup renders the sign-in prompt within 500 ms, the theme matches system preference, and the locale matches the browser language setting |

## Failure Modes

- **Popup React application fails to mount after the user clicks the extension icon in the toolbar**
    - **What happens:** The user clicks the extension icon and the browser creates the popup window, but the React application throws a JavaScript error during mounting due to a bundle compilation error, a missing module import, or an incompatible browser API call that prevents the component tree from rendering.
    - **Source:** A build-time error in the WXT compilation pipeline produced a malformed popup JavaScript bundle, a dependency from `@repo/ui` references a browser API not available in the extension popup context, or the popup HTML entry point references a script path that was renamed or moved during a refactor.
    - **Consequence:** The popup window opens but displays a blank white panel with no interactive elements — the user cannot see the sign-in prompt, cannot access authenticated features, and cannot interact with the extension through the popup interface at all.
    - **Recovery:** The popup catches the mount error in a top-level error boundary and logs the error details to the browser extension console — the user falls back to closing the popup and reopening it, and if the error persists the user reinstalls the extension to obtain a corrected bundle from the store.

- **Background service worker fails to respond to API request messages from the popup within the expected timeout**
    - **What happens:** The popup sends an API request message to the background service worker via `chrome.runtime.sendMessage()` but the service worker does not respond within 10000 ms because it is terminated by the browser, stuck processing a previous request, or encountered an unhandled exception in the message listener.
    - **Source:** The browser terminated the service worker due to memory pressure or inactivity timeout and the restart takes longer than expected, the service worker's message listener throws an uncaught error before sending the response callback, or a deadlock occurs in the token read from `chrome.storage.local`.
    - **Consequence:** The popup displays a loading indicator that never resolves, and the user cannot view data or perform actions that require API communication — the popup remains in a stale loading state until the user closes and reopens it.
    - **Recovery:** The popup implements a 10000 ms timeout on service worker messages and displays an error state with a retry button when the timeout fires — the user retries the request which triggers a fresh service worker wake-up, and the popup logs the timeout event for debugging purposes.

- **Content script messaging fails because the active tab page blocks or restricts extension communication**
    - **What happens:** The popup sends a message to the content script via `chrome.tabs.sendMessage()` but the content script is not injected or cannot respond because the active page uses a Content Security Policy that blocks extension scripts, the page is a browser-internal URL, or the content script was not loaded due to a manifest configuration error.
    - **Source:** The user clicked the extension icon while viewing a chrome://, about://, or edge:// page where content scripts cannot execute, the active page's Content Security Policy includes a directive that blocks injected scripts, or the WXT manifest configuration omitted the content script entry for the active page's URL pattern.
    - **Consequence:** The popup cannot retrieve page information or trigger page actions through the content script — any feature that depends on tab interaction returns an error and the user cannot use page-contextual functionality for the current tab.
    - **Recovery:** The popup catches the `chrome.tabs.sendMessage()` error, detects the restricted page condition, and degrades gracefully by displaying a localized placeholder message explaining that page interaction is not available on this tab — the popup logs the tab URL pattern that triggered the failure for diagnostic purposes.

## Declared Omissions

- This specification does not define the token relay authentication
    flow that exchanges credentials between the web application and the
    extension — that mechanism is covered by the extension-authenticates
    -via-token-relay specification addressing the browser-to-extension
    token relay protocol and token storage lifecycle.
- This specification does not define the specific authenticated feature
    set available in the popup such as quick actions, notifications, or
    content displays — the authenticated popup feature panels and their
    data requirements are documented in a separate behavioral
    specification covering the extension feature set after
    authentication.
- This specification does not cover the extension installation flow
    including store listing, manifest generation, permission grants, and
    initial service worker startup — the installation process is covered
    by the user-installs-browser-extension specification defining the
    WXT build and browser registration steps.
- This specification does not address the session refresh timer or
    token expiration handling managed by the background service worker —
    the token refresh lifecycle is defined in the
    extension-authenticates-via-token-relay specification and the
    session-lifecycle specification.
- This specification does not define the content script injection rules,
    URL pattern matching, or page modification capabilities — content
    script configuration and injection behavior require a separate
    specification with their own permission model and lifecycle
    definition.

## Related Specifications

- [user-installs-browser-extension](user-installs-browser-extension.md)
    — defines the extension installation flow including WXT manifest
    generation, permission grants, service worker startup, and the
    initial unauthenticated popup state that precedes the interactions
    described in this specification
- [extension-authenticates-via-token-relay](extension-authenticates-via-token-relay.md)
    — defines the token relay authentication flow that writes the auth
    token to `chrome.storage.local`, which this specification reads on
    every popup open to determine whether to show the sign-in prompt or
    the authenticated interface
- [session-lifecycle](session-lifecycle.md) — defines the session
    creation, refresh, and revocation behavior on the server side that
    determines whether the auth token read by the popup from storage is
    valid or expired
- [user-changes-theme](user-changes-theme.md) — defines the theme
    switching mechanism that writes the theme preference to storage,
    which this specification reads on popup open to determine whether to
    apply the `dark` class or follow the system preference
- [user-changes-language](user-changes-language.md) — defines the
    language switching mechanism that writes the locale preference to
    storage, which this specification reads on popup open to load the
    correct `@repo/i18n` namespace and set the `dir` attribute for RTL
    locales like Arabic

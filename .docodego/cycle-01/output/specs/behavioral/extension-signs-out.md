---
id: SPEC-2026-081
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# Extension Signs Out

## Intent

This spec defines how a user signs out of the DoCodeGo browser
extension by clicking the localized "Sign out" button in the extension
popup. The "Sign out" button is only visible when the extension is in
an authenticated state — meaning a valid session token exists in
`chrome.storage.local` after a previous sign-in via the token relay
flow. When the user clicks "Sign out", the popup sends a message to
the background service worker requesting sign-out. The service worker
clears the session token from `chrome.storage.local` and cancels the
active session refresh timer so that no further automatic token refresh
attempts occur after the explicit sign-out. With the token removed,
the popup immediately reflects the unauthenticated state by replacing
the authenticated UI — user details, quick actions, and the sign-out
button — with a localized sign-in prompt rendered through @repo/i18n
translation keys. Signing out of the extension does not affect the
user's web session because the extension and web application maintain
separate authentication states — the extension relies on a token
stored in `chrome.storage.local` while the web application uses session
cookies managed by the API. The user remains signed in to the web
application and can continue using it normally after signing out of the
extension.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Extension popup UI (renders the "Sign out" button when a valid session token exists in `chrome.storage.local` and displays the authenticated state with user details and quick actions) | read/write | When the user opens the extension popup and the popup reads `chrome.storage.local` to determine the authentication state, rendering the "Sign out" button and authenticated UI when a valid token is present | The popup fails to render due to a browser extension framework error and the user cannot initiate sign-out — the user falls back to closing and reopening the popup to trigger a fresh render cycle that re-reads the storage state |
| Background service worker (receives the sign-out message from the popup, clears the session token from `chrome.storage.local`, and cancels the active session refresh timer to stop all automatic token refresh attempts) | read/write | When the popup sends a sign-out message to the service worker via the extension messaging API after the user clicks the "Sign out" button in the popup interface | The service worker is terminated by the browser due to inactivity or memory pressure and restarts on the next event — the restarted worker processes the sign-out message by clearing the token from `chrome.storage.local` and resetting the refresh timer state |
| `chrome.storage.local` (browser extension storage API that holds the session token, which the service worker deletes during sign-out to revoke the extension's authenticated state) | write | When the background service worker receives the sign-out message and calls `chrome.storage.local.remove()` to delete the session token key from the persistent extension storage | The storage API call fails due to a browser storage error or corrupted storage state — the service worker logs the storage removal failure and the popup falls back to re-reading storage on the next open to determine whether the token was cleared |
| Web application session cookies (HTTP-only session cookies managed by the DoCodeGo API that maintain the user's authenticated state in the web application independently of the extension token) | none | The extension sign-out flow does not interact with, read, modify, or clear the web application's session cookies at any point during the sign-out process | Not applicable because the extension sign-out intentionally does not interact with the web application's session cookies — the web session remains active and unaffected regardless of the extension's authentication state |
| @repo/i18n (localization infrastructure that provides translated strings for the sign-in prompt displayed after sign-out completes, including the call to action button and extension description text) | read | When the popup transitions to the unauthenticated state after sign-out and renders the localized sign-in prompt with translated button labels and description text via @repo/i18n translation keys | The i18n namespace fails to load and the popup degrades to displaying raw translation keys instead of localized strings — the extension logs the missing namespace and the popup remains functional with raw keys visible until the translations load on retry |

## Behavioral Flow

1. **[User]** opens the extension popup and sees the authenticated UI
    displaying user details, quick actions, and the localized "Sign
    out" button — the "Sign out" button is rendered only because a
    valid session token exists in `chrome.storage.local`

2. **[User]** clicks the localized "Sign out" button in the extension
    popup to initiate the sign-out process and end the authenticated
    extension session

3. **[Popup]** sends a sign-out message to the background service
    worker via the extension messaging API using
    `chrome.runtime.sendMessage()` with a payload identifying the
    request as a sign-out action

4. **[ServiceWorker]** receives the sign-out message from the popup
    via the `chrome.runtime.onMessage` listener and begins processing
    the sign-out by calling `chrome.storage.local.remove()` to delete
    the session token key from the persistent extension storage

5. **[ServiceWorker]** cancels the active session refresh timer that
    was running to keep the token valid — after cancellation the count
    of active refresh timers equals 0 and no further automatic token
    refresh requests are sent to the DoCodeGo API

6. **[ServiceWorker]** sends a confirmation message back to the popup
    indicating that the sign-out completed — the token is cleared from
    storage and the refresh timer is cancelled

7. **[Popup]** detects the token removal from `chrome.storage.local`
    via the `chrome.storage.onChanged` listener and immediately
    transitions from the authenticated UI to the unauthenticated state
    by replacing user details, quick actions, and the "Sign out" button
    with a localized sign-in prompt rendered through @repo/i18n
    translation keys

8. **[User]** sees the localized sign-in prompt in the popup and
    understands that the extension sign-out is complete — the web
    application session remains active and unaffected because the
    extension and web application maintain independent authentication
    states

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| authenticated | signing_out | The user clicks the "Sign out" button in the extension popup and the popup sends a sign-out message to the background service worker via the extension messaging API | The popup is in the authenticated state with a valid session token present in `chrome.storage.local` and the "Sign out" button is visible and enabled |
| signing_out | unauthenticated | The background service worker clears the session token from `chrome.storage.local` and cancels the active refresh timer, then the popup detects the token removal via `chrome.storage.onChanged` | The `chrome.storage.local.remove()` call completes without error and the refresh timer cancellation is confirmed by the service worker |
| signing_out | authenticated (rollback) | The `chrome.storage.local.remove()` call fails with a storage error and the session token remains in storage because the deletion did not complete | The service worker catches a storage API error during the token removal attempt and the token value in `chrome.storage.local` is still non-empty after the failed operation |

## Business Rules

- **Rule sign-out-button-visible-only-when-authenticated:** IF the
    extension popup opens and a valid session token exists in
    `chrome.storage.local` THEN the "Sign out" button is rendered and
    visible in the popup UI — the count of "Sign out" buttons visible
    when no token is present in storage equals 0
- **Rule popup-sends-message-to-service-worker:** IF the user clicks
    the "Sign out" button in the extension popup THEN the popup sends
    a sign-out message to the background service worker via
    `chrome.runtime.sendMessage()` — the count of sign-out messages
    sent to the service worker per "Sign out" click equals 1
- **Rule service-worker-clears-token:** IF the background service
    worker receives a sign-out message from the popup THEN it calls
    `chrome.storage.local.remove()` to delete the session token key
    from storage — the count of session tokens remaining in
    `chrome.storage.local` after a completed sign-out equals 0
- **Rule refresh-timer-cancelled-on-sign-out:** IF the background
    service worker processes a sign-out request THEN it cancels the
    active session refresh timer — the count of active refresh timers
    after sign-out completes equals 0 and no further refresh API
    requests are sent
- **Rule popup-immediately-shows-sign-in-prompt:** IF the session
    token is removed from `chrome.storage.local` during sign-out THEN
    the popup immediately transitions to the unauthenticated state and
    displays a localized sign-in prompt — the count of milliseconds
    from token removal to sign-in prompt visibility equals 1000 or
    fewer
- **Rule web-session-not-affected:** IF the user signs out of the
    extension THEN the web application's session cookies remain
    untouched and the web session continues to be valid — the count of
    web session cookies modified or cleared during extension sign-out
    equals 0
- **Rule no-api-calls-after-sign-out:** IF the extension is in the
    unauthenticated state after sign-out THEN no API calls are sent
    from the extension to the DoCodeGo API until the user signs in
    again — the count of authenticated API requests originating from
    the extension while in the unauthenticated state equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (interacts with the extension popup to view the authenticated state, click the "Sign out" button, and observe the transition to the unauthenticated sign-in prompt after sign-out completes) | Click the "Sign out" button in the extension popup to initiate the sign-out flow, observe the popup transition from authenticated UI to the sign-in prompt, continue using the web application normally after extension sign-out because web session cookies are independent | Cannot directly modify or access the session token stored in `chrome.storage.local` outside the extension UI, cannot cancel the refresh timer without clicking "Sign out", cannot sign out of the web application by signing out of the extension | The user sees the "Sign out" button and authenticated UI when a valid token exists in storage, and sees the localized sign-in prompt after sign-out completes with the authenticated UI hidden |
| Background service worker (receives the sign-out message from the popup, clears the session token from `chrome.storage.local`, and cancels the active session refresh timer to stop automatic token refresh) | Clear the session token from `chrome.storage.local` on receiving a sign-out message, cancel the active refresh timer, send a completion confirmation back to the popup via the extension messaging API | Cannot initiate a sign-out without receiving a message from the popup, cannot modify the web application's session cookies, cannot render or modify the popup UI directly | The service worker has visibility into the stored token value and refresh timer state but has no visibility into the popup rendering state or the web application session state |

## Constraints

- The background service worker clears the session token from
    `chrome.storage.local` within 500 ms of receiving the sign-out
    message from the popup — the count of milliseconds from sign-out
    message receipt to storage deletion completion equals 500 or fewer.
- The popup transitions from the authenticated UI to the localized
    sign-in prompt within 1000 ms of the token being removed from
    `chrome.storage.local` — the count of milliseconds from token
    removal to sign-in prompt visibility equals 1000 or fewer.
- The refresh timer cancellation completes within 100 ms of the
    service worker beginning the sign-out processing — the count of
    milliseconds from sign-out processing start to timer cancellation
    equals 100 or fewer.
- All user-facing text in the popup including the "Sign out" button
    label and the post-sign-out sign-in prompt uses @repo/i18n
    translation keys — the count of hardcoded English strings in the
    popup component tree equals 0.
- The extension sign-out does not send any HTTP requests to the
    DoCodeGo API — the count of API requests originating from the
    extension during the sign-out flow equals 0.
- The total end-to-end sign-out duration from the user clicking
    "Sign out" to the sign-in prompt being fully visible equals 2000
    ms or fewer — the count of milliseconds from button click to
    complete UI transition equals 2000 or fewer.

## Acceptance Criteria

- [ ] The "Sign out" button is visible in the extension popup when a valid session token exists in `chrome.storage.local` — the count of "Sign out" button elements rendered in the popup DOM when a token is present equals 1
- [ ] The "Sign out" button is not visible in the extension popup when no session token exists in `chrome.storage.local` — the count of "Sign out" button elements rendered in the popup DOM when no token is present equals 0
- [ ] Clicking "Sign out" sends a sign-out message from the popup to the background service worker via `chrome.runtime.sendMessage()` — the count of sign-out messages sent per button click equals 1
- [ ] The background service worker clears the session token from `chrome.storage.local` after receiving the sign-out message — the count of session tokens in `chrome.storage.local` after sign-out completion equals 0
- [ ] The background service worker cancels the active session refresh timer during sign-out processing — the count of active refresh timers after sign-out completion equals 0
- [ ] The popup transitions to the unauthenticated state and displays the localized sign-in prompt within 1000 ms of the token being removed from storage — the sign-in prompt element is present within 1000 ms of token removal
- [ ] The authenticated UI elements including user details, quick actions, and the "Sign out" button are removed from the popup DOM after sign-out — the count of authenticated UI components rendered after sign-out completion equals 0
- [ ] The web application session cookies remain unmodified during and after the extension sign-out — the count of web session cookies cleared or modified during extension sign-out equals 0
- [ ] No API requests are sent from the extension to the DoCodeGo API during the sign-out flow — the count of HTTP requests to the DoCodeGo API originating from the extension during sign-out equals 0
- [ ] The "Sign out" button label text is rendered via an @repo/i18n translation key — the count of hardcoded English strings for the "Sign out" button label equals 0
- [ ] The post-sign-out sign-in prompt text is rendered via @repo/i18n translation keys — the count of hardcoded English strings in the sign-in prompt after sign-out equals 0
- [ ] The total end-to-end sign-out duration from button click to visible sign-in prompt equals 2000 ms or fewer — the count of milliseconds from "Sign out" click to sign-in prompt visibility equals 2000 or fewer

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user clicks "Sign out" but the background service worker is terminated by the browser due to inactivity before the sign-out message arrives | The browser restarts the service worker to process the incoming message, the restarted worker clears the token from `chrome.storage.local` and cancels any refresh timer state, and the popup transitions to the sign-in prompt | The count of tokens in `chrome.storage.local` equals 0 after the sign-out completes and the sign-in prompt is visible in the popup |
| The user clicks "Sign out" and immediately closes the popup before the service worker finishes clearing the token from storage | The service worker continues processing the sign-out in the background because it runs independently of the popup lifecycle — the token is cleared from `chrome.storage.local` and the next popup open displays the sign-in prompt | The count of tokens in `chrome.storage.local` equals 0 after the service worker completes and the next popup open renders the sign-in prompt |
| The user double-clicks the "Sign out" button rapidly, causing two sign-out messages to be sent to the service worker in quick succession | The service worker processes the first message and clears the token from `chrome.storage.local` — the second message finds no token to clear and completes without error because `chrome.storage.local.remove()` is idempotent for absent keys | The count of tokens in `chrome.storage.local` equals 0 and no error is logged for the second redundant sign-out message |
| The user signs out of the extension while the web application is open in another tab with an active authenticated session | The web application session remains active and unaffected because the extension token in `chrome.storage.local` is independent of the web session cookies — the user can continue using the web application normally | The web application session cookie is present and valid after extension sign-out and the user can navigate authenticated web pages without interruption |
| The session refresh timer fires at the exact moment the user clicks "Sign out", creating a race between the refresh request and the sign-out processing | The service worker cancels the refresh timer before or after the in-flight refresh request completes — if the refresh response arrives after token clearing, the service worker does not re-store the refreshed token because the sign-out flag takes precedence | The count of tokens in `chrome.storage.local` equals 0 after both the sign-out and the concurrent refresh complete |
| The `chrome.storage.local.remove()` call fails with a storage quota or corruption error during the sign-out attempt | The service worker catches the storage error, logs the failure with the error code and message, and the popup re-reads storage on the next open to determine authentication state — the user retries sign-out or clears extension data manually | The service worker error log contains the storage API error details and the popup displays the authenticated UI because the token remains in storage |

## Failure Modes

- **`chrome.storage.local.remove()` fails during sign-out preventing token deletion from persistent storage**
    - **What happens:** The background service worker receives the sign-out message and calls `chrome.storage.local.remove()` to delete the session token, but the storage API returns an error because the browser's internal storage backend is corrupted, the storage quota is exceeded, or the browser profile's local storage files are damaged.
    - **Source:** Browser profile corruption, disk write errors during the storage deletion operation, or a browser update that corrupted the extension's local storage backend preventing write operations from completing.
    - **Consequence:** The session token remains in `chrome.storage.local` despite the user's intent to sign out, and the next popup open displays the authenticated UI instead of the sign-in prompt because the token is still present in storage.
    - **Recovery:** The service worker catches the storage API error, logs the error type and the storage operation that failed, and the popup falls back to displaying the authenticated UI — the user retries sign-out and if storage remains inaccessible the extension notifies the user to clear extension data from the browser settings to restore storage functionality.

- **Background service worker terminated during sign-out processing before token deletion completes**
    - **What happens:** The browser terminates the background service worker due to memory pressure or an unrelated crash while the service worker is in the middle of processing the sign-out request, after receiving the popup message but before the `chrome.storage.local.remove()` call completes.
    - **Source:** Chromium's service worker lifecycle management terminates the worker under memory pressure, or an unhandled exception in a concurrent event handler causes the worker to crash during the sign-out processing window.
    - **Consequence:** The sign-out is partially processed — the refresh timer state is lost due to the worker termination, but the session token remains in `chrome.storage.local` because the storage deletion did not complete before the crash.
    - **Recovery:** The service worker restarts on the next user interaction, re-reads `chrome.storage.local` to find the token still present, and resumes normal authenticated behavior — the user retries the sign-out by clicking "Sign out" again and the restarted worker completes the token deletion on the second attempt.

- **Popup messaging channel fails preventing the sign-out message from reaching the service worker**
    - **What happens:** The popup calls `chrome.runtime.sendMessage()` to send the sign-out request to the background service worker, but the messaging call fails because the service worker is not registered, the extension context is invalidated during a browser update, or the messaging port is disconnected.
    - **Source:** A concurrent browser extension update invalidates the extension context and disconnects the messaging port between the popup and the service worker, or the service worker registration is in a broken state after a failed extension reload.
    - **Consequence:** The sign-out message never reaches the service worker, the token remains in `chrome.storage.local`, the refresh timer continues running, and the popup remains in the authenticated state because no sign-out processing occurred.
    - **Recovery:** The popup catches the messaging error from the rejected `chrome.runtime.sendMessage()` promise, logs the error details including the disconnection reason, and degrades to displaying an error message instructing the user to close and reopen the popup or reload the extension from the browser extensions page to restore the messaging channel.

## Declared Omissions

- This specification does not define the token relay authentication
    flow that creates the session token in `chrome.storage.local`
    before sign-out — that mechanism is covered by the
    extension-authenticates-via-token-relay specification which handles
    the complete token acquisition lifecycle
- This specification does not cover the session refresh timer logic
    that keeps the token valid during the authenticated state — the
    refresh timer behavior including refresh intervals and API
    interaction is defined in the extension-authenticates-via-token-relay
    specification and this spec only addresses timer cancellation during
    sign-out
- This specification does not address the web application sign-out
    flow that clears session cookies and invalidates server-side
    sessions — web sign-out is defined in the user-signs-out
    specification and operates independently of the extension sign-out
    flow
- This specification does not cover the extension popup's
    authenticated feature set including quick actions, notifications,
    or user detail display — only the sign-out trigger, token removal,
    and transition to the unauthenticated state are in scope for this
    behavioral specification
- This specification does not define the specific @repo/i18n
    translation keys or locale files used for the "Sign out" button
    label or the post-sign-out sign-in prompt — localization key
    definitions and translation workflows are handled by the i18n
    infrastructure specification

## Related Specifications

- [extension-authenticates-via-token-relay](extension-authenticates-via-token-relay.md)
    — defines the token relay authentication flow that creates the
    session token in `chrome.storage.local` which this sign-out spec
    clears, including the refresh timer lifecycle that this spec
    cancels during sign-out
- [user-signs-out](user-signs-out.md) — defines the web application
    sign-out flow that clears session cookies and invalidates
    server-side sessions, confirming that extension sign-out and web
    sign-out operate independently without affecting each other
- [user-installs-browser-extension](user-installs-browser-extension.md)
    — defines the extension installation flow and background service
    worker initialization that establishes the runtime environment in
    which the sign-out messaging and storage operations execute
- [session-lifecycle](session-lifecycle.md) — defines the server-side
    session creation, refresh, and revocation behavior that governs
    the token lifecycle, including the expiry and refresh intervals
    that the extension respects before and after sign-out

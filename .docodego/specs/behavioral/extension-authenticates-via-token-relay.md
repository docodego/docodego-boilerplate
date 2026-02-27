---
id: SPEC-2026-080
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# Extension Authenticates via Token Relay

## Intent

This spec defines how the browser extension authenticates with the
DoCodeGo API using a token relay pattern. Browser extensions run on a
different origin than the web application and cannot access the API's
session cookies directly. Instead of implementing a separate
authentication flow, the extension delegates sign-in to the web
application and receives the resulting session token via
`chrome.runtime.sendMessage()`. When the user clicks the localized
"Sign in" button in the extension popup, the popup opens a new browser
tab pointing to the web application's sign-in page. The user
completes authentication through any standard method — email OTP,
passkey, or SSO. After the web application confirms a successful
sign-in, it sends the session token to the extension's background
service worker via `chrome.runtime.sendMessage()`. The service worker
stores the token in `chrome.storage.local`, which persists across
browser restarts. All subsequent API calls from the extension route
through the background service worker, which attaches the token as an
authorization header using the same oRPC client and typed contracts
from `@repo/contracts`. The service worker runs a session refresh
timer to keep the token valid. If a refresh fails because the session
was revoked server-side, the stored token is cleared and the popup
reverts to the sign-in prompt. Signing out from the extension clears
the token and cancels the refresh timer without affecting the user's
web session.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Extension popup UI (renders the "Sign in" button when unauthenticated and displays authenticated state with user context when a valid token exists in storage) | read/write | When the user opens the extension popup, the popup reads `chrome.storage.local` to determine authentication state and renders either the sign-in prompt or the authenticated view | The popup fails to render due to a browser extension framework error and the user cannot initiate sign-in or view authenticated content — the user falls back to closing and reopening the popup to trigger a fresh render cycle |
| Web application sign-in page (the standard `/signin` page that handles email OTP, passkey, and SSO authentication flows for all DoCodeGo users) | read/write | When the popup opens a new browser tab to the web application's sign-in URL, the user completes the full authentication flow in the web application context | The web application is unreachable due to network failure or server downtime and the user cannot complete authentication — the extension popup remains in the unauthenticated state and the user retries by clicking "Sign in" again after connectivity is restored |
| `chrome.runtime.sendMessage()` API (browser messaging API that enables the web application page to send the session token to the extension's background service worker after successful authentication) | write | After the web application confirms a successful sign-in, the web application page calls `chrome.runtime.sendMessage()` with the extension ID and the session token payload | The messaging call fails because the extension is not installed, the extension ID is incorrect, or the browser blocks cross-origin messaging — the web application logs the send failure and the user falls back to retrying sign-in from the extension popup |
| Background service worker (long-running extension script that receives tokens via `chrome.runtime.sendMessage()`, stores them, attaches authorization headers to API requests, and manages the session refresh timer) | read/write | On every token receipt from the web application, on every API request that requires authentication, and on every refresh timer tick to extend the session before expiry | The service worker is terminated by the browser due to inactivity or memory pressure and restarts on the next event — the restarted worker reads the token from `chrome.storage.local` and resumes the refresh timer without requiring user re-authentication |
| `chrome.storage.local` (browser extension storage API that persists key-value data across browser sessions and restarts, used to store the session token for the extension) | read/write | When the service worker receives a token and stores it, when the popup reads the token to determine auth state, and when sign-out clears the token from storage | The storage API call fails due to a browser storage quota exceeded error or a corrupted storage state — the service worker logs the storage failure and the popup falls back to displaying the sign-in prompt because no valid token is found |
| `@repo/contracts` oRPC typed contracts (shared API type definitions that define the request and response shapes for all DoCodeGo API endpoints used by both the web application and the extension) | read | When the background service worker constructs API requests using the oRPC client, the contracts provide compile-time type checking and runtime request/response validation | The contracts package fails to resolve at build time due to a missing workspace dependency — the build fails with a TypeScript compilation error and CI alerts to block deployment of the extension |

## Behavioral Flow

1. **[User]** opens the extension popup and sees the localized "Sign
    in" button because no valid token exists in `chrome.storage.local`
    — all popup text is rendered via @repo/i18n translation keys

2. **[User]** clicks the "Sign in" button in the extension popup to
    initiate the authentication flow via the web application

3. **[Popup]** calls `chrome.tabs.create()` to open a new browser tab
    pointing to the DoCodeGo web application's `/signin` page with a
    query parameter identifying the request as an extension-initiated
    sign-in

4. **[User]** completes authentication on the web application's
    `/signin` page using any of the standard methods — email OTP,
    passkey, or SSO — following the existing web authentication flows

5. **[WebApp]** confirms the sign-in is successful and detects the
    extension-initiated query parameter, then calls
    `chrome.runtime.sendMessage()` with the extension ID and a payload
    containing the session token to relay the credentials to the
    extension's background service worker

6. **[ServiceWorker]** receives the message via the
    `chrome.runtime.onMessageExternal` listener, validates that the
    message contains a non-empty session token string, and stores the
    token in `chrome.storage.local` under a dedicated key

7. **[ServiceWorker]** starts a session refresh timer that fires at a
    fixed interval before the token's expiry window to send a refresh
    request to the DoCodeGo API and replace the stored token with the
    refreshed value

8. **[Popup]** detects the token presence in `chrome.storage.local`
    via the `chrome.storage.onChanged` listener and transitions from
    the sign-in prompt to the authenticated state view showing the
    user's context information

9. **[User]** can close the web application sign-in tab at this point
    because the token has been relayed and stored — the extension
    operates independently of the web application tab from this point

10. **[ServiceWorker]** attaches the stored token as an `Authorization`
    header on every API request sent through the oRPC client configured
    with `@repo/contracts` typed contracts, ensuring all extension API
    calls are authenticated

11. **[ServiceWorker]** the refresh timer fires and sends a refresh
    request to the DoCodeGo API — if the API returns a new token, the
    service worker replaces the stored token in `chrome.storage.local`
    with the refreshed value and resets the timer

12. **[ServiceWorker]** if the refresh request fails because the
    session was revoked server-side or the token is expired, the
    service worker clears the token from `chrome.storage.local` and
    cancels the refresh timer

13. **[Popup]** detects the token removal via the
    `chrome.storage.onChanged` listener and reverts to displaying the
    "Sign in" prompt in the unauthenticated state

14. **[User]** clicks "Sign out" in the extension popup to end the
    authenticated session from the extension

15. **[ServiceWorker]** receives the sign-out request from the popup,
    clears the token from `chrome.storage.local`, and cancels the
    active refresh timer — the sign-out does not send a revocation
    request to the API and does not affect the user's web session

16. **[Popup]** detects the token removal and immediately transitions
    to the unauthenticated state, displaying the "Sign in" prompt
    again for the user

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| unauthenticated | awaiting_web_sign_in | The user clicks the "Sign in" button in the extension popup and a new browser tab opens to the web application's `/signin` page | The popup has no valid token in `chrome.storage.local` and the browser tab creation call completes without error |
| awaiting_web_sign_in | authenticated | The background service worker receives the session token via `chrome.runtime.onMessageExternal` from the web application and stores it in `chrome.storage.local` | The received message payload contains a non-empty session token string that passes validation |
| awaiting_web_sign_in | unauthenticated | The user closes the web application sign-in tab without completing authentication, or the token relay message fails to arrive within 300 seconds of opening the tab | The `chrome.storage.local` still contains no valid token after the timeout or tab closure event |
| authenticated | authenticated (refreshed) | The session refresh timer fires and the API returns a new token value that replaces the stored token in `chrome.storage.local` | The refresh API request returns HTTP 200 with a non-empty token in the response body |
| authenticated | unauthenticated | The session refresh timer fires but the API rejects the refresh request because the session was revoked server-side or the token has expired | The refresh API request returns HTTP 401 indicating the session is no longer valid |
| authenticated | unauthenticated | The user clicks "Sign out" in the extension popup, triggering the service worker to clear the token from `chrome.storage.local` and cancel the refresh timer | The user explicitly initiates the sign-out action from the popup UI |

## Business Rules

- **Rule extension-cannot-access-session-cookies:** IF the browser
    extension attempts to access the DoCodeGo API THEN it cannot use
    session cookies because the extension runs on a different origin
    than the web application — the count of API requests using session
    cookies from the extension equals 0
- **Rule popup-opens-web-tab-for-sign-in:** IF the user clicks "Sign
    in" in the extension popup THEN the popup opens a new browser tab
    to the web application's `/signin` page — the count of new tabs
    opened per sign-in click equals 1
- **Rule web-app-sends-token-via-message:** IF the web application
    confirms a successful sign-in with the extension query parameter
    present THEN it calls `chrome.runtime.sendMessage()` with the
    extension ID and the session token payload — the count of message
    send calls per successful sign-in equals 1
- **Rule service-worker-stores-token:** IF the background service
    worker receives a valid token message via
    `chrome.runtime.onMessageExternal` THEN it stores the token in
    `chrome.storage.local` under the dedicated key — the count of
    storage write operations per received token equals 1
- **Rule token-persists-across-restarts:** IF the user closes and
    reopens the browser THEN the token stored in
    `chrome.storage.local` remains available to the service worker —
    the token value after browser restart equals the token value
    stored before the restart
- **Rule api-calls-attach-token-header:** IF the background service
    worker sends an API request through the oRPC client THEN it
    attaches the stored token as an `Authorization` header on the
    request — the count of authenticated API requests missing the
    `Authorization` header equals 0
- **Rule refresh-timer-keeps-token-valid:** IF the extension is in
    the authenticated state THEN the background service worker runs
    a refresh timer that sends a refresh request to the API before
    the token expires — the count of active refresh timers per
    authenticated session equals 1
- **Rule refresh-failure-clears-token:** IF the session refresh
    request returns HTTP 401 indicating the session is revoked or
    expired THEN the service worker clears the token from
    `chrome.storage.local` and cancels the refresh timer — the count
    of tokens remaining in storage after a failed refresh equals 0
- **Rule sign-out-clears-token-not-web-session:** IF the user clicks
    "Sign out" in the extension popup THEN the service worker clears
    the token from `chrome.storage.local` and cancels the refresh
    timer without sending a session revocation request to the API —
    the count of API revocation requests sent during extension
    sign-out equals 0 and the web session remains unaffected

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| User (interacts with the extension popup to initiate sign-in via the web application, view authenticated state, and sign out from the extension independently of the web session) | Click "Sign in" to open the web application sign-in page in a new tab, complete authentication via email OTP or passkey or SSO on the web application, view authenticated extension state after token relay, click "Sign out" to clear the extension token and revert to unauthenticated state | Cannot modify the extension ID used for `chrome.runtime.sendMessage()`, cannot directly access or edit the token stored in `chrome.storage.local` outside the extension UI, cannot bypass the token relay by manually injecting a token into the extension | The user sees the "Sign in" button when unauthenticated, sees authenticated context after token relay completes, and sees the sign-in prompt again after sign-out or refresh failure |
| Background service worker (receives tokens from the web application via `chrome.runtime.onMessageExternal`, stores tokens in `chrome.storage.local`, attaches authorization headers to API requests, and manages the session refresh timer lifecycle) | Receive and validate token messages from the web application, store and retrieve tokens from `chrome.storage.local`, attach the `Authorization` header to all outgoing API requests via the oRPC client, start and cancel the session refresh timer, clear the token on refresh failure or user sign-out | Cannot initiate the web application sign-in flow, cannot modify the web application's session or cookies, cannot bypass the `@repo/contracts` typed contracts when constructing API requests | The service worker has visibility into the stored token value, the refresh timer state, and the API response status codes for refresh requests but has no visibility into the web application's session state |
| Web application (sends the session token to the extension via `chrome.runtime.sendMessage()` after the user completes authentication on the standard sign-in page) | Call `chrome.runtime.sendMessage()` with the extension ID and session token payload after confirming a successful sign-in with the extension query parameter present | Cannot access the extension's `chrome.storage.local`, cannot modify the extension's service worker state, cannot trigger the extension's refresh timer or sign-out flow | The web application has visibility into the session token it generated and the extension ID it targets but has no visibility into whether the extension received or stored the token |

## Constraints

- The `chrome.runtime.sendMessage()` call from the web application to
    the extension service worker completes within 2000 ms of the web
    application confirming the sign-in — the count of milliseconds from
    sign-in confirmation to message delivery equals 2000 or fewer.
- The background service worker stores the received token in
    `chrome.storage.local` within 500 ms of receiving the message — the
    count of milliseconds from message receipt to storage write
    completion equals 500 or fewer.
- The popup transitions from the unauthenticated sign-in prompt to the
    authenticated state view within 1000 ms of the token being written
    to `chrome.storage.local` — the count of milliseconds from storage
    write to UI state change equals 1000 or fewer.
- The session refresh timer fires at an interval that is at least 60
    seconds before the token's expiry time — the count of seconds
    between the refresh timer fire and the token expiry equals 60 or
    more, ensuring the token is refreshed before it becomes invalid.
- All user-facing text in the extension popup including the "Sign in"
    button label, authenticated state display, and "Sign out" button
    label uses @repo/i18n translation keys — the count of hardcoded
    English strings in the popup component equals 0.
- The extension uses `@repo/contracts` oRPC typed contracts for all
    API requests through the background service worker — the count of
    API requests constructed without `@repo/contracts` type definitions
    equals 0.

## Acceptance Criteria

- [ ] Clicking "Sign in" in the extension popup opens a new browser tab to the web application's `/signin` page — the count of new tabs created per sign-in click equals 1
- [ ] The web application calls `chrome.runtime.sendMessage()` with the extension ID and session token after successful sign-in with the extension query parameter present — the count of message send calls equals 1
- [ ] The background service worker receives the token via `chrome.runtime.onMessageExternal` and stores it in `chrome.storage.local` — the stored token value is non-empty after the relay completes
- [ ] The token stored in `chrome.storage.local` persists across browser restarts — the token value after restart equals the token value stored before the restart
- [ ] All API requests from the extension include the `Authorization` header with the stored token — the count of API requests missing the `Authorization` header equals 0
- [ ] The oRPC client in the background service worker uses `@repo/contracts` typed contracts for all API requests — the count of untyped API calls equals 0
- [ ] The session refresh timer starts when the extension enters the authenticated state — the count of active refresh timers in the authenticated state equals 1
- [ ] When the refresh API request returns HTTP 200 the service worker replaces the stored token with the refreshed value — the stored token value after refresh is non-empty and differs from the previous value
- [ ] When the refresh API request returns HTTP 401 the service worker clears the token from `chrome.storage.local` and cancels the refresh timer — the count of tokens in storage after a 401 refresh response equals 0
- [ ] The popup reverts to the "Sign in" prompt when the token is cleared from `chrome.storage.local` after a refresh failure — the sign-in button is present and visible within 1000 ms of token removal
- [ ] Clicking "Sign out" clears the token from `chrome.storage.local` and cancels the refresh timer — the count of tokens in storage after sign-out equals 0 and the count of active refresh timers equals 0
- [ ] Signing out from the extension does not send a session revocation request to the API — the count of API revocation requests during extension sign-out equals 0
- [ ] The popup displays the unauthenticated "Sign in" prompt when no valid token exists in `chrome.storage.local` — the sign-in button is present when the popup opens with no stored token
- [ ] All popup UI text is rendered via @repo/i18n translation keys — the count of hardcoded English strings in the extension popup components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user clicks "Sign in" in the extension popup but closes the web application sign-in tab before completing authentication without relaying a token | The extension popup remains in the unauthenticated state because no token message arrives at the service worker, and the user can click "Sign in" again to open a fresh sign-in tab | The count of tokens in `chrome.storage.local` equals 0 after the tab is closed and the "Sign in" button is present in the popup |
| The user completes sign-in on the web application but the extension is uninstalled before `chrome.runtime.sendMessage()` is called by the web page | The `chrome.runtime.sendMessage()` call throws a "Could not establish connection" error because the extension is absent, and the web application catches the error and logs the failure without affecting the user's web session | The web application's error log contains an entry with the extension ID and the connection error message and the web session remains valid |
| The browser terminates the background service worker due to inactivity while a valid token exists in `chrome.storage.local` and the user opens the popup | The service worker restarts on the popup open event, reads the token from `chrome.storage.local`, re-establishes the session refresh timer, and the popup displays the authenticated state without requiring re-authentication | The popup shows the authenticated view within 2000 ms of opening and the refresh timer count equals 1 after the service worker restarts |
| Two `chrome.runtime.sendMessage()` calls arrive at the service worker in rapid succession because the user completed sign-in in two tabs simultaneously | The service worker processes both messages sequentially and the last-write-wins strategy applies to `chrome.storage.local` — the stored token equals the value from the second message and exactly 1 refresh timer is active | The count of tokens in `chrome.storage.local` equals 1 and the count of active refresh timers equals 1 after both messages are processed |
| The user signs out from the web application while the extension holds a valid token and the refresh timer has not yet fired to detect the revocation | The extension continues to use the stored token for API requests until the next refresh timer fires, at which point the API returns HTTP 401 and the service worker clears the token and reverts the popup to the sign-in prompt | The count of tokens in `chrome.storage.local` equals 0 after the first refresh attempt following the web session revocation and the popup displays the sign-in button |
| The `chrome.storage.local` quota is exceeded when the service worker attempts to store the token after receiving it from the web application | The service worker catches the quota exceeded error from the storage write operation, logs the error with the current storage usage in bytes, and the popup remains in the unauthenticated state because no valid token is stored | The error log contains a quota exceeded entry and the popup displays the "Sign in" button because `chrome.storage.local` contains no valid token |

## Failure Modes

- **Token relay message fails to reach the service worker after web sign-in completes**
    - **What happens:** The web application calls `chrome.runtime.sendMessage()` after confirming a successful sign-in, but the message never arrives at the extension's background service worker because the extension ID is misconfigured, the extension was disabled between the sign-in initiation and completion, or the browser blocked the cross-origin message.
    - **Source:** Misconfigured extension ID in the web application's relay script, the user disabling the extension while the sign-in tab was open, or a browser security policy blocking `chrome.runtime.sendMessage()` calls from the web application origin.
    - **Consequence:** The user completed authentication on the web application but the extension remains in the unauthenticated state with no stored token, and the user sees the "Sign in" prompt when they return to the popup despite having signed in on the web.
    - **Recovery:** The web application logs the message send failure with the extension ID and the error details, and the user falls back to clicking "Sign in" in the extension popup again to open a new sign-in tab and retry the entire authentication and token relay flow.

- **Session refresh request fails because the server revoked the session externally**
    - **What happens:** The background service worker sends a refresh request to the DoCodeGo API when the refresh timer fires, but the API returns HTTP 401 because an administrator revoked the user's session from the server-side admin panel, or the user revoked all sessions from the web application's security settings.
    - **Source:** Server-side session revocation initiated by an administrator, the user revoking all sessions from the web application's session management page, or an automated security policy that invalidates sessions after detecting suspicious activity.
    - **Consequence:** The extension's stored token is no longer valid and all subsequent API requests from the extension will fail with HTTP 401 until the user re-authenticates through the token relay flow.
    - **Recovery:** The service worker detects the HTTP 401 response, clears the invalid token from `chrome.storage.local`, cancels the refresh timer, and the popup degrades to displaying the "Sign in" prompt so the user can re-authenticate through the web application.

- **`chrome.storage.local` becomes corrupted or inaccessible preventing token persistence**
    - **What happens:** The service worker attempts to read or write the token from `chrome.storage.local` but the storage API returns an error because the storage data is corrupted, the storage quota is exceeded, or the browser profile's local storage files are damaged.
    - **Source:** Browser profile corruption, disk write errors during a previous storage operation, storage quota exhaustion from other extensions or data stored by the same extension, or a browser update that reset or corrupted the extension's local storage.
    - **Consequence:** The service worker cannot store a new token received via the relay, cannot read an existing token to attach authorization headers to API requests, and the extension falls back to the unauthenticated state regardless of whether the user completed sign-in.
    - **Recovery:** The service worker catches the storage API error, logs the error type and the storage operation that failed, and the popup falls back to displaying the "Sign in" prompt — the user retries sign-in and if storage remains inaccessible the extension notifies the user to clear extension data or reinstall the extension to restore storage functionality.

- **Background service worker terminated by the browser during an active refresh cycle**
    - **What happens:** The browser terminates the background service worker due to inactivity or memory pressure while the refresh timer is counting down, and the timer is lost because service workers do not persist in-memory timers across restarts.
    - **Source:** Chromium's service worker lifecycle management that terminates idle service workers after 30 seconds of inactivity or when the browser reclaims memory under resource pressure conditions.
    - **Consequence:** The refresh timer is cancelled by the termination and the token in `chrome.storage.local` is not refreshed before expiry, potentially leading to an expired token that fails on the next API request attempt.
    - **Recovery:** The service worker re-reads the token from `chrome.storage.local` on restart, recalculates the time until expiry, and restarts the refresh timer — if the token has already expired the service worker clears it from storage and the popup degrades to the unauthenticated sign-in prompt.

## Declared Omissions

- This specification does not define the web application's sign-in UI or authentication flow logic for email OTP, passkey, or SSO — those flows are defined in their respective specifications and this spec only covers the token relay handoff after authentication completes
- This specification does not address the extension popup's authenticated feature set such as quick actions, notifications, or content display — only the authentication state transitions and token management lifecycle are covered here
- This specification does not define the oRPC client configuration or API endpoint definitions used by the extension — the shared contracts and client setup are defined in `@repo/contracts` and the API framework specification respectively
- This specification does not cover the extension's content script behavior or interaction with web page content — only the popup UI and background service worker authentication flow are in scope for this token relay specification
- This specification does not address rate limiting on the token relay message endpoint or the refresh API endpoint — rate limiting behavior is handled by the API framework and is defined in the api-framework foundation specification

## Related Specifications

- [session-lifecycle](session-lifecycle.md) — defines the session
    creation, refresh, and revocation behavior that governs the token
    lifecycle on the server side, including the expiry and refresh
    intervals that the extension's refresh timer must respect
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) —
    defines one of the three authentication methods the user completes
    on the web application's `/signin` page before the token is relayed
    to the extension via `chrome.runtime.sendMessage()`
- [user-signs-in-with-passkey](user-signs-in-with-passkey.md) —
    defines the passkey authentication method that the user can complete
    on the web application's `/signin` page as an alternative to email
    OTP or SSO before the token relay occurs
- [user-signs-in-with-sso](user-signs-in-with-sso.md) — defines the
    SSO authentication method available on the web application's
    `/signin` page, representing the third supported sign-in method
    that triggers the token relay to the extension after completion
- [user-signs-out](user-signs-out.md) — defines the web application
    sign-out behavior that is independent of the extension sign-out
    flow, confirming that extension sign-out does not affect the web
    session and vice versa

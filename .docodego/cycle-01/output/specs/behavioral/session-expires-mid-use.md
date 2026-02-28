---
id: SPEC-2026-020
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: approved
roles: [Authenticated User]
---

[← Back to Roadmap](../ROADMAP.md)

# Session Expires Mid-Use

## Intent

This spec defines the behavior when a user's session expires while they are actively using the application or have the application open in the background. After 7 days without a session refresh, the session token becomes invalid and the next API call returns HTTP 401. The client detects the 401, displays a localized notification informing the user that their session has expired, captures the current URL path as a return URL, and redirects to `/signin`. After successful re-authentication, the user is navigated back to the captured return URL. On the desktop app, if the expiry is detected during a background refetch while the app is not focused, an OS-native notification is sent. This spec ensures the user experience is clear, preserves navigation context, and handles both foreground and background expiry detection.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth (API server) | read | Every API request that includes a session token | The server returns HTTP 500 and the client falls back to the generic error handler without triggering session expiry logic |
| TanStack Query (client) | read/write | Every API call and background refetch across all platform targets | If the query client is misconfigured, the global 401 interceptor is absent and session expiry goes undetected until manual page reload |
| `@repo/i18n` | read | When the session-expired notification is displayed to the user | The notification text falls back to the default English locale string so the message remains readable but untranslated |
| Tauri notification plugin | write | When the desktop app detects 401 during a background refetch while the app window is not focused | The OS-native notification call fails silently and the system falls back to setting an in-app badge or visual indicator on the system tray icon |
| Client-side router | write | When the client redirects to `/signin` after detecting session expiry and after re-authentication completes | If the router is unavailable, the client falls back to a full page navigation via `window.location` to reach the sign-in page |

## Behavioral Flow

1. **[Server]** Sessions have a 7-day expiry window that refreshes automatically when the user is active. If the user leaves a browser tab or desktop app open without interacting for more than 7 days, the session expires on the server. The client still holds the session cookie, but the token it contains is no longer valid. The user is unaware that anything has changed — the UI looks exactly as they left it.
2. **[Server]** When the user returns and performs any action that triggers an API call — navigating to a new page, refreshing data, submitting a form — the server evaluates the session token attached to the request. It finds no matching active session in the `session` table (or finds one whose `expiresAt` timestamp has passed) and responds with a `401 Unauthorized` status.
3. **[Client]** The client's API layer intercepts the 401 response. Rather than displaying a generic error or silently failing, it recognizes this as a session expiration event. The client displays a localized toast notification or modal dialog informing the user that their session has expired and they need to sign in again. The message is clear and non-technical — for example "Your session has expired. Please sign in to continue."
4. **[Client]** After the user acknowledges the notification, the client redirects them to the sign-in page. Before redirecting, the client captures the current URL path and preserves it as a return URL parameter. This ensures the user does not lose their place — after signing in successfully through any of the standard methods (email OTP, passkey, or SSO), they are navigated back to the exact page they were on before the session expired.
5. **[Client]** Any unsaved work in progress at the time of the 401 — a half-filled form, a draft in a text field — is lost unless the client has persisted it locally. The session expiration notification appears before the page is torn down, giving the user a moment to note their context. The application does not attempt to queue or retry the failed request after re-authentication. The user starts fresh on the restored page.
6. **[Desktop app — Tauri]** On the desktop app, session expiry detection works the same way — the client intercepts the 401 and displays an in-app toast or modal. Additionally, if the app is not in the foreground when the expiration is detected (for example, a background TanStack Query refetch triggers the 401 while the user is in another application), the desktop app sends an OS-native notification informing the user that their session has expired. Clicking the notification brings the app to the foreground and navigates to the sign-in page. When the app is already focused, the native notification is suppressed and only the in-app toast appears.

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| Authenticated | Session Expired (detected) | API call returns HTTP 401 with session-expired error code | The debounce flag is not already set from a prior 401 in the same cycle |
| Session Expired (detected) | Notification Shown | 401 handler fires notification display | The debounce flag prevents duplicate notifications — only the first 401 triggers display |
| Notification Shown | Redirecting to Sign-In | Client router captures return URL and initiates redirect to `/signin` | The return URL contains only pathname and search parameters with 0 protocol or hostname segments |
| Redirecting to Sign-In | Awaiting Re-Authentication | The `/signin` page loads and the user is presented with sign-in options | The `returnUrl` query parameter is present in the URL or the handler falls back to `/app` |
| Awaiting Re-Authentication | Re-Authenticated (restored) | The user completes sign-in via email OTP, passkey, or SSO | Authentication succeeds and a new valid session token is issued by the server |
| Re-Authenticated (restored) | Returned to Original Page | The sign-in handler reads `returnUrl` and navigates the user to the captured path | The `returnUrl` parameter is present and passes validation as a relative path |

## Business Rules

- **Rule (single-401-processing):** IF a 401 session-expired response is received AND the debounce flag is already set from a previous 401 in the same processing cycle THEN the duplicate 401 is silently ignored and logged, and no additional notification or redirect is triggered
- **Rule (desktop-notification-routing):** IF the platform is Tauri desktop AND the app window is not in the foreground at the time the 401 is detected THEN an OS-native notification is sent via `tauri-plugin-notification` instead of the in-app toast, and the count of in-app toasts shown equals 0
- **Rule (desktop-foreground-suppression):** IF the platform is Tauri desktop AND the app window is in the foreground at the time the 401 is detected THEN only the in-app toast is shown and the count of OS-native notifications sent equals 0
- **Rule (return-url-safety):** IF the captured return URL contains a protocol or hostname segment THEN the return URL is rejected and the sign-in handler falls back to the default `/app` redirect to prevent open redirect attacks
- **Rule (no-request-replay):** IF session expiry is detected and the user re-authenticates THEN the client does not retry or queue the original failed API request — the user starts fresh on the restored page with 0 queued or retried requests

## Permission Model

Single role; no permission model is needed because all authenticated users experience the same session expiry behavior regardless of their role or permission level.

## Acceptance Criteria

- [ ] When the server receives a request with an expired session token, it returns HTTP 401 — the response status code equals 401 and no session refresh occurs
- [ ] The client's API layer intercepts the 401 response and identifies it as a session expiration event — the interception handler is present in the API client configuration
- [ ] The client displays a localized toast notification or modal dialog informing the user that their session has expired — the notification element is present and visible after the 401 is received
- [ ] The notification message is non-technical and translated — the text is rendered via an i18n translation key and the count of hardcoded English strings in the notification equals 0
- [ ] Before redirecting, the client captures the current URL path and stores it as a return URL parameter — the return URL parameter is present in the redirect to `/signin`
- [ ] After the notification, the client redirects to `/signin` — the redirect is present and the window location pathname changes to `/signin`
- [ ] After successful re-authentication, the client navigates the user back to the captured return URL — the return URL is present in the navigation and the user lands on the original page
- [ ] The return URL redirect works for all 3 sign-in methods (email OTP, passkey, SSO) — the return URL parameter is present and applied after authentication completes via each method
- [ ] On the desktop app (Tauri), when the 401 is detected during a background TanStack Query refetch while the app is not in the foreground, an OS-native notification is sent — the notification call via `tauri-plugin-notification` is present in the background expiry handler
- [ ] On the desktop app, clicking the OS-native notification brings the app to the foreground and navigates to `/signin` — the window focus and navigation calls are both present in the notification click handler
- [ ] On the desktop app, when the 401 is detected while the app is already in the foreground, the OS-native notification is suppressed and only the in-app toast appears — the count of OS-native notifications sent when the app is focused equals 0
- [ ] Unsaved work in progress (form data, draft text) is not preserved across the session expiry redirect — the count of queued or retried requests after re-authentication equals 0
- [ ] The session expiry interception handles all API call origins (page navigation, data refresh, form submission) — the 401 handler is present at the global API client level, not per-route

## Constraints

- The 401 interception is global and applies to all API calls — the handler is configured once in the API client (TanStack Query's global `onError` or a fetch interceptor), not duplicated per route or component. The count of per-route 401 handling implementations equals 0.
- The return URL captures only the pathname and search parameters, not the full URL with origin — the return URL parameter contains 0 protocol or hostname segments. This prevents open redirect vulnerabilities where an attacker could inject an external URL as the return destination.
- The client does not retry or queue the failed API request after re-authentication — the user starts fresh on the restored page. The count of automatic request retry mechanisms triggered by session expiry 401 responses equals 0.
- The OS-native notification on desktop is sent only when the app is not in the foreground — this prevents duplicate notifications (in-app toast plus OS notification) when the user is actively using the app. The foreground detection uses the Tauri window focus state.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user has multiple browser tabs open with active sessions and the session expires across all of them simultaneously | Each tab independently detects the 401 on its next API call and redirects to `/signin` with its own return URL — there is no cross-tab coordination or conflict | Each tab's URL changes to `/signin` with a `returnUrl` parameter matching that tab's original pathname |
| The return URL contains special characters such as query parameters and encoded segments that must survive the redirect round-trip | The client URL-encodes the return URL before appending it as a query parameter, and the sign-in page decodes it correctly after re-authentication | The decoded return URL after re-authentication matches the original captured URL character-for-character |
| The session expires while the user is on the `/signin` page itself, causing a redundant redirect loop back to `/signin` | The 401 handler detects that the current pathname is already `/signin` and suppresses the redirect and notification to avoid an infinite loop | The count of redirect attempts when the current page is `/signin` equals 0 |
| The user's network connection is lost at the same moment the session expires, and API calls fail with a network error instead of HTTP 401 | The client treats network errors and 401 responses as distinct failure types — network errors trigger the offline error handler, not the session expiry handler | The session expiry notification is absent when the failure is a network error, and the offline indicator is present instead |
| The `returnUrl` query parameter is tampered with to contain an absolute URL pointing to an external domain such as `https://evil.com/steal` | The sign-in page validates that the return URL is a relative path with 0 protocol or hostname segments, rejects the tampered value, and falls back to `/app` | The navigation target after re-authentication equals `/app` and the external URL is never loaded |
| The desktop app receives a 401 during a background refetch but the `tauri-plugin-notification` API call throws a permission-denied error because the user disabled OS notifications | The notification error is caught and the system falls back to setting an in-app badge or visual indicator on the system tray icon, and logs the notification permission status | The system tray badge or visual indicator is present and the error log entry contains the notification permission status |

## Failure Modes

- **Return URL lost during redirect**
    - **What happens:** The client captures the return URL but a code error or browser extension strips the query parameter during the redirect to `/signin`, causing the user to land on `/app` instead of their original page after re-authentication.
    - **Source:** Code defect in the redirect logic or interference from a third-party browser extension that modifies URL parameters.
    - **Consequence:** The user loses their navigation context and is redirected to the default `/app` dashboard instead of the page they were working on before session expiry.
    - **Recovery:** The sign-in page validates the return URL parameter on load and if it is absent, falls back to the default `/app` redirect and logs a warning that the return URL was missing for diagnostics.
- **Multiple 401 responses trigger duplicate notifications and redirects**
    - **What happens:** Several concurrent API calls all return 401 simultaneously (TanStack Query fires multiple refetches in parallel), causing the client to process multiple session expiry events and attempt multiple redirect navigations.
    - **Source:** Normal application behavior where multiple data-fetching queries are active at the same time and all fail when the session expires.
    - **Consequence:** The user sees multiple notification toasts stacked on screen and the router receives conflicting redirect instructions, potentially causing navigation errors.
    - **Recovery:** The client's 401 handler uses a boolean debounce flag to ensure only the first 401 triggers the notification and redirect, and subsequent 401 responses within the same cycle are silently ignored — the handler logs each suppressed duplicate for diagnostics.
- **Desktop notification fails to send due to permission denial**
    - **What happens:** The `tauri-plugin-notification` API call fails because the user has disabled OS notifications for the application in their system settings, and the background session expiry goes unnoticed until the user returns to the app.
    - **Source:** User-configured OS-level notification permissions that block the desktop application from sending native notifications.
    - **Consequence:** The user is unaware that their session has expired while the app is in the background, and discovers the expiry only when they bring the app to the foreground.
    - **Recovery:** The notification call catches the error and falls back to setting an in-app badge or visual indicator on the system tray icon, and logs the notification permission status for diagnostics.
- **Session refresh race condition between concurrent requests**
    - **What happens:** A session is within seconds of expiring when two requests arrive simultaneously — one triggers a refresh that extends the session while the other hits the old `expiresAt` and returns 401, causing the client to show the expiry notification even though the session was just refreshed.
    - **Source:** Timing race between the session refresh mechanism and a concurrent API request that evaluates the session token before the refresh takes effect.
    - **Consequence:** The user is incorrectly shown a session expiry notification and redirected to `/signin` even though their session is still valid after the refresh completes.
    - **Recovery:** The 401 handler retries the failed request once before showing the notification, and if the retry succeeds (because the refresh has taken effect), the expiry notification is suppressed — this single retry prevents false positives from timing races.

## Declared Omissions

- This specification does not address session creation, token issuance, or automatic session refresh mechanics, which are covered by `session-lifecycle.md` in the foundation specs
- This specification does not address the session management user interface for manually revoking active sessions, which is covered by `user-manages-sessions.md`
- This specification does not address desktop notification configuration, permission prompts, or notification channel setup, which are covered by `desktop-sends-a-notification.md`
- This specification does not address the sign-in flow after the user is redirected to `/signin`, which is covered by the individual sign-in method specs (email OTP, passkey, SSO)
- This specification does not address offline detection or network error handling, which is treated as a separate failure mode from session expiry across all platform targets

## Related Specifications

- [session-lifecycle](session-lifecycle.md) — Defines session creation, automatic refresh mechanics, and the 7-day expiration policy that triggers the mid-use expiry behavior
- [user-manages-sessions](user-manages-sessions.md) — Covers the user-facing session management UI for viewing active sessions and manually revoking them
- [desktop-sends-a-notification](desktop-sends-a-notification.md) — Covers OS-native notification infrastructure, permission handling, channel configuration, and permission prompts for the Tauri desktop app
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — Defines the email OTP sign-in flow that handles the `returnUrl` parameter after session expiry re-authentication
- [user-signs-in-with-passkey](user-signs-in-with-passkey.md) — Defines the passkey sign-in flow that handles the `returnUrl` parameter after session expiry re-authentication

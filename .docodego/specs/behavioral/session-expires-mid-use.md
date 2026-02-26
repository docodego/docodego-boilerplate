[← Back to Roadmap](../ROADMAP.md)

# Session Expires Mid-Use

## Intent

This spec defines the behavior when a user's session expires while they are actively using the application or have the application open in the background. After 7 days without a session refresh, the session token becomes invalid and the next API call returns HTTP 401. The client detects the 401, displays a localized notification informing the user that their session has expired, captures the current URL path as a return URL, and redirects to `/signin`. After successful re-authentication, the user is navigated back to the captured return URL. On the desktop app, if the expiry is detected during a background refetch while the app is not focused, an OS-native notification is sent. This spec ensures the user experience is clear, preserves navigation context, and handles both foreground and background expiry detection.

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

- The 401 interception is global and applies to all API calls — the handler is configured once in the API client (e.g., TanStack Query's global `onError` or an Axios/fetch interceptor), not duplicated per route or component. The count of per-route 401 handling implementations equals 0.
- The return URL captures only the pathname and search parameters, not the full URL with origin — the return URL parameter contains 0 protocol or hostname segments. This prevents open redirect vulnerabilities where an attacker could inject an external URL as the return destination.
- The client does not retry or queue the failed API request after re-authentication — the user starts fresh on the restored page. The count of automatic request retry mechanisms triggered by session expiry 401 responses equals 0.
- The OS-native notification on desktop is sent only when the app is not in the foreground — this prevents duplicate notifications (in-app toast + OS notification) when the user is actively using the app. The foreground detection uses the Tauri window focus state.

## Failure Modes

- **Return URL lost during redirect**: The client captures the return URL but a code error or browser extension strips the query parameter during the redirect to `/signin`, causing the user to land on `/app` instead of their original page after re-authentication. The sign-in page validates the return URL parameter on load, and if it is absent, falls back to the default `/app` redirect and logs a warning that the return URL was missing for diagnostics.
- **Multiple 401 responses trigger multiple redirects**: Several concurrent API calls all return 401 simultaneously (e.g., TanStack Query fires multiple refetches), causing the client to show multiple notification toasts and attempt multiple redirects. The client's 401 handler uses a boolean flag (or equivalent debounce mechanism) to ensure only the first 401 triggers the notification and redirect, and subsequent 401 responses within the same cycle are silently ignored, logging each suppressed duplicate.
- **Desktop notification fails to send**: The `tauri-plugin-notification` API call fails because the user has disabled OS notifications for the application, and the background session expiry goes unnoticed until the user returns to the app. The notification call catches the error and falls back to setting an in-app badge or visual indicator on the system tray icon, and logs the notification permission status for diagnostics.
- **Session refresh race condition**: A session is within seconds of expiring when two requests arrive simultaneously — one triggers a refresh that extends the session while the other hits the old `expiresAt` and returns 401. The client receives the 401 and shows the expiry notification even though the session was just refreshed. The 401 handler retries the failed request once before showing the notification, and if the retry succeeds (because the refresh has taken effect), the expiry notification is suppressed.

## Declared Omissions

- Session creation and refresh mechanics (covered by `session-lifecycle.md`)
- Session management UI for manual revocation (covered by `user-manages-sessions.md`)
- Desktop notification configuration and permissions (covered by `desktop-sends-a-notification.md`)
- Sign-in flow after re-authentication (covered by individual sign-in specs)

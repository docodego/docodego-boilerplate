[← Back to Roadmap](../ROADMAP.md)

# User Signs Out

## Intent

This spec defines the sign-out flow for the DoCodeGo boilerplate across all platform targets. The user clicks a "Sign out" button in the application header dropdown menu, which triggers `authClient.signOut()`. The server invalidates the current session by removing or expiring the session record in the `session` table, clears the session cookie and the `docodego_authed` hint cookie from the response, and the client redirects the user to `/signin`. After sign-out, any attempt to access authenticated routes under `/app/*` is intercepted by the auth guard and redirected back to `/signin`. On the desktop app, the sign-out flow works identically via the Tauri webview's native cookie handling, and the app remains open showing the sign-in page. This spec ensures that sign-out is complete, that no stale session state persists on the client, and that route protection is enforced immediately after sign-out.

## Acceptance Criteria

- [ ] The application header displays a user avatar that opens a dropdown menu on click — the avatar element and dropdown container are both present in the DOM
- [ ] The dropdown menu contains a "Sign out" button at the bottom — the button element is present and visible as the last item in the dropdown
- [ ] Clicking "Sign out" calls `authClient.signOut()` — the client method invocation is present in the click handler
- [ ] The server invalidates the session by removing or expiring the session record in the `session` table — the session row is either absent or has its `expiresAt` set to a past timestamp after the call
- [ ] The server clears the session cookie from the response — a `Set-Cookie` header is present with `Max-Age` = 0 or an `Expires` value in the past for the session cookie name
- [ ] The server clears the `docodego_authed` hint cookie — a `Set-Cookie` header is present with `Max-Age` = 0 or an `Expires` value in the past for the `docodego_authed` cookie name
- [ ] After sign-out, the client redirects to `/signin` — the redirect is present and the window location pathname changes to `/signin` after navigation completes
- [ ] After sign-out, navigating to any route under `/app/*` triggers the auth guard — the redirect to `/signin` is present and the user cannot access authenticated content
- [ ] The auth guard intercepts direct URL entry, browser back navigation, and stale bookmarks — all 3 navigation methods result in a redirect that is present and leads to `/signin` when the count of valid sessions equals 0
- [ ] On the desktop app (Tauri), the sign-out flow clears cookies via the same API calls — the Tauri webview handles cookie clearing natively and the count of additional IPC commands required equals 0
- [ ] On the desktop app, after sign-out the application window remains open and displays the `/signin` page — the window is present and the sign-in UI is visible
- [ ] The "Sign out" button text is rendered via an i18n translation key — the count of hardcoded English strings for the sign-out button equals 0
- [ ] The sign-out API call returns HTTP 200 on success — the response status code equals 200

## Constraints

- Sign-out invalidates only the current session — other active sessions for the same user (on different devices or browsers) remain valid. The count of session records deleted or expired for sessions other than the current one equals 0 during a standard sign-out. Revoking all sessions is a separate operation covered by the session management spec.
- The `docodego_authed` hint cookie must be cleared alongside the session cookie — if the hint cookie persists after sign-out, Astro SSG pages would incorrectly render authenticated UI for an unauthenticated user. Both cookies are cleared in the same response, and the count of responses where only one cookie is cleared equals 0.
- The auth guard on `/app/*` routes is client-side for SSG pages — the guard checks for a valid session by calling the auth API or reading the hint cookie, and redirects to `/signin` if no valid session is found. The redirect happens before the page content is rendered, and the count of authenticated page content flashes visible to unauthenticated users equals 0.
- The sign-out flow does not require confirmation — clicking "Sign out" immediately initiates the process with 0 confirmation dialogs or prompts. The action is considered low-risk because the user can sign in again immediately.

## Failure Modes

- **Sign-out API call fails due to network error**: The client calls `authClient.signOut()` but the request fails due to a network interruption or server error, leaving the session active on the server. The client catches the error and falls back to clearing the local cookies regardless (session cookie and `docodego_authed` hint cookie), then redirects to `/signin`. The server-side session expires naturally based on its `expiresAt` timeout of 7 days, and the client logs the sign-out failure reason for diagnostics.
- **Stale hint cookie persists after sign-out**: A code change inadvertently removes the `docodego_authed` cookie clearing from the sign-out response, causing Astro pages to render authenticated UI after the session is invalidated on the server. The CI test suite includes a test that calls the sign-out endpoint and asserts that both the session cookie and the `docodego_authed` cookie are present in the response `Set-Cookie` headers with expired values, and returns error if either cookie clearing is absent, blocking the build.
- **Auth guard bypass via cached page**: The browser serves an authenticated page under `/app/*` from its local cache after sign-out, displaying stale content that the user is no longer authorized to see. The auth guard runs on every page mount (not just initial load), checks for a valid session via the hint cookie, and if the cookie is absent, falls back to redirecting to `/signin` and logs a cache-hit bypass event for diagnostics.
- **Desktop app window closes on sign-out**: A misconfiguration in the Tauri event handler causes the application window to close when the sign-out navigation occurs, instead of remaining open on the `/signin` page to allow re-authentication. The Tauri `on_window_event` handler rejects close events triggered by navigation and only calls `app.exit(0)` on the explicit close (X button) event, and logs a warning if a navigation-triggered close is intercepted.

## Declared Omissions

- Revoking all user sessions across devices (covered by `user-manages-sessions.md`)
- Admin-initiated session revocation (covered by `app-admin-revokes-user-sessions.md`)
- Session expiry mid-use behavior (covered by `session-expires-mid-use.md`)
- Sign-out from the browser extension (covered by `extension-signs-out.md`)

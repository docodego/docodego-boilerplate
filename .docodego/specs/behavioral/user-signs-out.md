---
id: SPEC-2026-018
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# User Signs Out

## Intent

This spec defines the sign-out flow for the DoCodeGo boilerplate across all platform targets. The user clicks a "Sign out" button in the application header dropdown menu, which triggers `authClient.signOut()`. The server invalidates the current session by removing or expiring the session record in the `session` table, clears the session cookie and the `docodego_authed` hint cookie from the response, and the client redirects the user to `/signin`. After sign-out, any attempt to access authenticated routes under `/app/*` is intercepted by the auth guard and redirected back to `/signin`. On the desktop app, the sign-out flow works identically via the Tauri webview's native cookie handling, and the app remains open showing the sign-in page. This spec ensures that sign-out is complete, that no stale session state persists on the client, and that route protection is enforced immediately after sign-out.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth (server) | write | When `authClient.signOut()` sends the sign-out request to `/api/auth/sign-out` | The client falls back to clearing local cookies (session and `docodego_authed`) and redirects to `/signin`; the server-side session expires naturally at its `expiresAt` timeout |
| D1 `session` table | write | When Better Auth invalidates the session record during sign-out processing | The sign-out endpoint returns 500 and the client falls back to clearing local cookies and redirecting to `/signin`; the orphaned session expires at its `expiresAt` timeout of 7 days |
| Auth guard (client) | read | On every `/app/*` page mount after sign-out completes | If the guard script fails to load, the page degrades to rendering unauthenticated content because the API calls within the page will return 401 and trigger redirect logic |
| Tauri webview | read/write | On desktop platform when the sign-out navigation triggers cookie clearing and page transition | The webview falls back to standard browser cookie handling; no additional IPC commands are required because cookie clearing is handled natively by the webview engine |

## Behavioral Flow

1. **[User]** → clicks on their avatar in the application header → a dropdown menu opens with the translated "Sign out" button at the bottom of the dropdown
2. **[User]** → clicks the "Sign out" button → the client calls `authClient.signOut()` to begin the sign-out process
3. **[Server]** → receives the sign-out request and invalidates the session token → removes or marks the session record in the `session` table as expired
4. **[Server]** → clears the session cookie from the response → also clears the `docodego_authed` hint cookie so that Astro pages no longer detect an authenticated state on the client side
5. **[Client]** → redirects the user to `/signin` after the sign-out response is received from the server
6. **[Auth guard]** → from this point, any attempt to navigate to routes under `/app/*` triggers the auth guard → since no valid session exists, the guard redirects the user back to `/signin`
7. **[Auth guard]** → the redirect applies regardless of whether the user types a URL directly, uses browser back navigation, or follows a stale bookmark to an authenticated route

**Desktop variant:** On the desktop application (Tauri), the sign-out flow works identically because the Tauri webview handles cookies natively. The session and cookies are cleared through the same API calls. After sign-out, the desktop app remains open and displays the sign-in page, and the user can sign in again without restarting the application.

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| Authenticated | Unauthenticated | User clicks "Sign out" and `authClient.signOut()` completes with HTTP 200 | Session record exists in D1 and the session cookie is present in the request |
| Authenticated | Unauthenticated (fallback) | User clicks "Sign out" but the sign-out API call fails due to network error or server error | Client catches the error, clears local cookies, and redirects to `/signin` regardless of the server-side session state |

## Business Rules

- **Rule single-session-invalidation:** IF the user triggers sign-out THEN only the current session record is invalidated AND all other active sessions for the same user on different devices or browsers remain valid and unaffected
- **Rule dual-cookie-clearing:** IF the sign-out response is sent THEN both the session cookie and the `docodego_authed` hint cookie are cleared in the same response with `Max-Age=0` AND the count of responses where only one cookie is cleared equals 0
- **Rule no-confirmation:** IF the user clicks "Sign out" THEN the sign-out process begins immediately with 0 confirmation dialogs or prompts because the action is low-risk and the user can sign back in immediately
- **Rule auth-guard-enforcement:** IF the user has signed out AND navigates to any route under `/app/*` THEN the auth guard redirects to `/signin` before page content is rendered AND the count of authenticated page content flashes visible to unauthenticated users equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated user | Click "Sign out" button, trigger `authClient.signOut()`, access the sign-out endpoint at `/api/auth/sign-out` | N/A — sign-out is always permitted for authenticated users | The "Sign out" button is present and visible in the header dropdown only when a valid session exists |
| Unauthenticated user | N/A — the sign-out button is not rendered and the header dropdown is absent | Cannot access the sign-out endpoint because the session cookie is absent and Better Auth returns 401 | The header dropdown with the "Sign out" button is not present in the DOM when no valid session exists |

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
- The `docodego_authed` hint cookie is cleared alongside the session cookie — if the hint cookie persists after sign-out, Astro SSG pages would incorrectly render authenticated UI for an unauthenticated user. Both cookies are cleared in the same response, and the count of responses where only one cookie is cleared equals 0.
- The auth guard on `/app/*` routes is client-side for SSG pages — the guard checks for a valid session by calling the auth API or reading the hint cookie, and redirects to `/signin` if no valid session is found. The redirect happens before the page content is rendered, and the count of authenticated page content flashes visible to unauthenticated users equals 0.
- The sign-out flow does not require confirmation — clicking "Sign out" immediately initiates the process with 0 confirmation dialogs or prompts. The action is considered low-risk because the user can sign in again immediately.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user clicks "Sign out" while a background API request is still in-flight and has not yet received a response | The sign-out completes and the in-flight request receives a 401 response because the session is invalidated server-side before the request is processed | The in-flight request returns HTTP 401 and the client redirects to `/signin` without displaying an unhandled error to the user |
| The user double-clicks the "Sign out" button rapidly, sending two concurrent sign-out requests to the server | The first request invalidates the session and returns 200; the second request finds no valid session and returns 200 or 401 without causing a server error | Both responses have a status code of 200 or 401 and the count of 500-level responses equals 0 |
| The browser has disabled cookies entirely, preventing the session cookie from being sent with the sign-out request | Better Auth receives no session token in the request and returns 401 because it cannot identify the session to invalidate | The response status code is 401 and the client falls back to redirecting to `/signin` because no authenticated session is detectable |
| The user presses the browser back button after sign-out completes, attempting to return to an authenticated `/app/*` page | The auth guard runs on page mount, detects that no valid session exists (hint cookie is absent), and redirects to `/signin` before rendering any authenticated content | The redirect to `/signin` is present and the count of authenticated page content rendered equals 0 |
| The user has multiple browser tabs open on authenticated pages and signs out in one tab while the other tabs remain open | The other tabs continue displaying stale content until the next page mount or API call, at which point the auth guard or API 401 response triggers a redirect to `/signin` | On the next navigation or API call in the other tabs, the redirect to `/signin` is present and the authenticated content is no longer accessible |
| The Tauri desktop app receives a navigation event during sign-out that would normally trigger a window close event | The `on_window_event` handler rejects the close event triggered by navigation and the application window remains open, displaying the `/signin` page after the sign-out redirect completes | The window is present after sign-out and the sign-in page is visible with 0 close events processed during the navigation |

## Failure Modes

- **Sign-out API call fails due to network error or server unavailability during the sign-out request**
    - **What happens:** The client calls `authClient.signOut()` but the request fails due to a network interruption or server error, leaving the session active on the server.
    - **Source:** Network interruption, DNS resolution failure, or server-side error (500) during the sign-out request processing.
    - **Consequence:** The server-side session remains valid and could be reused if the session cookie is recovered, creating a stale session that persists until its `expiresAt` timeout.
    - **Recovery:** The client catches the error and falls back to clearing the local cookies regardless (session cookie and `docodego_authed` hint cookie), then redirects to `/signin`. The server-side session expires naturally based on its `expiresAt` timeout of 7 days, and the client logs the sign-out failure reason for diagnostics.

- **Stale docodego_authed hint cookie persists in the browser after the sign-out response clears the session cookie**
    - **What happens:** A code change inadvertently removes the `docodego_authed` cookie clearing from the sign-out response, causing Astro pages to render authenticated UI after the session is invalidated on the server.
    - **Source:** Developer error during refactoring of the sign-out response handler that removes or bypasses the hint cookie clearing logic.
    - **Consequence:** Users see authenticated navigation elements and UI on Astro SSG pages despite having no valid session, leading to confusing 401 errors when they attempt to interact with protected features.
    - **Recovery:** The CI test suite includes a test that calls the sign-out endpoint and alerts on failure — the test asserts that both the session cookie and the `docodego_authed` cookie are present in the response `Set-Cookie` headers with expired values, and returns error if either cookie clearing is absent, blocking the build.

- **Auth guard bypass via browser-cached page serving stale authenticated content to the user after sign-out completes**
    - **What happens:** The browser serves an authenticated page under `/app/*` from its local cache after sign-out, displaying stale content that the user is no longer authorized to see.
    - **Source:** Aggressive browser caching of HTML pages combined with the user pressing the back button or accessing a stale bookmark after sign-out.
    - **Consequence:** The user briefly sees authenticated page content from the cache, which degrades the security perception of the application.
    - **Recovery:** The auth guard runs on every page mount (not just initial load), checks for a valid session via the hint cookie, and if the cookie is absent, falls back to redirecting to `/signin` and logs a cache-hit bypass event for diagnostics.

- **Desktop app window closes unexpectedly during the sign-out navigation instead of remaining open on the sign-in page**
    - **What happens:** A misconfiguration in the Tauri event handler causes the application window to close when the sign-out navigation occurs, instead of remaining open on the `/signin` page to allow re-authentication.
    - **Source:** Incorrect event filtering in the Tauri `on_window_event` handler that treats navigation-triggered events the same as user-initiated window close events.
    - **Consequence:** The user loses the application window entirely and must relaunch the desktop app to sign back in, degrading the user experience.
    - **Recovery:** The Tauri `on_window_event` handler rejects close events triggered by navigation and only calls `app.exit(0)` on the explicit close (X button) event, and logs a warning if a navigation-triggered close is intercepted so the issue degrades to a logged diagnostic rather than a crash.

## Declared Omissions

- This specification does not cover revoking all user sessions across multiple devices, which is defined in `user-manages-sessions.md` as a separate operation
- This specification does not cover admin-initiated session revocation workflows, which are defined in `app-admin-revokes-user-sessions.md` as an administrative action
- This specification does not cover session expiry behavior while the user is actively using the application mid-session, which is defined in `session-expires-mid-use.md`
- This specification does not cover the sign-out flow for the browser extension platform target, which is defined in `extension-signs-out.md` as a separate spec
- This specification does not cover the sign-in flow or authentication methods used to create new sessions after sign-out, which are defined in the authentication behavioral specs

## Related Specifications

- [user-manages-sessions](user-manages-sessions.md) — covers the ability to revoke all active sessions across devices, which is explicitly excluded from this single-session sign-out spec
- [session-expires-mid-use](session-expires-mid-use.md) — covers the behavior when a session expires while the user is actively navigating authenticated pages, complementing this sign-out spec
- [extension-signs-out](extension-signs-out.md) — covers the sign-out flow for the browser extension platform target, which has different cookie and storage handling than the web and desktop targets
- [auth-server-config](../foundation/auth-server-config.md) — defines Better Auth plugin configuration, session strategy, and the session table schema that this spec depends on for session invalidation
- [app-admin-revokes-user-sessions](app-admin-revokes-user-sessions.md) — covers admin-initiated session revocation, a separate workflow from user-initiated sign-out defined in this spec

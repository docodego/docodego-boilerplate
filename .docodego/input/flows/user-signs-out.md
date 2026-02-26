[← Back to Index](README.md)

# User Signs Out

## Initiating Sign-Out

The user clicks on their avatar in the application header, which opens a dropdown menu. At the bottom of the dropdown, they click "Sign out." The client calls `authClient.signOut()` to begin the sign-out process.

## Server-Side Cleanup

The server receives the sign-out request and invalidates the session token, removing or marking the session record in the `session` table as expired. The server clears the session cookie from the response. The `docodego_authed` hint cookie is also cleared so that Astro pages no longer detect an authenticated state on the client side.

## Redirect and Route Protection

The client redirects the user to `/signin`. From this point, any attempt to navigate to routes under `/app/*` triggers the auth guard. Since no valid session exists, the guard redirects the user back to `/signin`. This applies regardless of whether the user types a URL directly, uses browser back navigation, or follows a stale bookmark.

## Desktop Behavior

On the desktop application (Tauri), the sign-out flow works identically. The session and cookies are cleared through the same API calls since the Tauri webview handles cookies natively. After sign-out, the desktop app remains open and displays the sign-in page. The user can sign in again without restarting the application.

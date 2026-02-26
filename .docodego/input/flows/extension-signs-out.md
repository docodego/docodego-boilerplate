[← Back to Index](README.md)

# Extension Signs Out

## Initiating Sign-Out

The user opens the browser extension popup and clicks the localized "Sign out" button. This button is only visible when the extension is in an authenticated state — meaning a valid session token is stored in `chrome.storage.local` after a previous sign-in via the token relay flow (see [Extension Authenticates via Token Relay](extension-authenticates-via-token-relay.md)).

## Clearing the Token and Canceling Refresh

When the sign-out action is triggered, the popup sends a message to the background service worker requesting sign-out. The background worker clears the session token from `chrome.storage.local` and cancels the active session refresh timer. This ensures no further automatic token refresh attempts are made after the user has explicitly signed out.

## Reverting to Unauthenticated State

With the token removed, the popup immediately reflects the unauthenticated state. The authenticated UI — user details, quick actions, and the sign-out button — is replaced by a localized sign-in prompt inviting the user to authenticate again. Any subsequent API calls from the extension will fail without a valid token, so the extension does not attempt them until the user signs in again.

## Web Session Independence

Signing out of the extension does not affect the user's web session. The extension and web app maintain separate authentication states — the extension relies on a token stored in `chrome.storage.local`, while the web app uses session cookies managed by the API. The user remains signed in to the web app and can continue using it normally after signing out of the extension.

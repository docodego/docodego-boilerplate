[← Back to Index](README.md)

# Extension Authenticates via Token Relay

## Why Token Relay

Browser extensions run on a different origin than the web app, which means they cannot access the API's session cookies. The extension uses a token relay pattern instead: the user authenticates through the normal web sign-in flow (see [User Signs In with Email OTP](user-signs-in-with-email-otp.md), [User Signs In with Passkey](user-signs-in-with-passkey.md), or [User Signs In with SSO](user-signs-in-with-sso.md)), and the resulting session token is passed to the extension via browser messaging.

## Sign-In Handoff

When the user clicks the localized "Sign in" button in the extension popup, the popup opens a new browser tab pointing to the DoCodeGo web app's sign-in page. The user completes authentication through any of the standard web methods — email OTP, passkey, or SSO. The web app handles the entire sign-in flow using its own UI and auth logic. From the user's perspective, they are signing in to the web app as usual.

## Token Transfer

After the web app confirms a successful sign-in, it sends the session token to the extension via `chrome.runtime.sendMessage()`. The background service worker listens for this message, receives the token, and stores it in `chrome.storage.local`. This storage persists across browser restarts, so the user does not need to sign in again each time they open the browser. The browser tab used for sign-in can be closed at this point.

## Authenticated State

With the token stored, all subsequent API calls from the extension route through the background service worker. The service worker attaches the token as an authorization header on every request to the DoCodeGo API, using the same oRPC client and typed contracts from `@repo/contracts` that the web app uses. The background service worker also runs a session refresh timer to keep the token valid before it expires. If a refresh fails — because the session was revoked server-side, for example — the stored token is cleared and the popup reverts to showing the sign-in prompt.

## Sign Out

When the user signs out from the extension, the background service worker clears the token from `chrome.storage.local` and cancels the refresh timer. The popup immediately reflects the unauthenticated state, showing the sign-in prompt again. Signing out of the extension does not affect the user's web session — the two are independent.
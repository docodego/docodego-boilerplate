[← Back to Index](README.md)

# Session Expires Mid-Use

## How a Session Becomes Stale

As described in [Session Lifecycle](session-lifecycle.md), sessions have a 7-day expiry window that refreshes automatically when the user is active. However, if a user leaves a browser tab or desktop app open without interacting for more than 7 days, the session expires on the server. The client still holds the session cookie, but the token it contains is no longer valid. The user is unaware that anything has changed — the UI looks exactly as they left it.

## The Next API Call Fails

When the user returns and performs any action that triggers an API call — navigating to a new page, refreshing data, submitting a form — the server evaluates the session token attached to the request. It finds no matching active session in the `session` table (or finds one whose `expiresAt` timestamp has passed) and responds with a `401 Unauthorized` status.

## The Client Detects the Expiration

The client's API layer intercepts the 401 response. Rather than displaying a generic error or silently failing, it recognizes this as a session expiration event. The client shows a localized toast notification or modal dialog informing the user that their session has expired and they need to sign in again. The message is clear and non-technical — something like "Your session has expired. Please sign in to continue."

## Redirect to Sign-In

After the user acknowledges the notification, the client redirects them to the sign-in page. Before redirecting, the client captures the current URL path and preserves it as a return URL parameter. This ensures the user does not lose their place — after signing in successfully through any of the standard methods ([Email OTP](user-signs-in-with-email-otp.md), [Passkey](user-signs-in-with-passkey.md), or [SSO](user-signs-in-with-sso.md)), they are navigated back to the exact page they were on before the session expired.

## Unsaved Work

Any unsaved work in progress at the time of the 401 — a half-filled form, a draft in a text field — is lost unless the client has persisted it locally. The session expiration notification should appear before the page is torn down, giving the user a moment to note their context. However, the application does not attempt to queue or retry the failed request after re-authentication. The user starts fresh on the restored page.

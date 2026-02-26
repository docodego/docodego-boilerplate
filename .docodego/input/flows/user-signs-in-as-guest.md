[← Back to Index](README.md)

# User Signs In as Guest

## Starting a Guest Session

The user arrives at `/signin` and sees a "Continue as guest" option alongside the standard email and passkey sign-in methods. They click it, and the client calls `authClient.signIn.anonymous()` with no additional input required. The flow is instant — no email, no credentials, no verification step.

## Server Creates an Anonymous User

The server creates a new user record with `isAnonymous` set to `true`. An auto-generated email in the format `anon-{uuid}@anon.docodego.com` is assigned to the user record to satisfy the email uniqueness constraint without requiring real contact information. A full session is created in the `session` table with all standard fields — signed token cookie, `userId`, `ipAddress`, `userAgent`, and `expiresAt` at 7 days. The `docodego_authed` hint cookie is set so that Astro pages recognize the user as authenticated.

## The Guest Experience

The client redirects the guest to `/app`. The guest can browse and interact with the application as a logged-in user. A persistent banner is displayed encouraging the guest to [create a full account](guest-upgrades-to-full-account.md) by linking a real email address. This banner remains visible throughout the guest's session to remind them that their activity can be preserved by upgrading. Until they upgrade, the guest account functions like any other account but is flagged as anonymous in the system.

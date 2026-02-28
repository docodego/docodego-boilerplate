[← Back to Index](README.md)

# Guest Deletes Anonymous Account

## Finding the Delete Option

A [guest user](user-signs-in-as-guest.md) who signed in anonymously navigates to their account settings or opens a menu within the guest UI. Among the available actions, they see a localized "Delete guest account" option. This option is only visible to users whose account is flagged as anonymous (`isAnonymous: true`). Full account holders see the standard [account deletion flow](user-deletes-their-account.md) instead.

## Confirming Deletion

The guest clicks the "Delete guest account" option. A brief localized confirmation dialog appears explaining that the anonymous session and any associated data will be permanently removed. Unlike full account deletion, there is no "type to confirm" step — since the guest has no verified email, no organization memberships, and no long-term data at stake, a simple confirm/cancel dialog is sufficient. The guest clicks the localized "Confirm" button to proceed.

## Server-Side Cleanup

On confirmation, the client calls `authClient.deleteAnonymousUser()`. The server deletes the anonymous user record from the database, including any session records in the `session` table associated with that user. The session token is invalidated and the session cookie is cleared. The `docodego_authed` hint cookie is also removed so that Astro pages no longer detect an authenticated state.

## Redirect to Landing

The client clears any remaining local state and redirects the user to the landing page or `/signin`. From this point the user is fully unauthenticated — there is no residual anonymous record in the database. This is distinct from [signing out](user-signs-out.md), which ends the session but leaves the anonymous user record intact, and from [upgrading to a full account](guest-upgrades-to-full-account.md), which preserves the session and converts the guest identity into a permanent one.

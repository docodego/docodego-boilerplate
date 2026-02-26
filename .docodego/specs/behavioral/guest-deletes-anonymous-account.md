[← Back to Roadmap](../ROADMAP.md)

# Guest Deletes Anonymous Account

## Intent

This spec defines the flow for deleting an anonymous guest account in the DoCodeGo boilerplate. A guest user navigates to account settings, clicks "Delete guest account," confirms via a simple confirmation dialog (no "type to confirm" step since the guest has no verified email or long-term data), and the server deletes the anonymous user record along with all associated session records. The session cookie and `docodego_authed` hint cookie are cleared, and the client redirects to `/signin`. This is distinct from signing out (which preserves the anonymous user record) and from upgrading (which converts the guest to a full account). This spec ensures that guest deletion is permanent, that all associated data is removed, and that the user is fully unauthenticated afterward.

## Acceptance Criteria

- [ ] The account settings page displays a "Delete guest account" option — the option element is present and visible when `user.isAnonymous` equals true
- [ ] The "Delete guest account" option is absent for non-anonymous users — when `user.isAnonymous` equals false, the element is absent from the rendered DOM
- [ ] Clicking "Delete guest account" opens a confirmation dialog with a localized warning message — the dialog element is present and visible after the click
- [ ] The confirmation dialog contains a "Confirm" button and a "Cancel" button — both button elements are present in the dialog
- [ ] The confirmation dialog does not contain a "type to confirm" text input — the count of text input fields in the dialog equals 0
- [ ] Clicking "Cancel" closes the dialog without deleting the account — the dialog is absent after clicking cancel and the user record is still present in the `user` table
- [ ] Clicking "Confirm" calls `authClient.deleteAnonymousUser()` — the client method invocation is present in the confirm handler
- [ ] The server deletes the anonymous user record from the `user` table — the row is absent from the table after the call completes
- [ ] The server deletes all session records associated with the anonymous user from the `session` table — the count of session rows with the deleted user's `userId` equals 0
- [ ] The server clears the session cookie from the response — a `Set-Cookie` header is present with `Max-Age` = 0 or `Expires` in the past for the session cookie
- [ ] The server clears the `docodego_authed` hint cookie — a `Set-Cookie` header is present with `Max-Age` = 0 or `Expires` in the past for the `docodego_authed` cookie
- [ ] After deletion, the client redirects to `/signin` — the redirect is present and the window location pathname changes to `/signin`
- [ ] After deletion, navigating to any `/app/*` route triggers the auth guard redirect to `/signin` — the redirect is present and no authenticated content is accessible
- [ ] All UI text in the deletion flow is rendered via i18n translation keys — the count of hardcoded English strings in the deletion components equals 0

## Constraints

- The "Delete guest account" option is only available to anonymous users — the visibility is controlled by the `user.isAnonymous` flag. Full account holders see the standard account deletion flow (which requires "type to confirm" and handles organization ownership transfer). The count of `deleteAnonymousUser` call sites accessible to non-anonymous users equals 0.
- The confirmation dialog is intentionally simple (confirm/cancel only) because anonymous accounts have no verified email, no organization memberships, and no long-term data. The count of text input fields in the guest deletion dialog equals 0, compared to the full account deletion dialog which requires typing a confirmation phrase.
- Deleting the anonymous account is permanent and removes the user record from the database — this is unlike signing out, which only invalidates the session but leaves the anonymous user record intact. After deletion, the anonymous user ID cannot be recovered and any data associated with it is permanently lost.
- The server deletes all sessions for the anonymous user, not just the current session — if the guest somehow has multiple active sessions (from different devices), all are invalidated when the account is deleted.

## Failure Modes

- **Delete call fails due to server error**: The client calls `authClient.deleteAnonymousUser()` but the server encounters a database error while deleting the user record, leaving the account intact. The server returns error HTTP 500, and the client displays a localized message notifying the user that the deletion failed and they can retry. The confirmation dialog remains open so the user can click "Confirm" again.
- **Non-anonymous user calls delete endpoint**: A full account user crafts a direct API request to the anonymous user deletion endpoint, attempting to bypass the UI restriction. The server checks `user.isAnonymous` before processing the deletion, and if the value equals false, the server rejects the request and returns error HTTP 403 with a diagnostic message. The user record remains intact.
- **Session cookie not cleared after deletion**: The server deletes the user record but the response fails to deliver the `Set-Cookie` clearing headers due to a network interruption mid-response. The client still holds a cookie referencing a deleted user, and on the next API call, the server finds no matching user for the session token, rejects the request with HTTP 401, and the client falls back to redirecting to `/signin`.
- **Concurrent deletion and upgrade**: The guest initiates account deletion in one browser tab while simultaneously starting an upgrade flow in another tab, causing a race condition between the delete and upgrade operations. The server uses a database transaction for deletion that locks the user row, and if the upgrade transaction attempts to read the same row, it retries after the deletion completes and returns error HTTP 404 because the user no longer exists.

## Declared Omissions

- Full account deletion flow with "type to confirm" (covered by `user-deletes-their-account.md`)
- Guest sign-in flow that creates the anonymous account (covered by `user-signs-in-as-guest.md`)
- Guest upgrade flow as an alternative to deletion (covered by `guest-upgrades-to-full-account.md`)
- Sign-out flow that preserves the anonymous user record (covered by `user-signs-out.md`)

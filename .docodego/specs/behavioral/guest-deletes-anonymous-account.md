---
id: SPEC-2026-022
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Guest Deletes Anonymous Account

## Intent

This spec defines the flow for deleting an anonymous guest account in the DoCodeGo boilerplate. A guest user navigates to account settings, clicks "Delete guest account," confirms via a simple confirmation dialog (no "type to confirm" step since the guest has no verified email or long-term data), and the server deletes the anonymous user record along with all associated session records. The session cookie and `docodego_authed` hint cookie are cleared, and the client redirects to `/signin`. This is distinct from signing out (which preserves the anonymous user record) and from upgrading (which converts the guest to a full account). This spec ensures that guest deletion is permanent, that all associated data is removed, and that the user is fully unauthenticated afterward.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth server SDK | write | Client calls `authClient.deleteAnonymousUser()` which hits the Better Auth anonymous user deletion endpoint | The server returns HTTP 500 and the client falls back to displaying a localized error message while keeping the confirmation dialog open for retry |
| D1 (Cloudflare SQL) | write | Server deletes the `user` row and all associated `session` rows via Drizzle ORM inside a database transaction | The transaction rolls back and the server returns HTTP 500 and the client degrades to showing a localized error message prompting the user to retry the deletion |
| `@repo/i18n` | read | Every UI string in the deletion flow is rendered via i18n translation keys for localization | Translation function falls back to the default English locale strings so the dialog remains readable but untranslated for non-English users |

## Behavioral Flow

1. **[Guest user]** → a guest user who signed in anonymously navigates to their account settings or opens a menu within the guest UI and sees a localized "Delete guest account" option among the available actions — this option is only visible to users whose account is flagged as anonymous (`isAnonymous` equals true) and full account holders see the standard account deletion flow instead
2. **[Guest user]** → clicks the "Delete guest account" option and the client displays a brief localized confirmation dialog explaining that the anonymous session and any associated data will be permanently removed — unlike full account deletion there is no "type to confirm" step because the guest has no verified email, no organization memberships, and no long-term data at stake, so a simple confirm/cancel dialog is sufficient
3. **[Guest user]** → clicks the localized "Confirm" button to proceed with the deletion of their anonymous account
4. **[Client]** → on confirmation the client calls `authClient.deleteAnonymousUser()` which sends the deletion request to the Better Auth anonymous user deletion endpoint on the server
5. **[Better Auth server]** → receives the deletion request and deletes the anonymous user record from the database including any session records in the `session` table associated with that user — the session token is invalidated, the session cookie is cleared, and the `docodego_authed` hint cookie is also removed so that Astro pages no longer detect an authenticated state
6. **[Client]** → clears any remaining local state and redirects the user to the landing page or `/signin` — from this point the user is fully unauthenticated with no residual anonymous record in the database, which is distinct from signing out (which ends the session but leaves the anonymous user record intact) and from upgrading to a full account (which preserves the session and converts the guest identity into a permanent one)

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| Authenticated (anonymous guest) | Dialog open | Guest clicks "Delete guest account" button | `user.isAnonymous` equals true |
| Dialog open | Authenticated (anonymous guest) | Guest clicks "Cancel" button in the confirmation dialog | None |
| Dialog open | Deletion in progress | Guest clicks "Confirm" button in the confirmation dialog | None |
| Deletion in progress | Unauthenticated | Server returns HTTP 200 after successful deletion of user and session records | Database transaction commits successfully |
| Deletion in progress | Dialog open (error displayed) | Server returns HTTP 500 due to a database or server error during deletion | Transaction rolls back and user record remains intact |

## Business Rules

- **Rule guest-only-delete:** IF `user.isAnonymous` equals true THEN the "Delete guest account" option is visible and the deletion endpoint accepts the request; IF `user.isAnonymous` equals false THEN the option is absent from the UI and the server rejects the deletion request with HTTP 403
- **Rule simple-confirmation:** IF the user is an anonymous guest THEN the confirmation dialog contains only "Confirm" and "Cancel" buttons with 0 text input fields; this is because anonymous accounts have no verified email, no organization memberships, and no long-term data requiring additional verification
- **Rule all-sessions-deleted:** IF the anonymous user deletion succeeds THEN the server deletes all session rows associated with the user's ID from the `session` table, not only the current session, ensuring that concurrent sessions on other devices are also invalidated
- **Rule permanent-deletion:** IF the anonymous user record is deleted from the `user` table THEN the deletion is permanent and the anonymous user ID cannot be recovered, and any data associated with that user ID is permanently lost

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Anonymous guest (`isAnonymous` = true) | View and click "Delete guest account," confirm deletion via dialog, trigger `authClient.deleteAnonymousUser()` | Access the full account deletion flow which requires "type to confirm" verification | Sees the "Delete guest account" option in account settings; does not see the full account deletion option |
| Authenticated full user (`isAnonymous` = false) | Access the standard account deletion flow with "type to confirm" and organization ownership transfer | Call the anonymous user deletion endpoint (server returns HTTP 403 rejection) | Does not see the "Delete guest account" option; sees the standard "Delete account" option instead |
| Unauthenticated visitor | None — all account settings pages require an active session to access | All deletion actions and account settings page access (auth guard redirects to `/signin`) | Cannot view account settings or any deletion options because the auth guard redirects before rendering |

## Constraints

- The "Delete guest account" option is only available to anonymous users — the visibility is controlled by the `user.isAnonymous` flag and the count of `deleteAnonymousUser` call sites accessible to non-anonymous users equals 0
- The confirmation dialog is intentionally simple (confirm/cancel only) because anonymous accounts have no verified email, no organization memberships, and no long-term data — the count of text input fields in the guest deletion dialog equals 0
- Deleting the anonymous account is permanent and removes the user record from the database — after deletion the anonymous user ID cannot be recovered and any data associated with it is permanently lost, unlike signing out which only invalidates the session but leaves the anonymous user record intact
- The server deletes all sessions for the anonymous user inside a single database transaction, not just the current session — if the guest has multiple active sessions from different devices, the count of remaining session rows with the deleted user's `userId` equals 0 after the transaction commits

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

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The guest clicks "Confirm" but the network connection drops before the request reaches the server, leaving the deletion request undelivered | The client receives a network error and displays a localized error message inside the dialog, keeping the dialog open so the user can retry the deletion when connectivity is restored | The confirmation dialog remains visible with an error message present and the user record is still present in the `user` table |
| The guest opens the deletion dialog in two browser tabs simultaneously and clicks "Confirm" in both tabs at nearly the same time | The first request succeeds and deletes the user and sessions; the second request finds no matching user record and the server returns HTTP 404, and the client falls back to redirecting to `/signin` since the account no longer exists | The first tab redirects to `/signin` after success and the second tab also redirects to `/signin` after receiving the 404 response |
| The guest clicks "Confirm" and the server begins the database transaction, but the D1 service experiences a transient failure causing the transaction to roll back mid-execution | The server returns HTTP 500 with a generic error message, the user record remains intact because the transaction rolled back, and the client displays a localized retry message inside the dialog | The dialog remains open with an error message present, and the user record and all session rows are still present in the database |
| A non-anonymous full-account user crafts a direct HTTP request to the anonymous deletion endpoint, bypassing the UI restriction entirely | The server checks `user.isAnonymous` before processing and rejects the request with HTTP 403, returning a diagnostic error message, and the user record remains intact in the database | The response status equals 403 and the user record is still present in the `user` table |
| The guest's session cookie has already expired or been invalidated before they click "Confirm" on the deletion dialog | The server rejects the request with HTTP 401 because no valid session exists, and the client falls back to redirecting to `/signin` since the user is already unauthenticated | The response status equals 401 and the client redirects to `/signin` without deleting any records |

## Failure Modes

- **Delete call fails due to server error or database transaction failure during the anonymous account deletion process**
    - **What happens:** The client calls `authClient.deleteAnonymousUser()` but the server encounters a D1 database error while deleting the user record inside the transaction, causing the transaction to roll back and leaving the account intact.
    - **Source:** Database service degradation, transient D1 connection failure, or exceeded rate limits on the Cloudflare Workers platform.
    - **Consequence:** The anonymous user record and all session rows remain intact in the database, and the guest sees an error state in the confirmation dialog instead of being redirected to `/signin`.
    - **Recovery:** The server returns HTTP 500 with a generic error message, and the client falls back to displaying a localized error message inside the dialog while keeping the "Confirm" button enabled so the user can retry the deletion after the transient issue resolves.

- **Non-anonymous user calls the anonymous deletion endpoint by crafting a direct API request to bypass the UI restriction**
    - **What happens:** A full account user sends a direct HTTP request to the Better Auth anonymous user deletion endpoint, attempting to delete their full account through the simplified anonymous deletion path that lacks "type to confirm" verification.
    - **Source:** Adversarial or accidental direct API call from a non-anonymous authenticated user who bypasses the client-side UI restriction.
    - **Consequence:** If the server did not validate the `isAnonymous` flag, a full account with organization memberships and long-term data could be deleted without proper confirmation, causing permanent data loss.
    - **Recovery:** The server rejects the request with HTTP 403 because `user.isAnonymous` equals false, the user record remains intact, and the client falls back to displaying the rejection error message to the user.

- **Session cookie not cleared after deletion due to a network interruption occurring mid-response from the server**
    - **What happens:** The server successfully deletes the anonymous user record and session rows from the database, but the HTTP response containing the `Set-Cookie` clearing headers is interrupted by a network failure before reaching the client browser.
    - **Source:** Network interruption, client-side connection drop, or proxy timeout occurring between the server sending the response and the client receiving it.
    - **Consequence:** The client still holds a session cookie referencing a deleted user, and subsequent API calls will send this stale cookie to the server, which finds no matching user record for the session token.
    - **Recovery:** On the next API call, the server finds no matching user for the stale session token, rejects the request with HTTP 401, and the client falls back to redirecting to `/signin` where the auth guard clears the invalid session state.

- **Concurrent deletion and upgrade race condition when the guest initiates both operations simultaneously in separate browser tabs**
    - **What happens:** The guest opens account settings in two browser tabs, clicks "Delete guest account" in one tab and starts the upgrade-to-full-account flow in the other tab, creating a race condition between the delete and upgrade database transactions.
    - **Source:** User-initiated concurrent operations from multiple browser tabs accessing the same anonymous account simultaneously.
    - **Consequence:** Without proper transaction isolation, the upgrade could partially complete on a user record that is simultaneously being deleted, leaving orphaned data or an inconsistent account state.
    - **Recovery:** The server uses a database transaction for deletion that locks the user row, and if the upgrade transaction attempts to read the same row it retries after the deletion completes and returns HTTP 404 because the user no longer exists, causing the upgrade client to fall back to redirecting to `/signin`.

## Declared Omissions

- This specification does not address the full account deletion flow with "type to confirm" verification and organization ownership transfer, which is covered by `user-deletes-their-account.md`
- This specification does not address the guest sign-in flow that creates the anonymous account in the first place, which is covered by `user-signs-in-as-guest.md`
- This specification does not address the guest upgrade flow as an alternative path to deletion where the anonymous account is converted to a full account, which is covered by `guest-upgrades-to-full-account.md`
- This specification does not address the sign-out flow that preserves the anonymous user record and only invalidates the session, which is covered by `user-signs-out.md`
- This specification does not address server-side rate limiting or throttling of the deletion endpoint, which is an infrastructure concern defined at the API framework level in `api-framework.md`

## Related Specifications

- [user-deletes-their-account](user-deletes-their-account.md) — Full account deletion flow with "type to confirm" verification and organization ownership transfer for non-anonymous users
- [user-signs-in-as-guest](user-signs-in-as-guest.md) — Guest sign-in flow that creates the anonymous user record which this spec's deletion flow permanently removes
- [guest-upgrades-to-full-account](guest-upgrades-to-full-account.md) — Alternative path where the guest converts their anonymous account to a full account instead of deleting it
- [user-signs-out](user-signs-out.md) — Sign-out flow that invalidates the session but preserves the anonymous user record, unlike deletion which removes it permanently
- [session-lifecycle](session-lifecycle.md) — Session management specification covering session creation, validation, and expiration that interacts with the session deletion in this flow
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth plugin configuration including the anonymous user plugin that provides the `deleteAnonymousUser` endpoint used in this spec

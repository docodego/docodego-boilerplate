---
id: SPEC-2026-053
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Removes a Passkey

## Intent

This spec defines the flow by which an authenticated user permanently
removes a previously registered passkey from their account within the
DoCodeGo dashboard. The user navigates to the security settings page at
`/app/settings/security`, views the list of registered passkeys showing
each entry's friendly name, device type, creation date, and last-used
date, then clicks the "Delete" button next to the passkey they want to
remove. A confirmation dialog with localized text appears identifying
the passkey by name so the user can verify they are deleting the correct
credential. If the passkey is the user's only registered passkey, the
dialog includes an informational warning explaining that removal will
leave the account with no passkey-based authentication, but this is not
a blocker because the user can still sign in via email OTP or SSO. Upon
confirmation, the client calls `authClient.passkey.deletePasskey({ id })`
with the credential ID, and the server verifies ownership then deletes
the passkey record from the `passkey` table, permanently removing the
public key, credential ID, counter, and transport data. The passkey list
refreshes to reflect the deletion and the user can register a new
passkey at any time.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth server SDK (`passkey` plugin) | write | Client calls `authClient.passkey.deletePasskey({ id })` after the user confirms the deletion dialog to permanently remove the passkey record from the database | The server returns HTTP 500 and the client falls back to displaying a localized error toast message, leaving the passkey record intact and allowing the user to close the dialog and retry the deletion |
| `passkey` table (D1) | write | Server deletes the `passkey` row matching the credential ID after verifying the passkey belongs to the authenticated user's account | The database write fails, the server returns HTTP 500, and the client falls back to showing a localized error toast — the passkey record remains fully intact because no deletion is committed until the write succeeds |
| `@repo/i18n` | read | All confirmation dialog text, last-passkey warning message, button labels, empty-state message, and error toasts displayed during the passkey removal flow are rendered via i18n translation keys | Translation function falls back to the default English locale strings so the confirmation dialog and passkey list remain functional but untranslated for non-English users |

## Behavioral Flow

1. **[User]** navigates to the security settings page at
    `/app/settings/security` where the passkeys section displays a list
    of all previously registered passkeys for the authenticated user's
    account
2. **[Client]** renders each passkey entry in the list showing the
    friendly name (or a default label if none was assigned during
    registration), the device type, the creation date formatted via
    `Intl.DateTimeFormat`, and the last-used date formatted via
    `Intl.DateTimeFormat`
3. **[Branch — no passkeys registered]** If the user has not registered
    any passkeys, the section displays a localized message: "No passkeys
    registered yet" and no delete buttons are rendered because the list
    is empty
4. **[User]** locates the passkey they want to remove and clicks the
    "Delete" button rendered next to that specific passkey entry in the
    list
5. **[Client]** opens a confirmation dialog with localized text asking
    the user to confirm that they want to permanently remove this
    passkey from their account — the dialog identifies the passkey by
    its friendly name so the user can verify they are deleting the
    correct credential
6. **[Branch — last passkey warning]** If the passkey being deleted is
    the user's only registered passkey (count of remaining passkeys
    equals 1), the confirmation dialog includes an additional localized
    warning explaining that removing it will leave the account with no
    passkey-based authentication — the warning is informational and not
    a blocker because the user can still sign in using email OTP or SSO,
    so the confirm button remains enabled
7. **[User]** clicks the confirm button inside the dialog to proceed
    with the deletion, or clicks cancel to abort and close the dialog
    without making any changes
8. **[Branch — user cancels]** If the user clicks cancel or dismisses
    the confirmation dialog, the dialog closes, the passkey list remains
    unchanged, and no delete request is sent to the server
9. **[Client]** upon confirmation, calls
    `authClient.passkey.deletePasskey({ id })` with the credential ID of
    the passkey to remove, disabling the confirm button and displaying a
    loading indicator while the request is in flight
10. **[Server]** receives the delete request, verifies that the passkey
    with the given credential ID belongs to the authenticated user's
    account by checking the `userId` field on the `passkey` row, and
    rejects the request with HTTP 403 if the ownership check fails
11. **[Server]** deletes the passkey record from the `passkey` table,
    permanently removing the stored public key, credential ID, counter
    value, and transport data associated with that credential
12. **[Client]** receives the success response and refreshes the passkey
    list to reflect the deletion — the removed passkey no longer appears
    in the list
13. **[Branch — last passkey removed]** If the deleted passkey was the
    user's only registered passkey, the section returns to the empty
    state displaying the localized "No passkeys registered yet" message
    and the user can register a new passkey at any time
14. **[Branch — deletion fails]** If the delete request fails due to a
    network error or server error, the client displays a localized error
    toast and the passkey remains unchanged in the list — the user can
    retry the deletion by clicking the "Delete" button again

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| passkey_list | dialog_open | User clicks the "Delete" button next to a passkey entry | Authenticated user is viewing the security settings page at `/app/settings/security` |
| dialog_open | deleting | User clicks the confirm button inside the confirmation dialog | Confirmation action is present within the dialog — not a single click from the list |
| dialog_open | passkey_list | User clicks cancel or dismisses the confirmation dialog | None — cancel is always available regardless of passkey count |
| deleting | deletion_complete | Server returns HTTP 200 from the deletePasskey endpoint | Passkey row is removed from the `passkey` table and the server confirms deletion |
| deleting | dialog_error | Server returns non-200 or network error during the delete request | HTTP response status does not equal 200 or the request times out |
| dialog_error | deleting | User clicks retry inside the error state or re-initiates the deletion | Passkey record still exists in the database and the retry request can proceed |
| deletion_complete | passkey_list | Client refreshes the passkey list after receiving the success response | List re-renders with the deleted passkey removed from the displayed entries |
| deletion_complete | empty_state | Client refreshes and detects 0 remaining passkeys for the user | Count of remaining passkey rows for the authenticated user equals 0 |

## Business Rules

- **Rule confirmation-required:** IF the user clicks the "Delete"
    button next to a passkey entry THEN a confirmation dialog must be
    presented AND the passkey is not deleted unless the user explicitly
    clicks the confirm button within the dialog — a single click on the
    delete button alone does not trigger deletion
- **Rule last-passkey-warning-informational:** IF the passkey being
    deleted is the user's only registered passkey (count of remaining
    passkeys equals 1) THEN the confirmation dialog includes an
    additional localized warning about losing passkey-based
    authentication, but the warning is informational and not a blocker
    — the confirm button remains enabled because the user can still sign
    in via email OTP or SSO
- **Rule ownership-validation:** IF the credential ID in the delete
    request does not belong to the authenticated user's account (the
    `userId` field on the `passkey` row does not match the session user
    ID) THEN the server rejects the request with HTTP 403 and the
    passkey record is not modified — no user can delete another user's
    passkey regardless of client-side state
- **Rule other-auth-methods-remain:** IF the user removes their only
    passkey THEN the account retains access to email OTP and SSO
    sign-in methods — passkey removal does not lock the user out of
    their account because at least 1 alternative authentication method
    remains available at all times

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner (account holder) | View the full passkey list on the security settings page, click the delete button to open the confirmation dialog for any of their own passkeys, and confirm deletion to permanently remove a passkey from their account | Delete passkeys belonging to other user accounts — the server rejects cross-account deletion requests with HTTP 403 after ownership validation | Full passkey list is present and visible with delete buttons rendered next to each passkey entry owned by the authenticated user |
| Admin (org context) | View their own passkey list on the security settings page and delete their own passkeys — passkey management is account-scoped and not affected by organization role | Delete passkeys belonging to other user accounts regardless of their admin role — organization admin privileges do not extend to other users' passkey credentials | Only the authenticated admin's own passkeys are present in the list — no cross-account passkey visibility exists |
| Member (org context) | View their own passkey list on the security settings page and delete their own passkeys — passkey management is account-scoped and not affected by organization role | Delete passkeys belonging to other user accounts regardless of their member role — organization membership does not grant access to other users' passkey credentials | Only the authenticated member's own passkeys are present in the list — no cross-account passkey visibility exists |
| Unauthenticated | None — route guard redirects to `/signin` before the security settings page loads at `/app/settings/security` | Access any part of the security settings page or call the deletePasskey endpoint — all requests without a valid session are rejected | Security settings page is not rendered — redirect to `/signin` occurs before any component mounts |

## Constraints

- The delete button next to each passkey entry must not trigger
    deletion without a confirmation dialog — the count of
    `passkey.deletePasskey` API calls triggered without a prior
    confirmation dialog interaction equals 0
- The server must validate passkey ownership before deletion — the
    count of successful deletions where the `userId` on the passkey row
    does not match the authenticated session user ID equals 0
- All UI text in the passkey list, confirmation dialog, last-passkey
    warning, empty-state message, and error toasts is rendered via i18n
    translation keys — the count of hardcoded English strings in the
    passkey management components equals 0
- Dates in the passkey list (creation date and last-used date) must be
    formatted using `Intl.DateTimeFormat` and not with date-fns or any
    third-party date library — the count of date-fns imports in the
    passkey management components equals 0
- The passkey list must refresh after a successful deletion to reflect
    the current state — the count of stale passkey entries displayed
    after a confirmed successful deletion response equals 0

## Acceptance Criteria

- [ ] The security settings page at `/app/settings/security` displays a passkey list — the count of rendered passkey entries equals the count of passkey rows in the database for the authenticated user and the count of missing entries equals 0
- [ ] Each passkey entry displays the friendly name, device type, creation date, and last-used date — all 4 data fields are present and non-empty for each entry in the rendered list
- [ ] If the user has 0 registered passkeys, the section displays a localized "No passkeys registered yet" message — the empty-state message element is present and the count of delete button elements equals 0
- [ ] Clicking the "Delete" button next to a passkey entry opens a confirmation dialog — the dialog element is present and visible within 300ms of the button click
- [ ] The confirmation dialog identifies the passkey by its friendly name — the dialog content contains the passkey name string and the count of dialogs missing the passkey name equals 0
- [ ] If the passkey is the user's only registered passkey (count equals 1), the dialog includes an additional last-passkey warning element — the warning text element is present within the dialog and the confirm button remains enabled
- [ ] If the user has more than 1 registered passkey, the last-passkey warning element is absent from the dialog — the warning element count within the dialog equals 0
- [ ] Clicking cancel closes the dialog without sending a delete request — the dialog element is absent from the DOM after cancel and the count of deletePasskey API calls equals 0
- [ ] Clicking confirm calls `authClient.passkey.deletePasskey({ id })` with the correct credential ID — the delete API request is present in the network activity with the matching credential ID value
- [ ] The confirm button is disabled and a loading indicator is present while the delete request is in flight — the disabled attribute is present on the confirm button during the API call
- [ ] On HTTP 200, the passkey row is removed from the `passkey` table — the count of passkey rows matching the deleted credential ID in the database equals 0
- [ ] On HTTP 200, the passkey list refreshes and the deleted entry is absent — the count of rendered passkey entries decreases by 1 after the success response
- [ ] If the deleted passkey was the only one, the section returns to empty state — the empty-state message is present and the count of rendered passkey entries equals 0
- [ ] A direct deletePasskey call with a credential ID belonging to a different user returns HTTP 403 — the response status equals 403 and the passkey record is not modified
- [ ] If the delete request fails with a network or server error, a localized error toast is displayed — the toast element is present with a non-empty error message and the passkey entry remains in the list unchanged

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User double-clicks the confirm button in the deletion dialog before the first request completes | The client disables the confirm button immediately on the first click, preventing duplicate requests — the server receives exactly 1 deletePasskey request and the count of deletion API calls equals 1 | The disabled attribute is present on the confirm button within 100ms of the first click and the network log shows exactly 1 delete request |
| User opens the deletion dialog for a passkey that is concurrently deleted from another browser tab or session | The second deletion request returns HTTP 404 because the passkey row no longer exists in the database — the client displays a localized error message and refreshes the passkey list to reflect the current state | The response status equals 404 and the passkey list re-renders without the already-deleted entry |
| User opens the deletion dialog and their session expires before they click confirm | Clicking confirm triggers a 401 response from the server because the session is no longer valid — the client redirects to `/signin` and the passkey record is not deleted | HTTP response status equals 401 and the passkey row still exists in the database |
| User navigates away from the security settings page while the confirmation dialog is open but before confirming | The dialog closes due to the route change, no delete request is sent to the server, and the passkey record remains unchanged in the database | The dialog element is absent from the DOM after navigation and the count of deletePasskey API calls equals 0 |
| The passkey list contains exactly 1 entry and the user deletes it, then immediately clicks "Register new passkey" | The empty state renders after the deletion completes and the registration flow starts from the empty state — the count of passkey entries equals 0 before the registration ceremony begins | The empty-state message is present before the registration dialog opens |

## Failure Modes

- **Delete API call fails due to a transient D1 database error preventing the passkey row from being removed**
    - **What happens:** The client calls `authClient.passkey.deletePasskey({ id })` after the user confirms, but the D1 database returns an error during the delete operation, causing the passkey record to remain intact in the `passkey` table with no modifications applied.
    - **Source:** Transient Cloudflare D1 database failure, Worker resource exhaustion, or a network interruption between the Worker and the D1 service during the delete write operation.
    - **Consequence:** The user sees an error toast and the passkey remains fully functional for authentication — the deletion did not complete and the credential can still be used for future sign-in attempts.
    - **Recovery:** The server returns HTTP 500 and logs the database error with the credential ID and timestamp — the client falls back to displaying a localized error toast and the user can retry the deletion by clicking the "Delete" button again once the D1 service recovers.
- **Unauthorized user attempts to delete a passkey belonging to a different account by crafting a direct API request**
    - **What happens:** An authenticated user crafts a direct HTTP request to the `passkey.deletePasskey` endpoint using a credential ID that belongs to a different user's account, attempting to remove another user's passkey without their knowledge or consent.
    - **Source:** Adversarial action where a user inspects the API surface, obtains or guesses a credential ID belonging to another account, and sends a hand-crafted delete request with their own valid session token.
    - **Consequence:** Without server-side ownership validation, any authenticated user could permanently delete another user's passkey credential, removing their ability to use passkey-based sign-in without authorization.
    - **Recovery:** The server rejects the request with HTTP 403 after reading the `userId` field on the `passkey` row and confirming it does not match the session user ID — the target passkey record is not modified and the server logs the unauthorized deletion attempt with both user IDs and the credential ID for audit review.
- **Network connection drops after the user clicks confirm but before the server response reaches the client**
    - **What happens:** The user confirms the deletion and the client sends the `authClient.passkey.deletePasskey({ id })` request, but the network connection is lost after the server processes and commits the deletion — the client never receives the HTTP 200 response confirming the passkey was removed.
    - **Source:** Unstable network conditions where the client-to-server connection drops during the response phase of the delete request, leaving the client unable to determine whether the deletion succeeded.
    - **Consequence:** The passkey is deleted on the server but the client still displays the passkey in the list because it did not receive the success response — the UI is temporarily out of sync with the database state until the user takes further action.
    - **Recovery:** The client displays a localized error toast notifying the user that the request failed, and when the user retries or refreshes the passkey list, the client fetches the current passkey data from the server — the list then falls back to reflecting the true database state where the passkey is already absent.

## Declared Omissions

- Passkey registration flow is not covered by this spec and is defined separately in `user-registers-a-passkey.md` which handles the credential creation ceremony and initial setup
- Passkey renaming flow is not covered by this spec and is defined separately in `user-renames-a-passkey.md` which handles updating the friendly name label for an existing passkey
- Rate limiting on the `passkey.deletePasskey` endpoint is not covered by this spec — that behavior is enforced by the global rate limiter defined in `api-framework.md` covering all mutation endpoints uniformly
- Notification of the user via email when a passkey is deleted from their account is not covered by this spec — any notification behavior for credential changes is defined as a separate concern in a dedicated notification spec
- Mobile passkey management on React Native is not covered because passkeys are not available in the Expo environment as documented in `expo-build.md` platform constraints

## Related Specifications

- [user-registers-a-passkey](user-registers-a-passkey.md) — defines the passkey registration ceremony where the user creates and stores a new WebAuthn credential that appears in the passkey list
- [user-renames-a-passkey](user-renames-a-passkey.md) — defines the flow for renaming an existing passkey entry's friendly name in the user's credential management interface on the security settings page
- [user-signs-in-with-passkey](user-signs-in-with-passkey.md) — defines the passkey sign-in flow that relies on credentials stored in the `passkey` table which this spec's deletion operation permanently removes
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — defines the email OTP sign-in flow that remains available as an alternative authentication method after the user removes their passkey credentials
- [auth-server-config](../foundation/auth-server-config.md) — defines Better Auth plugin configuration including the passkey plugin that provides the `deletePasskey` endpoint and enforces ownership validation
- [database-schema](../foundation/database-schema.md) — defines the Drizzle ORM `passkey` table schema containing the public key, credential ID, counter, and transport fields permanently removed during deletion

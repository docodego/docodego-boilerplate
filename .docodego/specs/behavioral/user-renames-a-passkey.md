---
id: SPEC-2026-052
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Renames a Passkey

## Intent

This spec defines the flow by which an authenticated user renames one
of their registered passkeys to update its friendly display name. The
user navigates to the security settings page at `/app/settings/security`
where the passkeys section lists all passkeys previously registered by
the user. Each entry displays the passkey's friendly name (or a default
label if none was assigned), the device type, and the creation date.
The user clicks the edit icon next to the target passkey to open an
inline input field or a rename dialog pre-filled with the current name.
The user clears the field, types a new friendly name, and submits the
change. The client calls
`authClient.passkey.updatePasskey({ id, name })` with the passkey's
credential ID and the new name. The server validates that the passkey
belongs to the authenticated user by checking ownership in the `passkey`
table, updates only the `name` column, and returns the updated record.
No other passkey fields — public key, credential ID, counter, or
transports — are modified by a rename operation. After a successful
rename the passkey list refreshes to display the updated name and the
user can rename the same passkey again at any time by repeating the
process. This operation is purely cosmetic and does not affect how the
passkey functions during WebAuthn authentication ceremonies.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth passkey plugin (`updatePasskey`) | write | User clicks save in the rename dialog and the client calls `authClient.passkey.updatePasskey({ id, name })` to persist the new friendly name to the database | The server returns HTTP 500 and the client falls back to displaying a localized error message inside the rename dialog while keeping the original passkey name intact until the user retries |
| `passkey` table (D1) | read/write | Server reads the existing passkey row to confirm ownership by matching `userId`, then updates only the `name` column with the new value provided in the `updatePasskey` request payload | The database read or update operation fails and the server returns HTTP 500 — the client notifies the user with a localized error message so the passkey name is not left in a partial state |
| `session` table (D1) | read | Server reads the active session to resolve the calling user's identity and verify their authenticated status before processing the rename request on the passkey record | The session lookup fails and the server returns HTTP 401 — the client redirects the user to `/signin` so they can re-authenticate before retrying the passkey rename operation |
| `@repo/i18n` | read | All dialog labels, input placeholders, button text, validation messages, and error strings in the rename flow are rendered via i18n translation keys at component mount time | Translation function falls back to the default English locale strings so the rename dialog remains fully functional but displays untranslated text for non-English locale users |

## Behavioral Flow

1. **[User]** navigates to `/app/settings/security` and views the
    passkeys section, which lists all passkeys registered by the user
    with each entry displaying the friendly name, device type, and
    creation date — the edit icon is visible next to each passkey entry

2. **[User]** clicks the edit icon next to the target passkey entry
    to initiate the rename flow, which triggers an inline input field
    or a localized rename dialog to appear with the current passkey
    name pre-filled in the input field

3. **[Client]** renders the rename input with translated labels via
    `@repo/i18n` and the passkey's current name pre-filled so the
    user can see exactly what they are changing from — the save button
    is enabled only when the input value differs from the current name
    and is non-empty after trimming whitespace characters

4. **[User]** clears the pre-filled value, types a new friendly name
    for the passkey, and clicks the save button to submit the rename
    request, or clicks cancel to dismiss the dialog without making any
    changes to the passkey record in the database

5. **[Branch -- user cancels]** The rename dialog closes and the
    passkey retains its original name with no changes made to the
    `passkey` table row, the passkey list display, or any other
    passkey fields such as the public key or credential ID

6. **[Client]** disables the save button, displays a loading
    indicator, and calls
    `authClient.passkey.updatePasskey({ id, name })` using the
    passkey's credential ID and the new name value from the input
    field to request the rename on the server

7. **[Server]** receives the update request, reads the calling user's
    session to resolve their identity, and queries the `passkey` table
    to confirm that the target passkey's `userId` column matches the
    authenticated user's ID — this ownership check prevents users from
    renaming passkeys that belong to other accounts

8. **[Branch -- passkey not owned by caller]** The server rejects the
    request with HTTP 403 because the target passkey's `userId` does
    not match the authenticated user — the client displays a localized
    error message explaining insufficient permissions

9. **[Branch -- new name is empty or blank]** The server rejects the
    request with HTTP 400 because the passkey name field is required
    and cannot be an empty string or whitespace-only value — the
    client displays a localized validation error message in the rename
    dialog

10. **[Server]** updates only the `name` column in the `passkey`
    table row for the target passkey with the new value and returns
    HTTP 200 with the updated passkey record — no other columns
    (`publicKey`, `credentialID`, `counter`, `transports`) are
    modified by this operation

11. **[Client]** closes the rename dialog and refreshes the passkey
    list so the updated friendly name is visible in the entry that was
    edited — the displayed name in that entry matches the new value
    submitted by the user

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| passkey_list_idle | dialog_open | User clicks the edit icon next to a passkey entry to open the rename dialog | The edit icon element is present on the passkey entry and the user is authenticated with a valid session |
| dialog_open | passkey_list_idle | User clicks the cancel button or presses Escape to dismiss the rename dialog | None — cancel is always available regardless of input state or loading status |
| dialog_open | rename_pending | User clicks the save button in the rename dialog to submit the new passkey name | Input value is non-empty after trimming and differs from the current passkey name and the save button is not already disabled |
| rename_pending | renamed | Server returns HTTP 200 confirming the passkey name update in the database | The `passkey` table row `name` column value equals the new name submitted in the request payload |
| rename_pending | rename_error | Server returns non-200 or the request times out before a response arrives from the server | HTTP response status does not equal 200 or the network request exceeds the configured timeout threshold |
| rename_error | dialog_open | Client re-enables the save button and displays a localized error message inside the dialog | Server error was transient and the passkey record is still present with its previous name in the database |
| renamed | passkey_list_refreshed | Client refreshes the passkey list to display the updated friendly name in the edited entry | The passkey entry name text content equals the new name after the client-side refresh completes |

## Business Rules

- **Rule rename-cosmetic-only:** IF the `updatePasskey` request
    succeeds and updates the `name` column in the `passkey` table THEN
    no other columns in the passkey row are modified — the `publicKey`,
    `credentialID`, `counter`, and `transports` columns retain their
    original values before and after the rename operation, ensuring the
    passkey continues to function identically during WebAuthn
    authentication ceremonies
- **Rule ownership-validation:** IF the target passkey's `userId`
    column does not match the authenticated caller's user ID THEN the
    server rejects the `updatePasskey` request with HTTP 403 AND the
    passkey name remains unchanged in the database — the server
    enforces this ownership check independently of any client-side
    guards so direct API calls from unauthorized users are rejected
- **Rule name-required:** IF the new passkey name submitted in the
    rename request is an empty string or contains only whitespace
    characters THEN the server rejects the `updatePasskey` request
    with HTTP 400 AND the client prevents submission by disabling the
    save button when the trimmed input value is empty — the server
    enforces this independently of the client-side guard to prevent
    blank passkey names via direct API calls
- **Rule error-retention:** IF the `updatePasskey` request fails due
    to a server error or network timeout THEN the passkey's name in
    the `passkey` table retains its previous value and the rename
    dialog remains open with the user's input preserved — the client
    re-enables the save button and displays a localized error message
    so the user retries without retyping the desired name

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner (passkey owner) | View all passkey entries on the security settings page, click the edit icon on any of their own passkey entries, edit the friendly name in the rename dialog, and submit the `updatePasskey` request to rename any passkey they own | Renaming passkeys that belong to other user accounts — the server rejects requests where the passkey `userId` does not match the caller's ID with HTTP 403 | The edit icon is visible on every passkey entry listed in the user's security settings page and the rename dialog is accessible for all of the user's own passkeys |
| Admin | View their own passkey entries on their security settings page and rename only passkeys they own — admin role does not grant cross-user passkey rename privileges | Renaming passkeys that belong to other user accounts — the `updatePasskey` endpoint checks passkey `userId` ownership, not organization role, so admin role provides no additional access to other users' passkeys | The admin sees only their own passkey entries on `/app/settings/security` and has no visibility into other users' registered passkeys |
| Member | View their own passkey entries on their security settings page and rename only passkeys they own — member role does not restrict access to self-owned passkey rename operations | Renaming passkeys that belong to other user accounts — the `updatePasskey` endpoint checks passkey `userId` ownership regardless of organization membership role | The member sees only their own passkey entries on `/app/settings/security` and has no visibility into other users' registered passkeys |
| Unauthenticated | None — the route guard redirects unauthenticated requests to `/signin` before the security settings page component renders any content or passkey data | Accessing `/app/settings/security` or calling the `updatePasskey` endpoint without a valid authenticated session — the server returns HTTP 401 for direct API calls | The security settings page is not rendered; the redirect to `/signin` occurs before any passkey UI or rename controls are mounted or visible |

## Constraints

- The `updatePasskey` endpoint enforces ownership validation
    server-side by comparing the passkey's `userId` column against the
    authenticated caller's user ID — the count of successful rename
    operations on passkeys owned by a different user equals 0 because
    the server validates ownership before any update occurs
- The rename dialog pre-fills the input field with the current passkey
    friendly name so the user can see the existing value — the input
    element's initial value equals the passkey's current `name` column
    value from the `passkey` table at the time the dialog opens
- After a successful rename the `passkey` table row's `name` column
    value equals the new name submitted in the request, and the passkey
    list displays the updated name in the entry that was edited without
    requiring a full page reload or re-authentication
- The rename dialog contains localized text rendered via i18n
    translation keys — the count of hardcoded English string literals
    in the rename dialog component equals 0, and all labels,
    placeholders, buttons, and error messages use translation keys
    from `@repo/i18n`
- The save button is disabled when the trimmed input value equals the
    current passkey name or is empty — the count of `updatePasskey`
    requests sent with an unchanged or empty name value from the dialog
    equals 0 under normal client-side operation
- The rename operation modifies only the `name` column in the
    `passkey` table — the count of UPDATE queries that modify
    `publicKey`, `credentialID`, `counter`, or `transports` columns
    during a rename operation equals 0

## Acceptance Criteria

- [ ] The security settings page at `/app/settings/security` displays a passkeys section listing all passkeys registered by the authenticated user — the passkey entry count equals the number of rows in the `passkey` table where `userId` matches the caller
- [ ] Each passkey entry displays the friendly name, device type, and creation date — the count of entries missing any of these 3 fields equals 0 in the passkeys section
- [ ] An edit icon is present next to each passkey entry in the list — the edit icon element count per passkey entry equals 1
- [ ] Clicking the edit icon opens a rename dialog with the current passkey name pre-filled — the input element value equals the current passkey name within 200ms of the click event
- [ ] The save button is disabled when the trimmed input value equals the current passkey name — the disabled attribute is present on the save button when the input value has not changed
- [ ] The save button is disabled when the trimmed input value is empty — the disabled attribute is present on the save button when the input field contains an empty string or whitespace-only characters
- [ ] Cancelling the dialog leaves the passkey name unchanged — the `passkey` table row `name` column value equals the original name and the count of `updatePasskey` requests sent equals 0 after the cancel button is clicked
- [ ] Confirming the rename calls `authClient.passkey.updatePasskey` with the correct credential ID and new name — the method invocation count equals 1 after the save click
- [ ] The save button displays a loading indicator and its `disabled` attribute is present while the rename request is in flight — the disabled attribute is present within 100ms of the save click
- [ ] A successful rename returns HTTP 200 and the `passkey` table row `name` column equals the new value — the response status equals 200 and the database column matches the submitted name
- [ ] After a successful rename the `publicKey`, `credentialID`, `counter`, and `transports` columns in the `passkey` table row retain their original values — the count of modified non-name columns equals 0
- [ ] After a successful rename the passkey list displays the updated name in the edited entry — the entry text content equals the new passkey name within 500ms after the client refresh completes
- [ ] A rename attempt targeting a passkey owned by a different user returns HTTP 403 — the response status equals 403 and the `passkey` table row `name` column remains unchanged
- [ ] A rename attempt with an empty name returns HTTP 400 — the response status equals 400 and the `passkey` table row `name` column retains the previous value
- [ ] All dialog labels, input placeholders, button text, and error messages are rendered via i18n translation keys — the count of hardcoded English string literals in the rename dialog component equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User clicks the save button twice in rapid succession before the first rename request completes | The save button is disabled on the first click, preventing duplicate rename requests — the server receives exactly 1 `updatePasskey` call and no duplicate update occurs | The disabled attribute is present on the save button within 100ms of the first click and the count of outbound `updatePasskey` requests equals 1 |
| User submits a name that is identical to the current passkey name by modifying and then reverting the input field | The client-side guard prevents submission because the save button is disabled when the trimmed input value equals the current name — no `updatePasskey` request is sent to the server | The disabled attribute is present on the save button and the count of outbound `updatePasskey` requests equals 0 after the user reverts the input |
| User submits a name containing only whitespace characters such as spaces or tabs in the input field | The client-side guard prevents submission because the save button is disabled for empty or whitespace-only input — additionally the server rejects the request with HTTP 400 if the guard is bypassed via a direct API call | The disabled attribute is present on the save button for whitespace-only input and a direct API call with whitespace-only name returns HTTP 400 |
| User loses network connectivity after clicking save but before the server responds with a result | The rename request times out on the client — the dialog remains open with a loading indicator and a localized error message appears so the user retries once connectivity returns | The error element is present in the dialog after the request timeout and the `passkey` table row `name` column retains its previous value in the database |
| User deletes the passkey from another browser tab while the rename dialog is still open in the current tab | The `updatePasskey` request reaches the server but the target passkey row no longer exists in the `passkey` table — the server returns HTTP 404 and the client displays a localized error message | The response status equals 404 and the client closes the rename dialog after displaying the error message for the deleted passkey |
| User submits a very long passkey name that exceeds the maximum allowed length for the name column in the database | The server rejects the request with HTTP 400 because the name exceeds the column length constraint — the client displays a localized validation error in the rename dialog | The response status equals 400 for names exceeding the column limit and the `passkey` table row `name` column retains its previous value |

## Failure Modes

- **Rename request fails due to a transient D1 database error during the passkey row update operation**
    - **What happens:** The client calls `authClient.passkey.updatePasskey` and the server's UPDATE query against the `passkey` table fails due to a transient Cloudflare D1 error or Worker timeout, leaving the passkey name unchanged and the original name still displayed in the passkeys list.
    - **Source:** Transient Cloudflare D1 database failure or network interruption between the Worker process and the D1 binding during the UPDATE operation execution on the `passkey` table row.
    - **Consequence:** The user receives an error response after clicking save — the passkey retains its original name in the database and the rename dialog remains visible until the user dismisses it or retries the operation.
    - **Recovery:** The server returns HTTP 500 and logs the D1 error with the query context and the target passkey ID — the client falls back to re-enabling the save button and displaying a localized error message so the user retries the rename once the D1 service recovers.

- **Unauthorized user crafts a direct API call to rename a passkey belonging to a different account**
    - **What happens:** An attacker with a valid authenticated session crafts a direct HTTP request to the `updatePasskey` endpoint using a passkey credential ID that belongs to a different user, attempting to rename another user's passkey without ownership authorization.
    - **Source:** Adversarial action where an authenticated user sends a hand-crafted API request directly to the rename endpoint using a credential ID discovered through enumeration or leaked data, bypassing the client-side UI that only displays the user's own passkeys.
    - **Consequence:** Without server-side ownership enforcement any authenticated user could rename passkeys belonging to other accounts, causing confusion about passkey identity and disrupting other users' security settings display.
    - **Recovery:** The `updatePasskey` handler rejects the request with HTTP 403 after verifying that the passkey's `userId` column does not match the caller — the server logs the unauthorized attempt with the caller's user ID, target passkey ID, and timestamp for audit purposes, and no passkey name update occurs.

- **Session expires between opening the rename dialog and clicking the save button to submit the new name**
    - **What happens:** The user opens the rename dialog, edits the passkey name, but their session expires before they click save — the `updatePasskey` request reaches the server with an invalid or expired session token and the server cannot resolve the calling user's identity for ownership validation.
    - **Source:** Session expiration due to the configured session TTL elapsing while the user has the rename dialog open and is composing the new passkey name, producing a stale session cookie in the subsequent API request.
    - **Consequence:** The rename request fails because the server cannot authenticate the caller — the user loses the name they typed in the dialog input field and the passkey retains its previous name in the database.
    - **Recovery:** The server returns HTTP 401 for the expired session and the client notifies the user by redirecting to `/signin` — after re-authentication the user navigates back to `/app/settings/security` and retries the rename with the desired name value.

## Declared Omissions

- This specification does not address registering a new passkey — that behavior is covered by a separate spec defining the WebAuthn credential creation ceremony and the `passkey` table insertion flow
- This specification does not address removing or deleting a passkey from the user's account — that behavior is covered by a separate spec defining the deletion confirmation dialog and the `passkey` table row removal flow
- This specification does not address how the passkey functions during WebAuthn authentication ceremonies — that behavior is defined in `user-signs-in-with-passkey.md` covering the credential verification and session creation flow
- This specification does not address rate limiting on the `updatePasskey` endpoint — that behavior is enforced by the global rate limiter covering all mutation endpoints uniformly across the API layer
- This specification does not address mobile passkey management because passkeys are not supported in the Expo React Native environment as documented in the mobile platform constraints

## Related Specifications

- [user-signs-in-with-passkey](user-signs-in-with-passkey.md) — Passkey sign-in flow that uses the credential verified by the same `passkey` table entries whose friendly names are managed by this rename spec
- [user-registers-a-passkey](user-registers-a-passkey.md) — Passkey registration ceremony that creates the `passkey` table entries with initial friendly names that the user can later change using this rename flow
- [user-removes-a-passkey](user-removes-a-passkey.md) — Passkey deletion flow that removes the `passkey` table entries whose names are managed by this spec, sharing the same ownership validation pattern
- [session-lifecycle](session-lifecycle.md) — Session management spec that governs the session creation, validation, and expiration logic used to authenticate the caller in the `updatePasskey` ownership check
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth server configuration including the passkey plugin that provides the `updatePasskey` endpoint and enforces ownership validation
- [database-schema](../foundation/database-schema.md) — Schema definitions for the `passkey` and `session` tables read and written during the rename operation and the ownership validation steps

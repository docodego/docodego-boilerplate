[← Back to Index](README.md)

# User Removes a Passkey

## Viewing Registered Passkeys

The user navigates to the security settings page at `/app/settings/security`. The passkeys section displays a list of all passkeys the user has [previously registered](user-registers-a-passkey.md). Each entry in the list shows the passkey's friendly name (or a default label if none was assigned), the device type, the date it was created, and the date it was last used for authentication. If the user has not registered any passkeys, the section shows a message: "No passkeys registered yet."

## Initiating Removal

The user locates the passkey they want to remove and clicks the "Delete" button next to it. A confirmation dialog appears asking the user to confirm that they want to permanently remove this passkey from their account. The dialog identifies the passkey by name so the user can verify they are deleting the correct one.

## Last Passkey Warning

If the passkey being deleted is the user's only registered passkey, the confirmation dialog includes an additional warning explaining that removing it will leave the account with no passkey-based authentication. The user can still sign in using other methods such as [email OTP](user-signs-in-with-email-otp.md) or [SSO](user-signs-in-with-sso.md), so the removal is allowed. The warning is informational, not a blocker — the user can proceed if they choose to.

## Server Processing

When the user confirms, the client calls `authClient.passkey.deletePasskey({ id })` with the credential ID of the passkey to remove. The server verifies that the passkey belongs to the authenticated user's account and then deletes the passkey record from the `passkey` table. The associated public key, credential ID, counter, and transport data are permanently removed.

## After Removal

The passkey list refreshes to reflect the deletion. The removed passkey no longer appears in the list. If it was the only passkey, the section returns to the empty state with the "No passkeys registered yet" message. The user can [register a new passkey](user-registers-a-passkey.md) at any time by clicking the "Register passkey" button.

## Failure Handling

If the deletion request fails due to a network error or server issue, an error toast appears and the passkey remains unchanged. The user can retry the deletion by clicking the "Delete" button again.

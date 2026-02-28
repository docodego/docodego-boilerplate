[← Back to Index](README.md)

# User Renames a Passkey

## Viewing Registered Passkeys

The user navigates to the security settings page at `/app/settings/security`. The passkeys section displays a list of all passkeys the user has [previously registered](user-registers-a-passkey.md). Each entry shows the passkey's friendly name (or a default label if none was assigned), the device type, and the creation date. When a user has multiple passkeys, distinguishing them by name becomes important — for example, telling apart "MacBook Pro" from "iPhone" or "Work Laptop."

## Initiating the Rename

The user locates the passkey they want to rename and clicks the edit icon or "Rename" option next to it. An inline input field or a small dialog with localized labels appears, pre-filled with the passkey's current name. The user can clear the field and type a new friendly name for the passkey.

## Submitting the New Name

The user submits the updated name. The client calls `authClient.passkey.updatePasskey({ id, name })` with the passkey's credential ID and the new name. The server validates that the passkey belongs to the authenticated user and updates the name in the `passkey` table. No other passkey fields — public key, credential ID, counter, or transports — are affected by a rename operation.

## After Renaming

The passkey list refreshes to show the updated name. The change is purely cosmetic and does not affect how the passkey functions during [sign-in](user-signs-in-with-passkey.md). The user can rename the same passkey again at any time by repeating the process. If the user wants to remove the passkey entirely instead, they can use the [delete option](user-removes-a-passkey.md).

## Failure Handling

If the rename request fails due to a network error or server issue, an error toast appears and the passkey's name remains unchanged. The user can retry by clicking the edit option again.

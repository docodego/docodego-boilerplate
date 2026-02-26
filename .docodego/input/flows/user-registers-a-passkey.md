[← Back to Index](README.md)

# User Registers a Passkey

## Starting Point

The user navigates to the security settings page at `/app/settings/security`. The passkeys section displays a list of registered passkeys. If the user has not registered any passkeys yet, the section shows a localized message: "No passkeys registered yet."

## Registration Ceremony

The user clicks the "Register passkey" button, which triggers `authClient.passkey.addPasskey()`. This initiates the WebAuthn registration ceremony in the browser. The browser prompts the user with their platform authenticator — this could be a fingerprint reader, facial recognition, or a device PIN, depending on the hardware and OS. The user completes the biometric or PIN prompt to confirm their identity.

## Server Storage and Naming

Once the ceremony succeeds, the server stores the passkey data in the `passkey` table. The stored fields include the public key, credential ID, counter, device type, whether the credential is backed up, and the supported transports. The user can optionally assign a friendly name to the passkey, such as "MacBook Pro Touch ID," to help identify it later among multiple registered passkeys.

## After Registration

The passkey list refreshes to show the newly registered passkey with its name (or a default label), the device type, and the creation date. Each passkey in the list has a Delete button. Clicking it triggers a confirmation dialog, and upon confirmation, the client calls `authClient.passkey.deletePasskey({ id })` to remove the passkey from the account.

## Failure Handling

If the WebAuthn ceremony fails or the user cancels the browser prompt, an error toast appears and no passkey is created. The user can try again by clicking the "Register passkey" button once more.

[← Back to Index](README.md)

# User Signs In with Passkey

## Initiating Passkey Authentication

The user arrives at `/signin` and sees a translated "Sign in with passkey" button alongside other authentication options. They click it, and the client calls `authClient.signIn.passkey()`, which initiates the WebAuthn authentication ceremony. The browser immediately presents its native biometric or PIN prompt — Touch ID on macOS, Windows Hello on Windows, or the platform-specific equivalent on other systems. The user authenticates using their biometric (fingerprint, face) or device PIN.

## Server Verification

The browser sends the signed authentication response to the server. The server looks up the credential by `credentialID` in the `passkey` table and retrieves the stored `publicKey`. It verifies the signature on the authenticator response using that public key, confirming the user possesses the private key associated with the registered passkey. The server also checks and increments the `counter` value to prevent replay attacks — if the counter in the response is not greater than the stored counter, the authentication is rejected.

## Successful Sign-In

Once the credential is verified, the server creates a session in the `session` table with the standard fields: signed token cookie, `userId`, `ipAddress`, `userAgent`, and `expiresAt` set to 7 days out. The `docodego_authed` hint cookie is set alongside the session cookie so that Astro pages can detect authenticated state client-side without a server round-trip. The client redirects the user to `/app`.

## Cancellation and Errors

If the user dismisses the browser's biometric prompt — clicking "Cancel" or pressing Escape — no request is sent to the server. The user remains on the `/signin` page with no error shown, free to try again or choose a different sign-in method. If the browser sends a credential that the server cannot match to any entry in the `passkey` table, the server returns an error and the UI displays a localized message suggesting the user try another sign-in method such as email OTP.

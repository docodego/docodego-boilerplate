# Guest Upgrades to Full Account

## Deciding to Upgrade

An anonymous user who has been browsing the application as a guest decides to link a real email address. They click the persistent upgrade banner or navigate to their account settings, where they find an option to convert their guest account into a full account. The user enters their real email address and the system initiates the standard OTP verification flow — a 6-digit code is generated, stored in the `verification` table with a 5-minute expiry, and sent to the provided email (logged to console in development).

## Verifying and Linking

The user receives the OTP and enters it through the same six-digit code entry UI used during normal sign-in. Once the code is verified, Better Auth's `onLinkAccount` callback fires with `{ anonymousUser, newUser }`, signaling that a guest identity is being merged into a full account. The system migrates all guest data — preferences, drafts, and any other activity accumulated during the anonymous session — to the new full account. The original anonymous user record is deleted and the `isAnonymous` flag is cleared from the now-upgraded user.

## Continuing as a Full User

After the upgrade completes, the user continues their session seamlessly. Their existing session remains valid — no re-authentication is required. All activity from the guest period is preserved and attributed to the new full account. The upgrade banner disappears since the user now has a verified email. From this point forward the user signs in with their real email via OTP, passkey, or any other method they configure.

[← Back to Index](README.md)

# Banned User Attempts Sign-In

## The Banned User Tries to Sign In

A user whose account has been [banned by an app admin](app-admin-bans-a-user.md) arrives at the sign-in page and attempts to authenticate. The user may try any available sign-in method: [email OTP](user-signs-in-with-email-otp.md), [passkey](user-signs-in-with-passkey.md), or [SSO](user-signs-in-with-sso.md). The sign-in form accepts the input and processes it normally up to the point of credential verification.

## The Server Rejects the Attempt

After the user's credentials are verified as correct, the server checks the `user.banned` field on the user's record. Because the user is banned, the server rejects the sign-in attempt regardless of valid credentials. The server does not create a session. The rejection response includes the ban metadata: the `banReason` field if the app admin provided a reason when issuing the ban, and the `banExpires` field if the ban is temporary. No session token or authentication cookie is set.

## The UI Displays the Ban Message

The client receives the ban rejection and displays a dedicated localized ban message screen instead of the usual error toast. This screen clearly communicates that the account has been banned and that access is denied. If a ban reason was provided, it is displayed so the user understands why the action was taken — for example, "Your account has been banned for violating community guidelines." If the ban has an expiration date, the screen shows when the ban will be lifted — for example, "This ban expires on March 15, 2026." If the ban is permanent, the screen states that the ban is indefinite and does not display an expiration date.

## No Bypass Is Possible

The ban screen does not offer any way to circumvent the ban. There is no "try again" button, no appeal form, and no alternative sign-in method that would succeed. The user can only navigate back to the landing page. Attempting to sign in again through any method results in the same ban rejection. The ban remains in effect until it either expires on its scheduled date or is manually lifted by an app admin who [unbans the user](app-admin-unbans-a-user.md).

## Temporary Ban Expiration

If the ban was set with an expiration date and that date has passed, the server no longer treats the user as banned. The `user.banned` field is effectively ignored once the current time exceeds `user.banExpires`. The user can then sign in normally through any authentication method, and the application behaves as if the ban never existed. No action from an app admin is required for a temporary ban to expire.

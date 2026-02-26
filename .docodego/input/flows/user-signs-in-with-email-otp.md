[← Back to Index](README.md)

# User Signs In with Email OTP

## Arriving at Sign-In

The user navigates to `/signin` and sees the authentication page. Among the available options, they find an email input field with a "Send code" button. The user types their email address and clicks "Send code." The client calls `authClient.emailOtp.sendVerificationOtp({ email, type: "sign-in" })` to request a one-time passcode.

## Server Generates the OTP

The server generates a 6-digit numeric OTP and stores it in the `verification` table with a 5-minute expiry timestamp. It then [dispatches the code via email](system-sends-otp-email.md) — in development, the code is logged to the console instead. The server responds with a generic success message regardless of whether the email is associated with an existing account. This enumeration protection ensures that an attacker cannot probe the system to discover which emails are registered.

## Entering the Code

The UI transitions to a code entry step showing six individual digit inputs. As the user types each digit, focus automatically advances to the next input. If the user pastes a full 6-digit code, it fills all inputs at once. Once all six digits are present, the client calls `authClient.signIn.emailOtp({ email, otp })` to verify the code.

## Successful Sign-In

When the code is correct, the server creates a new session in the `session` table, recording the session token as a signed cookie along with the user's `ipAddress`, `userAgent`, and an `expiresAt` timestamp set to 7 days from now. The server also sets the `docodego_authed` hint cookie — a JS-readable, non-httpOnly cookie that Astro pages use to prevent a flash of unauthenticated content (FOUC). The client then redirects the user to `/app`. If the email does not belong to an existing user, a new user record is automatically created since `disableSignUp` is set to `false` — the OTP sign-in flow doubles as a sign-up flow for new users.

## Wrong or Expired Code

If the user enters an incorrect code, the UI displays an inline error message beneath the code inputs. The user can retry up to 3 times. After 3 failed attempts, the OTP is invalidated and the user must request a new code. If the code has expired (more than 5 minutes have passed since it was generated), the UI displays a message explaining the code has expired and prompts the user to request a fresh one by clicking "Send code" again.

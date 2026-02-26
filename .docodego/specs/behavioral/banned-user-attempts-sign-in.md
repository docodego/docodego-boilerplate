[← Back to Roadmap](../ROADMAP.md)

# Banned User Attempts Sign-In

## Intent

This spec defines the behavior when a banned user attempts to sign in to the DoCodeGo boilerplate. A user whose account has been banned by an app admin arrives at `/signin` and attempts to authenticate via any method (email OTP, passkey, or SSO). The server verifies the credentials normally, then checks the `user.banned` field — if the user is banned and the ban has not expired, the server rejects the sign-in attempt without creating a session. The client displays a dedicated localized ban message screen showing the ban reason (if provided) and expiration date (if temporary). No bypass is available — the user can only navigate back to the landing page. Temporary bans expire automatically when the current time exceeds `user.banExpires`, after which the user can sign in normally without admin intervention. This spec ensures that banned users receive clear feedback and that the ban is enforced consistently across all sign-in methods.

## Acceptance Criteria

- [ ] After credential verification succeeds, the server checks the `user.banned` field — the ban check is present in the sign-in flow after credential validation and before session creation
- [ ] If `user.banned` equals true and the ban has not expired, the server rejects the sign-in — the count of session records created for banned users equals 0
- [ ] The server returns a rejection response that includes `banReason` (if present) and `banExpires` (if present) — both fields are present in the response body when the admin provided them
- [ ] No session token or authentication cookie is set for a banned user — the `Set-Cookie` header for the session cookie is absent from the rejection response
- [ ] The `docodego_authed` hint cookie is not set for a banned user — the hint cookie is absent from the rejection response
- [ ] The client displays a dedicated localized ban message screen instead of a generic error toast — the ban screen element is present and visible after the rejection
- [ ] If a ban reason was provided by the admin, the ban screen displays the reason text — the reason element is present and non-empty when `banReason` is non-null
- [ ] If the ban reason is absent (null), the ban screen displays a generic ban message without a reason — the reason element is absent and a default message is present
- [ ] If the ban has an expiration date, the ban screen displays when the ban will be lifted — the expiration date element is present and non-empty when `banExpires` is non-null
- [ ] If the ban is permanent (no expiration), the ban screen states the ban is indefinite — the permanent ban message element is present and the expiration element is absent
- [ ] The ban screen does not contain a "try again" button, appeal form, or alternative sign-in option — the count of interactive sign-in elements on the ban screen equals 0
- [ ] The ban screen contains a link or button to navigate back to the landing page — the navigation element is present and functional
- [ ] The ban enforcement is consistent across all 3 sign-in methods (email OTP, passkey, SSO) — the ban check is present in the common sign-in pipeline, not per-method
- [ ] If `user.banExpires` is set and the current time exceeds the expiry timestamp, the server treats the user as not banned — the sign-in proceeds normally and a session is created with the session record present
- [ ] All text on the ban screen is rendered via i18n translation keys — the count of hardcoded English strings on the ban screen equals 0

## Constraints

- The ban check occurs after credential verification, not before — the server does not reveal whether an email is banned before the user provides valid credentials. This maintains the same enumeration protection as the normal sign-in flow, where the server does not disclose account status to unauthenticated requests.
- The ban is enforced server-side in the common sign-in pipeline — the ban check is not implemented per sign-in method. The count of separate ban check implementations across email OTP, passkey, and SSO handlers equals 0. A single check point covers all methods.
- Temporary ban expiration is automatic and requires no admin action — when the current time exceeds `user.banExpires`, the ban is no longer enforced. The server does not update the `user.banned` field to false; it simply ignores the ban when the expiry has passed. The `user.banned` field remains true in the database until an admin explicitly unbans the user.
- The ban screen is a dead end with no bypass — there are no alternative authentication paths, retry buttons, or appeal mechanisms on the screen. The only interactive element is a navigation link back to the landing page.

## Failure Modes

- **Ban check skipped due to code error**: A refactoring of the sign-in pipeline inadvertently removes or bypasses the ban check, allowing banned users to create sessions and access the application. The CI test suite includes a test that attempts sign-in with a banned user fixture and asserts that the response status is not 200 and no session is created — the test returns error if the ban is not enforced, blocking the build.
- **Temporary ban not expiring correctly**: The ban expiry comparison uses a timezone-unaware timestamp or incorrect date parsing, causing a temporary ban to remain in effect after its scheduled expiration date. The server uses UTC timestamps for all ban expiry comparisons, and the CI test suite includes a test that sets `banExpires` to a past UTC timestamp and asserts that sign-in succeeds, the test returns error and logs the timestamp mismatch if the ban is still enforced.
- **Ban metadata missing from rejection response**: The server rejects the banned user's sign-in but fails to include the `banReason` or `banExpires` fields in the response body due to a serialization error, causing the ban screen to display a generic message without the specific reason or expiration. The client falls back to displaying a default ban message when the fields are absent, and logs a warning that the ban metadata was missing from the server response for diagnostics.
- **Banned user attempts SSO callback bypass**: A banned user authenticates at an external IdP and the SSO callback arrives at the server with valid tokens, attempting to create a session by bypassing the ban check at the initial sign-in step. The ban check is present in the SSO callback handler after token validation and before session creation, and the server rejects the callback and returns error HTTP 403, preventing session creation for the banned user.

## Declared Omissions

- Admin banning a user (covered by `app-admin-bans-a-user.md`)
- Admin unbanning a user (covered by `app-admin-unbans-a-user.md`)
- Ban enforcement on existing active sessions (admin revokes sessions separately via `app-admin-revokes-user-sessions.md`)
- Guest user ban behavior (anonymous users have no email-linked identity to ban)

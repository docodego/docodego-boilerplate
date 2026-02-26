[← Back to Roadmap](../ROADMAP.md)

# Banned User Attempts Sign-In

## Intent

This spec defines the behavior when a banned user attempts to sign in to the DoCodeGo boilerplate. A user whose account has been banned by an app admin arrives at `/signin` and attempts to authenticate via any method (email OTP, passkey, or SSO). The server verifies the credentials normally, then checks the `user.banned` field — if the user is banned and the ban has not expired, the server rejects the sign-in attempt without creating a session. The client displays a dedicated localized ban message screen showing the ban reason (if provided) and expiration date (if temporary). No bypass is available — the user can only navigate back to the landing page. Temporary bans expire automatically when the current time exceeds `user.banExpires`, after which the user can sign in normally without admin intervention. This spec ensures that banned users receive clear feedback and that the ban is enforced consistently across all sign-in methods.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Better Auth | read | Every sign-in attempt after credential verification completes | The sign-in flow fails entirely and the error handler falls back to a generic authentication error JSON response with HTTP 500 |
| D1 (Cloudflare SQL) | read | Ban check queries the `user.banned` and `user.banExpires` fields from the user record | The ban check cannot complete and the error handler falls back to a 500 response, blocking sign-in rather than allowing a potentially banned user through |
| `@repo/i18n` | read | Rendering the ban message screen on the client with localized ban reason and expiration text | The client falls back to the default English locale strings so the ban screen remains readable but untranslated for non-English users |
| `@repo/contracts` | read | Compile time — the ban rejection response shape is defined in the shared contracts package | The build fails at compile time because the response type cannot be resolved and CI alerts to block deployment |

## Behavioral Flow

1. **[User]** → a user whose account has been banned by an app admin arrives at the sign-in page and attempts to authenticate using any available sign-in method: email OTP, passkey, or SSO — the sign-in form accepts the input and processes it normally up to the point of credential verification
2. **[Server — Auth Pipeline]** → after the user's credentials are verified as correct, the server checks the `user.banned` field on the user's record — because the user is banned, the server rejects the sign-in attempt regardless of valid credentials and does not create a session
3. **[Server — Ban Rejection]** → the rejection response includes the ban metadata: the `banReason` field if the app admin provided a reason when issuing the ban, and the `banExpires` field if the ban is temporary — no session token or authentication cookie is set
4. **[Client — Ban Screen]** → the client receives the ban rejection and displays a dedicated localized ban message screen instead of the usual error toast, clearly communicating that the account has been banned and that access is denied
5. **[Client — Ban Screen]** → if a ban reason was provided, the screen displays it so the user understands why the action was taken (for example, "Your account has been banned for violating community guidelines") — if the ban has an expiration date, the screen shows when the ban will be lifted (for example, "This ban expires on March 15, 2026") — if the ban is permanent, the screen states that the ban is indefinite and does not display an expiration date
6. **[User]** → the ban screen does not offer any way to circumvent the ban — there is no "try again" button, no appeal form, and no alternative sign-in method that would succeed — the user can only navigate back to the landing page
7. **[User]** → attempting to sign in again through any method results in the same ban rejection — the ban remains in effect until it either expires on its scheduled date or is manually lifted by an app admin who unbans the user
8. **[Server — Ban Expiration]** → if the ban was set with an expiration date and that date has passed, the server no longer treats the user as banned — the `user.banned` field is effectively ignored once the current time exceeds `user.banExpires` and the user can then sign in normally through any authentication method
9. **[Server — Ban Expiration]** → the application behaves as if the ban never existed after expiration — no action from an app admin is required for a temporary ban to expire automatically

## State Machine

No stateful entities. The ban check is a single evaluation within the sign-in request-response cycle — the `user.banned` field is read but not modified by this flow, and no new entity lifecycle is introduced by the ban rejection.

## Business Rules

- **Rule ban-active:** IF `user.banned` equals true AND (`user.banExpires` is null OR the current UTC time is less than or equal to `user.banExpires`) THEN the server rejects the sign-in attempt, returns the ban rejection response, and does not create a session
- **Rule ban-expired:** IF `user.banned` equals true AND `user.banExpires` is set AND the current UTC time exceeds `user.banExpires` THEN the server treats the user as not banned and proceeds with session creation normally without requiring admin intervention
- **Rule ban-reason-display:** IF the ban rejection response includes a non-null `banReason` field THEN the ban screen displays the admin-provided reason text; otherwise the ban screen falls back to a generic default ban message
- **Rule ban-expiry-display:** IF the ban rejection response includes a non-null `banExpires` field THEN the ban screen displays the formatted expiration date and time; otherwise the ban screen displays a permanent ban notice indicating no expiration

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Banned User (active ban) | Submit credentials for verification, view the ban message screen, navigate back to the landing page | Create a session, access any authenticated route, retry sign-in from the ban screen, use alternative sign-in methods to bypass the ban | Can see the ban reason and expiration date if provided by the admin, but cannot see any authenticated content |
| Banned User (expired ban) | Submit credentials and complete the full sign-in flow normally, same as an unbanned user | N/A — treated as a normal user for sign-in purposes once the ban has expired | Same as an authenticated user after successful sign-in |

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

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A banned user has `banExpires` set to a timestamp exactly equal to the current UTC time at the moment of the ban check evaluation | The server treats the ban as still active because the expiry comparison uses a strict greater-than check, meaning the ban is active when current time is less than or equal to `banExpires` | The sign-in is rejected, no session is created, and the ban screen is displayed with the expiration date shown |
| A banned user has `banReason` set to an empty string rather than null, indicating the admin cleared the reason field after initially providing one | The client treats an empty string as equivalent to null for display purposes and falls back to the generic default ban message on the ban screen | The ban screen shows the generic default message and the reason-specific element is absent from the rendered output |
| A banned user submits valid credentials via SSO and the external IdP callback arrives at the server with valid tokens after the user authenticated externally | The ban check is present in the SSO callback handler after token validation and before session creation, rejecting the callback with an error response and preventing session creation | The server returns an error HTTP 403 response for the SSO callback and no session record is created for the banned user |
| A banned user has `banExpires` set to a past timestamp by one second, and the user submits credentials at the exact moment the ban should have expired | The server compares the current UTC time against `banExpires` and determines the ban has expired because the current time exceeds the expiry timestamp | The sign-in proceeds normally, a session is created, and the user is redirected to the authenticated dashboard |
| The server returns a ban rejection response but the `banExpires` field contains an unparseable or malformed date string that the client cannot format | The client falls back to displaying the permanent ban notice message because it cannot determine a valid expiration date from the malformed value | The ban screen shows the permanent ban message instead of a formatted date, and a warning is logged on the client side |
| A user's ban status changes from banned to unbanned by an admin while the user is on the ban screen viewing the ban message | The ban screen is a static display with no polling or real-time updates — the user must navigate back to the landing page and attempt sign-in again to benefit from the unban | The ban screen remains displayed until the user navigates away, and a subsequent sign-in attempt succeeds after the admin unbans the user |

## Failure Modes

- **Ban check skipped due to code error during sign-in pipeline refactoring**
    - **What happens:** A refactoring of the sign-in pipeline inadvertently removes or bypasses the ban check middleware, allowing banned users to create sessions and access the authenticated application areas.
    - **Source:** Incorrect code change during development that removes the ban check from the common sign-in pipeline path.
    - **Consequence:** Banned users gain full application access, undermining admin enforcement and potentially exposing the platform to abusive users who were previously banned.
    - **Recovery:** The CI test suite includes a test that retries sign-in with a banned user fixture and asserts that the response status is not 200 and no session is created — CI alerts and blocks deployment if the ban check is missing.
- **Temporary ban not expiring correctly due to timezone mismatch in timestamp comparison logic**
    - **What happens:** The ban expiry comparison uses a timezone-unaware timestamp or incorrect date parsing library, causing a temporary ban to remain enforced after its scheduled UTC expiration date has passed.
    - **Source:** Incorrect date handling in the ban check logic that fails to normalize timestamps to UTC before comparison.
    - **Consequence:** Users with expired temporary bans are locked out indefinitely until an admin manually unbans them, creating unnecessary support burden and degraded user experience.
    - **Recovery:** The server falls back to UTC timestamps for all ban expiry comparisons, and the CI test suite includes a test that sets `banExpires` to a past UTC timestamp and asserts that sign-in succeeds — CI alerts and blocks deployment if the expired ban is still enforced.
- **Ban metadata missing from rejection response due to serialization error in response construction**
    - **What happens:** The server rejects the banned user's sign-in but fails to include the `banReason` or `banExpires` fields in the response body due to a field omission or serialization error in the response builder.
    - **Source:** Incorrect response construction that omits optional ban metadata fields from the serialized JSON response body sent to the client.
    - **Consequence:** The ban screen displays only a generic message without the specific admin-provided reason or expiration date, reducing transparency for the banned user.
    - **Recovery:** The client falls back to displaying a default ban message when the metadata fields are absent, and the client degrades gracefully by logging a warning that ban metadata was missing from the server response for diagnostics.
- **Banned user attempts SSO callback bypass by authenticating directly with external identity provider**
    - **What happens:** A banned user authenticates at an external IdP and the SSO callback arrives at the server with valid OAuth tokens, attempting to create a session by bypassing the initial sign-in ban check step entirely.
    - **Source:** Adversarial action by a banned user who navigates directly to the external IdP authentication URL to obtain valid tokens.
    - **Consequence:** If the SSO callback handler lacks its own ban check, the banned user successfully creates a session and gains full application access despite the active ban.
    - **Recovery:** The ban check is present in the SSO callback handler after token validation and before session creation — the server rejects the callback with HTTP 403 and escalates by logging the bypass attempt for admin review.

## Declared Omissions

- This specification does not address the admin workflow for banning a user — that behavior is fully defined in the separate `app-admin-bans-a-user.md` specification
- This specification does not address the admin workflow for unbanning a user — that behavior is fully defined in the separate `app-admin-unbans-a-user.md` specification
- This specification does not address ban enforcement on existing active sessions — admin revocation of active sessions is covered separately in `app-admin-revokes-user-sessions.md`
- This specification does not address guest user ban behavior because anonymous guest users have no email-linked identity or user record that can be banned
- This specification does not address the ban appeal or dispute process because no appeal mechanism exists in the current boilerplate scope

## Related Specifications

- [app-admin-bans-a-user](app-admin-bans-a-user.md) — Defines the admin workflow for banning a user, including setting the `banned`, `banReason`, and `banExpires` fields
- [app-admin-unbans-a-user](app-admin-unbans-a-user.md) — Defines the admin workflow for unbanning a user, including clearing the ban fields and restoring access
- [app-admin-revokes-user-sessions](app-admin-revokes-user-sessions.md) — Defines admin revocation of active sessions, which complements the banning flow by forcibly terminating any existing authenticated sessions for the banned user
- [auth-server-config](../foundation/auth-server-config.md) — Better Auth plugin configuration and session strategy that the ban check integrates with during the sign-in pipeline
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) — Email OTP sign-in flow that the ban check intercepts after credential verification succeeds, serving as one of the three authentication methods subject to ban enforcement

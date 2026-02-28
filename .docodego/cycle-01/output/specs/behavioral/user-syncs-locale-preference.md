---
id: SPEC-2026-050
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Syncs Locale Preference

## Intent

This spec defines the flow by which an authenticated user changes their
language preference on any platform — web, mobile, desktop, or browser
extension — and that preference is persisted to the server by setting the
`user.preferredLocale` field in the database via an API call. When the
user signs in on a different device, the client reads `preferredLocale`
during initialization and applies it immediately, ensuring consistent
language selection across every platform without requiring the user to
reconfigure the setting. Server-generated content such as OTP verification
emails and invitation emails resolves the recipient's preferred locale
from this field, and when the field is null the system falls back to
platform-specific detection chains: `Accept-Language` header on the API
side, localStorage then `navigator.language` on the web, and device locale
via `expo-localization` on mobile.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `user.preferredLocale` update endpoint | write | The client calls this endpoint when the user selects a new language in the locale picker on any platform (web, mobile, desktop, or extension) | The client receives an error response and displays a localized error toast via Sonner — the locale change is applied locally but the server record retains the previous value until the endpoint recovers |
| `user` table (D1) | read/write | On sign-in the client reads `preferredLocale` to apply the stored language, and on locale change the endpoint writes the selected locale code to the user record | The read returns a 500 error and the client falls back to the platform-specific locale detection chain, and the write rejects with a 500 so the user record retains the previous locale value |
| Email service (OTP and invitation locale resolution) | read | When composing transactional emails such as OTP verification or invitation emails, the service reads the recipient's `preferredLocale` to determine which language template to render | The email service falls back to parsing the `Accept-Language` header from the original request to determine locale, and if that header is absent the email defaults to the English locale template |
| `@repo/i18n` | read | All locale picker labels, confirmation toasts, error messages, and fallback strings are rendered through translation keys provided by the i18n infrastructure package | Translation function falls back to the default English locale strings so the locale settings interface remains fully usable without localized text for the currently active locale |

## Behavioral Flow

1. **[User]** opens the language or locale settings on any platform — web
    settings page, mobile settings screen, desktop preferences panel, or
    browser extension options page — and selects a new language from the
    locale picker dropdown or list
2. **[Client]** applies the selected locale immediately on the local
    device by updating the i18n runtime configuration, causing all
    visible UI text to re-render in the newly selected language without
    waiting for the server round-trip to complete
3. **[Client]** sends an API request to the `user.preferredLocale` update
    endpoint with the selected locale code (for example `en` or `ar`),
    persisting the user's explicit language choice to the server for
    cross-device consistency
4. **[Server]** receives the update request, validates that the locale
    code matches a supported locale from the application's locale
    registry, and writes the value to the `user.preferredLocale` column
    in the D1 user table
5. **[Branch — mutation succeeds]** The server returns a 200 response
    confirming the locale was persisted — the client displays a localized
    success toast via Sonner confirming the language preference was saved
    and the `preferredLocale` field in the database now equals the
    selected locale code
6. **[Branch — mutation fails]** The server returns a non-200 response or
    the request times out — the client displays a localized error toast
    via Sonner describing what went wrong, and the local locale change
    remains active on the current device while the server record retains
    the previous value until a successful retry
7. **[User]** signs in on a different device or platform at a later time,
    and the client reads the `user.preferredLocale` field during the
    post-authentication initialization sequence
8. **[Client]** checks whether `preferredLocale` is non-null — if the
    field contains a locale code, the client applies that locale
    immediately by configuring the i18n runtime to use the stored
    preference instead of relying on browser, device, or OS-level locale
    detection
9. **[Client]** checks whether `preferredLocale` is null — if the field
    is null, the client falls back to the platform-specific detection
    chain: the web reads localStorage then `navigator.language`, the
    mobile app reads device locale via `expo-localization`, and the
    desktop app inherits the web detection chain through the Tauri wrapper
10. **[Server]** when composing a transactional email (OTP verification or
    invitation), resolves the recipient's preferred locale by reading
    `user.preferredLocale` from the database — if the field is non-null,
    the email template is rendered in that locale regardless of which
    device or browser triggered the action
11. **[Server]** when `user.preferredLocale` is null for the email
    recipient, falls back to parsing the `Accept-Language` header from
    the original HTTP request to determine locale, and if that header is
    absent or unparseable the email defaults to the English locale
    template

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| idle | locale_selected | User selects a new language from the locale picker on any platform | User is authenticated and the selected locale differs from the current active locale |
| locale_selected | local_applied | Client applies the selected locale to the i18n runtime on the current device | The selected locale code matches a supported locale in the i18n configuration |
| local_applied | syncing | Client sends the API request to persist `preferredLocale` to the server | The user is authenticated and the session token is valid for write operations |
| syncing | synced | Server returns 200 and the `preferredLocale` field in the database equals the selected locale code | HTTP response status equals 200 and the response body confirms the update was persisted |
| syncing | sync_error | Server returns non-200 or the network request times out before receiving a response | HTTP response status does not equal 200 or the request exceeds the configured timeout threshold |
| sync_error | syncing | User retries by re-selecting the same locale or clicking a retry action in the error toast | The user is authenticated and the session token remains valid for write operations |
| synced | idle | Success toast is displayed and the locale preference is confirmed persisted on the server | Toast notification is rendered and the client state resets to idle for the next locale change |
| signin_init | locale_resolved | Client reads `preferredLocale` during post-authentication initialization and the field is non-null | The `preferredLocale` value matches a supported locale in the i18n locale registry |
| signin_init | fallback_resolved | Client reads `preferredLocale` during post-authentication initialization and the field is null | The `preferredLocale` field is null and the platform-specific detection chain returns a valid locale |
| locale_resolved | idle | Client applies the stored `preferredLocale` to the i18n runtime, overriding device or browser defaults | The i18n runtime accepts the locale code and re-renders all UI text in the stored language |
| fallback_resolved | idle | Client applies the platform-detected locale from the fallback chain to the i18n runtime | The fallback detection chain returns a non-empty locale code that the i18n runtime accepts |

## Business Rules

- **Rule preferred-locale-overrides-detection:** IF `user.preferredLocale`
    is non-null THEN the client and server use that value as the
    authoritative locale for the user, overriding all platform-specific
    detection mechanisms including `Accept-Language` header, localStorage,
    `navigator.language`, and `expo-localization` device locale
- **Rule fallback-chain-when-null:** IF `user.preferredLocale` is null
    THEN the system falls back to the platform-specific detection chain —
    the API parses the `Accept-Language` header, the web checks
    localStorage then `navigator.language`, and the mobile app reads
    device locale via `expo-localization` — and the system never stores
    a default value in the `preferredLocale` field without an explicit
    user action
- **Rule cross-device-apply-on-signin:** IF the user signs in on a new
    device and `user.preferredLocale` is non-null THEN the client reads
    the stored locale during post-authentication initialization and
    applies it immediately to the i18n runtime before rendering the
    dashboard, ensuring the user sees the interface in their chosen
    language from the first screen after sign-in
- **Rule email-uses-preferred-locale:** IF the server composes a
    transactional email (OTP verification or invitation) and the
    recipient's `user.preferredLocale` is non-null THEN the email
    template is rendered in that locale, taking priority over the
    `Accept-Language` header from the original request that triggered
    the email — and if `preferredLocale` is null, the email service
    falls back to parsing the `Accept-Language` header and then to the
    English locale template

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner (of the user account) | View the locale picker with the current language highlighted, select a new locale from the picker, trigger the API call to persist `preferredLocale` to the server, and see success or error toast | Change another user's `preferredLocale` — the update endpoint only accepts writes targeting the authenticated user's own record in the database | The locale picker is visible and interactive, showing all supported locales, and the current selection reflects the active locale |
| Admin (any org admin viewing their own settings) | View and change their own locale preference identically to the Owner row — locale settings are user-level and not organization-scoped, so org role has no effect | Change another user's `preferredLocale` — the same restriction applies regardless of the user's administrative role within any organization | The locale picker is visible and interactive identically to the Owner row because locale settings are user-scoped |
| Member (any org member viewing their own settings) | View and change their own locale preference identically to the Owner row — locale settings are user-level and not organization-scoped, so org role has no effect | Change another user's `preferredLocale` — the same restriction applies regardless of the user's membership role within any organization | The locale picker is visible and interactive identically to the Owner row because locale settings are user-scoped |
| Unauthenticated | None — the locale settings page requires authentication and the update endpoint rejects unauthenticated requests with HTTP 401, preventing any locale persistence | Access to the locale settings page, viewing the locale picker, or submitting any `preferredLocale` update request to the server endpoint | The locale settings page is not rendered; the route guard redirects to `/signin` immediately upon navigation |

## Constraints

- The `user.preferredLocale` column is nullable — the count of non-null
    values for users who have never explicitly selected a language equals
    0 in the database at all times
- The locale code stored in `preferredLocale` is validated against the
    application's supported locale registry — the count of records
    containing unsupported locale codes equals 0 in the user table
- The API call to update `preferredLocale` completes within 2000ms
    under normal conditions — the 95th-percentile response time for the
    update endpoint is at most 2000ms
- The local locale change is applied before the server round-trip
    completes — the count of milliseconds between the user selecting a
    locale and the UI re-rendering in that language equals 0 network
    dependency because the local change is synchronous
- All locale picker labels, toast messages, and error descriptions are
    rendered via i18n translation keys — the count of hardcoded English
    strings in the locale settings UI components equals 0
- The update endpoint rejects unauthenticated requests with HTTP 401 —
    the count of successful `preferredLocale` writes from unauthenticated
    callers equals 0

## Acceptance Criteria

- [ ] Selecting a new language in the locale picker immediately re-renders all visible UI text in the selected language on the current device — the count of UI elements still displaying the previous language after locale selection equals 0 within 500ms
- [ ] The client sends an API request to the `preferredLocale` update endpoint with the selected locale code after the user picks a new language — the HTTP request payload contains the selected locale code and the request count equals 1 per locale change
- [ ] On successful API response with status 200 the `user.preferredLocale` field in the D1 database equals the selected locale code — a database query for the user record returns the new locale value and the count of mismatched locale fields equals 0
- [ ] On successful API response a localized success toast appears via Sonner — the toast element is present and visible within 500ms of the API returning a 200 response
- [ ] On API failure or network timeout a localized error toast appears via Sonner — the error toast element is present and visible after the API returns a non-200 response or the request times out
- [ ] On API failure the local locale change remains active on the current device — the count of UI elements that reverted to the previous language after a non-200 server response equals 0 and the i18n runtime locale is non-empty
- [ ] Signing in on a new device with a non-null `preferredLocale` applies the stored locale during initialization — the i18n runtime locale is non-empty and the count of screens rendered before the stored locale is applied equals 0 after authentication completes
- [ ] Signing in on a new device with a null `preferredLocale` falls back to the platform-specific detection chain — the i18n runtime locale is non-empty and the count of locale detection sources consulted is at least 1 from the platform-specific fallback chain
- [ ] An OTP verification email sent to a user with a non-null `preferredLocale` is rendered in that locale — the count of email sections (subject and body) not matching the stored locale translation template equals 0
- [ ] An invitation email sent to a user with a non-null `preferredLocale` is rendered in that locale — the count of email sections using the `Accept-Language` header locale instead of the stored `preferredLocale` equals 0
- [ ] An OTP verification email sent to a user with a null `preferredLocale` falls back to the `Accept-Language` header locale — the email template locale is non-empty and the count of emails rendered in a locale other than the `Accept-Language` primary language equals 0
- [ ] An unauthenticated request to the `preferredLocale` update endpoint returns HTTP 401 — the response status code equals 401 and the `preferredLocale` field in the database is unchanged
- [ ] The `preferredLocale` field rejects unsupported locale codes — the API returns HTTP 400 when the request body contains a locale code not present in the supported locale registry

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User selects the same locale that is already active and stored in `preferredLocale` | The client either prevents the API call because the selected locale equals the current value, or the API treats it as a no-op returning 200 without modifying the database timestamp — the count of unnecessary writes equals 0 | HTTP request count equals 0 or HTTP response status equals 200 with unchanged `preferredLocale` value and `updated_at` timestamp |
| User changes locale while offline and the API request never reaches the server | The local locale change is applied immediately and the API request fails with a network error — the client displays an error toast and the local UI remains in the selected language while the server record retains the previous locale code | Error toast element is present, UI text displays in the selected language, and `preferredLocale` in the database equals the previous value |
| User changes locale on device A, then signs in on device B before the sync completes on device A | Device B reads the `preferredLocale` value that was stored before device A's pending update — device B applies the previous locale and device A's update completes independently, with the final database value reflecting whichever write completed last | `preferredLocale` in the database equals the locale code from the last successful write, and device B initially renders the previous locale |
| User changes locale rapidly multiple times within a few seconds on the same device | The client sends one API request per locale change — the final `preferredLocale` value in the database equals the last selected locale code, and intermediate values are overwritten by subsequent writes | The `preferredLocale` field in the database equals the last selected locale code after all requests complete |
| Server receives a `preferredLocale` update with an unsupported locale code not in the registry | The server rejects the request with HTTP 400 and the `preferredLocale` field in the database is unchanged — the client displays a validation error toast and the local UI reverts to the previous locale or remains unchanged | HTTP response status equals 400, error toast element is present, and `preferredLocale` in the database equals the previous value |
| User's session expires between selecting a locale and the API request reaching the server | The API request returns HTTP 401 because the session token is expired — the local locale change remains active on the current device and the client displays an error toast or redirects to `/signin` | HTTP response status equals 401 and the `preferredLocale` field in the database retains the previous value |

## Failure Modes

- **Locale sync mutation fails due to a transient D1 write error on the user table**
    - **What happens:** The client sends the `preferredLocale` update
        request to the server but the D1 write operation fails due to a
        transient database error, preventing the new locale code from
        being persisted to the user record even though the request was
        valid and authenticated.
    - **Source:** Cloudflare D1 transient write failure or connection
        timeout between the Worker and the D1 binding during the UPDATE
        operation on the `preferredLocale` column of the user table.
    - **Consequence:** The user receives a non-200 error response and
        sees an error toast via Sonner — the local UI remains in the
        newly selected language but the server record retains the
        previous locale value, causing cross-device inconsistency until
        the user successfully retries the sync.
    - **Recovery:** The server logs the D1 write failure with the user
        ID and locale context, and the client retries the mutation when
        the user re-selects the locale or clicks a retry action after
        the transient D1 failure recovers and connectivity is restored.
- **Email service fails to resolve recipient locale from the user record**
    - **What happens:** The email service attempts to read the
        recipient's `user.preferredLocale` from the database before
        composing an OTP or invitation email, but the database read
        fails due to a transient D1 error, leaving the service without
        the user's explicit locale preference.
    - **Source:** Cloudflare D1 transient read failure or connection
        timeout between the email service Worker and the D1 binding
        during the SELECT query on the user table to resolve the
        recipient's `preferredLocale` value.
    - **Consequence:** The email service cannot determine the user's
        explicit locale preference and the transactional email risks
        being rendered in the wrong language if the fallback detection
        chain produces a different locale than the user's stored
        preference.
    - **Recovery:** The email service falls back to parsing the
        `Accept-Language` header from the original request that
        triggered the email, and if that header is absent or
        unparseable the service defaults to the English locale template
        and logs the D1 read failure for operational monitoring.
- **Client reads a null `preferredLocale` on sign-in despite the user having previously set one**
    - **What happens:** The user previously synced a locale preference
        to the server, but when signing in on a new device the client
        reads `preferredLocale` as null due to a replication lag or
        database inconsistency, causing the client to fall back to
        platform-specific detection instead of applying the stored
        preference.
    - **Source:** D1 read-replica lag or a database inconsistency where
        the `preferredLocale` column returns null despite a prior
        successful write, possibly caused by an incomplete replication
        cycle between D1 storage nodes or a cache serving stale data.
    - **Consequence:** The user sees the interface in the
        platform-detected locale (which could differ from their chosen
        language) on the new device, creating a confusing inconsistency
        that persists until the client re-reads the user record and the
        replication catches up.
    - **Recovery:** The client notifies the user via the fallback
        locale display and the user can re-select their preferred
        language from the locale picker, which triggers a fresh write
        to the `preferredLocale` field and restores cross-device
        consistency after the new write is replicated.

## Declared Omissions

- This specification does not address adding or removing supported locales
    from the application's locale registry — that behavior is managed by the
    i18n infrastructure package and build-time configuration outside the scope
    of runtime locale syncing
- This specification does not address locale-specific formatting of dates,
    numbers, or currencies beyond language selection — those formatting rules
    are handled by the `Intl` API and the i18n infrastructure and are not
    stored in the `preferredLocale` field
- This specification does not address rate limiting on the `preferredLocale`
    update endpoint — that behavior is enforced by the global rate limiter
    defined in `api-framework.md` covering all mutation endpoints uniformly
    across the API
- This specification does not address right-to-left layout direction switching
    triggered by locale changes — RTL support is a CSS and layout concern
    handled separately by the UI framework and the Tailwind logical properties
    configuration
- This specification does not address guest or anonymous users syncing locale
    preferences — guest accounts do not have a `preferredLocale` field and
    their locale is determined solely by the platform-specific detection chain

## Related Specifications

- [auth-server-config](../foundation/auth-server-config.md) — Better Auth
    server configuration including the user update endpoint that validates
    authentication and persists the updated `preferredLocale` to the user
    record in the D1 database
- [database-schema](../foundation/database-schema.md) — Schema definition
    for the `user` table that includes the nullable `preferredLocale` column
    read during sign-in initialization and written when the user changes
    their language preference
- [shared-i18n](../foundation/shared-i18n.md) — Internationalization
    infrastructure providing the locale registry, translation keys, and
    runtime configuration used by the client to apply locale changes and
    render all locale settings UI text
- [api-framework](../foundation/api-framework.md) — Hono middleware stack
    and global error handler that wraps the `preferredLocale` update endpoint
    and returns consistent JSON error shapes for 400, 401, and 500 responses
    consumed by the locale settings form

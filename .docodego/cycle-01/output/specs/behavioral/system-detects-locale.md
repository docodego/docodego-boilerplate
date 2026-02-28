---
id: SPEC-2026-088
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [System, User]
---

[← Back to Roadmap](../ROADMAP.md)

# System Detects Locale

## Intent

This spec defines how the DoCodeGo application detects the user's preferred locale across all platform targets — API, web, desktop, mobile, and browser extension — and initializes the i18next translation system with the resolved language. Each platform follows a defined priority chain to determine the active locale: the API inspects the `Accept-Language` header on every request via Hono middleware, the web checks localStorage then `navigator.language`, the desktop uses the same chain but with bundled translations for instant rendering, and mobile reads the device locale via `expo-localization` with MMKV persistence. A `user.preferredLocale` database field provides an explicit override that takes precedence over all platform-level detection when set. The supported locales are English (`en`) and Arabic (`ar`), and any unsupported or missing locale input results in an English fallback. Translations are organized into five namespaces (`common`, `auth`, `dashboard`, `email`, `extension`) loaded independently per screen, with the core `@repo/i18n` module remaining React-free and React bindings exported from `@repo/i18n/react`.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Hono locale middleware (server-side middleware in the API layer that parses the `Accept-Language` header from every incoming HTTP request and resolves it to a supported locale for that request's scope) | read/write | On every incoming HTTP request to the API, the middleware reads the `Accept-Language` header, resolves the locale to `en` or `ar`, creates a scoped i18next instance, and attaches the `t()` function to the Hono context for downstream handlers | The middleware fails to parse the header due to a malformed value or the middleware itself throws an error during initialization — the system falls back to English as the default locale and attaches an English-scoped `t()` function to the Hono context so downstream handlers continue operating |
| `navigator.language` browser API (client-side browser API that returns the user's preferred language as a BCP 47 tag, used as the second priority in the web and desktop locale detection chain after localStorage) | read | During web and desktop application initialization, after checking localStorage for a persisted locale preference and finding none, the detection chain reads `navigator.language` to determine the browser's preferred language setting | The `navigator.language` API returns an undefined or empty value because the browser does not expose language preferences — the detection chain skips this step and falls back to English as the final default locale in the priority chain |
| localStorage (browser-based key-value storage used by the web and desktop applications to persist the user's explicit locale choice across sessions and page reloads as the highest-priority client-side detection source) | read | At application startup, the locale detection chain reads localStorage first to check whether the user has previously selected a language preference that was persisted from the language switcher in a prior session | The localStorage read fails due to browser privacy restrictions, storage quota exceeded, or corrupted storage state — the detection chain logs the read failure and proceeds to the next source in the priority chain which is `navigator.language` |
| `expo-localization` (Expo SDK module that reads the mobile device's system locale setting and provides it to the React Native application during initialization for locale detection on iOS and Android) | read | During mobile application initialization, `expo-localization` reads the device's system locale setting and passes it to i18next as the initial locale before checking MMKV for a persisted override from a previous session | The `expo-localization` module fails to read the device locale due to a platform API error or the module is not linked — the mobile application falls back to English as the default locale and logs the detection failure for debugging |
| MMKV storage (high-performance key-value storage on mobile that persists the resolved locale across application launches so subsequent startups use the same language preference without re-reading the device setting) | read/write | After the initial locale is resolved on mobile, the value is written to MMKV storage, and on subsequent launches the stored value is read first to avoid re-reading the device locale setting through `expo-localization` each time | The MMKV read or write operation fails due to storage corruption or initialization error on the native side — the mobile application falls back to reading the device locale through `expo-localization` and logs the MMKV failure for debugging |
| `user.preferredLocale` database field (nullable column in the user table that stores an explicit language choice, overriding all platform-level detection when set and falling back to the standard detection chain when null) | read | On every authenticated API request, the system checks the `user.preferredLocale` field after resolving the user's identity — if the field contains a non-null value, it overrides the `Accept-Language` header result for that request's translation scope | The database query fails or the field cannot be read due to a connection error — the system falls back to the locale resolved from the `Accept-Language` header by the Hono middleware and logs the database read failure |
| `i18next-resources-to-backend` plugin (lazy-loading plugin for i18next on the web that loads translation JSON files for the active locale and namespace on demand, keeping the initial JavaScript bundle small) | read | When a web page component references a translation namespace that has not been loaded yet, the plugin fetches the corresponding JSON file for the active locale from the server and registers it with the i18next instance | The plugin fails to fetch the translation file due to a network error or the file is missing from the build output — the i18next instance returns the translation key as-is instead of the translated string and logs the resource loading failure |

## Behavioral Flow

1. **[System]** on every incoming HTTP request to the API, the Hono
    locale middleware parses the `Accept-Language` header and resolves
    it to a supported locale — currently `en` (English) or `ar`
    (Arabic)

2. **[System]** the middleware creates an i18next instance scoped to
    that request and attaches the `t()` translation function to the
    Hono context, making it available to all downstream route handlers
    and middleware

3. **[System]** the API includes a `Content-Language` header in the
    response reflecting the resolved locale so the client knows which
    language the server used for any translated content in the response

4. **[System]** if the `Accept-Language` header is missing, malformed,
    or specifies an unsupported language, the middleware falls back to
    English (`en`) as the default locale for that request

5. **[System]** for authenticated requests, the system checks the
    `user.preferredLocale` database field — if the field contains a
    non-null value, it overrides the locale resolved from the
    `Accept-Language` header

6. **[System]** on web application startup, the locale detection chain
    checks localStorage first for a persisted user choice, then reads
    `navigator.language` from the browser, and finally falls back to
    `en` as the default if neither source yields a supported locale

7. **[System]** the `i18next-resources-to-backend` plugin lazy-loads
    only the translation JSON files needed for the active locale and
    referenced namespace, keeping the initial JavaScript bundle small

8. **[System]** the static HTML produced by Astro's SSG build renders
    English-only content — when React hydrates, i18next initializes
    with the detected locale and the UI updates to the correct language,
    producing an initial English flash before the resolved locale renders

9. **[System]** on desktop application startup, the locale detection
    chain follows the same priority (localStorage, `navigator.language`,
    English fallback), but translations are bundled inline rather than
    lazy-loaded, eliminating the initial English flash seen on web

10. **[System]** on mobile application startup, `expo-localization`
    reads the device's system locale and feeds it into i18next during
    initialization — the resolved locale is persisted in MMKV storage
    so subsequent launches use the same preference without re-reading
    the device setting

11. **[System]** if the mobile device locale is not among the supported
    languages (`en` or `ar`), the application falls back to English as
    the default locale

12. **[User]** interacts with the application in their detected locale,
    with translations organized into 5 namespaces (`common`, `auth`,
    `dashboard`, `email`, `extension`) that are loaded independently
    per screen

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| uninitialized | locale_resolved | The platform-specific detection chain completes and produces a supported locale value (`en` or `ar`) from the highest-priority source that yields a valid result | At least one source in the detection chain returns a value that maps to a supported locale, or the fallback to English is applied when no source matches |
| locale_resolved | override_applied | The system reads the `user.preferredLocale` database field for an authenticated user and finds a non-null value that differs from the locale resolved by the platform detection chain | The user is authenticated, the database query succeeds, and the `user.preferredLocale` field contains a non-null value that is a supported locale |
| locale_resolved | translations_loading | The i18next instance begins loading translation resources for the resolved locale and the namespaces required by the current screen or request handler | The locale is resolved and the application has identified which translation namespaces are needed for the current context |
| override_applied | translations_loading | The overridden locale from `user.preferredLocale` replaces the detected locale and the i18next instance begins loading translations for the override locale instead of the originally detected one | The override locale is a supported value and the system has replaced the detected locale with the override value in the i18next configuration |
| translations_loading | translations_ready | All required translation namespace files for the active locale are loaded into the i18next instance and the `t()` function returns translated strings instead of raw keys | The translation resources for every referenced namespace have been successfully loaded or were already bundled inline (desktop and mobile) |
| translations_loading | fallback_to_english | The translation resource loading fails for the active locale due to a network error or missing file and the i18next instance falls back to using English translations as the default | The resource loader encounters an error fetching the translation file and the English fallback resources are available in the i18next instance |

## Business Rules

- **Rule accept-language-parsed-per-request:** IF an HTTP request arrives
    at the API THEN the Hono locale middleware parses the
    `Accept-Language` header and resolves it to `en` or `ar` for that
    request — the count of API requests processed without locale
    resolution equals 0
- **Rule missing-header-defaults-to-english:** IF the `Accept-Language`
    header is missing, malformed, or specifies an unsupported language
    THEN the middleware resolves the locale to English (`en`) — the
    resolved locale value for requests with unsupported headers equals
    `en`
- **Rule content-language-header-set:** IF the API processes a request
    and resolves a locale THEN the response includes a
    `Content-Language` header matching the resolved locale value — the
    count of API responses missing the `Content-Language` header
    equals 0
- **Rule user-preferred-locale-overrides-header:** IF the authenticated
    user's `user.preferredLocale` field is non-null THEN the stored
    value overrides the locale resolved from the `Accept-Language`
    header — the active locale for that request equals the value stored
    in `user.preferredLocale`
- **Rule web-detection-priority-chain:** IF the web application starts
    THEN the detection chain checks localStorage first, then
    `navigator.language`, then falls back to `en` — the count of
    detection sources checked before localStorage equals 0
- **Rule desktop-no-english-flash:** IF the desktop application starts
    with a non-English resolved locale THEN translations render on
    first paint because they are bundled inline — the count of English
    flash frames before the correct locale renders on desktop equals 0
- **Rule mobile-persists-to-mmkv:** IF the mobile application resolves
    a locale during startup THEN the resolved value is written to MMKV
    storage for subsequent launches — the stored MMKV locale value
    after initialization equals the resolved locale value
- **Rule namespaces-loaded-independently:** IF a screen references
    translation namespaces THEN only those referenced namespaces are
    loaded — the count of unreferenced namespaces loaded for a given
    screen equals 0
- **Rule i18n-core-react-free:** IF the `@repo/i18n` core module is
    imported by a non-React context such as the API THEN the import
    contains zero React dependencies — the count of React imports in
    the `@repo/i18n` core entry point equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| System (the platform-specific runtime that executes locale detection, initializes i18next, loads translation resources, and attaches the translation function to request contexts or application state across API, web, desktop, and mobile targets) | Parse the `Accept-Language` header and resolve it to a supported locale, read localStorage and `navigator.language` on web and desktop, read the device locale via `expo-localization` on mobile, persist the resolved locale to MMKV on mobile, create scoped i18next instances, lazy-load or bundle translation namespaces, set the `Content-Language` response header, read the `user.preferredLocale` database field for authenticated users | Cannot change the user's browser language setting or device locale, cannot modify the `user.preferredLocale` database field (that requires an explicit user action through the language switcher), cannot add new supported locales at runtime without a code deployment | The system has visibility into the `Accept-Language` header value, the localStorage and `navigator.language` values, the device locale on mobile, and the `user.preferredLocale` database field for authenticated users, but has no visibility into what locale the user intends to use beyond these signals |
| User (the person using the application across any platform who benefits from automatic locale detection and can override the detected locale through the language switcher, which persists the choice in localStorage, MMKV, or the `user.preferredLocale` database field) | Interact with the application in the detected locale, override the detected locale by using the language switcher which persists the choice to localStorage on web and desktop, MMKV on mobile, and the `user.preferredLocale` database field for authenticated users | Cannot directly set the `Accept-Language` header sent by the browser (the browser determines this from OS settings), cannot bypass the locale detection chain to force an unsupported locale, cannot load translation namespaces that are not referenced by the current screen | The user sees the application rendered in the resolved locale, sees the initial English flash on web before hydration when the resolved locale is non-English, and does not see which detection source was used to determine the active locale |

## Constraints

- The Hono locale middleware resolves the locale from the
    `Accept-Language` header within 5 ms per request — the count of
    milliseconds from header read to locale resolution equals 5 or
    fewer.
- The web locale detection chain (localStorage check, then
    `navigator.language` read, then fallback) completes within 10 ms
    of application initialization — the count of milliseconds from
    detection start to resolved locale equals 10 or fewer.
- The `i18next-resources-to-backend` plugin loads a single translation
    namespace JSON file within 200 ms on a 3G connection — the count
    of milliseconds from namespace request to loaded state equals 200
    or fewer.
- The mobile `expo-localization` device locale read and MMKV
    persistence completes within 50 ms of application startup — the
    count of milliseconds from startup to persisted locale equals 50
    or fewer.
- The total number of supported locales is 2 (`en` and `ar`) and all
    detection chains validate against this list — the count of
    supported locale values in the detection chain equals 2.
- Each translation namespace JSON file is loaded independently with
    zero unnecessary namespaces fetched — the count of translation
    namespaces loaded that are not referenced by the current screen
    equals 0.

## Acceptance Criteria

- [ ] The Hono locale middleware resolves `Accept-Language: ar` to locale `ar` and attaches an Arabic-scoped `t()` function — the count of requests where the resolved locale does not match `ar` when the header specifies `ar` equals 0
- [ ] The API response includes a `Content-Language` header matching the resolved locale — the count of API responses missing the `Content-Language` header equals 0
- [ ] A request with a missing `Accept-Language` header resolves to English — the count of requests with missing headers that resolve to a locale other than `en` equals 0
- [ ] A request with a malformed `Accept-Language` header resolves to English — the count of requests with malformed headers that resolve to a locale other than `en` equals 0
- [ ] An authenticated user with `user.preferredLocale` set to `ar` overrides an `Accept-Language: en` header — the count of requests where the override locale does not equal `ar` equals 0
- [ ] An authenticated user with `user.preferredLocale` set to null uses the locale from the `Accept-Language` header — the count of null-preference requests where the active locale differs from the header-resolved value equals 0
- [ ] The web detection chain checks localStorage first and uses a persisted value of `ar` when present — the count of detection runs that skip localStorage equals 0
- [ ] The web detection chain falls back to `navigator.language` when localStorage has no persisted locale — the count of detection runs that skip `navigator.language` when localStorage is empty equals 0
- [ ] The desktop application renders the correct locale on first paint without an English flash because translations are bundled inline — the count of English flash frames on desktop equals 0
- [ ] The mobile application reads the device locale via `expo-localization` and persists it to MMKV storage — the MMKV stored locale value after initialization is non-empty
- [ ] The mobile application falls back to English when the device locale is unsupported — the count of unsupported device locales that resolve to a value other than `en` equals 0
- [ ] Translation namespaces are loaded independently per screen with zero unreferenced namespaces fetched — the count of unreferenced namespaces loaded equals 0
- [ ] The `@repo/i18n` core module contains zero React imports and is consumable by the API without React as a dependency — the count of React imports in the core entry point equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The `Accept-Language` header contains multiple languages with quality values like `ar;q=0.9, en;q=0.8` and the highest-priority language is a supported locale | The middleware selects the highest-quality supported locale from the header, resolving to `ar` because it has the highest quality value among supported languages | The resolved locale equals `ar` and the `Content-Language` header equals `ar` |
| The `Accept-Language` header specifies a language subtag like `ar-EG` that is not an exact match but the base language `ar` is supported | The middleware normalizes the subtag to its base language `ar` and resolves the locale to `ar` because the base language is in the supported locale list | The resolved locale equals `ar` and the `Content-Language` header equals `ar` |
| The user's localStorage contains a locale value that was valid in a previous version but is no longer in the supported locale list after an update | The detection chain rejects the invalid localStorage value, proceeds to `navigator.language` as the next source, and ultimately falls back to English if no supported locale is found | The resolved locale equals `en` or matches `navigator.language` if that value is supported, and the invalid localStorage entry is ignored |
| The `user.preferredLocale` field contains a value but the database query times out during an authenticated API request | The system catches the database timeout, logs the failure, and falls back to the locale resolved from the `Accept-Language` header instead of the database override | The response uses the header-resolved locale and an error log entry for the database timeout is present |
| The mobile device locale changes while the application is in the background and the user returns to the foreground | The application reads the MMKV-persisted locale on resume rather than re-reading the device locale, maintaining the previous language until the user explicitly changes it through the language switcher | The active locale after resume equals the MMKV-stored value, not the newly changed device locale |
| The web application loads on a browser that blocks localStorage access due to strict privacy settings or incognito mode restrictions | The detection chain catches the localStorage access error, skips to `navigator.language` as the next source, and resolves the locale from the browser language setting or falls back to English | The resolved locale is determined from `navigator.language` or equals `en` and the application renders without errors |

## Failure Modes

- **Hono locale middleware throws an unhandled error during header parsing on an API request**
    - **What happens:** The middleware encounters a malformed `Accept-Language` header value that causes an unexpected parsing exception, or the i18next instance creation fails due to a missing translation resource during middleware initialization.
    - **Source:** A client sends a header with non-standard encoding or characters that the parsing library does not handle, or a deployment is missing the expected translation files for the API namespace.
    - **Consequence:** The request fails to have a locale-scoped `t()` function attached to the Hono context, and downstream route handlers that call `t()` receive undefined, potentially causing error responses to the client.
    - **Recovery:** The middleware catches the parsing error, logs the malformed header value and exception details, and falls back to creating an English-scoped i18next instance so the request proceeds with English translations instead of failing entirely.

- **Web translation namespace JSON file fails to load due to a network error or missing build artifact**
    - **What happens:** The `i18next-resources-to-backend` plugin attempts to fetch a translation namespace JSON file for the active locale, but the network request fails due to a connectivity issue or the file is missing from the build output because of a build pipeline error.
    - **Source:** The user's network connection drops during the lazy-load fetch, a CDN serves a stale or missing asset after a deployment, or the build pipeline failed to generate the translation file for a specific namespace and locale combination.
    - **Consequence:** The i18next instance returns raw translation keys instead of translated strings for the affected namespace, and the user sees untranslated key identifiers in the UI until the resource is successfully loaded.
    - **Recovery:** The plugin retries the namespace fetch once after a 1-second delay, and if the retry fails, the i18next instance falls back to English translations for that namespace if English resources are already loaded in memory, and logs the fetch failure with the namespace name and locale.

- **MMKV storage fails to persist the resolved locale on mobile during application startup**
    - **What happens:** The mobile application resolves the device locale through `expo-localization` and attempts to write it to MMKV storage, but the write operation fails due to native storage initialization failure, insufficient device storage, or MMKV library corruption.
    - **Source:** The device runs low on storage and the MMKV write is rejected, the MMKV native module fails to initialize on a specific OS version, or the MMKV storage file becomes corrupted from a previous unclean application termination.
    - **Consequence:** The current session uses the correctly resolved locale, but subsequent application launches cannot read a persisted value from MMKV and must re-read the device locale through `expo-localization` each time, adding startup latency.
    - **Recovery:** The application catches the MMKV write error, logs the failure details including the error code and attempted locale value, and degrades to re-reading the device locale via `expo-localization` on every launch until MMKV storage recovers or is re-initialized.

- **Database query for `user.preferredLocale` fails during an authenticated API request**
    - **What happens:** The system attempts to read the `user.preferredLocale` field for an authenticated user to check for a locale override, but the database connection is unavailable or the query times out due to high server load.
    - **Source:** The database server is experiencing high latency or is temporarily unreachable, the connection pool is exhausted under peak traffic, or a network partition between the API worker and the database prevents the query from completing.
    - **Consequence:** The system cannot determine whether the user has an explicit locale preference, and the request proceeds without the override check, potentially serving content in the header-detected locale instead of the user's stored preference.
    - **Recovery:** The system catches the database query error, logs the failure with the user identifier and query timeout duration, and falls back to using the locale resolved from the `Accept-Language` header for that request without the `user.preferredLocale` override.

## Declared Omissions

- This specification does not define the language switcher UI or the user-initiated locale change flow — that behavior is covered in the user-changes-language specification with its own interaction patterns and persistence logic
- This specification does not cover the translation key authoring format, namespace file structure, or the build pipeline that generates translation JSON files from source strings for each supported locale
- This specification does not address adding new supported locales beyond English and Arabic — expanding the locale list requires code changes to the detection chains, middleware configuration, and translation file generation pipeline
- This specification does not define the Intl API-based formatters for numbers, dates, and relative time that are exported from `@repo/i18n/formatters` — those are utility functions independent of the locale detection flow
- This specification does not cover the browser extension locale detection behavior, which is defined in a separate specification covering the extension popup's language initialization and the service worker's locale handling

## Related Specifications

- [user-changes-language](user-changes-language.md) — defines the
    user-initiated locale switching flow that persists the chosen
    language to localStorage on web, MMKV on mobile, and the
    `user.preferredLocale` database field for authenticated users
- [app-renders-rtl-layout](app-renders-rtl-layout.md) — defines how
    the application switches to right-to-left layout direction when
    the resolved locale is an RTL language like Arabic, consuming the
    locale value produced by this detection flow
- [session-lifecycle](session-lifecycle.md) — defines the
    authenticated session that provides the user identity needed to
    read the `user.preferredLocale` database field for the locale
    override check on authenticated API requests
- [extension-authenticates-via-token-relay](extension-authenticates-via-token-relay.md)
    — defines the browser extension authentication flow that
    establishes the session context from which the extension popup
    determines the user's locale preference for rendering translated
    content

---
id: SPEC-2026-010
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: draft
roles: [Framework Adopter]
---

[← Back to Roadmap](../ROADMAP.md)

# Shared i18n

## Intent

This spec defines the `@repo/i18n` package that provides internationalization infrastructure for the DoCodeGo boilerplate across all platform targets. The package wraps i18next with a React-free core module, separate React bindings, and locale-aware formatters using native Intl APIs. It supports 2 locales (English and Arabic) organized into 5 translation namespaces, with lazy-loading on web and inline bundling on desktop. This spec ensures that the i18n package maintains a strict separation between core functionality (consumed by the API and non-React contexts) and React bindings, that translations are loaded efficiently per platform, and that RTL layout direction is derived from the active locale.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| i18next | read | App startup and every translation call via `t()` | Build fails at compile time because the core module cannot resolve the i18next dependency and CI alerts to block deployment |
| react-i18next | read | React component render when using `@repo/i18n/react` hooks | Build fails at compile time for React workspaces that import the React subpath and CI alerts to block deployment |
| i18next-resources-to-backend | read | Web platform lazy-loads a translation namespace on first access | Translation loading falls back to the bundled default English namespace strings so the UI degrades to English-only text instead of crashing |
| `@repo/library` | read | Formatter functions reference shared constants or utility types | Build fails at compile time if the library package export is missing and CI alerts to block deployment |
| Hono API (`apps/api`) | read | Every API request when locale middleware calls `t()` from the core module | Locale middleware falls back to default English locale strings so API responses remain readable but untranslated for non-English users |

## Behavioral Flow

1. **[Build system]** → compiles `@repo/i18n` package and resolves 3 export subpaths: core, react, and formatters
2. **[Consuming workspace]** → imports from the relevant subpath (`@repo/i18n` for core, `@repo/i18n/react` for React bindings, `@repo/i18n/formatters` for Intl wrappers)
3. **[Core module]** → initializes i18next with the supported locale list (`en`, `ar`), the 5 namespace declarations (`common`, `auth`, `dashboard`, `email`, `extension`), and the fallback locale set to `en`
4. **[Platform runtime]** → resolves the active locale using the detection priority chain: database `user.preferredLocale` field first, then platform-specific detection (localStorage and navigator on web, MMKV and expo-localization on mobile), then `en` as the default fallback
5. **[Translation loader]** → loads the namespace files for the resolved locale — on web via `i18next-resources-to-backend` lazy-loading, on desktop via inline bundling at compile time
6. **[Calling code]** → invokes `t("namespace:key")` and receives the translated string for the active locale, or the English fallback string if the key is absent in the active locale
7. **[Direction resolver]** → returns `"rtl"` for Arabic, Hebrew, Farsi, and Urdu locale codes, and returns `"ltr"` for all other locales — the layout direction is consumed by UI components for bidirectional rendering

## State Machine

No stateful entities. The i18n package is a stateless translation resolution layer — locale selection is an input parameter, not a managed lifecycle. The active locale is held externally by each platform's state management (React context on web, MMKV on mobile) and is not owned by this package.

## Business Rules

- **Rule locale-priority:** IF the `user.preferredLocale` database field is present AND non-null THEN the resolved locale equals that database value, overriding all client-side detection mechanisms
- **Rule fallback-locale:** IF the detected locale is not in the supported locale list (`en`, `ar`) THEN the resolved locale falls back to `en` as the default
- **Rule namespace-isolation:** IF a route references only the `auth` namespace THEN only the `auth` namespace files are loaded for that route, and the remaining 4 namespaces are not fetched until explicitly referenced
- **Rule rtl-detection:** IF the active locale code is one of `ar`, `he`, `fa`, or `ur` THEN the direction resolver returns `"rtl"`, otherwise it returns `"ltr"`

## Permission Model

Single role; no permission model needed. The i18n package is a shared utility consumed by all workspaces regardless of user authentication status. Every caller — authenticated or unauthenticated — has identical access to translation functions and locale resolution. No actions are restricted based on user role or session state within this package.

## Acceptance Criteria

- [ ] The `packages/i18n` directory is present and contains a `package.json` with `"name"` set to `"@repo/i18n"` — this value is present in the file
- [ ] The `package.json` sets `"type"` to `"module"` (present) and `"private"` to true (present) — both values are present in the file
- [ ] The package depends on `i18next` and `react-i18next` via catalog references — both dependencies are present and use `"catalog:"` versions in `package.json`
- [ ] The package exports at least 3 subpaths: a core module (default or named), `@repo/i18n/react` for React bindings, and `@repo/i18n/formatters` for locale-aware formatting — all 3 are present in the `"exports"` field
- [ ] The count of React imports in the core module source files equals 0 — the string `from "react"` is absent from all core module files, returning 0 matches in a search
- [ ] The `@repo/i18n/react` subpath imports from `react-i18next` — this import is present and provides React hooks and components for translation
- [ ] The `@repo/i18n/formatters` subpath exports at least 3 formatter functions for numbers, dates, and relative time — all 3 are present and use the native `Intl` API internally
- [ ] The count of `date-fns` imports across the entire i18n package equals 0 — native `Intl` APIs are used exclusively for date and number formatting
- [ ] Translation files are present for exactly 2 locales: `en` (English) and `ar` (Arabic) — both locale directories or file sets are present on disk
- [ ] Translations are organized into exactly 5 namespaces: `common`, `auth`, `dashboard`, `email`, and `extension` — all 5 are present for each locale
- [ ] Each namespace contains at least 1 translation key — no namespace file is empty (word count > 0 for each file)
- [ ] The package exports a direction resolver that returns `"rtl"` when the locale equals `"ar"` and returns `"ltr"` when the locale equals `"en"` — both return values are present and correct
- [ ] The RTL detection covers at least 4 RTL language codes: `ar`, `he`, `fa`, and `ur` — all 4 are present in the RTL locale list
- [ ] The `i18next-resources-to-backend` dependency is present in `package.json` for lazy-loading translation files on web — this entry exists and is non-empty
- [ ] The package contains a `"typecheck"` script and a `"test"` script in `package.json` — both are present and non-empty
- [ ] Running `pnpm --filter i18n typecheck` exits with code = 0 and produces 0 type errors

## Constraints

- The core i18n module never imports React — this is the foundational constraint of the package architecture. The core module is consumed by the Hono API server (which has no React dependency) and by other non-React contexts. The count of `react` or `react-dom` imports in the core module source files equals 0. React bindings are strictly isolated to the `@repo/i18n/react` subpath.
- All date, number, and relative time formatting uses native `Intl` APIs (`Intl.DateTimeFormat`, `Intl.NumberFormat`, `Intl.RelativeTimeFormat`) — the `date-fns` library is not installed and not referenced. The count of `date-fns` entries in `package.json` dependencies equals 0 across the entire monorepo.
- Translation namespaces are loaded independently per screen — a given route loads only the namespaces it references, not all 5. The lazy-loading mechanism via `i18next-resources-to-backend` ensures that the initial bundle includes 0 translation strings on web; they are fetched on demand at runtime.
- The `user.preferredLocale` database field takes precedence over all client-side detection when present and non-null. The locale detection priority chain is: database preference first, then platform-specific detection (localStorage and navigator on web, MMKV and expo-localization on mobile), then English as the default fallback when no preference is detected.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| A translation key is present in the English `dashboard` namespace but absent from the Arabic `dashboard` namespace | i18next falls back to the English string for that specific key and renders the English text instead of an empty string or raw key | The rendered output for locale `ar` contains the English fallback string and does not contain the raw key identifier |
| The `Accept-Language` header on an API request contains a locale code (`fr`) that is not in the supported locale list | The locale resolution falls back to `en` and the `t()` function returns English translations for all keys in that request | The API response includes `Content-Language: en` and the response body contains English-language strings |
| A formatter function receives `undefined` as the locale parameter instead of a valid locale string | The formatter falls back to `"en"` as the default locale and formats the value using English Intl conventions | The formatter output matches the expected English-formatted pattern (e.g., `1,234.56` for number formatting) |
| The web platform attempts to lazy-load a namespace file that does not exist on the CDN or returns HTTP 404 | The `i18next-resources-to-backend` loader degrades gracefully and i18next falls back to the bundled default English namespace content | The UI renders English fallback strings instead of displaying raw translation keys or crashing |
| A developer registers a 6th namespace in i18next configuration but does not create corresponding translation files on disk for either locale | i18next logs a warning at initialization listing the missing namespace and all `t()` calls for that namespace return the raw key string as visible feedback | The raw key string is visible in the UI output and the console contains a warning identifying the unregistered namespace |

## Failure Modes

- **React import leaks into the core i18n module causing the API server build to fail because apps/api does not list React as a dependency**
    - **What happens:** A developer adds a React hook or JSX component to a core module file, causing the API server build to fail because `apps/api` does not list React as a dependency and cannot resolve the import at compile time.
    - **Source:** Incorrect file placement during development when React-dependent code is added to the core subpath instead of the `@repo/i18n/react` subpath by a developer unfamiliar with the package boundary.
    - **Consequence:** The `apps/api` workspace typecheck fails with a "module not found" diagnostic for the React import, blocking the entire CI pipeline from proceeding to deployment until the import is removed.
    - **Recovery:** The CI typecheck step alerts by returning a non-zero exit code that identifies the offending file and import line, and the system falls back to the last successful build until the developer moves the React-dependent code to the `@repo/i18n/react` subpath.
- **Missing translation keys for a locale where a developer adds keys to English but omits the corresponding keys from Arabic**
    - **What happens:** A developer adds a new translation key to the English `dashboard` namespace but omits the corresponding key from the Arabic `dashboard` namespace, causing Arabic users to see English fallback strings instead of translated text in the dashboard.
    - **Source:** Incomplete translation file update during feature development when only one locale file is modified and the other locale is not synchronized with the new key additions.
    - **Consequence:** Arabic-speaking users see mixed-language UI where some strings appear in English instead of Arabic, degrading the localized experience without causing a runtime crash or data loss.
    - **Recovery:** The CI test suite runs a key-parity check that alerts by listing every key present in one locale but absent in another, and i18next falls back to the English string for each missing key so the UI degrades to partial English rather than displaying raw key identifiers.
- **Formatter receives a hardcoded locale instead of the active i18next locale causing numbers and dates to render in the wrong format**
    - **What happens:** A developer passes a hardcoded locale string such as `"en"` directly to an `Intl` formatter function instead of using the active i18next locale, causing numbers and dates to render in the wrong format when the user switches to Arabic.
    - **Source:** Developer error during implementation when the formatter call bypasses the locale parameter provided by the i18n package and uses a static string literal instead of the dynamic locale value.
    - **Consequence:** Users who switch to Arabic see Western-formatted numbers (`1,234.56`) instead of Arabic-Indic numerals, breaking the locale-consistent formatting expectation across the entire interface for all number and date displays.
    - **Recovery:** The unit test for each formatter function alerts by verifying that calling it with locale `"ar"` produces Arabic-formatted output and calling it with locale `"en"` produces English-formatted output, and the test falls back to failing the CI pipeline when the output pattern does not match the expected locale format.
- **Lazy-loading transport fails to fetch namespace file on web when the CDN returns HTTP 404 or a network timeout interrupts the request**
    - **What happens:** The `i18next-resources-to-backend` loader attempts to fetch a translation namespace file from the CDN but receives an HTTP 404 or network timeout error, leaving the namespace with 0 loaded translation strings for the requested locale.
    - **Source:** CDN deployment omits translation files, the file path convention changes without updating the loader configuration, or the network connection is interrupted during the fetch request to the translation endpoint.
    - **Consequence:** All `t()` calls for the affected namespace return raw key strings (e.g., `"dashboard:welcome_message"`) instead of translated text, rendering an unusable interface for that screen until the page is refreshed.
    - **Recovery:** i18next falls back to the English locale strings bundled as the default fallback resource, and the system degrades to displaying English text instead of raw keys — the loader logs the fetch failure to the console so developers can identify and fix the missing file during development or staging review.

## Declared Omissions

- Per-platform locale detection implementation details including localStorage sniffing on web and expo-localization on mobile are not covered here and are defined in `system-detects-locale.md`
- RTL CSS layout rules, logical property conventions, and bidirectional rendering behavior for UI components are not covered here and are defined in `shared-ui.md` and `app-renders-rtl-layout.md`
- Language switching UI components and user preference persistence to the database are not covered here and are defined in `user-changes-language.md` and `user-syncs-locale-preference.md`
- Email template translation rendering and locale resolution for transactional emails are not covered here and are defined in `system-sends-otp-email.md` and `system-sends-invitation-email.md`
- Translation key naming conventions, plural form rules, and interpolation syntax standards are not covered here and are deferred to the translation authoring guide

## Related Specifications

- [api-framework](api-framework.md) — Defines the Hono middleware stack that consumes the core i18n module for per-request locale resolution and response translation
- [database-schema](database-schema.md) — Defines the `user.preferredLocale` column that serves as the highest-priority locale source in the detection chain
- [shared-ui](shared-ui.md) — Consumes the direction resolver output (`"rtl"` or `"ltr"`) to apply bidirectional layout classes across all UI components
- [shared-contracts](shared-contracts.md) — Defines oRPC contract types that reference locale-aware validation messages produced by the i18n translation functions
- [system-detects-locale](../behavioral/system-detects-locale.md) — Implements the platform-specific locale detection logic that feeds into the i18n initialization on each target

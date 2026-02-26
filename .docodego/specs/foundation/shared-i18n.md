[← Back to Roadmap](../ROADMAP.md)

# Shared i18n

## Intent

This spec defines the `@repo/i18n` package that provides internationalization infrastructure for the DoCodeGo boilerplate across all platform targets. The package wraps i18next with a React-free core module, separate React bindings, and locale-aware formatters using native Intl APIs. It supports 2 locales (English and Arabic) organized into 5 translation namespaces, with lazy-loading on web and inline bundling on desktop. This spec ensures that the i18n package maintains a strict separation between core functionality (consumed by the API and non-React contexts) and React bindings, that translations are loaded efficiently per platform, and that RTL layout direction is derived from the active locale.

## Acceptance Criteria

- [ ] The `packages/i18n` directory is present and contains a `package.json` with `"name"` set to `"@repo/i18n"`
- [ ] The `package.json` sets `"type"` to `"module"` and `"private"` to true
- [ ] The package depends on `i18next` and `react-i18next` via catalog references — both dependencies are present and use `"catalog:"` versions
- [ ] The package exports at least 3 subpaths: a core module (default or named), `@repo/i18n/react` for React bindings, and `@repo/i18n/formatters` for locale-aware formatting — all 3 are present in the `"exports"` field
- [ ] The core module export contains 0 React imports — the string `from "react"` is absent from all core module files, returning 0 matches in a search
- [ ] The `@repo/i18n/react` subpath imports from `react-i18next` — this import is present and provides React hooks and components for translation
- [ ] The `@repo/i18n/formatters` subpath exports at least 3 formatter functions for numbers, dates, and relative time — all 3 are present and use the native `Intl` API internally
- [ ] The count of `date-fns` imports across the entire i18n package equals 0 — native `Intl` APIs are used exclusively for date and number formatting
- [ ] Translation files are present for exactly 2 locales: `en` (English) and `ar` (Arabic) — both locale directories or file sets are present on disk
- [ ] Translations are organized into exactly 5 namespaces: `common`, `auth`, `dashboard`, `email`, and `extension` — all 5 are present for each locale
- [ ] Each namespace contains at least 1 translation key — no namespace file is empty (word count > 0 for each)
- [ ] The package exports a direction resolver that returns `"rtl"` when the locale equals `"ar"` and returns `"ltr"` when the locale equals `"en"` — both return values are present and correct
- [ ] The RTL detection covers at least 4 RTL language codes: `ar`, `he`, `fa`, and `ur` — all 4 are present in the RTL locale list
- [ ] The `i18next-resources-to-backend` dependency is present for lazy-loading translation files on web
- [ ] The package contains a `"typecheck"` script and a `"test"` script in `package.json` — both are present and non-empty
- [ ] Running `pnpm --filter i18n typecheck` exits with code = 0 and produces 0 errors

## Constraints

- The core i18n module must never import React — this is the foundational constraint of the package architecture. The core module is consumed by the Hono API server (which has no React dependency) and by other non-React contexts. The count of `react` or `react-dom` imports in the core module source files equals 0. React bindings are strictly isolated to the `@repo/i18n/react` subpath.
- All date, number, and relative time formatting uses native `Intl` APIs (`Intl.DateTimeFormat`, `Intl.NumberFormat`, `Intl.RelativeTimeFormat`) — the `date-fns` library is not installed and not referenced. The count of `date-fns` entries in `package.json` dependencies equals 0 across the entire monorepo.
- Translation namespaces are loaded independently per screen — a given route loads only the namespaces it references, not all 5. The lazy-loading mechanism via `i18next-resources-to-backend` ensures that the initial bundle includes 0 translation strings; they are fetched on demand.
- The `user.preferredLocale` database field takes precedence over all client-side detection when present and non-null. The locale detection priority chain is: database preference, then platform-specific detection (localStorage/navigator on web, MMKV/expo-localization on mobile), then English as the default fallback.

## Failure Modes

- **React import in core module**: A developer adds a React hook or component to the core i18n module, breaking the API server build because `apps/api` does not depend on React. The CI typecheck step for `apps/api` returns error with a "module not found" diagnostic for the React import, identifying the offending file in `@repo/i18n` and prompting the developer to move the React-dependent code to the `@repo/i18n/react` subpath.
- **Missing namespace for a locale**: A developer adds a new translation key to the English `dashboard` namespace but forgets to add the corresponding key to the Arabic `dashboard` namespace, causing the Arabic UI to display the English fallback string. The CI test suite runs a key-parity check that compares the key sets of each namespace across all locales and returns error listing every key that is present in one locale but absent in another.
- **Formatter locale mismatch**: A developer passes a hardcoded locale string to an `Intl` formatter instead of using the active i18next locale, causing numbers and dates to render in the wrong format when the user switches language. The unit test for each formatter verifies that calling it with locale `"ar"` produces Arabic-formatted output (e.g., Arabic-Indic numerals) and calling it with `"en"` produces English-formatted output, and returns error if the output does not match the expected locale pattern.
- **Stale translations after namespace addition**: A developer creates a 6th namespace but does not register it in the i18next configuration, causing all keys in the new namespace to return their raw key strings instead of translated text. The i18next initialization validates that every namespace listed in the configuration has a corresponding translation file present on disk, and logs a warning at startup listing any namespace that is declared but has no translation file, prompting the developer to create the missing files.

## Declared Omissions

- Per-platform locale detection implementation (covered by `system-detects-locale.md`)
- RTL CSS layout and logical property conventions (covered by `shared-ui.md` and `app-renders-rtl-layout.md`)
- Language switching UI and user preference persistence (covered by `user-changes-language.md` and `user-syncs-locale-preference.md`)
- Email template translation rendering (covered by `system-sends-otp-email.md` and `system-sends-invitation-email.md`)

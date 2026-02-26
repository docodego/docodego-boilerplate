# System Detects Locale

## API Side

On every incoming request, the Hono locale middleware parses the `Accept-Language` header and resolves it to a supported locale — currently `en` (English) or `ar` (Arabic). The middleware creates an i18next instance scoped to that request and attaches the `t()` translation function to the Hono context, making it available to all downstream route handlers and middleware. The response includes a `Content-Language` header reflecting the resolved locale. If the header is missing, malformed, or specifies an unsupported language, the system falls back to English.

## Web Side

On the web, locale detection follows a priority chain: first localStorage (where a previous user choice is persisted), then `navigator.language` from the browser, and finally `"en"` as the default fallback. The `i18next-resources-to-backend` plugin lazy-loads only the translation files needed for the active locale, keeping the initial bundle small. The static HTML produced by Astro's SSG build is English-only — when React hydrates, it initializes i18next with the detected locale and the UI updates to the user's language. This means the initial page flash is always English, then the correct locale renders once React is active.

## Mobile Side

On mobile, `expo-localization` reads the device's system locale and feeds it into i18next during initialization. The resolved locale is persisted in MMKV storage so subsequent launches use the same preference without re-reading the device setting. If the device locale is not among the supported languages, the app falls back to English.

## User Preference Override

The `user.preferredLocale` field in the database stores an explicit language choice (nullable). When this field is set, it overrides whatever `Accept-Language` header the client sends or whatever the device locale returns. When it is null, the system falls back to the standard detection chain for each platform. This allows users to explicitly choose a language that differs from their browser or device setting.

## Translation Namespaces

Translations are organized into 5 namespaces: `common` (shared UI strings), `auth` (sign-in, sign-up, verification), `dashboard` (app navigation and workspace), `email` (email templates and subjects), and `extension` (browser extension popup). Each namespace is loaded independently — a given screen only loads the namespaces it references. The i18n package lives in `@repo/i18n`, with the core module being React-free (consumed by the API and other non-React contexts) and React bindings exported separately from `@repo/i18n/react`. Locale-aware formatters (numbers, dates, relative time) are available from `@repo/i18n/formatters` and use the Intl API internally.

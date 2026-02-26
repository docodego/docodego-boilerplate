[← Back to Index](README.md)

# User Changes Language on Mobile

## The Language Selector

The user navigates to the settings screen within the Expo mobile app, where a localized language selector is available. The selector lists the supported languages — English and Arabic — with each option displayed in its own language so the user can identify their preference regardless of the currently active locale.

## Switching Languages

When the user selects a different language, the app calls `i18next.changeLanguage(locale)` with the selected locale code. i18next loads the new translation resources and re-renders all translated strings throughout the application. Navigation labels, button text, form labels, headings, and all other translated content update to reflect the new language. This follows the same i18next-based switching mechanism used on the [web platform](user-changes-language.md).

## RTL Layout for Arabic

When the user switches to Arabic, the app calls `I18nManager.forceRTL(true)` to flip the entire layout direction. React Native's layout engine reverses `flexDirection`, `textAlign`, and all directional styles at the framework level. When switching back to English, `I18nManager.forceRTL(false)` restores the left-to-right orientation. Unlike the web, where the layout flips instantly via the `dir` attribute, React Native may require an app restart for the RTL direction change to take full effect. The app prompts the user to restart when an RTL direction change is detected.

## Persistence

The selected language is persisted to MMKV storage on the device. On subsequent app launches, the stored locale is read during i18next initialization so the correct language and text direction are applied before the first render. The user always returns to the app in their chosen language without any flash of the default locale.

## Syncing to Server

In addition to local persistence, the language preference is synced to the server as `user.preferredLocale` via an API call. This ensures the preference follows the user across devices and platforms. The server uses this field to determine the locale for server-rendered content and transactional emails. See [User Syncs Locale Preference](user-syncs-locale-preference.md) for the full syncing flow, and [System Detects Locale](system-detects-locale.md) for how the server resolves locale on each request.

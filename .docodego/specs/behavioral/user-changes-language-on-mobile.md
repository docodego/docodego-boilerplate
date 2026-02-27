---
id: SPEC-2026-078
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Changes Language on Mobile

## Intent

This spec defines how an authenticated user changes the application
language within the Expo mobile app from the settings screen. The
settings screen presents a localized language selector listing the
supported languages — English and Arabic — with each option displayed
in its own native script so the user can identify their preference
regardless of the currently active locale. When the user selects a
different language, the app calls `i18next.changeLanguage(locale)` with
the selected locale code, which loads the new translation resources and
re-renders all translated strings throughout the application including
navigation labels, button text, form labels, and headings. When the
user switches to Arabic, the app calls `I18nManager.forceRTL(true)` to
flip the entire layout direction at the React Native framework level,
reversing `flexDirection`, `textAlign`, and all directional styles.
When switching back to English, `I18nManager.forceRTL(false)` restores
the left-to-right orientation. Unlike the web where `dir` attribute
changes take effect instantly, React Native requires an app restart for
the RTL direction change to take full effect, so the app prompts the
user to restart when an RTL direction change is detected. The selected
language is persisted to MMKV storage on the device so that on
subsequent launches the stored locale is read during i18next
initialization and applied before the first render, ensuring the user
always returns to the app in their chosen language with zero flash of
the default locale. The language preference is also synced to the
server as `user.preferredLocale` via an API call so the preference
follows the user across devices and platforms.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| i18next.changeLanguage() (locale switching API that loads new translation resources and triggers re-render of all translated strings) | write | When the user selects a different language from the selector on the mobile settings screen, the app calls this function with the selected locale code to load the new translation resources and re-render the UI | The locale change fails and the UI remains in the current language — the app catches the changeLanguage error, logs the failure, and displays a localized toast notification telling the user that the language switch did not complete |
| I18nManager.forceRTL() (React Native layout direction API that toggles the entire layout between left-to-right and right-to-left orientations) | write | Immediately after i18next.changeLanguage() resolves and the new locale is Arabic, the app calls `I18nManager.forceRTL(true)` to flip the layout direction, or `forceRTL(false)` when switching back to English | The RTL flag fails to apply and the layout remains in the previous direction — the app logs the I18nManager error and prompts the user to restart the app manually to correct the layout direction |
| react-native-mmkv (native key-value storage used to persist the selected locale code on the device between app launches) | read/write | On language change the app writes the selected locale code to MMKV storage, and on app initialization i18next reads the stored locale to restore the language before the first render | The app falls back to the default English locale when MMKV storage is unavailable, and the user's language preference is lost between sessions — each launch starts in English until the user manually reselects their language |
| user.preferredLocale server sync API (endpoint that persists the locale preference to the server database so the language follows the user across devices and platforms) | write | After the language change completes locally and the new locale is persisted to MMKV, the app fires an API call to update `user.preferredLocale` on the server with the newly selected locale code | The server sync fails and the locale preference remains local to the device only — the app logs the API error, retries on the next app launch, and the user's preference does not follow them to other devices until the sync succeeds |
| Language selector UI (settings screen component displaying self-labelled language options in their own native scripts for identification regardless of the active locale) | render | When the user navigates to the settings screen within the Expo mobile app, the language selector renders with 2 options: English displayed as "English" and Arabic displayed as its Arabic script label | The language selector fails to render and the user cannot change the language — the app logs the component render error and the settings screen displays without the selector until the user navigates away and returns |
| Restart prompt dialog (modal alert shown to the user when an RTL direction change is detected and a full app restart is required for the layout flip to take effect) | render | Immediately after I18nManager.forceRTL() is called and the RTL direction changes from the previous state, the app displays a restart prompt telling the user to restart for the layout change to take full effect | The restart prompt fails to display and the user is not informed that a restart is needed — the app logs the prompt rendering failure and the layout direction does not visually update until the next manual app restart |

## Behavioral Flow

1. **[User]** navigates to the settings screen within the Expo mobile
    app, where a localized language selector is rendered listing the
    supported languages: English and Arabic, with each option displayed
    in its own native script

2. **[User]** selects a different language from the selector — if the
    current language is English the user selects Arabic, or if Arabic
    the user selects English

3. **[App]** calls `i18next.changeLanguage(locale)` with the selected
    locale code — i18next loads the new translation resources and
    re-renders all translated strings throughout the application
    including navigation labels, button text, form labels, headings,
    and all other translated content without a navigation event

4. **[App]** when the user switches to Arabic, calls
    `I18nManager.forceRTL(true)` to flip the entire layout direction
    — React Native's layout engine reverses `flexDirection`,
    `textAlign`, and all directional styles at the framework level so
    the layout mirrors to right-to-left orientation

5. **[App]** when the user switches back to English, calls
    `I18nManager.forceRTL(false)` to restore the left-to-right
    orientation — React Native's layout engine returns all directional
    styles to their default left-to-right values

6. **[App]** detects that an RTL direction change occurred (either
    from LTR to RTL or from RTL to LTR) and displays a restart prompt
    dialog telling the user to restart the app for the layout direction
    change to take full visual effect across the entire application

7. **[App]** writes the selected locale code to MMKV storage on the
    device immediately after i18next.changeLanguage() resolves — on
    subsequent app launches the stored locale is read during i18next
    initialization so the correct language and text direction are
    applied before the first render

8. **[App]** fires an API call to update `user.preferredLocale` on the
    server with the newly selected locale code — the server persists
    the preference so it follows the user across devices and platforms
    for server-rendered content and transactional emails

9. **[Server]** receives the preferredLocale update and writes the
    new locale value to the user record in the database — the server
    uses this field to determine the locale for server-rendered content
    and transactional emails sent to this user

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| displaying_english | switching_to_arabic | User selects Arabic from the language selector on the mobile settings screen | The current active locale in i18next is English and the selected locale code differs from the current one |
| switching_to_arabic | displaying_arabic_pending_restart | i18next.changeLanguage("ar") resolves, I18nManager.forceRTL(true) is called, and the restart prompt is shown to the user | Arabic translation resources loaded and the forceRTL call completed without error |
| displaying_arabic_pending_restart | displaying_arabic_rtl | The user restarts the app and the RTL layout direction takes full effect across the entire React Native view hierarchy | The app process restarted and I18nManager.isRTL equals true on the new launch |
| displaying_arabic | switching_to_english | User selects English from the language selector on the mobile settings screen | The current active locale in i18next is Arabic and the selected locale code differs from the current one |
| switching_to_english | displaying_english_pending_restart | i18next.changeLanguage("en") resolves, I18nManager.forceRTL(false) is called, and the restart prompt is shown to the user | English translation resources loaded and the forceRTL call completed without error |
| displaying_english_pending_restart | displaying_english_ltr | The user restarts the app and the LTR layout direction takes full effect across the entire React Native view hierarchy | The app process restarted and I18nManager.isRTL equals false on the new launch |
| app_initializing | displaying_stored_locale | The app reads the stored locale from MMKV storage during i18next initialization and applies it before the first render with the matching RTL direction | A valid locale code exists in MMKV storage and the corresponding translation resources are available for loading |
| app_initializing | displaying_english | The app initializes without a stored locale in MMKV or the stored locale is invalid and falls back to the default English locale with LTR direction | No locale is found in MMKV storage or the stored value does not match any supported locale code in the configuration |

## Business Rules

- **Rule changeLanguage-rerenders-all-strings:** IF the user selects a
    different language from the selector THEN the app calls
    `i18next.changeLanguage(locale)` and all translated strings in the
    UI re-render to the new language — the count of elements displaying
    stale translations from the previous locale equals 0 after the
    change completes
- **Rule arabic-forces-rtl:** IF the user selects Arabic from the
    language selector THEN the app calls `I18nManager.forceRTL(true)`
    to flip the layout direction to right-to-left — the value of
    the `I18nManager.forceRTL` call argument equals true when the
    selected locale is Arabic
- **Rule ltr-restored-on-english:** IF the user selects English from
    the language selector THEN the app calls
    `I18nManager.forceRTL(false)` to restore the left-to-right layout
    direction — the value of the `I18nManager.forceRTL` call argument
    equals false when the selected locale is English
- **Rule restart-required-for-rtl-change:** IF the RTL direction
    changes as a result of a language switch (LTR to RTL or RTL to LTR)
    THEN the app displays a restart prompt dialog informing the user
    that a restart is needed — the count of restart prompts shown per
    RTL direction change equals 1
- **Rule locale-persisted-to-mmkv:** IF the user selects a language
    from the selector THEN the app writes the selected locale code to
    MMKV storage immediately after i18next.changeLanguage() resolves —
    the count of MMKV writes per language change equals 1 and the
    stored value matches the newly selected locale code
- **Rule locale-synced-to-server:** IF the user selects a language
    from the selector THEN the app fires an API call to update
    `user.preferredLocale` on the server with the selected locale code
    — the count of API calls to the preferredLocale endpoint per
    language change equals 1
- **Rule mmkv-read-before-first-render:** IF the app launches and a
    locale code exists in MMKV storage THEN i18next initializes with
    the stored locale and the corresponding RTL direction is applied
    before the first visible render — the count of frames rendered with
    the default locale before the stored locale loads equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated User (signed in with a valid session token and accessing the settings screen within the Expo mobile app) | Selects any supported language from the selector on the settings screen, persists the preference to MMKV storage, syncs the locale to the server via the preferredLocale API, and triggers the RTL layout direction change with restart prompt | No language-related actions are denied to an authenticated user — all supported languages are selectable and the preference persists locally and syncs to the server | The language selector is fully visible and interactive on the settings screen, displaying all supported languages with the current selection highlighted and each option labelled in its own native script |
| Unauthenticated User (not signed in, with no valid session token in the encrypted credential store) | No actions are permitted — the settings screen requires authentication and the Expo Router route guard redirects unauthenticated users to the sign-in screen before any settings components mount | Cannot view or interact with the language selector because the settings screen is behind the authentication guard and does not render for unauthenticated users in the Expo mobile app | No settings UI is visible — the redirect to the sign-in screen occurs before any settings screen components mount in the React Native view hierarchy |

## Constraints

- The language switch via i18next.changeLanguage() completes within
    500 ms of the user selecting a new locale from the selector —
    measured from the selection event to all translated strings
    displaying in the new language, with 0 untranslated strings visible
    after completion.
- The restart prompt dialog appears within 200 ms of the
    I18nManager.forceRTL() call completing — the count of milliseconds
    from the forceRTL call return to the restart prompt being visible
    equals 200 or fewer.
- The MMKV write for the selected locale completes within 10 ms of
    the write call — the count of milliseconds from MMKV write start
    to write confirmation equals 10 or fewer because MMKV is a
    synchronous native storage engine.
- The language selector on the settings screen displays exactly 2
    options (English and Arabic) — the count of options in the selector
    equals 2 and each option's label is rendered in its own native
    language script for identification.
- The server sync API call to update user.preferredLocale fires within
    1000 ms of the local language change completing — the count of
    milliseconds from MMKV write completion to the API request being
    sent equals 1000 or fewer.
- On subsequent app launches with a stored locale in MMKV, the stored
    locale is applied during i18next initialization before the first
    visible render — the count of frames rendered with the default
    English locale before the stored locale takes effect equals 0.

## Acceptance Criteria

- [ ] The language selector on the mobile settings screen displays exactly 2 options (English and Arabic) and the count of selector options equals 2
- [ ] Each language option in the selector is labelled in its own native script and the count of options not displayed in their own native language equals 0
- [ ] Selecting Arabic from the selector calls `i18next.changeLanguage("ar")` and all translated strings update to Arabic — the count of elements still displaying English text after the change equals 0
- [ ] Selecting English from the selector calls `i18next.changeLanguage("en")` and all translated strings update to English — the count of elements still displaying Arabic text after the change equals 0
- [ ] When the user switches to Arabic, `I18nManager.forceRTL(true)` is called and the forceRTL argument equals true
- [ ] When the user switches to English, `I18nManager.forceRTL(false)` is called and the forceRTL argument equals false
- [ ] When an RTL direction change occurs (LTR to RTL or RTL to LTR), a restart prompt dialog is shown and the count of restart prompts displayed per direction change equals 1
- [ ] The selected locale code is written to MMKV storage after each language change and the count of MMKV writes per language change equals 1
- [ ] On app launch with a stored locale in MMKV, i18next initializes with the stored locale and the count of frames rendered with the default locale before the stored locale loads equals 0
- [ ] The app fires an API call to update user.preferredLocale on the server after each language change and the count of API calls per language change equals 1
- [ ] The language switch from English to Arabic completes within 500 ms — the elapsed time from selection event to all strings re-rendered is at most 500 ms
- [ ] Navigation labels, button text, form labels, and headings all update to the selected language in place — the count of component unmount events triggered by the language switch equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User selects the same language that is already active from the selector on the settings screen | The app calls `i18next.changeLanguage()` with the current locale code, which resolves immediately as a no-op — no MMKV write, no forceRTL call, and no restart prompt occur because the locale and direction did not change | The count of MMKV writes triggered by the selection equals 0, the count of forceRTL calls equals 0, and the count of restart prompts shown equals 0 |
| User switches language while the device is in airplane mode with no network connectivity available | The language change completes locally — i18next loads bundled translation resources, MMKV persists the locale, and the restart prompt appears if the direction changed — but the server sync API call to update user.preferredLocale fails due to no network | The active locale in i18next matches the selected language, the MMKV stored value matches the selected locale code, and the count of successful server sync responses equals 0 because the network is unavailable |
| User switches to Arabic on a screen that contains user-generated content not managed by i18next translation functions | The I18nManager.forceRTL(true) call flips the layout direction for all content including user-generated text regions, which reflow to right-to-left — i18next does not translate user content but the directional layout still mirrors it at the framework level | The layout direction for user-generated content regions matches RTL, and the count of i18next translation calls for user-generated content equals 0 |
| MMKV storage is corrupted or inaccessible when the user changes language on the settings screen | The language change still completes in the current session because i18next holds the active locale in memory — the MMKV write fails and the app logs a warning about the persistence failure, but the UI continues in the new language | The active locale in i18next matches the selected language, all translated strings display correctly, and the count of uncaught exceptions from the MMKV write equals 0 because the error is caught |
| User changes language, dismisses the restart prompt without restarting, and then changes language again before restarting the app | The second language change overrides the first — i18next loads the new translation resources, the forceRTL call updates to the latest direction, MMKV stores the latest locale, and a new restart prompt appears if the direction changed from the current runtime direction | The MMKV stored locale matches the most recently selected language, the active i18next locale matches the last selection, and the count of active locale values after both changes settle equals 1 |
| User changes language immediately after the app launches before the server sync from the previous change has completed | The new language change queues a new server sync API call — the previous in-flight sync completes or is superseded by the latest locale value, and the final server-side preferredLocale reflects the most recently selected language | The server-side user.preferredLocale value matches the last selected locale code, and the count of preferredLocale values stored on the server equals 1 |

## Failure Modes

- **i18next.changeLanguage() fails to load translation resources for the target locale on the mobile app**

    **What happens:** The user selects a new language from the selector on the settings screen and the app calls `i18next.changeLanguage()` with the target locale code, but the translation resource loading fails because the bundled resources are corrupted or the locale code does not match any available translation bundle in the app binary.

    **Source:** A corrupted OTA update that damaged the translation JSON files in the app bundle, a build configuration error that excluded the target locale's translation namespace from the binary, or an unsupported locale code passed to changeLanguage that does not match any configured language bundle.

    **Consequence:** The UI remains in the previous language because i18next cannot switch to a locale without loaded resources — the user sees no change in the displayed text, the forceRTL call is not triggered because the language change did not complete, and the MMKV storage is not updated with the failed locale.

    **Recovery:** The app catches the changeLanguage error, falls back to keeping the current locale active, and logs the translation resource loading failure — a toast notification alerts the user that the language switch did not complete, and the user can retry by selecting the language again after restarting the app.

- **MMKV storage write fails when persisting the selected locale code after a language change**

    **What happens:** After i18next.changeLanguage() resolves and the UI updates to the new language, the app attempts to write the selected locale code to MMKV storage but the write operation throws an error because the MMKV file is corrupted, the filesystem denies write access, or the device storage is full and no additional data can be written.

    **Source:** A previous force-kill interrupted an MMKV write operation and corrupted the storage file, the operating system reclaimed app storage due to critically low disk space, or a device migration transferred the app without its complete data directory leaving the MMKV file inaccessible.

    **Consequence:** The language change works correctly in the current session because i18next holds the active locale in memory, but the preference is lost when the user closes the app — the next launch falls back to the default English locale and the user has to reselect their preferred language manually from the settings screen.

    **Recovery:** The app catches the MMKV write error, logs a warning to the console with the storage error details, and degrades to in-memory-only locale persistence for the current session — the UI continues to function in the selected language without interruption, and the next app launch retries writing to MMKV when the user changes language again.

- **Server sync API call to update user.preferredLocale fails after the local language change completes**

    **What happens:** The app fires the API call to update `user.preferredLocale` on the server with the newly selected locale code, but the request fails due to a network timeout, server error, or the authentication token expiring before the request completes, leaving the server-side locale preference unchanged.

    **Source:** A transient network interruption between the mobile device and the API server, a server-side outage or rate limit that rejects the preference update request, or the user's session token expiring between the local language change and the server sync API call.

    **Consequence:** The locale preference is persisted locally in MMKV but does not reach the server — the user's language preference does not follow them to other devices or platforms, and server-rendered content such as transactional emails continues to use the previous locale until a future sync succeeds.

    **Recovery:** The app catches the API error, logs the sync failure with the HTTP status code and error details, and retries the server sync on the next app launch by reading the MMKV-stored locale and sending a fresh preferredLocale update — the local language preference remains unaffected by the server sync failure.

## Declared Omissions

- This specification does not define the full list of supported locales beyond English and Arabic — adding new languages requires updating the i18next configuration, providing translation JSON files, and extending the language selector component with new options.
- This specification does not cover the translation authoring workflow, translation file format, or namespace organization within @repo/i18n — those concerns are defined in the shared-i18n foundation spec as infrastructure-level details separate from the mobile language switching flow.
- This specification does not address automatic locale detection from the device operating system settings during app launch — device locale detection is covered by the user-launches-mobile-app specification and the expo-localization integration described there.
- This specification does not define the full server sync protocol, retry logic, or conflict resolution for user.preferredLocale — the complete syncing flow is documented in the user-syncs-locale-preference specification as a cross-platform concern.
- This specification does not cover locale-specific content formatting such as date formats, number formats, or currency display — those are handled by native Intl APIs and are outside the scope of the i18next language switching mechanism defined here.

## Related Specifications

- [user-changes-language](user-changes-language.md) — Defines the web-platform language change flow using the same i18next.changeLanguage() mechanism but with `dir` attribute on `<html>` instead of I18nManager.forceRTL() and localStorage instead of MMKV for persistence
- [user-syncs-locale-preference](user-syncs-locale-preference.md) — Defines the full server sync protocol for user.preferredLocale that the mobile language change triggers after persisting the locale locally to MMKV storage on the device
- [user-launches-mobile-app](user-launches-mobile-app.md) — Defines the mobile app launch sequence including MMKV state hydration and expo-localization device locale detection that determines the initial language and RTL direction before the first render
- [user-navigates-mobile-app](user-navigates-mobile-app.md) — Defines the mobile navigation structure including tab bar and screen transitions that re-render translated labels when i18next.changeLanguage() updates the active locale on the mobile app
- [session-lifecycle](session-lifecycle.md) — Defines the authentication session lifecycle including token validation that gates access to the mobile settings screen where the language selector is rendered for authenticated users

---
id: SPEC-2026-049
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Changes Language

## Intent

This spec defines how an authenticated user changes the application
language from the appearance settings page at `/app/settings/appearance`.
The language selector dropdown lists all supported languages — English
and Arabic — and selecting a different locale triggers
`i18next.changeLanguage(locale)` to load the new translation resources
and re-render all translated strings without a page reload or route
change. When Arabic is selected, the app sets `dir="rtl"` on the
`<html>` element and Tailwind CSS logical properties mirror the entire
layout automatically. When English is selected, `dir="ltr"` is restored
and the layout returns to left-to-right orientation. On the desktop
app built with Tauri, all translation files are bundled inline and
`i18next.changeLanguage()` resolves synchronously with zero network
requests. The selected locale persists to localStorage so the correct
language and text direction are applied on the next visit before the
first render, preventing any flash of the default locale.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| i18next.changeLanguage() (locale switching API) | write | When the user selects a different language from the dropdown on the appearance settings page, the client calls this function with the selected locale code to load new translation resources | The locale change fails silently and the UI remains in the current language — the client logs the changeLanguage error and displays a localized toast notification informing the user that the language switch did not complete |
| `dir` attribute on `<html>` element (document directionality) | write | Immediately after i18next.changeLanguage() resolves, the client sets the `dir` attribute on the `<html>` element to `rtl` for Arabic or `ltr` for English to control the document's text direction | The document direction remains unchanged and the layout does not mirror — the user sees left-to-right layout with Arabic text, causing misaligned reading flow until the page is reloaded and directionality is corrected |
| localStorage (locale persistence store) | read/write | On language change the client writes the selected locale to localStorage, and on app initialization i18next reads the stored locale to restore the language before the first render | The client falls back to the default locale (English) when localStorage is unavailable, and the user's language preference is lost between sessions — each visit starts in English until the user manually selects their preferred language again |
| @repo/i18n translation resources (JSON namespace files) | read | When i18next.changeLanguage() is called, i18next loads the translation JSON files for the target locale — on web these are fetched over the network, on desktop they are read from the bundled inline resources | The translation resources fail to load and i18next falls back to displaying raw translation keys instead of localized strings — the client logs the resource loading failure and the user sees keys like `settings.appearance.title` throughout the interface |
| Tailwind logical properties (CSS layout mirroring system) | read | When the `dir` attribute changes on `<html>`, Tailwind CSS logical properties (`ms-`, `me-`, `ps-`, `pe-`, `start`, `end`) automatically resolve to the correct physical direction based on the document's directionality | Logical properties are not affected by unavailability since they are compiled into the CSS at build time — if a component uses physical properties instead of logical ones, that specific component does not mirror correctly and the user sees inconsistent layout direction for that element |

## Behavioral Flow

1. **[User]** navigates to `/app/settings/appearance` where a language
    selector dropdown is rendered alongside the theme controls, listing
    the supported languages: English and Arabic

2. **[User]** selects a different language from the dropdown — if the
    current language is English the user selects Arabic, or if Arabic
    the user selects English

3. **[Client]** calls `i18next.changeLanguage(locale)` with the
    selected locale code — i18next loads the new translation resources
    for that locale and re-renders all translated strings throughout
    the application without a page reload or route change

4. **[Client]** updates every piece of text rendered through i18next's
    translation functions in place: navigation labels, button text,
    form labels, headings, and any other translated content swap to the
    new language immediately without any visible delay or flicker

5. **[Client]** when the user switches to Arabic, sets `dir="rtl"` on
    the `<html>` element — Tailwind CSS logical properties throughout
    the UI (`ms-` and `me-` instead of `ml-` and `mr-`, `ps-` and
    `pe-` instead of `pl-` and `pr-`, `start` and `end` instead of
    `left` and `right`) cause the entire layout to mirror automatically:
    the sidebar moves to the right side, text aligns to the right, and
    spacing flips to match the right-to-left reading direction

6. **[Client]** when the user switches back to English, sets `dir="ltr"`
    on the `<html>` element — all logical properties resolve back to
    their LTR equivalents and the layout restores to the standard
    left-to-right orientation with the sidebar on the left side

7. **[Client]** on the desktop app built with Tauri, all translation
    files are bundled inline rather than lazy-loaded over the network —
    since the app ships as a local binary with no download cost for
    assets, `i18next.changeLanguage()` resolves synchronously from the
    bundled resources with zero network requests

8. **[Client]** writes the selected locale code to localStorage
    immediately after the language change completes — on the next visit,
    the stored locale is loaded during i18next initialization so the
    correct language and text direction are applied before the first
    render, and the user always returns to the app in their chosen
    language without any flash of the default locale

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| displaying_english | loading_arabic | User selects Arabic from the language selector dropdown on the appearance settings page | The current active locale in i18next is English and the selected locale code differs from the current one |
| loading_arabic | displaying_arabic | i18next.changeLanguage() resolves after loading Arabic translation resources and the client sets `dir="rtl"` on the `<html>` element | Arabic translation resources loaded and the `dir` attribute on `<html>` equals `rtl` |
| displaying_arabic | loading_english | User selects English from the language selector dropdown on the appearance settings page | The current active locale in i18next is Arabic and the selected locale code differs from the current one |
| loading_english | displaying_english | i18next.changeLanguage() resolves after loading English translation resources and the client sets `dir="ltr"` on the `<html>` element | English translation resources loaded and the `dir` attribute on `<html>` equals `ltr` |
| app_initializing | displaying_stored_locale | The app reads the stored locale from localStorage during i18next initialization and applies it before the first render | A valid locale code exists in localStorage and the corresponding translation resources are available for loading |
| app_initializing | displaying_english | The app initializes without a stored locale in localStorage or the stored locale is invalid and falls back to the default English locale | No locale is found in localStorage or the stored value does not match any supported locale code in the configuration |
| loading_arabic | displaying_english | i18next.changeLanguage() fails to load Arabic translation resources and the client falls back to the current English locale | The Arabic translation resource request returned an error or timed out and i18next reverted to the previous locale |
| loading_english | displaying_arabic | i18next.changeLanguage() fails to load English translation resources and the client falls back to the current Arabic locale | The English translation resource request returned an error or timed out and i18next reverted to the previous locale |

## Business Rules

- **Rule rtl-on-arabic:** IF the user selects Arabic from the language
    selector THEN the client sets `dir="rtl"` on the `<html>` element
    and all Tailwind CSS logical properties (`ms-`, `me-`, `ps-`, `pe-`,
    `inset-inline-start`, `inset-inline-end`, `text-start`, `text-end`)
    resolve to their right-to-left physical equivalents — the count of
    elements using physical directional properties (`ml-`, `mr-`, `pl-`,
    `pr-`, `left`, `right`) instead of logical properties equals 0
- **Rule ltr-on-english:** IF the user selects English from the language
    selector THEN the client sets `dir="ltr"` on the `<html>` element
    and all Tailwind CSS logical properties resolve to their
    left-to-right physical equivalents — the `<html>` element's `dir`
    attribute value equals `ltr` after the language change completes
- **Rule localStorage-persistence:** IF the user selects a language
    from the dropdown THEN the client writes the selected locale code
    to localStorage immediately after i18next.changeLanguage() resolves
    — the count of localStorage writes per language change equals 1 and
    the stored value matches the newly selected locale code
- **Rule desktop-bundled-no-network:** IF the app is running in the
    Tauri desktop environment THEN i18next.changeLanguage() resolves
    from bundled inline translation resources with zero network requests
    — the count of HTTP requests issued during a language change on
    desktop equals 0
- **Rule no-page-reload:** IF the user selects a different language
    from the dropdown THEN the language change completes entirely on the
    client without a page reload, route change, or full DOM re-mount —
    the count of page navigation events during a language change
    equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | Selects any supported language from the dropdown on the appearance settings page, and the selected locale persists to localStorage and applies immediately across the entire application UI | No language-related actions are denied to the owner — all supported languages are selectable and the preference persists across sessions | The language selector dropdown is fully visible and interactive, displaying all supported languages with the current selection highlighted |
| Admin | Selects any supported language from the dropdown on the appearance settings page, and the selected locale persists to localStorage and applies immediately across the entire application UI | No language-related actions are denied to admins — all supported languages are selectable and the preference persists across sessions | The language selector dropdown is fully visible and interactive, displaying all supported languages with the current selection highlighted |
| Member | Selects any supported language from the dropdown on the appearance settings page, and the selected locale persists to localStorage and applies immediately across the entire application UI | No language-related actions are denied to members — language preference is a personal setting that does not affect other users or organization-level configuration | The language selector dropdown is fully visible and interactive, displaying all supported languages with the current selection highlighted |
| Unauthenticated | No actions are permitted — the appearance settings page at `/app/settings/appearance` requires authentication and the route guard redirects unauthenticated users to the sign-in page | Cannot view or interact with the language selector because the settings page is behind the authentication guard and does not render for unauthenticated users | No settings UI is visible — the redirect to sign-in occurs before any settings page components mount in the DOM |

## Constraints

- The language switch must complete within 500 ms of the user selecting
    a new locale from the dropdown — measured from the dropdown
    selection event to all translated strings displaying in the new
    language, with 0 untranslated strings visible after completion.
- The `dir` attribute on the `<html>` element must update within 100 ms
    of i18next.changeLanguage() resolving — the count of render frames
    where the `dir` attribute does not match the active locale's
    expected directionality equals 0 after the update completes.
- The localStorage write for the selected locale must complete before
    any subsequent page unload event — the count of page reloads that
    fail to restore the persisted locale equals 0 when localStorage
    is available and writable.
- On the Tauri desktop app, i18next.changeLanguage() must resolve
    with 0 network requests — the total count of HTTP requests issued
    by the i18next resource loader during a desktop language change
    equals 0 because all translation files are bundled inline.
- All UI components must use Tailwind CSS logical properties for
    directional styling — the count of physical directional classes
    (`ml-`, `mr-`, `pl-`, `pr-`, `left-`, `right-`, `text-left`,
    `text-right`) in the rendered component tree equals 0, with the
    sole exception of `translate-x` which has no logical equivalent
    and uses an `rtl:` override instead.
- The language selector dropdown must display exactly 2 options
    (English and Arabic) — the count of options in the dropdown equals
    2 and each option's label is rendered in its own native language
    script.

## Acceptance Criteria

- [ ] The language selector dropdown on `/app/settings/appearance` displays exactly 2 options (English and Arabic) and the count of dropdown options equals 2
- [ ] Selecting Arabic from the dropdown calls `i18next.changeLanguage("ar")` and all translated strings in the UI update to Arabic text — the count of elements still displaying English translation keys equals 0 after the change completes
- [ ] Selecting English from the dropdown calls `i18next.changeLanguage("en")` and all translated strings in the UI update to English text — the count of elements still displaying Arabic text equals 0 after the change completes
- [ ] When Arabic is active, the `<html>` element's `dir` attribute is non-empty and set to `rtl`, and the count of layout regions that fail to mirror to right-to-left orientation equals 0
- [ ] When English is active, the `<html>` element's `dir` attribute is non-empty and set to `ltr`, and the count of layout regions that fail to render in left-to-right orientation equals 0
- [ ] The language change completes without a page reload or route change — the count of `beforeunload` events and navigation events during a language switch equals 0
- [ ] The selected locale is written to localStorage immediately after the language change — the count of localStorage writes per language change equals 1 and `localStorage.getItem("i18nextLng")` is non-empty and matches the selected locale code
- [ ] On page reload, the stored locale is read from localStorage and applied during i18next initialization — the UI renders in the persisted language on the first paint with 0 visible flashes of the default English locale
- [ ] On the Tauri desktop app, switching language issues 0 network requests — the count of HTTP requests captured during `i18next.changeLanguage()` on desktop equals 0 because translation resources are bundled inline
- [ ] All directional styling uses Tailwind CSS logical properties — the count of physical directional utility classes (`ml-`, `mr-`, `pl-`, `pr-`) in the rendered component tree equals 0 except for `translate-x` which uses an `rtl:` override
- [ ] The language switch from English to Arabic completes within 500 ms — the elapsed time from the dropdown selection event to the final translated string render is at most 500 ms
- [ ] Navigation labels, button text, form labels, and headings all update to the selected language in place without unmounting or remounting their parent components — the count of component unmount events during a language switch equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User selects the same language that is already active from the dropdown | The client calls `i18next.changeLanguage()` with the current locale code, which resolves immediately as a no-op — no re-render, no localStorage write, and no `dir` attribute change occur because the locale did not change | The count of re-render cycles triggered by the language change equals 0, and the localStorage value remains unchanged from before the selection |
| User switches language while a network request for translation resources is still in progress from a previous language switch | The client cancels or ignores the previous in-flight translation resource request and processes only the latest language selection — the UI settles on the most recently selected locale without displaying an intermediate language | The final active locale in i18next matches the last language selected by the user, and the count of active locale values after settling equals 1 |
| User switches to Arabic on a page that contains user-generated content not managed by i18next | The `dir="rtl"` attribute applies to the entire document including user-generated content regions, which reflow to right-to-left — i18next does not translate user content but the directional layout still mirrors it | The `dir` attribute on `<html>` equals `rtl`, user-generated text blocks reflow to right-aligned, and the count of i18next translation calls for user content equals 0 |
| localStorage is full or write-protected when the user changes language | The language change still completes in the current session because i18next holds the active locale in memory — the localStorage write fails silently and the client logs a warning about the persistence failure | The active locale in i18next matches the selected language, all translated strings display correctly, and the count of thrown exceptions from the localStorage write equals 0 because the error is caught |
| User opens the app for the first time with no stored locale in localStorage | i18next initializes with the default English locale, sets `dir="ltr"` on `<html>`, and renders all strings in English — no fallback or error state occurs because English is the configured default locale | The active locale equals `en`, the `dir` attribute equals `ltr`, and the count of missing translation warnings in the console equals 0 |
| User clears browser storage and reloads the page after previously selecting Arabic | The app falls back to the default English locale because the stored Arabic preference was deleted — i18next initializes with English, sets `dir="ltr"`, and the user must manually re-select Arabic from the settings page | The active locale after reload equals `en`, the `dir` attribute equals `ltr`, and the language selector dropdown shows English as the current selection |

## Failure Modes

- **Translation resource loading failure: i18next cannot load the target locale's JSON files**

    **What happens:** The user selects a new language from the dropdown and `i18next.changeLanguage()` attempts to fetch the translation JSON files for the target locale, but the network request fails due to a server error, DNS failure, or timeout, leaving i18next without the resources needed to display translated strings in the new language.

    **Source:** A transient network interruption between the browser and the static asset server, a CDN cache miss combined with an origin server outage, or a deployment that removed or renamed the translation JSON file for the target locale from the asset bundle.

    **Consequence:** The UI remains in the previous language because i18next cannot switch to a locale without loaded resources — the user sees no change in the displayed text and the `dir` attribute is not updated because the language change did not complete, leaving the layout in its current directional orientation.

    **Recovery:** The client falls back to keeping the current locale active and logs the translation resource loading error to the console — a toast notification alerts the user that the language switch failed, and the user can retry by selecting the language again from the dropdown after the network issue resolves.

- **localStorage write failure: selected locale cannot be persisted across sessions**

    **What happens:** After i18next.changeLanguage() resolves and the UI updates to the new language, the client attempts to write the selected locale code to localStorage but the write operation throws an error because the storage quota is exceeded, the browser has disabled localStorage, or the user is in a restricted browsing mode that blocks persistent storage access entirely.

    **Source:** Browser privacy settings that disable localStorage access, storage quota exceeded from accumulated data written by other parts of the application or third-party scripts, or a browser extension that intercepts and blocks localStorage write operations for security or privacy enforcement.

    **Consequence:** The language change works correctly in the current session because i18next holds the active locale in memory, but the preference is lost when the user closes or reloads the page — the app falls back to the default English locale on the next visit and the user must re-select their preferred language manually from the settings page every time they return.

    **Recovery:** The client catches the localStorage write error, logs a warning to the console with the storage error details, and degrades to in-memory-only locale persistence for the current session — the UI continues to function in the selected language without interruption, and the user is not shown an error dialog because the failure only affects cross-session persistence.

- **`dir` attribute update failure: document directionality does not match the active locale**

    **What happens:** The client calls `i18next.changeLanguage("ar")` and the translation strings update to Arabic, but the code that sets `dir="rtl"` on the `<html>` element throws an error or is bypassed due to a race condition, leaving the document in `dir="ltr"` mode while displaying Arabic text in a left-to-right layout.

    **Source:** A race condition between the i18next language change callback and the DOM update logic that sets the `dir` attribute, a browser extension that intercepts and blocks mutations to the `<html>` element's attributes, or an error in the event handler that reads the new locale and maps it to the correct directionality value.

    **Consequence:** The user sees Arabic text rendered in a left-to-right layout — the sidebar remains on the left, text aligns to the left, and spacing follows LTR conventions, making the Arabic content difficult to read and navigate because the visual flow contradicts the natural right-to-left reading direction of Arabic script.

    **Recovery:** The language change callback retries setting the `dir` attribute on the `<html>` element after a 100 ms delay if the attribute value does not match the expected directionality for the active locale — the client logs the mismatch and the retry attempt, and if the retry also fails the client notifies the user to reload the page to correct the layout direction.

## Declared Omissions

- This specification does not define the full list of supported locales beyond English and Arabic — adding new languages requires updating the i18next configuration, providing translation JSON files, and extending the language selector dropdown options.
- This specification does not cover the translation authoring workflow, translation file format, or namespace organization within @repo/i18n — those concerns are defined in the shared-i18n foundation spec as infrastructure-level details.
- This specification does not address server-side locale detection, Accept-Language header parsing, or automatic locale selection based on browser settings — the locale is always set explicitly by the user through the settings dropdown or read from localStorage.
- This specification does not define the theme toggle behavior or any other controls on the appearance settings page beyond the language selector — theme switching is covered by its own dedicated behavioral specification.
- This specification does not cover locale-specific content formatting such as date formats, number formats, or currency display — those are handled by native Intl APIs and are outside the scope of the i18next language switching mechanism defined here.

## Related Specifications

- [shared-i18n](../foundation/shared-i18n.md) — Defines the i18next initialization, namespace loading strategy, and translation resource infrastructure that the language selector relies on to load and apply locale-specific translation files
- [user-navigates-the-dashboard](user-navigates-the-dashboard.md) — Describes the dashboard shell layout including the sidebar that mirrors position when the document direction changes from LTR to RTL during a language switch
- [session-lifecycle](session-lifecycle.md) — Covers authentication and session management that gates access to the appearance settings page where the language selector dropdown is rendered
- [auth-server-config](../foundation/auth-server-config.md) — Configures the authentication guard that redirects unauthenticated users away from the settings page, preventing access to the language selector without a valid session

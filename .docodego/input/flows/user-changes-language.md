# User Changes Language

## The Language Selector

The user navigates to `/app/settings/appearance`, where a language selector dropdown is available alongside the theme controls. The dropdown lists the supported languages: English and Arabic.

## Switching Languages

When the user selects a different language from the dropdown, the app calls `i18next.changeLanguage(locale)` with the selected locale code. i18next loads the new translation resources for that locale and re-renders all translated strings throughout the application. This happens entirely on the client — no page reload, no route change.

Every piece of text rendered through i18next's translation functions updates in place: navigation labels, button text, form labels, headings, and any other translated content swap to the new language immediately.

## RTL Layout for Arabic

When the user switches to Arabic, the app sets `dir="rtl"` on the `<html>` element. Tailwind CSS uses logical properties throughout the UI — `ms-` and `me-` instead of `ml-` and `mr-`, `ps-` and `pe-` instead of `pl-` and `pr-`, `start` and `end` instead of `left` and `right`. This means the entire layout mirrors automatically: the sidebar moves to the right side, text aligns to the right, and spacing flips to match the right-to-left reading direction.

When the user switches back to English, `dir="ltr"` is set on `<html>`, and the layout restores to the standard left-to-right orientation. All logical properties resolve back to their LTR equivalents.

## Persistence

The selected language is persisted to localStorage. On the next visit, the stored locale is loaded during i18next initialization, so the correct language and text direction are applied before the first render. The user always returns to the app in their chosen language without any flash of the default locale.

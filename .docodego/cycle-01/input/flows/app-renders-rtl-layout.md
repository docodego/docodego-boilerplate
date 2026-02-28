[← Back to Index](README.md)

# App Renders RTL Layout

## Trigger

When the resolved locale is a right-to-left language — Arabic, Hebrew, Farsi, or Urdu — the application switches its entire layout direction. This happens automatically based on the locale detection described in [System Detects Locale](system-detects-locale.md), with no separate user toggle for direction.

## Web Implementation

On the web, the `dir="rtl"` attribute is set on the `<html>` element when the active locale is an RTL language. All layout throughout the application uses Tailwind CSS logical properties exclusively: `ps-` and `pe-` for inline padding (start/end), `ms-` and `me-` for inline margin (start/end), `text-start` and `text-end` for text alignment. Physical directional utilities like `ml-`, `mr-`, `pl-`, `pr-`, `left-`, and `right-` are never used — this is a hard rule across the entire codebase. Because CSS logical properties derive their meaning from the document's `dir` attribute, every layout automatically mirrors when the direction changes: the sidebar moves to the right side of the screen, text aligns to the right, and inline spacing flips correctly.

A `DirectionProvider` from `@repo/ui` wraps the React tree. This provider communicates the current direction to all Shadcn components built on Base UI primitives, so dropdowns, popovers, dialogs, and other overlays position themselves correctly in RTL mode without any component-level overrides. An `icon-directional` utility class is available for icons that should visually mirror in RTL — arrow icons, chevrons, and navigation indicators that carry directional meaning. Icons that are inherently symmetrical (like a settings gear or a search magnifier) do not use this class and remain unchanged.

Switching the language toggles the direction live, with no page reload. The `dir` attribute update propagates through CSS instantly, and all logical properties recalculate. The user sees the layout flip in place.

## Mobile Implementation

React Native has built-in RTL support through its layout engine. When the locale is an RTL language, `I18nManager.forceRTL()` is called during initialization (driven by `expo-localization`). This flips `flexDirection`, `textAlign`, and all directional styles at the framework level. The same principle applies — layout is always authored in start/end terms, never left/right — so the mobile app mirrors correctly without RTL-specific code paths.

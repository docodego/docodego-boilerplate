---
id: SPEC-2026-089
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [System, User]
---

[← Back to Roadmap](../ROADMAP.md)

# App Renders RTL Layout

## Intent

This spec defines how the DoCodeGo application switches its entire layout direction to right-to-left (RTL) when the resolved locale is an RTL language such as Arabic, Hebrew, Farsi, or Urdu. The direction change is triggered automatically by the locale detection flow with no separate user toggle for direction. On the web and desktop, setting `dir="rtl"` on the `<html>` element causes all CSS logical properties to flip layout direction, moving the sidebar to the right side, aligning text to the right, and mirroring inline spacing. The codebase enforces exclusive use of Tailwind CSS logical properties (`ps-`, `pe-`, `ms-`, `me-`, `text-start`, `text-end`) and prohibits physical directional utilities (`ml-`, `mr-`, `pl-`, `pr-`, `left-`, `right-`). A `DirectionProvider` from `@repo/ui` wraps the React tree and communicates the current direction to all Shadcn components built on Base UI primitives. On mobile, React Native's `I18nManager.forceRTL()` flips all layout at the framework level during initialization. Switching language toggles direction live without a page reload on web.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Locale detection chain (platform-specific mechanism described in system-detects-locale that resolves the active locale to a supported language, providing the input signal that determines whether the layout direction is LTR or RTL) | read | At application startup and whenever the user changes their language preference through the language switcher, the RTL layout system reads the resolved locale to determine whether to apply right-to-left direction | The locale detection chain fails to resolve a locale due to a detection error — the system falls back to English which is an LTR language, and the layout renders in the default left-to-right direction without any RTL transformations |
| `dir` attribute on the `<html>` element (the HTML document-level direction attribute that controls CSS logical property behavior for the entire page, set to `rtl` for right-to-left languages and `ltr` for left-to-right languages on web and desktop platforms) | write | When the resolved locale is an RTL language, the application sets `dir="rtl"` on the `<html>` element, and when the locale is an LTR language, it sets `dir="ltr"` — this attribute change triggers all CSS logical properties to recalculate their directional behavior | The `dir` attribute fails to update due to a DOM manipulation error during hydration — the layout remains in its previous direction state (defaulting to LTR if no previous value was set) and the user sees misaligned content until the attribute is corrected |
| `DirectionProvider` from `@repo/ui` (React context provider that wraps the application tree and communicates the current layout direction to all Shadcn components built on Base UI primitives for correct overlay and dropdown positioning) | read/write | When the `dir` attribute changes on the `<html>` element, the `DirectionProvider` updates its context value so all consuming Shadcn components (dropdowns, popovers, dialogs, tooltips) receive the new direction and position themselves correctly in RTL mode | The `DirectionProvider` is missing from the component tree or fails to initialize — Shadcn components built on Base UI primitives do not receive direction context and fall back to their default LTR positioning, causing overlays and dropdowns to appear misaligned in RTL mode |
| Tailwind CSS logical properties (CSS utility classes in the Tailwind configuration that map to CSS logical properties, ensuring layout responds to the document direction rather than fixed physical directions across the entire codebase) | read | On every render cycle, the browser evaluates CSS logical properties (`padding-inline-start`, `margin-inline-end`, `text-align: start`) against the current `dir` attribute value to compute the correct physical direction for each styled element | Tailwind CSS fails to generate the logical property classes during the build process due to a configuration error — the styled elements have no directional padding, margin, or alignment applied, and the layout appears unstyled regardless of the active direction |
| `I18nManager.forceRTL()` React Native API (framework-level API on mobile that flips the entire layout engine's direction to right-to-left, affecting `flexDirection`, `textAlign`, and all directional styles at the framework level for iOS and Android) | write | During mobile application initialization, when `expo-localization` reports an RTL locale, the application calls `I18nManager.forceRTL(true)` to switch the entire React Native layout engine to right-to-left mode before the first render | The `I18nManager.forceRTL()` call fails or is not invoked due to a missing locale detection result — the mobile layout remains in its default LTR direction and Arabic or Hebrew content renders with incorrect alignment and directional flow |
| `icon-directional` CSS utility class (a utility class in the codebase that applies a horizontal mirror transform to icons that carry directional meaning, such as arrows and chevrons, so they point correctly in RTL mode) | read | When the document direction is `rtl`, elements with the `icon-directional` class receive a CSS transform that mirrors them horizontally so directional icons like back arrows and navigation chevrons point in the correct RTL direction | The `icon-directional` class is missing from the stylesheet or the CSS transform is not applied — directional icons render in their original LTR orientation in RTL mode, pointing in the wrong direction and confusing the user's navigation expectations |

## Behavioral Flow

1. **[System]** the locale detection chain (described in
    system-detects-locale) resolves the active locale to a supported
    language and determines whether the resolved locale is a
    right-to-left language (Arabic, Hebrew, Farsi, or Urdu)

2. **[System]** on web and desktop, when the resolved locale is an RTL
    language, the application sets `dir="rtl"` on the `<html>` element
    — when the resolved locale is an LTR language, it sets `dir="ltr"`

3. **[System]** the `DirectionProvider` from `@repo/ui` wraps the React
    tree and updates its context value to reflect the current direction,
    communicating the direction to all Shadcn components built on Base
    UI primitives

4. **[System]** all layout throughout the application uses Tailwind CSS
    logical properties exclusively — `ps-` and `pe-` for inline padding,
    `ms-` and `me-` for inline margin, `text-start` and `text-end` for
    text alignment, `inset-s-` and `inset-e-` for positioning

5. **[System]** physical directional utilities (`ml-`, `mr-`, `pl-`,
    `pr-`, `left-`, `right-`, `text-left`, `text-right`, `rounded-l-`,
    `rounded-r-`) are never used in the codebase — this is enforced as
    a hard rule to prevent layout bugs in RTL mode

6. **[System]** CSS logical properties derive their physical direction
    from the `dir` attribute, so when direction changes, every layout
    automatically mirrors: the sidebar moves to the right side, text
    aligns to the right, and inline spacing flips correctly

7. **[System]** dropdowns, popovers, dialogs, tooltips, and other
    overlay components receive the direction from the
    `DirectionProvider` context and position themselves correctly in
    RTL mode without component-level overrides

8. **[System]** elements with the `icon-directional` utility class
    receive a horizontal mirror transform in RTL mode, flipping
    directional icons like arrows, chevrons, and navigation indicators
    to point in the correct direction

9. **[System]** symmetrical icons (settings gear, search magnifier,
    close button) do not use the `icon-directional` class and remain
    unchanged regardless of the active direction

10. **[User]** switches language through the language switcher and the
    direction toggles live without a page reload on web — the `dir`
    attribute update propagates through CSS instantly and all logical
    properties recalculate, flipping the layout in place

11. **[System]** on mobile, when the locale is an RTL language,
    `I18nManager.forceRTL(true)` is called during initialization
    (driven by `expo-localization`), flipping `flexDirection`,
    `textAlign`, and all directional styles at the React Native
    framework level

12. **[System]** on mobile, layout is authored in start/end terms and
    never left/right, so the mobile application mirrors correctly
    without RTL-specific code paths, using the same directional
    principles as the web and desktop implementations

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| direction_unknown | ltr_active | The locale detection chain resolves the active locale to a left-to-right language such as English and the application sets `dir="ltr"` on the document element or maintains the default LTR layout on mobile | The resolved locale is not in the list of RTL languages (Arabic, Hebrew, Farsi, Urdu) and the application initializes with left-to-right as the default direction |
| direction_unknown | rtl_active | The locale detection chain resolves the active locale to a right-to-left language such as Arabic and the application sets `dir="rtl"` on the document element or calls `I18nManager.forceRTL(true)` on mobile | The resolved locale is in the list of RTL languages (Arabic, Hebrew, Farsi, Urdu) and the direction switch is applied before the first user-visible render |
| ltr_active | rtl_active | The user switches language through the language switcher to an RTL language, triggering the `dir` attribute to change from `ltr` to `rtl` on the document element, causing all CSS logical properties to recalculate | The new locale is an RTL language and the `dir` attribute update propagates to the DOM, triggering CSS recalculation across all styled elements |
| rtl_active | ltr_active | The user switches language through the language switcher to an LTR language, triggering the `dir` attribute to change from `rtl` to `ltr` on the document element, causing all CSS logical properties to recalculate | The new locale is an LTR language and the `dir` attribute update propagates to the DOM, triggering CSS recalculation across all styled elements |

## Business Rules

- **Rule logical-properties-only:** IF any layout styling is applied in
    the codebase THEN it uses Tailwind CSS logical properties (`ps-`,
    `pe-`, `ms-`, `me-`, `text-start`, `text-end`, `inset-s-`,
    `inset-e-`, `rounded-s-`, `rounded-e-`) and never physical
    directional utilities — the count of physical directional utility
    classes (`ml-`, `mr-`, `pl-`, `pr-`, `left-`, `right-`,
    `text-left`, `text-right`, `rounded-l-`, `rounded-r-`) in the
    codebase equals 0
- **Rule dir-attribute-reflects-locale:** IF the resolved locale is an
    RTL language (Arabic, Hebrew, Farsi, or Urdu) THEN the `dir`
    attribute on the `<html>` element equals `rtl` — the `dir`
    attribute value for RTL locales always equals `rtl`
- **Rule direction-provider-wraps-tree:** IF the React application
    renders on web or desktop THEN the `DirectionProvider` from
    `@repo/ui` wraps the entire React tree and provides the current
    direction to all consuming Shadcn components — the count of
    Shadcn overlay components without access to direction context
    equals 0
- **Rule no-page-reload-on-switch:** IF the user switches language
    through the language switcher on web THEN the direction change
    applies instantly without a page reload — the count of page
    navigations triggered by a language switch equals 0
- **Rule directional-icons-mirror:** IF an icon carries directional
    meaning (arrows, chevrons, navigation indicators) and the layout
    is RTL THEN the icon element has the `icon-directional` class and
    receives a horizontal mirror transform — the count of directional
    icons without the `icon-directional` class equals 0
- **Rule symmetrical-icons-unchanged:** IF an icon is symmetrical
    (settings gear, search magnifier, close button) THEN it does not
    use the `icon-directional` class regardless of direction — the
    count of symmetrical icons with the `icon-directional` class
    equals 0
- **Rule mobile-force-rtl-on-init:** IF the mobile device locale is an
    RTL language THEN `I18nManager.forceRTL(true)` is called during
    initialization before the first render — the `I18nManager` RTL
    state after initialization equals `true` for RTL locales
- **Rule no-rtl-specific-code-paths:** IF layout is authored for mobile
    THEN it uses start/end terms and never left/right, requiring zero
    RTL-specific conditional branches — the count of RTL-specific
    layout conditionals in mobile code equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| System (the platform runtime that evaluates the resolved locale, sets the `dir` attribute, initializes the `DirectionProvider`, applies CSS logical property calculations, calls `I18nManager.forceRTL()` on mobile, and manages the `icon-directional` transform for directional icons) | Set the `dir` attribute on the `<html>` element based on the resolved locale, update the `DirectionProvider` context value when the locale changes, apply CSS logical property recalculations when the `dir` attribute changes, call `I18nManager.forceRTL()` during mobile initialization, apply the `icon-directional` horizontal mirror transform to directional icons in RTL mode | Cannot add new RTL languages to the supported list at runtime without a code deployment, cannot override the direction derived from the resolved locale with a separate user direction toggle, cannot apply physical directional CSS properties as fallbacks when logical properties fail | The system has visibility into the resolved locale value, the current `dir` attribute state, the `DirectionProvider` context value, and the `I18nManager` RTL state on mobile, but has no visibility into whether the user perceives the layout as correctly mirrored |
| User (the person using the application who triggers direction changes by switching language through the language switcher and interacts with the mirrored layout when using an RTL language like Arabic) | Switch language through the language switcher to trigger a direction change between LTR and RTL, interact with the mirrored layout including sidebar navigation on the right side and right-aligned text in RTL mode, view correctly mirrored directional icons in RTL mode | Cannot toggle the layout direction independently from the language selection, cannot force LTR layout while using an RTL language, cannot override the automatic direction switch that is derived from the resolved locale | The user sees the layout in the direction matching their active locale, sees directional icons mirrored in RTL mode, sees symmetrical icons unchanged regardless of direction, and observes the live direction flip without a page reload when switching language on web |

## Constraints

- The `dir` attribute update on the `<html>` element propagates to all
    CSS logical properties within 16 ms (one animation frame at 60fps)
    — the count of milliseconds from attribute change to visual layout
    flip equals 16 or fewer.
- The `DirectionProvider` context update reaches all consuming Shadcn
    components within 1 React render cycle after the `dir` attribute
    changes — the count of render cycles between direction change and
    component re-render equals 1 or fewer.
- The count of physical directional Tailwind utility classes (`ml-`,
    `mr-`, `pl-`, `pr-`, `left-`, `right-`, `text-left`, `text-right`,
    `rounded-l-`, `rounded-r-`) in the codebase source files equals 0.
- The `I18nManager.forceRTL()` call on mobile completes before the
    first React Native render cycle — the count of renders that occur
    before the RTL state is applied equals 0.
- The `icon-directional` transform applies to directional icons within
    16 ms of the direction change — the count of milliseconds from
    `dir` attribute change to icon mirror transform equals 16 or fewer.
- All overlay components (dropdowns, popovers, dialogs, tooltips)
    position correctly in RTL mode with zero manual position overrides
    — the count of component-level RTL position overrides equals 0.

## Acceptance Criteria

- [ ] When the resolved locale is Arabic the `dir` attribute on the `<html>` element equals `rtl` — the count of RTL locales where the `dir` attribute does not equal `rtl` equals 0
- [ ] When the resolved locale is English the `dir` attribute on the `<html>` element equals `ltr` — the count of LTR locales where the `dir` attribute does not equal `ltr` equals 0
- [ ] The `DirectionProvider` from `@repo/ui` wraps the React tree and provides direction context to Shadcn components — the count of application renders without the `DirectionProvider` in the component tree equals 0
- [ ] The codebase contains zero physical directional Tailwind utility classes (`ml-`, `mr-`, `pl-`, `pr-`, `text-left`, `text-right`) — the count of physical directional utilities equals 0
- [ ] All layout uses logical Tailwind properties (`ps-`, `pe-`, `ms-`, `me-`, `text-start`, `text-end`) — the count of styled elements using logical properties is non-empty
- [ ] The sidebar moves to the right side of the screen when the direction is RTL — the count of RTL renders where the sidebar is not positioned at inline-end equals 0
- [ ] Dropdowns and popovers position correctly in RTL mode without component-level overrides — the count of manual RTL position overrides equals 0
- [ ] Directional icons (arrows, chevrons) receive a horizontal mirror transform in RTL mode via the `icon-directional` class — the transform is present on directional icons in RTL
- [ ] Symmetrical icons (settings gear, search magnifier) remain unchanged in RTL mode — the `icon-directional` class is absent on symmetrical icons
- [ ] Switching language on web toggles the direction live without a page reload — the count of page navigations during a language switch equals 0
- [ ] On mobile, `I18nManager.forceRTL(true)` is called during initialization when the locale is an RTL language — the `I18nManager` RTL state equals `true`
- [ ] On mobile, layout authored in start/end terms mirrors correctly without RTL-specific code paths — the count of RTL-specific layout conditionals equals 0
- [ ] The direction change from LTR to RTL completes visual layout flip within 16 ms of the `dir` attribute update — the flip duration equals 16 ms or fewer

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user switches rapidly between an LTR and RTL language multiple times in quick succession using the language switcher on web | Each `dir` attribute change triggers a CSS recalculation and the layout settles into the final direction matching the last selected locale without intermediate visual glitches or layout corruption | The final `dir` attribute value matches the last selected locale's direction and the count of layout corruption artifacts equals 0 |
| A Shadcn dropdown is open when the user switches from LTR to RTL through the language switcher | The `DirectionProvider` updates its context and the open dropdown repositions to the correct RTL-aligned position or closes and reopens at the correct position on the next trigger | The dropdown renders at the correct inline-end position after the direction change and the count of dropdowns positioned on the wrong side equals 0 |
| A third-party component embedded in the application does not use CSS logical properties and uses physical `left`/`right` positioning | The third-party component does not mirror in RTL mode because it uses physical properties, while all application-authored components mirror correctly via logical properties | The third-party component remains in its original LTR position and the count of application-authored components using physical properties equals 0 |
| The `DirectionProvider` is accidentally removed from the component tree during a code refactor and Shadcn overlay components lose direction context | Shadcn components fall back to their default LTR positioning regardless of the active `dir` attribute, causing overlays to appear misaligned in RTL mode until the provider is restored | The count of correctly positioned overlays in RTL mode without the `DirectionProvider` equals 0, indicating the provider is a required dependency |
| The mobile application starts with an RTL locale but `I18nManager.forceRTL()` is called after the first render cycle has already committed to screen | The first frame renders in LTR direction and subsequent frames render in RTL after the `I18nManager` state takes effect, causing a visible direction flash on the first launch | The count of LTR frames before RTL takes effect equals 1 or more, confirming that `forceRTL` must be called before the first render to avoid the flash |
| A layout component uses `translate-x` for animation which has no logical CSS equivalent and needs RTL-specific handling | The component uses the `rtl:` Tailwind variant prefix to apply the opposite `translate-x` value in RTL mode, because `translate-x` is a physical property with no logical alternative | The `rtl:` variant is present on the element and the translate direction is reversed in RTL mode compared to LTR mode |

## Failure Modes

- **The `dir` attribute fails to update on the `<html>` element after a locale change to an RTL language**
    - **What happens:** The user switches to an RTL language through the language switcher, but the JavaScript code responsible for setting `dir="rtl"` on the `<html>` element encounters an error, leaving the attribute at its previous `ltr` value while the translation text updates to Arabic.
    - **Source:** A runtime error in the direction update logic, a race condition between the locale change event and the DOM attribute setter, or a browser extension that blocks DOM modifications on the `<html>` element for security reasons.
    - **Consequence:** The UI displays Arabic text with left-to-right layout direction, causing text alignment, sidebar position, and inline spacing to be incorrect, making the interface unusable for RTL users.
    - **Recovery:** The application detects the mismatch between the resolved locale direction and the current `dir` attribute value on the next render cycle, logs the discrepancy, and retries setting the `dir` attribute to correct the layout direction.

- **The `DirectionProvider` context value becomes stale after a rapid sequence of locale changes**
    - **What happens:** The user switches between LTR and RTL locales in rapid succession and the `DirectionProvider` context update is debounced or batched by React, causing Shadcn overlay components to receive a stale direction value that does not match the current `dir` attribute.
    - **Source:** React's concurrent rendering batches multiple state updates and the `DirectionProvider` value lags behind the `dir` attribute change by one or more render cycles during rapid switching.
    - **Consequence:** Overlay components (dropdowns, popovers, dialogs) position themselves according to the stale direction while the rest of the layout has already flipped, causing visual misalignment until the context update catches up.
    - **Recovery:** The `DirectionProvider` reconciles its context value with the current `dir` attribute on the next stable render cycle, and any open overlays reposition themselves correctly — the application logs the context staleness duration for monitoring.

- **`I18nManager.forceRTL()` fails to execute before the first render on mobile causing a direction flash**
    - **What happens:** The mobile application starts with an RTL locale but the `I18nManager.forceRTL(true)` call executes after the first React Native render cycle has already committed a frame to the screen, causing the user to see a brief flash of LTR layout before the direction corrects.
    - **Source:** The `expo-localization` locale read is asynchronous and completes after the React Native root component has rendered its first frame, or the `forceRTL` call is placed in a lifecycle method that runs after the initial render.
    - **Consequence:** The user sees the layout in LTR direction for one or more frames before it flips to RTL, creating a visual flash that degrades the perceived quality of the application startup experience.
    - **Recovery:** The application degrades to showing the brief LTR flash and corrects the direction on the subsequent render cycle — the developer addresses this by moving the `forceRTL` call to the earliest possible initialization point before the React tree mounts, and logs the flash occurrence for monitoring.

## Declared Omissions

- This specification does not define the locale detection chain that determines which language is active — that behavior is covered in the system-detects-locale specification and this specification consumes the resolved locale as an input signal
- This specification does not cover the user-initiated language switching flow or the persistence of language preferences — that behavior is defined in the user-changes-language specification which triggers the direction change as a side effect
- This specification does not define the specific Shadcn component APIs or Base UI primitive behaviors for overlay positioning — it defines the direction context delivery mechanism that those components consume for correct RTL positioning
- This specification does not address bidirectional text rendering within a single text block (mixing LTR and RTL content in one paragraph) — that is handled by the Unicode Bidirectional Algorithm built into the browser and React Native rendering engines
- This specification does not cover the creation or maintenance of the `icon-directional` utility class implementation — it defines the behavioral expectation that directional icons mirror in RTL mode using this class

## Related Specifications

- [system-detects-locale](system-detects-locale.md) — defines the
    locale detection chain across all platforms that provides the
    resolved locale value consumed by this specification to determine
    whether the layout direction is LTR or RTL
- [user-changes-language](user-changes-language.md) — defines the
    user-initiated language switching flow that triggers the direction
    change defined in this specification as a side effect of selecting
    an RTL or LTR language
- [user-installs-browser-extension](user-installs-browser-extension.md)
    — defines the browser extension installation flow including the
    popup UI initialization that inherits the direction context from
    the extension's locale detection for correct RTL rendering in the
    popup
- [extension-receives-an-update](extension-receives-an-update.md) —
    defines the extension update flow where the service worker restarts
    and the popup re-initializes its direction context based on the
    stored locale preference after the update is applied

---
id: SPEC-2026-077
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Changes Theme on Mobile

## Intent

This spec defines how an authenticated user navigates to the settings
screen within the Expo mobile app and changes their theme preference
using a localized theme selector offering three options: Light, Dark,
and System. When the user taps a different option, the Zustand
theme-store updates immediately, UniWind's native theming system
applies the new color scheme to all components styled with `dark:`
variants, and the `expo-status-bar` component adjusts the status bar
icon color to maintain contrast with the active theme. The selected
preference is persisted to `react-native-mmkv` so that subsequent
launches restore the correct theme before the first frame renders,
preventing any flash of the wrong color scheme behind the splash
screen. When the System option is active, the app reads the device
appearance setting and listens for real-time OS changes, updating the
UI immediately whenever the device switches between light and dark
mode without requiring any interaction within the app.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Zustand theme-store (client state manager that holds the selected theme preference and broadcasts changes to all subscribed components) | read/write | When the user taps a theme option in the selector control on the settings screen and the store updates with the new preference value, and on app initialization when the store reads the persisted value from MMKV | The store falls back to the default System preference and resolves the theme from the device OS appearance setting, and the user loses any previously persisted explicit Light or Dark selection until MMKV becomes readable again |
| UniWind native theming system (applies color scheme changes to all React Native components styled with `dark:` variant utilities based on the active theme) | write | When the Zustand theme-store value changes after the user taps a theme option, UniWind receives the updated color scheme and triggers a re-render of all components that use `dark:` prefixed style variants | UniWind does not receive the color scheme update and the UI remains in the previous visual theme — the user sees the theme selector highlighting the new option while the rendered components retain the old color palette |
| react-native-mmkv (synchronous native key-value store that persists the theme preference for restoration on subsequent app launches before the first frame) | read/write | When the theme-store persists the selected preference after a user tap, and during app initialization when the store reads the stored preference to hydrate the theme before the splash screen hides | The theme-store cannot read or write the persisted preference and falls back to the System default on every launch — the user loses their explicit Light or Dark selection and the app resolves the theme from the device OS appearance setting each time |
| expo-status-bar (component that styles the system status bar icon color as light or dark to maintain visual contrast with the active theme background) | write | When the theme-store value changes and the active color scheme is resolved, the status bar component updates the icon color — light icons for dark backgrounds and dark icons for light backgrounds | The status bar retains its previous icon color and the icons do not contrast correctly with the new theme background — the runtime logs the status bar update failure and the user sees mismatched status bar icons until the next app restart |
| OS appearance listener (reactive system that detects real-time device appearance changes and propagates them to the app when System mode is active) | read | When the System theme option is active and the user changes their device appearance setting from light to dark or vice versa while the app is in the foreground | The app does not detect OS appearance changes while System is active and the UI retains the theme that was resolved at the time of selection — the user must reopen the settings screen to trigger a manual re-read of the device appearance |
| @repo/i18n (localization infrastructure that supplies translated labels for the theme selector options and settings screen text elements) | read | When the settings screen renders the theme selector control with localized labels for Light, Dark, and System options and any accompanying descriptive text | The UI degrades to displaying raw translation keys instead of localized strings for the theme selector labels, and the user sees untranslated identifiers until the i18n namespace loads on the next navigation event |

## Behavioral Flow

1. **[User]** navigates to the settings screen within the Expo mobile
    app — the screen presents a localized theme selector with three
    options: Light, Dark, and System, and the currently active option
    is visually highlighted to indicate the selected preference

2. **[App]** reads the current value from the Zustand theme-store and
    visually highlights the active option in the theme selector control
    so the user can see which theme preference is currently selected
    before making any changes

3. **[User]** taps a different theme option in the selector control —
    the tap triggers an immediate update to the Zustand theme-store
    with the new preference value (Light, Dark, or System)

4. **[App]** the Zustand theme-store updates with the new preference
    value and UniWind's native theming system receives the updated
    color scheme — all components styled with `dark:` variant utilities
    re-render with the new color palette immediately

5. **[App]** the `expo-status-bar` component adjusts the status bar
    icon color to maintain contrast with the new theme — light icons
    are displayed on dark backgrounds and dark icons are displayed on
    light backgrounds so the system chrome stays consistent

6. **[App]** the selected preference — Light, Dark, or System — is
    persisted to `react-native-mmkv` by the Zustand theme-store so
    that subsequent app launches restore the correct theme before the
    first frame renders behind the splash screen

7. **[App]** on subsequent app launches, the theme-store reads the
    stored preference from MMKV during state hydration before the
    splash screen is hidden — the correct color scheme is applied
    before the first visible frame, preventing any flash of the wrong
    theme during the launch sequence

8. **[User]** selects the System option — the app reads the device
    current appearance setting via the OS appearance API to determine
    whether to apply light or dark styling to the UI

9. **[App]** when System is active, the app registers a reactive
    appearance listener that monitors the device OS appearance
    preference for real-time changes — this listener fires whenever
    the device switches between light and dark mode

10. **[OS]** the user changes the device appearance setting from light
    to dark or vice versa while the app is open — the reactive
    appearance listener detects the change and the Zustand theme-store
    updates the active color scheme immediately

11. **[App]** UniWind re-renders all components with the updated
    color scheme matching the new OS appearance and the status bar
    icon color adjusts to maintain contrast — no interaction within
    the app is required because the listener propagates the OS change
    automatically through the theme-store

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| settings_screen_loading | theme_selector_ready | The settings screen mounts and the Zustand theme-store provides the current preference value to the theme selector control for visual highlighting | The screen component mounted and the theme-store returned a valid preference value of Light, Dark, or System from memory or MMKV hydration |
| theme_selector_ready | theme_applying | The user taps a different theme option in the selector control and the Zustand theme-store updates with the new preference value | The tapped option differs from the currently active preference value in the theme-store |
| theme_applying | theme_selector_ready | UniWind applies the new color scheme, the status bar icon adjusts, and the MMKV persistence write completes for the selected preference | The rendered color scheme matches the selected preference, the status bar icon color is consistent, and MMKV contains the updated preference string |
| system_theme_active | theme_applying | The OS appearance setting changes while the System option is the active preference in the theme-store and the reactive appearance listener detects the change | The current theme-store preference equals System and the reactive appearance listener detected a different value from the device appearance API |
| theme_applying | system_theme_active | UniWind finishes applying the resolved OS appearance and the reactive appearance listener remains registered for future OS appearance changes | The theme-store preference equals System and the rendered color scheme matches the current device OS appearance setting |
| theme_selector_ready | theme_selector_ready | The user taps the already-active theme option in the selector control — no state change occurs because the tapped option matches the current preference | The tapped option equals the currently active preference so no theme-store update or UniWind re-render is triggered |

## Business Rules

- **Rule theme-store-updates-immediately:** IF the user taps a theme
    option in the selector control THEN the Zustand theme-store updates
    with the new preference value within the same event loop tick — the
    count of render frames showing the previous theme after the tap
    equals 0
- **Rule uniwind-rerenders-on-store-change:** IF the Zustand
    theme-store value changes THEN UniWind applies the new color
    scheme to all components styled with `dark:` variant utilities —
    the count of components still rendering the previous color palette
    after the re-render cycle completes equals 0
- **Rule status-bar-icon-matches-theme:** IF the active theme resolves
    to dark styling THEN the `expo-status-bar` displays light-colored
    icons, and IF the active theme resolves to light styling THEN the
    status bar displays dark-colored icons — the count of status bar
    icon color mismatches with the active theme background equals 0
- **Rule preference-persisted-to-mmkv:** IF the user taps any theme
    option THEN the Zustand theme-store writes the preference string
    to `react-native-mmkv` — the count of MMKV writes per selection
    equals 1 and the stored value matches the selected option exactly
- **Rule system-reads-device-appearance:** IF the user selects the
    System option THEN the app reads the device current OS appearance
    setting to determine the active color scheme — the resolved theme
    matches the device OS appearance (light or dark) at the time of
    selection
- **Rule system-listens-for-os-changes:** IF the active preference
    equals System THEN the app registers a reactive appearance listener
    that fires when the device OS appearance changes — the count of
    registered listeners while System is active equals 1 and the
    listener is removed when the user switches to Light or Dark
- **Rule mmkv-restores-before-first-frame:** IF a theme preference
    is stored in MMKV from a previous session THEN the theme-store
    reads and applies it during state hydration before the splash
    screen hides — the count of frames rendered with the wrong theme
    before MMKV hydration completes equals 0

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated User | Navigate to the settings screen, view the theme selector control with all three options (Light, Dark, and System), tap any theme option and have the selection persisted to MMKV and applied to the UI immediately | No theme-related actions are denied to an authenticated user — theme preference is a personal device-level setting that does not require elevated permissions or organization membership | The settings screen is fully visible with the theme selector displaying Light, Dark, and System options and the currently active selection visually highlighted |
| Unauthenticated User | No actions are permitted — the Expo Router route guard redirects the user to the sign-in screen before the settings screen renders and no theme controls are displayed on the sign-in screen | Cannot view or interact with the settings screen, the theme selector control, or any settings element — the redirect to sign-in occurs before any settings components mount in the view hierarchy | The settings screen is not rendered and the redirect to sign-in occurs before any settings components mount, so the theme selector control is never visible to an unauthenticated user |

## Constraints

- The Zustand theme-store update and UniWind color scheme
    application complete within 16 ms of the user tapping a theme
    option — the count of intermediate render frames showing the
    previous theme after the tap equals 0.
- The theme preference stored in MMKV is one of exactly three string
    values: `light`, `dark`, or `system` — the count of invalid or
    unrecognized values written to MMKV by the theme-store equals 0.
- On subsequent app launches the theme-store reads MMKV and applies
    the correct theme before the splash screen hides — the count of
    visible theme flashes (wrong theme rendered then corrected) during
    the launch sequence equals 0.
- When the System preference is active exactly 1 reactive appearance
    listener is registered for device OS appearance changes — the
    count of duplicate listeners equals 0 and the listener is removed
    when the preference changes to Light or Dark.
- The theme selector labels for Light, Dark, and System are rendered
    via @repo/i18n translation keys — the count of hardcoded English
    strings in the theme selector component equals 0.
- The reactive OS appearance listener detects and propagates device
    theme changes within 100 ms of the OS broadcasting the appearance
    change event — the UI update completes within 100 ms of the OS
    event firing.

## Acceptance Criteria

- [ ] The settings screen renders a theme selector with exactly 3 options labeled Light, Dark, and System — the count of theme options in the selector control equals 3
- [ ] The currently active theme preference is visually highlighted in the selector control — the count of highlighted options equals 1 and the highlighted option matches the Zustand theme-store value
- [ ] Tapping the Dark option triggers UniWind to apply dark color scheme to all components within 16 ms — the count of components still showing the light palette after the re-render equals 0
- [ ] Tapping the Light option triggers UniWind to apply light color scheme to all components within 16 ms — the count of components still showing the dark palette after the re-render equals 0
- [ ] Tapping the System option resolves the theme from the device OS appearance setting — the active color scheme matches the device appearance and the count of mismatches between OS appearance and rendered theme equals 0
- [ ] The selected preference is persisted to MMKV within 16 ms of the tap — the MMKV stored value is non-empty and equals the string `light`, `dark`, or `system` matching the tapped option
- [ ] On app relaunch the theme is applied from MMKV before the splash screen hides — the count of visible theme flashes during the launch sequence equals 0 and the rendered theme matches the stored MMKV value
- [ ] The expo-status-bar displays light icons when the dark theme is active and dark icons when the light theme is active — the count of status bar icon color mismatches equals 0
- [ ] When System is active and the device OS switches from light to dark, the UI updates to dark without user interaction — the count of user-initiated actions required to reflect the OS change equals 0
- [ ] When System is active and the device OS switches from dark to light, the UI updates to light without user interaction — the count of user-initiated actions required to reflect the OS change equals 0
- [ ] Exactly 1 reactive appearance listener is registered when System is active — the count of registered OS appearance listeners equals 1 and the count of duplicate listeners equals 0
- [ ] An unauthenticated user attempting to access the settings screen is redirected to sign-in — the rendered screen path equals the sign-in route and the count of rendered settings components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user taps the theme option that is already active in the selector control | No state change occurs — the theme-store value remains unchanged, UniWind does not re-render, and MMKV is not written to because the tapped option matches the current preference | The count of UniWind re-render cycles equals 0 and the MMKV stored value is unchanged after tapping the already-active option |
| MMKV storage is unavailable because the native storage file is corrupted or the filesystem denied read access during the write | The theme-store falls back to holding the preference in memory for the current session — the theme applies correctly during the session but on the next launch the store initializes with the System default | The theme renders correctly during the session, and on the next launch the default System preference is active instead of the explicitly selected option |
| The user switches the device OS appearance while the app is open and the active preference is Light or Dark, not System | The reactive appearance listener does not fire because it is only registered when System is active — the UI retains the explicitly selected Light or Dark theme regardless of the OS appearance change | The rendered color scheme remains unchanged after the OS appearance switch and the count of theme-store updates from the listener equals 0 |
| The user opens the app for the first time with no MMKV entry for the theme preference stored from a previous session | The theme-store initializes with the System default and resolves the theme from the device OS appearance setting — the selector control highlights System as the active option on the settings screen | The MMKV key for theme is absent before first interaction, the selector shows System as highlighted, and the rendered color scheme matches the device OS appearance |
| The user rapidly taps between Light, Dark, and System options within 100 ms intervals between each tap | Each tap updates the theme-store and triggers UniWind sequentially — the final rendered color scheme and MMKV stored value match the last option the user tapped in the sequence | The rendered color scheme matches the last-tapped theme and the MMKV stored value equals the last-tapped preference string after the rapid tap sequence settles |
| The device OS broadcasts an appearance change event while the app is in the background and System is the active preference | The reactive appearance listener processes the event when the app returns to the foreground and UniWind applies the updated color scheme — the UI reflects the new OS appearance when the user resumes the app | The rendered color scheme matches the current device OS appearance after the app returns to the foreground, and the count of stale theme frames equals 0 |

## Failure Modes

- **MMKV write failure prevents theme preference persistence across app launches**
    - **What happens:** The Zustand theme-store attempts to write the
        selected theme preference to MMKV but the write operation fails
        because the native storage file is corrupted, the filesystem
        denied write access, or the storage directory was cleared by
        the operating system storage management process.
    - **Source:** A previous force-kill interrupted an MMKV write
        operation and corrupted the storage file, or the OS reclaimed
        app storage due to low disk space, or a device migration
        transferred the app binary without its associated data
        directory containing the MMKV files.
    - **Consequence:** The theme applies correctly for the current
        session because the Zustand store holds the preference in
        memory, but on the next app launch the theme-store cannot read
        the persisted preference and falls back to the System default
        which resolves from the device OS appearance setting.
    - **Recovery:** The theme-store catches the MMKV write error and
        logs a warning with the storage file path and error details —
        the theme selection remains functional in memory for the
        current session, and the next user preference change retries
        writing to MMKV to re-create the storage file.

- **Reactive OS appearance listener fails to detect device theme change while System is active**
    - **What happens:** The reactive appearance listener registered by
        the app does not fire when the user changes the device OS
        appearance setting, leaving the UI stuck on the previously
        resolved theme while the System preference is active and the
        OS has transitioned to a different color scheme.
    - **Source:** A platform-level API limitation on certain Android
        versions that do not broadcast appearance change events to
        background-aware listeners, or the listener reference was
        garbage-collected because it was not retained in the component
        lifecycle, or the React Native bridge dropped the native event
        during a high-priority UI thread operation.
    - **Consequence:** The app content remains in the previous light
        or dark state while the OS has switched to the opposite scheme,
        creating a visual inconsistency that the user notices when
        comparing the app to other native applications on the device.
    - **Recovery:** The app falls back to re-reading the device OS
        appearance setting on the next navigation event or screen focus
        change and re-applies the correct theme through the theme-store
        — the runtime logs the missed listener event and the user can
        also manually select Light or Dark to override the stale System
        resolution.

- **UniWind fails to apply color scheme change after theme-store update**
    - **What happens:** The Zustand theme-store updates with the new
        preference value but UniWind does not receive or process
        the color scheme change, leaving the rendered components
        displaying the previous color palette while the theme selector
        control shows the newly selected option as highlighted.
    - **Source:** A version mismatch between UniWind and the React
        Native runtime that causes the color scheme propagation to
        fail silently, or a race condition in the UniWind context
        provider that drops the update during a concurrent rendering
        cycle, or a corrupted style cache that prevents UniWind
        from resolving the updated `dark:` variant styles.
    - **Consequence:** The user sees the theme selector highlighting
        the new option while the rest of the UI retains the old color
        palette — the visual mismatch persists until the user navigates
        away from the settings screen and returns, triggering a fresh
        component mount that re-reads the theme-store value.
    - **Recovery:** The theme-store detects the mismatch by comparing
        the store value with the UniWind reported color scheme and
        retries the color scheme propagation after a 100 ms delay —
        the runtime logs the UniWind update failure and if the retry
        also fails the app alerts the user to restart the application
        to restore visual consistency.

## Declared Omissions

- This specification does not define the visual design, color palette,
    or UniWind theme tokens used by the light and dark themes —
    those are defined in the UniWind configuration and the design
    token foundation spec covering color variables and semantic tokens.
- This specification does not cover per-organization theme branding
    or custom theme colors that organizations can configure — that
    behavior requires a separate spec covering organization-level
    appearance customization with custom style variable overrides.
- This specification does not address contrast or accessibility
    compliance of the light and dark color schemes themselves — WCAG
    contrast ratios and accessible color selection are covered by the
    design system foundation spec defining the color token hierarchy.
- This specification does not cover the web-based theme switching
    mechanism that uses `.dark` class mutation on the `<html>` element
    and Tailwind CSS — the web flow is defined in the user-changes-theme
    behavioral specification and uses a different rendering approach.
- This specification does not cover server-side theme preference
    syncing across devices — the theme preference is stored exclusively
    in MMKV on the local device and is not persisted to any server-side
    user profile record or cross-device synchronization endpoint.

## Related Specifications

- [user-changes-theme](user-changes-theme.md) — Defines the web-based
    theme switching mechanism using `.dark` class mutation on the
    `<html>` element and Tailwind CSS that this mobile specification
    mirrors in behavior but replaces with UniWind native theming
- [user-launches-mobile-app](user-launches-mobile-app.md) — Defines
    the mobile app launch sequence including MMKV state hydration that
    restores the theme preference before the splash screen hides, which
    this specification references for persistence across app launches
- [user-navigates-mobile-app](user-navigates-mobile-app.md) — Defines
    the mobile navigation structure including the settings screen where
    the theme selector control described in this specification is
    rendered as part of the appearance settings section
- [session-lifecycle](session-lifecycle.md) — Defines the
    authentication session management and route guard behavior that
    determines whether the user can access the mobile settings screen
    or is redirected to the sign-in screen before the screen renders
- [shared-i18n](../foundation/shared-i18n.md) — Provides the
    internationalization infrastructure and translation loading
    mechanism that supplies localized labels for the Light, Dark, and
    System options rendered in the mobile theme selector control

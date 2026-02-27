---
id: SPEC-2026-048
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: draft
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Changes Theme

## Intent

This spec defines how an authenticated user navigates to the
appearance settings page at `/app/settings/appearance`, selects a
theme preference from a segmented control offering Light, Dark, and
System options, and has the chosen theme applied immediately across
the entire UI without a page reload. The Zustand theme-store updates
on selection, the `applyTheme()` function resolves the effective
visual theme — direct mapping for Light and Dark, or a
`prefers-color-scheme` media query read for System — and sets or
removes the `.dark` class on the `<html>` element. Tailwind CSS
responds to this class to re-render every component using `dark:`
prefixed utilities. The selected preference is persisted to
localStorage so that subsequent visits restore the theme before first
paint, preventing a flash of the wrong color scheme. When System is
active, a `matchMedia` listener tracks real-time OS theme changes and
updates the UI instantly. On the Tauri desktop app, the webview
content follows the same mechanism, but the OS-rendered native title
bar always follows the OS theme, creating a visual mismatch when the
user explicitly picks Light or Dark that differs from the OS setting.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| Zustand theme-store (client state manager for selected preference) | read/write | When the user selects a theme option in the segmented control and the store updates the preference value, and on app initialization when the store reads the persisted preference from localStorage | The store falls back to the default System preference so the app resolves the theme from the OS `prefers-color-scheme` media query, and the user loses any previously persisted explicit Light or Dark selection |
| localStorage (browser persistence layer for theme preference) | read/write | When the theme-store persists the selected preference after a user selection, and during app initialization when the store reads the stored preference to restore the theme before first paint | The theme-store cannot read or write the persisted preference and falls back to the System default on every page load, losing the user's explicit Light or Dark selection until localStorage becomes available again |
| `applyTheme()` function with `.dark` class mutation on `<html>` element | write | When the theme-store value changes and the function resolves the effective visual theme by either mapping Light or Dark directly or reading the OS media query for System, then sets or removes the `.dark` class | The `.dark` class on the `<html>` element is not updated and the UI remains in its previous visual theme state, creating a mismatch between the selected preference in the segmented control and the rendered color scheme |
| `prefers-color-scheme` media query listener via `window.matchMedia` | read | When the System theme option is active and the OS theme changes in real time, the listener fires and triggers `applyTheme()` to re-resolve the effective theme and update the `.dark` class on the `<html>` element | The app does not detect OS theme changes while System is active and the UI retains the theme that was resolved at the time of selection, requiring a manual page reload to pick up the new OS preference |
| @repo/i18n (localization infrastructure for UI labels) | read | When the appearance settings page renders the segmented control labels for Light, Dark, and System options and any accompanying descriptive text on the settings page | The UI degrades to displaying raw translation keys instead of localized strings for the theme selector labels, and the user sees untranslated identifiers until the i18n namespace loads |

## Behavioral Flow

1. **[User]** navigates to `/app/settings/appearance` — the page
    presents a theme selector rendered as a segmented control or
    radio group with three localized options: Light, Dark, and System

2. **[Client]** reads the current value from the Zustand theme-store
    and visually highlights the active option in the segmented control
    so the user can see which theme preference is currently selected

3. **[User]** selects a different theme option by clicking one of the
    three choices in the segmented control — the selection triggers
    an immediate update to the Zustand theme-store

4. **[Client]** the Zustand theme-store updates with the new
    preference value and calls the `applyTheme()` function to resolve
    the effective visual theme that will be applied to the UI

5. **[Client]** the `applyTheme()` function resolves the visual theme
    — for Light the resolution is direct and the function removes the
    `.dark` class from the `<html>` element; for Dark the resolution
    is direct and the function adds the `.dark` class to the `<html>`
    element

6. **[Client]** for the System option the `applyTheme()` function
    reads the operating system `prefers-color-scheme` media query via
    `window.matchMedia("(prefers-color-scheme: dark)")` to determine
    whether to apply light or dark styling, then sets or removes the
    `.dark` class accordingly

7. **[Client]** Tailwind CSS uses the `.dark` class on the `<html>`
    element as the basis for its dark mode variant — every component
    styled with the `dark:` prefix responds to the class change and
    the entire UI re-renders with the new color scheme instantly
    without a page reload

8. **[Client]** the selected preference — Light, Dark, or System — is
    persisted to localStorage by the Zustand theme-store so the
    preference survives browser restarts and subsequent visits

9. **[Client]** on subsequent visits the theme-store reads the stored
    preference from localStorage during initialization and calls
    `applyTheme()` before the first paint — this prevents any flash
    of the wrong theme during page load by resolving and applying the
    correct `.dark` class state before React hydration completes

10. **[Client]** when the System option is active the app registers a
    `matchMedia` change listener on the `prefers-color-scheme` media
    query — if the user switches their operating system from light to
    dark mode or vice versa while the app is open, the listener fires
    and calls `applyTheme()` to update the `.dark` class immediately
    without any user interaction in the app

11. **[Client]** on the Tauri desktop app the theme switching works
    identically inside the webview — the `.dark` class mutation,
    localStorage persistence, and `prefers-color-scheme` listening
    all behave the same way as in the browser

12. **[Client]** the native title bar on the desktop app (minimize,
    maximize, and close buttons) is rendered by the operating system
    and always follows the OS theme — when the user selects Light or
    Dark explicitly and that choice differs from the current OS theme
    the title bar and the app content will not match visually, which
    is expected behavior for native windows with OS-rendered title
    bars; the System option avoids this mismatch by keeping the app
    content in sync with the OS theme

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| appearance_page_loading | theme_selector_ready | Appearance settings page loads and the Zustand theme-store provides the current preference to the segmented control | The page component mounted and the theme-store returned a valid preference value of Light, Dark, or System |
| theme_selector_ready | theme_applying | User clicks a different theme option in the segmented control and the Zustand theme-store updates with the new preference | The selected option differs from the currently active preference in the theme-store |
| theme_applying | theme_selector_ready | The `applyTheme()` function resolves the effective theme, mutates the `.dark` class on `<html>`, and localStorage persistence completes | The `.dark` class state on the `<html>` element matches the resolved theme and localStorage contains the updated preference string |
| system_theme_active | theme_applying | The OS `prefers-color-scheme` media query value changes while the System option is the active preference in the theme-store | The current theme-store preference equals System and the `matchMedia` listener detected a change in the OS color scheme |
| theme_applying | system_theme_active | The `applyTheme()` function finishes applying the resolved OS theme and the `matchMedia` listener remains registered for future OS changes | The theme-store preference equals System and the `.dark` class state matches the current OS color scheme |
| theme_selector_ready | theme_selector_ready | User clicks the already-active theme option in the segmented control — no state change occurs because the selection matches the current preference | The selected option equals the currently active preference so no theme-store update or `applyTheme()` call is triggered |

## Business Rules

- **Rule theme-immediate-apply:** IF the user selects a theme option
    in the segmented control THEN the `applyTheme()` function sets or
    removes the `.dark` class on the `<html>` element within the same
    event loop tick — the count of page reloads required to see the
    new theme equals 0
- **Rule system-theme-os-listener:** IF the active theme preference
    equals System THEN the app registers a `matchMedia` change
    listener on `prefers-color-scheme` that calls `applyTheme()` when
    the OS theme changes — the count of registered listeners while
    System is active equals 1 and the listener is removed when the
    user switches to Light or Dark
- **Rule localStorage-persistence:** IF the user selects any theme
    option THEN the Zustand theme-store writes the preference string
    to localStorage — the count of localStorage writes per selection
    equals 1 and the stored value matches the selected option
- **Rule desktop-title-bar-mismatch-expected:** IF the Tauri desktop
    user selects Light or Dark and the OS theme differs THEN the
    native title bar rendered by the OS does not match the webview
    content theme — this visual mismatch is expected behavior and no
    corrective action is taken because the OS controls the title bar
    rendering independently from CSS

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Owner | Navigate to `/app/settings/appearance`, view the theme segmented control with all three options, select any theme option, and have the selection persisted to localStorage and applied to the UI | No actions are denied to the owner on the appearance settings page — all theme options are selectable and the page is fully interactive | The appearance settings page is fully visible with the segmented control displaying Light, Dark, and System options and the current selection highlighted |
| Admin | Navigate to `/app/settings/appearance`, view the theme segmented control with all three options, select any theme option, and have the selection persisted to localStorage and applied to the UI | No actions are denied to admins on the appearance settings page — theme preference is a user-level setting not restricted by organization role | The appearance settings page is fully visible with the segmented control displaying Light, Dark, and System options and the current selection highlighted |
| Member | Navigate to `/app/settings/appearance`, view the theme segmented control with all three options, select any theme option, and have the selection persisted to localStorage and applied to the UI | No actions are denied to members on the appearance settings page — theme preference is a user-level setting not restricted by organization role | The appearance settings page is fully visible with the segmented control displaying Light, Dark, and System options and the current selection highlighted |
| Unauthenticated | No actions are permitted — the route guard redirects the user to the sign-in page before the appearance settings page renders and no theme controls are displayed | Cannot view or interact with the appearance settings page, the theme segmented control, or any other element on the settings page | The appearance settings page is not rendered and the redirect to sign-in occurs before any settings components mount in the DOM |

## Constraints

- The `applyTheme()` function resolves and applies the `.dark` class
    on the `<html>` element within 16 ms of the theme-store update —
    the count of intermediate render frames showing the previous theme
    after a selection equals 0.
- The theme preference stored in localStorage is one of exactly three
    string values: `light`, `dark`, or `system` — the count of
    invalid or unrecognized values written to localStorage by the
    theme-store equals 0.
- On subsequent visits the theme-store reads localStorage and applies
    the correct theme before the first paint — the count of visible
    theme flashes (wrong theme rendered then corrected) during page
    load equals 0.
- When the System preference is active exactly 1 `matchMedia` change
    listener is registered on the `prefers-color-scheme` media query
    — the count of duplicate listeners equals 0 and the listener is
    removed when the preference changes to Light or Dark.
- The segmented control labels for Light, Dark, and System are
    rendered via @repo/i18n translation keys — the count of hardcoded
    English strings in the theme selector component equals 0.
- The appearance settings page renders identically in LTR and RTL
    locales using logical CSS properties — the segmented control uses
    `padding-inline-start` and `padding-inline-end` instead of
    directional padding.

## Acceptance Criteria

- [ ] Navigating to `/app/settings/appearance` renders a theme selector with exactly 3 options labeled Light, Dark, and System — the count of theme options in the segmented control equals 3
- [ ] The currently active theme preference is visually highlighted in the segmented control — the count of highlighted options equals 1 and the highlighted option text equals the value stored in the Zustand theme-store
- [ ] Selecting the Dark option adds the `.dark` class to the `<html>` element within 16 ms — `document.documentElement.classList.contains("dark")` returns true after selecting Dark
- [ ] Selecting the Light option removes the `.dark` class from the `<html>` element within 16 ms — `document.documentElement.classList.contains("dark")` returns false after selecting Light
- [ ] Selecting the System option resolves the theme from the OS `prefers-color-scheme` media query — the `.dark` class is present on `<html>` when `window.matchMedia("(prefers-color-scheme: dark)").matches` equals true, and absent when it equals false
- [ ] The selected preference is persisted to localStorage within 16 ms of selection — `localStorage.getItem("theme")` is non-empty and returns the string `light`, `dark`, or `system` matching the selected option
- [ ] On page reload the theme is applied before first paint — the count of visible theme flashes equals 0 and the `.dark` class state on `<html>` is present or absent matching the localStorage value
- [ ] When System is active and the OS theme changes from light to dark, the `.dark` class is added to `<html>` without user interaction — `document.documentElement.classList.contains("dark")` returns true and the count of user-initiated actions required equals 0
- [ ] When System is active and the OS theme changes from dark to light, the `.dark` class is removed from `<html>` without user interaction — `document.documentElement.classList.contains("dark")` returns false and the count of user-initiated actions required equals 0
- [ ] On the Tauri desktop app the `.dark` class mutation, localStorage persistence, and `prefers-color-scheme` listener produce the same results as the browser — the count of behavioral differences equals 0 and `document.documentElement.classList.contains("dark")` returns true or false identically
- [ ] The native title bar on the desktop app follows the OS theme independently — when the user selects Dark and the OS is light, the title bar remains light-themed and `document.documentElement.classList.contains("dark")` is true
- [ ] An unauthenticated user navigating to `/app/settings/appearance` is redirected to the sign-in page — the final `window.location.pathname` equals the sign-in route and the count of rendered settings components equals 0

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| User selects the theme option that is already active in the segmented control | No state change occurs — the theme-store value remains unchanged, `applyTheme()` is not called, and localStorage is not written to because the selection matches the current preference | The count of `applyTheme()` invocations equals 0 and the localStorage value is unchanged after clicking the already-active option |
| localStorage is unavailable because the browser has disabled storage access or quota is exceeded | The theme-store falls back to the System default and resolves the theme from the OS `prefers-color-scheme` media query — theme selection still works for the current session but the preference is lost on page reload | The theme applies correctly during the session, and on reload the theme resets to the OS preference instead of the user's explicit selection |
| User switches the OS theme while the app is open and the active preference is Light or Dark, not System | The `matchMedia` listener does not fire because it is only registered when System is active — the UI retains the explicitly selected Light or Dark theme regardless of the OS change | The `.dark` class state on `<html>` remains unchanged after the OS theme switch and the count of `applyTheme()` calls from the listener equals 0 |
| User opens the app for the first time with no localStorage entry for the theme preference | The theme-store initializes with the System default and resolves the theme from the OS `prefers-color-scheme` media query — the segmented control highlights System as the active option | The localStorage key for theme is absent before first interaction, the segmented control shows System as highlighted, and the `.dark` class matches the OS preference |
| User rapidly clicks between Light, Dark, and System options within 100 ms intervals | Each click updates the theme-store and calls `applyTheme()` sequentially — the final `.dark` class state and localStorage value match the last option the user selected | The `.dark` class state on `<html>` matches the last-selected theme and `localStorage.getItem("theme")` equals the last-selected preference string |
| The `prefers-color-scheme` media query is not supported by the browser environment | The `applyTheme()` function treats the media query result as false (no dark preference) and applies the light theme when System is selected — no runtime error is thrown | The `.dark` class is absent from `<html>` when System is selected in a browser without media query support, and the count of uncaught exceptions equals 0 |

## Failure Modes

- **localStorage write failure prevents theme preference persistence**
    - **What happens:** The Zustand theme-store attempts to write the
        selected theme preference to localStorage but the write
        operation fails because storage quota is exceeded or the
        browser has restricted storage access in the current context.
    - **Source:** Browser storage quota exceeded from accumulated
        application data, or a restricted browsing mode that blocks
        localStorage writes such as certain privacy-focused browser
        configurations or enterprise group policies.
    - **Consequence:** The theme applies correctly for the current
        session because the Zustand store holds the preference in
        memory, but on the next page load the theme-store cannot read
        the persisted preference and falls back to the System default
        which resolves from the OS media query.
    - **Recovery:** The theme-store catches the localStorage write
        error and logs a warning to the console without crashing the
        application — the theme selection remains functional in memory
        and the user falls back to re-selecting their preference on
        each visit until localStorage becomes available again.

- **`matchMedia` listener fails to detect OS theme change**
    - **What happens:** The `prefers-color-scheme` media query listener
        registered by the app does not fire when the user changes the
        OS theme, leaving the UI stuck on the previously resolved
        theme while the System preference is active and the OS has
        transitioned to a different color scheme.
    - **Source:** A browser environment that does not fully support
        the `matchMedia` `change` event, or a garbage-collected
        listener reference that was not properly retained, or a Tauri
        webview configuration that does not propagate OS theme change
        events to the web content layer.
    - **Consequence:** The app content remains in the previous light
        or dark state while the OS has switched to the opposite theme,
        creating a visual inconsistency that the user notices when
        comparing the app to other OS-native windows or applications.
    - **Recovery:** The app falls back to re-resolving the OS theme
        on the next user-initiated navigation or page reload by
        calling `applyTheme()` during route transitions — the user
        can also manually select Light or Dark to override the stale
        System resolution and regain a consistent visual state.

- **`applyTheme()` function throws during `.dark` class mutation**
    - **What happens:** The `applyTheme()` function encounters a
        runtime error when attempting to set or remove the `.dark`
        class on the `<html>` element, leaving the DOM class list in
        an inconsistent state where the theme-store preference does
        not match the rendered visual theme.
    - **Source:** An unexpected `document.documentElement` reference
        error in a server-side rendering context where the DOM is not
        available, or a browser extension that intercepts and blocks
        class mutations on the root element through a MutationObserver
        override or content security policy restriction.
    - **Consequence:** The UI displays the wrong color scheme because
        the `.dark` class was not properly added or removed — Tailwind
        components render with stale `dark:` variant styles that do
        not match what the user selected in the segmented control.
    - **Recovery:** The theme-store catches the class mutation error
        and logs the failure with the attempted theme value and the
        current class list state — on the next navigation event or
        page reload the app retries the `applyTheme()` call which
        re-attempts the `.dark` class mutation on a fresh DOM state.

## Declared Omissions

- This specification does not define the visual design, color palette,
    or CSS custom properties used by the light and dark themes — those
    are defined in the Tailwind configuration and the design token
    foundation spec covering color variables and semantic tokens.
- This specification does not address per-organization theme branding
    or custom theme colors that organizations can configure — that
    behavior requires a separate spec covering organization-level
    appearance customization with custom CSS variable overrides.
- This specification does not cover the theme toggle button behavior
    in the dashboard header bar — that quick-access toggle is defined
    in the user-navigates-the-dashboard spec as part of the header
    controls section and delegates to the same Zustand theme-store.
- This specification does not address contrast or accessibility
    compliance of the light and dark color schemes themselves — WCAG
    contrast ratios and accessible color selection are covered by the
    design system foundation spec defining the color token hierarchy.
- This specification does not cover server-side theme rendering or
    theme preference syncing across multiple devices — the theme
    preference is stored exclusively in localStorage on the local
    device and is not persisted to any server-side user profile record.

## Related Specifications

- [user-navigates-the-dashboard](user-navigates-the-dashboard.md) —
    Defines the dashboard shell including the header bar theme toggle
    that provides quick-access theme switching using the same Zustand
    theme-store and `applyTheme()` function documented in this spec
- [shared-i18n](../foundation/shared-i18n.md) — Provides the
    internationalization infrastructure and translation loading
    mechanism that supplies localized labels for the Light, Dark, and
    System options rendered in the appearance settings segmented
    control
- [session-lifecycle](session-lifecycle.md) — Defines the
    authentication session management and route guard behavior that
    determines whether the user can access the appearance settings
    page or is redirected to the sign-in page before the page renders
- [auth-server-config](../foundation/auth-server-config.md) —
    Configures the Better Auth server and session validation that the
    appearance settings route guard relies on to verify the user is
    authenticated before rendering the theme selector controls

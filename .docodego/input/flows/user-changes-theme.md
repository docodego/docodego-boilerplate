[← Back to Index](README.md)

# User Changes Theme

## The Appearance Settings Page

The user navigates to `/app/settings/appearance`. The page presents a theme selector with three localized options: Light, Dark, and System. The selector is rendered as a segmented control or radio group, with the currently active option visually highlighted.

## Selecting a Theme

When the user selects a different theme option, the Zustand theme-store updates immediately. The `applyTheme()` function resolves the actual visual theme to apply. For Light and Dark, the resolution is direct. For System, the function reads the operating system's `prefers-color-scheme` media query to determine whether to apply light or dark styling.

The function sets or removes the `.dark` class on the `<html>` element. Tailwind CSS uses this class as the basis for its dark mode variant, so the entire UI re-renders with the new color scheme instantly — no page reload required. Every component styled with Tailwind's `dark:` prefix responds to the class change.

## Persistence and Return Visits

The selected preference — Light, Dark, or System — is persisted to localStorage. When the user returns to the app on a subsequent visit, the theme-store reads the stored preference during initialization and applies the correct theme before the first paint. This prevents any flash of the wrong theme during page load.

When the System option is active, the app also listens for real-time changes to the OS theme preference. If the user switches their operating system from light to dark mode (or vice versa) while the app is open, the UI updates immediately to match without any user interaction in the app.

## Desktop Behavior

On the desktop app, theme switching works identically inside the Tauri webview — the `.dark` class, localStorage persistence, and `prefers-color-scheme` listening all behave the same. However, the native title bar (minimize, maximize, and close buttons) is rendered by the operating system, not by CSS. It always follows the OS theme. When the user selects "Light" or "Dark" explicitly and that choice differs from the OS theme, the title bar and the app content will not match visually. This is expected behavior for native windows with OS-rendered title bars. The "System" option avoids this mismatch since it keeps the app in sync with the OS.

[← Back to Index](README.md)

# User Changes Theme on Mobile

## The Mobile Settings Screen

The user navigates to the settings screen within the Expo mobile app. The screen presents a localized theme selector with three options: Light, Dark, and System. The currently active option is visually highlighted. This mirrors the web [appearance settings](user-changes-theme.md), but the underlying mechanism is native rather than browser-based.

## Selecting a Theme

When the user taps a different theme option, the Zustand theme-store updates immediately. Unlike the web flow, which toggles a `.dark` class on the `<html>` element and relies on Tailwind CSS, the mobile app applies the new color scheme through NativeWind's native theming system. All components styled with NativeWind's `dark:` variants respond to the store change and re-render with the updated color palette. The `expo-status-bar` component adjusts the status bar icon color — light icons on dark backgrounds, dark icons on light backgrounds — so the system chrome stays consistent with the app's appearance.

## Persistence with MMKV

The selected preference — Light, Dark, or System — is persisted to `react-native-mmkv`, the same synchronous key-value store used during [app launch](user-launches-mobile-app.md) for state hydration. On subsequent launches, the theme-store reads the stored preference from MMKV before the first frame renders, preventing any flash of the wrong theme behind the splash screen.

## System Theme Behavior

When the user selects the System option, the app reads the device's current appearance setting to determine whether to apply light or dark styling. The app also listens for real-time changes to the OS appearance preference. If the user switches their device from light to dark mode (or vice versa) while the app is open, the UI updates immediately to match — no interaction within the app is required. This uses the same reactive appearance listener that is initialized during [app launch](user-launches-mobile-app.md).

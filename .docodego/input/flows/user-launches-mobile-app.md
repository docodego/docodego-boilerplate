# User Launches Mobile App

## Splash and Asset Loading

When the user taps the DoCodeGo icon on their phone, `expo-splash-screen` immediately displays the branded splash image while the app initializes behind the scenes. During this window, `expo-font` loads the custom Geist typeface so that the first rendered screen uses the correct typography with no flash of unstyled text. The splash screen remains visible until both font loading and the initial state hydration complete.

## Locale and State Hydration

While the splash is still showing, `expo-localization` reads the device's native locale and RTL direction. These values feed directly into i18next initialization via `@repo/i18n`, so the app renders in the correct language and text direction from the first frame. In parallel, `react-native-mmkv` loads persisted Zustand state — the same theme store and sidebar preference store used on the web, but backed by MMKV instead of localStorage. This means a user who chose dark mode on their last visit sees dark mode immediately, with no theme flicker.

## Authentication Check and Navigation

With state hydrated, the app checks for an existing session. The `@better-auth/expo` client reads the stored session token from `expo-secure-store`, which keeps credentials in the device's encrypted keychain storage. If a valid token is found, Expo Router navigates the user directly to their active organization's dashboard — the same resolution logic as the web app, skipping sign-in entirely. If no token exists or the token has expired, the user is directed to the sign-in screen.

## Platform Display Setup

On Android, `react-native-edge-to-edge` extends the app content behind the system navigation bar and status bar for a modern, immersive appearance. The `expo-status-bar` component styles the status bar icons as light or dark depending on the active theme and the current screen's background color. Once all initialization is complete and the root layout has mounted, the splash screen is hidden and the user sees the fully rendered app.
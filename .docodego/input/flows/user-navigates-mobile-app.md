# User Navigates Mobile App

## Routing and Screen Structure

Expo Router v6 provides file-based routing for the mobile app, mirroring the convention used by TanStack Router on the web. Screens are organized as files within the app directory, and Expo Router generates typed routes automatically. The primary navigation structure uses either tab navigation for top-level sections — dashboard, members, teams, settings — or stack navigation for drill-down flows within each section. Navigating between tabs preserves the state of each section, so the user can switch away and return without losing their place.

## Gestures, Animations, and Safe Areas

`react-native-gesture-handler` enables native gesture recognition throughout the app. The user can swipe from the left edge to go back in a stack, long-press items for contextual actions, and use pull-to-refresh on list screens to reload data. `react-native-reanimated` drives smooth, performant transitions between screens — push and pop animations run on the UI thread for 60fps fluidity. `react-native-safe-area-context` ensures that content respects device-specific insets for notches, status bars, dynamic islands, and home indicators. No content is clipped or hidden behind system UI elements.

## Deep Linking and Org Switching

Deep links using the `docodego://` scheme open directly to the corresponding screen inside the app. If a user taps a `docodego://` link on their device — from a notification, email, or chat message — Expo Router resolves the path and navigates to the matching route. If the user is not authenticated, the app redirects to sign-in first and returns to the deep link target after successful authentication. Organization switching is available within the navigation structure, allowing the user to change their active org context without leaving the app.

## Shared Packages and Data Patterns

The mobile app consumes the same shared packages as the web. `@repo/contracts` provides typed oRPC contracts for API calls, ensuring the mobile client and API stay in sync at compile time. `@repo/i18n` delivers translations in all supported locales — Arabic RTL works through React Native's built-in RTL layout support, which `expo-localization` activates based on the detected device locale. `@repo/library` supplies validators, constants, and formatters shared across platforms. Lists use infinite scroll for paginated data and pull-to-refresh for manual reloading, following standard mobile interaction patterns.
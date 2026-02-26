[← Back to Roadmap](../ROADMAP.md)

# Expo Build

## Intent

This spec defines the Expo 54 mobile application configuration for the DoCodeGo boilerplate, covering EAS Build profiles, Metro bundler configuration, native module integration, and platform-specific setup for iOS and Android. The mobile app shares `@repo/contracts`, `@repo/library`, and `@repo/i18n` with the rest of the monorepo. Authentication uses `@better-auth/expo` with `expo-secure-store` for token persistence. This spec ensures that the Expo project is configured with correct build profiles for development, preview, and production, that all native modules are installed and linked, and that the Metro bundler resolves monorepo workspace dependencies correctly.

## Acceptance Criteria

- [ ] The `apps/mobile` directory is present and contains `app.json` (or `app.config.ts`) with the Expo project configuration
- [ ] The `app.json` sets the `expo.scheme` to `"docodego"` for deep linking — this value is present and non-empty
- [ ] The `app.json` sets the `expo.sdkVersion` to a value >= 54 — the SDK version is present
- [ ] An `eas.json` file is present and defines at least 4 build profiles: `development`, `development:device`, `preview`, and `production` — all 4 are present
- [ ] The `development` profile sets `developmentClient` to true and `distribution` to `"internal"` — both values are present
- [ ] The `production` profile sets `distribution` to `"store"` — this value is present for app store submission
- [ ] The `metro.config.js` file is present and configures the Metro bundler to resolve workspace packages from the monorepo root `node_modules` — the resolver configuration is present and references the root directory
- [ ] The `@better-auth/expo` package is present in `package.json` dependencies for mobile auth
- [ ] The `expo-secure-store` package is present in `package.json` dependencies for encrypted token storage
- [ ] The `react-native-mmkv` package is present in `package.json` dependencies with version >= 3
- [ ] The `react-native-reanimated` package is present in `package.json` dependencies with version >= 4
- [ ] The `expo-localization` package is present in `package.json` dependencies for native locale detection
- [ ] The `expo-router` package is present in `package.json` dependencies with version >= 6 for file-based routing
- [ ] The Expo auth client is configured with at least 4 plugin clients: `expoClient()`, `emailOTPClient()`, `organizationClient()`, and `ssoClient()` — all 4 are present in the client setup
- [ ] The Expo auth client does not include `passkeyClient()` — the count of passkey client references in the mobile auth setup equals 0 (WebAuthn is not supported on React Native)
- [ ] Running `pnpm --filter mobile typecheck` exits with code = 0 and produces 0 errors
- [ ] The `package.json` contains a `"typecheck"` script and a `"test"` script — both are present and non-empty

## Constraints

- The mobile app does not support passkey authentication — WebAuthn is not available in React Native. The count of `@better-auth/passkey` or `passkeyClient` references in `apps/mobile` equals 0. The sign-in screen displays only Email OTP, SSO, and Guest sign-in options.
- The mobile app uses MMKV for persistent key-value storage instead of AsyncStorage — the count of `@react-native-async-storage/async-storage` imports in `apps/mobile` equals 0. MMKV is at least 10x faster and pairs with Zustand persistence for the theme and sidebar stores.
- The Metro bundler requires explicit configuration for monorepo workspace resolution — the `metro.config.js` sets `watchFolders` to include the monorepo root and configures `nodeModulesPaths` to resolve packages from both the workspace and root `node_modules`. Without this, Metro fails to resolve `@repo/*` packages.
- E2E testing on mobile uses Maestro, not Playwright — the count of Playwright references in `apps/mobile` equals 0. Maestro YAML test files are located in the `apps/mobile/maestro/` directory.

## Failure Modes

- **Metro fails to resolve workspace package**: The Metro bundler cannot find `@repo/contracts` or `@repo/i18n` because the `watchFolders` configuration does not include the monorepo root, causing a "module not found" error at bundling time. The Metro config validates that the root `node_modules` path is present in `watchFolders`, and if absent, the dev server returns error with a diagnostic message listing the unresolved package name and suggesting the `watchFolders` fix.
- **Native module not linked**: A developer adds a new native module dependency but does not run `npx expo prebuild` to regenerate the native project, causing a runtime crash with "module not registered" on app launch. The Expo dev client logs the missing module name in the error overlay, and the developer runs `npx expo prebuild --clean` to regenerate the native project with the new module linked.
- **EAS build profile misconfiguration**: The `production` build profile sets `developmentClient` to true by mistake, causing the production binary to include development tools and a larger bundle size. The CI build step validates that the `production` profile has `developmentClient` absent or set to false, and returns error if the development client is enabled in a production build, blocking the release.
- **Keychain access failure**: The `expo-secure-store` API fails to read or write the auth token on a specific device because the device's keychain is locked or corrupted, causing the user to be signed out on every app restart. The auth client catches the keychain exception and falls back to a non-persistent in-memory session, logging a warning that notifies the user to re-sign-in and that their session will not persist across app restarts.

## Declared Omissions

- Mobile sign-in UI and auth flow behavior (covered by `user-signs-in-on-mobile.md`)
- Expo Router navigation and deep linking (covered by `user-navigates-mobile-app.md` and `mobile-handles-deep-link.md`)
- Mobile theme and language switching (covered by `user-changes-theme-on-mobile.md` and `user-changes-language-on-mobile.md`)
- Maestro E2E test definitions (implementation detail, not spec-level concern)
- App store submission and review process (operational concern)

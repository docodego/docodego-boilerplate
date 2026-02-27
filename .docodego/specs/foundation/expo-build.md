---
id: SPEC-2026-013
version: 1.0.0
created: 2026-02-26
owner: Mayank (Intent Architect)
status: draft
roles: [Framework Adopter]
---

[← Back to Roadmap](../ROADMAP.md)

# Expo Build

## Intent

This spec defines the Expo 54 mobile application build
configuration for the DoCodeGo boilerplate, covering EAS Build
profiles, Metro bundler configuration, native module
integration, and platform-specific setup for iOS and Android.
The mobile app shares `@repo/contracts`, `@repo/library`, and
`@repo/i18n` with the rest of the monorepo through workspace
dependencies. Authentication uses `@better-auth/expo` with
`expo-secure-store` for encrypted token persistence on device.
This spec ensures that the Expo project is configured with
correct build profiles for development, preview, and
production, that all native modules are installed and linked,
and that the Metro bundler resolves monorepo workspace
dependencies correctly through explicit path configuration.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `@repo/contracts` | read | Build time — Metro bundles shared API types | Build fails at compile time because the bundler cannot resolve contract type imports and CI alerts to block deployment |
| `@repo/library` | read | Build time — Metro bundles shared validators and utilities | Build fails at compile time because the bundler cannot resolve library module imports and CI alerts to block deployment |
| `@repo/i18n` | read | Runtime — locale detection and translation lookups | Translation function falls back to default English locale strings so the app remains readable but untranslated for non-English users |
| EAS Build | write | CI or developer triggers a cloud build | Local development continues unaffected because `expo start` runs the Metro dev server independently of EAS cloud infrastructure |
| `expo-secure-store` | read/write | Runtime — auth token persistence via device keychain | Auth client falls back to non-persistent in-memory session storage, logging a warning that the session will not persist across app restarts |
| `react-native-mmkv` | read/write | Runtime — persistent key-value storage for theme and sidebar state | Zustand stores that depend on MMKV persistence fall back to in-memory state, losing user preferences on app restart |

## Behavioral Flow

1. **[Developer]** runs `pnpm --filter mobile start`
   to launch the Expo dev server in the `apps/mobile`
   workspace directory
2. **[Metro bundler]** reads `metro.config.js` and resolves
   `watchFolders` to include the monorepo root directory so
   that `@repo/*` workspace packages are discoverable
3. **[Metro bundler]** resolves `nodeModulesPaths` to include
   both the workspace-level and root-level `node_modules`
   directories for dependency resolution
4. **[Expo dev client]** launches on the target device or
   simulator and connects to the Metro dev server over the
   local network
5. **[Metro bundler]** bundles the JavaScript source including
   all workspace dependencies and serves it to the Expo dev
   client on the connected device
6. **[Developer]** triggers an EAS Build by running
   `eas build --profile <name>` where `<name>` is one of the
   4 defined profiles: `development`, `development:device`,
   `preview`, or `production`
7. **[EAS Build]** reads `eas.json` to determine the build
   profile settings including `developmentClient` and
   `distribution` values for the selected profile
8. **[EAS Build]** produces the platform binary (`.apk` or
   `.ipa`) and uploads it to the EAS dashboard for
   distribution or store submission

## State Machine

No stateful entities. The Expo build configuration is a
declarative setup with no entities that transition through
lifecycle states within this spec's scope.

## Business Rules

No conditional business rules. Build profile selection is an
explicit developer choice, not a conditional runtime decision.

## Permission Model

Single role; no permission model needed. All developers with
repository access have identical capabilities for running
builds and configuring the Expo project.

## Constraints

- The mobile app does not include passkey authentication
  because WebAuthn is not available in React Native — the
  count of `@better-auth/passkey` or `passkeyClient`
  references in `apps/mobile` equals 0, and the sign-in
  screen displays only Email OTP, SSO, and Guest sign-in
  options.
- The mobile app uses MMKV for persistent key-value storage
  instead of AsyncStorage — the count of
  `@react-native-async-storage/async-storage` imports in
  `apps/mobile` equals 0 because MMKV is at least 10x
  faster and pairs with Zustand persistence for the theme
  and sidebar stores.
- The Metro bundler requires explicit configuration for
  monorepo workspace resolution — the `metro.config.js`
  sets `watchFolders` to include the monorepo root and
  configures `nodeModulesPaths` to resolve packages from
  both the workspace and root `node_modules` directories,
  without which Metro fails to resolve `@repo/*` packages.
- E2E testing on mobile uses Maestro, not Playwright — the
  count of Playwright references in `apps/mobile` equals 0
  and Maestro YAML test files are located in the
  `apps/mobile/maestro/` directory.
- The mobile app uses `pnpm` exclusively for all package
  management — the count of `npx`, `bunx`, or `yarn`
  invocations in mobile workspace scripts equals 0.

## Acceptance Criteria

- [ ] The `apps/mobile` directory is present and contains `app.json` (or `app.config.ts`) with a non-empty Expo project configuration
- [ ] The `app.json` sets `expo.scheme` to the value `"docodego"` — this string is present and non-empty for deep linking
- [ ] The `app.json` sets `expo.sdkVersion` to a value >= 54 — the SDK version number is present and equals at least 54
- [ ] An `eas.json` file is present and defines at least 4 build profiles: `development`, `development:device`, `preview`, and `production`
- [ ] The `development` profile sets `developmentClient` to true and `distribution` to `"internal"` — both values are present
- [ ] The `production` profile sets `distribution` to `"store"` and `developmentClient` is absent or false — both conditions are true
- [ ] The `metro.config.js` file is present and configures `watchFolders` to include at least 1 path referencing the monorepo root directory
- [ ] The `metro.config.js` configures `nodeModulesPaths` to include at least 2 paths for workspace-level and root-level `node_modules`
- [ ] The `@better-auth/expo` package is present in `package.json` dependencies with a non-empty version string for mobile auth
- [ ] The `expo-secure-store` package is present in `package.json` dependencies with a non-empty version string for encrypted token storage
- [ ] The `react-native-mmkv` package is present in `package.json` dependencies with version >= 3 — the version number is at least 3
- [ ] The `react-native-reanimated` package is present in `package.json` dependencies with version >= 4 — the version is at least 4
- [ ] The `expo-localization` package is present in `package.json` dependencies with a non-empty version string for native locale detection
- [ ] The `expo-router` package is present in `package.json` dependencies with version >= 6 — the version number is at least 6
- [ ] The Expo auth client is configured with at least 4 plugin clients: `expoClient()`, `emailOTPClient()`, `organizationClient()`, and `ssoClient()` — all 4 are present
- [ ] The Expo auth client does not include `passkeyClient()` — the count of passkey client references in the mobile auth setup equals 0
- [ ] Running `pnpm --filter mobile typecheck` exits with code 0 and produces 0 TypeScript errors in output
- [ ] The `package.json` contains a `"typecheck"` script and a `"test"` script — both keys are present and their values are non-empty strings

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The developer runs `expo start` without first running `pnpm install` at the monorepo root, leaving workspace symlinks unresolved | Metro bundler exits with a "module not found" error listing the missing `@repo/*` package name and does not silently fall back to stale cached modules | The Metro process exit code is non-zero and stderr contains the unresolved package name |
| The `eas.json` file is missing entirely when a developer runs `eas build` from the mobile workspace directory | EAS CLI exits with a non-zero exit code and prints an error message indicating that `eas.json` is not found in the project | The EAS CLI exit code is non-zero and stderr contains a reference to the missing `eas.json` file |
| The `app.json` contains an `expo.sdkVersion` value that does not match the installed `expo` package version in `node_modules` | Expo CLI prints a version mismatch warning at startup indicating the `sdkVersion` and installed version differ, but does not crash | The warning message is present in stdout and the dev server starts with exit code 0 |
| A native module listed in `package.json` (such as `react-native-mmkv`) has not been linked via `expo prebuild`, causing the native binary to lack the module | The Expo dev client displays a red-screen error overlay naming the unregistered native module and does not crash to the home screen silently | The error overlay text contains the module name and the phrase "not registered" or "not found" |
| The device keychain is locked or corrupted when `expo-secure-store` attempts to read the stored auth token on app launch | The auth client catches the keychain exception and falls back to non-persistent in-memory session, displaying a re-sign-in prompt to the user | The app launches without crashing and the user sees a sign-in screen rather than an unhandled exception |

## Failure Modes

- **Metro fails to resolve workspace packages from the
    monorepo root directory**
    - **What happens:** The Metro bundler cannot locate
        `@repo/contracts` or `@repo/i18n` because the
        `watchFolders` configuration in `metro.config.js`
        does not include the monorepo root path, producing
        a "module not found" error at bundle time.
    - **Source:** Incorrect or missing `watchFolders` path
        in the Metro bundler configuration file.
    - **Consequence:** The dev server cannot produce a
        working bundle and the mobile app fails to launch
        on any device or simulator until the path is
        corrected.
    - **Recovery:** Metro returns error with a diagnostic
        message listing the unresolved package name, and
        the developer corrects the `watchFolders` path in
        `metro.config.js` — CI typecheck alerts and blocks
        deployment because unresolved imports produce
        TypeScript compilation errors.
- **EAS production build profile includes development client
    tools by mistake**
    - **What happens:** The `production` build profile in
        `eas.json` has `developmentClient` set to true,
        causing the production binary to include debugging
        tools, a larger bundle size, and an exposed dev
        menu in the released application.
    - **Source:** Copy-paste error from the `development`
        profile when configuring `eas.json` build profiles.
    - **Consequence:** End users receive a production build
        containing development tools that expose internal
        debugging interfaces and increase the binary size
        by at least 5 MB compared to a clean production
        build.
    - **Recovery:** The CI build step validates that the
        `production` profile has `developmentClient` absent
        or set to false, and CI alerts and blocks the
        release pipeline if the development client is
        enabled in the production build profile.
- **Keychain access failure prevents auth token retrieval
    on app launch**
    - **What happens:** The `expo-secure-store` API fails
        to read the persisted auth token because the device
        keychain is locked, corrupted, or has been reset
        after an OS update, causing the stored session to
        be inaccessible.
    - **Source:** Device-level keychain state change outside
        the app's control, such as a factory reset, OS
        update, or keychain corruption.
    - **Consequence:** The user is signed out on every app
        restart and loses their persisted session, requiring
        re-authentication through the sign-in flow each
        time the app launches.
    - **Recovery:** The auth client catches the keychain
        read exception and falls back to a non-persistent
        in-memory session, logging a warning that notifies
        the user to re-sign-in because their stored session
        could not be retrieved from the device keychain.
- **MMKV native module not linked after dependency install
    without prebuild step**
    - **What happens:** A developer adds `react-native-mmkv`
        to `package.json` but does not run `expo prebuild`
        to regenerate the native project, causing a runtime
        crash with "module not registered" when the app
        attempts to initialize MMKV storage on launch.
    - **Source:** Missing prebuild step after adding a new
        native module dependency to the mobile workspace.
    - **Consequence:** The app crashes on launch before
        reaching the main screen because the MMKV native
        module binary is not present in the compiled
        application, blocking all users from using the app.
    - **Recovery:** The Expo dev client logs the missing
        module name in the error overlay, and the developer
        runs `expo prebuild --clean` to regenerate the
        native project — CI alerts on the build failure
        because the EAS Build step degrades to a non-zero
        exit code when native modules are unresolved.

## Declared Omissions

- Mobile sign-in UI layout, auth flow behavior, and
  screen transitions are not covered here and are defined
  in `user-signs-in-on-mobile.md` instead of this spec.
- Expo Router file-based navigation structure and deep
  linking route resolution are not covered here and are
  defined in `user-navigates-mobile-app.md` and
  `mobile-handles-deep-link.md` instead of this spec.
- Mobile theme switching, dark mode toggle, and language
  switching UI are not covered here and are defined in
  `user-changes-theme-on-mobile.md` and
  `user-changes-language-on-mobile.md` instead of this
  spec.
- Maestro E2E test file definitions and test scenario
  authoring are implementation-level concerns that belong
  in the test workspace, not in this build configuration
  specification.
- App store submission workflows, review processes, and
  release versioning are operational concerns handled by
  the release management process, not this build
  configuration specification.

## Related Specifications

- [shared-contracts](shared-contracts.md) — oRPC contract
  definitions and Zod schemas that the mobile app imports
  for type-safe API communication with the backend
- [shared-i18n](shared-i18n.md) — Internationalization
  infrastructure providing locale detection and translation
  functions consumed by the mobile app at runtime
- [auth-server-config](auth-server-config.md) — Better Auth
  server configuration that the `@better-auth/expo` client
  connects to for authentication on mobile devices
- [ci-cd-pipelines](ci-cd-pipelines.md) — CI/CD pipeline
  configuration that triggers EAS Build profiles for mobile
  app builds and distribution to testers and app stores
- [database-schema](database-schema.md) — Database schema
  definitions that underpin the API endpoints consumed by
  the mobile app through the shared contracts package

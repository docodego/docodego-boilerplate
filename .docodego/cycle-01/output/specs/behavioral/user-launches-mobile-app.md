---
id: SPEC-2026-073
version: 1.0.0
created: 2026-02-27
owner: Mayank (Intent Architect)
status: approved
roles: [User]
---

[← Back to Roadmap](../ROADMAP.md)

# User Launches Mobile App

## Intent

This spec defines how a user launches the DoCodeGo mobile application
on iOS or Android and reaches a fully interactive state with the
correct theme, locale, and authentication context resolved before the
first visible frame. When the user taps the DoCodeGo icon on their
device home screen, `expo-splash-screen` immediately displays a
branded splash image while the Expo runtime initializes behind the
scenes. During this window `expo-font` loads the custom Geist typeface
so the first rendered screen uses the correct typography with zero
flash of unstyled text. In parallel `expo-localization` reads the
device locale and RTL direction, feeding those values into i18next
initialization via `@repo/i18n` so the app renders in the correct
language and text direction from the first frame. At the same time
`react-native-mmkv` loads persisted Zustand state including the theme
store and sidebar preference store, ensuring a user who chose dark mode
on their last visit sees dark mode immediately with no theme flicker.
The `@better-auth/expo` client reads the stored session token from
the Expo encrypted credential store in the device keychain. If a
valid token exists, Expo Router navigates the user directly to their
active organization dashboard. If the token is absent or expired, the
user is directed to the sign-in screen. On Android
`react-native-edge-to-edge` extends app content behind the system
navigation bar and status bar for an immersive appearance. The
`expo-status-bar` component styles status bar icons as light or dark
depending on the active theme. Once all initialization completes and
the root layout mounts, the splash screen is hidden and the user sees
the fully rendered application.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| expo-splash-screen (displays a branded static image while the Expo runtime initializes all subsystems behind the scenes) | render | Immediately when the user taps the app icon on the device home screen, before any JavaScript bundle execution begins | The app displays a blank white screen during initialization instead of the branded splash image, and the user sees raw component mounting — the runtime logs the splash screen initialization failure and continues startup without the branded image |
| expo-font with Geist typeface (preloads the custom Geist font family so the first rendered screen uses correct typography without fallback) | read | During the splash screen display window, before the root layout component mounts and renders any text-bearing UI elements | The font loading call rejects and the app falls back to the platform default system font (San Francisco on iOS, Roboto on Android) — the runtime logs the font loading failure and the user sees system typography instead of Geist on all text elements |
| expo-localization (reads the device native locale identifier and RTL text direction preference from operating system settings) | read | During the splash screen display window, in parallel with font loading and state hydration, before i18next initialization | The locale detection returns a null value and i18next falls back to the default English locale with LTR text direction — the runtime logs the locale detection failure and the user sees English text regardless of their device language setting |
| @repo/i18n (i18next initialization infrastructure that configures language bundles and text direction based on the detected device locale) | config | Immediately after expo-localization provides the device locale and RTL direction, during the splash screen display window | The i18n namespace fails to load and the UI degrades to displaying raw translation keys instead of localized strings — the runtime logs the missing namespace and retries loading the translations on the next navigation event |
| react-native-mmkv with Zustand persistence (loads persisted theme store and sidebar preference store from MMKV native key-value storage) | read | During the splash screen display window, in parallel with font loading and locale detection, before the root layout renders | The MMKV read operation fails and the Zustand stores initialize with default values (light theme, sidebar collapsed) — the runtime logs the MMKV read failure and the user sees the default theme instead of their previously saved preference |
| @better-auth/expo v1 (authentication client that manages session tokens and communicates with the auth server for token validation) | read | After state hydration completes, during the splash screen display window, to determine whether the user has an active authenticated session | The auth client fails to initialize and the app falls back to treating the user as unauthenticated — Expo Router navigates to the sign-in screen and the runtime logs the auth client initialization failure |
| Expo encrypted credential store (Keychain on iOS and encrypted SharedPreferences on Android that persists the session token between app launches) | read | When the @better-auth/expo client checks for an existing session token during the authentication verification step | The credential store returns no token because the keychain is locked or the encrypted storage is corrupted — the auth client treats the result as no session and the app falls back to navigating the user to the sign-in screen |
| Expo Router (file-based navigation system that resolves the initial route based on authentication state and active organization context) | navigate | After the authentication check completes and the auth state is determined, the router resolves whether to navigate to the dashboard or the sign-in screen | The router fails to resolve the initial route and falls back to the root index screen — the runtime logs the navigation resolution failure and the user sees the default landing route instead of the dashboard or sign-in screen |
| react-native-edge-to-edge on Android (extends app content rendering behind the system navigation bar and status bar for immersive display) | write | During the root layout mount phase on Android devices, after all initialization tasks complete and before the splash screen is hidden | The edge-to-edge configuration fails and the app renders with standard system bar insets — the status bar and navigation bar retain their default opaque backgrounds and the runtime logs the edge-to-edge setup failure |
| expo-status-bar (component that styles the system status bar icon color as light or dark based on the active theme and current screen background) | write | After the theme store hydrates from MMKV and the root layout renders, the status bar component applies the icon style matching the active theme | The status bar component fails to apply the icon style and the system retains its default status bar appearance — the runtime logs the status bar configuration failure and the user sees default OS-themed status bar icons |

## Behavioral Flow

1. **[User]** taps the DoCodeGo application icon on the device home
    screen — the operating system launches the Expo runtime process
    and begins loading the JavaScript bundle for the application

2. **[App]** expo-splash-screen immediately displays the branded
    static splash image covering the entire screen while the Expo
    runtime initializes — the splash remains visible until all
    initialization tasks (font loading, locale detection, state
    hydration, and auth check) complete

3. **[App]** expo-font begins loading the custom Geist typeface from
    the bundled assets in parallel with locale detection and state
    hydration — the font loading operation runs concurrently to
    minimize total initialization time

4. **[OS]** expo-localization reads the device native locale
    identifier (such as "en-US" or "ar-SA") and the RTL text direction
    preference from the operating system settings — this read executes
    in parallel with font loading and MMKV state hydration

5. **[App]** the detected locale and RTL direction values feed
    directly into i18next initialization via @repo/i18n — the i18n
    infrastructure configures the correct language bundle and text
    direction so the first rendered screen displays localized strings
    in the correct language and layout direction

6. **[App]** react-native-mmkv loads persisted Zustand state from the
    native MMKV key-value storage — the theme store and sidebar
    preference store hydrate with the values the user saved in their
    previous session, so dark mode users see dark mode immediately
    with zero theme flicker

7. **[App]** the @better-auth/expo client reads the stored session
    token from the Expo encrypted credential store in the device
    keychain (Keychain on iOS, encrypted SharedPreferences on Android)
    to determine whether the user has an active authenticated session

8. **[App]** if a valid session token is found in the credential store
    and the token has not expired, Expo Router navigates the user
    directly to their active organization dashboard — the same
    organization resolution logic used on the web determines which
    organization dashboard loads, and the sign-in screen is skipped
    entirely

9. **[App]** if no session token exists in the credential store or the
    token has expired or been revoked on the server side, Expo Router
    navigates the user to the sign-in screen where they authenticate
    using any configured method (email OTP, passkey, or SSO)

10. **[App]** on Android devices, react-native-edge-to-edge extends
    the app content rendering behind the system navigation bar and
    status bar for a modern immersive appearance — the app content
    fills the entire screen area including the system bar regions

11. **[App]** expo-status-bar styles the system status bar icons as
    light or dark depending on the active theme restored from MMKV
    and the current screen background color — dark theme uses light
    icons and light theme uses dark icons for contrast

12. **[App]** once all initialization tasks have completed and the
    root layout component has mounted with the correct theme, locale,
    font, and navigation state, expo-splash-screen hides the splash
    image and the user sees the fully rendered interactive application

## State Machine

| From State | To State | Trigger | Guard Condition |
|------------|----------|---------|-----------------|
| not_running | splash_visible | User taps the DoCodeGo app icon on the device home screen and the operating system launches the Expo runtime process | The application binary exists on the device and the operating system grants permission to start the process |
| splash_visible | initializing_parallel | The Expo runtime begins executing the JavaScript bundle and starts parallel initialization of font loading, locale detection, and MMKV state hydration | The JavaScript bundle loaded without a fatal parse error and the Expo runtime allocated the required native modules |
| initializing_parallel | state_hydrated | All parallel initialization tasks complete — expo-font loaded the Geist typeface, expo-localization read the device locale, and react-native-mmkv restored the Zustand stores | Each parallel task either succeeded or fell back to its default value (system font, English locale, or default theme) |
| state_hydrated | session_checking | The @better-auth/expo client reads the session token from the Expo encrypted credential store to verify whether the user has an active authenticated session | The Zustand stores are hydrated and the i18n infrastructure is initialized with the detected or fallback locale |
| session_checking | app_ready_authenticated | The auth client finds a valid, non-expired session token in the encrypted credential store and confirms the session with the auth server | The session token exists in the Expo encrypted credential store, has not expired, and the auth server validates the token |
| session_checking | app_ready_unauthenticated | The auth client finds no session token, or the token has expired, or the auth server rejects the token as invalid or revoked | The encrypted credential store returned no token, or the token failed server-side validation due to expiration or revocation |
| app_ready_authenticated | app_interactive | Expo Router navigates to the active organization dashboard, expo-splash-screen hides the splash image, and the root layout renders the fully interactive application | The root layout component mounted, the navigation resolved to the dashboard route, and all UI elements use the hydrated theme and locale |
| app_ready_unauthenticated | app_interactive | Expo Router navigates to the sign-in screen, expo-splash-screen hides the splash image, and the sign-in form renders with the correct locale and theme | The root layout component mounted, the navigation resolved to the sign-in route, and all UI elements use the hydrated theme and locale |
| app_interactive | not_running | The user closes the application by swiping it away from the task switcher, or the operating system terminates the process due to memory pressure | No guard — the operating system terminates the process and all in-memory state is lost (persisted state remains in MMKV and the encrypted credential store) |

## Business Rules

- **Rule splash-visible-until-hydration-complete:** IF the Expo
    runtime is initializing the application THEN the splash screen
    remains visible until font loading, locale detection, MMKV state
    hydration, and the authentication check all complete — the count
    of frames where the user sees a partially initialized UI equals 0
- **Rule no-font-flash:** IF expo-font is loading the Geist typeface
    during initialization THEN the splash screen remains visible until
    the font is loaded or the load fails — the count of text elements
    rendered with the system fallback font before Geist loads equals 0
    on successful font load
- **Rule locale-from-device:** IF expo-localization reads the device
    native locale THEN i18next initializes with that locale and the
    corresponding RTL direction — the locale code passed to i18next
    equals the locale code returned by expo-localization
- **Rule mmkv-restores-theme-immediately:** IF the user previously
    selected dark mode and the preference is stored in MMKV THEN the
    first rendered frame after the splash screen uses the dark theme
    — the count of frames rendered with the wrong theme before MMKV
    hydration completes equals 0
- **Rule valid-token-skips-sign-in:** IF the @better-auth/expo client
    reads a valid non-expired session token from the credential store
    THEN Expo Router navigates directly to the active organization
    dashboard — the count of sign-in screen renders for a user with a
    valid token equals 0
- **Rule expired-token-redirects-to-sign-in:** IF the session token
    in the encrypted credential store has expired or is absent THEN Expo Router
    navigates to the sign-in screen — the rendered route path equals
    the sign-in screen path
- **Rule android-edge-to-edge:** IF the device is running Android
    THEN react-native-edge-to-edge extends app content behind the
    system navigation bar and status bar — the count of pixels between
    the app content edge and the physical screen edge equals 0 on
    Android devices

## Permission Model

| Role | Actions Permitted | Actions Denied | Visibility Constraints |
|------|------------------|----------------|----------------------|
| Authenticated User (valid session token found in the encrypted credential store during the launch authentication check) | Launch the application, view the organization dashboard, interact with all authenticated routes, use all navigation features provided by Expo Router, toggle theme and sidebar preferences persisted in MMKV | No actions are denied to an authenticated user within the mobile application — all features available after authentication are identically accessible regardless of the launch path | The full application UI is visible including the dashboard, settings, navigation drawer, and all organization-scoped screens rendered in the user's device locale and selected theme |
| Unauthenticated User (no valid session token found in the encrypted credential store, or the token has expired or been revoked by the auth server) | Launch the application, view the sign-in screen rendered with the correct locale and theme, authenticate using email OTP or passkey or SSO, view the splash screen during initialization | Cannot access the dashboard or any authenticated routes — the Expo Router route guard redirects all navigation attempts to the sign-in screen until authentication completes and a valid token is written to the encrypted credential store | Only the sign-in screen is visible — authenticated routes and dashboard content are not rendered until the user completes the sign-in flow and a valid session token is stored in the encrypted credential store |
| OS (operating system that launches the Expo runtime process and manages device-level resources including locale, keychain, and system bars) | Start the application process when the user taps the icon, provide the device locale and RTL direction via expo-localization, manage the encrypted keychain used by the Expo credential store, render the system status bar and navigation bar | Cannot modify the application UI rendered by React Native, cannot read the session token stored in the encrypted credential store without device unlock, cannot alter the theme or locale preferences stored in MMKV | The OS renders the system status bar and navigation bar but has no visibility into the application state, authentication status, or user data displayed within the React Native view hierarchy |

## Constraints

- The total time from the user tapping the app icon to the splash
    screen being hidden and the interactive application displayed is
    at most 3000 ms — the count of milliseconds from process start to
    interactive UI equals 3000 or fewer.
- The expo-font Geist typeface loading completes within 1000 ms of
    the font load call starting — the count of milliseconds from font
    load start to font available equals 1000 or fewer.
- The MMKV state hydration of the Zustand theme store and sidebar
    preference store completes within 50 ms of the read call — the
    count of milliseconds from MMKV read start to stores hydrated
    equals 50 or fewer.
- The expo-localization device locale read completes within 100 ms of
    the call — the count of milliseconds from locale read start to
    locale value available equals 100 or fewer.
- The session token read from the Expo encrypted credential store
    completes within 500 ms of the read call — the count of
    milliseconds from credential store read start to token available
    equals 500 or fewer.
- All UI text rendered in the application uses @repo/i18n translation
    keys with zero hardcoded English strings — the count of hardcoded
    user-facing strings in the rendered application equals 0.

## Acceptance Criteria

- [ ] Tapping the app icon displays the branded splash image within 500 ms of the tap — the count of milliseconds from icon tap to splash visible equals 500 or fewer
- [ ] The Geist typeface is loaded before the splash screen is hidden — the count of text elements rendered with the system fallback font after splash hide equals 0 on successful font load
- [ ] The device locale detected by expo-localization matches the locale passed to i18next — the locale code difference between the detected value and the i18next configured value equals 0
- [ ] The RTL text direction from expo-localization is applied to the root layout — the count of layout direction mismatches between the device RTL setting and the rendered root layout direction equals 0
- [ ] The Zustand theme store hydrates from MMKV before the splash is hidden — the count of frames rendered with the default theme when a saved dark theme preference exists equals 0
- [ ] A user with a valid session token in the encrypted credential store is navigated to the dashboard — the count of sign-in screen renders for a user with a valid token equals 0
- [ ] A user with an expired token in the encrypted credential store is navigated to the sign-in screen — the count of dashboard renders before re-authentication equals 0
- [ ] A user with no token in the encrypted credential store is navigated to the sign-in screen — the count of dashboard renders before authentication equals 0
- [ ] On Android, react-native-edge-to-edge extends content behind system bars — the count of pixels between app content edge and physical screen edge equals 0
- [ ] The expo-status-bar icon style matches the active theme — dark theme displays light status bar icons and light theme displays dark status bar icons with zero mismatches
- [ ] The splash screen is hidden only after all initialization completes — the count of initialization tasks still pending when the splash hides equals 0
- [ ] The total launch time from icon tap to interactive UI is at most 3000 ms — the count of milliseconds from process start to app_interactive state equals 3000 or fewer

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The user launches the app while the device is in airplane mode with no network connectivity available | The app completes all local initialization (font loading, locale detection, MMKV hydration) and reads the session token from the encrypted credential store — if the token exists the user sees the dashboard with cached data, if not the user sees the sign-in screen with an offline indicator | The app reaches the interactive state without a network timeout, and the count of crash-level errors during offline launch equals 0 |
| The device locale is set to an RTL language (such as Arabic or Hebrew) that the app has not translated yet | expo-localization detects the RTL locale, i18next falls back to the default English language bundle, but the layout direction is still set to RTL based on the device setting — the user sees English text in an RTL layout | The i18n fallback locale equals "en", the layout direction attribute equals RTL, and the count of layout direction mismatches between the device setting and the rendered UI equals 0 |
| The MMKV storage file is corrupted from a previous force-kill that interrupted a write operation during the last session | react-native-mmkv fails to read the persisted state and the Zustand stores initialize with default values (light theme, sidebar collapsed) — the app continues startup without the user's saved preferences | The app reaches the interactive state with default theme values, the count of uncaught exceptions from MMKV read equals 0, and the MMKV error is logged with the storage file path |
| The Expo encrypted credential store keychain is locked because the user has not unlocked the device with biometrics since a restart | The credential store read returns an error because the keychain requires device unlock — the auth client treats this as no token available and Expo Router navigates to the sign-in screen | The rendered route path equals the sign-in screen path, the count of keychain access errors logged equals 1, and the app does not crash from the keychain access denial |
| The user launches the app immediately after an OS-level force stop that cleared the process from memory | The app performs a full cold start — all initialization tasks run from scratch with no cached runtime state, the splash screen displays during the full initialization cycle, and MMKV and encrypted credential store data persist because they use native storage independent of the process lifecycle | The initialization sequence completes identically to a normal cold start, the count of missing MMKV entries after force stop equals 0, and the credential store token remains accessible |
| The Geist font asset file is missing or corrupted in the application bundle due to a failed build or incomplete download | expo-font rejects the font load promise and the app falls back to the platform default system font (San Francisco on iOS, Roboto on Android) — the splash screen hides after the fallback is applied and the user sees the app with system typography | The count of font load errors logged equals 1, the rendered text uses the system font family, and the app reaches the interactive state without crashing |

## Failure Modes

- **Expo encrypted credential store keychain read fails during session token retrieval**
    - **What happens:** The @better-auth/expo client calls the Expo
        encrypted credential store to read the session token but the
        keychain returns an error because the encrypted storage is
        inaccessible, corrupted, or the device keychain is locked
        after a restart without biometric unlock.
    - **Source:** The user rebooted the device and has not unlocked it
        with biometrics, or the keychain storage was corrupted by a
        failed OS update, or the hardware enclave on the device denied
        access due to a changed policy.
    - **Consequence:** The auth client cannot determine whether the
        user has a valid session and the user is forced to re-authenticate
        even though a valid token existed — the dashboard is not shown
        and the sign-in screen appears instead.
    - **Recovery:** The auth client catches the credential store read
        error and logs the error with the keychain access failure
        reason — Expo Router falls back to navigating the user to
        the sign-in screen, and after authentication a new token is
        written to the credential store for future launches.

- **MMKV native storage read fails during Zustand state hydration**
    - **What happens:** The react-native-mmkv module attempts to read
        the persisted Zustand stores (theme and sidebar preferences)
        but the MMKV file is corrupted, the filesystem denies read
        access, or the storage directory was cleared by the operating
        system storage management process.
    - **Source:** A previous force-kill interrupted an MMKV write
        operation and corrupted the storage file, or the OS reclaimed
        app storage due to low disk space, or a device migration
        transferred the app without its data directory.
    - **Consequence:** The Zustand stores cannot restore the user's
        saved preferences and initialize with default values — a dark
        mode user sees light mode on launch, and the sidebar state
        resets to the default collapsed position.
    - **Recovery:** The MMKV read operation catches the storage error
        and the Zustand stores fall back to default initial values
        (light theme, sidebar collapsed) — the runtime logs the MMKV
        corruption error with the file path, and the next user
        preference change retries writing to re-create the storage.

- **Expo-font fails to load the Geist typeface from bundled assets**
    - **What happens:** The expo-font load call rejects because the
        Geist font asset file is missing from the bundle, is corrupted,
        or the native font registration API returns an error on the
        target platform version.
    - **Source:** An incomplete application build excluded the font
        asset from the bundle, a partial OTA update delivered a
        corrupted asset, or the device is running an OS version that
        rejects the font file format.
    - **Consequence:** The first rendered screen uses the platform
        default system font (San Francisco on iOS, Roboto on Android)
        instead of Geist — the typography does not match the design
        system and text metrics differ from the intended layout.
    - **Recovery:** The expo-font module catches the load rejection
        and the app falls back to the platform system font — the
        runtime logs the font load failure with the asset path and
        error details, and the splash screen proceeds to hide after
        the fallback font is applied so the user is not blocked.

- **i18next namespace loading fails during locale initialization**
    - **What happens:** The @repo/i18n infrastructure attempts to load
        the language namespace matching the detected device locale but
        the namespace file is missing, corrupted, or the locale code
        does not match any available translation bundle.
    - **Source:** The detected locale is a regional variant (such as
        "fr-CA") that has no dedicated translation bundle, or the
        translation namespace file was excluded from the application
        bundle during a build optimization step.
    - **Consequence:** The UI renders raw translation keys (such as
        "common.signIn" or "dashboard.title") instead of localized
        human-readable strings — the application is functional but the
        text content is unintelligible to the user.
    - **Recovery:** The i18n infrastructure catches the namespace load
        error and falls back to the default English locale bundle —
        the runtime logs the missing namespace with the requested
        locale code, and retries loading the correct namespace on the
        next navigation event.

## Declared Omissions

- This specification does not define the specific sign-in flows
    (email OTP, passkey, or SSO) available on the sign-in screen —
    those authentication methods are documented in their respective
    behavioral specifications (user-signs-in-with-email-otp,
    user-signs-in-with-passkey, user-signs-in-with-sso).
- This specification does not cover the push notification
    registration or token refresh that occurs after the app reaches
    the interactive state — push notification setup and permission
    prompts are defined in a separate notification spec.
- This specification does not address OTA update checks that Expo
    performs after the app launches — the update download, staging,
    and restart behavior are covered by a separate OTA update spec.
- This specification does not define the visual theme switching
    mechanism or the theme store schema — the theme selection logic
    and persistence format are defined in the user-changes-theme
    behavioral specification.
- This specification does not cover crash reporting or telemetry
    collection that occurs when the Expo runtime encounters an
    unrecoverable error — crash reporting integration and data
    collection consent are covered by a separate observability spec.

## Related Specifications

- [user-changes-theme](user-changes-theme.md) — Defines the theme
    switching mechanism including the MMKV-backed Zustand persistence
    that determines which theme the mobile app restores during the
    launch state hydration phase described in this specification
- [session-lifecycle](session-lifecycle.md) — Defines the full
    authentication session lifecycle including token creation,
    validation, expiration, and revocation that determines whether the
    mobile app user is authenticated on launch or redirected to the
    sign-in screen
- [user-signs-in-with-email-otp](user-signs-in-with-email-otp.md) —
    Defines the email OTP sign-in flow that unauthenticated mobile
    app users follow when no valid session token exists in
    the encrypted credential store and the sign-in screen is rendered
- [user-navigates-the-dashboard](user-navigates-the-dashboard.md) —
    Defines the dashboard shell and navigation structure that the
    authenticated mobile app user sees after the session token is
    validated and Expo Router navigates to the dashboard route
- [user-changes-language](user-changes-language.md) — Defines the
    language change flow that interacts with the @repo/i18n
    infrastructure initialized during the mobile app launch locale
    detection phase described in this specification

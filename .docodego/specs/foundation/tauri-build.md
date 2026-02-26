---
id: SPEC-2026-012
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](../ROADMAP.md)

# Tauri Build

## Intent

This spec defines the Tauri 2 desktop application configuration for the DoCodeGo boilerplate, covering the Rust backend setup, IPC commands, plugin configuration, system tray behavior, deep link registration, and platform-specific build targets. The desktop app is a thin Rust shell wrapping the `apps/web` frontend in a native webview — it contains 0 TypeScript application code and 0 React components of its own. Authentication works via cookies natively in the Tauri webview, and i18n is fully inherited from the web app. This spec ensures that the Tauri configuration produces correct native binaries for Windows, macOS, and Linux with all plugins functional and the system tray operational.

## Integration Map

| System | Interaction Type | When Called | What Happens If Unavailable |
|--------|-----------------|-------------|------------------------------|
| `apps/web` build output | read | Tauri loads `frontendDist` at app startup and `devUrl` during development | The webview displays a connection error page because no frontend content is available to render |
| `@tauri-apps/cli` | build tool | `tauri dev` and `tauri build` commands invoked by the developer or CI | Build fails at compile time with a missing dependency error and CI alerts to block the release |
| `@tauri-apps/api` | read | Web app calls IPC commands via `window.__TAURI__` at runtime | Feature detection returns false and the web app falls back to browser-only behavior without calling Tauri APIs |
| Tauri updater endpoint | read | App startup check for new versions via the configured endpoint URL | The updater plugin times out after 10 seconds and falls back to the current version without blocking app launch |
| OS deep-link registry | write | App installation registers the `docodego://` URL scheme with the operating system | Deep links do not route to the app and the user falls back to a manual URL input dialog for invitation and SSO callback links |

## Behavioral Flow

1. **[Developer]** runs `pnpm dev` at the monorepo root, which starts the web dev server before the Tauri process via Turborepo task dependency chain
2. **[Tauri CLI]** launches the Rust backend process and opens a native webview window pointed at the configured `devUrl` (the web dev server URL)
3. **[Tauri runtime]** initializes 5 plugins in the builder chain: `opener`, `updater`, `notification`, `deep-link`, and `window-state`
4. **[Tauri runtime]** creates the system tray icon with a context menu containing "Show/Hide" and "Quit" menu items
5. **[User]** interacts with the web app rendered inside the native webview — all routing, auth cookies, and i18n are handled by the web app without Tauri involvement
6. **[User]** left-clicks the system tray icon, and the tray event handler toggles window visibility by calling `show` or `hide` based on the current visibility state
7. **[User]** selects "Quit" from the tray context menu, which triggers the `quit_app` IPC command that closes the window, removes the tray icon, and exits the process with code 0
8. **[OS]** receives a `docodego://` deep link request, and the deep-link plugin routes the URL to the running Tauri app instance for the web app to handle

## State Machine

No stateful entities. The desktop app is a thin shell with no lifecycle entities of its own — window state persistence is delegated to the `window-state` plugin, and all application state lives in the web frontend.

## Business Rules

No conditional business rules. The Tauri configuration is declarative and all plugin behavior is unconditional — no branching logic exists in the Rust backend beyond feature detection gating for `#[cfg(desktop)]`.

## Permission Model

Single role; no permission model needed. All users of the desktop app have identical capabilities — there is no multi-user access control within the Tauri shell, and all authorization is handled by the web app and API server.

## Acceptance Criteria

- [ ] The `apps/desktop/src-tauri/` directory is present and contains `Cargo.toml`, `tauri.conf.json`, and a `src/` directory with at least 1 Rust source file
- [ ] The `Cargo.toml` lists `tauri` as a dependency with the `tray-icon` feature enabled — both the dependency and the feature flag are present
- [ ] The `Cargo.toml` lists `serde` and `serde_json` as dependencies — both are present for IPC serialization
- [ ] The `tauri.conf.json` sets the `devUrl` to the `apps/web` dev server URL and the `frontendDist` to the web build output path — both values are present and non-empty
- [ ] Exactly 5 Tauri plugins are configured: `opener`, `updater`, `notification`, `deep-link`, and `window-state` — all 5 are present in both `Cargo.toml` dependencies and `tauri.conf.json` plugin configuration
- [ ] Exactly 3 IPC commands are defined in the Rust source: `show_window`, `quit_app`, and `get_app_version` — all 3 are present as `#[tauri::command]` functions
- [ ] The `show_window` command calls `show` and `set_focus` methods to bring the window to the foreground — both calls are present in the function body
- [ ] The `quit_app` command closes the window, removes the tray icon, and exits the process — all 3 actions are present in the function body
- [ ] The `get_app_version` command returns the version string from `Cargo.toml` — the return type is `String` and the value is non-empty
- [ ] A system tray is configured with a context menu containing at least 2 items: "Show/Hide" (toggles window visibility) and "Quit" (exits the app) — both menu items are present
- [ ] Left-clicking the tray icon toggles window visibility — the tray event handler is present and calls `show` or `hide` based on the current visibility state
- [ ] The deep-link plugin registers the `docodego://` URL scheme — this scheme is present in the plugin configuration
- [ ] The window-state plugin is enabled to persist window size and position across restarts — the plugin is present in the builder chain
- [ ] The updater plugin is configured with an endpoint URL — the `endpoints` array contains at least 1 URL entry that is present and non-empty
- [ ] Running `tauri build` from `apps/desktop` produces platform-specific binaries and exits with code = 0
- [ ] The close button (X) on the window quits the application — minimize-to-tray behavior is absent, and the `on_window_event` handler calls `app.exit(0)` on close

## Constraints

- The desktop app contains 0 TypeScript source files and 0 React components — all application code is in Rust (`src-tauri/src/`) and configuration files. The count of `.ts` or `.tsx` files inside `apps/desktop/src-tauri/` equals 0. The frontend is served entirely from `apps/web` build output.
- The `@tauri-apps/cli` and `@tauri-apps/api` packages are installed via the pnpm catalog — both catalog entries are present in `pnpm-workspace.yaml` with version `^2`.
- Feature detection for Tauri APIs in the web app uses `window.__TAURI__` — the web code checks for this global before calling any Tauri IPC command, and the count of unconditional Tauri API calls in `apps/web` equals 0.
- The updater plugin is gated behind `#[cfg(desktop)]` in Rust — it is only compiled for desktop targets. The notification and deep-link plugins follow the same pattern, ensuring 0 compilation errors when building for non-desktop targets.

## Edge Cases

| Scenario | Expected Behavior | Test Signal |
|----------|------------------|-------------|
| The web dev server at `devUrl` is not running when a developer launches `tauri dev` from the terminal | Tauri logs a warning to the terminal identifying the unreachable `devUrl` and the webview displays a connection error page instead of crashing the process | The Tauri process remains running with exit code != 0 only after explicit quit, and the terminal output contains the expected URL string |
| The user's system has another application already registered for the `docodego://` URL scheme causing a conflict | On macOS the bundled `Info.plist` registration takes priority; on Windows and Linux the app logs a warning and falls back to displaying a manual URL input dialog for invitation and SSO callback links | The app launches without crashing and deep link routing either succeeds or the manual input dialog is displayed |
| The updater endpoint URL returns a non-200 HTTP status or a network timeout occurs during the version check on launch | The updater plugin times out after 10 seconds and falls back to running the current installed version without blocking app startup or displaying an error to the user | The app launches within 15 seconds regardless of endpoint availability and the Tauri log file contains the connection error |
| The `window-state` plugin encounters a corrupted or missing state file from a previous session on disk | The plugin falls back to the default window size and position defined in `tauri.conf.json` without crashing the application or showing an error dialog | The app window opens at the default dimensions and the corrupted state file is overwritten on next close |
| The user clicks the close button (X) on the window while expecting minimize-to-tray behavior | The `on_window_event` handler calls `app.exit(0)` and the application quits immediately instead of minimizing — minimize-to-tray is explicitly absent from this configuration | The process exits with code 0 and no tray icon remains after window close |

## Failure Modes

- **Web dev server not running during development**
    - **What happens:** A developer runs `tauri dev` before starting the web dev server, causing the webview to display a connection error instead of the application because `devUrl` is unreachable.
    - **Source:** Incorrect manual startup order when not using the root `pnpm dev` command that handles dependency ordering via Turborepo.
    - **Consequence:** The developer sees a blank or error page in the native window and cannot interact with the application until the web server is started.
    - **Recovery:** The Turborepo `dev` task dependency chain ensures that running `pnpm dev` at the root starts the web server before the Tauri process, and Tauri logs a warning with the expected URL — the developer falls back to restarting with the correct command.
- **Missing system dependency on Linux CI runner**
    - **What happens:** The Tauri build fails on Linux CI because a required system library such as `libwebkit2gtk-4.1-dev` is not installed on the runner, causing the Rust linker to fail.
    - **Source:** CI runner image does not include the full set of WebKit and GTK development headers required by the Tauri Rust compilation process.
    - **Consequence:** The CI build returns a non-zero exit code and no Linux binary is produced, blocking the release pipeline for that platform.
    - **Recovery:** The CI workflow includes an explicit `apt-get install` step that installs all required Linux dependencies before the build, and if a dependency is missing the linker diagnostic alerts with the specific library name so the developer can update the CI config.
- **Deep link scheme conflict with another application**
    - **What happens:** Another application on the user's system has already registered the `docodego://` URL scheme, causing deep link routing to fail silently because the OS routes the link to the wrong application.
    - **Source:** A previously installed application or a duplicate installation registered the same custom URL scheme in the OS registry.
    - **Consequence:** Invitation links and SSO callback URLs using the `docodego://` scheme do not open in the correct application, breaking the authentication flow.
    - **Recovery:** On macOS the bundled `Info.plist` registration takes priority for the app; on Windows and Linux the app logs a warning if the scheme is already registered and falls back to displaying a manual URL input dialog for the affected links.
- **Updater endpoint unreachable at app launch**
    - **What happens:** The auto-updater plugin cannot reach the update server on launch due to network issues or a misconfigured endpoint URL in the plugin configuration.
    - **Source:** Network connectivity failure, DNS resolution error, or an incorrect URL in the `endpoints` array of the updater plugin configuration.
    - **Consequence:** The app cannot check for or download new versions, leaving the user on an outdated release until the next successful update check.
    - **Recovery:** The updater plugin uses a timeout of 10 seconds and falls back to the current version silently without blocking app startup, logging the connection error to the Tauri log file for diagnosis.

## Declared Omissions

- Tauri webview behavior differences from standard browsers are not covered here and are defined in desktop behavioral specs that address rendering quirks and API availability
- Desktop auto-update flow, version comparison logic, and user prompts for installing updates are not covered here and are defined in `desktop-auto-updates.md`
- System tray interactions, menu item UX design, and tray icon visual states are not covered here and are defined in `user-uses-system-tray.md`
- Deep link routing from the OS to TanStack Router path matching is not covered here and are defined in `user-opens-a-deep-link.md`
- CI/CD matrix build workflow, platform-specific signing, and artifact publishing are not covered here and are defined in `ci-cd-pipelines.md`

## Related Specifications

- [ci-cd-pipelines](ci-cd-pipelines.md) — CI/CD matrix build workflow, platform-specific signing, and artifact publishing for Windows, macOS, and Linux desktop binaries
- [shared-i18n](shared-i18n.md) — Internationalization infrastructure providing locale resolution and translation functions inherited by the desktop app via the web frontend
- [auth-server-config](auth-server-config.md) — Better Auth server configuration for cookie-based authentication that works natively in the Tauri webview without extra setup
- [api-framework](api-framework.md) — Hono API framework and CORS configuration that the desktop webview communicates with for all backend operations

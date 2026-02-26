[← Back to Roadmap](../ROADMAP.md)

# Tauri Build

## Intent

This spec defines the Tauri 2 desktop application configuration for the DoCodeGo boilerplate, covering the Rust backend setup, IPC commands, plugin configuration, system tray behavior, deep link registration, and platform-specific build targets. The desktop app is a thin Rust shell wrapping the `apps/web` frontend in a native webview — it contains 0 TypeScript application code and 0 React components of its own. Authentication works via cookies natively in the Tauri webview, and i18n is fully inherited from the web app. This spec ensures that the Tauri configuration produces correct native binaries for Windows, macOS, and Linux with all plugins functional and the system tray operational.

## Acceptance Criteria

- [ ] The `apps/desktop/src-tauri/` directory is present and contains `Cargo.toml`, `tauri.conf.json`, and a `src/` directory with at least 1 Rust source file
- [ ] The `Cargo.toml` lists `tauri` as a dependency with the `tray-icon` feature enabled — both the dependency and the feature flag are present
- [ ] The `Cargo.toml` lists `serde` and `serde_json` as dependencies — both are present for IPC serialization
- [ ] The `tauri.conf.json` sets the `devUrl` to the `apps/web` dev server URL and the `frontendDist` to the web build output path — both values are present and non-empty
- [ ] Exactly 5 Tauri plugins are configured: `opener`, `updater`, `notification`, `deep-link`, and `window-state` — all 5 are present in both `Cargo.toml` dependencies and `tauri.conf.json` plugin configuration
- [ ] Exactly 3 IPC commands are defined in the Rust source: `show_window`, `quit_app`, and `get_app_version` — all 3 are present as `#[tauri::command]` functions
- [ ] The `show_window` command brings the window to the foreground — it calls `show` and `set_focus` methods, and both calls are present in the function body
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

## Failure Modes

- **Web dev server not running**: A developer runs `tauri dev` before starting the web dev server, causing the webview to display a connection error instead of the application. The Tauri dev process detects that the `devUrl` is unreachable and logs a warning to the terminal with the expected URL, prompting the developer to start `pnpm --filter web dev` first. The Turborepo `dev` task dependency chain ensures that running `pnpm dev` at the root starts the web server before the Tauri process.
- **Missing system dependency on Linux**: The Tauri build fails on Linux CI because a required system library (e.g., `libwebkit2gtk-4.1-dev`) is not installed on the runner. The CI workflow includes an explicit `apt-get install` step that installs all required Linux dependencies before the build, and if a dependency is missing, the build returns error with the specific linker diagnostic identifying the missing library name.
- **Deep link scheme conflict**: Another application on the user's system has already registered the `docodego://` scheme, causing deep link routing to fail silently on that machine. On macOS, the `Info.plist` registration takes priority for the bundled app. On Windows and Linux, runtime registration logs a warning if the scheme is already registered by another process, and the application falls back to displaying a manual URL input dialog for invitation and SSO callback links.
- **Updater endpoint unreachable**: The auto-updater plugin cannot reach the update server on launch, either due to network issues or a misconfigured endpoint URL. The updater plugin uses a timeout of 10 seconds and falls back to the current version silently without blocking app startup, logging the connection error to the Tauri log file for the developer to diagnose.

## Declared Omissions

- Tauri webview behavior differences from standard browsers (covered by desktop behavioral specs)
- Desktop auto-update flow and user prompts (covered by `desktop-auto-updates.md`)
- System tray interactions and UX (covered by `user-uses-system-tray.md`)
- Deep link routing to TanStack Router (covered by `user-opens-a-deep-link.md`)
- CI/CD matrix build workflow (covered by `ci-cd-pipelines.md`)

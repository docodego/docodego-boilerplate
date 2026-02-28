# Tech Stack — docodego-boilerplate

---

## 1. Core Platform

| Technology | Version | Reasoning |
|---|---|---|
| **TypeScript** | ^5.9.3 | Strict-mode TS everywhere — type safety across all 5 platform targets. ES2024 target with `verbatimModuleSyntax` for native ESM. |
| **Node.js (ESM)** | ES2024 | All packages use `"type": "module"`. Modern ESM-first approach eliminates CJS/ESM interop headaches. |

---

## 2. Monorepo & Package Management

| Technology | Version | Used In | Reasoning |
|---|---|---|---|
| **pnpm** | 10.29.2 | Root | Strict dependency isolation via `node_modules/.pnpm`, workspace protocol (`workspace:*`), and **catalog** feature for centralized version management in `pnpm-workspace.yaml`. Fastest install times among Node package managers. |
| **pnpm Workspace Catalog** | — | `pnpm-workspace.yaml` | Single source of truth for shared dependency versions. Packages reference `"catalog:"` instead of hardcoding versions — eliminates version drift across workspaces. |
| **Turborepo** | ^2.8.0 | Root | Orchestrates `build`, `dev`, `typecheck`, `test`, `typegen`, and `storybook` tasks across workspaces. Topological dependency ordering (`dependsOn: ["^build"]`), remote caching, and the new TUI (`"ui": "tui"`). Chosen over Nx for simplicity and zero-config caching. |

### Workspace Structure

```
apps/
  web/          → Astro 5 + React 19 (SSG landing + SPA dashboard)
  api/          → Hono 4 on Cloudflare Workers
  mobile/       → Expo 54 + React Native
  desktop/      → Tauri 2 wrapping web
  browser-ext/  → WXT + React 19

packages/
  library/      → Shared validators, constants, utils
  contracts/    → oRPC contracts (shared API types)
  ui/           → Shadcn component library
  i18n/         → i18next infrastructure

e2e/            → Playwright E2E tests
```

---

## 3. Frontend — Web (`apps/web`)

| Technology | Version | Reasoning |
|---|---|---|
| **Astro** | ^5.17.0 | Static-first framework — SSG for marketing/landing pages, with React islands for interactive sections. Zero JS by default keeps landing pages fast. |
| **React** | ^19.2.0 | UI library for interactive SPA dashboard at `/app/*`. React 19 brings Server Components support and the new React Compiler. |
| **React Compiler** | latest (`babel-plugin-react-compiler`) | Automatic memoization — eliminates manual `useMemo`/`useCallback`. Configured as a Babel plugin in Astro's React integration. |
| **TanStack Router** | ^1.162.0 | File-based, fully type-safe routing for the SPA portion. Auto code-splitting enabled via Vite plugin. Generates `routeTree.gen.ts` at build time. Chosen over React Router for end-to-end type safety. |
| **TanStack Query** | ^5.90.0 | Async state management with caching, deduplication, and background refetching. Paired with oRPC for type-safe data fetching. Devtools included in dev. |
| **Zustand** | ^5.0.0 | Lightweight client state management. Minimal API surface vs Redux; no boilerplate. Used for UI state: **theme store** (light/dark/system with localStorage persistence) and **sidebar store**. |
| **Motion** (Framer Motion) | ^12.34.0 | Animation library for UI transitions and micro-interactions. Declarative API with React integration. |
| **Tailwind CSS** | ^4.2.0 | Utility-first CSS with v4's new engine (Oxide). Integrated via PostCSS (`@tailwindcss/postcss`). Logical properties enforced for RTL support. |
| **Lucide React** | ^0.575.0 | Icon library — tree-shakeable SVG icons. Lighter alternative to FontAwesome with consistent design. |
| **Vite** | (via Astro) | Underlying build tool. Astro uses Vite internally. `vite-tsconfig-paths` plugin resolves TS path aliases. |
| **PostCSS** | latest | CSS processing pipeline — solely hosts the `@tailwindcss/postcss` plugin. |

---

## 4. Backend — API (`apps/api`)

| Technology | Version | Reasoning |
|---|---|---|
| **Hono** | ^4.12.2 | Ultra-lightweight web framework designed for edge runtimes. Perfect fit for Cloudflare Workers — tiny bundle size, fast cold starts, Express-like DX. Middleware stack includes CORS, request logging, locale/i18n detection, and structured error handling. |
| **Cloudflare Workers** | via Wrangler ^4.68.0 | Edge compute platform. Serverless, globally distributed, with D1 and R2 bindings. Zero infrastructure management. `nodejs_compat` flag enabled for Node.js API compatibility. |
| **Cloudflare D1** | (Wrangler binding) | SQLite-based serverless database on Cloudflare's edge. Zero-latency reads at the edge. Used as the primary database with Drizzle ORM. |
| **Cloudflare R2** | (Wrangler binding) | S3-compatible object storage. Used for file/asset storage (`STORAGE` binding). Zero egress fees. |
| **Drizzle ORM** | ^0.45.1 | Type-safe SQL ORM with zero runtime overhead. SQLite dialect for D1. Schema-first approach with migration generation via `drizzle-kit`. Chosen over Prisma for edge compatibility and smaller bundle. |
| **Drizzle Kit** | ^0.31.9 | Migration toolkit for Drizzle — generates SQL migrations from schema diffs, provides a database studio UI. |
| **oRPC (server)** | ^1.13.5 | Type-safe RPC framework — server-side router + OpenAPI generation. Contracts shared with frontend via `@repo/contracts`. Chosen over tRPC for OpenAPI-first design and contract separation. |
| **Scalar Hono API Reference** | ^0.9.44 | Auto-generated API documentation from OpenAPI spec. Integrated as Hono middleware for interactive API explorer. |
| **Better Auth** | ^1.4.19 | Full-featured auth library with multiple plugins: **Passkey** (`@better-auth/passkey`) for WebAuthn, **SSO** (`@better-auth/sso`), **Email OTP**, **Organization & Teams** (multi-tenancy), **Admin impersonation**, **Anonymous** (guest sessions promotable to full accounts), and **DodoPayments** (`@dodopayments/better-auth`) for payment/subscription integration. Framework-agnostic, works on edge runtimes. Cookie-based sessions with device tracking (IP, userAgent). |
| **tsx** | ^4.21.0 | TypeScript execution for scripts (e.g., `db:seed`). Fast, zero-config TS runner. |
| **@faker-js/faker** | ^10.3.0 | Generates realistic seed data for development. Used in `scripts/seed.ts`. |
| **@libsql/client** | ^0.15.8 | LibSQL client for local D1 development. Provides SQLite-compatible driver for Drizzle's local dev mode. |

---

## 5. Shared Packages

### `packages/contracts` — API Contracts

| Technology | Version | Reasoning |
|---|---|---|
| **@orpc/contract** | catalog (^1.13.0) | Defines typed RPC contracts shared between `apps/api` (server) and `apps/web` (client). Single source of truth for API types — changes are caught at compile time across both apps. |
| **Zod** | catalog (^4.0.0) | Runtime schema validation. Zod v4 with smaller bundle. Used in contracts for input/output validation that works both client-side and server-side. |

### `packages/ui` — Component Library

| Technology | Version | Reasoning |
|---|---|---|
| **Shadcn UI** (`base-vega` style) | N/A (code-gen) | Copy-paste component library — components are owned, not imported from `node_modules`. Uses `base-vega` variant which builds on Base UI instead of Radix. 17+ components: Button, Card, Dialog, Drawer, Dropdown Menu, Input, Label, Popover, Select, Separator, Table, Tabs, Textarea, Tooltip, Badge, Toaster. Includes `DirectionProvider` for RTL and dark mode support. |
| **@base-ui/react** | ^1.2.0 | Unstyled, accessible React primitives from MUI. Foundation for Shadcn `base-vega` components. Chosen over Radix for the Shadcn variant used. |
| **Class Variance Authority (CVA)** | ^0.7.0 | Type-safe variant management for components. Creates variant maps (e.g., `size: "sm" | "md" | "lg"`) with full TS inference. |
| **clsx** | ^2.1.1 | Conditional className builder. Tiny utility (~228B) for composing CSS classes. |
| **tailwind-merge** | ^3.5.0 | Intelligently merges Tailwind classes — resolves conflicts (e.g., `p-2 p-4` → `p-4`). Used in the `cn()` utility alongside `clsx`. |
| **Sonner** | ^2.0.7 | Toast notification library. Minimal API, accessible, styled with Tailwind. |
| **tw-animate-css** | ^1.4.0 | Tailwind CSS animation utilities. Extends default Tailwind animations for Shadcn component transitions. |
| **@fontsource-variable/geist** | ^5.2.8 | Self-hosted Geist font (Vercel's typeface). Variable font for optimal loading — no external font requests. |

### `packages/i18n` — Internationalization

| Technology | Version | Reasoning |
|---|---|---|
| **i18next** | catalog (^25.8.0) | Industry-standard i18n framework. Core package has zero React dependency — the `@repo/i18n` package separates core from React bindings. Ships with **English (en)** and **Arabic (ar)** locales across 5 namespaces: common, auth, dashboard, email, extension. Built-in RTL detection for ar/he/fa/ur. |
| **react-i18next** | catalog (^16.5.0) | React bindings for i18next. Exported from `@repo/i18n/react` subpath to keep the core import React-free (important for non-React consumers like the API). |
| **i18next-resources-to-backend** | latest | Lazy-loads translation files as async resources. Keeps initial bundle small by loading translations on demand. |

### `packages/library` — Shared Utilities

| Technology | Version | Reasoning |
|---|---|---|
| **Zod** | catalog (^4.0.0) | Shared validators and schemas used across all apps. Single validation layer for forms, API inputs, and type inference. |

---

## 6. Frontend Data Layer

| Technology | Version | Used In | Reasoning |
|---|---|---|---|
| **@orpc/client** | catalog (^1.13.0) | `apps/web` | Type-safe RPC client that consumes `@repo/contracts`. End-to-end type safety from API to UI. |
| **@orpc/openapi-client** | catalog (^1.13.0) | `apps/web` | OpenAPI-based HTTP client for oRPC. Enables standard REST calls with full type inference from contracts. |
| **@orpc/tanstack-query** | catalog (^1.13.0) | `apps/web` | Bridges oRPC with TanStack Query — auto-generates query keys and typed hooks from contracts. Eliminates manual query key management. |

---

## 7. Testing

| Technology | Version | Used In | Reasoning |
|---|---|---|---|
| **Vitest** | ^4.0.0 | All workspaces (except mobile) | Vite-native test runner — shares the same transform pipeline as the build. Workspace-aware via `projects: ["apps/*", "packages/*"]` in root config. Faster than Jest with native ESM support. |
| **@vitest/browser-playwright** | latest | `apps/web` | Browser-based component testing using Playwright. Tests run in real browsers instead of JSDOM for higher fidelity. |
| **Playwright** | (via e2e/) | `e2e/` | E2E testing across browsers (Chromium, Firefox, WebKit). Industry standard for cross-browser automation. |

Mobile uses Maestro for E2E testing — see section 10.

---

## 8. Code Quality & Linting

| Technology | Version | Reasoning |
|---|---|---|
| **Biome** | ^2.4.0 | All-in-one linter + formatter replacing ESLint + Prettier. Written in Rust — orders of magnitude faster. Handles JS/TS/JSON/CSS. Configured with recommended rules, import sorting, and Tailwind directive support. |
| **Knip** | ^5.84.0 | Dead code and unused dependency detector. Runs with `--cache` for performance. Workspace-aware configuration in `knip.json`. Catches unused exports, files, and dependencies before they accumulate. |
| **Commitlint** | ^20.4.0 (`@commitlint/cli` + `@commitlint/config-conventional`) | Enforces Conventional Commits format. Custom type/scope enums matching the workspace structure. Runs on `commit-msg` hook. |
| **Lefthook** | ^2.1.0 | Git hooks manager written in Go — fast and zero-dependency. Runs commitlint on `commit-msg`, quality gate on `pre-push`, and `pnpm install` on `post-merge`. Chosen over Husky for speed and cross-platform support. |

---

## 9. Editor & DX

| Technology | Config | Reasoning |
|---|---|---|
| **VS Code** | `.vscode/settings.json` | Configured as the recommended editor. Biome set as default formatter for TS/JS/JSON/CSS with format-on-save. Tab size 4 spaces. Auto-fix on save. |
| **Storybook** | ^10 | Component development environment. Addons: `@storybook/react-vite` (Vite-native framework), `@storybook/addon-essentials` (controls, actions, viewport, docs), `@storybook/addon-a11y` (accessibility testing), `@storybook/addon-vitest` (run stories as Vitest tests). Story globs cover `packages/ui` + `apps/web` + `apps/browser-extension`. |
| **Changesets** | latest | Release automation (opt-in). Manages versioning and changelog generation for publishable packages. |

---

## 10. Mobile — `apps/mobile`

### Core

| Technology | Version | Reasoning |
|---|---|---|
| **Expo** | ^54 | Managed React Native workflow — simplifies native builds, OTA updates, and config plugins. Wraps React Native with a batteries-included SDK. |
| **React Native** | ^0.81 | Cross-platform mobile using the same React component model as the web app. Shares `@repo/contracts`, `@repo/library`, `@repo/i18n`. |
| **EAS (Expo Application Services)** | — | Cloud build profiles for iOS/Android: `development` (simulator), `development:device`, `preview` (internal distribution), `production` (app store). Replaces local Xcode/Gradle builds. |
| **Expo Dev Client** | latest | Custom development client beyond Expo Go — required for native modules like MMKV. Enables full native debugging. |
| **Metro Bundler** | (via Expo) | React Native's bundler. Requires platform-specific extension config (`.ios.ts`, `.android.ts`) and CJS compatibility for certain native packages. |

### Navigation

| Technology | Version | Reasoning |
|---|---|---|
| **Expo Router** | ^6 | File-based routing for React Native — chosen for consistency with TanStack Router on web. Provides automatic deep linking and typed routes. Chosen over React Navigation for file-based convention parity. |

### Auth

| Technology | Version | Reasoning |
|---|---|---|
| **@better-auth/expo** | latest | Mobile auth client with secure store integration. Handles session persistence via `expo-secure-store`. |
| **expo-secure-store** | latest | Encrypted credential storage on device. Used by Better Auth's Expo client for secure token persistence. |

Note: Passkey not included on mobile (WebAuthn RN support limited).
Auth plugins: `expoClient()`, `emailOTPClient()`, `organizationClient()`, `ssoClient()`.

### Mobile-Specific Libraries

| Technology | Version | Reasoning |
|---|---|---|
| **react-native-mmkv** | ^3 | High-performance key-value storage (10x faster than AsyncStorage). Pairs with Zustand persistence — mobile equivalent of `localStorage` used by web's theme/sidebar stores. |
| **react-native-reanimated** | ^4 | Performant UI-thread animations. Required by many navigation transitions and gesture-driven interactions. |
| **react-native-gesture-handler** | latest | Gesture recognition — swipes, pans, long-press. Foundation for navigation gestures and interactive UI. |
| **react-native-safe-area-context** | latest | Safe area insets for notches, status bars, and home indicators. Required by virtually all RN layouts. |
| **react-native-keyboard-controller** | latest | Keyboard-aware layouts — handles keyboard show/hide animations and input focus management. |
| **react-native-edge-to-edge** | latest | Modern edge-to-edge display on Android. Extends content behind system bars. |
| **expo-localization** | latest | Native locale and RTL detection. Complements `@repo/i18n` by providing device-level locale that feeds into i18next initialization. |
| **expo-status-bar** | latest | Status bar styling (light/dark/auto) per screen. |
| **expo-splash-screen** | latest | Splash screen management — controls visibility during app initialization. |
| **expo-font** | latest | Custom font loading. Ensures fonts are ready before first render. |

### Mobile Testing

| Technology | Version | Reasoning |
|---|---|---|
| **Maestro** | latest | YAML-based mobile E2E testing framework. Mobile equivalent of Playwright — simpler than Detox/Appium, tests run on simulators and real devices. |

---

## 11. Desktop — `apps/desktop`

Thin Tauri 2 shell around `apps/web`. Zero React code, zero TypeScript
application code — only Rust (`src-tauri/src/`) and config files. Auth
works via cookies natively in the Tauri webview. i18n fully inherited
from web.

### Core

| Technology | Version | Reasoning |
|---|---|---|
| **Tauri** | ^2 | Desktop app framework with Rust backend + webview frontend. Much smaller binaries than Electron (~10MB vs ~150MB). Compiles to native code per OS. |
| **@tauri-apps/cli** | ^2 (catalog) | CLI for `tauri dev` (launches native window) and `tauri build` (produces distributable binary). |
| **@tauri-apps/api** | ^2 (catalog) | JS bridge to Tauri APIs — IPC calls from web to Rust. Used in `apps/web` behind `window.__TAURI__` feature detection. |

### Tauri Plugins (Rust crates)

| Plugin | Version | Reasoning |
|---|---|---|
| **tauri-plugin-opener** | 2 | Opens URLs in default browser — OAuth redirects, external links. Replaces Tauri 1's `shell.open`. |
| **tauri-plugin-updater** | 2 | Auto-update from release server. Checks on launch, optional user-initiated restart. `#[cfg(desktop)]` gated. |
| **tauri-plugin-notification** | 2 | OS-native notifications callable from web code via `@tauri-apps/api`. |
| **tauri-plugin-deep-link** | 2 | Custom URL scheme (`docodego://`). Routes forwarded to TanStack Router. Runtime registration on Linux/Windows, `Info.plist` on macOS. |
| **tauri-plugin-window-state** | 2 | Remembers window size and position across restarts. Uses builder pattern. |

### Rust Dependencies

| Crate | Version | Reasoning |
|---|---|---|
| **tauri** | 2 (with `tray-icon` feature) | Core framework — webview, window management, event system, system tray API. |
| **tauri-build** | 2 | Build script for Tauri compilation. |
| **serde + serde_json** | 1 | Rust serialization for IPC command arguments and return values. |

### IPC Commands (3 total)

| Command | Purpose |
|---|---|
| `show_window` | Brings window to foreground (tray click, deep link activation) |
| `quit_app` | Clean shutdown — closes window, removes tray, exits process |
| `get_app_version` | Returns version string for display in settings/about |

### System Tray

- Context menu: Show/Hide (toggles visibility), Quit (exits app)
- Left-click on tray icon toggles window visibility
- Close button (X) quits the app — no minimize-to-tray

### Build Targets

| OS | Formats |
|---|---|
| Windows | `.msi` + `.exe` |
| macOS | `.dmg` + `.app` |
| Linux | `.AppImage` + `.deb` |

---

## 12. Browser Extension — `apps/browser-extension`

### Core

| Technology | Version | Reasoning |
|---|---|---|
| **WXT** | latest | Extension framework — file-based entrypoints, auto Manifest V3 generation, multi-browser support, full HMR. Chosen over CRXJS (unmaintained since 2023) and manual Vite. |
| **@wxt-dev/module-react** | latest | React integration for WXT. Enables React components in popup and other extension pages. |
| **React** | ^19.2 (catalog) | UI framework for the popup. Same version as web — components from `@repo/ui` work directly. |
| **oRPC client** | latest | Type-safe API client — same as web, consumes `@repo/contracts`. |
| **Better Auth client** | ^1.4 | Auth via token relay through background service worker (extensions can't use cookies directly). |

### Entrypoints

| Entrypoint | Type | Purpose |
|---|---|---|
| `src/entrypoints/popup/` | React app | Main extension UI (index.html, main.tsx, App.tsx) |
| `src/entrypoints/background.ts` | Service worker | Auth token relay, API calls, session refresh on timer |
| `src/entrypoints/content.ts` | Content script | Minimal default for page interaction |

### Auth Pattern (Token Relay)

Extensions cannot use cookies directly (different origin). Flow:

1. Popup opens web sign-in tab
2. Web sends token via `chrome.runtime.sendMessage`
3. Background stores token in `chrome.storage.local`
4. All API calls route through background with token attached

### Browser Targets

| Browser | Support |
|---|---|
| Chrome | Yes (primary) |
| Firefox | Yes (WXT handles MV2/MV3 differences) |
| Safari | No (requires Xcode, opt-in) |

### Permissions (default, minimal)

| Permission | Purpose |
|---|---|
| `storage` | Auth token persistence |
| `activeTab` | Access current tab on click |
| `host_permissions` | API URL for authenticated requests |

### Shared Package Dependencies

Consumes `@repo/contracts`, `@repo/ui`, and `@repo/library`. Shares
Storybook stories with `apps/web`.

---

## 13. Infrastructure & Deployment

| Technology | Details | Reasoning |
|---|---|---|
| **Cloudflare Workers** | Wrangler ^4.68.0, `compatibility_date: 2025-01-01` | Edge-first deployment. API runs globally on Cloudflare's network. Wrangler handles local dev, type generation, and deployment. |
| **Cloudflare D1** | SQLite on the edge | Serverless relational database. Embedded in Workers — zero network hop for reads. Migration-based schema management via Drizzle Kit. |
| **Cloudflare R2** | S3-compatible storage | Object storage for files/assets. `STORAGE` binding in `wrangler.toml`. Zero egress costs vs AWS S3. |
| **Git** | `.gitattributes`, `.gitignore` | Version control with configured attributes and comprehensive ignore rules. |
| **MIT License** | `LICENSE` | Permissive open-source license (Copyright 2026 Mayank Tomar). |

| **GitHub Actions** | CI/CD pipeline | Automated quality gates, deployment, and desktop matrix builds (Windows/macOS/Linux runners). |

**Deployment strategy**: Platform-specific, no Docker or unified
deployment config. Quality enforced locally via Lefthook and in CI
via GitHub Actions:

- `apps/web` → Cloudflare Pages (static SSG output)
- `apps/api` → Cloudflare Workers (via `wrangler deploy`)
- `apps/mobile` → Expo EAS Build
- `apps/desktop` → Tauri platform-specific builds
- `apps/browser-extension` → Browser store submissions

---

## 14. Dependency Version Strategy

The project uses **pnpm's catalog feature** (`pnpm-workspace.yaml`) to
centralize versions of shared dependencies. Individual `package.json`
files reference `"catalog:"` instead of version ranges, ensuring:

- No version drift between workspaces
- Single place to update shared dependency versions
- Clear visibility into which dependencies are shared vs. workspace-specific

### Catalog Dependencies (shared across workspaces)

| Package | Catalog Version |
|---|---|
| `@astrojs/react` | ^4.4.0 |
| `@tauri-apps/cli` | ^2 |
| `@tauri-apps/api` | ^2 |
| `@better-auth/passkey` | ^1.4.19 |
| `@better-auth/sso` | ^1.4.19 |
| `@orpc/client` | ^1.13.0 |
| `@orpc/contract` | ^1.13.0 |
| `@orpc/openapi-client` | ^1.13.0 |
| `@orpc/tanstack-query` | ^1.13.0 |
| `@tanstack/react-query` | ^5.90.0 |
| `@tanstack/react-router` | ^1.162.0 |
| `astro` | ^5.17.0 |
| `better-auth` | ^1.4.19 |
| `class-variance-authority` | ^0.7.0 |
| `clsx` | ^2.1.1 |
| `i18next` | ^25.8.0 |
| `lucide-react` | ^0.575.0 |
| `motion` | ^12.34.0 |
| `react` | ^19.2.0 |
| `react-dom` | ^19.2.0 |
| `react-i18next` | ^16.5.0 |
| `sonner` | ^2.0.7 |
| `tailwind-merge` | ^3.5.0 |
| `tailwindcss` | ^4.2.0 |
| `typescript` | ^5.9.3 |
| `zod` | ^4.0.0 |
| `zustand` | ^5.0.0 |

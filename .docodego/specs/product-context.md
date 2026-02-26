---
id: SPEC-2026-001
version: 1.0.0
created: 2026-02-26
owner: Mayank
role: Intent Architect
status: draft
---

[← Back to Roadmap](ROADMAP.md)

# Product Context

Shared reference document for the DoCodeGo boilerplate. All scored specs reference this file for constraints, roles, glossary, and platform context. This document is NOT scored by ICS — it serves as the single source of truth that individual specs build upon.

---

## Product Overview

DoCodeGo boilerplate is an open-source TypeScript monorepo template that scaffolds a multi-platform SaaS application with authentication, multi-tenancy, i18n, and billing pre-wired. It targets five platforms from a single codebase: web, API, mobile, desktop, and browser extension. The install command is `pnpm create docodego-boilerplate@latest`.

---

## Platform Matrix

| Platform | App Path | Framework | Runtime / Host | Auth Mechanism |
|---|---|---|---|---|
| **Web** | `apps/web` | Astro 5 + React 19 | Cloudflare Pages (SSG) | Cookie-based sessions |
| **API** | `apps/api` | Hono 4 | Cloudflare Workers | Cookie-based sessions |
| **Mobile** | `apps/mobile` | Expo 54 + React Native | iOS / Android | Secure store tokens via `@better-auth/expo` |
| **Desktop** | `apps/desktop` | Tauri 2 (Rust shell wrapping web) | Windows / macOS / Linux | Cookie-based sessions (native webview) |
| **Browser Extension** | `apps/browser-extension` | WXT + React 19 | Chrome / Firefox (Manifest V3) | Token relay via background service worker |

### Shared Packages

| Package | Path | Purpose |
|---|---|---|
| `@repo/library` | `packages/library` | Shared validators, constants, utils |
| `@repo/contracts` | `packages/contracts` | oRPC contracts (shared API types via Zod v4) |
| `@repo/ui` | `packages/ui` | Shadcn `base-vega` components (`@base-ui/react`) |
| `@repo/i18n` | `packages/i18n` | i18next infrastructure (core is React-free) |

---

## Roles

### App-Level Roles

| Role | Field | Description |
|---|---|---|
| **User** | `user.role = "user"` | Default role. Can create orgs, manage own profile, join orgs via invitation. |
| **App Admin** | `user.role = "admin"` | System-level administrator. Can list/search/ban/unban/impersonate/create/remove users, revoke sessions, and change app-level roles. Managed via Better Auth admin plugin. |

### Org-Level Roles

| Role | Field | Description |
|---|---|---|
| **Owner** | `member.role = "owner"` | Organization creator. Can transfer ownership, delete org. One owner per org. |
| **Admin** | `member.role = "admin"` | Can invite/remove members, change member roles, configure SSO, manage teams, manage custom roles. |
| **Member** | `member.role = "member"` | Default org role. Can create/rename/delete teams, switch teams, view org content. |
| **Custom Roles** | `member.role = <custom>` | Organization-specific roles with configurable permissions beyond the three built-in roles. |

### Special States

| State | Description |
|---|---|
| **Guest** | Anonymous user with `isAnonymous = true`. Can upgrade to full account or self-delete. Cannot create or join organizations. |
| **Banned** | User with `banned = true`, optional `banReason` and `banExpires`. Blocked from sign-in. Existing sessions invalidated. |

---

## Auth Methods

All authentication is passwordless. The system supports four sign-in methods:

| Method | Availability | Plugin |
|---|---|---|
| **Email OTP** | All platforms | `emailOTP` |
| **Passkey (WebAuthn)** | Web, Desktop (Windows/macOS only — hidden on Linux) | `passkey` |
| **SSO (SAML/OIDC)** | Web, Mobile, Desktop (opens system browser) | `sso` |
| **Guest (Anonymous)** | Web, Mobile, Desktop | `anonymous` |

---

## Supported Locales

| Locale | Language | Direction |
|---|---|---|
| `en` | English | LTR |
| `ar` | Arabic | RTL |

### i18n Namespaces

| Namespace | Scope |
|---|---|
| `common` | Shared UI strings |
| `auth` | Sign-in, verification |
| `dashboard` | App navigation, workspace |
| `email` | Email templates, subjects |
| `extension` | Browser extension popup |

### Locale Detection Priority

| Platform | Chain |
|---|---|
| API | `user.preferredLocale` → `Accept-Language` header → `en` |
| Web | `user.preferredLocale` → `localStorage` → `navigator.language` → `en` |
| Desktop | `user.preferredLocale` → `localStorage` → `navigator.language` → `en` (translations bundled inline) |
| Mobile | `user.preferredLocale` → MMKV → `expo-localization` device locale → `en` |

---

## Tech Stack Summary

| Layer | Technology |
|---|---|
| Language | TypeScript ^5.9, ES2024, strict mode, `moduleResolution: "bundler"` |
| Package manager | pnpm 10 with workspace catalog |
| Monorepo orchestration | Turborepo ^2.8 |
| Web framework | Astro 5 (SSG) + React 19 (SPA dashboard) |
| Web routing | TanStack Router (file-based, type-safe) |
| Server state | TanStack Query ^5 + oRPC |
| Client state | Zustand ^5 (theme store, sidebar store) |
| API framework | Hono 4 on Cloudflare Workers |
| RPC | oRPC ^1.13 with Zod v4 contracts |
| Database | Cloudflare D1 (SQLite) via Drizzle ORM |
| Object storage | Cloudflare R2 |
| Auth | Better Auth ^1.4 (7 plugins: Email OTP, Passkey, Anonymous, SSO, Organization, Admin, DodoPayments) |
| CSS | Tailwind CSS ^4 with logical properties for RTL |
| Components | Shadcn `base-vega` style (`@base-ui/react`, not Radix) |
| Icons | Lucide React |
| Animations | Motion (Framer Motion) ^12 |
| i18n | i18next ^25, react-i18next ^16, 2 locales (en, ar), 5 namespaces |
| Mobile | Expo 54, React Native ^0.81, Expo Router ^6, MMKV, Reanimated ^4 |
| Desktop | Tauri 2 (Rust), 5 plugins (opener, updater, notification, deep-link, window-state) |
| Browser extension | WXT, Manifest V3, token relay auth |
| Testing | Vitest ^4 (unit/integration), Playwright (E2E web), Maestro (E2E mobile) |
| Linting | Biome ^2.4 |
| Dead code | Knip ^5 |
| Commits | Commitlint (conventional commits) |
| Git hooks | Lefthook ^2.1 |
| CI/CD | GitHub Actions |
| License | MIT (Copyright 2026 Mayank Tomar) |

---

## Coding Conventions

| Convention | Rule |
|---|---|
| Indent | 4 spaces |
| Line endings | CRLF |
| Line width | 90 characters |
| Quotes | Double quotes |
| Trailing commas | Always |
| Semicolons | Always |
| File/folder naming | Kebab-case |
| Module imports | No file extensions (`moduleResolution: "bundler"`) |
| Type imports | `import type` enforced (`verbatimModuleSyntax: true`) |
| Package scope | `@repo/<name>` for all workspace packages |
| Package manager | pnpm only — never npx, bunx, yarn |
| i18n core | `@repo/i18n` must never import React — use `@repo/i18n/react` subpath |
| Date/number formatting | Native `Intl` APIs — no date-fns |
| CSS direction | Logical properties only (`ps-`/`pe-`, `text-start`/`text-end`, `rounded-s-`/`rounded-e-`) |
| Dependencies | Zero-dep TS preferred; <5KB ok, >10KB needs justification |
| File limits | Source ~300 lines, tests ~400 lines, types ~250 lines |

### Commit Message Format

```
type(scope): message
```

**Types:** feat, fix, docs, refactor, test, chore, ci, dx, perf, build, revert

**Scopes:** web, api, mobile, desktop, extension, contracts, ui, library, i18n, deps, repo

---

## Quality Gates

| Gate | Command | Description |
|---|---|---|
| Lint | `pnpm lint` | Biome format + lint check (read-only) |
| Typecheck | `pnpm typecheck` | TypeScript strict mode across all workspaces |
| Test | `pnpm test` | Vitest across all workspaces |
| Dead code | `pnpm knip` | Unused exports, files, dependencies |
| Full | `pnpm quality` | lint → typecheck → test → knip (sequential) |
| Commit | `pnpm lint:commit` | Conventional commit format validation |

Quality gate is cumulative — later milestones must not break checks that previously passed.

---

## Database Tables (Drizzle + D1)

Core tables from Better Auth and its plugins:

| Table | Source | Purpose |
|---|---|---|
| `user` | Core | User accounts, `role`, `banned`, `banReason`, `banExpires`, `preferredLocale` |
| `session` | Core | Active sessions, `token`, `expiresAt`, `ipAddress`, `userAgent`, `activeOrganizationId` |
| `account` | Core | Auth provider links (email, passkey, SSO) |
| `verification` | Core | OTP codes and verification tokens |
| `organization` | Org plugin | Orgs with `name`, `slug`, `logo`, `metadata` |
| `member` | Org plugin | Org membership, `role`, `teamId` |
| `invitation` | Org plugin | Pending invitations, `email`, `role`, `status`, `expiresAt` |
| `team` | Org plugin | Teams within orgs |
| `passkey` | Passkey plugin | WebAuthn credentials |
| `ssoProvider` | SSO plugin | OIDC/SAML provider configs per org |
| `subscription` | DodoPayments plugin | Payment subscriptions *(planned)* |

---

## Deployment Targets

| App | Host | Method |
|---|---|---|
| `apps/web` | Cloudflare Pages | Static SSG output |
| `apps/api` | Cloudflare Workers | `wrangler deploy` |
| `apps/mobile` | App Store / Play Store | Expo EAS Build |
| `apps/desktop` | Direct download | Tauri builds (`.msi`/`.exe`, `.dmg`/`.app`, `.AppImage`/`.deb`) |
| `apps/browser-extension` | Chrome Web Store / Firefox Add-ons | WXT build + store submission |

---

## Glossary

| Term | Definition |
|---|---|
| **Boilerplate** | The DoCodeGo starter template that scaffolds a multi-platform SaaS monorepo |
| **Catalog** | pnpm workspace catalog — centralized dependency versions in `pnpm-workspace.yaml` |
| **D1** | Cloudflare's serverless SQLite database at the edge |
| **Deep link** | Custom URL scheme (`docodego://`) handled by desktop and mobile apps |
| **ICS** | Intent Clarity Score — spec quality metric (0-100) across four dimensions |
| **Logical properties** | CSS properties that adapt to text direction (e.g., `padding-inline-start` instead of `padding-left`) |
| **MMKV** | High-performance key-value storage on mobile (replacement for AsyncStorage) |
| **Namespace (i18n)** | Scoped group of translation strings loaded independently |
| **oRPC** | Type-safe RPC framework with OpenAPI-first design and contract separation |
| **R2** | Cloudflare's S3-compatible object storage with zero egress fees |
| **SSG** | Static Site Generation — HTML generated at build time |
| **SPA** | Single Page Application — client-side routing at `/app/*` |
| **Token relay** | Browser extension auth pattern where tokens flow through the background service worker |
| **WebAuthn** | Web standard for passwordless auth via biometrics/hardware keys (passkeys) |
| **Webview** | Native window rendering web content — Tauri uses the OS webview engine |

---

## Related Inputs

| Input | Path |
|---|---|
| Tech stack | `.docodego/input/tech-stack.md` |
| Behavioral flows | `.docodego/input/flows/` (81 flows) |
| Framework | `.docodego/input/framework.md` |
| Better Auth research | `.docodego/input/research/better-auth-plugins-research.md` |
| Spec roadmap | `.docodego/specs/ROADMAP.md` |

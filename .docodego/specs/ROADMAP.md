# Spec Creation Roadmap

Phased plan for creating all DoCoDeGo specs with ICS 100 scores, auditable via commit history.

→ [Spec Review Roadmap](REVIEW.md)

## Structure

| Level | Count | Scored? |
|---|---|---|
| Product Context | 1 | No — shared reference doc |
| Foundation Specs | 12 | Yes — ICS 100 |
| Behavioral Specs | 81 | Yes — ICS 100 |
| Convention Specs | 12 | Yes — CCS 100 |
| **Total** | **106** | **105 scored** |

## ICS 100 Requirements

Each scored spec needs 25/25 on four dimensions:

- **Completeness (25)**: Intent + Acceptance Criteria + Constraints + Failure Modes, each ≥50 words
- **Testability (25)**: ≥90% acceptance criteria contain measurable language (numbers, thresholds, HTTP codes, true/false)
- **Unambiguity (25)**: Zero vague qualifiers (should, may, fast, good, intuitive, reasonable, appropriate, robust, scalable, efficient, secure, as needed)
- **Threat Coverage (25)**: ≥3 failure modes, each ≥15 words with recovery keyword (falls back, retries, returns error, rejects, logs, notifies, etc.)

---

## Checklist

### Phase 1: Product Context

- [x] [product-context.md](product-context.md) — shared constraints, roles, glossary, tech stack summary, platform matrix

### Phase 2: Foundation Specs

#### Commit 2a — Project Infrastructure
- [x] [monorepo-structure.md](foundation/monorepo-structure.md) — workspace layout, pnpm catalog, Turborepo pipeline
- [x] [typescript-config.md](foundation/typescript-config.md) — tsconfig hierarchy, strict mode, path aliases, ES2024 target
- [x] [code-quality.md](foundation/code-quality.md) — Biome, Knip, Commitlint rules, Lefthook hooks

#### Commit 2b — Backend Foundation
- [x] [database-schema.md](foundation/database-schema.md) — Drizzle tables, D1 bindings, migrations, seed script
- [x] [auth-server-config.md](foundation/auth-server-config.md) — Better Auth plugin wiring, cookie config, session strategy
- [x] [api-framework.md](foundation/api-framework.md) — Hono middleware stack, CORS, error handler, oRPC router, Scalar

#### Commit 2c — Shared Packages
- [x] [shared-contracts.md](foundation/shared-contracts.md) — `@repo/contracts` oRPC definitions, Zod schemas
- [x] [shared-ui.md](foundation/shared-ui.md) — `@repo/ui` Shadcn components, cn(), DirectionProvider
- [x] [shared-i18n.md](foundation/shared-i18n.md) — `@repo/i18n` namespaces, subpaths, formatters, lazy-loading

#### Commit 2d — Build & Deploy
- [x] [ci-cd-pipelines.md](foundation/ci-cd-pipelines.md) — GitHub Actions workflows, deployment strategy per platform
- [x] [tauri-build.md](foundation/tauri-build.md) — Rust config, IPC commands, plugins, build targets per OS
- [x] [expo-build.md](foundation/expo-build.md) — EAS profiles, Metro config, native modules

### Phase 3: Behavioral Specs — Auth & Session

#### Commit 3a — Sign-in methods (4 specs)
- [x] [user-signs-in-with-email-otp.md](behavioral/user-signs-in-with-email-otp.md) ← flow #3
- [x] [user-signs-in-with-passkey.md](behavioral/user-signs-in-with-passkey.md) ← flow #4
- [x] [user-signs-in-as-guest.md](behavioral/user-signs-in-as-guest.md) ← flow #5
- [x] [user-signs-in-with-sso.md](behavioral/user-signs-in-with-sso.md) ← flow #8

#### Commit 3b — Sign-out & session lifecycle (3 specs)
- [x] [user-signs-out.md](behavioral/user-signs-out.md) ← flow #9
- [x] [session-lifecycle.md](behavioral/session-lifecycle.md) ← flow #10
- [x] [session-expires-mid-use.md](behavioral/session-expires-mid-use.md) ← flow #11

#### Commit 3c — Guest lifecycle & access control (3 specs)
- [x] [guest-upgrades-to-full-account.md](behavioral/guest-upgrades-to-full-account.md) ← flow #6
- [x] [guest-deletes-anonymous-account.md](behavioral/guest-deletes-anonymous-account.md) ← flow #7
- [x] [banned-user-attempts-sign-in.md](behavioral/banned-user-attempts-sign-in.md) ← flow #12

### Phase 4: Behavioral Specs — Org & Members

#### Commit 4a — Org creation & switching (4 specs)
- [x] [user-creates-first-organization.md](behavioral/user-creates-first-organization.md) ← flow #13
- [x] [user-creates-an-organization.md](behavioral/user-creates-an-organization.md) ← flow #14
- [x] [user-switches-organization.md](behavioral/user-switches-organization.md) ← flow #15
- [x] [user-updates-organization-settings.md](behavioral/user-updates-organization-settings.md) ← flow #16

#### Commit 4b — Org settings & departure (4 specs)
- [x] [user-uploads-organization-logo.md](behavioral/user-uploads-organization-logo.md) ← flow #17
- [x] [user-transfers-organization-ownership.md](behavioral/user-transfers-organization-ownership.md) ← flow #18
- [x] [user-leaves-an-organization.md](behavioral/user-leaves-an-organization.md) ← flow #19
- [x] [user-deletes-an-organization.md](behavioral/user-deletes-an-organization.md) ← flow #20

#### Commit 4c — Invitations (4 specs)
- [x] [org-admin-invites-a-member.md](behavioral/org-admin-invites-a-member.md) ← flow #22
- [x] [user-accepts-an-invitation.md](behavioral/user-accepts-an-invitation.md) ← flow #23
- [x] [user-declines-an-invitation.md](behavioral/user-declines-an-invitation.md) ← flow #24
- [x] [org-admin-cancels-an-invitation.md](behavioral/org-admin-cancels-an-invitation.md) ← flow #25

#### Commit 4d — Member & SSO management (4 specs)
- [x] [org-admin-changes-member-role.md](behavioral/org-admin-changes-member-role.md) ← flow #26
- [x] [org-admin-removes-a-member.md](behavioral/org-admin-removes-a-member.md) ← flow #27
- [x] [org-admin-configures-sso-provider.md](behavioral/org-admin-configures-sso-provider.md) ← flow #28
- [x] [org-admin-manages-custom-roles.md](behavioral/org-admin-manages-custom-roles.md) ← flow #29

#### Commit 4e — Teams (4 specs)
- [x] [user-creates-a-team.md](behavioral/user-creates-a-team.md) ← flow #30
- [x] [user-renames-a-team.md](behavioral/user-renames-a-team.md) ← flow #31
- [x] [org-admin-manages-team-members.md](behavioral/org-admin-manages-team-members.md) ← flow #32
- [x] [user-switches-active-team.md](behavioral/user-switches-active-team.md) ← flow #33

### Phase 5: Behavioral Specs — Dashboard, Settings, Admin

#### Commit 5a — Dashboard & profile (4 specs)
- [x] [user-navigates-the-dashboard.md](behavioral/user-navigates-the-dashboard.md) ← flow #21
- [x] [user-deletes-a-team.md](behavioral/user-deletes-a-team.md) ← flow #34
- [x] [user-updates-profile.md](behavioral/user-updates-profile.md) ← flow #35
- [x] [user-uploads-profile-avatar.md](behavioral/user-uploads-profile-avatar.md) ← flow #36

#### Commit 5b — Theme, language & locale (3 specs)
- [x] [user-changes-theme.md](behavioral/user-changes-theme.md) ← flow #37
- [x] [user-changes-language.md](behavioral/user-changes-language.md) ← flow #38
- [x] [user-syncs-locale-preference.md](behavioral/user-syncs-locale-preference.md) ← flow #39

#### Commit 5c — Passkeys & sessions (4 specs)
- [x] [user-registers-a-passkey.md](behavioral/user-registers-a-passkey.md) ← flow #40
- [x] [user-renames-a-passkey.md](behavioral/user-renames-a-passkey.md) ← flow #41
- [x] [user-removes-a-passkey.md](behavioral/user-removes-a-passkey.md) ← flow #42
- [x] [user-manages-sessions.md](behavioral/user-manages-sessions.md) ← flow #43

#### Commit 5d — Account & admin basics (4 specs)
- [x] [user-deletes-their-account.md](behavioral/user-deletes-their-account.md) ← flow #44
- [x] [app-admin-lists-and-searches-users.md](behavioral/app-admin-lists-and-searches-users.md) ← flow #45
- [x] [app-admin-views-user-details.md](behavioral/app-admin-views-user-details.md) ← flow #46
- [x] [app-admin-updates-user-details.md](behavioral/app-admin-updates-user-details.md) ← flow #47

#### Commit 5e — Admin moderation (4 specs)
- [x] [app-admin-bans-a-user.md](behavioral/app-admin-bans-a-user.md) ← flow #48
- [x] [app-admin-unbans-a-user.md](behavioral/app-admin-unbans-a-user.md) ← flow #49
- [x] [app-admin-impersonates-a-user.md](behavioral/app-admin-impersonates-a-user.md) ← flow #50
- [x] [app-admin-creates-a-user.md](behavioral/app-admin-creates-a-user.md) ← flow #51

#### Commit 5f — Admin role & session ops (3 specs)
- [x] [app-admin-changes-user-role.md](behavioral/app-admin-changes-user-role.md) ← flow #52
- [x] [app-admin-removes-a-user.md](behavioral/app-admin-removes-a-user.md) ← flow #53
- [x] [app-admin-revokes-user-sessions.md](behavioral/app-admin-revokes-user-sessions.md) ← flow #54

### Phase 6: Behavioral Specs — Platforms

#### Commit 6a — Desktop core (4 specs)
- [x] [user-launches-desktop-app.md](behavioral/user-launches-desktop-app.md) ← flow #55
- [x] [user-uses-system-tray.md](behavioral/user-uses-system-tray.md) ← flow #56
- [x] [user-opens-a-deep-link.md](behavioral/user-opens-a-deep-link.md) ← flow #57
- [x] [desktop-opens-external-link.md](behavioral/desktop-opens-external-link.md) ← flow #58

#### Commit 6b — Desktop system (3 specs)
- [x] [desktop-auto-updates.md](behavioral/desktop-auto-updates.md) ← flow #59
- [x] [desktop-sends-a-notification.md](behavioral/desktop-sends-a-notification.md) ← flow #60
- [x] [user-views-desktop-app-version.md](behavioral/user-views-desktop-app-version.md) ← flow #61

#### Commit 6c — Mobile core (4 specs)
- [x] [user-launches-mobile-app.md](behavioral/user-launches-mobile-app.md) ← flow #62
- [x] [user-signs-in-on-mobile.md](behavioral/user-signs-in-on-mobile.md) ← flow #63
- [x] [user-navigates-mobile-app.md](behavioral/user-navigates-mobile-app.md) ← flow #64
- [x] [mobile-handles-deep-link.md](behavioral/mobile-handles-deep-link.md) ← flow #65

#### Commit 6d — Mobile preferences & extension auth (4 specs)
- [x] [user-changes-theme-on-mobile.md](behavioral/user-changes-theme-on-mobile.md) ← flow #66
- [x] [user-changes-language-on-mobile.md](behavioral/user-changes-language-on-mobile.md) ← flow #67
- [x] [user-installs-browser-extension.md](behavioral/user-installs-browser-extension.md) ← flow #68
- [x] [extension-authenticates-via-token-relay.md](behavioral/extension-authenticates-via-token-relay.md) ← flow #69

#### Commit 6e — Extension behavior (3 specs)
- [x] [extension-signs-out.md](behavioral/extension-signs-out.md) ← flow #70
- [x] [user-interacts-with-extension-popup.md](behavioral/user-interacts-with-extension-popup.md) ← flow #71
- [x] [extension-receives-an-update.md](behavioral/extension-receives-an-update.md) ← flow #72

### Phase 7: Behavioral Specs — System & Cross-Cutting

#### Commit 7a — Landing & email system (4 specs)
- [x] [user-visits-landing-page.md](behavioral/user-visits-landing-page.md) ← flow #1
- [x] [user-enters-the-app.md](behavioral/user-enters-the-app.md) ← flow #2
- [x] [system-sends-otp-email.md](behavioral/system-sends-otp-email.md) ← flow #73
- [x] [system-sends-invitation-email.md](behavioral/system-sends-invitation-email.md) ← flow #74

#### Commit 7b — i18n, uploads & error handling (4 specs)
- [x] [system-detects-locale.md](behavioral/system-detects-locale.md) ← flow #75
- [x] [app-renders-rtl-layout.md](behavioral/app-renders-rtl-layout.md) ← flow #76
- [x] [user-uploads-a-file.md](behavioral/user-uploads-a-file.md) ← flow #77
- [x] [system-handles-errors.md](behavioral/system-handles-errors.md) ← flow #78

#### Commit 7c — API reference & billing (3 specs)
- [x] [developer-views-api-reference.md](behavioral/developer-views-api-reference.md) ← flow #79
- [x] [user-subscribes-to-a-plan.md](behavioral/user-subscribes-to-a-plan.md) ← flow #80
- [x] [user-manages-billing-portal.md](behavioral/user-manages-billing-portal.md) ← flow #81

### Phase 8: Full Review Pass

- [x] Run ICS scorer on all 93 scored specs, fix regressions, verify ICS 100

### Phase 9: Convention Specs

#### Commit conv-1a — Code Shape
- [x] [code-style.md](conventions/code-style.md)
- [x] [typescript-discipline.md](conventions/typescript-discipline.md)
- [x] [module-boundaries.md](conventions/module-boundaries.md)

#### Commit conv-1b — React Architecture
- [x] [component-design.md](conventions/component-design.md)
- [x] [hooks-conventions.md](conventions/hooks-conventions.md)
- [x] [state-management-conventions.md](conventions/state-management-conventions.md)

#### Commit conv-1c — API & Data Layer
- [x] [api-layer-conventions.md](conventions/api-layer-conventions.md)
- [x] [error-handling-conventions.md](conventions/error-handling-conventions.md)
- [x] [data-access-conventions.md](conventions/data-access-conventions.md)

#### Commit conv-1d — Quality & Delivery
- [x] [testing-conventions.md](conventions/testing-conventions.md)
- [x] [ui-styling-conventions.md](conventions/ui-styling-conventions.md)
- [x] [project-hygiene-conventions.md](conventions/project-hygiene-conventions.md)

### Phase 10: Convention Review Pass (CCS)

- [ ] Run CCS scorer on all 12 convention specs, fix regressions, verify CCS 100

---

## Commit History

```
phase-1:  add product context foundation
phase-2a: add project infrastructure specs (ICS 100)
phase-2b: add backend foundation specs (ICS 100)
phase-2c: add shared package specs (ICS 100)
phase-2d: add build & deploy specs (ICS 100)
phase-3a: add sign-in method specs (ICS 100)
phase-3b: add sign-out & session lifecycle specs (ICS 100)
phase-3c: add guest lifecycle & access control specs (ICS 100)
phase-4a: add org creation & switching specs (ICS 100)
phase-4b: add org settings & departure specs (ICS 100)
phase-4c: add invitation specs (ICS 100)
phase-4d: add member & SSO management specs (ICS 100)
phase-4e: add team specs (ICS 100)
phase-5a: add dashboard & profile specs (ICS 100)
phase-5b: add theme, language & locale specs (ICS 100)
phase-5c: add passkeys & sessions specs (ICS 100)
phase-5d: add account & admin basics specs (ICS 100)
phase-5e: add admin moderation specs (ICS 100)
phase-5f: add admin role & session ops specs (ICS 100)
phase-6a: add desktop core specs (ICS 100)
phase-6b: add desktop system specs (ICS 100)
phase-6c: add mobile core specs (ICS 100)
phase-6d: add mobile prefs & extension auth specs (ICS 100)
phase-6e: add extension behavior specs (ICS 100)
phase-7a: add landing & email system specs (ICS 100)
phase-7b: add i18n, uploads & error handling specs (ICS 100)
phase-7c: add API reference & billing specs (ICS 100)
phase-8:     review pass — all 93 specs verified ICS 100
conv-1a:     add code shape convention specs (CCS 100)
conv-1b:     add React architecture convention specs (CCS 100)
conv-1c:     add API & data layer convention specs (CCS 100)
conv-1d:     add quality & delivery convention specs (CCS 100)
conv-review: review pass — all 12 convention specs verified CCS 100
```

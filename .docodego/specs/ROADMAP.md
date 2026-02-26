# Spec Creation Roadmap

Phased plan for creating all DoCoDeGo specs with ICS 100 scores, auditable via commit history.

## Structure

| Level | Count | Scored? |
|---|---|---|
| Product Context | 1 | No — shared reference doc |
| Foundation Specs | 12 | Yes — config, schema, build, packages |
| Behavioral Specs | 81 | Yes — 1:1 with flows |
| **Total** | **94** | **93 scored** |

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

#### Commit 3a — Sign-in methods (5 specs)
- [x] [user-signs-in-with-email-otp.md](behavioral/user-signs-in-with-email-otp.md) ← flow #3
- [x] [user-signs-in-with-passkey.md](behavioral/user-signs-in-with-passkey.md) ← flow #4
- [x] [user-signs-in-as-guest.md](behavioral/user-signs-in-as-guest.md) ← flow #5
- [x] [user-signs-in-with-sso.md](behavioral/user-signs-in-with-sso.md) ← flow #8
- [x] [user-signs-out.md](behavioral/user-signs-out.md) ← flow #9

#### Commit 3b — Session & guest lifecycle (5 specs)
- [ ] [guest-upgrades-to-full-account.md](behavioral/guest-upgrades-to-full-account.md) ← flow #6
- [ ] [guest-deletes-anonymous-account.md](behavioral/guest-deletes-anonymous-account.md) ← flow #7
- [ ] [session-lifecycle.md](behavioral/session-lifecycle.md) ← flow #10
- [ ] [session-expires-mid-use.md](behavioral/session-expires-mid-use.md) ← flow #11
- [ ] [banned-user-attempts-sign-in.md](behavioral/banned-user-attempts-sign-in.md) ← flow #12

### Phase 4: Behavioral Specs — Org & Members

#### Commit 4a — Org lifecycle (6 specs)
- [ ] [user-creates-first-organization.md](behavioral/user-creates-first-organization.md) ← flow #13
- [ ] [user-creates-an-organization.md](behavioral/user-creates-an-organization.md) ← flow #14
- [ ] [user-switches-organization.md](behavioral/user-switches-organization.md) ← flow #15
- [ ] [user-updates-organization-settings.md](behavioral/user-updates-organization-settings.md) ← flow #16
- [ ] [user-uploads-organization-logo.md](behavioral/user-uploads-organization-logo.md) ← flow #17
- [ ] [user-transfers-organization-ownership.md](behavioral/user-transfers-organization-ownership.md) ← flow #18

#### Commit 4b — Org departure + members (6 specs)
- [ ] [user-leaves-an-organization.md](behavioral/user-leaves-an-organization.md) ← flow #19
- [ ] [user-deletes-an-organization.md](behavioral/user-deletes-an-organization.md) ← flow #20
- [ ] [org-admin-invites-a-member.md](behavioral/org-admin-invites-a-member.md) ← flow #22
- [ ] [user-accepts-an-invitation.md](behavioral/user-accepts-an-invitation.md) ← flow #23
- [ ] [user-declines-an-invitation.md](behavioral/user-declines-an-invitation.md) ← flow #24
- [ ] [org-admin-cancels-an-invitation.md](behavioral/org-admin-cancels-an-invitation.md) ← flow #25

#### Commit 4c — Member ops + teams (8 specs)
- [ ] [org-admin-changes-member-role.md](behavioral/org-admin-changes-member-role.md) ← flow #26
- [ ] [org-admin-removes-a-member.md](behavioral/org-admin-removes-a-member.md) ← flow #27
- [ ] [org-admin-configures-sso-provider.md](behavioral/org-admin-configures-sso-provider.md) ← flow #28
- [ ] [org-admin-manages-custom-roles.md](behavioral/org-admin-manages-custom-roles.md) ← flow #29
- [ ] [user-creates-a-team.md](behavioral/user-creates-a-team.md) ← flow #30
- [ ] [user-renames-a-team.md](behavioral/user-renames-a-team.md) ← flow #31
- [ ] [org-admin-manages-team-members.md](behavioral/org-admin-manages-team-members.md) ← flow #32
- [ ] [user-switches-active-team.md](behavioral/user-switches-active-team.md) ← flow #33

### Phase 5: Behavioral Specs — Dashboard, Settings, Admin

#### Commit 5a — Dashboard + user settings (7 specs)
- [ ] [user-deletes-a-team.md](behavioral/user-deletes-a-team.md) ← flow #34
- [ ] [user-navigates-the-dashboard.md](behavioral/user-navigates-the-dashboard.md) ← flow #21
- [ ] [user-updates-profile.md](behavioral/user-updates-profile.md) ← flow #35
- [ ] [user-uploads-profile-avatar.md](behavioral/user-uploads-profile-avatar.md) ← flow #36
- [ ] [user-changes-theme.md](behavioral/user-changes-theme.md) ← flow #37
- [ ] [user-changes-language.md](behavioral/user-changes-language.md) ← flow #38
- [ ] [user-syncs-locale-preference.md](behavioral/user-syncs-locale-preference.md) ← flow #39

#### Commit 5b — Security settings (5 specs)
- [ ] [user-registers-a-passkey.md](behavioral/user-registers-a-passkey.md) ← flow #40
- [ ] [user-renames-a-passkey.md](behavioral/user-renames-a-passkey.md) ← flow #41
- [ ] [user-removes-a-passkey.md](behavioral/user-removes-a-passkey.md) ← flow #42
- [ ] [user-manages-sessions.md](behavioral/user-manages-sessions.md) ← flow #43
- [ ] [user-deletes-their-account.md](behavioral/user-deletes-their-account.md) ← flow #44

#### Commit 5c — App admin (10 specs)
- [ ] [app-admin-lists-and-searches-users.md](behavioral/app-admin-lists-and-searches-users.md) ← flow #45
- [ ] [app-admin-views-user-details.md](behavioral/app-admin-views-user-details.md) ← flow #46
- [ ] [app-admin-updates-user-details.md](behavioral/app-admin-updates-user-details.md) ← flow #47
- [ ] [app-admin-bans-a-user.md](behavioral/app-admin-bans-a-user.md) ← flow #48
- [ ] [app-admin-unbans-a-user.md](behavioral/app-admin-unbans-a-user.md) ← flow #49
- [ ] [app-admin-impersonates-a-user.md](behavioral/app-admin-impersonates-a-user.md) ← flow #50
- [ ] [app-admin-creates-a-user.md](behavioral/app-admin-creates-a-user.md) ← flow #51
- [ ] [app-admin-changes-user-role.md](behavioral/app-admin-changes-user-role.md) ← flow #52
- [ ] [app-admin-removes-a-user.md](behavioral/app-admin-removes-a-user.md) ← flow #53
- [ ] [app-admin-revokes-user-sessions.md](behavioral/app-admin-revokes-user-sessions.md) ← flow #54

### Phase 6: Behavioral Specs — Platforms

#### Commit 6a — Desktop (7 specs)
- [ ] [user-launches-desktop-app.md](behavioral/user-launches-desktop-app.md) ← flow #55
- [ ] [user-uses-system-tray.md](behavioral/user-uses-system-tray.md) ← flow #56
- [ ] [user-opens-a-deep-link.md](behavioral/user-opens-a-deep-link.md) ← flow #57
- [ ] [desktop-opens-external-link.md](behavioral/desktop-opens-external-link.md) ← flow #58
- [ ] [desktop-auto-updates.md](behavioral/desktop-auto-updates.md) ← flow #59
- [ ] [desktop-sends-a-notification.md](behavioral/desktop-sends-a-notification.md) ← flow #60
- [ ] [user-views-desktop-app-version.md](behavioral/user-views-desktop-app-version.md) ← flow #61

#### Commit 6b — Mobile (6 specs)
- [ ] [user-launches-mobile-app.md](behavioral/user-launches-mobile-app.md) ← flow #62
- [ ] [user-signs-in-on-mobile.md](behavioral/user-signs-in-on-mobile.md) ← flow #63
- [ ] [user-navigates-mobile-app.md](behavioral/user-navigates-mobile-app.md) ← flow #64
- [ ] [mobile-handles-deep-link.md](behavioral/mobile-handles-deep-link.md) ← flow #65
- [ ] [user-changes-theme-on-mobile.md](behavioral/user-changes-theme-on-mobile.md) ← flow #66
- [ ] [user-changes-language-on-mobile.md](behavioral/user-changes-language-on-mobile.md) ← flow #67

#### Commit 6c — Browser extension (5 specs)
- [ ] [user-installs-browser-extension.md](behavioral/user-installs-browser-extension.md) ← flow #68
- [ ] [extension-authenticates-via-token-relay.md](behavioral/extension-authenticates-via-token-relay.md) ← flow #69
- [ ] [extension-signs-out.md](behavioral/extension-signs-out.md) ← flow #70
- [ ] [user-interacts-with-extension-popup.md](behavioral/user-interacts-with-extension-popup.md) ← flow #71
- [ ] [extension-receives-an-update.md](behavioral/extension-receives-an-update.md) ← flow #72

### Phase 7: Behavioral Specs — System & Cross-Cutting

#### Commit 7a — Landing, i18n, infra (6 specs)
- [ ] [user-visits-landing-page.md](behavioral/user-visits-landing-page.md) ← flow #1
- [ ] [user-enters-the-app.md](behavioral/user-enters-the-app.md) ← flow #2
- [ ] [system-sends-otp-email.md](behavioral/system-sends-otp-email.md) ← flow #73
- [ ] [system-sends-invitation-email.md](behavioral/system-sends-invitation-email.md) ← flow #74
- [ ] [system-detects-locale.md](behavioral/system-detects-locale.md) ← flow #75
- [ ] [app-renders-rtl-layout.md](behavioral/app-renders-rtl-layout.md) ← flow #76

#### Commit 7b — Remaining system (5 specs)
- [ ] [user-uploads-a-file.md](behavioral/user-uploads-a-file.md) ← flow #77
- [ ] [system-handles-errors.md](behavioral/system-handles-errors.md) ← flow #78
- [ ] [developer-views-api-reference.md](behavioral/developer-views-api-reference.md) ← flow #79
- [ ] [user-subscribes-to-a-plan.md](behavioral/user-subscribes-to-a-plan.md) ← flow #80
- [ ] [user-manages-billing-portal.md](behavioral/user-manages-billing-portal.md) ← flow #81

### Phase 8: Full Review Pass

- [ ] Run ICS scorer on all 93 scored specs, fix regressions, verify ICS 100

---

## Commit History

```
phase-1:  add product context foundation
phase-2a: add project infrastructure specs (ICS 100)
phase-2b: add backend foundation specs (ICS 100)
phase-2c: add shared package specs (ICS 100)
phase-2d: add build & deploy specs (ICS 100)
phase-3a: add auth sign-in specs (ICS 100)
phase-3b: add session & guest lifecycle specs (ICS 100)
phase-4a: add org lifecycle specs (ICS 100)
phase-4b: add org departure & member specs (ICS 100)
phase-4c: add member ops & team specs (ICS 100)
phase-5a: add dashboard & user settings specs (ICS 100)
phase-5b: add security settings specs (ICS 100)
phase-5c: add app admin specs (ICS 100)
phase-6a: add desktop app specs (ICS 100)
phase-6b: add mobile app specs (ICS 100)
phase-6c: add browser extension specs (ICS 100)
phase-7a: add landing & i18n system specs (ICS 100)
phase-7b: add remaining system specs (ICS 100)
phase-8:  review pass — all 93 specs verified ICS 100
```

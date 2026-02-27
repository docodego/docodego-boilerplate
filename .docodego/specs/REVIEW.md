# Spec Review Roadmap

Phased review of all DoCoDeGo specs, auditable via commit history.
Covers what the ICS scorer cannot — consistency, correctness, and coverage.

→ [Spec Creation Roadmap](ROADMAP.md)

## Review Dimensions

Each spec is reviewed across five dimensions:

| Code | Dimension | What It Checks |
|------|-----------|----------------|
| **T** | Terminology | Names (methods, fields, routes, roles) match the glossary in `product-context.md` — no drift or synonyms across specs |
| **L** | Link Integrity | Every path in Related Specifications resolves to a real file — no dead links, no renamed targets |
| **C** | Coverage | Every flow cross-referenced inside this spec has its own spec file — no orphan references |
| **X** | Contradiction | No business rule, state transition, or API behaviour conflicts with any other spec describing the same system |
| **O** | Omissions Audit | Every Declared Omission names a spec that exists and covers the described behaviour |

Sign-off codes: `✓` pass · `✗` fail (note the issue) · `—` not applicable

---

## Checklist

### Phase 1: Product Context

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [product-context.md](product-context.md) | ✓ | ✓ | ✓ | ✓ | — |

### Phase 2: Foundation Specs

#### Review 2a — Project Infrastructure

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [monorepo-structure.md](foundation/monorepo-structure.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [typescript-config.md](foundation/typescript-config.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [code-quality.md](foundation/code-quality.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 2b — Backend Foundation

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [database-schema.md](foundation/database-schema.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [auth-server-config.md](foundation/auth-server-config.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [api-framework.md](foundation/api-framework.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 2c — Shared Packages

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [shared-contracts.md](foundation/shared-contracts.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [shared-ui.md](foundation/shared-ui.md) | ✓ | ✓ | ✓ | ✓ | — |
| [shared-i18n.md](foundation/shared-i18n.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 2d — Build & Deploy

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [ci-cd-pipelines.md](foundation/ci-cd-pipelines.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [tauri-build.md](foundation/tauri-build.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [expo-build.md](foundation/expo-build.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

### Phase 3: Behavioral Specs — Auth & Session

#### Review 3a — Sign-in methods

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-signs-in-with-email-otp.md](behavioral/user-signs-in-with-email-otp.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-signs-in-with-passkey.md](behavioral/user-signs-in-with-passkey.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-signs-in-as-guest.md](behavioral/user-signs-in-as-guest.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-signs-in-with-sso.md](behavioral/user-signs-in-with-sso.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 3b — Sign-out & session lifecycle

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-signs-out.md](behavioral/user-signs-out.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [session-lifecycle.md](behavioral/session-lifecycle.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [session-expires-mid-use.md](behavioral/session-expires-mid-use.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 3c — Guest lifecycle & access control

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [guest-upgrades-to-full-account.md](behavioral/guest-upgrades-to-full-account.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [guest-deletes-anonymous-account.md](behavioral/guest-deletes-anonymous-account.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [banned-user-attempts-sign-in.md](behavioral/banned-user-attempts-sign-in.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

### Phase 4: Behavioral Specs — Org & Members

#### Review 4a — Org creation & switching

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-creates-first-organization.md](behavioral/user-creates-first-organization.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-creates-an-organization.md](behavioral/user-creates-an-organization.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-switches-organization.md](behavioral/user-switches-organization.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-updates-organization-settings.md](behavioral/user-updates-organization-settings.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 4b — Org settings & departure

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-uploads-organization-logo.md](behavioral/user-uploads-organization-logo.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-transfers-organization-ownership.md](behavioral/user-transfers-organization-ownership.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-leaves-an-organization.md](behavioral/user-leaves-an-organization.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-deletes-an-organization.md](behavioral/user-deletes-an-organization.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 4c — Invitations

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [org-admin-invites-a-member.md](behavioral/org-admin-invites-a-member.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-accepts-an-invitation.md](behavioral/user-accepts-an-invitation.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-declines-an-invitation.md](behavioral/user-declines-an-invitation.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [org-admin-cancels-an-invitation.md](behavioral/org-admin-cancels-an-invitation.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 4d — Member & SSO management

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [org-admin-changes-member-role.md](behavioral/org-admin-changes-member-role.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [org-admin-removes-a-member.md](behavioral/org-admin-removes-a-member.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [org-admin-configures-sso-provider.md](behavioral/org-admin-configures-sso-provider.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [org-admin-manages-custom-roles.md](behavioral/org-admin-manages-custom-roles.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 4e — Teams

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-creates-a-team.md](behavioral/user-creates-a-team.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-renames-a-team.md](behavioral/user-renames-a-team.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [org-admin-manages-team-members.md](behavioral/org-admin-manages-team-members.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-switches-active-team.md](behavioral/user-switches-active-team.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

### Phase 5: Behavioral Specs — Dashboard, Settings, Admin

#### Review 5a — Dashboard & profile

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-navigates-the-dashboard.md](behavioral/user-navigates-the-dashboard.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-deletes-a-team.md](behavioral/user-deletes-a-team.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-updates-profile.md](behavioral/user-updates-profile.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-uploads-profile-avatar.md](behavioral/user-uploads-profile-avatar.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 5b — Theme, language & locale

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-changes-theme.md](behavioral/user-changes-theme.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-changes-language.md](behavioral/user-changes-language.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-syncs-locale-preference.md](behavioral/user-syncs-locale-preference.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 5c — Passkeys & sessions

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-registers-a-passkey.md](behavioral/user-registers-a-passkey.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-renames-a-passkey.md](behavioral/user-renames-a-passkey.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-removes-a-passkey.md](behavioral/user-removes-a-passkey.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-manages-sessions.md](behavioral/user-manages-sessions.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 5d — Account & admin basics

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-deletes-their-account.md](behavioral/user-deletes-their-account.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [app-admin-lists-and-searches-users.md](behavioral/app-admin-lists-and-searches-users.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [app-admin-views-user-details.md](behavioral/app-admin-views-user-details.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [app-admin-updates-user-details.md](behavioral/app-admin-updates-user-details.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 5e — Admin moderation

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [app-admin-bans-a-user.md](behavioral/app-admin-bans-a-user.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [app-admin-unbans-a-user.md](behavioral/app-admin-unbans-a-user.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [app-admin-impersonates-a-user.md](behavioral/app-admin-impersonates-a-user.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [app-admin-creates-a-user.md](behavioral/app-admin-creates-a-user.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 5f — Admin role & session ops

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [app-admin-changes-user-role.md](behavioral/app-admin-changes-user-role.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [app-admin-removes-a-user.md](behavioral/app-admin-removes-a-user.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [app-admin-revokes-user-sessions.md](behavioral/app-admin-revokes-user-sessions.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

### Phase 6: Behavioral Specs — Platforms

#### Review 6a — Desktop core

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-launches-desktop-app.md](behavioral/user-launches-desktop-app.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-uses-system-tray.md](behavioral/user-uses-system-tray.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-opens-a-deep-link.md](behavioral/user-opens-a-deep-link.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [desktop-opens-external-link.md](behavioral/desktop-opens-external-link.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 6b — Desktop system

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [desktop-auto-updates.md](behavioral/desktop-auto-updates.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [desktop-sends-a-notification.md](behavioral/desktop-sends-a-notification.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-views-desktop-app-version.md](behavioral/user-views-desktop-app-version.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 6c — Mobile core

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-launches-mobile-app.md](behavioral/user-launches-mobile-app.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-signs-in-on-mobile.md](behavioral/user-signs-in-on-mobile.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-navigates-mobile-app.md](behavioral/user-navigates-mobile-app.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [mobile-handles-deep-link.md](behavioral/mobile-handles-deep-link.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 6d — Mobile preferences & extension auth

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-changes-theme-on-mobile.md](behavioral/user-changes-theme-on-mobile.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-changes-language-on-mobile.md](behavioral/user-changes-language-on-mobile.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-installs-browser-extension.md](behavioral/user-installs-browser-extension.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [extension-authenticates-via-token-relay.md](behavioral/extension-authenticates-via-token-relay.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 6e — Extension behavior

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [extension-signs-out.md](behavioral/extension-signs-out.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-interacts-with-extension-popup.md](behavioral/user-interacts-with-extension-popup.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [extension-receives-an-update.md](behavioral/extension-receives-an-update.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

### Phase 7: Behavioral Specs — System & Cross-Cutting

#### Review 7a — Landing & email system

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [user-visits-landing-page.md](behavioral/user-visits-landing-page.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [user-enters-the-app.md](behavioral/user-enters-the-app.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [system-sends-otp-email.md](behavioral/system-sends-otp-email.md) | ✓ | ✓ | ✓ | ✓ | ✓ |
| [system-sends-invitation-email.md](behavioral/system-sends-invitation-email.md) | ✓ | ✓ | ✓ | ✓ | ✓ |

#### Review 7b — i18n, uploads & error handling

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [system-detects-locale.md](behavioral/system-detects-locale.md) | | | | | |
| [app-renders-rtl-layout.md](behavioral/app-renders-rtl-layout.md) | | | | | |
| [user-uploads-a-file.md](behavioral/user-uploads-a-file.md) | | | | | |
| [system-handles-errors.md](behavioral/system-handles-errors.md) | | | | | |

#### Review 7c — API reference & billing

| Spec | T | L | C | X | O |
|------|---|---|---|---|---|
| [developer-views-api-reference.md](behavioral/developer-views-api-reference.md) | | | | | |
| [user-subscribes-to-a-plan.md](behavioral/user-subscribes-to-a-plan.md) | | | | | |
| [user-manages-billing-portal.md](behavioral/user-manages-billing-portal.md) | | | | | |

### Phase 8: Cross-Cutting Checks

Run once after all per-spec batches (1–7) are complete.

- [ ] Role names (`owner`, `admin`, `member`) spelled identically in all Permission Model tables across all 93 specs
- [ ] Route patterns (`/app/$orgSlug/`, `/app/onboarding`, `/signin`) identical across every spec that references them
- [ ] API method names (`authClient.organization.*`, `authClient.session.*`) match the definitions in `shared-contracts.md`
- [ ] Field names (`activeOrganizationId`, `activeTeamId`) consistent in all state machine and business rule sections
- [ ] Count of files in `input/flows/` equals count of behavioral spec files in `behavioral/`
- [ ] Every path in every Related Specifications section resolves to an existing file in the repo
- [ ] Every Declared Omissions entry names a spec file that exists and covers the described behaviour
- [ ] Invitation 7-day expiry stated identically across `org-admin-invites-a-member.md`, `user-accepts-an-invitation.md`, `user-declines-an-invitation.md`, and `org-admin-cancels-an-invitation.md`
- [ ] HTTP 401 used exclusively for unauthenticated callers and HTTP 403 used exclusively for unauthorized role — no swapped status codes across any spec

---

## Commit History

```
review-1:  product context reviewed
review-2a: project infrastructure specs reviewed
review-2b: backend foundation specs reviewed
review-2c: shared package specs reviewed
review-2d: build & deploy specs reviewed
review-3a: sign-in method specs reviewed
review-3b: sign-out & session lifecycle specs reviewed
review-3c: guest lifecycle & access control specs reviewed
review-4a: org creation & switching specs reviewed
review-4b: org settings & departure specs reviewed
review-4c: invitation specs reviewed
review-4d: member & SSO management specs reviewed
review-4e: team specs reviewed
review-5a: dashboard & profile specs reviewed
review-5b: theme, language & locale specs reviewed
review-5c: passkeys & sessions specs reviewed
review-5d: account & admin basics specs reviewed
review-5e: admin moderation specs reviewed
review-5f: admin role & session ops specs reviewed
review-6a: desktop core specs reviewed
review-6b: desktop system specs reviewed
review-6c: mobile core specs reviewed
review-6d: mobile prefs & extension auth specs reviewed
review-6e: extension behavior specs reviewed
review-7a: landing & email system specs reviewed
review-7b: i18n, uploads & error handling specs reviewed
review-7c: API reference & billing specs reviewed
review-8:  cross-cutting checks resolved — all 94 specs approved
```

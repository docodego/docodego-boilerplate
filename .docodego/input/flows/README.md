# Behavioral Flows — Master Index

Narrative user-journey flows for the DoCodeGo boilerplate. Each file covers one action. Flows are grouped by domain and ordered for reading — start at the top and follow the links.

**Role distinction:**
- **App admin** — system-level admin (`user.role = "admin"`), manages all users via Better Auth admin plugin
- **Org admin** — organization-level admin (`member.role = "admin"`), manages members/teams within a single org

---

## 1. Landing & Entry

| # | Flow | Description |
|---|------|-------------|
| 1 | [User Visits Landing Page](user-visits-landing-page.md) | Static SSG page at `/`, hero, feature cards |
| 2 | [User Enters the App](user-enters-the-app.md) | Auth guard, org check, routing to dashboard or onboarding |

## 2. Authentication

| # | Flow | Description |
|---|------|-------------|
| 3 | [User Signs In with Email OTP](user-signs-in-with-email-otp.md) | Email + 6-digit code verification |
| 4 | [User Signs In with Passkey](user-signs-in-with-passkey.md) | WebAuthn biometric sign-in |
| 5 | [User Signs In as Guest](user-signs-in-as-guest.md) | Anonymous session, `isAnonymous` flag |
| 6 | [Guest Upgrades to Full Account](guest-upgrades-to-full-account.md) | Link real email, migrate data |
| 7 | [User Signs In with SSO](user-signs-in-with-sso.md) | Enterprise SAML/OIDC redirect |
| 8 | [User Signs Out](user-signs-out.md) | Session + cookie clear, redirect |
| 9 | [Session Lifecycle](session-lifecycle.md) | Creation, refresh, expiry, org/team context |

## 3. Onboarding & Organizations

| # | Flow | Description |
|---|------|-------------|
| 10 | [User Creates First Organization](user-creates-first-organization.md) | Onboarding flow for new users |
| 11 | [User Creates an Organization](user-creates-an-organization.md) | Additional org from switcher |
| 12 | [User Switches Organization](user-switches-organization.md) | Org switcher, URL-driven context |
| 13 | [User Updates Organization Settings](user-updates-organization-settings.md) | Edit org name/slug |
| 14 | [User Deletes an Organization](user-deletes-an-organization.md) | Danger zone, owner only |

## 4. Dashboard & Navigation

| # | Flow | Description |
|---|------|-------------|
| 15 | [User Navigates the Dashboard](user-navigates-the-dashboard.md) | Sidebar, header, layout, mobile drawer |

## 5. Member Management (Org Admin)

| # | Flow | Description |
|---|------|-------------|
| 16 | [Org Admin Invites a Member](org-admin-invites-a-member.md) | Email invitation with role, 7-day expiry |
| 17 | [User Accepts an Invitation](user-accepts-an-invitation.md) | Accept/reject/cancel/expire |
| 18 | [Org Admin Changes Member Role](org-admin-changes-member-role.md) | `member.role` update within org |
| 19 | [Org Admin Removes a Member](org-admin-removes-a-member.md) | Remove from org |

## 6. Team Management (Org Admin)

| # | Flow | Description |
|---|------|-------------|
| 20 | [User Creates a Team](user-creates-a-team.md) | Create team, 25 max per org |
| 21 | [User Renames a Team](user-renames-a-team.md) | Rename dialog |
| 22 | [Org Admin Manages Team Members](org-admin-manages-team-members.md) | Add/remove members from team |
| 23 | [User Deletes a Team](user-deletes-a-team.md) | Delete with last-team guard |

## 7. User Settings

| # | Flow | Description |
|---|------|-------------|
| 24 | [User Updates Profile](user-updates-profile.md) | Edit display name |
| 25 | [User Changes Theme](user-changes-theme.md) | Light/dark/system toggle |
| 26 | [User Changes Language](user-changes-language.md) | Language + RTL switching |
| 27 | [User Registers a Passkey](user-registers-a-passkey.md) | WebAuthn registration + management |
| 28 | [User Manages Sessions](user-manages-sessions.md) | View/revoke active sessions |

## 8. App Admin Operations

| # | Flow | Description |
|---|------|-------------|
| 29 | [App Admin Bans a User](app-admin-bans-a-user.md) | Ban with reason/expiry, session invalidation |
| 30 | [App Admin Unbans a User](app-admin-unbans-a-user.md) | Clear ban fields |
| 31 | [App Admin Impersonates a User](app-admin-impersonates-a-user.md) | See app as target user |
| 32 | [App Admin Creates a User](app-admin-creates-a-user.md) | Provision account |
| 33 | [App Admin Changes User Role](app-admin-changes-user-role.md) | Set `user.role` (app-level) |

## 9. Desktop App

| # | Flow | Description |
|---|------|-------------|
| 34 | [User Launches Desktop App](user-launches-desktop-app.md) | Tauri window, state restore |
| 35 | [User Uses System Tray](user-uses-system-tray.md) | Tray toggle, context menu |
| 36 | [User Opens a Deep Link](user-opens-a-deep-link.md) | `docodego://` routing |
| 37 | [Desktop Auto-Updates](desktop-auto-updates.md) | Updater plugin |

## 10. Mobile App

| # | Flow | Description |
|---|------|-------------|
| 38 | [User Launches Mobile App](user-launches-mobile-app.md) | Splash, fonts, locale, auth check |
| 39 | [User Signs In on Mobile](user-signs-in-on-mobile.md) | OTP + SSO (no passkey) |
| 40 | [User Navigates Mobile App](user-navigates-mobile-app.md) | Expo Router, gestures, deep links |

## 11. Browser Extension

| # | Flow | Description |
|---|------|-------------|
| 41 | [User Installs Browser Extension](user-installs-browser-extension.md) | Install, permissions, first run |
| 42 | [Extension Authenticates via Token Relay](extension-authenticates-via-token-relay.md) | Token relay auth pattern |
| 43 | [User Interacts with Extension Popup](user-interacts-with-extension-popup.md) | Popup UI, API calls |

## 12. System & Cross-Cutting

| # | Flow | Description |
|---|------|-------------|
| 44 | [System Sends OTP Email](system-sends-otp-email.md) | OTP email template + delivery |
| 45 | [System Sends Invitation Email](system-sends-invitation-email.md) | Invitation email + link |
| 46 | [System Detects Locale](system-detects-locale.md) | API/web/mobile locale detection |
| 47 | [App Renders RTL Layout](app-renders-rtl-layout.md) | RTL with logical CSS properties |
| 48 | [User Uploads a File](user-uploads-a-file.md) | R2 object storage |
| 49 | [System Handles Errors](system-handles-errors.md) | Global error handler, toasts |
| 50 | [User Subscribes to a Plan](user-subscribes-to-a-plan.md) | DodoPayments *(planned)* |

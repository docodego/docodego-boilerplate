# Behavioral Flows — Master Index

Narrative user-journey flows for the DoCodeGo boilerplate. Each file covers one action. Flows are grouped by domain and ordered for reading — start at the top and follow the links.

**Role distinction:**
- **App admin** — system-level admin (`user.role = "admin"`), manages all users via Better Auth admin plugin
- **Org admin** — organization-level admin (`member.role = "admin"`), manages members/teams within a single org

---

## 1. Landing & Entry

| # | Flow | Description |
|---|------|-------------|
| 1 | [User Visits Landing Page](user-visits-landing-page.md) | Static SSG page at `/`, hero, install command, tech grid |
| 2 | [User Enters the App](user-enters-the-app.md) | Auth guard, org check, routing to dashboard or onboarding |

## 2. Authentication

| # | Flow | Description |
|---|------|-------------|
| 3 | [User Signs In with Email OTP](user-signs-in-with-email-otp.md) | Email + 6-digit code verification |
| 4 | [User Signs In with Passkey](user-signs-in-with-passkey.md) | WebAuthn biometric sign-in |
| 5 | [User Signs In as Guest](user-signs-in-as-guest.md) | Anonymous session, `isAnonymous` flag |
| 6 | [Guest Upgrades to Full Account](guest-upgrades-to-full-account.md) | Link real email, migrate data |
| 7 | [Guest Deletes Anonymous Account](guest-deletes-anonymous-account.md) | Self-service anonymous record cleanup |
| 8 | [User Signs In with SSO](user-signs-in-with-sso.md) | Enterprise SAML/OIDC redirect |
| 9 | [User Signs Out](user-signs-out.md) | Session + cookie clear, redirect |
| 10 | [Session Lifecycle](session-lifecycle.md) | Creation, refresh, expiry, org/team context |
| 11 | [Session Expires Mid-Use](session-expires-mid-use.md) | Stale session detection, redirect to sign-in |
| 12 | [Banned User Attempts Sign-In](banned-user-attempts-sign-in.md) | Ban message, reason, expiry display |

## 3. Onboarding & Organizations

| # | Flow | Description |
|---|------|-------------|
| 13 | [User Creates First Organization](user-creates-first-organization.md) | Onboarding flow for new users |
| 14 | [User Creates an Organization](user-creates-an-organization.md) | Additional org from switcher |
| 15 | [User Switches Organization](user-switches-organization.md) | Org switcher, URL-driven context |
| 16 | [User Updates Organization Settings](user-updates-organization-settings.md) | Edit org name/slug |
| 17 | [User Uploads Organization Logo](user-uploads-organization-logo.md) | Upload logo to R2, display in switcher/header |
| 18 | [User Transfers Organization Ownership](user-transfers-organization-ownership.md) | Hand off owner role to an admin |
| 19 | [User Leaves an Organization](user-leaves-an-organization.md) | Voluntary departure from org |
| 20 | [User Deletes an Organization](user-deletes-an-organization.md) | Danger zone, owner only |

## 4. Dashboard & Navigation

| # | Flow | Description |
|---|------|-------------|
| 21 | [User Navigates the Dashboard](user-navigates-the-dashboard.md) | Sidebar, header, layout, mobile drawer |

## 5. Member Management (Org Admin)

| # | Flow | Description |
|---|------|-------------|
| 22 | [Org Admin Invites a Member](org-admin-invites-a-member.md) | Email invitation with role, 7-day expiry |
| 23 | [User Accepts an Invitation](user-accepts-an-invitation.md) | Accept invitation, join org |
| 24 | [User Declines an Invitation](user-declines-an-invitation.md) | Decline invitation, token invalidated |
| 25 | [Org Admin Cancels an Invitation](org-admin-cancels-an-invitation.md) | Revoke pending invitation |
| 26 | [Org Admin Changes Member Role](org-admin-changes-member-role.md) | `member.role` update within org |
| 27 | [Org Admin Removes a Member](org-admin-removes-a-member.md) | Remove from org |
| 28 | [Org Admin Configures SSO Provider](org-admin-configures-sso-provider.md) | OIDC/SAML setup + domain verification |
| 29 | [Org Admin Manages Custom Roles](org-admin-manages-custom-roles.md) | Create/edit/delete roles beyond owner/admin/member |

## 6. Team Management (Org Admin)

| # | Flow | Description |
|---|------|-------------|
| 30 | [User Creates a Team](user-creates-a-team.md) | Create team, 25 max per org |
| 31 | [User Renames a Team](user-renames-a-team.md) | Rename dialog |
| 32 | [Org Admin Manages Team Members](org-admin-manages-team-members.md) | Add/remove members from team |
| 33 | [User Switches Active Team](user-switches-active-team.md) | Change active team context within org |
| 34 | [User Deletes a Team](user-deletes-a-team.md) | Delete with last-team guard |

## 7. User Settings

| # | Flow | Description |
|---|------|-------------|
| 35 | [User Updates Profile](user-updates-profile.md) | Edit display name |
| 36 | [User Uploads Profile Avatar](user-uploads-profile-avatar.md) | Upload avatar to R2, initials fallback |
| 37 | [User Changes Theme](user-changes-theme.md) | Light/dark/system toggle |
| 38 | [User Changes Language](user-changes-language.md) | Language + RTL switching |
| 39 | [User Syncs Locale Preference](user-syncs-locale-preference.md) | Persist preferredLocale to server across devices |
| 40 | [User Registers a Passkey](user-registers-a-passkey.md) | WebAuthn registration + management |
| 41 | [User Renames a Passkey](user-renames-a-passkey.md) | Update passkey friendly name |
| 42 | [User Removes a Passkey](user-removes-a-passkey.md) | Delete a registered passkey |
| 43 | [User Manages Sessions](user-manages-sessions.md) | View/revoke active sessions |
| 44 | [User Deletes Their Account](user-deletes-their-account.md) | Permanent self-service account deletion |

## 8. App Admin Operations

| # | Flow | Description |
|---|------|-------------|
| 45 | [App Admin Lists and Searches Users](app-admin-lists-and-searches-users.md) | User management dashboard |
| 46 | [App Admin Views User Details](app-admin-views-user-details.md) | User detail page, hub for admin actions |
| 47 | [App Admin Updates User Details](app-admin-updates-user-details.md) | Edit name/email/image on behalf of user |
| 48 | [App Admin Bans a User](app-admin-bans-a-user.md) | Ban with reason/expiry, session invalidation |
| 49 | [App Admin Unbans a User](app-admin-unbans-a-user.md) | Clear ban fields |
| 50 | [App Admin Impersonates a User](app-admin-impersonates-a-user.md) | See app as target user |
| 51 | [App Admin Creates a User](app-admin-creates-a-user.md) | Provision account |
| 52 | [App Admin Changes User Role](app-admin-changes-user-role.md) | Set `user.role` (app-level) |
| 53 | [App Admin Removes a User](app-admin-removes-a-user.md) | Permanent account deletion by admin |
| 54 | [App Admin Revokes User Sessions](app-admin-revokes-user-sessions.md) | Force-terminate user sessions |

## 9. Desktop App

| # | Flow | Description |
|---|------|-------------|
| 55 | [User Launches Desktop App](user-launches-desktop-app.md) | Tauri window, state restore |
| 56 | [User Uses System Tray](user-uses-system-tray.md) | Tray toggle, context menu |
| 57 | [User Opens a Deep Link](user-opens-a-deep-link.md) | `docodego://` routing |
| 58 | [Desktop Opens External Link](desktop-opens-external-link.md) | Opens URL in system browser via opener plugin |
| 59 | [Desktop Auto-Updates](desktop-auto-updates.md) | Updater plugin |
| 60 | [Desktop Sends a Notification](desktop-sends-a-notification.md) | OS-native notifications via Tauri plugin |
| 61 | [User Views Desktop App Version](user-views-desktop-app-version.md) | About section, `get_app_version` IPC |

## 10. Mobile App

| # | Flow | Description |
|---|------|-------------|
| 62 | [User Launches Mobile App](user-launches-mobile-app.md) | Splash, fonts, locale, auth check |
| 63 | [User Signs In on Mobile](user-signs-in-on-mobile.md) | OTP + SSO (no passkey) |
| 64 | [User Navigates Mobile App](user-navigates-mobile-app.md) | Expo Router, gestures, deep links |
| 65 | [Mobile Handles Deep Link](mobile-handles-deep-link.md) | Auth guard on `docodego://` links |
| 66 | [User Changes Theme on Mobile](user-changes-theme-on-mobile.md) | MMKV persistence, native theming |
| 67 | [User Changes Language on Mobile](user-changes-language-on-mobile.md) | MMKV persistence, I18nManager RTL |

## 11. Browser Extension

| # | Flow | Description |
|---|------|-------------|
| 68 | [User Installs Browser Extension](user-installs-browser-extension.md) | Install, permissions, first run |
| 69 | [Extension Authenticates via Token Relay](extension-authenticates-via-token-relay.md) | Token relay auth pattern |
| 70 | [Extension Signs Out](extension-signs-out.md) | Clear token, revert to sign-in prompt |
| 71 | [User Interacts with Extension Popup](user-interacts-with-extension-popup.md) | Popup UI, API calls |
| 72 | [Extension Receives an Update](extension-receives-an-update.md) | Auto-update, token migration, what's new |

## 12. System & Cross-Cutting

| # | Flow | Description |
|---|------|-------------|
| 73 | [System Sends OTP Email](system-sends-otp-email.md) | OTP email template + delivery |
| 74 | [System Sends Invitation Email](system-sends-invitation-email.md) | Invitation email + link |
| 75 | [System Detects Locale](system-detects-locale.md) | API/web/mobile locale detection |
| 76 | [App Renders RTL Layout](app-renders-rtl-layout.md) | RTL with logical CSS properties |
| 77 | [User Uploads a File](user-uploads-a-file.md) | R2 object storage |
| 78 | [System Handles Errors](system-handles-errors.md) | Global error handler, toasts |
| 79 | [Developer Views API Reference](developer-views-api-reference.md) | Scalar interactive API docs |
| 80 | [User Subscribes to a Plan](user-subscribes-to-a-plan.md) | DodoPayments *(planned)* |
| 81 | [User Manages Billing Portal](user-manages-billing-portal.md) | Self-service billing *(planned)* |

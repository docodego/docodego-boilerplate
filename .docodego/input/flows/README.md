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
| 10 | [Session Expires Mid-Use](session-expires-mid-use.md) | Stale session detection, redirect to sign-in |
| 11 | [Banned User Attempts Sign-In](banned-user-attempts-sign-in.md) | Ban message, reason, expiry display |

## 3. Onboarding & Organizations

| # | Flow | Description |
|---|------|-------------|
| 12 | [User Creates First Organization](user-creates-first-organization.md) | Onboarding flow for new users |
| 13 | [User Creates an Organization](user-creates-an-organization.md) | Additional org from switcher |
| 14 | [User Switches Organization](user-switches-organization.md) | Org switcher, URL-driven context |
| 15 | [User Updates Organization Settings](user-updates-organization-settings.md) | Edit org name/slug |
| 16 | [User Transfers Organization Ownership](user-transfers-organization-ownership.md) | Hand off owner role to an admin |
| 17 | [User Leaves an Organization](user-leaves-an-organization.md) | Voluntary departure from org |
| 18 | [User Deletes an Organization](user-deletes-an-organization.md) | Danger zone, owner only |

## 4. Dashboard & Navigation

| # | Flow | Description |
|---|------|-------------|
| 19 | [User Navigates the Dashboard](user-navigates-the-dashboard.md) | Sidebar, header, layout, mobile drawer |

## 5. Member Management (Org Admin)

| # | Flow | Description |
|---|------|-------------|
| 20 | [Org Admin Invites a Member](org-admin-invites-a-member.md) | Email invitation with role, 7-day expiry |
| 21 | [User Accepts an Invitation](user-accepts-an-invitation.md) | Accept/reject/cancel/expire |
| 22 | [Org Admin Changes Member Role](org-admin-changes-member-role.md) | `member.role` update within org |
| 23 | [Org Admin Removes a Member](org-admin-removes-a-member.md) | Remove from org |

## 6. Team Management (Org Admin)

| # | Flow | Description |
|---|------|-------------|
| 24 | [User Creates a Team](user-creates-a-team.md) | Create team, 25 max per org |
| 25 | [User Renames a Team](user-renames-a-team.md) | Rename dialog |
| 26 | [Org Admin Manages Team Members](org-admin-manages-team-members.md) | Add/remove members from team |
| 27 | [User Deletes a Team](user-deletes-a-team.md) | Delete with last-team guard |

## 7. User Settings

| # | Flow | Description |
|---|------|-------------|
| 28 | [User Updates Profile](user-updates-profile.md) | Edit display name |
| 29 | [User Changes Theme](user-changes-theme.md) | Light/dark/system toggle |
| 30 | [User Changes Language](user-changes-language.md) | Language + RTL switching |
| 31 | [User Registers a Passkey](user-registers-a-passkey.md) | WebAuthn registration + management |
| 32 | [User Removes a Passkey](user-removes-a-passkey.md) | Delete a registered passkey |
| 33 | [User Manages Sessions](user-manages-sessions.md) | View/revoke active sessions |
| 34 | [User Deletes Their Account](user-deletes-their-account.md) | Permanent self-service account deletion |

## 8. App Admin Operations

| # | Flow | Description |
|---|------|-------------|
| 35 | [App Admin Lists and Searches Users](app-admin-lists-and-searches-users.md) | User management dashboard |
| 36 | [App Admin Bans a User](app-admin-bans-a-user.md) | Ban with reason/expiry, session invalidation |
| 37 | [App Admin Unbans a User](app-admin-unbans-a-user.md) | Clear ban fields |
| 38 | [App Admin Impersonates a User](app-admin-impersonates-a-user.md) | See app as target user |
| 39 | [App Admin Creates a User](app-admin-creates-a-user.md) | Provision account |
| 40 | [App Admin Changes User Role](app-admin-changes-user-role.md) | Set `user.role` (app-level) |

## 9. Desktop App

| # | Flow | Description |
|---|------|-------------|
| 41 | [User Launches Desktop App](user-launches-desktop-app.md) | Tauri window, state restore |
| 42 | [User Uses System Tray](user-uses-system-tray.md) | Tray toggle, context menu |
| 43 | [User Opens a Deep Link](user-opens-a-deep-link.md) | `docodego://` routing |
| 44 | [Desktop Auto-Updates](desktop-auto-updates.md) | Updater plugin |
| 45 | [Desktop Sends a Notification](desktop-sends-a-notification.md) | OS-native notifications via Tauri plugin |

## 10. Mobile App

| # | Flow | Description |
|---|------|-------------|
| 46 | [User Launches Mobile App](user-launches-mobile-app.md) | Splash, fonts, locale, auth check |
| 47 | [User Signs In on Mobile](user-signs-in-on-mobile.md) | OTP + SSO (no passkey) |
| 48 | [User Navigates Mobile App](user-navigates-mobile-app.md) | Expo Router, gestures, deep links |
| 49 | [Mobile Handles Deep Link](mobile-handles-deep-link.md) | Auth guard on `docodego://` links |

## 11. Browser Extension

| # | Flow | Description |
|---|------|-------------|
| 50 | [User Installs Browser Extension](user-installs-browser-extension.md) | Install, permissions, first run |
| 51 | [Extension Authenticates via Token Relay](extension-authenticates-via-token-relay.md) | Token relay auth pattern |
| 52 | [User Interacts with Extension Popup](user-interacts-with-extension-popup.md) | Popup UI, API calls |
| 53 | [Extension Receives an Update](extension-receives-an-update.md) | Auto-update, token migration, what's new |

## 12. System & Cross-Cutting

| # | Flow | Description |
|---|------|-------------|
| 54 | [System Sends OTP Email](system-sends-otp-email.md) | OTP email template + delivery |
| 55 | [System Sends Invitation Email](system-sends-invitation-email.md) | Invitation email + link |
| 56 | [System Detects Locale](system-detects-locale.md) | API/web/mobile locale detection |
| 57 | [App Renders RTL Layout](app-renders-rtl-layout.md) | RTL with logical CSS properties |
| 58 | [User Uploads a File](user-uploads-a-file.md) | R2 object storage |
| 59 | [System Handles Errors](system-handles-errors.md) | Global error handler, toasts |
| 60 | [User Subscribes to a Plan](user-subscribes-to-a-plan.md) | DodoPayments *(planned)* |

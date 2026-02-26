# User Settings

## Navigating to Settings

The user clicks a settings link or avatar menu option from anywhere inside `/app`. The app navigates to `/app/settings`. At the top of the settings page, a back link points to `/app` so the user can return to the main dashboard.

The settings page uses a layout with navigation tabs along the side (or top on mobile). The tabs are: **Profile**, **Appearance**, and **Security**. Clicking a tab navigates to the corresponding nested route. By default, visiting `/app/settings` redirects to `/app/settings/profile`.

---

## Profile Settings

**Route:** `/app/settings/profile`

The user sees a profile form with the following fields:

- **Display name** -- a text input, pre-filled with the user's current name. The user can edit this freely.
- **Email** -- a text input showing the user's email address. This field is disabled/read-only. The user cannot change their email from this screen.
- **Avatar** -- a placeholder area for the user's profile image. Initially this shows a generic avatar or the user's initials. (Avatar upload is not wired up in the initial build -- the placeholder is there for future use.)

Below the form, a **Save** button submits the changes. When the user clicks Save, the app calls `authClient.updateUser()` (or an equivalent oRPC mutation) with the updated display name. While the request is in flight, the button shows a loading state. On success, a toast notification confirms the update. On failure, an error toast appears with the issue.

The form uses TanStack Query for the mutation. After a successful save, the cached user data is invalidated so the rest of the app picks up the new display name immediately.

---

## Appearance Settings

**Route:** `/app/settings/appearance`

### Theme Toggle

The user sees a theme selector with three options: **Light**, **Dark**, and **System**. These are presented as a segmented control or radio group.

When the user picks an option, the Zustand theme-store updates immediately. The store calls `applyTheme()`, which resolves the actual theme (if "System" is selected, it reads `prefers-color-scheme` from the OS) and then sets or removes the `.dark` class on the `<html>` element. Tailwind picks up the class change and the entire UI re-renders with the new color scheme instantly -- no page reload needed.

The selected preference is persisted to `localStorage`. When the user refreshes the page or comes back later, the theme-store reads from `localStorage` on initialization and applies the saved preference before the first paint, preventing any flash of wrong theme.

If the user chose "System" and later changes their OS theme, the app reacts to the `prefers-color-scheme` media query change and updates in real time.

### Language Selector

Below the theme toggle, the user sees a language selector component. This is a dropdown or select control listing the available languages: **English** and **Arabic** (with more possible in the future).

When the user selects a different language, the app calls `i18next.changeLanguage(locale)`. i18next loads the new translation resources and triggers a re-render of all translated strings across the UI. The change is immediate -- no page reload.

When the user switches to **Arabic**, the app sets `dir="rtl"` on the `<html>` element. Tailwind's logical properties (start/end instead of left/right, ms/me instead of ml/mr) automatically mirror the entire layout. Navigation moves to the right side, text aligns right, and all spacing flips. Switching back to English restores `dir="ltr"` and the layout mirrors back.

The selected language is persisted to `localStorage`. On the next visit, the app reads the stored locale during i18next initialization and loads the correct language and direction before the UI renders.

---

## Security Settings

**Route:** `/app/settings/security`

This page has two sections: **Passkeys** and **Active Sessions**.

### Passkeys

The user sees a passkeys section with a header and a list of their registered passkeys. If no passkeys are registered yet, the list area shows an empty state message like "No passkeys registered yet."

A **Register passkey** button sits above or next to the list. When the user clicks it, the app calls `authClient.passkey.addPasskey()`. This triggers the browser's WebAuthn registration ceremony -- the browser prompts the user to authenticate with their device (fingerprint, face recognition, security key, etc.). If the user completes the ceremony, the new passkey is stored in the `passkey` table on the server. The passkey list refreshes and now shows the newly registered passkey with its name, device type, and creation date.

Each passkey in the list has a **Delete** button. When the user clicks Delete, a confirmation prompt appears. On confirmation, the app calls `authClient.passkey.deletePasskey({ id })` to remove that passkey from the server. The list refreshes to reflect the removal.

If the WebAuthn ceremony fails (the user cancels the browser prompt, or the device doesn't support it), the app shows an error toast explaining what happened. No passkey is created.

### Active Sessions

Below the passkeys section, the user sees an **Active sessions** section. The app fetches the session list using `authClient.listSessions()`. The results are displayed in a table with these columns:

- **User agent** -- the browser and OS info for the session (e.g., "Chrome on Windows")
- **Created** -- when the session was created
- **Actions** -- a Revoke button for each session

The current session (the one the user is browsing with right now) is identified and marked with a **"Current"** badge next to the user agent text. The Revoke button is not shown for the current session -- the user cannot revoke their own active session from here.

For every other session, the **Revoke** button calls `authClient.revokeSession({ token })` for that specific session. The session is terminated on the server, and the session list refreshes to reflect the change. If someone was using that session on another device, they are signed out on their next request.

When there is more than one session (meaning other sessions exist besides the current one), a **"Revoke all other sessions"** button appears at the top or bottom of the section. Clicking it calls `authClient.revokeOtherSessions()`. All sessions except the current one are terminated in a single call. The list refreshes and only the current session remains.

After any revocation action, the session list is refetched so the displayed data is always up to date.

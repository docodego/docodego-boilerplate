[← Back to Index](README.md)

# User Updates Profile

## Navigating to Profile Settings

The user navigates to `/app/settings/profile` via the Settings link in the sidebar's user section. This is a user-level route, not scoped to any specific organization — it lives outside the `$orgSlug/` namespace.

## The Profile Form

The profile page displays a form with localized labels and the user's current information. The display name field is editable. The email field is shown but disabled or read-only, since email changes are not handled through this form. An avatar section is present as a placeholder for future avatar upload functionality.

## Saving Changes

The user edits their display name and clicks the Save button. The button transitions to a loading state while the request is in flight. The app calls `authClient.updateUser()` with the updated name.

On success, a toast confirmation appears via Sonner, confirming the profile was updated. The cached user data is invalidated in TanStack Query, causing any component that displays the user's name — the avatar dropdown in the header, for instance — to re-fetch and reflect the new name immediately across the entire app.

On failure, an error toast appears describing what went wrong. The form retains the user's edits so they can retry without re-entering their changes.

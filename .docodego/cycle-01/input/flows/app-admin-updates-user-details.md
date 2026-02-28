[← Back to Index](README.md)

# App Admin Updates User Details

## Navigating to the Edit Form

The app admin opens the [user detail page](app-admin-views-user-details.md) for the target user and clicks the "Edit" action button. A localized form appears — either inline on the detail page or as a modal — pre-filled with the user's current display name, email address, and profile image. This flow is for editing basic user information only; changing a user's role is handled in a [separate flow](app-admin-changes-user-role.md).

## Editing the User's Information

The form fields are editable and include localized labels and placeholder text. The app admin modifies whichever fields need updating — for example, correcting a misspelled name or changing an email address. Client-side validation ensures the email field contains a valid email format and that the display name is not empty before the form can be submitted. The "Save" button remains disabled until at least one field differs from its original value.

## Saving the Changes

The app admin clicks "Save" and the button transitions to a loading state. The client calls `authClient.admin.updateUser({ userId, name, email, image })` with only the changed fields. The server verifies that the caller has the app admin role (`user.role = "admin"`) and applies the updates to the target user's record. On success, a localized toast notification confirms that the user's details were updated, and the detail page refreshes to display the new values immediately.

## Error Handling

If the server rejects the update — for example, because the new email address is already in use by another account — a localized error message is displayed. The form retains the app admin's edits so they can correct the issue and retry without re-entering all fields. Network errors are handled with a generic localized error toast.

## Self-Edit Restriction

This flow is restricted to editing other users' accounts. If the app admin attempts to open the edit form for their own account, the "Edit" button is either hidden or disabled with a localized tooltip explaining that personal account changes should be made through the standard [profile settings](user-updates-profile.md). This separation ensures that admin actions are always performed on behalf of another user, maintaining a clear audit boundary between self-service and administrative operations.

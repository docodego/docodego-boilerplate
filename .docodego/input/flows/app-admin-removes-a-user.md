[← Back to Index](README.md)

# App Admin Removes a User

## The app admin locates the user to remove

The app admin navigates to the user management section of the app admin dashboard. This view [lists all registered users](app-admin-lists-and-searches-users.md) with their current status, role, and account details. The app admin searches for or scrolls to the specific user they need to permanently remove, then selects that user to open their profile detail view. From here, the app admin clicks the "Remove" action button, which opens a destructive action confirmation dialog.

## The app admin confirms the permanent removal

Because removing a user is irreversible and fundamentally different from [banning a user](app-admin-bans-a-user.md) (which can be undone), the localized confirmation dialog makes the consequences explicit. The dialog states that this action will permanently delete the user's account, revoke all active sessions, remove the user from every organization they belong to, and erase their account record entirely. The app admin must type the user's email address into a confirmation field to proceed, preventing accidental deletions. Only after the confirmation input matches does the "Remove permanently" button become active.

## The system processes the removal

When the app admin confirms, the client calls `authClient.admin.removeUser({ userId })`. The server receives the request, verifies the caller has the app admin role (`user.role = "admin"`), and begins the removal sequence. First, all active sessions belonging to the user are revoked immediately, signing them out everywhere. Next, the user's memberships in all organizations are deleted — they are removed from every org roster and every team they belonged to. Finally, the user's account record itself is deleted from the system. This entire operation is atomic: either all steps complete successfully, or none of them take effect.

## The removed user experiences the removal

Because all sessions are invalidated, any active browsing session the removed user had fails on their next API request. The client receives an authentication error, and the user is signed out. If the removed user attempts to sign in again, the system finds no matching account and treats them as an unrecognized user. Unlike a [banned user](banned-user-attempts-sign-in.md) who sees a ban message, a removed user simply cannot authenticate — as far as the system is concerned, their account never existed. The user would need to register a completely new account to use the application again.

## The action is audit logged

The removal action is recorded in the audit log, capturing which app admin performed the removal, which user was removed, and the timestamp. Even though the user's account record no longer exists, the audit entry preserves a reference to the deleted user's identifier and email so that the action remains traceable for compliance and accountability purposes.

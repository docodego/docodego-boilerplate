[← Back to Index](README.md)

# User Deletes an Organization

## The Danger Zone

On the organization settings page at `/app/$orgSlug/settings`, a danger zone section appears at the bottom of the page. This section is only visible to the organization owner — admins and regular members do not see it.

## Initiating Deletion

The owner clicks the delete button in the danger zone. A confirmation dialog appears with a clear, permanent warning explaining that deleting the organization cannot be undone. All organization data, member associations, and team structures will be permanently removed. The dialog requires an explicit confirmation action to proceed — there is no way to accidentally trigger deletion with a single click.

## After Deletion

When the owner confirms, the app calls `authClient.organization.delete({ organizationId })`. Upon success, the user is redirected to `/app`. From there, the standard entry logic takes over: if the user still belongs to other organizations, they are redirected to their next active org's dashboard. If the deleted org was their only organization, they are redirected to `/app/onboarding` to create a new one.

All members of the deleted organization lose access immediately. Any member who was viewing the org's dashboard at the time of deletion will encounter the org context becoming invalid on their next navigation or data fetch, and they will be routed away.

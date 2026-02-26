# Org Admin Removes a Member

## Initiating Removal

From the Members tab on the `/app/$orgSlug/members` page, each member row has a delete button that allows an org admin or owner to remove that member from the organization. The owner's row does not have a delete button — the owner cannot be removed from their own organization.

## Confirmation and Execution

When the org admin clicks the delete button, a confirmation step appears to prevent accidental removals. After the org admin confirms, the client calls `authClient.organization.removeMember({ memberIdOrEmail, organizationId })`. The server removes the member's association with the organization, revoking all their access immediately.

## After Removal

The members list refreshes to reflect the removal. If the removed member happens to be currently viewing the organization — browsing its pages or working within its context — their next request to the server will fail the membership check. At that point, they are redirected away from the organization, typically back to a default page or an organization selector. The removed user's account is not deleted; they simply no longer have any relationship with this organization.

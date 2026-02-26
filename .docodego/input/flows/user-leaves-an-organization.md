[← Back to Index](README.md)

# User Leaves an Organization

## Initiating Departure

From the organization settings page at `/app/$orgSlug/settings`, or from the members list at `/app/$orgSlug/members`, the user sees a "Leave organization" option. This option is available to any member who is not the organization owner. The owner does not see this option — an owner cannot leave their own organization. If the owner wants to step away, they must first transfer ownership to another member or [delete the organization](user-deletes-an-organization.md) entirely.

## Confirmation

When the user clicks "Leave organization," a confirmation dialog appears with translated text warning that they will lose access to all resources within the organization. The dialog makes clear that this action is voluntary and that the user will need a new [invitation](user-accepts-an-invitation.md) to rejoin. The user must explicitly confirm to proceed.

## Processing the Departure

After confirmation, the client calls `authClient.organization.removeMember({ memberIdOrEmail, organizationId })` with the user's own member identity. The server validates the request, confirms that the user is not the organization owner, and removes the membership association. All access the user had within this organization is revoked immediately.

## After Leaving

The user is redirected away from the organization they just left. If the user belongs to other organizations, they are redirected to the next available organization's dashboard. If this was their only organization, they are redirected to `/app/onboarding` to [create a new one](user-creates-first-organization.md). Any subsequent attempt to navigate to the former organization's routes will fail the membership check, and the user will be routed to an organization selector or their default organization.

## Impact on the Organization

The organization's members list updates to reflect the departure. Other members and admins can see that the user is no longer part of the organization. This flow is the voluntary counterpart to [Org Admin Removes a Member](org-admin-removes-a-member.md), which covers involuntary removal by an administrator.

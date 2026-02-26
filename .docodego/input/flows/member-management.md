# Member Management

## Viewing Members

The members page lives at `/app/$orgSlug/members`. When a user navigates there, the page presents three tabs: Members, Pending, and History.

The Members tab is the default view. It shows a table of all current members of the organization. Each row displays the member's name, email address, and role. Admin and owner rows also have action buttons for role changes and removal. The data is fetched via `authClient.organization.listMembers({ query: { organizationId } })`.

The Pending tab shows invitations that have been sent but not yet accepted or rejected. Each pending invitation displays the invitee's email, the role they were invited with, and when the invitation expires. Admins and owners see a cancel button on each pending invitation so they can revoke it before the invitee responds.

The History tab shows a log of past invitations. Each entry has the invitee's email, the role, and a status badge indicating the outcome: green for accepted, red for rejected, and a neutral color for canceled. This gives admins visibility into the invitation lifecycle without cluttering the active members view.

## Inviting a Member

From the members page, an admin or owner clicks the "Invite member" button. A dialog opens with two fields: an email input and a role dropdown. The role dropdown offers Member and Admin as options.

The user types the invitee's email address, selects the role, and clicks submit. The frontend calls `authClient.organization.inviteMember({ email, inviteRole, organizationId })`. Better Auth creates an invitation record with a 7-day expiry and triggers an invitation email to the provided address.

In development, the email is logged to the console rather than actually sent. In production, the configured email transport delivers the invitation.

After successful submission, the dialog closes and the Pending tab refreshes to show the new invitation. If the email address belongs to someone who already has a pending invitation, the system handles it according to the configured behavior (either canceling the old one and creating a new one, or rejecting the duplicate).

## Accepting and Rejecting Invitations

When someone receives an invitation email, it contains a link to accept the invitation. Clicking the link brings them to the app.

If the invitee already has an account, the link resolves to accepting the invitation directly. The frontend calls `authClient.organization.acceptInvitation()` and the user becomes a member of the organization with the role specified in the invitation. They are then navigated to the org's dashboard.

If the invitee does not have an account, they go through the standard sign-up flow first. After creating their account, the invitation acceptance completes and they land in the org.

The invitee can also reject the invitation by calling `authClient.organization.rejectInvitation()`. A rejected invitation moves to the History tab with a "rejected" status badge.

Back on the inviting org's side, admins can cancel a pending invitation at any time from the Pending tab. Canceling an invitation invalidates the link and moves the record to the History tab with a "canceled" status.

Invitations expire after 7 days. Expired invitations become invalid and the link no longer works. The admin can send a fresh invitation if needed.

## Changing Member Roles

An admin or owner can change a member's role from the Members tab. Each member row (except the owner's own row) has a role control that allows changing the assignment.

When an admin selects a new role for a member, the frontend calls `authClient.organization.updateRole()` with the member ID and the new role. The available role options depend on the organization's configuration -- by default, the choices are Member and Admin.

Owners have a special status and cannot have their role changed by anyone other than themselves (through ownership transfer, which is a separate flow). The owner row does not show a role-change control.

Role changes take effect immediately. The affected member's permissions update on their next request, and if they are currently viewing the dashboard, their UI reflects the new capabilities on the next data refresh.

## Removing Members

An admin or owner can remove a member from the organization. Each member row in the Members tab has a delete button -- except for the owner's row, since the owner cannot be removed.

When the admin clicks the delete button, a confirmation step ensures the action is intentional. After confirmation, the frontend calls `authClient.organization.removeMember({ memberIdOrEmail, organizationId })`. The member record is deleted and the member loses access to the organization immediately.

The members list refreshes after the removal to reflect the updated roster. If the removed member is currently viewing the org's dashboard, their next navigation or data fetch will fail the membership check and they will be redirected away from the org.
